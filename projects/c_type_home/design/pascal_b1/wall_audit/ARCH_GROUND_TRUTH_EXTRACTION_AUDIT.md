# ARCH GROUND TRUTH EXTRACTION AUDIT

任务：QUERY ONLY — 未修改 MASTER_V2 / canonical / Pascal scene / register。

裁判标准（用户定义）：**凡是 MASTER_V2 里存在的建筑墙体 linework，Pascal 2D 就必须存在。**

## 方法

- 从 `世纪欣园FF_PRE_BLENDER_MASTER_V2.FCStd` 重新 dump 全部 438 对象，这次捕获了 `Layer.Group`（`App::PropertyLinkListHidden` —— 旧 dump 只查 `App::PropertyLinkList`，所以一直没拿到图层归属）。产出 `MASTER_ARCH_OBJECT_INVENTORY.json`（含每条 edge 的端点坐标）。
- 对每条 master linework 按 40mm 采样，判定是否落在某个 Pascal 存储墙体 rect ±80mm 内。
- 同样对 FINAL_WALL_ACTIVE_REGISTER 的 rect 做覆盖判定，区分"register 就没收"与"register 有、Pascal 没发"。

## MASTER_V2 实际结构（DWG 图层）

| DWG layer | objects | 内容 |
|---|---|---|
| `S-S.WALL` | 209 | 结构墙线稿（201 Part::Line + 8 Part::Feature polyline） |
| `F-DOOR` | 90 | 门扇/门洞线稿（门洞弧线 swing arcs） |
| `S-楼梯` | 7 | 楼梯/错层 |
| `F-SAN FIT` | 16 | 洁具 guide |
| `F-FURN` | 41 | 家具 guide |
| 无 layer | 67 | WINDOW_REF 语义组 + 家具/洁具 Part2D 矩形 |

**注意：MASTER_V2 是纯 2D 线稿（303 Edge / 63 Wire / 50 Face，无墙体实体）。** "墙"本身是 linework 对——wall register 是对线稿的一次解释，不是事实本身。这正好证实三层模型：

```
Layer1 物理事实 = MASTER linework (墙在哪)
Layer2 语义     = wall/opening registers + WINDOW_REF (这段线是什么)
Layer3 派生     = canonical → Pascal
```

## 覆盖统计

```
S-S.WALL linework objects      = 209
Pascal 覆盖 ≥50%               = 153
未覆盖 (<50%)                  = 56
  ├─ register 同样没有         = 50   ← 上游解释时就丢了
  └─ register 覆盖但 Pascal 无  = 6    ← 全部是被 register 判 REMOVED 的 rect 覆盖
```

## 缺口分组（RED = `MASTER_DIRECT_VS_PASCAL_OVERLAY.png`）

### A. 真正的漏墙（register 从未登记）

| 位置 | 对象 | 判断 |
|---|---|---|
| 东块内隔墙 x≈14650, y6600–11800 | Line100/101/102/103 + Line041 部分 | **REG_MISS** — 主卧/书房带内一条纵向分隔墙的整条面线 |
| x≈8000, y8000–10900 | Line032 | REG_MISS — 西侧内隔墙 |
| x≈9200, y4971–6450 | Line061 | REG_MISS — 内隔墙 |
| y≈10900–11100 横线 x8000–15600 | Line002/079/080/082/084/087/096/097/100 | REG_MISS — 客房/书房带南界多条墙段 |
| 北阳台周界 x7900–13020, y11100–13820 | Polyline011/012/013（三条同心轮廓） | REG_MISS 部分（38% 覆盖） |
| 书房北侧 y11700–11800 x13500–15800 | Line101/102/103 | REG_MISS |
| 北边界 y13000–14953 | Line001/020/027/028 | REG_MISS — 北立面/女儿墙面线 |

### B. 系统性"内侧面向外偏 200"（南立面 y≈140–500 整排红）

master 南立面画出**两条**面线：y=0 和 y≈+140/+200；register 的南侧墙体 rect 全部是 `y −200..0`。y0 被覆盖、y200 整排未覆盖 → 两种可能，需要人裁决：

1. 真实墙 = 0..200 向内厚 → **Pascal 南墙整体外移了 200mm**（边界错）；
2. 真实墙 = −200..0 向外厚 → y140/200 是窗台/踢脚等细部线，不缺墙（但同一对象在 S-S.WALL 层）。

涉及对象：Line133–135/137/147/157–159/164/170–177、Polyline015/016/017、Line012 等约 20 条。
同类偏移疑似也存在于东立面（x15300/16200 vs register 15400–15600/16300–16500，Line014/016/041）和北立面 y13000/13900–14953。

### C. REMOVED_WALL_FALSE_POSITIVE 候选（register 判"拆"，master 还在画）

register 覆盖、Pascal 无墙的 6 条全部是覆盖在 removed rect 上：

| 对象 | 位置 | 覆盖它的 removed wall | 含义 |
|---|---|---|---|
| Line053/054 | x1300–2900, y2300–2500 | W-BALC-N [1300,2400,5800,2560] | 厨房↔生活阳台分隔墙被标"拆"——**用户看到的厨房缺墙大概率是这条** |
| Line166/200 | x5700–5900, y4100–4500 | W-INT-X5800/STUB | 厨房东墙垛被标"拆" |
| Line064/066/056 | x10725–11400, y4500–4725 | W-INT-Y4500-b-CLKSEG | **次主卧北墙一段被标"拆"** |
| Line061 部分 | x9200 y4971–6450 | —（register 全无） | 见 A |

→ 厨房/次主卧缺墙的直接原因不是"没提取到对象"，而是**这些墙被 reconcile 判成了 REMOVED_BY_RENOVATION**，Pascal 正确地没建它们——但拆改决定是否还成立，是人审问题，不是脚本问题。

### D. 预期缺（不算 bug）

- F-DOOR 68 条：门扇开启弧线，Pascal 门由 registry 语义发，不走 linework；
- NO_LAYER 家具/洁具矩形（床/沙发/电视柜/打印机/nas…）：Design Guide，本就不该进建筑层；
- 小尺寸 y0–200 竖短线：飘窗垛/窗台边缘刻度，被 sill slab 表达。

## 五个问题的回答

**1. 为什么厨房墙丢了？**
两类原因叠加：(a) 阳台北墙 y2300–2500（W-BALC-N）和东墙垛 x5700–5900 被 register 判 REMOVED，Pascal 忠实执行了拆改；(b) 南立面内侧面线 y≈200 整排未被任何 register rect 覆盖（偏移或细部线，待定）。不是坐标变换错，是**墙集合定义阶段的取舍**。

**2. 为什么次主卧墙丢了？**
其北墙 x10800–11400 @y4500/4700 被 REMOVED 覆盖（CLKSEG）；x9200 内隔墙和西段 y10900–11100 界墙从未进 register；南立面内面线同上。

**3. 为什么 G-GB-BALC 正确？**
它有独立的权威链：`WINDOW_REF_G_GB_BALC` → 5 条物理对象（Line081/088/089/090/094, canonical x9900–12900 y10900–11100）→ `FINAL_WINDOW_REGISTER_95ab90e` 显式记录 `opening_rect=[10400,10700,12400,10900]、span=2000、type=GLASS_DOOR、host=W-INT-Y10800` → Pascal `door_v2_0057`（w=2.0m）+ 两侧 PARAPET `W-INT-Y10800#G-GB-BALC.0/.1`。**开口走的是语义层直通，不依赖墙线稿解释**——这正是墙缺而门对的根因。

**4. 旧 384-object classification 漏了多少？**
384-object ARCH 分类本身没错——漏的不在对象分类层，而在下游 **wall register 解释层**：209 条 S-S.WALL 对象里 56 条未被 Pascal 覆盖，其中 50 条 register 也没收。register 来自 `walls_baseline_246ff12`（更早的 canonical 解释），与 MASTER linework 存在系统性 100–200mm 面线偏移 + 整段漏墙。

**5. 应该怎样直接从 MASTER 提取？**
不再"linework → 猜墙 → register → Pascal"，而是：
- **物理层**：MASTER linework 按图层直接取用（S-S.WALL=墙线稿、F-DOOR=门洞、楼梯=错层）——不重建，只配对面线成墙；
- **语义层**：现有 register/WINDOW_REF 只回答"这段线是什么/拆不拆"，不决定"墙在哪"；
- **拆改裁决**：C 类每条 REMOVED 判定需要人逐条确认（拆 or 留），因为现状 DWG 仍在画它们；
- **偏移裁决**：B 类先判南立面内侧面线 y200 到底是墙内面（→ 修正 wall 厚度方向）还是细部线。

## 修订建议（未写入）

```
ARCH_GROUND_TRUTH_CONTAINER = PRE_BLENDER_MASTER_V2
ARCH_GROUND_TRUTH_GEOMETRY  = MASTER linework, by DWG layer — 权威
ARCH_EXTRACTOR_RESULT       = DERIVED / NON-AUTHORITATIVE
FINAL_WALL_REGISTER         = AUDIT / SEMANTIC SUPPORT（拆改裁决待人审）
WINDOW_REGISTER_95ab90e     = GROUND_TRUTH_OPENING SEMANTICS（已验证直通）
```
