# 提示词合同与三方向差异

## 三种模式按不同任务定义（2026-10-09用户修正）

Faithful是忠实呈现；Designer是主体保留后的完整软装设计；Creative是AI自由创意探索。它们不是同一套家具换三个颜色，也不是固定的石材/灰绿/藤编流派。先看用户授权和用途。Creative的自由度不自动取消用户已经确认的整体审美；先分开记录必须保持的风格基因与可以自由探索的家具、布局和构成。此前原包络内材质变化小样被用户明确否定，不能再作为成功路线。

| 模式 | 允许变化 | 保留/权威 | 输入 |
|---|---|---|---|
| Faithful | 真实材质、织物与实物机制、摄影化表达 | 源空间、家具、布局与机位 | 当前几何、实物reference |
| Designer | 挂画、摆件、植物、抱枕/毯/地毯/窗帘、装饰灯具及整体软装搭配；用户另有授权才改主体 | 建筑和主要家具家族/位置保持，原模型不改；新增软装是提案 | 同viewFaithful＋必要几何，独立软装reference |
| Creative | 在用户已定整体审美内替换家具、改变布局/数量、艺术、灯光及授权表现；配色边界由用户brief决定 | 原模型/GroundTruth不修改；图片标INSPIRATION_ONLY，合理尺度与功能仍需判断 | 原图作空间与审美背景；不锁原家具，但保留用户色系/材料/简洁程度 |

Creative可以在图片中重构，不代表现有房屋已变更。进入采购、精细建模或施工需要另做可行性审核和人工选择。真实产品reference在确定落地对象时必需；概念阶段不强制先锁SKU，但不把AI设计冒充真实产品。

## 每次提示词组成

1. **输入角色**逐张编号：当前几何/当前同viewFaithful/产品机制/材质参考。后续视角改变reference次序时同步改编号，不能保留“Image2厨房参考”再说Image2是roomhero。
2. **模式合同**：Faithful/Designer锁定建筑、相机和主要家具；Designer明确授权新增哪些软装。Creative列少量空间/功能背景及可自由改变内容，不能继承锁原家具数量/包络的长负面清单。
3. **本view可见性**：正面/侧墙的开口；behind-camera与hidden对象禁止入画；镜中真实可见方向；不存在的物不通过文字补入。
4. **对象语义**：布runner可垂落，chaise为躺椅有足部，椅子有靠背，gas有锅架，冰柜顶开等。
5. **change ledger**：对象或可见区域 → 原表现 → 目标表现 → 保留项 → 支持reference。
6. **摄影/材料**：光从哪个真实窗入、纹理尺度、阴影、白色保细节；不以新增建筑/道具替代设计。
7. **avoid与验收**：只列此view实际风险，避免一长串无关空间陈设。

不要在提示词里塞“请找人确认”来代替执行前的人类gate，或塞“至少改变两个对象”但不命名对象。ledger应在任务manifest明确，不由生成模型猜。

## 差异设计与小样闸门

Designer为整个画面组织软装：明确视觉焦点、挂画与灯光、织物层次和陈设分组。其缩略图差异应是“同一主体经过设计”，不是只把沙发变灰。Creative提出整体不同的概念：家具轮廓/布局、墙面焦点、材料与配色能形成新想法。不要用几个具体材质替换把AI再次约束成换色任务。

Designer保持原机位便于对比；Creative可优先相似方向帮助理解，但不把相机/家具复制当通过条件。参考各有角色；Creative无须强完整hero或白模。去掉标签，人应能指出Designer新增的整体软装以及Creative重新构思的设计。若Creative只是另一套颜色，不通过。

一view两候选起步；一轮不佳只修一个失败原因，最多一次自动修图，保留original/new与重试证据。结果仍相似则暂停传播、重审模式约束/参考；不要自动全屋扩展。只有小样通过才写`STYLE_DISTINCTION_VISUALLY_VERIFIED`，否则`PROMPT_RULES_UPDATED_UNVERIFIED`。

## Faithful/Designer可复制的编辑骨架

```text
Image1: approved geometry and camera for this view.
Image2: selected Faithful image of the SAME room and view; preserve all untouched regions.
Image3: material/construction reference ONLY for the named object below.
CAMERA/ARCHITECTURE: preserve current viewpoint, crop, openings, ceiling, floor levels, steps.
VISIBILITY: [exact anchors and hidden/behind-camera objects from this view register].
CHANGE LEDGER: [object id / visible region / before / target / reference id].
KEEP: [object counts, envelope, seams, functions and surfaces outside ledger].
PHOTOGRAPHY: [brief-specific daylight/practical balance and texture requirements].
AVOID: [view-specific prior failures].
Output one unlabeled photo; no new objects to compensate for hidden regions.
```

方括号字段必须用当前view/reference数据填完才发送。This view geometry的权威是数值底模，AI输出仍可能漂移。

Creative提示词骨架：原图为房间与风格背景 → 列必须保持的色系/主材/氛围/装饰密度 → 明确家具/布局/造型可自由重构 → 给用途与氛围，不规定每个物品 → 保持住宅尺度、可用动线和物理合理 → 标为灵感概念 → 人工挑想法后才研究落地。
