from flask import Flask, request,jsonify
from main import build_features, calculate_risk

app= Flask(__name__)

@app.route("/risk", methods=["GET"])
def risk():
    lat = float(request.args.get("lat"))
    lon = float(request.args.get("lon"))

    features = build_features(lat,lon)

    score = calculate_risk(
        features["hour"],
        features["is_weekend"],
        features["rain"],
        features["wind_speed"],
        features["bars"]
    )

    return jsonify({
        "risk_score":score,
        "features":features
    })

if __name__ == "__main__":
    app.run(debug=True)

