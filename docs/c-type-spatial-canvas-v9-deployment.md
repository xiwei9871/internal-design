# Spatial Canvas 5176 + C-Type V9 — 2026-10-14

用户要求在http://127.0.0.1:5176/部署SpatialCanvas并导入V9。复用Spatial-Canvas V0.5.1现有Vite与local-export流程，没有改应用源码或增加功能。

服务通过bundled Node启动Vite，host127.0.0.1、strictPort5176；持久进程PID/log：/tmp/spatial-canvas-5176.pid、/tmp/spatial-canvas-5176.log。原端口无监听，启动后HTTP200。应用目录/Users/xiwei/Documents/ChatGPT/Spatial-Canvas。

模型 /Users/xiwei/.codex/worktrees/c-type-study-daybed/interior_design/projects/c_type_home/design/glass_visibility_v9/WHOLE_HOUSE_GLASS_VISIBILITY_V9.blend
SHA256 42beee4cb51bce1487edbe0003b226951986ca073b2d2e3b4ffec9305c80f9cf
导出/导入 /Users/xiwei/Documents/ChatGPT/Spatial-Canvas/task-output/c_type_v9/full/interaction_proxy.glb 与manifest同目录。

依现有frozen sidecar exporter，不向.blend初始化ID或保存。1571可见可交互实体，916个旧ID沿用，其余新ID仅外部registry初始化一次。对象均DERIVED_DESIGN_MODEL；frozen含义是锁定当前hash供交接，不代表物理GroundTruth。源字节哈希保持；新的床/沙发/电视柜和玻璃门存在，顶板在默认overiew源状态下不纳入代理，逐对象交互边界保留。导出38,234,736字节，独立GLB重新导入ID/native绑定检查通过。

网页Open local export实际导入成功，Resource/状态显示glass-visibility-v9-review-1和1571stableentities。点选HUNYUAN_V3_COUPLE_BED检查Inspector原生名与2130×1910×1070外包正确。17继承房间候选区域重新绑定V9sourceSHA，Import spatial semantics成功，状态PARTIAL，未升级其既有验证状态；旧关系图不导入，避免错带旧家具关系。

网页是交互代理：无纹理simple PBR颜色、普通玻璃alpha.14/磨砂.68，以查看与点选为目的，不承诺还原Cycles.shader。真实V9.blend及全部纹理保留。没有Image2调用/批量渲染。页刷新会丢失本地加载内存，需要通过Open local export再次选manifest/GLB，这属于现有产品行为；未擅自加自动导入或文件watcher。

浏览器实截 /Users/xiwei/Documents/ChatGPT/Spatial-Canvas/task-output/c_type_v9/SPATIAL_CANVAS_V9.jpg
交付/源校验 /Users/xiwei/Documents/ChatGPT/Spatial-Canvas/task-output/c_type_v9/DEPLOYMENT.json
