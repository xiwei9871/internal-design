# Decision register

ACTIVE entries block conflicting requests — report, never silently implement.

| ID | Decision | Status |
| --- | --- | --- |
| D01 | Frozen Ground Truth never modified without explicit authorization (R4 blend SHA256 pinned) | **ACTIVE** |
| D02 | Generated artifacts (renders/overlays/proxies/caches) never committed; explicit path staging only, no git add . | **ACTIVE** |
| D03 | Never auto-merge; stop at requested Gate / HUMAN_REVIEW | **ACTIVE** |
| D04 | No deleting/moving existing assets without explicit request | **ACTIVE** |
| D05 | Preview-first rendering; no Cycles before approval; ≤1 auto retry | **ACTIVE** |
| D06 | Manifest-hashed authorities (B0, kitchen freeze, FreeCAD source, room boundaries) re-verified when in scope | **ACTIVE** |
| D07 | Report format: TASK STATUS/BRANCH/COMMIT/PR/FILES/GT/ARTIFACTS/GATES/ISSUES/NEXT | **ACTIVE** |
