# V5 corner repair and requested follow-up

Primary task: fix true L/T missing wall quadrants, then freeze corrected house geometric baseline. User also clarified former cloakroom/current study SOUTH OPENING is intentional as-is; do not fill it. Future secondary bath must be two separate options, both south entrance: sliding vs inward hinged. Black solid original walls no demolition; white walls modifiable.

V4 remains source, all pins MATCH. V4_JUNCTION_REFERENCE.json exports actual closed skin and113 authored wall bands. CORNER_REPAIR_REGISTER.json:56 candidate joins,26 missing sites,34 height-specific patches. Includes window lower/header corners. Intended study opening excluded. Bespoke D107 angled return above FFL preserved.

Next: build V5 from actualV4 skin + registered patches, no global dilation; verify void-before/solid-after probes, outside-patch surface invariants, all openings and furniture. Render fixed before/after evidence; freeze HOUSE_BASE_GEOMETRY_V1 after passing.

Bath planning facts: inner room roughly x9200–11400/y4700–6450; existing bedroom wardrobe x9863.625–11363.625/y3853.28125–4453.28125 H2200. Bedroom-side hanging slider conflicts with that wardrobe's rear clearance. Need compare bathroom-side sliding vs inward swing using same geometry/fixtures, keeping original black walls/stub. Partial west wall near D107 must not be blindly made rectangular if it collides with the angled door. Manufacturer basin600x400 reference verified from Lusso official product; other sanitary references research pending.

Skills: iterative-refinement critic/repair/recheck ledger; space-planning and residential design. User explicitly prescribed and authorized two comparison concepts, not installation. All output images filesystem/paths-only.

## Base freeze and next design decision

`HOUSE_BASE_GEOMETRY_V1.blend` is frozen from V5 after 26 corner repairs; V5 QA PASS. Current-study south opening stays open. Secondary-bath alternatives are documented separately in `../secondary_bath_options/OPTION_SPEC.md`: A south sliding (recommended), B south inward hinged. No bath option has been written into the base.
