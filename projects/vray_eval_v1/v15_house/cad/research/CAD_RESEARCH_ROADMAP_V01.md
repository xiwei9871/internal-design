# 室内设计施工图自动化：现状诊断、工具调研与实施路线 V0.1

- 日期：2026-10-18
- 输入：用户提供的 `cad.zip`（包含 6 张 DXF、20 个 Python 脚本以及 JSON/图片等中间数据）
- 范围：C 型住宅设计流程的施工图改进；本报告不是施工审图意见。
- 总结：**保留 FreeCAD/Blender/渲染链路；单独建设「工程语义数据 → CAD 出图 → 机器核查 → CAD 可视检查 → 人审」体系。**

## 1. 已核实的现状

| 图号 | 图纸 | Modelspace 实体数 | 原生 DIMENSION | DXF 格式 | 备注 |
| --- | --- | ---: | ---: | --- | --- |
| A102 | 墙体拆改 | 345 | 0 | AC1032 | A-UNCERTAIN 有 38 个可见对象，A-SOURCE-REF 有 62 个可见对象；结构读取修复 6 处 |
| A103 | 平面布置 | 418 | 0 | AC1032 | 继承手绘尺寸线文字，暂无工程标注对象 |
| A201 | 天花布置 | 436 | 0 | AC1024 | 结构读取修复 9 处；格式与其它图不统一 |
| A202 | 地面铺装 | 682 | 0 | AC1032 | 地面分区部分通过 Blender 顶视图像素分割推断 |
| A302 | 电气点位 | 560 | 0 | AC1032 | 点位有表示，但本包不能证明与实际安装标高/回路一致 |
| A303 | 给排水点位 | 436 | 0 | AC1032 | 点位有表示，但本包不能证明与现场立管/排水坡度一致 |

补充：

1. 6 张图均指定毫米作为 DXF 单位；全部只有 Modelspace 实体，内置 `Layout1` 为空。该事实不等于无法打印，但固定纸张图框、出图比例和布局还不能由纸空间验证。
2. 字体样式 HZTXT 使用 macOS 系统的绝对字体路径 `/System/Library/Fonts/STHeiti Medium.ttc`，存在跨电脑字体替代风险。
3. 多个生成脚本引用 `/Users/xiwei/interior_design/projects/...` 的绝对路径，输入基准图等文件未随压缩包提供，因此当前无法完整重放生成流程或做 FreeCAD 对照。
4. `make_a201_v2.py` 自行用 `LINE` + `TEXT` 拼尺寸；`make_a202_v6.py` 使用像素语义和固定坐标处理材料、门槛石、地漏、标高。该数据可用作*视觉或概念验证*，不应直接作为施工交底依据。
5. 本轮 QA 识别 7 个 BLOCK、15 个 WARN（含规则选择），详见 `CAD_QA_BASELINE_V01.json`。可打开、没有不可修复 DXF 结构错误 ≠ 施工正确。

**重要边界**：压缩包没有现场最新复尺表、完整 FCStd/IFC 施工基准、建筑结构图、批准的施工材料/机电方案。故**尚未验证**墙厚尺寸正确性、门窗洞口真实位置、适老净距、实际排水可行性及图纸之间的几何一致性。

## 2. 推荐工具栈

| 角色 | 首选 | 作用 | 关键局限/测试 |
| --- | --- | --- | --- |
| 可追溯几何与语义 | FreeCAD BIM + 原始实测 DXF/FCStd | 墙、门、窗、台阶、房间的稳定 ID、三维几何、2D 精确投影 | FCStd 里若只有实体、没有门窗/房间语义，必须补中间层；FreeCAD/TechDraw DXF 导出有视图限制 |
| 图纸引擎 | ezdxf + Python/Shapely | 原生 DIMENSION、INSERT 块、MTEXT、层/线宽、图框、检查 | 不自带设计逻辑；必须从真实坐标锚定标注而非猜测 |
| 人审和交付预检 | QCAD Professional（优先 POC） | 实际 CAD 视图、中文字体检查、批量 PDF、图层开关、打印 | 付费，必须验证具体 macOS 版本和文件兼容性 |
| DWG 终验（按需） | BricsCAD / AutoCAD | 高兼容度 DWG、打印和人工编辑 | 许可证成本/平台和自动化接口需要单独验证 |
| BIM 研究分支 | Bonsai + IfcOpenShell | IFC 语义图纸、剖面标注研究 | 2D drafting 仍在演进，不作为当前关键路径 |
| 结构核查 | `ezdxf.audit()` + 自研 lint | 原生实体、图层、单位、尺寸规则、冻结状态 | 结构审计不能判断现场可施工性 |
| 图像/渲染 | Blender / Image2 / V-Ray | 视觉沟通、材料/光效确认 | **不能作为任何几何尺寸、材质边界、管线位置唯一来源** |

来源：
- FreeCAD BIM https://github.com/FreeCAD/FreeCAD-documentation/blob/main/wiki/BIM_Workbench.md
- TechDraw https://github.com/FreeCAD/FreeCAD-documentation/blob/main/wiki/TechDraw_Workbench.md
- TechDraw DXF 导出局限 https://github.com/FreeCAD/FreeCAD-documentation/blob/main/wiki/TechDraw_ExportPageDXF.md
- ezdxf DIMENSION https://ezdxf.readthedocs.io/en/stable/dxfentities/dimension.html
- ezdxf 审计 https://ezdxf.readthedocs.io/en/stable/drawing/drawing.html
- QCAD CLI https://www.qcad.org/en/products/qcad-command-line-tools
- Bonsai 图纸文档 https://docs-unstable.bonsaibim.org/guides/drawings/index.html

## 3. 最关键的系统架构改造

```text
         [现场实测 / 原始户型 / 结构限制]
                       |        禁止静默覆盖
                 measured baseline
                       |
          [FreeCAD 冻结的设计修订 FCStd]
                       +------[明确的设计参数/施工意图 YAML/JSON]
                       |           - status: verified / design_intent / to_verify
                       |           - source_file_hash / revision
                       |           - object_id / room_id / elevation / material
                       v
           [Construction Semantic Registry]
                   |      |       |
                墙/窗   灯具    材料/地漏/门
                   +------v-------+
                    精确 2D 投影
                          |
                [版式与 CAD 引擎 ezdxf]
                   几何、尺寸、符号块、索引
                          |
              [DXF + 可打印 PDF + 清单]
                          |
               [自动 QA / 跨图检查]
                          |
             [QCAD/AutoCAD 实际打开复核]
                          |
                [现场/设计师人工审定]
```

**具体政策**：
- FreeCAD/实测数据是**尺寸/几何的可信输入**。Blender 场景可以传递设计意图，但渲染图的像素值不是可测量的建筑数据。
- 所有对象带稳定 `source_object_id`，图纸引用该 ID；所有尺寸必须按两端几何锚点计算，而非在图纸里手动填写数值。
- 每张图固化输入快照、源文件 SHA256、设计修订、CAD 引擎版本、标准配置版本。未满足输入条件则 `BLOCK`，不得悄悄填充一个“合理值”。
- 对 `status=to_verify` 的结构墙、门窗洞口、排水接驳、现场标高等节点，施工交付前必须有明确批准或保持 HOLD。

## 4. 应当落实的 CAD 制图约束

### 图面约束
- 统一 DXF 版本、图层名称及语义、线型/线宽、汉字字体替代、尺寸样式、图块、图例、编号、标题栏、比例和出图纸幅。
- 施工定位尺寸使用原生 `DIMENSION`，不能仅以 `TEXT` + `LINE` 拼接替代；标注值由两端锚点计算。细部局部尺寸与总尺寸交叉检查。
- 图层区分 EXISTING、DEMOLISH、NEW、SOURCE_REFERENCE、UNVERIFIED，并对后两类在正式施工交付中实行强制可见性 Gate。
- 安装点位统一成 `INSERT` 图块 + 属性（设备 ID、型号、安装高度、墙/天花依附对象、房间、回路/管路 ID），避免不同图纸重复画符号后失联。
- 图框、比例、图名、索引、版本、审校状态在交付前必须可查询；生成 PDF、校验字体及落点。

### 工程语义约束
- 墙体拆除/新建、门窗洞口、净距以及防水边界必须与对应实体/设计意图一致；未经确认的承重属性不可从视觉结果推断。
- 天花设备位置与设计灯光方案建立明确映射；但效果图照明强度、太阳、补光面板不是实际安装灯具，必须排除。
- 地面铺装用明确的房间地面面层/铺法/门槛规则生成，不允许从 Blender 顶视图渲染像素推测材料边界。
- 强弱电、给排水：点位图不自动等于回路/管路施工图。需要设备型号、标高、施工走向、接驳点、维护空间、冲突关系等额外数据。
- 局部节点及索引：主卫适老淋浴、次主卧新增套卫、防水排水、错层/台阶/缓坡、门槛、落地窗与柜体关系，需要独立详图与人审。

### 规范依据
- 《房屋建筑制图统一标准》GB/T 50001-2017（住房城乡建设部正式 PDF：https://www.mohurd.gov.cn/file/old/2017/20170930/GBT%2050001-2017%20%E6%88%BF%E5%B1%8B%E5%BB%BA%E7%AD%91%E5%88%B6%E5%9B%BE%E7%BB%9F%E4%B8%80%E6%A0%87%E5%87%86.pdf ）
- 《建筑制图标准》GB/T 50104-2010
- 《房屋建筑室内装饰装修制图标准》JGJ/T 244-2011
- **重要**：以上为制图标准研究入口；建筑/结构/消防/电气/给排水/适老化/防水等适用规范须按所在地、项目审批要求确认。本文**没有**根据标准全文确立所有必需线宽、标高、容差、节点做法，也不代替专业审图。

## 5. 推进优先级与预计工作量（人日级估算，需 Codex 勘察后校准）

| 阶段 | 先决条件和工作 | 验收 |
| --- | --- | --- |
| P0 / 0.5–1 日 | 从真实项目定位输入 DXF/FCStd、构建文件清单、哈希、对象 ID 清单；对现有 6 张执行 QA；将 `A-UNCERTAIN` 在正式输出变为交付阻断项 | 来源可追溯、旧产物未覆盖 |
| P1 / 1–2 日 | 建立统一 CAD style、可编辑图框/图块/原生尺寸；只试 A103 | A103 能以原生标注重新生成；图层一致；QCAD 可读 |
| P2 / 2–3 日 | A102 拆改图与设计模型墙体差集；禁止手工猜结构状态 | 拆除/保留/新建墙体 ID 可追溯，所有未核实对象进入 HOLD |
| P3 / 2–4 日 | A201 天花灯具/高度，A202 地面材料边界的语义抽取；与渲染灯光脱钩 | 灯具清单/平面一致，地板分区不依赖像素分割 |
| P4 / 3–5 日 | A302/A303 点位 ID、安装标高、关联墙/洁具/设备；评估补齐回路和管线图 | 每点有依据，缺失工程参数明确 HOLD |
| P5 / 1–2 日 | 批量 PDF、中文字体、线宽打印、回归测试、专业人审与发布 Gate | QA 无 BLOCK、纸张打印核对通过、人工签审 |

说明：可以先做 P0–P1 的小范围 POC，避免 6 张重构后才发现 CAD 兼容性问题。P2–P5 是研发规划，不保证自动解决所有现场问题。

## 6. 第一轮自动 QA 的明确边界

已经验证的：读取、实体类型、图层开关、毫米单位、DXF 基础审计、布局数量、字体路径；生成一个可重新读取的原生尺寸标注样例。`cad_qa.py` 不修改输入文件。

未验证的：与 FCStd 一致性、人工图纸预览中的遮挡细节、打印后的字号/字体、现场建造可行性、真实项目中的设计变更传播。下一个任务优先补上这些能力。
