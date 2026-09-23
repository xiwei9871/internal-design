# TASK01 REPORT — C 型户型原始平面图数字化重建

**状态定义**: SOURCE PLAN RECONSTRUCTION / 原始户型图数字化基准图。
**不是** As-Built / 竣工实测图。所有几何未经现场复核。

## 1. 原图明确给出的尺寸（P1）

| 链 | 位置 | 内容 | 置信度 |
|---|---|---|---|
| CHAIN-TOP-OUT | 顶部外链 | 5100 + 1900 + 3200 + 3300 | HIGH |
| CHAIN-TOP-IN | 顶部内链 | 1000/3100/1000/1000/900/700/1800/700/700/1900/700/100 | HIGH |
| CHAIN-BOTTOM-OUT | 底部外链 | 1400+1400+3000+2100+3600+3900+900 = 16300 | HIGH |
| CHAIN-BOTTOM-IN | 底部内链 | 14 段已录 + 尾部 2 段不可读（UNKNOWN） | MEDIUM |
| CHAIN-RIGHT-IN | 右侧内链 | 1000/700/2100/3000/1400/1900/2200/1800/500/700 | HIGH |
| CHAIN-RIGHT-OUT | 右侧总量 | 12900 | HIGH |

水平总宽 16300mm（顶部外链与底部外链互相印证）；竖向主包络 12900mm。

## 2. 尺寸约束固定的构件

- **南立面**：W-EXT-S 及窗洞 WIN-S1（2200）、WIN-S2（2500）— HIGH
- **西墙轴线**：W-EXT-W 位于外链刻度 X2800 — MEDIUM（外皮线部分缺绘，ISSUE-011）
- **分户内墙**：W-INT-X11500（X11500）、W-INT-X5800（X5800）、W-INT-X9800（X9800）、W-INT-X13000（X13000）— 由两条水平链交叉定位
- **北立面**：客厅凸窗 WIN-N1 = 3100mm（内链分段 + 像素缺口吻合）— HIGH
- **东立面**：W-EXT-E2 段窗洞 WIN-E2 = 3000mm、WIN-E3 = 1900mm（LOW）、主卧东窗 WIN-E1 = 1800mm（MEDIUM，见 ISSUE-005）
- **标高线**：Y0 南墙皮、Y4500 主卫南墙线、Y7800 公卫/书房南墙线、Y10800 阳台南墙线

## 3. 纯像素推算（P4）的构件

- 生活阳台三边栏杆/矮墙（W-BALC-*）
- 厨房→阳台门 D-11、各室内门洞宽度/位置（D-02…D-12）
- 衣帽间墙体（W-INT-CLK-*）
- 主卧东墙 W-EXT-E1、卧室北墙 W-EXT-NE
- 全部 AC 机位、柱、烟道（W-SHAFT-K、COL-*）

## 4. 仍然不确定 → 需现场复尺

见 `unresolved_issues.md`，共 11 项：底部外链左基准、底部内链尾部数字、内链 +400 偏移、黑墙结构属性、主卧东窗像素/尺寸冲突、12900 北端基准、厨房-阳台门位歧义、厨房南 1400 段、休闲厅垭口、东北角机位区、西墙外皮缺失段。

## 5. 同一 geometry source → 三端输出

`data/geometry.json` 为唯一契约：

- `scripts/build_dxf.py` → `cad/C型_原始户型数字化基准图.dxf`（mm, INSUNITS=4, R2018）
- `scripts/build_freecad.py` → `cad/C型_原始户型数字化基准模型.FCStd`（freecadcmd 生成；DesignID/SourceBasis/Confidence/NeedsFieldVerification 属性保留）
- `scripts/build_ifc.py` → `ifc/C型_原始户型数字化基准模型.ifc`（IFC4；Project→Site→Building→Storey；FieldVerified=false）
- `scripts/build_overlay.py` → `qc/overlay_*.png` + `overlay_metrics.json`
- `scripts/validate.py` → `qc/calibration.json` + `dimension_chain_audit.json` + `geometry_audit.json`

层高不在源数据中：IFC/FCStd 的拉伸使用 `visualization_only_height_mm=2800`，明确标注 NOT SOURCE DATA / NOT FOR CONSTRUCTION。

## 6. Overlay 叠回验证

`overlay_full.png` / `overlay_walls.png` / `overlay_openings.png`：重建几何以绿(HIGH)/橙(MEDIUM)/红(LOW) 半透明叠于原图之上。

自动指标（辅助，不构成验收）：24 面 MEDIUM+ 墙的边中点到源图暗线距离均值 **0.96 px ≈ 35.4 mm**，最大 4.4 px。

**硬门状态：MANUAL_PENDING — 需业主/复核人目视确认 overlay 无整体漂移、无旋转/比例错误、无房间错位。** 自动检查未发现 X/Y 比例错误（sx=37.0, sy=36.5, 差异 ~1.5%，见 calibration.json）。

尺寸优先的可见差异：主卧东窗 WIN-E1 按尺寸定位于 Y500-2300，源图绘制窗缝偏北 ~500mm（ISSUE-005，已在 overlay 中可见并记录）。

## 7. Gate 结果

| Gate | 结果 | 说明 |
|---|---|---|
| T01-1 Source Integrity | PASS | 原图未修改，SHA256 记录于 source_manifest.json |
| T01-2 Dimension Extraction | PASS | 6 条链全部录入；尾部不可读段标 UNKNOWN，未猜数字 |
| T01-3 Dimension Closure | PASS | 顶部内链分组=外链精确闭合；底部外链 16300 与顶部一致；右链中段=12900 闭合；两处 source 自身歧义标 SOURCE_CONFLICT（CONF-1/CONF-2），未静默处理 |
| T01-4 Geometry Validity | PASS | geometry_audit 无退化矩形/重复 ID/孤儿洞口；所有结构属性 UNKNOWN |
| T01-5 DXF | PASS | ezdxf 可重读；mm；图层 A-WALL/A-DOOR/A-WINDOW/A-DIMS/A-UNCERTAIN 等；无家具层 |
| T01-6 FreeCAD | PASS | freecadcmd 1.1.3 由 geometry.json 生成 FCStd（37 墙 + 3 柱，含溯源属性） |
| T01-7 IFC | PASS / Bonsai visual = MANUAL_PENDING | IFC4，ifcopenshell.open 成功；76 对象；IfcDoor/IfcWindow 带 HostWallID 属性（洞口未布尔切割，已在脚本注释说明）；Bonsai 目视检查待人工 |
| T01-8 Overlay | MANUAL_PENDING | 自动指标均值 35mm；硬性人工目视验收待业主确认 |
| T01-9 Provenance | PASS | 抽样 5 墙/3 门/3 窗/5 尺寸均可追溯至尺寸链刻度或像素区域（test_provenance_spot_check） |
| T01-10 Regression | PASS | 旧 37 项测试 + 新 23 项 = 60/60 PASS |

## 8. 结论

**PARTIAL**（除 T01-7 Bonsai 目视与 T01-8 overlay 人工验收外全部通过；这两项按任务定义必须人工确认，不能伪造 PASS）。

模型可用于后续空间规划/建模的基准输入；所有 LOW/UNKNOWN 项已隔离并可追溯。
