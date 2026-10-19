HUMAN_CAD_REVIEW_V01 — 人工审图包
==================================================

组1 现状 vs A102:  g1_measured_full / g1_a102_full / g1_overlay / g1_*crop
组2 俯视 vs A103:  blender_ortho_top / g2_a103_full / g2_overlay / g2_*crop

源 sha256(前10):
  A102_WALL_DIFF_POC_V3.dxf  34f11ea61d
  A103_CONSTRUCTION_POC_V7.dxf  cc49a4917c
  measured_working.dxf  3711c47c11
  V15_WORK.blend  feaeed380c (权威哈希未变)

注意: blender_ortho_top 为 Workbench 俯视, 渲染严格遵循文件内 hide_render 状态(未改blend).
台阶平面图语义: 3级=3条踢面线. WAVE_STEP_3_ARRIVAL 为+450到达平台,
A102/A103 中已并入 STEP_2 轮廓(XDATA: merged_arrival), 不再显示为第4级.
g2 叠加中俯视底图色深=实体, A103轮廓线=墙体层.
本包为人工审图资料, 非正式施工图; 专业CAD编辑验证仍 NOT_RUN.