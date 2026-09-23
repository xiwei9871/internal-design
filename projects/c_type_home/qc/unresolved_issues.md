# Task 01 — Unresolved Issues / 待现场复核项

SOURCE PLAN RECONSTRUCTION — 以下为原图无法可靠判定、需要业主原始资料或现场复尺确认的条目。
像素坐标均基于当前正式源图 **1279×1986**（SHA256 0125ad6c…d3c1）。

---

## ISSUE-001 — 底部外链左端基准点无墙

- **location**: 底部尺寸链最左端界线 px x≈168.5（世界坐标 X0）
- **observed evidence**: 该列向上在 py575–1008 仅穿过左侧户号文字笔画，py1456–1567 为尺寸线本身；界线与任何墙线均不相连；最近的实体构件为生活阳台西栏（px x≈235–242，X≈1300）
- **why unresolved**: 尺寸链基准通常对应墙/柱面，此处悬空；X0 落在阳台西墙以西约 1400mm
- **possible interpretations**: (a) 基准为户型图外框/投影线边界；(b) 基准对应未绘制的相邻户型分界面；(c) 1400 段实际量到阳台栏杆柱中心
- **required verification**: 原始 DWG；现场复尺阳台西缘至外墙皮距离

## ISSUE-002 — 底部内链尾部数字（已解决）

- **status**: RESOLVED（高分辨率源图复核）
- **resolution**: 尾部两段为 **200 + 100**；内链完整转录为 1000+1000+400+2100+900+1400+700+700+2200+700+700+2500+700+700+200+100 = **16000**，自 datum X400（px189.5）至建筑外立面 X16400（px1025），与像素刻度逐一吻合
- **残留注意**: 两个百位数字仍部分贴压界线，另有像素间距（≈210mm / ≈86mm）与总值闭合佐证

## ISSUE-003 — 底部内链基准 +400mm 偏移

- **location**: 底部内链起点 px189.5（X400）vs 外链起点 px168.5（X0）
- **observed evidence**: 内链整体自 X400 起量，其后刻度 px241.5/293.5/314.5/423.5… 与外链刻度完全重合
- **why unresolved**: 内链 0 基准对应的构件不明（X400 处无墙线）
- **possible interpretations**: 内链自阳台栏板内侧某构件起量；或属另一体系基准
- **required verification**: 原始图纸

## ISSUE-004 — 黑粗墙一律不判定为承重墙

- **location**: 全图外圈粗墙（W-EXT-* 系列）与厨房北墙等黑色填充墙段
- **observed evidence**: 原图为开发商销售户型图，粗黑填充仅为图面表达，无结构标注
- **why unresolved**: 无任何结构信息来源
- **required verification**: 结构图或现场勘测；当前全部 `structural_role = UNKNOWN`

## ISSUE-005 — 主卧东窗位置：尺寸与像素冲突

- **location**: 东墙下段 W-EXT-E1（X15400 一线）
- **observed evidence（高分辨率复核）**: 右链 1800 段刻度 py1204→1300 对应 Y527–2335；但墙内窗符号（墙厚内白色块）实测 py1178–1232 ≈ Y1810–2824，偏北约 500–800mm 且符号读高约 1000mm
- **why unresolved**: dimension annotation > pixel，已按 1800 段定位开窗（opening Y500–2300）；绘制缝位偏差超出读图误差
- **possible interpretations**: 绘图示意偏差；或窗实际居 Y1810–2824 而尺寸链分段对应其他界线
- **required verification**: 现场或原图复核；overlay 上该差异可见（WIN-E1 残差 ~70px）

## ISSUE-006 — 右侧 12900 总尺寸北端无墙线对应

- **location**: 右侧外链北端界线 py≈643（Y12900）
- **observed evidence（高分辨率复核）**: 东缘 x980–1160 在 py540–760 区间仅见卧室北墙转角（py≈715，Y≈11400）及其上方空白；py643 高度无任何东西向墙线，对应东北角空调机位凹槽带
- **why unresolved**: 总尺寸北端终止于机位凹槽顶缘还是未绘出的外墙皮，图面不能确定
- **required verification**: 原始图纸；当前卧室北墙按像素证据建模（Y11350–11550, LOW）

## ISSUE-007 — 厨房/餐厅/生活阳台门位（已解决）

- **status**: RESOLVED（高分辨率复核）
- **resolution**:
  - **D-11** 确认开在 X5800 墙，洞口约 Y1400–2300，铰点在北端（Y2300 角部），门扇以约 45° 开启态绘于厨房内侧 → 生活阳台↔厨房
  - **D-13（新增）** 餐厅南墙（Y2400–2560）存在约 **1900mm 宽洞口** X2900–4830（py1194–1196 实测缺口 px320–421），判定为推拉门，是室内进入生活阳台的唯一通道
  - 通行路径：餐厅 →(D-13)→ 生活阳台 →(D-11)→ 厨房
- **残留注意**: D-13 洞口宽且以细线绘制，推拉门类型为推断（图面无门扇符号），见 ISSUE-013

## ISSUE-008 — 厨房南侧 1400 段（已解决）

- **status**: RESOLVED（高分辨率复核）
- **resolution**: 1400 段（X5800–7200）对应厨房南窗 **WIN-S3** —— 高分辨率下窗符号（墙厚内多条平行线 px476–542, py1320–1332）清晰可见；置信度提升为 HIGH（尺寸约束+图符双重证据）

## ISSUE-009 — 休闲厅↔走廊 1800mm 宽开口无门扇

- **location**: X7900 墙 Y4670–6450
- **observed evidence**: 约 1780mm 缺口，无门扇弧线
- **why unresolved**: 可能是垭口/开放式连通，也可能漏绘
- **required verification**: 现场

## ISSUE-010 — 东北角机位/凹槽区域几何不完整

- **location**: X13100–16500, Y10900–12900 区域
- **observed evidence**: 检测到机位方框与凹槽短线，但区域整体边界关系不清晰；右链 12900 北端界线亦落在该区（见 ISSUE-006）
- **why unresolved**: 图块叠加，像素证据不足以唯一重建
- **required verification**: 原图/现场；当前以 LOW confidence AC-bay 区块标注

## ISSUE-011 — 客厅西墙外缘线缺失段

- **location**: W-EXT-W 外侧面，墙外皮黑填终止于 py747（Y≈10940），py747–975 段仅余双细线，py975 以下为入户门 D-01 洞口区
- **observed evidence（高分辨率复核）**: 内皮线连续，外皮黑填充在 Y≈6650–10940 大范围未绘制；入户门洞与 WIN-W1 薄线区均落在该段内
- **why unresolved**: 图纸表达缺失；可能因西侧紧邻公共走廊而省略外皮
- **required verification**: 原图/现场

## ISSUE-012 — 西墙薄线区性质不明（WIN-W1）

- **location**: W-EXT-W，Y6650–10940（py747–975 双细线 + 白色块）
- **observed evidence**: 该段墙体以无填充细线表达，py782 处有一条横向界线将其分为上下两段；是否为窗带、西向阳台推拉门带或仅未填充的墙厚，图面无法判定
- **why unresolved**: 无任何尺寸标注指向该区；符号画法不规范
- **possible interpretations**: (a) 客厅西向窗/落地窗带；(b) 省略填充的普通墙体
- **required verification**: 现场；当前 WIN-W1 记 LOW，范围取整段 Y6650–10940

## ISSUE-013 — D-13 餐厅→生活阳台开口类型为推断

- **location**: 餐厅南墙 W-BALC-N，洞口 X2900–4830（约 1900mm）
- **observed evidence**: 高分辨率下洞口明确（py1194–1196 缺口 px320–421），但内部仅有细线，无门扇/推拉轨道细节
- **why unresolved**: 开口类型（推拉门 / 平开门联窗 / 栏杆开口）不能唯一确定；因其为阳台唯一室内通道，按推拉门候选建模
- **required verification**: 现场/原图；`type = sliding_door_candidate`

---

## 附：模型与源图的系统性偏差说明

matched-source 残差显示：多数门/窗洞口的实测像素缺口比模型洞口宽约 20px（≈380mm）、并向尺寸链基准反方向偏移约 10px（≈190mm）。原因是源图把门弧/框线画入洞口、且绘制墙线与尺寸界线基准本身存在 ~100–250mm 的制图偏差。按任务规则 **dimension annotation wins**，模型几何以尺寸链为准；残差仅作诊断，不作为门禁依据。外墙皮实测带与模型面的系统性偏移（如 W-EXT-S 外皮绘于 py1321 而尺寸基准 Y0 在 py1328）属同一制图误差。
