# TASK01 REPORT — C 型户型原始平面图数字化重建（RC1 / 高分辨率源图版）

**状态定义**: SOURCE PLAN RECONSTRUCTION / 原始户型图数字化基准图。
**不是** As-Built / 竣工实测图。所有几何未经现场复核。

## 0. 源文件

| 项 | 值 |
|---|---|
| 文件 | `source/source_plan_original.jpg` |
| 尺寸 | **1279 × 1986** RGB（高分辨率业主源图，RC1 替换 659×1024 降采样副本） |
| SHA256 | `0125ad6c169550e5d1230bb3a3e5023bceaa81e10ed8ee69ff665b30d0a8d3c1` |
| 标定 | sx = 19.131 mm/px，sy = 18.832 mm/px（各向异性 ~1.6%，见 calibration.json） |
| manifest | `source/source_manifest.json` |

所有 pixel anchor / px_evidence / 派生坐标均在高分辨率源上重新检测，未继承低分辨率坐标。

## 1. 原图明确给出的尺寸（P1，高分辨率复核）

| 链 | 位置 | 内容 | 置信度 |
|---|---|---|---|
| CHAIN-TOP-OUT | 顶部外链 | 5100 + 1900 + 3200 + 3300 | HIGH |
| CHAIN-TOP-IN | 顶部内链 | 1000/3100/1000/1000/900/700/1800/700/700/1900/700/100 | HIGH |
| CHAIN-BOTTOM-OUT | 底部外链 | 1400+1400+3000+2100+3600+3900+900 = 16300 | HIGH |
| CHAIN-BOTTOM-IN | 底部内链 | 1000+1000+400+2100+900+1400+700+700+2200+700+700+2500+700+700+**200+100** = **16000**（X400→X16400 闭合，RC1 尾部已读出） | HIGH |
| CHAIN-RIGHT-IN | 右侧内链 | 1000/700/2100/3000/1400/1900/2200/1800/500/700 | HIGH |
| CHAIN-RIGHT-OUT | 右侧总量 | 12900 | HIGH |

水平总宽 16300mm；内链自 X400 至外立面 X16400；竖向主包络 12900mm。

## 2. 高分辨率复核带来的实质修正（vs 71760fa）

- **底部内链尾部 200+100 读出**，内链 16000 完全闭合（原 UNKNOWN 消除）
- **新增 D-13**：餐厅南墙发现 ~1900mm 宽洞口 X2900–4830（生活阳台唯一室内通道，判定推拉门候选，MEDIUM）
- **WIN-S3 确认**：厨房南窗 X5800–7200（1400 尺寸段 + 多线窗符号），LOW → HIGH
- **D-11 确认**：厨房↔生活阳台门在 X5800 墙 Y1400–2300，门扇绘于厨房内侧
- **衣帽间西墙** 像素校正 X9200 → **X9000**（W-INT-CLK-W）
- **Y4500 墙系细化**：厚墙至 X8236；X8236–9000 为 D-08 洞口；X9000–11400 为薄墙（新增 W-INT-Y4500-b）
- **WIN-S2 校正为 2500mm**（X12200–14700，与内链 2500 段吻合，原 1400 有误）
- **D-07/D-08/D-09 洞口** 按实测缺口修正
- **WIN-W1** 重读：西墙 Y6650–10940 为无填充薄线区，性质不明 → LOW，入 ISSUE-012

## 3. 尺寸约束固定的构件（P1/P2）

- **南立面**：W-EXT-S 及窗洞 WIN-S1（2200, HIGH）、WIN-S2（2500, HIGH）、WIN-S3（1400, HIGH）
- **西墙轴线**：W-EXT-W（X2800）— MEDIUM（外皮线部分缺绘，ISSUE-011/012）
- **分户内墙**：W-INT-X11500、W-INT-X5800、W-INT-X9800、W-INT-X13000 — 水平链交叉定位
- **北立面**：客厅凸窗 WIN-N1 = 3100mm — HIGH
- **东立面**：WIN-E2 = 3000mm、WIN-E3 = 1900mm（LOW）、WIN-E1 = 1800mm（MEDIUM，源内尺寸/像素冲突，ISSUE-005）
- **标高线**：Y0 南墙皮、Y4500、Y7800、Y10800、Y12900（外链总量基准，ISSUE-006）

## 4. 纯像素推算（P4）的构件

- 生活阳台三边栏板/墙（W-BALC-*）、餐厅↔阳台推拉洞口 D-13
- 各室内门洞（D-02…D-12）、衣帽间墙体（W-INT-CLK-*）
- 主卧东墙 W-EXT-E1、卧室北墙 W-EXT-NE
- 全部 AC 机位、柱、烟道（W-SHAFT-K、COL-*）

## 5. 仍不确定 → 需现场复尺

见 `unresolved_issues.md`，**13 项中 3 项已解决**（ISSUE-002/007/008），遗留 10 项：
ISSUE-001 底部外链左基准悬空、003 内链 +400 偏移、004 结构属性、005 主卧东窗冲突、006 12900 北端基准、009 休闲厅垭口、010 东北角机位区、011 西墙外皮缺失段、012 西墙薄线区性质、013 D-13 洞口类型推断。

## 6. 同一 geometry source → 三端输出

`data/geometry.json` 为唯一契约（38 墙 / 3 柱 / 13 门 / 11 窗 / 13 空间 / 6 机位）：

- `build_dxf.py` → `cad/C型_原始户型数字化基准图.dxf`（mm, INSUNITS=4, R2018, 1:1）
- `build_freecad.py` → `cad/C型_原始户型数字化基准模型.FCStd`（65 对象：38 墙 + 3 柱 + 13 门 + 11 窗；含 DesignID/SourceBasis/Confidence/NeedsFieldVerification/HostWallID 属性）
- `build_ifc.py` → `ifc/C型_原始户型数字化基准模型.ifc`（IFC4；**24× IfcOpeningElement + 24× IfcRelVoidsElement + 24× IfcRelFillsElement**；IfcDoor/IfcWindow 各与唯一宿主洞口关联并带 40mm 可视化门板；FieldVerified=false / SourceStatus="Source Plan Reconstruction" 写入项目 pset；**RC2 修复 IfcRectangleProfileDef 剖面原点 —— 世界包围盒与契约逐面对齐 ≤1mm**）
- `build_overlay.py` → overlay_*.png + `overlay_metrics.json`（matched-source 残差）
- `validate.py` → calibration.json + dimension_chain_audit.json + `dimension_model_measurements.json` + geometry_audit.json（Shapely）

层高不在源数据中：拉伸参数 `visualization_only_height_mm=2800`，标注 NOT SOURCE DATA / NOT FOR CONSTRUCTION。

## 7. Overlay 叠回验证

`overlay_full.png` / `overlay_walls.png` / `overlay_openings.png`（1279×1986 全图叠加，绿=HIGH / 橙=MEDIUM / 红=LOW）。

**matched-source 指标**（主指标，对比同一构件的实测像素带/缺口）：
- `wall_edge_residuals`：37 面墙，带外溢出最大 12.9px（W-BAY-JW，LOW），边缘均值差 5.7px
- `opening_anchor_residuals`：24 个洞口；多数 |Δ|≤13px —— 系统性约 +12px/−10px 不对称源于源图把门弧/框线画入洞口（缺口实测值偏宽），属绘制习惯非模型错误
- 显著残差：WIN-E1 Δ≈70px = **ISSUE-005 已记录的尺寸↔像素冲突**（尺寸优先）；W-BAY-JW / W-EXT-S / W-EXT-E2 外墙皮绘制与尺寸基准偏差 ~100–250mm（制图误差，详见 unresolved_issues.md 附录）
- 次级诊断（仅供参考，不作门禁）：nearest-dark-pixel 均值 1.31px

**硬门状态：MANUAL_PENDING — 需目视确认无整体漂移/旋转/比例错误/房间错位。** 自动检查：sx/sy 各向异性 ~1.6%，无比例或旋转错误迹象。

## 8. Gate 结果（RC1 重报）

| Gate | 结果 | 说明 |
|---|---|---|
| T01-1 Source Integrity | **PASS** | 1279×1986 真源，SHA256 已记录，原图未覆盖 |
| T01-2 Dimension Extraction | **PASS** | 6 条链全部录入；高分辨率下尾部 200+100 已读出；无 UNKNOWN 段残留 |
| T01-3 Dimension Closure | **PASS** | `qc/dimension_model_measurements.json`：24 个 HIGH 段全部模型实测 ≤1mm（实测全部 0 误差），HIGH 链累计误差 ≤2mm（全 0）；真模型测量而非算术闭合 |
| T01-4 Geometry Validity | **PASS** | Shapely 校验：valid/正面积/无自交/无重复/无非预期重叠；geometry_audit problems=[] |
| T01-5 DXF | **PASS** | ezdxf 可重读；mm；1:1；图层齐；无家具层 |
| T01-6 FreeCAD | **PASS** | FCStd 重开校验：墙 38/门 13/窗 11 = geometry.json 精确一致；溯源属性齐全 |
| T01-7 IFC | **PASS** | IFC4；IfcOpeningElement=24、IfcRelVoidsElement=24、IfcRelFillsElement=24；**几何包围盒实测**：38 墙 + 24 洞口经 `ifcopenshell.geom.create_shape` 与契约逐面对齐 ≤1mm；**Bonsai 目视 PASS**：Blender 5.2 + Bonsai 导入后 38 墙网格包围盒与契约 ≤1mm（`qc/bonsai_scene_audit.json`），开洞位置正确、无半宽平移；`qc/bonsai_ifc_overview.png` / `qc/bonsai_ifc_openings.png` |
| T01-8 Overlay | **MANUAL_PENDING** | matched-source 指标已出（见 §7）；硬性人工目视验收待业主 |
| T01-9 Provenance | **PASS** | 抽样 5 墙/3 门/3 窗/5 尺寸全部可追溯 |
| T01-10 Regression | **PASS** | 72/72（旧 A14 回归 + Task01/RC1/RC2 新增测试） |

## 9. 结论

**PARTIAL → 待业主验收**：自动化可验证的门禁全部 PASS，T01-7 已于 RC2 完整通过（语义关系 + 几何包围盒 + Bonsai 目视三重验证）；仅剩 T01-8 overlay 人工验收按任务定义必须人工确认，不伪造 PASS。

模型可用于后续空间规划/建模的基准输入；所有 LOW/UNKNOWN 项已隔离并可追溯。
