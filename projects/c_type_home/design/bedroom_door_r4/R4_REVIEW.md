# 次主卧直门与地坪修正 R4 · 2026-10-02

最新用户纠正：撤销斜门不是取消次主卧入口；门应为东西向门洞，向南进入卧室内平开。R3曾把旧斜门及围合撤回后保留成开放无门空间，这一表达被本轮R4替代。北侧拟次主卫的完整西墙和推拉门A方案保留。

随后用户指出门口三角地面问题，本轮实际修复了旧斜门地坪边界、重叠补面和地坪间隙。不是让AI盖掉模型问题，也没有添加新台阶。平整地面顶面仍为+450mm，局部填补约0.155m²；修复区外的上层地坪平面包络差异为0。原上层地坪及三个相关旧补块保留为隐藏来源，新的四个闭合板域取代其活动表面；没有用薄面掩盖缺口。

## 审核入口

- [修正前后及向内开启对照](/Users/xiwei/interior_design/projects/c_type_home/design/bedroom_door_r4/renders/DOOR_AND_FLOOR_REPAIR_COMPARISON.png)
- [门位与公共区：关门，地面已平整](/Users/xiwei/interior_design/projects/c_type_home/design/bedroom_door_r4/renders/R4_A_DOOR_CONTEXT_00.png)
- [向卧室内开45°检查](/Users/xiwei/interior_design/projects/c_type_home/design/bedroom_door_r4/renders/R4_A_DOOR_FRONT_45.png)
- [90°开启轴测检查](/Users/xiwei/interior_design/projects/c_type_home/design/bedroom_door_r4/renders/R4_A_DOOR_AXON_90.png)
- [A推拉门方案完整R4模型](/Users/xiwei/interior_design/projects/c_type_home/design/bedroom_door_r4/OPTION_A_SLIDING_R4.blend)
- [B内开卫生间门方案完整R4模型](/Users/xiwei/interior_design/projects/c_type_home/design/bedroom_door_r4/OPTION_B_INWARD_R4.blend)

两模型新增的是同一樘次主卧普通门，不是卫生间入口。普通门当前默认关闭，父对象`R4_BEDROOM_INWARD_HINGE_ROOT`绕Z负向旋转为向南内开；0/45/90°状态已经检查。卫生间A/B以及书房造型、位置和功能均承接R3。

## 位置与尺寸依据

FreeCAD实际门扇符号Polyline044–047登记长850mm，仍带多个历史开启姿态。用户本轮的明确“东西向、向内开”高于这些斜向符号；R4不会按旧26.3°重建围合。完整西墙外侧X9059mm为新门东侧门框的接合面，旧墙带Y4500.2–4700.2mm为东西向门洞墙厚依据。门在卧室北缘，向南进入卧室。

本版门扇宽850mm。为了补门框及审阅安装缝，示意毛口910mm、框间860mm、两侧框25mm、名义门高2100mm；门扇实际包络高2090mm，保留上下审阅缝。西端铰链X8179 /Y4480.2mm，门洞和东门套接西侧隔断。这里的门框截面、安装缝和新铰链位置属于布置审阅尺寸，需要现场复尺，不能声称是FreeCAD中新增实测值。旧D107的RED50/BLUE0历史关系不用于这樘新的直门尺寸。

门扇、框、两侧门套、完整上方墙、东西侧连接实墙及五金已建模。旧斜门保持停用，黑色原实墙没有打拆；新增围合进入R3的开放区域，厨房和其他家具没有重建或挪动。

## 验证

- A/B各独立重开，1519 /1518个继承对象状态按授权地坪可见性调整核对，网格和姿态来源保留；原R3与冻结文件不覆盖。
- 三条门洞穿墙射线净空；门套外西、东、上方均命中实体墙。旧斜门活动对象数0。
- 向南内开0–90°共721角度采样，门扇不与周围原家具包络冲突。
- 地面63个样点高度均为+450mm，测得高度范围约0.000119mm；新地坪边界边和非流形边为0，修复区外平面包络变化0。
- 新白模已目视检查，门口三角面消失。修复后AI图仍需视觉审核，不能用AI输出作为门框或地面尺寸确认。

[A校验记录](/Users/xiwei/interior_design/projects/c_type_home/design/bedroom_door_r4/R4_OPTION_A_QA.json) · [B校验记录](/Users/xiwei/interior_design/projects/c_type_home/design/bedroom_door_r4/R4_OPTION_B_QA.json) · [读取的FreeCAD局部门扇与墙线](/Users/xiwei/interior_design/projects/c_type_home/design/secondary_bath_options/FREECAD_BEDROOM_DOOR_LOCAL.json)

## AI图修订范围

[门纠正后的出图目录](/Users/xiwei/interior_design/projects/c_type_home/renders/r3_option_a/living_batch_v2_door)使用R4作为新几何源。A2反向视角可见新门，A4公共区视角保留真实局部遮挡，D1新增门位核对视角；各重出strict/design/explore，共9张。旧批次A1/A3/A5没有朝这个门位拍摄，仍可作为风格参考；旧A2/A4不再作为当前门位权威。所有正式图、白模和代理以路径交付。
