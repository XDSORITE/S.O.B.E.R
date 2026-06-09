import requests, time, random, math, joblib, os, numpy as np
from datetime import datetime

MODEL_PATH = os.path.join(os.path.dirname(__file__), "model.pkl")
try:
    severity_model = joblib.load(MODEL_PATH)
    print("ML model loaded successfully")
except Exception as e:
    severity_model = None
    print(f"Model load failed: {e}")

OVERPASS_ENDPOINTS = [
    "https://overpass-api.de/api/interpreter",
]

def get_overpass_url():
    return random.choice(OVERPASS_ENDPOINTS)

def get_time_features():
    now = datetime.now()
    hour = now.hour
    day_of_week = now.weekday()
    is_weekend = 1 if day_of_week >= 5 else 0
    return hour, day_of_week, is_weekend

def get_weather(lat, lon):
    try:
        url = (
            "https://api.open-meteo.com/v1/forecast"
            f"?latitude={lat}&longitude={lon}"
            "&current=temperature_2m,weather_code,wind_speed_10m"
        )
        response = requests.get(url, timeout=5)
        data = response.json()
        current = data["current"]
        temperature = current["temperature_2m"]
        weather_code = current["weather_code"]
        wind_speed = current["wind_speed_10m"]
        rain = 1 if weather_code in [51,53,55,61,63,65,80,81,82] else 0
        return temperature, rain, wind_speed
    except Exception as e:
        print(f"Weather error: {e}")
        return 20, 0, 0

def get_bars(lat, lon, radius=1000):
    cache_key = f"bars_{round(lat,3)}_{round(lon,3)}"
    url = get_overpass_url()
    query = f"""[out:json][timeout:25];
(
  node["amenity"="bar"](around:{radius},{lat},{lon});
  node["amenity"="pub"](around:{radius},{lat},{lon});
  node["amenity"="nightclub"](around:{radius},{lat},{lon});
  node["amenity"="lounge"](around:{radius},{lat},{lon});
);
out count;"""
    headers = {
        "Content-Type": "application/x-www-form-urlencoded",
        "Accept": "application/json",
        "User-Agent": "SOBER-Project/1.0"
    }
    for attempt in range(2):
        try:
            response = requests.post(url, data={"data": query}, headers=headers, timeout=30)
            data = response.json()
            count = int(data.get("elements", [{}])[0].get("tags", {}).get("total", 0))
            _overpass_cache[cache_key] = count
            return count
        except Exception as e:
            print(f"Bars error (attempt {attempt+1}): {e}")
            time.sleep(1)
    cached = _overpass_cache.get(cache_key)
    return cached if cached is not None else 0

def get_accident_density(lat, lon, radius=2000):
    cache_key = f"accidents_{round(lat,3)}_{round(lon,3)}"
    url = get_overpass_url()
    query = f"""[out:json][timeout:25];
(
  node["accident"](around:{radius},{lat},{lon});
  node["hazard"="accident_prone"](around:{radius},{lat},{lon});
  node["highway"="traffic_signals"]["accident_prone"](around:{radius},{lat},{lon});
  way["accident_prone"="yes"](around:{radius},{lat},{lon});
);
out count;"""
    headers = {
        "Content-Type": "application/x-www-form-urlencoded",
        "Accept": "application/json",
        "User-Agent": "SOBER-Project/1.0"
    }
    for attempt in range(2):
        try:
            response = requests.post(url, data={"data": query}, headers=headers, timeout=30)
            data = response.json()
            count = int(data.get("elements", [{}])[0].get("tags", {}).get("total", 0))
            _overpass_cache[cache_key] = count
            return count
        except Exception as e:
            print(f"Accident density error (attempt {attempt+1}): {e}")
            time.sleep(1)
    cached = _overpass_cache.get(cache_key)
    return cached if cached is not None else 0

def get_cached_overpass(lat,lon):
    key = (round(lat,2), round(lon,2))
    if key in _overpass_cache:
        print(f"Cache hit for {key}")
        return _overpass_cache[key]
    bars = get_bars(lat,lon, radius = 1000)
    accident_density = get_accident_density(lat, lon, radius=2000)
    _overpass_cache[key] = (bars, accident_density)
    return bars, accident_density

_overpass_cache = {}

def build_features(lat, lon):
    hour, day_of_week, is_weekend = get_time_features()
    temperature, rain, wind_speed = get_weather(lat, lon)
    bars = get_bars(lat, lon)
    accident_density = get_accident_density(lat, lon)
    return {
        "hour": hour,
        "day_of_week": day_of_week,
        "is_weekend": is_weekend,
        "latitude": lat,
        "longitude": lon,
        "temperature": temperature,
        "rain": rain,
        "wind_speed": wind_speed,
        "bars": bars,
        "accident_density": accident_density
    }

def predict_severity(hour, is_weekend, temperature, rain, wind_speed, bars, accident_density):
    """ML severity prediction - runs alongside rule-based score"""
    if severity_model is None:
        return "unknown", 0.0
    
    features = np.array([[hour, is_weekend, temperature, rain, wind_speed, bars, accident_density]])
    proba = severity_model.predict_proba(features)[0]
    predicted_class = int(np.argmax(proba))
    confidence = round(float(np.max(proba)), 2)

    severity_map = {
        0: "property_damage_only",
        1: "injury_likely",
        2: "fatal_risk"
    }
    return severity_map[predicted_class], confidence












def calculate_risk(hour, is_weekend, rain, wind_speed, bars, accident_density, temperature):
    hour = hour or 0
    is_weekend = is_weekend or 0
    rain = rain or 0
    wind_speed = wind_speed or 0
    bars = bars or 0
    accident_density = accident_density or 0
    temperature = temperature or 0
    risk = 0
    reasons = []

    if hour >= 22 or hour <= 5:
        risk += 30
        reasons.append("Night-time driving (high DUI window)")
    elif 17 <= hour <= 19:
        risk += 10
        reasons.append("Rush hour traffic (increased congestion)")
    if is_weekend:
        risk += 10
        reasons.append("Weekend (elevated DUI risk)")

    if rain:
        risk += 15
        reasons.append("Rain detected (reduced visibility and traction)")
    if wind_speed > 20:
        risk += 10
        reasons.append(f"High wind speed ({wind_speed} km/h)")

    if temperature >= 38:
        risk += 15
        reasons.append(f"Extreme heat ({temperature}°C)")
    elif temperature >= 32:
        risk += 8
        reasons.append(f"High temperature ({temperature}°C)")

    if bars <= 0:
        pass
    elif bars <= 5:
        risk += 5
        reasons.append(f"Low nightlife density ({bars} venues)")
    elif bars <= 20:
        risk += 20
        reasons.append(f"Moderate nightlife density ({bars} venues)")
    else:
        risk += 35
        reasons.append(f"High nightlife density ({bars} venues)")

    if accident_density <= 0:
        pass
    elif accident_density <= 10:
        risk += 10
        reasons.append(f"Low accident history ({accident_density} incidents)")
    elif accident_density <= 50:
        risk += 20
        reasons.append(f"Moderate accident history ({accident_density} incidents)")
    else:
        risk += 30
        reasons.append(f"High accident history ({accident_density} incidents)")

    risk = min(risk, 100)

    if risk >= 75:
        risk_level = "CRITICAL"
        action = "Avoid driving if possible. Consider alternative transportation."
    elif risk >= 50:
        risk_level = "HIGH"
        action = "Drive with extreme caution. Avoid high-risk areas."
    elif risk >= 25:
        risk_level = "MEDIUM"
        action = "Drive with caution and stay alert."
    else:
        risk_level = "LOW"
        action = "Normal driving conditions. Drive safely."

    if not reasons:
        reasons.append("No significant risk factors detected.")

    return risk, risk_level, reasons, action

def get_routes(origin_lat, origin_lon, dest_lat, dest_lon):
    url = (
        f"http://router.project-osrm.org/route/v1/driving/"
        f"{origin_lon},{origin_lat};{dest_lon},{dest_lat}"
        f"?alternatives=3&geometries=geojson&overview=full"
    )
    try:
        response = requests.get(url, timeout=10)
        data = response.json()
        if data.get("code") != "Ok":
            return []
        return data.get("routes", [])
    except Exception as e:
        print(f"OSRM error: {e}")
        return []

def sample_waypoints(geometry, num_points=6):
    coords = geometry.get("coordinates", [])
    if not coords:
        return []
    total = len(coords)
    if total <= num_points:
        return [{"lat": c[1], "lon": c[0]} for c in coords]
    step = total // num_points
    sampled = [coords[i] for i in range(0, total, step)][:num_points]
    return [{"lat": c[1], "lon": c[0]} for c in sampled]

