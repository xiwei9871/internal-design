# PASCAL_VISUAL_FIDELITY_DIAGNOSIS

Date: 2026-09-29. Trigger: user opened `pascal-b1-full-v1` and judged
`PASCAL FULL SCENE VISUAL FIDELITY = FAIL`. This document is the
visual-geometric proof of whether Pascal represents the same house as
`PRE_BLENDER_MASTER_V2 / B1_BLOCKOUT_V003`.

## 1. Scene identity

See `PASCAL_ACTIVE_SCENE_IDENTITY.md`. Reviewed-failed scene =
`pascal-b1-full-v1` (v4, 141 nodes). Diagnostic scenes rebuilt under project
`c-type-home-pascal-b1-v1`: arch-only v3 (101 nodes), blocks v2 (157),
full-v2 v2 (157). PoC/demo/stale scenes excluded.

## 2. Source / reference identity

- Architectural truth: `PRE_BLENDER_MASTER_V2.FCStd` — untouched.
- Canonical extraction: `design/b1_blockout/b1_model.json`
  (`canonical_task01_mm`, x-east y-north mm; `transform_fc_to_canon`
  = translation only, no rotation/flip — matches FreeCAD Top view).
- Render reference: `B1_BLOCKOUT_V003.blend` — untouched.

## 3. Coordinate transform audit

| check | result |
|---|---|
| X/Y swap | none — canonical x → Pascal x |
| sign flip | **FOUND + FIXED**: canonical +y north was written to Pascal +z; Pascal's 2D north convention is −z → whole plan displayed south-up. Converter now uses `mz(v) = −v·0.001` for all north coords (walls, openings, zones, slabs, item positions). Verified in-browser: R-BALC-N (y≈12250) renders at top, R-BALC-LIFE (y≈950) at bottom. |
| rotation convention | furniture canonical rects are axis-aligned; `rotation:[0,0,0]` used. No degree/radian path exists in converter. |
| centre vs corner origin | item `position` = rect centre ✓ (GLB footprint centre); wall `start/end` = centreline with `thickness` ✓; zones = polygon points ✓ |
| width/depth swap | `actual_project_size_m=[w,d]` → `scale=[w, h, d]` ✓ (verified 0.0 mm on overlay) |
| wall endpoint ordering | centreline preserved; residual 0.0 mm |
| local/global confusion | opening `position[0]` = distance along host wall from `start` ✓ (9/9 windows exact) |
| mm → m scale | `MM=0.001` uniform |
| room-local as world | none — all coords are site-frame |

Root cause of the FAIL judgement: the plan was displayed **north/south
mirrored** (data correct, view convention wrong), plus catalog GLBs failed to
load (CORS) leaving red wireframes — together making the scene unrecognisable.

## 4. Architecture visual overlay — **PASS**

`MASTER_V2_2D_REFERENCE.png` vs `PASCAL_ARCH_2D.png`, same frame/scale/crop/
north-up. Overlay `PASCAL_VS_MASTER_ARCH_OVERLAY.png`: wall outlines, 13 door
openings, 10 window/glazing segments, bay fronts, balconies all coincide.
Numeric: every canonical wall centreline covered, max residual **0.0 mm**.

`ARCHITECTURE_VISUAL_OVERLAY = PASS`

## 5. Furniture visual overlay — **PASS**

`pascal-b1-blocks-v1` uses only `blockout-box` (local unit-cube GLB, origin
= footprint centre, base y=0) scaled to actual MASTER_V2 w×d.
`MASTER_V2_FURNITURE_PLAN.png` vs `PASCAL_FURNITURE_PLAN.png`;
`PASCAL_VS_MASTER_FURNITURE_OVERLAY.png` shows all 56 footprints coincident.
Numeric: max centre residual **0.1 mm**; zero unmatched.

`FURNITURE_VISUAL_OVERLAY = PASS`

## 6. Metadata vs rendered bbox (8 objects, FIDELITY_NUMERIC.json)

Blockout rendered bbox == metadata == canonical for all 8. Catalog meshes
(`pascal-b1-full-v2`) are systematically undersized — **VISUAL_ASSET_SIZE_MISMATCH**:

| object | canonical mm | catalog rendered mm | asset |
|---|---|---|---|
| SOFA_3S | 900×2300 | 738×1548 | sofa |
| SOFA_2S | 1900×850 | 1558×572 | sofa |
| CHAISE | 1700×900 | 1244×642 | livingroom-chair |
| DINING_TABLE | 1600×800 | 1378×753 | dining-table |
| GUEST_BED | 1800×1200 | 1364×957 | double-bed |
| OWNER_BED | 2100×1500 | 1591×1196 | double-bed |
| MOTHER_BED | 2100×1500 | 1591×1196 | double-bed |
| STUDY_WORKSTATION | 350×1650 | 3×17 | table |

→ catalog meshes render ~65–80% of project footprint (table effectively
degenerate). Catalog visual assets remain banned for fidelity use;
`blocks`/`arch-only` are the trustworthy scenes.

## 7. Asset loading status

- `blockout-box/model.glb` (local): `GET http://pascal.localhost:57071/… 200` ✓
  after patching the editor's asset resolver to honour relative paths on the
  local host (was fetching `editor.pascal.app` → CORS).
- `save_scene` rejects absolute http `asset.src` (`graph_invalid`); relative
  `/items/...` required — converter emits relative paths.

## 8. Remaining representation limitations (unchanged, documented)

- Synthetic host walls for 4 bay fronts + G-DIN-LIV glazing (`L-05`);
- parapet glazing clamped to host (`CLAMPED_TO_HOST_WALL`);
- D-SM (−236 mm) / D-MB (−66 mm) host-gap clipping (`L-02`);
- blockout heights are `BLOCKOUT_TEMP_VALUE`, not design heights;
- item meshes carry no rotation detail beyond axis-aligned footprint.

## 9. Gate decision

```
ARCHITECTURE_VISUAL_OVERLAY = PASS
FURNITURE_VISUAL_OVERLAY      = PASS
```

Per protocol this allows return to `DRAFT_HUMAN_REVIEW` **only after** the
user opens `pascal-b1-blocks-v1` (recommended) or `pascal-b1-full-v2` and
confirms "这就是世纪欣园当前方案". Until then:

```
PASCAL_B1_FULL = FAIL   (gate held pending human visual confirmation)
Human Review = STOPPED
B2 = HOLD
formal_cad_allowed = false
```

## 10. Follow-up gates (2026-09-29)

Two upstream gaps identified and split:

- `PRE_3D_FURNITURE_DIMENSION_GATE` = **HUMAN_APPROVED_WITH_TO_VERIFY** —
  `design/b1_blockout/furniture_3d_dimension_register_v01.json` +
  `FURNITURE_3D_DIMENSION_REGISTER_V01.{md,csv}` + anomaly report (FAIL=0).
  TO_VERIFY (non-blocking): 3kg wall-mounted washer mount_z; freezer final
  SKU; final floating media treatment.
  Semantic corrections applied: `主人椅`→STUDY_ARMCHAIR; `主卧床头柜占位`
  →HEADBOARD (SOURCE_LABEL_SEMANTIC_CORRECTION); living TV unit →
  MEDIA_CABINET h480 floor-standing.
- `PASCAL_WALL_TOPOLOGY` = **FAIL** — wall lines without explicit thickness
  were dropped by the converter → floating glass / missing walls. Next gate
  before any Pascal re-review.
