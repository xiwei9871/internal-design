# PASCAL_B1 — REPRESENTATION LIMITATIONS

Every case where Pascal's representation cannot exactly express the measured
source. Nothing is silently altered; each case is traceable in
`pascal_full_id_map.json` (`status: REPRESENTATION_LIMITATION` / node metadata).

## L-01 Heights are TEMP values (BLOCKOUT_TEMP_VALUE)

| element | value used | evidence |
|---|---|---|
| interior wall height | 2.5 m | none — nominal |
| parapet height | 1.05 m | none — nominal |
| window sill / head | 0.6 / 2.4 m | none — nominal |
| door height | 2.1 m (ENT-1 2.2 m) | none — nominal |
| glass door height | 2.4 m | none — nominal |
| zone ceilingHeight | 2.7 m | none — nominal |
| split-level elevation | 0 / +350 mm in metadata only | none — TO_VERIFY |
| bay-window Z geometry | nominal | TO_VERIFY |

All carry `*_TEMP` metadata flags. None may be cited as measurements.

## L-02 Opening clipping (2 doors)

Source wall segments do not fully bound the opening band; Pascal clamps the
leaf to the measured gap:

| id | source span | represented | along drift | cause |
|---|---|---|---|---|
| D-SM | 700 mm | 464 mm | 118 mm | host wall line only covers 8236–9050 of the 8000–8700 band |
| D-MB | 500 mm | 434 mm | 33 mm | gap between measured wall segments is 434 mm |

The source rect presumably includes frame/casing tolerance. Marked
`REPRESENTATION_LIMITATION` — not silently widened.

## L-03 Cross-band centerline anchoring (informational)

Opening rects are ~400 mm asymmetric bands around 200 mm walls. Pascal anchors
doors/windows to the wall centerline; reported "cross offset" 50–200 mm
(D-BATHM 200, D-MB 100, W-LBALC-S 50) is a metric artifact, not movement.

## L-04 W-LBALC-S glazed band on parapet

South balcony band sits on a 1.05 m parapet; a 1.8 m nominal window cannot
exceed its host wall in Pascal → represented as full-height glazing within the
parapet (`glazing_fit: CLAMPED_TO_HOST_WALL`). Real sill/head: TO_VERIFY.

## L-05 Synthesized host walls (4)

Pascal requires doors/windows to hang on a wall node. Synthesized hosts:

- `G-DIN-LIV` — dining/living glass partition → thin wall + sliding door
- `W-LIV-N-BAY-FRONT` + 3 more `*-BAY-FRONT` — bay front glazed band → thin
  wall + full-width window; jambs remain real walls

These walls exist in Pascal only to carry the opening; they are marked
`SYNTHESIZED_HOST_WALL` / `BAY_FRONT_GLAZED` and must not be read as new walls.

## L-06 No slabs / ceilings / stairs meshes

`verify_scene` reports "zones but no slabs/floors" and "no ceilings". Split-level
steps and the wheelchair ramp are flat annotation zones (`STEP-1..4`,
`RAMP-FUTURE`), not modeled stair geometry — the +350 mm level delta exists
only as zone metadata.

## L-07 Placeholder item meshes

Items use catalog GLBs uniformly scaled so the plan footprint equals the
measured rect (`actual_project_size_m` is authoritative; `catalog_nominal_size_m`
is recorded separately). Stretched placeholders (e.g. a cabinet mesh stretched
7×) are **not** the real product shape — blockout volume only.

## L-08 verify_scene advisories (recorded, not auto-fixed)

- 15 × "door blocked by item" — human-approved as-drawn layout; Pascal keep-out
  is advisory only. Policy: `ACKNOWLEDGED_HUMAN_OVERRIDE`, no move.
- 19 item-item overlaps — all as-drawn (kitchen runs contain sub-elements;
  湿区/3kg洗衣机; 矮书柜/打印机/NAS; headboard+desk+bed cluster).
- "no slabs/ceilings" per L-06.
