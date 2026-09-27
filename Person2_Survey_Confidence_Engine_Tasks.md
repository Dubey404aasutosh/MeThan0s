# Person 2 — Survey Confidence Engine + Incident/Verification Loop

**Role:** You own the "trust layer" — deciding whether a survey's data is good enough to act on, and the loop that turns a confirmed leak into an updated history.

## Responsibilities

1. Build the **Survey Confidence Score** calculation (0–100) from survey metadata
2. Build the **Accept / Re-survey** decision logic
3. Build the **Verification workflow** (anomaly → field check → Leak or False Alarm)
4. Build the **48-Hour Dig Notice & Early Warning Engine** (evaluates contractor excavation notices filed $\ge 48$ hours prior, triggers control room alerts, and manages monitor dispatch / map-sharing status)
5. Build the **Incident Engine** for real-time third-party damage reports (bypasses normal cycle)
6. Define how a confirmed leak/repair **feeds back** into Person 1's Priority Engine (history update)

## Deliverables for the Demo

- [x] A working scoring function: `calculate_confidence(survey_metadata) → {score, decision}` (see `confidence_engine/scoring.py`)
- [x] Two concrete example survey records: one that scores HIGH confidence (`S-2101` on P-104), one that scores LOW (`S-2201` on P-118 = 43, RE-SURVEY) — ready for live demo (see `confidence_engine/surveys.py`)
- [x] A simple state machine for verification: `CH4 anomaly → confidence check → (accept → field verify → leak/false_alarm) or (reject → re-survey)` (see `confidence_engine/verification.py`)
- [x] A 48-Hour Dig Notice evaluator & state machine: `contractor notice (hours >= 48h) → control room alert → dispatch monitor / share safety map` (see `confidence_engine/dig_prevention.py`)
- [x] An Incident Engine trigger: a simple "report incident" action (button in demo) that marks a segment CRITICAL immediately (see `confidence_engine/incidents.py`)
- [x] A documented feedback rule: what changes in a segment's data after a leak is confirmed and repaired (`previous_incidents += 1`, `last_survey_date = today`) (see `confidence_engine/verification.py` & `priority_engine/mutators.py`)

## Interface Contract (what Person 3 needs from you)

```json
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
```

Dig notice ticket shape (48-Hour Early Warning):

```json
{
  "notice_id": "DIG-801",
  "segment_id": "P-104",
  "contractor_name": "Metro Fiber Net / Municipal Water",
  "notice_advance_hours": 52.0,
  "is_compliant_48h": true,
  "dig_depth_meters": 1.5,
  "pipeline_depth_meters": 0.8,
  "proximity_buffer_m": 8.5,
  "status": "MONITOR_DISPATCHED",
  "assigned_monitor": "Patrol Officer R. Sharma",
  "safety_map_shared": true
}
```

Incident report shape:

```json
{
  "segment_id": "P-205",
  "incident_type": "third_party_damage",
  "reported_at": "timestamp",
  "status": "CRITICAL_RESPONSE_TRIGGERED"
}
```

## 48-Hour Dig Early Warning & Prevention State Logic (PRD §8A)

```
T - 48 Hours: Contractor Submits Dig Notice
   │ (Coordinates, planned depth, start time, contractor ID)
   ▼
T - 36 Hours: GIS Conflict & Proximity Analysis
   │ • Proximity check: is dig within 50m safety buffer of pipeline?
   │ • Depth clash check: is dig depth >= pipeline depth?
   │ • Fires Control Room alert: COMPLIANT_NOTICE (if >=48h) or SHORT_NOTICE_VIOLATION (if <48h)
   ▼
T - 24 Hours: Control Room Actions & Dispatch
   │ • Dispatch Monitor: assign field patrol officer to supervise
   │ • Share Route Map: generate safety blueprint for contractor
   │ • Update segment in Person 1 engine: third_party_activity = "planned_48h_notice"
   ▼
T - 0 (Dig Day): Zero-Leak Supervised Digging
   │ • Status shifts to "active_supervised"
```

## Confidence Scoring — Suggested Simple Model

Since there's no strict published formula given, propose something defensible and simple for the hackathon (state clearly in the pitch that real weights would be tuned against field data):

| Check | Points | Condition |
|---|---|---|
| GPS coverage | 20 | continuous signal throughout survey |
| Sensor health | 20 | no fault/error flags |
| Survey speed | 20 | within recommended range (cite: speed affects detection reliability) |
| Weather suitability | 20 | wind/atmospheric conditions within acceptable range |
| Route completeness | 20 | % of planned segment actually covered |

Score < 60 → RE-SURVEY. Score ≥ 60 → ACCEPT, proceed to verification if anomaly present.

## Suggested Build Order

1. Define the survey metadata schema (fields above) and hand it to Person 1/3 early
2. Build the confidence scoring function with the 5-check model
3. Build the accept/reject decision logic and the two example records (good survey / bad survey)
4. Build the verification state machine (can just be a simple flowchart/logic, doesn't need a full UI — Person 3 will visualize it)
5. Build the Incident Engine trigger — simplest version is just a function that sets a segment's tier to CRITICAL and logs a timestamp
6. Write the feedback rule connecting back to Priority Engine data

## Stretch Goals

- Simulate a full loop live: report incident → critical response → "field verify" → "repair" → show the segment's score change on next recalculation
- Add a basic false-alarm rate tracker (how often re-surveys turn out to be nothing) — nice data point for the pitch

## Sync Points with Teammates

- **With Person 1:** agree on exactly which fields change on a segment record after a repair, so the recalculation is consistent
- **With Person 3:** confirm how the Incident Engine trigger should be exposed (a button, an API call) so it's demoable live on stage
