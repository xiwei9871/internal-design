# P0 报告：施工图源数据勘察与基线（V15 全屋 / C 型）

日期：2026-10-18 · 任务书：CODEX_TASK_CONSTRUCTION_DRAWINGS_V01 · 本报告只读，未修改任何设计源文件

## 1. 输入清单（manifest）

`cad/CONSTRUCTION_INPUT_MANIFEST.json` —— 13 项输入全部定位，附 SHA256 + 来源性质 + 状态：

| 类别 | 文件 | 状态 |
|---|---|---|
| as_built | C型_原始户型数字化基准图.dxf / 基准模型.FCStd | verified |
| design | S2_CURRENT_DESIGN_V1_R2_2_AUDIT.FCStd、WORKING/WINDOW_RESTORED/PRE_BLENDER_MASTER.FCStd | design_intent |
| design | V15_WORK.blend（灯具已修）、V15_PBR.blend | design_intent |
| verified | brief_v01.md、FINAL_WINDOW_REGISTER_95ab90e.json | verified |
| derived | plan_geom.json、stair_*.json、model_walls*.json | design_intent |
| visual_only | topmap.png（材质编码俯视图） | visual_only |

坐标系证据：基准 DXF 与 Blender 零偏移对齐（西墙 x2700-2900、南墙 y-200、北缘 y13400-13600）。无 MISSING 项。

## 2. QA 基线（`qa/baseline_v01.json`，只读脚本）

7 张 DXF（6 图+自动拾取 1 张重复名）→ **7 BLOCK / 16 WARN**：

| 发现 | 级别 | 范围 |
|---|---|---|
| 原生 DIMENSION = 0（尺寸全是 LINE+TEXT 拼装） | BLOCK | 全部 6 图 |
| A-UNCERTAIN 38 实体 + A-SOURCE-REF 62 实体**可见** | BLOCK+WARN | **仅 A102**（其余图已冻结） |
| DXF 版本混用（A201=AC1024，其余 AC1032） | WARN | A201 |
| 无纸空间布局（Layout1 全空） | WARN | 全部 |
| HZTXT 字体 = macOS 绝对路径 | WARN | 全部 |
| 结构读取自动修复 6/9 处 | WARN | A102/A201 |

## 3. 问题台账（5 类）

### 3.1 图纸结构性
- 全部图纸无原生标注实体；A102 漏冻结校核层；版本/图层约定不统一；脚本含绝对路径+硬编码坐标，无对象 ID 追溯。

### 3.2 交付表现
- 标注值非锚点计算 → 设计变更不传播；符号为散装折线非 INSERT 块；无 PDF/纸幅验证；无跨图一致性检查。

### 3.3 设计缺失
- 客卫无台盆对象（图上已标"待确认"）；马桶坑距未知；配电/弱电箱按原位假设；台阶 450mm 在模型成立但 brief 标注"待实测"；家具全部包围盒。

### 3.4 现场复尺待确认（HOLD 类）
- **北阳台**：brief_v01 `OPEN_NOT_ENCLOSED` vs 模型封闭——**OWNER_RESOLVED (D01)**：按封窗设计；构造/尺寸/合规 `to_verify`。详 `DESIGN_DECISIONS_V01.md`。
- **拆改墙体**：brief"既有墙洞口不可变" vs 模型已拆 5 处——**OWNER_RESOLVED (D02)**：设计认可保留；结构属性 `HOLD`，A102 未经结构核实不得作施工依据。
- **RAMP**：brief 临时适老坡道 vs 业主指令移除——**OWNER_RESOLVED (D03)**：本期不设，仅为未来预案；不因 brief 自动恢复。450mm 高差/踏步 `to_verify`。
- 坑距/立管/坡度/门窗洞口现场尺寸/面层选型 → `to_verify`。

### 3.5 安全/合规高风险
- 拆除段承重属性未核实 → A102 在结构审查前**不得作为施工依据**（图上已注明"承重构件严禁拆改"）。
- 主卫适老（扶手/零门槛/坐浴）设计要点无节点详图表达。
- A302/A303 是点位示意图，非回路/管路施工图，缺管线拓扑不得交付施工。
- 台阶踏步深度变化大，净宽/踏步一致性/扶手连续性未核。

## 4. P0 Gate 自评

| 要求 | 状态 |
|---|---|
| 全部源文件找到或列缺项 | PASS（0 MISSING） |
| 单位/变换有证据 | PASS |
| 图号→工程对象→源文件映射 | **PARTIAL**：图纸实体尚无 source_object_id（P1 任务） |
| 未修改既有设计文件 | PASS |

## 5. 建议

P0 → **PROCEED TO P1**（A103 原生标注 POC）。
设计冲突三项已于 2026-10-18 由业主决策：**OWNER_RESOLVED**（D01 北阳台封窗 / D02 五处拆改 / D03 缓坡不设），见 `DESIGN_DECISIONS_V01.md`。仍独立 HOLD：拆改段结构安全核实、450mm 高差/踏步现场复核、封窗构造合规——属业主/结构职权，不阻塞出图管线研发。
