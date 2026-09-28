# Residential Design Pipeline v2.0 Implementation Plan

> **For agentic workers:** Execute this plan inline as a documentation-and-gate task. The owner supplied the complete approved workflow. Do not change design geometry or formal CAD.

**Goal:** Freeze a stage-gated residential design production workflow that requires functional design, 3D spatial review, human approval, and an approved design contract before formal CAD or construction documentation.

**Architecture:** Put normative workflow, machine-readable stage/gate definitions, templates, checklists, provenance lessons, and the current project state under \`projects/c_type_home/workflow/\`. Add a project-local skill that routes residential design work through those gates. A small validator reads \`pipeline_v2.yaml\`, \`gates_v2.yaml\`, and \`project_state.json\`; it computes formal CAD permission and verifies archived experiment labels.

**Tech Stack:** Markdown, YAML, JSON Schema, Python 3 standard library + PyYAML, unittest.

---

### Files and responsibilities

- \`workflow/RESIDENTIAL_DESIGN_PIPELINE_V2.md\`: normative stages S0–S7, principles, ownership, transitions.
- \`workflow/pipeline_v2.yaml\`: machine-readable stage definitions and artifact inputs/outputs.
- \`workflow/gates_v2.yaml\`: named gates and the exact formal CAD allow expression.
- \`workflow/project_state.json\`: C-type current status; formal CAD and construction docs remain HOLD.
- \`workflow/lessons_learned.md\`: D0.1/D0.2/F1R research findings and non-approval status.
- \`workflow/previous_project_forensics.md\`: evidence-backed provenance from A7/A11/A12/v14.
- \`workflow/source_integrity_v2.json\`: before/after hashes for protected current project inputs.
- \`workflow/templates/*\`: brief, concept, decision log, review, human gate, contract schema.
- \`workflow/checklists/*\`: functional plan, blockout, spatial review, pre-CAD freeze.
- \`skills/residential-design-pipeline/SKILL.md\`: project-local operating instructions.
- \`skills/residential-design-pipeline/references/*\`: stage-specific procedures.
- \`workflow/validate_pipeline_state.py\`: evaluate machine-readable state and gates.
- \`workflow/tests/test_pipeline_state.py\`: current HOLD state and prerequisite logic tests.

### Task 1: Write failing state-gate tests

- [ ] Create unittest coverage for current formal-CAD HOLD, required stage statuses, D0/F1R labels, and every prerequisite in the allow expression.
- [ ] Run tests and confirm expected failure because the validator/workflow files do not exist.

### Task 2: Implement machine-readable state and validator

- [ ] Create pipeline and gate YAML plus current state JSON.
- [ ] Implement validator: formal CAD is allowed iff S2 human approval, S3 blockout, S4 spatial review, S4 human approval, and S5 design-contract freeze all equal PASS.
- [ ] Run the focused test suite.

### Task 3: Document prior-project provenance and lessons

- [ ] Record exact file paths, repository commit provenance, SHA256, and verified observations from A7, A11, A12, approved_v14, design_model, A101, cad_common and README.
- [ ] Record D0.1 as infrastructure prototype pass / skill benchmark invalid; D0.2 as valid benchmark execution / design quality not accepted; F1R as research only / not approved.
- [ ] Preserve all experiments; change no experiment outputs.

### Task 4: Create templates, checklists and local skill

- [ ] Write the design brief, concept, design-decision, spatial-review and human-gate templates.
- [ ] Write the approved-design JSON Schema with provenance, dimensions, orientation/front/head axes, functional group, role, basis, approval state and verification state.
- [ ] Write S2/S3/S4/S5 checklists and the local skill with the three mandatory principles.
- [ ] Keep construction-documentation skills confined to S7.

### Task 5: Verify and commit only R1 files

- [ ] Verify required files and state values, exact CAD allow expression, and prior-project source hashes.
- [ ] Verify protected V02/canonical/window/A0/A1/A2 hashes are unchanged.
- [ ] Confirm no V03 was created and no formal CAD changed.
- [ ] Run unittest and \`git diff --check\`.
- [ ] Commit only \`projects/c_type_home/workflow/\`, \`projects/c_type_home/skills/residential-design-pipeline/\`, and this plan.
