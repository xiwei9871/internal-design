---
name: blender-plan-geometry-extraction
description: Extract trustworthy 2D plan geometry from a Blender interior model — region-based object queries, wall masks from merged shell meshes, true XY footprints from mesh triangles, and model-vs-plan audits. Use before any CAD drafting that depends on the model.
---

# Blender Plan Geometry Extraction

Object names lie; coordinates don't. Extract plan truth from evaluated geometry, not name filters.

## Gotchas that burned us

- **Hidden objects return origin matrices**: objects keyframe-hidden at frame N report `matrix_world` at origin. `frame_set()` to a frame where everything is visible before reading bounds.
- **Names are unreliable**: toilets/vanities may not contain toilet/basin keywords (`FN_次主卫马桶` style or worse). Query by **coordinate region** — list every object whose XY center falls in the room rect.
- **Overheads aren't walls**: filter wall candidates by z (`z0>600` ⇒ cabinets/headers; `z1<1800` ⇒ half-walls/plinths).
- **Merged shells have useless bboxes**: `*_WALL_SHELL` / `*_HOUSE_WALLS_*` objects span the whole unit. Take their **vertex cloud** (z<1600) → rasterize 100mm/px → dilate → wall band mask for hit-testing.
- **Convex hull ≠ footprint**: wavy/curved objects (sculptural stairs) get fattened wrong by `convex_hull`. Instead project all mesh **loop triangles** to XY and `unary_union` → exact footprint (simplify tolerance ~8mm). Nested step shapes → visible riser line = `boundary(F_i) − F_{i+1}.buffer(60)`; a platform at the same height as the top step is a landing, not another riser — check z-tops to count real risers.
- **Z-top reveals design intent**: step z-tops (+150/+300/+450) vs main floor slab top (+450) told us it's a 3-riser split-level, not a stair to another floor. Always read z before labeling direction arrows (上/下).

## Standard extraction recipe

1. `frame_set` to an all-visible frame; use `evaluated_depsgraph_get` for evaluated bounds.
2. World-space `bound_box` (8 corners) ×1000 → mm.
3. Bucket by region rects (room coordinates), not regex.
4. Export JSON: `items{walls,doors,windows,floors,fixtures,furniture,lights}[{name,bbox6}]` + separate `clouds` for shells.
5. For curves/stairs/custom: dump loop-triangles to JSON, union them in Shapely outside Blender (no shapely in Blender's python).

## Audit patterns

- **Wall diff**: baseline wall polyline sampled ≤400mm segments vs dilated model mask → demolished/kept/new lists. Report segments, not just whole walls (partial demolition is common: kitchen west wall kept only its stubs).
- **Purpose audit**: lights/fixtures vs furniture — mirror light above actual mirror bbox, bedside lamp outside bed bbox, strip light parallel to cabinet run.
- **Missing-object detection**: empty region where design expects a fixture → `待现场确认` on the sheet, never invent a position.
