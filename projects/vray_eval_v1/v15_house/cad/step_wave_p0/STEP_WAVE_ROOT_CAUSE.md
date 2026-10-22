# P0_STEP_WAVE_AUTHORITY_BREAK — 根因报告

日期: 2026-10-19 | 状态: CAD 侧已修复并回归通过; Blender 侧根因已定位, 需业主授权改 blend
范围: 仅错层/波浪楼梯/休闲厅弧线 (窗口 x5200–9200, y4300–8600mm), 不扩散

## 一句话结论

**主根因 = `CAD_GENERATOR_LOGIC_ERROR`**（可复现、已修复、QA 回归 PASS）。
第二根因 = `OLD_OBJECT_NOT_REMOVED`（Blender 底图大弧是 `FLOOR_LOWER` 网格边界沿用的旧休闲平台轮廓——冻结 blend 内容问题，需业主授权才能改，非渲染管线 bug）。

## A — Blender 权威源核查（必查项A）

| 项 | 值 |
|---|---|
| blend 绝对路径 | `/Users/xiwei/interior_design/projects/vray_eval_v1/v15_house/V15_WORK.blend` |
| SHA256 | `feaeed380c12e99c…`（与审图包登记 `feaeed380c` 一致，**未变**） |
| scene | `Scene` |
| view_layer | `OVERVIEW_CEILING_HIDDEN` |
| 渲染引擎 | 脚本强制 `BLENDER_WORKBENCH`（文件内原为 CYCLES，未落盘改动） |
| 总对象 | 3510；错层窗内渲染对象 200+ |

**渲染到底用没用 V15_WORK.blend：用了。** 本次 `step_wave_evidence_01_blender.png` 为全新直渲（非缓存），与旧审图底图弧线一致 → 排除 `WRONG_BLEND_SOURCE` / `STALE_RENDER_CACHE`。

**错层区可见/隐藏对象（audit_report.json 实测）：**

| 对象 | z(m) | hide_render | 结论 |
|---|---|---|---|
| STEP_0 / STEP_1 / STEP_2 | 0–0.45 | False | 可见，波浪楼梯 3 踏 |
| WAVE_STEP_3_ARRIVAL | 0–0.45 | **True** | 隐藏（+450 到达平台，不渲） |
| FASCIA_PLATFORM_CURVE | 0–0.45 | **True** | 隐藏（旧休闲厅曲线对象） |
| FASCIA_CEILING_CURVE | 2.8–3.25 | **True** | 隐藏 |
| D107_V3_PLATFORM_BASE_CLOSURE | 0.4–0.45 | **True** | 隐藏 |
| FLOOR_LOWER | -0.1–0 | False | **可见——弧线来源** |
| R4_UPPER_FLOOR_…_THRESHOLD | 0–0.45 | False | 可见（上层地坪） |
| WAVE_HANDRAIL_* / 扶手构件 | 0–1.35 | False | 可见 |

→ `HIDE_RENDER_STATE_ERROR` 排除：所有具名旧对象 hide_render=True 且 vis_vl=False，**没有误入渲染**。

**底图大弧是谁：** 对 FLOOR_LOWER / R4_UPPER_FLOOR / FASCIA_PLATFORM_CURVE 顶面顶点逐 500mm 采样西缘：

| y(mm) | FLOOR_LOWER | FASCIA_PLATFORM_CURVE(隐藏) | STEP_0 西缘 |
|---|---|---|---|
| 5000 | 5700 | 5700 | 5660 |
| 5500 | 5705 | 5700 | 5723 |
| 6000 | **5712** | **5712** | 5952 |
| 6500 | 6051 | 5957 | 6350 |
| 7000 | — | — | 6708 |

FLOOR_LOWER 西缘与隐藏 FASCIA 曲线在 y5000–6000 **逐点重合**——地坪板边界沿用旧休闲平台弧线；它比 STEP_0 权威西缘西偏 **~240–300mm**（y6000 处 5712 vs 5952）。叠加图 03 中底图弧与 CAD 第一波 w0 的偏移与此数值吻合。
另测得 R4_UPPER_FLOOR 边缘弧 = 到达平台东缘 w4 同线（6710→8050）——证明 w4 与 +450 上层地坪同层相接，CAD 中本就不该画成台阶线。

**结论：底图弧线 = 当前可见网格 `FLOOR_LOWER` 的边界，形状是旧平台轮廓的残留** → `OLD_OBJECT_NOT_REMOVED`。具名旧对象已隐藏，但同一轮廓以地坪网格边形式存活。修复须在 `V15_WORK.blend` 中把 FLOOR_LOWER 该区边界重切至波浪楼梯西缘（或业主确认的 fascia 方案）——**冻结权威文件，需业主授权，本任务未改动**。

## B — CAD 生成源核查（必查项B）

错层窗实体全清单：`step_wave_entity_map.csv`（141 条，含 handle/图层/XDATA/语义）。

**多余的第 4 条波线是谁生成的：**
`draw_stair()`（make_a102_poc_v3.py / make_a103_poc_v7.py）把 `union(STEP_0∪1∪2∪WAVE_STEP_3_ARRIVAL)` 的**闭合外轮廓**整体画成一条 LWPOLYLINE。该轮廓含到达平台东缘 w4——一条与 3 条踢面同族同向的波线 → 视觉上=第 4 级。w4 实为 +450 平台与同层 R4 上层地坪的相接边（无高差），按工程表达**不应画线**。

不是旧对象、不是缓存、不是 XDATA 错配：`STAIR_GROUP` 实体 XDATA 完整（STEP_0/1/2 + merged_arrival），问题在多边形构造逻辑 → `CAD_GENERATOR_LOGIC_ERROR`。

## 修复（已从真实源重生成）

| 实体 | 图层 | 表达 |
|---|---|---|
| 闭合足迹（含 w4） | **A-STAIR-AREA（冻结）** | 仅面积/语义载体，不打印 |
| 开放轮廓 = 并集边界 − w4 | A-STAIR / A-STAIR-NEW | **3 条波线**（w0 西缘 + w1/w2 踢面） |
| STAIR_RISER_L2 / L3 | A-STAIR / A-STAIR-NEW | 不变 |

- 新 XDATA 标记：`east_edge_open:meets_floor_450`、`area_only:frozen`
- `joint_acceptance_v2.py`：QJ9 将 A-STAIR-AREA（冻结面积层）计入可见并集——否则整段台阶误报 missing
- QA 结果：**PASS**（QJ9 missing 2751mm² 均为 ≤647mm² 既有边界碎屑，STAIR_STEP 类 missing=0，extra=0；QJ10 台阶语义=true）
- A102 台阶层实体：F1(冻结足迹) + F2(开放轮廓) + F3/172(踢面线)；A103：217/218/219/298 同构

## C — 单一真值证据（同窗口 x5200–9200, y4300–8600）

| 文件 | 内容 |
|---|---|
| `step_wave_evidence_01_blender.png` | 新渲 Blender 俯视（Workbench, 错层窗直出） |
| `step_wave_evidence_02_cad.png` | 修复后 A102/A103 实体图：可见 3 波 + 虚线冻结足迹 |
| `step_wave_evidence_03_overlay.png` | 底图+CAD 叠加：CAD 3 波；底图弧 = FLOOR_LOWER 旧轮廓（见上表） |
| `step_wave_evidence_04_objid.png` | 对象ID标注图（handle + DEVINSRC） |
| `step_wave_entity_map.csv` | 141 条实体映射 |
| `audit_report.json` | Blender 权威源核查原始数据 |

## D — 为什么"发现问题又反复犯"

1. **修的都是"多余实体"，没修"多边形构造逻辑"**：历次修复删重复边、冻结 legacy 曲线、合并 ARRIVAL——但闭合足迹本身始终被当作合法轮廓整绘，w4 随之每轮再生。
2. **语义规则没进代码**：「同层相接边不是踢面线」从未编码——生成器只知道"并集边界=轮廓"，不知道"轮廓的哪一段不许画"。
3. **审图粒度不对**：此前审图看整图叠加，4 条波线混在墙线里不显眼；无实体级窗口审计。
4. **Blender 侧误诊**：旧 FASCIA 对象确认隐藏后即口头宣布"俯视已一致"——但弧线本体是 `FLOOR_LOWER` 的边界，对象级检查（谁隐藏）代替不了像素/边级检查（渲出来的边属于谁）。

## 待业主决策（阻断项）

- `FLOOR_LOWER` 错层区西缘是否按波浪楼梯重切（改 `V15_WORK.blend`，需授权）。在授权前，底图弧线为当前权威文件的真实内容，CAD 三波线已与其区分表达。
- HUMAN_CAD_REVIEW_V01 维持 **FAIL / NOT APPROVED**：台阶区修复待业主看证据图后再定。

## 复现命令

```bash
blender -b <abs>/V15_WORK.blend -P cad/step_wave_p0_audit.py -- <abs>/cad/step_wave_p0
python make_a102_poc_v3.py && python make_a103_poc_v7.py
python joint_acceptance_v2.py    # → verdict PASS
python make_step_wave_p0_evidence.py
```
