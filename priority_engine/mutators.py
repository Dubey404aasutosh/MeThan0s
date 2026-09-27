"""
METHANOS — Closed-Loop State Handlers & Mutators (Person 1 + Person 2 Integration)
Provides post-repair feedback updates, excavation state transitions,
and emergency incident escalation.
"""

from typing import Dict, Any, Optional
from datetime import datetime, timezone
from .dataset import SegmentRepository, global_repo
from .scoring import calculate_priority


def recalculate_after_repair(
    segment_id: str,
    repo: Optional[SegmentRepository] = None,
    clear_hazard: bool = True
) -> Dict[str, Any]:
    """
    Executes the post-survey / post-repair closed-loop feedback:
    1. Increments `previous_incidents += 1` (historical risk goes up)
    2. Resets `last_survey_date = today`
    3. Resets `days_since_survey = 0` (fresh inspection completed)
    4. Clears active third-party hazard if specified
    5. Re-runs priority scoring and returns updated segment object
    """
    target_repo = repo or global_repo
    segment = target_repo.get_raw_segment(segment_id)
    if not segment:
        raise ValueError(f"Segment '{segment_id}' not found.")

    today_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    # Closed-loop feedback mutations (per PRD §8B & Person 2 §12)
    segment["previous_incidents"] = int(segment.get("previous_incidents", 0)) + 1
    segment["last_survey_date"] = today_str
    segment["days_since_survey"] = 0

    if clear_hazard and segment.get("third_party_activity") == "direct_excavation_hazard":
        segment["third_party_activity"] = "none"

    updated = target_repo.get_scored_segment(segment_id)
    return {
        "status": "REPAIR_COMPLETED_HISTORY_UPDATED",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "segment": updated
    }


def update_third_party_status(
    segment_id: str,
    new_status: str,
    repo: Optional[SegmentRepository] = None
) -> Dict[str, Any]:
    """
    Updates the excavation / dig notice status on a segment:
    Valid statuses:
    - 'none'
    - 'planned_48h_notice'
    - 'active_supervised'
    - 'direct_excavation_hazard'
    """
    target_repo = repo or global_repo
    segment = target_repo.get_raw_segment(segment_id)
    if not segment:
        raise ValueError(f"Segment '{segment_id}' not found.")

    valid_statuses = [
        "none",
        "planned_48h_notice",
        "active_supervised",
        "direct_excavation_hazard"
    ]
    if new_status not in valid_statuses:
        raise ValueError(f"Invalid third-party status '{new_status}'. Must be one of {valid_statuses}")

    segment["third_party_activity"] = new_status
    updated = target_repo.get_scored_segment(segment_id)

    return {
        "status": "EXCAVATION_STATUS_UPDATED",
        "new_status": new_status,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "segment": updated
    }


def trigger_emergency_incident(
    segment_id: str,
    incident_type: str = "third_party_strike",
    repo: Optional[SegmentRepository] = None
) -> Dict[str, Any]:
    """
    Emergency incident trigger (PRD §8B / §10, Person 2 §20):
    Bypasses normal cycle entirely:
    - Sets third_party_activity to 'direct_excavation_hazard'
    - Flags urgent critical response
    - Returns updated segment with immediate CRITICAL escalation
    """
    target_repo = repo or global_repo
    segment = target_repo.get_raw_segment(segment_id)
    if not segment:
        raise ValueError(f"Segment '{segment_id}' not found.")

    segment["third_party_activity"] = "direct_excavation_hazard"
    segment["emergency_incident_active"] = True
    segment["emergency_incident_type"] = incident_type
    segment["emergency_reported_at"] = datetime.now(timezone.utc).isoformat()

    updated = target_repo.get_scored_segment(segment_id)
    # Ensure immediate critical override
    updated["tier"] = "CRITICAL"
    updated["score"] = max(updated["score"], 95)

    return {
        "status": "CRITICAL_RESPONSE_TRIGGERED",
        "segment_id": segment_id,
        "incident_type": incident_type,
        "reported_at": segment["emergency_reported_at"],
        "segment": updated
    }
