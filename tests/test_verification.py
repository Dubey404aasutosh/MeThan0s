"""
Unit Tests for METHANOS — Anomaly Verification & Closed-Loop Feedback (Person 2 - Phase 2)
Validates verification state machine, leak confirmation, repair feedback, and metrics.
"""

import unittest
from confidence_engine.verification import (
    VerificationStore,
    create_verification_ticket,
    verify_field_anomaly,
    complete_repair_and_feedback,
    get_verification_metrics,
    STATUS_OBSERVED,
    STATUS_RE_SURVEY_QUEUED,
    STATUS_FIELD_VERIFY_PENDING,
    STATUS_CONFIRMED_LEAK,
    STATUS_FALSE_ALARM,
    STATUS_REPAIRED,
)
from confidence_engine.surveys import HIGH_CONFIDENCE_SURVEY, LOW_CONFIDENCE_SURVEY
from priority_engine.dataset import SegmentRepository


class TestVerificationWorkflow(unittest.TestCase):
    def setUp(self):
        self.store = VerificationStore()
        self.store.reset()
        self.repo = SegmentRepository()
        self.repo.reset()

    def test_create_ticket_high_confidence_accepted(self):
        """Accepted high-confidence survey with CH4 anomaly advances to FIELD_VERIFY_PENDING."""
        ticket = create_verification_ticket(HIGH_CONFIDENCE_SURVEY, store=self.store)

        self.assertEqual(ticket["survey_id"], "S-2101")
        self.assertEqual(ticket["segment_id"], "P-104")
        self.assertEqual(ticket["status"], STATUS_FIELD_VERIFY_PENDING)
        self.assertEqual(ticket["qc_decision"], "ACCEPT")
        self.assertEqual(ticket["confidence_score"], 100)
        self.assertIn("Field Patroller Dispatched", ticket["assigned_technician"])

    def test_create_ticket_low_confidence_resurvey(self):
        """Rejected low-confidence survey transitions directly to RE_SURVEY_QUEUED."""
        ticket = create_verification_ticket(LOW_CONFIDENCE_SURVEY, store=self.store)

        self.assertEqual(ticket["survey_id"], "S-2201")
        self.assertEqual(ticket["segment_id"], "P-118")
        self.assertEqual(ticket["status"], STATUS_RE_SURVEY_QUEUED)
        self.assertEqual(ticket["qc_decision"], "RE-SURVEY")
        self.assertIsNone(ticket["assigned_technician"])

    def test_verify_anomaly_confirmed_leak(self):
        """Field technician confirms leak on site -> CONFIRMED_LEAK."""
        ticket = self.store.get_by_id("VER-701")
        self.assertEqual(ticket["status"], STATUS_FIELD_VERIFY_PENDING)

        res = verify_field_anomaly("VER-701", outcome="leak", technician_notes="Pinhole leak at PE riser", store=self.store)
        self.assertEqual(res["status"], "VERIFICATION_RECORDED")
        self.assertEqual(res["ticket"]["status"], STATUS_CONFIRMED_LEAK)
        self.assertTrue(res["ticket"]["confirmed_leak"])
        self.assertIsNotNone(res["ticket"]["verified_at"])

    def test_verify_anomaly_false_alarm(self):
        """Field technician confirms false alarm (e.g. sewer gas) -> FALSE_ALARM."""
        ticket = self.store.get_by_id("VER-701")
        res = verify_field_anomaly("VER-701", outcome="false_alarm", technician_notes="Rotten organic matter in stormwater drain", store=self.store)

        self.assertEqual(res["ticket"]["status"], STATUS_FALSE_ALARM)
        self.assertFalse(res["ticket"]["confirmed_leak"])

    def test_closed_loop_repair_and_priority_recalculation(self):
        """
        Validates closed loop feedback (PRD §8B & Person 2 Deliverables):
        1. Complete repair on confirmed leak
        2. previous_incidents increments by 1
        3. days_since_survey resets to 0
        4. Priority score updates
        """
        # VER-703 is pre-seeded on P-105 with status CONFIRMED_LEAK
        ticket = self.store.get_by_id("VER-703")
        self.assertEqual(ticket["status"], STATUS_CONFIRMED_LEAK)
        self.assertEqual(ticket["segment_id"], "P-105")

        seg_before = self.repo.get_scored_segment("P-105")
        prev_incidents_before = seg_before["previous_incidents"]
        days_before = seg_before["days_since_survey"]

        res = complete_repair_and_feedback(
            "VER-703",
            repair_notes="Electrofusion sleeve installed and leak bubble test passed.",
            store=self.store,
            repo=self.repo,
        )

        self.assertEqual(res["status"], "REPAIR_COMPLETED_CLOSED_LOOP_UPDATED")
        self.assertEqual(res["ticket"]["status"], STATUS_REPAIRED)
        self.assertTrue(res["ticket"]["history_updated"])

        seg_after = self.repo.get_scored_segment("P-105")
        # previous_incidents must have increased
        self.assertEqual(seg_after["previous_incidents"], prev_incidents_before + 1)
        # days_since_survey must be reset to 0
        self.assertEqual(seg_after["days_since_survey"], 0)
        self.assertEqual(seg_after["factors"]["days_since_survey"], 0.0)

    def test_metrics_calculation(self):
        """Verifies calculation of survey quality and false-alarm analytics."""
        metrics = get_verification_metrics(store=self.store)

        self.assertEqual(metrics["total_tickets"], 4)
        self.assertEqual(metrics["re_survey_queued"], 1)
        self.assertEqual(metrics["pending_verification"], 1)
        self.assertEqual(metrics["confirmed_leaks"], 1)
        self.assertEqual(metrics["false_alarms"], 1)
        self.assertEqual(metrics["total_verified"], 2)
        self.assertEqual(metrics["false_alarm_rate_pct"], 50.0)
        self.assertEqual(metrics["leak_confirmation_rate_pct"], 50.0)

    def test_invalid_transitions(self):
        """Prevents illegal state transitions (e.g. repairing ticket not in CONFIRMED_LEAK)."""
        with self.assertRaises(ValueError):
            # VER-702 is RE_SURVEY_QUEUED, cannot verify
            verify_field_anomaly("VER-702", outcome="leak", store=self.store)

        with self.assertRaises(ValueError):
            # VER-701 is pending verification, cannot repair before leak is confirmed
            complete_repair_and_feedback("VER-701", store=self.store, repo=self.repo)


if __name__ == "__main__":
    unittest.main()
