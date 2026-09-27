"""
METHANOS Priority Engine Package (Person 1)
"""

from .scoring import (
    calculate_priority,
    classify_tier,
    DEFAULT_WEIGHTS,
    FACTOR_BASELINES,
    evaluate_previous_incidents,
    evaluate_pe_vulnerability,
    evaluate_days_since_survey,
    evaluate_third_party_activity,
    evaluate_rodent_history,
    evaluate_public_consequence
)

from .dataset import (
    RAW_SEGMENTS,
    SegmentRepository,
    global_repo
)

from .mutators import (
    recalculate_after_repair,
    update_third_party_status,
    trigger_emergency_incident
)

__all__ = [
    "calculate_priority",
    "classify_tier",
    "DEFAULT_WEIGHTS",
    "FACTOR_BASELINES",
    "evaluate_previous_incidents",
    "evaluate_pe_vulnerability",
    "evaluate_days_since_survey",
    "evaluate_third_party_activity",
    "evaluate_rodent_history",
    "evaluate_public_consequence",
    "RAW_SEGMENTS",
    "SegmentRepository",
    "global_repo",
    "recalculate_after_repair",
    "update_third_party_status",
    "trigger_emergency_incident"
]
