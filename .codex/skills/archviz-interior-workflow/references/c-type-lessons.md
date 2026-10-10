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

## 全屋三模式V3完成记录

225候选槽位完整、三方向各75；15房矩阵及41修正候选已打开，停止HUMAN_REVIEW。299旧图及源/R4/B0哈希保持。复用77张，新增148基础图+8主图修正+33视角/语义修正共189请求，无传输重试；38个选入derivative，原图未覆盖。主图输入改善了模式区分但跨view仍有陈设移墙和细节机位主图化；强geometry+局部appearance能恢复取景，却可能削弱Creative概念，不能包装为完全成功。Faithful三残留失败：厨房VIEW05气灶圆盘、母亲卧室VIEW05椅子/邻物、次主卫VIEW02门外结构；一次视觉修正后停止。家具/设备语义的局部ref应明确真实机制，不要仅用材质crop，后续改进需用户指定。详见docs/whole-house-three-modes-v3-final.md和本地FINAL_REVIEW.json。

## 2026-10-10 资产复用模型试点

业主认可 appearance_match_v2 的颜色 / 材质有较大进步，家具样式和质感仍需改善；要求永远先找可借鉴方法，再自研缺口。已授权制作客厅与厨房一版资产复用模型。asset_model_v3 实际下载 &Tradition Fly SC2 官方 OBJ 与 Poly Haven rough_linen / ash_veneer 原生 Blender 材质文件。先做隔离供应商测试，再按原包络复用八个软包分件，保留原木框 / 布局 / 数量，不加入额外抱枕。原生材质含反射强度、纤维方向、粗糙度和位移方案，不能再把只有三张图的手调 shader 称为完整供应商材质。

终端 assets-library TLS / DNS 失败已通过正常浏览器下载解决；API files 元数据可定位原生 .blend 及完整 include 依赖，校验上游 MD5 并保存本地 SHA256。不是所有库里的预览资产都已本地验证。资产适配及材质代码、单件测试和五张实渲见 docs/c-type-asset-model-v3-review.md。977 个登记源对象不变，八个新软包包络校验通过。Kitchen 灶具只按官方参考补可见机制，SKU / 安装数据仍未确认。V3 当前为 HUMAN_REVIEW，不能自动推广其他房间或声称完整 1:1 已通过。

## V3 沙发失败与整件实物优先

后续业主指出 V3 坐垫 / 背垫间隙过大、整体样式仍不符。read-only 核对确认：旧简模的坐垫 70 / 60 mm 与背垫 90 / 70 mm 间隙被当作硬尺寸保留；供应商 OBJ 分件提取漏掉对象导入旋转，深度和厚度轴交换。包络校验无法发现产品结构失真，V3 沙发不能标为通过或传播到资产库。

业主再次明确：任何家具 / 设备都先从实际出发。桌面白蜡木图册 PDF 第 8 页的 802 / 1030 有白蜡木、海绵坐包、麻棉、羽绒＋丝棉、木蜡油实物条目；同页 1028 却注明多层板加松木、科技布，不因系列标题就认定为白蜡木。先绑定实物产品或有依据的定制构造，再找同款完整资产或按同一实物建立整件。旧简模只承载有依据的空间约束，内部形状 / 间距不成为物理真值；不继续混用旧木框与别款软包再逐处修补。来源与尺寸冲突记录见 docs/c-type-product-first-workflow-2026-10-10.md 与 render_config/product_first_v1/REAL_PRODUCT_REGISTER.json。

## V4 整件重建测试：闭合室内与实物尺度

V4 客餐厅按图册与已选 A / B / C 外观建立整件定制候选；没有找到对应的完整原厂资产，不能称原厂 SKU 复刻。自建闭合 cloth pressure 原型配合缝边 / 支撑生成静态软包，座包实际缝约 7.5 / 10 mm、背包约 8 mm，替代旧 60–90 mm 简模缝。此方法已在本地 Blender 执行并检查实际形变，不认证泡棉 / 羽绒力学；家具松软感与参考一致性仍需人工评审，不作为已批准资产传播。

加入环境后暴露旧 `03_EXISTING_CEILING` 集合 `hide_render/hide_viewport` 均开启，室内顶面出现天空照明。只检查单个顶板的可见性会漏掉父集合与 View Layer 排除。V4 恢复原集合 / 层可见性，天花网格不改，两处向上射线实际命中 `CEILING_LOWER` 的 z=2.8 m；恢复闭合室内后重新 lookdev，不能靠环境亮度、曝光或假补光掩盖漏顶。

图册 6010A 餐椅 560×560×850 mm 大于旧 400×400 mm 示意椅。按真实尺寸建立整件椅后与桌柱发生适配问题，测试摆位每侧外拉 180 mm，静态椅桌无网格穿插、扶手至桌底约 54.5 mm。此结果不代表拉椅通道或人体膝脚空间已通过，也不代表用户已采购该椅。实际产品比预留大时保留产品比例、报告摆位差异，不能缩窄实物去满足旧示意图。证据见 `render_config/product_rebuild_v4/PRODUCT_REGISTER.json` 与 `design/product_rebuild_v4/VERIFICATION.json`。

## V5 木色 / 布套：资产标签不等于合适外观

业主继续指出 V4 偏白、细密直纹与自然木色参考不符，软包仍薄平。先打开供应商原图再归因；原 `ash_veneer` 的均匀细直纹就是源图特征，不能凭成图先认定纹理方向转错。新的公开白蜡木程序材质经 CC0、完整贴图及本地渲染核查，也出现粗重板纹；不能把通过下载 / 材质导入等同于符合目标。固定房间相机、灯光、曝光再比较木色 / 纹理，成功配方仅记录为本轮候选，不将浅原木解释为漂白，也不把未知供应商物理尺度或程序图宣称为实物扫描。

布料过多松量造成整面褶皱，降低松量后仍需比较实际靠垫丰满度，不以“有褶皱”宣称更真实。细分曾令座包缝从 7.5 / 10 mm 变成 16.6 / 19.0 mm；验收须在最终细分 / 修改器状态下测量外包络和承托接触，必要时在细分后恢复目标边界。V5 保留 2% 布套松量候选与正确缝距，软包总体外观仍待人审，未获整件高精度实物验证，不进入 OWNER_ACCEPTED 资产库。详见 `docs/c-type-lookdev-v5-review.md` 和 `render_config/lookdev_v5/SOURCE_REGISTER.json`。

## 2026-10-11：V5 木色保留，软包未接受

业主明确木色明显改善、软包几乎无改善。V5 不再把软包标成待认可的成功改进；木色与软包分项记录，不能将一项正面反馈升级为整个模型通过。新研究核查到与此相近的社区案例：Cloth Brush 过度扭曲后用褶皱 alpha 定点雕刻，但评论仍指出凹陷被做成凸起。真实感要求参考约束的形体 / 凹凸方向与实际布艺检查，不是褶皱数量。

已核查 Blender Guru 完整课程、Blender 官方工具、厂家泡棉芯 / 柔软包覆与分仓靠垫构造，以及 MD 的纸样 / avatar / garment / 拓扑整理路线。下一轮先分别建立坐包与靠垫的大形、冠部、侧围及承托关系，再模拟 / 局部雕刻、缝口和材质；通用气体 Pressure 原型不能自动复现泡棉与羽绒。研究未在本项目实施，外部示例状态为 PAGE_VERIFIED，不称 CYCLES_VALIDATED。教程完整模型的纹理可能仅授权用于原模型，不能因模型免费就移植其材质。详情与来源见 `docs/c-type-sofa-softness-research-2026-10-11.md` 及 `render_config/sofa_softness_research_v1/SOURCE_REGISTER.json`。
