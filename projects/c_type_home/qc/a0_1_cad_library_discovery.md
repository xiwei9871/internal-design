# A0.1 Internet CAD Library Discovery

**Date:** 2026-09-26
**Scope:** source discovery only. No CAD block was downloaded, converted,
normalized, or added to the project library.

## Decision rules

- `license unclear = HOLD`; a free download page is not a reuse license.
- A source is a first-round fit only when it has 2D plan geometry, a reliable
  DXF/DWG path, units that can be checked, and an explicit asset license.
- Manufacturer and community portals are discovery sources until the specific
  asset license grants local reuse, repackaging, and commercial use.
- No furniture geometry was authored in this phase.

## Source matrix

| # | Source | License evidence | Commercial use | Format / units | 2D plan + categories | Status |
|---:|---|---|---|---|---|---|
| 1 | [Lendres/CAD-Support-Files](https://github.com/Lendres/CAD-Support-Files) | MIT `License.txt`; repo contains explicit Blocks tree | Yes, with MIT notice; verify asset provenance per file | 353 DWG blocks; imperial dimensions in names | Yes; beds, desks, chairs, sofas, doors, WC, sinks, appliances | **SHORTLIST / conditional approve** |
| 2 | [GSStnb/dxfBlocks](https://github.com/GSStnb/dxfBlocks) | GitHub API says CC0-1.0, but README says CC BY-NC-SA 4.0 | Unknown because license conflict | DXF; README says full-scale inches | Yes; furniture, fixtures, appliances, doors, windows | **HOLD — license conflict** |
| 3 | [uncreatednet/DXF-library](https://github.com/uncreatednet/DXF-library) | No repository license found | Unknown | 2,264 DXF files; units not documented | Yes; beds, chairs, lounge, tables, WC, basins, appliances | **HOLD — no license** |
| 4 | [LibreCAD/Resources](https://github.com/LibreCAD/Resources) | README permits contributor CC BY 4.0, MIT, or CC0; per-folder license files required | Conditional, per asset | DXF templates; cm/inch/mm templates | 2D templates/tooling, not a furniture block library | **SHORTLIST — tooling only** |
| 5 | [Bollos00/DXF-ElectronicComponentsLibrary](https://github.com/Bollos00/DXF-ElectronicComponentsLibrary) | GPL-3.0 metadata | Yes with GPL obligations | DXF; units not confirmed | 2D electronic components, not furniture/fixtures | **OUT — wrong category** |
| 6 | [vcfxb/Furniture](https://github.com/vcfxb/Furniture) | MIT | Yes with MIT notice | OpenSCAD `.scad`; no DXF/DWG | 3D furniture source, not plan blocks | **DEFER — 3D only** |
| 7 | [partcad/partcad-furniture-basic](https://github.com/partcad/partcad-furniture-basic) | No repository license found | Unknown | PartCAD assembly; no DXF | 3D desk example only | **HOLD — no license / wrong format** |
| 8 | [growdigital/blocks-furniture](https://github.com/growdigital/blocks-furniture) | No repository license metadata found | Unknown | CAD blocks format not confirmed | Garden furniture only | **HOLD — no license** |
| 9 | [Preetpalkaur3701/FreeCAD_Furniture_Library](https://github.com/Preetpalkaur3701/FreeCAD_Furniture_Library) | No license metadata found | Unknown | Default branch has no inspectable block files | Furniture library claim, format unavailable | **HOLD — no license / unavailable** |
| 10 | [QCAD Part Library documentation](https://qcad.org/doc/qcad/latest/reference/en/tutorials/part_library_blocks/working_with_the_part_library/working_with_the_part_library_en.html) | Documentation, not an asset license | N/A | Supports DXF/DWG/SVG part libraries | 2D workflow guidance; points to external sources | **DISCOVERY GUIDE** |
| 11 | [ARCAT CAD Details](https://www.arcat.com/details/cad_details.shtml) | Manufacturer/content terms must be checked per asset | Unknown | DWG/DXF availability varies | Architectural products and details | **HOLD — asset terms required** |
| 12 | [CAD-Blocks.net](https://www.cad-blocks.net/) | QCAD lists it as a source; asset license not verified | Unknown | DWG free/premium; units not confirmed | Furniture and architectural blocks | **HOLD — license unverified** |
| 13 | [CAD-block.com](https://www.cad-block.com/) | Site says free DWG downloads and “all rights reserved”; no reuse grant found | Unknown | DWG, 2D/3D mixed | Furniture, appliances, architecture | **HOLD — redistribution unclear** |
| 14 | [First In Architecture CAD blocks](https://www.firstinarchitecture.co.uk/free-cad-blocks/) | Copyright statement says content belongs to site or listed manufacturers | Not granted for library redistribution | CAD blocks; file/unit details vary | Furniture, bathroom, accessibility, people, landscape | **HOLD — copyright/redistribution restriction** |
| 15 | [Archweb CAD blocks](https://www.archweb.com/en/cad-dwg/) | Site footer says all rights reserved; subscription/download terms apply | Unknown | DWG; units vary | Furnishings, bathrooms, mobility and architecture | **HOLD — all rights reserved** |
| 16 | [BIMobject](https://www.bimobject.com/en) | Manufacturer platform terms; asset-specific rights | Unknown | Mostly BIM/3D formats | Manufacturer objects; 2D plan availability varies | **HOLD — not DXF-first** |
| 17 | [CADdetails](https://www.caddetails.com/) | Manufacturer/content terms; asset-specific rights | Unknown | DWG/BIM varies | Product CAD/BIM, not a reusable open block corpus | **HOLD — asset terms required** |
| 18 | [TraceParts](https://www.traceparts.com/en) | Manufacturer platform terms; asset-specific rights | Unknown | Mostly 3D CAD formats | Product parts, not 2D interior symbols | **HOLD — not plan-block fit** |

## Shortlist

1. **Lendres/CAD-Support-Files** is the strongest first source: explicit MIT
   license, a large architectural block tree, and named beds/desks/sofas/WC/
   sinks/appliances. It is DWG/inch-first, so the next phase must convert a
   small sample to DXF, normalize inches to mm, and verify dimensions.
2. **LibreCAD/Resources** is suitable as a standards/template reference. It
   is not a furniture source, and every contributed folder still needs its own
   license file before reuse.
3. **GSStnb/dxfBlocks** is technically the best DXF/category match, but the
   CC0 API result conflicts with the README's CC BY-NC-SA declaration. It stays
   HOLD until the upstream license is clarified.
4. **uncreatednet/DXF-library** is technically rich and directly DXF, but has
   no license file or commercial reuse grant. It stays HOLD.
5. **QCAD's part-library guide** is a workflow reference, not a source to
   import. Its linked third-party sites remain asset-license checks.

## Approved status

**Approved for download:** none in A0.1.

**Conditional next-phase candidate:** Lendres, after file-level provenance and
unit conversion checks.
**No source files were downloaded into the repository.**

## Next phase, only after approval

Take 10–20 representative blocks from the conditional candidate, convert a
small sample to DXF, normalize units/base points/layers/block names, and run
footprint/scale/orientation QA. Do not build a furniture library from
unlicensed or ambiguous sources.
