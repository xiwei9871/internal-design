---
name: interior-renovation-cad-docs
description: Generate interior renovation construction DXF sheets (墙体拆改/平面布置/天花/地面铺装/水电点位/走顶路由) from an as-built CAD base plus real geometry extracted from the design Blender model, then gate each sheet with automated DXF QA. Use when producing 施工图 that must match a real model. Not for proving site dimensions, structure, or MEP feasibility.
---

# Interior Renovation CAD Docs

Every line on a sheet must trace to either the as-built base or real model geometry.
Never hand-place room fills, and never derive zones from rendered images.

## Source hierarchy (highest first)

1. **As-built survey CAD** (e.g. `projects/c_type_home/cad/measured_working.dxf`): walls, openings, dimensions.
2. **Developer original plan**: which walls are structural (black = keep, white = may change).
3. **Owner decisions** (`DESIGN_DECISIONS_*.md`, chat decisions recorded in the review doc).
4. **Design Blender model**: room use, finish zones, ceiling zones, fixtures, furniture.

When the model disagrees with 1–3, draw per 1–3 and list the difference. Do not edit the model.

## Geometry rules (real geometry first)

- **Floor and ceiling zones come from mesh faces**, via
  `../blender-plan-geometry-extraction/scripts/extract_plan_geometry.py` (up-facing faces for
  floors, down-facing for ceilings), unioned in Shapely outside Blender.
- **Forbidden:** material-paint top renders, pixel colour masks, contour tracing of PNGs,
  hard-coded intent rectangles. POC V01 measured this method at wood IoU 0.82 / tile IoU 0.77,
  one room missed entirely, Hausdorff error up to 4.4 m (`docs/skills_upgrade_poc_v01/`).
- Walls are subtracted from zones using the CAD base, not the model's wall meshes.
- Run `scripts/zone_qa.py` on every zone set: no overlaps > 0.01 m², every gap > 0.3 m²
  either filled from enclosed-interior geometry or listed as HOLD. Model floor gaps are
  common (door vestibules, bay sills); fill them from wall-enclosed interior, never by guessing.
- Material comes from the model material name. Owner overrides are recorded with
  status `OWNER_REVIEW` until confirmed; a recommendation is not a signed decision.

## Sheet output

- Model space, 1:1 mm, `$INSUNITS=4`, DXF R2010 (`AC1024`).
- Frame and title block in model space scaled ×50 on layer `A-FRAME` (A1 border 42050×29700).
  Paper-space viewports rendered blank in QCAD 3.33; do not depend on them.
- Text style `gbenor.shx` + bigfont `gbcbig.shx`. No absolute font paths. (`txt.shx`+`hztxt.shx`
  showed `??` in QCAD; verified in `QCAD_VERIFY_V01.md`.)
- Text heights at 1:50: 175 (3.5 mm), 125 (2.5 mm), titles 300.
- Finish to an issue copy with the repo's `publish_dxf.py` (post-processes fonts, frame, R2010, PDF).

## Automated QA gate (run on every issued sheet)

```bash
python scripts/dxf_sheet_qa.py SHEET.issue.dxf --src SHEET.dxf --json SHEET.qa.json
```

Checks DXF version, `ezdxf audit`, units, portable fonts, CJK-capable styles, no paper-space
viewport dependency, A1 frame at scale, content inside frame, entity count preserved.
PASS is file-level only. Visual review in QCAD (or the PDF) is still required.

## Sheet-specific rules

- **A202 floor**: wood laying direction stated; tile module from the actual spec, centred per
  room with the start point marked; threshold stone only where material or level changes, or at
  wet-room doors. Accessible (elderly) bathrooms: no raised threshold — flag `HOLD` until the
  drainage/level solution is confirmed.
- **A201 ceiling**: soffit levels from ceiling meshes; finished level = soffit − drop; draw the
  high/low step line where the two ceiling meshes share a boundary; zones with clear height below
  the agreed minimum stay at original soffit (no new drop) and are flagged `SITE_VERIFY_REQUIRED`.
- Lighting and overhead MEP: follow `references/lighting-and-mep-review.md`.

## Acceptance labels

Use `PRELIMINARY_DESIGN_PASS` (design intent correct, fit for a contractor to develop) and
`SITE_VERIFY_REQUIRED` (dimensions, structure, services need site or professional checks).
Never label a sheet construction-ready. Structural demolition, unverified dimensions, ceiling
void capacity, accessible-bathroom thresholds and unresolved zone gaps/overlaps are `HOLD`.
