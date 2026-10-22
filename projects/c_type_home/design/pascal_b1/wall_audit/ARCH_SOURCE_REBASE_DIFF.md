# ARCH_SOURCE_REBASE_DIFF — registers vs canonical vs Pascal(只读 diff)

事实源:`FINAL_WALL_REGISTER_V01`(sha ccc78186b4b9)+ `FINAL_WINDOW_REGISTER_95ab90e`(sha 73dcee675d5e)
被审计对象:`b1_model.json`(sha 4d1fca081caa)+ `pascal_arch_scene.json`(当前 arch)

## A. REGISTER vs CANONICAL

### A1. 墙体 — ALIGNED ✓
canonical `walls+parapets` 42 段与 register active 42 段 1:1 对应(含 W-BAY-STUDY-* add-back)。
removed_walls 9 段与 register EXISTING_REMOVED 一致。

### A2. 开窗 — 4 处偏差
| id | register | canonical 现状 | 判定 |
|---|---|---|---|
| W-STUDY-NE | opening_rect [13600,10900,15700,11100] 立面线 | rect 改写为凸出正面 [11350–11550],host_wall→W-BAY-STUDY-F | 立面开口线在 canonical 丢失;需在 v2 中同时保留 facade opening + bay box |
| W-LIV-N | bay,proj 900 | bay.jambs/front 仅为元数据;cheek 已是实体墙(W-BAY-JW/JE),**front band 未建墙** | front 需升格 |
| W-SMB-S | bay,proj 700 | jambs/front 仅元数据,**cheeks+front 全无实体墙** | 三段全需升格 |
| W-MB-S | bay,proj 700 | 同上 | 三段全需升格 |

### A3. 门 — ALIGNED ✓
13 条 openings 与 B1_DOOR_SEMANTIC_RESOLUTION v002 一致(含 G-* 三条玻璃门类)。

## B. CANONICAL vs PASCAL

### B1. 墙体
42/42 register 墙有 Pascal 节点且几何非零(rendered spec 完整)。遗留:`W-INT-X13000`⊃`W-NBALC-E-PAR` 嵌套重叠待裁决。

### B2. 飘窗 — 结构性错误
| 问题 | 影响 |
|---|---|
| 每飘窗生成**两个** glazed 元素:立面 window + `BAY_FRONT_GLAZED` 薄墙+全宽窗 | 双重玻璃,立面开口和凸出正面同时亮 |
| LIV-N/SMB-S/MB-S **cheek 侧墙从不发射** | 南向两飘窗 = 两片玻璃夹空气,无凸出盒体感 |
| 全飘窗无 sill/platform blockout | 窗台高度不可见 |
| BAY_FRONT_GLAZED 用 `wall` 类型但本质是玻璃 | 与"实体墙"审计混淆 |

### B3. 门 — emitted 宽度错误
| door | canonical 开口宽 | Pascal width | 判定 |
|---|---|---|---|
| D-SM | 700 | 464 | WRONG(取了墙厚向尺寸) |
| D-MB | 400?rect 12900–13300 = 400 | 434 | 近似,待核 |
| D-BATHM | 600 | 400 | WRONG |
| D-STUDY | 600 | 400 | WRONG |
| D-ENS-OWNER | 700 | 700 | OK |
| G-* / ENT-1 / D-CONN-MB-SMB / OPEN-COR-LIV | — | 正确 | OK |

> 注:converter 对"厚墙带上的门洞"把 host wall 的窄向尺寸当成了门宽。rebuild 时统一用 opening rect 的**沿墙方向**长边。

## C. Phase 2 rebuild 输入(冻结清单)

1. `canonical_arch_v2.json` 内容:
   - 42 active walls(register 原样)+ 9 removed(仅历史,不渲染)
   - 飘窗升格为建筑构件:`BAY-*-CHEEK-L/R` + `BAY-*-FRONT`(实体矮墙或玻璃幕按 register disposition)+ `BAY-*-SILL` platform + facade `opening`(在 host wall 上开洞)
   - 9 openings(register 原样 rect/type/host)
   - 13 doors/openings(resolution 原样)
   - split-level +350mm 平台
2. `pascal-arch-truth-v1`:仅墙/门窗/飘窗盒/错层;新 scene,不在旧 scene 上 patch。
3. 家具、厨房**不进本轮**。

STOP — 等待确认后进入 rebuild。
