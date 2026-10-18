# P1.1 验证报告 — A103 工程数据闭环

日期: 2026-10-18 | 提交对象: A103_CONSTRUCTION_POC_V2

## 端到端闭环 (已建立)
```
FCStd/Blender/DXF 源对象 → extract_anchors_v02.py → geometry_v02.json
  (source_object_id + subelement + sha256 + revision)
→ make_a103_poc_v2.py (生成前 hash 校验)
→ A103_CONSTRUCTION_POC_V2.dxf (原生 DIMENSION + INSERT)
→ qa_a103_poc.py → qa_report_v02.json (程序化, 非手工)
```

## 测试结果

| 测试 | 结果 | 证据 |
|---|---|---|
| change_propagation_test.py | **PASS** | FreeCAD 测试副本 `W_BALC_S.Placement.x += 100` → 重提锚点 → 重生成 → `south_total` 14300→**14200**，实测位移 100mm ±0mm。`derived/prop_test_result.json` |
| stale_source_test.py | **PASS** | 篡改 FCStd 1 字节 → 提取器标记 `STALE_OR_MISSING` → 生成器退出码 1 + BLOCK。`derived/stale_test_result.json` |
| 锚点一致性 ≤1mm | **PASS** | 12 个 DIMENSION `get_measurement` vs 轴投影锚点距 0 超限 |
| 对象级溯源 | **PASS** | 26/26 锚点带 `source_object_id`+`subelement_reference`；门洞 9/9 带 `dxf_handle` |
| 原生标注图层 | **PASS** | 12 DIMENSION 全部在 `A-DIMS`；旧 LINE+TEXT 移入 `A-DIMS-LEGACY`(冻结) |
| 门符号真实宽度 | **PASS** | 9 个门洞 750–1930mm 参数化 INSERT（V1 固定 900 已废除）|
| A-UNCERTAIN 处置 | **HOLD** | 38 个墙体候选实体已冻结并逐条登记于 object_mapping_v02.csv（状态 `UNADJUDICATED_FROZEN`），待人审 |
| CAD 编辑器验证 | **PARTIAL** | FreeCAD importDXF 读取 12 DIMENSION + 10 INSERT + 2 BLOCK 全部识别；Draft 不实例化可编辑标注对象（FreeCAD 限制）。QCAD/LibreCAD 交互选择/编辑 **NOT_RUN** |
| 纸空间/PDF | **PARTIAL** | `A103_CONSTRUCTION_POC_V2.pdf` 真 A1 1:50 矢量输出已生成；物理打印与图纸空间视口 **NOT_RUN** |

## 审阅者上轮问题逐条回应

1. **锚点人工坐标 → 已对象化**：锚点现全部来自 `Shape.Vertexes[i]`（FCStd 语义对象 W_EXT_S/W_BALC_S…）、`bbox.corner`（Blender 对象 R3_COMPLETE_PARTITION_WALLS/KITCHEN_DIVIDER_PIER…）、`footprint.vertex[i]`（STEP_*）、`dxf_handle`（A-DOOR 实体）。0 个 MANUAL_MAPPING_PENDING。
2. **100mm JSON 测试 → 端到端 FreeCAD 传播**：测试修改的是 FreeCAD 文档对象 Placement 并 `doc.save()`，链路上没有手写 JSON。
3. **DIMENSION 图层 → A-DIMS**：12/12。
4. **失效保护 → 实现**：提取器重算全部源 SHA256 vs manifest；失配 `STALE_OR_MISSING` → 生成器 BLOCK 退出码 1。
5. **门窗固定 900 → 参数化**：洞口长度来自基准 DXF `A-DOOR` 实体 handle 实测。
6. **绝对路径 → 相对**：全部脚本 `Path(__file__).parent` 定位。
7. **QA 可复现 → 程序化**：`qa_a103_poc.py` 重跑即重写 `qa_report_v02.json`。

## 附加发现（诚实记录）
- `kitchen_open` 对象级修正：模型残墙 KITCHEN_DIVIDER_PIER (ymax=1430) ↔ 北墙 stub (ymin=4100) → 洞口 **2670mm**，纠正 V1 手工推测 2000mm。
- FreeCAD Draft 导入器识别 DIMENSION 但不生成可编辑标注对象；如需交互编辑验证，需 QCAD/AutoCAD/BricsCAD。
- `RAMP_FUTURE_OPTION` 与 `WAVE_WALL_HANDRAIL_900` 按业主决策 D03 不进入台阶锚点。

## 未决 HOLD（不阻塞本 POC，阻塞施工交付）
- 拆改墙体结构安全核实（业主认可设计≠结构审批）
- 北阳台封窗构造/安装尺寸/合规
- 台阶高差 450mm 现场复尺
- A-UNCERTAIN 38 实体逐条裁决
