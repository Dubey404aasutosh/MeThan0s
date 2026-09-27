"""
METHANOS — Emergency Incident Engine Module (Person 2 - Phase 4)
Handles real-time third-party damage strikes, mechanical ruptures, and construction punctures.
Bypasses the normal survey cycle entirely, marking the segment CRITICAL immediately.
"""

from typing import Dict, Any, List, Optional
from datetime import datetime, timezone

from priority_engine.dataset import SegmentRepository, global_repo
from priority_engine.mutators import trigger_emergency_incident as priority_trigger_incident


class IncidentStore:
    """In-memory store for emergency incident reports and active critical response dispatches."""

    def __init__(self, repo: Optional[SegmentRepository] = None):
        self.repo = repo or global_repo
        self.incidents: Dict[str, Dict[str, Any]] = {}
        self._seed_default_incidents()

    def _seed_default_incidents(self):
        """Pre-seeds sample incident matching Person 2 §59-68."""
        self.incidents["INC-901"] = {
            "incident_id": "INC-901",
            "segment_id": "P-104",
            "incident_type": "third_party_damage",
            "reporter_name": "Delhi Jal Board Field Crew",
            "severity": "CRITICAL_LEVEL_1",
            "reported_at": "2026-09-27T07:10:00Z",
            "status": "CRITICAL_RESPONSE_TRIGGERED",
            "dispatch_team": "Emergency Rapid Isolation Squad #1",
            "notes": "Backhoe excavator snagged 32mm PE service riser. High-pressure whistling sound reported.",
            "resolved": False,
        }

    def reset(self):
        self.incidents.clear()
        self._seed_default_incidents()

    def get_all(self) -> List[Dict[str, Any]]:
        return list(self.incidents.values())

    def get_by_id(self, incident_id: str) -> Optional[Dict[str, Any]]:
        return self.incidents.get(incident_id.upper())


# Global singleton store
global_incident_store = IncidentStore()


def report_emergency_incident(
    segment_id: str,
    incident_type: str = "third_party_damage",
    reporter_name: str = "Control Room Dispatch",
    notes: str = "",
    store: Optional[IncidentStore] = None,
    repo: Optional[SegmentRepository] = None,
) -> Dict[str, Any]:
    """
    Simulates real-time unauthorized construction damage report:
    1. Immediately overrides segment priority to CRITICAL (score >= 95, tier: CRITICAL).
    2. Sets third_party_activity = 'direct_excavation_hazard'.
    3. Logs incident ticket strictly matching Person 2 contract:
       {
         "segment_id": "P-104",
         "incident_type": "third_party_damage",
         "reported_at": "timestamp",
         "status": "CRITICAL_RESPONSE_TRIGGERED"
       }
    """
    target_store = store or global_incident_store
    target_repo = repo or global_repo

    target_segment_id = segment_id.upper()
    segment = target_repo.get_raw_segment(target_segment_id)
    if not segment:
        raise ValueError(f"Segment '{target_segment_id}' not found in pipeline GIS network.")

    # Mutate segment in Priority Engine
    mutation_res = priority_trigger_incident(
        segment_id=target_segment_id,
        incident_type=incident_type,
        repo=target_repo
    )

    incident_id = f"INC-{len(target_store.incidents) + 901}"
    now_iso = datetime.now(timezone.utc).isoformat()

    ticket = {
        "incident_id": incident_id,
        "segment_id": target_segment_id,
        "incident_type": incident_type,
        "reporter_name": reporter_name,
        "severity": "CRITICAL_LEVEL_1",
        "reported_at": now_iso,
        "status": "CRITICAL_RESPONSE_TRIGGERED",
        "dispatch_team": "Emergency Rapid Isolation Squad",
        "notes": notes or f"Emergency third-party strike reported on {target_segment_id}.",
        "resolved": False,
        "segment": mutation_res["segment"],
    }

    target_store.incidents[incident_id] = ticket

    return {
        "status": "CRITICAL_RESPONSE_TRIGGERED",
        "incident_id": incident_id,
        "segment_id": target_segment_id,
        "incident_type": incident_type,
        "reported_at": now_iso,
        "incident": ticket,
        "updated_segment": mutation_res["segment"],
    }


def resolve_emergency_incident(
    incident_id: str,
    resolution_notes: str = "",
    store: Optional[IncidentStore] = None,
    repo: Optional[SegmentRepository] = None,
) -> Dict[str, Any]:
    """
    Resolves emergency incident, resets hazard on segment, and records clearance.
    """
    target_store = store or global_incident_store
    target_repo = repo or global_repo

    incident = target_store.get_by_id(incident_id)
    if not incident:
        raise ValueError(f"Incident '{incident_id}' not found.")

    incident["resolved"] = True
    incident["status"] = "INCIDENT_RESOLVED_LINE_SECURED"
    incident["resolved_at"] = datetime.now(timezone.utc).isoformat()
    incident["resolution_notes"] = resolution_notes or "Line isolated, emergency sleeve clamped, pressure stabilized."

    # Reset segment emergency flag
    segment = target_repo.get_raw_segment(incident["segment_id"])
    if segment:
        segment["emergency_incident_active"] = False
        segment["third_party_activity"] = "none"

    updated = target_repo.get_scored_segment(incident["segment_id"])
    return {
        "status": "INCIDENT_RESOLVED",
        "incident_id": incident_id,
        "incident": incident,
        "updated_segment": updated,
    }
