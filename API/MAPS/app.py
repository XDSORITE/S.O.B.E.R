from flask import Flask, request, jsonify
from flask_cors import CORS
from main import build_features, calculate_risk, predict_severity, get_routes, sample_waypoints, get_bars, get_accident_density, get_weather, get_time_features, get_cached_overpass
import concurrent.futures, time

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
    routes = get_routes(origin_lat, origin_lon, dest_lat, dest_lon)
    
    if not routes:
        return jsonify({"error": "No routes found"}),500
    
    def score_route(route):
        waypoints = sample_waypoints(route["geometry"])
        first = waypoints[0]
        bars = get_bars(first["lat"], first["lon"], radius=1000)
        accident_density = get_accident_density(first["lat"], first["lon"], radius=2000)

        def score_point(wp):
            hour, day_of_week, is_weekend = get_time_features()
            temperature, rain, wind_speed = get_weather(wp["lat"], wp["lon"])
            
            score, level, reasons, action = calculate_risk(
                hour,
                is_weekend,
                rain,
                wind_speed,
                bars,
                accident_density,
                temperature
            )
            return {
                "lat": wp["lat"],
                "lon": wp["lon"],
                "risk_score": score,
                "risk_level": level,
            }
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
            scored_waypoints = list(executor.map(score_point, waypoints))

        avg_risk = round(sum(w["risk_score"] for w in scored_waypoints)/len(scored_waypoints))

        if avg_risk >=75:
            risk_level = "CRITICAL"
        elif avg_risk >=50:
            risk_level = "HIGH"
        elif avg_risk >=25:
            risk_level = "MEDIUM"
        else:
            risk_level = "LOW"

        return {
            "average_risk": avg_risk,
            "risk_level": risk_level,
            "distance_km": round(route["distance"]/1000,2),
            "duration_min": round(route["duration"]/60,1),
            "waypoints": scored_waypoints,
            "geometry": [[c[1], c[0]] for c in route ["geometry"]["coordinates"]]
        }
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
        scored_routes = list(executor.map(score_route, routes))
    
    scored_routes.sort(key=lambda r: r["average_risk"])

    for i, r in enumerate(scored_routes):
        r["rank"] = i+1

    return jsonify({
        "origin": {"lat": origin_lat, "lon": origin_lon},
        "destination": {"lat": dest_lat, "lon": dest_lon},
        "recommended_route": 0,
        "routes": scored_routes
    })

if __name__ == "__main__":
    app.run(debug=True)
