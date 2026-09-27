"""
METHANOS — Priority Engine Scoring Module (Person 1)
Calculates Survey Priority Score (0-100) based on PNGRB CGD Risk Factors.
"""

from typing import Dict, Any, Tuple, Optional

# Default factor weight configuration (Sums to 100)
DEFAULT_WEIGHTS: Dict[str, float] = {
    "previous_incidents": 25.0,
    "pe_vulnerability": 20.0,
    "days_since_survey": 20.0,
    "third_party_activity": 15.0,
    "rodent_history": 10.0,
    "public_consequence": 10.0,
}

# Baseline max values used to normalize raw factor ratios [0.0 - 1.0]
FACTOR_BASELINES: Dict[str, float] = {
    "previous_incidents": 25.0,
    "pe_vulnerability": 20.0,
    "days_since_survey": 20.0,
    "third_party_activity": 15.0,
    "rodent_history": 10.0,
    "public_consequence": 10.0,
}


def evaluate_previous_incidents(incidents_count: int) -> float:
    """
    Previous incident history: max 25
    0 incidents -> 0
    1 incident  -> 10
    2 incidents -> 18
    3+ incidents -> 25
    """
    if incidents_count <= 0:
        return 0.0
    elif incidents_count == 1:
        return 10.0
    elif incidents_count == 2:
        return 18.0
    else:
        return 25.0


def evaluate_pe_vulnerability(material: str) -> float:
    """
    PE / service-line vulnerability: max 20
    steel_main -> 5
    pe_distribution -> 15
    pe_service_hotspot -> 20
    """
    mat = (material or "").strip().lower()
    if mat in ["steel_main", "steel main", "steel"]:
        return 5.0
    elif mat in ["pe_distribution", "pe distribution", "pe_dist"]:
        return 15.0
    elif mat in ["pe_service_hotspot", "pe service hotspot", "pe_service", "pe hotspot"]:
        return 20.0
    # Safe fallback
    return 10.0


def evaluate_days_since_survey(days_since: int, target_cycle: int = 12) -> float:
    """
    Days since last survey: max 20
    Formula: min(20, 20 * days_since / target_cycle)
    """
    if target_cycle <= 0:
        target_cycle = 12
    if days_since <= 0:
        return 0.0
    val = (20.0 * days_since) / float(target_cycle)
    return min(20.0, max(0.0, val))


def evaluate_third_party_activity(activity: str) -> float:
    """
    Third-party excavation / dig activity: max 15
    none -> 0
    planned_48h_notice -> 5
    active_supervised -> 10
    direct_excavation_hazard -> 15
    """
    act = (activity or "").strip().lower()
    if act in ["none", "no_activity", ""]:
        return 0.0
    elif act in ["planned_48h_notice", "planned_notice", "48h_notice"]:
        return 5.0
    elif act in ["active_supervised", "supervised_dig", "active_patrol"]:
        return 10.0
    elif act in ["direct_excavation_hazard", "direct_hazard", "unauthorized_dig", "critical_hazard"]:
        return 15.0
    return 0.0


def evaluate_rodent_history(rodent_incidents: int) -> float:
    """
    Rodent damage history: max 10
    0 incidents -> 0
    1 incident  -> 3
    2-3 incidents -> 6
    4+ incidents -> 10
    """
    if rodent_incidents <= 0:
        return 0.0
    elif rodent_incidents == 1:
        return 3.0
    elif 2 <= rodent_incidents <= 3:
        return 6.0
    else:
        return 10.0


def evaluate_public_consequence(area_type: str) -> float:
    """
    Public consequence / population density: max 10
    low_density -> 2
    residential -> 5
    dense_residential -> 7
    sensitive (school/hospital/market) -> 10
    """
    area = (area_type or "").strip().lower()
    if "sensitive" in area or "school" in area or "hospital" in area or "market" in area:
        return 10.0
    elif "dense" in area:
        return 7.0
    elif "residential" in area:
        return 5.0
    elif "low" in area:
        return 2.0
    return 5.0


def classify_tier(score: float) -> str:
    """
    Classify score into PNGRB Priority Tiers:
    0–39   -> LOW
    40–69  -> MEDIUM
    70–84  -> HIGH
    85–100 -> CRITICAL
    """
    if score >= 85.0:
        return "CRITICAL"
    elif score >= 70.0:
        return "HIGH"
    elif score >= 40.0:
        return "MEDIUM"
    else:
        return "LOW"


def calculate_priority(
    segment_data: Dict[str, Any],
    custom_weights: Optional[Dict[str, float]] = None,
    normalize_to_100: bool = False,
    monsoon_mode: bool = False
) -> Dict[str, Any]:
    """
    Calculates Survey Priority Score (0-100) and factor breakdown for a pipeline segment.

    Args:
        segment_data: Dict containing segment attributes
        custom_weights: Optional dict overriding weights for any of the 6 factors.
        normalize_to_100: If True, normalizes final score to 0-100 if sum of custom weights != 100.
        monsoon_mode: If True, applies seasonal rain multiplier (1.25x) to PE vulnerability.:
            - previous_incidents (int)
            - material (str)
            - days_since_survey (int)
            - target_survey_cycle (int, default=12)
            - third_party_activity (str)
            - rodent_incidents (int)
            - area_type (str)
        custom_weights: Optional dict overriding weights for any of the 6 factors.
        normalize_to_100: If True, normalizes final score to 0-100 if sum of custom weights != 100.

    Returns:
        Dict matching Person 3's interface contract:
        {
            "segment_id": ...,
            "score": round(total_score),
            "tier": "LOW" | "MEDIUM" | "HIGH" | "CRITICAL",
            "material": ...,
            "depth_meters": ...,
            "operating_pressure_bar": ...,
            "third_party_activity": ...,
            "factors": {
                "previous_incidents": ...,
                "pe_vulnerability": ...,
                "days_since_survey": ...,
                "third_party_activity": ...,
                "rodent_history": ...,
                "public_consequence": ...
            },
            "location": {"lat": ..., "lng": ...}
        }
    """
    # 1. Merge weights
    weights = dict(DEFAULT_WEIGHTS)
    if custom_weights:
        for k, v in custom_weights.items():
            if k in weights and v is not None:
                weights[k] = float(v)

    # 2. Extract input values with safe defaults
    prev_incidents = int(segment_data.get("previous_incidents", 0))
    material = str(segment_data.get("material", "pe_distribution"))
    days_since = int(segment_data.get("days_since_survey", 0))
    target_cycle = int(segment_data.get("target_survey_cycle", 12))
    third_party = str(segment_data.get("third_party_activity", "none"))
    rodent = int(segment_data.get("rodent_incidents", 0))
    area_type = str(segment_data.get("area_type", "residential"))

    # Check monsoon mode flag from parameter or segment data
    is_monsoon = monsoon_mode or bool(segment_data.get("monsoon_mode", False))

    raw_pe = evaluate_pe_vulnerability(material)
    if is_monsoon and ("pe" in material.lower() or "distribution" in material.lower() or "service" in material.lower()):
        # Soil erosion and moisture ingress increase PE joint and pipe risk
        raw_pe = min(20.0, raw_pe * 1.25)

    # 3. Calculate raw factor scores (based on default baseline scales)
    raw_scores = {
        "previous_incidents": evaluate_previous_incidents(prev_incidents),
        "pe_vulnerability": raw_pe,
        "days_since_survey": evaluate_days_since_survey(days_since, target_cycle),
        "third_party_activity": evaluate_third_party_activity(third_party),
        "rodent_history": evaluate_rodent_history(rodent),
        "public_consequence": evaluate_public_consequence(area_type),
    }

    # 4. Scale by weights:
    # factor_score = (raw_score / baseline_max) * weight
    factor_breakdown: Dict[str, float] = {}
    for factor, raw_score in raw_scores.items():
        baseline = FACTOR_BASELINES[factor]
        weight = weights[factor]
        scaled = (raw_score / baseline) * weight
        factor_breakdown[factor] = round(scaled, 1)

    # Calculate total score
    raw_total = sum(factor_breakdown.values())

    total_weight = sum(weights.values())
    if normalize_to_100 and total_weight > 0 and total_weight != 100.0:
        total_score = (raw_total / total_weight) * 100.0
    else:
        total_score = raw_total

    # Clamp total score between 0 and 100
    final_score = max(0.0, min(100.0, round(total_score)))
    tier = classify_tier(final_score)

    # Emergency Incident Bypass (PRD §8B / §10): active emergency strike overrides to CRITICAL
    if segment_data.get("emergency_incident_active"):
        final_score = 100.0
        tier = "CRITICAL"

    # 5. Format factors for integer/clean display while preserving precision
    clean_factors = {k: int(v) if v.is_integer() else v for k, v in factor_breakdown.items()}

    return {
        "segment_id": segment_data.get("segment_id", "UNKNOWN"),
        "score": int(final_score),
        "tier": tier,
        "material": material,
        "depth_meters": segment_data.get("depth_meters", 1.0),
        "operating_pressure_bar": segment_data.get("operating_pressure_bar", 4.0),
        "third_party_activity": third_party,
        "factors": clean_factors,
        "location": segment_data.get("location", {"lat": 28.6139, "lng": 77.2090})
    }
