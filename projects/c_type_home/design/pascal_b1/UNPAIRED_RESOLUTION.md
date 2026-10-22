# UNPAIRED RESIDUAL RESOLUTION — master_direct_arch_v1

Every UNPAIRED S-S.WALL line is classified. unexplained_unpaired = 0.

| obj | segment (canonical mm) | category | evidence |
|---|---|---|---|
| Polyline | V x8200 y13000–13400 | WALL_RETURN | end-cap of band WB-057 (balcony pier box 7800–8200 × 13000–13400); band already covers the box |
| Polyline014 | H y0 x5500–5900 | WALL_RETURN | end-cap of band WB-005 stub (kitchen facade nib 5500–5900 × 0–700) |
| Polyline014 | H y700 x5500–5900 | WALL_RETURN | end-cap of band WB-005 stub |
| Line043 | V x12900 y4500–4800 | PIER_JAMB_DETAIL | T-junction pier with Line042 (x13100 y4700–4800) + Line118 (y4800 x12900–13100) at WB-042 west end → emitted as `PIER-00` wall node [12900,4500,13100,4800] |
| Line077 | H y13000 x3800–6900 | BAY_DETAIL | facade inner face line across W-LIV-N bay opening [3800,12750,6900,12950] |
| Line100 | H y10900 x13700–15600 | BAY_DETAIL | opening edge line of W-STUDY-NE bay [13600,10900,15700,11100] |
| Line137 | H y200 x12200–14700 | BAY_DETAIL | facade inner face across W-MB-S bay [12100,-200,14800,0] |
| Line147 | H y200 x8600–10800 | BAY_DETAIL | facade inner face across W-SMB-S bay [8500,-200,10900,0] |

Categories not requiring action: NON_WALL_DETAIL (61 short detail segments),
DIAGONAL_OR_DETAIL (8 diagonal detail segments), F-DOOR swing/leaf symbols
(represented by Pascal door nodes).

## WB-008 axis normalization

WB-008 band rect [7450,200,7800,450] (350 thick × 250 long) was emitted by
`wall_node_rect` using longest-side inference → horizontal wall. Now emits the
declared band axis → vertical wall x7450–7800, y200–450, t=350.
Physical footprint identical to the extracted band. Recorded as
WB008_AXIS_NORMALIZATION.

## Host helpers frozen separately

10 `OPENING_HOST_BAND` nodes carry
`role: PASCAL_OPENING_HOST_HELPER`, `physical_ground_truth: false`.
Ground-truth wall count = 60 face-pair bands + 1 junction pier.
