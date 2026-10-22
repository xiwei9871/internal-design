# S2 GUIDE BASELINE V1 — Fidelity Report

Status: `DRAFT_HUMAN_REVIEW`
Fidelity gate: `PASS`

## Policy

FCStd named guide objects are `HUMAN_LAYOUT_INTENT = LOCKED`. This baseline replays their exact task-coordinate bbox and orientation. It does not normalize dimensions, rotate objects, move furniture, or re-plan rooms.

## Room-role authority

- Middle guest room: `次卧小床1.2` + `次卧衣柜` + `次卧凳子`.
- Study / backup sleep: `床背板+窄书桌占位` + `书柜` + `书柜001` + `茶台` + `主人椅` + `条凳` + `凳子`.
- Historical geometry room labels are polygon references only; they do not override the named FreeCAD guide.

## Gate checks

- Named guide objects checked: 38
- Maximum displacement: 0.0 mm
- Maximum rotation delta: 0.0°
- 90° orientation drift: none in the replay
- Cross-room relayout: none in the replay
- Wall relationship: preserved by exact guide bbox replay

## Per-object checks

| object | semantic | room role | guide orientation | reconstructed orientation | displacement | rotation delta | result |
|---|---|---|---|---|---:|---:|---|
| 双人位沙发 | `SOFA_2S` | `living` | `LONG_AXIS_X` | `LONG_AXIS_X` | 0.0 | 0.0° | `PASS` |
| 角几 | `SIDE_TABLE` | `living` | `SQUARE` | `SQUARE` | 0.0 | 0.0° | `PASS` |
| 茶几 | `COFFEE_TABLE_OPTIONAL` | `living` | `LONG_AXIS_Y` | `LONG_AXIS_Y` | 0.0 | 0.0° | `PASS` |
| lounge | `LOUNGE_CHAIR` | `living` | `LONG_AXIS_X` | `LONG_AXIS_X` | 0.0 | 0.0° | `PASS` |
| 电视柜（或者悬浮电视墙） | `MEDIA_EDGE` | `living` | `LONG_AXIS_Y` | `LONG_AXIS_Y` | 0.0 | 0.0° | `PASS` |
| 斜坡（轮椅用 | `ACCESSIBILITY_RAMP` | `transition` | `LONG_AXIS_X` | `LONG_AXIS_X` | 0.0 | 0.0° | `PASS` |
| 客卫（湿区） | `GUEST_BATH_WET_ZONE` | `guest_bath` | `LONG_AXIS_X` | `LONG_AXIS_X` | 0.0 | 0.0° | `PASS` |
| 客卫马桶 | `WC_GUEST` | `guest_bath` | `LONG_AXIS_X` | `LONG_AXIS_X` | 0.0 | 0.0° | `PASS` |
| 次主卧床头占位 | `NIGHTSTAND_OWNER` | `owner_bedroom` | `LONG_AXIS_Y` | `LONG_AXIS_Y` | 0.0 | 0.0° | `PASS` |
| 次主卧床 | `BED_OWNER` | `owner_bedroom` | `LONG_AXIS_X` | `LONG_AXIS_X` | 0.0 | 0.0° | `PASS` |
| 主卧床 | `BED_MOTHER` | `mother_bedroom` | `LONG_AXIS_X` | `LONG_AXIS_X` | 0.0 | 0.0° | `PASS` |
| 主卧床头柜占位 | `NIGHTSTAND_MOTHER` | `mother_bedroom` | `LONG_AXIS_Y` | `LONG_AXIS_Y` | 0.0 | 0.0° | `PASS` |
| 主卧衣柜 | `WARDROBE_MOTHER` | `mother_bedroom` | `LONG_AXIS_X` | `LONG_AXIS_X` | 0.0 | 0.0° | `PASS` |
| 次卧小床1.2 | `BED_GUEST_1200` | `guest_room` | `LONG_AXIS_X` | `LONG_AXIS_X` | 0.0 | 0.0° | `PASS` |
| 床背板+窄书桌占位 | `STUDY_DESK_BACKBOARD` | `study` | `LONG_AXIS_Y` | `LONG_AXIS_Y` | 0.0 | 0.0° | `PASS` |
| 次卧衣柜 | `WARDROBE_GUEST` | `guest_room` | `LONG_AXIS_Y` | `LONG_AXIS_Y` | 0.0 | 0.0° | `PASS` |
| 次主卧衣柜 | `WARDROBE_OWNER` | `owner_bedroom` | `LONG_AXIS_X` | `LONG_AXIS_X` | 0.0 | 0.0° | `PASS` |
| 主卧电视柜 | `MEDIA_EDGE_MOTHER` | `mother_bedroom` | `LONG_AXIS_Y` | `LONG_AXIS_Y` | 0.0 | 0.0° | `PASS` |
| 次主卧电视柜 | `MEDIA_EDGE_OWNER` | `owner_bedroom` | `LONG_AXIS_Y` | `LONG_AXIS_Y` | 0.0 | 0.0° | `PASS` |
| 书柜 | `BOOKCASE_STUDY_TALL` | `study` | `LONG_AXIS_Y` | `LONG_AXIS_Y` | 0.0 | 0.0° | `PASS` |
| 书柜001 | `BOOKCASE_STUDY_LOW` | `study` | `LONG_AXIS_X` | `LONG_AXIS_X` | 0.0 | 0.0° | `PASS` |
| 茶台 | `TEA_TABLE_STUDY` | `study` | `LONG_AXIS_Y` | `LONG_AXIS_Y` | 0.0 | 0.0° | `PASS` |
| 主人椅 | `STUDY_CHAIR` | `study` | `SQUARE` | `SQUARE` | 0.0 | 0.0° | `PASS` |
| 条凳 | `STUDY_BENCH` | `study` | `LONG_AXIS_Y` | `LONG_AXIS_Y` | 0.0 | 0.0° | `PASS` |
| 凳子 | `STUDY_STOOL` | `study` | `SQUARE` | `SQUARE` | 0.0 | 0.0° | `PASS` |
| 次卧凳子 | `GUEST_STOOL` | `guest_room` | `SQUARE` | `SQUARE` | 0.0 | 0.0° | `PASS` |
| 餐椅 | `DINING_CHAIR_1` | `dining` | `SQUARE` | `SQUARE` | 0.0 | 0.0° | `PASS` |
| 餐椅003 | `DINING_CHAIR_2` | `dining` | `SQUARE` | `SQUARE` | 0.0 | 0.0° | `PASS` |
| 餐桌 | `DINING_TABLE` | `dining` | `LONG_AXIS_X` | `LONG_AXIS_X` | 0.0 | 0.0° | `PASS` |
| 餐椅004 | `DINING_CHAIR_4` | `dining` | `SQUARE` | `SQUARE` | 0.0 | 0.0° | `PASS` |
| 现有橱柜 | `KITCHEN_KEEP` | `kitchen` | `LONG_AXIS_Y` | `LONG_AXIS_Y` | 0.0 | 0.0° | `PASS` |
| 三人位沙发 | `SOFA_3S` | `living` | `LONG_AXIS_Y` | `LONG_AXIS_Y` | 0.0 | 0.0° | `PASS` |
| 客卫洗手盆柜体 | `VANITY_GUEST` | `guest_bath` | `LONG_AXIS_Y` | `LONG_AXIS_Y` | 0.0 | 0.0° | `PASS` |
| 鞋柜 | `ENTRY_SHOE_STORAGE` | `entry` | `LONG_AXIS_Y` | `LONG_AXIS_Y` | 0.0 | 0.0° | `PASS` |
| 橱柜 | `KITCHEN_AUX_STORAGE` | `kitchen` | `LONG_AXIS_X` | `LONG_AXIS_X` | 0.0 | 0.0° | `PASS` |
| 主卫湿区 | `BATH_MOTHER_WET_ZONE` | `mother_bathroom` | `LONG_AXIS_Y` | `LONG_AXIS_Y` | 0.0 | 0.0° | `PASS` |
| 主卫马桶 | `WC_MOTHER` | `mother_bathroom` | `LONG_AXIS_Y` | `LONG_AXIS_Y` | 0.0 | 0.0° | `PASS` |
| 主卫洗手盆和柜体 | `VANITY_MOTHER` | `mother_bathroom` | `LONG_AXIS_X` | `LONG_AXIS_X` | 0.0 | 0.0° | `PASS` |

## Stop gate

This baseline stops for human review. Only after baseline approval may a copy be used for dimension normalization. Any nonzero rotation delta requires explicit human approval.

The previous normalized run is preserved under `S2_CURRENT_DESIGN_V1_REJECTED*` because it failed `HUMAN_GUIDE_LAYOUT_DRIFT`.
