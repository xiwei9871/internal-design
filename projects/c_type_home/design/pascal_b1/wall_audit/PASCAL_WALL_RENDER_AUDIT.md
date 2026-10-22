# PASCAL_WALL_RENDER_AUDIT — register → node → stored rendered geometry

Date: 2026-09-30. Scene audited: `pascal-wall-debug-v1` v2 (40 wall nodes ONLY — no
furniture/zones/doors/windows/glass/kitchen/fixtures). Stored graph fetched via
`GET /api/scenes/pascal-wall-debug-v1`.

Method: for each FINAL_WALL_REGISTER_V01 wall (EXISTING_KEEP / NEW_WALL / BAY_ENCLOSURE /
PARAPET), locate the Pascal wall node covering ≥50% of its rect, then verify the node's
rendered-geometry spec — non-zero length, thickness ≥40mm, resolvedHeight>0, visible=true
(Pascal wall nodes ARE the render geometry spec; `describe_node` confirms
`resolvedHeight`/`heightIsExplicit` server-side). Per-wall table:
`pascal_wall_render_audit.json`.

## Result

```
register walls (KEEP/NEW/BAY/PARAPET) : 42
RENDERED_CORRECTLY                    : 42/42
MISSING_NODE                          : 0
NODE_EXISTS_BUT_NO_VISIBLE_GEOMETRY   : 0
WRONG_HEIGHT                          : 0  (38×2.5m walls, 4×1.05m parapets)
WRONG_THICKNESS                       : 0  (all ≥ 50mm)
WRONG_TRANSFORM                       : 0
```

## Why the previous screenshot still "looked" short of walls

The stored node set is complete per the register — the visual sparseness is explained by:

1. **Intended open boundaries** (reconciliation): corridor north band REMOVED_BY_RENOVATION,
   kitchen/dining divider pier REMOVED_BY_RENOVATION, DIN-LIV glazed screen (no solid wall
   by design), stair split-level treads = NON_WALL. These boundaries have no wall *by design*.
2. Wall nodes render as thin 100–250mm prisms at WALL_H=2.5 (TEMP) — visually lighter than
   the CAD double-line bands.
3. The stale draft/version mix earlier (save_scene `id` vs `scene_id`, bridge writes 502).

## Residual issues (documented, non-blocking)

- `W-INT-X13000` vs `W-NBALC-E-PAR`: parapet band nested inside interior wall band
  (120×2500 overlap) — pre-existing duplicate registration, needs semantic adjudication.
- Study bay front depth: master remnant linework sits ~200mm deeper than baseline
  W-EXT-NE rect used for `W-BAY-STUDY-F` — TO_VERIFY bump-out depth.
- WALL_H=2.5 remains TEMP storey height; parapets 1.05 TEMP.
- `W-BAY-STUDY-JW/JE` thickness 100 = BLOCKOUT_TEMP_VALUE (existence CONFIRMED).
- Bay front deeper in master linework (~11750 vs 11550 used) — 200mm TO_VERIFY.

## Infrastructure note (why writes appeared to hang)

- `save_scene` requires `includeCurrentScene: false` + `graph` — default TRUE silently
  saved the bridge's loaded scene instead of the graph argument (this is how the first
  wall-debug save came back with 154 nodes).
- Python `urllib` picks up macOS *system* proxy and 502s loopback MCP; fixed in
  `scripts/pascal_mcp_http.py` via `ProxyHandler({})`. curl unaffected.
- `get_scene` ignores its arg and returns the bridge-current scene; use
  `GET /api/scenes/{id}` for the stored graph.

## Gate

```
unexplained_wall_segments = 0
missing_confirmed_walls   = 0
duplicate_wall_segments   = 0 new (1 pre-existing overlap flagged above)
overlay                   = MASTER_VS_PASCAL_WALL_OVERLAY_V2.png
PASCAL_WALL_ONLY_VISUAL   = HUMAN_REVIEW  → open pascal-wall-debug-v1
```
