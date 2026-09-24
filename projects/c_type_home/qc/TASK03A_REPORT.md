# TASK 03A RC1 — Measured Existing → Verified Owner Brief → Concept Floor Plan

Status: **REVIEW-READY / GATES PASS 15/15** (not FINAL PASS — owner review gates pending)
Branch: `feat/c-type-task03a-measured-concept` (base `improve/design-output-v14 @ 20637d1`)

> **RC1 corrections applied** (owner review of first pass):
> 1. Cloakroom zone re-truthed: walls/door owner-confirmed demolished → ABSENT; DWG remnant lines = `dwg_stale_geometry`. The zone is continuous secondary-master space.
> 2. White/black wall class now comes ONLY from manual per-wall visual read of the dev plan + owner declaration (`VISUAL` table in builder). Thickness/hatch inference removed as a criterion.
> 3. "White walls demolished" claim withdrawn as fact → 4 walls flagged `CLASSIFICATION_CONFLICT_TO_REVIEW` (CLK-N/W/E + Y4500-b-CLKSEG read WHITE_FILL yet demolished).
> 4. North balcony corrected: currently `OPEN_NOT_ENCLOSED`; enclosure = `PROPOSED`. The guest-bedroom↔balcony double glass door is an interior door, not exterior glazing.
> 5. Level delta `LEVEL_DELTA_TO_VERIFY`: owner ≤350 vs CAD ~400 recorded as open conflict; ramp slope, platform cut and living rectangle all marked PROVISIONAL.
> 6. Secondary master bath W-vs-S redone: **both feasible** (doors land on NEW partitions); W preferred, S conditional.

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
- Walls: 39 records — 28 EXISTING, 8 DEMOLISHED_OWNER_CONFIRMED, 3 PARTIAL_TO_VERIFY.
- Policy classes (visual read + owner rule, no thickness inference):
  - `NO_OPEN_EXTERIOR_ENVELOPE` ×12 (envelope untouchable regardless of drawn color)
  - `OWNER_DECLARED_NO_DEMOLITION_NO_OPENING` ×4 (white-class interior, present)
  - `MODIFIABLE_DECLARED` ×11 (black-class/thin, present)
  - `CLASSIFICATION_CONFLICT_TO_REVIEW` ×4 (white-class but demolished)
  - `CLASSIFICATION_TO_REVIEW` ×1 (Y4500-bc ambiguous fill)
  - `DEMOLISHED_OR_PARTIAL` ×7 (black-class removed/partial)
- Openings 13 — incl. `G-DIN-LIV` 3-track sliding glass door (~2700, owner blue line) and `G-GB-BALC` interior double glass door to balcony.

## 3. Current-condition corrections (owner over DWG)

| Area | DWG draws | Confirmed truth |
|---|---|---|
| Cloakroom CLK-N/W/E | partial stale lines | demolished, merged into suite |
| Y4500-b cloakroom seg. | only 600 mm stub x10800–11400 | open/continuous; stub TO_VERIFY |
| Kitchen/dining walls | mostly absent | opened up ✓ consistent |
| N balcony | parapet/rail lines | **not enclosed**; enclosure proposed |

## 4. Split level

- Stair `x7200–7800 × y6600–7800`: 2 risers, 300 mm treads, climb +x.
- **Delta unresolved**: owner ≤350 vs CAD ~400 → `LEVEL_DELTA_TO_VERIFY`; field measure requested (L1→L2 finished-floor delta).
- Platform arm `x5900–7200 × y4650–7800` (≈4.09 m²) returned to L1 — **PROVISIONAL** pending delta.
- Ramp `x4150–7150 × y5600–6700`, 3000×1100, climbs +x to open passage → landing; slope **1:7.5–1:8.6 PROVISIONAL**, assisted-use only.

## 5. Concept result (provisional where level-dependent)

- Living core 4850×4850 + returned annex; flexible core 2800×3200 clear of fixed furniture.
- Master 1800×2100 bed, gaps 900/1000; secondary master 1800×2100, gaps 800/770 (below 900 target — flagged).
- Guest bedroom bunk 1500×2100 west wall; balcony glass-door zone clear (≥1500 aisle).
- Study: 1700×800 desk (side-lit), daybed, wardrobe-storage, NAS shelf.
- Baths: master walk-in shower 2200×800 + WC + vanity + radiator; guest bath wet/dry preserved; secondary bath 3-piece in 2250×1650.
- Entry: low shoe cabinet + bench only.

## 6. Secondary master bath — W vs S (RC1 verdict)

| Option | Verdict |
|---|---|
| **W** (west door → suite foyer) | **FEASIBLE — preferred**: private vestibule; door not facing bed; new partition only |
| **S** (south door → bedroom direct) | **FEASIBLE — conditional**: door sits in NEW south wall (former Y4500-b cloakroom segment is absent/stale); shortest path but door faces bed zone; keep clear of residual 600 mm stub x10800–11400 (TO_VERIFY) |
| Drain | East wall shared with master-bath wet zone — candidate only, TO_VERIFY |

The earlier "S INFEASIBLE (no-opening wall)" conclusion is **withdrawn** — it rested on stale DWG lines plus a thickness-based class that RC1 removes.

## 7. Gates — `qc/task03a_gates.json`: **15/15 PASS**

G1 source ✓ · G2 honest W/S + conflicts flagged ✓ · G3 cabinets ✓ · G4 glazing ✓ · G5 beds ✓ · G6 3-piece ✓ · G7 balcony route ✓ · G8 living core ✓ · G9 ramp PROVISIONAL ✓ · G10 delta conflict recorded ✓ · G10b balcony OPEN/PROPOSED ✓ · G11 study ✓ · G12 wet/dry ✓ · G13 KEEP ✓ · G14 program ✓

## 8. Deliverables

- `brief/owner_brief_v1.md` + `.json`
- `current_existing/current_existing_v1.dxf` + `.json`, `source_delta_report.md` (RC1), `source_manifest.json`
- `concept/task03a_preferred_plan.dxf`, `option_smb_entry_W.dxf`, `option_smb_entry_S.dxf`, `split_level_study.dxf`, `concept_data.json`
- `qc/task03a_s1…s6_*` PNG + PDF

## 9. Unresolved / for owner + field

1. **Level delta** — measure L1→L2 finished-floor vertical (one number settles ramp, platform cut, living rectangle).
2. 4 `CLASSIFICATION_CONFLICT` walls (CLK-N/W/E, Y4500-b-CLKSEG): white-class yet demolished — convention reading needs owner confirmation; remaining white set not reliable until then.
3. Y4500-bc + X7900-U ambiguous fill — review.
4. Residual stub x10800–11400 on site? (Option S door clearance.)
5. Secondary bath drain feasibility (same-floor/dropped slab).
6. `D-MASTER?` position; `D-LIV-STUDY?` mystery arc; 10 kg washer arrangement; SMB bedside 800/770 < 900.
7. Balcony enclosure approval boundary (property mgmt).

Commit SHA: RC1 — see git log.
