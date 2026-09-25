# TASK03A RC2.3 — Window Registry Final Truth Alignment

Base: `feat/c-type-task03a-measured-concept` @ `246ff12`(+RC2.2 `7fefe29` 图面工作合并）
Scope: **window/glass-door registry + opening geometry ONLY** — no furniture, bath, ramp, or room-layout change (G27 freeze PASS).

## 1. Source authority (locked)

| Domain | Authority |
|---|---|
| Windows / glass doors | `OWNER_CONFIRMED_FENESTRATION_REFERENCE_2026-09-25` (owner-final annotated image) |
| Walls / ordinary doors / topology | `source/世纪欣园FF.dwg` (measured, sha `f01a9bb5…`) |

The owner image is a fenestration truth sheet, not full CAD — ordinary door
openings (entry, room, bath doors) remain sourced from the measured DWG.

## 2. Final registry — exactly 9 records

`current_existing/window_register.json` + `.csv`

| ID | Zone | Type | Status | Span | Host wall |
|---|---|---|---|---|---|
| W-LIV-N | living north | BAY_WINDOW | EXISTING_CONFIRMED | 3100 (+900 proj) | W-EXT-N-LV |
| G-LIV-NBALC | TV wall → N balcony | GLASS_DOOR | EXISTING_CONFIRMED | **850** | W-INT-X7900-U-TV |
| G-GB-BALC | guest bed → N balcony | GLASS_DOOR | EXISTING_KEEP | 2000 | W-INT-Y10800 |
| W-STUDY-NE | study NE | BAY_WINDOW | EXISTING_CONFIRMED | 2100 (+700 proj) | — |
| G-DIN-LIV | kitchen/dining ↔ living | GLASS_SLIDING_DOOR | EXISTING_KEEP | 2700 | — |
| W-LBALC-S | life balcony | BALCONY_WINDOW | EXISTING_CONFIRMED | 4500 | on parapet |
| W-KIT-S | kitchen south | STANDARD_WINDOW | EXISTING_CONFIRMED | 1000 | W-EXT-S |
| W-SMB-S | sec-master south | BAY_WINDOW | EXISTING_CONFIRMED | 2400 (+700 proj) | W-EXT-S |
| W-MB-S | master south | BAY_WINDOW | EXISTING_CONFIRMED | 2700 (+700 proj) | W-EXT-S |

Removed: `W-KIT-SW`, `W-GBATH-N`, `D-BALC-W`, `N-BALC-ENCL`, `N-BALC-ENCL-E`,
`W-LBALC-W`, all `TO_VERIFY` window records. Added: `G-LIV-NBALC`.

## 3. G-LIV-NBALC — the real balcony door

- Owner confirmed: glass door on the **TV wall's north section**, ~800mm.
- Measured DWG: wall `W-INT-X7900-U-TV` (x7800–7900, y7800–13550) has a face
  gap **y12050–12900 = 850mm** + door-block insert on the wall line — per owner
  instruction the register uses the measured **850mm**.
- The old `D-BALC-W` record was **the same door mis-read** as a west-parapet
  door (the insert at meas(6700,14236) sits ON the TV wall). Deleted; G24
  asserts no phantom record remains.
- Wall is split at the opening (`W-INT-X7900-U-TV#G-LIV-NBALC.0/.1`).

## 4. North balcony — current state OPEN

- No enclosure records in the **current** registry (removed `N-BALC-ENCL(-E)`).
- Model keeps the honest split: `balconies.north_balcony` records
  `existing_north_enclosure=false`, `existing_east_enclosure=false`, and the
  future L-shaped enclosure intent under `future_design_constraints`
  (next-stage PROPOSED design, not current existing).
- Parapets kept where DWG draws them: north band (`W-EXT-N-BAL`) + NEW east
  leg `W-NBALC-E-PAR` (nested LWPOLYs x12900–13020, y11100–13820) — drawn as
  parapet/railing, not red exterior wall.

## 5. Life balcony — W-LBALC-S only

Owner image confirms glazing on the **south** parapet edge only (4500mm,
`BALCONY_WINDOW`, CONFIRMED). The RC2.2 speculative west leg `W-LBALC-W` and
the L-shaped TO_VERIFY band are removed. Parapet base walls unchanged.

## 6. Owner-confirmed wall correction

`OWNER_CONFIRMED_WALL_CORRECTION_2026-09-25`: the south-wall gap
x5000–5380 at the kitchen/life-balcony SE corner is **not** a window — closed
as wall (`W-EXT-S-W1` now ends x5380; `W-EXT-S-W2` starts x5380). Local segment
only; no other wall redrawn. Recorded in `source_delta_report`-equivalent
register meta.

## 7. Ordinary doors preserved

14 measured openings retained in the model (entry, all room/bath doors,
G-GB-BALC, G-DIN-LIV, G-LIV-NBALC, open passage). G26 asserts
`missing_door_ids = ∅`. Overlay now draws real door swings.

## 8. Gates — 28/28 PASS

- **G21** registry IDs == owner truth set, exact (missing 0, unexpected 0, total 9)
- **G22** type correctness + no solid wall through opening middle-half
- **G23** north balcony current = OPEN (north & east enclosure = false; no enclosure records)
- **G24** G-LIV-NBALC on TV wall, 850mm, northern section, wall split, no phantom D-BALC-W
- **G25** 4 bays all have opening + jambs + front projection geometry
- **G26** ordinary door topology preserved (14/14)
- **G27** layout freeze vs RC2.1 — changed = none

## 9. Outputs

- `qc/window_register_overlay.png` — blue confirmed only; parapets tan;
  OPEN BALCONY label; door swings; no purple/green ghosts
- `qc/wall_window_conflict_check.png` — 0 conflicts
- `qc/task03a_s3_furniture_presentation.png` — owner-facing plan
- `current_existing/current_existing_v1.{json,dxf}`, `concept/*.dxf` regenerated
