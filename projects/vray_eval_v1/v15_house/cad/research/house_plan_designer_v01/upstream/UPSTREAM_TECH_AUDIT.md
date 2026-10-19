# 上游技术审计 — house-plan-designer @ ab7bb1c

范围：`scripts/cadvec.py`（1451 行）、`scripts/dimtext.py`（266 行）、`scripts/cadsplit.py`（682 行）、
`assets/template.html` 内 DXF 导出（约 8229–8300 行按钮 + `HR`/EZDXF JS 写入器）、`reference/spec-format.md`、
`reference/cad-conventions.md`。只读审阅，未执行 SKILL.md 工作流。

## cadvec.py 实际机制（源码读到的，非 README）

1. **输入**：`.pdf`（`fitz.get_drawings()` 提取矢量图元）或 `.dxf`（ezdxf，含 INSERT 递归展开至 6 层）。
   DWG 不支持；位图走另一个脚本 `analyze.py`。
2. **尺寸刻度检测**：尺寸线 = "直线上落 ≥2 个 45° 短斜杠"（`is_tick_shape` + `_on_line`，
   斜杠按大小过滤，近心合并）；每个刻度再找垂直的尺寸界线（`feet`）——**界线另一头指向被量构件**，
   这是它"尺寸关联到构件"的关键，不只是读数字。
3. **标注数字三来源**：① 文字层直接读（`dims_from_textlayer`，要求刻度中点附近、垂直偏移在字高 2.5 内）；
   ② `dimtext.py` 字形破译（SHX/轮廓字聚类 + 用几何长度反投票数字）；③ DXF 原生 `DIMENSION`
   （`get_measurement()`，文字被改写时以文字为准）。
4. **加权最小二乘解算**（`build_axis`）：每个方向一张节点图，方程 xⱼ−xᵢ=标注值。
   权重 = 外侧尺寸中"分段越细权重越高"（`（段数/maxseg)²`，室内尺寸固定 0.02）。
   弱正则项把节点锚向原始比例坐标。迭代 4 轮剔除残差 >max(25mm, 2%) 的最坏方程并记 `conflict`。
5. **构件吸附**：墙/洞口边距某刻度 ≤15mm 时直接取该刻度 mm 值，刻度选择看尺寸界线是否伸到构件；
   否则节点间线性插值。
6. **输出**：`cad.json`（墙/门窗/dims 明细+conflict）、`draft.json`（HouseSpec）、`cad.png` 核对图。
   `--no-dims` 可关闭尺寸约束退回整体比例。

### 已识别的限制（对我们输入重要）

- **DIMENSION 处理粗糙**：只取 `defpoint2/defpoint3` 连线 + `get_measurement()`，按跨度方程处理。
  对 **ordinate 标注（dimtype 32）**，measurement 是坐标原点距（~10⁶ mm 量级），会被当成
  普通跨度方程注入，理论上会被离群剔除，但存在污染风险——实测验证。
- **必须存在 45° 起止符号**才能建立"尺寸线+刻度"；`A-DIMS` 只有尺寸线/界线但无斜杠的图
  （手工数字化的图常见画法）不会触发约束模式。
- 承重判定按颜色/厚度启发式，仅供参考。
- 墙识别依赖"实心填充"或"双线描边带"；单线墙、LWPOLYLINE 轮廓矩形需实测。

## dimtext.py

仅在无文字层时启用：收集尺寸线附近小图元 → 包围盒并查集成"字符" → 字形聚类 →
用刻度几何长度与候选 mm/px 比例做"哪个字形是哪个数字"的投票。位图不适用（只处理矢量图元）。

## template.html 内 DXF 导出（JS，手写 DXF 写入器，非 ezdxf）

实际审查后发现比预期完整：

- **原生 `DIMENSION` 实体**：`AcDbAlignedDimension`/`AcDbRotatedDimension`（dimtype 32|128），
  配合匿名 `*D` 块渲染标注图形——是 CAD 里可编辑的真标注，不是画的线。
- **DIMSTYLE 表**：`Standard` + `GB` 两种样式；GB 用建筑起止斜杠（oblique tick）、
  `@DIMSCALE@` 占位符按出图比例替换。
- **中文字体**：STYLE `HZ` = `gbenor.shx` + `gbcbig.shx` 大字体（国标 SHX 方案）——
  在未装这两款 SHX 的 CAD 里中文会缺字，稳定性存疑；我们现有图纸用的 TTF 方案反而更稳。
- **图层**：WALL/WALL-NEW/WALL-DEMO/WALL-HATCH/COLUMN/WINDOW/DOOR/DIM/AXIS(CENTER线型)/
  AXIS-NUM/FURN/ELEC/STRUCT/TITLE/FRAME/ROOM-TEXT 等，线宽用 group 370 分级。
- **三道/四道尺寸链**：`E.begin/end` 把每段标注图形收进匿名块；三道=洞口/轴线/总尺寸，
  装修版四道加墙厚净距。
- **标题栏**：中文字段（工程名称/图名/比例/日期/单位/图号）齐全。
- **短板**：图框画在**模型空间**按出图比例放大，LAYOUT 只有 A3 占位记录、无真正纸空间
  VIEWPORT；无 XDATA 追溯、无对象身份语义。打印比例验证 = NOT_RUN。

## 可复用性结论

| 模块 | 判断 | 说明 |
|---|---|---|
| `cadvec.py` 约束解算核心 | ADAPT | 最小二乘+权重+冲突标记可直接抽取（~150 行纯 numpy）；输入侧 tick/界线检测适配我们图层结构后要改 |
| `dimtext.py` | REJECT（现阶段） | 我们的 DXF 都有文字层或原生 DIMENSION，不需要字形破译 |
| `cadsplit.py` | ADAPT（未来） | 多层对齐逻辑，v15 单层用不上，复式/别墅项目可再用 |
| template DXF 导出 | ADAPT（部分） | 原生 DIMENSION+DIMSTYLE+三道尺寸链思路可借鉴；但模型空间图框、SHX 依赖、无纸空间/无 XDATA，整体低于我们现有水平 |
| `reference/cad-conventions.md` | ADOPT | 国标画法整理，可作我们图层/图例规范的校验清单 |

MIT 许可，vendor 目录保留 LICENSE。
