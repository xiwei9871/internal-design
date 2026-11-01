---
name: residential-interior-design-principles
description: Review and improve a real home's interior design room by room — function, furniture layout, ergonomics and circulation, elderly/child safety, lighting layers and glare, floor finishes and wet-area detailing, buildability. Reads actual furniture and fixture coordinates, then proposes keep / move / add / remove changes with reasons. Use for design-intent drafts handed to a design and build team; pairs with china-residential-design-code for clause references. Not a compliance certificate.
---

# Residential Interior Design Principles

Goal: give design judgement on a real room, not a checklist. Every finding names the room, the
object or point involved (with coordinates), what goes wrong for the person using it, and a
concrete change. Code clauses come only from `china-residential-design-code`; everything else here
is professional practice and must be labelled as such.

## Inputs to read first

- Room zones and levels (e.g. `data/a202_zones.json`), ceiling zones (`data/a201_ceiling_zones.json`)
- Real furniture/fixture footprints and heights from the model inventory — beds, wardrobes,
  desks, counters, wall cabinets, mirrors, showers, sofas, TV consoles
- Who uses each room (owner brief): e.g. elderly mother's bedroom, owner couple, guest, study
- Owner-approved decisions (never undo them; flag conflicts instead)

## How to review (per room)

1. **Name the activities** at each place: sleep, dress, read in bed, work at desk, cook, wash,
   watch TV, dine, pass through at night.
2. **Map each activity to real objects**: the bed's head side (from bedside tables/headboard), the
   desk, the counter run under wall cabinets, the mirror. Do not guess positions the model gives.
3. **Check the design against the activity** using the principles below; record evidence as
   coordinates and distances.
4. **Propose**: keep / move (to x,y) / add / remove / convert type, each with a reason tied to the
   activity. Never remove items just to reduce counts.
5. **Mark the boundary**: what needs product data (IES/LDT, COF, IP rating), site survey, or a
   licensed designer/electrician to decide.

## Principles (professional practice — not code)

### Space, furniture, circulation
- Keep a clear path from each bed side to the door and bathroom; note the narrowest gap.
- Full-height storage (top within ~600 of the ceiling) occupies that ceiling area: no downlight,
  access panel or diffuser above it.
- Furniture facing a screen or mirror defines where light must and must not be.

### Elderly and child safety
- Night route bed → bathroom: continuous low-level light (plinth, low wall or sensor light),
  switched without walking in the dark (bedside switch or presence sensor), low output, warm end
  of the owner's colour range. No raised thresholds on that route.
- Grab rails or blocking beside WC and shower; slip-resistant wet floors; rounded corners where
  the route passes furniture.
- Avoid glare when lying down: no downlight directly above the bed or the pillow zone.

### Lighting layers and visual comfort
- Four layers per room: **base** (even general light), **task** (desk, counter, mirror, bedside
  reading), **accent** (wall-wash, cove, display), **night/orientation**.
- Task light goes where the eyes and hands are, and in front of the person, not behind: a ceiling
  light behind a person at a counter or desk throws their shadow onto the work.
- Kitchen counters under wall cabinets: under-cabinet linear light; ceiling lights above wall
  cabinets do not reach the counter.
- Mirror lighting lights the face from the front/sides; an overhead light alone shadows the face.
- TV walls: avoid bright sources reflected in the screen; prefer dimmable wall-wash beside the TV.
- Practice ranges (rules of thumb, verify with photometry): downlight spacing ≈ 1.0–1.5 × mounting
  height above the work plane; 300–600 mm from walls unless deliberately washing them.
- Control by scene: separate circuits for base, task, accent and night; two-way switching at
  bedroom door and bed.
- Never state illuminance or glare compliance without luminaire photometric files and surface
  reflectances. Lumen counts are not evidence.

### Floors, wet areas, maintenance
- Wet floors: slip resistance from product data; tile size follows the fall to the drain.
- Transitions: same-level joins where possible; where materials meet, a defined edge profile.
- Access: valves, manifolds and junctions need an access panel the user can reach.

### Buildability and boundaries
- Every point that a trade will build must have a source: model object, survey CAD, or owner
  decision. Points proposed by review are marked `PROPOSED` until the owner confirms.
- Conflicts between model and survey CAD are reported, not resolved by editing frozen sources.
- Bathroom electrical zones, structure, drainage and ceiling void depth are decided by the
  responsible professional; the review only flags them.

## Output

Per room: activities → findings (evidence, impact) → changes (keep/move/add/remove with reason)
→ open items (data / site / professional). Then a summary table old vs new.
Label results `FUNCTIONAL_DESIGN_REVIEW`; this skill has not been validated by a controlled A/B test.

See `references/lighting-review-procedure.md` for the lighting review data checks.

Organisation adapted from `Abhinavbwj/Skills-Architects` (MIT; topic structure only, no numbers
copied) and guardrail wording from `constructelligence-lab/construction-agent-skills` (CC BY 4.0).
