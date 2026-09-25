# RC4.2 Wall Readability Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Regenerate the RC4.1 V01/V02 Presentation artifacts with render-only, CAD-aligned wall fragments while proving that no frozen CAD or semantic geometry changed.

**Architecture:** `canonical_plan_v1.json` supplies semantic wall/window classification and the versioned V01/V02 DXFs supply graphical geometry truth. The renderer validates coverage, subtracts axis-aligned opening/window unions into rectangular wall fragments, then draws explicit z-ordered overlays under the DXF linework. The existing gate checker consumes renderer reports and exact frozen hashes; human visual review remains a required review status rather than an automatic pass.

**Tech Stack:** The project `.venv/bin/python` runtime, ezdxf, Matplotlib, Pillow, JSON, SHA-256, existing `task03a_render_dxf.py` and `task03a_gate_check.py` scripts.

---

## File map

- Modify: `projects/c_type_home/scripts/task03a_render_dxf.py`
  - Switch the semantic input to `current_existing/canonical_plan_v1.json`.
  - Add DXF coverage validation, deterministic rectangular wall-fragment subtraction, explicit style/z-order handling, baseline-aware before/after assembly, and render reports.
- Modify: `projects/c_type_home/scripts/task03a_gate_check.py`
  - Add RC4-G14 through RC4-G18 and keep all existing gates unchanged.
- Create: `projects/c_type_home/qc/rc4_2_baseline/rc4_1_v01_presentation.png`
- Create: `projects/c_type_home/qc/rc4_2_baseline/rc4_1_v02_f1_presentation.png`
- Create: `projects/c_type_home/qc/rc4_2_baseline/rc4_1_v01_presentation.pdf`
- Create: `projects/c_type_home/qc/rc4_2_baseline/rc4_1_v02_f1_presentation.pdf`
- Create: `projects/c_type_home/qc/rc4_2_baseline/manifest.json`
- Create: `projects/c_type_home/qc/rc4_render_report.json`
- Create: `projects/c_type_home/qc/rc4_2_wall_display_before_after.png`
- Create: `projects/c_type_home/qc/rc4_2_wall_readability_check.png`
- Create: `projects/c_type_home/qc/rc4_2_wall_readability_check.pdf`
- Regenerate: `projects/c_type_home/qc/rc4_v01_presentation.png/.pdf/.render.json`
- Regenerate: `projects/c_type_home/qc/rc4_v02_f1_presentation.png/.pdf/.render.json`
- Update: `projects/c_type_home/qc/task03a_gates.json`

The implementation must leave `cad/measured_working.dxf`, V01, V02, all
canonical JSON files, the change registry, and F1 furniture data untouched.

## Task 1: Freeze the RC4.1 baseline before overwriting outputs

**Files:**

- Create: `projects/c_type_home/qc/rc4_2_baseline/*`
- Modify: `projects/c_type_home/scripts/task03a_render_dxf.py` only after the baseline copy exists

- [ ] **Step 1: Verify the four source presentation artifacts exist and match the recorded RC4.1 hashes.**

Run:

```bash
rtk shasum -a 256 \
  projects/c_type_home/qc/rc4_v01_presentation.png \
  projects/c_type_home/qc/rc4_v02_f1_presentation.png \
  projects/c_type_home/qc/rc4_v01_presentation.pdf \
  projects/c_type_home/qc/rc4_v02_f1_presentation.pdf
```

Expected hashes:

```text
37a9fb82ad7cd4219fc9cdb204b45edc7e65fcfff723394ecac3cdf3d6ef9dec  rc4_v01_presentation.png
ae226d24e58dea0ae9e1269d75e8759d39df2e1ec54af25386a61a6a7f48ee53  rc4_v02_f1_presentation.png
099c289079e74785de743adbcb21d77f640081d2b37dce497e045cf549623c3a  rc4_v01_presentation.pdf
8200025316220af26a0d59d9fec5a0d9ba6b32701c609cb126b587cec97c4509  rc4_v02_f1_presentation.pdf
```

- [ ] **Step 2: Copy the four artifacts to the immutable RC4.2 baseline directory.**

Run `rtk proxy mkdir -p projects/c_type_home/qc/rc4_2_baseline`, then copy each source to the matching `rc4_1_*` destination with `rtk proxy cp`. Do not move or delete the existing files.

- [ ] **Step 3: Write `manifest.json` with source path, destination path, SHA-256, image dimensions, and the renderer view box used by the existing outputs.**

The manifest must include one record per artifact and must fail closed if any source file or hash is missing. Compute the V01/V02 view boxes with the same pre-RC4.2 linework-extents helper and Presentation filters that produced the source outputs, then store task01-coordinate and absolute-coordinate bounds. The view box is needed to crop baseline and after images in the same CAD coordinate frame.

- [ ] **Step 4: Re-run the four SHA checks against the copied baseline files.**

Expected: all four copied hashes equal the RC4.1 values above before any renderer invocation.

## Task 2: Align canonical semantics with active V01/V02 DXF geometry

**Files:**

- Modify: `projects/c_type_home/scripts/task03a_render_dxf.py`

- [ ] **Step 1: Load `current_existing/canonical_plan_v1.json` and retain the existing DXF inputs.**

Do not load `current_existing_v1.json` as the wall semantic source. Preserve the canonical records for `walls`, `openings`, `windows`, and `balconies`.

- [ ] **Step 2: Define the active geometry layer set and coverage check.**

For each target DXF, inspect only active wall geometry on `S-S.WALL` and `A-WALL-EXST-CORR`; inspect `A-PARP-EXST` for parapets. Use the existing rectangle coverage helper pattern from `task03a_gate_check.py`. A canonical wall must have at least 50% covered linework, and a parapet must have at least 50% covered parapet or source wall linework. Record the matched layers and coverage in the render report.

- [ ] **Step 3: Validate canonical rectangles before fragment generation.**

Reject malformed rectangles (`x2 <= x1` or `y2 <= y1`), unknown wall types, missing IDs, and any existing wall with insufficient active-DXF coverage. Never create a render-only face for a failed alignment.

- [ ] **Step 4: Add a read-only alignment smoke check.**

Run the renderer module’s alignment function against both V01 and V02 without saving output. Expected: all 39 `EXISTING` canonical wall records align, consisting of 35 solid wall faces plus 4 parapets, and no canonical wall is painted from JSON alone.

## Task 3: Implement deterministic axis-aligned wall fragments

**Files:**

- Modify: `projects/c_type_home/scripts/task03a_render_dxf.py`

- [ ] **Step 1: Collect and clip cuts per wall.**

Use all 14 canonical ordinary openings plus all 9 registered windows. For every rectangle that overlaps a wall, clip it to the wall bounds and retain its ID, source type, and clipped rectangle. A window with no `host_wall_id` is still eligible when its opening rectangle overlaps the aligned wall or parapet geometry; when it is already a gap between active wall segments, retain an explicit `active_gap` association backed by glazing coverage and gap-boundary checks.

- [ ] **Step 2: Form the cut union with a coordinate grid.**

For one wall, build sorted x coordinates from the wall edges and every clipped cut’s x edges, and sorted y coordinates from the wall edges and every clipped cut’s y edges. Emit each grid cell whose midpoint is outside every cut. This is the exact axis-aligned rectangle difference `wall - union(cuts)` and avoids compound-path winding behavior.

- [ ] **Step 3: Record area accounting.**

For every wall report:

```text
wall_area_mm2
cut_union_area_mm2
fragment_area_mm2
area_error_mm2
fragment_rects
cut_ids
```

The area error must be zero within integer millimetre arithmetic. Merge adjacent cells only when the merged rectangle remains axis-aligned and preserves the same area; merging is optional and must not change the report identity.

- [ ] **Step 4: Add focused fragment cases before rendering the plan.**

Check a wall with no cut, a wall with one full-width cut, a wall with two overlapping cuts, a wall with a bay-window cut, and a parapet with a glazing cut. Expected: no negative-area fragment, no double-subtracted overlap, and exact area identity in every case.

## Task 4: Apply fixed styles and z-order

**Files:**

- Modify: `projects/c_type_home/scripts/task03a_render_dxf.py`

- [ ] **Step 1: Define separate styles for exterior wall, interior wall, shaft, and parapet.**

Use a darker/heavier exterior poche, a lighter interior/shaft poche, and a lighter/thinner parapet. Keep glazing and opening layer restyling in memory only.

- [ ] **Step 2: Draw fragment fills and outlines as separate artists.**

Assign fixed z-orders: fill `10`, wall outline `20`, parapet `30`. Use the same z-order for every fragment in a given category so insertion order cannot change the result.

- [ ] **Step 3: Draw the filtered DXF and raise all DXF artists to z-order 40 or higher.**

Capture the Matplotlib artist collection before and after the ezdxf frontend call, then set every newly created DXF line, patch, collection, and text artist to a z-order of at least `40`. Keep diagnostic labels at `50`. Ensure hidden Presentation layers/types remain hidden; do not save the mutated in-memory document.

- [ ] **Step 4: Verify the hierarchy numerically.**

The sidecar/report must record the minimum style line widths and z-orders. Expected ordering: fill < outline < parapet < DXF glazing/door/furniture/text. No glazing style may be heavier than the exterior wall outline.

## Task 5: Regenerate formal outputs and baseline-based comparisons

**Files:**

- Modify: `projects/c_type_home/scripts/task03a_render_dxf.py`
- Create/regenerate: files listed in the file map

- [ ] **Step 1: Render the existing RC4 review outputs and the V01/V02 Presentation pairs from their versioned DXFs.**

Keep the current formal names and sidecar provenance fields. Add wall fragment, alignment, area, style, z-order, and view-box fields to the Presentation sidecars.

- [ ] **Step 2: Assemble `rc4_2_wall_display_before_after.png` from frozen baseline PNGs and new after PNGs.**

Use the baseline manifest’s view box and image dimensions to map each fixed CAD zone to pixel crops. The top row must load the copied RC4.1 baseline files; the bottom row must load the newly rendered images. Do not rerender a synthetic “before” image after overwriting the old filenames.

- [ ] **Step 3: Render `rc4_2_wall_readability_check.png/.pdf`.**

Use the V02 Presentation profile and add diagnostic wall IDs only to this check sheet. Keep diagnostic labels out of `rc4_v01_presentation` and `rc4_v02_f1_presentation`.

- [ ] **Step 4: Write `rc4_render_report.json`.**

Include per-version records, baseline manifest reference, view box, wall alignment, fragment areas, cut associations, style parameters, hidden layers/types, exact source DXF SHA, and the literal status `HUMAN VISUAL REVIEW = REQUIRED`.

## Task 6: Add RC4-G14 through RC4-G18

**Files:**

- Modify: `projects/c_type_home/scripts/task03a_gate_check.py`
- Update: `projects/c_type_home/qc/task03a_gates.json` by running the checker

- [ ] **Step 1: Add RC4-G14 wall-face completeness.**

Read `rc4_render_report.json` and require all 39 existing canonical wall records (35 solid wall faces plus 4 parapets) to have active-DXF alignment records, every solid wall and parapet to have fragments, zero area error, and no rejected wall. Report the missing wall ID or area mismatch. Keep human visual review outside the automatic gate result.

- [ ] **Step 2: Add RC4-G15 wall-window hierarchy.**

Require all 9 canonical fenestration IDs to appear in `wall_cut`, `parapet_cut`, or verified `active_gap` associations. For each one, verify its cut or gap is covered by an aligned wall/parapet or bounded by active DXF wall segments and glazing, and that the report does not mark it as an uncut solid overlay. Report the window ID and host wall/parapet or gap boundaries when failing.

- [ ] **Step 3: Add RC4-G16 parapet hierarchy.**

Require exactly the four canonical parapet IDs in `parapet_faces`, none in `wall_faces`, and a style record lighter/thinner than exterior walls. Report any layer or style mismatch.

- [ ] **Step 4: Add RC4-G17 Presentation layer hygiene.**

For both V01 and V02 Presentation sidecars, require the hidden layer/type sets to include DEMO, SURVEY_SUPERSEDED, SURVEY_HATCH, QC, TAG, HATCH, and DIMENSION, and require no corresponding layer/type in `visible_layers`.

- [ ] **Step 5: Add RC4-G18 geometry frozen.**

Compare live SHA-256 values directly to:

```text
V01 = 5210557086ce08d2ca40cb5b14be909ba83608e68b22bcfd151ed73904cf6c00
V02 = 4e9dd3d4faf137d5db06160843b5dfc024cfab9bfcf571db7911dd76ea0b1c1d
```

Also compare canonical hashes and F1 furniture rectangles against the RC4.1 parent snapshot. A SHA mismatch fails before any visual gate is reported.

- [ ] **Step 6: Preserve all existing gate logic and confirm the total increases by five.**

Expected result after the full run: previous 55 gates plus RC4-G14–G18, all automatic gates PASS, and the report still says `HUMAN VISUAL REVIEW = REQUIRED`.

## Task 7: Verify artifacts and complete human visual review

**Files:**

- Read: all generated PNG/PDF/JSON artifacts
- Update only if needed: `projects/c_type_home/qc/rc4_render_report.json`

- [ ] **Step 1: Run the renderer with the project virtualenv Python.**

Run:

```bash
.venv/bin/python \
  projects/c_type_home/scripts/task03a_render_dxf.py
```

Expected: V01/V02 formal PNG/PDF pairs, both new check images, baseline-aware before/after sheet, and render report are written without modifying any DXF.

- [ ] **Step 2: Run the gate checker with the same Python runtime.**

Run:

```bash
.venv/bin/python \
  projects/c_type_home/scripts/task03a_gate_check.py
```

Expected: all previous gates and RC4-G14–G18 pass; the output explicitly retains `HUMAN VISUAL REVIEW = REQUIRED`.

- [ ] **Step 3: Verify immutable CAD and semantic inputs.**

Recompute MEASURED, V01, and V02 SHA-256 values; compare V01/V02 to the exact frozen values and confirm all canonical/F1 snapshots are unchanged. Confirm `git diff --stat` contains no DXF or canonical JSON modifications.

- [ ] **Step 4: Inspect the full-plan renders and all four before/after zones.**

Review the living north window, north balcony, guest bath/bed/study boundary, dining/life-balcony/kitchen, and south bay-window bedrooms. Record the result in the render report as either pending or reviewed; keep the automatic gate separate from this human decision.

## Task 8: Commit the RC4.2 implementation without merging

- [ ] **Step 1: Review the final diff and generated artifact list.**

Confirm no V03 files, no parent overwrite, no canonical regeneration, and no unrelated layout changes.

- [ ] **Step 2: Commit the renderer, gate checker, baseline, render report, new QC outputs, and documentation with one focused commit.**

Use a message such as:

```bash
git add projects/c_type_home/scripts/task03a_render_dxf.py \
  projects/c_type_home/scripts/task03a_gate_check.py \
  projects/c_type_home/qc/rc4_2_baseline \
  projects/c_type_home/qc/rc4_render_report.json \
  projects/c_type_home/qc/rc4_2_wall_display_before_after.png \
  projects/c_type_home/qc/rc4_2_wall_readability_check.png \
  projects/c_type_home/qc/rc4_2_wall_readability_check.pdf \
  projects/c_type_home/qc/rc4_v01_presentation.* \
  projects/c_type_home/qc/rc4_v02_f1_presentation.* \
  projects/c_type_home/qc/task03a_gates.json
git commit -m "feat: improve RC4.2 presentation wall readability"
```

- [ ] **Step 3: Stop after reporting the commit SHA, diff stat, gate results, geometry hashes, formal renders, baseline before/after, and visual review status.**

Do not merge the branch or start V03.
