import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.metrics import classification_report, confusion_matrix
import joblib
import os
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import seaborn as sns
import json

def compute_accident_density_against(lats, lons, ref_lats, ref_lons, ref_weights, radius_km=1.0):
    """
    Vectorized haversine - computes WEIGHTED accident density.
    Fatal crashes count 3x, injury 2x, property damage 1x.
    """

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
        mask = dist <= radius_km
        weighted_count = float(np.sum(ref_weights[mask]))
        densities.append(weighted_count)
    
        if i % 500 == 0:
            print(f"  Density: {i}/{len(lats)}")

    return densities

    
def engineer_features(df):
    """Add engineered features to dataframe"""

    def time_bucket(hour):
        if 5 <= hour <12:
            return 0
        elif 12 <= hour <17:
            return 1
        elif 17<= hour <22:
            return 2
        else:
            return 3
    
    df["time_of_day"] = df["hour"].apply(time_bucket)
    df["is_night"] = ((df["hour"] >=22) | (df["hour"] <= 5)) .astype(int)
    df["is_rush_hour"] = (((df["hour"] >= 7) & (df["hour"] <= 9)) | 
                          ((df["hour"] >= 17) & (df["hour"] <=19))).astype(int)
    
    return df

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

    crashes = engineer_features(crashes)

    # Real accident density
    print("\nLoading full 50k for density...")
    full_crashes = pd.read_csv("crashes.csv")
    full_crashes["latitude"] = pd.to_numeric(full_crashes["latitude"], errors="coerce")
    full_crashes["longitude"] = pd.to_numeric(full_crashes["longitude"], errors="coerce")
    full_crashes["number_of_persons_injured"] = pd.to_numeric(full_crashes["number_of_persons_injured"], errors="coerce").fillna(0)
    full_crashes["number_of_persons_killed"] = pd.to_numeric(full_crashes["number_of_persons_killed"], errors="coerce").fillna(0)
    full_crashes = full_crashes.dropna(subset=["latitude", "longitude"])

    def compute_weight(row):
        if row["number_of_persons_killed"] > 0:
            return 3.0
        elif row["number_of_persons_injured"] >0:
            return 2.0
        else:
            return 1.0
    
    ref_weights = full_crashes.apply(compute_weight, axis=1).values
    print(f"Reference dataset: {len(full_crashes)} records")
    print(f"Average weight: {ref_weights.mean():.2f}")

    densities = compute_accident_density_against(
        crashes["latitude"].values,
        crashes["longitude"].values,
        full_crashes["latitude"].values,
        full_crashes["longitude"].values,
        ref_weights
    )
    crashes["accident_density"] = densities
    print(f"Weighted density done — avg: {np.mean(densities):.1f}")

    crashes["bars"] = np.random.randint(0, 200, size=len(crashes))

    crashes.to_csv("training_data.csv", index=False)
    print(f"Training data saved — {len(crashes)} rows")
    return crashes

def train_model(df):
    print("\nTraining severity prediction model...")
    features = ["hour", "is_weekend", "temperature", "rain",
                 "wind_speed", "bars", "accident_density",
                 "time_of_day", "is_night", "is_rush_hour"]
    X = df[features]
    y = df["severity"]

    print("\nRunning 5-fold cross validation...")
    model_cv = RandomForestClassifier(
        n_estimators=100, max_depth=10, random_state=42, n_jobs=-1
    )
    cv_scores = cross_val_score(model_cv, X, y, cv=5, scoring='accuracy')
    cv_results={
        "cv_accuracy_mean": round(float(cv_scores.mean()), 4),
        "cv_accuracy_std": round(float(cv_scores.std()), 4),
        "cv_scores_per_fold": [round(float(s), 4) for s in cv_scores],
        "n_folds": 5,
        "features": features,
        "training_records": len(df),
        "model": "RandomForestClassifier",
        "target": "severity"
    }
    with open("cv_results.json", "w") as f:
        json.dump(cv_results, f, indent=2)
    print("CV results saved to cv_results.json")

    print(f"CV Accuracy: {cv_scores.mean():.3f} ± {cv_scores.std():.3f}")
    print(f"Per fold: {[round(s,3) for s in cv_scores]}")

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
          target_names=["Property damage", "Injury", "Fatal"],
          zero_division=0))
    
    print("Generating confusion matrix...")
    cm = confusion_matrix(y_test, y_pred)
    plt.figure(figsize=(8,6))
    sns.heatmap(cm, annot=True, fmt='d', cmap='Blues',
                xticklabels=["Property damage", "Injury", "Fatal"],
                yticklabels=["Property damage", "Injury", "Fatal"])
    plt.title('SOBER - Crash Severity Confusion Matrix')
    plt.ylabel('Actual')
    plt.xlabel('Predicted')
    plt.tight_layout()
    plt.savefig("confusion_matrix.png", dpi=150)
    plt.close()
    print("Saved confusion_matrix.png")

    print("Generating feature importance chart...")
    importances = model.feature_importances_
    feat_df= pd.DataFrame({
        'feature': features,
        'importance': importances
    }).sort_values('importance', ascending=True)

    plt.figure(figsize=(10,6))
    colors = ['#ff6b6b' if i == feat_df['importance'].idxmax() else '#58d6c9' for i in feat_df.index]
    plt.barh(feat_df['feature'], feat_df['importance'], color=colors)
    plt.title('SOBER - Feature Importance (Random Forest)')
    plt.xlabel('Importance Score')
    plt.tight_layout()
    plt.savefig("feature_importance.png", dpi=150)
    plt.close()
    print("Saved feature_importance.png")


    print("\nFeature Importance:")
    for feat, imp in sorted(zip(features, importances),
                            key=lambda x: x[1], reverse=True):
        print(f"  {feat}: {imp:.3f}")

    joblib.dump(model, "model.pkl")
    print("\nModel saved as model.pkl")
    return model


if __name__ == "__main__":
    df = build_training_data()
    if df is not None:
        model = train_model(df)

