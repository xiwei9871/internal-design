# V9：布套材质能否改善填充松软感

2026-10-11。业主指出“褶皱现在出现了，但是松软感还没出来”，要求查一般沙发坐垫与靠包材料，先验证修改材质是否优化。暂停几何加码，保持 V7 网格和 V8 方向光，做 A 原布艺 / B 微纤维表面层对照。

## 结果

网页：<http://127.0.0.1:5188/sofa_material_pilot_v9/review_gallery.html>。原生整体与近景各一对，模型、贴图、颜色参数、UV、灯光、相机、曝光与色彩管理一致。

实际已打开联系表、1500×1200 整体和近景检查。B 更亮、反射更柔和，部分浅褶皱被淡化；填充体积、下沉、侧围轮廓未改善。自评关键蓬松目标未通过，保留 A 原材质，B 只作实验记录。该结论只针对本轮纤维层调整，不能泛化为材质对所有松软观感都无作用。

B 独立模型：`design/sofa_material_pilot_v9/surface_test/SOFA_SURFACE_FIBER_TEST_V9.blend`，SHA256 `06c26fdf852cb14bd3c3069d8fc4c354fde0c9096bdf840bd63192afa3500dd4`。没有写回源模型、全屋或资产库。

## 已核查的真实构造

实际读取 [Vanguard Cushion Options](https://www.vanguardfurniture.com/CushionOptions) 的 Spring Lux、Majestic、Feather Lux、Bliss 与 Relaxed Down 条目。它们明确把坐芯和靠包分别设计，提供从 Firm 到 Soft 的不同构造；不是一套布料参数决定软硬。

| 部位 | 常见厂家实例 | 本项目的含义 |
|---|---|---|
| 坐垫 | 聚氨酯泡棉支撑芯，聚酯包覆；可加羽毛 / 羽绒 / 纤维混合外套或弹簧芯 | 中心支撑与外层柔软可以共存。泡棉密度单独不能定硬度 |
| 靠包 | 较松的聚酯 / 超细纤维或羽毛 / 羽绒 / 纤维混填，装入保持形态的分仓 | 靠包不必采用坐芯同样的实体芯；松填充与分仓影响堆积、下沉和回弹 |
| 布套 | 棉麻、合成混纺等家具布 | 光学材质决定织纹、反光、纤维感；不直接令静态内部填充变软 |

业主图册第 8 页的海绵坐包、麻棉、羽绒＋丝棉与这个分层思路一致。准确 SKU、丝棉具体成分、泡棉硬度与制造剖面仍未确认。厂家实例不是本户采购配方。

## 成熟方法与有控制的试验

复用项目已验证的 Poly Haven rough_linen 原生 Blender shader、完整 4K 贴图和 0.3 m 物理重复尺度。只读搜索 cotton fabric / linen；Fabric Pattern 05 公开页显示卡其＋蓝色窗格纹，虽有 CC0 和 0.5 m 尺度，仍不符合素色棉麻方向，未下载。没有购买、安装或将不相符资产强行套入。

实际读取 [Blender 5.2 Principled BSDF](https://docs.blender.org/manual/en/5.2/render/shader_nodes/shader/principled.html#sheen) 的 Sheen、Diffuse Roughness、Subsurface、Specular 和 Coat 定义。Sheen 是微小表面纤维反射层，不是填充硬度。保留所有原生贴图与连线，复制布艺材质，仅将 Sheen Weight 0.2→0.5、Sheen Roughness 0.5→0.8；SSS / Coat / Transmission 保持 0。公开声明这是测试值，不是实测材料常数或供应商已验证的棉麻成品配方。结果不符合目标，因此不进入成功配方库。

## 验证与范围

三个新 PNG（A 近景、B 整体、B 近景），复用一个既有 A 整体基线，全部 1500×1200、Cycles / Metal / 64 samples / OIDN GPU High Accurate，新增实渲合计 55.53 秒。加入同一近景相机，不变更既有相机。

独立重开比较：70 个原对象、54 个原始及评价后网格、UV、Shape Key、变换、曲线、灯光、World、已有相机、曝光与色彩管理保持。两个布套材质槽换到副本，副本与原图仅两项 Sheen 输入不同。12 项保护哈希不变，18 张图像打包无缺失。几何不变，复用 V7 已验的闭合 / 接触 / 无穿插证据；没有冒称测试了填充力学。

当前仍是未批准适配的 810 mm 总高 / 483 mm 冠部试点。用户说坐垫支撑应较强、靠包更软，不授权变更最终住宅尺寸、实际产品或批准 V7 整体形态。

下一阶段若继续，应分别校准坐芯与柔软包覆的外形、靠包松填充 / 分仓的外形，在同样布艺与光照下复核；暂不继续增加褶皱或传播全屋。

TASK STATUS: HUMAN_REVIEW_PR_BLOCKED。BRANCH: `codex/c-type-sofa-material-test-v9`。PR: GitHub CLI 尚未登录，创建受阻。FILES CHANGED: 只提交渲染诊断 / 材质试验源码、研究与反馈；未完成形体源和所有二进制留在本地。GROUND TRUTH: 十二项保护哈希不变。GATES: 技术通过、蓬松改善未通过。KNOWN ISSUES: 填充大形未解决，最终坐高 / 采购 / 适配未批准。NEXT ACTION: 人工查看材料事实和对照，保留原布艺，不自动推进。
