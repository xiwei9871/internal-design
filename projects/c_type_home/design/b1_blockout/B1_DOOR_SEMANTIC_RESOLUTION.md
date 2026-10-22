# B1 DOOR SEMANTIC RESOLUTION — V002

Method: canonical opening rect → pierced wall (EXISTING only) + flanking space polygons on all four sides.

## Resolved

| Source ID | Formal ID | Wall pierced | Connects | Evidence | Action |
|---|---|---|---|---|---|
| `D-CLK` | **D-ENS-OWNER** | `W-INT-CLK-N` | 休闲厅 (N) ↔ 次主卫区 (S, former cloakroom) | matches owner-ensuite review history (`R2_2_LOCAL_DETAIL_REVIEW`) | KEPT, renamed, leaf in `04_DOORS` |
| `D-MASTER?` | **D-CONN-MB-SMB** | `W-INT-X11500` | 次主卧 owner bedroom (W) ↔ 主卧 mother bedroom (E) | real opening in canonical EXISTING wall between the two south bedrooms | KEPT, renamed, leaf in `04_DOORS` |

## Removed

| Source ID | Verdict | Why |
|---|---|---|
| `D-LIV-STUDY?` | **REMOVE_FALSE_SEED** | all four flanking samples resolve to the same space `R-LEISURE`; its rect [7900,4564,8300,5664] overlaps the real door `D-SM` [8000,4364,8700,4764] on the same walls — a stale reconstruction seed, not a distinct opening. No leaf, no hole cut. The wall runs solid. |

## Remaining door/opening set (13)

`ENT-1` entry double-leaf · `D-SM` (owner bedroom) · `D-MB` (mother bath) · `D-BATHM` (mother bedroom) · `D-STUDY` (study/NE bedroom) · `D-GBATH` + `D-GBED` (guest bath + guest room off hall) · `D-ENS-OWNER` · `D-CONN-MB-SMB` · `OPEN-COR-LIV` (open cased passage) · `G-GB-BALC` / `G-DIN-LIV` / `G-LIV-NBALC` (glazed, handled in window collection)
