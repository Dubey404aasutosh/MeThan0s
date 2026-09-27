# Person 1 — Priority Engine (Backend / Scoring Logic)

**Role:** You own the "brain" of METHANOS — the algorithm that decides which pipeline segments get surveyed first.

## Responsibilities

1. Build the **Priority Score calculation** using the 6-factor weighted formula (see PRD §6)
2. Build the **synthetic dataset** of pipeline segments (8–12 segments) with realistic values for each factor including **GIS attributes** (`depth_meters`, `operating_pressure_bar`, `material`, `coordinates`)
3. Support **Third-Party Dig Activity states**: `none` (0), `planned_48h_notice` (5), `active_supervised` (10), `direct_excavation_hazard` (15)
4. Expose a simple API/function that the frontend can call to get scores and segment GIS attributes
5. Make the 6 weights **configurable** (not hardcoded) so the frontend can offer sliders
6. Implement the **priority tier** classification (LOW/MEDIUM/HIGH/CRITICAL)

## Deliverables for the Demo

- [x] A working scoring function: `calculate_priority(segment_data, weights) → {score, tier, factor_breakdown}` (see `priority_engine/scoring.py`)
- [x] Sample dataset (JSON or CSV) with 12 segments covering a spread of tiers (3 LOW, 4 MEDIUM, 3 HIGH, 2 CRITICAL) (see `priority_engine/dataset.py` & `segments.json`)
- [x] One fully worked example matching the reference doc (P-104 = 85/100, CRITICAL) sanity-checked and unit-tested
- [x] A production-ready REST API (`GET /api/segments`, `GET /api/segments/{id}`, `POST /api/recalculate`, `POST /api/segments/{id}/repair`, etc.) AND static `segments.json` fallback
- [x] Configurable weight sliders support with dynamic normalization
- [x] Stretch Goal: Seasonal Monsoon / Rain modifier (amplifies PE vulnerability during monsoon periods)
- [x] Stretch Goal: Closed-loop `recalculate_after_repair(segment_id)` and emergency incident escalations

## Interface Contract (what Person 3 needs from you)

Your output for each segment should look like this — agree on this shape early so integration doesn't break late:

```json
{
  "segment_id": "P-104",
  "score": 85,
  "tier": "CRITICAL",
  "material": "pe_service_hotspot",
  "depth_meters": 0.8,
  "operating_pressure_bar": 0.1,
  "third_party_activity": "direct_excavation_hazard",
  "factors": {
    "previous_incidents": 18,
    "pe_vulnerability": 20,
    "days_since_survey": 15,
    "third_party_activity": 15,
    "rodent_history": 10,
    "public_consequence": 7
  },
  "location": { "lat": 28.6139, "lng": 77.2090 }
}
```

## Scoring Formula Reference

| Factor | Max | Rule |
|---|---|---|
| Previous incidents | 25 | 0→0, 1→10, 2→18, 3+→25 |
| PE/service vulnerability | 20 | steel main→5, PE distribution→15, PE hotspot→20 |
| Days since survey | 20 | `min(20, 20 × days_since / target_cycle)` |
| Third-party activity | 15 | none→0, planned_48h_notice→5, active_supervised→10, direct_excavation_hazard→15 |
| Rodent history | 10 | 0→0, 1→3, 2-3→6, 4+→10 |
| Public consequence | 10 | low-density→2, residential→5, dense residential→7, sensitive→10 |

## Suggested Build Order

1. Hardcode the formula for one segment (P-104) and verify it matches 85/100 — this is your correctness check
2. Generalize into a function that takes any segment's raw data + the weight config
3. Build the synthetic dataset (vary values so you get a nice spread across tiers — makes the demo visually interesting)
4. Wrap it in an endpoint or export as JSON for Person 3 to consume
5. If time remains: add the weight-configuration piece (accept custom weights, recompute)

## Stretch Goals (only if core is done early)

- Rain/seasonal modifier: add a 7th optional factor or a multiplier applied to vulnerability during "monsoon mode"
- Simple `recalculate_after_repair(segment_id)` function that resets incident-related factors after a repair is logged — ties into the feedback loop story

## Sync Points with Teammates

- **With Person 2:** confirm the segment_id naming convention matches what their Confidence Engine will reference
- **With Person 3:** lock the JSON shape above in the first hour so they can start building the map UI against mock data immediately, even before your real logic is done
