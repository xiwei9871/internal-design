# FURNITURE_ORIENTATION_AUDIT V1

自动推断家具语义朝向，替代 FreeCAD 手工标注。
生成: `scripts/furniture_orientation_inference_v1.py`

## Convention

```
geometry_axis_deg    长轴方向 [0,180)  CCW from +X (CAD mm, x东 y北)
semantic_facing_deg  正面朝向 [0,360)  0=E 90=N 180=W 270=S; null=NOT_APPLICABLE
```

GEOMETRIC_AXIS ≠ SEMANTIC_FACING：矩形只能定轴，180° 正反由语义规则解决。

## Inputs（read-only）

- `b1_model.json` — 47 furniture rects + room polygons
- `furniture_3d_dimension_register_v01.json` — semantic types
- `KITCHEN_CABINET_3D_REGISTER_V01.json` — 橱柜 PDF 权威（supersedes generic K-*）
- `master_direct_arch_v1_walls.json` — 提取的墙带（判"靠墙"）

## 核心规则实现

| 规则 | 实现 |
|---|---|
| back-against-wall 类（衣柜/电视柜/浴室柜/马桶/书柜/冰箱/洗衣机…） | `interior_facing`: 找出有墙贴合的边（gap<400mm，含嵌入墙内的负 gap），**正面 = 无墙侧中朝向房间中心的方向** — 解决了"嵌入墙带导致靠墙检测漏检"和"角落两面靠墙"两个坑 |
| BED | 同 zone 找 HEADBOARD；facing = 床头板→床方向（脚的方向） |
| HEADBOARD | 反面贴墙，正面朝 BED_BASE |
| SOFA/CHAISE | 朝 coffee table（无则 media cabinet，再退 room center），约束在长轴的法线方向 |
| DESK | 朝同 zone 的 chair/stool；无则朝房间内侧 |
| DINING_CHAIR | 朝餐桌中心 |
| SHOWER_ZONE | 玻璃隔断朝浴室内侧 |
| DINING/COFFEE/SIDE TABLE、STOOL、BENCH | `NOT_APPLICABLE` 不画箭头 |
| 橱柜(PDF) | `interior_facing` 朝厨房内侧；保留 PDF confidence |

## 结果分布

```
HIGH   31   自动接受
MEDIUM 26   见图核对
LOW     1   Circle007 STUDY_ARMCHAIR —— 无规则命中，HUMAN REVIEW REQUIRED
```

58 件 = 47 FreeCAD 家具 + 11 PDF 橱柜（generic K-* 已排除）。

## 抽查核对

- SOFA_3S(西墙) → E(0°) 朝电视柜 ✓
- 主/次卧床 → W(180°)，床头板在东墙 ✓
- K-RUN-E/K-WALL-E(东段) → W(180°) ✓；K-RUN-S/K-SINK(南段) → N(90°) ✓；冰箱+高柜 → S(270°) ✓
- 客卫马桶 → E(0°)，背贴西墙 ✓

## Outputs

- `furniture_orientation_register_v01.json`
- `FURNITURE_FACING_REVIEW.png`（绿=HIGH 橙=MEDIUM 红=LOW，NOT_APPLICABLE 不画箭头）

## 下一步

`asset native forward-axis calibration`：把 `semantic_facing_deg` 映射到 Pascal catalog 模型的本征 forward 轴 —— 本轮未做。
