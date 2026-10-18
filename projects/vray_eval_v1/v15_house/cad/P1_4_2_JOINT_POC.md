# P1.4.2 — 结构提取收尾 + A102/A103 联合 POC

**前审**：`fca2ab6` 通过，遗留两项（HATCH 孔洞未真扣、`S-S.WALL` ≠ 开发商黑白墙字段）
**本提交**：四阶段全部完成
**联合 QA**：`qa_joint.json` = **PASS**（QJ1–QJ7 全过）
**回归测试**：`p14_tests.py` = **13/13 PASS**

---

## 一、技术修复（第一阶段）

| 项 | 实现 | 验证 |
|---|---|---|
| HATCH 孔洞真布尔 | 奇偶深度判定后，内环作为 `Polygon.interiors` 从外环**布尔扣除**（不再仅靠深度选择跳过）；修复后 `HOLES_SUBTRACTED` 记入 anomalies | T9a/T9b/T10 |
| EdgePath 连续性 | 逐边验证链连续（相邻边端点距 ≤1mm）+ 首尾闭合才成环；不连续/非线性边 → `OPEN_EDGEPATH`/`NONLINEAR_EDGE` 异常，各边仍进线网 | T11 |
| 真实 6×HATCH/16 路径 | 核查无嵌套孔洞、无不连续——现有提取对真实文件无行为变化 | 脚本核查 |
| 测试可移植 | `p14_tests.py` 真实文件路径改为 `Path(__file__).parents` 解析 | T12 |
| 语义隔离 | `semantic_limits` 明记：结构层覆盖率 ≠ 拆改权限；`S-S.WALL` 属测绘语义 | registry meta |

## 二、统一墙体状态台账（第二阶段）

`derived/wall_state_registry.json` + `.csv` — **139 条**，A102/A103 共用同一数据源（同一 `geometry_v05` 快照 SHA 记录于 meta）。

| A102 角色 | 数量 | 含义 |
|---|---|---|
| RETAINED | 36 | 现状保留墙 |
| RETAINED_STRUCT | 5 | 保留墙且结构覆盖>60% |
| DEMOLISHED_CONFIRMED | 4 | D02 已批拆（X5800/X7900_U/BALC_N/N_LV） |
| **DEMOLITION_HOLD** | **1** | **`W_EXT_N_BAL` — 0% 覆盖但黑白语义未核实，预防性 HOLD** |
| PENDING_REVIEW | 4 | CLK×3 + 存疑残段 |
| NEW | 89 | 拟建 |

**结构证据分级**：`HATCH_FILL`（剪力墙填充，最强）29 条 / `BOUNDARY_RING` 32 条 / `CLASSIFICATION_UNVERIFIED` 18 条（含全部外墙未被覆盖者 + CLK 部分）/ `NO_STRUCT_OVERLAP` 60 条。

**16 处拟建重叠候选分类**：`STRUCT_HATCH_CONFLICT` ×15（骑跨 HATCH 剪力墙/柱，真冲突）/ `BOUNDARY_OVERLAP_REVIEW` ×1。15 处 HATCH 冲突含南侧窗槛带（`md_0036–40`，测绘显示为混凝土槛）与东墙柱位——需结构方判定贴建或替换。

## 三、联合 POC（第三阶段）

| 图 | 文件 | 表达 |
|---|---|---|
| **A102** | `A102_WALL_DIFF_POC_V1.dxf` | 灰=结构底层（仅闭合+HATCH+真环）/ 黑=保留（粗=结构证据）/ 红+X=已批拆 / 品红=HOLD（含 "拆除未批-待结构核实" 注记）/ 橙=待裁 / 蓝=新建 |
| **A103** | `A103_CONSTRUCTION_POC_V5.dxf` | 既有 V5 管线重生成：黑=保留 / 蓝=拟建 / 品红=A-CONFLICT / A-DEMO 冻结；原生 DIMENSION×12 + 门×9 |

`W_EXT_N_BAL`：A102 上品红 HOLD 层 + X 叉 + 文字注记（**不是** A-WALL-DEMO）；A103 上其拆除段在冻结 A-DEMO 层、目标新墙照常绘制——保留设计表达但不发布为已批拆除。两图共用 XDATA 对象绑定与同坐标基准。

## 四、联合 QA（第四阶段）

| 检查 | 断言 | 结果 |
|---|---|---|
| QJ1 | 两图同 geometry_v05 快照 SHA | ✅ |
| QJ2 | A102 拆除集 == registry DEMOLISHED_CONFIRMED（4）；HOLD 集 == {N_BAL#demol0} | ✅ |
| QJ3 | A103 可见层无 SUPPRESS*；A-DEMO 冻结 | ✅ |
| QJ4 | 冲突对象在 A103 `A-CONFLICT` 品红层可见 | ✅ |
| QJ5 | 两图 DIMENSION 锚点对完全一致 | ✅ |
| QJ6 | A102 保留墙对象 ⊆ A103 可见墙 | ✅ |
| QJ7 | 全部源文件 live SHA FRESH | ✅ |

叠加检查图 `a102_a103_overlay.png`：同坐标基准下 A102 灰保留面与 A103 黑保留线重合、红拆段被 A103 新蓝墙正确避开、HOLD 品红区唯一且明显。

## 五、未决异常清单（仅此）

| 项 | 状态 | 归属 |
|---|---|---|
| `W_EXT_N_BAL` 拆除权限 | **HOLD**（0% 测绘覆盖，黑白语义未核实） | 结构方+开发商原图核对 |
| 15 处 STRUCT_HATCH_CONFLICT | REVIEW（贴建 or 替换判定） | 结构方 |
| 4 处 PENDING_REVIEW（CLK 隔墙等） | REVIEW（设计表达，不影响出图管线） | 设计确认 |
| 18 处 CLASSIFICATION_UNVERIFIED | REVIEW（外墙/柱无测绘结构覆盖） | 结构方 |
| 结构/复尺/封窗合规 | HOLD | 专业人员 |

## 六、产物

`P1_4_2_JOINT_POC.md` · `wall_state_registry.json/csv` · `A102_WALL_DIFF_POC_V1.dxf` · `A103_CONSTRUCTION_POC_V5.dxf` · `A102_POC.pdf`+`png` · `A103_POC.pdf`+`png` · `a102_a103_overlay.png` · `qa_joint.json` · `build_wall_registry.py` · `make_a102_poc_v1.py` · `joint_acceptance.py` · `three_source_mapping.py`（HATCH 孔洞修复）· `p14_tests.py`（13 项）

**边界**：两图均为 POC 测试版，非正式施工图；`V15_WORK.blend` 未动；源 DXF 未动。停 A102/A103 联合验收 Gate。
