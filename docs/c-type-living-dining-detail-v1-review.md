# 客厅餐厅精细模型 V1 · 首轮评审

TASK STATUS: HUMAN_REVIEW_PR_BLOCKED。已制作可编辑独立候选和五张实际 Cycles 渲染，不宣称选定参考已逐项精确复刻。

BRANCH: codex/c-type-living-dining-detail-v1。PR 创建因本地 GitHub CLI 未登录而受阻；不改变认证设置。

## 已实现

客厅选定木框 L 沙发、窗边躺椅、双层茶几、长开放低柜；加入 Designer 方向的浅亚麻窗帘、几何地毯、东墙画。无 Creative 元素，未自动增加落地灯、搭毯、摆件。餐厅使用原 1600×800×750 mm 包络的跑道形桌面、窄双支撑、四把原位椅子及可擦洗圆润吊灯候选，无挂画。

木框支撑、坐垫、缝边、桌板厚度、柜板和灯罩内外壳分别建模，共 173 个新增展示部件。用本地木甲木乙图册指导木框与家具构造，扫描贴图来自已有 CC0 Poly Haven ash_veneer、rough_linen；颜色明确统一至浅原木和米白，窗口外为中性展示背景。画作和地毯为代码绘制的原创近似图案。

## Gates / Ground Truth

- 独立 Blender 5.2.1 进程重新打开通过；977 个登记源对象的网格及世界矩阵一致。
- 计算后几何包络校验通过：沙发、躺椅、茶几、餐桌未超出原约束（3 mm 容差）；四把椅子平面尺寸不超过 400 mm。
- 原模型、北阳台候选、R4、B0 文件 SHA256 均与前值一致。
- 打包 9 张图像；没有缺失图像依赖。来源二进制、生成二进制及渲染留在本地，不进入 Git。
- Cycles，Apple M4 Metal GPU，128 samples，OIDN GPU 开启，AgX Medium High Contrast，曝光 +0.25。四张 1920×1080，餐厅主视图 1440×1920。
- 五张最终图片已打开检查，浏览器评审页正常显示。

## Generated artifacts

模型：projects/c_type_home/design/living_dining_detail_v1/LIVING_DINING_DETAIL_V1.blend。

渲染：同目录 final/；验证：BUILD_AUDIT.json、VERIFICATION.json。

网页：http://127.0.0.1:5188/living_dining_detail_v1/review_gallery.html。

## Known issues / 下一步

本轮几何与外观方向稳定，视觉完成度仍低于参考图：软包与窗帘褶皱较规整；画作与地毯只复刻配色和构图方向；日光层次尚需进一步 look development。椅子按真实源和图册基线，不自动采用 Creative 藤编扶手椅。灯罩已做可擦洗候选，具体 SKU 和材质实样未定；现场景观未重建。腿部空间、椅子拉出与施工安装仍需动态/现场评审，静态包络验证不等于产品制造和安全认证。

展示层隐藏了与低柜重叠的 READING_3205A_PADDED_BENCH，源几何保留。北阳台静态 50 mm 身高差未升级为动态防碰头结论。其他房间和此前阅读角移位、书房挂画不属于本轮实现。

下一步：业主对照参考评审这一轮，再在同一候选内细化软包、布料、画作和光照；不批量重跑 Image2。
