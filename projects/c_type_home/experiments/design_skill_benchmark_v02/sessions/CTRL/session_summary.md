# CTRL Session Summary

## Method rationale

This session used only the C-type owner brief, A0.4 manifest/block library, A1 rulebook, A2 pattern library, canonical geometry, window register, kitchen register, and the approved `cad_tool.py` interface. No third-party method material was used. `files_opened.json` records the allowed session inputs and SHA-256 hashes.

The public zone was treated as a retained-structure grid. The layout follows the brief and the applicable A2 patterns: clear central living core, edge-loaded furniture, dining as a kitchen extension, balcony visual extension, furniture-free circulation spine, visible social route, and non-TV-centric flexible living. All DXF mutations were issued through `cad_tool.py`.

## Topology and iterations

- **r01:** a west-edge 3-seat sofa, north-edge 2-seat sofa, east lounge chair, and a compact south dining table with three chairs. The arrangement deliberately leaves the center of the living room open and keeps the north-balcony door, entry route, and stair approach free.
- **r02:** the 2-seat sofa moved 200 mm west and 100 mm south; the lounge chair moved 700 mm west and 500 mm north and rotated 270 degrees; the kitchen-side dining chair was deleted; the dining table moved 150 mm south. The resulting six-piece topology keeps the same edge-loaded logic while making the seating group more coherent and the kitchen-side dining edge visually lighter.

## Evidence and tradeoffs

Both saved iterations have zero furniture overlaps and transformed block bounding boxes within the tool tolerance. r01 contains seven furniture blocks; r02 contains six. The living route measurements remain wide at the saved anchors: entry-to-living 2676.6 mm, living-to-stair 2047.4 mm, living-to-north-balcony 2107.3 mm, and dining-to-living transition 1900.0 mm. The automated dining-to-keep-kitchen anchor remains 15.0 mm in both iterations because the tool treats the retained kitchen keep rectangle as an immutable obstacle at that cross-section; the r02 deletion keeps loose furniture away from that edge but does not change the underlying architectural datum. Field verification is required before construction.

The main tradeoff is between a larger furniture-free activity field and a seating group that reads as a family room. Moving the lounge chair inward improves the conversation triangle but consumes some flexible floor. Moving the 2-seat sofa south and west improves the north-bay breathing room while keeping a readable edge anchor. Keeping only two dining chairs in r02 avoids forcing a fourth chair into the constrained service side; the table remains suitable for normal daily use with adaptable seating.

## Approved block IDs used

- `SOFA_3S_2200x900_PLAN`
- `SOFA_2S_1800x850_PLAN`
- `LOUNGE_CHAIR_900x900_PLAN`
- `DINING_TABLE_1500x600_PLAN`
- `DINING_CHAIR_450x500_PLAN`

No fixed coffee table, projector, or storage block was added because those blocks are not in the approved D0.2 public-zone set. The lounge chair is documented in A0.4 as a semantic proxy footprint. The two iteration reviews record the visual failures, spatial reasons, hierarchy, and next checks.
