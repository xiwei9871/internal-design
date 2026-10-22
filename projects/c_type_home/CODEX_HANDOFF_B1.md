# CODEX HANDOFF — c_type_home B1

## 1. FROZEN FACTS

- `B0_EXISTING_BASELINE = PASS`; ARCH_XY, Z_DATUM, LEVEL_SEMANTICS and OPENINGS are HUMAN APPROVED + FROZEN.
- Authority: `design/blender_b0/B0_FREEZE_MANIFEST.json`. Initial read-only Codex preflight on 2026-10-01: all 7 SHA256 entries MATCH; `B0_INTEGRITY = PASS`.
- Permanent Existing master: `design/blender_b0/B0_EXISTING_AS_IS.blend` (SHA256 `717e6dc4a3d4fb6325512236f5c235ded702376309456028129bf0889548efcb`).
- Split-level residence: LOWER FFL 0 / ceiling 2800 mm; UPPER FFL 450 / ceiling 3250 mm; stairs 150 / 300 / 450 mm.
- Fan leisure hall is Existing UPPER +450; preserve the original CAD r1000 arc. Architectural XY and exact floor/ceiling geometry are inherited from frozen B0.
- 50 mm level field is SEMANTIC_HELPER_ONLY, geometry_authority=false. Nine verified openings are frozen; D-107 remains angled approximately 26.3 degrees; preserve four bay-window geometries.
- GAP-20, AC niche detail, stairwell ceiling local treatment and beam/pipe/soffit dimensions remain TO_VERIFY. Report only; do not infer new Existing geometry.

## 2. CURRENT KITCHEN AUTHORITY — FROZEN V1 (2026-10-01)

- User confirmed the current kitchen views and instructed a complete lock. Official master: `design/kitchen_frozen_v1/KITCHEN_APPROVED_AS_IS_V1.blend`. Read `KITCHEN_FREEZE_MANIFEST.json`, `KITCHEN_FREEZE_REPORT.md`, and `KITCHEN_DIMENSION_SCHEDULE.csv` in that directory before kitchen work. Historic V1–V4 candidates remain evidence, not the current editing entry point.
- State: `HUMAN_APPROVED_SPATIAL_MODEL_FROZEN`. Preserve kitchen layout, coordinates, facing, cabinet/equipment relationships, window corrections, island/connector, adjacent tall cabinet, photo5 buffet and the 11 review cameras. Reopening needs an explicit user request and a new version; keep V1 intact.
- Cabinet order from door inward: 320 mm narrow cabinet → refrigerator and its overhead → inner high-cabinet/niche column. Narrow front aligns with refrigerator; depth range 760–770, model 765; rear socket allowance range 50–60, model 55. Four narrow fronts: top matches overhead; lower three equal. Main countertop H/D 820/600; refrigerator W/D/H 905/710/1700 mm.
- Kitchen small window X6100–7100, model span1000; sill1020 = countertop820 + exposed wall200; head2400. Balcony blue window segment is approximately X2100–5100, span approximately3000 from the user-approved registration diagram. The 4 m wall-derived inference is withdrawn. Approximate diagram coordinates are not surveyed fabrication measurements.
- Red-region `W_wall_md_0042` is a full 1050 mm window-under-wall, not a cabinet. Keep its full height in temporary cut renders. Photo5 buffet stays in its guide footprint1500×500, with four upper/four lower doors, two drawers and an open middle; nominal review height2710, counter1100. Original PDF nominal1580×600 is retained as a fabrication discrepancy, not silently substituted.
- Original PDF C island/connector is retained (counter800×467, H960). Adjacent cabinet W600/H2000 and AC above are confirmed spatial relationships. Depth500 and AC dimensions/mount height remain schematic values; they are not newly measured or released for fabrication.
- Simple review materials remain the target. Final materials, lighting and fabrication nodes are later stages. Kitchen approval does not validate historic LOW/FAILED photo registrations or authorize new photo-derived metric estimates.
- Non-kitchen furniture authority remains the Human Design Guide and registers in `design/b1_blockout/`, calibrated via `design/pascal_b1/FURNITURE_ASSET_CALIBRATION_V02.json`; frozen Z datum supersedes old 350/700 offsets. Do not revert kitchen corrections from initial-PDF blockouts or older B1.1 packages.
- Initial cabinet PDF `source/世纪欣园3-1-901_cabinet_plan.pdf` is only the original installation drawing. Current user-confirmed site relationships take priority; original island pages1/4 C and buffet page6 are component references. Approval attachments and all image evidence are stored on the filesystem. See `design/kitchen_frozen_v1/KITCHEN_VIEW_INDEX.md`.

## 2A. CURRENT WHOLE-HOUSE CANDIDATE V4 (2026-10-01)

- Current full-house candidate: `design/wall_junctions_v4/B1_WALL_JUNCTIONS_CORRECTED_V4.blend`, HUMAN_REVIEW. Read `V4_REVIEW.md`, `V4_MANIFEST.json`, `V4_QA.json`, `V4_VIEW_INDEX.md` and `OPENING_AND_BAY_REGISTER.json`.
- Latest user authorized global continuous/flush wall junctions, all marked ordinary doors/casings/surrounds, a correctly cut guest sliding door and all bay windows using the accepted living-bay method. V4 implements this scope in actual geometry, inheriting V3.
-83 active source walls plus completed opening/bay wall parts produce one closed continuous skin; shared planar-cell geometry avoids coplanar Boolean artifacts.335 unchanged-area exterior samples PASS, max0.30mm finish deviation; zero open/nonmanifold edges. All original wall meshes/poses remain hidden sources, not overwritten CAD/B0.
- Six new registered ordinary door groups including entry double leaf; indoor widths750/850 fromF-DOOR spans, entry350+750. Review height2100; frames/casings/header/side-wall closure included. D107 preserved. GuestG-GB-BALC cut through actual wall y10900–11100, copied frame/glass moved into center11000. Three-trackG-DIN-LIV has complete piers/header/casing.
- W-SMB-S,W-MB-S,W-STUDY-NE now have open inner aperture, projecting sill, front/side-return glazing; old flat-inner and full-height outer proxies inactive. Sill900/head2850/projection700 from inherited data; upper ceiling3250. Living bay method retained.
- Kitchen266 non-wall protected objects unchanged;6 original finish walls retain mesh/pose as hidden sources and are represented by the continuous wall skin. Cabinet/equipment/window dimensions and placement unchanged. B0/kitchen/V1–V3 frozen files hash match. Fifteen paths-only review images inspected; no pending render job.
- Permanent rule: ALL doors, ordinary or sliding glass, have casing/frame and solid continuous walls above/left/right; zero extra pier means casing touches return wall, not a floating door. Never use the withdrawnD107200mm.

### Prior V3 corrections and history

- Current full-house candidate is now `design/living_correction_v3/B1_LIVING_CORRECTED_V3.blend`, HUMAN_REVIEW. Read `V3_REVIEW.md`, `V3_MANIFEST.json`, `V3_QA.json`. The actual mesh now implements RED side50mm / BLUE side0mm visible pier, per the user's final marked screenshot. 200mm was withdrawn. The V2 text-only clarification is historical; it is no longer the current modification status.
- V3 preserves the door leaf and timber frame, the north-balcony door and kitchen272 protected objects. It corrects the side-return boundary, full above-door connection and local overlapping old rectangular wall; no200mm blue-side pier was created and door850×2100 remains inherited. Fresh-open974 states and actual side geometry/ray/projection checks PASS. New corresponding axon/front images are in `design/living_correction_v3/renders/`, return paths only.

### Prior V2 work and clarification history

- Latest D107 user clarification supersedes earlier chat estimates: in the user's annotated view, RED side approximately50mm, BLUE side has no solid wall pier. The earlier200mm side-wall statement was explicitly withdrawn. Read `design/living_correction_v2/D107_LATEST_USER_CLARIFICATION.md`; never add200mm to the blue side or narrow the door from that withdrawn value. No V3 geometry was created/applied. Door850×2100 remains inherited, not a new site measurement.

- Current full-house candidate: `design/living_correction_v2/B1_LIVING_CORRECTED_V2.blend`, HUMAN_REVIEW. Read `V2_REVIEW.md`, `V2_MANIFEST.json`, `V2_QA.json`. It inherits all V1 fixes and the approved kitchen.
- User identified that V1 D107 had no complete frame, surround walls or header/top connection. V2 retains its restored location and26.3° angle, and adds left/right wood frame/architrave, full above-door wall, side-wall joins and upper connection to3250. The frame/beam sections are review values, not surveyed fabrication or structural-engineering dimensions.
- User also identified incomplete north-balcony door framing/walls. V2 closes the north pier y12650–13000.2, joins the original wall corner, keeps the south full wall and extends solid header to2800. The old flat/double-panel proxies are inactive; black single glazed hinged door/frame/threshold/handle/hinges follow photo relationships. Opening850/head2400/room datum are inherited; exact profile remains TO_VERIFY.
- Fresh-open965 states and14 enclosure checks PASS; kitchen272 protected objects unchanged. Prior V1 package, B0 and kitchen freeze files remain intact. Five complete-door views are in `design/living_correction_v2/renders/`, wall cuts absent; always return image paths only.

### Retained V1 corrections and history

- The user reported impossible inner-window/outer-wall layering at the living bay, a missing living/guest-bath partition, and the blue panel beside the chaise. New review candidate: `design/living_correction_v1/B1_LIVING_CORRECTED_V1.blend`, inherited from kitchen frozenV1. Read `LIVING_REVIEW.md`, `LIVING_CORRECTION_MANIFEST.json`, and `LIVING_CORRECTION_QA.json`.
- User site photos establish a projecting sill platform with front and side-return glazing; the inner wall aperture is open to the bay. Corrected B1 layer hides the old inner GLZ/host-window and overlapping full-height bay-front/side proxies. Original CAD XY/window datum retained; photos are relationship evidence, not new metric measurements.
- `W_wall_md_0013` was wrongly classified PARAPET1050 in the intermediary source. New B1 wall retains its exact XY and reaches guest-bath ceiling3250, with guest-bath north junction/adjacent TV return closed. Living ceiling remains2800.
- Red-frame `LEAF_D107` is D-107 = D-SM, the secondary-bedroom angled door. It was displaced by rotating baked world vertices about the origin. New B1 copy restores registered hinge8332/4543/Z450, angle26.3°,850×40×2100 envelope and existing hardware. The old blue proxy is inactive; the new copy is a solid-door review color.
- B0 and kitchen frozen files remain unchanged. These specifically authorized site/bug corrections supersede their erroneous B1 proxy representations while retaining all original data for traceability. Kitchen272 protected objects match. Use this candidate for continuing living discussion; living status remains HUMAN_REVIEW.
- Geometry-review renders are in `design/living_correction_v1/renders/`; no wall cuts, ceiling/glass temporarily hidden,07 additionally hides furniture to show the sill. Rendering visibility never writes back to the complete model. Keep generated images out of chat context and return paths only.

## 3. DO NOT CHANGE

- Never overwrite B0 or any manifest-frozen source. Recheck hashes before modeling and before delivery; stop immediately on mismatch.
- Never reinterpret CAD, reconstruct B0 from historical scripts, revise zoning/Z datums, or generate architectural contours from the grid.
- Never move furniture, optimize circulation, swap rooms, demolish walls, enlarge the living room, implement the future ramp, or change bathroom layout/kitchen topology automatically. The kitchen as-built corrections listed above were explicitly authorized by the user; do not revert them to initial-PDF blockouts.
- Never orthogonalize D-107 or flatten bay windows.
- Keep ramp, leisure demolition and living expansion as hidden FUTURE DESIGN OPTIONS, separate from Existing.
- Do not begin final materials, final lighting, Cycles final rendering, AI image exploration or a web viewer in B1.1.

## 4. CONTEXT SIZE RULE — PERMANENT USER INSTRUCTION

Do not attach or inline large binary/image assets into chat context. Save all generated renders, overlays, contact sheets and photo proxies to the project filesystem and return paths only. Inspect high-resolution originals on demand, one or a few files at a time. The repository-level `AGENTS.md` carries the same rule.

## 2B. HOUSE BASE AND SECONDARY BATH OPTIONS (2026-10-02)

- Frozen base: `design/wall_corners_v5/HOUSE_BASE_GEOMETRY_V1.blend`, status `HOUSE_BASE_GEOMETRY_V1_FROZEN`; read `HOUSE_BASE_MANIFEST.json`. Branch all future renovation concepts from it and preserve it.
- Current study south opening stays open in the base; it is existing condition. Black solid walls are preserved; white/modifiable segments are the only candidates for future partitions.
- The requested secondary-bath decision is not in the base. Read `design/secondary_bath_options/OPTION_SPEC.md`: Option A is a south sliding door (recommended for the small room); Option B is a south inward-swinging hinged door. Both keep the original cloakroom footprint and existing black walls; approval is required before adding either option to geometry.

## 2C. CURRENT BASE V2 AND SECONDARY-BATH COMPARISON (2026-10-02)

- Updated frozen base: `design/wall_corners_v5/HOUSE_BASE_GEOMETRY_V2_FROZEN.blend`, with the rear wall behind the independent kitchen display cabinet. Read `HOUSE_BASE_GEOMETRY_V2_FROZEN_MANIFEST.json`; V1 remains preserved.
- Secondary-bath branches were rebuilt from the updated V2 geometry: `design/secondary_bath_options/OPTION_A_SLIDING.blend` and `OPTION_B_INWARD_SWING.blend`. Read `OPTION_COMPARISON.md` and `OPTION_COMPARISON.json`.
- Option A south sliding passes its clearance review. Option B south inward swing is modeled for comparison and is explicitly flagged because its sweep intersects the existing wet-zone envelope. Neither option is construction-released or written into the frozen base.

## 2D. LATEST RENOVATION R3 — SUPERSEDES 2C OPTIONS (2026-10-02)

- Current renovation comparison authority: `design/secondary_bath_options/CURRENT_REVIEW.md` → `r3/R3_REVIEW.md`. Use `r3/OPTION_A_SLIDING_R3.blend` / `r3/OPTION_B_INWARD_R3.blend`; old root A/B and R2 are historical, with their older layout/clearance conclusions withdrawn.
- Explicit latest instruction: REMOVE the later-added angled D107 leaf/frame/casings and its added surrounding walls in the active renovation branches, restore the pre-enclosure state, THEN build the full west wall from latest FreeCAD. Seven added surround sources are removed locally from the active skin; original black CAD wall operands remain. `r3/RESTORED_OPEN_STATE_BEFORE_BATH_R3.blend` is the separately saved intermediate. Frozen V2 file remains intact.
- `r3/LAYOUT_CONTRACT.json` records actual FreeCAD Shape geometry. Latest NW1200×500 vanity, NE chamfered shower, SE west-facing WC,1400×600 south wardrobe. Entrance is west of wardrobe; A slides east into the hidden wall pocket. The1200×100 guide is not clear door width. Full west rectangle retained without avoidance notch.
- A rail and hanger channel are continuous through entrance/parking; B is west-hinged inward85° with floor stop. Actual fresh-open geometry, same fixtures A==B==FreeCAD, full south/header closure, door motion and source/kitchen preservation verified. Approx729mm net entry and cramped shower/glass entry need final profiles/site/SKU review. A recommended; options remain unselected review branches.
- Study: user reference establishes natural wood long tea table + rear open bookcase + adjacent LOW TEA-SERVICE COUNTER, not low bookcase. Sink/tap/feed/drain and induction/kettle modeled. Current group is Rectangle024/025/026 (historical R-BED-N). User explicitly chose preserving FreeCAD positions; no350mm north table shift.297mm table/counter gap remains a documented real-use limitation. Read `r3/STUDY_TEA_REGISTER.json`.
- All render/plan/sheet/proxy assets are on disk, paths only. Review geometry/styles are not final materials/lighting or construction approval. Kitchen/frozen V2/B0 files unchanged; current renovation geometry changes stay in R3.

## 2E. LATEST R4 ORDINARY BEDROOM DOOR AND CONTINUOUS FLOOR (2026-10-02)

- User corrected the earlier removal interpretation: secondary-bedroom entrance remains, now an EAST-WEST ordinary door, west hinge, SOUTH inward swing. The old slanted D107 is still removed; the R3 no-door gap is superseded. Current full models: `design/bedroom_door_r4/OPTION_A_SLIDING_R4.blend` / `OPTION_B_INWARD_R4.blend`. Read `R4_REVIEW.md`, manifests and QA. R4 A is the latest source for rendering; all original R3/frozen files are retained.
- Ordinary leaf nominal850mm; complete frame/casing/header/side connections. Current gap/frame sections/hinge position are review installation geometry, not new site measurements. Bathroom A/B and full west rectangle, kitchen and study remain inherited.
- User found old triangular threshold floor artifacts. Active upper floor rebuilt as closed slabs with only the local old angled transition filled at+450mm; no added step, thin visual cover, or remote plan-boundary change.63 floor rays at450mm and721 angular samples including actual handles PASS. Closed floor topology has zero boundary/nonmanifold edges.
- Corrected AI candidates: `renders/r3_option_a/living_batch_v2_door/CORRECTED_IMAGE_INDEX.md`: A2,A4,D1 × strict/design/explore =9 generated, using new clay from R4. Old batch A2/A4 are historical visual candidates, not current door/layout evidence. AI surfaces/exterior styling are inspiration and not geometric proof. Continue simple geometry/clay and AI-first output; no Blender final rendering work.
