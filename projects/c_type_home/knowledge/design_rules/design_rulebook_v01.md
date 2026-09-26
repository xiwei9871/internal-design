# Residential Design Rulebook v0.1

This rulebook is a planning reference for the C-type home. It separates general guidance from project principles and local-code checks.

**Jurisdiction:** unconfirmed. US or other foreign guidance is reference material only and is never silently promoted to mandatory project code.

## Coverage

| Category | Rules |
|---|---:|
| aging_in_place | 10 |
| bathroom | 10 |
| bedroom | 10 |
| child_friendly | 10 |
| circulation | 10 |
| dining | 10 |
| kitchen | 10 |
| living | 10 |
| storage | 10 |
| study | 10 |

## Rule fields

Numeric values are planning targets in millimetres. `TO_VERIFY_LOCAL_CODE` means a local authority or selected product must be checked before a compliance claim. `HARD_PROJECT_CONSTRAINT` and `PROJECT_PREFERENCE` are kept visible here only for queryability; the authoritative project-specific list is in `project_design_principles.json`.

## aging_in_place

### AGE-CIR-001 — main route

- **Type / priority:** `TECHNICAL_GUIDELINE` / `HIGH`
- **Statement:** Design the primary daily route so an older adult can walk with a helper or mobility aid without a furniture pinch point.
- **Planning target:** min 900 mm, preferred 1100 mm
- **Applies when:** daily_route
- **Tags:** aging-in-place, clear-circulation
- **Source:** [SRC-AARP-HOMEFIT](https://www.aarp.org/livable-communities/info-2020/homefit-guide.html) — general_reference
- **Notes:** Use as a design check; verify the actual room, product and local requirements.

### AGE-CIR-002 — future mobility width

- **Type / priority:** `BEST_PRACTICE` / `HIGH`
- **Statement:** Where future wheelchair or power-chair use is a project goal, test wider route segments instead of only the minimum walking route.
- **Planning target:** min 1100 mm, preferred 1200 mm
- **Applies when:** future_wheelchair
- **Tags:** aging-in-place, step-free-route
- **Source:** [SRC-PRACTICE-ERGONOMICS](https://www.archdaily.com/tag/interior-design) — general_reference
- **Notes:** Use as a design check; verify the actual room, product and local requirements.

### AGE-TURN-003 — turning area

- **Type / priority:** `BEST_PRACTICE` / `HIGH`
- **Statement:** Reserve a turning test area at key changes of direction, especially near bathroom and bedroom entries.
- **Planning target:** min 1500 mm
- **Applies when:** future_wheelchair, turning
- **Tags:** aging-in-place, accessible-bathroom
- **Source:** [SRC-PRACTICE-ERGONOMICS](https://www.archdaily.com/tag/interior-design) — general_reference
- **Notes:** Use as a design check; verify the actual room, product and local requirements.

### AGE-DOOR-004 — clear door opening

- **Type / priority:** `TO_VERIFY_LOCAL_CODE` / `HIGH`
- **Statement:** Confirm local clear-opening and maneuvering-side requirements for doors serving the aging-in-place route.
- **Planning target:** min 810 mm
- **Applies when:** door, future_wheelchair
- **Tags:** aging-in-place, step-free-route
- **Source:** [SRC-ADA-2010-REFERENCE](https://www.ada.gov/law-and-regs/design-standards/2010-stds/) — local_unconfirmed
- **Notes:** 810 mm is a reference target only; verify local code and door hardware.

### AGE-THR-005 — thresholds

- **Type / priority:** `TO_VERIFY_LOCAL_CODE` / `HIGH`
- **Statement:** Measure and confirm each level change, threshold and ramp slope before treating the route as accessible.
- **Planning target:** min 0 mm
- **Applies when:** split_level, ramp
- **Tags:** aging-in-place, step-free-route, split-level
- **Source:** [SRC-ADA-2010-REFERENCE](https://www.ada.gov/law-and-regs/design-standards/2010-stds/) — local_unconfirmed
- **Notes:** The existing level delta and ramp are explicitly TO_VERIFY in the project record.

### AGE-HDW-006 — hardware

- **Type / priority:** `BEST_PRACTICE` / `MEDIUM`
- **Statement:** Prefer lever handles and controls that can be operated without tight grasping or twisting.
- **Planning target:** qualitative
- **Applies when:** aging_in_place
- **Tags:** aging-in-place
- **Source:** [SRC-PRACTICE-ERGONOMICS](https://www.archdaily.com/tag/interior-design) — general_reference
- **Notes:** Use as a design check; verify the actual room, product and local requirements.

### AGE-BTH-007 — bathroom backing

- **Type / priority:** `TECHNICAL_GUIDELINE` / `HIGH`
- **Statement:** Coordinate structural backing for grab rails and future supports before bathroom finishes are closed.
- **Planning target:** qualitative
- **Applies when:** aging_in_place
- **Tags:** aging-in-place, accessible-bathroom
- **Source:** [SRC-PRACTICE-ERGONOMICS](https://www.archdaily.com/tag/interior-design) — general_reference
- **Notes:** Use as a design check; verify the actual room, product and local requirements.

### AGE-BTH-008 — seated shower

- **Type / priority:** `BEST_PRACTICE` / `HIGH`
- **Statement:** Provide a shower layout that can accept a stable seat and reachable controls without blocking the entry.
- **Planning target:** min 900 mm
- **Applies when:** aging_in_place, shower
- **Tags:** aging-in-place, accessible-bathroom
- **Source:** [SRC-PRACTICE-ERGONOMICS](https://www.archdaily.com/tag/interior-design) — general_reference
- **Notes:** Use as a design check; verify the actual room, product and local requirements.

### AGE-LGT-009 — lighting continuity

- **Type / priority:** `BEST_PRACTICE` / `MEDIUM`
- **Statement:** Keep lighting even along night routes and avoid abrupt glare or shadow at steps and bathroom entries.
- **Planning target:** qualitative
- **Applies when:** night_route
- **Tags:** aging-in-place, clear-circulation
- **Source:** [SRC-PRACTICE-ERGONOMICS](https://www.archdaily.com/tag/interior-design) — general_reference
- **Notes:** Use as a design check; verify the actual room, product and local requirements.

### AGE-LEV-010 — level delta

- **Type / priority:** `HARD_PROJECT_CONSTRAINT` / `HIGH`
- **Statement:** Do not label the assisted or power-wheelchair route as compliant until the actual level delta and slope are field measured.
- **Planning target:** qualitative
- **Applies when:** split_level, ramp
- **Tags:** aging-in-place, step-free-route, split-level
- **Source:** [SRC-C-TYPE-BRIEF](https://github.com/xiwei9871/internal-design) — project
- **Notes:** Current project data records owner <=350 mm versus CAD approximately 400 mm; both remain provisional.

## bathroom

### BTH-WC-001 — WC front clearance

- **Type / priority:** `TECHNICAL_GUIDELINE` / `HIGH`
- **Statement:** Keep a clear approach in front of the WC for transfer, cleaning and assisted use.
- **Planning target:** min 600 mm, preferred 750 mm
- **Applies when:** wc
- **Tags:** aging-in-place, accessible-bathroom
- **Source:** [SRC-PRACTICE-ERGONOMICS](https://www.archdaily.com/tag/interior-design) — general_reference
- **Notes:** Use as a design check; verify the actual room, product and local requirements.

### BTH-WC-002 — WC side clearance

- **Type / priority:** `TECHNICAL_GUIDELINE` / `HIGH`
- **Statement:** Check side clearance beside the WC against the user's transfer method and local requirements.
- **Planning target:** min 380 mm, preferred 450 mm
- **Applies when:** wc, transfer
- **Tags:** aging-in-place, accessible-bathroom
- **Source:** [SRC-PRACTICE-ERGONOMICS](https://www.archdaily.com/tag/interior-design) — general_reference
- **Notes:** Use as a design check; verify the actual room, product and local requirements.

### BTH-VAN-003 — vanity front

- **Type / priority:** `TECHNICAL_GUIDELINE` / `HIGH`
- **Statement:** Keep a clear standing or seated approach in front of the vanity.
- **Planning target:** min 750 mm, preferred 900 mm
- **Applies when:** vanity
- **Tags:** aging-in-place, accessible-bathroom
- **Source:** [SRC-PRACTICE-ERGONOMICS](https://www.archdaily.com/tag/interior-design) — general_reference
- **Notes:** Use as a design check; verify the actual room, product and local requirements.

### BTH-SHW-004 — shower footprint

- **Type / priority:** `BEST_PRACTICE` / `HIGH`
- **Statement:** Use a shower footprint large enough for safe entry, turning and a future seat when aging-in-place is a priority.
- **Planning target:** qualitative; target [900, 1200] mm
- **Applies when:** shower, aging_in_place
- **Tags:** aging-in-place, accessible-bathroom
- **Source:** [SRC-PRACTICE-ERGONOMICS](https://www.archdaily.com/tag/interior-design) — general_reference
- **Notes:** Use as a design check; verify the actual room, product and local requirements.

### BTH-AGE-005 — shower support

- **Type / priority:** `TO_VERIFY_LOCAL_CODE` / `HIGH`
- **Statement:** Confirm local requirements and backing for grab rails, a seat and controls before closing bathroom walls.
- **Planning target:** qualitative
- **Applies when:** aging_in_place, shower
- **Tags:** aging-in-place, accessible-bathroom
- **Source:** [SRC-ADA-2010-REFERENCE](https://www.ada.gov/law-and-regs/design-standards/2010-stds/) — local_unconfirmed
- **Notes:** The ADA source is a US reference only; local jurisdiction is not confirmed.

### BTH-CIR-006 — turning area

- **Type / priority:** `BEST_PRACTICE` / `HIGH`
- **Statement:** Where future wheelchair use is a stated goal, test a turning area rather than relying on a narrow aisle.
- **Planning target:** min 1500 mm
- **Applies when:** future_wheelchair
- **Tags:** aging-in-place, accessible-bathroom
- **Source:** [SRC-PRACTICE-ERGONOMICS](https://www.archdaily.com/tag/interior-design) — general_reference
- **Notes:** Use as a design check; verify the actual room, product and local requirements.

### BTH-DOOR-007 — door swing

- **Type / priority:** `TECHNICAL_GUIDELINE` / `HIGH`
- **Statement:** Keep the bathroom door swing out of the transfer, shower entry and only clear aisle.
- **Planning target:** min 750 mm
- **Applies when:** near_door
- **Tags:** accessible-bathroom, clear-circulation
- **Source:** [SRC-PRACTICE-ERGONOMICS](https://www.archdaily.com/tag/interior-design) — general_reference
- **Notes:** Use as a design check; verify the actual room, product and local requirements.

### BTH-SAF-008 — threshold

- **Type / priority:** `TO_VERIFY_LOCAL_CODE` / `HIGH`
- **Statement:** Confirm local threshold, waterproofing and drainage requirements before fixing the shower build-up.
- **Planning target:** qualitative
- **Applies when:** shower, wet_area
- **Tags:** aging-in-place, accessible-bathroom
- **Source:** [SRC-ADA-2010-REFERENCE](https://www.ada.gov/law-and-regs/design-standards/2010-stds/) — local_unconfirmed
- **Notes:** Exact threshold and drainage rules depend on the local authority and selected system.

### BTH-SAF-009 — slip and contrast

- **Type / priority:** `BEST_PRACTICE` / `MEDIUM`
- **Statement:** Use slip-resistant wet-area finishes and enough visual contrast to distinguish fixtures and floor edges.
- **Planning target:** qualitative
- **Applies when:** aging_in_place
- **Tags:** aging-in-place, accessible-bathroom
- **Source:** [SRC-PRACTICE-ERGONOMICS](https://www.archdaily.com/tag/interior-design) — general_reference
- **Notes:** Use as a design check; verify the actual room, product and local requirements.

### BTH-MNT-010 — maintenance access

- **Type / priority:** `TECHNICAL_GUIDELINE` / `MEDIUM`
- **Statement:** Reserve access to shut-offs, traps, drains and exhaust equipment without removing fixed cabinetry.
- **Planning target:** min 600 mm
- **Applies when:** services
- **Tags:** accessible-bathroom
- **Source:** [SRC-PRACTICE-ERGONOMICS](https://www.archdaily.com/tag/interior-design) — general_reference
- **Notes:** Use as a design check; verify the actual room, product and local requirements.

## bedroom

### BED-CIR-001 — bed-side route

- **Type / priority:** `TECHNICAL_GUIDELINE` / `HIGH`
- **Statement:** Keep a usable clear route beside the bed rather than forcing entry across the bed end.
- **Planning target:** min 750 mm, preferred 900 mm
- **Applies when:** bed_access
- **Tags:** clear-circulation, elderly-bedroom
- **Source:** [SRC-PRACTICE-ERGONOMICS](https://www.archdaily.com/tag/interior-design) — general_reference
- **Notes:** Use as a design check; verify the actual room, product and local requirements.

### BED-AGE-002 — both-side access

- **Type / priority:** `BEST_PRACTICE` / `HIGH`
- **Statement:** For an aging-in-place bedroom, prefer access on both sides of the bed or document the assisted side explicitly.
- **Planning target:** min 900 mm
- **Applies when:** aging_in_place, caregiver_access
- **Tags:** aging-in-place, elderly-bedroom
- **Source:** [SRC-PRACTICE-ERGONOMICS](https://www.archdaily.com/tag/interior-design) — general_reference
- **Notes:** Use as a design check; verify the actual room, product and local requirements.

### BED-CIR-003 — bed-foot route

- **Type / priority:** `TECHNICAL_GUIDELINE` / `HIGH`
- **Statement:** Keep the bed foot clear enough for turning, making the bed and passing to storage.
- **Planning target:** min 900 mm, preferred 1100 mm
- **Applies when:** bed_foot_route
- **Tags:** clear-circulation
- **Source:** [SRC-PRACTICE-ERGONOMICS](https://www.archdaily.com/tag/interior-design) — general_reference
- **Notes:** Use as a design check; verify the actual room, product and local requirements.

### BED-STOR-004 — wardrobe operation

- **Type / priority:** `TECHNICAL_GUIDELINE` / `HIGH`
- **Statement:** Keep a clear standing zone in front of wardrobe doors and drawers.
- **Planning target:** min 900 mm, preferred 1000 mm
- **Applies when:** wardrobe_or_drawer
- **Tags:** storage, clear-circulation
- **Source:** [SRC-PRACTICE-ERGONOMICS](https://www.archdaily.com/tag/interior-design) — general_reference
- **Notes:** Use as a design check; verify the actual room, product and local requirements.

### BED-DOOR-005 — door swing

- **Type / priority:** `TECHNICAL_GUIDELINE` / `HIGH`
- **Statement:** Keep bedroom door swings from colliding with the bed, wardrobe or the only bed-side route.
- **Planning target:** min 800 mm
- **Applies when:** near_door
- **Tags:** clear-circulation
- **Source:** [SRC-PRACTICE-ERGONOMICS](https://www.archdaily.com/tag/interior-design) — general_reference
- **Notes:** Use as a design check; verify the actual room, product and local requirements.

### BED-WIN-006 — window access

- **Type / priority:** `BEST_PRACTICE` / `MEDIUM`
- **Statement:** Keep at least one usable approach to an operable window for daylight, ventilation and maintenance.
- **Planning target:** min 750 mm
- **Applies when:** window_present
- **Tags:** daylight, clear-circulation
- **Source:** [SRC-PRACTICE-ERGONOMICS](https://www.archdaily.com/tag/interior-design) — general_reference
- **Notes:** Use as a design check; verify the actual room, product and local requirements.

### BED-ERG-007 — bedside reach

- **Type / priority:** `BEST_PRACTICE` / `MEDIUM`
- **Statement:** Place lighting, call controls and a landing surface within seated reach at the assisted bed side.
- **Planning target:** min 600 mm
- **Applies when:** aging_in_place
- **Tags:** aging-in-place, elderly-bedroom
- **Source:** [SRC-PRACTICE-ERGONOMICS](https://www.archdaily.com/tag/interior-design) — general_reference
- **Notes:** Use as a design check; verify the actual room, product and local requirements.

### BED-ERG-008 — headboard wall

- **Type / priority:** `BEST_PRACTICE` / `MEDIUM`
- **Statement:** Prefer a stable wall behind the headboard and keep a window opening free from headboard conflicts.
- **Planning target:** qualitative
- **Applies when:** bed_head
- **Tags:** elderly-bedroom, daylight
- **Source:** [SRC-PRACTICE-ERGONOMICS](https://www.archdaily.com/tag/interior-design) — general_reference
- **Notes:** Use as a design check; verify the actual room, product and local requirements.

### BED-FLEX-009 — flexible clear zone

- **Type / priority:** `PROJECT_PREFERENCE` / `MEDIUM`
- **Statement:** Retain a clear zone that can accept a cot, luggage, caregiver chair or temporary child use.
- **Planning target:** min 1800 mm
- **Applies when:** periodic_family
- **Tags:** flexible-living, child-friendly
- **Source:** [SRC-PRACTICE-ERGONOMICS](https://www.archdaily.com/tag/interior-design) — general_reference
- **Notes:** Use as a design check; verify the actual room, product and local requirements.

### BED-AGE-010 — route to bathroom

- **Type / priority:** `TECHNICAL_GUIDELINE` / `HIGH`
- **Statement:** Keep the bedroom-to-bathroom route direct, well lit and free from loose furniture.
- **Planning target:** min 900 mm, preferred 1100 mm
- **Applies when:** ensuite_or_night_route
- **Tags:** aging-in-place, clear-circulation
- **Source:** [SRC-PRACTICE-ERGONOMICS](https://www.archdaily.com/tag/interior-design) — general_reference
- **Notes:** Use as a design check; verify the actual room, product and local requirements.

## child_friendly

### CHD-ACT-001 — activity core

- **Type / priority:** `BEST_PRACTICE` / `HIGH`
- **Statement:** Give children a visible, furniture-light activity area that does not occupy the only adult route.
- **Planning target:** min 2500 mm, preferred 3000 mm
- **Applies when:** child_activity
- **Tags:** child-friendly, furniture-free-core
- **Source:** [SRC-PRACTICE-ERGONOMICS](https://www.archdaily.com/tag/interior-design) — general_reference
- **Notes:** Use as a design check; verify the actual room, product and local requirements.

### CHD-VIS-002 — adult sightline

- **Type / priority:** `BEST_PRACTICE` / `HIGH`
- **Statement:** Keep a direct sightline from everyday seating or dining to the child activity area.
- **Planning target:** qualitative
- **Applies when:** child_activity, supervision
- **Tags:** child-friendly, visual-connection
- **Source:** [SRC-PRACTICE-ERGONOMICS](https://www.archdaily.com/tag/interior-design) — general_reference
- **Notes:** Use as a design check; verify the actual room, product and local requirements.

### CHD-CIR-003 — play route

- **Type / priority:** `TECHNICAL_GUIDELINE` / `HIGH`
- **Statement:** Keep the child activity edge outside the main walking route and away from door swings.
- **Planning target:** min 900 mm
- **Applies when:** child_activity
- **Tags:** child-friendly, clear-circulation
- **Source:** [SRC-PRACTICE-ERGONOMICS](https://www.archdaily.com/tag/interior-design) — general_reference
- **Notes:** Use as a design check; verify the actual room, product and local requirements.

### CHD-FUR-004 — stable furniture

- **Type / priority:** `BEST_PRACTICE` / `HIGH`
- **Statement:** Use stable, anti-tip furniture and anchor tall storage where children can reach it.
- **Planning target:** qualitative
- **Applies when:** child_present
- **Tags:** child-friendly, storage
- **Source:** [SRC-PRACTICE-ERGONOMICS](https://www.archdaily.com/tag/interior-design) — general_reference
- **Notes:** Use as a design check; verify the actual room, product and local requirements.

### CHD-FUR-005 — edge safety

- **Type / priority:** `BEST_PRACTICE` / `MEDIUM`
- **Statement:** Prefer protected or rounded exposed corners on furniture at child head and shoulder height.
- **Planning target:** qualitative
- **Applies when:** child_present
- **Tags:** child-friendly
- **Source:** [SRC-PRACTICE-ERGONOMICS](https://www.archdaily.com/tag/interior-design) — general_reference
- **Notes:** Use as a design check; verify the actual room, product and local requirements.

### CHD-STOR-006 — reachable toy storage

- **Type / priority:** `PROJECT_PREFERENCE` / `MEDIUM`
- **Statement:** Keep daily toy and activity storage within a reachable band while keeping heavy or hazardous items locked.
- **Planning target:** max 1200 mm
- **Applies when:** child_activity
- **Tags:** child-friendly, storage
- **Source:** [SRC-PRACTICE-ERGONOMICS](https://www.archdaily.com/tag/interior-design) — general_reference
- **Notes:** Use as a design check; verify the actual room, product and local requirements.

### CHD-SAF-007 — outlet safety

- **Type / priority:** `TO_VERIFY_LOCAL_CODE` / `MEDIUM`
- **Statement:** Confirm local electrical and outlet protection requirements for areas used by children.
- **Planning target:** qualitative
- **Applies when:** child_present
- **Tags:** child-friendly
- **Source:** [SRC-CPSC-HOME-SAFETY](https://www.cpsc.gov/Safety-Education/Safety-Guides) — local_unconfirmed
- **Notes:** Local electrical rules are not established in this project phase.

### CHD-SAF-008 — blind corners

- **Type / priority:** `BEST_PRACTICE` / `MEDIUM`
- **Statement:** Avoid sharp visual blind corners where children enter a route from the activity area.
- **Planning target:** min 900 mm
- **Applies when:** child_activity
- **Tags:** child-friendly, visual-connection
- **Source:** [SRC-PRACTICE-ERGONOMICS](https://www.archdaily.com/tag/interior-design) — general_reference
- **Notes:** Use as a design check; verify the actual room, product and local requirements.

### CHD-CLN-009 — cleanable boundary

- **Type / priority:** `BEST_PRACTICE` / `LOW`
- **Statement:** Choose a cleanable, replaceable edge for messy activity rather than hard-wiring a fragile finish into the main route.
- **Planning target:** qualitative
- **Applies when:** child_activity
- **Tags:** child-friendly, flexible-living
- **Source:** [SRC-PRACTICE-ERGONOMICS](https://www.archdaily.com/tag/interior-design) — general_reference
- **Notes:** Use as a design check; verify the actual room, product and local requirements.

### CHD-FLEX-010 — reconfiguration

- **Type / priority:** `PROJECT_PREFERENCE` / `MEDIUM`
- **Statement:** Keep at least one furniture arrangement that can change as a child grows without moving walls.
- **Planning target:** min 900 mm
- **Applies when:** periodic_family
- **Tags:** child-friendly, flexible-living
- **Source:** [SRC-PRACTICE-ERGONOMICS](https://www.archdaily.com/tag/interior-design) — general_reference
- **Notes:** Use as a design check; verify the actual room, product and local requirements.

## circulation

### CIR-PRI-001 — primary path

- **Type / priority:** `TECHNICAL_GUIDELINE` / `HIGH`
- **Statement:** Keep the primary path continuous, readable and free from furniture overlap.
- **Planning target:** min 900 mm, preferred 1100 mm
- **Applies when:** daily_route
- **Tags:** clear-circulation
- **Source:** [SRC-PRACTICE-ERGONOMICS](https://www.archdaily.com/tag/interior-design) — general_reference
- **Notes:** Use as a design check; verify the actual room, product and local requirements.

### CIR-PRI-002 — preferred path

- **Type / priority:** `BEST_PRACTICE` / `HIGH`
- **Statement:** Prefer a wider path where an older adult, helper or child may meet another person.
- **Planning target:** min 1100 mm, preferred 1200 mm
- **Applies when:** assisted_movement
- **Tags:** clear-circulation, aging-in-place
- **Source:** [SRC-PRACTICE-ERGONOMICS](https://www.archdaily.com/tag/interior-design) — general_reference
- **Notes:** Use as a design check; verify the actual room, product and local requirements.

### CIR-SEC-003 — secondary path

- **Type / priority:** `TECHNICAL_GUIDELINE` / `MEDIUM`
- **Statement:** Keep secondary routes wide enough for a person to pass without turning sideways.
- **Planning target:** min 750 mm, preferred 900 mm
- **Applies when:** secondary_route
- **Tags:** clear-circulation
- **Source:** [SRC-PRACTICE-ERGONOMICS](https://www.archdaily.com/tag/interior-design) — general_reference
- **Notes:** Use as a design check; verify the actual room, product and local requirements.

### CIR-TURN-004 — turning node

- **Type / priority:** `BEST_PRACTICE` / `HIGH`
- **Statement:** At a route change or dead-end, test a turning area rather than assuming a straight width is enough.
- **Planning target:** min 1500 mm
- **Applies when:** turning, future_wheelchair
- **Tags:** aging-in-place, clear-circulation
- **Source:** [SRC-PRACTICE-ERGONOMICS](https://www.archdaily.com/tag/interior-design) — general_reference
- **Notes:** Use as a design check; verify the actual room, product and local requirements.

### CIR-DOOR-005 — door maneuvering

- **Type / priority:** `TECHNICAL_GUIDELINE` / `HIGH`
- **Statement:** Keep door maneuvering space outside the only circulation route and avoid overlapping furniture.
- **Planning target:** min 900 mm
- **Applies when:** door
- **Tags:** clear-circulation
- **Source:** [SRC-PRACTICE-ERGONOMICS](https://www.archdaily.com/tag/interior-design) — general_reference
- **Notes:** Use as a design check; verify the actual room, product and local requirements.

### CIR-PINCH-006 — pinch point

- **Type / priority:** `TECHNICAL_GUIDELINE` / `HIGH`
- **Statement:** Investigate any path segment below 750 mm and do not hide it inside a furniture annotation.
- **Planning target:** min 750 mm
- **Applies when:** narrow_segment
- **Tags:** clear-circulation, aging-in-place
- **Source:** [SRC-PRACTICE-ERGONOMICS](https://www.archdaily.com/tag/interior-design) — general_reference
- **Notes:** Use as a design check; verify the actual room, product and local requirements.

### CIR-CONT-007 — balcony continuity

- **Type / priority:** `BEST_PRACTICE` / `HIGH`
- **Statement:** Keep the path from living space to a currently open balcony continuous; future enclosure is a separate scenario.
- **Planning target:** min 900 mm
- **Applies when:** balcony_connected
- **Tags:** balcony-connected, clear-circulation
- **Source:** [SRC-C-TYPE-BRIEF](https://github.com/xiwei9871/internal-design) — project
- **Notes:** Use as a design check; verify the actual room, product and local requirements.

### CIR-STAIR-008 — stair landing

- **Type / priority:** `TECHNICAL_GUIDELINE` / `HIGH`
- **Statement:** Keep a stable landing at the top and bottom of stairs and prevent furniture from narrowing it.
- **Planning target:** min 900 mm
- **Applies when:** stairs
- **Tags:** split-level, clear-circulation
- **Source:** [SRC-PRACTICE-ERGONOMICS](https://www.archdaily.com/tag/interior-design) — general_reference
- **Notes:** Use as a design check; verify the actual room, product and local requirements.

### CIR-RAMP-009 — alternate route

- **Type / priority:** `HARD_PROJECT_CONSTRAINT` / `HIGH`
- **Statement:** Document the assisted or power-wheelchair route beside the existing stair and keep both routes legible until field verification.
- **Planning target:** min 1100 mm
- **Applies when:** split_level, ramp
- **Tags:** split-level, step-free-route, aging-in-place
- **Source:** [SRC-C-TYPE-BRIEF](https://github.com/xiwei9871/internal-design) — project
- **Notes:** Use as a design check; verify the actual room, product and local requirements.

### CIR-VIS-010 — visual orientation

- **Type / priority:** `BEST_PRACTICE` / `MEDIUM`
- **Statement:** Use lighting, sightlines or a stable edge to make route junctions readable without adding a fixed obstacle.
- **Planning target:** qualitative
- **Applies when:** route_junction
- **Tags:** visual-connection, clear-circulation
- **Source:** [SRC-PRACTICE-ERGONOMICS](https://www.archdaily.com/tag/interior-design) — general_reference
- **Notes:** Use as a design check; verify the actual room, product and local requirements.

## dining

### DIN-TBL-001 — table width

- **Type / priority:** `TECHNICAL_GUIDELINE` / `MEDIUM`
- **Statement:** Use a table width that supports place settings without reducing the circulation strip.
- **Planning target:** min 750 mm, preferred 900 mm
- **Applies when:** daily_dining
- **Tags:** dining-kitchen-extension
- **Source:** [SRC-PRACTICE-ERGONOMICS](https://www.archdaily.com/tag/interior-design) — general_reference
- **Notes:** Use as a design check; verify the actual room, product and local requirements.

### DIN-TBL-002 — four-seat table

- **Type / priority:** `BEST_PRACTICE` / `MEDIUM`
- **Statement:** A compact four-seat table is commonly planned around a 1200 by 750 mm footprint before chair clearances.
- **Planning target:** qualitative; target [1200, 750] mm
- **Applies when:** four_seats
- **Tags:** dual-mode-dining
- **Source:** [SRC-PRACTICE-ERGONOMICS](https://www.archdaily.com/tag/interior-design) — general_reference
- **Notes:** Use as a design check; verify the actual room, product and local requirements.

### DIN-TBL-003 — six-seat table

- **Type / priority:** `BEST_PRACTICE` / `MEDIUM`
- **Statement:** A six-seat table is commonly planned around a 1500 by 800 mm footprint before chair clearances.
- **Planning target:** qualitative; target [1500, 800] mm
- **Applies when:** six_seats
- **Tags:** dual-mode-dining
- **Source:** [SRC-PRACTICE-ERGONOMICS](https://www.archdaily.com/tag/interior-design) — general_reference
- **Notes:** Use as a design check; verify the actual room, product and local requirements.

### DIN-TBL-004 — eight-seat table

- **Type / priority:** `BEST_PRACTICE` / `LOW`
- **Statement:** An eight-seat table is commonly planned around a 1800 by 900 mm footprint before chair clearances.
- **Planning target:** qualitative; target [1800, 900] mm
- **Applies when:** eight_seats
- **Tags:** dual-mode-dining
- **Source:** [SRC-PRACTICE-ERGONOMICS](https://www.archdaily.com/tag/interior-design) — general_reference
- **Notes:** Use as a design check; verify the actual room, product and local requirements.

### DIN-CIR-005 — chair pull-out

- **Type / priority:** `TECHNICAL_GUIDELINE` / `HIGH`
- **Statement:** Allow room to pull a dining chair out and sit without blocking the adjacent path.
- **Planning target:** min 600 mm, preferred 750 mm
- **Applies when:** seated_use
- **Tags:** clear-circulation, dual-mode-dining
- **Source:** [SRC-PRACTICE-ERGONOMICS](https://www.archdaily.com/tag/interior-design) — general_reference
- **Notes:** Use as a design check; verify the actual room, product and local requirements.

### DIN-CIR-006 — passage behind diner

- **Type / priority:** `TECHNICAL_GUIDELINE` / `HIGH`
- **Statement:** Where people pass behind a seated diner, retain a clear passage beyond the chair pull-out zone.
- **Planning target:** min 900 mm, preferred 1000 mm
- **Applies when:** through_route_behind_seats
- **Tags:** clear-circulation
- **Source:** [SRC-PRACTICE-ERGONOMICS](https://www.archdaily.com/tag/interior-design) — general_reference
- **Notes:** Use as a design check; verify the actual room, product and local requirements.

### DIN-CIR-007 — kitchen relationship

- **Type / priority:** `BEST_PRACTICE` / `HIGH`
- **Statement:** Keep a direct, unobstructed path between dining and kitchen work zones.
- **Planning target:** min 1000 mm, preferred 1100 mm
- **Applies when:** open_plan
- **Tags:** dining-kitchen-extension, clear-circulation
- **Source:** [SRC-PRACTICE-ERGONOMICS](https://www.archdaily.com/tag/interior-design) — general_reference
- **Notes:** Use as a design check; verify the actual room, product and local requirements.

### DIN-CIR-008 — door swing conflict

- **Type / priority:** `TECHNICAL_GUIDELINE` / `HIGH`
- **Statement:** Do not let a door swing overlap the table, chair pull-out or the only dining route.
- **Planning target:** min 900 mm
- **Applies when:** near_door
- **Tags:** clear-circulation
- **Source:** [SRC-PRACTICE-ERGONOMICS](https://www.archdaily.com/tag/interior-design) — general_reference
- **Notes:** Use as a design check; verify the actual room, product and local requirements.

### DIN-FAM-009 — child sightline

- **Type / priority:** `BEST_PRACTICE` / `MEDIUM`
- **Statement:** Place the everyday child seat where an adult can see the activity area and kitchen without turning through a door swing.
- **Planning target:** qualitative
- **Applies when:** child_present
- **Tags:** child-friendly, visual-connection
- **Source:** [SRC-PRACTICE-ERGONOMICS](https://www.archdaily.com/tag/interior-design) — general_reference
- **Notes:** Use as a design check; verify the actual room, product and local requirements.

### DIN-FLEX-010 — flexible seating side

- **Type / priority:** `PROJECT_PREFERENCE` / `MEDIUM`
- **Statement:** Keep at least one long side of the table adaptable for a child seat, wheelchair approach or temporary extension.
- **Planning target:** min 900 mm
- **Applies when:** flexible_household
- **Tags:** child-friendly, aging-in-place, dual-mode-dining
- **Source:** [SRC-PRACTICE-ERGONOMICS](https://www.archdaily.com/tag/interior-design) — general_reference
- **Notes:** Use as a design check; verify the actual room, product and local requirements.

## kitchen

### KIT-CIR-001 — single-cook aisle

- **Type / priority:** `TECHNICAL_GUIDELINE` / `HIGH`
- **Statement:** Keep the primary kitchen work aisle clear of doors, stools and loose furniture.
- **Planning target:** min 1000 mm, preferred 1100 mm
- **Applies when:** single_cook
- **Tags:** kitchen-adjacency, clear-circulation
- **Source:** [SRC-NKBA-KITCHEN](https://www.nkba.org/standards-guidelines/kitchen-planning-guidelines/) — general_reference
- **Notes:** Use as a design check; verify the actual room, product and local requirements.

### KIT-CIR-002 — preferred work aisle

- **Type / priority:** `BEST_PRACTICE` / `MEDIUM`
- **Statement:** Prefer a wider work aisle when two people may pass or work at the same time.
- **Planning target:** min 1100 mm, preferred 1200 mm
- **Applies when:** two_cooks
- **Tags:** kitchen-adjacency, clear-circulation
- **Source:** [SRC-NKBA-KITCHEN](https://www.nkba.org/standards-guidelines/kitchen-planning-guidelines/) — general_reference
- **Notes:** Use as a design check; verify the actual room, product and local requirements.

### KIT-CIR-003 — two-cook aisle

- **Type / priority:** `TECHNICAL_GUIDELINE` / `HIGH`
- **Statement:** For opposing work runs, check appliance doors and two-person movement at the same time.
- **Planning target:** min 1200 mm, preferred 1300 mm
- **Applies when:** opposing_runs
- **Tags:** kitchen-adjacency
- **Source:** [SRC-NKBA-KITCHEN](https://www.nkba.org/standards-guidelines/kitchen-planning-guidelines/) — general_reference
- **Notes:** Use as a design check; verify the actual room, product and local requirements.

### KIT-WRK-004 — prep run

- **Type / priority:** `TECHNICAL_GUIDELINE` / `HIGH`
- **Statement:** Provide a usable continuous prep run beside the sink or cooking zone.
- **Planning target:** min 600 mm, preferred 900 mm
- **Applies when:** food_prep
- **Tags:** kitchen-adjacency
- **Source:** [SRC-NKBA-KITCHEN](https://www.nkba.org/standards-guidelines/kitchen-planning-guidelines/) — general_reference
- **Notes:** Use as a design check; verify the actual room, product and local requirements.

### KIT-WRK-005 — sink landing

- **Type / priority:** `TECHNICAL_GUIDELINE` / `MEDIUM`
- **Statement:** Keep a landing area beside the sink for dishes and transfer tasks.
- **Planning target:** min 600 mm
- **Applies when:** sink
- **Tags:** kitchen-adjacency
- **Source:** [SRC-NKBA-KITCHEN](https://www.nkba.org/standards-guidelines/kitchen-planning-guidelines/) — general_reference
- **Notes:** Use as a design check; verify the actual room, product and local requirements.

### KIT-WRK-006 — refrigerator landing

- **Type / priority:** `TECHNICAL_GUIDELINE` / `MEDIUM`
- **Statement:** Provide a landing surface at the refrigerator opening side.
- **Planning target:** min 450 mm
- **Applies when:** refrigerator
- **Tags:** kitchen-adjacency
- **Source:** [SRC-NKBA-KITCHEN](https://www.nkba.org/standards-guidelines/kitchen-planning-guidelines/) — general_reference
- **Notes:** Use as a design check; verify the actual room, product and local requirements.

### KIT-WRK-007 — cooking landing

- **Type / priority:** `TECHNICAL_GUIDELINE` / `MEDIUM`
- **Statement:** Provide a landing surface beside the cooking appliance and confirm heat-safe clearance.
- **Planning target:** min 300 mm
- **Applies when:** hob_or_oven
- **Tags:** kitchen-adjacency
- **Source:** [SRC-NKBA-KITCHEN](https://www.nkba.org/standards-guidelines/kitchen-planning-guidelines/) — general_reference
- **Notes:** Use as a design check; verify the actual room, product and local requirements.

### KIT-SAF-008 — appliance doors

- **Type / priority:** `TECHNICAL_GUIDELINE` / `HIGH`
- **Statement:** Test refrigerator, oven and dishwasher doors against each other and against the main route.
- **Planning target:** min 900 mm
- **Applies when:** appliance_door_open
- **Tags:** kitchen-adjacency, clear-circulation
- **Source:** [SRC-NKBA-KITCHEN](https://www.nkba.org/standards-guidelines/kitchen-planning-guidelines/) — general_reference
- **Notes:** Use as a design check; verify the actual room, product and local requirements.

### KIT-SAF-009 — pinch points

- **Type / priority:** `TECHNICAL_GUIDELINE` / `HIGH`
- **Statement:** Do not create a sub-900 mm pinch point between cabinetry, an island and an open appliance door.
- **Planning target:** min 900 mm
- **Applies when:** island_or_peninsula
- **Tags:** kitchen-adjacency, clear-circulation
- **Source:** [SRC-NKBA-KITCHEN](https://www.nkba.org/standards-guidelines/kitchen-planning-guidelines/) — general_reference
- **Notes:** Use as a design check; verify the actual room, product and local requirements.

### KIT-KEEP-010 — retained cabinetry record

- **Type / priority:** `BEST_PRACTICE` / `HIGH`
- **Statement:** When existing cabinetry is KEEP, record its measured footprint and services before proposing adjacent changes.
- **Planning target:** qualitative
- **Applies when:** existing_cabinetry_keep
- **Tags:** existing-structure, kitchen-adjacency
- **Source:** [SRC-C-TYPE-BRIEF](https://github.com/xiwei9871/internal-design) — project
- **Notes:** This protects the current kitchen cabinet decision without redesigning it.

## living

### LIV-CIRC-001 — primary route

- **Type / priority:** `TECHNICAL_GUIDELINE` / `HIGH`
- **Statement:** Keep the main living route continuously clear for normal walking and assisted movement.
- **Planning target:** min 900 mm, preferred 1100 mm
- **Applies when:** entry_to_living, living_to_stair
- **Tags:** clear-circulation, aging-in-place
- **Source:** [SRC-AARP-HOMEFIT](https://www.aarp.org/livable-communities/info-2020/homefit-guide.html) — general_reference
- **Notes:** Use as a design check; verify the actual room, product and local requirements.

### LIV-CIRC-002 — secondary route

- **Type / priority:** `TECHNICAL_GUIDELINE` / `HIGH`
- **Statement:** Keep a secondary route around the seating group where the plan has more than one approach.
- **Planning target:** min 750 mm, preferred 900 mm
- **Applies when:** two_sided_access
- **Tags:** clear-circulation
- **Source:** [SRC-PRACTICE-ERGONOMICS](https://www.archdaily.com/tag/interior-design) — general_reference
- **Notes:** Use as a design check; verify the actual room, product and local requirements.

### LIV-FLEX-003 — activity core

- **Type / priority:** `BEST_PRACTICE` / `HIGH`
- **Statement:** Reserve a central, furniture-light activity core for children, conversation and temporary setups.
- **Planning target:** min 2500 mm, preferred 3000 mm
- **Applies when:** child_activity, flexible_living
- **Tags:** child-friendly, furniture-free-core, flexible-living
- **Source:** [SRC-PRACTICE-ERGONOMICS](https://www.archdaily.com/tag/interior-design) — general_reference
- **Notes:** Use as a design check; verify the actual room, product and local requirements.

### LIV-FLEX-004 — movable furniture

- **Type / priority:** `PROJECT_PREFERENCE` / `MEDIUM`
- **Statement:** Use movable tables and seats for flexible living instead of fixing every object in the activity core.
- **Planning target:** max 900 mm
- **Applies when:** projector_living, child_activity
- **Tags:** projector-media, child-friendly, flexible-living
- **Source:** [SRC-PRACTICE-ERGONOMICS](https://www.archdaily.com/tag/interior-design) — general_reference
- **Notes:** Use as a design check; verify the actual room, product and local requirements.

### LIV-MEDIA-005 — projector sightline

- **Type / priority:** `TECHNICAL_GUIDELINE` / `HIGH`
- **Statement:** Check projector or laser-TV throw, sightline and glare against the selected device before fixing the media wall.
- **Planning target:** qualitative
- **Applies when:** projector_or_laser_tv
- **Tags:** projector-media, non-tv-centric
- **Source:** [SRC-ENERGY-STAR](https://www.energystar.gov/products/appliances) — general_reference
- **Notes:** Device throw distance is product-specific; verify the selected model.

### LIV-MEDIA-006 — media wall and glazing

- **Type / priority:** `BEST_PRACTICE` / `HIGH`
- **Statement:** Keep media equipment and its viewing axis outside the opening swing and clear route to a balcony or window.
- **Planning target:** min 900 mm
- **Applies when:** balcony_connected
- **Tags:** projector-media, balcony-connected, clear-circulation
- **Source:** [SRC-PRACTICE-ERGONOMICS](https://www.archdaily.com/tag/interior-design) — general_reference
- **Notes:** Use as a design check; verify the actual room, product and local requirements.

### LIV-DIST-007 — viewing distance

- **Type / priority:** `TECHNICAL_GUIDELINE` / `MEDIUM`
- **Statement:** Set viewing distance from the selected image size and device specification, then test the furniture arrangement at full scale.
- **Planning target:** qualitative
- **Applies when:** projector_or_laser_tv
- **Tags:** projector-media
- **Source:** [SRC-ENERGY-STAR](https://www.energystar.gov/products/appliances) — general_reference
- **Notes:** No universal screen distance is assumed.

### LIV-EDGE-008 — edge-loaded furniture

- **Type / priority:** `BEST_PRACTICE` / `HIGH`
- **Statement:** Place large fixed furniture along room edges so the center can support more than one use.
- **Planning target:** qualitative
- **Applies when:** flexible_living
- **Tags:** edge-loaded-furniture, furniture-free-core
- **Source:** [SRC-PRACTICE-ERGONOMICS](https://www.archdaily.com/tag/interior-design) — general_reference
- **Notes:** Use as a design check; verify the actual room, product and local requirements.

### LIV-SOC-009 — social seating

- **Type / priority:** `BEST_PRACTICE` / `MEDIUM`
- **Statement:** Arrange at least two seats to support face-to-face conversation without crossing the primary route.
- **Planning target:** min 900 mm
- **Applies when:** conversation
- **Tags:** clear-circulation, flexible-living
- **Source:** [SRC-PRACTICE-ERGONOMICS](https://www.archdaily.com/tag/interior-design) — general_reference
- **Notes:** Use as a design check; verify the actual room, product and local requirements.

### LIV-BAL-010 — balcony connection

- **Type / priority:** `TECHNICAL_GUIDELINE` / `HIGH`
- **Statement:** Keep the living-to-balcony route continuous and free of fixed furniture; treat a future enclosure as a separate option.
- **Planning target:** min 900 mm, preferred 1100 mm
- **Applies when:** open_balcony
- **Tags:** balcony-connected, clear-circulation
- **Source:** [SRC-C-TYPE-BRIEF](https://github.com/xiwei9871/internal-design) — project
- **Notes:** Current north balcony is open; future enclosure remains proposed.

## storage

### STO-WARD-001 — wardrobe depth

- **Type / priority:** `TECHNICAL_GUIDELINE` / `MEDIUM`
- **Statement:** Use approximately 600 mm depth for a full-depth hanging wardrobe unless the product requires more.
- **Planning target:** min 600 mm, preferred 600 mm
- **Applies when:** hanging_storage
- **Tags:** storage
- **Source:** [SRC-PRACTICE-ERGONOMICS](https://www.archdaily.com/tag/interior-design) — general_reference
- **Notes:** Use as a design check; verify the actual room, product and local requirements.

### STO-WARD-002 — wardrobe front

- **Type / priority:** `TECHNICAL_GUIDELINE` / `HIGH`
- **Statement:** Keep a clear operating zone in front of wardrobe doors and drawers.
- **Planning target:** min 900 mm, preferred 1000 mm
- **Applies when:** wardrobe_or_drawer
- **Tags:** storage, clear-circulation
- **Source:** [SRC-PRACTICE-ERGONOMICS](https://www.archdaily.com/tag/interior-design) — general_reference
- **Notes:** Use as a design check; verify the actual room, product and local requirements.

### STO-DRAW-003 — drawer front

- **Type / priority:** `TECHNICAL_GUIDELINE` / `MEDIUM`
- **Statement:** Test drawer pull-out against the adjacent path, bed and door swing.
- **Planning target:** min 900 mm
- **Applies when:** drawer
- **Tags:** storage, clear-circulation
- **Source:** [SRC-PRACTICE-ERGONOMICS](https://www.archdaily.com/tag/interior-design) — general_reference
- **Notes:** Use as a design check; verify the actual room, product and local requirements.

### STO-REACH-004 — reachable shelf

- **Type / priority:** `BEST_PRACTICE` / `MEDIUM`
- **Statement:** Keep frequently used shelves within a reachable band and reserve high shelves for occasional or light items.
- **Planning target:** max 1800 mm
- **Applies when:** aging_in_place, daily_storage
- **Tags:** storage, aging-in-place
- **Source:** [SRC-PRACTICE-ERGONOMICS](https://www.archdaily.com/tag/interior-design) — general_reference
- **Notes:** Use as a design check; verify the actual room, product and local requirements.

### STO-ENTRY-005 — shoe storage depth

- **Type / priority:** `BEST_PRACTICE` / `LOW`
- **Statement:** Keep entry shoe storage shallow enough that it does not reduce the entry route.
- **Planning target:** max 350 mm
- **Applies when:** entry
- **Tags:** storage, clear-circulation
- **Source:** [SRC-PRACTICE-ERGONOMICS](https://www.archdaily.com/tag/interior-design) — general_reference
- **Notes:** Use as a design check; verify the actual room, product and local requirements.

### STO-ENTRY-006 — entry bench

- **Type / priority:** `BEST_PRACTICE` / `MEDIUM`
- **Statement:** Provide a stable seated perch with clear approach at the entry when shoes or mobility aids are used.
- **Planning target:** min 600 mm
- **Applies when:** entry, aging_in_place
- **Tags:** storage, aging-in-place
- **Source:** [SRC-PRACTICE-ERGONOMICS](https://www.archdaily.com/tag/interior-design) — general_reference
- **Notes:** Use as a design check; verify the actual room, product and local requirements.

### STO-KIT-007 — pantry aisle

- **Type / priority:** `TECHNICAL_GUIDELINE` / `MEDIUM`
- **Statement:** Keep pantry and tall-unit doors from reducing the main kitchen aisle when open.
- **Planning target:** min 900 mm
- **Applies when:** pantry_or_tall_unit
- **Tags:** storage, kitchen-adjacency, clear-circulation
- **Source:** [SRC-NKBA-KITCHEN](https://www.nkba.org/standards-guidelines/kitchen-planning-guidelines/) — general_reference
- **Notes:** Use as a design check; verify the actual room, product and local requirements.

### STO-BAL-008 — balcony cabinet

- **Type / priority:** `PROJECT_PREFERENCE` / `MEDIUM`
- **Statement:** Retain existing balcony storage only when its doors and counter do not block the open-balcony route.
- **Planning target:** min 900 mm
- **Applies when:** existing_balcony_cabinet
- **Tags:** storage, balcony-connected, existing-structure
- **Source:** [SRC-C-TYPE-BRIEF](https://github.com/xiwei9871/internal-design) — project
- **Notes:** Use as a design check; verify the actual room, product and local requirements.

### STO-LINEN-009 — linen shelf

- **Type / priority:** `BEST_PRACTICE` / `LOW`
- **Statement:** Allow enough shelf depth for folded linen while keeping the front clear for opening and retrieval.
- **Planning target:** min 300 mm
- **Applies when:** linen_storage
- **Tags:** storage
- **Source:** [SRC-PRACTICE-ERGONOMICS](https://www.archdaily.com/tag/interior-design) — general_reference
- **Notes:** Use as a design check; verify the actual room, product and local requirements.

### STO-MNT-010 — service access

- **Type / priority:** `TECHNICAL_GUIDELINE` / `MEDIUM`
- **Statement:** Do not bury service valves, electrical panels or appliance connections behind fixed storage without a removable access strategy.
- **Planning target:** min 600 mm
- **Applies when:** services
- **Tags:** storage, existing-structure
- **Source:** [SRC-PRACTICE-ERGONOMICS](https://www.archdaily.com/tag/interior-design) — general_reference
- **Notes:** Use as a design check; verify the actual room, product and local requirements.

## study

### STD-DESK-001 — desk depth

- **Type / priority:** `TECHNICAL_GUIDELINE` / `HIGH`
- **Statement:** Use enough desk depth for the monitor, working documents and a comfortable keyboard position.
- **Planning target:** min 750 mm, preferred 800 mm
- **Applies when:** desk
- **Tags:** study-guest-hybrid
- **Source:** [SRC-PRACTICE-ERGONOMICS](https://www.archdaily.com/tag/interior-design) — general_reference
- **Notes:** Use as a design check; verify the actual room, product and local requirements.

### STD-DESK-002 — desk width

- **Type / priority:** `BEST_PRACTICE` / `MEDIUM`
- **Statement:** Provide a work width that supports the planned displays and a clear writing zone.
- **Planning target:** min 1200 mm, preferred 1700 mm
- **Applies when:** desk, dual_monitor
- **Tags:** study-guest-hybrid
- **Source:** [SRC-PRACTICE-ERGONOMICS](https://www.archdaily.com/tag/interior-design) — general_reference
- **Notes:** Use as a design check; verify the actual room, product and local requirements.

### STD-CIR-003 — chair pullback

- **Type / priority:** `TECHNICAL_GUIDELINE` / `HIGH`
- **Statement:** Keep a clear pullback zone behind the desk chair.
- **Planning target:** min 900 mm, preferred 1100 mm
- **Applies when:** desk
- **Tags:** clear-circulation, study-guest-hybrid
- **Source:** [SRC-PRACTICE-ERGONOMICS](https://www.archdaily.com/tag/interior-design) — general_reference
- **Notes:** Use as a design check; verify the actual room, product and local requirements.

### STD-CIR-004 — shared aisle

- **Type / priority:** `TECHNICAL_GUIDELINE` / `HIGH`
- **Statement:** Do not let a daybed, storage unit or chair pullback close the only study aisle.
- **Planning target:** min 900 mm
- **Applies when:** study_plus_sleep
- **Tags:** clear-circulation, study-guest-hybrid
- **Source:** [SRC-PRACTICE-ERGONOMICS](https://www.archdaily.com/tag/interior-design) — general_reference
- **Notes:** Use as a design check; verify the actual room, product and local requirements.

### STD-TECH-005 — screen glare

- **Type / priority:** `BEST_PRACTICE` / `MEDIUM`
- **Statement:** Place monitors so window glare can be controlled without blocking the required daylight route.
- **Planning target:** qualitative
- **Applies when:** window_present, screen
- **Tags:** daylight, study-guest-hybrid
- **Source:** [SRC-PRACTICE-ERGONOMICS](https://www.archdaily.com/tag/interior-design) — general_reference
- **Notes:** Use as a design check; verify the actual room, product and local requirements.

### STD-TECH-006 — printer reach

- **Type / priority:** `BEST_PRACTICE` / `LOW`
- **Statement:** Put printer and frequently used equipment within a short reach of the work chair without encroaching on the route.
- **Planning target:** min 450 mm
- **Applies when:** printer_or_NAS
- **Tags:** study-guest-hybrid, storage
- **Source:** [SRC-PRACTICE-ERGONOMICS](https://www.archdaily.com/tag/interior-design) — general_reference
- **Notes:** Use as a design check; verify the actual room, product and local requirements.

### STD-FLEX-007 — backup sleep footprint

- **Type / priority:** `PROJECT_PREFERENCE` / `MEDIUM`
- **Statement:** If the study doubles as guest sleep, reserve the sleep footprint before fixing storage or equipment.
- **Planning target:** min 900 mm
- **Applies when:** backup_sleep
- **Tags:** study-guest-hybrid, flexible-living
- **Source:** [SRC-PRACTICE-ERGONOMICS](https://www.archdaily.com/tag/interior-design) — general_reference
- **Notes:** Use as a design check; verify the actual room, product and local requirements.

### STD-FLEX-008 — daybed route

- **Type / priority:** `TECHNICAL_GUIDELINE` / `MEDIUM`
- **Statement:** Keep a clear approach to a daybed so the backup sleeping mode does not block the desk route.
- **Planning target:** min 900 mm
- **Applies when:** daybed
- **Tags:** study-guest-hybrid, clear-circulation
- **Source:** [SRC-PRACTICE-ERGONOMICS](https://www.archdaily.com/tag/interior-design) — general_reference
- **Notes:** Use as a design check; verify the actual room, product and local requirements.

### STD-STOR-009 — equipment ventilation

- **Type / priority:** `TECHNICAL_GUIDELINE` / `MEDIUM`
- **Statement:** Provide ventilation and service access for NAS, printer or other heat-producing equipment.
- **Planning target:** min 100 mm
- **Applies when:** NAS_or_equipment
- **Tags:** storage, study-guest-hybrid
- **Source:** [SRC-PRACTICE-ERGONOMICS](https://www.archdaily.com/tag/interior-design) — general_reference
- **Notes:** Use as a design check; verify the actual room, product and local requirements.

### STD-WIN-010 — window route

- **Type / priority:** `BEST_PRACTICE` / `LOW`
- **Statement:** Keep one clear path to the study window for ventilation and maintenance.
- **Planning target:** min 750 mm
- **Applies when:** window_present
- **Tags:** daylight, clear-circulation
- **Source:** [SRC-PRACTICE-ERGONOMICS](https://www.archdaily.com/tag/interior-design) — general_reference
- **Notes:** Use as a design check; verify the actual room, product and local requirements.

## Project principles

The following are project-owned decisions and statuses, not generic rules:

- **P-AGE-MOTHER** `HARD_PROJECT_CONSTRAINT` — Mother is 68; aging-in-place is a first-order planning priority for daily routes, bedroom and bathroom decisions. (status: `CONFIRMED`)
- **P-OWNER-COUPLE** `PROJECT_PREFERENCE` — The owner couple are permanent residents; periodic family and guests must be accommodated without making the daily plan hotel-like. (status: `CONFIRMED`)
- **P-ROOM-PROGRAM** `HARD_PROJECT_CONSTRAINT` — Retain four rooms and three bathrooms as the confirmed program. (status: `CONFIRMED`)
- **P-KITCHEN-KEEP** `HARD_PROJECT_CONSTRAINT` — Existing kitchen cabinetry is KEEP; do not redesign or silently relocate it during concept studies. (status: `CONFIRMED`)
- **P-PROJECTOR-LIVING** `PROJECT_PREFERENCE` — Living is projector/laser-TV dominant rather than TV-centric; media equipment must coexist with a flexible central activity area. (status: `CONFIRMED`)
- **P-CHILD-ACTIVITY** `PROJECT_PREFERENCE` — Provide a visible child activity area that can be cleared or reconfigured without moving walls. (status: `CONFIRMED`)
- **P-NORTH-BALCONY** `HARD_PROJECT_CONSTRAINT` — North balcony is OPEN_NOT_ENCLOSED now; any enclosure is a future proposal and must not be drawn as existing. (status: `CONFIRMED`)
- **P-SPLIT-LEVEL** `HARD_PROJECT_CONSTRAINT` — Existing stairs remain the daily route; an assisted/power-wheelchair alternate route is documented beside them, but its level delta and slope are provisional. (status: `CONFIRMED_WITH_TO_VERIFY`)
- **P-KEEP-FURNITURE** `HARD_PROJECT_CONSTRAINT` — Confirmed KEEP furniture and cabinetry remain unless an explicit later decision changes them. (status: `CONFIRMED`)
- **P-UNRESOLVED-STATUS** `TO_VERIFY_LOCAL_CODE` — Unresolved dimensions, levels, fixture clearances, local code and product selections remain explicitly TO_VERIFY; they cannot be promoted to PASS by visual plausibility. (status: `TO_VERIFY`)
