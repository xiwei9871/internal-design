# SKILLS_UPGRADE_POC_V01 — CAD / Blender / MEP Skill 能力升级

日期：2026-10-31 · 分支：`skills-upgrade-poc-v01`（基于 `origin/improve/design-output-v14` `bd38f30`）
范围：升级 Skill 与配套 QA 脚本。不重写施工图管线，不修改任何冻结模型或实测 CAD。

## 1. 结论

| 项 | 状态 |
|---|---|
| 旧 Skill 的"渲染图分割地面/天花"规则改为真实几何优先 | PASS |
| 新增只读几何提取脚本（Blender，两次运行字节一致，模型哈希不变） | PASS |
| 新增 DXF 出图自动 QA 与分区覆盖/重叠/漏填 QA | PASS（15 项单元测试含负向测试） |
| `.claude/skills/` 入口（符号链接到 `.codex/skills/`，单点维护） | PASS（文件层校验）；会话内加载 NOT_RUN |
| A202/A201 升级前后 POC 对比 | PASS（指标见第 5 节） |
| 灯光与走顶 MEP 审核方法 | PASS（写入参考文档；不证明施工可行性） |
| 外部仓库许可证与安全检查 | PASS（只读 API 查看，未克隆、未执行任何外部代码） |
| QCAD 界面复验新 QA 结论 | NOT_RUN |

## 2. 新设计基准模型核对

模型：`projects/c_type_home/design/whole_house_model_v2/WHOLE_HOUSE_CORRECTED_SUPPORTED_V2.blend`
SHA256：`5a8bf58aaea0978147db40e1c7c68d57c27be6f9b254c9a6191ca7ef32c11801`（前后一致，只读）
明细：`results/model_check.json`

| 条件 | 结果 |
|---|---|
| C1 错层 450、三级台阶 | PASS：下层地坪 z=0，上层 z=450，STEP_0/1/2 顶面 150/300/450 |
| C2 天花 x=8000 跌级、下返 150 | DIFF_RECORDED：原顶 2800/3250 正确；模型高区在 x=5700–8000（楼梯区 4.7m²）向西延伸，低区在阳光房 x=8000–13100 向东延伸，交界不是单一 x=8000 直线；模型无下返 150 构造。CAD 按业主参数 x=8000 + 下返 150 表达 |
| C3 房间、门窗、洁具 | PASS_WITH_NOTES：11 个房间地面分区齐全；厨房水槽、三处台盆、次卫马桶/淋浴/地漏、茶水台盆、阳光房洗衣柜均在。主卫、客卫马桶按名称未找到，出 A303 前需按坐标区域查询 |

## 3. Skill 能力矩阵

状态：HAVE 已有可用 · UPGRADED 本轮升级 · NEW 本轮新增 · CONFLICT 与项目规则冲突 · GAP 仍缺失

| 能力 | 升级前 | 升级后 | 落点 |
|---|---|---|---|
| 地面分区来源 | CONFLICT：材质着色俯视渲染 + 像素分割 | UPGRADED：网格上表面三角形并集 | `blender-plan-geometry-extraction` |
| 天花分区来源 | CONFLICT：同上（A201 v2 读 `topmap.png`） | UPGRADED：网格下表面 + 共享边界=跌级线 | 同上 |
| 只读提取脚本 | GAP（散落在项目里，写死路径） | NEW：`scripts/extract_plan_geometry.py` inventory/extract | 同上 |
| 墙体来源 | HAVE：实测 CAD 底图 | HAVE，明确优先级：实测 > 开发商 > 业主决定 > 模型 | `interior-renovation-cad-docs` |
| 分区覆盖/重叠/漏填检查 | GAP | NEW：`scripts/zone_qa.py` | 同上 |
| DXF 出图 QA（版本/字体/图框/比例/实体保留/audit） | GAP（只在对话里人工查） | NEW：`scripts/dxf_sheet_qa.py` | 同上 |
| 中文字体规则 | CONFLICT：Skill 写 `HZTXT`+STHeiti 绝对路径 | UPGRADED：`gbenor.shx`+`gbcbig.shx`，禁止绝对路径 | 同上 |
| 图框与比例 | CONFLICT：依赖纸空间视口（QCAD 显示为空） | UPGRADED：模型空间 ×50 图框，复用 `publish_dxf.py` | 同上 |
| 尺寸标注 | HAVE：原生 DIMENSION（A102/A103 生成器） | HAVE；QA 未检查标注内容 | GAP：标注值与几何一致性校验 |
| 灯具点位 | HAVE：按用途审核（镜前灯、床头、柜下） | UPGRADED：统一点位数据字段，3000–4000K，Blender 只做副本预览 | `references/lighting-and-mep-review.md` |
| 走顶 MEP | GAP | NEW：审核清单（吊顶空间、交叉、下引路径、禁止暗中开槽、排水 OUT_OF_SCOPE） | 同上 |
| 施工可行性证明 | — | 明确不在 Skill 能力内，标 SITE_VERIFY_REQUIRED / HOLD | 两个 Skill |
| 验收标签 | GAP | NEW：PRELIMINARY_DESIGN_PASS / SITE_VERIFY_REQUIRED / HOLD | `interior-renovation-cad-docs` |
| DWG 读写 | GAP | GAP（未引入；交付 DXF + PDF） | — |
| Claude Code 发现入口 | GAP（仅 `.codex/skills/`） | NEW：`.claude/skills/<name>` → `../../.codex/skills/<name>` 符号链接 | `.claude/skills/` |

## 4. 外部仓库评估

均通过 GitHub API 只读查看元数据、文件树和关键文件，未克隆、未安装、未执行。

| 仓库 | 许可证 | 内容与依赖 | 可执行代码风险 | 采用方式 |
|---|---|---|---|---|
| `delancy827/cad-skills` | MIT | 2 个 SKILL.md；AutoCAD COM（`pyautocad`/`win32com`，仅 Windows）为主，`ezdxf` 为降级路线 | 示例脚本驱动本机 AutoCAD 进程 | 只借鉴方法：模型空间 1:1 mm、标准图层、输出前 L3 验证（对象数、关键图层、尺寸、文字存在性）。已体现在 `dxf_sheet_qa.py`。不引入 COM 路线（本机为 macOS，无 AutoCAD） |
| `RobLe3/cc-blender-skill` | MIT | 30+ Skill，依赖 Blender MCP（`execute_blender_code`） | MCP 可在 Blender 内执行任意代码，可能写回打开的模型 | 不采用。面向造型和渲染，不涉及平面几何提取；与"冻结模型只读"规则冲突 |
| `ProfRino/bonsai-bim-skills` | GPL-3.0 | 7 个 Skill + 245KB 辅助模块，依赖 Blender + Bonsai（IFC） | 未发现网络/子进程调用；但复制代码会带入 GPL-3.0 义务 | 不复制代码。记录其思路（图纸实体应是模型的一部分）作为远期 BIM 路线参考；现有模型为网格，不是 IFC 构件 |
| `constructelligence-lab/construction-agent-skills` | CC BY 4.0（API 显示 NOASSERTION，LICENSE 文件写明 CC BY 4.0） | 28 个纯文本 SKILL.md，无运行依赖 | 只有构建索引用的 `scripts/*.py` | 采用审核措辞与边界：`mep-coordination-clash-triage`、`constructability-risk-review` 的"区分真实冲突与建模噪声""间距来自规范不来自模型建议"。已注明出处 |
| `kasc0206/dwg-reader-skill` | MIT（字体库来源未单独声明） | 只读 DWG/DXF 解析；`ezdxf` + ODA File Converter；内置 322 个 SHX 字体约 159MB | `subprocess.run` 调用 ODA/LibreDWG；字体文件版权存疑 | 暂不引入。需要读外部 DWG 时再评估；不入库其字体包 |

## 5. POC：A202 / A201 升级前后对比

参考真值：新模型自身的地面/天花网格（`PRESENTATION_*` 房间地面 + 楼板剩余区，扣除 A103 V7 墙体）。
脚本：`poc_compare.py`；结果：`results/poc_metrics.json`。

旧方法输入是 V15 时期入库的 `topmap.png`、`seg_meta.json`、`plan_geom.json`。它们来自旧模型，
所以"材质"指标里包含新旧模型材质差异（例如生活阳台 V15 为木地板，V2 为瓷砖）。
"仅几何"一列不看材质，只衡量方法本身的边界误差。

### A202 地面

| 指标 | 旧：像素分割 | 新：真实几何 |
|---|---|---|
| 仅几何 IoU | 0.884 | 1.000 |
| 仅几何 漏填 / 溢出 | 9.34 / 9.11 m² | 0 / 0 m² |
| 仅几何 Hausdorff 最大偏差 | 1852 mm | 0 mm |
| 木地板 IoU / 瓷砖 IoU | 0.825 / 0.768 | 1.000 / 1.000 |
| 材质错分面积 | 6.83 m² | 0 m² |
| 覆盖率 <95% 的房间 | 生活阳台 0%、次卫 86.6%、客厅/餐厅/台阶 86.2% | 无 |
| 精度来源 | 9.96 mm/px 栅格 + 150 mm 简化 + 2 个写死的"设计意图"矩形 | 网格三角形 |
| 可复现 | 同一输入两次结果一致；但依赖人工渲染的 PNG | 两次提取 JSON 字节一致，可从 .blend 直接重跑 |

新方法的 `zone_qa.py` 还找出 6 处 >0.3 m² 的未覆盖区（合计 7.5 m²），包括主卫/母卧门前过道 2.25 m²。
这些是模型地面本身的缺口，旧方法会把它们静默吞掉或分错材质；新方法把它们列出来，按 Skill 规则补齐或标 HOLD。

### A201 天花

| 指标 | 旧 A201 DXF | 新：真实几何 |
|---|---|---|
| 标高 | 全部写 `H=2950` | 低区原顶 2800、高区 3250；下返 150 后 2650 / 3100 |
| 是否区分高低区 | 否 | 是，共享边界 8240 mm 作为跌级线 |
| 跌级线图层 | 无 | 由共享边界生成 |
| 覆盖低区 / 高区 | 68.4 / 80.2 m²（模型 74.4 / 90.1） | 74.4 / 90.1 m² |

### 出图 QA（`dxf_sheet_qa.py`）

| 文件 | 结果 | 失败项 |
|---|---|---|
| 旧 `A202_地面铺装图.dxf` | FAIL | R2018；HZTXT 绝对字体路径；30 处中文不可用字体；无 A1 图框 |
| 旧 `A201_天花布置图.dxf` | FAIL | HZTXT 绝对字体路径；79 处中文不可用字体；无 A1 图框 |
| `publish_dxf.py` 处理后的 A202 | PASS | — |
| `publish_dxf.py` 处理后的 A103 V7 | PASS | — |

## 6. Skill 文件与入口

- `.codex/skills/interior-renovation-cad-docs/SKILL.md`：重写。删除像素分割，加入来源优先级、QA 门、验收标签。
- `.codex/skills/interior-renovation-cad-docs/scripts/dxf_sheet_qa.py`、`zone_qa.py`：新增。
- `.codex/skills/interior-renovation-cad-docs/references/lighting-and-mep-review.md`：新增。
- `.codex/skills/blender-plan-geometry-extraction/SKILL.md`：重写；`scripts/extract_plan_geometry.py` 新增。
- `.claude/skills/<name>`：7 个符号链接，指向 `../../.codex/skills/<name>`。Claude Code 官方文档说明项目级 Skill 目录支持符号链接，
  并按目标去重加载。只维护 `.codex/skills/` 一份。
- `tests/test_skill_cad_qa.py`：15 项测试，含版本、绝对字体、`hztxt` 大字体、缺图框、出框、实体数、重叠、漏填的负向用例，
  以及入口链接与 Skill 头信息检查。

## 7. 未解决与后续

- C2 天花交界差异：模型与业主确认的 x=8000 不一致。施工图按业主参数画，差异已记录，未改模型。
- 新模型地面缺口 6 处（7.5 m²）：A202 正式出图时按墙体围合补齐，补不齐的标 HOLD。
- 主卫、客卫马桶需按坐标区域查询后才能出 A303。
- 尺寸标注值与几何的一致性校验仍是缺口。
- 新 QA 的结论未在 QCAD 界面复验（NOT_RUN）。
- 主工作区的 `.venv` 已不在，本轮在 `/tmp` 临时环境运行（ezdxf 1.4.5、shapely 2.2.0）。

## 8. 复现

```bash
blender -b MODEL.blend -P .codex/skills/blender-plan-geometry-extraction/scripts/extract_plan_geometry.py -- extract docs/skills_upgrade_poc_v01/extract_cfg.json /tmp/extract.json
python docs/skills_upgrade_poc_v01/poc_compare.py /tmp/extract.json /tmp/poc_out
python -m pytest tests/test_skill_cad_qa.py -q
```
