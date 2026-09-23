# Task 02 — 现状空间语义与设计约束模型 报告

> Task 01 几何已冻结（geometry/dimensions 哈希锁定于 commit `7e2aa0f`）。
> 本任务只做语义与约束建模，**不做任何设计**。
> 全部数据引用 Task 01 对象 ID，不复制坐标真值。

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
- **modeled_plan_area = 150.48 m²**（湿/服务 38.33 m²，干区 112.15 m²）—— 为各空间多边形直接求和，**非销售/产权面积**；多边形沿墙面绘制，含局部重叠（休闲厅多边形覆盖衣帽间足迹）。
- 另有 1 个**未建模内部区**（`UNMODELED_INTERIOR_ZONE`：衣帽间以东、主卫/北卧/主卧门前的走廊带，约 x11300–12900 / y4650–6500）。源图无标注、无多边形，仅作图节点存在——已目视核实源图该区无文字。

## 2. 连接关系（circulation，17 条边）

- **入户**：EXTERNAL_COMMON_AREA →(D-01)→ 餐厅
- **开放连通**（无墙门洞）: 客厅↔餐厅、客厅↔休闲厅、餐厅↔休闲厅、休闲厅↔未建模走廊区
- **门洞连通**: 客厅↔北阳台(D-02)、休闲厅↔公卫(D-03)/书房(D-04)/北卧(D-05)/南卧(D-08)、走廊区↔主卫(D-06)/主卧(D-09)、衣帽间↔休闲厅(D-07)、生活阳台↔厨房(D-11)、北阳台↔北卧(D-12)、餐厅↔生活阳台(D-13)
- **连通分量 = 1**（含外部节点与未建模区）。
- **事实观察**（非评价）:
  - 厨房唯一通行路径 = 餐厅 →(D-13)→ 生活阳台 →(D-11)→ 厨房（CONSTRAINT-CIRC-KITCHEN，需现场核实是否有第二入口）
  - 书房、公卫、衣帽间、休闲厅**均无直接外窗**（无贴外墙洞口）——书房/公卫采光依赖相邻空间或外窗缺失需现场确认
  - 休闲厅是通行枢纽（7 条通行边），同时自身无窗

## 3. 邻接图（adjacency，25 条边）

几何邻接（共边）与通行边**不等价**：如 客厅↔公卫、厨房↔南卧 相邻但无洞口；反之开放通道无门洞。详见 `adjacency_graph.json`。

## 4. 门窗语义

- 13 门全部解析两侧空间（含外部节点/未建模区），**0 UNRESOLVED**；D-13 保持 `sliding_door_candidate`，D-10 西侧落在 niche 夹缝 → 标 UNMODELED_INTERIOR_ZONE（ISSUE-009）。
- 11 窗全部绑定室内空间 + 宿主墙 + `PLAN_*` 图像相对朝向（源图无指北针，未断言地理方位）。WIN-W1 跨餐厅/客厅两空间 → 双绑定 + LOW 置信度（ISSUE-012）。

## 5. 湿区/服务敏感区

WET: 主卫、公卫；SERVICE: 厨房（邻服务井 W-SHAFT-K, LOW）; SEMI_WET: 生活阳台、北阳台。
**未推断**任何管径/坡度/立管走向/燃气/电路 —— 全部记为需现场核实的 SERVICE_DEPENDENCY 约束。

## 6. 约束登记（24 条，21 条 ACTIVE）

| 严重度 | 数量 | 含义 |
|---|---|---|
| BLOCKING | 3 | 拆改前硬约束（结构鉴定、X0 基准、承重未知） |
| HIGH | 9 | 布局决策前必须核实（层高、围护权限、MEP、WIN-E1 冲突、WIN-W1、东北角、湿区） |
| MEDIUM | 7 | 需核实但不阻塞概念阶段 |
| LOW / INFORMATIONAL | 2 | 方向基准、法规体系未知 |

- 全部 13 个 Task 01 issue 已映射（ISSUE-002/007/008 记为 RESOLVED_HISTORICAL）。
- severity = "未来设计代理在不核实的情况下做假设有多危险"，**不表示构件不可改**。

## 7. IFC 语义模型

`ifc/C型_现状语义约束模型.ifc` —— 在 Task 01 IFC 上**只加元数据**:
- `Pset_Task02SpaceSemantics` × 13（IfcSpace）
- `Pset_Task02ElementSemantics` × 75（墙/门/窗/柱）
- `Pset_Task02Constraints` 按 subject_refs 绑定（含 ActiveConstraintCount / HighestConstraintSeverity）
- **几何不可变实测**: 全部 IfcWall/IfcColumn/IfcOpeningElement/IfcDoor/IfcWindow 世界包围盒 delta = **0.0mm**（容差 0.1mm）

## 8. 回归发现（Task 01 缺陷，未静默修复）

- **spaces[].label_px 为旧低分辨率（659×1024）坐标** —— 与 1279×1986 源图不符。属元数据字段非几何坐标，Task 02 未使用；建议 Task 01 后续修正。
- 休闲厅多边形足迹覆盖衣帽间（空间多边形为近似房间范围），面积合计存在 ~3.7m² 重叠 —— modeled_plan_area 仅供参考。

## 9. Gate 结果

| Gate | 结果 | 依据 |
|---|---|---|
| T02-1 Task01 不可变 | **PASS** | geometry/dimensions 哈希 = 基线 |
| T02-2 空间语义 | **PASS** | 13/13 映射；卧室重复名按位置区分；面积=多边形实算 |
| T02-3 元素-空间绑定 | **PASS** | 24 门窗全部解析（含外部/未建模节点），0 静默猜测 |
| T02-4 邻接/通行 | **PASS** | 25 邻接 + 17 通行边；邻接≠通行；分量=1 |
| T02-5 约束登记 | **PASS** | 13/13 issue 映射；每条含 evidence/confidence/verification；结构全 UNKNOWN |
| T02-6 湿区/服务语义 | **PASS** | 分类均有标注证据；无虚构 MEP |
| T02-7 IFC 语义 | **PASS** | pset 可查；几何 delta 0.0mm ≤0.1 |
| T02-8 可视 QC | **PASS** | 3 图与源图叠合核对：标注与源图一致、连线对应真实洞口、约束图不遮挡扭曲源几何 |
| T02-9 设计就绪 | **PASS** | known/unknown/owner-input/field-verification 四层已分离（见下） |
| T02-10 回归 | **PASS** | 92/92（72 旧 + 20 新） |

## 10. 就绪结论

- **已知（可安全使用）**: 空间清单与面积、门窗绑定、邻接/通行图、湿区分类、外围护判定。
- **未知但已登记**: 结构、层高、MEP、洞口精尺、东北角、薄线区 —— 均在 `constraint_register.json` + `field_verification_plan.md`。
- **待业主输入**: `owner_inputs_required.md` 17 组问题（Task 03 前置）。
- **阻塞项**: 3 条 BLOCKING 均针对"拆改决策"，不阻塞概念布局。

**Task 02 result: PASS_READY_FOR_BRIEF**
（= 现状语义模型足以支撑业主需求访谈与概念布局；不代表可出拆改图）
