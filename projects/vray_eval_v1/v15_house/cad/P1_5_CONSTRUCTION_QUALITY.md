# P1.5 — A102/A103 施工图质量专项报告
基线: `e0db4ad` | 分支: `v15-cad-pipeline-2026-10-17` | 产物: `A102_WALL_DIFF_POC_V3.dxf` + `A103_CONSTRUCTION_POC_V7.dxf`

## 任务一 — "新建墙"语义纠正（最高优先级）

### 问题
89 个 Blender `PROPOSED_NEW` 对象此前全部按新建墙出图；三源交叉显示其中 28 个与现状保留墙高度重叠（属 Blender 重建副本）、30 个部分重叠、仅 29 个真正不重叠、2 个压在拟拆墙上。

### 方法（compute_new_construction.py）
- 现状保留墙集合：registry 中 `RETAINED`/`RETAINED_STRUCT`/`DESIGN_APPROVED_DEMO`/`DEMOLITION_HOLD`/`PENDING_REVIEW` 的全部测绘 part 多边形（union）。
- 对每个 `PROPOSED_NEW` Blender 对象做 2D 差集：`new_geom = blender_part − existing_union`，`retained_geom = blender_part ∩ existing_union`，并单独统计与 `demolished_parts` 的交集。
- 输出四级角色 + 分段几何（无静默删墙；碎片写入 `new_geoms`/`retained_geoms` 供审图）。

### 结果（derived/new_construction_v1.json + new_construction_v1.csv）

| 角色 | 数量 | 含义 |
|---|---|---|
| `NEW` (ACTUAL_NEW_CONSTRUCTION) | 30 | 与现状墙基本不重叠，真实新增 |
| `RETAINED_MODEL_EQUIV` | 30 | Blender 对象 ≈ 现状保留墙重画副本；A102 落冻结层 `A-WALL-RETAIN-EQUIV` 留痕不重复绘制，A103 `SUPPRESS_DUPLICATE` |
| `SPLIT_PARTIAL_NEW` | 26 | 部分重叠，差集段入 `new_geoms` |
| `NEW_REPLACES_DEMO` | 3 | 落在拟拆区上的替换墙 |
| 合计 | 89 | 无静默删除 |

- 实际新增墙面积: **21,960,476 mm²**；保留等价面积: **15,414,567 mm²**。
- `SPLIT` 对象的保留等价部分画到 `A-STRUCT-UNDERLAY`（浅灰，表示"此处现状墙保留"），真实新增段仍画 `A-DESIGN` 蓝；**既不再整段涂蓝，也不再丢几何**。
- 每项 `area_before`/`area_new`/`area_retained` 逐行核算在 CSV；对比图见 review pack `overlay_a102a103.png`（灰=现状、红=拟拆、蓝=实际新建段）。

### 语义不变式（保持）
`design_intent`/`structural_verification`/`construction_authorization` 仍三分；`W_EXT_N_BAL` 维持 `DEMOLITION_HOLD`；15 处 `UNVERIFIED_STRUCT_OVERLAP` 照旧待核实。

## 任务二 — A103 清洁化

| 项 | 处理 |
|---|---|
| 图层色彩 | A-WALL 黑(7)、A-DESIGN 蓝(5)=新建、A-DEMO 红(1)、A-CONFLICT 品红(6)、A-REVIEW 橙(30)、家具/洁具灰(8)、标注绿(3) — 不再全图红 |
| 线宽 | A-WALL 0.50 / A-DESIGN 0.30 / A-CONFLICT 0.40 / A-REVIEW 0.25 / 家具 0.13 |
| 重复/渲染专用线 | `A-DUP` `A-UNCERTAIN` `A-SOURCE-REF` `A-ROOM` 层 flag=1 冻结隐藏；`A-DIMS-LEGACY` 冻结 |
| 拆分残墙 | SPLIT 保留等价段 → 浅灰 `A-STRUCT-UNDERLAY` |
| 对象身份 | `DEVINSRC` XDATA 保留在图元上，图面不堆对象 ID |

## 任务三 — 尺寸（12 → 29）

新增 17 个由模型几何计算的标注（`build_dims_extra.py` → `derived/dims_extra.json`，统一 `DEVINDIM=[tag,锚A,锚B,轴,值mm]`）：
- 拆改段长度 ×5：`W_EXT_N_LV` 5200 / `W_EXT_N_BAL` 5100(HOLD)/`W_BALC_N` 2500/`W_INT_X5800` 2000/`W_INT_X7900_U` 2800
- 新建隔墙定位：`new_pos_W_wall_md_0062`=5140（新墙中心到南侧内墙净距）等
- 门洞净宽：M0800（次卫/客卫门）
- QJ5 计数断言已修正为 `len(GEO.dims)+len(dims_extra)=29` 两图一致。

未纳入自动标注的项（现场未确认，禁止猜测）：台阶各级踏面进深、封窗框料定位、门洞高度 — 列入异常清单"待复尺"。

## 任务四 — 制图与打印

| 验证 | 结果 |
|---|---|
| VIEWPORT 参数（API 读取） | 两图 Layout1：780×520mm 视口，view_height=26000 → **精确 1:50**，同中心 (8250,7000) |
| 原生 DXF→PDF | `render_dxf_native.py` 经 ezdxf RenderContext 直读模型空间，冻结层正确不渲染 |
| 专业 CAD 编辑器打开/打印预览 | **NOT_RUN**（本机无 AutoCAD/QCAD；FreeCAD importDXF 可开但报 VIEWPORT 等非支持特性） |
| A1 版面 | 图纸占视口高约 56%，未强行放大——可读性优先，图幅留白符合"不强求填满" |

## 任务五 — 审图包 `review_packages/P1_5/`

- `A102_WALL_DIFF_POC_V3.native.png/.pdf` — 修正后拆改图
- `A103_CONSTRUCTION_POC_V7.native.png/.pdf` — 清洁化最终平面
- `overlay_a102a103.png` — 同坐标叠加（灰现状/红拟拆/蓝实际新建段）
- `crop1_kitchen.png` `crop2_bath2.png` `crop3_nbalc.png` `crop4_step.png`
- `anomaly_list.png` — 一页异常/待核实清单

## 联合 QA（A102 V3 × A103 V7）

```
QJ1_same_snapshot        true   QJ5_dims_valid          true (29 dims, DEVINDIM 全字段)
QJ2_demo_set             true   QJ6_pass                true (polygon 对称差)
QJ2_hold_set             true   QJ7_sources_fresh       true
QJ3_no_suppress_visible  true   QJ8_viewport_present    true
QJ4_all_conflicts_shown  true   verdict                 PASS
```
破坏性测试沿用 P1.4.3 五项（删XDATA/改尺寸/移墙/删冲突/HOLD解禁）— 测试用例不变，仍全部检出。

## 未决 HOLD（独立列出，不随技术 PASS 消除）

1. `W_EXT_N_BAL` 拆除实施权限 — 结构/封窗合规未批。
2. 15 处 `UNVERIFIED_STRUCT_OVERLAP` — 拟建骑跨测绘 HATCH 柱位，待结构方判贴建/替换。
3. 4 处 `PENDING_REVIEW`（CLK/衣帽间等设计待裁）。
4. 18 处 `CLASSIFICATION_UNVERIFIED` — 映射不到开发商黑白墙语义。
5. 专业 CAD 编辑器与物理打印验证 — NOT_RUN。
6. 现场复尺：台阶踏面、封窗定位、门洞高度。

## 文件清单（本次新增/变更）

- `compute_new_construction.py`、`derived/new_construction_v1.json`、`derived/new_construction_v1.csv`
- `build_dims_extra.py`、`derived/dims_extra.json`
- `build_wall_registry.py`（施工语义角色写入）
- `make_a102_poc_v2.py`（extra dims + 图层色阶）、`make_a103_poc_v7.py`（role→layer 含 SPLIT/STRUCT-UNDERLAY + extra dims）
- `joint_acceptance_v2.py`（QJ5 计数修正）
- `render_dxf_native.py`、`build_p15_review.py`
- `A102_WALL_DIFF_POC_V3.dxf`、`A103_CONSTRUCTION_POC_V7.dxf`、对应 `.native.png/.pdf`
- `review_packages/P1_5/`（6 图）
