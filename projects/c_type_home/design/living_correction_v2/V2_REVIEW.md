# 两处门洞围合修正 V2

2026-10-01 · HUMAN_REVIEW。当前全屋讨论入口为[新模型](/Users/xiwei/interior_design/projects/c_type_home/design/living_correction_v2/B1_LIVING_CORRECTED_V2.blend)，继承已确认厨房及客厅V1修正。

| 部位 | 完成本轮修正 |
|---|---|
| 次主卧D107斜门 | 保留已纠正的门扇、铰链位置和26.3°角度；增加左右木门框、三边门套、门上实体墙、两侧接墙及顶部梁形连接。门扇处在完整门洞里 |
| 客厅到北阳台门 | 补齐北侧墙垛y12650–13000.2并接入原墙角；门上填墙至2800；保留南侧完整墙。按现场关系替换为黑框单扇玻璃门，补门套、扇框、阈框、铰链和把手 |

次主卧围合到上层吊顶3250，北阳台门围合到下层吊顶2800。门的位置/主体跨度/高度继承登记，照片确认实体关系；门框、门套及梁形截面属于审阅尺寸，需现场复尺。它们不作为结构工程或加工尺寸的确认。

上轮V1确实只修了门扇位置而未补足完整次主卧门洞；北阳台门上横块也缺北侧完整接墙。本轮先在V1复现了这两处缺口，再检查V2的门上墙、门框和墙垛。14个检查点通过，独立重开965个对象状态通过，厨房272保护对象保持一致；V1、厨房冻结包及B0源文件哈希保持一致。

## 查看结果

| 图 | 内容 | 路径 |
|---|---|---|
| 01 | 次主卧门框和完整门上墙 | [DOOR_ENCLOSURE_01.png](/Users/xiwei/interior_design/projects/c_type_home/design/living_correction_v2/renders/DOOR_ENCLOSURE_01.png) |
| 02 | 次主卧门洞顶部与两侧接墙 | [DOOR_ENCLOSURE_02.png](/Users/xiwei/interior_design/projects/c_type_home/design/living_correction_v2/renders/DOOR_ENCLOSURE_02.png) |
| 03 | 客厅侧看北阳台门 | [DOOR_ENCLOSURE_03.png](/Users/xiwei/interior_design/projects/c_type_home/design/living_correction_v2/renders/DOOR_ENCLOSURE_03.png) |
| 04 | 阳台侧看门周边墙体 | [DOOR_ENCLOSURE_04.png](/Users/xiwei/interior_design/projects/c_type_home/design/living_correction_v2/renders/DOOR_ENCLOSURE_04.png) |
| 05 | 北阳台门头及墙垛轴测 | [DOOR_ENCLOSURE_05.png](/Users/xiwei/interior_design/projects/c_type_home/design/living_correction_v2/renders/DOOR_ENCLOSURE_05.png) |

Workbench简单材质，1600×1200；墙体、门头和新门扇均完整显示，没有剖切墙体。原整屋吊顶和不相关玻璃在检查图中暂隐，门洞顶部围合保持可见；可见性处理不写回模型。完整模型可继续在Blender中自由查看。

## 校验与依据

- [校验报告](/Users/xiwei/interior_design/projects/c_type_home/design/living_correction_v2/V2_QA.json)
- [V1缺口复现](/Users/xiwei/interior_design/projects/c_type_home/design/living_correction_v2/V1_DOOR_ENCLOSURE_FAILURE.json)
- [修正清单](/Users/xiwei/interior_design/projects/c_type_home/design/living_correction_v2/V2_MANIFEST.json)
- [现场关系和审阅值记录](/Users/xiwei/interior_design/projects/c_type_home/design/living_correction_v2/reference_notes.md)

原V1及冻结文件保留，本轮新模型为待业主审阅的V2。CONTEXT SIZE RULE继续生效：图像在文件系统保存、交付只返回路径，高分辨率原图按需少量检查。
