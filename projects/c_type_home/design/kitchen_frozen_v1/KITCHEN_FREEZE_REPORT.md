# 厨房现状模型冻结 V1

冻结日期：2026-10-01（Asia/Shanghai）。状态：HUMAN_APPROVED_SPATIAL_MODEL_FROZEN；独立重开与重出图核验 PASS。

业主已确认当前几张图基本正确，本版将厨房布局、柜列、岛台、旁柜、设备相邻关系、窗体修正和图5储物柜正式收口。后续厨房工作从本版继承；更改已锁定的空间关系需要业主明确要求，并另存新版本。

## 正式入口

- [冻结母版](/Users/xiwei/interior_design/projects/c_type_home/design/kitchen_frozen_v1/KITCHEN_APPROVED_AS_IS_V1.blend)
- [冻结清单](/Users/xiwei/interior_design/projects/c_type_home/design/kitchen_frozen_v1/KITCHEN_FREEZE_MANIFEST.json)
- [尺寸台账](/Users/xiwei/interior_design/projects/c_type_home/design/kitchen_frozen_v1/KITCHEN_DIMENSION_SCHEDULE.csv)
- [模型对象/坐标台账](/Users/xiwei/interior_design/projects/c_type_home/design/kitchen_frozen_v1/KITCHEN_MODEL_REGISTER.json)
- [11张检查图索引](/Users/xiwei/interior_design/projects/c_type_home/design/kitchen_frozen_v1/KITCHEN_VIEW_INDEX.md)
- [长期上下文规则](/Users/xiwei/interior_design/AGENTS.md)

## 已锁定的关系

| 部位 | 冻结内容 |
|---|---|
| 冰箱柜列 | 门口向内：320窄柜 → 冰箱及上柜 → 内侧高柜/凹格；窄柜与冰箱前脸齐平 |
| 窄柜门板 | 四段；顶段与冰箱吊柜上下边齐平；下三段等高 |
| 主厨房 | 保留V4灶台、水槽、转角、长边柜和岛台/连接柜坐标及朝向；主台面H820/D600 |
| 冰箱 | 905×710×1700；窄柜模型深765；背部余量55（各自原确认范围已在台账注明） |
| 厨房小窗 | 对应窗体X6100–7100，跨度1000；窗台1020；比台面高200；窗顶2400 |
| 阳台蓝色窗段 | 登记图约X2100–5100，约3000；撤回4米推断；不以整段墙长代替窗长 |
| 窗下墙 | 完整保留1050高度，连续墙面；红圈部位语义为窗下墙；出图剖切不得截短它 |
| 图5储物柜 | 导引位置及1500×500包络保留；上四门、下四门、两抽屉、中部开放台；正/侧视角固定 |
| 岛台与旁柜 | 原岛台台面800×467/H960及连接段保留；600宽、2000高旁柜及上方挂机相邻关系固定 |

单位为毫米；约值、继承值和示意尺寸的证据等级见尺寸台账。冻结母版保留V4全部源对象和隐藏的历史代理，不重新解释户型。B0原始建筑基线保持独立冻结；厨房窗体使用B1现状修正覆盖层。

## 锁定机制与检验

厨房相关对象加选择与平移/旋转/缩放保护，检查相机一并保护。清单钉住母版、源V4、相机源、对象状态、来源登记和11张检查图的SHA256。对象快照覆盖网格、姿态、层级、材质、修饰器、可见状态及相机参数。

复核命令（在项目根目录执行）：

```bash
rtk proxy /Applications/Blender.app/Contents/MacOS/Blender --background --factory-startup --disable-autoexec --python-exit-code 1 --python projects/c_type_home/design/kitchen_frozen_v1/freeze_kitchen.py -- verify
rtk proxy .venv/bin/python projects/c_type_home/design/kitchen_frozen_v1/package_kitchen.py audit
```

核验文件：[母版校验](/Users/xiwei/interior_design/projects/c_type_home/design/kitchen_frozen_v1/KITCHEN_QA.json)、[视角像素比较](/Users/xiwei/interior_design/projects/c_type_home/design/kitchen_frozen_v1/PIXEL_EQUIVALENCE_QA.json)、[业主确认依据](/Users/xiwei/interior_design/projects/c_type_home/design/kitchen_frozen_v1/APPROVAL_EVIDENCE.json)。临时剖切只存在于重出图进程，母版完整墙体不被写回裁切。

## 加工深化边界

空间方案和现状模型已锁定；本包未放行下单加工。现场复尺和设备/五金深化需补齐：约3米窗跨实测，旁柜深度，挂机型号及安装/检修尺寸，继承柜体细部，台面开孔与收口，以及图5柜导引1500×500和原PDF1580×600之间的差异。图5柜中段450为名义分段，当前模型18厚底板下净空为432。

保留简单审阅材质；最终表面、照明、生产节点在后续对应阶段处理。复尺更新只进入新版本，并保留本次确认关系与来源。

## 文件与聊天规则

所有渲染、叠加图、联系表和照片代理图保存到项目文件系统，聊天只返回路径。高分辨率原图按需一次检查一张或少数几张。禁止把大二进制或图像批量内联到上下文。
