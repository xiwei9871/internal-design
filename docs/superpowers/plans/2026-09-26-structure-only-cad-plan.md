# Structure Only CAD Output Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build and verify a furniture-free structure-only DXF derived from the direct 世纪欣园 CAD conversion, with all retained wall geometry source-matched.

**Architecture:** Read `cad/measured_working.dxf` as the direct graphical source, delete only explicit furniture/text overlay entities, serialize a new DXF, and compare retained entity signatures against the source. Render the derived DXF directly with ezdxf for inspection; do not use RC4.2 synthetic wall faces or V02 furniture data.

**Tech Stack:** Python 3.14 project virtualenv, ezdxf, Matplotlib, JSON, SHA-256, unittest.

---

### Task 1: Add source-match regression tests

**Files:**

- Create: `projects/c_type_home/scripts/audit_lounge_entities.py`
- Create: `tests/test_structure_only_cad.py`
- Test target: `projects/c_type_home/scripts/build_structure_only_cad.py`

- [ ] **Step 1: Write failing tests for output contract.**

  Assert the output/report do not exist yet, then specify these behaviors:

  ```python
  def test_source_wall_entities_are_retained_exactly():
      report = json.loads(REPORT.read_text())
      assert report["wall_match"]["missing"] == []
      assert report["wall_match"]["extra"] == []
      assert report["wall_match"]["max_coordinate_delta_mm"] <= 0.01

  def test_no_furniture_or_leisure_overlay_remains():
      report = json.loads(REPORT.read_text())
      assert report["residual_furniture_entities"] == []
      assert report["deleted_overlay_text"]

  def test_green_box_source_wall_checks_pass():
      report = json.loads(REPORT.read_text())
      assert all(item["source_wall_linework"] for item in report["green_box_checks"])
  ```

- [ ] **Step 2: Run the focused test and verify the expected missing-output failure.**

  Run:

  ```bash
  rtk .venv/bin/python -m unittest -v tests/test_structure_only_cad.py
  ```

  Expected: FAIL because the builder and report do not exist.

- [ ] **Step 3: Run the source lounge geometry audit before deletion.**

  ```bash
  rtk .venv/bin/python projects/c_type_home/scripts/audit_lounge_entities.py
  ```

  Confirm the audit reports `30830F`, `308310`, `308311` on `S-楼梯` as the
  fan-shaped lounge/platform candidates, the straight stair handles as retained
  context, and `307F68` as a nested `F-FURN` block. Review
  `qc/lounge_entity_audit.png` before the builder deletes any candidate.

### Task 2: Implement the source-faithful DXF builder

**Files:**

- Create: `projects/c_type_home/scripts/build_structure_only_cad.py`
- Create: `projects/c_type_home/qc/structure_only_cad_report.json`
- Create: `projects/c_type_home/qc/lounge_entity_audit.json`
- Create: `projects/c_type_home/qc/lounge_entity_audit.png`
- Create: `projects/c_type_home/cad/structure_only_source_sync.dxf`

- [ ] **Step 1: Load and freeze the direct source.**

  Read `cad/measured_working.dxf`, assert its SHA-256 is
  `3711c47c1172fbdb13fead356bd5b2285e66925f6aca4a62c49ff118437ba233`, and
  record the source DWG SHA from `cad/cad_version_manifest.json`.

- [ ] **Step 2: Define the deletion predicate.**

  Use the audit-approved exclusions exactly:
  `30830F`, `308310`, `308311` (`S-楼梯` fan-shaped lounge/platform),
  `307F67` (`F-FURN` text), and `307F68` (`S-S.WALL` INSERT with nested
  `F-FURN` block). Do not delete the straight stair handles
  `308341`, `308342`, `308343`, `308345`, or any other wall/window/door/column
  entity.

- [ ] **Step 3: Serialize the derived DXF without synthetic geometry.**

  Clone the source document, delete only the predicate matches, save to
  `cad/structure_only_source_sync.dxf`, and never call canonical wall-face
  drawing or copy V01/V02 design layers.

- [ ] **Step 4: Build exact retained-entity signatures.**

  For each retained wall/column/door/window/stair entity, record handle, layer,
  DXF type, and normalized geometry. Compare output to source by source handle;
  report missing, extra, and coordinate deltas. Require
  `expected retained entities = source entities - explicit lounge exclusions -
  furniture exclusions`, maximum retained wall delta `<= 0.01 mm`, and zero
  unexplained missing/extra handles.

- [ ] **Step 5: Add green-box checks.**

  Check these task-coordinate rectangles against source `S-S.WALL` linework:

  ```python
  GREEN_BOXES = {
      "upper_horizontal": [9735, 6226, 10551, 6566],
      "right_vertical": [11382, 2955, 11643, 3398],
      "life_balcony": [1292, -197, 5426, 2575],
  }
  ```

  Record intersecting source wall handles and require at least one source wall
  linework record in each region.

- [ ] **Step 6: Record standard-window checks.**

  Cross-check `W-KIT-S` as a standard window and record that its source glazing
  entities occupy only `[6100, -200, 7100, 0]`; surrounding source wall
  linework must remain present. Include all nine current registry IDs only as
  evidence; do not synthesize new wall cuts.

### Task 3: Render the derived CAD file directly

**Files:**

- Create: `projects/c_type_home/scripts/render_structure_only_cad.py`
- Create: `projects/c_type_home/qc/structure_only_cad.png`
- Create: `projects/c_type_home/qc/structure_only_cad.pdf`
- Create: `projects/c_type_home/qc/structure_only_cad.render.json`

- [ ] **Step 1: Write a direct ezdxf renderer.**

  Use `RenderContext`, `Frontend`, and `MatplotlibBackend` on the derived DXF;
  set equal aspect and plan extents from source linework. Do not import or call
  `draw_wall_faces()` and do not draw furniture, platform, leisure labels, or
  synthetic wall poche.

- [ ] **Step 2: Record render provenance.**

  Store source/output DXF SHA, renderer SHA, canvas mapping, visible layers,
  hidden/deleted layers, and output PNG/PDF SHA values in the render sidecar.

### Task 4: Verify, document, and commit

**Files:**

- Modify: `docs/superpowers/specs/2026-09-26-structure-only-cad-design.md`
- Modify: `docs/superpowers/plans/2026-09-26-structure-only-cad-plan.md`
- Create: `projects/c_type_home/qc/structure_only_cad_report.json`

- [ ] **Step 1: Run focused and existing tests.**

  Run:

  ```bash
  rtk .venv/bin/python -m unittest -v tests/test_structure_only_cad.py
  rtk .venv/bin/python -m unittest -v tests/test_rc42_presentation.py
  ```

- [ ] **Step 2: Run builder and renderer from the project virtualenv.**

  ```bash
  rtk .venv/bin/python projects/c_type_home/scripts/build_structure_only_cad.py
  rtk .venv/bin/python projects/c_type_home/scripts/render_structure_only_cad.py
  ```

  Expected: report PASS, zero missing/extra retained wall entities, zero
  furniture residues, all green-box checks PASS, and CAD PNG/PDF/DXF outputs.

- [ ] **Step 3: Recompute hashes and inspect the CAD deliverable.**

  ```bash
  rtk shasum -a 256 \
    projects/c_type_home/cad/structure_only_source_sync.dxf \
    projects/c_type_home/qc/structure_only_cad.png \
    projects/c_type_home/qc/structure_only_cad.pdf
  rtk git diff --check
  ```

  Confirm no frozen V01/V02, canonical JSON, or F1 JSON file changed.

- [ ] **Step 4: Commit the structure-only CAD deliverable.**

  ```bash
  git add docs/superpowers/specs/2026-09-26-structure-only-cad-design.md \
    docs/superpowers/plans/2026-09-26-structure-only-cad-plan.md \
    projects/c_type_home/scripts/build_structure_only_cad.py \
    projects/c_type_home/scripts/render_structure_only_cad.py \
    projects/c_type_home/cad/structure_only_source_sync.dxf \
    projects/c_type_home/qc/structure_only_cad_report.json \
    projects/c_type_home/qc/structure_only_cad.render.json \
    projects/c_type_home/qc/structure_only_cad.png \
    projects/c_type_home/qc/structure_only_cad.pdf \
    tests/test_structure_only_cad.py
  git commit -m "feat: add source-matched structure-only CAD output"
  ```

- [ ] **Step 5: Report the commit SHA and exact CAD paths.**

  Do not merge or modify furniture/canonical design data in this task.
