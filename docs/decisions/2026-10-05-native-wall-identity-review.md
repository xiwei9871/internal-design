# Native Blender wall identity in Spatial Canvas Proxy - HUMAN_REVIEW

The owner confirmed that Blender already has independent wall operands, but the current Proxy displayed two large derived wall shells. This review restores selectable wall-part identity on the exact current review surface without changing the authoritative source.

## Source and scope

Input review source: /Users/xiwei/interior_design/projects/c_type_home/design/dining_chairs_r4_review/OPTION_A_R4_DINING_CHAIRS_ALIGNED_REVIEW.blend, SHA256 e2f3f107eb6619ae28a363e0e4e36019cdae94c89aabe9ac4b8c0c07b14b14ac, revision r4-dining-chairs-review-1.

The visible wall surface is partitioned using the source wall operand inputs used to build the current Blender review: the 108-wall rollback input for R3_HOUSE_WALLS_D107_ROLLED_BACK and the authored A wall input for R3_COMPLETE_PARTITION_WALLS. Each derived part retains its source operand names and a stable deterministic entity ID. The two parent shells are hidden only in the derived review copy. Their surface area is conserved; no cap, opening, room boundary, thickness, or new construction geometry is invented.

The new derived revision is r4-walls-view-review-1, with 98 independent wall-part entities and 919 retained non-wall entity IDs, for 1,017 entities total. Relationship edges mark only part_of from each view wall part to its original wall assembly. Physical connectivity, adjacency and room membership remain unavailable or candidate as before.

## Gates

- Blender source and frozen R4/kitchen files retain original SHA/size/mtime.
- All non-wall object states are unchanged; current parent wall geometry remains unchanged in the derived file.
- Partition surface area is preserved for both parent shells.
- Fresh GLB import contains 1,017 entities and all 98 wall-part bounds.
- 1,356 sampled source surface points resolve to the corresponding independent wall parts; maximum observed nearest-surface deviation is under 0.01 mm in the exported check.
- Browser loaded the new Proxy, restored the same camera view, clicked a real wall part (VIEW_WALL_W_wall_md_0006), and Ghost affected only that entity.
- Blender View Handoff adapter applied a single-wall ghost preset to a new snapshot without modifying the source.

This is a derived HUMAN_REVIEW Proxy identity repair. It does not promote the source to a new authority or change frozen R4.
