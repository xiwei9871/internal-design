# WALL_TOPOLOGY_RECONSTRUCTION — 2026-09-29

Gate: `PASCAL_WALL_TOPOLOGY`. Question: did any 2D wall line without explicit
thickness silently fail to become a solid wall, leaving floating glass /
missing walls?

## Finding: canonical walls were never thin

All 35 walls + 4 parapets in `b1_model.json` carry explicit `rect` thickness
(50–300 mm; dominant structural class = 200). The converter emitted all of
them (37 merged Pascal walls, heights 2500 / parapets 1050). **No wall was
dropped for lacking thickness.**

The real defect was **opening → host assignment**, three causes:

| # | cause | affected | fix |
|---|---|---|---|
| 1 | `PARTIAL_REMOVED_TO_VERIFY` walls excluded wholesale → retained openings lost their host | OPEN-COR-LIV (was floating on a synthesized wall) | `removed_host_for()`: a retained opening inside a partial-removed wall means the wall still stands around it → reinstate as `RECONSTRUCTED_HOST_WALL`. W-INT-NICHE (t=250, y4700–7800) now hosts OPEN-COR-LIV; wall extent TO_VERIFY |
| 2 | bridge-gap tolerance off by ~50 mm — hole span 6100–7100 vs gap 6050–7100 | W-KIT-S (kitchen window floated on synthetic wall) | `BRIDGE_TOL=75` mm in both the assignment score and the gap-cover test → now hosted on the merged south facade W-EXT-S |
| 3 | drawn opening rect over-wide across the wall band → center never inside any band | D-CONN-MB-SMB (0 hosted lines) | `HOST_OVERRIDE={'D-CONN-MB-SMB':'W-INT-X11500'}`; along-wall width reconstructed from rect long axis = 800 mm; node flagged `host_override` + TO_VERIFY |

## Cases that are legitimately not masonry (documented, not defects)

- `G-DIN-LIV` — owner blue-line **new** 3-track sliding glass partition
  (2700×185 zone, installed where old wall x5700-5900 was demolished).
  Host tagged `GLAZED_SCREEN`, t=185 — honest semantics, no fake masonry.
- 4 × `*-BAY-FRONT` — bay glazing fronts sit beyond the wall face; canonical
  records them as `bay.front` only. Synthesized `BAY_FRONT_GLAZED` bands
  (t=100) = glass curtain face, `REPRESENTATION_LIMITATION`.
- `G-GB-BALC`, `G-LIV-NBALC` — glazing doors hosted on real wall segments.

## Post-fix opening → host map (pascal-b1-blocks-v1 v7 / full-v2 v3, 154 nodes)

Every one of 13 doors + 10 windows now resolves to a real canonical wall or an
explicitly-classified screen/bay host. Zero generic `SYNTHESIZED_HOST_WALL`.

```
W-KIT-S      → W-EXT-S merged facade       w=1.0  (was orphan)
D-CONN-MB-SMB→ W-INT-X11500                w=0.8  (was orphan; width TO_VERIFY)
OPEN-COR-LIV → W-INT-NICHE (reconstructed) w=3.1  (was orphan)
G-DIN-LIV    → GLAZED_SCREEN               w=2.7  (correct by design)
*-BAY-FRONT ×4 → BAY_FRONT_GLAZED                 (correct by design)
其他 17      → real canonical walls                  (unchanged)
```

## Still clipped (L-02, unchanged, documented)

- D-SM: canonical 700 → Pascal 464 (−236; hole pokes 236 mm west of host
  segment FOYER x8236) — source ambiguity, kept as-is.
- D-MB: 500 → 434 (−66 mm).

## Remaining TO_VERIFY (walls not emitted — flagged in canonical, no opening
## depends on them)

- `W-INT-X7900-U-OPEN` [7800,4670–7900,7800] PARTIAL_REMOVED — the corridor→
  living open edge; whether a wall stub stands here is owner-confirmable.
- `W-SHAFT-K` [7150,750–7250,3650] PARTIAL_REMOVED — kitchen shaft face.
- `W-INT-NICHE` upper extent y6464–7800 — wall emitted full span; if the niche
  removal included more of the wall, extent is TO_VERIFY.

## Status

```
PASCAL_WALL_TOPOLOGY = RECONSTRUCTED_PENDING_HUMAN_VISUAL
PRE_3D_FURNITURE_DIMENSION_GATE = HUMAN_APPROVED_WITH_TO_VERIFY
```
Scenes regenerated: arch-only v4 (101), blocks v7 (154), full-v2 v3 (154).
Visual residuals unchanged: arch 0.0 mm, furniture 0.1 mm.
