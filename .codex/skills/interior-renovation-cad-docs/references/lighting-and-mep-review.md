# Lighting placement and overhead MEP review

A sheet and its QA can show that a layout is *consistent*. They cannot show that it is
*buildable*. Ceiling-void capacity, structure, code clearances and drainage need site checks or
the responsible trade's sign-off. Mark those items `SITE_VERIFY_REQUIRED` or `HOLD`.

## Lighting points

Export every fixture as data before drawing it, so the same list feeds A201, A302 and a Blender
preview:

`lighting_points.json/csv` fields: `id, room, layer(base|task|accent), type, x, y, z_abs,
mount(recessed|surface|track|cove|wall), cct_k, beam_deg, lumen, circuit, switch_id, status`.

- `z_abs` = finished floor level + finished ceiling height (split levels: lower +0 / upper +450).
- CCT within the owner range (C-Type: 3000–4000 K). State it per point, not per sheet.
- Purpose checks: task lights over the real work surface (counter, desk, vanity mirror bbox);
  bedside lights outside the bed bbox; strip lights parallel to the cabinet run; furniture lamps
  (desk/floor) are not ceiling points.
- Spacing sanity: downlights roughly 1.0–1.5 × mounting height apart, ≥ 300–500 mm from walls
  unless they are deliberate wall-washers. Treat these as review prompts, not rules.
- Preview in Blender only through a *separate* scene or copy that imports the JSON. Never write
  points into a frozen model.

## Overhead MEP routing (走顶)

Draw routing as a *schematic* on separate layers (`M-PLUM-COLD`, `M-PLUM-HOT`, `E-POWER`,
`E-DATA`), each run ending at a marked vertical drop.

Review checklist (each item must be answered on the sheet or listed as open):

1. **Void depth**: available drop (e.g. 150 mm) minus joist/keel depth minus fixture can depth.
   Compare against the largest pipe bundle and its insulation. If not measured → `SITE_VERIFY_REQUIRED`.
2. **Crossings**: list every location where water crosses power/data; water runs below power,
   or use a stated separation. Mark crossings on the sheet.
3. **Fixture conflicts**: no recessed fixture or access panel directly on a pipe run; keep access
   panels at valves, junctions and manifolds.
4. **Vertical drops**: every point fed from the ceiling needs a drop path. With a "no wall
   chasing" constraint, drops go in partition voids, furniture backs, surface trunking or
   boxing-out. Name which one. Never fall back to a wall chase silently.
5. **Beams and step lines**: runs crossing the high/low ceiling step or a beam need a stated
   detail or stay `HOLD`.
6. **Out of scope**: gravity drainage cannot route through the ceiling of the same floor. List
   drainage as `OUT_OF_SCOPE` unless the owner provides a solution.

## Method sources

Triage and guardrail language adapted from `constructelligence-lab/construction-agent-skills`
(`mep-coordination-clash-triage`, `constructability-risk-review`), CC BY 4.0. Clash resolution
is a design decision; clearances come from the specification, not from a model's suggestion.
