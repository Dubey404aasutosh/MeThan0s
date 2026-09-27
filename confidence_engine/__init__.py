"""
METHANOS — Confidence Engine & Prevention/Incident Loop (Person 2)
Provides:
1. Survey Quality Control (QC) & Confidence scoring (calculate_confidence)
2. Anomaly Verification state machine & closed-loop feedback
3. 48-Hour Pre-Excavation Early Warning & Prevention Engine
4. Real-time Emergency Incident trigger
"""

from .scoring import (
    calculate_confidence,
    CONFIDENCE_ACCEPT_THRESHOLD,
    DEFAULT_CONFIDENCE_WEIGHTS,
    DECISION_ACCEPT,
    DECISION_RESURVEY,
)
from .surveys import (
    SAMPLE_SURVEYS,
    HIGH_CONFIDENCE_SURVEY,
    LOW_CONFIDENCE_SURVEY,
    get_sample_survey,
    get_all_sample_surveys,
)
from .verification import (
    VerificationStore,
    global_verification_store,
    create_verification_ticket,
    verify_field_anomaly,
    complete_repair_and_feedback,
    get_verification_metrics,
    STATUS_OBSERVED,
    STATUS_RE_SURVEY_QUEUED,
    STATUS_FIELD_VERIFY_PENDING,
    STATUS_CONFIRMED_LEAK,
    STATUS_FALSE_ALARM,
    STATUS_CLEARED_NO_ANOMALY,
    STATUS_REPAIRED,
)
from .dig_prevention import (
    DigNoticeStore,
    global_dig_store,
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
from .incidents import (
    IncidentStore,
    global_incident_store,
    report_emergency_incident,
    resolve_emergency_incident,
)

__all__ = [
    # Scoring & QC
    "calculate_confidence",
    "CONFIDENCE_ACCEPT_THRESHOLD",
    "DEFAULT_CONFIDENCE_WEIGHTS",
    "DECISION_ACCEPT",
    "DECISION_RESURVEY",
    # Sample Surveys
    "SAMPLE_SURVEYS",
    "HIGH_CONFIDENCE_SURVEY",
    "LOW_CONFIDENCE_SURVEY",
    "get_sample_survey",
    "get_all_sample_surveys",
    # Verification State Machine
    "VerificationStore",
    "global_verification_store",
    "create_verification_ticket",
    "verify_field_anomaly",
    "complete_repair_and_feedback",
    "get_verification_metrics",
    "STATUS_OBSERVED",
    "STATUS_RE_SURVEY_QUEUED",
    "STATUS_FIELD_VERIFY_PENDING",
    "STATUS_CONFIRMED_LEAK",
    "STATUS_FALSE_ALARM",
    "STATUS_CLEARED_NO_ANOMALY",
    "STATUS_REPAIRED",
    # 48-Hour Dig Prevention
    "DigNoticeStore",
    "global_dig_store",
    "evaluate_and_submit_dig_notice",
    "dispatch_on_site_monitor",
    "share_safety_route_map",
    "activate_supervised_dig",
    "complete_zero_leak_dig",
    "STATUS_PENDING_REVIEW",
    "STATUS_MONITOR_DISPATCHED",
    "STATUS_ACTIVE_SUPERVISED",
    "STATUS_COMPLETED_ZERO_LEAK",
    "STATUS_SHORT_NOTICE_VIOLATION",
    # Incident Engine
    "IncidentStore",
    "global_incident_store",
    "report_emergency_incident",
    "resolve_emergency_incident",
]
