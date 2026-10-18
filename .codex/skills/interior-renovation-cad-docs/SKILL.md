---
name: interior-renovation-cad-docs
description: Generate standardized interior construction DXF sheets (墙体拆改/平面布置/天花/地面铺装/电气点位/给排水) for a renovation project by diffing an authoritative as-built CAD base against the design Blender model. Use when producing 施工图 that must match a real model, not hand-drawn guesses.
---

# Interior Renovation CAD Docs

Produce renovation construction drawings where every line is accountable to either the authoritative as-built plan or the design model. Never hand-place room fills or walls.

## Inputs

1. **As-built authoritative DXF** (e.g. FreeCAD-exported original plan) with proper layers (`A-WALL/A-DOOR/A-WINDOW/A-DIMS/A-TEXT`). This is the frozen base — copy it, don't redraw it.
2. **Design Blender model** (the renovation design). Verify coordinate alignment once (compare west wall / south wall positions); expect it to match the base within ~250mm offsets for facade-face vs structure edges.
3. **Design intent notes** (owner decisions, e.g. "kitchen is tile even though model floor material is unified wood-look").

## Core methods

### Wall diff (拆除/新建/保留)
- Model walls come in two forms: thin partition objects (bbox = wall band) and giant merged `*_WALL_SHELL` meshes (bbox useless — whole house).
- Rasterize a **model wall mask**: thin-wall bboxes + SHELL vertex cloud (verts z<1600), 100mm/px grid, dilate ~250mm to absorb alignment tolerance.
- Sample each baseline wall polyline along its centerline (≤400mm segments). Segment hit <55% → demolished; the rest → kept. Trim partially-demolished walls into kept stubs + demo segments.
- New walls = model thin walls <55% covered by baseline (+250mm buffer). Cross-check with owner: model may omit real walls (e.g. balcony enclosure was a model bug, restored per owner).
- Draw on a 拆改图 (A102): retained=thin gray `A-EXIST`, demolished=red dashed `A-DEMO`, new=thick `A-NEW`. All other sheets use the corrected wall set.

### Floor finish zones (地面铺装)
- Do NOT hand-draw rectangles — they leak outside walls and miss alcoves.
- Render a **material-paint orthographic top view** (wood=red, tile=green, wall=blue, furniture=gray, override materials temporarily, emission shader + flat ortho camera).
- Pixel-segment: interior mask = outer envelope (wall-shell contours filled) minus walls; furniture pixels assign to nearest material; tile/wood connected regions → simplify → DXF polylines.
- Apply **design-intent overrides** where model material is placeholder (verify each override with the owner — wrong in both directions happened).
- Symbols: wood = parallel lines along real laying direction at plank pitch (150mm), tile = module grid (600×600), threshold stone rect **only where sampled materials differ across the opening** (probe multiple depths, door leaves can spoof single-sample reads), floor drain ◎ + 1% slope note, 起铺点 diamond, dry ±0.000 / wet −0.015 elevations.

### Ceiling / electrical / plumbing sheets
- Fixture symbols must be **graded by type** (筒灯○⊕ vs 吊灯⊗ vs 灯带双线 vs 镜前灯竖条); identical circles for everything is a fail.
- Audit every luminaire against use: cabinet strip follows cabinet direction; bedside lamps outside bed bbox; mirror light over the actual mirror (check mirror object coords, not room center); furniture lamps (desk/floor) are not ceiling fixtures — draw dashed or omit.
- Sockets/switches located relative to real furniture bboxes (bedside flanking bed, TV wall, counter run); label `H<height>` per convention (300/700/1200/1300/2200, 马桶400, 台面1200).
- Plumbing points from real fixture objects (toilet/basin/drain/washer/sink); route lines only where modeled — concealed pipe topology is never invented; mark `待现场复尺`.

## Sheet set

A102 墙体拆改 · A103 平面布置 · A201 天花布置 · A202 地面铺装 · A302 电气点位 · A303 给排水. Every sheet: legend box, Chinese notes (material/spec/verification), title block (项目/图名/图号/比例/单位/版本/日期), frozen audit layers (`A-SOURCE-REF` etc.) turned off.

## Conventions

- Units mm, scale annotation 1:50; Chinese-capable text style (`HZTXT` with STHeiti) — preview renderers need a CJK font override (e.g. matplotlib `Heiti TC`).
- Keep the base file's layers/lineweights; add design layers (`A-FURN/A-FIXT/A-DESIGN/A-ELEC-*/A-PLUM-*`) alongside.
- Version tags on sheets (R1/R2…) and in filenames' sibling `_preview.png`; one render script regenerates all previews after any edit.
- Honesty: anything not modeled or owner-unconfirmed gets `待现场确认`/`按现状估计`, never fabricated dimensions.

## Verification loop

Render preview PNG → compare against model top view and owner reference drawings → fix → re-render. Do not declare done until walls (demo/new), room names, fixture purposes, and finish zones all agree with both sources.
