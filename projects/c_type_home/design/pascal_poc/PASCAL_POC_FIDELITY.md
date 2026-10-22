# PASCAL_POC_FIDELITY — 客厅+餐厅+北阳台

> 源:`PRE_BLENDER_MASTER_V2` / `b1_model.json`(canonical mm)→ Pascal m(X/Z 平面)

## 家具位置(中心点,实测)

| 对象 | canonical→Pascal 中心偏移 |
|---|---|
| SOFA_3S 三人位 | 0.2 mm |
| SOFA_2S 双人位 | 0.4 mm |
| CHAISE 贵妃椅 | 0.3 mm |
| COFFEE_TABLE 茶几 | 0.4 mm |
| SIDE_TABLE 角几 | 0.3 mm |
| DINING_TABLE 餐桌 | 0.6 mm |
| DINING_CHAIRS ×4 | 0.3–0.6 mm |
| LAUNDRY_STACK 洗烘叠放 | 0.4 mm |
| FREEZER 冰柜 | 0.4 mm |

**max drift = 0.6 mm(仅 mm→m 舍入)。room reassignment = 0,semantic reassignment = 0。**

## 开口

| ID | canonical | Pascal | Δ |
|---|---|---|---|
| W-LIV-N(凸窗主洞) | x3800–6900 w=3100 | wall t=0.51→center 5.352 w=3.1 | +2 mm |
| W-LIV-N bay front | —(飘窗正面) | w=3.1 center 5.35 | 0 |
| G-LIV-NBALC | y11800–12650 w=850 | t=0.774→z 12.223 w=0.85 | −2 mm |
| G-GB-BALC | x10400–12400 w=2000 | center 11.4 w=2.0 | 0 |
| ENT-1 | y5064–6764 w=1700 | z 5.908 w=1.7 | −6 mm |
| G-DIN-LIV | x2950–5650 | wall 2.7m + window w=2.6 | −0.05m 宽(玻璃隔断以窗近似) |

## 墙

12 段全部按 canonical 中心线建(thickness 0.2/0.12/0.1),北阳台 parapet h=1.05 TEMP,其余 h=2.5。

## 已知 catalog 尺寸差异(非位置误差)

catalog 资产为名义尺寸:sofa 2.5×1.5(源 2.3×0.9)、dining-table 2.5×1.0(源 1.6×0.8)、
washing-machine 1×1(源 0.6×0.6)、fridge 1×1(源 1.2×0.6)。
→ `check_collisions` 报出的 5 处 overlap 全部是 catalog 名义尺寸造成,非源位置错误。
要尺寸精确需自定义 item / scale,当前 blockout 阶段记录即可。

## 缺项

- 无 slab/ceiling(verify_scene issue,PoC 范围未建,renders 中无地板)
- 错层:本区域不涉及(东翼+350 在卧室翼)

## furniture-fit 实测(furniture-fit skill 方法,check_collisions.candidate)

候选 `DINING_TABLE_real_1600x800`(实测 1.6×0.8,h=0.75)@ 人工位姿 (3.828,3.464) rot=0:

- footprint bounds [3.028–4.628]×[3.064–3.864]m,**完全在 ROOM_DINING 多边形 [2.9–5.7]×[2.56–7.9] 内**
- 与 4 把餐椅(真实位)无碰撞 — 唯一报告的 overlap 是与 catalog 占位餐桌自身(同位,预期)
- **verdict: footprint fits at tested pose**(零间隙)
- 未测/不声明:垂直净空、门扇摆动、搬运路径、mesh 细节接触、安全规范 —— 全部 `not checked`
