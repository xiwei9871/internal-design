# TASK 03A — Measured Existing → Verified Owner Brief → Concept Floor Plan

Status: **REVIEW-READY / GATES PASS 14/14** (not FINAL PASS — owner review gates pending)
Branch: `feat/c-type-task03a-measured-concept` (base `improve/design-output-v14 @ 20637d1`)

---

## 1. Source verification

| Item | Value |
|---|---|
| Source DWG | `projects/c_type_home/source/世纪欣园FF.dwg` (copy of `/Users/xiwei/interior_design/世纪欣园FF.dwg`, original untouched) |
| SHA256 | `f01a9bb5de964e0362296d12ca510fd7dc99060ddd0e8f8c4b6ab1e63a6fc360` |
| Version / units | AC1018 (AutoCAD 2004), INSUNITS=4 → **mm** |
| Working conversion | `current_existing/measured_working.dxf` (dwg2dxf/LibreDWG; ACDB_BLOCKREPRESENTATION warnings benign) |
| Cabinet PDF | `source/世纪欣园3-1-901_cabinet_plan.pdf`, sha `434af535…`, 6pp, 2024-08-31 可米家居 |
| Authority order | measured DWG > owner statements > developer plan (wall policy + history) > Task02 semantics |

## 2. Measured-plan extraction

- Model extents `15100 × 15653 mm`; normalized origin meas ≈ (1299472, −297794); comparison-only mapping `task01 = meas + (1300, −1336)` — **no scaling of the source**.
- Dimension chains cross-validated against Task01 grid (1400/3000/2100/3600/3900/900 etc.).
- Walls: 38 tracked — 28 EXISTING, 7 DEMOLISHED_OWNER_CONFIRMED, 3 PARTIAL_REMOVED_TO_VERIFY.
- Wall classes: 28 `OWNER_DECLARED_NO_DEMOLITION_NO_OPENING` (structural-fill overlap ∪ exterior ∪ ≥180 mm thick), 5 `INTERIOR_TO_VERIFY`, 5 `MODIFIABLE_PARTITION`.
- Openings: 13 tracked — entry, 8 interior doors, `G-DIN-LIV` sliding glass door (≈2700 mm triple-track at meas y≈5900 — the owner-confirmed 蓝线门), `G-GB-BALC` guest-bedroom↔balcony glazing, west balcony door.
- `D-MASTER?` marked TO_VERIFY (dev-plan position, no block insert in measured DWG).
- `D-LIV-STUDY?` mystery arc at platform west edge retained TO_VERIFY.

## 3. Key deltas vs Task01 (developer-plan reconstruction)

| # | Delta | Status |
|---|---|---|
| 1 | Dining/kitchen + life balcony already opened up; kitchen cabinetry KEEP (PDF footprint ~5500×4700 zone) | CONFIRMED |
| 2 | Cloakroom walls/door removed, absorbed into secondary master — **but measured DWG still draws them** → recorded as source conflict | TO_VERIFY |
| 3 | Study↔north-balcony wall removed; large double glass door now exists | CONFIRMED |
| 4 | 蓝线 sliding glass door dining↔living installed, KEEP | CONFIRMED |
| 5 | North balcony may be legally enclosed (enclosure glazing present in DWG) | CONFIRMED |
| 6 | 10 kg washer/dryer in north-balcony west end (stacked ~700×700 assumed) | TO_VERIFY (arrangement) |
| 7 | 4 walls classed NO_OPENING yet owner-confirmed demolished (W-BALC-N, X5800, CLK-E, DRY-STUB) — white-wall is **owner-declared policy, not proven structure** | TO_VERIFY structural |

## 4. Split level (measured)

- Stair block meas `x5900–6500 × y7936–9136` (task01 `x7200–7800 × y6600–7800`): **2 risers, 300 mm treads, climb +x** — west = lower public (living/dining/kitchen/balconies), east = upper (bedroom wing + landing + corridor).
- Rise ≈ **400 mm** owner-reported → `ELEVATION_TO_VERIFY`.
- Former leisure/platform arm `x5900–7200 × y4650–7800` (**1300 × 3150 = 4.09 m²**) returned to L1 → living/dining gain.
- Kept upper landing: foyer `x7800–9100 × y4650–6300` + corridor `x7800–13000 × y6300–7800`.
- **Ramp option**: `4150–7150 × 5600–6700`, run **3000 × 1100**, climbs +x onto the former-niche open passage → landing. Slope **1 : 7.5** @400 mm — steep; labelled `ASSISTED_WHEELCHAIR_FUTURE_PROVISION`, **no accessibility-code claim**.
- Stair approach zones clear both ends.

## 5. Concept result (preferred plan)

- Final usable living rectangle: **4850 × 4850 mm core** (x2900–7750 / y7900–12750) + returned annex strip; open flexible core 2800 × 3200 kept furniture-free (small movable table exempt).
- Living furniture: 3-seat sofa (west wall, faces east projection wall), 2-seat (south), lounge chair, movable coffee table; no TV, no island.
- Dining table 1500×600 in dining zone; kitchen cabinets untouched.
- Master: 1800×2100 bed, bedside gaps 900 (E) / 1000 (W); existing wardrobe KEEP.
- Secondary master: 1800×2100 bed, gaps 800/770 (below the 900 target — flagged `TO_IMPROVE`); wardrobe rebuilt on east wall.
- Guest bedroom: bunk 1500×2100 on west wall, balcony glass-door zone kept clear (route ≥1500 mm east aisle); desk SE.
- Study: 1700×800 desk on south wall (east window = side light), daybed backup-sleep, existing wardrobe→file/book storage, NAS shelf.
- Guest bath: wet=rear (shower + 3 kg washer), dry=front (WC + vanity) — owner red/green preserved.
- Master bath: tub→walk-in shower 2200×800 N strip (zero-threshold target, seat+grab bars), WC SE, vanity NE, radiator kept.
- Entry: low shoe cabinet + bench, no full-height storage wall.

## 6. Secondary master bath — W vs S verdict

| Option | Result |
|---|---|
| **W (west entry via suite foyer)** | **Preferred** — door `x8950 y5200–5950` in NEW partition; foyer `7800–9050 × 4650–6300`; door does not face bed; 3-piece fits 2250×1650 = 3.71 m² |
| S (south entry) | **INFEASIBLE** — requires new opening in `W-INT-Y4500-b`, classified `OWNER_DECLARED_NO_OPENING` (white-fill 200 mm + column overlap). Not pursued unless owner reclassifies after structural check |
| Drain | East wall shared with master-bath wet zone — best drain/vent candidate — `TO_VERIFY` (same-floor/dropped-slab feasibility) |

## 7. Gate results — `qc/task03a_gates.json`: **14/14 PASS**

G1 units/hash ✓ · G2 Option-S blocked honestly ✓ · G3 cabinets ✓ · G4 glazing ✓ · G5 beds ✓ · G6 3-piece ✓ · G7 balcony route ✓ · G8 living core ✓ · G9 stair/ramp ✓ · G10 level TO_VERIFY ✓ · G11 study ✓ · G12 wet/dry ✓ · G13 KEEP items ✓ · G14 program ✓

## 8. Deliverables

- `brief/owner_brief_v1.md` + `.json` (every item CONFIRMED/PREFERRED/TO_VERIFY)
- `current_existing/current_existing_v1.dxf` + `.json`, `source_delta_report.md`, `source_manifest.json`
- `concept/task03a_preferred_plan.dxf`, `option_smb_entry_W.dxf`, `option_smb_entry_S.dxf`, `split_level_study.dxf`, `concept_data.json`
- `qc/task03a_s1…s6_*.png` + `.pdf` (existing / demo-keep-new / furniture / split-level / bathrooms / W-vs-S)

## 9. Unresolved items (all preserved, none hidden)

1. Exact level difference — ~400 mm owner estimate → field verify.
2. Cloakroom drawn-but-demolished conflict — owner re-confirm.
3. Secondary-bath drain/vent feasibility (same-floor? dropped slab?).
4. 4 white-policy walls already demolished — structural verification needed before relying on remaining NO_OPENING set.
5. Master door position (`D-MASTER?`), mystery arc `D-LIV-STUDY?`.
6. 10 kg washer/dryer arrangement (stacked assumed).
7. SMB bedside gaps 800/770 < 900 target — furniture swap or slight wall shift in next iteration.
8. Ramp slope 1:7.5 steep — acceptable only as assisted-use provision; revisit if elderly wheelchair independence required.
9. Guest-bedroom door swing vs bunk west edge — verify clearance on site.

## 10. Owner review gates (requested focus)

1. Measured CAD inheritance — see §2, overlay evidence in delta report.
2. Platform reduction benefits living room — **+4.09 m² returned**, core 4850×4850.
3. Secondary master bath W vs S — **W wins; S blocked by policy wall**.
4. Guest-bedroom bunk + balcony route — works, ≥1500 aisle, glass-door zone clear.

Commit SHA: _see git log on `feat/c-type-task03a-measured-concept`_
