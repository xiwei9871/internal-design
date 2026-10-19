# B1 — CAD 制图表达差距分析

对照：上游 `house-plan-designer` DXF 导出（template.html 内手写 DXF writer）
vs 我们 `A102_WALL_DIFF_POC_V3.dxf` / `A103_CONSTRUCTION_POC_V7.dxf`（HUMAN_CAD_REVIEW 最新版）。

## 逐项对比

| 研究项 | 上游做法 | 我们现状 | 判定 |
|---|---|---|---|
| 多道尺寸链 | 三道（洞口/轴线/总尺寸）、装修四道（+墙厚净距） | 34 个语义化原生 DIMENSION（拆除跨度/定位/台阶/门宽），但**无分链排列、无总尺寸链** | 需要适配本项目——我们的语义标注更优，但缺"外围多道尺寸链"形式 |
| 原生 DIMENSION | 真 `AcDbAlignedDimension` + `*D` 匿名块，可编辑 | 同（ezdxf add_linear_dim，34 条） | ✅ 已具备，且我们多 XDATA 语义字段 |
| 文字覆写 | 未使用（值=几何） | 未使用 | ✅ 一致（这是优点：覆写=审计风险，见 Part A D1 测试） |
| 线宽 | group 370 分层 | 部分分层（A-WALL 50/A-DIMS 18/A-FURN 13 等），大量层 -3 默认 | 值得直接借鉴——已并入 POC 线宽表 |
| 轴线 | AXIS（CENTER 线型）+ AXIS-NUM（圈号）自动生成 | **完全没有轴网** | 需要适配——已 POC 实现（从墙中线推导，纯标注） |
| 门窗表达 | M/C 编号规则 + 门窗表 | 有 `SYM-DOOR-LEAF`/`SYM-WIN-SPAN` 块参照（9+1），**无编号文字、无门窗表** | 需要适配——已 POC 加 M1-M9/W1 编号；门窗表待做 |
| 图框标题栏 | 中文字段（工程名称/图名/比例/日期/单位/图号），但**画在模型空间** | 纸空间 A1 + 1:50 视口 + 2 行标题文字 | 我们更规范（真纸空间）；POC 补全中文字段 |
| 文字字体 | SHX 方案 `gbenor.shx+gbcbig.shx`（经典但依赖字体文件分发） | TTF（OpenSans/Liberation 族），中文靠系统字体 | 不适合采用——SHX 大字体换机器易缺字，TTF 更稳；我们的中文渲染已验证 |
| 线型 | CENTER/DASHED 按需创建 | 已加载全套（CENTER/DASHED/PHANTOM…），轴线层未用 | POC 已启用 CENTER |
| 图纸空间 | LAYOUT 占位（A3），图框实为模型空间放大绘制，无视口 | 真 Layout1 纸空间 + 780×520@1:50 视口 + A1 图框 | ✅ 我们明显更规范 |
| 填充 | ANSI31（拆除/新砌区分） | 无实体填充（HATCH），拆除用红色+叉线表达 | 可选借鉴：拆改图加 ANSI31 斜纹增强打印辨识度 |
| 追溯 | 无 | DEVINSRC/DEVINDIM XDATA | ✅ 我们独有，不受影响 |
| DXF 兼容性 | R12-风格手写，无 AUDIT 风险声明；首版曾有 handle 冲突隐患（我 POC 也踩过 dimblk 生成 _OBLIQUE 块撞 handle，已修） | ezdxf 生成，audit 0 errors | 大体相当 |
| 打印验证 | 无 | 原生 PDF 渲染 + 1:50 视口校验脚本 | ✅ 已具备；专业编辑器验证双方均 NOT_RUN |

## 分类汇总

- **已具备无须改动**：原生可编辑 DIMENSION、真纸空间视口、XDATA 追溯、TTF 字体、冻结层留痕、门弧块
- **值得直接借鉴**：分层线宽完整体系；图框中文字段补全
- **需要适配本项目**：轴网（我们无设计院轴号来源，只能几何推导——POC 已演示）；
  门窗编号（按块参照生成，POC 已演示）；多道外围尺寸链（需新排布逻辑，工作量中等）；
  门窗表（需要洞口宽高等结构化数据，建议下一步做）
- **不适合采用**：SHX 大字体方案、模型空间图框、其 HTML/JS 整体导出管线
- **需专业 CAD 验证**：GB dimstyle 在各 CAD 的渲染、CENTER 线型比例、中文 TTF 在 AutoCAD/浩辰的替换行为、1:50 打印实测

## POC 实现（`make_style_poc.py`，纯样式）

- 图层线宽规范化（墙 0.50/拆除 0.35/门窗 0.25/尺寸 0.13/家具 0.13/文字 0.25/轴 0.13）
- 新增 `AXIS`（CENTER 线型）+`AXIS-NUM` 层，从墙中线推导轴网（竖轴 1..n、横轴 A..n，外伸 1800mm+圈号）
- 门窗编号 M1–M9、W1（新层 `A-DOOR-NUM`/`A-WIN-NUM`，锚定现有块参照位置）
- 纸空间标题栏 7 个中文字段
- 新增 `GB` DIMSTYLE 定义（斜杠起止、dimtsz=140）供后续标注使用，**未改任何现有 DIMENSION**

全部新增实体登记在 `style_poc_manifest.json`（A102 +21 项 / A103 +31 项逻辑项）。
