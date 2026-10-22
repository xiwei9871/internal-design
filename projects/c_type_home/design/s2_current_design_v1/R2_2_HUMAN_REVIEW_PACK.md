# R2.2 HUMAN REVIEW PACK

Status: `HUMAN_REVIEW`

Layout fidelity: `PASS`

This pack only reorganizes existing R2.2 measurements. It does not recalculate layout, move objects, rotate objects, or propose replacement layouts.

Latest FCStd SHA256: `17340e63f808f7563c64674ad4b43942765044d946b463cb2fb32d373a7817d1`

## 1. OWNER ENSUITE

最新 FCStd 已有次主卫湿区、台盆柜体和马桶对象。当前布局、顺序、朝向和出入口关系均按人工方案保留；本包只汇总测量结果。

| Finding | Actual measured clearance | Target/reference | Status | Conflict amount | Door collision | What would need to change to solve it | Decision |
|---|---:|---:|---|---|---|---|---|
| 次主卫马桶 front clearance | -120.8 | 800 | `CONFLICT` | shortfall 920.8 mm | D-CLK overlaps 次主卫马桶 (45,504.3 mm²) | Would require a human decision on fixture/door/partition relationship; no automatic move. | **HUMAN DECISION REQUIRED** |
| 次主卫湿区 internal footprint | 1.44 | — | `TO_VERIFY` | area is reference only | D-CLK overlaps wet-zone guide (1,309.2 mm²) | Confirm actual internal boundary and door opening before judging usability. | **HUMAN DECISION REQUIRED** |
| Owner ensuite door/opening | — | — | `TO_VERIFY` | not measurable as a named FCStd door | D-CLK is the canonical candidate; swing remains TO_VERIFY | Confirm the real door/opening in field or FreeCAD. | **HUMAN DECISION REQUIRED** |

## 2. MOTHER BEDROOM + MOTHER BATH

母亲主卧床、衣柜、床头柜和主卫三件套均来自最新 FCStd。母亲卧室与主卫关系保持不变。

| Finding | Actual measured clearance | Target/reference | Status | Conflict amount | Door collision | What would need to change to solve it | Decision |
|---|---:|---:|---|---|---|---|---|
| 主卧床 side clearance | 173.6 | 600 | `CONFLICT` | shortfall 426.4 mm | No direct door overlap in this metric | Human decision required if assisted-side clearance is to be increased. | **HUMAN DECISION REQUIRED** |
| 主卧床 foot clearance | 1387.9 | 600 | `PASS` | none | none | none | **NO CHANGE REQUIRED** |
| 主卫马桶 front clearance | -71.1 | 800 | `CONFLICT` | shortfall 871.1 mm | D-BATHM low clearance to 主卫洗手盆和柜体: 38.5 mm | Human decision required; do not move fixture automatically. | **HUMAN DECISION REQUIRED** |
| 主卫湿区 footprint | 1.57 | — | `TO_VERIFY` | area reference only | door/fixture usability requires field check | Verify wet/dry and assisted-use clearances. | **HUMAN DECISION REQUIRED** |

## 3. GUEST BATH

客卫边界和最新 FCStd 的客卫湿区、马桶、台盆柜体保持不变。3kg 小洗衣机在最新 FCStd 中没有命名对象。

| Finding | Actual measured clearance | Target/reference | Status | Conflict amount | Door collision | What would need to change to solve it | Decision |
|---|---:|---:|---|---|---|---|---|
| 客卫马桶 front clearance | 1044.0 | 800 | `PASS` | none | none | none | **NO CHANGE REQUIRED** |
| 客卫（湿区） footprint | 1.64 | — | `TO_VERIFY` | area reference only | door swing remains part of audit | Verify shower/wet-zone usable arrangement without enlarging boundary. | **HUMAN DECISION REQUIRED** |
| 3kg small washer | — | 600 | `TO_VERIFY` | not available: no named latest-FCStd object | no washer-specific door conflict measured | Human decision required: add/confirm its exact position in FreeCAD. | **HUMAN DECISION REQUIRED** |

## 4. MIDDLE GUEST ROOM + OWNER BEDROOM

中间客房与 owner bedroom 的最新人工对象均按 FCStd 保持；本节记录床侧/床尾和既有门洞关系。

| Finding | Actual measured clearance | Target/reference | Status | Conflict amount | Door collision | What would need to change to solve it | Decision |
|---|---:|---:|---|---|---|---|---|
| 次卧小床1.2 side clearance | 215.4 | 600 | `CONFLICT` | shortfall 384.6 mm | D-GBATH overlap 57,256.8 mm²; D-GBED overlap 110,275.0 mm² | Human decision required; no bed rotation or relocation applied. | **HUMAN DECISION REQUIRED** |
| 次卧小床1.2 foot clearance | 1437.8 | 600 | `PASS` | none | none | none | **NO CHANGE REQUIRED** |
| 次主卧床 side clearance | 233.4 | 600 | `CONFLICT` | shortfall 366.6 mm | none in direct metric | Human decision required if owner bed access is to be widened. | **HUMAN DECISION REQUIRED** |
| 次主卧床 foot clearance | 1412.8 | 600 | `PASS` | none | none | none | **NO CHANGE REQUIRED** |
| 次卧衣柜 / balcony door | — | 100 | `CONFLICT` | 0 mm minimum distance; overlap 22,014.6 mm² | G-GB-BALC overlap 次卧衣柜 | Human decision required; do not move wardrobe automatically. | **HUMAN DECISION REQUIRED** |

## 5. STUDY

书房按最新 FCStd 的床背板+窄书桌、书柜、茶台、椅、条凳和凳子读取。正式办公设备没有单独命名对象。

| Finding | Actual measured clearance | Target/reference | Status | Conflict amount | Door collision | What would need to change to solve it | Decision |
|---|---:|---:|---|---|---|---|---|
| Formal workstation / chair pull-back | — | 900 | `TO_VERIFY` | no named printer/NAS or explicit operating-zone object | no dedicated door collision measured | Human decision required: verify workstation operation, dual monitors, printer and NAS access. | **HUMAN DECISION REQUIRED** |
| Bookcase / tea-table topology | — | — | `PASS` | no numerical target in source report | none directly reported | No change required for topology; usability still needs human review. | **NO CHANGE REQUIRED** |
| Study printer/NAS provision | — | — | `TO_VERIFY` | missing named object in latest FCStd | none | Human decision required: add/confirm only if desired in FreeCAD. | **HUMAN DECISION REQUIRED** |

## 6. DINING + NORTH BALCONY / LAUNDRY

餐桌、三把命名餐椅和未命名辅助餐椅按最新 FCStd 读取。北阳台洗衣机+烘干机叠放对象已存在；本包只核验，不改变并排/叠放关系。

| Finding | Actual measured clearance | Target/reference | Status | Conflict amount | Door collision | What would need to change to solve it | Decision |
|---|---:|---:|---|---|---|---|---|
| 餐椅 table gap | 121.1 | 150 | `CONFLICT` | shortfall 28.9 mm | none direct; G-DIN-LIV / 鞋柜 overlap 4,490.6 mm² | Human decision required; do not shift table/chairs automatically. | **HUMAN DECISION REQUIRED** |
| 餐椅003 table gap | 121.1 | 150 | `CONFLICT` | shortfall 28.9 mm | none direct | Human decision required. | **HUMAN DECISION REQUIRED** |
| 餐椅004 table gap | 198.5 | 150 | `PASS` | none | none | none | **NO CHANGE REQUIRED** |
| 洗衣机+烘干机（叠放） | — | — | `TO_VERIFY` | latest object present; generic/SKU envelope not measured here | glass-door/service relationship remains TO_VERIFY | Human decision required for SKU, service, ventilation and balcony conditions. | **HUMAN DECISION REQUIRED** |
| Main laundry service | — | — | `TO_VERIFY` | drainage/power/SKU not verified | none | Human decision required; no equipment movement applied. | **HUMAN DECISION REQUIRED** |

## Critical issue map

Numbers correspond to `R2_2_CRITICAL_ISSUES.png`. No alternative layout is shown.

| # | Object / source | Existing status |
|---:|---|---|
| 1 | 次卧小床1.2 | `CONFLICT` |
| 2 | 次主卧床 | `CONFLICT` |
| 3 | 主卧床 | `CONFLICT` |
| 4 | 主卫马桶 | `CONFLICT` |
| 5 | 次主卫马桶 | `CONFLICT` |
| 6 | 餐椅 | `CONFLICT` |
| 7 | 餐椅003 | `CONFLICT` |
| 8 | 次主卫湿区 | `TO_VERIFY` |
| 9 | 主卫湿区 | `TO_VERIFY` |
| 10 | 客卫（湿区） | `TO_VERIFY` |
| 11 | 鞋柜 | `CLEARANCE_LOW` |
| 12 | 斜坡（轮椅用 | `CLEARANCE_LOW` |
| 13 | 主卧衣柜 | `CLEARANCE_LOW` |
| 14 | 主卫洗手盆和柜体 | `CLEARANCE_LOW` |
| 15 | 次主卫湿区 | `CONFLICT` |
| 16 | 次主卧床头占位 | `CLEARANCE_LOW` |
| 17 | 主卧电视柜 | `CONFLICT` |
| 18 | 次卧衣柜 | `CONFLICT` |
| 19 | 鞋柜 | `CONFLICT` |
| 20 | 斜坡（轮椅用 | `CONFLICT` |
| 21 | 洗衣机+烘干机（叠放） | `TO_VERIFY` |

## Stop gate

`LATEST_HUMAN_GUIDE = HUMAN_REVIEW`
`S2_LAYOUT = HOLD`
`Blender = HOLD`
`formal_cad_allowed = false`

No furniture position, orientation, room assignment or wall anchor was changed in this pack.
