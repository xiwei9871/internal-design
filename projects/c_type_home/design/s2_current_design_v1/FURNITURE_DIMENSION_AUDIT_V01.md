# FURNITURE DIMENSION AUDIT V01

Status: `FURNITURE_DIMENSION_GATE = HUMAN_REVIEW`

Source mtime: `1790600038.7061121`
Source SHA256: `ff80a059b76f495390b69c1346e7d77fd34529e5598919101aec3aff0b6ceaa5`
FreeCAD objects: 427; named objects audited: 46

No FCStd object was moved, rotated, resized, replaced or redesigned.

## Classification legend

- `OK`: plausible generic footprint.
- `MINOR_ADJUSTMENT`: small reference mismatch; human may update FreeCAD later.
- `RECOMMEND_RESIZE`: visible footprint is materially unlike the reference; recommendation only.
- `CUSTOM_FURNITURE_PLAUSIBLE`: custom/placeholder geometry can be valid; field or joinery review required.
- `SKU_TO_VERIFY`: generic envelope is insufficient for a final product.
- `USER_CONFIRMED_DO_NOT_CHANGE`: user-confirmed bed dimensions are preserved.

## Per-object audit

| Object | Room | Category | Current W×D | Reference W | Reference D | Recommended W×D | Classification | Source | Reason |
|---|---|---|---:|---:|---:|---:|---|---|---|
| 双人位沙发 | living | seating | 1942×747 | [1500, 1900] | [850, 1000] | 1800×850 | `MINOR_ADJUSTMENT` | `ASSET_LIBRARY` | Depth is slightly below the compact reference; no automatic change. |
| 角几 | living | side_table | 649×649 | [400, 500] | [400, 500] | 450×450 | `MINOR_ADJUSTMENT` | `GENERIC_REFERENCE` | Current side table is larger than the common compact reference. |
| 茶几 | living | coffee_table | 648×1469 | [450, 600] | [800, 1000] | 500×900 | `RECOMMEND_RESIZE` | `GENERIC_REFERENCE` | Current long axis is plausible as a coffee table only after a depth/length calibration; no automatic rotation. |
| lounge | living | seating | 2216×623 | [800, 1000] | [1500, 1900] | 1700×900 | `RECOMMEND_RESIZE` | `MARKET_REFERENCE` | Current footprint is a long shallow guide; chaise reference should be elongated with a more usable depth. Preserve long-axis direction. |
| 电视柜（或者悬浮电视墙） | living | media_edge | 299×2889 | — | — | — | `SKU_TO_VERIFY` | `TO_VERIFY` | Media edge intent is ambiguous (cabinet or suspended media wall); no generic resize should be applied. |
| 客卫（湿区） | guest_bath | shower_zone | 1644×996 | [900, 1000] | [900, 1200] | 1643.75×996.15625 | `SKU_TO_VERIFY` | `TO_VERIFY` | Wet-zone guide is a region, not a final shower product footprint. |
| 客卫马桶 | guest_bath | wc | 747×324 | [650, 750] | [380, 420] | 700×400 | `MINOR_ADJUSTMENT` | `GENERIC_REFERENCE` | Current footprint is plausible but shallow; confirm actual SKU and orientation. |
| 次主卧床头占位 | owner_bedroom | bed | 199×2640 | — | — | 199.25×2639.875 | `TO_VERIFY` | `TO_VERIFY` | No reliable category reference without inventing a product assumption. |
| 次主卧床 | owner_bedroom | bed | 2100×1500 | [1500, 1500] | [2100, 2100] | 2100.0×1500.0 | `USER_CONFIRMED_DO_NOT_CHANGE` | `USER_CONFIRMED` | User-confirmed 1500x2100 owner bed; current axes preserve the locked guide orientation. |
| 主卧床 | mother_bedroom | bed | 2100×1500 | [1500, 1500] | [2100, 2100] | 2100.0×1500.0 | `USER_CONFIRMED_DO_NOT_CHANGE` | `USER_CONFIRMED` | User-confirmed 1500x2100 mother bed; current axes preserve the locked guide orientation. |
| 主卧床头柜占位 | mother_bedroom | bed | 150×2500 | [450, 500] | [400, 450] | 450×450 | `RECOMMEND_RESIZE` | `GENERIC_REFERENCE` | This is a placeholder guide, not a literal nightstand footprint. |
| 主卧衣柜 | mother_bedroom | wardrobe | 2100×600 | [550, 650] | [550, 650] | 2100.0×600 | `OK` | `MARKET_REFERENCE` | Wardrobe depth is assessed against the 600 mm generic reference while preserving wall/axis intent. |
| 次卧小床1.2 | middle_guest_room | bed | 1800×1200 | [1200, 1200] | [1800, 1800] | 1800.0×1200.0 | `USER_CONFIRMED_DO_NOT_CHANGE` | `USER_CONFIRMED` | User-confirmed 1200x1800 guest bed; current axes preserve the locked guide orientation. |
| 床背板+窄书桌占位 | study | bed | 199×2839 | [1600, 1800] | [700, 800] | 1700×800 | `RECOMMEND_RESIZE` | `MARKET_REFERENCE` | Current object is a narrow backboard/desk placeholder and does not represent a dual-monitor workstation footprint. |
| 次主卧衣柜 | owner_bedroom | wardrobe | 1500×600 | [550, 650] | [550, 650] | 1500.0×600 | `OK` | `MARKET_REFERENCE` | Wardrobe depth is assessed against the 600 mm generic reference while preserving wall/axis intent. |
| 主卧电视柜 | living | media_edge | 500×2000 | — | — | — | `SKU_TO_VERIFY` | `TO_VERIFY` | Media edge intent is ambiguous (cabinet or suspended media wall); no generic resize should be applied. |
| 次主卧电视柜 | living | media_edge | 500×2000 | — | — | — | `SKU_TO_VERIFY` | `TO_VERIFY` | Media edge intent is ambiguous (cabinet or suspended media wall); no generic resize should be applied. |
| 书柜 | study | bookcase | 450×4200 | [300, 350] | [300, 350] | 450.0×4200.0 | `CUSTOM_FURNITURE_PLAUSIBLE` | `GENERIC_REFERENCE` | Custom full-height/low bookcase guide; depth and joinery require furniture design/SKU review. |
| 矮书柜 | study | bookcase | 1600×450 | [300, 350] | [300, 350] | 1600.0×450.0 | `CUSTOM_FURNITURE_PLAUSIBLE` | `GENERIC_REFERENCE` | Custom full-height/low bookcase guide; depth and joinery require furniture design/SKU review. |
| 茶台 | study | tea_table | 800×2200 | [600, 900] | [800, 1500] | 800×1200 | `RECOMMEND_RESIZE` | `GENERIC_REFERENCE` | Current 2200 mm long tea-table guide is unusually large for a tea surface; preserve guide axis. |
| 主人椅 | study | chair_bench_stool | 400×400 | [450, 550] | [500, 600] | 500×550 | `MINOR_ADJUSTMENT` | `GENERIC_REFERENCE` | Current 400 mm circular placeholder is below a common seated footprint. |
| 条凳 | study | chair_bench_stool | 300×1600 | [350, 500] | [1200, 1800] | 400×1500 | `MINOR_ADJUSTMENT` | `GENERIC_REFERENCE` | Bench depth is slightly below a comfortable reference; preserve long axis. |
| 凳子 | study | chair_bench_stool | 400×400 | [450, 550] | [500, 600] | 500×550 | `MINOR_ADJUSTMENT` | `GENERIC_REFERENCE` | Current 400 mm circular placeholder is below a common seated footprint. |
| 次卧凳子 | middle_guest_room | chair_bench_stool | 400×400 | [450, 550] | [500, 600] | 500×550 | `MINOR_ADJUSTMENT` | `GENERIC_REFERENCE` | Current 400 mm circular placeholder is below a common seated footprint. |
| 餐椅 | dining | dining_chair | 400×400 | [450, 550] | [500, 600] | 500×550 | `MINOR_ADJUSTMENT` | `GENERIC_REFERENCE` | Current circular guide is a compact placeholder; chair product envelope is larger. |
| 餐椅003 | dining | dining_chair | 400×400 | [450, 550] | [500, 600] | 500×550 | `MINOR_ADJUSTMENT` | `GENERIC_REFERENCE` | Current circular guide is a compact placeholder; chair product envelope is larger. |
| 餐桌 | dining | dining_table | 1600×700 | [1400, 1600] | [750, 850] | 1500×800 | `MINOR_ADJUSTMENT` | `USER_CONFIRMED` | Current table is slightly shallow versus the compact reference; preserve long-axis direction. |
| 餐椅004 | dining | dining_chair | 400×400 | [450, 550] | [500, 600] | 500×550 | `MINOR_ADJUSTMENT` | `GENERIC_REFERENCE` | Current circular guide is a compact placeholder; chair product envelope is larger. |
| 现有橱柜 | kitchen | cabinet | 500×1500 | — | — | 500.0×1500.0 | `CUSTOM_FURNITURE_PLAUSIBLE` | `USER_CONFIRMED` | Existing/custom fixed item; field/SKU verification required. |
| 三人位沙发 | living | seating | 847×3163 | [2000, 2400] | [850, 1000] | 2200×900 | `RECOMMEND_RESIZE` | `MARKET_REFERENCE` | Current guide aspect is much longer/narrower than a normal 3-seat sofa; preserve orientation, resize only after human decision. |
| 客卫洗手盆柜体 | guest_bath | vanity | 600×1200 | [600, 900] | [500, 550] | 600.0×1200.0 | `SKU_TO_VERIFY` | `TO_VERIFY` | Guide appears composite or axis-swapped; verify actual cabinet product before Blender. |
| 鞋柜 | entry | shoe_storage | 300×722 | — | — | 300.0×722.25 | `CUSTOM_FURNITURE_PLAUSIBLE` | `USER_CONFIRMED` | Existing/custom fixed item; field/SKU verification required. |
| 橱柜 | kitchen | cabinet | 1200×500 | — | — | 1200.0×500.0 | `CUSTOM_FURNITURE_PLAUSIBLE` | `USER_CONFIRMED` | Existing/custom fixed item; field/SKU verification required. |
| 主卫湿区 | mother_bath | shower_zone | 1000×1569 | [900, 1000] | [900, 1200] | 1000.0×1569.0 | `SKU_TO_VERIFY` | `TO_VERIFY` | Wet-zone guide is a region, not a final shower product footprint. |
| 主卫马桶 | mother_bath | wc | 500×650 | [380, 420] | [650, 750] | 500.0×650.0 | `SKU_TO_VERIFY` | `TO_VERIFY` | Axis-swapped WC guide is plausible but fixture orientation/SKU must be verified. |
| 主卫洗手盆和柜体 | mother_bath | vanity | 1200×500 | [600, 1200] | [500, 550] | 1200.0×500 | `OK` | `GENERIC_REFERENCE` | Vanity depth is in the normal range; width is room-specific. |
| 次主卫湿区 | owner_ensuite | shower_zone | 900×1600 | [900, 1000] | [900, 1200] | 900.0×1600.0 | `SKU_TO_VERIFY` | `TO_VERIFY` | Wet-zone guide is a region, not a final shower product footprint. |
| 次主卫台盆和柜体 | owner_ensuite | vanity | 1000×500 | [600, 1200] | [500, 550] | 1000.0×500 | `OK` | `GENERIC_REFERENCE` | Vanity depth is in the normal range; width is room-specific. |
| 次主卫马桶 | owner_ensuite | wc | 500×600 | [380, 420] | [650, 750] | 500.0×600.0 | `SKU_TO_VERIFY` | `TO_VERIFY` | Axis-swapped WC guide is plausible but fixture orientation/SKU must be verified. |
| 冰柜 | north_balcony_laundry | freezer | 1200×600 | [600, 1000] | [600, 750] | 800×650 | `SKU_TO_VERIFY` | `TO_VERIFY` | Freezer footprint is market-plausible but needs selected SKU, door and ventilation check. |
| 洗衣机+烘干机（叠放） | north_balcony_laundry | washer_dryer | 600×600 | [600, 600] | [600, 650] | 600×650 | `SKU_TO_VERIFY` | `TO_VERIFY` | Current stacked arrangement is human-locked; generic appliance depth/SKU and service clearances remain to verify. |
| 3kg洗衣机 | north_balcony_laundry | washer_dryer | 450×450 | [450, 600] | [450, 650] | 450.0×450.0 | `SKU_TO_VERIFY` | `TO_VERIFY` | Small-washer guide is present; final product and service clearances remain to verify. |
| 斜坡给未来轮椅使用预留 | transition | ramp | 2100×1100 | — | — | 2100.0×1100.0 | `SKU_TO_VERIFY` | `TO_VERIFY` | Assisted route guide; slope, landings and code status remain field verification. |
| 打印机 | study | equipment | 400×400 | [300, 600] | [300, 600] | 400.0×400.0 | `OK` | `GENERIC_REFERENCE` | Current equipment placeholder is a plausible generic envelope; final model is TO_VERIFY. |
| nas | study | equipment | 400×400 | [300, 600] | [300, 600] | 400.0×400.0 | `OK` | `GENERIC_REFERENCE` | Current equipment placeholder is a plausible generic envelope; final model is TO_VERIFY. |
| 次卧衣柜 | middle_guest_room | wardrobe | 500×2000 | [550, 650] | [550, 650] | 2000×600 | `MINOR_ADJUSTMENT` | `MARKET_REFERENCE` | Wardrobe depth is assessed against the 600 mm generic reference while preserving wall/axis intent. |

## Asset library

The existing normalized library is reference-only. It is not inserted into or substituted for the human FCStd objects.

| ID | Category | Target bbox | File |
|---|---|---:|---|
| BED_1800x2100_PLAN | bed | [1800, 2100] | normalized/BED_1800x2100_PLAN.dxf |
| BED_1500x2000_PLAN | bed | [1500, 2000] | normalized/BED_1500x2000_PLAN.dxf |
| BED_900x2000_PLAN | bed | [900, 2000] | normalized/BED_900x2000_PLAN.dxf |
| SOFA_3S_2200x900_PLAN | sofa | [2200, 900] | normalized/SOFA_3S_2200x900_PLAN.dxf |
| SOFA_2S_1800x850_PLAN | sofa | [1800, 850] | normalized/SOFA_2S_1800x850_PLAN.dxf |
| LOUNGE_CHAIR_900x900_PLAN | lounge_chair | [900, 900] | normalized/LOUNGE_CHAIR_900x900_PLAN.dxf |
| DESK_1700x800_PLAN | desk | [1700, 800] | normalized/DESK_1700x800_PLAN.dxf |
| DINING_TABLE_1500x600_PLAN | dining_table | [1500, 600] | normalized/DINING_TABLE_1500x600_PLAN.dxf |
| DINING_CHAIR_450x500_PLAN | dining_chair | [450, 500] | normalized/DINING_CHAIR_450x500_PLAN.dxf |
| WC_STD_450x700_PLAN | wc | [450, 700] | normalized/WC_STD_450x700_PLAN.dxf |
| VANITY_600x500_PLAN | vanity | [600, 500] | normalized/VANITY_600x500_PLAN.dxf |
| VANITY_900x500_PLAN | vanity | [900, 500] | normalized/VANITY_900x500_PLAN.dxf |
| SHOWER_900x1200_PLAN | shower | [900, 1200] | normalized/SHOWER_900x1200_PLAN.dxf |
| WARDROBE_D600_PLAN | wardrobe | [965.1999999999999, 600.0] | normalized/WARDROBE_D600_PLAN.dxf |
| WASHER_600x650_PLAN | washer | [600, 650] | normalized/WASHER_600x650_PLAN.dxf |
| DRYER_600x650_PLAN | dryer | [600, 650] | normalized/DRYER_600x650_PLAN.dxf |
