# P0.1+P0.2 — 错层波浪楼梯修复与审图视图纠正

## 根因修正（对 P0 的更正）

P0 曾将俯视弧归因于 `FLOOR_LOWER` 西缘。P0.2 实验证明**两个缺陷并存，但可见弧的真身是天花**：

| 部位 | 几何 | 与旧 FASCIA 曲线偏差 | 渲染可见 |
|---|---|---|---|
| `V7_CEILING_450MM_TRANSITION` 西缘(z2.80) | 旧弧整体抬升复制 | **均值 3mm** | **是 — 俯视里的弧** |
| `FLOOR_LOWER` 西缘 | 同族旧弧残余 | ~1mm | **否**（被踏步覆盖，原/候选渲染零像素差） |
| `STEP_0` 西缘 | 确认楼梯几何 | vs 天花 264–407mm | 是 |

天花专项图 `ceil_stair.png` 直接可见：过渡带西缘是一整条大弧面。量化：`ceil_edge vs fascia = mean 3mm / max 45mm (n=18)`；`vs step0 = mean 264mm / max 407mm`。**判定：旧休闲厅设计遗留**——吊顶过渡从未随波浪楼梯同步。不构成"有意独立造型"的证据：它与隐藏旧对象逐点重合。修正需业主单独授权（当前未授权，未动）。

## FLOOR_LOWER 修复（候选保留，不合入）

- 原网格备份 `floor_lower_orig_backup.json`；差异 `floor_moved_verts.json`
- 顶点吸附到 STEP_0 西缘：凸出 120 点东移 + 退缩 4 点西拉，**0 非流形 / 0 退化面 / validate 通过**，316v/502f 拓扑不变
- 新西缘贴合曲线 ≤±10mm；最大修正 380mm @y6.15；影响面积 **209,245 mm²**
- 渲染差异：俯视/全屋原候选均 0 像素差（该缘被踏步覆盖不可见）——数值修复有效，非视觉要素
- 原始 `V15_WORK.blend` sha `feaeed380c` **未变**；候选 `4a04a3e5`，仅候选修改

## P0.2 审核视图

`review_views.py`：临时 Scene 集合隔离，不改源对象 `hide_*`。
- **ARCH_FLOOR_PLAN_REVIEW**：排除 `V7_CEILING_TOGGLE_FOR_OVERVIEW`、`03_EXISTING_CEILING`；守卫=z>2.5m 水平面>1m²且占比>50%且与楼梯区重叠→FAIL；含 CEILING/吊顶 名→FAIL
- **REFLECTED_CEILING_REVIEW**：天花+楼梯+错层参照

守卫实跑验证：楼梯窗口 0 泄漏（manifest 记录）；全屋视图按"楼梯区重叠"判定不误伤墙楣/柜顶。

## CAD 防复发（joint_acceptance_v2 QJ11）

- **w4 不可识别→BLOCK**：冻结面积足迹缺失/不闭合/东缘<8300 → verdict=BLOCK
- 面积校验（冻结层）与可见线校验分开
- 可见层全开放+东缘<8300+恰 3 波线（顶点>20）+无独立第4条
- 方向箭头独立层且非波线实体
- 负向测试：删面积层→BLOCK、闭合可见轮廓→BLOCK、可见东缘→BLOCK、少踢面→HOLD
- 联合 QA：`verdict=PASS`（含 QJ11_stair_visible_lines=true）

## 证据（同窗口 5200–9200×4300–8600，全部直渲）

| 文件 | 内容 |
|---|---|
| `arch_orig_stair.png` / `arch_orig_plan.png` | 原版 ARCH 视图（无吊顶，楼梯3波显现） |
| `arch_cand_stair.png` / `arch_cand_plan.png` | 候选 ARCH 视图 |
| `arch_diff_overlay.png` | 原/候选叠加（0px 差，缘不可见） |
| `fix_candidate_oblique2.png` | 候选斜视：3级踏步+上下地坪交接清晰 |
| `p02_cand_a103_overlay.png` | 候选 Blender + A103 同坐标叠加，3 波重合 |
| `ceil_stair.png` | 天花专项：过渡带西缘=旧弧 |
| `*.manifest.json` | 各视图渲染集合/排除清单 |

STALE：旧底图/叠加已重命名 `*_STALE_20261019.png`（审图包 README 已更新）。

## 结论

1. 波浪楼梯 3 级表达在真实几何与 CAD 中均成立；旧弧=未同步天花设计遗留，已定位待业主授权。
2. FLOOR_LOWER 候选修复有效但非视觉要素，**保留候选不合入**（业主决策）。
3. 审图链路已改为隔离视图 + 守卫，"天花遮挡当地坪"类错误将直接 FAIL。
4. 维持 HUMAN_REVIEW：天花是否按楼梯边界重切为待定设计决策。
