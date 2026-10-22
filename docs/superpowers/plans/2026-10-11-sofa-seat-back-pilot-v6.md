# Sofa Seat and Back Pilot V6 Implementation Plan

> **For agentic workers:** Execute inline with `executing-plans`; subagents=0 per project instructions. Steps use checkbox (`- [ ]`) syntax for tracking. The user already approved this bounded pilot; no further implementation-choice question is required.

**Goal:** Produce one visibly softer seat/back assembly from real-product construction evidence, with editable geometry and fixed before/after views.

**Architecture:** Preserve all V5 and architectural files. Build a separate, isolated custom-construction candidate guided by owner catalog p4/p8, the selected A reference, and the researched Blender Guru / local-sculpt workflow. Seat foam/core/soft wrap and channel-filled back use different shapes; macroform must improve in clay before fabric. Trial proportions may reveal a conflict with the old 700 mm furniture placeholder, which must be reported without writing back to the house.

**Tech Stack:** Blender5.2 Python/CLI, native sculpt brushes when supported, existing V5 packed wood/linen materials, Pillow for smallJPEG review, SHA256 preservation checks.

---

## Task 1: Evidence and native tool probe

- [x] Confirm worktree writes, task branch and nine protected hashes; save `design/sofa_soft_pilot_v6/PRESERVATION.json`.
- [x] Extract catalogp4/p8 and selectedA into compact local references; confirm the whole construction rather than borrowing unrelated cushions.
- [x] Read the actual photos and note seat crown, boxing, back contour and unsupported dimensional assumptions in `docs/c-type-sofa-pair-pilot-v6-review.md`.
- [x] Probe native Blender sculpt brushes on an isolated disposable mesh. Record whether actual stroke changes occur; do not claim sculpting if the operator is unavailable or unchanged.

## Task 2: Whole-pair macro geometry and clay evidence

- [x] Create `projects/c_type_home/scripts/build_sofa_pair_pilot_v6.py`, loading only V5 material/old-pair data into a new empty scene.
- [x] Reproduce a V5 pair in an independent comparison collection. Use source pose, not nonuniform asset resizing.
- [x] Build the candidate as documented custom construction: foam core, supported base, soft wrap, separate top/bottom panels and boxing; separately shaped feather/fiber back with restrained local seams. Keep reference-target widths/depths as recorded trial dimensions; don't force old pad thickness or pinning into the new shape.
- [x] Save `SOFA_SEAT_BACK_MACRO_V6.blend`; render front/profile/three-quarter with neutral Workbench shading. Compare with V5 and the same references.
- [x] Reject a macroform that remains flat or boxlike; allow one coherent source repair and keep before/after outputs. Record actual dimensions, support contacts and any source-height conflict.

## Task 3: Local finishing, fabric and delivery

- [x] Complete the source with native local sculpt or explicitly documented reference-constrained static surface edits; no periodic/noise field as a surrogate for cushion form.
- [x] Use existing V5 wood unchanged and native 4K linen with actual-scale pattern UVs. Don't add unselected pillows or borrow restricted tutorial textures.
- [x] Render only the three decision views, plus matching V5 comparisons, in the same neutral studio. Room/house rendering is outside this pilot.
- [x] Fresh-open verification checks: nine protected hashes; closed/supported primary shell; no missing textures; output dimensions recorded; baseline objects intact; numerical shape checks distinct from visual acceptance.
- [x] Package `renders/whole_house_final_study_v1/sofa_soft_pilot_v6/review_gallery.html`, small JPEG contact and native .blend links. Open actual images and browser gallery before completion.
- [x] Persist `render_config/sofa_soft_pilot_v6/CONTRACT.json`, review/limitations and owner-review status. Explicitly stage scripts/docs/registry only, diff-check, commit/push task branch, report PR auth blocker if present. Stop at HUMAN_REVIEW; no whole-house propagation.

## Verification commands

All commands start with `rtk`; Blender runs one process at a time with two CPU threads. Use the saved source scripts to build, render and verify in fresh background processes. All scripts must parse using Python `ast.parse`; final `git diff --cached --check` and staged-path review must pass. Generated binaries, images and source textures remain local. The user judges photo likeness; file existence or a mesh-bound check is not the aesthetic pass criterion.
