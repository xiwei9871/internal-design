# S2 CURRENT DESIGN V1 — Design Audit

Status: `DRAFT_HUMAN_REVIEW`

## Scope

This is a schematic design review generated from the latest named FreeCAD guide. It does not modify the FCStd, canonical plan, V02/V03, formal CAD, or project approval gates.

## Guide ingestion

- Primary named guide objects: 38
- Auxiliary / unnamed objects retained: 9
- All unnamed auxiliary geometry remains semantically unresolved.
- `电视柜（或者悬浮电视墙）` remains `INTENT_AMBIGUOUS`.
- `次卧小床1.2` is normalized as a nominal 1200 mm bed-width guide.
- `斜坡（轮椅用` remains an assisted-route guide with slope and final length `TO_VERIFY`.
- Room-role authority follows the named FreeCAD guide: `次卧小床1.2` + `次卧衣柜` = middle guest room; `书柜` + `茶台` + `床背板+窄书桌占位` = study / backup sleep. Historical `R-STUDY` / `R-BED-N` labels are retained only as polygon references.

## Current schematic decisions

- Living: 3-seat sofa anchor + 2-seat conversation edge + at most one lounge chair; media edge remains secondary.
- Dining: four daily seats linked to KEEP kitchen; G-DIN-LIV transition is explicitly checked.
- Middle guest room: nominal 1200 mm bed guide retained as a normalized target.
- South study / backup sleep: desk and storage remain primary; flexible seating is optional.
- Guest bathroom: boundary unchanged; WC, vanity, shower and 3 kg washer are shown as a feasibility study.
- Mother bathroom: aging-in-place shower/WC/vanity intent shown; exact clearances and services remain field/SKU verification.

## Geometry screening

- Furniture collisions: 0
- Door-swing conflicts: 0
- KEEP kitchen conflicts: 0
- Route warnings: 1

The route values are axis-aligned schematic screening envelopes. They are not construction clearances or accessibility certification. `G-LIV-NBALC` remains an existing 850 mm limitation under a no-worsening rule.

## Human review focus

1. Does the normalized 3+2+lounge living group preserve the intended central activity field?
2. Does the middle guest room remain comfortable at a nominal 1200 mm bed width?
3. Can the unchanged guest bath hold shower, WC, vanity and small washer without compromising door use?
4. Does the study remain a real work room while retaining backup sleep/flexible seating?
5. Does dining preserve the kitchen relationship and leave the G-DIN-LIV transition usable?

## Outputs

- `human_guide_inventory.json`
- `furniture_dimension_register_v01.json`
- `design_model_v01.json`
- `s2_collision_circulation_report.json`
- `S2_CURRENT_DESIGN_V1.png`
- `S2_CURRENT_DESIGN_V1.pdf`

Next gate: human review. No S2 approval or formal CAD write-back is implied.
