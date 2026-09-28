# Residential Design Pipeline v2.0

## Purpose

This workflow governs residential design in c_type_home. It separates measured existing truth, functional design truth, 3D spatial review, human approval and production documentation.

## Non-negotiable principles

1. **Design before documentation.** Formal CAD is a production consumer, not the primary furniture-design medium.
2. **Existing truth and design truth are separate.** Existing geometry comes from measured DXF, canonical existing data, the window register and field measurements. Approved design truth comes only from an approved design contract.
3. **Clearance compliance is not design approval.** Geometry gates do not decide hierarchy, grouping, proportion, sightlines or spatial quality.
4. **One contract, many consumers.** CAD, Blender, FreeCAD, schedules and construction drawings consume one frozen contract.
5. **Review is independent.** Geometry review and spatial/visual review are separate roles.

## Stages

### S0 — EXISTING / MEASURED FREEZE

Inputs: source DWG, measured DXF, canonical data, window register and field measurements. Outputs: existing_geometry_contract.json and existing_geometry_report.md. Preserve TO_VERIFY; never turn an assumption into an existing fact.

### S1 — DESIGN BRIEF

Record household, daily and periodic users, activities, storage, aging-in-place, child use, KEEP items, must-haves, nice-to-haves and forbidden changes. Outputs: design/brief_v01.json and design/brief_v01.md.

### S2 — FUNCTIONAL SPATIAL DESIGN

Design spatial relationships before formal CAD using structured 2D plans, SVG/PNG or simple top views. Every major object has a role, functional group, reason and relationship. At least two genuinely different concepts are required. A human approves the functional plan before S3.

### S3 — 3D BLOCKOUT

Build actual-scale walls, openings, windows, stairs, fixed cabinets, furniture envelopes and fixtures in Blender or FreeCAD. Render top/axon and eye-level route views. Materials are secondary.

### S4 — VISUAL / SPATIAL REVIEW

Run independent geometry review and independent spatial/visual review. Revise the design model after review; image-only edits do not count. A human approves after review.

### S5 — APPROVED DESIGN CONTRACT

Create design/approved_design_vXX.json only after S2, S3 and S4 human gates. Record architecture reference, zones, furniture, fixtures, cabinetry, positions, orientations, dimensions, axes, heights, groups, roles, basis and verification status.

### S6 — MULTI-CONSUMER PRODUCTION

Blender, CAD, FreeCAD, elevations and schedules read the same frozen contract. Production problems return to the contract; they are never silently fixed in one consumer.

### S7 — CONSTRUCTION DOCUMENTATION

Only after design confirmation: plans, demolition/new work, floors, ceilings/electrical, plumbing, elevations, details and schedules. Construction-documentation skills do not create S2 layouts.

## Formal CAD gate

Formal design CAD is allowed only when:

`S2_HUMAN_APPROVAL AND S3_3D_BLOCKOUT AND S4_SPATIAL_REVIEW AND S4_HUMAN_APPROVAL AND S5_DESIGN_CONTRACT_FREEZE`

Otherwise the state is BLOCK/HOLD.
