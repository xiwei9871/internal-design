# Visual notes (EEVEE 32spp preview, 1600x900, existing cameras, file sha feaeed38)

## Sheet 2 (opened)
- CAM_master_bath_VIEW_03: mirror shows blurred mountain landscape — reflection falls back to world HDRI (bath has no window in that direction) -> EEVEE probe/SSR artifact; must be checked in Cycles before judging. Framing cramped: 22mm close to vanity, toilet cut at right edge; basin reads as flat rectangle. Marble tile and wood shelf read well.
- CAM_mother_bedroom_VIEW_01: bed, linen, bedside table read as finished; scale plausible. Window exterior = arid mountain HDRI (kiara_3_morning) — not plausible for an urban Chengdu apartment, pulls style off. Duvet grey band flat. Wall/ceiling neutral, low contrast.
- CAM_north_sunroom_VIEW_02: SUNROOM_PLANT_LEAF_* "plants" read as abstract wooden sculptures; dark grey freezer block is the only strong value and draws the eye; upper cabinet cut at top-right; large frosted glass flat white. Floor marble ok. Same arid HDRI outside.
- CAM_reading_transition_VIEW_01: three wave steps clear and handrail present; but floor, steps, door leaves, casings, shelf all the same pale ash -> monotone, no figure/ground; step nosing has no contrast strip (also a safety/visibility point for mother at night).
- CAM_secondary_bath_VIEW_01: round mirror again shows HDRI landscape (artifact); basin is a flat inset outline in the wood top — reads unfinished; frosted shower door large flat area; vanity wood good.
- CAM_study_VIEW_02: camera very close to movable desk (desk dominates foreground, edge-on); art/shelf/tea counter fine; walls flat.

## Sheet 1 (opened)
- CAM_couple_bedroom_VIEW_01: bed/pillows/linen read well, proportions plausible; window = arid mountain HDRI; no curtain visible at window in frame; walls/ceiling flat, low tonal separation.
- CAM_dining_VIEW_02: 22mm, foreground chairs and table edge cut and stretched at frame edges; wave glass + kitchen marble + art read; whole frame dominated by one pale ash tone (floor, table, chairs, cabinets).
- CAM_guest_bedroom_VIEW_01: very cramped framing; pillow is a smooth flat block; large frosted glass reads as blank white wall; desk/chair/pegboard fine.
- CAM_kitchen_VIEW_01: fridge (V3_BRUSHED_STAINLESS) reads as a featureless gradient slab, no handle/gap detail; hob detail good; marble backsplash veining large and high contrast; ceiling band above cabinets darker; under-cabinet light effect not visible.
- CAM_living_VIEW_01: window = desert HDRI; curtains at window read as dark corrugated columns; rug and artwork are the only saturated elements (orange/navy) and compete; grainy speckle at ceiling/wall junction.
- CAM_living_VIEW_05: same ceiling-edge speckle (EEVEE 32spp noise/AO, not judged final); HDRI shrub/desert; overall flat light, little directional sun.

## Cycles 64spp (file's own AgX MHC, exposure 0.15) vs EEVEE 32 — compare_engines.jpg (opened)
- master_bath_VIEW_03: Cycles mirror reflects wall + shelf correctly -> EEVEE landscape-in-mirror is a PREVIEW ARTIFACT, not a model defect. Cycles frame is high-key / washed out: white marble, white basin, white wall merge; very low contrast; basin edges hard and boxy.
- living_VIEW_01: Cycles curtains read as light pleated linen (EEVEE dark-striped = artifact); ceiling speckle gone (EEVEE noise). Desert/hill HDRI still visible through window in Cycles -> REAL issue. Lighting soft and sourceless; rug + art carry all colour.
- kitchen_VIEW_01: Cycles fridge = flat brushed panel with centre gap, no handles/reveals -> geometry/detail issue confirmed; stainless isotropic. Hob detail good. Counter/backsplash bright and flat.

## History compare living (compare_history.jpg, opened)
- v1 = clay/workbench geometry only (not a lookdev reference).
- pale_ash_v7: glass shows interior reflection, exterior darker -> window reads as glass, less "poster".
- glass_v9 and V15F: clear glass shows bright desert HDRI full-frame -> exterior dominates, poster-like.
- V15F adds V14 rower (HOUSE_V1_V14_ROWER_*) directly in front of north window (y12105-12715): blocks window base and the chaise view; visual clutter in hero view.
