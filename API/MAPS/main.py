import requests
from datetime import datetime

def get_time_features():
    now=datetime.now()
    hour=now.hour
    day_of_week=now.weekday()
    is_weekend=1 if day_of_week>=5 else 0

    return hour, day_of_week, is_weekend

def get_weather(lat,lon):
    url = (
         "https://api.open-meteo.com/v1/forecast"
        f"?latitude={lat}&longitude={lon}"
        "&current=temperature_2m,weather_code,wind_speed_10m"
    )

    response=requests.get(url)
    data=response.json()
    current=data["current"]
    temperature=current["temperature_2m"]
    weather_code=current["weather_code"]
    wind_speed=current["wind_speed_10m"]

    rain =1 if weather_code in [51,53,55,61,63,65,80,81,82] else 0

    return temperature, rain, wind_speed  

def get_bars(lat,lon, radius=3000):
    url = "https://overpass-api.de/api/interpreter"

    query = f"""
    [out:json];
    (
    node["amenity"="bar"](around:{radius},{lat},{lon});
    node["amenity"="pub"](around:{radius},{lat},{lon});
    node["amenity"="nightclub"](around:{radius},{lat},{lon});
    );
    out;
    """
    headers = {
        "User-Agent": "SOBER-Project/1.0 (contact: your-email@example.com)",
        "Content-Type": "text/plain",
    }

    try:
        response = requests.post(url,data=query.encode("utf-8"), headers=headers)

        data = response.json()
        return len(data.get("elements",[]))
    except Exception as e:
        print("An error occurred:", e)
        return 0
    

def build_features(lat,lon):
    hour,day_of_week,is_weekend = get_time_features()
    temperature,rain,wind_speed = get_weather(lat,lon)
    bars=get_bars(lat,lon)

    features = {
        "hour":hour,
        "day_of_week": day_of_week,
        "is_weekend": is_weekend,
        "latitude": lat,
        "longitude": lon,
        "temperature": temperature,
        "rain": rain,
        "wind_speed": wind_speed,
        "bars":bars
    }

    return features  
    
def calculate_risk(hour, is_weekend,rain,wind_speed,bars):
    risk=0

    if hour >=22 or hour <=5:
        risk += 30
    if is_weekend:
        risk +=10

    if rain:
        risk +=15
    if wind_speed>20:
        risk +=10

    if bars <=5:
        risk +=5
    elif bars <=20:
        risk +=20
    else:
        risk +=35
    
    if risk>100:
        risk=100

    return risk


