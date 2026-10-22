# D107门侧实际修改 V3

本轮已实际编辑并保存[全屋V3模型](/Users/xiwei/interior_design/projects/c_type_home/design/living_correction_v3/B1_LIVING_CORRECTED_V3.blend)，不是仅修改文字记录。客厅仍为HUMAN_REVIEW。

以用户最后标注为准：同一轴测角度画面左侧红框约50mm可见实体墙，右侧蓝框门套外缘直接到墙体转角，没有可见实体墙垛。200mm的旧说法已作废，模型没有增加该墙垛，也没有据此收窄门洞。

门套外缘的斜门局部坐标为[-70,920]mm，转角边界为[-70,970]mm，所以红框余墙=970−920=50mm，蓝框余墙=−70−(−70)=0。蓝侧只有与既有墙接合的转角墙/门框背衬，不增加门套旁的正面墙垛。左右名称仅对应用户给出的相机，不改变斜门26.3°方向。

旧的矩形转角墙`W_wall_md_0018`遮挡了红侧测量面；V3保留该旧对象为隐藏源，并以原尺寸保留y5230.2–6450.2的主体余段，用新局部门侧转角连接消除重叠。门扇及木门套未移动，实际门扇模型仍850×40×2100mm；这些是继承登记值，不是本轮实测。

## 检查文件

- [与用户标注相同角度](/Users/xiwei/interior_design/projects/c_type_home/design/living_correction_v3/renders/D107_SIDES_01.png)
- [正面检查](/Users/xiwei/interior_design/projects/c_type_home/design/living_correction_v3/renders/D107_SIDES_02.png)
- [独立重开校验](/Users/xiwei/interior_design/projects/c_type_home/design/living_correction_v3/V3_QA.json)
- [来源与尺寸清单](/Users/xiwei/interior_design/projects/c_type_home/design/living_correction_v3/V3_MANIFEST.json)

974个对象状态在独立进程重开后通过。实际网格顶点与门套边界校核、红侧墙面射线及红/蓝标注在原相机中的投影顺序通过；厨房272个保护对象、北阳台门、门扇位置和尺寸保持一致。此前V1/V2及B0、厨房冻结文件哈希保持一致。

两张1600×1200 Workbench检查图保存到项目文件系统；墙体不剖切，相关门侧部件完整显示。新图已通过少量低分辨率代理检查。所有图片仅返回路径。
