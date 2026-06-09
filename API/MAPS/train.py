import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report
import joblib
import requests
import time

def get_historical_weather(lat, lon, date, hour):
    """Get historical weather for a specific location and time"""
    try:
        url = (
            f"https://archive-api.open-meteo.com/v1/archive"
            f"?latitude={lat}&longitude={lon}"
            f"&start_date={date}&end_date={date}"
            f"&hourly=temperature_2m,weather_code,wind_speed_10m"
        )
        response = requests.get(url, timeout=5)
        data = response.json()
        hourly = data.get("hourly",{})
        temperature = hourly.get("temperature_2m", [20])[hour]
        weather_code = hourly.get("weather_code", [0])[hour]
        wind_speed = hourly.get("wind_speed_10m", [0])[hour]
        rain =1 if weather_code in [51,53,55,61,63,65,80,81,82] else 0
        return temperature, rain, wind_speed
    except Exception as e:
        return 20, 0, 0
    
def build_training_data():
    print("Loading crash data...")
    df = pd.read_csv("crashes.csv")

    df["crash_date"] = pd.to_datetime(df["crash_date"])
    df["hour"] = pd.to_datetime(df["crash_time"], format="%H:%M", errors="coerce").dt.hour
    df["day_of_week"] = df["crash_date"].dt.dayofweek
    df["is_weekend"] = (df["day_of_week"] >= 5).astype(int)
    df["date_str"] = df["crash_date"].dt.strftime("%Y-%m-%d")
    df["latitude"] = pd.to_numeric(df["latitude"], errors="coerce")
    df["longitude"] = pd.to_numeric(df["longitude"], errors="coerce")
    df = df.dropna(subset=["latitude", "longitude" ,"hour"])

    df["crashed"] = 1

    crashes = df.sample(n=min(5000, len(df)), random_state=42).reset_index(drop=True)
    print(f"Using {len(crashes)} crash records")

    print("Generating non-crash scenarios...")
    non_crashes=[]
    for _ in range(len(crashes)):
        non_crashes.append({
            "hour": np.random.randint(0,24),
            "is_weekend": np.random.randint(0,2),
            "temperature": np.random.uniform(0,40),
            "rain": np.random.choice([0,1], p=[0.85, 0.15]),
            "wind_speed": np.random.uniform(0,50),
            "bars": np.random.randint(0,200),
            "accident_density": np.random.randint(0,300),
            "crashed": 0
        })
    non_crash_df = pd.DataFrame(non_crashes)

    print("Fetching historical weather for cashes (this takes a few minutes)...")
    temperatures, rains, wind_speeds = [], [], []
    for i, row in crashes.iterrows():
        if i % 100 == 0:
            print(f" Weather: {i}/{len(crashes)}")
        temp, rain, wind = get_historical_weather(
            row["latitude"], row["longitude"], 
            row["date_str"], int(row["hour"])
        )
        temperatures.append(temp)
        rains.append(rain)
        wind_speeds.append(wind)
        time.sleep(0.05)
    
    crashes = crashes.copy()
    crashes["temperature"] = temperatures
    crashes["rain"] = rains
    crashes["wind_speed"] = wind_speeds

    crashes["bars"] = np.random.randint(0,200, size=len(crashes))
    crashes["accident_density"] = np.random.randint(0,300, size=len(crashes))
    crashes.to_csv("crashes_with_weather.csv", index=False)  #
    print("Weather data saved to crashes_with_weather.csv")
    crash_features = crashes[["hour", "is_weekend", "temperature", "rain", "wind_speed", "bars", "accident_density", "crashed"]].copy()
    full_df = pd.concat([crash_features, non_crash_df], ignore_index=True)
    full_df.to_csv("training_data.csv", index=False)
    print(f"Training data saved - {len(full_df)} rows")
    return full_df

def train_model(df):
    print("\nTraining Random Forest model...")
    features = ["hour", "is_weekend", "temperature", "rain", "wind_speed", "bars", "accident_density"]
    X = df[features]
    y = df["crashed"]
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    model = RandomForestClassifier(
        n_estimators=100, 
        max_depth=10,
        random_state=42,
        n_jobs=-1
    )
    model.fit(X_train, y_train)

    print("\nModel Performance:")
    y_pred = model.predict(X_test)
    print(classification_report(y_test, y_pred))

    print("\nFeature Importance:")
    for feat, imp in sorted(zip(features, model.feature_importances_), key=lambda x: x[1], reverse=True):
        print(f"{feat}:{imp:.3f}")

    joblib.dump(model, "model.pkl")
    print("\nModel saved as model.pkl")
    return model

if __name__ == "__main__":
    df = build_training_data()
    model = train_model(df)

