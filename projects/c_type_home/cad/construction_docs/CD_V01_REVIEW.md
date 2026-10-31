# CD_V01 审图说明 — A202 地面铺装图 / A201 天花布置图

日期：2026-11-01 · 分支：`cd-a202-a201-v01`（基于 `skills-upgrade-poc-v01` `b0c6d32`）
验收口径：`PRELIMINARY_DESIGN_PASS` / `SITE_VERIFY_REQUIRED` / `HOLD`。本图为初步设计施工图初稿，不可不经现场复核直接施工。

## 1. 交付物

| 图 | DXF（R2010，A1 1:50，模型空间图框） | PDF | 预览 |
|---|---|---|---|
| A202 地面铺装图 | `issue/A202_地面铺装图.issue.dxf` | `issue/A202_地面铺装图.issue.pdf` | `preview/A202_地面铺装图_full.png` |
| A201 天花布置图 | `issue/A201_天花布置图.issue.dxf` | `issue/A201_天花布置图.issue.pdf` | `preview/A201_天花布置图_full.png` |

局部图：`preview/A202_crop_service_balcony.png`（生活阳台）、`A202_crop_vestibule_masterbath.png`（主卧/主卫前过道）、
`A202_crop_stair.png`（三级台阶）、`A201_crop_ceiling_step.png`（吊顶跌级）、`A201_crop_section.png`（错层剖面）、
`A201_crop_stair_nodrop.png`（楼梯区原顶不吊顶）。

数据：`data/a202_rooms.csv`（房间面积与材质）、`data/a202_gap_disposition.json`（缺口处置）、
`data/a202_tiles_doors.json`（排砖、门洞、HOLD）、`data/lighting_points.json/csv`（灯位）、`data/a201_ceiling_zones.json`（天花分区与标高）。
QA：`qa/*.json`；来源清单：`qa/source_manifest.json`。

生产脚本：`cd_common.py`、`make_a202.py`、`make_a201.py`、`sheet_checks.py`、`publish_dxf.py`（与仓库原版一致）。
`work/` 为未加图框的生成稿，`issue/` 为发布稿。

## 2. 来源

| 来源 | 文件 | SHA256 | 用途 |
|---|---|---|---|
| 设计模型（只读） | `design/whole_house_model_v2/WHOLE_HOUSE_CORRECTED_SUPPORTED_V2.blend` | `5a8bf58aaea0978147db40e1c7c68d57c27be6f9b254c9a6191ca7ef32c11801` | 房间分区、地面材质、洁具、家具、灯位参照 |
| 实测底图（冻结） | `cad/measured_working.dxf` | `3711c47c…`（与版本清单一致） | A103 的上游 |
| 平面底图 | `inputs/A103_CONSTRUCTION_POC_V7.dxf` | 见 `qa/source_manifest.json` | 墙体、门窗洞口、34 道尺寸 |
| 业主天花方案 | `vray_eval_v1/v15_house/cad/step_wave_p0/P03_CEILING_SCHEME_A.md` @ `0123a9d` | — | 跌级路径与标高 |
| 模型提取 | `inputs/plan_extract.json`、`inputs/model_inventory.json` | 见清单；提取记录的模型 SHA 与上表一致 | 网格上下表面三角形，非渲染图 |

模型前后哈希一致，未修改。

## 3. 设计决定（本图采用）

- 标高：下区地面 ±0，上区 +450；原顶 +2800 / +3250；吊顶下返 150，完成面 +2650 / +3100，两区净高 2650。
- 天花跌级按业主方案：`x=8000`（y 4700→10900），北端沿 `y=10900` 东延至 x 13100（P0.3.2 焊接条带路径）。南端在电视墙（x 7800–8000）内收口。**不采用**模型天花轮廓。
- 上区地面（+450）位于下区原顶（2800）之下的区域净高只有 2350，不吊顶，用明装灯（斜线区，4.31m²，含楼梯）。
- 生活阳台用 300×600 防滑砖（模型材质也是瓷砖），规格 `OWNER_REVIEW`。
- 卫生间统一 300×600 防滑砖；厨房、阳光房 600×1200；其余白蜡木地板南北向。规格均 `OWNER_REVIEW`。
- 主卫（母亲适老）门口不设凸起门槛，排水/挡水做法 `HOLD`（H1）。
- 房间命名：主卧（母亲）、次主卧（业主）、书房、客卧；主卫、次主卫、客卫。

## 4. A202 检查结果

| 项 | 结果 |
|---|---|
| 独立室内边界 | A103 墙+窗+门围合的封闭环，**无缓冲闭合**；室内 147.73m²（8 个房间环），另有 3 个飘窗凹位、1 个窄条不计地面 |
| 分区覆盖（zone_qa） | PASS：14 区共 147.70m²，重叠 0，>0.05m² 的漏填 0 |
| 木地板 / 瓷砖 | 109.40 / 38.30m²（明细见 `a202_rooms.csv`） |
| 出图 QA（dxf_sheet_qa） | PASS：R2010、audit 0、字体可移植、中文字体、A1 图框、内容在框内、7 个必需图层有可见图元、34 道尺寸值与几何一致、5 个实测锚点坐标命中、实体数 632=632 |
| 文字重叠 | PASS（79 条文字） |

### POC 6 处缺口处置

| 位置 | 面积 | 分类 | 处置 |
|---|---|---|---|
| (12250, 5900) | 2.25m² | 真实室内漏填 | 模型地面缺失；按 A103 墙体围合补为"主卧/主卫前过道"，+450 木地板，材质 `OWNER_REVIEW` |
| (4809, 109) | 0.87m² | 室外 / 算法误判 | 在墙线以南，不在封闭室内 |
| (2540, 3754) | 1.05m² | 算法误判 | 餐厅西墙 x=2700 以外，由 3000mm 缓冲闭合产生 |
| (3296, 14142) | 1.14m² | 室外（客厅飘窗） | 不计地面 |
| (15730, 3474) | 0.64m² | 算法误判 | 母卧东墙以外，由缓冲闭合产生 |
| (13459, 12670) | 1.53m² | 室外（书房东北飘窗） | 不计地面 |

另有 8 块模型地面剩余区（门洞、窗台内侧、台阶东侧等）并入相邻房间，见 `a202_gap_disposition.json`。

### 门洞（A103 共 9 处）

门槛石 4 处：入户、客厅→阳光房、走廊→客卫（平接+挡水）、餐厅→生活阳台。主卫 1 处平接 `HOLD`。连续铺装 4 处。

### 模型有门、A103 无洞口（`HOLD`，墙体按 A103 保留）

| 标记 | 模型对象 | 位置 |
|---|---|---|
| H2 | `R3_SLIDING_LEAF` | 次主卫北侧推拉门 |
| H3 | `V4_D-BATHM_LEAF_0` | 主卫—书房之间 |
| H4 | `V4_D-GUEST-ROOM_LEAF_0` | 客卧门（y≈7900） |

## 5. A201 检查结果

| 项 | 结果 |
|---|---|
| 天花分区覆盖（zone_qa） | PASS：16 区共 147.64m²，重叠 0，>0.3m² 漏填 0 |
| 出图 QA | PASS：同 A202 各项；11 个必需图层有可见图元 |
| 文字重叠 | PASS（71 条文字） |
| 与模型天花的差异 | 2 处：模型高区（3250）伸到 x 5750–7150 和 x 7400–8000 的楼梯区，共 3.83m²。CAD 按业主方案画为低区，模型未改 |
| 灯具 | 94 个：嵌入筒灯 72、防潮筒灯 13、镜前灯 3、踏步灯 3、明装射灯 1、餐厅吊灯 1、跌级暗藏灯带 1 段；3000–4000K |
| 灯位避让 | 9 个网格点因位于床正上方被去掉；距跌级线 <350、距检修口 <300 的点同样去掉 |
| 检修口 | 5 个 450×450：厨房、三卫、走廊 |
| 剖面 | 1-1 剖面示意（y≈6000，西→东）：三级台阶、x=8000 跌级、原顶与吊顶完成面 |

## 6. QA 脚本修补（本 PR）

- `zone_qa.py`：没有独立室内边界时，覆盖率记为 `NOT_RUN`，结果为 `PARTIAL`，不再给 PASS。
- `dxf_sheet_qa.py`：必需图层须有**可见**图元；线性尺寸的测量值、文字覆盖值与定义点距离比对；锚点坐标抽检（实体数不变但坐标被改也能发现）。
- `extract_plan_geometry.py`：可见性改为沿集合父链判断（父集合隐藏则不导出）；输出写入模型 SHA256、Blender 版本、提取器版本。
- 测试：`tests/test_skill_cad_qa.py` 20 项、`tests/test_skill_blender_extract.py` 4 项（真实 Blender 5.2.1：隐藏父集合、世界变换、下表面、来源哈希与只读），共 24 passed。

## 7. 未验证（NOT_RUN）

- QCAD 界面打开 `issue/*.dxf` 复核中文、图框、尺寸、比例：**NOT_RUN**，需业主在 QCAD 里看。
- 新 Claude Code 会话发现 `.claude/skills/`：**NOT_RUN**。`claude -p` 返回 `Not logged in`，无法在无头模式启动。
- 吊顶内龙骨、管线、梁位空间：**SITE_VERIFY_REQUIRED**。150 下返不代表管线能全部装下。

## 8. 未解决与现场复核

| 编号 | 事项 | 状态 |
|---|---|---|
| H1 | 主卫门口无凸起门槛，排水/挡水做法 | HOLD |
| H2–H4 | 模型有门、A103 无洞口的三处墙体是否开洞 | HOLD（涉及墙体拆改须结构核实） |
| — | 楼梯区与上区 x<8000 处原顶不吊顶，净高 2350，逐踏步净高 | SITE_VERIFY_REQUIRED |
| — | 主卧/主卫前过道 2.25m² 由墙体围合补齐，材质与标高 | OWNER_REVIEW / SITE_VERIFY_REQUIRED |
| — | 瓷砖、地板规格与排砖起点 | OWNER_REVIEW |
| — | y=10900 东延段跌级灯带：路径落在墙线上，本版只画了 x=8000 段 | 待 A201 下一版处理 |
| — | 所有面积为图面净面积，下单以现场复尺为准 | SITE_VERIFY_REQUIRED |
| — | 墙体拆改结构安全、拆除许可（沿用 A102 HOLD） | HOLD |

## 9. A301–A303 下一阶段输入

| 输入 | 来源 | 状态 |
|---|---|---|
| 天花分区、完成面标高、检修口 | `data/a201_ceiling_zones.json` | 就绪 |
| 灯位、回路建议、开关编号 | `data/lighting_points.json` | 就绪（OWNER_REVIEW） |
| 房间分区与地面标高 | `data/a202_zones.json`、`a202_rooms.csv` | 就绪 |
| 洁具坐标（按房间区域查询，非名称） | 主卫 `B11_Rectangle034_CATALOG_00_00`、客卫 `B11_Rectangle008_CATALOG_00_00`、次主卫 `R3_WC_LATEST`；台盆 `CBM_GUEST/MASTER_BASIN`、`R3_VANITY_BASIN_REVIEW`；厨房 `B11_K-SINK_BOTTOM`；茶水台 `R3_TEA_SINK_BOTTOM`；淋浴 `R3_SHOWER_TRAY/DRAIN` | 就绪 |
| 洗衣机位 | `SUNROOM_LAUNDRY_*`（阳光房） | 就绪 |
| 配电箱、弱电箱、水表/总阀位置 | 无可靠来源 | **缺**，需业主或现场提供 |
| 吊顶内可用净空实测 | 无 | **缺**，SITE_VERIFY_REQUIRED |
| 竖向下引方式（隔墙空腔/柜体背板/明装线槽） | 无 | 需业主确认，不得默认开槽 |
| 排水 | 业主自行处理 | OUT_OF_SCOPE |

## 10. 复现

```bash
blender -b WHOLE_HOUSE_CORRECTED_SUPPORTED_V2.blend -P .codex/skills/blender-plan-geometry-extraction/scripts/extract_plan_geometry.py -- extract inputs/extract_cfg.json inputs/plan_extract.json
python make_a202.py && python make_a201.py
python publish_dxf.py work/A202_地面铺装图.dxf issue --title 'A202 地面铺装图' --no A202
python publish_dxf.py work/A201_天花布置图.dxf issue --title 'A201 天花布置图' --no A201
```
