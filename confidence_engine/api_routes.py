"""
METHANOS — Person 2 REST API Router
Exposes endpoints for Survey Confidence QC, Anomaly Verification, 48-Hour Dig Prevention,
and Emergency Incident triggers.
"""

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field
from typing import Dict, Any, List, Optional

from .scoring import calculate_confidence, DEFAULT_CONFIDENCE_WEIGHTS
from .surveys import (
    get_sample_survey,
    get_all_sample_surveys,
    HIGH_CONFIDENCE_SURVEY,
    LOW_CONFIDENCE_SURVEY,
)
from .verification import (
    global_verification_store,
    create_verification_ticket,
    verify_field_anomaly,
    complete_repair_and_feedback,
    get_verification_metrics,
)
from .dig_prevention import (
    global_dig_store,
    evaluate_and_submit_dig_notice,
    dispatch_on_site_monitor,
    share_safety_route_map,
    activate_supervised_dig,
    complete_zero_leak_dig,
)
from .incidents import (
    global_incident_store,
    report_emergency_incident,
    resolve_emergency_incident,
)

router = APIRouter(prefix="/api", tags=["Person 2 - Confidence, Prevention & Incidents"])


# --- Request Models ---

class SurveyEvaluationRequest(BaseModel):
    survey_id: Optional[str] = "S-CUSTOM"
    segment_id: Optional[str] = "P-104"
    gps_coverage: Optional[bool] = None
    gps_fix_pct: Optional[float] = None
    sensor_health: Optional[bool] = None
    sensor_fault: Optional[bool] = None
    sensor_health_status: Optional[str] = None
    speed_ok: Optional[bool] = None
    vehicle_speed_kmh: Optional[float] = None
    weather_ok: Optional[bool] = None
    wind_speed_kmh: Optional[float] = None
    weather_conditions: Optional[str] = None
    route_complete: Optional[bool] = None
    route_completeness_pct: Optional[float] = None
    ch4_reading_ppm: Optional[float] = 0.0
    weights: Optional[Dict[str, float]] = None


class VerifyAnomalyRequest(BaseModel):
    outcome: str = Field(..., description="Must be 'leak' or 'false_alarm'")
    technician_notes: Optional[str] = ""


class CompleteRepairRequest(BaseModel):
    repair_notes: Optional[str] = ""


class DigNoticeRequest(BaseModel):
    notice_id: Optional[str] = None
    segment_id: str = "P-104"
    contractor_name: str = "General Civic Contractor"
    contractor_contact: Optional[str] = "+91-98000-00000"
    notice_advance_hours: float = 52.0
    dig_depth_meters: float = 1.5
    proximity_buffer_m: Optional[float] = 8.5
    planned_start: Optional[str] = None
    notes: Optional[str] = ""


class DispatchMonitorRequest(BaseModel):
    monitor_name: Optional[str] = "Patrol Officer Dispatched"


class ShareMapRequest(BaseModel):
    contractor_email: Optional[str] = None


class IncidentReportRequest(BaseModel):
    segment_id: str = Field(..., description="Pipeline segment ID (e.g. P-104)")
    incident_type: Optional[str] = "third_party_damage"
    reporter_name: Optional[str] = "Control Room Live Report"
    notes: Optional[str] = "Unauthorized mechanical excavator strike reported."


# --- Endpoints ---

@router.get("/confidence/weights")
def get_confidence_weights():
    """Returns standard 5-check QC weights."""
    return {
        "status": "success",
        "weights": DEFAULT_CONFIDENCE_WEIGHTS,
        "accept_threshold": 60.0
    }


@router.get("/confidence/surveys")
def list_sample_surveys():
    """Returns sample survey records evaluated with confidence score and QC checks."""
    surveys = get_all_sample_surveys(evaluated=True)
    return {
        "status": "success",
        "count": len(surveys),
        "surveys": surveys
    }


@router.get("/confidence/surveys/{survey_id}")
def get_single_survey(survey_id: str):
    """Retrieves specific survey evaluated with QC score."""
    survey = get_sample_survey(survey_id)
    if not survey:
        raise HTTPException(status_code=404, detail=f"Survey '{survey_id}' not found.")
    eval_res = calculate_confidence(survey)
    survey.update({
        "confidence_score": eval_res["confidence_score"],
        "decision": eval_res["decision"],
        "checks": eval_res["checks"],
        "factor_scores": eval_res["factor_scores"],
        "action_recommendation": eval_res["action_recommendation"],
    })
    return {"status": "success", "survey": survey}


@router.get("/confidence/examples")
def get_confidence_demo_benchmarks():
    """
    Convenience endpoint for Person 3 demo UI:
    Returns High Confidence vs Low Confidence survey cards ready for instant toggle.
    """
    high = dict(HIGH_CONFIDENCE_SURVEY)
    high_eval = calculate_confidence(high)
    high.update(high_eval)

    low = dict(LOW_CONFIDENCE_SURVEY)
    low_eval = calculate_confidence(low)
    low.update(low_eval)

    return {
        "status": "success",
        "high_confidence_example": high,
        "low_confidence_example": low,
    }


@router.post("/confidence/evaluate")
def evaluate_survey_qc(req: SurveyEvaluationRequest):
    """Computes confidence score and Accept/Re-survey decision on arbitrary survey payload."""
    payload = req.model_dump(exclude_none=True)
    weights = payload.pop("weights", None)
    result = calculate_confidence(payload, weights=weights)
    return {
        "status": "success",
        "result": result
    }


# --- Verification Endpoints ---

@router.get("/verification/tickets")
def list_verification_tickets():
    """Returns all verification tickets across observed anomalies."""
    tickets = global_verification_store.get_all()
    return {
        "status": "success",
        "count": len(tickets),
        "tickets": tickets
    }


@router.post("/verification/tickets")
def submit_survey_to_verification(req: SurveyEvaluationRequest):
    """Ingests survey observation into verification state machine."""
    payload = req.model_dump(exclude_none=True)
    ticket = create_verification_ticket(payload)
    return {
        "status": "success",
        "ticket": ticket
    }


@router.post("/verification/tickets/{ticket_id}/verify")
def verify_ticket(ticket_id: str, req: VerifyAnomalyRequest):
    """Records on-site technician ground verification ('leak' or 'false_alarm')."""
    try:
        res = verify_field_anomaly(ticket_id, outcome=req.outcome, technician_notes=req.technician_notes)
        return {"status": "success", "data": res}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/verification/tickets/{ticket_id}/repair")
def repair_ticket(ticket_id: str, req: CompleteRepairRequest):
    """Completes repair on confirmed leak and triggers closed-loop Priority Engine recalculation."""
    try:
        res = complete_repair_and_feedback(ticket_id, repair_notes=req.repair_notes)
        return {"status": "success", "data": res}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/verification/metrics")
def get_audit_metrics():
    """Returns false-alarm rate and survey QC operational metrics."""
    metrics = get_verification_metrics()
    return {
        "status": "success",
        "metrics": metrics
    }


# --- 48-Hour Dig Prevention Endpoints ---

@router.get("/dig-notices")
def list_dig_notices():
    """Returns all contractor excavation notices and control room alerts."""
    notices = global_dig_store.get_all()
    return {
        "status": "success",
        "count": len(notices),
        "notices": notices
    }


@router.post("/dig-notices")
def submit_dig_notice(req: DigNoticeRequest):
    """Ingests contractor excavation ticket and evaluates 48-hour compliance + depth clash."""
    try:
        res = evaluate_and_submit_dig_notice(req.model_dump(exclude_none=True))
        return {"status": "success", "notice": res}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/dig-notices/{notice_id}/dispatch-monitor")
def dispatch_monitor(notice_id: str, req: DispatchMonitorRequest):
    """Control Room Action 1: Dispatches on-site line monitor & updates segment third_party_activity."""
    try:
        res = dispatch_on_site_monitor(notice_id, monitor_name=req.monitor_name)
        return {"status": "success", "data": res}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/dig-notices/{notice_id}/share-map")
def share_map(notice_id: str, req: ShareMapRequest):
    """Control Room Action 2: Issues digital safety blueprint to contractor."""
    try:
        res = share_safety_route_map(notice_id, contractor_email=req.contractor_email)
        return {"status": "success", "data": res}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/dig-notices/{notice_id}/start-dig")
def start_dig(notice_id: str):
    """Dig Day Transition: Shifts excavation to active supervised state."""
    try:
        res = activate_supervised_dig(notice_id)
        return {"status": "success", "data": res}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/dig-notices/{notice_id}/complete")
def complete_dig(notice_id: str):
    """Excavation Completed Safely: Closes notice and resets segment third_party_activity to 'none'."""
    try:
        res = complete_zero_leak_dig(notice_id)
        return {"status": "success", "data": res}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# --- Incident Engine Endpoints ---

@router.get("/incidents")
def list_incidents():
    """Lists emergency incident reports."""
    incidents = global_incident_store.get_all()
    return {
        "status": "success",
        "count": len(incidents),
        "incidents": incidents
    }


@router.post("/incidents/report")
def report_incident(req: IncidentReportRequest):
    """
    Demo Action: 'Report Incident' button!
    Escalates target segment to CRITICAL instantly (100) and triggers emergency dispatch.
    """
    try:
        res = report_emergency_incident(
            segment_id=req.segment_id,
            incident_type=req.incident_type,
            reporter_name=req.reporter_name,
            notes=req.notes
        )
        return {"status": "success", "data": res}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/incidents/{incident_id}/resolve")
def resolve_incident(incident_id: str):
    """Resolves incident and clears active emergency hazard."""
    try:
        res = resolve_emergency_incident(incident_id)
        return {"status": "success", "data": res}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
