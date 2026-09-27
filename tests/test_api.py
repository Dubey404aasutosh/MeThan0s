"""
Integration tests for Person 1 FastAPI REST Endpoints.
Verifies HTTP API responses, serialization, CORS compliance, and state mutations.
"""

import sys
import os
import unittest
from fastapi.testclient import TestClient

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from priority_engine.api import app


class TestPriorityEngineAPI(unittest.TestCase):

    def setUp(self):
        self.client = TestClient(app)
        # Reset data before each test
        self.client.post("/api/reset")

    def test_health(self):
        response = self.client.get("/api/health")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["status"], "healthy")
        self.assertEqual(data["total_segments"], 12)

    def test_get_weights(self):
        response = self.client.get("/api/weights")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("default_weights", data)
        self.assertIn("factor_baselines", data)
        self.assertEqual(data["default_weights"]["previous_incidents"], 25.0)

    def test_get_segments(self):
        response = self.client.get("/api/segments")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["count"], 12)
        self.assertEqual(len(data["segments"]), 12)

        # Check first segment is sorted highest score
        first = data["segments"][0]
        self.assertGreaterEqual(first["score"], data["segments"][-1]["score"])

    def test_get_p104_detail(self):
        response = self.client.get("/api/segments/P-104")
        self.assertEqual(response.status_code, 200)
        seg = response.json()
        self.assertEqual(seg["segment_id"], "P-104")
        self.assertEqual(seg["score"], 85)
        self.assertEqual(seg["tier"], "CRITICAL")
        self.assertEqual(seg["material"], "pe_service_hotspot")
        self.assertEqual(seg["depth_meters"], 0.8)
        self.assertEqual(seg["operating_pressure_bar"], 0.1)

    def test_recalculate_custom_weights(self):
        # Scale third party weight down to 0
        custom = {
            "previous_incidents": 25.0,
            "pe_vulnerability": 20.0,
            "days_since_survey": 20.0,
            "third_party_activity": 0.0,
            "rodent_history": 10.0,
            "public_consequence": 10.0
        }
        response = self.client.post("/api/recalculate", json={"weights": custom})
        self.assertEqual(response.status_code, 200)
        data = response.json()

        # Find P-104 in recalculated list
        p104 = next(s for s in data["segments"] if s["segment_id"] == "P-104")
        # Previously 85, with third_party=0, should drop by 15 -> 70 (HIGH)
        self.assertEqual(p104["score"], 70)
        self.assertEqual(p104["tier"], "HIGH")

    def test_repair_endpoint(self):
        response = self.client.post("/api/segments/P-104/repair", json={"clear_hazard": True})
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["status"], "REPAIR_COMPLETED_HISTORY_UPDATED")
        self.assertEqual(data["segment"]["third_party_activity"], "none")
        self.assertEqual(data["segment"]["factors"]["days_since_survey"], 0)

    def test_excavation_status_endpoint(self):
        response = self.client.post(
            "/api/segments/P-101/excavation-status",
            json={"new_status": "planned_48h_notice"}
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["new_status"], "planned_48h_notice")
        self.assertEqual(data["segment"]["third_party_activity"], "planned_48h_notice")

    def test_emergency_incident_endpoint(self):
        response = self.client.post(
            "/api/segments/P-101/emergency-incident",
            json={"incident_type": "backhoe_pipeline_strike"}
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["status"], "CRITICAL_RESPONSE_TRIGGERED")
        self.assertEqual(data["segment"]["tier"], "CRITICAL")
        self.assertGreaterEqual(data["segment"]["score"], 95)


if __name__ == "__main__":
    unittest.main()
