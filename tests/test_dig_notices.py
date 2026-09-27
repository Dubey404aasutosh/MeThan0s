"""
Unit Tests for METHANOS — 48-Hour Pre-Excavation Early Warning Engine (Person 2 - Phase 3)
Validates contractor notice ingestion, 48-hour compliance, depth clashes, and control room actions.
"""

import unittest
from confidence_engine.dig_prevention import (
    DigNoticeStore,
    evaluate_and_submit_dig_notice,
    dispatch_on_site_monitor,
    share_safety_route_map,
    activate_supervised_dig,
    complete_zero_leak_dig,
    STATUS_PENDING_REVIEW,
    STATUS_MONITOR_DISPATCHED,
    STATUS_ACTIVE_SUPERVISED,
    STATUS_COMPLETED_ZERO_LEAK,
    STATUS_SHORT_NOTICE_VIOLATION,
)
from priority_engine.dataset import SegmentRepository


class TestDigEarlyWarningEngine(unittest.TestCase):
    def setUp(self):
        self.repo = SegmentRepository()
        self.repo.reset()
        self.store = DigNoticeStore(repo=self.repo)
        self.store.reset()

    def test_default_seeded_dig_notices(self):
        """Validates pre-seeded DIG-801 contract matching Person 2 §43-57."""
        notice = self.store.get_by_id("DIG-801")
        self.assertIsNotNone(notice)
        self.assertEqual(notice["segment_id"], "P-104")
        self.assertEqual(notice["notice_advance_hours"], 52.0)
        self.assertTrue(notice["is_compliant_48h"])
        self.assertEqual(notice["dig_depth_meters"], 1.5)
        self.assertEqual(notice["pipeline_depth_meters"], 0.8)
        self.assertTrue(notice["depth_clash_hazard"])
        self.assertEqual(notice["status"], STATUS_MONITOR_DISPATCHED)
        self.assertEqual(notice["assigned_monitor"], "Patrol Officer R. Sharma")
        self.assertTrue(notice["safety_map_shared"])

        # Check DIG-802 short-notice violation
        notice_short = self.store.get_by_id("DIG-802")
        self.assertFalse(notice_short["is_compliant_48h"])
        self.assertEqual(notice_short["status"], STATUS_SHORT_NOTICE_VIOLATION)

    def test_submit_compliant_notice_with_depth_clash(self):
        """Submitting a notice with 50 hours advance notice on P-102 (depth 1.4m) with dig depth 1.8m."""
        new_ticket = {
            "notice_id": "DIG-901",
            "segment_id": "P-102",
            "contractor_name": "Delhi Power Grid Trenching",
            "notice_advance_hours": 50.0,
            "dig_depth_meters": 1.8,
            "proximity_buffer_m": 5.0,
        }
        res = evaluate_and_submit_dig_notice(new_ticket, store=self.store, repo=self.repo)

        self.assertEqual(res["notice_id"], "DIG-901")
        self.assertTrue(res["is_compliant_48h"])
        self.assertEqual(res["pipeline_depth_meters"], 1.4)
        self.assertTrue(res["depth_clash_hazard"])
        self.assertEqual(res["status"], STATUS_PENDING_REVIEW)
        self.assertEqual(res["alert_level"], "HIGH_DEPTH_CLASH_WARNING")

    def test_submit_short_notice_violation(self):
        """Submitting notice with < 48 hours notice triggers SHORT_NOTICE_VIOLATION alert."""
        new_ticket = {
            "notice_id": "DIG-902",
            "segment_id": "P-101",
            "contractor_name": "Urgent Drainage Excavator",
            "notice_advance_hours": 12.0,  # < 48h
            "dig_depth_meters": 1.0,
            "proximity_buffer_m": 8.0,
        }
        res = evaluate_and_submit_dig_notice(new_ticket, store=self.store, repo=self.repo)

        self.assertFalse(res["is_compliant_48h"])
        self.assertEqual(res["status"], STATUS_SHORT_NOTICE_VIOLATION)
        self.assertEqual(res["alert_level"], "URGENT_UNAUTHORIZED_EXCAVATION_RISK")

    def test_dispatch_monitor_and_priority_engine_sync(self):
        """
        Dispatching on-site monitor:
        1. Updates notice status to MONITOR_DISPATCHED
        2. Assigns monitor name
        3. Updates segment in Priority Engine: third_party_activity = 'planned_48h_notice'
        """
        # Create a pending notice on P-103
        new_ticket = {
            "notice_id": "DIG-903",
            "segment_id": "P-103",
            "contractor_name": "Jal Board Water Pipeline",
            "notice_advance_hours": 55.0,
            "dig_depth_meters": 1.2,
        }
        evaluate_and_submit_dig_notice(new_ticket, store=self.store, repo=self.repo)

        res = dispatch_on_site_monitor(
            "DIG-903",
            monitor_name="Field Supervisor K. Mehta",
            store=self.store,
            repo=self.repo
        )

        self.assertEqual(res["status"], "MONITOR_DISPATCHED")
        self.assertEqual(res["notice"]["status"], STATUS_MONITOR_DISPATCHED)
        self.assertEqual(res["notice"]["assigned_monitor"], "Field Supervisor K. Mehta")

        # Verify segment was updated in Priority Engine
        seg = self.repo.get_scored_segment("P-103")
        self.assertEqual(seg["third_party_activity"], "planned_48h_notice")
        self.assertEqual(seg["factors"]["third_party_activity"], 5.0)

    def test_share_safety_map_action(self):
        """Sharing pipeline route map sets safety_map_shared to True and returns blueprint URL."""
        res = share_safety_route_map("DIG-802", contractor_email="super@rapidroad.com", store=self.store)

        self.assertEqual(res["status"], "SAFETY_MAP_DISPATCHED")
        self.assertEqual(res["recipient"], "super@rapidroad.com")
        self.assertTrue(res["notice"]["safety_map_shared"])
        self.assertIn("/map-blueprint", res["blueprint_url"])

    def test_full_excavation_lifecycle(self):
        """
        Full lifecycle:
        Pending -> Dispatch Monitor ('planned_48h_notice') ->
        Dig Day Supervised ('active_supervised') -> Complete ('none')
        """
        notice = evaluate_and_submit_dig_notice(
            {"notice_id": "DIG-904", "segment_id": "P-105", "notice_advance_hours": 60.0},
            store=self.store,
            repo=self.repo
        )

        # 1. Dispatch Monitor
        dispatch_on_site_monitor("DIG-904", "Monitor A", store=self.store, repo=self.repo)
        seg_1 = self.repo.get_scored_segment("P-105")
        self.assertEqual(seg_1["third_party_activity"], "planned_48h_notice")

        # 2. Shift to Active Supervised on Dig Day
        res_active = activate_supervised_dig("DIG-904", store=self.store, repo=self.repo)
        self.assertEqual(res_active["notice"]["status"], STATUS_ACTIVE_SUPERVISED)
        seg_2 = self.repo.get_scored_segment("P-105")
        self.assertEqual(seg_2["third_party_activity"], "active_supervised")
        self.assertEqual(seg_2["factors"]["third_party_activity"], 10.0)

        # 3. Complete excavation safely (Zero-leak clearance)
        res_done = complete_zero_leak_dig("DIG-904", store=self.store, repo=self.repo)
        self.assertEqual(res_done["notice"]["status"], STATUS_COMPLETED_ZERO_LEAK)
        seg_3 = self.repo.get_scored_segment("P-105")
        self.assertEqual(seg_3["third_party_activity"], "none")
        self.assertEqual(seg_3["factors"]["third_party_activity"], 0.0)


if __name__ == "__main__":
    unittest.main()
