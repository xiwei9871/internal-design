# TASK 03A RC2 — Measured Existing → Verified Owner Brief → Concept Floor Plan

Status: **REVIEW-READY / GATES PASS 21/21** (not FINAL PASS — owner review gates pending)
Branch: `feat/c-type-task03a-measured-concept` (base `improve/design-output-v14 @ 20637d1`)

> **RC1 + RC1.5 + RC2 corrections applied** (owner reviews):
> 1. White/black wall class comes ONLY from manual per-wall visual read of the dev plan + owner declaration (`VISUAL` table). Thickness/hatch inference removed as a criterion.
> 2. North balcony: `OPEN_NOT_ENCLOSED` now; enclosure `PROPOSED`. Guest-bedroom↔balcony glass door = interior door.
> 3. Level delta `LEVEL_DELTA_TO_VERIFY` (owner ≤350 vs CAD ~400, conflict recorded); ramp slope 1:7.5–1:8.6, platform cut and living rectangle PROVISIONAL.
> 4. Cloakroom N/W/E walls are RETAINED (owner image markup green + DWG drawn — consistent); south side open to bedroom. Bath = shell + NEW partitions. Zero demolition.
> 5. Bath entries: **S = FEASIBLE-RECOMMENDED** (door in new partition); **W = CONSTRAINED** (sliding door in retained white-class CLK-W → owner exception); **N = fallback**.
> 6. Conflict set: `Y4500-b-CLKSEG` (white-class yet opened — flagged for review).
> 7. **RC2 geometry closure**: secondary bath enlarged 3.71 → **5.0 m²** (shell + L-annex into bedroom, new south partition at y3800, annex walls, wardrobe wall preserved); S door re-positioned west end, swing zone fixture-free; study daybed/bookcase overlap fixed + desk/NAS moved out of door swing; master bath shower re-proportioned 2200×800 → **1600×900 corner** (fold seat + grab bars); guest-room bunk rotated landscape clear of door swing + glass-door zone; split-level honest area account (returned 4.09 m² vs ramp 3.30 m² → net +0.79 m²).
> 8. **RC2 new gates**: G15 furniture overlap · G16 door-swing vs new fixtures · G17 bath service clearances · G18 guest-room aisle · G19 study circulation · G20 net-area account.

---

## 1. Source verification

| Item | Value |
|---|---|
| Source DWG | `projects/c_type_home/source/世纪欣园FF.dwg` (original at repo root untouched) |
| SHA256 | `f01a9bb5de964e0362296d12ca510fd7dc99060ddd0e8f8c4b6ab1e63a6fc360` |
| Version / units | AC1018 (AutoCAD 2004), INSUNITS=4 → **mm** |
| Working conversion | `current_existing/measured_working.dxf` (dwg2dxf; block warnings benign) |
| Cabinet PDF | `source/世纪欣园3-1-901_cabinet_plan.pdf`, sha `434af535…`, 6pp |
| Authority | DWG = dimensions · owner = wall existence · dev plan = white/black policy + history |

## 2. Measured-plan extraction

- Extents `15100 × 15653 mm`; mapping `task01 = meas + (1300, −1336)` translation only.
- Dimension chains cross-validated (1400/3000/2100/3600/3900/900; 5100/1900/3200/3300).
- Walls: 40 records — 31 EXISTING, 5 DEMOLISHED_OWNER_CONFIRMED, 3 PARTIAL_TO_VERIFY, plus D-CLK opening record.
- Policy classes (visual read + owner rule, no thickness inference):
  - `NO_OPEN_EXTERIOR_ENVELOPE` ×12
  - `OWNER_DECLARED_NO_DEMOLITION_NO_OPENING` ×7 (white-class interior incl. retained CLK-N/W/E)
  - `MODIFIABLE_DECLARED` ×11
  - `CLASSIFICATION_CONFLICT_TO_REVIEW` ×1 (Y4500-b-CLKSEG)
  - `CLASSIFICATION_TO_REVIEW` ×1 (Y4500-bc)
  - `DEMOLISHED_OR_PARTIAL` ×8
- Openings 14 — incl. `G-DIN-LIV` sliding glass door, `G-GB-BALC` interior balcony door, `D-CLK` cloakroom north opening.

## 3. Current-condition truth (RC1.5)

| Area | DWG draws | Confirmed truth |
|---|---|---|
| Cloakroom CLK-N/W/E | lines present (cov 0.75–1.0) | **RETAINED** — shell kept |
| Cloakroom south (Y4500-b seg.) | only 600 mm stub x10800–11400 | **open to bedroom** — this is the "merge" |
| Kitchen/dining walls | mostly absent | opened up ✓ consistent |
| N balcony | parapet/rail lines | **not enclosed**; enclosure proposed |

Secondary master bath = cloakroom shell + south L-annex into bedroom + NEW south partition/frosted glass + interior wet/dry glass. **No existing wall is demolished or cut for the recommended scheme.**

## 4. Split level

- Stair `x7200–7800 × y6600–7800`: 2 risers, 300 mm treads, climb +x.
- **Delta unresolved**: owner ≤350 vs CAD ~400 → `LEVEL_DELTA_TO_VERIFY`; field measure requested (L1→L2 finished-floor delta).
- Platform arm `x5900–7200 × y4650–7800` (≈4.09 m²) returned to L1 — **PROVISIONAL** pending delta.
- Ramp `x4150–7150 × y5600–6700`, 3000×1100, climbs +x to open passage → landing; slope **1:7.5–1:8.6 PROVISIONAL**, assisted-use only.
- **RC2 area account**: returned 4.09 m² vs ramp footprint 3.30 m² → **net +0.79 m²** only. Real value = regular living rectangle + future step-free route, not net floor area. Recorded in `concept_data.json → level.area_comparison`.

## 5. Concept result (provisional where level-dependent)

- Living core 4850×4850 + returned annex; flexible core 2800×3200 clear of fixed furniture.
- Master 1800×2100 bed, gaps 900/1000; secondary master 1800×2100, gaps 800/770 (below 900 target — flagged).
- Guest bedroom bunk 2100×1500 landscape (head east wall, ladder west end in 900 mm aisle); balcony glass-door zone + door swing clear; desk SE.
- Study: 1700×800 desk (east of door swing), daybed 800×2000 west wall, wardrobe-storage KEEP east, NAS shelf — no overlaps, aisle 1500 mm.
- Baths: master corner shower **1600×900** NE (fold seat + grab bars + handheld) + WC SE + vanity NW + radiator; guest bath wet/dry preserved; secondary bath 3-piece in **shell + annex ≈ 5.0 m²**.
- Entry: low shoe cabinet + bench only.

## 6. Secondary master bath — W vs S (RC2 verdict)

| Option | Verdict |
|---|---|
| **S** (door in NEW south partition y3800 → bedroom) | **FEASIBLE — RECOMMENDED**: zero demolition; hinge east, swings into annex; swing zone fixture-free; annex 1700×550 reaches owner ~5 m² target |
| **W** (SLIDING door cut in retained CLK-W → foyer) | **CONSTRAINED**: private vestibule + door not facing bed, sliding leaf saves swing space — but requires new opening in white-class retained wall → owner exception + structural check |
| **N** (reuse existing CLK-N door) | **FALLBACK**: zero work, but opens to shared corridor — not en-suite |
| Drain | East wall shared with master-bath wet zone — candidate only, TO_VERIFY |

## 7. Gates — `qc/task03a_gates.json`: **21/21 PASS**

G1 source ✓ · G2 shell kept / S feasible / W constrained ✓ · G3 cabinets ✓ · G4 glazing ✓ · G5 beds ✓ · G6 ~5m² 3-piece ✓ · G7 balcony route ✓ · G8 living core ✓ · G9 ramp PROVISIONAL ✓ · G10 delta conflict ✓ · G10b balcony OPEN/PROPOSED ✓ · G11 study ✓ · G12 wet/dry ✓ · G13 KEEP ✓ · G14 program ✓ · **G15 no furniture overlap ✓ · G16 door swings clear ✓ · G17 bath clearances ✓ · G18 guest-room aisle ✓ · G19 study circulation ✓ · G20 net-area account ✓**

## 8. Deliverables

- `brief/owner_brief_v1.md` + `.json`
- `current_existing/current_existing_v1.dxf` + `.json`, `source_delta_report.md` (RC1), `source_manifest.json`
- `concept/task03a_preferred_plan.dxf`, `option_smb_entry_W.dxf`, `option_smb_entry_S.dxf`, `split_level_study.dxf`, `concept_data.json`
- `qc/task03a_s1…s6_*` PNG + PDF

## 9. Unresolved / for owner + field

1. **Level delta** — measure L1→L2 finished-floor vertical (one number settles ramp, platform cut, living rectangle).
2. `Y4500-b-CLKSEG` conflict: white-class yet opened — owner to confirm classification convention.
3. Y4500-bc + X7900-U ambiguous fill — review.
4. Residual stub x10800–11400 on site? (bath SE boundary.) Cloakroom N door leaf status.
5. Option W requires owner exception to open retained white-class CLK-W (sliding door) — decide S vs W.
6. Secondary bath drain feasibility (same-floor/dropped slab).
7. `D-MASTER?` position; `D-LIV-STUDY?` mystery arc; 10 kg washer arrangement; SMB bedside 800/770 < 900.
8. Balcony enclosure approval boundary (property mgmt).
9. Guest-room bunk is 2100×1500 landscape (east wall) to clear the door swing; alternative = re-hang door outward/sliding → portrait 1500×2100 on west wall.

Commit SHA: RC1 `27d9ff9` · RC1.5 `b01cd19` · RC2 — see git log.
