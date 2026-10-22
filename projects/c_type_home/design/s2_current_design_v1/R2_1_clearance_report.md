# R2.1 Clearance Report

Status: `DRAFT_HUMAN_REVIEW`

R2 layout is locked. Values below are schematic review values, not construction certification.

| Metric | Available | Target | Shortfall | Status | Source |
|---|---:|---:|---:|---|---|
| BED_GUEST_1200 side clearance | 15 mm | 600 mm | 585 mm | `CONFLICT` | room boundary minus R2 bed bbox |
| BED_GUEST_1200 end clearance | 1438 mm | 600 mm | 0 mm | `PASS` | room boundary minus R2 bed bbox |
| BED_OWNER side clearance | 233 mm | 600 mm | 367 mm | `CONFLICT` | room boundary minus R2 bed bbox |
| BED_OWNER end clearance | 1113 mm | 600 mm | 0 mm | `PASS` | room boundary minus R2 bed bbox |
| BED_MOTHER side clearance | 174 mm | 600 mm | 426 mm | `CONFLICT` | room boundary minus R2 bed bbox |
| BED_MOTHER end clearance | 1088 mm | 600 mm | 0 mm | `PASS` | room boundary minus R2 bed bbox |
| guest WC front clearance | 1044 mm | 800 mm | 0 mm | `PASS` | R2 WC bbox to locked guest-bath north boundary |
| guest WC side clearance | 121 mm | 600 mm | 479 mm | `CONFLICT` | R2 WC bbox to locked guest-bath side boundary |
| guest vanity operating clearance | 1042 mm | 600 mm | 0 mm | `PASS` | locked guest-bath side clearance proxy |
| 3kg washer operating clearance | — | 600 mm | — | `TO_VERIFY` | no approved anchor; candidate is intentionally unplaced |
| owner ensuite candidate area | 4 mm | 5 mm | 1 mm | `CONFLICT` | existing R-CLOAK candidate polygon |
| study chair pull-back clearance | — | 900 mm | — | `TO_VERIFY` | formal workstation operating zone candidate |
| dining chair pull-back clearance | 40 mm | 900 mm | 860 mm | `CONFLICT` | R2 dining table bbox to dining room boundary |
| mother bath critical operating clearance | — | 900 mm | — | `TO_VERIFY` | aging-in-place fixtures require human/SKU review |
| owner ensuite critical clearance | — | 900 mm | — | `TO_VERIFY` | candidate bathroom boundary not yet confirmed |
| living to north balcony existing door clear width | 850 mm | 850 mm | 0 mm | `PASS` | confirmed existing glass door |

## Conflict handling

Conflicts remain marked and are not solved by rotating or moving locked R2 furniture. Each item requires a human decision or field/SKU verification.

## Door evidence

All canonical openings are drawn in R2.1 review outputs; the door rectangles and schematic swing arcs are visible for human review.
