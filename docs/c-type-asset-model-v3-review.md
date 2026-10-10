# 客厅与厨房 · 资产复用精细模型 V3

**2026-10-10 后续复核：V3 沙发整体造型未通过，禁止作为已验证家具库资产传播。** 用户指出过大软包缝隙；read-only 核查确认旧坐垫间距 70 / 60 mm、背垫 90 / 70 mm 被继承，且 OBJ 分件提取未应用导入旋转，深度 / 厚度轴交换。此前数值包络检查通过不构成真实产品造型通过。当前文件作为失败证据保留；新沙发实现改从业主真实图册绑定整件产品 / 构造，见 c-type-product-first-workflow-2026-10-10.md。厨房及材质的历史记录保留，不因此升级为人工接受。

TASK STATUS: HUMAN_REVIEW。已制作一版独立可编辑模型与五张实渲，待业主逐项外观验收。未认定达到全部 1:1 外观目标。

BRANCH: codex/c-type-asset-model-v3。采购 / 安装：无付费购买或插件安装。Image2：0 次，未重启全屋队列。

## 实际采用的新路线

下载并核查 &Tradition Fly SC2 官方包，OBJ 中等精度为 34594 顶点、33450 面、46 个连通部件，带 UV。完成隔离灰模及原始供应商材质实渲后，复用两个软包原型：坐垫部件 41、背垫部件 43，适配现有三组沙发坐垫 / 三组背垫 / 躺椅坐垫 / 躺椅背垫共八件。原木框与数量保持；不引入供应商额外抱枕。大尺寸座垫延长内部面板、保留边缘区；软包按实际尺寸重新做物理 UV 密度。

实际下载 Poly Haven rough_linen 与 ash_veneer 原生 .blend 和完整贴图依赖，保留其节点、反射、roughness、normal、纤维方向、sheen、位移设置；使用 .3 m 亚麻 / 1 m 木纹尺度。亚麻只做燕麦米白色调整，主要贴图换为 4K；木纹沿构造方向。供应商原方案保存在单件测试文件中用于比较。可追溯登记为 render_config/asset_model_v3/IMPLEMENTATION.json。

厨房使用消息字面指定的开放式厨房。冻住房间布局、柜体位置、数量、台面高度、设备中心、窗洞和标高，深化柜门边缘、金属、双燃气灶锅架 / 火盖 / 旋钮、烟机滤网 / 控制区、柜下灯槽及光源。设备细节依据已有方太官方参考，SKU 尚未确认。缺合适 CC0 双燃气灶资产时只补机制，不拿电灶模型替代。安静浅色台面在检索库未找到合适款，保留本项目定制石材基线，注明非供应商扫描材质。

## 审阅结果

供应商分件使背垫从规整圆角块改为有浅褶皱、松弛和收边的软包；坐垫边缘和织纹更清晰。厨房设备从平面炉圈深化为有锅架、阶梯火盖和旋钮的燃气灶，金属 / 木材 / 浅色台面分开。

仍需评审：供应商背垫的松弛形态是否足够接近 A Faithful；白蜡木的饰面与实木端纹差异；软包厚重感、实际选购面料，以及厨房台面与光照层次。画作、地毯图案与现场窗外景观不是本轮实现重点，维持 V2，仍未逐项完成复现。家具造型与照片感的判断不能由源哈希或采样数替代。

## Gates / Ground Truth

- 六个最初保护模型与厨房冻结清单的二十个文件 SHA256 保持。
- 独立进程重新打开验证：1826 个既有网格和世界矩阵保留，977 个登记源对象不变。
- 八个资产软包适配在原尺寸包络内。躺椅倾斜后的约 3 mm 顶部越界已修正；源码、重新打开数据和图像均反映修正。
- 厨房原灶具平面符号顶 844 mm；新锅架顶 878 mm，作为所需真实机制的展示层细化，未改变源符号或冻结设备点位。它不构成设备选型、开孔、锅底 / 烟机净距和安全安装认证。
- 厨房柜门的小倒角 / 法线在派生修改器中；基础网格保留。形态检查使用完整闭合建筑和真实机位，不隐藏墙 / 天花伪造画面。
- 30 张图像打包，无缺失依赖。模型约 370 MB，二进制与扫描图本地保存；聊天与网页只使用小 JPEG 评审图。
- Workbench 五视角已打开联系表；最终五张 Cycles 实渲已打开联系表及近景，网页正常显示。
- Blender 5.2.1 LTS，Apple M4 Metal GPU，128 samples，OIDN GPU High / Accurate，AgX Medium High Contrast，曝光 +0.15，五张 1920×1080。最终时间以 review_renders/render-manifest.json 为准。

## Generated artifacts

可编辑打包模型：projects/c_type_home/design/asset_model_v3/LIVING_KITCHEN_LIBRARY_V3.blend。

供应商原始测试：SUPPLIER_NATIVE_TEST.blend；原生材料测试图：SUPPLIER_NATIVE_MATERIAL_TEST.png；灰模：geometry/；实渲：review_renders/；总览：V3_REVIEW_CONTACT.jpg；数值验证：VERIFICATION.json；来源适配：BUILD_AUDIT.json。第一次完整候选保留在 first_candidate_preserved/。

网页：http://127.0.0.1:5188/asset_model_v3/review_gallery.html。

## Source / 后续

源码仅含 inspect / native material test / build / verify / render / package 脚本、小合同、评审说明与资源登记，未提交模型、原厂纹理、扫描图或生成图。

重新运行需要保留当前 V2 输入及登记哈希的官方 OBJ、原生材质 / 贴图。顺序：inspect_supplier_fly_sc2_v3.py → inspect_native_materials_v3.py → prepare_supplier_test_v3.py → build_asset_model_v3.py → verify_asset_model_v3.py → render_asset_model_v3.py -- review_renders → package_asset_model_v3.py。原材质测试和当前模型的节点适配均可复查，后续先复用本轮已经验证的导入 / UV / 材质流程。

NEXT ACTION: 人工比较参考、V2、V3 主图和软包近景，决定是否保留新软包形态及材质方案，随后只修具体差距。当前阶段不自动扩展其他房间。
