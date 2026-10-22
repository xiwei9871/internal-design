# FURNITURE_3D_DIMENSION_REGISTER_V01

Gate: `PRE_3D_FURNITURE_DIMENSION_GATE`. Units mm. XY from MASTER_V2 (unchanged). Heights from the B1 default table — **no furniture may use floor/room/wall height as fallback**; missing -> TO_VERIFY.

Split level: `upper` zones sit +350 (stairs.delta_mm). Wall-mounted candidates: `base_z = TO_VERIFY`.

Category rules: real `NIGHTSTAND` (if one ever appears) = ~500 generic height — NEVER 2200; `STUDY_ARMCHAIR`/`OWNER_CHAIR` is not `DINING_CHAIR` (seat≈430, overall 850); `MEDIA_CABINET` B1 = floor-standing h480, floating treatment TO_VERIFY in B2.

| label | type | L×D×H | base_z | source | notes |
|---|---|---|---|---|---|
| 电视柜（或者悬浮电视墙） | MEDIA_CABINET | 299×2889×480 | 0 | STANDARD_BLOCKOUT | B1_REPRESENTATION=FLOOR_STANDING; FINAL_MEDIA_SOLUTION=TO_VERIFY; FLOATING_MOUNT_Z=TO_VERIFY; DO NOT use room height |
| 客卫（湿区） | SHOWER_ZONE | 1644×813×2000 | 350 | HUMAN_CONFIRMED | not solid furniture — glass screen blockout only |
| 客卫马桶 | WC | 747×324×780 | 350 | HUMAN_CONFIRMED | overall blockout height |
| 次主卧床头占位 | HEADBOARD | 199×2640×1050 | 350 | STANDARD_BLOCKOUT | separate block behind bed |
| 次主卧床 | BED_BASE | 2100×1500×550 | 350 | HUMAN_CONFIRMED | mattress/base envelope only; separate HEADBOARD block |
| 主卧床 | BED_BASE | 2100×1500×550 | 350 | HUMAN_CONFIRMED | mattress/base envelope only; separate HEADBOARD block |
| 主卧床头柜占位 | HEADBOARD | 150×2500×1050 | 350 | SOURCE_LABEL_SEMANTIC_CORRECTION | source_label kept for traceability; geometry is a backboard panel — never reclassify as nightstand |
| 主卧衣柜 | WARDROBE | 2100×600×2200 | 350 | STANDARD_BLOCKOUT |  |
| 次卧小床1.2 | BED_BASE | 1800×1200×550 | 350 | HUMAN_CONFIRMED | mattress/base envelope only; separate HEADBOARD block |
| 次主卧衣柜 | WARDROBE | 1500×600×2200 | 350 | STANDARD_BLOCKOUT |  |
| 主卧电视柜 | TV_CABINET | 500×2000×480 | 350 | STANDARD_BLOCKOUT | was stretched to ~level height — fixed |
| 次主卧电视柜 | TV_CABINET | 500×2000×480 | 350 | STANDARD_BLOCKOUT | was stretched to ~level height — fixed |
| 书柜 | TALL_BOOKCASE | 450×4200×2000 | 350 | HUMAN_CONFIRMED |  |
| 矮书柜 | LOW_BOOKCASE | 1600×450×900 | 350 | HUMAN_CONFIRMED |  |
| 茶台 | STUDY_WORKSTATION | 800×2200×750 | 350 | HUMAN_CONFIRMED | 2200×800 workstation/tea table — footprint human confirmed |
| 主人椅 | STUDY_ARMCHAIR | 400×400×850 | 350 | STANDARD_BLOCKOUT | OWNER_CHAIR; seat_height=430; do not classify as DINING_CHAIR |
| 条凳 | BENCH | 300×1600×450 | 350 | STANDARD_BLOCKOUT | seat-height bench |
| 凳子 | STOOL | 400×400×450 | 350 | STANDARD_BLOCKOUT |  |
| 次卧凳子 | STOOL | 400×400×450 | 350 | STANDARD_BLOCKOUT |  |
| 餐椅 | DINING_CHAIR | 400×400×850 | 0 | HUMAN_CONFIRMED | seat_height=450 |
| 餐椅003 | DINING_CHAIR | 400×400×850 | 0 | HUMAN_CONFIRMED | seat_height=450 |
| 餐椅 | DINING_CHAIR | 400×400×850 | 0 | HUMAN_CONFIRMED | seat_height=450 |
| 餐椅004 | DINING_CHAIR | 400×400×850 | 0 | HUMAN_CONFIRMED | seat_height=450 |
| 现有橱柜 | CABINET | 500×1500×850 | 0 | STANDARD_BLOCKOUT | life-balcony counter |
| 客卫洗手盆柜体 | VANITY | 600×1200×850 | 350 | HUMAN_CONFIRMED | countertop height |
| 鞋柜 | SHOE_CABINET | 300×722×1000 | 0 | HUMAN_CONFIRMED |  |
| 橱柜 | CABINET | 1200×500×850 | 0 | STANDARD_BLOCKOUT | life-balcony counter |
| 主卫湿区 | SHOWER_ZONE | 1000×1522×2000 | 350 | HUMAN_CONFIRMED | not solid furniture — glass screen blockout only |
| 主卫马桶 | WC | 500×650×780 | 350 | HUMAN_CONFIRMED | overall blockout height |
| 主卫洗手盆和柜体 | VANITY | 1200×500×850 | 350 | HUMAN_CONFIRMED | countertop height |
| 次主卫湿区 | SHOWER_ZONE | 823×1547×2000 | 350 | HUMAN_CONFIRMED | not solid furniture — glass screen blockout only |
| 次主卫台盆和柜体 | VANITY | 1000×500×850 | 350 | HUMAN_CONFIRMED | countertop height |
| 次主卫马桶 | WC | 500×600×780 | 350 | HUMAN_CONFIRMED | overall blockout height |
| 冰柜 | FREEZER | 1200×600×850 | 0 | SKU_TO_VERIFY | temporary B1 value; SKU TO_VERIFY |
| 洗衣机+烘干机（叠放） | STACKED_WASHER_DRYER | 600×600×1700 | 0 | HUMAN_CONFIRMED | two units stacked 850+850 |
| 3kg洗衣机 | 3KG_WASHER | 450×450×550 | TO_VERIFY | SKU_TO_VERIFY | wall-mounted candidate; physical body ~500–600; mount/base_z TO_VERIFY |
| 打印机 | PRINTER | 400×400×300 | 350 | STANDARD_BLOCKOUT | generic blockout |
| nas | NAS | 400×400×400 | 350 | STANDARD_BLOCKOUT | generic blockout |
| 次卧衣柜 | GUEST_WARDROBE | 500×2000×2200 | 350 | STANDARD_BLOCKOUT | depth 500 = HUMAN_CONFIRMED |
| 三人位 | SOFA_3S | 900×2300×850 | 0 | HUMAN_CONFIRMED | seat_height=430; compound: seat+back+arms envelope ok for B1 |
| 双人位 | SOFA_2S | 1900×850×850 | 0 | HUMAN_CONFIRMED | seat_height=430 |
| 贵妃椅 | CHAISE | 1700×900×800 | 0 | HUMAN_CONFIRMED | seat_height=430 |
| 茶几 | COFFEE_TABLE | 550×1000×400 | 0 | HUMAN_CONFIRMED |  |
| 角几 | SIDE_TABLE | 500×500×500 | 0 | HUMAN_CONFIRMED | Ø500 nominal |
| 餐桌 | DINING_TABLE | 1600×800×750 | 0 | HUMAN_CONFIRMED | 1600×800 |
| 床背板 | HEADBOARD | 200×1200×1050 | 350 | STANDARD_BLOCKOUT | separate block behind study bed |
| 窄书桌 | NARROW_DESK | 350×1650×750 | 350 | HUMAN_CONFIRMED | 350×1650 |
| K-RUN-E | BASE_CABINET | 600×3215×900 | 0 | STANDARD_BLOCKOUT | east run; contains K-COOK/K-DISHW/K-BASKET |
| K-COOK | BASE_CABINET_MODULE | 600×900×900 | 0 | STANDARD_BLOCKOUT | nested in K-RUN-E — hob module |
| K-DISHW | BASE_CABINET_MODULE | 600×600×900 | 0 | STANDARD_BLOCKOUT | nested in K-RUN-E — dishwasher |
| K-BASKET | BASE_CABINET_MODULE | 600×450×900 | 0 | STANDARD_BLOCKOUT | nested in K-RUN-E — pull basket |
| K-FRIDGE-TALL | TALL_CABINET | 1840×700×2000 | 0 | STANDARD_BLOCKOUT | tall unit housing fridge cavity |
| K-FRIDGE | TALL_CABINET_MODULE | 905×700×2000 | 0 | ARCHITECTURAL_TO_VERIFY | nested cavity inside K-FRIDGE-TALL; exact appliance recess TO_VERIFY |
| K-RUN-S | BASE_CABINET | 1210×600×900 | 0 | STANDARD_BLOCKOUT | south run; contains K-SINK |
| K-SINK | BASE_CABINET_MODULE | 990×600×900 | 0 | STANDARD_BLOCKOUT | nested in K-RUN-S — sink module |
| K-WALL-E | WALL_CABINET | 380×3215×700 | 1400 | STANDARD_BLOCKOUT | wall-hung cabinet; bottom z=1400, top=2100 |
