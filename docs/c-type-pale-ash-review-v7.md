# C-Type 浅白蜡木、门材质及天花查看 V7 — 2026-10-14

业主指出V5顶板挡查看、画面/材质质感较弱、木色偏深，指定大门金属、内部平开门木材、推拉门玻璃。业主补充澄清：上方板为天花，休闲厅天花高450mm。V5源及所有旧图保持，独立分支codex/c-type-pale-ash-review-v7。

## 参考与原因

实际打开桌面《木甲木乙—白蜡木系列》17页（2116、2201、2206等）及既有客厅Faithful/Designer选图。此前TextureCan灰木atlas的目标linear RGB .31/.195/.102和779左右旧材质使用偏棕；旧Poly Haven native木材、无纹理旧木色混用。混元床/柜的贴图含烘入明暗，不能按暖色阈值划分材料（以前已失败）。复用已有兼容完整PBR，不重新手绘纹理或生产泛型家具。Atlas出处https://www.texturecan.com/details/389/，CC0，已在项目renderer验证；麻布为已取得的Poly Haven rough_linen完整原生材质。

## 实际修改

774可见物件材料槽统一到浅白蜡木或米白麻布。浅木材复制已有节点，Value1.5、Saturation.78保留木纹，高光roughness映射.36–.58；这是图册方向校准，不是实物色卡测量。织物沿用4K完整法线/roughness/height，米白浅麻颜色、金属项归零。床只按低于785mm的明确承托框架表面分木材，共20067三角形；布品源UV/颜色、枕纹保留。电视柜根据V5已有柜体/摆件顶点集合，仅18793柜体三角形用浅木，陈设不染木色。几何不再改。

V4_ENT-1_LEAF_0/1改哑光金属，框和把手保留金属。原R3_SLIDING_LEAF隐藏保留；沿用项目已建立的framed-glazing构造流程，40mm外包内采用10mm清玻璃、25mm金属框。玻璃Transmission1、IOR1.45、roughness.035，门扇整体外包/位置/开启关系保持。玻璃厚度/边框分件为定制表现推定，未指认成品SKU或供应商安全规格。原把手安装位置保留，新玻璃厚度变薄后补四个表面夹持支柱，避免把手悬空；固定构造为推定，未认证钢化开孔。六个内部平开门木色验收；既有其他玻璃推拉门保持。

天花原分片有共面叠片、200mm墙带缝及无效凹多边形；Shapely2.1的make_valid/平面union/constrained triangulation用于表现层修补，<=202mm接缝闭合、<=.15m²内洞补面。高区增加覆盖4.935m²、低区增加.363m²，消除高低投影重叠.021m²，顶板外界基本保持（0.1mm snap）。原CEILING网格隐藏保留；新低/高板底标高2.8/3.25m、厚.12m，补450mm交接立面。这些板缝施工构造仍为推定，不修改冻结建筑authority、墙窗和地面，不把天花叫屋顶/上一层地板。

默认OVERVIEW_CEILING_HIDDEN仅在viewport隐藏新天花；INTERIOR_CLOSED_CEILING用于闭合室内光路。Overview关闭render use，F12仅渲染Interior。默认快速Material Preview采用工作室光，因此应通过实际Cycles图验收室内材质。

## 验证与交付

Fresh-open比较3461原对象mesh/world矩阵保持、16保护源保持。床2130×1910×1070mm、电视柜2000×460×400mm及657mm床尾净距保持。原客房布局与尚未解决门问题保持。新天花顶面法线修正向上；初版候选保留，没有覆盖。

模型 /Users/xiwei/.codex/worktrees/c-type-study-daybed/interior_design/projects/c_type_home/design/pale_ash_review_v7/WHOLE_HOUSE_PALE_ASH_DELIVERY_V7.blend
SHA256 e325b355d94a7d6d7cb88ca06e18f0eeeab5a96493a33266cf1e57a73f0cecf5
图库 http://127.0.0.1:5188/pale_ash_review_v7/review_gallery.html

对照：原/新客厅和次主卧同相机、同照明/AgX；另玄关、走廊、玻璃推拉门、电视柜细节共8张实际1600×900/128samples/Cycles Metal/OIDNHighAccurate。另3张Workbench整屋带顶前后和去顶几何证据。模型保存未来渲染2560×1440/256samples，不能把检查图称该尺寸。所有图片/模型本地，0Image2；源码/小合同进Git，不合并，HUMAN_REVIEW。

## 复现

依次Blender CLI运行inspect_ceiling_source_v7.py；配置Python Shapely>=2.1（本次仅task-local /tmp/c-type-finish-v7-deps，不改用户环境），运行prepare_ceiling_planar_repair_v7.py；Blender运行build、finalize、finish_framed_slider、complete_slider_mount、verify、render及render_detail脚本；bundled Pillow运行package脚本。脚本保护已有产物，不重复启动已完成队列。原源几何/照片、当前成功产物保留。

## 防复发

查看顶板可见性与室内遮光是两个模式，不能用永久删顶获得明亮效果。只改material.diffuse_color不会改变已连颜色贴图的Cycles外观；必须检查实际shader输入。照片烘入阴影不能作为材质语义，复用既有真实构造分区。颜色修正、摄影清晰度、松软造型分别验收；提高采样不会改变填充物和床品轮廓。

全屋房间及带顶/去顶检查图来自同材质的framed候选，最终delivery只补四个玻璃把手夹持支柱；最终玻璃门与电视柜近景从delivery重新渲染，两个阶段路径/哈希分开记录，未把夹持支柱修改说成其他家具改动。

补充最终门扇独立Cycles1000×1100/64samples整件图已打开：透明玻璃、细框与把手连接可读；背景棋盘仅检查透射。脚本render_slider_isolated_v7和append_slider_studio_v7保存来源不回写模型。技术检查通过，外观仍待业主接受。
