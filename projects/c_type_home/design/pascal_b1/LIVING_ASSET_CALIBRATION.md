# LIVING ASSET CALIBRATION V1 — HUMAN_REVIEW

状态：**HUMAN_REVIEW**（本轮门槛，等待人工确认）
场景：http://pascal.localhost:57071/editor/pascal-living-calib-v1
（96 个 arch 节点原样保留 + 6 个校准 item；未改动 FreeCAD / 建筑 / 家具位置 / 朝向登记册）

## 约定（统一写死在 scripts/pascal_living_asset_calibration_v1.py）

- 世界系：x=东(+CAD x)，y=上，z=南(-CAD y)
- `cad_facing_to_pascal_yaw(θ) = (90 + θ) mod 360°`，θ 为 CAD 方位角（0=东，90=北）
- 前提：候选 asset 的 native front 均为 GLB +Z（由模型结构判断，见下表证据列）
- 锚点：FOOTPRINT_CENTER_ON_FLOOR——`position.xz = 目标中心 − R·(s ⊙ 局部bbox中心)`，`position.y = −minY·sy`
- 渲染器实测（item_renderer bundle）：`scale` 直接乘 GLB 米单位；`rotation` 是 three.js Euler 弧度 [x,y,z]
- catalog `dimensions` 字段只是标称展示值，本表 scale 按 GLB 实测 bbox 计算

## 逐件结果

| 家具 | asset | native dims (x,y,z m) | native front | yaw | scale (x,y,z) | 判定 |
|---|---|---|---|---|---|---|
| SOFA_3S Rectangle046 | sofa | 2.05×0.73×1.01 | +Z（框架背侧伸到 z−0.55，坐垫开口 +z+0.45） | 90° | 1.12×1.16×0.89 | PASS（plan 比 1.26，中等拉伸，MEDIUM） |
| SOFA_2S Rectangle047 | sofa | 同上 | +Z | 0° | 0.93×1.16×0.84 | PASS（近似等比，HIGH） |
| CHAISE Rectangle048 | lounge-chair | 0.67×1.03×1.25 | +Z（靠背块 z<0，腿托伸 +z） | 90° | 1.34×0.78×1.36 | PASS（等比 ~1.35；朝向语义存疑→见下） |
| COFFEE_TABLE Rectangle049 | coffee-table | 1.72×0.29×1.03 | n/a 对称 | 90°（长轴转南北） | 0.58×1.36×0.53 | PASS（plan 近似等比；拉高 1.36 达 400 高） |
| SIDE_TABLE Circle | bedside-table | 0.44×0.48×0.46 | +Z（抽屉拉手在 +z） | 0° | 1.13×1.04×1.10 | PASS（近似等比） |
| MEDIA_CABINET Rectangle004 | tv-stand | 1.85×0.35×0.32 | +Z?（开口面假设，待渲染复核） | 270° | 1.56×1.39×0.94 | **SIZE_DISTORTION**（plan 比 1.66：长向拉伸 56%） |

## 需要人工复核的点

1. **MEDIA_CABINET = SIZE_DISTORTION**：目标 2.89m 长墙挂电视柜 vs tv-stand 原生 1.85m → x 拉伸 1.56。观感上是细框开放格，拉伸后格子变稀。可选：换 `closet`/`dresser`/双拼两个 tv-stand，或接受拉伸。
2. **tv-stand 开口面假设 +Z**：GLB 只有单个对称 box primitive，bbox 无法判定开口侧；当前按全 catalog 惯例 +Z。若渲染出面朝墙，把 yaw 270°→90°（correction 180°）即可。
3. **CHAISE 朝向语义**：登记册 facing=90°(北) 但 footprint 1.7(E-W)×0.9。按"躺轴 E-W、靠背西端、开放侧朝北"放置（yaw 90）；若设计意图是"躺轴南北正对茶几"，则 footprint 与 facing 自相矛盾，需回设计层。
4. tv-stand pivot 悬空在中高（minY=-0.207）——已用锚点归一化抬到 y=0.287，落地高度正确；若最终要悬浮式电视柜，挂载标高 TO_VERIFY（登记册本来就标了）。

## 已排除

- `couch-medium`/`couch-small`：原生 4.69m / 2.89m 宽且座深 2.2m 的 stylized 比例，缩到目标 footprint 会压扁座深 → WRONG_ASSET
- `sunbed`：户外躺床语义不符
- `livingroom-chair`：扶手椅语义不符贵妃榻 footprint（改用 lounge-chair）

## 产物

- `FURNITURE_ASSET_CALIBRATION_V01.json` — 每件含 native dims/pivot/front/correction/final_yaw/anchor_offset/scale/分类
- `SOFA_NATIVE_AXIS_REVIEW.png` — 5 个候选 asset 的 primitive 结构四向视图（front 判定证据）
- `LIVING_PRIMITIVE_VS_ASSET_PLAN.png` — primitive 矩形 vs 预测 asset footprint（6/6 边重合）
- `LIVING_CALIBRATED_3D.png` — 校准场景实拍：SOFA_3S 朝东、SOFA_2S 朝南、贵妃椅东西躺轴靠背在西、茶几/角几/电视柜落位正确

验证方式：plan overlay 全部重合（解析验证）+ 3D 实拍朝向语义核对（视觉验证）。
