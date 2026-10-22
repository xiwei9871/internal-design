# DWG → FreeCAD DXF conversion report

## Result

- **Source:** `/Users/xiwei/interior_design/世纪欣园FF.dwg`
- **Converter:** official LibreDWG `dwg2dxf 0.14`
- **Working file:** `世纪欣园FF_freecad_WORKING.dxf`
- **FreeCAD:** 1.1.3
- **FreeCAD import:** PASS — 363 geometry entities created from 363 DXF entities
- **Units:** millimeters (`$INSUNITS = 4`)
- **DXF:** ASCII R2000 (`AC1015`)
- **Working extents:** 15100.000 × 15653.012 mm

## Files

- Full LibreDWG candidate: `世纪欣园FF_freecad_2000_ascii.dxf`
- R12 candidate: `世纪欣园FF_freecad_r12_ascii.dxf`
- FreeCAD working copy: `世纪欣园FF_freecad_WORKING.dxf`
- Previous block-based working copy retained as: `世纪欣园FF_freecad_WORKING_blocks_legacy.dxf`
- Machine-readable QA: `working_v2_qa.json`

## Working-copy policy

The working copy is generated from the official LibreDWG R2000 result. It keeps the source model-space architectural geometry and expands source INSERTs into WCS 2D geometry. It removes TEXT/MTEXT, DIMENSION, HATCH, CIRCLE-only off-origin reference content, and block containers because FreeCAD 1.1.3 fails during DXF post-processing on these source objects. No retained wall/door/stair/sanitary/fixed-fixture geometry is translated, rotated, or scaled.

The layer `USER_GUIDE_FURNITURE` is present and empty for manual furniture placement.

## Structure retained

- `S-S.WALL`: wall linework and wall polylines
- `F-DOOR`: door geometry expanded to editable linework
- `S-\U+697c\U+68af`: stair geometry
- `F-SAN FIT`: sanitary fixtures
- `F-FURN`: fixed fixture geometry from the source block

## Limitations

FreeCAD's DXF importer can edit the imported 2D linework, arcs, and polylines. Source annotations and hatch fills are intentionally omitted from the working copy; the full LibreDWG candidate remains available for audit.
