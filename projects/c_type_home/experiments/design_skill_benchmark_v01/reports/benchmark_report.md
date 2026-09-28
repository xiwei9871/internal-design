# D0.1 Residential CAD Design Skill Benchmark

STATUS = HUMAN_REVIEW

## Scope

This benchmark compares four method arms on the same clean public-zone CAD base. It stops before V03 and writes no formal CAD.

## Pinned sources

- Skills-Architects: 30a0845dddcaebd765fc396059573d02e99c5b63
  - adopted: room/program reading, spatial hierarchy, functional zoning, circulation, residential typology, accessibility, concept organization
  - excluded: jurisdiction-specific code claims, structural/MEP calculators, non-residential content not needed for this home
  - files with READ status: 6
- asset-management-interior: 478d5ae32806e5a95dfcbeb70ba5a68126c22e9e
  - adopted: benchmark -> concept -> plan, one dominant spatial device, red-team review, CAD revision
  - excluded: financial-office program content, office asset procurement and budget assumptions
  - files with READ status: 7
- ReRoom: arXiv:2609.03596
  - adopted: Functional Grouping, Anchor Furniture Selection, Geometry-Guided Refinement, Render -> Review -> Revise
  - excluded: claim of a public code implementation, unavailable implementation details beyond the paper and Appendix S6
  - files with READ status: 1
  - paper_sha256: f114affd5240b7634e88a31b2d6e3d881a6b3883bbd5c2e20fde93d9743022f7

## Common CAD inputs

- V02 source SHA256: 4e9dd3d4faf137d5db06160843b5dfc024cfab9bfcf571db7911dd76ea0b1c1d
- clean base SHA256: 0bdc0c5cc8b716122af39d48547f8031dde0fd607dd03c8903e1702121381368
- canonical SHA256: e83c1d69e6b5da74cb7481536f056dc5b9ccf0f4bd643995c10f4bcbc78b3444
- A0.4 compiled block library SHA256: a10f61f253c2340e8ac070f14b51242f7b9d56615fb98aee5a5458db7d618a9e
- common input set: 088f6875b55f49982d2e48d6da84a310452929d4c54b2471063c40f530ebcca3

## Arm results

| arm | blind label | final DXF SHA256 | iterations | geometry violations r01/r02/final |
|---|---|---|---:|---|
| CTRL | C | 4dcccfb8e48e78e4999570b7ee7e26c140979f30cece5f6b3494e5ff51dfefc3 | 2 | 2/1/1 |
| ARCH | A | 4c1fdf7254e8f697fccc038c67aef60755192bd0b93bac17a01d5c70ef3ae40f | 2 | 1/1/1 |
| STUDIO | D | d38c6fdf5fd9d00be81535ce683ffb10204d602d98654c1fd886cdc9d3be1da1 | 2 | 1/1/1 |
| REROOM | B | aae168901fdfddc87f1663ed3465bd2266598f816d56da3f89d6e9c9b3734c48 | 2 | 2/1/1 |

## Gates

- G0_SOURCE_AUDIT: PASS
- G1_BASE_CAD: PASS
- G2_ISOLATION: PASS
- G3_CAD_FIRST: PASS
- G4_ACTUAL_BLOCKS: PASS
- G5_ITERATIVE_REVIEW: PASS
- G6_SAME_INPUTS: PASS
- G7_BLIND_OUTPUT: PASS
- G8_FORMAL_CAD_SAFETY: PASS

## Tests

- unittest: 4 tests, all PASS.
- verifier: 37 checks, all PASS.

## Review files

- Blind plans: blind_review/A.png through D.png
- Clearance overlays: blind_review/A_clearance.png through D_clearance.png
- Same-scale sheet: blind_review/comparison_sheet.png
- Human form: blind_review/human_review_form.md
- Mapping: blind_review/arm_mapping.json

## Stop condition

Do not start V03, do not modify V02/V03/canonical CAD, and do not treat any arm as selected until human review is complete.
