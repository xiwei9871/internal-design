# Kitchen prompt and failed whole-house batch audit — 2026-10-08

Status: USER_REJECTED_VISUAL_DIRECTION. Read-only source inspection, no new generation. Existing175 images are historical trials, not approved design effects.50 missing images remain outstanding; do not fill them using the rejected generic prompt.

## Sources actually checked

- Codex thread `锁定厨房建设方案`, id01a0f702-42b3-7620-811e-63fc3dda7df1: user required visibly different variants; original A1-only validation used concrete sofa/table constructions, then propagated candidate design across views.
- `/Users/xiwei/interior_design/projects/c_type_home/design/kitchen_frozen_v1/FREEZE_CONTRACT.md`: freezes spatial model and11review cameras, explicitly does NOT freeze final materials/lighting. `material_stage=SIMPLE_REVIEW`, no fabrication release.
- `/Users/xiwei/interior_design/projects/c_type_home/renders/r4_option_a/whole_house_ai_v1/prompt_system.py`: room-specific surface/material variants; kitchen designer lower ash/upper warm-white/grey stone/nickel, creative sage/grey panels/fine tile/warm metal. Not simply more lighting on the same all-wood scheme.
- `/Users/xiwei/interior_design/projects/c_type_home/renders/r4_option_a/whole_house_ai_v1/03_kitchen/prompts/kitchen_K1_designer_v1_review_retry.txt` and matching creative retry: concrete visible material splits and exact window/door/cabinet preservation.
- `/Users/xiwei/interior_design/projects/c_type_home/renders/r4_option_a/whole_house_ai_v1/03_kitchen/reports/ROOM_REVIEW.md`: old set had9geometryPASS,2WARNING,1FAIL and multiple insufficient-divergence warnings. Better photo character does not mean historic geometry is fully trustworthy.
- `/Users/xiwei/interior_design/projects/c_type_home/renders/r3_option_a/living_a1_validation_v2/LIVINGROOM_PROMPT_PACK_V2.md`: geometry clay is authority for layout/camera, not the style template; independent furniture construction hypotheses.
- `/Users/xiwei/.codex/worktrees/c-type-study-daybed/interior_design/projects/c_type_home/renders/whole_house_final_study_v1/production_batch_v1/kitchen/02_designer/VIEW_01.prompt.txt` and creative: generic shared palette, preserve baseline colors, preserve main silhouettes; mediumquality.

## Evidence and diagnosis

1. Current Designer/Creative text similarity87.7% (character SequenceMatcher; prompt diagnostic, not image similarity). Only one short generic design paragraph materially differs. Common instruction says all3versions share the same palette and keep colors close to image1. Result: same ash fronts/creamstone, mostly added lights/decor. Historical room-specific surface splits were lost.
2. Geometry locking expanded into surface/style locking. Fixed architecture/cabinet topology must stay; existing placeholder furniture silhouettes and pale render colors should not dictate every expressive variant. Room-specific rules are needed; do not force upholstery/bedroom mirror instructions into kitchen prompts.
3. Current accurate Blender bases are pale, evenly filled and low in material contrast. AI is asked to preserve lighting, moderate contrast and source colors, so it inherits that weak photographic cue. Low local contrast/contact shadow, timid finishes and blanket ash/color mapping reduce material separation. Concrete photo corrections matter more than adjectives such as photorealistic.
4. Historical runner used Image2highquality on one geometry reference. Current runner uses medium on a materialbase plus geometryreference; all100AIoutputs1672×941 despite requested1920×1080. Highquality is an appropriate test setting, not proof that provider native size/visual quality will improve.
5.175 includes75rawBlenderfaithfuls and100AIvariants. A coarse, pale Blender baseline is useful geometry evidence but not automatically a photograph-quality FAITHFUL presentation. Increasing samples improves noise, not furniture fidelity or artistic lighting.
6. No style-reference raster from the old kitchen case or catalog was actually included in current CLI input; catalog numbers appeared in text only. A selected case/catalog image should be an explicit material/finish reference, with geometry authority limited to latest approved model.

## Corrected pilot, not an automatic new batch

Keep latest full-house model and reviewedV3cameras. Use a current clear geometry input to lock frame/topology. The old case is a finish/photo reference only; never transfer its room/door/window/fridge arrangement. Do not use scheme_a_v12/v13 historical kitchen service-wall text: its layout conflicts with current frozen kitchen.

Kitchen surface hypotheses (draft, not chosen):
A — natural ash base: ash fronts, neutral white quartz, brushed nickel; visible wood/stone/metal separation.
B — warm-white/light-grey: ash lower fronts and narrow surround; existing upper/high panels warmwhite; light warmgrey stone counter/backsplash; nickel tasklight detail.
C — restrained sage: existing upper/high panels muted sage/greige, ashlower; finewarmwhite vertical tile on EXISTING backsplash plane; separate quietstone and warmmetal.

Same camera, fixed cabinet splits, all equipment positions, openings and passage. Distinguish with substantive surface allocations; do not create geometry to reach a count of differences. Retain whiteflatceiling, no cove/curvedceiling. Keep owner furniture counts/function/envelopes elsewhere; evaluate specific furniture forms without reverting accepted later edits.

Photo layer: one believable daylight direction, recognizable penumbra, support contact shadows, retained highlight detail, darkappliance/metal separation, real grainscale, mattefinish and textile microstructure. Do not copy paleclay color/brightness. No vague demand for higher contrast everywhere; preserve darkdetail and windows. Native outputsize recorded, not secretly upscaled.

First produce one kitchencamera×3surface studies and review actual visual difference, cabinet/window fidelity and photograph quality; only a successful pilot justifies propagation. NoAPIcalls in this audit. Pending401/503provider state remains independent of this creative correction.
