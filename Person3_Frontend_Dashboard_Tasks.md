# Person 3 — Frontend Dashboard, Map & Route Planner (Demo Face of the Project)

**Role:** You own everything the judges actually *see*. This is the highest-leverage role for hackathon scoring — a great demo UI can outweigh backend polish, so prioritize a clean, working, visually clear dashboard over extra features.

## Responsibilities

1. Build the **map/dashboard** showing pipeline segments color-coded by priority tier, displaying GIS attributes (**Depth of burial**, **Operating pressure**, and **Material**)
2. Build the **segment detail view** showing the full 6-factor breakdown when a segment is clicked (mirroring P-104 = 85/100)
3. Build **configurable weight sliders** that trigger a live recompute (via Person 1's function/API)
4. Build the **48-Hour Excavation Notice & Control Room Alert Panel** with real-time alert banner, "Dispatch On-Site Monitor", and "Share Route Map" actions
5. Build a simple **route/team assignment view** (Team A/B/C → assigned segments)
6. Build the **Confidence Engine display** (good survey vs. bad survey example, accept/re-survey badge)
7. Build the **Incident trigger demo** — a button/action that simulates a construction-damage report and shows the segment jump to CRITICAL live

## Deliverables for the Demo

- [x] Map or schematic view of 8–10 pipeline segments, color-coded 🟢🟡🟠🔴 by tier, with GIS metadata cards (depth in meters, pressure bar, material) (see `frontend/index.html` & `frontend/app.js`)
- [x] Click-through detail panel showing the 6-factor breakdown adding up to the total score (mirroring the P-104 = 85/100 example) (see `frontend/index.html` & `frontend/app.js`)
- [x] 48-Hour Dig Notice Panel: displays incoming excavation tickets, countdown to dig, proximity conflict, and `[Dispatch Monitor]` / `[Share Safety Map]` buttons (see `frontend/index.html`, `frontend/styles.css`, `frontend/app.js`)
- [x] A simple 3-column "Team A / Team B / Team C" route view listing assigned segments in priority order (see `frontend/index.html`, `frontend/styles.css`, `frontend/app.js`)
- [x] A toggle or two example cards showing Confidence Engine output (HIGH vs LOW confidence survey) (see `frontend/index.html`, `frontend/styles.css`, `frontend/app.js`)
- [x] One "Report Incident / Excavation Breach" button that visibly escalates a segment to CRITICAL in real time (see `frontend/index.html`, `frontend/styles.css`, `frontend/app.js`)

## What You Need From Teammates (lock these early — hour 1)

- **From Person 1:** the segment JSON shape (see their file) — build your UI against **mock/hardcoded JSON matching this shape first**, so you're never blocked waiting for their backend to be "done"
- **From Person 2:** the confidence/incident JSON shapes — same approach, mock it first

## Suggested Tech Stack

- React + Leaflet (or Mapbox GL) if you want a real map; or a simple SVG/CSS schematic layout of segments if a real map is overkill for your synthetic data (often faster to build and just as clear for judges)
- Keep it to one page/screen if possible — hackathon demos are stronger when judges don't have to navigate

## Suggested Build Order

1. Hardcode 8–10 mock segments matching Person 1's JSON shape → get the color-coded map/list rendering first, before any real backend exists
2. Build the click-through detail panel showing factor breakdown
3. Wire in real data from Person 1 once their function/endpoint is ready (should be a small swap if the shape was agreed early)
4. Add weight sliders + recompute
5. Add the route/team assignment view
6. Add Confidence Engine display + Incident button last (they're visually simpler, lower risk)

## Demo Flow to Design For

This is the script from the PRD — build your UI so this sequence is smooth and requires no fumbling on stage:

1. Show full map with GIS attributes (depth, pressure, material), colors visible at a glance
2. Click P-104 → factor breakdown visible, adds to 85
3. Drag a weight slider → watch score/colors update live
4. Show 48-Hour Dig Notice Alert (contractor notice near P-104) → click "Dispatch On-Site Monitor" & "Share Safety Route Map"
5. Show a Confidence example flip from HIGH to LOW (bad weather/speed triggers RE-SURVEY)
6. Click "Report Incident" → a segment jumps to CRITICAL instantly
7. End on the team/route view: "Team A should visit P-104 today"

## Stretch Goals

- Smooth color transition animation when scores change (small visual polish, judges notice this)
- A tiny legend/key explaining tier thresholds (0–39 / 40–69 / 70–84 / 85–100) so judges don't have to ask
- Mobile-responsive layout if you have spare time (nice but not demo-critical)

## Sync Points with Teammates

- **Hour 1:** lock JSON shapes with both teammates before anyone writes real logic
- **Mid-build checkpoint:** confirm Person 1's weight-slider recompute function signature works with what you built
- **Before final demo run-through:** rehearse the full click sequence at least twice as a team
