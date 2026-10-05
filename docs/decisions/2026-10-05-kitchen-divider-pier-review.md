# C-Type kitchen divider pier and oblique AC — HUMAN_REVIEW

The owner identified missing solid wall/pier in the gap between `B11_K-ISLAND_CONNECTOR_COUNTER` (ent_3dd98b68abbf480185c4a6c4ccf37453) and `B11_K-UTILITY_UPPER_DOOR_1` (ent_6bdf6778082342f78521def1ff6d8084), supported by the marked on-site photo. Owner rules: island notch determines wall depth; utility cabinet position determines width. AC size is secondary; its installation is oblique in the photograph.

## Exact authority and scope

Base: `/Users/xiwei/interior_design/projects/c_type_home/design/bedroom_door_r4/OPTION_A_SLIDING_R4.blend`, SHA256 `d109c7efcfa2b2b2565e4c073ee0cdf5282b23c01122bc9c1bbe7b8791ac3afb`. Frozen R4 and `KITCHEN_APPROVED_AS_IS_V1.blend` are retained byte-for-byte with unchanged mtimes; their manifests are not changed. This is a separate unapproved review snapshot, not a new frozen authority or construction release.

Read-only investigation confirmed an inherited CAD pier `W_wall_md_0009` with bounds approximately X5.4999–5.8999, Y0.0002–0.7002, Z0–2.8 m. The active unified R4 wall shell covers that back portion; top rays at Y0.85, 1.10 and 1.20 found a genuine empty forward area. This is a local model omission rather than only an export visibility issue. Historic blanket removal classification of the kitchen west wall must not erase the owner-confirmed surviving pier.

## Modeling decisions

Add `KITCHEN_DIVIDER_PIER_SITE_REVIEW` as one closed 8-vertex/6-face solid, with bounds X5.522375–5.900000, Y0.700200–1.430000, Z0–2.8 m. X comes from the utility cabinet's right extent to the connector's left plane. Y ends exactly at the shared rounded-island notch/connector corner; body panel inset is not used as the notch. Added span is about 377.6 ×729.8 ×2800 mm. Existing rear pier remains intact, for about1430mm combined depth from its back datum. These are inherited model anchors plus owner alignment instructions, not newly surveyed metric dimensions or proof of bearing capacity.

Yaw `B11_K-UTILITY-WALL-AC` by +60° around its original body center. Child mesh shapes/dimensions remain unchanged. The angle is an explicit model review value representing the photo's oblique installation; it is not a measured mounting angle. This resolves the prior schematic casing's roughly90mm overlap with the new pier without altering the wall width/depth or cabinet placement. Only the AC root and its five child poses/review-state annotations change; all other1538 inherited objects retain mesh, pose, parent, visibility, material references and custom properties.

## Latest owner refinement

The owner explicitly deferred further HVAC installation studies. Starting from displayed review-2 (not the inward-shift clearance study), reduce the added pier thickness by50mm: keep island-side X5.9, island-notch Y1.43 and height Z2.8 fixed; retreat the utility-side face to X5.572375. Final added solid is about327.6 ×729.8 ×2800mm. Raise the existing oblique AC assembly exactly300mm; retain X/Y, yaw, scale and child meshes. Its body now spans Z2.45–2.73m, fitting beneath the inherited2.8m model top without resizing. Cabinetry/island and unrelated objects stay unchanged. These are model review values, with HVAC detailing deferred.

## Delivered artifact paths

- Review .blend: `/Users/xiwei/interior_design/projects/c_type_home/design/kitchen_divider_r4_review/OPTION_A_R4_PIER_THINNER_AC_RAISED_REVIEW.blend`
- SHA256: `bffc60b456e81e30a29613e9b3ef07b6684a16700233c5a6673fab5bf49588ed`
- Geometry/source QA: `.../kitchen_divider_r4_review/THINNER_PIER_RAISED_AC_QA.json`
- Final browser view: `.../kitchen_divider_r4_review/THINNER_RAISED_WORKSPACE.png`
- Derived proxy and version-linked sidecars: `.../kitchen_divider_r4_review/proxy-thinner-raised/`
- Source scripts: `projects/c_type_home/scripts/restore_kitchen_divider_pier.py` and `projects/c_type_home/scripts/refine_kitchen_pier_review.py`

The wall-only intermediate file and prior R4 proxies are preserved. The new proxy has921 entities, preserves all920 prior visible stable IDs, and adds `ent_b1bbaaf28737516b9c695b249f0d7ea5`. New context source resource `c_type_r4_pier_review`, revision `r4-pier-ac-review-4`. The export uses an immutable read-only review snapshot for adapter safety; manifest review metadata explicitly distinguishes it from an approved frozen design. Space/graph registries are explicitly versioned for this derived snapshot; inherited relations retain original evidence rather than inventing supports or functional contact edges for the new pier.

## Original restoration gates (review-2)

- Original R4, kitchen frozen .blend and both freeze manifests: SHA/size/mtime unchanged.
- All protected furniture/island positions unchanged; AC local mesh shapes unchanged.
- Added pier: positive volume, zero open/nonmanifold edges, three top-ray hits at+2800mm; cabinet/island and AC AABB overlaps empty.
- Fresh independent .blend reopen:1538 unchanged objects plus six authorized AC pose objects; exactly one added mesh.
- Fresh GLB import:921 entities and exact pier bounds, including Y1.43 notch alignment and Z2.8 height.
- Runtime GLB preflight and stable-ID checks pass; actual browser click hits the new wall at source point[5.754373547,1.430000067,1.916269363].
- Packet/source/registry/binding byte-hash and graph-neighborhood verification passes for that click.

## Latest refinement gates

- Fresh .blend reopen comparison to displayed review-2: exactly50mm wall reduction and300mm AC translation; all other object states unchanged.
- Latest proxy and browser wall bounds match X5.572375–5.9; all921 binding identities are retained.
- Browser actually loaded revision `r4-pier-ac-review-4`; wall raycast and ContextPacket source/hash/bindings checked.
- Frozen R4, kitchen .blend and both freeze manifests retain original SHA/size/mtime.

Stop at HUMAN_REVIEW. Exact wall survey dimensions, AC installation angle and structural bearing classification require site/engineering evidence; no fabrication or structural claim is made.
