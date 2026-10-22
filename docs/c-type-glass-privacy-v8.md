# C-Type 透明与隐私磨砂玻璃 V8 — 2026-10-14

业主询问墨色/茶色玻璃是否修正，要求普通玻璃透明；随后明确隐私区磨砂：三个卫生间淋浴，次主卫推拉门，通北阳台双扇推拉门。经户型登记核对，该双扇门为客房↔北阳台，业主已确认纠正客卫标签。主卫/客卫入口仍用木门。家电黑色镜面舱门、灯罩、镜子保持。

源V7 /Users/xiwei/.codex/worktrees/c-type-study-daybed/interior_design/projects/c_type_home/design/pale_ash_review_v7/WHOLE_HOUSE_PALE_ASH_DELIVERY_V7.blend
SHA256 e325b355d94a7d6d7cb88ca06e18f0eeeab5a96493a33266cf1e57a73f0cecf5
派生模型 /Users/xiwei/.codex/worktrees/c-type-study-daybed/interior_design/projects/c_type_home/design/glass_privacy_v8/WHOLE_HOUSE_GLASS_PRIVACY_DELIVERY_V8.blend
SHA256 e9b3e3d4766f161e2b7f6450475c8d0f8af4c59469709747356ad7f744e58928

47个可见建筑玻璃物件逐名/材质槽确认：31透明、16磨砂。磨砂包含R3_SHOWER_GLASS0–2（次主卫）、Rectangle007/G_wall0007客卫分隔、Rectangle033/G_wall0033主卫分隔、V7薄玻璃推拉门、客房北侧两玻璃门扇。普通窗及客厅/餐厅玻璃门/阳台玻璃采用无色transparent。BaseColor1、Metallic0、Transmission1、IOR1.45，clear roughness.015、privacy roughness.68，无颜色吸收节点。磨砂并不无条件遮挡近距离轮廓/夜间背光，未作人体隐私认证。

原玻璃本来大多已有透射，茶色/墨色观感还包含深色环境反射；V7环境/室内灯不改。不能为去除反射把IOR改1或把所有镜面当玻璃。第一版统一纯Principled玻璃后客厅明显变暗，原因旧GLASS材质有专用于shadow ray的白Transparent光路。在实际同机位比较后拒绝该亮度回退，恢复这个已验证的ArchViz采光近似，camera/reflection继续无色透明/磨砂表面。非光度学认证，不是改变窗洞/灯强度伪装传光。

3473源对象网格/世界矩阵/渲染可见性、非目标材质槽均要求fresh-open保持。16保护源保持。主卫/客卫木门、家具及V7天花高差450mm、默认去顶模式保持。初版模型/失败明度图保留；没有覆盖旧模型。只修改材质，0Image2。

5个已登记机位：客厅、主卫、次主卫、客卫、客房北阳台门。实际Cycles1600×900/96samples/MetalGPU/OIDNHighAccurate，V7客厅同镜头1600×900/128sample作为before参考。新的玻璃surface不等于现场隐私样品，通过照片不能认证夜间人体轮廓遮蔽。

脚本：inspect_glass_source_v8 → build_glass_privacy_v8 → restore_glass_light_transport_v8 → verify_glass_privacy_v8 → render_glass_privacy_v8 → package_glass_privacy_v8。脚本拒绝覆盖现有模型；源码和小合同进Git，Blender/图留本地，不合并。最终候选HUMAN_REVIEW。

图库 http://127.0.0.1:5188/glass_privacy_v8/review_gallery.html

最终fresh-open检查通过：3473源对象、非目标材质槽、16保护文件保持；5张最终图已打开联系表/客厅对照检查，室内平均图像亮度比V7为1.0251（只用于回归，不是照度）。透明玻璃反射仍映室外棕色景物，不能承诺所有角度无暗色。最终图库HTTP200，人工外观接受待定。
