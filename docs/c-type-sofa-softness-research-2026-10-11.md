# 沙发软包：实际问题案例与可借鉴路线

2026-10-11。业主确认 V5 木色明显改善，认为沙发软包几乎没有改善，要求先上网研究类似问题与成熟解决办法。本轮只检索 / 核查网页、现有脚本与来源，未启动 Blender、未改模型、未渲染、未调用 Image2、未购买 / 安装软件。

## 结论

有成熟办法，但蓬松感主要来自填充体积、轮廓、缝口和受压关系；布艺材质负责纱线、微表面与纤维反射。参考资料支持「真实构造与大形 → 布套 / 局部雕刻 → 缝线 → 材质」路线。压力模拟可用于生成形态，却不能将一个通用鼓包自动变成指定实物沙发。

V5 木色保留为业主正面认可的外观方向，尚非实物涂装样板或采购确认。V5 软包标为业主不接受，不传播到家具库。下一步针对软包本体，不继续调木色或重跑全屋。

## 核查过的案例与方法

| 来源 | 真实问题 / 处理 | 可借鉴与限制 |
|---|---|---|
| [Blender Stack Exchange：Best workflow to create creases/folds on chair?](https://blender.stackexchange.com/questions/338581/best-workflow-to-create-creases-folds-on-chair) | 作者已完成椅子主体，但 Cloth Brush 过度扭曲网格、褶皱不可信。最终用灰度 wrinkle/fold alpha 作为 Draw 雕刻笔刷，调尺寸、强度、旋转，逐处匹配参考，并发布结果。评论指出参考是凹陷，而作品做成凸起，仍会影响真实感。 | 本轮阅读完整提问、回答与关键评论，并打开作者前后两张图。作者报告成功不等于已达完美；笔刷适合定点中尺度褶皱，不能替代饱满的大形，也不自动授权下载任意笔刷包。 |
| [Blender Guru：How to Make a Couch in Blender](https://www.blenderguru.com/posts/couch-william) | Part 2 处理坐垫网格 / 压力与定制褶皱；Part 3 用 Cloth Brushes 雕刻、Face Sets 处理缝口；Part 4 做坐垫；Part 5 导入布艺贴图并补细褶皱；Part 6 做缝线。 | 页面明确将模拟、雕刻、材质、缝线分开。已阅读作者课程说明与章节点；未逐帧观看全部视频或在本项目复现。适合作为优先学习路线，不能照搬旧 Blender 数值。 |
| [Blender Stack Exchange：Long cushion for lounge chair or sofa](https://blender.stackexchange.com/questions/326298/long-cushion-for-lounge-chair-or-sofa) | 用户问连续坐背垫的转折如何形成。回答先建立包含转折的网格及局部 pin group，再用压力膨胀，适时应用 Cloth，挤出侧边面环做缝口，最后细分。 | 说明要先建立对象特有的折线 / 支撑 / 缝口。回答的 Pressure=1 和关闭重力属于该例，不是沙发通用成功参数。 |
| [Learn Arch Viz：Model Perfect Wrinkled Cushions…](https://www.learnarchviz.com/single-post/2019/05/05/model-perfect-wrinkled-cushions-furniture-with-marvelous-designer-and-3ds-max) | 作者长期寻找既有自然褶皱又保持可编辑拓扑的方法。路线是基础模型与简单展开 → 在 Marvelous Designer 中作为 avatar 和由展开生成的 garment → 修缝合 / 模拟 → 回到 Max 用 conform 等工具重拓扑，再补细节。 | 已读取具体文本流程；这是 MD8 / Max 的历史案例，可借鉴“内形支撑 + 布套纸样 + 整理网格”的思路，未在 Blender 5.2 测试。不是宣称必须换软件。 |
| [Marvelous Designer 官方：Pillow](https://support.marvelousdesigner.com/hc/en-us/articles/47358258513177-Pillow) | 官方课程明确分别制作 pillow 与 pillow case，并用压力处理形态和褶皱。 | 确认专门的布套 / 纸样路线存在；网页说明简短，未据此推断完整泡棉或羽绒求解。没有安装 / 订阅。 |
| [Vanguard 厂家：Cushions](https://www.vanguardfurniture.com/CushionOptions) | Relaxed Down 坐垫为泡棉芯 + 聚酯包覆 + 羽绒 / 纤维外套；Feather Lux 靠垫则将混合填充吹入保持形态的分仓。其它结构明确强调 Comfort Crown 和 loft。 | 厂家证据说明坐垫与靠垫构造不同，表面柔软包覆和中心支撑可共存。本户图册 p8 同样列海绵坐包、麻棉、羽绒＋丝棉，但未提供完整分层剖面。Vanguard 比例不能当本户采购规格。 |

## 官方工具与实际材料

- [Blender 5.2 Cloth Pressure](https://docs.blender.org/manual/en/5.2/physics/cloth/settings/physical_properties.html#pressure) 明确以气体方式模拟软壳内部流体；Internal Springs 可使网格表现类似 Soft Body。它并非泡棉 / 羽绒材料模型。为了静态 ArchViz，不必逐根模拟羽毛；需要复现可见的填充体积与外套受力形态。
- [Blender 5.2 Cloth Brush](https://docs.blender.org/manual/en/5.2/sculpt_paint/sculpting/brushes/cloth.html) 提供 Local / Dynamic 模拟区、Pin Simulation Boundary、Persistent Base、Push / Pinch / Inflate / Grab 等，以及 Soft Body Plasticity 保留原形。可以结合传统雕刻，局部处理边缘受压与缝口；全局铺褶皱不等于自然软包。
- 教程使用的 [Poliigon Moss Plain Weave Upholstery 4314](https://www.poliigon.com/texture/moss-plain-weave-upholstery-fabric-texture-green/4314) 当前页明确为细密平纹、哑光、微小纱线密度变化，物理尺寸 50×50 cm，1K–8K，JPG/TIF，12 个文件，支持 Blender。网页已核查，未购买 / 下载 / 本地测试。其绿色及物理尺度只属于该材质，不能照搬到我们的米白麻棉或取代实物布样。
- 教程另有 [完整 Williams Couch 学习模型](https://blenderguru.gumroad.com/l/WilliamSofa)，页面当前标 CA$0+，ZIP 含 couch.blend 及贴图。模型标 CC-BY 4.0，同时注明品牌形象 editorial 限制，Poliigon 纹理只用于提供的模型、不可复用于其它模型或重新分发。可作为形态 / 拓扑学习基准；未走领取流程、未下载，不能直接把该纹理搬到本户沙发或擅自将另一款整沙发替换进住宅。

上述新资料状态为 PAGE_VERIFIED / EXTERNAL_EXAMPLE，社区前后图已打开；均不是本项目 CYCLES_VALIDATED。搜索摘要和 AI Overview 不作为结论证据。

## 为什么我们的 V4 / V5 几乎没改善

现有脚本与用户反馈支持以下判断，它们是本项目诊断，不是外部教程对本模型的认证：

1. V5 从 V4 的通用压力鼓包生成坐垫 / 靠垫，再按各分件三轴边界归一化。坐包仍限制为 155 mm 厚，背包仍为 1027×296×214 mm 的局部分件。改变松量主要改变浅表褶皱，中心冠部、侧围厚度和靠垫整体轮廓仍被旧形状强烈约束。
2. 未建立本户实物的“坐包芯 + 柔软包覆 + 外套”和“靠垫填充袋 + 分仓 / 缝口”各自的大形，仅有内部弹簧和压力原型；因此不能把模拟执行成功当作填充结构复现。
3. 承托及缝距的数值检查发现并修复了回归，但它们证明的是接触与尺寸，不证明照片中的蓬松形态。后续必须检查正 / 侧面轮廓和同材质的参考对照。
4. 当前布艺已有完整 4K 亚麻材质，继续增大 bump / sheen 或换几组 roughness 不能改变大形。若网格轮廓像薄垫，远景仍像薄垫；细织纹也不应被放大为可见条纹去“补”蓬松感。

旧内部厚度和分块若没有实物依据，不能升级为 Ground Truth。另一方面，任何超过已确认整体占地 / 高度或需要改变木框的方案，应记录真实产品与预留的冲突；研究阶段不据此直接改尺寸。

## 推荐的下一轮试点

优先找与业主实物 / 定制构造匹配的完整高精度资产；没有同款时，以同一套产品依据重建，借用成熟方法，不重新拼别款坐垫与旧木框。

只选本沙发的一套“坐包＋背包＋对应承托”进行隔离试点。先以灰材质匹配真实冠部、侧围、靠垫饱满度 / 倾斜和接触受压；坐包与背包采用不同构造。形态不能像原来的薄平垫时才进入缝口、局部雕刻与布艺。局部褶皱必须对应参考中的来源、位置与凹凸方向，保留大面积平顺表面。布艺最后按真实纱线尺度、完整节点与实际灯光检查，不能用材质掩盖轮廓。

以正面、侧面和三分之四视角检查，灰材质 / 最终布艺分别比较。若该局部试点没有可见的轮廓改善，停止传播；若正确形态需要改动原预留总高或木框，先明确冲突。木色保持 V5，不改建筑，不跑全屋，不调用 Image2。

优先推荐 Blender 内完成“有依据的大形 + 局部雕刻”，可借鉴 Blender Guru 与社区实例；若真实缝合 / 布套松量难以控制，再考虑 MD 纸样路线或合适成品资产。MD 不是这次研究的安装或购买决定，程序压力的填充精细力学求解也不是静态效果图的必需前置步骤。

## 保留与交付状态

研究报告与来源登记保存；九项模型 / Ground Truth / 图册哈希在开始与结束核查。未生成新模型或效果图。

TASK STATUS: RESEARCH_COMPLETE / MODEL_UNCHANGED。分支 `codex/c-type-sofa-softness-research`；源码只包含研究、来源与人工反馈记录。PR 若仍因 GitHub CLI 未登录受阻，按项目要求如实报告，不自动合并。
