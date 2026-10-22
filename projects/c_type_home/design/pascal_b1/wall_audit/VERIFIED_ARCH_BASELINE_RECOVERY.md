# VERIFIED_ARCH_BASELINE_RECOVERY — 只读恢复报告

Phase: QUERY ONLY。未改任何 FCStd / canonical / Pascal / Blender。

## 回答 7 个问题

### 1. 昨天最终正确建筑基线 = 哪一个文件?

```text
cad/freecad_import/世纪欣园FF_PRE_BLENDER_MASTER_V2.FCStd
```

证据链:
- `PRE_B1_SOURCE_RESOLUTION.md`:WINDOW_RESTORED 与 WORKING 物理对象 415/415 全同,
  差异仅为 WORKING 多一个 null-shape `Bspline` 残骸 → CASE A,授权 WINDOW_RESTORED 为 B1 MASTER。
- `PRE_BLENDER_MASTER_V2`(2026-09-29 10:08)是 WINDOW_RESTORED 的 pre-blender 后继;
  dump 证实它**仍含全部 9 个 WINDOW_REF 语义对象**。
- `window_restore_verification_v02.md`:`links_resolve 9/9, drift 0, source untouched, PASS`。

### 2. SHA256

```text
PRE_BLENDER_MASTER_V2.FCStd = 0c30510bc3fe4862d5759c5402146987b6384558a063983b0cab66786de85469
(WINDOW_RESTORED          = 9c2aa9ba9bc8a26be7a3375b4e915c3d68680f20122370ed2c589500498de3e0)
原始 DWG 世纪欣园FF.dwg     = f01a9bb5de964e0362296d12ca510fd7dc99060ddd0e8f8c4b6ab1e63a6fc360
```

### 3. Architecture physical fingerprint 是否完整?

`ARCH_GROUND_TRUTH_FINGERPRINT.json`(438 objects 分类):

```text
GROUND_TRUTH_ARCH    = 384 objects(墙/洞口/阳台/飘窗/错层 linework)
GROUND_TRUTH_OPENING = 10 nodes(9 WINDOW_REF + 1 group container)
HUMAN_DESIGN_GUIDE   = 44 objects(家具/洁具/家电 — 非 ground truth)
```

完整——墙体、门洞几何、窗物理几何、阳台、飘窗凸出轮廓、错层均在。

### 4. 9 个 Window Registry 是否全部存在?

是。MASTER_V2 dump 中 `WINDOW_REF_*` **9/9 links resolved**,union bbox 全部非空:

| ref | links | resolved |
|---|---|---|
| W-LIV-N | 16 | 16 |
| G-LIV-NBALC | 3 | 3 |
| G-GB-BALC | 5 | 5 |
| W-STUDY-NE | 16 | 16 |
| G-DIN-LIV | 8 | 8 |
| W-LBALC-S | 6 | 6 |
| W-KIT-S | 5 | 5 |
| W-SMB-S | 13 | 13 |
| W-MB-S | 13 | 13 |

### 5. 真正 Ground Truth

- 384 个建筑 linework objects(墙/门洞/阳台/飘窗轮廓/错层)
- 9 WINDOW_REF 语义 + `FINAL_WINDOW_REGISTER_95ab90e`
- `FINAL_WALL_REGISTER_V01`(42 active + 9 removed)
- 门语义 `B1_DOOR_SEMANTIC_RESOLUTION` v002
- 业主拆改 `cad_change_registry` + `walls_baseline_246ff12`(原始户型语义)
- 错层 XY zone +350(Z 为 TEMP)
- 橱柜 PDF(`世纪欣园3-1-901_cabinet_plan.pdf`)= 厨房柜体事实源

### 6. 只是 Design Guide

- FreeCAD 里 44 个家具/洁具/家电对象(床、沙发、餐桌、茶台、马桶、3kg洗衣机、冰柜、nas、打印机…)
- `furniture_3d_dimension_register_v01`(高度是标准 blockout 值)
- 一切材质/灯光/颜色

### 7. 当前 Pascal 输入是否偏离 Ground Truth?

`canonical_arch_v2.json` → `pascal-arch-truth-v1` 的输入全部来自 FINAL registers
(它们又是 MASTER_V2 + baseline + owner-change 三源 reconcile 的结果),**没有偏离**。
偏离历史:旧 `b1_model.json` 曾漏墙/压平飘窗/synth host —— 已由 register 重建替代,
旧文件降级为"diff-only",不再作为建筑事实源。

## 产物

```text
ARCH_GROUND_TRUTH_FINGERPRINT.json
DATA_AUTHORITY_REGISTER_V01.md / .json
VERIFIED_ARCH_BASELINE_RECOVERY.md(本文件)
```

STOP — 等待 Human Review。
