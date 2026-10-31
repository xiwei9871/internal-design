---
name: blender-plan-geometry-extraction
description: Extract trustworthy 2D plan geometry (floor and ceiling zones, steps, fixtures) from a Blender interior model by reading mesh faces read-only, then audit it against the as-built CAD base. Use before any CAD drafting that depends on the model. Never segments rendered images.
---

# Blender Plan Geometry Extraction

Object names lie; coordinates don't. Read evaluated mesh geometry, never rendered pixels.

## Script (read-only, never saves the .blend)

```bash
blender -b MODEL.blend -P scripts/extract_plan_geometry.py -- inventory inventory.json
blender -b MODEL.blend -P scripts/extract_plan_geometry.py -- extract cfg.json extract.json
```

- `inventory`: every render-visible mesh with bbox, collection, materials and horizontal face
  areas (`floor_m2` = up-facing below 700 mm, `ceil_m2` = down-facing above 2200 mm). Use it to
  pick the right object names for the config.
- `extract`: triangles (XY + mean Z, mm) of horizontal faces for objects matched by regexes in
  `cfg.json` (`floor`, `ceiling`, `stair`, `fixture`). Union them in Shapely outside Blender.
- Record the model SHA256 before and after. A changed hash is FAIL.
- The output is deterministic: two runs on the same file must give byte-identical JSON.

## Rules

- **Never** build zones from a top-view render, colour masks or contour tracing. POC V01 measured
  that method against mesh geometry: wood IoU 0.82, tile IoU 0.77, one room missed.
- Visible means `hide_render` is off on the object and on every collection holding it. Hidden
  helper objects (old designs, review markers) are not design truth.
- Floors: prefer per-room finish objects (e.g. `PRESENTATION_FLOOR_*`) for material and room use;
  the slab objects give level (Z) and the residual area.
- Ceilings: down-facing faces give the soffit level. Where two ceiling meshes share a boundary,
  that boundary is the step line.
- Steps: read Z-tops. 150 / 300 / 450 with a +450 slab = three risers, not a stair to another floor.
  A platform level with the top step is a landing, not a fourth riser.
- Merged shells (`*_WALL_SHELL`) have whole-house bboxes. Take walls from the CAD base instead.
- Convex hull ≠ footprint. Union loop triangles for curved or wavy objects.
- Hidden objects can report origin matrices at some frames. `frame_set()` to an all-visible
  frame before reading bounds if animation is present.

## Audit before drafting

1. Confirm owner-stated parameters against extracted Z (split-level height, ceiling soffits,
   step levels). On disagreement, draw per the owner parameter and list the difference.
2. Subtract CAD-base walls from model zones; run `zone_qa.py`
   (`../interior-renovation-cad-docs/scripts/`) for overlaps and gaps.
3. Fixtures: query by coordinate region, not by name. A missing fixture is `待现场确认`; never
   invent a position.
