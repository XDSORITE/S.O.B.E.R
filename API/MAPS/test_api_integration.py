import pytest
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from app import app

@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

#SAFE_ROUTE TESTS

class TestSafeRouteEndpoint:

    def test_safe_route_missing_params_returns_400(self, client):
        response = client.get('/safe_route?olat=40.7580&olon=-73.9855')
        assert response.status_code == 400
    
    def test_safe_route_invalid_origin_returns_400(self, client):
        response = client.get('/safe_route?olat=999&olon=-73.9855&dlat=40.6892&dlon=-74.0445')
        assert response.status_code == 400
    
    def test_safe_route_invalid_destination_returns_400(self, client):
        response = client.get('/safe_route?olat=40.7580&olon=-73.9855&dlat=999&dlon=-74.0445')
        assert response.status_code == 400
    
    def test_safe_route_valid_returns_200(self, client):
        response = client.get('/safe_route?olat=40.7580&olon=-73.9855&dlat=40.689&dlon=-74.0445')
        assert response.status_code == 200
    
    def test_safe_route_has_routes_field(self, client):
        response = client.get('/safe_route?olat=40.7580&olon=-73.9855&dlat=40.6892&dlon=-74.0445')
        data = response.get_json()
        assert "routes" in data
    
    def test_safe_routes_have_rank(self, client):
        response = client.get('/safe_route?olat=40.7580&olon=-73.9855&dlat=40.6892&dlon=-74.0445')
        data = response.get_json()
        if data.get("routes"):
            assert "rank" in data["routes"][0]
    
    def test_safe_route_routes_sorted_by_risk(self, client):
        response = client.get('/safe_route?olat=40.7580&olon=-73.9855&dlat=40.6892&dlon=-74.0445')
        data = response.get_json()
        routes = data.get("routes", [])
        if len(routes) > 1:
            risks = [r["average_risk"] for r in routes]
            assert risks == sorted(risks)
    
    def test_safe_route_has_recommendation(self, client):
        response = client.get('/safe_route?olat=40.7580&olon=-73.9855&dlat=40.6892&dlon=-74.0445')
        data = response.get_json()
        assert "recommendation" in data

class TestNearestSafeEndpointFull:

    def test_nearest_safe_valid_returns_200(self, client):
        response = client.get('/nearest_safe?lat=40.7580&lon=-73.9855')
        assert response.status_code == 200
    
    def test_nearest_safe_has_stops_field(self, client):
        response = client.get('/nearest_safe?lat=40.7580&lon=-73.9855')
        data = response.get_json()
        assert "stops" in data 
    
    def test_nearest_safe_stops_sorted_by_priority(self, client):
        response = client.get('/nearest_safe?lat=40.7580&lon=-73.9855')
        data = response.get_json()
        stops = data.get("stops", [])
        if len(stops) > 1:
            priorities = [s["safety_priority"] for s in stops]
            assert priorities == sorted(priorities)
    
    def test_nearest_safe_has_distance_field(self, client):
        response = client.get('/nearest_safe?lat=40.7580&lon=-73.9855')
        data = response.get_json()
        stops = data.get("stops", [])
        if stops:
            assert "distance_m" in stops[0]
            assert "distance_km" in stops[0]
    
class TestHeatmapEndpoint:

    def test_heatmap_valid_returns_200(self, client):
        response = client.get('/heatmap?lat1=40.70&lon1=-74.02&lat2=40.72&lon2=-73.98&grid=2')
        assert response.status_code == 200
    
    def test_heatmap_has_heatmap_field(self, client):
        response = client.get('/heatmap?lat1=40.70&lon1=-74.02&lat2=40.72&lon2=-73.98&grid=2')
        data = response.get_json()
        assert "heatmap" in data
    
    def test_heatmap_grid_size_capped_at_8(self, client):
        response = client.get('/heatmap?lat1=40.70&lon1=-74.02&lat2=40.72&lon2=-73.98&grid=20')
        data = response.get_json()
        assert data["grid_size"] <= 8

class TestMLChartEndpoints:

    def test_confusion_matrix_returns_image(self, client):
        response = client.get('/ml/confusion_matrix')
        assert response.status_code == 200
        assert response.content_type == 'image/png'
    
    def test_feature_importance_returns_image(self, client):
        response = client.get('/ml/feature_importance')
        assert response.status_code == 200
        assert response.content_type == 'image/png'
    