"""
METHANOS — Synthetic GIS Segment Dataset (Person 1)
Contains 12 calibrated pipeline segments across an urban CGD network with GIS attributes
and a balanced distribution across all priority tiers (LOW, MEDIUM, HIGH, CRITICAL).
"""

from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta, timezone
from .scoring import calculate_priority, DEFAULT_WEIGHTS

# Base reference date for calculating relative days_since_survey
BASE_DATE = datetime.now(timezone.utc)

def _date_str(days_ago: int) -> str:
    return (BASE_DATE - timedelta(days=days_ago)).strftime("%Y-%m-%d")

RAW_SEGMENTS: List[Dict[str, Any]] = [
    {
        "segment_id": "P-101",
        "name": "Barakhamba Steel Transmission Main",
        "material": "steel_main",
        "depth_meters": 1.6,
        "operating_pressure_bar": 19.0,
        "previous_incidents": 0,
        "last_survey_date": _date_str(2),
        "days_since_survey": 2,
        "target_survey_cycle": 12,
        "third_party_activity": "none",
        "rodent_incidents": 0,
        "area_type": "low_density",
        "location": {"lat": 28.6295, "lng": 77.2285},
        "polyline": [
            [28.6280, 77.2260],
            [28.6295, 77.2285],
            [28.6310, 77.2310]
        ]
    },
    {
        "segment_id": "P-102",
        "name": "Lodhi Road Feeder Main",
        "material": "steel_main",
        "depth_meters": 1.4,
        "operating_pressure_bar": 16.0,
        "previous_incidents": 0,
        "last_survey_date": _date_str(8),
        "days_since_survey": 8,
        "target_survey_cycle": 12,
        "third_party_activity": "none",
        "rodent_incidents": 0,
        "area_type": "residential",
        "location": {"lat": 28.5910, "lng": 77.2220},
        "polyline": [
            [28.5895, 77.2195],
            [28.5910, 77.2220],
            [28.5925, 77.2245]
        ]
    },
    {
        "segment_id": "P-103",
        "name": "Mayur Vihar Phase 1 PE Line",
        "material": "pe_distribution",
        "depth_meters": 1.1,
        "operating_pressure_bar": 4.0,
        "previous_incidents": 1,
        "last_survey_date": _date_str(5),
        "days_since_survey": 5,
        "target_survey_cycle": 12,
        "third_party_activity": "none",
        "rodent_incidents": 1,
        "area_type": "residential",
        "location": {"lat": 28.6090, "lng": 77.2950},
        "polyline": [
            [28.6075, 77.2930],
            [28.6090, 77.2950],
            [28.6105, 77.2970]
        ]
    },
    {
        # BENCHMARK SEGMENT P-104 (PRD Reference: exact 85 / CRITICAL)
        "segment_id": "P-104",
        "name": "Chandni Chowk Market Service Line",
        "material": "pe_service_hotspot",
        "depth_meters": 0.8,
        "operating_pressure_bar": 0.1,
        "previous_incidents": 2,
        "last_survey_date": _date_str(9),
        "days_since_survey": 9,
        "target_survey_cycle": 12,
        "third_party_activity": "direct_excavation_hazard",
        "rodent_incidents": 4,
        "area_type": "dense_residential",
        "location": {"lat": 28.6506, "lng": 77.2303},
        "polyline": [
            [28.6490, 77.2280],
            [28.6506, 77.2303],
            [28.6520, 77.2325]
        ]
    },
    {
        "segment_id": "P-105",
        "name": "Saket Commercial Hub Feeder",
        "material": "pe_distribution",
        "depth_meters": 1.2,
        "operating_pressure_bar": 4.0,
        "previous_incidents": 1,
        "last_survey_date": _date_str(10),
        "days_since_survey": 10,
        "target_survey_cycle": 12,
        "third_party_activity": "planned_48h_notice",
        "rodent_incidents": 1,
        "area_type": "residential",
        "location": {"lat": 28.5244, "lng": 77.2167},
        "polyline": [
            [28.5230, 77.2145],
            [28.5244, 77.2167],
            [28.5260, 77.2190]
        ]
    },
    {
        "segment_id": "P-106",
        "name": "Karol Bagh High-Density PE Grid",
        "material": "pe_distribution",
        "depth_meters": 1.0,
        "operating_pressure_bar": 4.0,
        "previous_incidents": 1,
        "last_survey_date": _date_str(12),
        "days_since_survey": 12,
        "target_survey_cycle": 12,
        "third_party_activity": "planned_48h_notice",
        "rodent_incidents": 2,
        "area_type": "dense_residential",
        "location": {"lat": 28.6520, "lng": 77.1900},
        "polyline": [
            [28.6505, 77.1880],
            [28.6520, 77.1900],
            [28.6535, 77.1920]
        ]
    },
    {
        "segment_id": "P-107",
        "name": "AIIMS Medical Enclave Service Feeder",
        "material": "pe_distribution",
        "depth_meters": 1.0,
        "operating_pressure_bar": 4.0,
        "previous_incidents": 2,
        "last_survey_date": _date_str(11),
        "days_since_survey": 11,
        "target_survey_cycle": 12,
        "third_party_activity": "planned_48h_notice",
        "rodent_incidents": 2,
        "area_type": "sensitive(school/hospital/market)",
        "location": {"lat": 28.5672, "lng": 77.2100},
        "polyline": [
            [28.5655, 77.2080],
            [28.5672, 77.2100],
            [28.5690, 77.2120]
        ]
    },
    {
        "segment_id": "P-108",
        "name": "Lajpat Nagar Central Market PE Branch",
        "material": "pe_service_hotspot",
        "depth_meters": 0.7,
        "operating_pressure_bar": 0.1,
        "previous_incidents": 1,
        "last_survey_date": _date_str(14),
        "days_since_survey": 14,
        "target_survey_cycle": 12,
        "third_party_activity": "active_supervised",
        "rodent_incidents": 3,
        "area_type": "dense_residential",
        "location": {"lat": 28.5700, "lng": 77.2400},
        "polyline": [
            [28.5685, 77.2380],
            [28.5700, 77.2400],
            [28.5715, 77.2420]
        ]
    },
    {
        "segment_id": "P-109",
        "name": "Okhla Industrial Area PE Sector",
        "material": "pe_distribution",
        "depth_meters": 0.9,
        "operating_pressure_bar": 4.0,
        "previous_incidents": 2,
        "last_survey_date": _date_str(13),
        "days_since_survey": 13,
        "target_survey_cycle": 12,
        "third_party_activity": "active_supervised",
        "rodent_incidents": 2,
        "area_type": "dense_residential",
        "location": {"lat": 28.5355, "lng": 77.2750},
        "polyline": [
            [28.5340, 77.2730],
            [28.5355, 77.2750],
            [28.5370, 77.2770]
        ]
    },
    {
        "segment_id": "P-110",
        "name": "Rohini Sector 14 School Zone Service Line",
        "material": "pe_service_hotspot",
        "depth_meters": 0.6,
        "operating_pressure_bar": 0.1,
        "previous_incidents": 2,
        "last_survey_date": _date_str(12),
        "days_since_survey": 12,
        "target_survey_cycle": 12,
        "third_party_activity": "active_supervised",
        "rodent_incidents": 4,
        "area_type": "sensitive(school/hospital/market)",
        "location": {"lat": 28.7150, "lng": 77.1200},
        "polyline": [
            [28.7135, 77.1180],
            [28.7150, 77.1200],
            [28.7165, 77.1220]
        ]
    },
    {
        "segment_id": "P-111",
        "name": "Dwarka Sector 6 PE Feeder",
        "material": "pe_distribution",
        "depth_meters": 1.2,
        "operating_pressure_bar": 4.0,
        "previous_incidents": 0,
        "last_survey_date": _date_str(4),
        "days_since_survey": 4,
        "target_survey_cycle": 12,
        "third_party_activity": "none",
        "rodent_incidents": 0,
        "area_type": "residential",
        "location": {"lat": 28.5921, "lng": 77.0650},
        "polyline": [
            [28.5905, 77.0630],
            [28.5921, 77.0650],
            [28.5940, 77.0670]
        ]
    },
    {
        "segment_id": "P-112",
        "name": "Hauz Khas Village PE Hotspot",
        "material": "pe_service_hotspot",
        "depth_meters": 0.75,
        "operating_pressure_bar": 0.1,
        "previous_incidents": 1,
        "last_survey_date": _date_str(7),
        "days_since_survey": 7,
        "target_survey_cycle": 12,
        "third_party_activity": "planned_48h_notice",
        "rodent_incidents": 2,
        "area_type": "dense_residential",
        "location": {"lat": 28.5494, "lng": 77.1950},
        "polyline": [
            [28.5480, 77.1930],
            [28.5494, 77.1950],
            [28.5510, 77.1970]
        ]
    }
]


class SegmentRepository:
    """
    In-memory stateful repository for managing pipeline segments,
    priority score computation, and live state mutations.
    """
    def __init__(self, segments: Optional[List[Dict[str, Any]]] = None):
        self.reset(segments)

    def reset(self, segments: Optional[List[Dict[str, Any]]] = None):
        source = segments if segments is not None else RAW_SEGMENTS
        self._segments: Dict[str, Dict[str, Any]] = {
            s["segment_id"]: dict(s) for s in source
        }

    def get_raw_segment(self, segment_id: str) -> Optional[Dict[str, Any]]:
        return self._segments.get(segment_id)

    def get_all_scored_segments(
        self,
        custom_weights: Optional[Dict[str, float]] = None,
        sort_by_priority: bool = True,
        monsoon_mode: bool = False
    ) -> List[Dict[str, Any]]:
        """Returns all segments evaluated with priority scores and factors."""
        results = []
        for raw in self._segments.values():
            scored = calculate_priority(raw, custom_weights=custom_weights, monsoon_mode=monsoon_mode)
            # Retain descriptive fields for frontend display
            scored["name"] = raw.get("name", raw["segment_id"])
            scored["polyline"] = raw.get("polyline", [])
            scored["last_survey_date"] = raw.get("last_survey_date", "")
            scored["days_since_survey"] = raw.get("days_since_survey", 0)
            scored["target_survey_cycle"] = raw.get("target_survey_cycle", 12)
            scored["rodent_incidents"] = raw.get("rodent_incidents", 0)
            scored["previous_incidents"] = raw.get("previous_incidents", 0)
            scored["area_type"] = raw.get("area_type", "residential")
            scored["monsoon_mode"] = monsoon_mode
            results.append(scored)

        if sort_by_priority:
            results.sort(key=lambda s: s["score"], reverse=True)

        return results

    def get_scored_segment(
        self,
        segment_id: str,
        custom_weights: Optional[Dict[str, float]] = None,
        monsoon_mode: bool = False
    ) -> Optional[Dict[str, Any]]:
        raw = self.get_raw_segment(segment_id)
        if not raw:
            return None
        scored = calculate_priority(raw, custom_weights=custom_weights, monsoon_mode=monsoon_mode)
        scored["name"] = raw.get("name", raw["segment_id"])
        scored["polyline"] = raw.get("polyline", [])
        scored["last_survey_date"] = raw.get("last_survey_date", "")
        scored["days_since_survey"] = raw.get("days_since_survey", 0)
        scored["target_survey_cycle"] = raw.get("target_survey_cycle", 12)
        scored["rodent_incidents"] = raw.get("rodent_incidents", 0)
        scored["previous_incidents"] = raw.get("previous_incidents", 0)
        scored["area_type"] = raw.get("area_type", "residential")
        scored["monsoon_mode"] = monsoon_mode
        return scored

    def update_segment_field(self, segment_id: str, field: str, value: Any) -> Optional[Dict[str, Any]]:
        if segment_id not in self._segments:
            return None
        self._segments[segment_id][field] = value
        return self._segments[segment_id]


# Global singleton repository
global_repo = SegmentRepository()
