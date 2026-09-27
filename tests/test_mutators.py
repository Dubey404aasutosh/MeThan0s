"""
Unit tests for Person 1 Closed-Loop Mutators (Integration with Person 2).
"""

import sys
import os
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from priority_engine.dataset import SegmentRepository
from priority_engine.mutators import (
    recalculate_after_repair,
    update_third_party_status,
    trigger_emergency_incident
)


class TestMutators(unittest.TestCase):

    def setUp(self):
        # Create a fresh isolated repository instance for each test
        self.repo = SegmentRepository()

    def test_recalculate_after_repair(self):
        # Initial P-104: 2 incidents, 9 days since survey, direct_excavation_hazard -> score 85
        initial = self.repo.get_scored_segment("P-104")
        self.assertEqual(initial["score"], 85)
        self.assertEqual(initial["factors"]["previous_incidents"], 18)

        # Execute repair
        result = recalculate_after_repair("P-104", repo=self.repo, clear_hazard=True)
        updated = result["segment"]

        # previous_incidents should increment to 3 -> factor score 25
        # days_since_survey resets to 0 -> factor score 0
        # third_party_activity cleared to "none" -> factor score 0
        # rodent_history: 10, pe_vulnerability: 20, public_consequence: 7
        # Expected new score = 25 + 20 + 0 + 0 + 10 + 7 = 62 (MEDIUM)
        self.assertEqual(updated["factors"]["previous_incidents"], 25)
        self.assertEqual(updated["factors"]["days_since_survey"], 0)
        self.assertEqual(updated["third_party_activity"], "none")
        self.assertEqual(updated["score"], 62)
        self.assertEqual(updated["tier"], "MEDIUM")

    def test_update_third_party_status(self):
        # P-101 has initial activity "none" -> score ~10
        p101_init = self.repo.get_scored_segment("P-101")
        self.assertEqual(p101_init["third_party_activity"], "none")

        # Update to planned_48h_notice
        res1 = update_third_party_status("P-101", "planned_48h_notice", repo=self.repo)
        self.assertEqual(res1["segment"]["third_party_activity"], "planned_48h_notice")
        self.assertEqual(res1["segment"]["factors"]["third_party_activity"], 5)

        # Update to active_supervised
        res2 = update_third_party_status("P-101", "active_supervised", repo=self.repo)
        self.assertEqual(res2["segment"]["third_party_activity"], "active_supervised")
        self.assertEqual(res2["segment"]["factors"]["third_party_activity"], 10)

    def test_trigger_emergency_incident(self):
        # P-102 has initial score ~23 (LOW)
        p102_init = self.repo.get_scored_segment("P-102")
        self.assertEqual(p102_init["tier"], "LOW")

        # Trigger emergency pipeline strike report
        res = trigger_emergency_incident("P-102", incident_type="contractor_breach_strike", repo=self.repo)
        self.assertEqual(res["status"], "CRITICAL_RESPONSE_TRIGGERED")
        self.assertEqual(res["segment"]["tier"], "CRITICAL")
        self.assertGreaterEqual(res["segment"]["score"], 95)
        self.assertEqual(res["segment"]["third_party_activity"], "direct_excavation_hazard")


if __name__ == "__main__":
    unittest.main()
