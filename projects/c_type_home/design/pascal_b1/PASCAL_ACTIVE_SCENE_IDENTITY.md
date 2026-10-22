# PASCAL_ACTIVE_SCENE_IDENTITY

Retrieved from live Pascal records (`list_scenes` / `load_scene` via MCP, 2026-09-29 13:45 UTC).
Editor: `pascal editor --no-open --port 57071`, DB `~/.pascal/data/pascal.db`.

## Active diagnostic scenes (project `c-type-home-pascal-b1-v1`)

| scene_id | name | version | nodes | created_at | updated_at |
|---|---|---|---|---|---|
| pascal-b1-arch-only-v1 | PASCAL_B1_ARCH_ONLY_V1 | 3 | 101 | 2026-09-29T09:15:03Z | 2026-09-29T13:44:06Z |
| pascal-b1-blocks-v1 | PASCAL_B1_BLOCKS_V1 | 2 | 157 | 2026-09-29T09:25:18Z | 2026-09-29T13:44:06Z |
| pascal-b1-full-v2 | PASCAL_B1_FULL_V2 | 2 | 157 | 2026-09-29T09:25:18Z | 2026-09-29T13:45:05Z |

URLs:

    http://pascal.localhost:57071/scene/pascal-b1-arch-only-v1
    http://pascal.localhost:57071/scene/pascal-b1-blocks-v1
    http://pascal.localhost:57071/scene/pascal-b1-full-v2

All three contain the north-fixed geometry (canonical +y north → Pascal −z),
regenerated 2026-09-29T13:44–13:45Z. `full-v2` keeps catalog asset ids for
diagnostic comparison; `blocks-v1` uses only `blockout-box` (local unit cube).

## Superseded / not authoritative

| scene_id | note |
|---|---|
| pascal-b1-full-v1 | v4, 141 nodes — SOUTH-UP orientation bug (canonical +y → +z). The scene the user opened and judged FAIL. Kept for provenance only; do not review. |
| c-type-home-pascal-poc | PoC project, unrelated to B1 full-house graph. |
| 905df32d8105 | poc-living-dining-nbalc checkpoint. |
| (three hex-id scenes, deleted) | 7bd4f432a816 / dddefb52197b / 21170aef6694 were accidental duplicates created by `save_scene` with `includeCurrentScene` defaulting true; deleted 2026-09-29T13:42Z. |

## MCP save semantics discovered

- `save_scene.includeCurrentScene` defaults **true** → silently saves the
  bridge's currently-loaded graph and ignores the `graph` argument.
  All bulk writes must pass `includeCurrentScene:false`.
- `save_scene.id` updates an existing scene in place only when combined with
  `expectedVersion`; otherwise a new random-id scene is created.
- `asset.src` must be a relative `/items/<id>/model.glb` path —
  absolute `http://` URLs are rejected with `graph_invalid`.
- `export_json` ignores its `id` argument; it exports the bridge's loaded
  scene. Correct flow: `load_scene(id)` → `export_json`.

## Update 2026-09-30 — master-direct furnished series

| scene_id | note |
|---|---|
| pascal-master-direct-furnished-v1 | direct-arch + registered furniture + PDF kitchen blockouts |
| pascal-master-direct-furnished-v2 | full-house calibrated assets (FULL_HOUSE_FURNITURE_CALIBRATION pass) |
| pascal-master-direct-furnished-v3 | ARCH_FIXTURE_CLEANUP_V1: D-107(=D-SM) host helper re-aimed +26.3°; 3 SHOWER_ZONE blockout-boxes → sliding-glass enclosures (wall_gf/wall_gs glass panels + rail/track/jamb blockouts). HUMAN_REVIEW. |

http://pascal.localhost:57071/editor/pascal-master-direct-furnished-v3
