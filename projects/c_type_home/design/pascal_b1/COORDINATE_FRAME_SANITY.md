# COORDINATE FRAME SANITY CHECK — master_direct chain

Date: 2026-09-30. Query-only verification; no model changes.
Chain: PRE_BLENDER_MASTER_V2 (canonical mm) → wall_band_extractor_v2 →
master_direct_arch_v1.json → pascal-master-direct-arch-v1.

## 1. Actual transformation (verified per wall node)

```
canonical mm (x,y)  →  Pascal (x,z) m
[xp]   [0.001   0    ] [xc]
[zp] = [0     -0.001 ] [yc]
```

i.e. `pascal_x = cad_x · 0.001`, `pascal_z = -cad_y · 0.001`.

In plan-view frame (x, -z): **identity × 0.001** — determinant > 0, no mirror.

Checked: 60/61 extracted wall nodes have endpoints ==
`centerline_mm × (0.001, -0.001)` of their source band rect.
Exception: WB-008 (near-square corner band 350×250) — node emitted with
axis interpreted along the other direction; same rect patch, thickness/
length axis swapped. Minor axis-ambiguity bug, not a mirror.

## 2. Landmark table (verified-opening rect centers, canonical mm)

| id          | CAD rect-center | Pascal node (x,-z) | delta | cause |
|-------------|-----------------|--------------------|-------|-------|
| W-LIV-N     | (5350, 12850)   | (5350, 13845)      | +0,+995 | FRONT_GLAZING on projected bay band |
| G-LIV-NBALC | (7850, 12225)   | (7875, 12225)      | +25,+0  | host-band centerline |
| G-GB-BALC   | (11400, 10800)  | (11400, 11000)     | +0,+200 | host-band centerline |
| W-MB-S      | (13450, -100)   | (13450, -650)      | +0,-550 | FRONT_GLAZING on projected bay band |
| G-DIN-LIV   | (4300, 4622)    | (4300, 4622)       | +0,+0   | exact |

All deltas are documented node-placement conventions, not transforms.

## 3. Handedness

Triangle: G-LIV-NBALC → G-GB-BALC → G-DIN-LIV

```
CAD       (x,y)  : -16023812
EXTRACTOR (x,y)  : -16023812   (identical frame)
PASCAL    (x,-z) : -15588736   (same sign — orientation preserved)
PASCAL raw (x,z) : +15588736   (opposite sign — expected: z = -y)
```

Sign flip in raw (x,z) is the definition `z = -y`, not a data mirror.
Pascal top-down view presents -z as screen-up → rendered plan matches
CAD orientation (confirmed visually: living top-left, bedrooms
bottom-right, kitchen bottom-left).

## 4. Plot vs data

`MASTER_DIRECT_V1_CHECK.png` and extractor overlays use
`ax.set_ylim(14700, -1500)` (reversed ylim) so the picture looks like the
FreeCAD screen. Display-only.

```
PLOT_Y_INVERTED          = TRUE   (matplotlib reversed ylim)
DATA_GEOMETRY_MIRRORED   = FALSE
```

## 5. Gate

```
COORDINATE_FRAME = PASS
```

- extractor frame == canonical frame == CAD frame (bit-exact, no flip)
- Pascal = scale + z-negation; handedness preserved in plan-view frame
- residual: WB-008 axis-ambiguity on one near-square band (250×350);
  geometry patch identical, orientation annotation only.
