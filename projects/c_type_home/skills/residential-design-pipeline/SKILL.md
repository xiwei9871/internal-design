---
name: residential-design-pipeline
description: Enforce the staged residential design workflow for C-type and future homes.
---

# Residential Design Pipeline v2.0

Never start formal CAD furniture layout before an approved functional design and 3D spatial review exist.

CAD is a production consumer of the approved design contract, not the primary design generator.

Numerical clearance compliance does not constitute design approval.

## Routing

1. Read workflow/project_state.json and workflow/gates_v2.yaml.
2. Existing questions use measured DXF, canonical data, window register and field measurements.
3. New design uses S1 brief, then S2 functional concepts. Do not place production furniture in formal CAD during S2.
4. Obtain S2 human approval before S3 Blender blockout.
5. Run independent geometry and spatial/visual reviews on saved geometry and renders.
6. Obtain S4 human approval, then freeze S5 approved_design_vXX.json.
7. Generate CAD, Blender, FreeCAD and schedules from the same contract hash.
8. Use construction-documentation skills only in S7.

## Stop behavior

If any required gate is HOLD, NOT_STARTED, NOT_APPROVED or NOT_CREATED, report BLOCKED/HOLD and do not generate or modify formal design CAD. Experimental outputs can remain research records but cannot become design truth without the gates.
