# PASCAL ARCH/FIXTURE CLEANUP V1

状态:**ARCH_FIXTURE_CLEANUP = HUMAN_REVIEW**

场景:`pascal-master-direct-furnished-v3`(v1/v2 未动)
脚本:`scripts/pascal_arch_fixture_cleanup_v1.py`
本场景 JSON:`design/pascal_b1/pascal_master_direct_furnished_v3.json`

## 1. D-107 angled door

**源身份**:F-DOOR 里没有字面 `D-107`/`107` 标签;`Line107` 对象 SemanticId=W-STUDY-NE(墙线)。唯一非正交 swing 的门记录 = **D-SM**:

- hinge canonical (8332, 4543), leaf rest (9095, 4919) → 门框方向 **+26.3°**
- swing arc 296°→26°(90°),r=850
- 门洞横跨 E-W 墙带(WB-040 东端)与 N-S 墙 WB-014(x9050–9200)之间的斜角区 → 与用户"两段墙存在夹角"一致 ✓

**改动对象**:`PASCAL_OPENING_HOST_HELPER` `wall_md_0075`
(v2 中被正交化为 E-W;v3 改为 (8.332,-4.543)→(9.095,-4.919),即 +26.3° 斜置)
`door_md_0076` 本体参数未动(position t=0.5 居中于 850mm 门框)。

未触碰:门节点尺寸/swing 语义、任何真实墙带、FreeCAD、verified openings。

## 2. Shower wet-zone × 3

场景里 SHOWER_ZONE 共 3 处(任务说两处;第三处 Rectangle036 在 R-CLOAK zone、label=次主卫湿区,同语义同问题,一并处理——若它其实不是淋浴,回退 `item_v2_0042` 即可)。

| 源对象 | 房间 | 原表现 | 入口面 | 开口宽 |
|---|---|---|---|---|
| Rectangle007 | R-BATH-P 客卫 | solid box 1644×813 | 南 face=270° | 1644mm |
| Rectangle033 | R-BATH-M 主卫 | solid box 1000×1522 | 西 face=180° | 1522mm |
| Rectangle036 | R-CLOAK 次主卫 | solid box 823×1547 | 西 face=180° | 1547mm |

**新表达**(每处 6 节点):
- `wall_gf_0XXX` 固定玻璃——薄墙节点(t=15mm,半透明,编辑器里呈玻璃质感)
- `wall_gs_0XXX` 滑动玻璃——平行轨道,向干区偏移 40mm
- `item_rl_0XXX` 上轨 / `item_tr_0XXX` 下轨 / `item_jb_*` 两侧边框——浅灰 blockout
- 玻璃仅在**入口面**(其余侧由实体墙围合),没有四面包玻璃盒
- 高度 2000mm STANDARD_BLOCKOUT,base 随房间地面(0.7)

XY footprint 与朝向边全部沿用原湿区 rect;未改布局。

## 3. 审查图

- `D107_BEFORE_AFTER.png` — 平面图:v2 水平 host band → v3 26.3° 斜置
- `SHOWER_ENCLOSURE_REVIEW.png` — 三处湿区放大平面(青=固定玻、橙=滑动玻、灰=框)
- `FULL_HOUSE_3D_CLEAN_V3.png` — DESIGN_REVIEW(shadows off / solid / edges soft)全屋 3D

## 4. 遗留复核点

1. Rectangle036(R-CLOAK/次主卫湿区)纳入本轮改动——确认它确属淋浴间
2. Pascal 编辑模式墙体本身半透明;玻璃板用薄墙节点表达,观感与墙体一致——若需要更强的"玻璃"可读性,等下游 Blender 赋材质
3. host helper 斜置后,与 WB-040 东端仍保留 ~530mm 豁口(v2 原本就有,非新引入)

## Gate

`ARCH_FIXTURE_CLEANUP = HUMAN_REVIEW` — 等待确认,不推进 Blender/材质/渲染。
