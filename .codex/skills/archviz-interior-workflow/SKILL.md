---
name: archviz-interior-workflow
description: 制作、续跑或评审基于已确认室内模型的效果图，组织相机、实物参考、Faithful 基线和局部 Designer/Creative 对比，并控制图像请求体积与视觉漂移。用于室内 ArchViz 和模型引导的 AI 改图；不替代户型重建、布局设计或施工图。
---

# 室内效果图工作流

把效果图作为有来源、可复现、可逐张验收的候选表现。先查看项目最新人工决定；不要根据旧计划继续已暂停的风格或队列。用户对某一版摄影感满意，不代表认可每个机位、家具细节或施工尺寸。

## 开始与恢复

1. 定位实际仓库、分支/worktree、模型 authority manifest、相机 register、生成 policy、计数、视觉 flags 和运行进程。只读取明确相关的文件及紧凑摘要，避免递归扫描整个产物树。
2. 核对源模型和冻结层哈希。Presentation 文件单独保存；不得从效果图回写墙、门窗、标高、台阶、管线、设备位置或家具布局。Creative若获用户授权可在图片里探索不同布局/造型，须标为灵感概念，不能把它当已安装或已批准模型。
3. 报告真实数量、已认可部分和未完成部分。现有成功图、提示词、失败证据保留，不覆盖；原图与派生缩略图分别命名。
4. 根据用户当前授权确定 `enabled_levels`、房间、机位和停止条件。默认先 Faithful；Designer/Creative 在指定区域做小样，通过视觉比较后才扩展。已授权的续跑不逐房重复询问。单纯要求整理技能不授权生成图片。

遇到 C-Type 项目，读取 [项目经验与证据](references/c-type-lessons.md)。其他项目不要照搬 C-Type 的配色、75张计数、文件路径、镜头或设备型号。

## 生产顺序与闸门

**参考与空间 → 相机预览 → 单视角 Faithful → 人工认可摄影方向 → 分房机位扩展 → 逐图结构/取景复核 → 人工指定局部 → Designer/Creative 小样。**

- 实现或改善前先找可借鉴方案：当前项目 / 本地资产 → 厂家官方模型 → 合适且兼容的成熟家具 / 材质库与官方方法。合理检索仍无合适方案，再自研缺口。不要用泛型圆角块、任意扰动或不断手调替代已有精细软包、实物模型与完整材质方案。模型 / 材质借用的筛选、版本与验证方法见 [资产与成熟方法优先](references/assets-before-custom.md)。
- 精细物件先确定实物身份或有依据的定制构造，再找对应整件模型。业主图册 / 产品资料决定造型、结构和材料；布局简模仅承载有来源的空间约束，其内部坐垫、缝隙、分件和通用造型不能当作物理事实强制保留。禁止以别款软包、旧简模木框和统一材质拼装来代替整件实物复现；详见同一资产工作流。
- 先查本地图库、现场照片、业主资料和真实产品/家具目录。不足时研究网络官方产品页及多角度实物图；每个重要可见家具和家电都应有可追溯 reference，缺失项记录为未验证，不能以生成式旧效果图代替。详见 [实物参考与设备](references/references-and-appliances.md)。
- 每个机位写明所支持的设计判断、可见锚点及镜头后/遮挡物。使用低成本几何预览和房间联系表先查真实位置、透视、裁切及重复内容，再冻结相机。已确认相机不能被统一镜头建议覆盖。详见 [机位与镜头](references/cameras-and-lookdev.md)。
- 先用一个代表视角校准真实材质、接触阴影、日光方向、曝光和色彩；不要靠采样数或“高级、摄影级”词语补救错误材质/家具。纯 Blender 与模型引导 AI 都可采用，工具由任务决定。
- Faithful及Designer当前图的 geometry/camera 约束优先；Creative按用户授权可脱离原家具、布局与表现设定，以参考图作为空间背景而非必须复制的几何。旧 hero在锁定模式仅控制材质/家具家族。不能把复杂主视角直接作为所有细节机位的完整构图参考。详见 [提示词与三方向](references/prompt-contracts.md)。
- Designer保留主体，重点设计挂画、陈设、抱枕/地毯/窗帘、装饰灯具等完整软装；Creative可在用户已定风格基因内自由提出不同家具/布局/艺术与授权建筑表现概念；自由不默认允许整体审美、主材、色系和装饰密度漂移。详见模式合同，不能再次把B/C都写成原包络内的换材质。
- 每张输出打开检查；低分辨率筛查疑点后，局部裁图查细节，不把整批原图上传对话。照片质感、取景一致、结构一致、跨视角材质一致分别记录。文件存在或边缘分数不等于通过。

## 图像与请求体积

区分 **Codex 对话请求超限**、**Image2 编辑请求超限**、**网页图片下载量**。三者分开诊断。JPEG 网页缩略图减少下载量，但不会删除已经累计的聊天图片历史；`detail: low` 或 token 压缩也不保证传输字节减少。

默认评审联系表长边约1200–1600px、JPEG质量80–85，每次1–2张；疑点再传局部裁图。生成原图不降质，仍留在磁盘。工具文字只输出路径、状态、字节数、尺寸、哈希和短错误；不输出 base64、完整 API 响应或历史聊天全文。24 MiB是我们生成请求的保守预算，**不是供应商的通用官方上限**。

已超限的聊天不反复重试、不 fork 全部历史。在当前干净续接中读取紧凑 handoff；如用户要求新聊天再创建。需要迁移既有任务监控时核对目标 thread，不重复创建自动化。详见 [传输、缓存与续跑](references/transport-and-resume.md)。

## 工具和失败处理

AI 栅格图在此机器使用已安装 `codex-image2` 技能及持久 launcher：

```bash
rtk proxy python3 /Users/xiwei/.codex/skills/codex-image2/scripts/image2.py edit --image /absolute/current-geometry.png --image /absolute/relevant-reference.jpg --prompt-file /absolute/view.prompt.txt --out /absolute/new-candidate.png --model gpt-image-2 --quality high --size 1920x1080 --max-attempts 1
```

参数按当前合同配置，不强制所有项目1920×1080。若用户明确选其他工具，遵循用户选择。launcher 每次读本地配置；不输出 key、不写入项目、不因503重装/换供应商。授权缺失不索要聊天粘贴密钥。

单一串行 coordinator + OS 文件锁 + 每个 job 独立 meta/cache。已有成功图即便 meta 缺失也先保留核对。401/403为授权、400/413/422为请求问题，停止相关队列且不自动重发；429停止并尊重服务退避。瞬态5xx/超时最多一次逻辑重试，CLI transport attempts也计入总量并记录。失败或已耗尽重试的任务不得因重启再次请求。

## 可重复执行的小工具

本技能 `scripts/artifact_guard.py` 不生成图、不访问网络、不改模型：

```bash
# 图像真实字节+保守编码开销；超预算直接非零退出
rtk proxy python3 <skill>/scripts/artifact_guard.py preflight --image /abs/base.png --image /abs/reference.jpg --prompt-file /abs/view.txt
# 每次明确列出当前要评审的图，生成新JPEG联系表，不覆盖已有文件
rtk proxy <python-with-Pillow> <skill>/scripts/artifact_guard.py sheet --image /abs/geometry.png --image /abs/candidate.png --out /abs/review/view-check.jpg
# 首次记录/随后核对明确列出的原图或源模型
rtk proxy python3 <skill>/scripts/artifact_guard.py snapshot --file /abs/source.blend --file /abs/image.png --out /abs/review/preservation.json
rtk proxy python3 <skill>/scripts/artifact_guard.py verify --manifest /abs/review/preservation.json
```

`sheet` 需要Pillow，优先使用已配置 bundled Python，无需重装环境。详见 [合同和验收](references/contracts-and-qc.md)。

## 交付和记忆更新

交付画廊/输出路径、实际与目标计数、原生尺寸、采用的输入/reference/相机版本、视觉 flags、哈希核验、请求/重试数量、下一步。请求尺寸不等于实际尺寸；显示放大不等于原生分辨率。成功生成与人工设计接受分开。

Git只包含脚本、小合同、技能和人工决定记录，图片/纹理/Blender二进制留在本地。按项目Git规范提交。到用户规定的HUMAN_REVIEW停止并使监控不再自动生成。新问题记录“触发条件→证据→原因→有效修正→验证状态”，只有重复可复现的教训进入通用规则。
