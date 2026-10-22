# CANONICAL BAY ADD-BACK REPORT — W-BAY-STUDY-*

Date: 2026-09-30 · Executed per owner approval "STUDY BAY ENCLOSURE ADD-BACK"

## What was added to canonical (`b1_model.json`)

| wall_id | rect_mm | thickness | existence | confidence | status |
|---|---|---|---|---|---|
| W-BAY-STUDY-F | [13600,11350,15800,11550] | 200 | CONFIRMED | HIGH | ADDED |
| W-BAY-STUDY-JW | [13500,11100,13600,11550] | 100 TEMP | CONFIRMED | MEDIUM (thickness TO_VERIFY) | ADDED |
| W-BAY-STUDY-JE | [15700,11100,15800,11550] | 100 TEMP | CONFIRMED | MEDIUM (thickness TO_VERIFY) | ADDED |

`wall_family = BAY_ENCLOSURE` on all three.

## Supersede relationship (rule 5)

- Canonical `W-EXT-NE` [13000,10900,13600,11100] kept as **facade flank segment only** —
  annotated `note: baseline W-EXT-NE bay-front geometry carried by W-BAY-STUDY-F`.
- `W-STUDY-NE` window: `bay` synthesized-front record removed
  (`bay_superseded_by = [W-BAY-STUDY-F, JW, JE]`); glazing rect moved to bay-front
  plane [13600,11350,15700,11550]; `host_wall = W-BAY-STUDY-F`.
- Old synthesized node `W-STUDY-NE-BAY-FRONT` no longer emitted.
  MASTER_V2 / FCStd untouched.

## Pascal scenes re-saved (via direct MCP-HTTP after stdio bridge hung → `pascal restart`)

| scene | version | nodes |
|---|---|---|
| pascal-b1-arch-only-v1 | v5 | 100 |
| pascal-b1-blocks-v1 | v8 | 156 |
| pascal-b1-full-v2 | v4 | 156 |

Verified in graph: `window W-STUDY-NE` parent = `wall W-BAY-STUDY-F`
(start [13.6,−11.45] → [15.8,−11.45]); cheeks emitted at x=13.55/15.75.
Windows now 9 (bogus 10th was the synthesized front).

## Gate check

```
unexplained_wall_segments = 0
missing_confirmed_walls   = 0  (study bay box now in canonical + Pascal)
new duplicate segments    = 0
MASTER vs Pascal wall overlay = visually consistent
   (PASCAL_STUDY_BAY_REVIEW.png: green Pascal walls close the bay box
    around grey FC linework; red dash = glazing on bay front)

CANONICAL_WALL_COMPLETENESS     = PASS  (pending your visual confirm)
PASCAL_WALL_VISUAL_COMPLETENESS = PASS  (same)
PASCAL_B1                       = HOLD → awaiting human visual confirm
```

## Pre-existing finding (not introduced by this change)

`W-INT-X13000` [12900,4630,13100,13600] overlaps `W-NBALC-E-PAR`
[12900,11100,13020,13820] by 120×2500mm — parapet band sits inside the wall band
at the balcony east edge. Likely double-registration of the same physical
element. Documented; not auto-merged — needs ruling whether the parapet should
be `on-top-of` X13000 or a distinct free-standing rail.

## Artifacts

`PASCAL_STUDY_BAY_REVIEW.png`, `MASTER_VS_PASCAL_WALL_OVERLAY_V2.png`,
`PASCAL_FINAL_WALL_ONLY_V2.png`, `FINAL_WALL_REGISTER_V01.json` (statuses updated).

## Infra note

Pascal stdio MCP bridge + scene PUT path were wedged (502 on all writes while
GETs stayed 200). Worked around via direct MCP-over-HTTP on port 52658 with
`~/.pascal/run/mcp-token` (`scripts/pascal_mcp_http.py`), then `pascal restart`
restored the service. Also note: `save_scene` takes `id`, not `scene_id` —
the earlier `version_conflict` errors were misattributed to versions; the real
cause was the wrong argument name making it attempt a create.
