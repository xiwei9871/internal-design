# B0 EXISTING-STATE BASELINE — Report

Status: **PASS** — exact-geometry overlay gate passed; B1 not started
Frozen: `ARCH_XY = FROZEN` · `Z_DATUM = FROZEN` · `LEVEL_SEMANTICS = FROZEN`
Model: `design/blender_b0/B0_EXISTING_AS_IS.blend`
Build: `scripts/blender_b0_build.py` + `scripts/b0_zone_coverage_audit.py`
       + `scripts/b0_section_v5.py` (all reproducible)

## Authority chain

```
CAD XY truth   : 世纪欣园FF_freecad_WORKING_v2.dxf (S-S.WALL / S-楼梯 / F-DOOR)
Plan semantics : source/source_plan_original.jpg (room names, CA 空调机位)
Human rulings  : split-level datums, leisure=UPPER, GAP-06/08/17/20 rulings
Level field    : B0_LEVEL_FIELD.json
                 role = SEMANTIC_HELPER_ONLY
                 geometry_authority = false, physical_ground_truth = false
                 zones assign Z only; XY boundary always comes from CAD
```

## Exact-geometry closure (final freeze audit)

Every final Existing XY surface audited against the live `.blend` objects
(dumped from `B0_EXISTING_AS_IS.blend`, not the input files):

| Object | geometry_source |
|---|---|
| LOWER floor (`FLOOR_LOWER`) | CAD_EXACT_POLYGON + CAD_SNAPPED_CONTOUR |
| UPPER floor (`FLOOR_UPPER`) | CAD_EXACT_POLYGON + CAD_SNAPPED_CONTOUR |
| LOWER ceiling (`CEILING_LOWER`) | same XY as floor regions |
| UPPER ceiling (`CEILING_UPPER` + `CEILING_STAIRWELL`) | same XY + CAD stair-zone rect |
| split-level fascia (`FASCIA_PLATFORM_CURVE`, `FASCIA_CEILING_CURVE`) | CAD_EXACT — S-楼梯 r1000 arc, no offset |

Region construction (`B0_FLOOR_REGIONS.json`, 11 lower / 25 upper):
room polys authored from CAD coordinates (`CAD_EXACT_POLYGON`); uncovered
gap areas traced on the 50 mm field, then every boundary edge snapped onto
CAD wall faces / zone edges / D-SM jambs / the r1000 arc
(`CAD_SNAPPED_CONTOUR`, residual deviation 0 mm). Seam patches fill
door-jamb slivers. Zero uncovered interior cells; zero self-intersections.

Overlay gate (measured on blend geometry vs CAD linework):

- straight boundaries: max deviation **0.0 mm** (≤ 1 mm) ✓
- curved boundary: max chord deviation **0.34 mm** (≤ 2 mm;
  arc tessellation 3° → r·(1−cos1.5°)) ✓
- 50 mm staircase artifacts: **none** — no grid-derived edges remain
- `B0_FLOOR_CAD_OVERLAY.png` / `B0_CEILING_CAD_OVERLAY.png`

## Bug found during this build (fixed)

`b0_zone_coverage_audit.py` rasterized wall bands with the X-axis origin on
the Y axis (`ci()` used for both), shifting every wall ~2000mm. That produced
phantom wall cells, false LOWER↔UPPER adjacencies and miscounted coverage.
Fixed (`cj()` for Y); the level field, V8 map and Blender build were
regenerated. All downstream artefacts above the raster changed slightly —
reviewed again against the approved rulings (nook=LOWER, corridor=UPPER,
stair zone isolated) — consistent.

## Gate results — B0_GEOMETRY_GATE_V2.json

| Gate | Result | Evidence |
|---|---|---|
| A XY ground truth | PASS | `FASCIA_PLATFORM_CURVE` follows S-楼梯 r1000 arc; floor/ceiling from exact region polys (`B0_FLOOR_REGIONS.json`); no zone polygon created walls |
| B Z datum | PASS | step tops 0.15 / 0.30 / 0.45 m; FLOOR_LOWER top 0.0; FLOOR_UPPER top 0.45 |
| C Ceiling | PASS | region-level ceilings: CEILING_LOWER @2.8, CEILING_UPPER @3.25 (+ stairwell plate); no per-room tiles |
| D Openings | PASS | 9/9 glazing objects; LEAF_D107 at 26.3° |
| E Future isolation | PASS | ramp in `91_ACCESSIBILITY_OPTIONS`, `physical_ground_truth=false`, hidden by default |
| F Unknowns | PASS | GAP-20 = isolated `99_TO_VERIFY` plate; no floor/ceiling built there |

## What is in the model

- 68 wall bands: 19 LOWER_ONLY (0→2.8), 17 UPPER_ONLY (0.45→3.25),
  15 ENVELOPE_CONTINUOUS (0→3.25), 4 CONTINUOUS_SPLIT_BOUNDARY, 7 PARAPET
  — see `B0_CONTINUOUS_WALL_AUDIT.json/.png`
- Floors: `FLOOR_LOWER`/`FLOOR_UPPER`, exact CAD region polygons from
  `B0_FLOOR_REGIONS.json`; stair zone subtracted (steps form the surface)
- Stairs: `STEP_0/1/2` tops 150/300/450, zone 7200–7800 × 6600–7800,
  ascending west→east into the leisure platform
- Fan leisure hall: full UPPER +450, real S-楼梯 arc preserved
  (line (5700,4700)→(5700,5600) → r1000 arc c=(6700,5600) → (7200,6600))
- Fascia: `FASCIA_PLATFORM_CURVE` (0→0.45) + `FASCIA_CEILING_CURVE`
  (2.8→3.25) along the curve — the only confirmed open level edge
- Ceilings: continuous per-level surfaces, `CEILING_REVIEW_TRANSPARENT`
  material (alpha 0.12, EEVEE verified)
- Openings: 9 verified windows/doors incl. D-107 angled door leaf
- Furniture/sanitary: Pascal v3 guide blockouts, `05_HUMAN_DESIGN_GUIDE`,
  mutable, not ground truth
- Ramp: `91_ACCESSIBILITY_OPTIONS`, hidden, future-only
- Collections: `00_EXISTING_ARCH_GROUND_TRUTH` … `99_TO_VERIFY`

## PASS — verified

- Split-level datum: LOWER 0/2800, UPPER 450/3250, 3×150 stairs
- Fan leisure arc geometry from CAD (not rectangularised)
- Corridor/strip split via wall topology (single physical transition)
- 9 openings incl. D-107 angle
- Future intent fully isolated from Existing model

## TO_VERIFY — open items (non-blocking)

- **GAP-20** north recess (x12900–15200, y11300–13400): isolated magenta
  plate, no floor/ceiling; needs plan/CAD confirmation
- AC equipment niche (x15300–16200, y2550–4400): `EXTERIOR_AC_EQUIPMENT_ZONE`
  plate shown gray, `interior_floor=false`, exact detail TO_VERIFY
- Stair void ceiling height assumed 3250 (upper datum) — site verify
- Beam/soffit/pipe-boxing dims: deliberately NOT estimated from photos
- `OPEN_BOUNDARY` pocket at strip/corridor junction (x5700–5900, y3900–4100):
  resolved by corrected wall raster — zero unverified open edges remain

## FUTURE_OPTION — intentionally excluded from Existing

- `RAMP_FUTURE_OPTION` (5728–7828 × 4728–5828): accessibility intent,
  `physical_ground_truth=false`
- Any demolition of the fan leisure area / living expansion = B1+ scope

## Outputs

| File | Content |
|---|---|
| `B0_LEVEL_ZONE_MAP_V8_CLEAN.png` | approved level map (regenerated, unchanged semantics) |
| `B0_EXISTING_TOP_V1.png` | top ortho, ceiling hidden |
| `B0_SPLIT_LEVEL_SECTION_V5.png` | y=7300 cut: nook→stairs→leisure, all datum labels |
| `B0_SPLIT_LEVEL_AXON_V5.png` | axon, ceiling hidden |
| `B0_CEILING_AXON_V5.png` | axon, near-transparent ceilings (EEVEE) |
| `B0_EXISTING_VS_FUTURE_V1.png` | top view + orange ramp overlay |
| `B0_CONTINUOUS_WALL_AUDIT.png/.json` | per-wall span classification |
| `B0_GEOMETRY_GATE_V2.json` | 6 gates + geometry_source_audit, all pass |
| `B0_FLOOR_REGIONS.json` | exact floor/ceiling region polygons + edge report |
| `B0_FLOOR_CAD_OVERLAY.png` | floor projection vs CAD linework |
| `B0_CEILING_CAD_OVERLAY.png` | ceiling projection vs CAD linework |
| `B0_LEVEL_FIELD.json` | 50mm semantic raster — SEMANTIC_HELPER_ONLY |

## STOP STATE

`B0_EXISTING_AS_IS.blend` is the permanent AS-IS master:
`ARCH_XY / Z_DATUM / LEVEL_SEMANTICS / OPENINGS = FROZEN`,
`EXISTING/FUTURE = SEPARATED`.
Integrity pinned by `B0_FREEZE_MANIFEST.json` (SHA256 of blend, CAD DXF,
floor regions, Z-datum spec, gate JSON, level field, V8 map).
Do not edit for renovation proposals — all B1 work lives in
`B1_RENOVATION_DESIGN.blend` (branched copy).
GAP-20 and the AC-niche detail remain non-blocking TO_VERIFY items
listed above.
