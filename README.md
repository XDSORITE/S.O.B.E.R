# S.O.B.E.R
### System for Optimal Behaviour and Environment Risk

It's an AI-powered road safety system that predicts and prevents DUI-related collisions in real time by combining live environmental risk scoring, driver fatigue detection, and intelligent safe routing.

---

### How-it-works

S.O.B.E.R consists of three integrated modules:

| Module | Description | Status |
| ------ | ----------- | ------ |
| **A - External Risk Engine** | Live risk scoring using weather, nightlife, crash history, and time data | Complete |
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

---

### Project Structure 

```
S.O.B.E.R/
├── API/
│   └── MAPS/
│       ├── app.py              # Flask API server
│       ├── main.py             # Core logic, ML model, data fetching
│       ├── train.py            # ML model training pipeline
│       ├── collect_data.py     # NYC crash data collection
│       ├── crashes.csv         # 50,000 real NYC crash records
│       ├── model.pkl           # Trained Random Forest model
│       ├── cv_results.json     # Cross-validation results
│       ├── confusion_matrix.png
│       ├── feature_importance.png
│       ├── sober.db            # SQLite analytics database
│       ├── test_sober.py       # Unit tests (102 tests)
│       ├── test_api_integration.py  # Integration tests (18 tests)
|       └── requirements.text
└── README.md
```
 
---

## API Endpoints 

### Core Risk

| Endpoint | Method | Description |
| -------- | ------ | ----------- |
| `/risk` | GET | Live risk score for a location |
| `/risk/trend` | GET | 24-hour risk curve for a location |
| `/risk/compare` | GET | Side by side risk comparison of two locations |
| `/safe_route` | GET | Safest route between two points |
| `/nearest_safe` | GET | Nearest police station, hospital, or parking |
| `/heatmap` | GET | Risk grid over a bounding box |
| `/hotspots` | GET | Top 10 historical crash spots |

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

### Get risk score for a location
```bash
GET /risk?lat=40.7580&lon=-73.9855
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

### Get safest route
```bash
GET /safe_route?olat=40.7580&olon=-73.9855&dlat=40.6892&dlon=-74.0445
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

### Compare two locations
```bash
GET /risk/compare?lat1=40.7580&lon1=-73.9855&lat2=40.6892&lon2=-74.0445
```
```json
{
  "safer_location": "B",
  "risk_difference": 45,
  "recommendation": "Location B is safer by 45 points"
}
```

### Get 24-hour risk trend
```bash
GET /risk/trend?lat=40.7580&lon=-73.9855&day=5
```
```json
{
  "day": "Saturday",
  "peak_risk": { "hour": 0, "risk_score": 75, "risk_level": "CRITICAL" },
  "safest_time": { "hour": 6, "risk_score": 45, "risk_level": "MEDIUM" },
  "average_risk": 56.2
}
```

### Find nearest safe stop
```bash
GET /nearest_safe?lat=40.7580&lon=-73.9855
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