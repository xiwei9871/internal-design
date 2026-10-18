# P1.4.3 — A102/A103 联合验收修复

**审核**：`9312e51` 三个实质缺口（QJ5 假 PASS、A103 未由 registry 驱动、拆改语义混用）
**本提交**：T1–T5 全部落实
**正常 QA**：`qa_joint_v2.json` = **PASS**（QJ1–QJ8）
**破坏性测试**：`p143_negative_tests.py` = **5/5 检出**

---

## T1 — 两图统一由 registry 驱动

| 图 | 生成器 | 状态来源 |
|---|---|---|
| A102 | `make_a102_poc_v2.py` | `wall_state_registry.a102_role` → 图层/角色/XDATA |
| A103 | `make_a103_poc_v6.py` | `wall_state_registry.a103_role` → part 级图层分配 |

`geometry_v05.json` 只供几何轮廓、对象身份、标注锚点；工程状态一律由 registry 给出。A103 新增规则：`DRAW_NEW` 且带 `overlap_class` 的 16 个对象 → `A-REVIEW` 橙层（待核实重叠，不装作普通新建墙）。

## T2 — QJ5 尺寸一致性真实现

- 统一 schema：两图每个 `DIMENSION` 写 `DEVINDIM = [tag, anchorA, anchorB, axis, value(mm)]`
- 解析时缺任一字段 → 直接记入 `dim_errs`（不再吞异常成空集）
- 逐项比较两图 `tag/anchors/axis/value`；并复核 `value` 与锚点真实距离 ≤0.5mm
- **负向证明**：删除 XDATA → FAIL（`missing DEVINDIM`）；改值 +100 → FAIL（`schema mismatch 14300 vs 14400`）

## T3 — QJ4/QJ6 几何检查

- QJ4：逐冲突对验证——非保留方必须在 `A-CONFLICT`，双方都必须落在某可见层；16 个 `overlap_class` 对象必须在 `A-REVIEW`。**负向**：删一条 A-CONFLICT 实体 → 检出 `W_wall_md_0004: invisible` + `no non-retained side`
- QJ6：同名墙 `(base,#pN)` 归一化键 → **Polygon 对称差 <2%** 才一致。**负向**：南墙平移 100mm → 检出 `GEOM_DIFF 40000mm²`
- 缺绑定或几何不一致 → HOLD

## T4 — 拆改语义三分

registry 每条新增三个独立字段：

| 字段 | 取值 |
|---|---|
| `design_intent` | `OWNER_DESIGN_APPROVED`（D02 业主确认设计意图）/ RETAINED / UNRESOLVED |
| `structural_verification` | `VERIFIED_NO_STRUCT_FILL` / `UNVERIFIED_DEVELOPER_PLAN` / `BLOCKED_STRUCT_OVERLAP` |
| `construction_authorization` | `PENDING_SITE_VERIFY` / `HOLD` |

- 4 处 D02 拆改 → `DESIGN_APPROVED_DEMO`（**设计确认拟拆**，施工批准仍 PENDING）
- `W_EXT_N_BAL` → `DEMOLITION_HOLD` + `construction_authorization=HOLD`（设计目标不变）
- 15 处 HATCH 重叠 → `UNVERIFIED_STRUCT_OVERLAP`（**待核实重叠**，不宣称已证真冲突）

## T5 — CAD 可交付性

| 项 | 结果 |
|---|---|
| 真 A1 纸空间 VIEWPORT 1:50 | ✅ 两图各 1 个（780×520 纸面窗，view_height=26000 模型mm） |
| DXF 原生数据出 PDF | ✅ `ezdxf.addons.drawing` 直读 DXF 模型空间渲染（非平行重绘） |
| FreeCAD `importDXF` 打开 | ✅ 两图 open OK（仅常规 unsupported 警告：ATTDEF/ATTRIB/SOLID/VIEWPORT——FreeCAD 旧导入器限制，**不等于专业编辑器验收**） |
| QCAD/AutoCAD 编辑器 + 物理打印 | **NOT_RUN**（本机无 QCAD；专业编辑/打印验证保持未执行） |

## 破坏性测试台账

| 注入 | 检出 |
|---|---|
| N1 删 A102 dim XDATA | QJ5 FAIL：`missing DEVINDIM` |
| N2 A103 dim 值 +100 | QJ5 FAIL：`14300 vs 14400` |
| N3 A103 南墙平移 100mm | QJ6 FAIL：`GEOM_DIFF 40000mm²` |
| N4 删 A103 冲突实体 | QJ4 FAIL：`invisible` + `no non-retained side` |
| N5 A102 HOLD→已批拆除层 | QJ2 FAIL：demo/hold 集合同时破裂 |

## 产物

`make_a102_poc_v2.py` · `make_a103_poc_v6.py` · `joint_acceptance_v2.py` · `p143_negative_tests.py` · `A102_WALL_DIFF_POC_V2.dxf` · `A103_CONSTRUCTION_POC_V6.dxf` · 两图 native PDF+PNG · `qa_joint_v2.json` · `wall_state_registry.json`（语义三分字段）· `P1_4_3_JOINT_QA.md`

**独立 HOLD（不变）**：N_BAL 拆除实施、结构核验、现场复尺、封窗合规、专业 CAD 编辑器验收、物理打印。停审，不扩大图种。
