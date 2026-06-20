import pytest
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from main import (calculate_risk, validate_coordinates, get_time_features, get_crash_hotspots,
                  sample_waypoints)




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

# GET_CRASH_HOTSPOTS TESTS

class TestGetCrashHotspots:

    def test_returns_list(self):
        result = get_crash_hotspots(top_k=5)
        assert isinstance(result, list)
    
    def test_returns_correct_count(self):
        result = get_crash_hotspots(top_k=5)
        assert len(result) == 5

    def test_default_returns_10(self):
        result = get_crash_hotspots()
        assert len(result) == 10
    
    def test_hotspot_has_required_fields(self):
        result = get_crash_hotspots(top_k=1)
        hotspot = result[0]
        assert "rank" in hotspot
        assert "lat" in hotspot
        assert "lon" in hotspot
        assert "crash_count" in hotspot
        assert "risk_level" in hotspot

    def test_ranks_are_sequential(self):
        result = get_crash_hotspots(top_k=5)
        ranks = [h["rank"] for h in result]
        assert ranks == [1, 2, 3, 4, 5]
    
    def test_sorted_by_crash_count_descending(self):
        result = get_crash_hotspots(top_k=5)
        counts = [h["crash_count"] for h in result]
        assert counts == sorted(counts, reverse=True)
    
    def test_no_zero_coordinates(self):
        result = get_crash_hotspots(top_k=10)
        for h in result:
            assert not (h["lat"] == 0 and h["lon"] == 0), "Zero coordinates should be filtered"

    def test_coordinates_within_nyc_bounds(self):
        result = get_crash_hotspots(top_k=10)
        for h in result:
            assert 40.4 <= h["lat"] <= 41.0, f"Lat {h['lat']} outside NYC bounds"
            assert -74.5 <= h["lon"] <=-73.5, f"Lon {h['lon']} outside NYC bounds"
    
    def test_risk_levels_are_valid(self):
        result = get_crash_hotspots(top_k=10)
        valid_levels = {"LOW", "MEDIUM", "HIGH", "CRITICAL"}
        for h in result:
            assert h["risk_level"] in valid_levels
    
    def test_crash_count_positive(self):
        result = get_crash_hotspots(top_k=10)
        for h in result:
            assert h["crash_count"] > 0
    
    def test_top_k_zero_returns_empty(self):
        result = get_crash_hotspots(top_k=0)
        assert result == []
    
    def test_high_crash_count_is_critical_or_high(self):
        result = get_crash_hotspots(top_k=1)
        top = result[0]
        assert top["risk_level"] in {"HIGH", "CRITICAL"}
    
#ADDITIONAL TESTS FOR EDGE CASES

class TestCalculateRiskEdgeCases:

    def test_midnight_saturday_is_highest_risk(self):
        score_midnight_sat, _, _, _ = calculate_risk(0, 1, 0, 0, 0, 0, 20)
        score_noon_monday, _, _, _ = calculate_risk(12, 0, 0, 0, 0, 0, 20)
        assert score_midnight_sat > score_noon_monday
    
    def test_all_risk_factors_combined(self):
        score, level, reasons, action = calculate_risk(23, 1, 1, 25, 100, 200, 40)
        assert score == 100
        assert level == "CRITICAL"
        assert len(reasons) >= 4

    def test_early_morning_is_high_risk(self):
        score_3am, _, _, _ = calculate_risk(3, 0, 0, 0, 0, 0, 20)
        score_10am, _, _, _ = calculate_risk(10, 0, 0, 0, 0, 0, 20)
        assert score_3am > score_10am

    def test_moderate_bars_adds_risk(self):
        score_mod, _, _, _ = calculate_risk(12, 0, 0, 0, 10, 0, 20)
        score_none, _, _, _ = calculate_risk(12, 0, 0, 0, 0, 0, 20)
        assert score_mod > score_none

    def test_high_temperature_adds_risk(self):
        score_hot, _, _, _ = calculate_risk(12, 0, 0, 0, 0, 0, 39)
        score_mild, _, _, _ = calculate_risk(12, 0, 0, 0, 0, 0, 25)
        assert score_hot > score_mild

    def test_risk_level_matches_score(self):
        for hour in range(24):
            score, level, _, _ = calculate_risk(hour, 0, 0, 0, 0, 0, 20) 
            if score >= 75:
                assert level == "CRITICAL"
            elif score >= 50:
                assert level == "HIGH"
            elif score >= 25:
                assert level == "MEDIUM"
            else:
                assert level == "LOW"

    def test_zero_bars_adds_no_risk(self):
        score_zero, _, _, _ = calculate_risk(12, 0, 0, 0, 0, 0, 20)
        score_no_bars, _, _, _ = calculate_risk(12, 0, 0, 0, 0, 0, 20)
        assert score_zero == score_no_bars 

    def test_action_changes_with_risk_level(self):
        _, _, _, action_safe = calculate_risk(12, 0, 0, 0, 0, 0, 20)
        _, _, _, action_danger = calculate_risk(23, 1, 1, 25, 100, 200, 40)
        assert action_safe != action_danger 

class TestValidateCoordinatesEdgeCass:

    def test_negative_valid_coordinates(self):
        valid, _ = validate_coordinates(-33.8688, 151.2093)
        assert valid is True
    
    def test_valid_sharjah_coordinates(self):
        valid, _ = validate_coordinates(25.3463, 55.4209)
        assert valid is True
    
    def test_empty_string_rejected(self):
        valid, error = validate_coordinates("", -73.985)
        assert valid is False
    
    def test_none_rejected(self):
        valid, error = validate_coordinates(None, -73.985)
        assert valid is False
    
    def test_exactly_minus_90_lat_valid(self):
        valid, _ = validate_coordinates(-90, 0)
        assert valid is True
    
    def test_exactly_90_lat_valid(self):
        valid, _ = validate_coordinates(90, 0)
        assert valid is True
    
    def test_exactly_180_lon_valid(self):
        valid, _ = validate_coordinates(0, 180)
        assert valid is True
    
    def test_just_over_90_lat_invalid(self):
        valid, _ = validate_coordinates(90.001, 0)
        assert valid is False
    
    def test_just_over_180_lon_invalid(self):
        valid, _ = validate_coordinates(0, 180.001)
        assert valid is False
    
    def test_whitespace_string_rejected(self):
        valid, error = validate_coordinates("", -73.985)
        assert valid is False

    
#SAMPLE_WAYPOINTS TESTS

class TestSampleWaypoints:

    def test_returns_list(self):
        geometry = {"coordinates": [[-73.985, 40.758], [-73.990, 40.760], [-73.995, 40.762]]}
        result = sample_waypoints(geometry)
        assert isinstance(result, list)

    def test_each_waypoint_has_lat_lon(self):
        geometry = {"coordinates": [[-73.985, 40.758], [-73.990, 40.760], [-73.995, 40.762]]}
        result = sample_waypoints(geometry)
        for wp in result:
            assert "lat" in wp
            assert "lon" in wp
    
    def test_empty_geometry_returns_empty(self):
        geometry = {"coordinates": []}
        result = sample_waypoints(geometry)
        assert result == []
    
    def test_empty_dict_returns_empty(self):
        result = sample_waypoints({})
        assert result == []
    
    def test_coordinates_are_flipped(self):
        geometry = {"coordinates": [[-73.985, 40.758]]}
        result = sample_waypoints(geometry)
        assert result[0]["lat"] == 40.758
        assert result[0]["lon"] == -73.985
    
    def test_samples_correct_number_of_points(self):
        coords = [[-73.0 + i*0.001, 40.0 + i*0.001] for i in range(100)]
        geometry = {"coordinates": coords}
        result = sample_waypoints(geometry, num_points=6)
        assert len(result) == 6
    
    def test_small_geometry_returns_all_points(self):
        coords = [[-73.985, 40.758], [-73.990, 40.760]]
        geometry = {"coordinates": coords}
        result = sample_waypoints(geometry, num_points=6)
        assert len(result) == 2
    
    def test_single_coordinate(self):
        geometry = {"coordinates": [[-73.985, 40.758]]}
        result = sample_waypoints(geometry)
        assert len(result) == 1
        assert result[0]["lat"] == 40.758
        assert result[0]["lon"] == -73.985

#CALCULATE_RISK_BOUNDARY TESTS

class TestCalculateRiskBoundaries:

    def test_hour_exactly_22_is_night(self):
        score_22, level, reasons, _ = calculate_risk(22, 0, 0, 0, 0, 0, 20)
        assert score_22 >= 30
        assert 'Night-time' in "".join(reasons)
    
    def test_hour_exactly_5_is_night(self):
        score_5, level, reasons, _ = calculate_risk(5, 0, 0, 0, 0, 0, 20)
        assert score_5>= 30
    
    def test_hour_6_is_not_night(self):
        score_6, _, reasons, _ = calculate_risk(6, 0, 0, 0, 0, 0, 20)
        night_reasons = [r for r in reasons if "Night" in r]
        assert len(night_reasons) == 0

    def test_hour_17_is_rush_hour(self):
        _, _, reasons, _ = calculate_risk(17, 0, 0, 0, 0, 0, 20)
        assert any("Rush" in r or "rush" in r for r in reasons)

    def test_hour_19_is_rush_hour(self):
        _, _, reasons, _ = calculate_risk(19, 0, 0, 0, 0, 0, 20)
        assert any("Rush" in r or "rush" in r for r in reasons)

    def test_hour_20_is_not_rush_hour(self):
        _, _, reasons, _ = calculate_risk(20, 0, 0, 0, 0, 0, 20)
        rush_reasons = [r for r in reasons if "Rush" in r or "rush" in r]
        assert len(rush_reasons) == 0
    
    def test_wind_speed_exactly_20_no_penalty(self):
        score_20, _, _, _ = calculate_risk(12, 0, 0, 20, 0, 0, 20)
        score_0, _, _, _ = calculate_risk(12, 0, 0, 0, 0, 0, 20)
        assert score_20 == score_0
    
    def test_wind_speed_21_adds_penalty(self):
        score_21, _, _, _ = calculate_risk(12, 0, 0, 21, 0, 0, 20)
        score_0, _, _, _ = calculate_risk(12, 0, 0, 0, 0, 0, 20)
        assert score_21 > score_0
    
    def test_temperature_38_triggers_extreme_heat(self):
        score_39, _, reasons, _ = calculate_risk(12, 0, 0, 0, 0, 0, 38)
        assert any("heat" in r.lower() or "Extreme" in r for r in reasons)
    
    def test_temperature_37_no_extreme_heat(self):
        _, _, reasons, _ = calculate_risk(12, 0, 0, 0, 0, 0, 37)
        extreme = [r for r in reasons if "Extreme" in r]
        assert len(extreme) == 0
    
#CALULATE_RISK_REASONS TEST

class TestCalculateRiskReasons:

    def test_night_reason_contains_night(self):
        _, _, reasons, _ = calculate_risk(23, 0, 0, 0, 0, 0, 20)
        assert any("Night" in r or "night" in r for r in reasons)

    def test_weekend_reason_present(self):
        _, _, reasons, _ = calculate_risk(12, 1, 0, 0, 0, 0, 20)
        assert any("Weekend" in r or "weekend" in r for r in reasons)

    def test_rain_reason_present(self):
        _, _, reasons, _ = calculate_risk(12, 0, 1, 0, 0, 0, 20)
        assert any("Rain" in r or "rain" in r for r in reasons)
    
    def test_wind_reason_present(self):
        _, _, reasons, _ = calculate_risk(12, 0, 0, 25, 0, 0, 20)
        assert any("wind" in r.lower() for r in reasons)
    
    def test_extreme_heat_reason_present(self):
        _, _, reasons, _ = calculate_risk(12, 0, 0, 0, 0, 0, 39)
        assert any("heat" in r.lower() or "Extreme" in r for r in reasons)
    
    def test_moderate_heat_reason_present(self):
        _, _, reasons, _ = calculate_risk(12, 0, 0, 0, 0, 0, 33)
        assert any("temperature" in r.lower() or "heat" in r.lower() for r in reasons)
    
    def test_high_bars_reason_present(self):
        _, _, reasons, _ = calculate_risk(12, 0, 0, 0, 50, 0, 20)
        assert any("nightlife" in r.lower() or "bar" in r.lower() or "venue" in r.lower() for r in reasons)
    
    def test_low_bars_reason_present(self):
        _, _, reasons, _ = calculate_risk(12, 0, 0, 0, 3, 0, 20)
        assert any("nightlife" in r.lower() or "venue" in r.lower() for r in reasons)
    
    def test_accident_density_reason_present(self):
        _, _, reasons, _ = calculate_risk(12, 0, 0, 0, 0, 100, 20)
        assert any("accident" in r.lower() for r in reasons)
    
    def test_no_risk_factors_message(self):
        _, _, reasons, _ = calculate_risk(12, 0, 0, 0, 0, 0, 20)
        assert any("No significant" in r for r in reasons)
    
    def test_reasons_are_strings(self):
        _, _, reasons, _ = calculate_risk(23, 1, 1, 25, 50, 100, 40)
        for r in reasons:
            assert isinstance(r, str)
    
    def test_multiple_risk_factors_multiple_reasons(self):
        _, _, reasons, _ = calculate_risk(23, 1, 1, 25, 50, 100, 40)
        assert len(reasons) >= 4

#CALCULATE_RISK_ACTION tests

class TestCalculateRiskAction:

    def test_critical_action_is_avoid(self):
        score, level, _, action = calculate_risk(23, 1, 1, 25, 100, 200, 40)
        if level == "CRITICAL":
            assert "Avoid" in action or "STOP" in action or "caution" in action.lower()
    
    def test_low_risk_action_is_normal(self):
        score, level, _, action = calculate_risk(12, 0, 0, 0, 0, 0, 20)
        if level == "LOW":
            assert "Normal" in action or "safely" in action.lower()
    
    def test_action_is_not_empty(self):
        for hour in [0, 6, 12, 17, 22]:
            _, _, _, action = calculate_risk(hour, 0, 0, 0, 0, 0, 20)
            assert len(action) > 0
    
    def test_high_risk_action_mentions_caution(self):
        _, level, _, action = calculate_risk(23, 1, 0, 0, 50, 0, 20)
        if level in {"HIGH", "CRITICAL"}:
            assert "caution" in action.lower() or "Avoid" in action or "alert" in action.lower()

#SAMPLE_WAYPOINTS_ADDITIONAL TESTS

class TestSampleWaypointsAdditional:

    def test_large_geometry_sampled_correctly(self):
        coords = [[-73.0 + i*0.001, 40.0 + i*0.001] for i in range(200)]
        geometry = {"coordinates": coords}
        result = sample_waypoints(geometry, num_points=6)
        assert len(result) == 6
    
    def test_waypoints_within_original_bound(self):
        coords = [[-74.0 + i*0.01, 40.0 + i*0.01] for i in range(50)]
        geometry = {"coordinates": coords}
        result = sample_waypoints(geometry, num_points=6)
        lats = [wp["lat"] for wp in result]
        lons = [wp["lon"] for wp in result]
        assert min(lats) >= 40.0
        assert max(lats) <= 40.49
        assert min(lons) >= -74.0
        assert max(lons) <= -73.51

    def test_num_points_1_returns_1(self):
        coords = [[-73.985, 40.785], [-73.990, 40.760], [-73.995, 40.762]]
        geometry = {"coordinates": coords}
        result = sample_waypoints(geometry, num_points=1)
        assert len(result) == 1

#GET_TIME_FEATURES_ADDITIONAL TESTS

class TestGetTimeFeaturesAdditional:

    def test_weekend_correct_for_saturday(self):
        import datetime
        _, day, is_weekend = get_time_features()
        if day >= 5:
            assert is_weekend == 1
        else:
            assert is_weekend ==0
    
    def test_all_values_are_integers(self):
        hour, day, is_weekend = get_time_features()
        assert isinstance(hour, int)
        assert isinstance(day, int)
        assert isinstance(is_weekend, int)
    
    def test_consistent_results(self):
        result1 = get_time_features()
        result2 = get_time_features()
        assert result1[0] == result2[0]
        assert result1[1] == result2[1]

#VALIDATE_COORDINATES_STRESS TESTS

class TestValidateCoordinatesStress:

    def test_many_valid_world_cities(self):
        cities = [
            (51.5074, -0.1278),
            (48.8566, 2.3522),
            (35.6762, 139.6503),
            (-33.8688, 151.2093),
            (55.7558, 37.6173),
            (1.3521, 103.8198),
            (-23.5505, -46.6333),
            (19.4326, -99.1332)
        ]
        for lat, lon in cities:
            valid, error = validate_coordinates(lat, lon)
            assert valid is True, f"City ({lat}, {lon}) should be valid: {error}"
    
    def test_many_invalid_coordinates(self):
        invalid = [
            (91, 0), (-91, 0), (0, 181), (0, -181),
            (999, 999), (-999, -999), (float('inf'), 0)
        ]
        for lat, lon in invalid:
            valid, _ = validate_coordinates(lat, lon)
            assert valid is False, f"({lat}, {lon}) should be invalid"
    
