# S2 Current Design V1 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Convert the latest named FreeCAD guide into a machine-readable, human-reviewable S2 schematic plan without changing formal CAD.

**Architecture:** Read the FCStd as the human guide and preserve its named object labels, map them to semantic furniture/fixture intents, then place normalized real-size footprints against the frozen canonical plan in task coordinates. Generate a standalone JSON inventory/register, a schematic design model, geometry checks, and PNG/PDF review sheets.

**Tech Stack:** FreeCAD headless Python inspection, Python JSON, ezdxf only for source checks, Shapely for 2D collision checks, Matplotlib for PNG/PDF.

---

### Task 1: Ingest the latest FCStd guide

**Files:**
- Read: `projects/c_type_home/cad/freecad_import/世纪欣园FF_freecad_WORKING.FCStd`
- Create: `projects/c_type_home/design/s2_current_design_v1/human_guide_inventory.json`

- [ ] Open FCStd headlessly and collect named Draft 2D objects, native extrusion, auxiliary lines, and text labels.
- [ ] Convert absolute FCStd coordinates to task coordinates using `(x - 1298172, y + 296458)`.
- [ ] Mark `Rectangle033`, `Circle013`, `Line517–519`, and unlabeled text as `UNNAMED_AUXILIARY`; do not infer their meaning.
- [ ] Apply explicit semantic normalization for ambiguous TV wall, 1.2 m bed, and wheelchair ramp labels.

### Task 2: Build the dimension register and schematic model

**Files:**
- Create: `projects/c_type_home/design/s2_current_design_v1/furniture_dimension_register_v01.json`
- Create: `projects/c_type_home/design/s2_current_design_v1/design_model_v01.json`

- [ ] Use the human guide for topology and intent only.
- [ ] Use standard target footprints from the approved A0 library/brief, keeping guide bbox and target bbox separate.
- [ ] Keep kitchen geometry and guest-bath boundary fixed; keep south owner/study and middle guest-room roles as specified for this S2 pass.
- [ ] Record every adjustment and every `TO_VERIFY` item.

### Task 3: Validate schematic geometry

**Files:**
- Create: `projects/c_type_home/design/s2_current_design_v1/s2_collision_circulation_report.json`
- Create: `projects/c_type_home/design/s2_current_design_v1/s2_current_design_v1.py`

- [ ] Check furniture collisions, room containment, door-swing conflicts, circulation throats, bathroom fixture clearances, dining pull-out, and balcony/entry routes.
- [ ] Keep the result as design evidence; do not convert it into formal CAD approval.

### Task 4: Render human-review outputs

**Files:**
- Create: `projects/c_type_home/design/s2_current_design_v1/S2_CURRENT_DESIGN_V1.png`
- Create: `projects/c_type_home/design/s2_current_design_v1/S2_CURRENT_DESIGN_V1.pdf`
- Create: `projects/c_type_home/design/s2_current_design_v1/S2_CURRENT_DESIGN_V1_design_audit.md`

- [ ] Render canonical walls/openings, named target furniture, room labels, circulation overlays, and unresolved markers.
- [ ] Include a legend separating existing structure, target furniture, human guide bbox, and `TO_VERIFY` items.
- [ ] Stop at `DRAFT_HUMAN_REVIEW`; do not update `project_state.json` to human-approved and do not write formal CAD.
