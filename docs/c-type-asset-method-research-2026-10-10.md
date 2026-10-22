# C-Type 家具与材质资料研究 · 2026-10-10

本轮只研究资料与维护工作规则，没有启动 Blender、Image2、改模型或购买资产。业主认可 V2 的颜色与材质有较大进步，同时指出家具样式和质感仍与选定效果图存在明显差距。后续实现必须先查找可借鉴的成熟方案；合理检索后仍无合适来源，才自研缺口。

## 结论与推荐路线

采用「真实产品资料 + 成熟家具资产 + 成套材质及官方导入方法 + 固定测试场景」的混合流程。下一轮优先解决沙发和躺椅的造型、软包轮廓与布料物理表现。继续在简化圆角盒子上叠加参数，不足以取得参考图中的坐垫蓬松、缝边受压、背垫倾斜和自然褶皱。

不能因为一个资产宣称 photorealistic 就认定它在我们的 Blender 5.2 / Cycles 中验证成功。本轮确认了真实来源与方法，所有新家具候选仍处于 PAGE_VERIFIED，尚未导入或实渲验证。保留已选家具外观和真实尺寸，不能为使用库存模型擅自换款。

## 1. 家具模型：优先顺序及已查证候选

优先：业主本地产品图册 / 对应品牌官方 3D → 同类且造型相符的原生 Blender / 精细 OBJ 或 FBX → 在合适模型上做有限尺寸适配 → 对找不到的部件定向建模。品牌文件可能仅服务 BIM / CAD，需要检查文件，而不自动当作精细渲染资产。

| 来源 / 具体候选 | 本轮实际核查 | 可借鉴什么 | 使用边界 |
| --- | --- | --- | --- |
| 本地木甲木乙白蜡木系列 | 已有 32 页产品图册和前轮家具裁图，家具 reference 的首选 | 与业主家具一致的木色、木框、扶手、靠背与做工 | 是产品图片参考，目前未确认对应精细 3D 文件；不能说本地 CAD 家具包就是精细资产 |
| [&Tradition Fly SC2 官方产品](https://www.andtradition.com/products/fly-sc2) | 页面含实物图、规格、结构材料和 2D/3D ZIP 下载入口；1620×800×700 mm，座高 400 mm；橡木框、HR 泡棉 / 羽毛枕、布艺 | 松弛背垫、软包与硬木框分离、木工支撑，官方真实尺寸和多角度机制 | 它是橡木，不是本户白蜡木；款式亦不同。是几何方法 / 可评估资产来源，不能自动替换已选 L 沙发。下载 ZIP 的终端网络失败，未检查包内格式 / 网格 |
| [Design Connected Fly SC2](https://www.designconnected.com/de/Seating/Benches/fly-sc2_p6298) | 商品页和预览已查看；标 Polygonal / Photorealistic，Materials、Textures、UVW Mapped 为 Yes，Adjustable 为 No；购买弹窗当时显示单件 €8（原价 €24） | 比手工圆角块更成熟的背垫轮廓、分件和 UV；作为资产选型及软包质量基准 | 未购买、未下载；单件具体可交付格式、当前授权和本地 Cycles 材质兼容性仍需验证。价格是检索时显示，不是报价承诺 |
| [Design Connected GE 290 3-seater](https://www.designconnected.com/Sofas/3-seater/ge-seater-sofa_p4395) 及 [Plank Chair](https://www.designconnected.com/Seating/Armchairs/hans-wegner-plank-chair_p7047) | GE 290 家族页与沙发商品预览已查看，木框 / 薄扶手 / 倾斜靠背与当前方向较接近；页面 Materials / Textures 为 Yes，UVW Mapped 为 No，Adjustable 为 No | 木框结构、靠背角度、沙发与休闲椅家具家族；比 Fly 更接近直线木框语汇 | 不能假设可直接贴布艺；缺 UV 与非参数化适配增加工作量。Plank Chair 仅确认家族入口，尚未独立检查文件和完整详情；保留为结构参考候选 |
| BlenderKit / CGTrader / 3dsky | 前轮检索发现木框沙发条目；BlenderKit 入口遇安全验证，CGTrader 具体页未能取得完整可读详情 | 后续在厂家无合适模型时再补充模型筛选 | 尚未核实合适资产；不凭搜索摘要称其可用，不绕过安全验证。3ds Max / V-Ray / Corona 格式不能直接等同于 Cycles 可用材质 |

厂家 3D 入口：[Fly SC2 2D/3D package](https://assetslibrary.com/asset/f7356e45-57ee-4277-a375-04fd01042bb6/ATD_2D-3D-Packages_Fly_SC2.zip)。链接来自官方产品展开的 Downloads，不是猜测地址。本轮 urllib TLS EOF、随后 curl DNS 失败，停止下载；没有导入模型、执行文件或伪称成功。

筛选重点：正面 / 侧面 / 背面和线框，坐垫轮廓与缝线是否来自几何、木框是否有真实连接、纹理与 UV、真实单位、当前渲染引擎、修改与项目使用授权。优先 .blend；OBJ / FBX 能转入几何，但 V-Ray / Corona 参数需要转换与复核。仅有 .max 且无可用交换文件的资产不是当前首选。

## 2. 材质：复用完整方案，避免照抄几组数字

| 已验证的官方资料 | 查明的事实 | 对本项目的直接意义 |
| --- | --- | --- |
| [Poly Haven Ash Veneer](https://polyhaven.com/a/ash_veneer) | CC0；实物尺度标 1 m wide；含 Diffuse、Rough、Normal GL、Displacement、AO；低光泽、细直木纹的贴皮扫描 | 已有资产可继续复用，但按官方尺度映射；顺纹面、边面与端面分别处理。贴皮扫描不能自动表达实木端纹、木工接缝或涂装膜层 |
| [Poly Haven Rough Linen](https://polyhaven.com/a/rough_linen) | CC0；colormass Photography / Rico Cilliers Processing；尺度标 0.3 m tall；完整下载选项包括 anisotropy rotation / strength、spec IOR、displacement、normal、roughness、diffuse 等 | 我们只用了其中部分图；下一轮先检查完整材质方案与实际尺度，再校准燕麦米白色。V2 的 1.8 次 / m 手调比例与 0.3 m 的垂直扫描尺度需要复核，不能继续凭观感扩大织纹 |
| [Poly Haven Blender Asset Browser](https://polyhaven.com/plugins/blender) | 官方文档说明可拖入 HDRI / 材质 / 模型；Fix Texture Scale 用资产尺寸与网格面积校准；支持 displacement setup。资产免费，便利插件本轮页面显示 Patreon $5/月或一次性 $49 | 可以借鉴官方建材 / 比例 / 位移方案；不必为免费贴图强制买插件。插件如采用属于后续决策，本轮未安装 |
| [Poliigon Blender Addon 官方帮助](https://help.poliigon.com/en/articles/6342599-poliigon-blender-addon) | 文档标支持 Blender 2.83+（含 5.x）、Cycles / Eevee；自动材质节点、贴图分辨率 / 投影 / 比例 / 16-bit / 物理位移，位移强度以米计；优先 .blend 模型，可复用已导入材质；路径追踪 AO 默认关闭 | 成熟的材质导入与管理路线，优先现成可编辑的 Cycles 材质而非重写连接。资产可免费或付费；未安装、未登录、未购买，也未验证具体布艺 SKU |
| [Blender Principled BSDF 官方手册](https://docs.blender.org/manual/en/latest/render/shader_nodes/shader/principled.html) | 当前手册基于 OpenPBR；IOR Level 的 .5 是不调整，0 去反射；Sheen 模拟表面微纤维；Coat 独立涂层；法线、粗糙度、透光承担不同作用 | 使用官方物理含义和供应商完整节点作为起点。老 Blender 或 V-Ray 教程的“specular .2 / roughness .5”不能不分版本照抄；Sheen 无法让一块平板变成羽绒坐垫 |

可复用的应是**完整材质资产**：扫描图、物理尺度、色彩空间、法线方向、UV / 切线、涂层 / 纤维节点及参考渲染。粗糙度的最佳表现依赖表面、灯光与版本，不能承诺一组全屋通用数字可直接得到参考图。先保留供应商基线，再仅调整必要的色调和饰面；不要一开始压平扫描的色差、roughness 或 normal。

## 3. 布艺与木材的几何尺度分工

- 远处可见的坐垫厚度、边角、缝边、背垫倾斜、下垂和接触受压：来自模型轮廓与几何，优先成品软包模型或厂家模型；找不到时再用成熟的缝合 / 压力 / 布料模拟流程，而非任意周期正弦扰动。
- 中等距离的浅褶皱：合适扫描 normal / displacement 与几何细化共同处理，保持坐垫底部与框架接触。
- 近处纱线、木孔：成套 PBR 和真实比例，法线 / 微位移承担微结构；纤维边光 / 哑光反射与涂装另做材质层。
- 木色：厂家 / 图册在中性光下的颜色与已选渲染的受光后外观分开。不能把效果图里的亮部 RGB 直接当线性 Base Color。

方法依据：[Blender Cloth 设置](https://docs.blender.org/manual/en/latest/physics/cloth/settings/index.html)、[Pressure](https://docs.blender.org/manual/en/latest/physics/cloth/settings/pressure.html)、[Blender Color Management](https://docs.blender.org/manual/en/latest/render/color_management.html)。这些列为后续实施文档入口，本轮主要核实了 Principled、供应商资产和导入文档，尚未做布料模拟。

## 4. 下一轮的具体顺序

1. **模型选型**：先把本地产品图册、已选 A 家具外观和两类资产候选做造型对照。筛出木框 / 扶手 / 坐垫符合的资产，确认格式与授权。找到现成合适款之前，不开新的全屋建模。
2. **单件资产验证**：在隔离测试文件里打开一个沙发或一个坐垫，检查软包、缝线、UV、贴图和背面。先使用供应商原生材质与原测试灯光判断资产本身质量，再与参考图比形态。
3. **准确适配**：保留现有真实尺寸与家具位置。按构造调整木框长度、模块和坐垫分件；避免整件非均匀拉伸把木纹、缝线、软包厚度一并拉坏。库存模型与设计不符时只借鉴质量或做受授权的局部改造。
4. **材质基线**：采用完整扫描 / 官方导入节点，核对 .3 m 布艺和 1 m 白蜡木尺度、色彩空间、IOR / sheen / coat。保留供应商基线及差异记录，再匹配米白织物和白蜡木色。
5. **固定灯光检查**：同一中性材质测试灯光下确认木色、布纹与反射；再放回客厅同一相机，在真实窗洞和闭合天花下匹配日光方向与主辅光比。一次只回答模型、材质或灯光中的一个问题。
6. **建立自己的已验证库**：只有在当前 Blender / Cycles 中通过单件近景和客厅主图，并获业主接受，才标为 CYCLES_VALIDATED / OWNER_ACCEPTED。存为可复用家具、材质与灯光模板，附参考图、物理尺度、版本、授权、文件哈希，避免每次从零调。

建议下一轮从**沙发软包和窗边躺椅**开始；茶几与柜体继续保留准确的定制尺寸，套用通过验证的白蜡木材质和构造细节。餐桌 / 椅子的具体款式同样按已选项筛选，不能因 C 图片含藤编椅就自动认定已选该椅款。

## 保留与状态

TASK STATUS: RESEARCH_COMPLETE / MODEL_UNCHANGED。新资源尚未本地 Cycles 验证；本轮没有形成新的效果图候选。

BRANCH: codex/c-type-asset-research-v1。文件：此研究报告、来源登记 JSON、项目 / 全局工作偏好与 ArchViz 技能的“先借鉴再实现”规则。模型、贴图与 ZIP 不进入 Git。

源模型、V1、V2 的哈希在本轮开始 / 结束核对；模型未更改。没有批量渲染、Image2 调用、购买、插件安装、账号 / 密钥设置变更。
