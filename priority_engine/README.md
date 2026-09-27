# METHANOS — Person 1: Priority Engine Reference Guide

## Overview
The Priority Engine is the core decision-making backend of METHANOS. It evaluates urban City Gas Distribution (CGD) pipeline segments and assigns an objective **Survey Priority Score (0–100)** to optimize mobile survey routing based on PNGRB-recognized integrity risk factors.

---

## 1. Quick Start

### A. Run API Server
```bash
python run_server.py
```
- API Base: `http://localhost:8000`
- Interactive Swagger Docs: `http://localhost:8000/docs`

### B. Run Test Suite
```bash
python -m unittest discover tests
```

### C. Offline / Static Mode (Person 3 Fallback)
```bash
python export_static_json.py
```
Exports `segments.json` in the project root with all 12 pre-scored segments.

---

## 2. Priority Scoring Formula

$$\text{Priority Score} = \sum_{i=1}^{6} \text{Factor}_i \quad (\text{Max } 100)$$

| Factor | Baseline Max | Evaluation Rule |
|---|---|---|
| **Previous Incidents** | 25 | 0 incidents $\to$ 0, 1 $\to$ 10, 2 $\to$ 18, 3+ $\to$ 25 |
| **PE / Service Vulnerability** | 20 | Steel Main $\to$ 5, PE Distribution $\to$ 15, PE Service Hotspot $\to$ 20 |
| **Days Since Survey** | 20 | $\min\left(20, 20 \times \frac{\text{days\_since}}{\text{target\_cycle}}\right)$ |
| **Third-Party Dig Activity** | 15 | None $\to$ 0, Planned 48h Notice $\to$ 5, Active Supervised $\to$ 10, Direct Excavation Hazard $\to$ 15 |
| **Rodent Damage History** | 10 | 0 incidents $\to$ 0, 1 $\to$ 3, 2–3 $\to$ 6, 4+ $\to$ 10 |
| **Public Consequence** | 10 | Low Density $\to$ 2, Residential $\to$ 5, Dense Residential $\to$ 7, Sensitive (School/Hospital) $\to$ 10 |

### Priority Tiers
* 🟢 **LOW**: `0 – 39` (Normal survey cycle)
* 🟡 **MEDIUM**: `40 – 69` (Survey when due)
* 🟠 **HIGH**: `70 – 84` (Bring forward in survey route)
* 🔴 **CRITICAL**: `85 – 100` (Urgent / earliest inspection priority)

---

## 3. Reference Benchmark (`P-104`)

Segment `P-104` validates engine calibration:
* Previous Incidents: 2 ($\to 18$)
* Material: `pe_service_hotspot` ($\to 20$)
* Days Since Survey: 9 / 12 ($\to 15$)
* Third-Party Activity: `direct_excavation_hazard` ($\to 15$)
* Rodent History: 4 ($\to 10$)
* Public Consequence: `dense_residential` ($\to 7$)
* **Total Score: 85** | **Tier: CRITICAL**

---

## 4. API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/health` | Service health status and segment count |
| `GET` | `/api/weights` | Returns default factor weights and baseline thresholds |
| `GET` | `/api/segments` | Returns all 12 segments sorted by priority with full GIS metadata |
| `GET` | `/api/segments/{id}` | Returns single segment breakdown |
| `POST` | `/api/recalculate` | Dynamic recomputation with custom slider weights |
| `POST` | `/api/segments/{id}/repair` | Closed-loop repair update (`previous_incidents += 1`, `days = 0`) |
| `POST` | `/api/segments/{id}/excavation-status` | Updates 48-hr dig status (`none`, `planned_48h_notice`, etc.) |
| `POST` | `/api/segments/{id}/emergency-incident` | Escalates segment to CRITICAL instantly (100) |
| `POST` | `/api/reset` | Resets dataset to default values |
