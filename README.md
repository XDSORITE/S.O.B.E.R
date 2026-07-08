# S.O.B.E.R
### System for Optimal Behaviour and Environment Risk

It's an AI-powered road safety system that predicts and prevents DUI-related collisions in real time by combining live environmental risk scoring, driver fatigue detection, and location based risk like bar's, casinos and etc.

---

## Live Demo

| Component | URL |
|-----------|-----|
| **Backend API** | https://s-o-b-e-r.onrender.com |
| **Frontend** | https://diplomatic-sphere-494084.framer.app/ |

Test the API is live:
```
https://s-o-b-e-r.onrender.com/health
```

---

### How-it-works

S.O.B.E.R consists of three integrated modules:

| Module | Description | Status |
| ------ | ----------- | ------ |
| **A - Risk Engine** | Live risk scoring using weather, nightlife, crash history, and time data | Complete |
| **B - Driver Monitoring** | Real-time fatigue detection via webcam and computer vision | Ongoing |
| **C - Fusion Decision Layer** | Combines A + B into a signle final safety decision | Ongoing |

---

## Quick Start

### Prerequisities
- Python 3.10+
- pip

### 1. Clone the repository
```bash
git clone https://github.com/XDSORITE/S.O.B.E.R.git
cd S.O.B.E.R
```

### 2. Install dependencies 
```bash
cd API/MAPS
pip install -r requirements.txt
```

### 3. Run the backend
```bash
cd API/MAPS
python app.py
```

The API will start at `http://127.0.0.1:5000`


### 4. Frontend (Framer)
The frontend is built in Framer and runs seperately. Open the Framer project at `https://diplomatic-sphere-494084.framer.app/`.
Make sure backend is running first before opening Framer
Framer website still completing to add all the features

---

## API Endpoints:

**Base URL:** `https://s-o-b-e-r.onrender.com`
**Local URL:** `http://127.0.0.1:5000` (requires pulling code from github, follow ## Quick Start)

### Core Risk

| Endpoint | Method | Params | Description |
| -------- | ------ | ------ | ----------- |
| `/risk` | GET | `lat`, `lon` | Live risk score for a location |
| `/risk/trend` | GET | `lat`, `lon`, `day` | 24-hour risk curve for a location |
| `/risk/compare` | GET | `lat1`, `lon1`, `lat2`, `lon2` | Side by side risk comparison of two locations |
| `/safe_route` | GET | `olat`, `olon`, `dlat`, `dlon` | Safest route between two points |
| `/nearest_safe` | GET | `lat`, `lon`, `radius` | Nearest police station, hospital, or parking |
| `/heatmap` | GET | `lat1`, `lon1`, `lat2`, `lon2`, `grid` | Risk grid over a bounding box |
| `/hotspots` | GET | — | Top 10 historical crash spots |

### Analytics and monitoring

| Endpoint | Method | Description | 
| -------- | ------ | ----------- |
| `/stats` | GET | API usage analytics from SQLite |
| `/alerts` | GET | Active weather risk alerts |
| `/alerts/check` | GET | Manually trigger alert check |
| `/health` | GET | API health status |

### ML Model 

| Endpoint | Method | Description |
| -------- | ------ | ----------- |
| `/ml/status` | GET | Model info and feature importance |
| `/ml/confusion_matrix` | GET | Confusion matrix png |
| `/ml/feature_importance` | GET | Feature importance chart PNG |

---

## API Usage Examples

### Get risk score for a location (Paste in browser)
```
https://s-o-b-e-r.onrender.com/risk?lat=40.7580&lon=-73.9855

OR

http://127.0.0.1:5000/risk?lat=40.7580&lon=-73.9855
```
```json
{
  "risk_score": 65,
  "risk_level": "HIGH",
  "reasons": [
    "Night-time driving (high DUI window)",
    "High nightlife density (129 venues)"
  ],
  "action": "Drive with extreme caution",
  "ml_prediction": {
    "predicted_severity": "injury_likely",
    "confidence": 0.71
  }
}
```

### Get safest route (Paste in browser)
```
https://s-o-b-e-r.onrender.com/safe_route?olat=40.7580&olon=-73.9855&dlat=40.6892&dlon=-74.0445

OR

http://127.0.0.1:5000/safe_route?olat=40.7580&olon=-73.9855&dlat=40.6892&dlon=-74.0445
```
```json
{
  "recommended_route": 0,
  "recommendation": {
    "text": "Route 1 is the safest choice",
    "risk_reduction": 20
  },
  "routes": [
    {
      "rank": 1,
      "average_risk": 10,
      "risk_level": "LOW",
      "distance_km": 14.74,
      "duration_min": 21.7
    }
  ]
}
```

### Compare two locations (Paste in browser)
```
https://s-o-b-e-r.onrender.com/risk/compare?lat1=40.7580&lon1=-73.9855&lat2=40.6892&lon2=-74.0445

OR

http://127.0.0.1:5000/risk/compare?lat1=40.7580&lon1=-73.9855&lat2=40.6892&lon2=-74.0445
```
```json
{
  "safer_location": "B",
  "risk_difference": 45,
  "recommendation": "Location B is safer by 45 points"
}
```

### Get 24-hour risk trend (Paste in browser)
```
https://s-o-b-e-r.onrender.com/risk/trend?lat=40.7580&lon=-73.9855&day=5

OR

http://127.0.0.1:5000/risk/trend?lat=40.7580&lon=-73.9855&day=5
```
```json
{
  "day": "Saturday",
  "peak_risk": { "hour": 0, "risk_score": 75, "risk_level": "CRITICAL" },
  "safest_time": { "hour": 6, "risk_score": 45, "risk_level": "MEDIUM" },
  "average_risk": 56.2
}
```

### Find nearest safe stop (Paste in browser)
```
https://s-o-b-e-r.onrender.com/nearest_safe?lat=40.7580&lon=-73.9855

OR

http://127.0.0.1:5000/nearest_safe?lat=40.7580&lon=-73.9855
```
```json
{
  "nearest_stop": {
    "name": "Midtown South Precinct Police Station",
    "type": "police",
    "distance_m": 917
  }
}
```

### Get crash hotspots (Paste in browser)
```
https://s-o-b-e-r.onrender.com/hotspots

OR

http://127.0.0.1:5000//hotspots
```
```json
{
  "source": "crashes.csv (offline analysis)",
  "total_hotspots": 10,
  "hotspots": [
    { "rank": 1, "lat": 40.676, "lon": -73.897, "crash_count": 41, "risk_level": "HIGH" }
  ]
}
```

---

## ML Model

The severity prediction model is a **Random Forest Classifier** trained on **5,000 real NYC crash records** from NYC Open Data, with weighted accident density computed against the full **50,000 record** dataset.

| Metric | Value |
|--------|-------|
| Algorithm | Random Forest (100 trees) |
| Training records | 5,000 real crashes |
| Reference dataset | 50,000 NYC crash records |
| Cross-validation accuracy | 62.5% ± 0.7% |
| CV folds | 5 |
| Target | Crash severity (property damage / injury / fatal) |

### Features (10 total)
| Feature | Description |
|---------|-------------|
| `hour` | Hour of day (0-23) |
| `is_weekend` | Weekend flag |
| `temperature` | Temperature at location |
| `rain` | Rain detected |
| `wind_speed` | Wind speed km/h |
| `bars` | Nightlife venue density |
| `accident_density` | Weighted historical crash density |
| `time_of_day` | Morning / afternoon / evening / night bucket |
| `is_night` | Night flag (10pm–5am) |
| `is_rush_hour` | Rush hour flag (7–9am, 5–7pm) |

### Feature Importance
| Feature | Importance |
|---------|------------|
| accident_density | 0.216 |
| bars | 0.203 |
| wind_speed | 0.199 |
| temperature | 0.188 |
| hour | 0.105 |

View live charts:
- Confusion matrix: `https://s-o-b-e-r.onrender.com/ml/confusion_matrix`
- Feature importance: `https://s-o-b-e-r.onrender.com/ml/feature_importance`

---

## Testing

**[X] tests — [X]/[X] passing**

### Run unit tests
```bash
cd API/MAPS
pytest test_sober.py -v
```

### Run integration tests
```bash
pytest test_api_integration.py -v
```

### Run all tests
```bash
pytest test_sober.py test_api_integration.py -v
```

---

## Data Sources

| Source | Data | Coverage |
|--------|------|----------|
| NYC Open Data | 50,000 motor vehicle collisions | New York City |
| OpenStreetMap (Overpass API) | Bars, nightclubs, accident hazards | Global |
| Open-Meteo | Real-time + historical weather | Global |
| OSRM | Road routing and navigation | Global |

---

## Training the Model

```bash
cd API/MAPS

# 1. Collect crash data (50,000 records from NYC Open Data)
python collect_data.py

# 2. Train the model
python train.py
```

Outputs:
- `model.pkl` — trained Random Forest model
- `cv_results.json` — cross-validation scores
- `confusion_matrix.png` — model evaluation chart
- `feature_importance.png` — feature importance chart
- `crashes_with_weather.csv` — training dataset checkpoint

---

## Note that not all backend features have been added to the frontend yet, this is the first part of shipping so we are working on integrating all these features into the framer frontend.

---

## Built for Horizons hackathon

S.O.B.E.R targets the road safety and DUI prevention problem space, specificalyl designed as a commercial API for rideshare companies and city transit auhtorities.

---

## AI USAGE

AI was mostly used to write code for training the ML model and some Flask components
