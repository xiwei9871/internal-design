# TASK 03A RC2.2 — Measured Existing → Verified Owner Brief → Concept Floor Plan

Status: **REVIEW-READY / GATES PASS 26/26** (not FINAL PASS — owner review pending)
Branch: `feat/c-type-task03a-measured-concept` (base `improve/design-output-v14 @ 20637d1`)

> **RC2.2 (window register + drawing cleanup)**: 11-record window register (`current_existing/window_register.json/.csv`); all dev-plan windows/bays reconstructed with wall segmentation + glazing symbols; floating wall segments root-caused (living bay front misplaced → glazed front of `W-LIV-N`; study `W-EXT-NE` band was inside NE bay projection → corrected to measured face); bottom-left grey L = real life-balcony parapet, now labeled; furniture plan split into owner-facing **presentation** + diagnostic **QC** sheets; new gates G21–G25. Full detail: `qc/TASK03A_RC2_2_WINDOW_CLEANUP.md`. No layout/design coordinate changed (G25 freeze-verified vs `246ff12`).

---

# RC2.1 notes (kept for history)

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
> 9. **RC2.1 throat closure**: guest-room door re-hung outward / surface sliding on existing opening → bunk back to 1500×2100 portrait on west wall → continuous ≥800 mm path entry→balcony (old 300 mm throat eliminated). SMB bath re-balanced WC 650 / aisle **800 continuous** / shower 800×1650 with drawn glass panel + 750 entry; S door widened to 750. G17 now checks minimum aisle width; G18 checks connected-path throat widths, not just per-zone clearance.

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
- Guest bedroom bunk 1500×2100 portrait on west wall; entry door re-hung outward / surface sliding (existing opening, no new wall cut); continuous ≥800 mm lane entry → bedside → balcony glass door; desk SE.
- Study: 1700×800 desk (east of door swing), daybed 800×2000 west wall, wardrobe-storage KEEP east, NAS shelf — no overlaps, aisle 1500 mm.
- Baths: master corner shower **1600×900** NE (fold seat + grab bars + handheld) + WC SE + vanity NW + radiator; guest bath wet/dry preserved; secondary bath 3-piece in **shell + annex ≈ 5.0 m²** with **800 mm continuous main aisle** (WC 650 W / aisle x9700–10500 / shower 800 E, glass panel + 750 entry).
- Entry: low shoe cabinet + bench only.

## 6. Secondary master bath — W vs S (RC2 verdict)

| Option | Verdict |
|---|---|
| **S** (750 door in NEW south partition y3800 → bedroom) | **FEASIBLE — RECOMMENDED**: zero demolition; hinge east, swings into annex; swing zone fixture-free; annex reaches ~5 m²; internal aisle 800 continuous |
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
9. Guest-room entry door: re-hung outward into corridor or surface sliding on existing opening — TO_VERIFY on site (leaf/hardware); corridor-side swing envelope noted.
10. SMB bath aisle balanced at 800 mm (WC 650 / shower 800 deep) — further widening would cost WC width or shower depth below spec.

Commit SHA: RC1 `27d9ff9` · RC1.5 `b01cd19` · RC2 `8a5fdad` · RC2.1 — see git log.

---

## RC4 — Versioned CAD-Native Pipeline

Pipeline switched: immutable measured source -> copied design versions -> CAD gates -> PNG/PDF rendered FROM the versioned DXF. JSON stays semantic/QC truth; it no longer draws the formal output.

### Source freeze (immutable, read-only)
- `source/世纪欣园FF.dwg` sha `f01a9bb5de96`
- `cad/measured_working.dxf` sha `3711c47c1172` — dwg2dxf (LibreDWG), AC1018, INSUNITS=4 (mm), 342 entities, 8 layers (S-S.WALL 216 / RC-GRILL 60 / F-DOOR 18 / S-COLUMN 18 / F-SAN FIT 16 / F-TEXT 6 / S-楼梯 7 / F-FURN 1)

### Version chain — `cad/cad_version_manifest.json`
| version | file | parent | sha256[:16] |
|---|---|---|---|
| MEASURED | `cad/measured_working.dxf` | — | `3711c47c1172fbdb` |
| V01 | `cad/design_v01_existing_sync.dxf` | MEASURED | `684a172808709a39` |
| V02 | `cad/design_v02_f1_l1.dxf` | V01 | `ca592fcfd3e714ea` |

V01 = open measured + save-as (all 342 source entities inherited, `missing=0`; nothing deleted — dispositions move entities to audit layers). V02 = copy of V01 + F1.1 furniture only.

### Entity counts
- V01: 481 entities (342 inherited + corrections, tags, cabinets, labels)
- V02: 522 entities (+41 F1.1: furniture blocks/inserts, ramp, QC zones)

### Change registry — `cad/cad_change_registry.json` (41 entries)
- DEMOLITION: 6 (real removed walls, kept on `A-WALL-DEMO`)
- SURVEY_SUPERSEDED: 6 (stale survey lines + cosmetic wall hatches on `A-SURVEY-SUPERSEDED`/`A-SURVEY-HATCH`)
- OWNER_CORRECTION: 4 (`A-WALL-EXST-CORR` corrected current walls — incl. segments where survey only had fill hatches)
- NEW_DESIGN: 25 (cabinets, tags, F1 furniture)

Every DEMO/SUPERSEDED/CORRECTED entity carries a registry record with source handle, geometry, reason, evidence (G4/G11).

### CAD-native rendering — `scripts/task03a_render_dxf.py`
`design_vXX.dxf -> ezdxf MatplotlibBackend -> PNG/PDF`, two profiles from the same DXF:
- CAD_REVIEW: all layers incl. DEMO/SUPERSEDED/hatch/dims/tags
- PRESENTATION: hides audit/QC/old-survey-text layers
Each output has a `<name>.render.json` sidecar (source DXF sha, parent sha, profile, visible/hidden layers).

Notes: text in render needs inline font code + column width (MTEXT); ACI color 7 renders white on white — annotation layers use dark ACIs. Off-plan survey legend (RC-GRILL notes ~300000mm away) is clipped from view extents, not deleted.

### RC4 gates — 12/12 PASS (54/54 total)
RC4-G1 source immutable · G2 full-copy inheritance 342/342 · G3 lineage chain valid · G4 registry coverage complete · G5 9 windows tagged+glazed · G6 14 door openings · G7 9 kitchen cabinets · G8 F1 coords changed=none · G9 canonical walls covered · G10 render provenance traced · G11 SUPERSEDED never = DEMOLITION · G12 no parent overwrite

Legacy `task03a_render_qc.py` marked DEPRECATED_FOR_FORMAL_OUTPUT (kept for migration comparison; S1–S6 migrate after RC4 review PASS).

### Review outputs
- `qc/rc4_v01_cad_review.png/.pdf`, `qc/rc4_v01_presentation.png/.pdf`
- `qc/rc4_v02_f1_cad_review.png/.pdf`, `qc/rc4_v02_f1_presentation.png/.pdf`

---

## RC4.1 — closeout (review findings)

### cover_ratio() bug
`dy = min(ex[3], wr[1]) - max(ex[1], wr[1])` used `wr[1]` twice — zero-area
LINE entities took the 1D branch so walls were unaffected, but areal
entities (LWPOLYLINE/HATCH) could score wrong coverage. Fixed to `wr[3]`.
Re-run disposition diff (buggy → fixed, 16 handles):
- `307CB3`: KEEP → **DEMO** (W-INT-X5800 owner-confirmed demolished —
  the only semantic change; entity now correctly on A-WALL-DEMO)
- 15 others: KEEP → KEEP, now correctly matched to EXISTING walls
  (incl. W-EXT-N-BAL parapet polyline, FOYER/CLK-W bands — no layer change)

### Parapet/railing dispatch
Builder now branches on canonical `type`: `railing_parapet` → new layer
`A-PARP-EXST`, never `A-WALL-EXST-CORR`. Records: W-EXT-N-BAL,
W-NBALC-E-PAR (north balcony, OPEN_NOT_ENCLOSED), W-BALC-W, W-BALC-S.
New gate RC4-G13: no railing_parapet geometry on wall layers; parapet
linework must exist. `qc/rc4_v01_open_balcony_check.png` = cropped review
of the north balcony for eyeball confirmation.

### change_type refactor
`DEMOLITION` (real teardown) / `SURVEY_SUPERSEDED` (stale survey, audit) /
`EXISTING_CORRECTION` (current-condition fixes, was OWNER_CORRECTION/NEW_DESIGN) /
`EXISTING_ENRICHMENT` (survey of existing assets into CAD: kitchen cabinets,
keep-items — was NEW_DESIGN) / `PROPOSED_DESIGN` (F1 furniture etc.).
`owner_confirmation` is now false for PDF/CAD-derived records (kitchen
cabinets etc.); true only where the owner actually confirmed.

### Review render crop
Flat-banner bug was `MatplotlibBackend.finalize()` resizing the figure by
autoscaled content (off-plan RC-GRILL legend). Now `adjust_figure=False` +
explicit plan-region limits — CAD_REVIEW shares the plan crop with
PRESENTATION; nothing deleted from the DXF.

Registry now 42 entries; gates 55/55 PASS.
