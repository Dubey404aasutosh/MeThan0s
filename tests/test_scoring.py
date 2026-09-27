"""
Unit tests for Person 1 Priority Engine Scoring Logic.
Verifies the P-104 reference benchmark (85/100, CRITICAL) and all factor rules.
"""

import sys
import os
import unittest

# Add project root to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from priority_engine.scoring import (
    calculate_priority,
    classify_tier,
    evaluate_previous_incidents,
    evaluate_pe_vulnerability,
    evaluate_days_since_survey,
    evaluate_third_party_activity,
    evaluate_rodent_history,
    evaluate_public_consequence,
    DEFAULT_WEIGHTS
)


class TestPriorityEngineScoring(unittest.TestCase):

    def test_p104_reference_benchmark(self):
        """
        PRD & Person 1 benchmark:
        P-104 should score exactly 85/100 and classify as CRITICAL.
        Factors:
        - previous_incidents (2) -> 18
        - pe_vulnerability ('pe_service_hotspot') -> 20
        - days_since_survey (9 with target 12) -> 15
        - third_party_activity ('direct_excavation_hazard') -> 15
        - rodent_history (4) -> 10
        - public_consequence ('dense_residential') -> 7
        Sum = 18 + 20 + 15 + 15 + 10 + 7 = 85
        """
        p104_data = {
            "segment_id": "P-104",
            "material": "pe_service_hotspot",
            "depth_meters": 0.8,
            "operating_pressure_bar": 0.1,
            "previous_incidents": 2,
            "days_since_survey": 9,
            "target_survey_cycle": 12,
            "third_party_activity": "direct_excavation_hazard",
            "rodent_incidents": 4,
            "area_type": "dense_residential",
            "location": {"lat": 28.6139, "lng": 77.2090}
        }

        result = calculate_priority(p104_data)

        self.assertEqual(result["segment_id"], "P-104")
        self.assertEqual(result["score"], 85)
        self.assertEqual(result["tier"], "CRITICAL")
        self.assertEqual(result["material"], "pe_service_hotspot")
        self.assertEqual(result["depth_meters"], 0.8)
        self.assertEqual(result["operating_pressure_bar"], 0.1)
        self.assertEqual(result["third_party_activity"], "direct_excavation_hazard")

        # Verify exact factor breakdown
        expected_factors = {
            "previous_incidents": 18,
            "pe_vulnerability": 20,
            "days_since_survey": 15,
            "third_party_activity": 15,
            "rodent_history": 10,
            "public_consequence": 7
        }
        self.assertEqual(result["factors"], expected_factors)

    def test_previous_incidents_rules(self):
        # 0 -> 0, 1 -> 10, 2 -> 18, 3+ -> 25
        self.assertEqual(evaluate_previous_incidents(0), 0)
        self.assertEqual(evaluate_previous_incidents(1), 10)
        self.assertEqual(evaluate_previous_incidents(2), 18)
        self.assertEqual(evaluate_previous_incidents(3), 25)
        self.assertEqual(evaluate_previous_incidents(5), 25)

    def test_pe_vulnerability_rules(self):
        # steel main -> 5, pe distribution -> 15, pe hotspot -> 20
        self.assertEqual(evaluate_pe_vulnerability("steel_main"), 5)
        self.assertEqual(evaluate_pe_vulnerability("pe_distribution"), 15)
        self.assertEqual(evaluate_pe_vulnerability("pe_service_hotspot"), 20)

    def test_days_since_survey_rules(self):
        # min(20, 20 * days_since / target_cycle)
        self.assertEqual(evaluate_days_since_survey(0, 12), 0.0)
        self.assertEqual(evaluate_days_since_survey(6, 12), 10.0)
        self.assertEqual(evaluate_days_since_survey(12, 12), 20.0)
        self.assertEqual(evaluate_days_since_survey(24, 12), 20.0)  # Capped at 20

    def test_third_party_activity_rules(self):
        # none -> 0, planned_48h_notice -> 5, active_supervised -> 10, direct_excavation_hazard -> 15
        self.assertEqual(evaluate_third_party_activity("none"), 0)
        self.assertEqual(evaluate_third_party_activity("planned_48h_notice"), 5)
        self.assertEqual(evaluate_third_party_activity("active_supervised"), 10)
        self.assertEqual(evaluate_third_party_activity("direct_excavation_hazard"), 15)

    def test_rodent_history_rules(self):
        # 0 -> 0, 1 -> 3, 2-3 -> 6, 4+ -> 10
        self.assertEqual(evaluate_rodent_history(0), 0)
        self.assertEqual(evaluate_rodent_history(1), 3)
        self.assertEqual(evaluate_rodent_history(2), 6)
        self.assertEqual(evaluate_rodent_history(3), 6)
        self.assertEqual(evaluate_rodent_history(4), 10)
        self.assertEqual(evaluate_rodent_history(9), 10)

    def test_public_consequence_rules(self):
        # low-density -> 2, residential -> 5, dense residential -> 7, sensitive -> 10
        self.assertEqual(evaluate_public_consequence("low_density"), 2)
        self.assertEqual(evaluate_public_consequence("residential"), 5)
        self.assertEqual(evaluate_public_consequence("dense_residential"), 7)
        self.assertEqual(evaluate_public_consequence("sensitive_hospital_school"), 10)

    def test_tier_classification(self):
        self.assertEqual(classify_tier(0), "LOW")
        self.assertEqual(classify_tier(39), "LOW")
        self.assertEqual(classify_tier(40), "MEDIUM")
        self.assertEqual(classify_tier(69), "MEDIUM")
        self.assertEqual(classify_tier(70), "HIGH")
        self.assertEqual(classify_tier(84), "HIGH")
        self.assertEqual(classify_tier(85), "CRITICAL")
        self.assertEqual(classify_tier(100), "CRITICAL")

    def test_custom_weights_slider_recompute(self):
        """Test recalculating score when user moves weights via sliders."""
        base_data = {
            "segment_id": "P-101",
            "material": "pe_distribution",
            "previous_incidents": 1,
            "days_since_survey": 6,
            "target_survey_cycle": 12,
            "third_party_activity": "none",
            "rodent_incidents": 1,
            "area_type": "residential",
        }
        # With default weights (25, 20, 20, 15, 10, 10):
        # prev: (10/25)*25 = 10
        # pe: (15/20)*20 = 15
        # days: (10/20)*20 = 10
        # third_party: (0/15)*15 = 0
        # rodent: (3/10)*10 = 3
        # consequence: (5/10)*10 = 5
        # sum = 10 + 15 + 10 + 0 + 3 + 5 = 43 (MEDIUM)
        res_default = calculate_priority(base_data)
        self.assertEqual(res_default["score"], 43)
        self.assertEqual(res_default["tier"], "MEDIUM")

        # Now suppose third party weight slider moved up, or previous incidents moved down
        custom = {
            "previous_incidents": 10.0,
            "pe_vulnerability": 20.0,
            "days_since_survey": 20.0,
            "third_party_activity": 15.0,
            "rodent_history": 10.0,
            "public_consequence": 10.0,
        }
        # prev: (10/25)*10 = 4.0
        # rest unchanged -> total = 4 + 15 + 10 + 0 + 3 + 5 = 37 (LOW)
        res_custom = calculate_priority(base_data, custom_weights=custom)
        self.assertEqual(res_custom["score"], 37)
        self.assertEqual(res_custom["tier"], "LOW")

    def test_monsoon_mode_modifier(self):
        """Test seasonal monsoon multiplier on PE vulnerability."""
        pe_segment = {
            "segment_id": "P-103",
            "material": "pe_distribution",
            "previous_incidents": 0,
            "days_since_survey": 0,
            "third_party_activity": "none",
            "rodent_incidents": 0,
            "area_type": "residential",
        }
        # Normal mode: PE distribution raw vulnerability = 15
        normal_res = calculate_priority(pe_segment, monsoon_mode=False)
        self.assertEqual(normal_res["factors"]["pe_vulnerability"], 15)

        # Monsoon mode: PE distribution gets 1.25x -> 15 * 1.25 = 18.75 -> round to 18.8
        monsoon_res = calculate_priority(pe_segment, monsoon_mode=True)
        self.assertGreater(monsoon_res["factors"]["pe_vulnerability"], 15)
        self.assertEqual(monsoon_res["factors"]["pe_vulnerability"], 18.8)


if __name__ == "__main__":
    unittest.main()
