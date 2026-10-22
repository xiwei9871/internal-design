# PASCAL_B1 FULL — FIDELITY REPORT

**Scene**: `pascal-b1-full-v1` (project `c-type-home-pascal-b1-v1`) — http://pascal.localhost:57071/scene/pascal-b1-full-v1
**Version**: v3 checkpoint, published · **Nodes**: 141 · **Status**: `verify_scene` valid=true
**Source**: `世纪欣园FF_PRE_BLENDER_MASTER_V2.FCStd` → `b1_model.json` (canonical mm)
**Converter**: `scripts/master_v2_to_pascal.py` (deterministic; same input hash → same graph)

## Composition

| type | count | notes |
|---|---|---|
| walls | 40 | merged collinear source segments; real voids preserved |
| doors | 13 | incl. 3 GLASS_DOOR (G-LIV-NBALC / G-GB-BALC / G-DIN-LIV) + OPEN-COR-LIV |
| windows | 10 | 6 real windows + 4 bay-front glazed bands |
| zones | 19 | 14 rooms/balconies + 4 split-level steps + 1 ramp placeholder |
| items | 56 | 47 approved furniture + 9 canonical kitchen cabinets |
| site/building/level | 3 | single level, baseElevation 0 |

## Fidelity vs MASTER_V2 extraction (`pascal_b1_fidelity.py` → `fidelity_raw.json`)

| check | result | target |
|---|---|---|
| furniture center drift | **0.07 mm** max (56/56) | ≤ 1 mm ✓ |
| furniture w/d delta | ≤ 0.05 mm | exact ✓ |
| room reassignment | **0** | 0 ✓ |
| semantic reassignment | **0** | 0 ✓ |
| windows along-axis drift | **0.0 mm** (9/9) | ≤ 2 mm ✓ |
| windows width delta | **0.0 mm** | exact ✓ |
| doors along-axis drift | 11/13 = 0 mm; D-SM 118 mm, D-MB 33 mm | → LIMITATION L-02 |
| door width delta | 11/13 = 0; D-SM +236 mm, D-MB −66 mm | → LIMITATION L-02 |
| wall coverage | 0 uncovered source segments | ✓ |
| zone polygon match | 14/14 | ✓ |
| orphan nodes | 0 | ✓ |
| export round-trip | 141/141 node IDs identical | ✓ |

## Axis convention note

`drift` is split into **along-axis** (position along the host wall — the real
placement check) and **cross-band offset** (opening rect center vs wall
centerline). Source opening rects are ~400 mm bands that are asymmetric around
200 mm walls; Pascal anchors openings to the wall centerline, which is the
*correct* placement. Cross offsets of 14–200 mm are therefore source-data
artifacts, not placement errors. See L-02/L-03.

## Items NOT auto-moved (human-approved as drawn)

双人位 −83 mm · 主卫马桶 −74 mm · 次主卫马桶 −74 mm · 主卧电视柜 −277 mm
→ `review_status: HUMAN_ACCEPTED_AS_DRAWN`, `NO_MOVE`, `NO_AUTO_FORMALIZATION`

## Gate

```
PASCAL_B1_FULL_FIDELITY = PASS (with L-02 limitations recorded)
room/semantic reassignment = 0
furniture drift ≤ 0.07 mm
openings: 9/9 windows exact; 11/13 doors exact; 2 limitations
```
