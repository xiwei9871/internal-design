# Task03A-F1 — Level-1 Furniture Final

Base: RC3.1 frozen canonical base (`02dabd6`). L1 furniture only; walls, doors,
windows, kitchen cabinets and L2 untouched.

## Layout (owner-confirmed markup)

| item | rect_mm | note |
|---|---|---|
| LIV-SOFA-3 | [2900,9500,3800,11700] | 3-seat 2200×900 west wall, N-S |
| LIV-SOFA-2 | [4550,11800,6350,12650] | 2-seat 1800×850 under W-LIV-N |
| LIV-LOUNGE | [5450,6200,6950,7300] | single lounge south-central |
| LIV-SIDE-TABLE | [3450,11850,3900,12300] | NW corner movable (LOUNGE-1 deleted) |
| LIV-COFFEE-MOV | [5700,8400,6450,9500] | small movable 750×1100 |
| LIV-MEDIA-WALL | [7750,9000,7900,12400] | position locked; A clean / B floating-stone undecided |
| DIN-TABLE | [3300,3100,4800,3700] | 1500×600 in real dining zone (old transition-zone pos removed) |
| ENTRY-SHOE-CAB / ENTRY-BENCH | [2900,4600,3400,5600] / [2900,6800,3400,7200] | KEEP flanking entry |
| LBALC-CAB | [1400,64,2000,2564] | existing life-balcony cabinet KEEP |

## Level transition

- Old central ramp [4150,5600,7150,6700] DELETED.
- New ramp `RAMP` [5300,4715,7800,5815] — 2500×1100, south edge of public
  transition strip, climbs +x, top flush with L2 landing west edge x7800,
  65mm clear of G-DIN-LIV track. Slope 400/2500 = 1:6.25 PROVISIONAL.
  Semantics: ASSISTED / POWER-WHEELCHAIR RAMP (NOT code-compliant).
- STAIR-EXISTING [7200,6600,7800,7800] — owner: EXISTING 3-STEP TRANSITION;
  exact delta still TO_VERIFY.

## Data contract

`concept/furniture_l1_final.json` — categories fixed_keep /
proposed_large_furniture / movable_furniture / accessibility / media /
circulation + canonical_geometry_sha = e83c1d69e6b5da74 (matches frozen base).

## Outputs

- `qc/task03a_f1_level1_furniture_presentation.png/.pdf`
- `qc/task03a_f1_level1_furniture_qc.png/.pdf`
- `concept/task03a_f1_level1_furniture.dxf`
- S1–S6 sheets + preferred-plan DXF regenerated on same base.

## Gates

41/41 PASS — F1-G1..F1-G10 all green; G28 canonical + sidecars consistent;
canonical sha unchanged. L2 furniture/baths changed=none (F1-G10).
