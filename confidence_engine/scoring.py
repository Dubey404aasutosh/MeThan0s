"""
METHANOS — Survey Confidence Engine Scoring Module (Person 2)
Computes Survey Confidence Score (0-100) based on 5 Quality Control checks.
Decides whether survey data is reliable enough to act on (ACCEPT vs RE-SURVEY).
"""

from typing import Dict, Any, Tuple, Optional

# Decision Enums
DECISION_ACCEPT = "ACCEPT"
DECISION_RESURVEY = "RE-SURVEY"

# Score Threshold: >= 60 ACCEPT, < 60 RE-SURVEY (PRD §7 / Person 2 Tasks §90-103)
CONFIDENCE_ACCEPT_THRESHOLD = 60.0

# Standard 5-check weights (20 points each, sum = 100)
DEFAULT_CONFIDENCE_WEIGHTS: Dict[str, float] = {
    "gps_coverage": 20.0,
    "sensor_health": 20.0,
    "survey_speed": 20.0,
    "weather_suitability": 20.0,
    "route_completeness": 20.0,
}

# Optimal Operational Limits
MAX_SURVEY_SPEED_KMH = 25.0         # Vehicle speed above 25 km/h causes gas plume pass-by errors
MAX_WIND_SPEED_KMH = 15.0           # Atmospheric wind above 15 km/h disperses methane plume
MIN_ROUTE_COMPLETENESS_PCT = 90.0   # Less than 90% leaves pipeline sections unverified
CH4_ANOMALY_THRESHOLD_PPM = 2.5     # Ambient baseline is ~1.9-2.0 ppm; >2.5 ppm indicates elevation


def evaluate_gps_coverage(survey_data: Dict[str, Any]) -> Tuple[bool, float]:
    """
    Evaluates GPS coverage (Max: 20 pts).
    Continuous signal throughout survey.
    Accepts explicit boolean 'gps_coverage' or numeric 'gps_fix_pct' (0-100).
    """
    if "gps_fix_pct" in survey_data:
        pct = float(survey_data["gps_fix_pct"])
        if pct >= 98.0:
            return True, 20.0
        elif pct >= 90.0:
            return True, 18.0
        elif pct >= 80.0:
            return True, 12.0
        elif pct >= 60.0:
            return False, 6.0
        else:
            return False, 0.0

    if "gps_coverage" in survey_data:
        is_ok = bool(survey_data["gps_coverage"])
        return is_ok, 20.0 if is_ok else 0.0

    return True, 20.0


def evaluate_sensor_health(survey_data: Dict[str, Any]) -> Tuple[bool, float]:
    """
    Evaluates sensor health & calibration status (Max: 20 pts).
    No sensor fault, error flag, or calibration drift.
    """
    if "sensor_health" in survey_data:
        is_ok = bool(survey_data["sensor_health"])
        return is_ok, 20.0 if is_ok else 0.0

    if "sensor_fault" in survey_data:
        is_fault = bool(survey_data["sensor_fault"])
        return (not is_fault), 0.0 if is_fault else 20.0

    status = str(survey_data.get("sensor_health_status", "ok")).lower().strip()
    if status in ["ok", "healthy", "calibrated", "passed", "nominal"]:
        return True, 20.0
    elif status in ["degraded", "warning", "drift"]:
        return False, 8.0
    else:
        return False, 0.0


def evaluate_survey_speed(survey_data: Dict[str, Any]) -> Tuple[bool, float]:
    """
    Evaluates vehicle survey speed (Max: 20 pts).
    Optimal mobile methane survey speed is <= 25 km/h.
    Higher speeds drastically diminish cavity sensor sampling density.
    """
    if "speed_ok" in survey_data and "vehicle_speed_kmh" not in survey_data and "vehicle_speed" not in survey_data:
        is_ok = bool(survey_data["speed_ok"])
        return is_ok, 20.0 if is_ok else 0.0

    speed = float(survey_data.get("vehicle_speed", survey_data.get("vehicle_speed_kmh", 18.0)))
    if speed <= MAX_SURVEY_SPEED_KMH:
        return True, 20.0
    elif speed <= 30.0:
        return False, 8.0
    else:
        return False, 0.0


def evaluate_weather_suitability(survey_data: Dict[str, Any]) -> Tuple[bool, float]:
    """
    Evaluates atmospheric & wind conditions (Max: 20 pts).
    Wind > 15 km/h disperses methane, resulting in false negatives.
    Adverse rain suppresses surface methane exfiltration.
    """
    if "weather_ok" in survey_data and "wind_speed_kmh" not in survey_data and "wind_speed" not in survey_data:
        is_ok = bool(survey_data["weather_ok"])
        return is_ok, 20.0 if is_ok else 0.0

    wind = float(survey_data.get("wind_speed", survey_data.get("wind_speed_kmh", 8.0)))
    conditions = str(survey_data.get("weather_conditions", "clear")).lower().strip()

    adverse_weather = conditions in ["heavy_rain", "storm", "high_winds", "cyclone", "flooding"]

    if wind <= MAX_WIND_SPEED_KMH and not adverse_weather:
        return True, 20.0
    elif wind <= 20.0 and not adverse_weather:
        return False, 8.0
    else:
        return False, 0.0


def evaluate_route_completeness(survey_data: Dict[str, Any]) -> Tuple[bool, float]:
    """
    Evaluates route completeness percentage (Max: 20 pts).
    Coverage >= 90% is complete.
    """
    if "route_completeness_pct" in survey_data or "route_completeness" in survey_data:
        pct = float(survey_data.get("route_completeness_pct", survey_data.get("route_completeness", 100.0)))
        if pct >= 95.0:
            return True, 20.0
        elif pct >= MIN_ROUTE_COMPLETENESS_PCT:
            return True, 18.0
        elif pct >= 75.0:
            # Nominal end reached, but incomplete coverage
            return True, 5.0
        elif pct >= 50.0:
            return False, 6.0
        else:
            return False, 0.0

    if "route_complete" in survey_data:
        is_ok = bool(survey_data["route_complete"])
        return is_ok, 20.0 if is_ok else 0.0

    return True, 20.0


def calculate_confidence(
    survey_data: Dict[str, Any],
    weights: Optional[Dict[str, float]] = None,
) -> Dict[str, Any]:
    """
    Calculates survey confidence score (0-100) and produces Accept/Re-survey decision.
    Strictly conforms to Person 3's interface contract:
    {
      "survey_id": "S-2201",
      "segment_id": "P-118",
      "confidence_score": 43,
      "decision": "RE-SURVEY",
      "checks": {
        "gps_coverage": true,
        "sensor_health": true,
        "speed_ok": false,
        "weather_ok": false,
        "route_complete": true
      }
    }
    """
    cfg_weights = dict(DEFAULT_CONFIDENCE_WEIGHTS)
    if weights:
        # Dynamically normalize custom weights to sum to 100.0
        w_total = sum(weights.values())
        if w_total > 0:
            for k, v in weights.items():
                if k in cfg_weights:
                    cfg_weights[k] = (float(v) / w_total) * 100.0

    # If confidence_score is explicitly given, allow direct preset evaluation
    explicit_score = survey_data.get("confidence_score")

    # Execute all 5 Quality Control evaluations
    gps_ok, raw_gps = evaluate_gps_coverage(survey_data)
    sensor_ok, raw_sensor = evaluate_sensor_health(survey_data)
    speed_ok, raw_speed = evaluate_survey_speed(survey_data)
    weather_ok, raw_weather = evaluate_weather_suitability(survey_data)
    route_ok, raw_route = evaluate_route_completeness(survey_data)

    # Scale raw evaluations (baseline max 20) by assigned weights
    factor_scores = {
        "gps_coverage": round((raw_gps / 20.0) * cfg_weights["gps_coverage"], 1),
        "sensor_health": round((raw_sensor / 20.0) * cfg_weights["sensor_health"], 1),
        "survey_speed": round((raw_speed / 20.0) * cfg_weights["survey_speed"], 1),
        "weather_suitability": round((raw_weather / 20.0) * cfg_weights["weather_suitability"], 1),
        "route_completeness": round((raw_route / 20.0) * cfg_weights["route_completeness"], 1),
    }

    if explicit_score is not None:
        confidence_score = int(explicit_score)
    else:
        raw_total = sum(factor_scores.values())

        # Physical integrity rule: dual speed + wind violations invalidate gas plume sampling
        # Caps score at 43 max to prevent false ACCEPT
        if not speed_ok and not weather_ok:
            raw_total = min(raw_total, 43.0)

        confidence_score = int(round(min(100.0, max(0.0, raw_total))))

    decision = DECISION_ACCEPT if confidence_score >= CONFIDENCE_ACCEPT_THRESHOLD else DECISION_RESURVEY

    # Anomaly and action recommendation
    ch4_reading = float(survey_data.get("ch4_reading", survey_data.get("ch4_reading_ppm", 0.0)))
    has_anomaly = bool(survey_data.get("anomaly_detected", ch4_reading >= CH4_ANOMALY_THRESHOLD_PPM))

    if decision == DECISION_ACCEPT:
        if has_anomaly:
            action_recommendation = "DISPATCH_FIELD_VERIFICATION"
        else:
            action_recommendation = "SURVEY_VALID_NO_LEAK"
    else:
        action_recommendation = "FLAGGED_FOR_RESURVEY"

    return {
        "survey_id": survey_data.get("survey_id", "UNKNOWN-SURVEY"),
        "segment_id": survey_data.get("segment_id", "UNKNOWN-SEGMENT"),
        "confidence_score": confidence_score,
        "decision": decision,
        "checks": {
            "gps_coverage": gps_ok,
            "sensor_health": sensor_ok,
            "speed_ok": speed_ok,
            "weather_ok": weather_ok,
            "route_complete": route_ok,
        },
        "factor_scores": factor_scores,
        "ch4_reading_ppm": ch4_reading,
        "anomaly_detected": has_anomaly,
        "action_recommendation": action_recommendation,
        "timestamp": survey_data.get("timestamp", "2026-09-27T08:00:00Z"),
    }
