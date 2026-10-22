# PASCAL B1 FULL — HUMAN REVIEW PACK

**Status**: `PASCAL_B1_FULL = DRAFT_HUMAN_REVIEW` (unchanged; B2 = HOLD,
formal_cad_allowed = false, nothing committed)

**Scene**: `pascal-b1-full-v1` · checkpoint v4 · 141 nodes
**Editor**: http://pascal.localhost:57071/scene/pascal-b1-full-v1
(select room/object → metadata panel shows canonical_id, review_status,
actual_project_size_m; measure tool + 2D/3D + undo all available)

## Files for this review

| file | content |
|---|---|
| `PASCAL_B1_ADVISORY_AUDIT.md` | 47 advisories classified A–E; **10 UNREVIEWED** listed individually |
| `PASCAL_REVIEW_D_SM.png` | D-SM close-up: canonical 700 vs pascal 464, −236mm clip |
| `PASCAL_REVIEW_D_MB.png` | D-MB close-up: canonical 500 vs pascal 434, −66mm clip |
| `PASCAL_REVIEW_LIMITATIONS.png` | plan with L-02/L-04/L-05 hotspots marked |
| `PASCAL_REVIEW_ZONE_MAP.png` | room/zone labels map (clicking equivalent in editor = select zone) |
| `PASCAL_B1_FIDELITY.md` | numbers vs MASTER_V2 |
| `PASCAL_B1_REPRESENTATION_LIMITATIONS.md` | L-01..L-08 |
| `PASCAL_B1_FURNITURE_FIT.md` | footprint screen |
| `PASCAL_B1_VS_BLENDER_V003.md` | cross-check vs frozen V003 |
| `verify_scene_v3.json` `collisions_raw.json` `fidelity_raw.json` `furniture_fit_raw.json` | raw evidence |

## What needs your eyes (in priority order)

1. **The 10 UNREVIEWED advisories** — audit §E: the study/bedroom cluster
   (书柜/矮书柜/打印机/NAS), entry 鞋柜 vs ENT-1, G-GB-BALC vs 次卧凳子+洗烘叠放,
   D-BATHM vs 主卫台盆, D-CONN-MB-SMB vs 次主卧衣柜.
2. **D-SM** (−236mm clip) and **D-MB** (−66mm clip) — see close-up PNGs;
   decide whether source rect or wall gap is the truth.
3. **L-05 synthetic hosts** — 4 bay fronts + G-DIN-LIV partition: confirm the
   plan position is right even though the representation is approximate.
4. **Room-by-room** — walk the editor scene room by room (zone map as index).

## Standing answers are intentionally NOT given

客厅沙发组合尺度 / 1600×800 餐桌 / 2200×800 书房工作台 / 客房床+500浅柜 /
两个主卧尺度 / 三卫生间实感 / 3kg 壁挂机位 / 北阳台洗烘+冰柜 /
错层台阶坡道 / 飘窗玻璃门关系 — these are your calls in the editor.

## Authority boundaries kept

- catalog = visual placeholder only; `actual_project_size_m` = truth
- `pascal_mcp_rpc.py` = DEBUG/RECOVERY tool only; normal ops return to native
  MCP after Devin session restart (`mcp__pascal__*` already allow-listed)
- Pascal approximations must never be written back into MASTER_V2 / B2 CAD
  as architectural facts

Gate: `PASCAL_B1_FULL = DRAFT_HUMAN_REVIEW` — awaiting your adjudication on the
10 unreviewed items + L-02 doors.
