# B1 READINESS CHECKLIST

Prerequisite: `B0_EXISTING_AS_IS.blend` — FROZEN (see
`B0_FREEZE_MANIFEST.json`, SHA256-pinned).
B1 work happens in `B1_RENOVATION_DESIGN.blend` (branched copy) —
never write back to B0.

## B1 staging plan (agreed)

```
B1_RENOVATION_DESIGN.blend   (all renovation work lives here)
```

**B1.1 — Design Model** (dimensional/spatial correctness first)
- [ ] Kitchen custom cabinetry
- [ ] Three bathrooms (real fixtures, plumbing positions)
- [ ] Glass shower enclosures (replace ~2000mm blockouts)
- [ ] Wardrobes / bookcases / storage
- [ ] Real furniture assets: beds, sofa, dining table & chairs
- [ ] Door/window detail incl. D-107 leaf
- [ ] Stair & split-level edge finishing (fascia detailing)
- [ ] Basic ceiling coffers / light slots

**B1.2 — Visual Design** (Blender-only presentable renders)
- [ ] Flooring, wall paint, wood veneer, stone, fabric, metal, glass
- [ ] Daylight + artificial lighting + fixtures
- [ ] Fixed cameras (~1600 above local FFL: 1600 lower / 2050 upper)
- [ ] Cycles render pipeline

**B1.3 — AI Design Exploration**
```
Blender authoritative model
  -> Beauty + Depth + Normal + Masks
  -> AI divergence
     L1: materials / lighting / soft furnishing
     L2: TV wall / headboard / cabinetry / ceiling design
     L3: bolder creative challenge
  -> selected idea written BACK into Blender
```
AI enriches design; it never rewrites house facts.

## Resolve open items

## Resolve open items

- [ ] GAP-20 north recess: confirm vs original plan/CAD → assign level or
      mark confirmed void
- [ ] AC equipment niche: measure actual platform/louver detail on site
- [ ] Stair void ceiling height (assume 3250 until measured)
- [ ] Beam / soffit / pipe-boxing dimensions (photo only proves they exist)
- [ ] Existing stair exact tread/riser dims on site (model = 3×150 approved
      approx)

## Assets needed

- [ ] Real furniture library (replace blockout boxes): sofa, dining set,
      beds, wardrobes, desks
- [ ] Kitchen cabinetry + appliances (existing layout reference)
- [ ] Bathroom fixtures: WCs, vanities, shower glass hardware
      (2 shower boxes already simplified glass @2000mm STANDARD_BLOCKOUT —
      real SKU TO_VERIFY)
- [ ] Door leaf/window frame assets incl. D-107 26.3° angled door
- [ ] Stair balustrade / platform edge detail for fan leisure curve

## Design inputs

- [ ] Owner brief: finishes palette (wood/stone), style direction
- [ ] Future scope decision: ramp, fan-area demolition, living expansion
      — each becomes a `90_FUTURE_DESIGN_OPTIONS` variant branch
- [ ] Lighting plan input (ceiling transitions constrain fixture layout)
- [ ] Accessibility requirements (wheelchair clearances for ramp option)

## Technical prep

- [ ] Final Cycles materials (B0 uses review blockout materials)
- [ ] Camera set for design review (interior eye-level ~1600 above local FFL:
      1600 lower / 2050 upper)
- [ ] AI render pipeline inputs: clean white-box renders per room at both
      levels, material reference board
- [ ] Web viewer export format decision (glTF/IFC) — ifcopenshell available
      in project venv

## Explicit non-goals for B0 (done, do not revisit)

- Zone polygons do not create XY geometry (CAD owns XY)
- No raster/grid level inference without physical transition geometry
- Future options never enter Existing collections
