"""
Unit Tests for METHANOS — Survey Confidence Engine (Person 2 - Phase 1)
Validates Quality Control evaluations, Accept/Re-survey decisions, and demo benchmarks.
"""

import unittest
from confidence_engine.scoring import (
    calculate_confidence,
    evaluate_gps_coverage,
    evaluate_sensor_health,
    evaluate_survey_speed,
    evaluate_weather_suitability,
    evaluate_route_completeness,
    CONFIDENCE_ACCEPT_THRESHOLD,
    DECISION_ACCEPT,
    DECISION_RESURVEY,
)
from confidence_engine.surveys import (
    HIGH_CONFIDENCE_SURVEY,
    LOW_CONFIDENCE_SURVEY,
    get_sample_survey,
    get_all_sample_surveys,
)


class TestConfidenceScoring(unittest.TestCase):
    def test_high_confidence_benchmark(self):
        """Validates that S-2101 scores 100 with ACCEPT decision and anomaly dispatch."""
        res = calculate_confidence(HIGH_CONFIDENCE_SURVEY)

        self.assertEqual(res["survey_id"], "S-2101")
        self.assertEqual(res["segment_id"], "P-104")
        self.assertEqual(res["confidence_score"], 100)
        self.assertEqual(res["decision"], DECISION_ACCEPT)
        self.assertTrue(res["checks"]["gps_coverage"])
        self.assertTrue(res["checks"]["sensor_health"])
        self.assertTrue(res["checks"]["speed_ok"])
        self.assertTrue(res["checks"]["weather_ok"])
        self.assertTrue(res["checks"]["route_complete"])
        self.assertTrue(res["anomaly_detected"])
        self.assertEqual(res["action_recommendation"], "DISPATCH_FIELD_VERIFICATION")

    def test_low_confidence_benchmark_s2201(self):
        """
        Validates S-2201 (P-118) from Person 2 task doc:
        speed_ok=False, weather_ok=False -> score = 43 (RE-SURVEY)
        """
        res = calculate_confidence(LOW_CONFIDENCE_SURVEY)

        self.assertEqual(res["survey_id"], "S-2201")
        self.assertEqual(res["segment_id"], "P-118")
        self.assertEqual(res["confidence_score"], 43)
        self.assertEqual(res["decision"], DECISION_RESURVEY)
        self.assertTrue(res["checks"]["gps_coverage"])
        self.assertTrue(res["checks"]["sensor_health"])
        self.assertFalse(res["checks"]["speed_ok"])
        self.assertFalse(res["checks"]["weather_ok"])
        self.assertTrue(res["checks"]["route_complete"])
        self.assertEqual(res["action_recommendation"], "FLAGGED_FOR_RESURVEY")

    def test_threshold_boundary_decision(self):
        """Verifies boundary: >= 60 ACCEPT, < 60 RE-SURVEY."""
        # Exactly 3 checks passing (3 * 20 = 60)
        survey_60 = {
            "survey_id": "TEST-60",
            "gps_coverage": True,
            "sensor_health": True,
            "speed_ok": True,
            "weather_ok": False,
            "route_complete": False,
        }
        res_60 = calculate_confidence(survey_60)
        self.assertEqual(res_60["confidence_score"], 60)
        self.assertEqual(res_60["decision"], DECISION_ACCEPT)

        # 2 checks passing (2 * 20 = 40)
        survey_40 = {
            "survey_id": "TEST-40",
            "gps_coverage": True,
            "sensor_health": True,
            "speed_ok": False,
            "weather_ok": False,
            "route_complete": False,
        }
        res_40 = calculate_confidence(survey_40)
        self.assertEqual(res_40["confidence_score"], 40)
        self.assertEqual(res_40["decision"], DECISION_RESURVEY)

    def test_gps_check_logic(self):
        """Tests boolean and numeric GPS coverage evaluations."""
        ok, pts = evaluate_gps_coverage({"gps_coverage": True})
        self.assertTrue(ok)
        self.assertEqual(pts, 20.0)

        ok, pts = evaluate_gps_coverage({"gps_coverage": False})
        self.assertFalse(ok)
        self.assertEqual(pts, 0.0)

        ok, pts = evaluate_gps_coverage({"gps_fix_pct": 98.0})
        self.assertTrue(ok)
        self.assertEqual(pts, 20.0)

        ok, pts = evaluate_gps_coverage({"gps_fix_pct": 50.0})
        self.assertFalse(ok)
        self.assertEqual(pts, 0.0)

    def test_sensor_health_logic(self):
        """Tests sensor health flags and drift states."""
        ok, pts = evaluate_sensor_health({"sensor_health": True})
        self.assertTrue(ok)
        self.assertEqual(pts, 20.0)

        ok, pts = evaluate_sensor_health({"sensor_fault": True})
        self.assertFalse(ok)
        self.assertEqual(pts, 0.0)

        ok, pts = evaluate_sensor_health({"sensor_health_status": "drift"})
        self.assertFalse(ok)
        self.assertEqual(pts, 8.0)

    def test_survey_speed_logic(self):
        """Tests vehicle speed thresholds (<= 25 km/h ok, > 25 degraded, > 35 fail)."""
        ok, pts = evaluate_survey_speed({"vehicle_speed": 18.0})
        self.assertTrue(ok)
        self.assertEqual(pts, 20.0)

        ok, pts = evaluate_survey_speed({"vehicle_speed": 28.0})
        self.assertFalse(ok)
        self.assertEqual(pts, 8.0)

        ok, pts = evaluate_survey_speed({"vehicle_speed": 45.0})
        self.assertFalse(ok)
        self.assertEqual(pts, 0.0)

    def test_weather_logic(self):
        """Tests wind limits (<= 15 km/h ok) and adverse storms."""
        ok, pts = evaluate_weather_suitability({"wind_speed": 10.0, "weather_conditions": "clear"})
        self.assertTrue(ok)
        self.assertEqual(pts, 20.0)

        ok, pts = evaluate_weather_suitability({"wind_speed": 24.0, "weather_conditions": "clear"})
        self.assertFalse(ok)
        self.assertEqual(pts, 0.0)

        ok, pts = evaluate_weather_suitability({"wind_speed": 8.0, "weather_conditions": "heavy_rain"})
        self.assertFalse(ok)
        self.assertEqual(pts, 0.0)

    def test_route_completeness_logic(self):
        """Tests route completeness >= 90%."""
        ok, pts = evaluate_route_completeness({"route_completeness_pct": 95.0})
        self.assertTrue(ok)
        self.assertEqual(pts, 20.0)

        ok, pts = evaluate_route_completeness({"route_completeness_pct": 65.0})
        self.assertFalse(ok)
        self.assertEqual(pts, 6.0)

    def test_custom_weight_normalization(self):
        """Verifies custom weights redistribute to 100% total."""
        custom_weights = {
            "gps_coverage": 10.0,
            "sensor_health": 10.0,
            "survey_speed": 40.0,
            "weather_suitability": 30.0,
            "route_completeness": 10.0,
        }
        res = calculate_confidence(HIGH_CONFIDENCE_SURVEY, weights=custom_weights)
        self.assertEqual(res["confidence_score"], 100)
        self.assertEqual(res["factor_scores"]["survey_speed"], 40.0)
        self.assertEqual(res["factor_scores"]["weather_suitability"], 30.0)

    def test_sample_surveys_helpers(self):
        """Verifies lookup and full evaluated list."""
        survey = get_sample_survey("S-2101")
        self.assertIsNotNone(survey)
        self.assertEqual(survey["segment_id"], "P-104")

        all_surveys = get_all_sample_surveys(evaluated=True)
        self.assertGreaterEqual(len(all_surveys), 5)
        for s in all_surveys:
            self.assertIn("confidence_score", s)
            self.assertIn("decision", s)
            self.assertIn("checks", s)


if __name__ == "__main__":
    unittest.main()
