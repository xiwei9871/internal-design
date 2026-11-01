# CD_V01 A301–A303 水电·照明控制·网络示意图（SCHEMATIC）

日期：2026-11-01 · 分支：`cd-mep-a301-a303-v01`（基于 `a201-lighting-review-v01`）
深度：**示意级**。所有点位 `PROPOSED`，源头位置、物理回路、吊顶内净空、竖向下引均为 `TBD / SITE_VERIFY_REQUIRED`，不是施工定案。排水 `OUT_OF_SCOPE`（业主自行处理）。

## 图纸（`projects/c_type_home/cad/construction_docs/`）

| 图 | DXF | PDF | 预览 |
|---|---|---|---|
| A301 吊顶内管线路由示意 | `issue/A301_吊顶管线路由示意.issue.dxf` | `.issue.pdf` | `preview/A301_吊顶管线路由示意_full.png`、`A301_crop_upper.png` |
| A302 电气·照明控制·网络点位 | `issue/A302_电气照明控制网络点位.issue.dxf` | `.issue.pdf` | `preview/A302_电气照明控制网络点位_full.png`、`A302_crop_mother_bath.png`、`A302_crop_kitchen.png` |
| A303 给水点位（冷热水） | `issue/A303_给水点位.issue.dxf` | `.issue.pdf` | `preview/A303_给水点位_full.png`、`A303_crop_baths.png` |

数据：`data/mep_points.json/csv`（点位、来源对象、下引方式、所属干线）、`data/mep_routes.json`（示意路由段、交叉点）。
脚本：`mep_points.py`（点位表）、`make_mep.py`（生成与 QA）。

## 输入

- 灯位与逻辑场景组：`data/lighting_points_v2.json`（PR #14，`control_group`；`physical_circuit_id` 全部为空）
- 房间分区：A202；洁具/家具坐标：模型清单（`WHOLE_HOUSE_CORRECTED_SUPPORTED_V2.blend`，只读）
- 业主决定：水电网走吊顶、墙面不开槽；夜灯感应 + 手动兜底；床头灯壁装可调式（均 PROPOSED）

## 内容

| 项 | 数量 | 说明 |
|---|---|---|
| 给水点 | 22 | 厨房水槽/净水、三卫台盆/马桶/淋浴、书房茶水台、阳光房洗衣机、阳台备用 |
| 插座/设备/网络点 | 58 | 按床头柜、电视柜、书桌、台面、吊柜等真实对象定位；含 2 个紧急呼叫（母亲床头、主卫厕位旁） |
| 开关 | 20 | 每个开关列出所控场景组；双控/床头开关含夜灯手动兜底 |
| 感应器 | 5 | 随夜灯，PROPOSED |
| 场景组覆盖 | 31 组 | 每组至少有 1 个开关；夜间组同时有感应器和手动开关 |
| 示意路由长度 | 强电 112.8 m、弱电 49.9 m、冷水 66.0 m、热水 45.2 m | 仅示意，不是材料量 |
| 水电交叉 | 45 处 | A301 品红圈；水下电上，间距/套管由施工方定 |
| 跨吊顶高差 | 1 处 | 在 x=8000 电视墙附近（2650→3100），需开孔或绕行，结构许可待定 |

路由避开了楼梯区和 x<8000 上区地面这两块原顶无吊顶的区域（QA 检查 `ROUTE_IN_NO_DROP_ZONE` = 0）。

## QA（`qa/mep_qa.json`、`qa/a30x_sheet_qa.json`、`qa/a30x_text_overlaps.json`）

| 检查 | 结果 |
|---|---|
| 点位在房间内、状态只为 PROPOSED/TBD、不声称物理回路 | PASS |
| 淋浴区内无插座；距本房间淋浴区 <600mm 的插座提示 | 1 项 FLAG：客卫 S42 距淋浴 594mm，防溅型，分区由电气判定 |
| 每个场景组有开关；夜间组有感应 + 手动兜底 | PASS |
| 路由不进入无吊顶区 | PASS |
| 出图检查（R2010、字体、A1 图框、图层、尺寸值、锚点、实体数） | 三张均 PASS |
| 文字重叠 | 三张均 PASS |
| QCAD 界面复核 | NOT_RUN |

## TBD / SITE_VERIFY_REQUIRED

| 项 | 现状 |
|---|---|
| 强电配电箱、弱电箱、给水入户/水表/总阀 | 位置未知，图中为品红 TBD 占位（入户门旁 / 生活阳台） |
| 热水器 | 假定在生活阳台，型式待定 |
| 吊顶内净空、龙骨、梁位 | 未实测；150 下返不代表管线可全部装下 |
| 物理回路、开关接线、灯带驱动、大功率回路容量 | 未定；`circuit` / `switch_id` 为 `SCHEMATIC/TBD:` |
| 竖向下引 | 家具背板下引为 PROPOSED；卫浴（假墙/包管）、隔墙空腔/明装线槽、地插垫层为 TBD；不开槽 |
| 浴室电气分区 | L023、L033 及卫浴插座由电气专业判定 |
| H2–H4 门位 | 次主卫、客卧相关开关为 TBD |
| 排水 | OUT_OF_SCOPE |
