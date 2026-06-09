import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report
import joblib
import os

def compute_accident_density_against(lats, lons, ref_lats, ref_lons, radius_km=1.0):
    print("Computing real accident density against 50k records...")
    R = 6371
    lats_r = np.radians(lats)
    lons_r = np.radians(lons)
    ref_lats_r = np.radians(ref_lats)
    ref_lons_r = np.radians(ref_lons)
    densities = []

    for i in range(len(lats)):
        dlat = ref_lats_r - lats_r[i]
        dlon = ref_lons_r - lons_r[i]
        a = np.sin(dlat/2)**2 + np.cos(lats_r[i]) * np.cos(ref_lats_r) * np.sin(dlon/2)**2
        dist = 2 * R * np.arcsin(np.sqrt(a))
        count = int(np.sum(dist <= radius_km))
        densities.append(count)
        if i % 500 == 0:
            print(f"  Density: {i}/{len(lats)}")

    return densities

def build_training_data():
    print("Loading crash data with weather...")

    if not os.path.exists("crashes_with_weather.csv"):
        print("crashes_with_weather.csv not found")
        return None

    crashes = pd.read_csv("crashes_with_weather.csv")
    print(f"Loaded {len(crashes)} records")

    # Build severity label from real data
    crashes["number_of_persons_injured"] = pd.to_numeric(
        crashes["number_of_persons_injured"], errors="coerce").fillna(0)
    crashes["number_of_persons_killed"] = pd.to_numeric(
        crashes["number_of_persons_killed"], errors="coerce").fillna(0)

    def label_severity(row):
        if row["number_of_persons_killed"] > 0:
            return 2  # fatal
        elif row["number_of_persons_injured"] > 0:
            return 1  # injury
        else:
            return 0  # property damage only

    crashes["severity"] = crashes.apply(label_severity, axis=1)

    print("\nSeverity distribution:")
    print(crashes["severity"].value_counts())

    crashes["hour"] = crashes["hour"].fillna(0).astype(int)
    crashes["is_weekend"] = crashes["is_weekend"].fillna(0).astype(int)

    # Real accident density
    print("\nLoading full 50k for density...")
    full_crashes = pd.read_csv("crashes.csv")
    full_crashes["latitude"] = pd.to_numeric(full_crashes["latitude"], errors="coerce")
    full_crashes["longitude"] = pd.to_numeric(full_crashes["longitude"], errors="coerce")
    full_crashes = full_crashes.dropna(subset=["latitude", "longitude"])

    densities = compute_accident_density_against(
        crashes["latitude"].values,
        crashes["longitude"].values,
        full_crashes["latitude"].values,
        full_crashes["longitude"].values
    )
    crashes["accident_density"] = densities
    print(f"Density done — avg: {np.mean(densities):.1f}")

    crashes["bars"] = np.random.randint(0, 200, size=len(crashes))

    crashes.to_csv("training_data.csv", index=False)
    print(f"Training data saved — {len(crashes)} rows")
    return crashes

def train_model(df):
    print("\nTraining severity prediction model...")
    features = ["hour", "is_weekend", "temperature", "rain",
                 "wind_speed", "bars", "accident_density"]
    X = df[features]
    y = df["severity"]

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42
    )

    model = RandomForestClassifier(
        n_estimators=100,
        max_depth=10,
        random_state=42,
        n_jobs=-1
    )
    model.fit(X_train, y_train)

    print("\nModel Performance:")
    y_pred = model.predict(X_test)
    print(classification_report(y_test, y_pred, 
          target_names=["Property damage", "Injury", "Fatal"]))

    print("\nFeature Importance:")
    for feat, imp in sorted(zip(features, model.feature_importances_),
                            key=lambda x: x[1], reverse=True):
        print(f"  {feat}: {imp:.3f}")

    joblib.dump(model, "model.pkl")
    print("\nModel saved as model.pkl")
    return model

if __name__ == "__main__":
    df = build_training_data()
    if df is not None:
        model = train_model(df)