"""
METHANOS — Verification & Anomaly State Machine Module (Person 2 - Phase 2)
Implements:
1. Verification State Machine:
   CH4 Anomaly -> QC Confidence Check -> (Accept -> Field Verify -> Leak / False Alarm) or (Reject -> Re-survey)
2. Closed-Loop Feedback Hook:
   Confirmed Leak -> Repair -> History Updated (previous_incidents += 1, days = 0) -> Priority Recalculated
3. False-Alarm Rate Tracker & Survey Quality Metrics
"""

from typing import Dict, Any, List, Optional
from datetime import datetime, timezone
import uuid

from .scoring import calculate_confidence, DECISION_ACCEPT, DECISION_RESURVEY
from priority_engine.mutators import recalculate_after_repair
from priority_engine.dataset import SegmentRepository, global_repo

# Verification State Enums
STATUS_OBSERVED = "OBSERVED"
STATUS_RE_SURVEY_QUEUED = "RE_SURVEY_QUEUED"
STATUS_FIELD_VERIFY_PENDING = "FIELD_VERIFY_PENDING"
STATUS_CONFIRMED_LEAK = "CONFIRMED_LEAK"
STATUS_FALSE_ALARM = "FALSE_ALARM"
STATUS_CLEARED_NO_ANOMALY = "CLEARED_NO_ANOMALY"
STATUS_REPAIRED = "REPAIRED"


class VerificationStore:
    """In-memory store for anomaly verification tickets and quality audit logs."""

    def __init__(self):
        self.tickets: Dict[str, Dict[str, Any]] = {}
        self._seed_default_tickets()

    def _seed_default_tickets(self):
        """Pre-seeds standard tickets including benchmark S-2101 and S-2201."""
        self.tickets["VER-701"] = {
            "ticket_id": "VER-701",
            "survey_id": "S-2101",
            "segment_id": "P-104",
            "ch4_reading_ppm": 14.6,
            "confidence_score": 100,
            "qc_decision": DECISION_ACCEPT,
            "status": STATUS_FIELD_VERIFY_PENDING,
            "assigned_technician": "Field Patroller R. Sharma",
            "created_at": "2026-09-27T08:00:00Z",
            "verified_at": None,
            "repaired_at": None,
            "confirmed_leak": None,
            "notes": "High-confidence anomaly flagged near PE service joint. Pending ground probe verification.",
            "history_updated": False,
        }

        self.tickets["VER-702"] = {
            "ticket_id": "VER-702",
            "survey_id": "S-2201",
            "segment_id": "P-118",
            "ch4_reading_ppm": 8.4,
            "confidence_score": 43,
            "qc_decision": DECISION_RESURVEY,
            "status": STATUS_RE_SURVEY_QUEUED,
            "assigned_technician": None,
            "created_at": "2026-09-27T09:20:00Z",
            "verified_at": None,
            "repaired_at": None,
            "confirmed_leak": None,
            "notes": "QC failed (excessive speed & gusting wind). Ground verification skipped; re-survey queued.",
            "history_updated": False,
        }

        self.tickets["VER-703"] = {
            "ticket_id": "VER-703",
            "survey_id": "S-2104",
            "segment_id": "P-105",
            "ch4_reading_ppm": 11.2,
            "confidence_score": 100,
            "qc_decision": DECISION_ACCEPT,
            "status": STATUS_CONFIRMED_LEAK,
            "assigned_technician": "Senior Inspector V. Kumar",
            "created_at": "2026-09-27T06:30:00Z",
            "verified_at": "2026-09-27T07:15:00Z",
            "repaired_at": None,
            "confirmed_leak": True,
            "notes": "Physical pinhole leak confirmed on PE main using portable laser detector. Repair clamp scheduled.",
            "history_updated": False,
        }

        self.tickets["VER-704"] = {
            "ticket_id": "VER-704",
            "survey_id": "S-2105",
            "segment_id": "P-102",
            "ch4_reading_ppm": 3.8,
            "confidence_score": 80,
            "qc_decision": DECISION_ACCEPT,
            "status": STATUS_FALSE_ALARM,
            "assigned_technician": "Patrol Officer S. Patel",
            "created_at": "2026-09-26T12:00:00Z",
            "verified_at": "2026-09-26T13:10:00Z",
            "repaired_at": None,
            "confirmed_leak": False,
            "notes": "Field investigation found biological methane from adjacent open storm drain. Pipeline sound.",
            "history_updated": False,
        }

    def reset(self):
        """Resets verification store to default state."""
        self.tickets.clear()
        self._seed_default_tickets()

    def get_all(self) -> List[Dict[str, Any]]:
        return list(self.tickets.values())

    def get_by_id(self, ticket_id: str) -> Optional[Dict[str, Any]]:
        return self.tickets.get(ticket_id.upper())


# Global singleton instance
global_verification_store = VerificationStore()


def create_verification_ticket(
    survey_data: Dict[str, Any],
    assigned_technician: Optional[str] = None,
    store: Optional[VerificationStore] = None,
) -> Dict[str, Any]:
    """
    Ingests survey observation and advances it through the verification state machine:
    1. Evaluates Quality Control Confidence Score.
    2. If RE-SURVEY (<60): ticket moves to RE_SURVEY_QUEUED.
    3. If ACCEPT (>=60) and anomaly present: ticket moves to FIELD_VERIFY_PENDING.
    4. If ACCEPT (>=60) and no anomaly: ticket marked CLEARED_NO_ANOMALY.
    """
    target_store = store or global_verification_store
    qc_result = calculate_confidence(survey_data)

    ticket_id = f"VER-{len(target_store.tickets) + 701}"
    survey_id = qc_result["survey_id"]
    segment_id = qc_result["segment_id"]
    confidence_score = qc_result["confidence_score"]
    decision = qc_result["decision"]
    has_anomaly = qc_result["anomaly_detected"]
    ch4_reading = qc_result["ch4_reading_ppm"]

    if decision == DECISION_RESURVEY:
        status = STATUS_RE_SURVEY_QUEUED
        notes = f"QC Confidence ({confidence_score}/100) below threshold. Survey flagged for re-survey."
    elif has_anomaly:
        status = STATUS_FIELD_VERIFY_PENDING
        notes = f"Accepted anomaly ({ch4_reading} ppm, QC {confidence_score}/100). Ground verification dispatched."
    else:
        status = STATUS_CLEARED_NO_ANOMALY
        notes = f"Survey accepted ({confidence_score}/100). Baseline CH4 nominal. No anomaly detected."

    ticket = {
        "ticket_id": ticket_id,
        "survey_id": survey_id,
        "segment_id": segment_id,
        "ch4_reading_ppm": ch4_reading,
        "confidence_score": confidence_score,
        "qc_decision": decision,
        "status": status,
        "assigned_technician": assigned_technician or ("Field Patroller Dispatched" if status == STATUS_FIELD_VERIFY_PENDING else None),
        "created_at": datetime.now(timezone.utc).isoformat(),
        "verified_at": None,
        "repaired_at": None,
        "confirmed_leak": None,
        "notes": notes,
        "history_updated": False,
        "checks": qc_result["checks"],
    }

    target_store.tickets[ticket_id] = ticket
    return ticket


def verify_field_anomaly(
    ticket_id: str,
    outcome: str,
    technician_notes: str = "",
    store: Optional[VerificationStore] = None,
) -> Dict[str, Any]:
    """
    Records on-ground field check result:
    outcome: 'leak' -> marks CONFIRMED_LEAK (pending repair)
    outcome: 'false_alarm' -> marks FALSE_ALARM (pipeline intact)
    """
    target_store = store or global_verification_store
    ticket = target_store.get_by_id(ticket_id)
    if not ticket:
        raise ValueError(f"Verification ticket '{ticket_id}' not found.")

    if ticket["status"] not in [STATUS_FIELD_VERIFY_PENDING, STATUS_CONFIRMED_LEAK, STATUS_FALSE_ALARM]:
        raise ValueError(f"Cannot verify ticket in status '{ticket["status"]}'.")

    normalized_outcome = outcome.strip().lower()
    now_iso = datetime.now(timezone.utc).isoformat()

    if normalized_outcome in ["leak", "confirmed_leak", "true"]:
        ticket["status"] = STATUS_CONFIRMED_LEAK
        ticket["confirmed_leak"] = True
        ticket["verified_at"] = now_iso
        ticket["notes"] = f"Field confirmed leak: {technician_notes or 'Physical methane leak confirmed on site.'}"
    elif normalized_outcome in ["false_alarm", "false", "cleared"]:
        ticket["status"] = STATUS_FALSE_ALARM
        ticket["confirmed_leak"] = False
        ticket["verified_at"] = now_iso
        ticket["notes"] = f"False alarm verified: {technician_notes or 'No gas leak detected. Non-pipeline methane source.'}"
    else:
        raise ValueError(f"Invalid verification outcome '{outcome}'. Expected 'leak' or 'false_alarm'.")

    return {
        "status": "VERIFICATION_RECORDED",
        "ticket": ticket,
    }


def complete_repair_and_feedback(
    ticket_id: str,
    repair_notes: str = "",
    store: Optional[VerificationStore] = None,
    repo: Optional[SegmentRepository] = None,
) -> Dict[str, Any]:
    """
    Completes repair and triggers closed-loop feedback into Priority Engine (Person 1):
    1. Sets ticket status = REPAIRED.
    2. Increments segment previous_incidents += 1.
    3. Resets last_survey_date = today & days_since_survey = 0.
    4. Priority score is recalculated and updated live.
    """
    target_store = store or global_verification_store
    target_repo = repo or global_repo
    ticket = target_store.get_by_id(ticket_id)
    if not ticket:
        raise ValueError(f"Verification ticket '{ticket_id}' not found.")

    if ticket["status"] != STATUS_CONFIRMED_LEAK:
        raise ValueError(f"Cannot repair ticket in status '{ticket['status']}'. Must be 'CONFIRMED_LEAK'.")

    segment_id = ticket["segment_id"]
    before_segment = dict(target_repo.get_scored_segment(segment_id))

    # Trigger Person 1 closed-loop feedback mutation
    mutation_result = recalculate_after_repair(segment_id, repo=target_repo, clear_hazard=True)
    after_segment = mutation_result["segment"]

    now_iso = datetime.now(timezone.utc).isoformat()
    ticket["status"] = STATUS_REPAIRED
    ticket["repaired_at"] = now_iso
    ticket["history_updated"] = True
    ticket["notes"] = f"Repair completed: {repair_notes or 'Pipeline repair completed. History updated in Priority Engine.'}"

    return {
        "status": "REPAIR_COMPLETED_CLOSED_LOOP_UPDATED",
        "ticket_id": ticket_id,
        "segment_id": segment_id,
        "before": {
            "score": before_segment["score"],
            "tier": before_segment["tier"],
            "previous_incidents": before_segment["factors"]["previous_incidents"],
            "days_since_survey": before_segment["factors"]["days_since_survey"],
        },
        "after": {
            "score": after_segment["score"],
            "tier": after_segment["tier"],
            "previous_incidents": after_segment["factors"]["previous_incidents"],
            "days_since_survey": after_segment["factors"]["days_since_survey"],
        },
        "ticket": ticket,
        "segment": after_segment,
    }


def get_verification_metrics(store: Optional[VerificationStore] = None) -> Dict[str, Any]:
    """
    Calculates survey quality and false-alarm analytics for demo presentation.
    """
    target_store = store or global_verification_store
    all_tickets = target_store.get_all()

    total = len(all_tickets)
    re_survey_queued = sum(1 for t in all_tickets if t["status"] == STATUS_RE_SURVEY_QUEUED)
    pending_verification = sum(1 for t in all_tickets if t["status"] == STATUS_FIELD_VERIFY_PENDING)
    confirmed_leaks = sum(1 for t in all_tickets if t["status"] in [STATUS_CONFIRMED_LEAK, STATUS_REPAIRED])
    repaired_count = sum(1 for t in all_tickets if t["status"] == STATUS_REPAIRED)
    false_alarms = sum(1 for t in all_tickets if t["status"] == STATUS_FALSE_ALARM)

    total_verified = confirmed_leaks + false_alarms
    false_alarm_rate_pct = round((false_alarms / total_verified * 100.0), 1) if total_verified > 0 else 0.0
    leak_confirmation_rate_pct = round((confirmed_leaks / total_verified * 100.0), 1) if total_verified > 0 else 0.0

    return {
        "total_tickets": total,
        "re_survey_queued": re_survey_queued,
        "pending_verification": pending_verification,
        "confirmed_leaks": confirmed_leaks,
        "repaired_count": repaired_count,
        "false_alarms": false_alarms,
        "total_verified": total_verified,
        "false_alarm_rate_pct": false_alarm_rate_pct,
        "leak_confirmation_rate_pct": leak_confirmation_rate_pct,
    }
