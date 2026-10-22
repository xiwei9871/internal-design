# 普通玻璃可见性根因修正 V9 — 2026-10-14

业主截图：全屋Material Preview玻璃黑绿近乎不透明，Cycles客厅窗户棕暗且室内倒影过强。V8虽用无色PrincipledTransmission1，用户可见结果不合格。不能再次把“shader参数正确”当作“透光已修好”。

## 分开诊断

同机位1200×675/48sample baseline/去掉所有普通玻璃对照：去玻璃后外景仍棕暗，但室内倒影消失，说明灰暗外景与真实反射竞争。向窗中心发射空间射线，仅命中LIVING_FIX_BAY_FRONT_GLASS_1；此窗5块8mm玻璃closed box、法线合理，无前窗叠层证据。没有改尺寸/窗洞来伪装修正。

保存查看状态：Material Preview forest.exr，EEVEE use_raytracing=False，材质raytrace refraction亦未开启。用同forest、同玻璃、同外侧相机做EEVEE off/on控制，off黑色镜面，on可见屋内沙发/地毯/台阶。依官方Blender5.2说明，启用场景raytracing、材质use_raytrace_refraction，SLAB厚度近似8mm。此独立EEVEE渲染模拟Material Preview，不宣称截取了真实用户UI。

官方说明已在浏览器实际打开阅读：
https://docs.blender.org/manual/en/latest/render/eevee/render_settings/raytracing.html
https://docs.blender.org/manual/en/latest/render/eevee/material_settings.html
终端403后改用正常浏览器；未绕过验证码。

## 实施与可见比较

保留V8普通无色玻璃IOR1.45/roughness.015，隐私磨砂roughness.68，不用IOR1、Alpha透明或隐藏真实玻璃削掉反射。
复制已有世界节点，仅原先独立camera/transmission背景强度.6→3.6（+2.585档），日光可见背景更清楚。试过2.4/3.6控制，保留3.6；同源PolyHaven kiara_3_morning/CC0已在项目验证，外景仍为ILLUSTRATIVE而非实测现场。diffuse世界强度.22、原灯具energy及相机曝光保持；这种背景摄影校准不是物理辐射度/照度认证。
保存EEVEE场景和材料开关；世界/相机模式不改变家具和门窗实物尺寸。隐私16窗与木门、家电原样，去顶模式仍在。

源 /Users/xiwei/.codex/worktrees/c-type-study-daybed/interior_design/projects/c_type_home/design/glass_privacy_v8/WHOLE_HOUSE_GLASS_PRIVACY_DELIVERY_V8.blend
源SHA e9b3e3d4766f161e2b7f6450475c8d0f8af4c59469709747356ad7f744e58928
候选 /Users/xiwei/.codex/worktrees/c-type-study-daybed/interior_design/projects/c_type_home/design/glass_visibility_v9/WHOLE_HOUSE_GLASS_VISIBILITY_V9.blend
候选SHA 42beee4cb51bce1487edbe0003b226951986ca073b2d2e3b4ffec9305c80f9cf

新模型fresh-open验证3473原对象geometry/matrix/materialslots/rendervisibility及全部灯能量保持，16保护源保持；clear/frost物理表面参数保持，EEVEE透射开关和外景背景分支校验。旧V8及所有控制/失败证据保留。

交付3张1600×900/96samples真实Cycles（客厅、夫妻次卧、隐私客房北阳台门）与1张匹配forest世界的EEVEE外侧窗口检查。旧V8客厅/EEVEEoff用于对照，页面所有原图留本地，仅JPEG联系表进入对话。0Image2，当前HUMAN_REVIEW。

图库 http://127.0.0.1:5188/glass_visibility_v9/review_gallery.html

最终4视图已打开联系表及卧室/隐私组合图检查：EEVEE清楚见室内，Cycles室外细节清楚，磨砂保留。模型、原源哈希核对，页面全部9端点HTTP200。源码解析及source-only暂存检查通过后独立提交，不合并。

## 后续流程检查项

Transmission=1与白色BaseColor只验证shader意图，不证明Material Preview、EEVEE、Cycles可见结果。以后交付.blend前，同时检查保存的查看模式和正式渲染。若黑色玻璃反复出现，先做同相机有玻璃/无玻璃对照，检查网格法线/叠层、EEVEE场景及材质透射开关、预览HDRI及可见外景曝光；不先取消反射或把玻璃隐藏。在同环境控制实渲后再保留修正。所用外景未实测时继续标ILLUSTRATIVE。
