# A1/A2 F1 Design Knowledge Audit

**Scope:** F1 living / dining / kitchen relationship. This is an analysis artifact; it does not modify CAD or canonical data.

## 1. Rules already satisfied

- **LIV-CIRC-001 — SATISFIED_WITH_RESERVATION**: F1 P1/P3/P5 paths are explicitly recorded; public transition is documented as >=1100 mm in concept_data. _(source: SRC-AARP-HOMEFIT)_ **Issue:** Confirm wall-side pinch points after final furniture INSERTs.
- **LIV-FLEX-003 — SATISFIED**: F1 G8 gate defines a 3800 x 4350 mm flexible living core and exempts only small movable tables. _(source: SRC-PRACTICE-ERGONOMICS)_
- **LIV-MEDIA-006 — SATISFIED_WITH_RESERVATION**: LIV-MEDIA-WALL is locked at the east edge and P5 to the north balcony is recorded. _(source: SRC-PRACTICE-ERGONOMICS)_ **Issue:** Selected projector throw and glare remain TO_VERIFY.
- **LIV-EDGE-008 — SATISFIED**: Large sofas are edge-loaded west/north and the media wall is edge-loaded east. _(source: SRC-PRACTICE-ERGONOMICS)_
- **DIN-CIR-005 — SATISFIED**: DIN-SEATING-N/S zones record 600 mm pull-out each long side for the 1500 x 600 table. _(source: SRC-PRACTICE-ERGONOMICS)_
- **DIN-CIR-007 — SATISFIED_WITH_RESERVATION**: F1 P2 entry-to-dining-to-kitchen route is explicitly recorded. _(source: SRC-PRACTICE-ERGONOMICS)_ **Issue:** Check chair pull-out against the live kitchen edge after any change.
- **KIT-KEEP-010 — SATISFIED**: K-CAB is in fixed_keep and the project brief marks existing kitchen cabinetry KEEP. _(source: SRC-C-TYPE-BRIEF)_
- **AGE-CIR-001 — SATISFIED_WITH_RESERVATION**: F1 records a primary circulation target >=1100 mm and a separate ramp route. _(source: SRC-AARP-HOMEFIT)_ **Issue:** This is a planning record, not an accessibility compliance finding.
- **CIR-CONT-007 — SATISFIED**: P5 living -> G-LIV-NBALC -> north balcony is explicitly recorded; balcony current state is OPEN_NOT_ENCLOSED. _(source: SRC-C-TYPE-BRIEF)_
- **CIR-RAMP-009 — SATISFIED_WITH_TO_VERIFY**: Existing stair and assisted/power-wheelchair ramp are both documented in concept_data. _(source: SRC-C-TYPE-BRIEF)_ **Issue:** Level delta and slope remain provisional.

## 2. Potential rule conflicts

- **LIV-CIRC-002 — POTENTIAL_CONFLICT**: The current F1 record does not expose every secondary route width as a measured polygon. **Next check:** Verify every furniture-free segment around the seating group, not only named paths.
- **DIN-CIR-006 — POTENTIAL_CONFLICT**: Dining seating zones document 600 mm pull-out, but a separate behind-seated passage is not explicitly measured. **Next check:** Test the south and north sides against the 900 mm target before freezing dining furniture.
- **KIT-SAF-008 — UNRESOLVED**: The cabinet KEEP zone is protected, but appliance-door envelopes are not represented in furniture_l1_final.json. **Next check:** Verify selected refrigerator/oven/dishwasher doors and landing surfaces.
- **AGE-THR-005 — TO_VERIFY**: Ramp slope is recorded as 400 / 2500 = 1:6.25 PROVISIONAL and level delta is owner <=350 vs CAD ~400. **Next check:** Field measure level change and obtain local accessibility review.
- **BTH-AGE-005 — NOT_IN_F1_SCOPE**: F1 audit covers living/dining/kitchen; bathroom fixture backing and transfer geometry are not part of this layout snapshot. **Next check:** Carry into the bathroom-specific review before construction.

## 3. Project-specific conflicts

- **P-KITCHEN-KEEP — RESPECTED**: K-CAB remains in fixed_keep; no kitchen cabinet rewrite was proposed.
- **P-PROJECTOR-LIVING — PARTIAL**: Media wall position is locked and no full-wall cabinet is specified; device throw/glare still TO_VERIFY.
- **P-NORTH-BALCONY — RESPECTED**: Current model records OPEN_NOT_ENCLOSED; future enclosure remains note-only.
- **P-SPLIT-LEVEL — PARTIAL**: Existing stair and alternate ramp coexist; the project itself marks slope and level delta provisional.
- **P-CHILD-ACTIVITY — RESPECTED_WITH_CHECK**: Living core is kept open and sightline intent is documented; tall storage and final device placement still need checking.

## 4. Relevant precedents

- **PREC-002** Renovation of Joan Blanques apartment — relevance 0.9250; tags: before-after, clear-circulation, existing-structure, flexible-living, floor-plan, kitchen-adjacency, open-living-dining, renovation, visual-connection; [source](https://www.archdaily.com/962398/renovation-of-joan-blanques-apartment-allaround-lab)
- **PREC-003** Renovation of a Milan Laboratory to a Family Loft — relevance 0.9250; tags: adaptive-reuse, before-after, child-friendly, existing-structure, family-loft, flexible-living, floor-plan, kitchen-adjacency, multigenerational, open-living-dining, renovation; [source](https://www.archdaily.com/981991/renovation-of-a-milan-laboratory-to-a-family-loft-tomoarchitects)
- **PREC-015** Apartment Renovation in Sants — relevance 0.7250; tags: before-after, child-friendly, existing-structure, flexible-living, kitchen-adjacency, multigenerational, open-living-dining, renovation; [source](https://www.archdaily.com/985123/apartment-renovation-in-sants-parramon-plus-tahull-arquitectes)
- **PREC-017** Renovation of Sofia's apartment — relevance 0.7200; tags: before-after, child-friendly, existing-structure, flexible-living, kitchen-adjacency, multigenerational, open-living-dining, renovation; [source](https://www.archdaily.com/1029144/renovation-of-sofias-apartment-pedro-ignacio-yanez-plus-carolina-recondo)
- **PREC-001** Renovation of an Industrial Building into a Single Family House — relevance 0.9250; tags: adaptive-reuse, before-after, child-friendly, existing-structure, flexible-living, floor-plan, multigenerational, open-living-dining, renovation; [source](https://www.archdaily.com/505261/renovation-of-an-industrial-building-into-a-single-family-house-guim-costa-calsamiglia)
- **PREC-005** Residential Extension MF Pavilion — relevance 0.9062; tags: child-friendly, existing-structure, flexible-living, floor-plan, multigenerational, open-living-dining, renovation; [source](https://www.archdaily.com/920031/residential-extension-mf-pavilion-guillermo-tirado-gzz-architects)
- **PREC-008** Renovation of a Mill and Hayloft for Residential use — relevance 0.8350; tags: adaptive-reuse, before-after, community-living, existing-structure, family-loft, flexible-living, floor-plan, kitchen-adjacency, open-living-dining, renovation, study-guest-hybrid; [source](https://www.archdaily.com/983855/renovation-of-a-mill-and-hayloft-for-residential-use-funcionable-arquitectura)
- **PREC-055** Renovation of the Jiakaxia Ancient Courtyard — relevance 0.5150; tags: balcony-connected, before-after, courtyard, daylight, existing-structure, flexible-living, renovation, split-level, split-level-courtyard, visual-connection; [source](https://www.archdaily.com/1031087/renovation-of-the-jiakaxia-ancient-courtyard-hypersity-architects)

## 5. Applicable patterns

- **PAT-AGE-01 — STEP-FREE-ALTERNATE-ROUTE**; evidence: PREC-004, PREC-009, PREC-013, PREC-014, PREC-021
- **PAT-AGE-02 — VISIBLE-SOCIAL-ROUTE**; evidence: PREC-002, PREC-004, PREC-006, PREC-009, PREC-013
- **PAT-BED-01 — BEDROOM CLEAR-SIDE ROUTE**; evidence: PREC-002, PREC-004, PREC-006, PREC-009, PREC-027
- **PAT-CIR-01 — FURNITURE-FREE CIRCULATION SPINE**; evidence: PREC-002, PREC-004, PREC-006, PREC-009, PREC-027
- **PAT-KIT-01 — RETAINED-KITCHEN WORKFLOW**; evidence: PREC-001, PREC-002, PREC-003, PREC-004, PREC-005
- **PAT-KIT-02 — COMPACT-WORK-TRIANGLE**; evidence: PREC-002, PREC-003, PREC-006, PREC-007, PREC-008
- **PAT-LIV-01 — CLEAR CENTRAL LIVING CORE**; evidence: PREC-001, PREC-002, PREC-003, PREC-005, PREC-006
- **PAT-BED-02 — STUDY + BACKUP SLEEPING**; evidence: PREC-001, PREC-002, PREC-003, PREC-004, PREC-005

## 6. Unresolved spatial issues

- **U-001** Field measure the split-level level delta and ramp slope before treating the alternate route as accessible. _(citations: AGE-THR-005, CIR-RAMP-009, P-SPLIT-LEVEL)_
- **U-002** Verify projector/laser-TV throw, glare and cable/service path with the selected product. _(citations: LIV-MEDIA-005, LIV-DIST-007, P-PROJECTOR-LIVING)_
- **U-003** Measure dining chair pull-out and the behind-seated passage together with the retained kitchen edge. _(citations: DIN-CIR-005, DIN-CIR-006, DIN-CIR-007, P-KITCHEN-KEEP)_
- **U-004** Carry aging-in-place bathroom backing, transfer and turning checks into the later bathroom review. _(citations: BTH-AGE-005, BTH-CIR-006, P-AGE-MOTHER)_

## 7. Next design directions

- **D-01 — Test a furniture-free living spine**: Keep the current edge-loaded seating and compare one or two movable-table positions while protecting P1, P3 and P5. _(citations: LIV-CIRC-001, LIV-FLEX-003, PAT-CIR-01, PAT-LIV-01)_
- **D-02 — Resolve dining as a kitchen extension**: Run a full-size 1500 x 600 table test with 600 mm pull-out and a measured 900 mm behind-seated route against the KEEP cabinet edge. _(citations: DIN-CIR-005, DIN-CIR-006, DIN-CIR-007, PAT-LIV-04, PAT-LIV-05)_
- **D-03 — Verify the assisted route before styling**: Field-measure level delta, ramp slope and landing dimensions, then keep the current stair/ramp dual-route logic until local review is complete. _(citations: AGE-THR-005, CIR-RAMP-009, PAT-AGE-01, P-SPLIT-LEVEL)_

## Boundary

This audit does not authorize V03, furniture re-layout, or any CAD edit. Existing geometry remains the source of truth until the owner approves a next design direction and outstanding measurements are resolved.
