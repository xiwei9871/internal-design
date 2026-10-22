# 客厅结构修正 V1

2026-10-01 · 客厅修正候选（HUMAN_REVIEW）。本模型继承已确认厨房冻结V1，供继续讨论客厅。

## 红框蓝色板的身份

红框蓝色板确实是次主卧斜门D-107（D-SM），对象名`LEAF_D107`，蓝色原本是实心门审阅色，不能据此判断为玻璃。原生成器把顶点烘焙到世界坐标、归零对象位置后，赋26.3°旋转，使门扇绕世界原点移到贵妃椅旁。

本轮按原登记铰链(8332,4543,450)恢复门扇与五金位置，保留850×40×2100包络和26.3°角度；修正平移约(+2998,−3371,0)。新门扇采用实心门审阅色。原错误代理隐藏保留，未写回B0。新门扇位置对应绿框的次主卧门洞。

## 本次三处修正

| 部位 | 新模型行为 |
|---|---|
| 客厅飘窗 | 室内洞口通向外挑平台，前端外窗及两侧返窗围合；重复内层平窗和外端整高挡墙停用。平台、下部实体及顶侧围合补齐 |
| 客厅—客卫分隔墙 | 保留CAD墙带XY，恢复到客卫上层吊顶3250；客厅侧吊顶仍2800。连续墙体留在完整模型与检查图中 |
| 次主卧斜门 | 恢复到登记门洞及原铰链，离开贵妃椅范围；五金同步修正 |

飘窗结构关系以三张现场照片为准，XY及投影继承原CAD/登记。室内洞口跨度3100、登记外挑900，窗台450、窗顶2400为本轮沿用值；照片未用于新增尺寸测量。外窗分格为可读审阅比例，栏杆、暖气及五金的精确细节留待对应深化。

## 正式检查入口

- [新全屋模型（包含冻结厨房）](/Users/xiwei/interior_design/projects/c_type_home/design/living_correction_v1/B1_LIVING_CORRECTED_V1.blend)
- [修正/来源清单](/Users/xiwei/interior_design/projects/c_type_home/design/living_correction_v1/LIVING_CORRECTION_MANIFEST.json)
- [独立重开校验](/Users/xiwei/interior_design/projects/c_type_home/design/living_correction_v1/LIVING_CORRECTION_QA.json)
- [现场依据与错误来源](/Users/xiwei/interior_design/projects/c_type_home/design/living_correction_v1/reference_notes.md)

检查图采用Workbench1600×1200、32级抗锯齿、Standard色彩管理、简单审阅材质。玻璃面与吊顶在出图时临时隐藏，以看清结构；窗框和完整墙体保留，未剖短墙。07图额外隐藏遮挡平台的家具。临时可见性设置不写回母版。

| 图 | 内容 | 文件 |
|---|---|---|
| 01 | 客厅朝飘窗正面 | [LIVING_01.png](/Users/xiwei/interior_design/projects/c_type_home/design/living_correction_v1/renders/LIVING_01.png) |
| 02 | 飘窗平台与侧窗 | [LIVING_02.png](/Users/xiwei/interior_design/projects/c_type_home/design/living_correction_v1/renders/LIVING_02.png) |
| 03 | 完整客厅—客卫墙 | [LIVING_03.png](/Users/xiwei/interior_design/projects/c_type_home/design/living_correction_v1/renders/LIVING_03.png) |
| 04 | 全屋俯视与门扇定位 | [LIVING_04.png](/Users/xiwei/interior_design/projects/c_type_home/design/living_correction_v1/renders/LIVING_04.png) |
| 05 | 客厅轴测、完整墙体 | [LIVING_05.png](/Users/xiwei/interior_design/projects/c_type_home/design/living_correction_v1/renders/LIVING_05.png) |
| 06 | 次主卧门洞及门扇 | [LIVING_06.png](/Users/xiwei/interior_design/projects/c_type_home/design/living_correction_v1/renders/LIVING_06.png) |
| 07 | 飘窗平台结构（家具暂隐） | [LIVING_07.png](/Users/xiwei/interior_design/projects/c_type_home/design/living_correction_v1/renders/LIVING_07.png) |

厨房272个保护对象的网格、坐标、材质、层级、修饰器、可见性及相机与冻结V1一致。全部B0及厨房冻结文件哈希复核；仅在新B1副本中停用已确认错误代理并建立对应纠正层。

复核：独立重开新模型；检查内洞口通向外端玻璃、左右侧窗射线；核对分隔墙精确XY与完整Z；核对D-107中心、角度和客厅家具范围；核对厨房保护对象和所有冻结源哈希。隐藏历史代理在重新打开时Blender不计算`matrix_world`，因此检查其网格、原始变换和父级；活动对象精确比较世界矩阵。

所有检查图、照片及代理保存到项目文件系统，聊天只返回路径。
