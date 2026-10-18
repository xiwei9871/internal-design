# P1.3 施工平面几何正确性验证报告

**Gate: HOLD (几何正确性技术门已过, 交付/裁决项保留)** | 分支 v15-cad-pipeline-2026-10-17

## 审阅意见 → 落实

| 审阅发现 | 状态 | 实现 |
|---|---|---|
| 无真剖切, concave_hull 投影 | ✅ | blender `tri∩z=h` 剖切线段→polygonize 环; 双标高 1150/1650, 按 zmin 选层; `cut_height` 记入 XDATA。FC 实体保留 vertex 壳(标注 cut:FC_SHELL 待 OCC slice, 见局限) |
| MultiPolygon 丢部分 | ✅ | `parts[]` 多部分保留: W_INT_X5800→2 段、W_EXT_N_LV→2、W_INT_X7900_U→2、R3→2; 每 part 独立实体 `#p{i}` |
| 孔洞轮廓丢失 | ✅ | `part_dict{exterior,holes}`: 内环作为独立边界实体绘制 (`#p{i}h{j}`) |
| 现状与拟建共同绘制 | ✅ | 5 处 D02 拆除矩形对 FC 轮廓做 shapely 差集 → 拆除段入 `A-DEMO`(冻结); A103 只画装修后构件 |
| ≥6 组重复轮廓 | ✅ | 两级去重: bbox-IoU>0.7 对象合并(158→107); part 级 >95% 覆盖吸收(挂名+台账, `anomalies[]` 记录 30 条 subsumed) |
| 门洞被墙实体封死 | ✅ | 9 个基准洞口矩形沿薄轴 ±250mm 贯穿差集 → G11 全洞口中心 ±100mm 净空 |
| Blender 传播缺尺寸 | ✅ | T-B: VIEW_WALL_R3_WEST_PARTITION mesh +100 → 墙实体 xmax 9209→9309 **且** bath2_net_w 2191→2091 |
| bbox-only QA | ✅ | G9 对称差≤2%+500mm²、G10 实体重叠>95% 检测、G11 洞口连通、G12 锚点距墙界≤300mm |
| OUT==BASE 无保护 | ✅ | `sys.exit('BLOCK: OUT == BASE')` 硬阻断 |
| QA 形式化 | ✅ | G3 defpoint2/defpoint3 实测距离 vs 锚点独立复算 |

## 回归测试 (derived/p13_tests/)

| 测试 | 结果 |
|---|---|
| T-A FC 墙移 → 几何+标注 | PASS (14300→14200, xmin 1300→1400) |
| T-B Blender 移 → 几何+标注 | PASS (wall xmax 9209→9309, dim 2191→2091) |
| T-C 提取后篡改 → BLOCK | PASS (rc=1) |
| T-D 缺锚 → BLOCK | PASS (rc=1) |
| T-E 产物新鲜度 + 生产文件不变 | PASS |

## QA qa_report_v04.json

G1-G5,G7-G12 **PASS** | G6 HOLD(38存疑实体+4 UNVERIFIED 对象待裁决) | G13 PARTIAL(无专业CAD编辑器, NOT_RUN) | G14 PARTIAL(A1 图框, 真 VIEWPORT 未建, 物理打印 NOT_RUN)

## 剩余诚实局限

1. **FC 侧仍是顶点壳**: `Shape.Edges` 遍历在 freecadcmd 崩溃, 墙体取 vertex concave hull — 对矩形墙正确, 对带凹口的异形墙欠精确 (记 `cut:FC_SHELL` 待 OCC `Shape.slice()` 替代)
2. **剖切只切 1150/1650 两标高**: 错层上下分区已按对象 zmin 分配, 但同一对象跨层时未做分段剖切
3. **门窗过梁重合**: 窗头/窗下台墙对象已与外墙 part 级吸收去重 — 平面只画一遍, 正确; 但剖面语义未表达
4. **38 存疑 + 4 UNVERIFIED 对象** (W_INT_CLK_N/E/W 衣帽间原隔墙、W_INT_COR_N_STUB) 与 R3 新建隔墙位置接近, 需人工裁决保留/拆除 — 绘图已置 A-UNCERTAIN 冻结
5. 结构安全、封窗合规、现场复尺: 独立 HOLD, 不因技术通过而解除
