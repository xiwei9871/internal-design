# DATA_AUTHORITY_REGISTER_V01 — 世纪欣园数据分层

> **项目规则(直接引用)**:Furniture geometry in FreeCAD is not Ground Truth.
> It is a Human Design Guide. Architecture + verified openings are Ground Truth.

## 层级

| 层 | 内容 | 允许自动改 |
|---|---|---|
| **A. GROUND_TRUTH_ARCH** | 标准 CAD 墙体 / 实际尺寸 / 门洞 / 阳台边界 / 飘窗 XY 轮廓 / 错层平面 / 拆改后最终墙体 | ❌ |
| **B. GROUND_TRUTH_OPENING** | `95ab90e` FINAL_WINDOW_REGISTER 9 条窗/玻璃门 registry + WINDOW_REF_* 语义链接 | ❌ |
| **C. HUMAN_DESIGN_GUIDE** | FreeCAD 里的家具/洁具/家电 guide(床、沙发、桌椅、柜体占位、洗衣机、NAS、打印机…)——经人工确认但仍可在 B1/B2 调整 | ✅ |
| **D. BLOCKOUT_TEMP / TO_VERIFY** | 墙高 2.5、女儿墙 1.05、窗台/台面 Z、侧墙厚 100、家具高度标准值、柜体最终尺寸(施工前复尺) | ✅ |

## 容器文件(唯一 Ground Truth 容器)

```text
ARCH_GROUND_TRUTH_CONTAINER =
  cad/freecad_import/世纪欣园FF_PRE_BLENDER_MASTER_V2.FCStd
  sha256 = 0c30510bc3fe4862d5759c5402146987b6384558a063983b0cab66786de85469

  = WINDOW_RESTORED (sha 9c2aa9ba…de3e, 415 physical + 9 WINDOW_REF) 的 PRE_BLENDER 后续
  内含:384 GROUND_TRUTH_ARCH objects + 44 HUMAN_DESIGN_GUIDE + 10 WINDOW_REF 节点
```

原始 DWG 事实源:`世纪欣园FF.dwg` sha256 `f01a9bb5…c360`(结构现状；附图户型图:黑=不可拆,白=可拆)。

## 关键规则(防再犯)

1. 不得用家具位置反推 wall / room / window / door。
2. Pascal 需要 host wall 时,**只能查 register/removed_walls**,不得发明新墙。
3. `HUMAN_APPROVED DESIGN`(洁具位、沙发、床、茶台)≠ AS-BUILT——可继续改。
4. 建模链:**GROUND_TRUTH container → deterministic → Pascal Architecture**;
   家具独立链路 `FreeCAD guide → Furniture Design Register → Pascal blockout`,3D 里合并。
