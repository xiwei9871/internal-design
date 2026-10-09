# 提示词合同与三方向差异

## 共用几何，分开设计语言

Faithful/Designer/Creative是改变程度，**不是三个固定美学流派**。先写用户的风格brief，再定义三者允许改变的对象。不能把所有项目Designer写成石材、Creative写成灰绿藤编；这是C-Type的一组候选。没有人工指定的变更范围不启动B/C。当前规则是解决方向，仍需小样验证。

| 层级 | 允许变化 | 不允许 | 输入逻辑 |
|---|---|---|---|
| Faithful | 真实材料、软布/接缝、实物机制、照片感 | 新家具、新柜缝、新建筑；为美观改家具家族 | 本view几何 + 真reference + 必要照片质感参考 |
| Designer | 指定对象的材质分配、家具细部/软装搭配，在原包络与功能内 | 隐式扩大布局/换建筑；只写“更高级” | 本view几何 + 选定同房Faithful + 专属材质/构造参考 |
| Creative | 明确指定的更鲜明色块、纹理、造型语言和编辑型光线，仍在原包络 | 曲面天花、新开口、新增椅子、移设备；仅全局调色 | 本view几何 + 选定同房Faithful + 独立方向参考 |

摄影质量对三者同样要求；Faithful不是低质量，Creative不是随意违背源模型。需要几何重设计时单独提出model revision，不混在“创意改图”里。

## 每次提示词组成

1. **输入角色**逐张编号：当前几何/当前同viewFaithful/产品机制/材质参考。后续视角改变reference次序时同步改编号，不能保留“Image2厨房参考”再说Image2是roomhero。
2. **结构合同**：同相机/裁切/门窗/天花/层高/标高/台阶/家具数量与位置/柜缝/通道。
3. **本view可见性**：正面/侧墙的开口；behind-camera与hidden对象禁止入画；镜中真实可见方向；不存在的物不通过文字补入。
4. **对象语义**：布runner可垂落，chaise为躺椅有足部，椅子有靠背，gas有锅架，冰柜顶开等。
5. **change ledger**：对象或可见区域 → 原表现 → 目标表现 → 保留项 → 支持reference。
6. **摄影/材料**：光从哪个真实窗入、纹理尺度、阴影、白色保细节；不以新增建筑/道具替代设计。
7. **avoid与验收**：只列此view实际风险，避免一长串无关空间陈设。

不要在提示词里塞“请找人确认”来代替执行前的人类gate，或塞“至少改变两个对象”但不命名对象。ledger应在任务manifest明确，不由生成模型猜。

## 差异设计与小样闸门

先选变化在画面中占明显面积、且用户愿意改变的1–3个区域。示例C-Type客厅：Designer指定茶几石面/暖白柜面/结构化taupe软包；Creative指定原面板编织/灰绿软包/原茶几内自然边木面。原开放柜若没有闭面，不能为编织方案新增柜门。背景、摄影质量可以一致，但差异必须在物体和材料分配上可指出。

为B/C分别选择不同appearance reference，不同时用强势的同一厨房照片；同一Faithful只用于保留未改部分。缩略图上去掉标签，人能指出差异在哪，以及它是否符合各自ledger。若只有曝光/摆件不同，不通过。检查每个指定区域是否改变、未指定区域是否保持；再人工确认审美。可用差分定位，不能用全图pixel距离或CLIP分数自动宣称风格区分成功。

一view两候选起步；一轮不佳只修一个失败原因，最多一次自动修图，保留original/new与重试证据。结果仍相似则暂停传播、重审ledger/参考。只有小样通过才写`STYLE_DISTINCTION_VISUALLY_VERIFIED`，否则`PROMPT_RULES_UPDATED_UNVERIFIED`。

## 可复制的局部编辑骨架

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
