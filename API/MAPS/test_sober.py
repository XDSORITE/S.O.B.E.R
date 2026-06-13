import pytest
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from main import calculate_risk, validate_coordinates, get_time_features



#CALCULATE_RISK TESTS

class TestCalculateRisk:
    
    def test_night_time_increases_risk(self):
        score_night, _, _, _ = calculate_risk(23, 0, 0, 0, 0, 0, 20)
        score_day, _, _, _ = calculate_risk(14, 0, 0 ,0, 0, 0, 20)
        assert score_night > score_day, "Night should score higher than day"

    def test_weekend_increases_risk(self):
        score_weekend, _, _, _ = calculate_risk(14, 1, 0, 0 ,0, 0, 20)
        score_weekday, _, _, _ = calculate_risk(14, 0, 0, 0, 0, 0, 20)
        assert score_weekend > score_weekday, "Weekend should score higher than weekday"

    def test_rain_increases_risk(self):
        score_rain, _, _, _ = calculate_risk(14, 0, 1, 0, 0, 0, 20)
        score_dry, _, _, _ = calculate_risk(14, 0, 0, 0, 0, 0, 20)
        assert score_rain > score_dry, "Rain should increase risk"
    
    def test_high_wind_increases_risk(self):
        score_wind, _, _, _ = calculate_risk(14, 0, 0, 25, 0, 0, 20)
        score_calm, _, _, _ = calculate_risk(14, 0, 0, 5, 0, 0, 20)
        assert score_wind > score_calm, "High wind should increase risk"
    
    def test_extreme_heat_increases_risk(self):
        score_hot, _, _, _ = calculate_risk(14, 0, 0, 0, 0, 0, 40)
        score_normal, _, _, _ = calculate_risk(14, 0, 0, 0, 0, 0, 20)
        assert score_hot > score_normal, "Extreme heat should increase risk"
    
    def test_high_bars_increases_risk(self):
        score_bars, _, _, _ = calculate_risk(14, 0, 0, 0, 50, 0, 20)
        score_no_bars, _, _, _ = calculate_risk(14, 0, 0, 0, 0, 0, 20)
        assert score_bars > score_no_bars, "High nightlife density should increase risk"

    def test_high_accident_density_increases_risk(self):
        score_high, _, _, _ = calculate_risk(14, 0, 0, 0, 0, 100, 20)
        score_low, _, _, _ = calculate_risk(14, 0, 0, 0, 0, 0, 20)
        assert score_high > score_low, "High accident density should increase risk"

    def test_risk_score_capped_at_100(self):
        score, _, _, _ = calculate_risk(23, 1, 1, 30, 100, 200, 40)
        assert score <= 100, "Risk score should never exceed 100"

    def test_risk_score_minimum_zero(self):
        score, _, _, _ = calculate_risk(12, 0, 0, 0, 0, 0, 20)
        assert score >=0, "Risk score should never be negative"

    def test_rush_hour_increases_risk(self):
        score_rush, _, _, _ = calculate_risk(17, 0, 0, 0, 0, 0, 20)
        score_normal, _, _, _ = calculate_risk(11, 0, 0, 0, 0, 0, 20)
        assert score_rush > score_normal, "Rush hour should score higher than midday"
    
    def test_risk_levels_are_valid(self):
        valid_levels = {"LOW", "MEDIUM", "HIGH", "CRITICAL"}
        for hour in [0, 6, 12, 17 ,22]:
            _, level, _, _ = calculate_risk(hour, 0, 0, 0, 0, 0, 20)
            assert level in valid_levels, f"Risk level {level} is not valid"
    
    def test_reasons_not_empty_for_risky_conditions(self):
        _, _, reasons, _ = calculate_risk(23, 1, 1, 25, 50, 100, 40)
        assert len(reasons) > 0, "Risky conditions should produce reasons"
    
    def test_safe_conditions_produce_no_significant_risk(self):
        score, level, _, _ = calculate_risk(12, 0, 0, 5, 0, 0, 20)
        assert level in {"LOW", "MEDIUM"}, "Sfe midday conditions should not be CRITICAL"
    
    def test_none_values_dont_crash(self):
        try:
            score, _, _, _ = calculate_risk(None, None, None, None, None, None, None)
            assert score >= 0
        except Exception as e:
            pytest.fail(f"None values caused crash: {e}")
    
    def test_critical_threshold(self):
        score, level, _, _ = calculate_risk(23, 1, 1, 25, 50, 100, 40)
        if score >= 75:
            assert level == "CRITICAL"

    def test_action_is_string(self):
        _, _, _, action = calculate_risk(12, 0, 0, 0, 0, 0, 20)
        assert isinstance(action, str), "Action should be a string"

#VALIDATE_COORDINATES TESTS

class TestValidateCoordinates:

    def test_valid_nyc_coordinates(self):
        valid, error = validate_coordinates(40.758, -73.985)
        assert valid is True
        assert error is None
    
    def test_valid_dubai_coordinates(self):
        valid, error = validate_coordinates(25.2048, 55.2708)
        assert valid is True
    
    def test_invalid_latitude_too_high(self):
        valid, error = validate_coordinates(999, -73.985)
        assert valid is False
        assert "Latitude" in error
    
    def test_invalid_latitude_too_low(self):
        valid, error = validate_coordinates(-999, -73985)
        assert valid is False
        assert "Latitude" in error 

    def test_invalid_longitude_too_high(self):
        valid, error = validate_coordinates(40.758, 999)
        assert valid is False
        assert "Longitude" in error

    def test_non_numeric_latitude(self):
        valid, error = validate_coordinates("abc", -73.985)
        assert valid is False
        assert "numbers" in error
    
    def test_non_numeric_longitude(self):
        valid, error = validate_coordinates(40.758, "xyz")
        assert valid is False
        assert "numbers" in error

    def test_zero_coordinates_rejected(self):
        valid, error = validate_coordinates(0, 0)
        assert valid is False
        assert "ocean" in error

    def test_boundary_values(self):
        valid, _ = validate_coordinates(90, 180)
        assert valid is True
        valid, _ = validate_coordinates(-90, -180)
        assert valid is True
    
    def test_string_numbers_accepted(self):
        valid, _ = validate_coordinates("40.758", "-73.985")
        assert valid is True

#GET_TIME_FEATURES TESTS

class TestGetTimeFeatures:

    def test_returns_three_values(self):
        result = get_time_features()
        assert len(result) == 3
    
    def test_hour_in_valid_range(self):
        hour, _, _ = get_time_features()
        assert 0 <= hour <= 23

    def test_day_of_week_in_valid_range(self):
        _, day, _ = get_time_features()
        assert 0 <= day <= 6
    
    def test_is_weekend_is_binary(self):
        _, _, is_weekend = get_time_features()
        assert is_weekend in [0, 1]