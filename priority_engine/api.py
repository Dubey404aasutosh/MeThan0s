"""
METHANOS Priority Engine REST API (Person 1)
FastAPI service providing Priority Engine calculation, segment GIS data,
weight recalculations for sliders, and closed-loop feedback triggers.
"""

import os
from typing import Dict, Any, Optional
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from .scoring import DEFAULT_WEIGHTS, FACTOR_BASELINES
from .dataset import SegmentRepository, RAW_SEGMENTS, global_repo
from .mutators import (
    recalculate_after_repair,
    update_third_party_status,
    trigger_emergency_incident
)
from confidence_engine.api_routes import router as confidence_router

app = FastAPI(
    title="METHANOS API",
    description="Unified API for Priority Engine, Survey Confidence QC, Dig Prevention & Incidents",
    version="1.0.0"
)

# Mount Person 2 router (Confidence, Verification, 48-Hour Dig Prevention, Incidents)
app.include_router(confidence_router)

# Enable CORS for frontend integration (Vite, React, Next.js, or file://)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class CustomWeightsRequest(BaseModel):
    weights: Dict[str, float] = Field(
        default=DEFAULT_WEIGHTS,
        description="Dictionary mapping factor names to custom weight values"
    )
    normalize_to_100: bool = Field(
        default=False,
        description="Whether to normalize the sum of weights to 100"
    )
    monsoon_mode: bool = Field(
        default=False,
        description="Whether seasonal monsoon/rain multiplier is enabled for PE lines"
    )


class ExcavationStatusRequest(BaseModel):
    new_status: str = Field(
        ...,
        description="New excavation status: 'none', 'planned_48h_notice', 'active_supervised', 'direct_excavation_hazard'"
    )


class EmergencyIncidentRequest(BaseModel):
    incident_type: str = Field(
        default="third_party_strike",
        description="Type of emergency incident reported (e.g. excavator puncture, joint rupture)"
    )


class RepairRequest(BaseModel):
    clear_hazard: bool = Field(
        default=True,
        description="Whether to clear active direct excavation hazard on repair"
    )


@app.get("/api/health")
def health_check():
    return {
        "status": "healthy",
        "service": "METHANOS Priority Engine",
        "total_segments": len(global_repo._segments)
    }


@app.get("/api/weights")
def get_weights_config():
    """Returns default scoring weights and baseline factor thresholds."""
    return {
        "default_weights": DEFAULT_WEIGHTS,
        "factor_baselines": FACTOR_BASELINES,
        "tier_thresholds": {
            "LOW": [0, 39],
            "MEDIUM": [40, 69],
            "HIGH": [70, 84],
            "CRITICAL": [85, 100]
        }
    }


@app.get("/api/segments")
def list_segments(
    sort_by_priority: bool = Query(True, description="Sort segments by priority score descending"),
    monsoon_mode: bool = Query(False, description="Apply seasonal monsoon multiplier to PE vulnerability")
):
    """Returns all pipeline segments evaluated with priority scores, tiers, and GIS metadata."""
    segments = global_repo.get_all_scored_segments(sort_by_priority=sort_by_priority, monsoon_mode=monsoon_mode)
    return {
        "count": len(segments),
        "monsoon_mode": monsoon_mode,
        "segments": segments
    }


@app.get("/api/segments/{segment_id}")
def get_segment_detail(segment_id: str, monsoon_mode: bool = Query(False)):
    """Returns detailed score and factor breakdown for a specific segment."""
    segment = global_repo.get_scored_segment(segment_id, monsoon_mode=monsoon_mode)
    if not segment:
        raise HTTPException(status_code=404, detail=f"Segment '{segment_id}' not found.")
    return segment


@app.post("/api/recalculate")
def recalculate_all_with_custom_weights(payload: CustomWeightsRequest):
    """
    Recalculates all segment priority scores using custom slider weights and optional monsoon mode.
    Returns the updated segment list sorted by priority.
    """
    segments = global_repo.get_all_scored_segments(
        custom_weights=payload.weights,
        sort_by_priority=True,
        monsoon_mode=payload.monsoon_mode
    )
    return {
        "applied_weights": payload.weights,
        "monsoon_mode": payload.monsoon_mode,
        "count": len(segments),
        "segments": segments
    }


@app.post("/api/segments/{segment_id}/repair")
def repair_segment(segment_id: str, payload: RepairRequest = RepairRequest()):
    """
    Closed-loop feedback: Marks leak repaired, increments incident history,
    resets survey date, and recalculates segment priority.
    """
    try:
        result = recalculate_after_repair(
            segment_id=segment_id,
            repo=global_repo,
            clear_hazard=payload.clear_hazard
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@app.post("/api/segments/{segment_id}/excavation-status")
def update_segment_excavation(segment_id: str, payload: ExcavationStatusRequest):
    """
    Updates the 48-Hour excavation / third-party dig status on a segment.
    """
    try:
        result = update_third_party_status(
            segment_id=segment_id,
            new_status=payload.new_status,
            repo=global_repo
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/api/segments/{segment_id}/emergency-incident")
def report_emergency_incident(segment_id: str, payload: EmergencyIncidentRequest = EmergencyIncidentRequest()):
    """
    Simulates an urgent pipeline breach/strike, escalating the segment to CRITICAL instantly.
    """
    try:
        result = trigger_emergency_incident(
            segment_id=segment_id,
            incident_type=payload.incident_type,
            repo=global_repo
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@app.post("/api/reset")
def reset_database():
    """Resets the in-memory repository to default synthetic values."""
    global global_repo
    global_repo._segments = {s["segment_id"]: dict(s) for s in RAW_SEGMENTS}
    return {"status": "RESET_SUCCESSFUL", "total_segments": len(global_repo._segments)}


# Mount static frontend for instant browser access
frontend_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "frontend")
if os.path.exists(frontend_dir):
    app.mount("/", StaticFiles(directory=frontend_dir, html=True), name="frontend")

