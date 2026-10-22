# PASCAL_B1_FULL_V1 vs B1_BLOCKOUT_V003 — cross-check

V003 (`世纪欣园_B1_BLOCKOUT_V003.blend`) remains frozen reference/fallback.
Both derive from MASTER_V2/`b1_model.json`, so this is an independent
representation check, not a re-derivation.

## Furniture center comparison (real geometry, Blender meters)

47 `F.*` objects extracted from V003 vs 56 Pascal items:

| result | value |
|---|---|
| matched by label | 46 (V003 `餐椅.001` = Blender dedup suffix of the 2nd 餐椅; Pascal keeps source labels 餐椅003/餐椅004) |
| center drift | **45/46 ≤ 0.1 mm**; `餐椅` shows 1495 mm because label-matching paired two different chair instances — naming artifact, not drift |
| width/depth delta | ≤ 0.1 mm on all 46 |
| only in Pascal | 9 `K-*` kitchen cabinets (canonical cabinet runs — V003 folded them into a single `F.橱柜` placeholder) |

Coordinate frames are identical (canonical mm → m, same axes): e.g.
三人位 (3.8511, 10.3658), 餐桌 (3.8276, 3.4644), nas (14.9929, 6.8641) match
exactly in both files.

## Structure

| element | V003 | Pascal B1 |
|---|---|---|
| walls | 168 raw MESH boxes | 40 parametric walls + live door/window cutters |
| doors | `DOOR.*` meshes | 13 semantic door nodes (incl. 3 GLASS_DOOR, 1 OPEN) |
| windows | implicit/mesh | 10 window nodes (6 registry + 4 bay fronts) |
| rooms | annotation objects | 19 semantic zones w/ polygons |
| semantics | name-prefix convention | native type + metadata + id map |

## Differences traced to source

1. **K-* kitchen cabinets**: Pascal models all 9 canonical cabinet elements;
   V003 used one `F.橱柜` block. Pascal is the more complete representation of
   `kitchen_cabinets` in `b1_model.json`. Not a discrepancy — finer granularity.
2. **Bay fronts / glass partition**: Pascal adds 4 `*-BAY-FRONT` glazed bands +
   1 `G-DIN-LIV` synthesized host wall (LIMITATION L-05). V003 drew these as
   simple meshes. Geometry is identical in plan; representation differs.
3. **Split-level steps / ramp**: V003 had blockout meshes; Pascal uses flat
   annotation zones (L-06). Positions match; 3D ramp/step shape is not modeled
   in either.
4. **Item meshes**: V003 = dimensionally-exact boxes; Pascal = stretched catalog
   placeholders over identical footprints (L-07). Plan footprint equal; mesh
   appearance differs.

## Verdict

No spatial discrepancy beyond the catalogued representation differences.
Pascal full scene is faithful to the same MASTER_V2 source as V003 and adds
native room/door/window semantics + review tooling. V003 stays frozen as
fallback; Pascal B1 is the review representation going forward.
