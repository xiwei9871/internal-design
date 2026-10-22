# S2 CURRENT DESIGN V1 R2 — Review

Status: `DRAFT_HUMAN_REVIEW`

## Policy

This R2 is an incremental normalization from the approved Guide Baseline. Human layout intent is locked. No room reassignment, wall reassignment, automatic rotation, or furniture re-layout is performed.

## Gate results

- Guide fidelity baseline: `PASS`
- Room reassignment: 0
- Nonzero rotations: 0
- Furniture collisions: 2
- Door-swing conflicts: 5
- KEEP kitchen conflicts: 0
- Route warnings: 3
- Normalization proposals not applied because they would violate the locked room boundary: 2
- Operation-space / room containment conflicts: 0

## Anchor policy

Beds, wardrobes, desks, sofas, dining table and wet fixtures keep their guide bbox anchor and axis. Dimension changes use the lower-left or center anchor recorded per object. No object is moved more than the recorded `dx_mm` / `dy_mm`; any conflict remains visible for human review.

## Required human review

- Bed headboard-side interpretation remains `TO_VERIFY` where the guide shape alone does not identify it.
- The guest 3 kg washer has no named FCStd anchor and is not auto-placed.
- Any item with `TO_VERIFY`, `HUMAN_REVIEW_REQUIRED`, or `CONFLICT` must be resolved by review before another revision.
- The guest-room-to-balcony screening route remains below its 900 mm reference target in the schematic check; no furniture was rotated to hide this.

## Outputs

- `S2_CURRENT_DESIGN_V1_R2.FCStd`
- `S2_CURRENT_DESIGN_V1_R2.dxf`
- `S2_CURRENT_DESIGN_V1_R2.png`
- `S2_CURRENT_DESIGN_V1_R2.pdf`
- `S2_R2_DIFF_OVERLAY.png`
- `furniture_dimension_register_v02.json`
- `normalization_change_log_v01.json`

Blender and formal CAD remain HOLD.
