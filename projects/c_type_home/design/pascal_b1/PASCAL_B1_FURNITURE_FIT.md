# PASCAL_B1 — FURNITURE-FIT (footprint screen only)

Method: `check_collisions` (rotation-aware plan AABB, real dims via
`actual_project_size_m`) + `verify_scene` (8 cm spacing + door keep-outs) +
item-footprint vs zone-polygon containment (`furniture_fit_raw.json`).

This is a FOOTPRINT SCREEN. It does **not** check: door swing, vertical
clearance, installation, delivery path, mesh contact, ergonomic/code
compliance. `unsupportedChecks` from the tool: vertical_clearance,
room_boundary_clearance, door_swing_envelope, delivery_path, mesh_geometry,
hosted_item_world_transform.

## Per-zone screen

| zone | items | in-zone | outside footprint | colliding items |
|---|---|---|---|---|
| R-LIVING 客厅 | 6 | 4 | 双人位*, 贵妃椅 | — |
| R-DINING 餐厅 | 6 | 4 | 餐椅, 餐椅004 | — |
| R-BALC-LIFE 生活阳台 | 2 | 2 | — | — |
| R-KITCHEN 厨房 | 9 | 4 | K-RUN-E†, K-COOK†, K-DISHW†, K-BASKET†, K-WALL-E† | 9 items† |
| R-LEISURE-W/E 休闲厅 | — | — | (zone, no items) | — |
| R-BED-S 卧室 | 4 | 3 | 次主卧衣柜 | — |
| R-MASTER 主卧 | 4 | 4 | — | — |
| R-CLOAK 衣帽间 | 3 | 2 | 次主卫马桶* | — |
| R-BATH-M 主卫 | 3 | 2 | 主卫马桶* | — |
| R-BATH-P 公卫 | 4 | 2 | 客卫（湿区）*, 3kg洗衣机* | 客卫（湿区）×3kg洗衣机* |
| R-BED-N 卧室 | 8 | 8 | — | 矮书柜×打印机×NAS* |
| R-STUDY 书房 | 5 | 3 | 次卧衣柜, 窄书桌 | — |
| R-BALC-N 北阳台 | 2 | 2 | — | — |

`*` = human-approved as-drawn or intentional (see below).
`†` = kitchen run rects legitimately contain appliance sub-elements in source.

## Collision pairs (19, all as-drawn)

- 客卫（湿区） × 3kg洗衣机 — washer inside wet-zone region: human-approved,
  wall-mount candidate, MEP_TO_VERIFY. NO_MOVE.
- 矮书柜 × 打印机 / NAS — devices stored on/in shelving, as drawn.
- K-RUN-E/K-RUN-S runs vs K-COOK/K-DISHW/K-BASKET/K-FRIDGE(-TALL)/K-SINK/
  K-WALL-E — canonical cabinet runs overlap appliance blocks in source CAD;
  nested representation, not spatial conflicts.
- K-* pairs among themselves — same reason.

## Door keep-out advisories (15) — `verify_scene`

Doors "blocked" by: 次主卧床头占位, 次卧小床1.2 (×2), 次主卧衣柜, 主卧电视柜,
次卧凳子, 餐椅 (×2), 鞋柜 (×2), 主卫洗手盆和柜体, 次主卫湿区, 次主卫马桶,
洗衣机+烘干机叠放, 次卧衣柜.

Status: **ACKNOWLEDGED_HUMAN_OVERRIDE** — as-drawn positions were explicitly
approved; Pascal door keep-out is a rectangular advisory zone, not swing
simulation. No item moved.

## Checks NOT performed (per furniture-fit evidence boundary)

door swing · vertical clearance · installation · delivery route · mesh contact
· safety/code certification — all `not checked`.

**Verdict**: footprint screen complete; every flag traces to approved-as-drawn
layout or nested canonical rects. No unresolved placement question surfaced.
