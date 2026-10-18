# Codex 任务书：C 型住宅施工图生成体系 P0–P1（V0.1）

## 角色与目标

你是本项目的 CAD/FreeCAD 工具链工程师。任务不是重新装修设计、不是生成效果图，而是把既有施工图脚本升级为 **可追溯、可编辑、可审查的工程出图管线**。

**当前已知起点**：对 6 张现有 DXF 检查，全部没有 DXF 原生 `DIMENSION` 实体，且内置 Layout1 为空；A102 的 A-UNCERTAIN 有 38 个可见实体、A-SOURCE-REF 有 62 个可见实体；A201 使用了不同 DXF 版本；原有脚本若干使用本机绝对路径；A202 利用顶视图图像分割反推材料区域。辅助脚本见 `cad_qa.py` 和 `CAD_QA_BASELINE_V01.json`。

**必须尊重已有设计冻结**：不擅自移动承重/非承重墙、门窗、卫生间、楼梯、家具，也不得把 Blender/渲染估算坐标当作现场测绘结果；保留原始文件和现有渲染产物。不得重启不相关 Blender/Image2/V-Ray 任务。

## 任务范围

### P0：只读调查、基线与输入可信性（先完成再编码）

1. 在实际机器上定位真实项目代码、原始实测 DXF、`WORKING.FCStd`、`WINDOW_RESTORED.FCStd`、批准的设计修订、当前出图脚本与材料/灯光设备数据。用户打包的 `cad.zip` 是分析样本，不保证包含所有源文件。
2. 形成 `cad/CONSTRUCTION_INPUT_MANIFEST.json`，记录相对路径、文件 SHA256、revision、单位、坐标系、对象数、来源性质（as_built / design / visual_only）、status（verified / design_intent / to_verify）。对缺项明确记录，不猜补。
3. 在独立分支运行 `cad_qa.py`，存入 `cad/qa/baseline_v01.json`。检查工程现有 FreeCAD 对象中墙/窗/门/楼梯/地漏/灯具有没有稳定 ID 和几何锚点。
4. 编制问题台账：分为图纸结构性、图纸交付表现、设计缺失、现场复尺待确认、安全/合规高风险 5 类；每个发现必须附图号、对象 ID、证据位置、严重度、解决路径。
5. 只读核对设计冻结约束：北阳台为 `OPEN_NOT_ENCLOSED`、高差约 450mm 且施工步高待实测、主卫适老、次主卧新增套卫、公共卫不扩大等。对于现场尺寸/结构冲突仅报告 BLOCK，不更改设计源。

**P0 Gate**：全部源文件找到或列出缺项；所有单位/变换有证据；有图号→工程对象→源文件的映射表；没有修改既有项目设计文件。

### P1：做一张 A103 原生 CAD 工程标注 POC

1. 建立公共 CAD 样式配置（建议 YAML 或 JSON）：统一 DXF 格式版本、图层及其状态、线宽、标注样式、纸张、比例、中文字体替代链、图框字段、图块和图纸编号。参数依据正式制图规范与项目约定，不能引用未经查证的“国标硬性值”。
2. 从 FreeCAD/verified 几何抽取墙轴、墙边、门窗洞口锚点等，生成 `cad/derived/geometry_v01.json`：每个锚点有 `source_object_id`, `revision`, `units=mm`, `evidence`。
3. 将 A103 的关键定位尺寸替换为真正的 DXF `DIMENSION`（ezdxf add_linear_dim()/add_aligned_dim()，调用 render()），避免只画 LINE+TEXT。标注文字应等于锚点真实测量值；重载 DXF 复算关键尺寸。
4. 将重用的门、窗、设备符号标准化为 `INSERT`/块，新增 `source_object_id`、`room_id` 等可追踪属性；不要要求一次迁移所有家具细节。
5. 输出**新文件** `A103_CONSTRUCTION_POC.dxf`、`A103_CONSTRUCTION_POC.pdf`（若本机 QCAD/可靠 PDF 工具可用）、`qa_report.json`、`object_mapping.csv`、变更前后截图。不得覆盖原图。
6. 运行与原图对比：对同一个测量锚点的数值误差，内部预设目标为 `<= 1mm`，这只是**管线计算一致性门槛**，不是现场施工公差；符号/标注文字不得由渲染图推断。缺少有效锚点则 HOLD，不创造坐标。
7. 真实用 QCAD 或可用 CAD 工具重新打开 DXF、检查原生标注可编辑、中文显示、打印比例和相同图层的线宽；命令行重载与实际 CAD 软件打开都要留下证据。

**P1 Gate**：A103 中关键标注为原生 DIMENSION，且被真实 CAD 编辑器确认；全部定位标注可追溯到几何锚点；输入修订变化时不会悄然使用旧坐标；QA 无 BLOCK；未改动旧产物。

### 后续候选（不要在 P0–P1 未验收时批量开始）

- A102：拆改墙体的留/拆/新建标签化，模型差集核对，所有 A-UNCERTAIN 对象强制 HOLD。
- A201：设计安装灯具清单与灯位一一关联；去除为了效果图设置的补光面光源、太阳光等；标注天花高度及结构条件。
- A202：铺装来源改为人工确认的房间材质分区与几何边界，禁止用像素识别作施工依据；完善起铺点、门槛与防水高差核对。
- A302/A303：建立设备块属性与安装标高/墙面/房间的绑定；如果缺回路、管径、坡度、检修空间等，标记为“需要专业设计”，不能假装点位图已经构成完整机电施工图。
- 补充节点图：主卫适老、次卫排水/防水、错层台阶与坡道、窗/柜体关系；各节点必须有索引及工艺/构造信息。

## 严格禁止

- 读取 Image2/V-Ray/Blender 光照/材质像素后自行发明墙体、材料边界、安装坐标。
- 自动判定承重墙允许拆除；绕过结构、消防、防水、给排水等专业审查。
- 使用 `TODO`、默认数值、固定坐标悄悄通过重要工程约束。
- 为了让 QA 通过，简单把图层关掉但不记录未核实对象的去向。
- 将 DXF 能打开、DXF audit 结构通过等同于施工可行。
- 同时改变 6 张图而不做单张可复现 POC。

## 必须完成的自动化测试

1. 基线读取：现有 6 张均可解析，检查脚本不会覆盖文件。
2. 原生标注回归：至少 1 张 A103 POC 含真实 `DIMENSION`，重新打开标注仍可编辑且与锚点距离一致。
3. 源文件校验：改变 `revision`/SHA256 必须触发重建或 BLOCK，不能使用过期几何。
4. 未确认对象：A-UNCERTAIN 的可见实体或未审状态必须引发 BLOCK。
5. 变更传播：仅在测试副本把一个门/墙锚点改动 100mm，依赖的尺寸应自动改变；生产模型不变。
6. 图层和字体：图纸打开无缺失中文，图框/比例/打印纸幅由人工核对并留证。
7. 停机规则：缺结构属性、洞口现场测量、施工标高/洁具设备资料时输出 HOLD 清单，不臆造。

## 交付要求和汇报格式

- Git 分支建议 `codex/cad-construction-p0-p1`；不要未经确认直接 merge main。
- 先发 `P0_REPORT.md` 与 `P1_SPEC.md` 供人工审核；P0 Gate PASS 后再实施 P1。
- 输出 `README_CAD_PIPELINE.md`、样例 DXF/PDF、配置 schema、生成器和 QA 测试、明确的人工待办。
- 最后汇报：已运行命令、通过/失败测试、图纸前后对比、真实 CAD 打开截图、未解决风险、是否建议进入 A102 扩展。
- 最终结论只允许 **PASS / HOLD / FAIL**；没有执行的验证必须写 NOT_RUN，不能写 PASS。

## 权威参考资料

- FreeCAD BIM 工作台：https://github.com/FreeCAD/FreeCAD-documentation/blob/main/wiki/BIM_Workbench.md
- TechDraw DXF 限制：https://github.com/FreeCAD/FreeCAD-documentation/blob/main/wiki/TechDraw_ExportPageDXF.md
- ezdxf 标注 API：https://ezdxf.readthedocs.io/en/stable/dxfentities/dimension.html
- ezdxf DXF Audit：https://ezdxf.readthedocs.io/en/stable/drawing/drawing.html
- QCAD 命令行工具：https://www.qcad.org/en/products/qcad-command-line-tools
- 住建部制图统一标准 GB/T 50001-2017：https://www.mohurd.gov.cn/file/old/2017/20170930/GBT%2050001-2017%20%E6%88%BF%E5%B1%8B%E5%BB%BA%E7%AD%91%E5%88%B6%E5%9B%BE%E7%BB%9F%E4%B8%80%E6%A0%87%E5%87%86.pdf
