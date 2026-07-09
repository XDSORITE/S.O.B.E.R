import requests, time, random, math, joblib, os, numpy as np, sqlite3
from datetime import datetime
import pandas as pd
import threading
from functools import lru_cache

active_alerts = []
alert_lock = threading.Lock()
routes_lock = threading.Lock()
active_routes = {}
ROUTE_CACHE_EXPIRY = 300
DB_PATH = os.path.join(os.path.dirname(__file__), "sober.db")

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

def get_engineered_time_features(hour):
    if 5 <= hour < 12:
        time_of_day = 0
    elif 12 <= hour < 17:
        time_of_day = 1
    elif 17 <= hour < 22:
        time_of_day = 2
    else:
        time_of_day = 3

    is_night = 1 if (hour >= 22 or hour <= 5) else 0
    is_rush_hour = 1 if ((7 <= hour <= 9) or (17 <= hour <= 19)) else 0
    return time_of_day, is_night, is_rush_hour

weather_cache = {}
def get_weather(lat, lon):
    try:
        key = f"{lat},{lon}"
        if key in weather_cache:
            if time.time() - weather_cache[key]["time"] < 600:
                return weather_cache[key]["data"]
        url = (
            "https://api.open-meteo.com/v1/forecast"
            f"?latitude={lat}&longitude={lon}"
            "&current=temperature_2m,weather_code,wind_speed_10m"
        )
        response = requests.get(url, timeout=10)
        data = response.json()
        if "current" not in data:
            print("Weather failed:", data)
            return 20, 0, 0
        
        current = data["current"]

        result = (
            current["temperature_2m"],
            1 if current["weather_code"] in [51,53,55,61,63,65,80,81,82] else 0,
            current["wind_speed_10m"]
        )

        weather_cache[key] = {
            "time": time.time(),
            "data": result
        }

        return result

    except Exception as e:
        print("Weather error:", e)
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
    time_of_day, is_night, is_rush_hour = get_engineered_time_features(hour)
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
        "accident_density": accident_density,
        "time_of_day": time_of_day,
        "is_night": is_night,
        "is_rush_hour": is_rush_hour
    }

def predict_severity(hour, is_weekend, temperature, rain, wind_speed, bars, accident_density):
    if severity_model is None:
        return "unknown", 0.0
    
    def time_bucket(h):
        if 5 <= h <12: return 0
        elif 12 <= h <17: return 1
        elif 17 <h < 22: return 2
        else: return 3
    
    time_of_day = time_bucket(hour)
    is_night = 1 if (hour >= 22 or hour <= 5) else 0
    is_rush_hour = 1 if (7 <= hour <= 9 or 17 <= hour <=19) else 0

    features = pd.DataFrame([[
        hour, is_weekend, temperature, rain, wind_speed, bars,
        accident_density, time_of_day, is_night, is_rush_hour
    ]], columns=[
        "hour", "is_weekend", "temperature", "rain", "wind_speed", "bars",
        "accident_density", "time_of_day", "is_night", "is_rush_hour"
    ])

    proba = severity_model.predict_proba(features)[0]
    predicted_class = int(np.argmax(proba))
    confidence = round(float(np.max(proba)), 2)

    severity_map = {0: "property_damage_only", 1: "injury_likely", 2: "fatal_risk"}
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


def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS risk_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            endpoint TEXT,
            latitude REAL,
            longitude REAL,
            hour INTEGER,
            is_weekend INTEGER,
            risk_score INTEGER,
            risk_level TEXT,
            bars INTEGER,
            accident_density INTEGER,
            temperature REAL,
            rain INTEGER,
            wind_speed REAL
        )
    ''')
    c.execute('''
        CREATE TABLE IF NOT EXISTS route_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            origin_lat REAL,
            origin_lon REAL,
            dest_lat REAL,
            dest_lon REAL,
            routes_returned INTEGER,
            recommended_risk_score INTEGER,
            recommended_risk_level TEXT,
            distance_km REAL,
            duration_min REAL
        )
    ''')
    conn.commit()
    conn.close()
    print("Database initialized")

def log_risk(endpoint, lat, lon, hour, is_weekend, risk_score, risk_level, bars, accident_density, temperature, rain, wind_speed):
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute('''
            INSERT INTO risk_logs (endpoint, latitude, longitude, hour, is_weekend, risk_score, risk_level, bars, accident_density, temperature, rain, wind_speed)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (endpoint, lat, lon, hour, is_weekend, risk_score, risk_level, bars, accident_density, temperature, rain, wind_speed))
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"DB log error: {e}")

def log_route(origin_lat, origin_lon, dest_lat, dest_lon, routes_returned, recommended_risk_score, recommended_risk_level, distance_km, duration_min):
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute('''
            INSERT INTO route_logs(origin_lat, origin_lon, dest_lat, dest_lon, routes_returned, recommended_risk_score, recommended_risk_level, distance_km, duration_min)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (origin_lat, origin_lon, dest_lat, dest_lon, routes_returned, recommended_risk_score, recommended_risk_level, distance_km, duration_min))
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"DB route log error: {e}")

def check_weather_alerts(locations=None):
    """"
    Poll weather for a set of monitored locations.
    If conditions change significantly, add an alert.
    """

    if locations is None:
        locations = [
            {"name": "Times Square", "lat": 40.7580, "lon": -73.9855},
            {"name": "Downtown Dubai", "lat": 25.2048, "lon": 55.2708},
            {"name": "JFK Airport", "lat": 40.6413, "lon": -73.7781},
        ]
    
    new_alerts = []
    for loc in locations:
        try:
            temperature, rain, wind_speed = get_weather(loc["lat"], loc["lon"])
            alerts_for_loc = []

            if rain:
                alerts_for_loc.append({
                    "type":"RAIN",
                    "severity":"HIGH",
                    "message": f"Rain detected at  {loc['name']} - reduced visiblity, increased crash risk"
                })
            if wind_speed > 30:
                alerts_for_loc.append({
                    "type":"HIGH_WIND",
                    "severity":"HIGH",
                    "message": f"High winds ({wind_speed} km/h) at {loc['name']} - dangerous driving conditions"
                })
            elif wind_speed > 20:
                alerts_for_loc.append({
                    "type":"MODERATE_WIND",
                    "severity": "MEDIUM",
                    "message": f"Moderate winds ({wind_speed} km/h) at {loc['name']} - drive with caution"
                })
            if temperature >=38:
                alerts_for_loc.append({
                    "type": "EXTREME_HEAT",
                    "severity": "HIGH",
                    "message": f"Extreme heat ({temperature}°C) at {loc['name']} - risk of tyre blowouts and driver fatigue"
                })
            if rain and wind_speed > 20:
                alerts_for_loc.append({
                    "type": "SEVER_CONDITIONS",
                    "severity": "CRITICAL",
                    "message": f"Combined rain + high wind at {loc['name']} - avoid driving if possible"
                })
            
            for alert in alerts_for_loc:
                alert["location"] = loc["name"]
                alert["lat"] = loc["lat"]
                alert["lon"] = loc["lon"]
                alert["temperature"] = temperature
                alert["wind_speed"] = wind_speed
                alert["rain"] = bool(rain)
                alert["timestamp"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                new_alerts.append(alert)

            print(f"Alert check: {loc['name']} - {len(alerts_for_loc)} alerts")

        except Exception as e:
            print(f"Alert check error for {loc['name']}: {e}")
    
    with alert_lock:
        active_alerts.clear()
        active_alerts.extend(new_alerts)

    print(f"Alert system updated - {len(new_alerts)} active alerts")
    return new_alerts

def start_alert_poller(interval_minutes=30):
    """Runs weather alert check every interval_minutes in background"""
    def poller():
        while True:
            print("Running scheduled weather alert check...")
            check_weather_alerts()
            time.sleep(interval_minutes * 60)
        
    thread = threading.Thread(target=poller, daemon=True)
    thread.start()
    print(f"Alert poller started - checking every {interval_minutes} minutes")

def get_crash_hotspots(top_k=10):
    df = pd.read_csv("crashes.csv")
    df["latitude"] = pd.to_numeric(df["latitude"], errors="coerce")
    df["longitude"] = pd.to_numeric(df["longitude"], errors="coerce")

    df = df.dropna(subset=["latitude", "longitude"])
    df = df[(df["latitude"] != 0) & (df["longitude"] != 0)] 
    df = df[(df["latitude"].between(40.4, 41.0)) & (df["longitude"].between(-74.5, -73.5))]

    df["lat_r"] = df["latitude"].round(3)
    df["lon_r"] = df["longitude"].round(3)

    hotspots = df.groupby(["lat_r", "lon_r"]).size().reset_index(name="crash_count")
    hotspots = hotspots.sort_values("crash_count", ascending=False).head(top_k)
    hotspots = hotspots.reset_index(drop=True)

    return [
        {
            "rank": i+1,
            "lat": row["lat_r"],
            "lon": row["lon_r"],
            "crash_count": int(row["crash_count"]),
            "risk_level": "CRITICAL" if row["crash_count"] > 50 else
                          "HIGH" if row["crash_count"] >20 else
                          "MEDIUM"
        }
        for i, row in hotspots.iterrows()
    ]

def get_cached_route(route_id):
    with routes_lock:
        if route_id in active_routes:
            cached = active_routes[route_id]
            if time.time() - cached["last_updated"] < ROUTE_CACHE_EXPIRY:
                print(f"Route cache hit: {route_id}")
                return cached
            else:
                del active_routes[route_id]
    return None

def cache_route(route_id, data):
    with routes_lock:
        active_routes[route_id] = data

        expired = [k for k, v in active_routes.items()
                   if time.time() - v["last_updated"] > ROUTE_CACHE_EXPIRY]
        for k in expired:
            del active_routes[k]
    
def get_nearest_safe(lat, lon, radius=3000):
    """
    Find nearest safe stops - parking, police, hospitals within radius
    """

    url = get_overpass_url()
    query = f"""[out:json][timeout:25];
(
    node["amenity"="parking"](around:{radius},{lat},{lon});
    node["amenity"="police"](around:{radius},{lat},{lon});
    node["amenity"="hospital"](around:{radius},{lat},{lon});
    node["amenity"="clinic"](around:{radius},{lat},{lon});
    node["highway"="rest_area"](around:{radius},{lat},{lon});
);
out body;"""
    
    headers = {
        "Content-Type": "application/x-www-form-urlencoded",
        "Accept": "application/json",
        "User-Agent": "SOBER-Project/1.0"
    }

    for attempt in range(2):
        try:
            response = requests.post(
                url, data={"data":query},
                headers=headers, timeout=30
            )
            data = response.json()
            elements = data.get("elements", [])
            safe_stops = []
            for el in elements:
                el_lat = el.get("lat")
                el_lon = el.get("lon")
                if not el_lat or not el_lon:
                    continue

                R = 6371000
                dlat = math.radians(el_lat - lat)
                dlon = math.radians(el_lon - lon)
                a = math.sin(dlat/2)**2 + math.cos(math.radians(lat)) * math.cos(math.radians(el_lat)) * math.sin(dlon/2)**2
                distance_m = 2 * R * math.asin(math.sqrt(a))

                tags = el.get("tags", {})
                amenity = tags.get("amenity", "unknown")
                name = tags.get("name", amenity.replace("_", "").title())

                safety_priority = {
                    "police": 1,
                    "hospital": 2,
                    "clinic": 3,
                    "rest_area": 4,
                    "parking": 5
                }.get(amenity,6)

                safe_stops.append({
                    "name": name,
                    "type": amenity,
                    "lat": el_lat,
                    "lon": el_lon,
                    "distance_m": round(distance_m),
                    "distance_km": round(distance_m / 1000, 2),
                    "safety_priority": safety_priority
                })
            
            safe_stops.sort(key=lambda x: (x["safety_priority"], x["distance_m"]))
            return safe_stops[:10]
        except Exception as e:
            print(f"Nearest safe stop error (attempt {attempt+1}): {e}")
            time.sleep(1)
    return []

def validate_coordinates(lat,lon):
    """Returns (True, None) if valid, (False, error_message) if invalid"""
    try:
        lat = float(lat)
        lon = float(lon)
    except (TypeError, ValueError):
        return False, "Coordinates must be numbers"
    
    if not (-90 <= lat <= 90):
        return False, f"Latitude must be between -90 and 90, got {lat}"
    if not (-180 <= lon <= 180):
        return False, f"Longitude must be between -180 and 180, got {lon}"
    if lat == 0 and lon == 0:
        return False, "Coordinates (0,0) are invalid - that's the middle of the ocean"
    
    return True, None
