HUMAN_CAD_REVIEW_V01 — 人工审图包
==================================================

组1 现状 vs A102:  g1_measured_full / g1_a102_full / g1_overlay / g1_*crop
组2 俯视 vs A103:  (底图见下) / g2_a103_full / g2_*crop (g2_step已STALE)

源 sha256(前10):
  A102_WALL_DIFF_POC_V3.dxf  a3dc6631b5
  A103_CONSTRUCTION_POC_V7.dxf  381eacb73e
  measured_working.dxf  3711c47c11
  V15_WORK.blend  feaeed380c (权威哈希未变)

!! STALE 标记 (P0.2, 2026-10-19) !!
旧底图 blender_ortho_top / _stair_zoom / g2_overlay 已重命名 *_STALE_20261019.png,
不再作为审图依据。原因: 旧俯视把 V7_CEILING_* 吊顶构件一并渲染,
其过渡带西缘=旧休闲平台弧线(已确认非台阶/地坪几何)。
A103 一致性审图改用 ARCH_FLOOR_PLAN_REVIEW 隔离视图
(cad/review_views.py, 排除吊顶集合+楼板守卫),
新底图见 cad/step_wave_p0/arch_orig_plan.png (原) / arch_cand_plan.png (候选)。

台阶平面图语义: 3级=3条踢面线. WAVE_STEP_3_ARRIVAL 为+450到达平台,
A102/A103 中已并入 STEP_2 轮廓(XDATA: merged_arrival), 不再显示为第4级.
g2 叠加中俯视底图色深=实体, A103轮廓线=墙体层.
本包为人工审图资料, 非正式施工图; 专业CAD编辑验证仍 NOT_RUN.
