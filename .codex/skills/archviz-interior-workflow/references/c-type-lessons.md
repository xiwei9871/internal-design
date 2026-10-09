# C-Type 经验档案 — 2026-10-09

## 可靠程度

**已执行并获用户正面反馈：** 当前准确geometry机位 + 真实家具目录裁图 + 明确房间不可变项 + 摄影参考角色划分，先做Faithful。15空间×5视角75张完成；用户认为第一轮Faithful还不错。244旧图哈希验证不变，latest/R4/B0不变。

**有效工程控制：** 单实例锁、成功缓存、仅A启用policy、小JPEG联系表、网页缩略图、原生尺寸记录、续接聊天迁移监控。52补图请求完成，厨房已认可A主图复用。

**历史未验证阶段：** 早期B/C材质change-ledger未成功；后续V3小样被用户认为区别不足。最新已认可的是Designer V4软装、Creative V5简洁浅木家具概念，见末尾新决定。Faithful仍有7个明确待修项，不能称75张全部几何通过。

## 踩坑与防复发

| 触发/证据 | 原因或判断 | 后续规则 |
|---|---|---|
| 旧175/225三方向相似、素模感 | 同一浅木/厨房外观/光线锚点压过弱风格词；采样增加无法产生设计差异 | Faithful先行；B/C按可见对象分别列变化，用专属参考，小样通过再扩展 |
| 原聊天22次128MB task_complete错误，编码图像记录约77MB；Image2单次约2–5MB | 对话历史请求过大；精确网关序列化字节未测，不把77MB当完整请求大小 | 小JPEG/局部图+manifest；不要再唤醒已超限旧聊天；不要提高Image2限制来“修”聊天 |
| 同房hero参考导致细节图变为主图 | 语义丰富参考压过当前几何取景 | 细节视角裁局部材质参考，限制完整hero；检查crop/FOV/锚点，漂移图不通过 |
| Creative新增曲面天花 | “雕塑感”扩展到了建筑 | 变更仅限具体对象/表面，天花及开口锁定 |
| 绿色床尾平面生成硬板 | 简化底模语义模糊 | 明确柔软runner、垂落、织物参考；不拿成图回写床体 |
| 书房多椅、梳妆椅变凳 | 为美观补全或重新解释家具 | 记录数量、可见性、椅背/长椅/躺椅机制；隐藏物禁止入画 |
| 燃气灶成平面圆盘，烟机无功能细节 | 底模与旧AI参考都过度简化 | 查厂家实物顶视/斜视、锅架、火盖、旋钮、进风控制；外观参考不自动采用SKU尺寸 |
| 镜后新增梳洗区，树景作现场 | 反射和室外填充无证据 | 镜中可见关系写清，背景标ILLUSTRATIVE，现场照片优先 |
| 关闭天花集合、玻璃误分墙、重复墙挡厨房窗 | Presentation可见性/材质误判 | 核查集合与材质；源不改，任何hide override应有来源/授权并单独记录 |
| 窗内白色圆斑 | 补光发光面通过玻璃/反射可见 | Blender检查光源camera/transmission/glossy可见性，再确认光照贡献；非所有光源一律隐藏 |
| 原生1672×941/940但要求1920×1080 | 服务实际返回与请求不一致 | 记录真实尺寸，禁止称原生1920或静默放大 |
| 401/503后队列中止；僵尸被当运行 | 服务与进程状态分别判断 | 不反复改配置，真实process state+lock；缓存重启与失败job重试分开 |

明确待修：reading_transition VIEW_03/05、hallway VIEW_03、mother_bedroom VIEW_05、study VIEW_04、secondary_bath VIEW_02、kitchen VIEW_05。当前全部保留，等待用户指定修正。

## 查证路径（项目相对路径，非通用冻结值）

- `docs/whole-house-faithful-checkpoint-2026-10-09.md`
- `docs/whole-house-render-study-v1.md` 与 `docs/whole-house-photo-study-v2.md`
- `projects/c_type_home/render_config/CAMERA_REVIEW_LESSONS_V1.md`
- `projects/c_type_home/render_config/kitchen_prompt_review_v2/APPLIANCE_RESEARCH.md` 和 `APPLIANCE_OFFICIAL_REFERENCES.json`
- `projects/c_type_home/render_config/photo_study_v2/GENERATION_POLICY.json` 与 `STYLE_SEPARATION_V3.md`
- 本地产物 `projects/c_type_home/renders/whole_house_final_study_v1/photo_study_v2/00_MANIFEST/FAITHFUL_COMPLETION_REVIEW.json` 和各房 `FAITHFUL_VISUAL_QA.json`

原模型及worktree路径从当前registry解析，不从这里固定。此档案适用于C-Type；新项目另建经验档案。

## 2026-10-09后续人工修正

客厅V3仅灰褐石面与灰绿藤编/木面变化，用户仍认为没有本质区别，否定其设计定义。最新定义：Designer保留主体后设计软装（挂画、摆件、织物、装饰灯具等）；Creative可以脱离原家具与布局，让AI提出启发概念。V4按此执行，不能以“材质能辨认”宣称用户目标已达成。Creative图片不回写原模型，输出标为灵感概念。

## Creative V4审美漂移与新边界

用户认为Designer V4有改善，可保留；Creative V4的深石材、浓重配色和装饰墙不符合简洁浅原木住宅方向。自由重设计是家具、组合与空间想法的自由，不是整体风格无边界漂移。C-Type Creative继续以浅白蜡木/浅橡木、米白织物、明亮中性日光、留白和低装饰密度为锚点；只允许少量低饱和点色。V5只重做Creative，Designer V4不重跑，原模型不改。新小样仍待人审。

## 全屋传播授权与主图检查点

用户已认可客厅Faithful、Designer V4和Creative V5三模式，明确要求全屋15×3×5。新批whole_house_modes_v3复用75Faithful和2客厅主图，新增148张B/C；旧批与model不变。各房主图已逐张打开，8个需要改进的主图分别留原图并产生repair1，经agent候选检查后记录selected_derivative，不是自动人工接受。主图的装饰位置必须记录continuity：客厅反向view把原东柜上挂画移到沙发后墙，已标REJECT_DECOR_LOCATION_DRIFT，禁止用看起来同风格替代空间一致性。
