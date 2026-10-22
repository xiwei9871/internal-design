# B1 FORMALIZATION DELTA V003 — 世纪欣园

> 2026-09-29 | V003 HUMAN CORRECTION SYNC
> 政策:HARD ARCHITECTURE > HUMAN-APPROVED OBJECT > ANALYSIS/REGION BOUNDARY

## 源状态核查

- `世纪欣园FF_freecad_WORKING.FCStd` 已于 10:06 重新保存(sha `2eddf2b7…`)— **冻结后人工修改确实存在**
- 人工 delta:次卧小床 −27/−14、3kg洗衣机 +12/−33、客卫湿区 +45/−21、床背板+窄书桌占位拆分为 床背板(200×1200)+窄书桌(350×1650)
- → 已创建 `PRE_BLENDER_MASTER_V2.FCStd` = 最新 WORKING 物理 + 9 窗语义(85/85 链接解析)
- V003 家具源 = PRE_BLENDER_MASTER_V2,V002 旧 delta 全部不叠加

## V002 撤销项(不再作为事实)

| V002 delta | V003 处理 |
|---|---|
| 次卧衣柜 −187mm | **作废** → USER_MANUAL_CORRECTION,采用文件位置,深 500mm 不变 |
| 次卧小床 +197mm | **作废** → USER_MANUAL_CORRECTION,采用文件位置 |
| 3kg 洗衣机 −107mm | **作废** → 语义搞反:冲突对象是湿区边界不是洗衣机 |

## V003 正式化记录

### USER_MANUAL_CORRECTION_KEPT(人工位置原样保留)

- **次卧小床1.2** `Rectangle017` @ R-STUDY — 位置=FCStd 原文;owner: human position is authoritative; residual overlap 2 rect(s) accepted
- **3kg洗衣机** `Rectangle041` @ R-BATH-P — 位置=FCStd 原文;owner: human position is authoritative; residual overlap 1 rect(s) accepted
- **次卧衣柜** `Rectangle045` @ R-STUDY — 位置=FCStd 原文;owner: human position is authoritative; residual overlap 3 rect(s) accepted

### REGION_BOUNDARY_CLEANUP(修区域边界,不动内容)

- **客卫（湿区）** `Rectangle007` @ R-BATH-P
  - 手绘边界 `[8078.875, 9863.5, 9722.625, 10859.65625]` → 正式 `[8078.875, 9863.5, 9697, 10697]`(贴墙体内表面)
  - wet-zone boundary clipped to wall inner face; contents unmoved
- **主卫湿区** `Rectangle033` @ R-BATH-M
  - 手绘边界 `[15205.625, 4774.75, 16205.625, 6343.75]` → 正式 `[15205.625, 4774.75, 16205.625, 6297]`(贴墙体内表面)
  - wet-zone boundary clipped to wall inner face; contents unmoved
- **次主卫湿区** `Rectangle036` @ R-CLOAK
  - 手绘边界 `[10473.75, 4749.875, 11373.75, 6349.875]` → 正式 `[10473.75, 4749.875, 11297, 6297]`(贴墙体内表面)
  - wet-zone boundary clipped to wall inner face; contents unmoved

### AUTO_DRAFTING_CLEANUP(≤50mm 明显绘图误差自动修正)

- **主卧衣柜** `Rectangle015` @ R-MASTER:Δ +0.0/-31.2mm,尺寸 2100×600 不变
- **鞋柜** `Rectangle031` @ R-DINING:Δ +0.0/+18.0mm,尺寸 300×722 不变
- **主卫洗手盆和柜体** `Rectangle035` @ R-BATH-M:Δ +0.0/-48.7mm,尺寸 1200×500 不变

### HUMAN_ACCEPTED_AS_DRAWN(人工批准按原样,不再处理)

> owner decision 2026-09-29:以下项明确批准为按图所画,NO_MOVE / NO_AUTO_FORMALIZATION / NO_FURTHER_COLLISION_FIX,从 FORMALIZATION_PENDING 移除。
- **主卧电视柜** `Rectangle022` @ R-MASTER
- **主卫马桶** `Rectangle034` @ R-BATH-M
- **次主卫马桶** `Rectangle038` @ R-CLOAK
- **双人位** `Rectangle047` @ R-LIVING

## 3kg 洗衣机语义更新

```
3KG_WASHER_POSITION = HUMAN_APPROVED(FCStd 原位,未移动)
3KG_WASHER_INSIDE_WET_ZONE = TRUE
type = WALL_MOUNTED_COMPACT_WASHER_CANDIDATE (B1 按壁挂高度 blockout: z=+750, 450×450×500 TEMP)
SKU_TO_VERIFY | INSTALLATION_TO_VERIFY | MEP_TO_VERIFY
待落实:SKU 外形 / 墙体承重 / 安装高度 / 给排水 / 防水节点 / 插座 / 与淋浴玻璃和动线的关系
```

## 关闭状态(2026-09-29)

```
PRE_BLENDER_MASTER_V2 = PASS        WINDOW_SEMANTICS = PASS (9/9, 85/85 links)
LATEST_HUMAN_EDITS_SYNC = PASS      B1_V003_GEOMETRY = PASS
B1_V003_FIDELITY = PASS (47/47)     FORMALIZATION_REVIEW = CLOSED
B1_BLOCKOUT = READY_FOR_SPATIAL_HUMAN_REVIEW
formal_cad_allowed = false          construction_docs = HOLD
```