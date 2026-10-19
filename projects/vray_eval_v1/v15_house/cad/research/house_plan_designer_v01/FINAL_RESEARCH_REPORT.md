# CAD_RESEARCH_V02 — 最终研究报告（Gate 复核修订版）

研究线 A：CADVEC 尺寸审计 · 研究线 B：专业 DXF 制图表达
上游：`ZWD11/house-plan-designer` @ `ab7bb1c52eeb0056bfff782ba71bb9f5faa1e1ab`（MIT，已 vendor）
执行日期：2026-10-18 · 全部测试在 `research/` 隔离区完成，未触碰生产文件/冻结 Blender/台账。
本轮修订响应 Gate 复核意见：证据等级纠正、最小适配器实验、轴网改共享控制线、
编号绑定对象 handle、样式配置独立为候选文件。

---

## 研究线 A — CADVEC 判定：**ADAPT（收窄版）**

### 实际运行结果

| 测试 | 结果 |
|---|---|
| A 尺寸约束（measured_working.dxf） | ✅ 18 原生 DIMENSION 提取，13 条进入最小二乘方程，全自洽零冲突 |
| A 尺寸约束（数字化基准图） | ❌ `INSUFFICIENT_DIM_EVIDENCE`——A-DIMS 无起止符号，39 条标注不可机读 |
| B 纯几何 vs 约束模式 | ✅ 19/19 墙坐标逐位一致 |
| C 现状 vs 原始设计 | ⚠️ 外轮廓差 ~1%、内部隔墙体系不同、墙厚 200 vs 174–348——**改判 `CROSS_SOURCE_DERIVED_DIFF`**：基准图是同图派生数字化件，差异 ≠ 已证实的施工偏差，须独立现场复测佐证 |
| D 负向测试（3 种注入） | ⚠️ 仅 1/3 显式检出；文字覆写被静默采信且污染墙体坐标 27–443mm |

### A2 最小适配器实验（Gate 修正版 v2）

`mini_dim_adapter.py` + `dimension_audit_mini.csv` + `ground_truth_15.json`
+ `ground_truth_eval.csv` + `test_dimtype.py`（6 tests PASS）：

- **dimtype 误判修复**：`dimtype&32`（块参照标志）≠ ordinate。实测 18 条全部
  `dimtype=32=base0 线性旋转`，按 `(dimtype&7)` 分类型、按角度投影法取几何测量，
  18/18 `CONSISTENT`（测量=投影，残差≤2mm）；文字覆写 0 例
- **GT 统计修正**：15 条人工标准答案（text_handle↔LINE handle↔测量端点证据，
  label_mid_offset 全部恰为 200.0 印证绑定正确）。比对结果 **9 正确 / 0 误配 /
  6 UNRESOLVED**；其中纯位置绑定 **0**（同行双链不可分），值辅助 9
- 值辅助绑定仅用于链归属消歧，**不作为独立几何正确性证明**（标注值参与绑定有循环性）

**收窄判定**：约束求解器抽取**暂缓**不变；只读审计适配器修正后通过回归，
列入可吸收候选。

---

## 研究线 B — DXF 制图表达判定：**部分 ADOPT（候选配置已分离）**

详表见 `CAD_STYLE_GAP_ANALYSIS.md`。候选配置 = `dxf_style/cad_style_candidate.json`，
**不并入生产 cad_style.json**。

### POC v2 修正（相对 v1 的变化）

- **轴网**：v1 逐图推导 → 两图 7/8 轴不一致（判不合格）。v2 用共享 `axis_basis.json`
  （A103 墙系外包单一来源），两图只发 4 条外包控制线 1/2/A/B，灰细点划线。
  **未发正式编号轴网**（无设计院轴号来源，基准可信度不足以支撑全轴网）
- **门窗编号**：共享 `opening_basis.json` 保证跨图同号；每条编号文字带
  `DEVINPOC` XDATA（group 1005 = 本地对象 handle + `semantic_object_id`
  `OPENING_DOOR_x_y`/`OPENING_WIN_x_y`，由基准位置生成，与 handle/创建顺序无关）。
  窗按开口线逐条编号 W1–W6；A102 无窗层 → 6 条如实记 `unmatched`，不推测补充
- **稳定性验证**：同源重生成两次，label→semantic_id→handle 映射零漂移；
  24 条 group-1005 handle 全部经 `entitydb` 解析成功
- **标题栏**：校正到纸空间图框右下角右对齐，避开既有图名文字
- **撤除**：无信息增量的多余标注未加；轴号圈颜色降为灰（不再红色贯穿）

### 完整性断言（has_xdata/get_xdata 逐实体读取 + grep 双重验证，`test_style_poc.py` 7 tests PASS）

- 原实体缺失 0 / 几何变更 0（逐 handle 指纹对比）
- XDATA：A102 DEVINSRC 146→146、A103 205→205、DEVINDIM 34→34
- 新增 DEVINPOC 15 条（A103）/9 条（A102）= 编号标注的指针数据
- 34 条 DIMENSION 数值全部不变；冻结层一致；audit 0 errors
- 专业 CAD 编辑器验证：**NOT_RUN**（本机无 QCAD/AutoCAD）

---

## 一页技术清单 — 允许吸收 / 继续研究 / 不采用

| 技术项 | 判定 | 理由 |
|---|---|---|
| **分层线宽表**（墙50/拆35/门窗25/尺寸13/家具13/轴13） | ✅ 允许吸收 | 断言验证无几何副作用；已入 `cad_style_candidate.json` |
| **GB DIMSTYLE 定义**（斜杠起止） | ✅ 允许吸收 | 仅新增样式定义，不改实体 |
| **纸空间标题栏字段模板** | ✅ 允许吸收 | 纯标注，位置已校正 |
| **共享轴基准机制**（axis_basis.json → 控制线） | ✅ 允许吸收 | 解决了跨图轴网不一致的根因 |
| **编号绑定方式**（DEVINPOC XDATA 1005→handle） | ✅ 允许吸收 | 满足"稳定语义对象 ID"要求且可追溯 |
| **标注-几何只读审计适配器**（mini_dim_adapter + test_dimtype） | ✅ 允许吸收 | dimtype 分类修正、回归测试通过、UNRESOLVED 诚实拒绝、无写回 |
| **cadvec 最小二乘解算核心** | 🔸 继续研究 | 当前输入喂不出有效约束集；等标准画法输入再评 |
| **多道外围尺寸链生成** | 🔸 继续研究 | 需要新排布逻辑，中等工作量 |
| **门窗表** | 🔸 继续研究 | 需洞口宽高等结构化数据支撑 |
| **ANSI31 拆改填充** | 🔸 继续研究 | 需验证打印效果，非必须 |
| **SHX 大字体方案** | ❌ 不采用 | 换机器缺字风险，TTF 已验证 |
| **模型空间图框** | ❌ 不采用 | 我们的真纸空间视口更规范 |
| **逐图自动轴网推导** | ❌ 不采用 | 正是跨图不一致的根因，已被共享基准替代 |
| **上游 HTML/JS 整体导出管线** | ❌ 不采用 | 与我们 ezdxf+XDATA 栈不兼容 |
| **HouseSpec/HTML 设计器整体吸收** | ❌ 不采用 | 超出本研究边界（Gate 明确不再扩展） |

## Gate 状态

- [x] 未安装 skill 到全局 · [x] 未覆盖原始 CAD/正式 A102-A103 · [x] 未动 FreeCAD/Blender
- [x] 未自动采信解算结果 · [x] 未解除任何 HOLD · [x] 无大规模重构 · [x] 未推广到其他图
- [x] 证据等级已纠正（AS_BUILT_VARIATION → CROSS_SOURCE_DERIVED_DIFF）
- [x] 样式配置为候选文件，未碰生产 cad_style.json
- 结构/复尺/北阳台/专业编辑器打印等 HOLD 全部保持

**停在 Gate，等待 ChatGPT + 业主审核后决定是否吸收。**
