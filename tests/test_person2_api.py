"""
Integration Tests for METHANOS — Person 2 REST API Endpoints
Validates confidence evaluation, verification tickets, 48-hour dig notices, and emergency incidents.
"""

import unittest
from fastapi.testclient import TestClient

from priority_engine.api import app
from priority_engine.dataset import global_repo
from confidence_engine.verification import global_verification_store
from confidence_engine.dig_prevention import global_dig_store
from confidence_engine.incidents import global_incident_store


class TestPerson2API(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)
        global_repo.reset()
        global_verification_store.reset()
        global_dig_store.reset()
        global_incident_store.reset()

    def test_get_confidence_weights_and_examples(self):
        """Verifies QC weights and instant demo benchmark pair."""
        resp = self.client.get("/api/confidence/weights")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(data["weights"]["gps_coverage"], 20.0)
        self.assertEqual(data["accept_threshold"], 60.0)

        # Demo benchmarks
        bench = self.client.get("/api/confidence/examples").json()
        self.assertEqual(bench["status"], "success")
        self.assertEqual(bench["high_confidence_example"]["confidence_score"], 100)
        self.assertEqual(bench["high_confidence_example"]["decision"], "ACCEPT")
        self.assertEqual(bench["low_confidence_example"]["confidence_score"], 43)
        self.assertEqual(bench["low_confidence_example"]["decision"], "RE-SURVEY")

    def test_list_and_evaluate_surveys(self):
        """Verifies survey listing and dynamic evaluation endpoint."""
        surveys_resp = self.client.get("/api/confidence/surveys")
        self.assertEqual(surveys_resp.status_code, 200)
        surveys = surveys_resp.json()["surveys"]
        self.assertGreaterEqual(len(surveys), 5)

        # Single lookup
        single = self.client.get("/api/confidence/surveys/S-2101").json()
        self.assertEqual(single["survey"]["segment_id"], "P-104")

        # Custom evaluation
        eval_resp = self.client.post("/api/confidence/evaluate", json={
            "survey_id": "S-CUSTOM-TEST",
            "gps_coverage": True,
            "sensor_health": True,
            "speed_ok": True,
            "weather_ok": True,
            "route_complete": True,
            "ch4_reading_ppm": 12.0
        })
        self.assertEqual(eval_resp.status_code, 200)
        res = eval_resp.json()["result"]
        self.assertEqual(res["confidence_score"], 100)
        self.assertEqual(res["decision"], "ACCEPT")
        self.assertTrue(res["anomaly_detected"])

    def test_verification_workflow_via_api(self):
        """Verifies ticket creation, ground verification, repair, and metrics."""
        # 1. Ingest survey into verification
        ingest_resp = self.client.post("/api/verification/tickets", json={
            "survey_id": "S-INGEST-1",
            "segment_id": "P-104",
            "gps_coverage": True,
            "sensor_health": True,
            "speed_ok": True,
            "weather_ok": True,
            "route_complete": True,
            "ch4_reading_ppm": 9.5
        })
        self.assertEqual(ingest_resp.status_code, 200)
        ticket_id = ingest_resp.json()["ticket"]["ticket_id"]

        # 2. Field technician confirms leak
        verify_resp = self.client.post(f"/api/verification/tickets/{ticket_id}/verify", json={
            "outcome": "leak",
            "technician_notes": "Acoustic leak detector confirms joint hiss"
        })
        self.assertEqual(verify_resp.status_code, 200)
        self.assertEqual(verify_resp.json()["data"]["ticket"]["status"], "CONFIRMED_LEAK")

        # 3. Complete repair and verify closed-loop priority score update
        repair_resp = self.client.post(f"/api/verification/tickets/{ticket_id}/repair", json={
            "repair_notes": "Compression clamp bolted, pressure test nominal"
        })
        self.assertEqual(repair_resp.status_code, 200)
        repair_data = repair_resp.json()["data"]
        self.assertEqual(repair_data["status"], "REPAIR_COMPLETED_CLOSED_LOOP_UPDATED")
        self.assertEqual(repair_data["ticket"]["status"], "REPAIRED")

        # 4. Check metrics
        metrics = self.client.get("/api/verification/metrics").json()["metrics"]
        self.assertGreaterEqual(metrics["confirmed_leaks"], 1)

    def test_dig_notices_workflow_via_api(self):
        """Verifies contractor ticket submission, monitor dispatch, map sharing, and completion."""
        # 1. List pre-seeded notices
        notices = self.client.get("/api/dig-notices").json()["notices"]
        self.assertGreaterEqual(len(notices), 3)

        # 2. Submit new advance notice
        sub_resp = self.client.post("/api/dig-notices", json={
            "notice_id": "DIG-API-TEST",
            "segment_id": "P-104",
            "contractor_name": "Airtel Underground Fiber",
            "notice_advance_hours": 64.0,
            "dig_depth_meters": 1.4,
            "proximity_buffer_m": 7.0,
        })
        self.assertEqual(sub_resp.status_code, 200)
        self.assertTrue(sub_resp.json()["notice"]["is_compliant_48h"])

        # 3. Dispatch monitor
        disp_resp = self.client.post("/api/dig-notices/DIG-API-TEST/dispatch-monitor", json={
            "monitor_name": "Patrol Officer A. Verma"
        })
        self.assertEqual(disp_resp.status_code, 200)
        self.assertEqual(disp_resp.json()["data"]["notice"]["status"], "MONITOR_DISPATCHED")

        # 4. Share safety blueprint map
        map_resp = self.client.post("/api/dig-notices/DIG-API-TEST/share-map", json={
            "contractor_email": "contractor@airtel.in"
        })
        self.assertEqual(map_resp.status_code, 200)
        self.assertTrue(map_resp.json()["data"]["notice"]["safety_map_shared"])

        # 5. Start supervised excavation
        start_resp = self.client.post("/api/dig-notices/DIG-API-TEST/start-dig")
        self.assertEqual(start_resp.status_code, 200)
        self.assertEqual(start_resp.json()["data"]["notice"]["status"], "ACTIVE_SUPERVISED")

        # 6. Complete excavation with zero leaks
        comp_resp = self.client.post("/api/dig-notices/DIG-API-TEST/complete")
        self.assertEqual(comp_resp.status_code, 200)
        self.assertEqual(comp_resp.json()["data"]["notice"]["status"], "COMPLETED_ZERO_LEAK")

    def test_emergency_incident_trigger_and_resolve_via_api(self):
        """
        Demo Highlight Test:
        Simulate 'Report Incident' button:
        Jumps segment immediately to CRITICAL (score >= 95, tier: CRITICAL).
        """
        # Report incident on P-101 (which starts as LOW tier, score ~10)
        seg_before = self.client.get("/api/segments/P-101").json()
        self.assertEqual(seg_before["tier"], "LOW")

        report_resp = self.client.post("/api/incidents/report", json={
            "segment_id": "P-101",
            "incident_type": "third_party_puncture",
            "reporter_name": "Delhi Jal Board Emergency Line",
            "notes": "JCB backhoe severed PE service pipe. Urgent gas cloud visible."
        })
        self.assertEqual(report_resp.status_code, 200)
        inc_data = report_resp.json()["data"]
        self.assertEqual(inc_data["status"], "CRITICAL_RESPONSE_TRIGGERED")
        self.assertEqual(inc_data["incident_type"], "third_party_puncture")
        self.assertEqual(inc_data["updated_segment"]["tier"], "CRITICAL")
        self.assertGreaterEqual(inc_data["updated_segment"]["score"], 95)

        # Verify segment API reflects the emergency critical status
        seg_after = self.client.get("/api/segments/P-101").json()
        self.assertEqual(seg_after["tier"], "CRITICAL")
        self.assertGreaterEqual(seg_after["score"], 95)

        # Resolve incident
        inc_id = inc_data["incident_id"]
        res_resp = self.client.post(f"/api/incidents/{inc_id}/resolve")
        self.assertEqual(res_resp.status_code, 200)
        self.assertEqual(res_resp.json()["data"]["status"], "INCIDENT_RESOLVED")


if __name__ == "__main__":
    unittest.main()
