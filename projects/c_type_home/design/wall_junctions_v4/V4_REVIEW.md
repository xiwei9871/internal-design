# 全屋修订 V4

2026-10-01 · HUMAN_REVIEW。本轮已实际修改并保存到[完整模型](/Users/xiwei/interior_design/projects/c_type_home/design/wall_junctions_v4/B1_WALL_JUNCTIONS_CORRECTED_V4.blend)。后续整屋讨论从此版继续；V1–V3及厨房、B0原冻结包保留。

## 已处理

| 项目 | 模型结果 |
|---|---|
| 全屋墙体交界 | 活动墙体构成闭合连续墙壳，消除分段共面接口/重叠线和CAD转换细缝，统一审阅墙面材质。实际墙角、墙厚及分层标高保留 |
| 普通门 | 六处新增登记门组（含入户子母门），有门扇、门框、两侧门套、门上墙及左右围合。内门宽按原CAD750/850，入户350+750；高度2100为审阅值 |
| 书房门 | 按登记850mm门扇补齐原大缺口中的门套、门头和侧墙，没有把整个缺墙跨度作为门宽 |
| 客房玻璃移门 | 开口贯穿实际墙厚；框/门扇移到实际墙带中心Y11000，门所在位置没有挡墙；门套、轨道和围合补齐 |
| 休闲平台旁三轨门 | 补齐左右墙垛、门上实体墙及三边门套，保留已有门/轨道位置 |
| 全部飘窗 | 客厅方法扩展到次主卧、主卧、现书房：室内洞口通向外挑平台，玻璃在外端和两侧返窗；内层平窗和外端整高挡墙停用 |
| D107 | 保留V3门扇位置、26.3°及最终红侧50mm/蓝侧零额外墙垛关系；蓝侧门套仍连接转角实墙 |

永久门规则已写入项目[AGENTS.md](/Users/xiwei/interior_design/AGENTS.md)：普通门和推拉玻璃门均有门套，门套上方及左右连接连续实体墙，余墙宽度因位置而异。

## 检查图

十五张检查图及各门/飘窗入口见[视角索引](/Users/xiwei/interior_design/projects/c_type_home/design/wall_junctions_v4/V4_VIEW_INDEX.md)。主要检查：

- [全屋北侧轴测](/Users/xiwei/interior_design/projects/c_type_home/design/wall_junctions_v4/renders/WALL_JUNCTIONS_01.png)
- [书房门](/Users/xiwei/interior_design/projects/c_type_home/design/wall_junctions_v4/renders/WALL_JUNCTIONS_DOOR_D-STUDY.png)
- [客房移门](/Users/xiwei/interior_design/projects/c_type_home/design/wall_junctions_v4/renders/WALL_JUNCTIONS_GUEST_GLASS.png)
- [休闲平台旁移门](/Users/xiwei/interior_design/projects/c_type_home/design/wall_junctions_v4/renders/WALL_JUNCTIONS_LEISURE_GLASS.png)

Workbench1800×1350、32级抗锯齿、Standard色彩管理，简单审阅材质。整屋吊顶、玻璃面和非现状助手在检查图中暂隐，窗框、门套、门头、周边墙体完整保留，墙体没有剖短。图像临时可见性不写回模型。所有图像只以文件路径交付，已逐张查看少量512px代理。

## 校验及依据

独立重开1207个对象状态通过；连续墙壳6418顶点/8666面，开放边界0、非流形边0。335个未涉及授权门洞/飘窗修正的原外表面采样无丢失，最大偏差0.30mm；原内部共面接口已按预期移除。

六处新门的实际宽高及门套外左右/上方实体墙、11条门洞/飘窗净开口射线、三个新飘窗外端/侧端通透性均通过。D107门扇/门套及北阳台门保留。厨房266个非墙保护对象完全一致；6个原窗周/窗下墙网格与姿态保存为隐藏源，由连续墙壳继承表面。厨房柜体、设备、窗位置、尺寸和已确认布局保留；原冻结文件全部哈希一致。

- [独立校验](/Users/xiwei/interior_design/projects/c_type_home/design/wall_junctions_v4/V4_QA.json)
- [修订清单](/Users/xiwei/interior_design/projects/c_type_home/design/wall_junctions_v4/V4_MANIFEST.json)
- [逐门与逐飘窗登记](/Users/xiwei/interior_design/projects/c_type_home/design/wall_junctions_v4/OPENING_AND_BAY_REGISTER.json)
- [现场依据与尺寸精度](/Users/xiwei/interior_design/projects/c_type_home/design/wall_junctions_v4/reference_notes.md)

普通门宽来自CADF-DOOR登记，门高、门套截面、五金和未测梁截面仍为审阅尺寸，不能视为新现场测量。未开启最后材质/照明、施工加工放行或未来拆改方案。本版仍待业主审阅。
