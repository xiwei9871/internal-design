# R3 修订与对比 · 2026-10-02

本轮按最后的明确指示，先撤回后来补建的斜门及门框、门套、门上墙、侧墙和转角连接，恢复到补门以前的开放状态，再按最新 FreeCAD 建完整西侧隔断。后加围合墙的七组来源已从活动墙壳中移除；原始黑色实墙没有打拆。固定基础文件和厨房冻结包完整保留，R3 是独立审阅分支。

书房采用参考图的自然木色和格架关系：长茶台后方是书柜，旁边低柜改成专用茶水台，带水槽、龙头、给排水示意、独立电热煮茶位及收纳。用户已选择保持 FreeCAD 家具位置；长茶台没有北移。

## 先看这几张图

- [撤回斜门 → 新建西墙，同角度顺序图](/Users/xiwei/interior_design/projects/c_type_home/design/secondary_bath_options/r3/renders/WEST_WALL_RESTORE_SEQUENCE.png)
- [A/B 同角度模型对比](/Users/xiwei/interior_design/projects/c_type_home/design/secondary_bath_options/r3/renders/AB_MODEL_COMPARISON.png)
- [A/B 同尺度平面和尺寸](/Users/xiwei/interior_design/projects/c_type_home/design/secondary_bath_options/r3/renders/AB_PLAN_COMPARISON.png)
- [书房木色格架与茶水台功能](/Users/xiwei/interior_design/projects/c_type_home/design/secondary_bath_options/r3/renders/STUDY_STYLE_AND_FUNCTION.png)

## 模型文件

| 状态 | 文件 | 用途 |
|---|---|---|
| 撤回围合、未建新西墙的中间状态 | [RESTORED_OPEN_STATE_BEFORE_BATH_R3.blend](/Users/xiwei/interior_design/projects/c_type_home/design/secondary_bath_options/r3/RESTORED_OPEN_STATE_BEFORE_BATH_R3.blend) | 核对恢复顺序；原浴室家具尚未替换 |
| A：南侧推拉门 | [OPTION_A_SLIDING_R3.blend](/Users/xiwei/interior_design/projects/c_type_home/design/secondary_bath_options/r3/OPTION_A_SLIDING_R3.blend) | 当前推荐比较分支，包含最新浴室布局和书房修订 |
| B：南侧向内平开门 | [OPTION_B_INWARD_R3.blend](/Users/xiwei/interior_design/projects/c_type_home/design/secondary_bath_options/r3/OPTION_B_INWARD_R3.blend) | 同一入口、同一洁具位置，包含相同书房修订 |

两案时间轴 1 帧为关闭、100 帧为开启。完整模型包含真实完整墙体；内部剖视仅在出图时临时剖切，不写回模型。原始来源对象隐藏保存，便于追溯；活动场景内已没有后加斜门和围合墙。

## A/B 取舍

| 比较项 | A 推拉门 | B 向内开门 |
|---|---|---|
| 南侧入口 | 衣柜西侧可达位置 | 与 A 相同 |
| 门扇收纳 / 开启 | 向东收入南侧墙后、衣柜背后的隐藏段 | 西侧铰链向内约85°，设置门挡 |
| 墙体、门套、门上墙 | 完整，轨道贯穿门洞及收入段，吊轮有连续净空 | 完整，有三处铰链和限位门挡 |
| 室内开门回转 | 0 | 含把手约 0.423 m² |
| 门扇与墙 / 台盆 / 马桶 / 淋浴 | 本轮运动检查通过 | 721 个角度采样通过；避免把手在90°时碰西墙 |
| 马桶前操作区（深800×宽600示意） | 门运动和实体墙不占用 | 门运动和实体墙不占用 |

推荐 A：在现有小空间中，推拉门保留内部操作面积，入口可达，隐藏段与衣柜关系正确。B 可作为密封和构造取舍的备选；本版使用85°限位。

## 最新布局依据

源文件为 [世纪欣园FF_freecad_WORKING.FCStd](/Users/xiwei/interior_design/projects/c_type_home/cad/freecad_import/世纪欣园FF_freecad_WORKING.FCStd)，实际读取 Shape.BoundBox 与 Shape.Vertexes；哈希 `d69004b9912eaa6021cb793bee180615d49ef25528bc351033ec450f5de68c8f`。坐标换算为 x=FreeCAD x−1298172、y=FreeCAD y+296458（mm）。

| 部件 | 当前坐标包络 mm | 实施 |
|---|---|---|
| 西墙 Rectangle054 | x9059–9209，y4507.25–6507.25 | 完整150mm直墙；没有避让凹口 |
| 南侧补墙 Rectangle067 | x9988.125–10738.125，y4523.9375–4673.9375 | 保留原补墙关系，并闭合至既有东侧墙，浴室内侧连续齐平 |
| 台盆 Rectangle068 | x9228–10428，y5925.219–6425.219 | 西北侧1200×500 |
| 马桶 Rectangle061 | x10763.75–11363.75，y4935.531–5435.531 | 东南侧，朝西 |
| 淋浴 Wire | 东北角切角屏风轮廓 | 保留切角，托盘靠既有东、北墙闭合 |
| 外侧衣柜 Rectangle066 | x9972.25–11372.25，y3908.094–4508.094 | 1400×600；入口在其西侧 |

两案浴室和衣柜包络完全一致，已对照独立重开的实际网格。1200×100 的推拉示意矩形作为装配参考登记，不能当作1200mm净门宽。墙间毛口约779mm，本版两边示意门框各25mm，净通行约729mm；完整轨道约1.57m。

## 书房造型和功能

| 部件 | 保留位置 / 尺寸 | 当前模型 |
|---|---|---|
| 书柜 Rectangle024 | 4200×450，高2000，位于长茶台后方东侧 | 开放木色格架、少量书籍，原包络保留 |
| 长茶台 Rectangle026 | 2200×800，高750，位置不变 | 木色长台和细木格条收边 |
| 原矮书柜 Rectangle025 | 1600×450，高900，位置不变 | 改为专用茶水台、封闭下柜；350×280水槽和350×300煮茶位 |
| 主人椅 / 条凳 | 原家具位置保留 | 主人椅改为朝茶台的木格背造型，条凳木色统一 |

茶水台模型具有台面开孔、水槽、龙头、排水弯管、给水管及待确认接点。锅具、加热板和干区电源接点用于表达煮茶功能；管道去向和电源安装未按现场放行。原打印机 / NAS 占位没有继续放在新湿操作台上。

原茶台与茶水台之间净距约297mm。用户明确要求本轮保留 FreeCAD 位置，故没有借造型调整家具位置；此间距不能作为舒适站立操作通道的确认。

## 校验与后续尺寸

独立重开 A/B，各核对1244个原对象状态；厨房原对象和冻结文件哈希保留。新增隔断、局部撤回后的墙壳均为闭合索引网格，边界边和非流形边均为0。局部撤回区外4405处原墙面采样复核，最大测得偏差约0.215mm；长而薄的水平三角面采用双精度复核，避免单精度最近点误报。

- [门运动、墙体闭合和 FreeCAD 包络校验](/Users/xiwei/interior_design/projects/c_type_home/design/secondary_bath_options/r3/CLEARANCE_QA.json)
- [A 独立重开和书房位置校验](/Users/xiwei/interior_design/projects/c_type_home/design/secondary_bath_options/r3/A_FRESH_OPEN_QA.json)
- [B 独立重开和书房位置校验](/Users/xiwei/interior_design/projects/c_type_home/design/secondary_bath_options/r3/B_FRESH_OPEN_QA.json)
- [斜门围合撤回来源](/Users/xiwei/interior_design/projects/c_type_home/design/secondary_bath_options/r3/D107_ROLLBACK_REGISTER.json)
- [书房功能登记](/Users/xiwei/interior_design/projects/c_type_home/design/secondary_bath_options/r3/STUDY_TEA_REGISTER.json)

当前属于几何、造型和功能审阅，尚未施工放行。约729mm净入口和门框截面要复尺、选型；切角淋浴托盘约842×785mm、面积约0.619m²，切角段约418mm，不能直接把这段当作已确认的淋浴净门宽。淋浴门形式、洁具 SKU、给排水、墙体构造和电源点位仍需下一阶段确认。书房本轮仅更新造型和功能，保留用户选择的既有位置。

所有生成图保存在项目文件系统，以路径交付。Workbench1800×1400、32级抗锯齿、Standard色彩管理；简单审阅材质，未做最终材料和光照。旧根目录 A/B 及 R2 为历史候选，不能作为本轮最终结果使用。
