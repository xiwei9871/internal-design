# D0.2 Real-Agent Residential CAD Skill Benchmark

STATUS = HUMAN_REVIEW

D0.1 is retained as INFRASTRUCTURE PROTOTYPE PASS / SKILL BENCHMARK INVALID. D0.2 uses independent agent sessions and actual CAD command logs.

## Source locks

- Skills-Architects commit: 30a0845dddcaebd765fc396059573d02e99c5b63
- asset-management-interior commit: 478d5ae32806e5a95dfcbeb70ba5a68126c22e9e
- ReRoom: arXiv:2609.03596 Appendix S6
- clean base SHA256: 17c5d07fd5afec2a6b3751b89727f4e1329b9b0a2fccd5b221aad900a6954984
- V02 SHA256: 4e9dd3d4faf137d5db06160843b5dfc024cfab9bfcf571db7911dd76ea0b1c1d

## Blind outputs

| option | final DXF SHA256 | iteration count |
|---|---|---:|
| A | cb4c8033c226b324f949090a04c674a57428518db6558f0e0a9a86d044586f21 | 2 |
| B | 08c314d249758295540c832deac519dc87dabf183cee380d549f4979b526cd33 | 2 |
| C | 03357c87d323d291df5403d8aca933f06a328a4cee54f0da480136d68b2eeadd | 2 |
| D | 86ca60e3b01ac50f4d388578a7877bc1e47135d9a48edb2fd21e90555153f4be | 2 |

## Gates

- 17/17 gates PASS.
- r01 and r02 evidence is retained under each private session directory.
- r02 edits are timestamped after r01 render, geometry report and written visual review.
- No automatic winner or design-quality score is produced.

## Tests

- unittest: 6 tests, all PASS.

## Human review package

- blind_review/A.png through D.png
- blind_review/A_clearance.png through D_clearance.png
- blind_review/comparison_sheet.png
- blind_review/human_review_form.md
- blind_review/arm_mapping.secret.json is deliberately separate from this report.

## Stop condition

Do not start V03 and do not write any formal CAD until human review is complete.
