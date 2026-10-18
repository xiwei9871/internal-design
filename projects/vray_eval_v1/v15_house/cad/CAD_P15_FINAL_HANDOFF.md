# CAD P1.5 FINAL HANDOFF — A102/A103 移交专业 CAD 验收
生成基线: `cc59a5c` + 本收尾补丁 | 分支: `v15-cad-pipeline-2026-10-17`

## 交付物清单（本次重生成）

| 文件 | 说明 | sha256(前10) |
|---|---|---|
| `A102_WALL_DIFF_POC_V3.dxf` | 拆改图（registry+NC差集驱动） | 见 review_packages/P1_5_1 标题 |
| `A103_CONSTRUCTION_POC_V7.dxf` | 最终平面图 | 同上 |
| `*.native.png/.pdf` | ezdxf 原生渲染预览（模型空间） | — |
| `review_packages/P1_5_1/` | 全图×2、叠加、厨房/次卫/北阳台/错层、异常清单（DXF 直读+sha 标注） | — |
| `derived/new_construction_v1.{json,csv}` | 构件分类+二维占地面积 | — |
| `derived/dims_extra.json` | 22 条语义标注（measurement_type/ref/resurvey） | — |
| `derived/qa_joint_v2.json` | QJ1–QJ9 全 PASS | — |

## QJ9 已修正（Gate A）

- **双向检查**：`missing`（CAD 漏画）与 `extra`（CAD 多画）同时判定，任一超限即 HOLD。
- **零容差基线收紧**：单片差异 >1000mm² 即失败（原 20,000mm² 静默阈值废除）；累计 >3000mm² 失败——多删小墙段无法逃逸。
- **明细报告**：`QJ9_missing_detail`/`QJ9_extra_detail` 列出每片面积+质心（≥100mm²）；`QJ9_missing_by_type` 按 EXISTING/WALL_PARTITION/COLUMN_PIER/SOFFIT_HEADER/STAIR_STEP/DOOR_OPENING 分类。
- **定位声明**：QJ9 = **二维几何一致性 Gate**——证明同一 geometry_v05 快照与 CAD 的 2D 一致性；不声明 Blender 三维高度/洞口做法正确（属专业验收项）。
- **负向测试 7/7**：新增 N6（插入幻影墙→extra 检出）、N7（删 6 段小墙累计 43.6k→missing 检出）。
- 本次实跑：`missing_total=2751mm²`（5 片 <1000 的碎片，如实报告非零）、`extra=0`、`max_local_dev=647mm²`。

## 面积口径修正（Gate B）

`area_by_component_type` 字段已更名 `*_plan_footprint_mm2`——**二维占地面积**，非砌筑/抹灰/采购工程量：

| 类型 | 新增二维占地 | 备注 |
|---|---|---|
| WALL_PARTITION | 9.77 m² | 砌墙量需乘墙高/厚度另算 |
| COLUMN_PIER | 0.42 m² | 同上 |
| STAIR_STEP | 3.73 m² | 台阶展开面积另算 |
| SOFFIT_HEADER | 7.90 m² | **施工归类待人工复核**（砌墙/混凝土窗头/封板） |

## 专业 CAD 验收（Gate D — NOT_RUN）

本机无 QCAD/AutoCAD/浩辰/中望/LibreCAD（仅 FreeCAD.app，`importDXF` 可开但 VIEWPORT/ATTDEF 等特性不支持，不能代替专业编辑器）。**以下验证项保持 NOT_RUN，须在专业 CAD 软件中人工完成：**

### 待检查文件
`A102_WALL_DIFF_POC_V3.dxf`、`A103_CONSTRUCTION_POC_V7.dxf`

### 验收步骤（建议在 QCAD Pro 或 AutoCAD）
1. **打开**：无代理图形警告；中文字体（HZTXT/SimHei 回退）无缺字方块。
2. **原生 DIMENSION**：选中任一尺寸可编辑/重定位；`demo_span_*`/`new_loc_*`/`door_w_*` 值与图面一致；34 个尺寸全部存在（QJ5 已验数据层）。
3. **图层**：`A-WALL-RETAIN-EQUIV`/`A-DUP`/`A-UNCERTAIN`/`A-DIMS-LEGACY`/`A-SOURCE-REF`/`A-ROOM` 应处于冻结；解冻后重影副本可见（留痕可追溯）。
4. **纸空间**：Layout1 存在；视口 780×520mm，`view_height=26000` → **1:50**；A1 边框 841×594；标题栏文字可读。
5. **打印比例**：PDF 导出 Layout1，实测打印比例 1:50（用已知 14300mm 总长尺寸复核）。
6. **XDATA 抽查**：任一墙线 `DEVINSRC`、任一尺寸 `DEVINDIM` 可读（QCAD 需插件或属性编辑器；AutoCAD 用 (entget)）。
7. **施工可读性**：拆除红 X、HOLD 品红、新墙蓝、保留黑、家具灰——现场施工人员能否直接读图。

## 继续 HOLD（不随本轮解除）

- `W_EXT_N_BAL` 拆除实施许可（结构+封窗合规）
- 15 处 `UNVERIFIED_STRUCT_OVERLAP` 待结构方判定
- 4 处 `PENDING_REVIEW` 设计待裁 · 18 处 `CLASSIFICATION_UNVERIFIED`
- 现场复尺：全部 NEW_WALL_LOCATION/OPENING_WIDTH/STAIR_SPAN 标 SITE_VERIFY
- SOFFIT_HEADER 施工归类人工复核
- 台阶踏面进深、封窗框料定位、门洞高度（未自动标注，不猜值）

## 冻结声明

技术开发层到此为止：差集/分类/QA 管线不再扩展。下一阶段（A201/A202/A302/A303）须先完成本手动的专业 CAD 验收，且仅以通过验收的 A102/A103 管线复用，不做新一轮 BIM 算法研究。
