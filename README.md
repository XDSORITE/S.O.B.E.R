# S.O.B.E.R

We have named this project **S.O.B.E.R** which stands for **Situational Observation Based Emergency Risk System**.

S.O.B.E.R is a system that uses live locational events to guide drivers for safe paths rather then the fastest. It does this by accounting for driver's attentiveness, crash locations, high risk locations like bar's and clubs.

The goal is simple: help drivers, rideshare companies. It protects companies from potential lawsuits and protects drivers by keeping them safe.

The name reflects the system's purpose: keeping drivers aware, informed, and safer on the road.

# URL'S

> [!IMPORTANT]
> Before deploying, update the backend URL in the following files:
> - `website/app.js` — change `API_BASE` to point to your deployed backend
> - `website/index.html` — update the CSP `connect-src` to allow your backend domain
> - `docker-compose.yml` — update `Host()` rules to match your domain

---

# Quick explanation on how S.O.B.E.R works

It has 3 main steps:

1) The system observes and collects data on the surrounding and the driver.

2) System does analysis using multiple machine learning algorithms which allows it to stay small and efficient while still being powerful.

3) It calculates an efficient path while staying away from threats that can cause an accident.


# Quick Start

## Running Locally

### Prerequisites
- Python 3.11+

### Backend API
```bash
cd API/MAPS
pip install -r requirements.txt
python app.py
```
The API will start on `http://localhost:5000`.

### Frontend
The `website/` folder contains static HTML/JS/CSS. Serve it with any web server:
```bash
cd website
python -m http.server 8080
```

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/health` | GET | Health check |
| `/risk?lat=...&lon=...` | GET | Risk assessment for a location |
| `/safe_route?olat=...&olon=...&dlat=...&dlon=...` | GET | Safe route between two points |
| `/heatmap?lat1=...&lon1=...&lat2=...&lon2=...` | GET | Risk heatmap grid |
| `/hotspots` | GET | Top crash hotspots |
| `/stats` | GET | Usage statistics |
| `/alerts` | GET | Active weather alerts |

> [!WARNING]
> # Disclosure Notice
>
> This project is currently in active development.
>
> Some features are incomplete and the current version represents an early release.
>
> ## AI Usage
>
> README was not written with AI.
>
> Most of the code is hand written and not helped by AI, but some parts such as fixing small bugs, creating ML model training scripts, and fixing merge issues were done with AI assistance.
>
> AI was primarily used for speeding up development time :)
>
> ## ML Model
>
> Training was done using public images from Google and combining smaller datasets created from people.
>
> This allows us to quickly aggregate lots of images and complete training early.
