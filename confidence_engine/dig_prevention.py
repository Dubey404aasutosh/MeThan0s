"""
METHANOS — 48-Hour Pre-Excavation Early Warning & Prevention Engine (Person 2 - Phase 3)
Implements:
1. Contractor 48-Hour advance dig notice ingestion & compliance evaluation
2. GIS proximity and depth conflict analysis (dig depth vs pipeline depth)
3. Control Room dispatch workflow:
   - [Dispatch On-Site Monitor] -> assigns patrol officer & elevates segment to 'planned_48h_notice'
   - [Share Safety Map] -> issues digital underground blueprint to contractor
   - [Start Supervised Dig] -> moves to 'active_supervised'
   - [Complete Dig] -> clears hazard back to 'none'
4. Short-notice violation detection (<48h) to halt unmonitored mechanical excavation
"""

from typing import Dict, Any, List, Optional
from datetime import datetime, timezone

from priority_engine.dataset import SegmentRepository, global_repo
from priority_engine.mutators import update_third_party_status

# Dig Notice Status Enums
STATUS_PENDING_REVIEW = "PENDING_REVIEW"
STATUS_MONITOR_DISPATCHED = "MONITOR_DISPATCHED"
STATUS_ACTIVE_SUPERVISED = "ACTIVE_SUPERVISED"
STATUS_COMPLETED_ZERO_LEAK = "COMPLETED_ZERO_LEAK"
STATUS_SHORT_NOTICE_VIOLATION = "SHORT_NOTICE_VIOLATION"

# Thresholds
MANDATORY_NOTICE_HOURS = 48.0
PROXIMITY_SAFETY_BUFFER_MAX_M = 50.0


class DigNoticeStore:
    """In-memory store for 48-hour excavation notices, alerts, and monitor assignments."""

    def __init__(self, repo: Optional[SegmentRepository] = None):
        self.repo = repo or global_repo
        self.notices: Dict[str, Dict[str, Any]] = {}
        self._seed_default_notices()

    def _seed_default_notices(self):
        """Pre-seeds realistic contractor excavation notices matching PRD & Person 2/3 contracts."""
        # DIG-801 on P-104 (Matching contract in Person 2 tasks §43-57)
        self.notices["DIG-801"] = {
            "notice_id": "DIG-801",
            "segment_id": "P-104",
            "contractor_name": "Metro Fiber Net / Municipal Water",
            "contractor_contact": "+91-98110-23456",
            "notice_advance_hours": 52.0,
            "is_compliant_48h": True,
            "dig_depth_meters": 1.5,
            "pipeline_depth_meters": 0.8,
            "depth_clash_hazard": True,
            "proximity_buffer_m": 8.5,
            "status": STATUS_MONITOR_DISPATCHED,
            "assigned_monitor": "Patrol Officer R. Sharma",
            "safety_map_shared": True,
            "safety_map_blueprint_url": "/api/dig-notices/DIG-801/map-blueprint",
            "submitted_at": "2026-09-25T08:00:00Z",
            "planned_start": "2026-09-27T12:00:00Z",
            "alert_level": "HIGH_COMPLIANT_WARNING",
            "notes": "Trenching for 5G optical fiber crossing directly over P-104 PE service line.",
        }

        # DIG-802: Short-notice violation (< 48 hrs)
        self.notices["DIG-802"] = {
            "notice_id": "DIG-802",
            "segment_id": "P-106",
            "contractor_name": "Rapid Road Boring Co.",
            "contractor_contact": "+91-98711-98765",
            "notice_advance_hours": 14.0,  # Short notice violation
            "is_compliant_48h": False,
            "dig_depth_meters": 2.2,
            "pipeline_depth_meters": 1.1,
            "depth_clash_hazard": True,
            "proximity_buffer_m": 4.2,
            "status": STATUS_SHORT_NOTICE_VIOLATION,
            "assigned_monitor": None,
            "safety_map_shared": False,
            "safety_map_blueprint_url": "/api/dig-notices/DIG-802/map-blueprint",
            "submitted_at": "2026-09-26T22:00:00Z",
            "planned_start": "2026-09-27T12:00:00Z",
            "alert_level": "URGENT_UNAUTHORIZED_EXCAVATION_RISK",
            "notes": "Emergency culvert repair notice submitted only 14h before digging. Stop-work dispatched.",
        }

        # DIG-803: Active Supervised excavation
        self.notices["DIG-803"] = {
            "notice_id": "DIG-803",
            "segment_id": "P-107",
            "contractor_name": "State Jal Board Water Main Team",
            "contractor_contact": "+91-98101-55443",
            "notice_advance_hours": 72.0,
            "is_compliant_48h": True,
            "dig_depth_meters": 1.0,
            "pipeline_depth_meters": 1.5,
            "depth_clash_hazard": False,
            "proximity_buffer_m": 12.0,
            "status": STATUS_ACTIVE_SUPERVISED,
            "assigned_monitor": "Patrol Officer M. Verma",
            "safety_map_shared": True,
            "safety_map_blueprint_url": "/api/dig-notices/DIG-803/map-blueprint",
            "submitted_at": "2026-09-24T09:00:00Z",
            "planned_start": "2026-09-27T09:00:00Z",
            "alert_level": "MONITORED_SAFE",
            "notes": "Supervised manual digging with utility locator present on site.",
        }

    def reset(self):
        """Resets notices to default seeded state."""
        self.notices.clear()
        self._seed_default_notices()

    def get_all(self) -> List[Dict[str, Any]]:
        return list(self.notices.values())

    def get_by_id(self, notice_id: str) -> Optional[Dict[str, Any]]:
        return self.notices.get(notice_id.upper())


# Global singleton store
global_dig_store = DigNoticeStore()


def evaluate_and_submit_dig_notice(
    notice_data: Dict[str, Any],
    store: Optional[DigNoticeStore] = None,
    repo: Optional[SegmentRepository] = None,
) -> Dict[str, Any]:
    """
    Evaluates contractor excavation notice against 48-Hour Rule & pipeline GIS layer:
    1. Checks notice_advance_hours >= 48.0.
    2. Cross-references segment burial depth to check depth clash hazard.
    3. Issues Control Room alert.
    """
    target_store = store or global_dig_store
    target_repo = repo or global_repo

    segment_id = notice_data.get("segment_id", "P-104").upper()
    segment = target_repo.get_raw_segment(segment_id)
    if not segment:
        raise ValueError(f"Pipeline segment '{segment_id}' not found in GIS registry.")

    pipeline_depth = float(segment.get("depth_meters", 1.0))
    dig_depth = float(notice_data.get("dig_depth_meters", 1.2))
    advance_hours = float(notice_data.get("notice_advance_hours", 48.0))
    proximity_buffer = float(notice_data.get("proximity_buffer_m", 10.0))

    is_compliant_48h = advance_hours >= MANDATORY_NOTICE_HOURS
    depth_clash_hazard = dig_depth >= pipeline_depth

    notice_id = notice_data.get("notice_id", f"DIG-{len(target_store.notices) + 801}")

    if not is_compliant_48h:
        status = STATUS_SHORT_NOTICE_VIOLATION
        alert_level = "URGENT_UNAUTHORIZED_EXCAVATION_RISK"
    elif depth_clash_hazard:
        status = STATUS_PENDING_REVIEW
        alert_level = "HIGH_DEPTH_CLASH_WARNING"
    else:
        status = STATUS_PENDING_REVIEW
        alert_level = "STANDARD_ADVANCE_NOTICE"

    record = {
        "notice_id": notice_id,
        "segment_id": segment_id,
        "contractor_name": notice_data.get("contractor_name", "General Infrastructure Contractor"),
        "contractor_contact": notice_data.get("contractor_contact", "Unspecified"),
        "notice_advance_hours": advance_hours,
        "is_compliant_48h": is_compliant_48h,
        "dig_depth_meters": dig_depth,
        "pipeline_depth_meters": pipeline_depth,
        "depth_clash_hazard": depth_clash_hazard,
        "proximity_buffer_m": proximity_buffer,
        "status": status,
        "assigned_monitor": None,
        "safety_map_shared": False,
        "safety_map_blueprint_url": f"/api/dig-notices/{notice_id}/map-blueprint",
        "submitted_at": datetime.now(timezone.utc).isoformat(),
        "planned_start": notice_data.get("planned_start", "2026-09-29T09:00:00Z"),
        "alert_level": alert_level,
        "notes": notice_data.get("notes", "Submitted via contractor notification portal."),
    }

    target_store.notices[notice_id] = record
    return record


def dispatch_on_site_monitor(
    notice_id: str,
    monitor_name: str = "Patrol Officer Dispatched",
    store: Optional[DigNoticeStore] = None,
    repo: Optional[SegmentRepository] = None,
) -> Dict[str, Any]:
    """
    Action 1: Dispatch On-Site Monitor (PRD §3 / §8A):
    - Assigns utility line supervisor
    - Updates notice status to MONITOR_DISPATCHED
    - Syncs with Person 1 engine: updates segment third_party_activity to 'planned_48h_notice'
    """
    target_store = store or global_dig_store
    target_repo = repo or global_repo

    notice = target_store.get_by_id(notice_id)
    if not notice:
        raise ValueError(f"Dig notice '{notice_id}' not found.")

    notice["assigned_monitor"] = monitor_name
    notice["status"] = STATUS_MONITOR_DISPATCHED

    # Update Priority Engine segment state
    segment_id = notice["segment_id"]
    update_result = update_third_party_status(
        segment_id=segment_id,
        new_status="planned_48h_notice",
        repo=target_repo
    )

    return {
        "status": "MONITOR_DISPATCHED",
        "notice_id": notice_id,
        "assigned_monitor": monitor_name,
        "notice": notice,
        "updated_segment": update_result["segment"]
    }


def share_safety_route_map(
    notice_id: str,
    contractor_email: Optional[str] = None,
    store: Optional[DigNoticeStore] = None,
) -> Dict[str, Any]:
    """
    Action 2: Share Pipeline Route Map & Depth Clearance Blueprint (PRD §3 / §8A):
    Dispatches annotated underground route/depth blueprint directly to contractor.
    """
    target_store = store or global_dig_store
    notice = target_store.get_by_id(notice_id)
    if not notice:
        raise ValueError(f"Dig notice '{notice_id}' not found.")

    notice["safety_map_shared"] = True
    recipient = contractor_email or notice.get("contractor_contact", "contractor@metrofiber.in")

    return {
        "status": "SAFETY_MAP_DISPATCHED",
        "notice_id": notice_id,
        "segment_id": notice["segment_id"],
        "recipient": recipient,
        "blueprint_url": notice["safety_map_blueprint_url"],
        "pipeline_depth_meters": notice["pipeline_depth_meters"],
        "safe_buffer_distance_m": notice["proximity_buffer_m"],
        "notice": notice
    }


def activate_supervised_dig(
    notice_id: str,
    store: Optional[DigNoticeStore] = None,
    repo: Optional[SegmentRepository] = None,
) -> Dict[str, Any]:
    """
    Action 3: Shift to Active Supervised Digging on Dig Day (T-0):
    - Sets notice status = ACTIVE_SUPERVISED
    - Updates segment in Person 1 engine: third_party_activity = 'active_supervised'
    """
    target_store = store or global_dig_store
    target_repo = repo or global_repo

    notice = target_store.get_by_id(notice_id)
    if not notice:
        raise ValueError(f"Dig notice '{notice_id}' not found.")

    notice["status"] = STATUS_ACTIVE_SUPERVISED

    update_result = update_third_party_status(
        segment_id=notice["segment_id"],
        new_status="active_supervised",
        repo=target_repo
    )

    return {
        "status": "EXCAVATION_SUPERVISED_ACTIVE",
        "notice_id": notice_id,
        "notice": notice,
        "updated_segment": update_result["segment"]
    }


def complete_zero_leak_dig(
    notice_id: str,
    store: Optional[DigNoticeStore] = None,
    repo: Optional[SegmentRepository] = None,
) -> Dict[str, Any]:
    """
    Action 4: Close dig notice upon excavation completion without damage:
    - Sets notice status = COMPLETED_ZERO_LEAK
    - Resets segment third_party_activity to 'none'
    """
    target_store = store or global_dig_store
    target_repo = repo or global_repo

    notice = target_store.get_by_id(notice_id)
    if not notice:
        raise ValueError(f"Dig notice '{notice_id}' not found.")

    notice["status"] = STATUS_COMPLETED_ZERO_LEAK

    update_result = update_third_party_status(
        segment_id=notice["segment_id"],
        new_status="none",
        repo=target_repo
    )

    return {
        "status": "DIG_COMPLETED_INCIDENT_PREVENTED",
        "notice_id": notice_id,
        "notice": notice,
        "updated_segment": update_result["segment"]
    }
