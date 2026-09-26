# F1R-01H — Geometric Clearance Verification v2

This report preserves the F1R-01H furniture layout. It does not modify V02/V03, canonical data or formal CAD.

## Measurement method

- A0.4 normalized DXF block references are inserted at the F1R-01H placements and their transformed extents are audited within 1 mm.
- Existing canonical wall rectangles, KEEP kitchen, ramp, stair and registered openings are treated as geometry obstacles.
- Route values use sampled cross-sections along architectural anchor polylines. The old F1 path rectangles are retained only as reference envelopes.
- `path_blocker_count=0` remains a separate direct-intersection diagnostic; it is not a clearance pass.

## Actual vs reference

- Entry → living: **2280 mm actual**; reference min 900 / preferred 1100 mm.
- Living → stair: **1200 mm actual** = approach 2580 + stair opening 1200; reference secondary min 750 / preferred 900 mm. `TO_VERIFY`.
- Living → north balcony: **850 mm actual** = approach 980 + registered opening 850; reference min 900 / preferred 1100 mm. `TO_VERIFY`.
- Sofa-to-sofa: **1050 mm actual transformed-bbox gap**.
- Sofa-to-lounge: **900 mm actual transformed-bbox gap**.
- Actual largest clear rectangle: **2100.0 × 3000.0 mm** at `[5600.0, 7800, 7700, 10800.0]`; this is descriptive, not pass/fail.
- Dining chair pull-out: **150.0 mm actual** vs reference 600 mm.
- Behind-seated dining passage: **180.0 mm actual** (north side 180.0 mm; south side 2450.0 mm) vs reference 900 mm; `TO_VERIFY`.
- Table/chair to KEEP kitchen: **700.0 mm actual table edge gap** vs reference 1000 mm.

## Result

Geometry method is corrected, but the measured living→stair, living→balcony, behind-seated passage and kitchen-edge numbers remain human-review items. Do not write the layout into formal CAD yet.
