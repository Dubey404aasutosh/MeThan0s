"""
Unit tests for Person 1 Synthetic GIS Dataset.
Verifies dataset integrity, GIS attributes, and tier distributions.
"""

import sys
import os
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from priority_engine.dataset import SegmentRepository, RAW_SEGMENTS


class TestSegmentDataset(unittest.TestCase):

    def setUp(self):
        self.repo = SegmentRepository()

    def test_dataset_size(self):
        self.assertEqual(len(RAW_SEGMENTS), 12)

    def test_p104_exists_and_scores_85(self):
        p104 = self.repo.get_scored_segment("P-104")
        self.assertIsNotNone(p104)
        self.assertEqual(p104["score"], 85)
        self.assertEqual(p104["tier"], "CRITICAL")
        self.assertEqual(p104["depth_meters"], 0.8)
        self.assertEqual(p104["operating_pressure_bar"], 0.1)

    def test_tier_distribution_spread(self):
        all_segments = self.repo.get_all_scored_segments()
        tiers = [s["tier"] for s in all_segments]

        # Verify all 4 tiers are represented in the dataset
        self.assertIn("LOW", tiers)
        self.assertIn("MEDIUM", tiers)
        self.assertIn("HIGH", tiers)
        self.assertIn("CRITICAL", tiers)

        # Count per tier
        low_count = tiers.count("LOW")
        med_count = tiers.count("MEDIUM")
        high_count = tiers.count("HIGH")
        crit_count = tiers.count("CRITICAL")

        self.assertGreaterEqual(low_count, 2)
        self.assertGreaterEqual(med_count, 3)
        self.assertGreaterEqual(high_count, 2)
        self.assertGreaterEqual(crit_count, 2)

    def test_gis_contract_attributes(self):
        all_segments = self.repo.get_all_scored_segments()
        required_keys = [
            "segment_id", "score", "tier", "material",
            "depth_meters", "operating_pressure_bar",
            "third_party_activity", "factors", "location", "polyline"
        ]
        for seg in all_segments:
            for k in required_keys:
                self.assertIn(k, seg, f"Missing key {k} in segment {seg.get('segment_id')}")

            # Verify GPS coordinates
            loc = seg["location"]
            self.assertIn("lat", loc)
            self.assertIn("lng", loc)
            self.assertIsInstance(loc["lat"], (int, float))
            self.assertIsInstance(loc["lng"], (int, float))

            # Verify depth and pressure
            self.assertGreater(seg["depth_meters"], 0)
            self.assertGreaterEqual(seg["operating_pressure_bar"], 0)


if __name__ == "__main__":
    unittest.main()
