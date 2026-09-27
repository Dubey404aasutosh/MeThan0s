# METHANOS — Product Requirements Document

**Track 4: Cutting Fugitive Methane Emissions from City Gas Networks**

---

## 1. Problem Statement

Urban CGD (City Gas Distribution) pipeline networks leak methane — a GHG over 80x more potent than CO2 over 20 years — through three dominant, well-understood failure modes:

1. **Third-party damage** — construction/excavation crews digging near or into pipelines
2. **Rat/rodent damage** — rodents gnawing through PE (polyethylene) service lines and joints
3. **Weather-related degradation** — rainfall causing soil erosion, joint exposure, and accelerated corrosion

Survey teams cannot physically inspect the entire network at once. Today's approach is reactive: **Survey → Detect → Report**, with no systematic way to decide *where* to look first, and no way to know if a given survey's data can even be trusted.

## 2. Solution Overview

**METHANOS is an intelligence layer around existing mobile methane survey practice** — not a new detection hardware. It answers three separate questions that today get conflated into one:

| Question | Engine | Output |
|---|---|---|
| Where should we survey first? | **Priority Engine** | Survey Priority Score (0–100) per segment |
| Can we trust this survey's data? | **Confidence Engine** | Survey Confidence Score (0–100) |
| Did we actually find a leak? | **Verification/Incident Engine** | Confirmed leak → repair → history update |

**Critical framing for judges:** a high Priority Score means *"survey this earlier,"* not *"this pipe is leaking."* This distinction (explicit in the design) is what keeps the system honest and defensible — we are not claiming to predict leaks, we are prioritizing finite inspection resources using known risk factors.

This aligns with PNGRB's CGD Integrity Management System, which prioritizes threats by likelihood × consequence and explicitly names third-party/mechanical damage, rat bites, and PE joint failures as recognized threat categories.

## 3. Root Causes Addressed (per faculty guidance)

| Cause | How METHANOS addresses it |
|---|---|
| **Construction/excavation** | • **GIS Asset Layer:** Full geospatial mapping of underground lines with **depth of burial (m), material, and pressure rating (bar)**.<br>• **Mandatory 48-Hour Advance Dig Notice:** Contractors/agencies must inform the utility 2 days prior to excavation.<br>• **Control Room Real-Time Alerts:** Instant SMS/push & dashboard notifications when a dig is requested near a pipeline.<br>• **Proactive Prevention Actions:** One-click dispatch of an on-site monitor/patroller + instant sharing of the safe pipeline route map with the contractor.<br>• **Priority Engine Integration:** Active/planned digs elevate segment priority for pre-excavation baseline surveys; unauthorized digs trigger critical alerts. |
| **Rat bites** | PE Vulnerability + Rodent History factors in Priority Engine; retrofit prioritization output |
| **Rain/weather** | Feeds into asset vulnerability and can be added as a seasonal modifier (see §10 stretch goals) |

## 4. System Architecture

```
                                  METHANOS
                                     │
      ┌──────────────────────────────┼──────────────────────────────┐
      ▼                              ▼                              ▼
 1. PRIORITY ENGINE           2. CONFIDENCE ENGINE         3. PREVENTION & INCIDENTS
 "Where should we survey?"    "Can we trust this survey?"  "Prevent leaks & verify"
      │                              │                              │
      ▼                              ▼                              ▼
 • 6-Factor Weighted Score     • QC on vehicle speed,       • 48-Hr Dig Notice & Control
 • GIS Asset Risk (Depth,        wind, GPS & sensor           Room Real-Time Alerts
   Pressure, Material)         • Accept vs Re-survey        • Dispatch On-Site Monitor
 • Route Dispatch Order          decision                   • Anomaly Field Verification
                                                            • Closed-Loop History Update
```

Data flows in a continuous prevention and response loop:
**GIS Asset Layer + 48-Hr Dig Notices → Priority Score → Survey Planning → Mobile Survey → CH₄ Observation → Confidence Check → Field Verification / Monitor Dispatch → Repair / Clearance → Update History → Recalculate Priority → Next Cycle.**

## 5. Data Model — Pipeline Segment & Excavation Schema

Each pipeline segment record carries GIS asset attributes (minimum viable fields for hackathon):

```
segment_id            string   e.g. "P-104"
material              enum     [steel_main, pe_distribution, pe_service_hotspot]
depth_meters          float    depth of burial (e.g. 1.2m, 0.8m)
operating_pressure_bar float   pipeline pressure (e.g. 19.0 bar steel, 4.0 bar PE dist, 0.1 bar PE service)
gps_coordinates       polyline/points
previous_incidents    int      count of past leaks/incidents on this segment
last_survey_date      date
target_survey_cycle   int      days (default 12)
third_party_activity  enum     [none, planned_48h_notice, active_supervised, direct_excavation_hazard]
rodent_incidents       int      count of past rodent-related damage
area_type             enum     [low_density, residential, dense_residential, sensitive(school/hospital/market)]
```

Excavation / Dig Notice Ticket Schema (Pre-Excavation Early Warning):

```
notice_id             string   e.g. "DIG-801"
segment_id            string   e.g. "P-104"
contractor_name       string   e.g. "Metro Fiber Trenching Ltd / Jal Board"
submission_timestamp  timestamp
planned_dig_timestamp timestamp (Contractor must submit >= 48 hours before digging)
notice_advance_hours  float    (e.g., 52.0 hrs = compliant; <48 hrs = short-notice violation)
dig_depth_meters      float    proposed dig depth (checked against pipeline depth_meters)
proximity_buffer_m    float    proximity to gas pipeline (e.g. 8.5m)
status                enum     [pending_review, monitor_dispatched, safety_map_sent, urgent_violation]
assigned_monitor      string   name/ID of dispatched utility patrol officer
```

Survey/observation record (produced by mobile survey — see Survey Engine):

```
survey_id, segment_id, timestamp
ch4_reading
gps_log, vehicle_speed, wind_speed, weather_conditions
sensor_health_status
route_completeness_pct
```

## 6. Priority Engine — Scoring Formula

**Survey Priority Score = 0–100**, sum of 6 weighted factors. These weights are **prototype defaults**, explicitly configurable, and would be calibrated against an operator's real incident history before production use.

| Factor | Weight | Logic |
|---|---|---|
| Previous incident history | 25 | 0 incidents=0, 1=10, 2=18, 3+=25 |
| PE / service-line vulnerability | 20 | Main steel=5, PE distribution=15, PE hotspot=20 |
| Days since last survey | 20 | `min(20, 20 × days_since_survey / target_cycle)` |
| Third-party activity | 15 | none=0, planned_48h_notice=5, active_supervised=10, direct excavation=15 |
| Rodent damage history | 10 | 0=0, 1=3, 2–3=6, 4+=10 |
| Public consequence | 10 | low-density=2, residential=5, dense residential=7, school/hospital/market=10 |

**Priority tiers:**

```
0–39   🟢 LOW       — normal survey schedule
40–69  🟡 MEDIUM    — survey when due
70–84  🟠 HIGH      — bring forward in route
85–100 🔴 CRITICAL  — prioritize for earliest inspection
```

## 7. Survey Confidence Engine

Runs after every survey to answer: **is this data reliable enough to act on?**

Inputs: GPS coverage, sensor health, survey speed vs. optimal range, wind/weather suitability, route completeness. Research on mobile methane surveys shows detection performance is strongly affected by survey speed and atmospheric conditions — this is why confidence must be scored separately from the CH₄ reading itself.

Output: 0–100 confidence score →
- **High confidence + anomaly** → send to Verification
- **Low confidence** → flag for re-survey, regardless of what the CH₄ reading showed

## 8. 48-Hour Dig Prevention, Verification & Incident Loop

### A. 48-Hour Pre-Excavation Prevention Protocol

```
T - 48 Hours: Contractor Submits Dig Notice
   │ (Coordinates, planned depth, start time, contractor ID)
   │
   ▼
T - 36 Hours: METHANOS Control Room GIS Conflict Analysis
   │ • System checks pipeline depth (e.g. 1.0m) vs dig depth (e.g. 1.5m)
   │ • Analyzes pipeline pressure (High/Medium/Low) & material (Steel/PE)
   │ • Fires real-time SMS/push & dashboard alert to Gas Utility Control Room
   │
   ▼
T - 24 Hours: Proactive Action by Utility Control Room
   │ 1. Dispatches On-site Monitor / Field Patroller to mark exact pipe route with flags/spray
   │ 2. Priority Engine elevates segment to HIGH → Mobile vehicle runs a baseline pre-survey
   │ 3. Digital Pipeline Safety Map & Clearance issued to the contractor
   │
   ▼
T - 0 (Dig Day): Zero-Leak Supervised Digging
     On-site monitor present or clear buffer maintained → Incident prevented BEFORE it happens!
```

#### Control Room Contractor Notification Dashboard
The utility control room features a dedicated **Excavation Notification & Early Warning Feed**:
* **Live Ingestion Feed:** Receives real-time dig notices submitted by construction/civic contractors (water, telecom fiber, metro, road works).
* **GIS Proximity & Depth Conflict Engine:** Automatically cross-references incoming dig coordinates against the buried pipeline GIS layer to compute distance buffer (m) and depth conflict.
* **Instant Duty Officer Action Center:**
  * `[Dispatch On-Site Monitor]`: Assigns a line patrol supervisor to inspect and guide the site team.
  * `[Send Pipeline Route Map]`: Dispatches an annotated underground route/depth blueprint directly to the contractor.
* **Violation Guardrail:** Any dig requested with $<48$ hours notice or unnotified digging detected on-site immediately triggers an **Unauthorized Excavation Emergency Alert**, halting unmonitored work.

### B. Post-Survey Verification & Closed-Loop Feedback
- Accepted anomalies go to **field verification** → Leak or False Alarm.
- Leak → Repair → history updated (`previous_incidents += 1`, `last_survey_date = today`) → Priority recalculated for that segment and neighbors.
- **Incident Engine** bypasses the normal cycle entirely for real-time pipeline strikes/punctures → immediate critical response + team dispatch.

## 9. Route Planner

Combines: Priority Score + segment location + inter-segment distance + team availability/capacity + open incidents → assigns segments to teams for the day.

**Hackathon simplification:** greedy nearest-neighbor assignment sorted by priority score is sufficient for the demo; note in the pitch that production would use proper VRP (vehicle routing problem) optimization.

## 10. MVP Scope for Hackathon

**Must-have (demo-critical):**
- Priority Engine computing scores from the 6-factor formula on sample/synthetic segment data
- Map or list dashboard showing segments color-coded by priority tier
- At least one full example walkthrough (like P-104 in the reference doc) shown end-to-end
- Configurable weight sliders (proves the "calibratable" claim visually)

**Should-have:**
- Confidence Engine with a toggle-able example (good survey vs. poor survey)
- Simple route assignment view (Team A/B/C → segment list)

**Stretch goals:**
- Seasonal/rain modifier on vulnerability score
- Incident Engine live demo (simulate a contractor report triggering a critical response)
- Historical trend view showing score recalculation after a repair

## 11. Suggested Tech Stack

- **Backend/scoring:** Python (FastAPI/Flask) or Node.js — simple REST endpoints per engine
- **Frontend/map:** React + Leaflet/Mapbox for the segment map; plain HTML/CSS+JS is fine for a hackathon
- **Data:** JSON/CSV synthetic dataset (5–15 sample segments is enough for a compelling demo)

## 12. Success Metrics / Demo Script

1. Show the network map with GIS attributes (depth, pressure, material) and segments colored by priority tier
2. Click P-104 → show the full factor breakdown (25+20+20+15+10+9 = 85) live
3. Toggle a weight slider → show score recompute in real time
4. Show 48-Hour Dig Notice Alert (contractor notification near P-104) → click "Dispatch On-Site Monitor" & "Share Safety Route Map"
5. Show Confidence Engine flag a low-confidence survey (wind/speed violation) → trigger re-survey
6. Simulate an incident (unauthorized construction damage report) → show it jump the queue to CRITICAL
7. Close with the one-line pitch: *"METHANOS isn't new detection hardware — it's the intelligence layer that tells existing survey teams where to go first, whether to trust what they found, and what to do next."*

## 13. Team Split

Work is divided into three tracks — see the separate task files:
- `Person1_Priority_Engine_Tasks.md`
- `Person2_Survey_Confidence_Engine_Tasks.md`
- `Person3_Frontend_Dashboard_Tasks.md`
