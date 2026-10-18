# DESIGN_DECISIONS_V01 — 业主设计决策记录

日期：2026-10-18 · 状态：OWNER_CONFIRMED · 效力：优先于 `brief_v01.md` 中冲突的旧约束；brief 保留为历史记录，冲突项标记 `SUPERSEDED_BY_OWNER_DECISION`，不删除。

## D01 — 北阳台封窗

- `existing_state = OPEN_NOT_ENCLOSED`（原始建筑现状，brief_v01 记录）
- `proposed_state = ENCLOSED_GLAZING`（本次装修计划内工程）
- FreeCAD / Blender / 装修施工图均按封窗后目标状态表达，不回退为开放阳台
- 封窗具体构造、安装尺寸及实施合规条件 → `to_verify`（施工前核实）
- 原始约束状态：`SUPERSEDED_BY_OWNER_DECISION`

## D02 — 墙体拆改（5 处）

- 业主认可当前 5 处拆改设计：厨房西墙中段、走廊西墙中段（楼梯敞开）、阳台北墙东段、客厅北墙旧带、阳光房北带
- 保留 FreeCAD / Blender 现有拆改布局；A102 按现设计继续完善
- **业主认可设计 ≠ 结构安全审批**：未核实结构属性的拆改段保持施工交付 HOLD
- 原始约束状态：`SUPERSEDED_BY_OWNER_DECISION`（设计层）；结构核实 = `HOLD`（独立）

## D03 — 错层缓坡

- 当前装修不设置缓坡；仅为未来适老化改造预案
- FreeCAD / Blender / 施工图均不增加缓坡；保留既有 3 级台阶设计（+150/+300/+450）
- 约 450mm 高差及踏步尺寸 → `to_verify`（现场复核）
- 不因旧 brief 坡道约束自动恢复坡道
- 原始约束状态：`SUPERSEDED_BY_OWNER_DECISION`

## 流程约定

- 本文件版本化（V01）；后续决策追加 D04+ 并升版
- 出图管线读取本文件：`proposed_state` 为图纸表达依据；`existing_state` 仅用于拆改图对照与现状说明
- 渲染管线不受影响
