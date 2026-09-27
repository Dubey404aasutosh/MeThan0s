"""
METHANOS — Survey Confidence Engine Sample Datasets (Person 2)
Provides standardized sample survey records, including benchmark High Confidence and Low Confidence examples for live demo.
"""

from typing import Dict, Any, List, Optional
from .scoring import calculate_confidence

# Concrete Benchmark 1: High Confidence Valid Survey (ACCEPT -> Field Verify)
HIGH_CONFIDENCE_SURVEY: Dict[str, Any] = {
    "survey_id": "S-2101",
    "segment_id": "P-104",
    "surveyor_team": "Team Alpha (Mobile Van #1)",
    "timestamp": "2026-09-27T07:45:00Z",
    "gps_coverage": True,
    "gps_fix_pct": 99.2,
    "sensor_health": True,
    "sensor_health_status": "calibrated",
    "speed_ok": True,
    "vehicle_speed_kmh": 16.5,
    "weather_ok": True,
    "wind_speed_kmh": 6.2,
    "weather_conditions": "clear",
    "route_complete": True,
    "route_completeness_pct": 98.5,
    "ch4_reading_ppm": 14.6,
    "anomaly_detected": True,
    "notes": "Strong elevated CH4 localized near valve pit on PE service line hotspot.",
}

# Concrete Benchmark 2: Low Confidence Rejected Survey (Speed & Wind Violations -> RE-SURVEY)
# Strictly mirrors Person 2 tasks §25-39:
# speed_ok: false, weather_ok: false -> score 40-43, decision: RE-SURVEY
LOW_CONFIDENCE_SURVEY: Dict[str, Any] = {
    "survey_id": "S-2201",
    "segment_id": "P-118",
    "surveyor_team": "Team Beta (Mobile Van #2)",
    "timestamp": "2026-09-27T09:15:00Z",
    "gps_coverage": True,
    "gps_fix_pct": 96.0,
    "sensor_health": True,
    "sensor_health_status": "ok",
    "speed_ok": False,
    "vehicle_speed_kmh": 36.8,  # Excessive speed over 25 km/h
    "weather_ok": False,
    "wind_speed_kmh": 26.5,     # High gusting wind over 15 km/h
    "weather_conditions": "gusty_winds",
    "route_complete": True,
    "route_completeness_pct": 94.0,
    "ch4_reading_ppm": 8.4,
    "anomaly_detected": True,
    "notes": "Elevated CH4 flagged but vehicle speed was 36.8 km/h with 26.5 km/h gusts; plume dispersed. Unreliable.",
}

# Full synthetic dataset of survey logs across segments
SAMPLE_SURVEYS: List[Dict[str, Any]] = [
    HIGH_CONFIDENCE_SURVEY,
    LOW_CONFIDENCE_SURVEY,
    {
        "survey_id": "S-2102",
        "segment_id": "P-101",
        "surveyor_team": "Team Alpha (Mobile Van #1)",
        "timestamp": "2026-09-26T14:30:00Z",
        "gps_coverage": True,
        "gps_fix_pct": 98.0,
        "sensor_health": True,
        "sensor_health_status": "ok",
        "speed_ok": True,
        "vehicle_speed_kmh": 18.0,
        "weather_ok": True,
        "wind_speed_kmh": 8.0,
        "weather_conditions": "clear",
        "route_complete": True,
        "route_completeness_pct": 100.0,
        "ch4_reading_ppm": 1.9,
        "anomaly_detected": False,
        "notes": "Baseline ambient CH4 level confirmed. No anomalies detected.",
    },
    {
        "survey_id": "S-2103",
        "segment_id": "P-108",
        "surveyor_team": "Team Gamma (Patrol Bike #3)",
        "timestamp": "2026-09-26T16:00:00Z",
        "gps_coverage": False,      # Poor satellite lock under flyover
        "gps_fix_pct": 58.0,
        "sensor_health": True,
        "sensor_health_status": "ok",
        "speed_ok": True,
        "vehicle_speed_kmh": 14.0,
        "weather_ok": True,
        "wind_speed_kmh": 11.0,
        "weather_conditions": "partly_cloudy",
        "route_complete": False,    # Construction blocked roadway
        "route_completeness_pct": 62.0,
        "ch4_reading_ppm": 4.1,
        "anomaly_detected": True,
        "notes": "GPS dropout under concrete flyover + blocked lane. Re-survey required.",
    },
    {
        "survey_id": "S-2104",
        "segment_id": "P-105",
        "surveyor_team": "Team Beta (Mobile Van #2)",
        "timestamp": "2026-09-27T06:10:00Z",
        "gps_coverage": True,
        "gps_fix_pct": 100.0,
        "sensor_health": True,
        "sensor_health_status": "calibrated",
        "speed_ok": True,
        "vehicle_speed_kmh": 15.2,
        "weather_ok": True,
        "wind_speed_kmh": 5.0,
        "weather_conditions": "clear",
        "route_complete": True,
        "route_completeness_pct": 99.0,
        "ch4_reading_ppm": 11.2,
        "anomaly_detected": True,
        "notes": "Significant CH4 reading in dense residential market corridor. High priority verification.",
    },
    {
        "survey_id": "S-2105",
        "segment_id": "P-102",
        "surveyor_team": "Team Gamma (Patrol Bike #3)",
        "timestamp": "2026-09-26T11:20:00Z",
        "gps_coverage": True,
        "gps_fix_pct": 97.5,
        "sensor_health": False,     # Optical sensor filter clogged / drift flag
        "sensor_health_status": "drift_warning",
        "speed_ok": True,
        "vehicle_speed_kmh": 17.5,
        "weather_ok": True,
        "wind_speed_kmh": 7.0,
        "weather_conditions": "clear",
        "route_complete": True,
        "route_completeness_pct": 95.0,
        "ch4_reading_ppm": 2.1,
        "anomaly_detected": False,
        "notes": "Sensor calibration drift warning triggered during run. Low confidence.",
    },
]


def get_sample_survey(survey_id: str) -> Optional[Dict[str, Any]]:
    """Retrieves raw sample survey record by ID."""
    for s in SAMPLE_SURVEYS:
        if s["survey_id"].upper() == survey_id.upper():
            return dict(s)
    return None


def get_all_sample_surveys(evaluated: bool = True) -> List[Dict[str, Any]]:
    """
    Returns all sample survey records.
    If evaluated is True, computes and merges confidence score, checks, and decisions.
    """
    results = []
    for s in SAMPLE_SURVEYS:
        item = dict(s)
        if evaluated:
            eval_res = calculate_confidence(item)
            item.update({
                "confidence_score": eval_res["confidence_score"],
                "decision": eval_res["decision"],
                "checks": eval_res["checks"],
                "factor_scores": eval_res["factor_scores"],
                "action_recommendation": eval_res["action_recommendation"],
            })
        results.append(item)
    return results
