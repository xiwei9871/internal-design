# P1.3.1 几何裁决与 Gate 修复复核报告

**Gate: HOLD (自动判定已收紧, 遗留裁决项全部台账化)** | 分支 v15-cad-pipeline-2026-10-17 | 基线提交 a1fd046

## 审阅问题 → 处置

### A. 5 条未绑定可见 A-WALL → 全部处置 (`legacy_unbound` 台账)

| handle | bbox | 判定 | 处置 |
|---|---|---|---|
| 1CD | x7800-7900 y4670-5000 | 被 `W_INT_X7900_U#p0` 残段覆盖 | DELETED_superseded |
| 1D4 | x9050-9200 y4942-5150 | 被 R3 次卫隔墙覆盖 | DELETED_superseded |
| 1D5 | x9050-9200 y5230-6450 | 被 `md_0018`/R3 覆盖 | DELETED_superseded |
| 1E4 | x3700-7000 y13790-13900 | 被 W_BAY_F/soffit 组覆盖 | DELETED_superseded |
| 1F3 | x7400-7800 y200-500 | 被 `md_0012/md_0041` 覆盖 | DELETED_superseded |

`G15_no_unbound_visible_walls` = PASS (0 条可见无源墙线)。未被覆盖的将转 A-UNCERTAIN, 不会静默删除。

### B. 去重/差集收紧

- **跨状态自动合并 → 台账化**: bbox-IoU 合并遇 design_status 不同 → `merge_review` 登记; part 级吸收同样标 `review:REQUIRED`。`adjudication_ledger_v04.json` + `adjudication_v04.csv` 共 **40 条**裁决项(5 legacy + 跨状态合并 + 32 吸收)。`G16` = HOLD 等待人工裁决, 不再自动 PASS。
- **拆除 vs 门洞分离**: `demolished_parts`(DEMO 矩形差集) 与 `opening_cuts`(9 门洞差集) 分开登记; `G17` 验证 A-DEMO 实体数 == demolished_parts, 门洞裁切不计入拆除。
- **D02 五处拆改对象映射补齐**: `W_INT_CLK_N/E/W`(衣帽间隔墙)= 第 5 处拆改 → `EXISTING_DEMOLISHED` → A-DEMO 登记(修复了 parts:[] 被过滤的 bug); `W_INT_COR_N_STUB` 维持 UNVERIFIED。
- **静默回退不再算 PASS**: 剖切失败的墙对象标 `FOOTPRINT_FALLBACK`, `G18` = HOLD 列出全部 26 组。

### C. QA 真实性

| Gate | 修复 |
|---|---|
| G1 | 改为 live 重算衍生物 SHA + parent∈live sources |
| G4 | 对象名逐一查 fc/blender raw dump |
| G12 | 改为 polygon **boundary** 距离(不再允许锚点落在墙内) |
| G15-G18 | 新增: 未绑定墙线/跨状态合并台账/DEMOL分类/剖切回退 |
| 报告隔离 | 生成器 BLOCK 写 `derived/qa_block_<geo>.json`, 不再覆盖 `qa_report_v04.json` |

### D. 局部对比裁剪 (A103_V4_crop_*.png)

厨房拆改+门洞 / 错层台阶扶手 / 次卫新隔墙 vs 旧衣帽间 / 北阳台封窗位 — 各含 V3(淡)/V4(实) 对比 + 对象 ID 标注。

## 当前 Gate 一览 (qa_report_v04.json)

PASS: G1-G5,G7-G12,G15,G17 | **HOLD**: G6(38存疑+1 UNVERIFIED), G16(跨状态合并待裁决), G18(26组剖切回退) | PARTIAL: G13,G14

## 遗留

- G16 裁决需人工确认 40 条台账 → 裁决后可标 APPROVED
- G18 回退墙对象需 OCC slice / 更优剖切替代
- 结构安全/封窗合规/现场复尺独立 HOLD 不变
