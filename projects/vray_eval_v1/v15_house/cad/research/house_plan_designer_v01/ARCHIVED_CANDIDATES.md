# CAD_RESEARCH_V02 — 可复用候选归档（审核通过 7020a9a）

研究 Gate：**有条件通过 → 通过（封版）**。以下资产归档为"可复用候选"，
**状态为候选，不等于生产集成**；第三方研究本轮到此为止，不再扩展。

## 归档清单

| 候选 | 路径 | 状态 | 使用约束 |
|---|---|---|---|
| 统一线宽 + 中文标题栏模板 | `dxf_style/cad_style_candidate.json` | ✅ 可吸收候选 | 可在**独立副本**试用；**不得自动并入生产 cad_style.json** |
| 只读尺寸审计适配器 | `dimension_audit/mini_dim_adapter.py` | ✅ 可吸收候选 | 只读、无写回；dimtype 分类已由 `test_dimtype.py`（6 tests）锁定 |
| 15 条人工标准答案 + 审计报告 | `dimension_audit/ground_truth_15.json`、`ground_truth_eval.csv`、`CADVEC_POC_REPORT.md`、`dimension_audit*.csv` | ✅ 审计证据归档 | 标注权威/绘制几何近似的佐证；值辅助绑定不作独立正确性证明 |
| 样式 POC + 回归测试 | `dxf_style/A102_STYLE_POC.dxf`、`A103_STYLE_POC.dxf`、`make_style_poc.py`、`test_style_poc.py`（7 tests PASS）、`CAD_STYLE_GAP_ANALYSIS.md` | ✅ 可吸收候选 | 轴网只许走共享 `axis_basis`；编号机制见下 |
| 共享外包参考线机制 | `dxf_style/axis_basis.json` | ✅ 可吸收候选 | 单一来源、跨图同坐标；无可靠基准不发正式编号轴网 |
| 共享开口编号基准 | `dxf_style/opening_basis.json` | ⚠️ 条件性候选 | **门窗编号未来必须绑定永久工程对象 ID**（registry/台账对象），位置派生 ID（`OPENING_*_x_y`）仅为过渡方案，不得作为长期语义依据 |

## 明确不进入生产

- CADVEC 约束求解器（最小二乘核心）——暂缓，输入端喂不出有效约束集；
- house-plan-designer 完整 Skill / HouseSpec / HTML 设计器——不安装、不接入；
- `cad_style_candidate.json` 整体并入——禁止，须逐项经生产样式评审。

## 保留的 HOLD / NOT_RUN

- 人工审图未通过区域：全部保留 HOLD（台阶、北阳台、结构安全等）
- 专业 CAD 编辑与打印验证：`NOT_RUN`（本机无 QCAD/AutoCAD）
- 未自动采信任何第三方解算结果；未解除结构 HOLD

## 下一步

返回 `HUMAN_CAD_REVIEW_V01`：
- A102 — 现状真实性审核（对照实测测绘 CAD）
- A103 — Blender 设计一致性审核（对照冻结 `V15_WORK.blend` 俯视底图）

生成：2026-10-18 · 研究分支 `cad-research-v02-cadvec-style-poc`
