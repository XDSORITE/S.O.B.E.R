import threading
from flask import Flask, request, jsonify
from flask_cors import CORS
from main import (build_features, calculate_risk, predict_severity, get_routes, 
                  sample_waypoints, get_bars, get_accident_density, get_weather,
                    get_time_features, get_cached_overpass, init_db, log_risk, log_route, DB_PATH,
                    active_alerts, alert_lock, check_weather_alerts, start_alert_poller,
                    get_crash_hotspots, routes_lock, active_routes, get_cached_route,
                    cache_route)
import concurrent.futures, time
import numpy as np, sqlite3
from flask import Response
from datetime import datetime


init_db()
check_weather_alerts()
start_alert_poller(interval_minutes=30)

app= Flask(__name__)
CORS(app)

@app.route("/health")
def health():
    return jsonify({"status":"ok", "endpoints": ["/risk", "/safe_route", "/health"]})


@app.route("/risk", methods=["GET"])
def risk():
    lat = float(request.args.get("lat"))
    lon = float(request.args.get("lon"))

    features = build_features(lat,lon)

    score, risk_level, reasons, action= calculate_risk(
        features["hour"],
        features["is_weekend"],
        features["rain"],
        features["wind_speed"],
        features["bars"],
        features["accident_density"],
        features["temperature"]
    )

    predicted_severity, severity_confidence = predict_severity(
        features["hour"],
        features["is_weekend"],
        features["temperature"],
        features["rain"],
        features["wind_speed"],
        features["bars"],
        features["accident_density"]
    )

    log_risk(
        "/risk", lat, lon,
        features["hour"], features["is_weekend"],
        score, risk_level,
        features["bars"], features["accident_density"],
        features["temperature"], features["rain"], features["wind_speed"]
    )



    return jsonify({
        "risk_score":score,
        "risk_level":risk_level,
        "reasons": reasons,
        "action": action,
        "ml_prediction":{
            "predicted_severity": predicted_severity,
            "confidence": severity_confidence
        },
        "features":features
    })


@app.route("/safe_route", methods=["GET"])
def safe_route():
    origin_lat = float(request.args.get("olat"))
    origin_lon = float(request.args.get("olon"))
    dest_lat = float(request.args.get("dlat"))
    dest_lon = float(request.args.get("dlon"))

    # Check cache first
    route_id = f"{round(origin_lat,3)}_{round(origin_lon,3)}_{round(dest_lat,3)}_{round(dest_lon,3)}"
    cached = get_cached_route(route_id)
    if cached:
        return jsonify(cached["routes"])

    routes = get_routes(origin_lat, origin_lon, dest_lat, dest_lon)

    if not routes:
        return jsonify({"error": "No routes found"}), 500

    def score_route(route):
        geometry = route.get("geometry", [])
        waypoints = sample_waypoints(geometry) if geometry else []

        if len(waypoints) == 0:
            return {
                "average_risk": 999,
                "risk_level": "UNKNOWN",
                "distance_km": round(route.get("distance", 0) / 1000, 2),
                "duration_min": round(route.get("duration", 0) / 60, 1),
                "waypoints": [],
                "geometry": geometry
            }

        mid_index = len(waypoints) // 2
        mid = waypoints[mid_index]
        bars, accident_density = get_cached_overpass(mid["lat"], mid["lon"])

        def score_point(wp):
            hour, day_of_week, is_weekend = get_time_features()
            temperature, rain, wind_speed = get_weather(wp["lat"], wp["lon"])
            score, level, reasons, action = calculate_risk(
                hour, is_weekend, rain, wind_speed,
                bars, accident_density, temperature
            )
            return {
                "lat": wp["lat"],
                "lon": wp["lon"],
                "risk_score": score,
                "risk_level": level,
            }

        with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
            scored_waypoints = list(executor.map(score_point, waypoints))

        scores = [w["risk_score"] for w in scored_waypoints]
        avg_risk = round(sum(scores) / len(scores))
        max_risk = max(scores)

        if max_risk >= 75:
            avg_risk = min(100, avg_risk + 10)

        if avg_risk >= 75:
            risk_level = "CRITICAL"
        elif avg_risk >= 50:
            risk_level = "HIGH"
        elif avg_risk >= 25:
            risk_level = "MEDIUM"
        else:
            risk_level = "LOW"

        return {
            "average_risk": avg_risk,
            "risk_level": risk_level,
            "distance_km": round(route["distance"] / 1000, 2),
            "duration_min": round(route["duration"] / 60, 1),
            "waypoints": scored_waypoints,
            "geometry": [[c[1], c[0]] for c in route["geometry"]["coordinates"]],
            "max_waypoint_risk": max_risk
        }

    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
        scored_routes = list(executor.map(score_route, routes))

    # Deduplicate by distance
    seen_distances = set()
    unique_routes = []
    for r in scored_routes:
        key = round(r["distance_km"], 1)
        if key not in seen_distances:
            seen_distances.add(key)
            unique_routes.append(r)
    scored_routes = unique_routes

    # Sort safest first
    scored_routes.sort(key=lambda r: r["average_risk"])

    # Rank correctly
    for i, r in enumerate(scored_routes):
        r["rank"] = i + 1

    best = scored_routes[0]
    worst = scored_routes[-1]

    if scored_routes:
        log_route(
            origin_lat, origin_lon, dest_lat, dest_lon,
            len(scored_routes),
            best["average_risk"],
            best["risk_level"],
            best["distance_km"],
            best["duration_min"]
        )

    response_data = {
        "route_id": route_id,
        "origin": {"lat": origin_lat, "lon": origin_lon},
        "destination": {"lat": dest_lat, "lon": dest_lon},
        "recommended_route": 0,
        "total_routes": len(scored_routes),
        "recommendation": {
            "text": f"Route {best['rank']} is the safest choice",
            "risk_reduction": round(worst["average_risk"] - best["average_risk"])
        },
        "routes": scored_routes
    }

    cache_route(route_id, {
        "routes": response_data,
        "last_updated": time.time()
    })

    return jsonify(response_data)

@app.route("/heatmap", methods=["GET"])
def heatmap():
    lat1 = float(request.args.get("lat1"))
    lon1 = float(request.args.get("lon1"))
    lat2 = float(request.args.get("lat2"))
    lon2 = float(request.args.get("lon2"))

    grid_size = int(request.args.get("grid_size", request.args.get("grid",6)))
    grid_size = min(grid_size, 8)

    lat_steps = np.linspace(lat1, lat2, grid_size)
    lon_steps = np.linspace(lon1, lon2, grid_size)

    grid_points = []
    for lat in lat_steps:
        for lon in lon_steps:
            grid_points.append({"lat": round(lat,4), "lon": round(lon,4)})

    print(f"Heatmap: scoring {len(grid_points)} grid points...")

    hour, day_of_week, is_weekend = get_time_features()

    results = []
    for i, point in enumerate(grid_points):
        try:
            bars, accident_density = get_cached_overpass(point["lat"], point["lon"])
            temperature, rain, wind_speed = get_weather(point["lat"], point["lon"])

            score, risk_level, reasons, action = calculate_risk(
                hour, is_weekend, rain, wind_speed,
                bars, accident_density, temperature
            )

            predicted_severity, confidence = predict_severity(
                hour, is_weekend, temperature,
                rain, wind_speed, bars, accident_density
            )

            results.append({
                "lat": point["lat"],
                "lon": point["lon"],
                "risk_score": score,
                "risk_level": risk_level,
                "predicted_severity": predicted_severity
            })
            print(f"Point {i+1}/{len(grid_points)} - score: {score}")
            time.sleep(0.5)
        
        except Exception as e:
            print(f"Heatmap point error: {e}")
            return {
                "lat": point["lat"],
                "lon": point["lon"],
                "risk_score": 0,
                "risk_level": "LOW",
                "predicted_severity": "unknown"
            }

    return jsonify({
        "grid_size": grid_size,
        "total_points": len(results),
        "bounds": {
            "lat1": lat1, "lon1": lon1,
            "lat2": lat2, "lon2": lon2
        },
        "heatmap": results
    })


@app.route("/stats", methods=["GET"])
def stats():
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()

        c.execute("SELECT COUNT(*) FROM risk_logs")
        total_risk_requests = c.fetchone()[0]

        c.execute("SELECT COUNT(*) FROM route_logs")
        total_route_requests = c.fetchone()[0]

        c.execute("SELECT AVG(risk_score) FROM risk_logs")
        avg_risk = round(c.fetchone()[0] or 0,1)

        c.execute("""
            SELECT latitude, longitude, risk_score, risk_level
            FROM risk_logs
            ORDER BY risk_score DESC LIMIT 1
        """)
        highest = c.fetchone()

        c.execute("""
            SELECT hour, AVG(risk_score) as avg_score
            FROM risk_logs
            GROUP BY hour
            ORDER BY avg_score DESC LIMIT 1
        """)
        dangerous_hour = c.fetchone()

        c.execute("""
            SELECT risk_level, COUNT(*)
            FROM risk_logs
            GROUP BY risk_level
        """)
        breakdown = dict(c.fetchall())

        c.execute("""
            SELECT timestamp, latitude, longitude, risk_score, risk_level
            FROM risk_logs
            ORDER BY timestamp DESC LIMIT 5
        """)
        recent = [
            {"timestamp": r[0], "lat": r[1], "lon": r[2],
             "risk_score": r[3], "risk_level": r[4]}
            for r in c.fetchall()
        ]

        conn.close()

        return jsonify({
            "total_requests": {
                "risk": total_risk_requests,
                "routes": total_route_requests
            },
            "average_risk_score": avg_risk,
            "highest_risk_location":{
                "lat": highest[0] if highest else None,
                "lon": highest[1] if highest else None,
                "risk_score": highest[2] if highest else None,
                "risk_level": highest[3] if highest else None
            },
            "most_dangerous_hour": {
                "hour": dangerous_hour[0] if dangerous_hour else None,
                "average_score": round(dangerous_hour[1],1) if dangerous_hour else None
            },
            "risk_level_breakdown": breakdown,
            "recent_requests":recent
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/alerts", methods=["GET"])
def alerts():
    with alert_lock:
        current_alerts = list(active_alerts)

    return jsonify({
        "total_alerts": len(active_alerts),
        "alerts": current_alerts,
        "monitored_locations": 3,
        "next_check": "Every 30 minutes"
    })

@app.route("/alerts/check", methods=["GET"])
def alerts_check():
    """Manually trigger an alert check"""
    new_alerts = check_weather_alerts()
    return jsonify({
        "total_alerts": len(new_alerts),
        "alerts": new_alerts,
        "message": "Alert check completed"
    })

@app.route("/ml/stats", methods=["GET"])
def ml_stats():
    from main import severity_model

    features = [
        "hour", "is_weekend", "temperature", "rain", "wind_speed", "bars",
        "accident_density", "time_of_day", "is_night", "is_rush_hour"
    ]

    if severity_model:
        importance = {
            feat: round(float(imp), 3)
            for feat, imp in zip(features, severity_model.feature_importances_)
        }
        n_estimators = severity_model.n_estimators
    else:
        importance = {}
        n_estimators = 0


    return jsonify({
        "model": "Random Forest Classifier",
        "version": "2.0",
        "n_estimators": n_estimators,
        "features": features,
        "training_records": 5000,
        "cross_validation_accuracy": 0.628,
        "cv_std": 0.004,
        "target": "crash_severity",
        "classes": ["property_damage_only", "injury_likely", "fatal_risk"],
        "feature_importance": importance
    })

@app.route("/ml/confusion_matrix", methods=["GET"])
def confusion_matrix_img():
    from flask import send_file
    import os
    path = os.path.join(os.path.dirname(__file__), "confusion_matrix.png")
    return send_file(path, mimetype="image/png")

@app.route("/ml/feature_importance", methods=["GET"])
def feature_importance_img():
    from flask import send_file
    import os
    path = os.path.join(os.path.dirname(__file__), "feature_importance.png")
    return send_file(path, mimetype="image/png")

@app.route("/risk/trend", methods=["GET"])
def risk_trend():
    lat = float(request.args.get("lat"))
    lon = float(request.args.get("lon"))

    temperature, rain, wind_speed = get_weather(lat,lon)
    bars, accident_density = get_cached_overpass(lat,lon)

    trend = []
    day = int(request.args.get("day", datetime.now().weekday()))
    is_weekend = 1 if day >= 5 else 0
    day_names = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]

    for hour in range(24):
        try:
            score, risk_level, reasons, action = calculate_risk(
                hour, is_weekend, rain, wind_speed,
                bars, accident_density, temperature  
            )
            predicted_severity, confidence = predict_severity(
                hour, is_weekend, temperature,
                rain, wind_speed, bars, accident_density
            )
            trend.append({
                "hour": hour,
                "hour_label": f"{hour:02d}:00",
                "risk_score": score,
                "risk_level": risk_level,
                "predicted_severity": predicted_severity
            })
            print(f"Hour {hour}: {score} {risk_level}")
        except Exception as e:
            print(f"Hour {hour} error: {e}")
            trend.append({
                "hour": hour,
                "hour_label": f"{hour:02d}:00",
                "risk_score": 0,
                "risk_level": "LOW",
                "predicted_severity": "unknown"
            })


    peak = max(trend, key=lambda x: x["risk_score"])
    safest = min(trend, key=lambda x: x["risk_score"])

    return jsonify({
        "location": {"lat": lat, "lon": lon},
        "day": day_names[day],
        "is_weekend": bool(is_weekend),
        "trend": trend,
        "peak_risk": {
            "hour": peak["hour"],
            "hour_label": peak["hour_label"],
            "risk_score": peak["risk_score"],
            "risk_level": peak["risk_level"]
        },
        "safest_time": {
            "hour": safest["hour"],
            "hour_label": safest["hour_label"],
            "risk_score": safest["risk_score"],
            "risk_level": safest["risk_level"]
        },
        "average_risk": round(sum(h["risk_score"] for h in trend) / 24, 1)
    })
        
@app.route("/hotspots", methods=["GET"])
def hotspots():
    data = get_crash_hotspots(top_k=10)

    return jsonify({
        "source": "crashes.csv (offline analysis)",
        "total_hotspots": len(data),
        "hotspots": data
    })


if __name__ == "__main__":
    app.run(debug=True)
