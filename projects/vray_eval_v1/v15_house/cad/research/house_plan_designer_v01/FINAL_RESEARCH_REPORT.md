# CAD_RESEARCH_V02 — 最终研究报告

研究线 A：CADVEC 尺寸审计 · 研究线 B：专业 DXF 制图表达
上游：`ZWD11/house-plan-designer` @ `ab7bb1c52eeb0056bfff782ba71bb9f5faa1e1ab`（MIT，已 vendor）
执行日期：2026-10-18 · 全部测试在 `research/` 隔离区完成，未触碰生产文件/冻结 Blender/台账。

---

## 研究线 A — CADVEC 判定：**ADAPT（条件采用）**

### 实际运行结果（非纸面评估）

| 测试 | 结果 |
|---|---|
| A 尺寸约束（measured_working.dxf） | ✅ 18 原生 DIMENSION 提取，13 条进入最小二乘方程，**全自洽零冲突** |
| A 尺寸约束（数字化基准图） | ❌ `INSUFFICIENT_DIM_EVIDENCE`——A-DIMS 无 45° 起止符号，39 条标注不可机读 |
| B 纯几何 vs 约束模式 | ✅ 19/19 墙坐标逐位一致（约束不扭曲自洽输入） |
| C 现状 vs 原始设计 | ✅ 外轮廓差 ~1%，**内部隔墙体系完全不同**，墙厚 200 标称 vs 实测 174–348 → `AS_BUILT_VARIATION`（见 `dimension_overlay.png`） |
| D 负向测试（3 种注入） | ⚠️ **仅 1/3 显式检出**：同段互斥标注 → `dim_conflicts`；标注↔几何矛盾 → 降级 `?` 不报告；**DIMENSION 文字覆写 → 静默采信且污染墙体坐标 27–443mm，零告警** |

### 价值与缺陷

**能提供我们没有的能力**：标注当约束的加权最小二乘解算（细部>轴线>总尺寸的权重设计）、
刻度-界线-构件三方关联、图纸自相矛盾检测。

**实测暴露的缺陷**（决定了不能直接 ADOPT）：
1. 文字覆写盲信——对审计场景是**安全隐患级**缺陷；
2. 冲突报告只覆盖"互斥标注残差"一种情形；
3. ordinate 标注不可验证；无起止符号的图纸约束完全不启动。

**集成路径**：只抽取解算核心（~150 行 numpy），自写输入适配层（~300-400 行，从我们的
A-DIMS/原生 DIMENSION/台账喂三元组），并在采信任何标注前加"覆写值 vs 测量值"自校验。
**风险**：低——纯验证旁路，不触生产几何。

---

## 研究线 B — DXF 制图表达判定：**部分 ADOPT**

详表见 `CAD_STYLE_GAP_ANALYSIS.md`。我们原被低估：上游 DXF 导出是真原生
DIMENSION+DIMSTYLE，不是画线——但仍有模型空间图框、无纸空间视口、SHX 字体依赖等短板。

### POC 实测（`A102/A103_STYLE_POC.dxf`）

**实质改善**（对比图 `comparison/`）：
- 轴网从无到有（竖 1–8 / 横 A–F，CENTER 线型，几何推导自墙中线，纯标注）
- 门窗编号 M1–M9/W1 锚定现有块参照
- 线宽完整体系（原约半数图层为默认线宽）
- 中文标题栏字段补全

**数据完整性验证（脚本断言，非看图说话）**：
- 原实体缺失 0 / 几何变更 0（逐 handle 指纹对比）
- XDATA 实体 146→146 / 205→205 零丢失
- 34 条 DIMENSION 数值全部不变
- 冻结层集合一致、audit 0 errors、无 handle 冲突（曾踩 `dimblk=OBLIQUE` 生成块撞 handle，已改 `dimtsz` 方案修复）
- 新增标注对象全部登记 `style_poc_manifest.json`

**可安全并入 `cad_style.json` 的配置**：分层线宽表、AXIS/AXIS-NUM/DOOR-NUM/WIN-NUM 图层定义、
GB DIMSTYLE、标题栏字段模板。

**必须等专业 CAD 人工验证**：GB 斜杠标注渲染、CENTER 线型比例、中文 TTF 替换行为、
1:50 打印实测（本机无 QCAD/AutoCAD → `NOT_RUN`）。

**A201/A202/A302/A303 复用性**：线宽表+轴网生成器+门窗编号+标题栏全部可复用；
多道外围尺寸链与门窗表是下一步中等工作量项。

---

## Gate 状态

- [x] 未安装 skill 到全局 · [x] 未覆盖原始 CAD/正式 A102-A103 · [x] 未动 FreeCAD/Blender
- [x] 未自动采信解算结果 · [x] 未解除任何 HOLD · [x] 无大规模重构 · [x] 未推广到其他图
- 结构/复尺/北阳台/专业编辑器打印等 HOLD 全部保持

**停在 Gate，等待 ChatGPT + 业主审核后决定是否吸收。**
