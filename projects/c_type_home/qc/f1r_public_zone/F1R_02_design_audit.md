# F1R.2 — Dining Geometry Optimization

Dining-only concept comparison. Living F1R-01H, media wall, stair/ramp, walls/openings, KEEP kitchen and canonical data are frozen.

## Semantics

- `table_to_chair_near_edge_gap_mm`: table edge to chair near edge; it is not pullout space.
- `seated_envelope_from_table_edge_mm`: table edge to chair back edge when occupied.
- `extra_pullout_travel_available_mm`: minimum chair-back edge reserve to the first wall/opening/KEEP obstruction along that chair outward axis; per-chair values are listed.
- `through_passage_behind_seated_mm`: reported only when occupied chairs are directly between dining and G-DIN-LIV; for 90° orientation it is N/A, and the clear route around the north end is separately reported as `g_din_liv_transition_clear_mm`.
- Existing G-LIV-NBALC 850 mm is recorded as `EXISTING_CONFIRMED_LIMITATION / NO_WORSENING`.
- Both 0° and 90° table orientations were searched on a 50 mm grid; selected drawings use actual transformed A0.4 geometry.
- Reference rules: `DIN-CIR-005` chair pullout, `DIN-CIR-006` passage behind a seated diner, `DIN-CIR-007` dining/kitchen route. Values remain planning references, not automatic code gates.
- Pattern context: `PAT-LIV-04` dining as kitchen extension and `PAT-LIV-05` dual-mode dining.

## Candidate 1 — rotation 0°, center [3750, 2600]

- Plan: `F1R_02_candidate_1.png`
- Table bbox: `[3000.0, 2300.0, 4500.0, 2900.0]`
- Chair bboxes: `[[3150.0001396847206, 3000.0, 3599.9998603152794, 3500.0], [3900.0001396847206, 3000.0, 4349.99986031528, 3500.0], [3150.0001396847206, 1700.0, 3599.9998603152794, 2200.0], [3900.0001396847206, 1700.0, 4349.99986031528, 2200.0]]`
- Table→chair near-edge gap: **100.0 mm** (placement gap, not pullout space)
- Seated envelope from table edge: **600.0 mm**
- Extra pullout travel available (minimum of 4): **1030.0 mm**; per chair: `[{'chair_id': 'DIN-CHAIR-1', 'back_direction': (0, 1), 'extra_pullout_travel_available_mm': 1030.0}, {'chair_id': 'DIN-CHAIR-2', 'back_direction': (0, 1), 'extra_pullout_travel_available_mm': 1030.0}, {'chair_id': 'DIN-CHAIR-3', 'back_direction': (0, -1), 'extra_pullout_travel_available_mm': 1050.0}, {'chair_id': 'DIN-CHAIR-4', 'back_direction': (0, -1), 'extra_pullout_travel_available_mm': 1050.0}]`
- Through-passage behind occupied seat: **1030.0**
- G-DIN-LIV transition: **1030.0 mm**; basis: behind occupied north-side chairs
- Table→KEEP kitchen actual gap: **1000.0 mm**; closest chair→KEEP: **1150.0 mm**
- P2 entry/dining/kitchen path clear: `True`; all named paths clear: `True`; overlaps `0`
- Pros: meets kitchen-gap target with little extra; transition clear but closer to the target; four-seat setup preserved.
- Trade-offs: minimum outward reserve 1030.0 mm; north occupied chairs sit between dining and G-DIN-LIV; inspect occupied-state passage.

## Candidate 2 — rotation 90°, center [4200, 2550]

- Plan: `F1R_02_candidate_2.png`
- Table bbox: `[3900.0, 1800.0, 4500.0, 3300.0]`
- Chair bboxes: `[[3300.0, 1950.0001396847206, 3800.0, 2399.9998603152794], [3300.0, 2700.0001396847206, 3800.0, 3149.9998603152794], [4600.0, 1950.0001396847206, 5100.0, 2399.9998603152794], [4600.0, 2700.0001396847206, 5100.0, 3149.9998603152794]]`
- Table→chair near-edge gap: **100.0 mm** (placement gap, not pullout space)
- Seated envelope from table edge: **600.0 mm**
- Extra pullout travel available (minimum of 4): **400.0 mm**; per chair: `[{'chair_id': 'DIN-CHAIR-1', 'back_direction': (-1, 0), 'extra_pullout_travel_available_mm': 1800.0}, {'chair_id': 'DIN-CHAIR-2', 'back_direction': (-1, 0), 'extra_pullout_travel_available_mm': 400.0}, {'chair_id': 'DIN-CHAIR-3', 'back_direction': (1, 0), 'extra_pullout_travel_available_mm': 400.0}, {'chair_id': 'DIN-CHAIR-4', 'back_direction': (1, 0), 'extra_pullout_travel_available_mm': 400.0}]`
- Through-passage behind occupied seat: **N/A for this orientation**
- G-DIN-LIV transition: **1380.0 mm**; basis: clear passage around north end of occupied dining group
- Table→KEEP kitchen actual gap: **1000.0 mm**; closest chair→KEEP: **400.0 mm**
- P2 entry/dining/kitchen path clear: `True`; all named paths clear: `True`; overlaps `0`
- Pros: meets kitchen-gap target with little extra; large clear transition; four-seat setup preserved.
- Trade-offs: minimum outward reserve 400.0 mm; chairs sit on table long sides; G-DIN-LIV passes around north table end.

## Candidate 3 — rotation 90°, center [4200, 2800]

- Plan: `F1R_02_candidate_3.png`
- Table bbox: `[3900.0, 2050.0, 4500.0, 3550.0]`
- Chair bboxes: `[[3300.0, 2200.0001396847206, 3800.0, 2649.9998603152794], [3300.0, 2950.0001396847206, 3800.0, 3399.9998603152794], [4600.0, 2200.0001396847206, 5100.0, 2649.9998603152794], [4600.0, 2950.0001396847206, 5100.0, 3399.9998603152794]]`
- Table→chair near-edge gap: **100.0 mm** (placement gap, not pullout space)
- Seated envelope from table edge: **600.0 mm**
- Extra pullout travel available (minimum of 4): **400.0 mm**; per chair: `[{'chair_id': 'DIN-CHAIR-1', 'back_direction': (-1, 0), 'extra_pullout_travel_available_mm': 400.0}, {'chair_id': 'DIN-CHAIR-2', 'back_direction': (-1, 0), 'extra_pullout_travel_available_mm': 400.0}, {'chair_id': 'DIN-CHAIR-3', 'back_direction': (1, 0), 'extra_pullout_travel_available_mm': 400.0}, {'chair_id': 'DIN-CHAIR-4', 'back_direction': (1, 0), 'extra_pullout_travel_available_mm': 400.0}]`
- Through-passage behind occupied seat: **N/A for this orientation**
- G-DIN-LIV transition: **1130.0 mm**; basis: clear passage around north end of occupied dining group
- Table→KEEP kitchen actual gap: **1000.0 mm**; closest chair→KEEP: **400.0 mm**
- P2 entry/dining/kitchen path clear: `True`; all named paths clear: `True`; overlaps `0`
- Pros: meets kitchen-gap target with little extra; transition clear but closer to the target; four-seat setup preserved.
- Trade-offs: minimum outward reserve 400.0 mm; chairs sit on table long sides; G-DIN-LIV passes around north table end.

## Boundary

No candidate is written to formal CAD. Select one dining candidate only after human review of the real plan and chair crossing behavior.
