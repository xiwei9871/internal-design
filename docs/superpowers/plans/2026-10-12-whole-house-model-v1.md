# C-Type 全屋实际模型 V1 执行记录

业主确认15房风格与模型制作，继承既有客餐厅和V10软包经验。最终停在逐房 HUMAN_REVIEW，不自动接受外观、不合并。

- [x] V5完整住宅基础、16个受保护来源，production仅作75相机来源。
- [x] 逐房人工选择，AI只控制外观；图册/既有实物研究优先。
- [x] 制作实际家具、软包、木作、陈设和原生材质，不以属性代替模型。
- [x] 对面阅读柜、三阶木扶手、历史北阳台阶梯柜。
- [x] 15房灰模及实渲，修复靠包交叠、光斑、阅读柜/矮柜与床垫/床罩承托。
- [x] 最终fresh-open核验，打开18图评审并打包图库。
- [ ] 仅提交真实脚本、小合同与文档，推送分支；PR受身份可用性约束。

旧WHOLE_HOUSE_MODEL_V1.blend只是合同快照，保留但不作交付。真实制作链为build_house_assembly_v1 → repair_house_assembly_v1 → finalize_house_supports_v1 → finish_house_presentation_v1 → finish_house_bed_supports_v1。每步另存，BUILD_AUDIT追踪版本与哈希。

新沙发806mm高、坐面约484mm未作舒适度认证；阅读柜锚固与北上柜人体动态安全、采购SKU和施工节点待深化。预览1280×720、Cycles32 samples不是最终摄影级验收。
