# B1 FIDELITY REPORT V003 — 世纪欣园

> 2026-09-29 | 双轨制:RAW_SOURCE_FIDELITY + FORMALIZATION_DELTA

## RAW_SOURCE_FIDELITY(源文件 → Blender)

| Gate | 结果 |
|---|---|
| 家具/设备 XY 中心漂移 | **46/46 max 0.001mm**(blend 对象 vs b1_model 正式 rect) |
| 窗语义链接解析 | 9/9 WINDOW_REF → 物理几何(源端 freecadcmd 校验) |
| 墙/门洞/玻璃开口 | canonical rect 1:1 拉伸,门语义已决议(见 DOOR_SEMANTIC_RESOLUTION) |
| 错层 | 东翼 +350 TEMP,踏步 175/350 TEMP |
| `Rectangle` 847×3163 | 排除建模(recorded exclusion,FCStd 未动) |

## FORMALIZATION_DELTA(正式化层,b1_model.json 机读)

| 类别 | 数量 | 含义 |
|---|---|---|
| USER_MANUAL_CORRECTION_KEPT | 3 | 用户人工位=权威,撤销 V002 自动 delta |
| REGION_BOUNDARY_CLEANUP | 3 | 湿区边界裁剪贴墙内面,内容不动 |
| AUTO_DRAFTING_CLEANUP | 3 | ≤50mm 绘图误差自动平移 |
| FLAGGED_KEPT_HUMAN_POSITION | 5 | >50mm 冲突保留人工位,待裁决 |

## V003 vs V002 差异

V002 的 3 个大位移(衣柜−187/床+197/洗衣机−107)全部撤销 —— 语义错误:那些是人工设计位与区域边界问题,不是家具绘图误差。当前 blend 中次卧/客卫对象=FCStd 原文位置。
