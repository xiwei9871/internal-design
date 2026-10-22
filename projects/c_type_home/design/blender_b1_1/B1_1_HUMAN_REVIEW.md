# B1.1 Design Model — HUMAN_REVIEW

`B1_1_DESIGN_MODEL = HUMAN_REVIEW`。本轮交付可审阅的候选，尚未获得人工批准。

冻结基线复核：**B0_INTEGRITY = PASS，7/7 SHA256 MATCH**。新模型从 B1 分支加载；176 个源对象的网格与变换保持一致。B0 文件及冻结 CAD / floor-region / Z / gate / field / V8 文件均未改动。

本轮建立 58 项家具／厨房柜体登记、4 个飘窗组合、9 处冻结玻璃开口的框体与 D-107 五金、三卫布局与三套 2000 mm 淋浴审阅屏、可编辑衣柜／书柜／收纳，以及楼梯与 r1000 曲边的标高内收口。厨房 PDF 尺寸优先；全部使用简单审阅材质。

## 打开结果

- [模型](B1_1_DESIGN_MODEL_V1.blend)
- [全屋俯视](B1_1_TOP.png) · [全屋轴测](B1_1_AXON.png) · [完整视图索引](B1_1_REVIEW_CONTACT_SHEET.png)
- [客厅](B1_1_LIVING.png) · [厨房](B1_1_KITCHEN.png) · [休闲厅](B1_1_LEISURE.png)
- [主人卧室](B1_1_OWNER_BED.png) · [母亲卧室](B1_1_MOTHER_BED.png) · [书房](B1_1_STUDY.png) · [客卧](B1_1_GUEST_BED.png)
- [三卫联系表](B1_1_BATHROOMS_CONTACT_SHEET.png)
- [资产登记](B1_1_ASSET_REGISTER.json) · [厨房登记](KITCHEN_CABINET_3D_REGISTER_V01.json) · [QA](B1_1_QA_REPORT.json)

审阅图临时降低墙体并隐藏吊顶、玻璃面与 site-ground helper，使家具、柜体和 split-level 关系可见；这些剖切**未保存到模型**。模型原建筑保持完整。默认关闭 `03_EXISTING_CEILING` 的集合可见性供审阅；开启即可查看原精确吊顶体块。`05_HUMAN_DESIGN_GUIDE` 保留并隐藏。

## 数值检查

| 检查 | 结果 |
|---|---|
| 冻结文件 SHA256 | 7/7 MATCH |
| 原对象网格和变换 | 176/176 保留 |
| 家具／柜体包络 | 48 项受检；最大误差 0.173 mm；门槛 1 mm |
| 新对象求值三角面 | 55,229 |
| 标高 | LOWER FFL 0 / ceiling 2800；UPPER FFL 450 / ceiling 3250 mm；stairs 150 / 300 / 450 |
| 冻结开口 | 9 处保留；D-107 原角度约 26.3° |
| 飘窗 | 4 组，保留原投影 XY；前侧干涉待复核 |
| 最终状态 | HUMAN_REVIEW |

以上是明确范围内的数值检查，不等于设计批准。朝向向量检查还依赖 V02 native-front 假设，需结合图片审阅。

## 优先人工裁决

1. **三个朝向冲突**：Rectangle032 生活阳台柜、西→北；Rectangle030 公卫台盆、北→东；Rectangle035 母亲卫台盆、东→南。V02 标记待复核，未收到批准。本模型保留无方向红色体块；不自动采用覆盖值。
2. **四个飘窗前侧干涉**：冻结前墙带在原场景中呈全高，与新增飘窗前玻璃审阅组合重叠。原平面 GLZ 也保留。仅报告，不切墙、不移动冻结开口；需对 frozen authority 的解释给出人工裁决，才可进一步实施。
3. **厨房安装与模块映射**：PDF 明确台面 820、吊柜深 380、总高 2410、冰箱 1700 × 905 × 710。东吊柜采用 620 面板 + 120 上封板（底 1670）；冰箱上柜采用 470 面板 + 10 封板（底 1930），替代旧登记册近似值。柜体 XY 保持登记拓扑。地柜/吊柜内部分柜、冰箱周围左右分隔、南侧水槽腿原点及上柜深度仍未确认；当前门板分隔和板厚为通用审阅细节。
4. **卫生间与设备**：三卫布局保留；淋浴精确 SKU、开启方式、管线接点／安装高度未确认。3 kg 洗衣机、打印机、NAS 的物理体块在 `COL_B11_PENDING_INSTALL` 隐藏，图中只显示 XY helper；不为它们猜安装高度。主人椅方向仍未定。
5. **家具候选与吊顶**：电视柜候选仍标 SIZE_DISTORTION，悬浮／落地最终方案未定；贵妃椅保留 V02 躺轴候选待审。吊顶仅继承精确原体块，灯槽／吊顶细节、梁／包管尺寸缺少确认，未擅自设计。

休闲厅剖切图还记录了冻结 D-107 下缘相对邻近 LOWER 地面的高差观感，以及原曲边 fascia / floor edge 的表面条纹。它们仅作 `REPORT_ONLY_SOURCE_OBSERVATION`，未改变已确认门扇姿态、层级或原网格。

其他内门尚缺已核实的净宽／门扇开向与五金尺寸；只细化 9 处冻结玻璃开口及 D-107，不从旧门符号包围框猜净宽。现阶段不提供管线施工确认、完整门扇碰撞、产品 SKU 保证或规范合规认证。

## 只读报告与可复现来源

原可变家具导引有世界原点旋转与旧负标高异常。该问题已记录，原对象未修复；B1 新对象按 V02 / 朝向登记册中的 CAD 目标矩形归一化，按冻结 datum 放置。不能把历史 350 / Pascal 700 mm 偏移带入 B1。

- 主生成脚本：`build_design_model.py`
- 独立检查：`validate_candidate.py`；结果：`B1_1_FRESH_OPEN_VALIDATION.json`
- 审阅图：`render_review.py`；视图与临时剖切：`B1_1_RENDER_MANIFEST.json`
- 打包：`package_review.py`
- 源观察：`reference_notes.md`；只读源快照：`SOURCE_SCENE_SNAPSHOT.json`
- 候选 SHA256：`31beb580133e81c64c92dc71d4bb1213f6b0b9151e013c1fa1d5fac2d33178bd`

已遵守无自动重设计范围：未移动房间／调整动线／拆墙／扩大客厅／实施 ramp；未来选项保持隐藏。未开始 final materials、final lighting、Cycles final rendering、AI exploration 或 web viewer。
