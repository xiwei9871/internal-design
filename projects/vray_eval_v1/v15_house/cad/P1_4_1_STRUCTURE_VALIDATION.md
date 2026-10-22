# P1.4.1 — 结构墙几何误判修复与重新校验

**审查**：`e2243e4` 中 `Polygon(pts)` 对未闭合 LWPOLYLINE 隐式闭合的缺陷
**修复提交**：本提交（P1.4.1）
**判定**：**HOLD_PENDING_STRUCTURE_VERIFY** — 误判已消除；`W_EXT_N_BAL` 按审查指令**保持拆除 BLOCK**（预防性），待真实黑白墙语义核实
**回归测试**：`p14_tests.py` **9/9 PASS**（含真实文件端到端 T9：拆除矩形结构覆盖 = 0.000）

---

## 一、缺陷确认（审查者取证全部坐实）

`structure_only_source_sync.dxf` `S-S.WALL` 层 215 实体中，北阳台附近 **3 条开放 4 顶点折线**：

| handle | 顶点 | 首尾缺口 | bbox |
|---|---|---|---|
| `307C3E` | 4 | **5413 mm** | x8000–12900 × y11100–13700 |
| `307C3F` | 4 | **5558 mm** | x7920–12980 × y11100–13780 |
| `307C40` | 4 | **5631 mm** | x7880–13020 × y11100–13820 |

另有 4 条开放折线（`307B44`/`307CC0`/`307CC1`/`307CC3`）。旧代码 `Polygon(pts)` 隐式补首尾边 → `307C40` 闭合后形成跨房间三角形，**恰好吞下整个 `W_EXT_N_BAL` 拆除矩形（1,020,000 mm²）→ 伪造的 100% 结构覆盖**。审查者推断完全正确。

## 二、修复内容

| 项 | 旧行为 | 新行为 |
|---|---|---|
| LWPOLYLINE | ≥3 点一律 `Polygon` | **仅 `e.closed=True`** 才成面；开放折线只把真实边段投回线网 |
| HATCH | `b.vertices` 失败即静默跳过 | PolylinePath 按 `is_closed` 判定；EdgePath 解析 LineEdge；奇偶嵌套定孔洞；开放路径同样只贡献边段 |
| LINE | polygonize 全收 | 仅真实闭合环成面，逐面过异常筛 |
| 异常面 | 无 | 自交→`make_valid` 修复或剔除；最小旋转矩形短边 >1200mm 且面积 >2e6 → `LARGE_FACE_NOT_WALL`；≤4 顶点巨面 → `SUSPECT_TRIANGLE` |
| 语义 | 未覆盖=MODIFIABLE | 未覆盖=**UNMARKED_INTERIOR**（内墙）或 **ENVELOPE_REVIEW**（外墙/阳台墙/柱，保守不可拆待核） |

## 三、修复前后覆盖率对照（关键项）

| 对象 | 类别 | 旧(legacy) | 新 | Δ | 解释 |
|---|---|---|---|---|---|
| **`W_EXT_N_BAL` 拆除矩形** | D02#5 | **1.000** | **0.000** | **−1.00** | 100% 全系伪造面 |
| `W_INT_X7900_U`（保留段） | 现状 | 0.205 | **0.564** | +0.36 | 旧代码漏解析 EdgePath HATCH（`307CFC` path2 柱 x7800–8900 y10300–11900），新算法补上——**新发现的结构柱** |
| `W_INT_X13000`（保留段） | 现状 | 0.502 | 0.260 | −0.24 | 伪造三角虚增部分剔除 |
| `VIEW_WALL_LIVING_FIX_GUEST_BATH_NORTH_JUNCTION` | 拟建 | 0.0 | **0.800** | +0.80 | 同上 EdgePath 柱，拟建墙骑柱——**新增真实冲突项** |
| `VIEW_WALL_LIVING_FIX_TV_NORTH_SOLID_WALL` | 拟建 | 0.0 | **0.799** | +0.80 | 同上 |
| `W_wall_md_0054` | 拟建 | 0.0 | 0.529 | +0.53 | 同上 |
| `W_wall_md_0016` / `md_0062` | 拟建 | 0.60 / 0.84 | <0.5 | 下降 | 北阳台伪造三角虚增，真实覆盖不足阈值 |
| 其余 D02（X5800 / X7900_U / BALC_N / N_LV） | 拆除 | 0.000–0.038 | 0.000–0.038 | ≈0 | 不变，但仍按指令视为"低重叠"而非"安全 PASS" |

完整 68 行对照：`derived/struct_coverage_before_after.csv`。

## 四、`W_EXT_N_BAL` 证据结论

- **伪造 100% 已消除**：修正后拆除矩形与任何合法结构面**零相交**（见 `nbal_three_source_evidence.png` 四联图，同坐标同比例）。
- **但零覆盖 ≠ 已证明可拆**：`S-S.WALL` 来自现状测绘同步件，不是开发商原图黑白墙字段的直接载体；基准 DXF 仅有 `A-WALL`/`A-UNCERTAIN` 层，**无受保护/可改造分类数据**。
- 按审查指令：**拆除维持 BLOCK**（预防性）。放行条件不变——结构方对照开发商原始图纸核实该外墙带性质。差异在于：现在 BLOCK 是"待核实"而非"已证伪"。

## 五、语义关系核查（任务 3）

| 事实 | 后果 |
|---|---|
| `S-S.WALL` 源自 `measured_working.dxf` 同步件，属**测绘语义**而非开发商原图字段 | 结构判定证据等级：**HATCH 填充 > 闭合边界 > 线网环**；开放折线不算证据 |
| `W_EXT_S` 南外墙 0% 覆盖 | 由 MODIFIABLE 改判 **ENVELOPE_REVIEW**——外墙/柱不重叠不自动等于可拆 |
| 全部 `COL_*` 柱 | 同上默认 ENVELOPE_REVIEW |
| 旧 15 处 NEW_WALL_ON_PROTECTED | 重组为 16 处：3 处新增（EdgePath 柱）、2 处移除（伪三角）、11 处不变 |

## 六、回归测试（`p14_tests.py`）

| 用例 | 断言 | 结果 |
|---|---|---|
| T1 | 开放 4 点 U 形折线内部无面 | ✅ |
| T2 | 闭合跨房间巨面被 `LARGE_FACE_NOT_WALL` 剔除 | ✅ |
| T3 | 200mm 闭合墙带正常成面 | ✅ |
| T4 | 开放折线+真实 LINE 补口可成环（网络规则允许） | ✅ |
| T5 | 4 LINE 围合成面 | ✅ |
| T6 | 闭合 HATCH 路径成面 | ✅ |
| T7 | 开放 HATCH 路径不独立成面 | ✅ |
| T8 | 蝴蝶结自交被标记 anomaly | ✅ |
| T9 | **真实文件**：`W_EXT_N_BAL` 拆除矩形覆盖 <5% | ✅ 实测 0.000 |

## 七、产物

| 文件 | 内容 |
|---|---|
| `three_source_mapping.py` | v2：`extract_structural()` 纯函数 + legacy 对照 + 新分类 |
| `derived/three_source_mapping.json` | 修复后映射 + `extraction.anomalies`/`open_polylines`/`semantic_limits` |
| `derived/struct_coverage_before_after.csv` | 68 行新旧覆盖对照 |
| `nbal_three_source_evidence.png` | N_BAL 四联证据图（同坐标/比例） |
| `p14_tests.py` | 9 项回归测试 |
| `P1_4_1_STRUCTURE_VALIDATION.md` | 本文 |

**未动**：`V15_WORK.blend`、全部原始 DXF/FCStd、业主设计。
**不变 HOLD**：`W_EXT_N_BAL` 拆除（预防性）、结构安全核验、现场复尺、封窗合规。
**A102/A103**：非冲突区域 POC 按授权可继续；北阳台段在任何图纸上保持未决标记。
