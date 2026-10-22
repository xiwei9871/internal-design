# B0 ARCHITECTURE TRANSFER GATE

状态:**B0 = HUMAN_REVIEW**(几何检查通过,待人工过目)

## 冻结记录

- `PASCAL_LAYOUT = APPROVED`,`PASCAL_WALL_VISUAL = NON_BLOCKING`,`BLENDER_STAGE = AUTHORIZED`
- 冻结副本:`design/blender_b0/PASCAL_LAYOUT_FROZEN_v3.json`(场景全量) + `FURNITURE_TRANSFORMS_FROZEN_V02.json`
- 权威划分:**CAD/墙带 = 墙体几何真值;Pascal v3 = 家具布局真值**;Pascal 墙体 mesh 不作为建筑几何来源

## 构建(`scripts/blender_b0_build.py` → `B0_shell.blend`)

Blender 坐标:X=东(CAD x)、Y=北(CAD y)、Z=上;单位米。

- **墙**:61 根真实墙带(WB-*/PIER-00)按 rect_mm 成实体盒,厚度集 {100,110,150,200,250,300,350,400,500}mm,全部源自 S-S.WALL face-pair;10 个 HOSTBAND 门洞 helper **不建**(门洞=墙带豁口)
- **Z datum / SPLIT-LEVEL**(`Z_DATUM_SPEC.json`,建筑 Ground Truth 基准,正式命名 LOWER_SPLIT_LEVEL / UPPER_SPLIT_LEVEL,**不**叫 1F/2F):**LOWER FFL=Z0 / UPPER FFL=Z+450mm / 净高两侧均 ≈2800 → 天花 2800 / 3250**;FFL 关系与 3×150 踏步 = CONFIRMED;天花值 = HUMAN_CONFIRMED_FROM_EXISTING_HOUSE;梁/包管/造型细部 = TO_VERIFY;已全局清除旧 0.7/1.05/+350/2-step 偏移
- **墙体竖向跨度三规则**:lower-only 0→2800 / upper 内隔墙 450→3250 / 跨错层连续墙(上下层共享边界)0→3250;按墙两侧相邻空间 level 逐墙判定,非一刀切
- **天花**:每空间独立天花面(14 块,120mm 厚块),上下层开放边界处自动生 450mm 竖向 fascia;整体错层天花 = 建筑特征,AI 后续不得拉平
- **台阶**:3 级 ×150mm(顶面 +150/+300/+450)在 [7200-7800, 6600-7800](lower→upper)
- **坡道**:[5727-7827, 4727-5827] 橙色预留板 at lower FFL,**TO_VERIFY**(无障碍坡道,现场核实)
- **门洞**:墙带豁口天然成洞;D-107(=D-SM)门扇按 F-DOOR +26.3° 斜置显示(蓝色 LEAF_D107)
- **窗洞**:boolean 切除 + 玻璃面板(蓝);窗台板 slab 4 处沿用
- **楼板**:按 14 个 space 多边形分房间生成
- **家具**:全部 item 节点按冻结 transform 成间隙检查盒(米黄),含厨房 PDF blockout 与淋浴玻璃/框

## Gate 结果(`B0_GEOMETRY_GATE.json`)

| 检查 | 结果 |
|---|---|
| 墙带完整性 | PASS 61 real / 10 helper 排除 |
| 门洞不被实体墙堵 | PASS 0 处平行侵入 |
| 窗洞处理 | PASS(3 处贴带处 boolean 切除,其余为天然豁口) |
| 墙厚集合 | PASS 100–500mm 九档 |
| D-107 门洞方向 | PASS 26.2° vs 源 26.3° |
| 房间净尺寸 | PASS 14 空间量出(见 JSON) |
| 层高/Z datum | PASS split-level FFL 0/+450,天花 2800/3250,净高两侧≈2800,3 阶×150(CONFIRMED) |
| 坡道 | PASS 预留区标记,TO_VERIFY |
| 家具-墙重叠 | FLAG 8 处近似 AABB 重叠>50mm |

### 家具重叠 FLAG 明细(多为设计贴墙,逐一核对)

- WB-032 南墙 ×4(无 name 的厨房/窗边件,最大 1210×200mm 侵入)——疑似厨房南排柜贴墙编码误差,**重点目检**
- WB-008/WB-037 各 1(入口附近)
- 马桶 ×3(客卫 226×324、主卫 500×186、次主卫 500×119)——可能是 toilet asset pivot 偏移导致近似盒偏大,渲染图中未见明显穿墙;Pascal 场景里核对

## 图

- `B0_TOP.png` 顶视正交;`B0_AXON.png` 室内轴测;`B0_AXON_CEIL.png` 含错层天花体量
- `B0_SPLIT_LEVEL_SECTION_V3.png` Z 标高剖面(0/150/300/450/2800/3250);`B0_SPLIT_LEVEL_AXON_V3.png` 双联图

## 边界

B0 只做硬壳+布局校验。材质/灯光/软装/真实家具资产替换 = B1 以后。
