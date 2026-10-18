# P1.3.2 裁决执行安全与施工状态核对 — 复核报告

**Gate: HOLD (风险收敛为显式台账, 无静默自动裁决)** | 分支 v15-cad-pipeline-2026-10-17

## 任务落实

### 1. 跨状态合并: 真正禁止未批准合并

- 提取器 merge: `design_status` 不同 → **不合并**, 双方作为独立候选保留, 记入 `conflicts[]`
- 合并/吸收仅在同状态或 `adjudication_approvals.json` 显式批准时发生
- part 级 >95% 覆盖: 同状态→吸收(auto); 跨状态→`overlap_unresolved` 双保留
- **T-F 回归**: `W_EXT_N_BAL`(EXISTING_DEMOLISHED) vs `W_wall_md_0062`(PROPOSED_NEW) bbox 重合 → 双保留; 全图 0 个未批准混状态绑定 → PASS
- 冲突的非现状侧绘制到 `A-CONFLICT` 层(品红, 可见), 不静默不隐藏

### 2. D02 五处映射 (权威: make_a102 DEMO_FULL/PART)

| 决策 | 对象 | 范围 | 状态 |
|---|---|---|---|
| 厨房西墙中段 | W_INT_X5800 | y1800-3800 局部 | partial demo ✓ |
| 走廊西墙中段 | W_INT_X7900_U | y5000-7800 局部 | partial ✓ |
| 生活阳台北墙东段 | W_BALC_N | x3300-5800 局部 | partial ✓ |
| 客厅北墙旧带 | W_EXT_N_LV | 整段 | EXISTING_DEMOLISHED ✓ |
| 阳光房北带 | W_EXT_N_BAL | 整段 | EXISTING_DEMOLISHED ✓ |

**修正**: 此前把 `W_INT_CLK_N/E/W` 误记为第 5 处 → 实际第 5 处是 `W_EXT_N_BAL` 阳光房北带; CLK 三面墙改 `DESIGN_REVIEW_PENDING`(衣帽间→次卫映射待裁决, A-UNCERTAIN)。厨房拆除矩形由模型推测 y700-4100 更正为 A102 权威 y1800-3800。

`d02_mapping_v05.csv` = 对象×位置×决策×面积对应表。

### 3. 历史墙线删除复核 (任务3)

新规则: 覆盖>98% **且** 残余<5000mm² 才删; 否则残余保留→A-UNCERTAIN。结果: **7 条全部 MOVED_to_A-UNCERTAIN_residual_kept**, 0 删除 —— 包括:
- `1E4` 残余 363000mm² (大面积未等价, 正确保留)
- `1F3` 覆盖仅 87.5% → 保留
- `1D4`/`1D5` 对照 A102 NEW 清单是次卫门垛设计位 → 残余保留待裁

### 4. 台账归并 + 剖切回退分类

`wall_adjudication_v05.csv`: 32+事件按 2500mm 空间邻域归并为 **8 个物理案例**:
- CASE-01 西墙带(入口/阳台西墙, 冲突+fallback)
- CASE-02 厨卫中心带(最大群: R3/CLK/D107/md_* 共41对象)
- CASE-03 次卫隔墙, CASE-04 东北角, CASE-05 飘窗, CASE-06 入口墙, CASE-07 主卧南带, CASE-08 北阳台门垛
- `needs_owner=YES`: 4 组; `auto_resolvable`: 多数 subsumed/fallback

`FOOTPRINT_FALLBACK` 分类: `OVERHEAD_NOT_PLAN_WALL`(窗头/过梁, z>2000)→改画 A-DESIGN 不占墙线; `BELOW_CUT`(矮墙/窗台); 剩余真 fallback 全墙 → `G18` HOLD 列表。

### 5. 审查图 + QA

- 4 张局部图自动收紧到内容边界 + 对象 ID/状态标注 + 品红冲突/橙存疑/红新建着色
- QA: G16 未批准混状态绑定→**BLOCK**; G17 改对象级(实体 vs demolished_part 几何一致); G18 分类回退; 生产QA与测试BLOCK报告隔离
- `qa_report_v05.json`: PASS×13 / HOLD(G6存疑, G16冲突28项, G18回退) / PARTIAL(G13,G14)

## 需要谁判断

| 类型 | 可自动 | 业主裁决 | 专业(结构/现场) |
|---|---|---|---|
| subsumed 同状态重复 | ✅ (auto) | | |
| overlap_unresolved 跨状态 | | ✅ 28 项(CASE-01~06) | |
| DESIGN_REVIEW_PENDING CLK墙 | | ✅ 衣帽间→次卫映射 | |
| FOOTPRINT_FALLBACK 全墙 | | | ✅ 待 OCC slice 替代 |
| 结构安全/封窗合规 | | | ✅ 独立 HOLD 不变 |

## A102 只读勘察

`a102_diff_survey.csv`: 139 行对象级 EXISTING_RETAINED/DEMOLISHED/PROPOSED_NEW/PENDING/UNVERIFIED 差集台账(数据, 非图纸)。
