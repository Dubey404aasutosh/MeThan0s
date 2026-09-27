# METHANOS — Person 2: Survey Confidence Engine & Prevention/Incident Loop

## Overview
The **Confidence Engine & Prevention Loop** represents the operational trust layer of METHANOS. It answers two pivotal operational questions:
1. **"Can we trust this survey's data?"** (5-Factor Quality Control evaluation)
2. **"How do we prevent digs from puncturing pipes and verify anomalies?"** (48-Hour Pre-Excavation Early Warning & Anomaly Verification loop)

---

## 1. Quality Control & Confidence Scoring Formula

$$\text{Confidence Score} = \sum_{i=1}^{5} \text{Factor}_i \quad (\text{Max } 100)$$

| QC Check | Max Pts | Operational Acceptance Criteria |
|---|---|---|
| **GPS Coverage** | 20 | Continuous satellite lock ($\ge 90\%$ fix quality throughout survey) |
| **Sensor Health** | 20 | Zero optical sensor faults, error flags, or calibration drift |
| **Survey Speed** | 20 | Vehicle speed $\le 25\text{ km/h}$ (higher speeds cause methane plume pass-by error) |
| **Weather Suitability** | 20 | Ambient wind $\le 15\text{ km/h}$ & absence of heavy rain/suppression storms |
| **Route Completeness** | 20 | $\ge 90\%$ of designated pipeline segment physically surveyed |

### Decision Rule
* $\ge 60$ $\longrightarrow$ **`ACCEPT`**: Survey data is reliable. If elevated $\text{CH}_4$ ($\ge 2.5\text{ ppm}$) is detected, dispatches on-ground field verification.
* $< 60$ $\longrightarrow$ **`RE-SURVEY`**: Survey data is rejected due to environmental or sensor violations. Flagged for re-survey regardless of $\text{CH}_4$ reading.

### Demo Benchmark Records
* **High-Confidence (`S-2101` on `P-104`):** Score 100/100 (`ACCEPT` $\to$ `DISPATCH_FIELD_VERIFICATION`)
* **Low-Confidence (`S-2201` on `P-118`):** Score 43/100 (`RE-SURVEY` due to 36.8 km/h speed & 26.5 km/h gusting wind)

---

## 2. 48-Hour Pre-Excavation Early Warning & Prevention (PRD §8A)

```
T - 48 Hours: Contractor Submits Dig Notice
   │ (Coordinates, planned depth, start time, contractor ID)
   ▼
T - 36 Hours: GIS Conflict & Proximity Analysis
   │ • Checks dig depth vs pipeline burial depth (Depth Clash Hazard)
   │ • Checks proximity buffer (within 50m of gas line)
   │ • Fires Control Room alert: COMPLIANT_NOTICE (if >=48h) or SHORT_NOTICE_VIOLATION (if <48h)
   ▼
T - 24 Hours: Control Room Actions & Dispatch
   │ • [Dispatch Monitor]: Assigns utility patrol officer to supervise
   │ • [Share Route Map]: Issues annotated underground blueprint to contractor
   │ • Updates segment in Priority Engine: third_party_activity = "planned_48h_notice"
   ▼
T - 0 (Dig Day): Zero-Leak Supervised Digging
   │ • Shifts to "active_supervised"
   │ • On completion: resets hazard to "none" (Zero-leak clearance)
```

---

## 3. Anomaly Verification State Machine & Closed Loop

```
CH4 Anomaly Detected (Survey)
   │
   ▼
QC Confidence Check
   ├── If < 60  ──► Status: RE_SURVEY_QUEUED
   └── If >= 60 ──► Status: FIELD_VERIFY_PENDING
                          │
                          ▼
               Ground Field Investigation
                 ├── False Alarm ──► Status: FALSE_ALARM (Biogenic/sewer source)
                 └── Real Leak   ──► Status: CONFIRMED_LEAK
                                           │
                                           ▼
                                    Repair Executed
                                           │
                                           ▼
                                 Closed-Loop Feedback:
                                 • previous_incidents += 1
                                 • days_since_survey = 0
                                 • Priority Score Recalculated
```

---

## 4. Emergency Incident Engine (Queue Bypass)
* Action: `POST /api/incidents/report` (Simulates "Report Incident" demo button)
* Bypasses standard survey schedules
* Immediately overrides segment priority to `CRITICAL` (Score 95–100)
* Sets `third_party_activity = "direct_excavation_hazard"`

---

## 5. REST API Endpoints Summary

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/confidence/weights` | Returns 5-check QC weights and acceptance threshold (60) |
| `GET` | `/api/confidence/surveys` | Lists sample surveys with evaluated QC scores |
| `GET` | `/api/confidence/surveys/{id}` | Returns single survey evaluation |
| `GET` | `/api/confidence/examples` | Returns High Confidence (`S-2101`) & Low Confidence (`S-2201`) cards |
| `POST` | `/api/confidence/evaluate` | Evaluates arbitrary survey payload on the fly |
| `GET` | `/api/verification/tickets` | Lists ground verification tickets |
| `POST` | `/api/verification/tickets` | Ingests survey into verification state machine |
| `POST` | `/api/verification/tickets/{id}/verify` | Records field ground check (`leak` or `false_alarm`) |
| `POST` | `/api/verification/tickets/{id}/repair` | Completes repair and triggers closed-loop feedback |
| `GET` | `/api/verification/metrics` | Returns false alarm rate and verification analytics |
| `GET` | `/api/dig-notices` | Lists 48-hour contractor excavation notices and alerts |
| `POST` | `/api/dig-notices` | Ingests contractor notice (checks 48h rule & depth clash) |
| `POST` | `/api/dig-notices/{id}/dispatch-monitor` | Dispatches patrol officer and updates segment to `planned_48h_notice` |
| `POST` | `/api/dig-notices/{id}/share-map` | Issues digital underground blueprint to contractor |
| `POST` | `/api/dig-notices/{id}/start-dig` | Shifts excavation to `active_supervised` on dig day |
| `POST` | `/api/dig-notices/{id}/complete` | Safely closes notice with zero leaks |
| `GET` | `/api/incidents` | Lists emergency incident reports |
| `POST` | `/api/incidents/report` | Escalates segment to CRITICAL instantly (Demo button) |
| `POST` | `/api/incidents/{id}/resolve` | Resolves incident and clears emergency hazard |

---

## 6. Offline / Static Files for Frontend (Person 3)
Generate or refresh static JSON files anytime:
```bash
python export_static_json.py
```
Outputs:
* `segments.json` (12 pipeline segments with GIS attributes)
* `surveys.json` (Survey quality control logs and demo benchmark pair)
* `dig_notices.json` (48-hour contractor notices and control room alerts)
* `verification_tickets.json` (Anomaly ground verification queue)
