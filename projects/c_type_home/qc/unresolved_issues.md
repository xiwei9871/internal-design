# Task 01 — Unresolved Issues / 待现场复核项

SOURCE PLAN RECONSTRUCTION — 以下为原图无法可靠判定、需要业主原始资料或现场复尺确认的条目。

---

## ISSUE-001 — 底部外链左端基准点无墙

- **location**: 底部尺寸链最左端界线 px x≈86.5
- **observed evidence**: 界线向下仅延伸约 30px 即终止，下方没有任何墙线或构件线；最近构件为生活阳台西栏杆（px x≈124）
- **why unresolved**: 尺寸链基准通常对应墙/柱面，此处悬空
- **possible interpretations**: (a) 基准为户型图外框/投影线边界；(b) 基准对应被裁切的构件；(c) 1400 段实际量到阳台栏杆柱中心
- **required verification**: 获取原始 DWG 或更高清图片；现场复尺阳台西缘至外墙皮距离

## ISSUE-002 — 底部内链最右两段数字无法辨认

- **location**: 底部内尺寸链 px x>520 的尾部两个数字
- **observed evidence**: 数字被尺寸界线压住且超出 659px 宽度分辨率极限；像素锚点显示 px520→527 约 320mm，之后可能还有一段
- **why unresolved**: 文字不可读，禁止猜数字
- **possible interpretations**: 尾部为 300+300、400+0、或东墙厚度收口段
- **required verification**: 高清原图或 CAD 原文件

## ISSUE-003 — 底部内链与外链基准不一致（+400mm）

- **location**: 底部内链起点 px97 vs 外链起点 px86.5
- **observed evidence**: 内链整体右移约 10.8px（≈400mm），但其刻度在 px124/162/242/299/394/501 与外链完全重合
- **why unresolved**: 内链的 0 基准对应哪个构件不明
- **possible interpretations**: 内链从阳台栏杆内侧某构件起量；或绘制错位
- **required verification**: 原始图纸

## ISSUE-004 — 黑粗墙一律不判定为承重墙

- **location**: 全图外圈粗墙（W-EXT-* 系列）
- **observed evidence**: 原图为开发商销售户型图，粗黑填充仅为图面表达，无结构标注
- **why unresolved**: 无任何结构信息来源
- **possible interpretations**: 部分外墙/分户墙可能为结构墙，但不可从本图判定
- **required verification**: 结构图或现场勘测；当前全部 `structural_role = UNKNOWN`

## ISSUE-005 — 主卧东窗位置：尺寸与像素冲突

- **location**: 东墙下段 W-EXT-E1（X15400 一线）
- **observed evidence**: 右链 1800 段对应 Y500-2300；但墙面上绘制的窗缝图形位于约 Y1870-2890（偏北约 500-600mm）
- **why unresolved**: dimension annotation > pixel，已按 1800 段定位开窗；但绘制缝位偏差超出读图误差
- **possible interpretations**: 绘图示意偏差；或窗实际居 Y1870-2890 而尺寸链分段对应别的界线
- **required verification**: 现场或原图复核；当前按 P1 尺寸优先建模并在 overlay 可见差异

## ISSUE-006 — 右侧 12900 总尺寸北端无墙线对应

- **location**: 右侧外链北端界线 px y≈331（Y12900）
- **observed evidence**: 该扫描行 x420-545 无任何水平墙线；卧室北墙实测在 px y≈370（Y≈11400）；px331 对应的是东北角空调机位凹槽的上缘
- **why unresolved**: 总尺寸北端终止在机位凹槽还是某未绘出的外墙皮，图面不能确定
- **possible interpretations**: (a) 12900 量到机位/凹槽顶缘；(b) 卧室北外墙实际在 Y12900 但未被绘出（被机位图块遮挡）
- **required verification**: 原始图纸；当前卧室北墙按像素证据建模（Y11400-11550, LOW）

## ISSUE-007 — 厨房↔生活阳台 / 餐厅↔生活阳台 门位歧义

- **location**: X5800 墙与阳台北墙（Y2300-2500）交界
- **observed evidence**: 门弧铰点位于该转角；X5800 墙 Y1400-2300 与 Y2300-4050 的像素缺口、以及 Y2300 墙 X4600-5700 附近的弧线归属存在两种读法
- **why unresolved**: 弧线跨越转角，不能唯一确定开在哪面墙
- **possible interpretations**: (a) 门开在 X5800 墙（阳台→厨房）；(b) 门开在 Y2300 墙（餐厅→阳台）；当前按 (a) 建模
- **required verification**: 现场/原图复核；若为 (b)，厨房则无明显入口，需重新判断

## ISSUE-008 — 厨房南侧 1400 段是否为窗

- **location**: 南墙西段 X5800-7200
- **observed evidence**: 底部内链存在 1400 分段，但该范围 px 扫描未见墙线开窗，下方为空调机位/凹槽
- **why unresolved**: 尺寸分段对应构件不明
- **possible interpretations**: 厨房南窗；或机位凹槽宽度标注
- **required verification**: 原图/现场

## ISSUE-009 — 休闲厅↔走廊 1800mm 宽开口无门扇

- **location**: X7900 墙 Y4670-6450
- **observed evidence**: 约 1780mm 缺口，无门扇弧线
- **why unresolved**: 可能是垭口/开放式连通，也可能漏绘
- **required verification**: 现场

## ISSUE-010 — 东北角机位/凹槽区域几何不完整

- **location**: X13100-16500, Y10900-12900 区域
- **observed evidence**: 检测到机位方框（x437-455, y337-370）、短线段（y385-391 x506-529）与卧室北墙（y369-373），但区域整体边界关系不清晰
- **why unresolved**: 图块叠加，像素证据不足以唯一重建
- **required verification**: 原图/现场；当前以 LOW confidence AC-bay 区块标注

## ISSUE-011 — 客厅西墙外缘线缺失段

- **location**: W-EXT-W 外侧面 Y4560-10260
- **observed evidence**: 外墙外皮线在该段未绘制（内皮线连续）；入户门 D-01 也落在该缺口范围内
- **why unresolved**: 图纸表达缺失；可能因西侧紧邻公共走廊而省略外皮
- **possible interpretations**: 墙连续存在（当前建模假设）；或存在未绘制的凹陷
- **required verification**: 原图/现场
