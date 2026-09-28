# D0.1 Residential CAD Design Skill Benchmark Implementation Plan

> Approved design: execute the supplied D0.1 specification inline and stop at HUMAN_REVIEW.

**Goal:** Build an isolated, reproducible A/B/C/D CAD-first benchmark for CTRL, Skills-Architects, asset-management-interior, and ReRoom public-zone design methods without modifying formal project CAD.

**Architecture:** A deterministic runner creates a clean base DXF from V02, imports the frozen A0.4 block library, executes four method-specific arm layout strategies with two review iterations and a final CAD artifact, then renders and measures each artifact directly from DXF. Source pins, input hashes, method logs, geometry metrics, blind outputs, and gate results are stored under projects/c_type_home/experiments/design_skill_benchmark_v01/.

**Tech Stack:** Python 3, ezdxf, matplotlib, Pillow, Git, local A0.4 DXF block library.

---

### Task 1: Freeze source and input provenance

**Files:** sources/manifest.json; inputs/input_manifest.json; base/public_zone_clean_base.dxf

- Pin Skills-Architects, arch-skills, and ReRoom paper/release metadata.
- Record exact files/read sections and adopted/excluded principles.
- Hash project brief, A0/A1/A2 inputs, canonical data, window register, and V02.
- Copy V02 to the clean base and remove only old movable public furniture inserts/entities.

### Task 2: Implement CAD-first benchmark runner

**Files:** scripts/run_benchmark.py; scripts/verify_benchmark.py

- Import actual A0.4 blocks into each arm DXF.
- Build method-specific CTRL/ARCH/STUDIO/REROOM layouts with explicit method logs.
- Save trial_r01.dxf, trial_r02.dxf, trial_final.dxf and render each from the saved DXF.
- Measure transformed block bboxes, route clearances, wall/opening preservation, and diff against the clean base.
- Emit geometry_metrics.json, cad_diff.json, and design_log.md per arm.

### Task 3: Produce blind review package

**Files:** blind_review/A.png, B.png, C.png, D.png; blind_review/A_clearance.png, B_clearance.png, C_clearance.png, D_clearance.png; blind_review/comparison_sheet.png; blind_review/human_review_form.md; blind_review/arm_mapping.json; reports/gates.json

- Render unlabeled blind images and a same-scale comparison sheet.
- Keep arm mapping separate from blind images.
- Record G0-G8, iteration count, runtime, tool calls, manual interventions, and violations.
- Mark unavailable data UNKNOWN/NOT MEASURED.

### Task 4: Verify and freeze for human review

**Files:** tests/test_design_skill_benchmark.py

- Run the benchmark verifier and test suite.
- Confirm formal V02/V03/canonical files are unchanged by SHA.
- Confirm all four final DXFs are independent of old F1R outputs.
- Commit the benchmark artifacts and report STATUS = HUMAN_REVIEW; do not start V03 or write formal CAD.
