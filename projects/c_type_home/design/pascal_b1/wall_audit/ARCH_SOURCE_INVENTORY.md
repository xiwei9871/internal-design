# ARCH_SOURCE_INVENTORY — 事实源清单(Phase 1: QUERY ONLY)

| 事实源 | 文件 | sha | 状态 |
|---|---|---|---|
| 最终墙体 | `design/pascal_b1/wall_audit/FINAL_WALL_REGISTER_V01.json/.md` | `ccc78186b4b9` | SOURCE_OF_TRUTH(三源 reconcile 完成,unexplained=0) |
| 最终门窗 | `design/s2_current_design_v1/FINAL_WINDOW_REGISTER_95ab90e.json/.md/.csv` | `73dcee675d5e` | SOURCE_OF_TRUTH(Task03A RC2.3 frozen,28/28 PASS,冲突=0) |
| 开窗语义 | `design/s2_current_design_v1/window_semantic_register_reopened.json` | `fc57ca5f64be` | 9 entries,broken=0,含每窗源 linework links |
| 门语义 | `design/b1_blockout/B1_DOOR_SEMANTIC_RESOLUTION.md` v002 | — | 已解决(D-ENS-OWNER / D-CONN-MB-SMB / REMOVE_FALSE_SEED) |
| 业主改造 | `cad/cad_change_registry.json` | `c32c23212e87` | 拆除/保留裁决 |
| 户型基线 | `qc/walls_baseline_246ff12.json` | `9cf4c96ec406` | 原始语义证据 |
| canonical | `design/b1_blockout/b1_model.json` | `4d1fca081caa` | **UNTRUSTED_DERIVED**(待 v2 重建) |

## 六个问题的回答

### 1. 最终 active physical wall = **42 段**
34 EXISTING_KEEP(含 5 段飘窗围护:W-BAY-JW/JE 客厅飘窗侧墙、W-BAY-STUDY-F/JW/JE)+ 8 PARAPET;另 9 段 EXISTING_REMOVED 保留历史不入 Pascal。

### 2. 最终 9 opening 类型
| id | type | span | host |
|---|---|---|---|
| W-LIV-N | **BAY_WINDOW** | 3100 proj900 | W-EXT-N-LV |
| W-STUDY-NE | **BAY_WINDOW** | 2100 proj700 | (register null → canon 挂 W-BAY-STUDY-F) |
| W-SMB-S | **BAY_WINDOW** | 2400 proj700 | W-EXT-S |
| W-MB-S | **BAY_WINDOW** | 2700 proj700 | W-EXT-S |
| G-LIV-NBALC | GLASS_DOOR | 850 | W-INT-X7900-U-TV |
| G-GB-BALC | GLASS_DOOR (double) | 2000 | W-INT-Y10800 |
| G-DIN-LIV | GLASS_SLIDING_DOOR (3-track) | 2700 | null(业主玻璃隔断) |
| W-LBALC-S | BALCONY_WINDOW | 4500 | null(南女儿墙上) |
| W-KIT-S | STANDARD_WINDOW | 1000 | W-EXT-S |

### 3. 飘窗 = **4 个**:W-LIV-N、W-STUDY-NE、W-SMB-S、W-MB-S

### 4. 南侧两个飘窗的真实 projection topology(register + canonical bay 数据)
凸出 700mm 盒体:立面开口 [x,−200..0] + 两侧 cheek + 正面玻璃带:
- W-SMB-S: cheeks [8400,−700,8500,0]/[10900,−700,11000,0],front [8400,−700,11000,−600]
- W-MB-S: cheeks [12000,−700,12100,0]/[14800,−700,14900,0],front [12000,−700,14900,−600]
- 数据在 canonical `window.bay` 字段里,但**从未升格为实体墙**。

### 5. 当前 canonical 错处
- 3 个飘窗(LIV-N/SMB-S/MB-S)的 cheek+front 只是 window 元数据,不是实体墙 → Pascal 拿不到凸出盒体。
- W-STUDY-NE 的 rect 被改写成凸出正面,register 的立面开口线 [10900–11100] 在 canonical 里丢了(开口原位没了)。
- 其余 walls/openings 与 register 对齐。

### 6. 当前 Pascal 错处
- **飘窗双重表达**:立面窗 + `BAY_FRONT_GLAZED` 薄墙带窗,两玻璃并存。
- **cheek 侧墙缺失**:除 study 外 3 个飘窗无侧墙 → 南向飘窗 = 立面线一片玻璃 + 外侧一片玻璃带,中间空气。
- **无窗台/平台几何**。
- **门宽 bug**:≥4 扇门 emitted width = 墙厚而非净开(D-SM 0.464 应 0.70;D-MB 0.434;D-BATHM/D-STUDY 0.40)。
- `W-INT-X13000`/`W-NBALC-E-PAR` 重叠登记未裁决。

## Phase 2 重建要点(待批准后执行)
`canonical_arch_v2.json` 一次性从 FINAL_WALL_REGISTER + FINAL_WINDOW_REGISTER + FINAL_BAY_WINDOW_REGISTER + door resolutions 重建;飘窗作为**建筑构件类**(opening + cheeks + front + sill)生成;`pascal-arch-truth-v1` 纯建筑层(墙/门窗/飘窗/错层),不含家具厨房。
