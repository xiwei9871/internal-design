# Task 02 — 现状空间语义与设计约束模型 报告（RC1）

> Task 01 几何已冻结（geometry/dimensions 哈希锁定于 commit `7e2aa0f`，
> 已合入 `improve/design-output-v14`）。本任务只做语义与约束建模，
> **不做任何设计**。全部数据引用 Task 01 对象 ID，不复制坐标真值。

## 0. RC1 修正说明

相对初版（8d1871f）的实质修正：

- **分支基座**：Task01 已 FF 合入 `improve/design-output-v14`；本分支 rebase 后仅含 Task02 提交
- **取消通用 UNMODELED_INTERIOR_ZONE**：拆为定位明确的派生区 `ZONE-MASTER-CORRIDOR`（x11400–12900, y4650–6500，由 CLK-E/X13000/Y4500-bc/CLK-N/COR-N-STUB 墙面包络导出）；D-10 西侧 niche 夹缝证据不足 → **UNRESOLVED**，不再挂到走廊区
- **邻接算法重写**：`buffer∩buffer` 改为"平行对向边 + 墙带间隙 + 投影重叠 ≥400mm"；`shared_boundary_mm` = 实际投影重叠长度；角点邻近不计邻接 → **R-LEISURE↔R-BATH-M 假阳性已消除**（两空间仅角点接近，投影重叠为 0）
- **面积核算精确化**：exact_sum / union / overlap 三值分列，不再用已舍入值求和；**union=exact，overlap=0**（初版报告"休闲厅覆盖衣帽间"的表述有误：R-LEISURE 为 L 形多边形，实际绕开了衣帽间）
- **Task01 空间多边形的性质已显式记录**：近似标注区域（approximate label regions），非严格墙界单元 —— 例如 R-LEISURE 跨越 W-INT-X7900-U。门侧解析因此采用"墙体感知探针 + 派生区单元"，见 `semantics/space_cells.json`

## 1. 空间清单（13 个建模空间）

| space_id | 源标注 | canonical_role | 面积 m² | 周长 m | 贴外墙 m | 湿区类 | 置信度 |
|---|---|---|---|---|---|---|---|
| R-LIVING | 客厅 | living_room | 23.52 | 19.4 | 13.31 | DRY | MEDIUM |
| R-DINING | 餐厅 | dining_room | 14.95 | 16.28 | 6.24 | DRY | LOW |
| R-LEISURE | 休闲厅 | family_hall | 14.76 | 20.3 | 0 | DRY | LOW |
| R-KITCHEN | 厨房 | kitchen | 8.23 | 12.6 | 4.85 | SERVICE | MEDIUM |
| R-BALC-LIFE | 生活阳台 | service_balcony | 7.35 | 11.9 | 8.85 | SEMI_WET | MEDIUM |
| R-BED-S | 卧室 | bedroom | 15.00 | 15.64 | 4.27 | DRY | MEDIUM |
| R-MASTER | 主卧 | master_bedroom | 16.46 | 16.3 | 9.75 | DRY | MEDIUM |
| R-BED-N | 卧室 | bedroom | 15.52 | 16.1 | 10.20 | DRY | LOW |
| R-CLOAK | 衣帽间 | walk_in_closet | 3.71 | 7.8 | 0 | DRY | LOW |
| R-BATH-M | 主卫 | bathroom | 5.28 | 9.7 | 3.60 | WET | MEDIUM |
| R-BATH-P | 公卫 | bathroom | 4.72 | 8.9 | 0 | WET | MEDIUM |
| R-STUDY | 书房 | study | 8.23 | 11.5 | 0 | DRY | MEDIUM |
| R-BALC-N | 阳台 | balcony | 12.75 | 15.2 | 7.10 | SEMI_WET | MEDIUM |

- 两处"卧室"按位置区分 `R-BED-S` / `R-BED-N`，**均保留 `source_label_zh="卧室"`**，未推断儿童房/老人房/客房。
- 面积（未舍入多边形实算）:**exact_sum = 150.5035 m², union = 150.5035 m², overlap = 0.0000 m² → modeled_plan_area = 150.50 m²**（湿/服务 38.34，干区 112.16）。**非销售/产权面积**。
- 派生区 `ZONE-MASTER-CORRIDOR`：衣帽间以东、主卫/北卧/主卧门前的走廊带，源图无标注（已目视核实），由墙面包络导出边界，`derived_from_task01_geometry=true`，非 Task01 房间。

## 2. 连接关系（circulation，16 条边 + 1 条未解析）

- **入户**：EXTERNAL_COMMON_AREA →(D-01)→ 餐厅
- **开放连通**（无墙开口，几何检测）: 客厅↔餐厅(2750mm)、客厅↔休闲厅(1850mm)、餐厅↔休闲厅(3050mm)、休闲厅↔走廊区(700mm)
- **门洞连通**: 客厅↔北阳台(D-02)、休闲厅↔公卫(D-03)/书房(D-04)/南卧(D-08)/衣帽间(D-07)、走廊区↔北卧(D-05)/主卫(D-06)/主卧(D-09)、生活阳台↔厨房(D-11)、北阳台↔北卧(D-12)、餐厅↔生活阳台(D-13)
- **未解析**: **D-10** —— 西侧探针落在 W-INT-NICHE(LOW）墙体内/其与 X7900 墙间的 ~400mm 夹缝，证据不足以判归属 → `UNRESOLVED ↔ R-LEISURE`（ISSUE-009 保留）
- **连通分量 = 1**（含外部节点与走廊区）。
- **事实观察**（非评价）:
  - 厨房唯一通行路径 = 餐厅 →(D-13)→ 生活阳台 →(D-11)→ 厨房（CONSTRAINT-CIRC-KITCHEN，需现场核实是否有第二入口）
  - 书房、公卫、衣帽间、休闲厅**均无直接外窗**
  - 休闲厅是通行枢纽（5 条通行边）且自身无窗；走廊区无标注但有 3 个门洞汇入

## 3. 邻接图（adjacency，28 条边）

新算法：平行对向边 + 间隙 ≤600mm（墙带）+ **投影重叠 ≥400mm**。`shared_boundary_mm` 为实际投影重叠长度（例：客厅↔餐厅 = 2800mm = y7900 共线重叠 x2900–5700）。
已消除的假阳性：**R-LEISURE↔R-BATH-M**（角点邻近，重叠 0）等。
含 4 条走廊区邻接边（`involves_zone=true`）。几何邻接 ≠ 通行。

## 4. 门窗语义

- 13 门中 12 门解析两侧空间（含外部节点/走廊区）,**D-10 = UNRESOLVED**；无静默猜测。D-13 保持 `sliding_door_candidate`。
- 11 窗全部绑定室内空间 + 宿主墙 + `PLAN_*` 图像相对朝向（源图无指北针）。WIN-W1 跨餐厅/客厅 → 双绑定 + LOW。

## 5. 湿区/服务敏感区

WET: 主卫、公卫；SERVICE: 厨房（邻服务井 W-SHAFT-K, LOW）; SEMI_WET: 生活阳台、北阳台。
**未推断**任何管径/坡度/立管走向/燃气/电路 —— 全部记为 SERVICE_DEPENDENCY 约束待现场核实。

## 6. 约束登记（24 条，21 条 ACTIVE）

| 严重度 | 数量 | 含义 |
|---|---|---|
| BLOCKING | 3 | 拆改前硬约束（结构鉴定、X0 基准、承重未知） |
| HIGH | 9 | 布局决策前必须核实（层高、围护权限、MEP、WIN-E1 冲突、WIN-W1、东北角、湿区） |
| MEDIUM | 7 | 需核实但不阻塞概念阶段 |
| LOW / INFORMATIONAL | 2 | 方向基准、法规体系未知 |

- 全部 13 个 Task 01 issue 已映射（ISSUE-002/007/008 = RESOLVED_HISTORICAL）。
- severity = "未来设计代理不核实就做假设的风险"，**不表示构件不可改**。

## 7. IFC 语义模型

`ifc/C型_现状语义约束模型.ifc` —— 在 Task 01 IFC 上**只加元数据**:
- `Pset_Task02SpaceSemantics` × 13、`Pset_Task02ElementSemantics` × 75、`Pset_Task02Constraints` 按 subject_refs 绑定
- **几何不可变实测**: 世界包围盒 delta = **0.0mm**（≤0.1mm 门禁）

## 8. 回归发现（Task 01 缺陷，未静默修复）

- **spaces[].label_px 为旧低分辨率（659×1024）坐标**，与高分辨率源图不符。元数据字段非几何坐标；Task 02 未使用；建议 Task 01 后续修正。
- ~~休闲厅覆盖衣帽间~~（初版误报，实为 0 重叠 —— 见 §0）

## 9. Gate 结果

| Gate | 结果 | 依据 |
|---|---|---|
| T02-1 Task01 不可变 | **PASS** | geometry/dimensions 哈希 = 基线 |
| T02-2 空间语义 | **PASS** | 13/13 映射；卧室重复名按位置区分；多边形性质已显式标注 |
| T02-3 元素-空间绑定 | **PASS** | 12 门解析 + D-10 显式 UNRESOLVED；11 窗全绑 |
| T02-4 邻接/通行 | **PASS** | 面对边投影算法；假阳性消除；邻接≠通行；分量=1 |
| T02-5 约束登记 | **PASS** | 13/13 issue 映射；每条含 evidence/confidence/verification |
| T02-6 湿区/服务语义 | **PASS** | 分类均有标注证据；无虚构 MEP |
| T02-7 IFC 语义 | **PASS** | pset 可查；几何 delta 0.0mm |
| T02-8 可视 QC | **PASS** | 业主目视验收通过：语义叠图与源图一致、走廊区定位正确、D-10 保持 UNRESOLVED、无断区混并、通行边对应真实洞口、无角点假邻接、约束图未遮挡源几何 |
| T02-9 设计就绪 | **PASS** | known/unknown/owner-input/field-verification 四层分离 |
| T02-10 回归 | **PASS** | 100/100（72 旧 + 28 新） |

## 10. 就绪结论

- **已知**: 空间清单与面积、门窗绑定、邻接/通行图、湿区分类、外围护判定。
- **未知已登记**: 结构、层高、MEP、洞口精尺、东北角、薄线区、D-10 西侧归属（UNRESOLVED）。
- **待业主输入**: `owner_inputs_required.md` 17 组问题。
- **阻塞项**: 3 条 BLOCKING 均针对拆改决策，不阻塞概念布局。

**Task 02 result: FINAL PASS — PASS_READY_FOR_BRIEF**
（业主已验收 T02-8；语义模型足以支撑业主需求访谈与概念布局，不代表可出拆改图）

补充说明（文档级，未改数据）:**D-05** 的 `side_a_all = [ZONE-MASTER-CORRIDOR, R-LEISURE]` —— 洞口落在走廊区与休闲厅东北带的连续边界上，按源图洞口位置取 ZONE-MASTER-CORRIDOR 为规范侧，歧义记录保留于 `element_semantics.json`。
