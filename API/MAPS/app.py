from flask import Flask, request,jsonify
from main import build_features, calculate_risk, get_routes, sample_waypoints, get_bars, get_accident_density, get_weather, get_time_features
import concurrent.futures, time

app= Flask(__name__)

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

    return jsonify({
        "risk_score":score,
        "risk_level":risk_level,
        "reasons": reasons,
        "action": action,
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

@app.route("/test_overpass")
def test_overpass():
    import requests
    results = {}
    endpoints = [
        "https://overpass-api.de/api/interpreter",
        "https://overpass.kumi.systems/api/interpreter",
        "https://maps.mail.ru/osm/tools/overpass/api/interpreter",
    ]
    query = "[out:json];node[amenity=bar](around:500,40.758,-73.985);out count;"
    headers = {
        "Content-Type": "application/x-www-form-urlencoded",
        "Accept": "application/json",
        "User-Agent": "SOBER-Project/1.0"
    }
    for ep in endpoints:
        try:
            r = requests.post(ep, data={"data": query}, headers=headers, timeout=10)
            results[ep] = f"Status {r.status_code} — {r.text[:100]}"
        except Exception as e:
            results[ep] = f"ERROR: {str(e)[:100]}"
    return jsonify(results)

if __name__ == "__main__":
    app.run(debug=True)
