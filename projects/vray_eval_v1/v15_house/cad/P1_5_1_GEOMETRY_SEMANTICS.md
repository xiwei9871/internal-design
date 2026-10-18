# P1.5.1 — A102/A103 最终几何与施工语义收尾报告
基线: `e0b0d0a` | 产物: `A102_WALL_DIFF_POC_V3.dxf` + `A103_CONSTRUCTION_POC_V7.dxf`（同名覆盖重生成）

## T1 — 构件类型分类与面积纠正

88 个 Blender `PROPOSED_NEW` 对象按工程构件类型分类（名称规则 `classify()`，记录在 `new_construction_v1.json` 每行 `component_type`）：

| component_type | 对象数 | 新增去重并集 mm² | 保留等价并集 mm² | 说明 |
|---|---|---|---|---|
| WALL_PARTITION | 63 | 9,770,289 | 10,449,607 | 新建隔墙/墙体残段 |
| SOFFIT_HEADER | 14 | 7,904,280 | 2,762,122 | 窗头/过梁/吊顶上沿，**不再计入砌墙量** |
| STAIR_STEP | 4 | 3,728,976 | 588,481 | 错层台阶，**不再计入砌墙量** |
| COLUMN_PIER | 8 | 418,936 | 469,025 | 墙垛/门垛 |

- 面积 = 同类 `uncovered_new_geoms` 的 `unary_union`，去重；不再是 21.96m² 的对象相加。
- **新建砌墙面积 = 9.77m²（WALL_PARTITION）+ 0.42m²（COLUMN_PIER）≈ 10.19m²**；上部构件 7.90m²、台阶 3.73m² 独立统计。
- 工程量不含现场损耗；SOFFIT_HEADER 的"新增面积"大部分是剖切线以下的窗头下沿墙，施工归类仍待人工复核（已独立列出）。
- `SPLIT` 26→29、`REPLACES_DEMOLISHED` 3→0：分类边界微调（同阈值，本次按新 NC 计算口径），差异在 CSV 可逐项核对。

## T2 — REMODELED_RETAINED 残余不再静默隐藏

- `REMODELED_RETAINED` 30 个对象的差集残余 **403,842mm²（0.40m²）无覆盖证据**、34,387mm² 有证据。
- 处理：残余逐碎片查询"除自身外全部 Blender 施工几何"覆盖 ≥80% → `covered_by:[对象]` 证据，画在冻结层；**<80% 的 7 个对象残余一律按 component_type 出图**：
  `VIEW_WALL_B11_SITE_BALCONY_WINDOW_HEAD` 150,290（SOFFIT）· `W_wall_md_0046` 110,435 · `W_wall_md_0026` 44,290 · `W_wall_md_0047` 35,140 · BALCONY_WINDOW_L/R_RETURN 30,065/20,050（PIER）· `VIEW_WALL_V4_G_DIN_LIV_RIGHT_PIER` 12,293。
- **QJ9 新增**：Blender 目标建筑几何（EXISTING_RETAINED+PROPOSED_NEW+UNVERIFIED+PENDING 的 parts 并集 = 42.16m²）对 A103 可见墙层并集做双向差集：
  `missing=[]`、`extra=[]` —— **Blender 目标与 A103 可见建筑轮廓几何一致**。
- 保留等价部分不重复出图：A102 整段重画副本→冻结 `A-WALL-RETAIN-EQUIV`；A103 `A-DUP` 改冻结层（此前可见的 27 条重影灰线已隐藏）。

## T3 — 尺寸语义修正

`dims_extra.json` 全部带 `measurement_type`/`src`/`resurvey`，DEVINDIM XDATA 扩为 8 字段（tag,锚A,锚B,轴,值,mtype,ref,resurvey）：

| measurement_type | 数量 | 语义 |
|---|---|---|
| DEMOLITION_SPAN | 5 | 拆改段跨度（原 `demo_len_*` 更名 `demo_span_*`，语义正名） |
| NEW_WALL_LOCATION | 4 | 新隔墙定位：**保留墙近端面→新墙中心线投影**（不再用对象自身 bbox 跨度冒充） |
| STAIR_SPAN | 4 | 台阶构件跨度，独立类别 |
| OPENING_WIDTH | 9 | 门洞净宽（模型注册洞口），全部 SITE_VERIFY |

- 定位示例：`new_loc_1_W_wall_md_0062`=1101.8mm（W_INT_X7900_U 南端→新墙中心线）、`new_loc_2`=3551.8（W_INT_X13000）、`new_loc_3`=251.5（W_INT_X5800）。
- QA：extra dim 的 `mtype` 必须在词表且与 JSON 一致；NEW_WALL_LOCATION 必须有 ref；两图逐字段比对。
- 尺寸合计 12+22=**34**（原 29 中 5 个 demo_len 更名、new_pos 换定位语义、新增 step_span）。

## QA 结果（A102 V3 × A103 V7）

```
QJ1_same_snapshot           true   QJ6_pass                       true
QJ2_demo_set                true   QJ9_target_area_mm2        42158386
QJ2_hold_set                true   QJ9_blender_target_covered    true
QJ3_no_suppress_visible     true   QJ7_sources_fresh             true
QJ4_all_conflicts_shown     true   QJ8_viewport_present          true
QJ5_dims_valid              true   verdict                       PASS
```
破坏性测试 **5/5 检出**；N3（移墙100mm）现在同时击穿 QJ6 与 QJ9。

## 交付文件

- `A102_WALL_DIFF_POC_V3.dxf/.native.png/.pdf`
- `A103_CONSTRUCTION_POC_V7.dxf/.native.png/.pdf`
- `derived/new_construction_v1.json/.csv` — 含 component_type/uncovered/covered_by 逐行
- `derived/dims_extra.json` — 22 条语义标注
- `review_packages/P1_5/` — 叠加图 + 北阳台/次卫/厨房/错层局部 + 异常清单
- 重点局部：`crop3_nbalc.png`（北阳台封窗+HOLD）、`crop2_bath2.png`（次卫）、`crop4_step.png`（错层）

## 未决 HOLD（不变，不随技术验收解除）

1. `W_EXT_N_BAL` 拆除实施权限 — 结构核验/封窗合规未批。
2. 15 处 `UNVERIFIED_STRUCT_OVERLAP` — 拟建骑跨测绘柱位，待结构方判定。
3. 4 处 `PENDING_REVIEW` 设计待裁。
4. 18 处 `CLASSIFICATION_UNVERIFIED`。
5. 专业 CAD 编辑器/物理打印 — NOT_RUN。
6. 现场复尺：NEW_WALL_LOCATION/OPENING_WIDTH/STAIR_SPAN 全部 SITE_VERIFY；台阶踏面进深、封窗框料、门洞高度未自动标注。
7. SOFFIT_HEADER 7.90m² 的施工归类（砌墙/混凝土窗头/吊顶封板）待人工复核——面积已独立统计不混入砌墙量。
