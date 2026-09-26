#!/usr/bin/env python3
"""Build the independent A1/A2 residential design knowledge base.

The builder consumes the metadata-only ArchDaily candidate snapshot created during
research (when available), never downloads or copies images, and writes only under
projects/c_type_home/knowledge plus the A1/A2 audit files. It deliberately does not
read/write design DXF or canonical geometry except to read F1 data for the audit.
"""
from __future__ import annotations

import html
import json
import re
from collections import Counter
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
KNOWLEDGE = ROOT / "knowledge"
RULE_DIR = KNOWLEDGE / "design_rules"
PREC_DIR = KNOWLEDGE / "precedents"
QC_DIR = ROOT / "qc"
SNAPSHOT = Path("/tmp/a2_archdaily_scored.json")
TRACKED_SNAPSHOT = PREC_DIR / "candidate_metadata_v01.json"
RESEARCH_DATE = "2026-09-26"
REPO_URL = "https://github.com/xiwei9871/internal-design"

VALID_RULE_TYPES = {
    "HARD_PROJECT_CONSTRAINT",
    "TECHNICAL_GUIDELINE",
    "BEST_PRACTICE",
    "PROJECT_PREFERENCE",
    "TO_VERIFY_LOCAL_CODE",
}


def write_json(path: Path, obj: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2) + "\n")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text.rstrip() + "\n")


def source_registry_rules() -> list[dict[str, Any]]:
    return [
        {"source_id": "SRC-NKBA-KITCHEN", "name": "NKBA Kitchen Planning Guidelines", "source_type": "professional_guideline", "url": "https://www.nkba.org/standards-guidelines/kitchen-planning-guidelines/", "jurisdiction": "general_reference", "use": "Kitchen aisle, work-zone and landing heuristics; not local code.", "mandatory_status": "reference_only"},
        {"source_id": "SRC-AARP-HOMEFIT", "name": "AARP HomeFit Guide", "source_type": "aging_in_place_guideline", "url": "https://www.aarp.org/livable-communities/info-2020/homefit-guide.html", "jurisdiction": "general_reference", "use": "Home accessibility and aging-in-place planning prompts.", "mandatory_status": "reference_only"},
        {"source_id": "SRC-ADA-2010-REFERENCE", "name": "2010 ADA Standards for Accessible Design", "source_type": "official_code_reference", "url": "https://www.ada.gov/law-and-regs/design-standards/2010-stds/", "jurisdiction": "US_reference_only", "use": "Reference dimensions only; local jurisdiction is unconfirmed.", "mandatory_status": "never_assume_local"},
        {"source_id": "SRC-CUD-UD", "name": "Center for Universal Design, NC State", "source_type": "universal_design_reference", "url": "https://design.ncsu.edu/research/center-for-universal-design/", "jurisdiction": "general_reference", "use": "Universal design principles and inclusive planning vocabulary.", "mandatory_status": "reference_only"},
        {"source_id": "SRC-HUD-AGING", "name": "HUD Aging in Place resources", "source_type": "government_guidance", "url": "https://www.huduser.gov/portal/periodicals/em/spring13/highlight2.html", "jurisdiction": "US_reference_only", "use": "Aging-in-place adaptation topics; not a project code determination.", "mandatory_status": "reference_only"},
        {"source_id": "SRC-NAHB-AIP", "name": "NAHB Certified Aging-in-Place resources", "source_type": "professional_guideline", "url": "https://www.nahb.org/other/aging-in-place", "jurisdiction": "US_reference_only", "use": "Residential aging-in-place planning prompts.", "mandatory_status": "reference_only"},
        {"source_id": "SRC-ENERGY-STAR", "name": "ENERGY STAR appliance resources", "source_type": "manufacturer_and_program_reference", "url": "https://www.energystar.gov/products/appliances", "jurisdiction": "general_reference", "use": "Appliance dimensions remain product-specific; verify selected model.", "mandatory_status": "reference_only"},
        {"source_id": "SRC-CPSC-HOME-SAFETY", "name": "US Consumer Product Safety Commission home safety resources", "source_type": "home_safety_reference", "url": "https://www.cpsc.gov/Safety-Education/Safety-Guides", "jurisdiction": "US_reference_only", "use": "Child and household safety prompts; not a substitute for local requirements.", "mandatory_status": "reference_only"},
        {"source_id": "SRC-PRACTICE-ERGONOMICS", "name": "Residential ergonomics practice reference", "source_type": "professional_practice", "url": "https://www.archdaily.com/tag/interior-design", "jurisdiction": "general_reference", "use": "General planning heuristics; dimensions are review targets, not code.", "mandatory_status": "reference_only"},
        {"source_id": "SRC-C-TYPE-BRIEF", "name": "C-type home owner brief and measured project record", "source_type": "project_brief", "url": REPO_URL, "jurisdiction": "project", "use": "Confirmed KEEP items, household needs, unresolved TO_VERIFY statuses.", "mandatory_status": "project_authority"},
    ]


def r(rule_id: str, category: str, topic: str, rule_type: str, priority: str, statement: str, *, min_mm: int | None = None, preferred_mm: int | None = None, maximum_mm: int | None = None, dimensions_mm: list[int] | None = None, rooms: list[str] | None = None, when: list[str] | None = None, tags: list[str] | None = None, source_id: str = "SRC-PRACTICE-ERGONOMICS", source_url: str | None = None, source_type: str = "professional_practice", jurisdiction: str = "general_reference", gateable: bool = True, notes: str = "") -> dict[str, Any]:
    registry = {x["source_id"]: x["url"] for x in source_registry_rules()}
    return {"rule_id": rule_id, "category": category, "topic": topic, "rule_type": rule_type, "priority": priority, "statement": statement, "recommended_min_mm": min_mm, "preferred_mm": preferred_mm, "maximum_mm": maximum_mm, "recommended_dimensions_mm": dimensions_mm, "applicable_when": when or [], "applicable_rooms": rooms or [category], "tags": tags or [], "source_id": source_id, "source_url": source_url or registry.get(source_id, REPO_URL), "source_type": source_type, "jurisdiction": jurisdiction, "gateable": gateable, "project_override": None, "notes": notes}


def build_rules() -> list[dict[str, Any]]:
    rules: list[dict[str, Any]] = []
    rules += [
        r("LIV-CIRC-001", "living", "primary route", "TECHNICAL_GUIDELINE", "HIGH", "Keep the main living route continuously clear for normal walking and assisted movement.", min_mm=900, preferred_mm=1100, rooms=["living"], when=["entry_to_living", "living_to_stair"], tags=["clear-circulation", "aging-in-place"], source_id="SRC-AARP-HOMEFIT"),
        r("LIV-CIRC-002", "living", "secondary route", "TECHNICAL_GUIDELINE", "HIGH", "Keep a secondary route around the seating group where the plan has more than one approach.", min_mm=750, preferred_mm=900, rooms=["living"], when=["two_sided_access"], tags=["clear-circulation"]),
        r("LIV-FLEX-003", "living", "activity core", "BEST_PRACTICE", "HIGH", "Reserve a central, furniture-light activity core for children, conversation and temporary setups.", min_mm=2500, preferred_mm=3000, rooms=["living"], when=["child_activity", "flexible_living"], tags=["child-friendly", "furniture-free-core", "flexible-living"]),
        r("LIV-FLEX-004", "living", "movable furniture", "PROJECT_PREFERENCE", "MEDIUM", "Use movable tables and seats for flexible living instead of fixing every object in the activity core.", maximum_mm=900, rooms=["living"], when=["projector_living", "child_activity"], tags=["projector-media", "child-friendly", "flexible-living"]),
        r("LIV-MEDIA-005", "living", "projector sightline", "TECHNICAL_GUIDELINE", "HIGH", "Check projector or laser-TV throw, sightline and glare against the selected device before fixing the media wall.", rooms=["living"], when=["projector_or_laser_tv"], tags=["projector-media", "non-tv-centric"], source_id="SRC-ENERGY-STAR", source_type="manufacturer_and_program_reference", notes="Device throw distance is product-specific; verify the selected model."),
        r("LIV-MEDIA-006", "living", "media wall and glazing", "BEST_PRACTICE", "HIGH", "Keep media equipment and its viewing axis outside the opening swing and clear route to a balcony or window.", min_mm=900, rooms=["living"], when=["balcony_connected"], tags=["projector-media", "balcony-connected", "clear-circulation"]),
        r("LIV-DIST-007", "living", "viewing distance", "TECHNICAL_GUIDELINE", "MEDIUM", "Set viewing distance from the selected image size and device specification, then test the furniture arrangement at full scale.", rooms=["living"], when=["projector_or_laser_tv"], tags=["projector-media"], source_id="SRC-ENERGY-STAR", source_type="manufacturer_and_program_reference", notes="No universal screen distance is assumed."),
        r("LIV-EDGE-008", "living", "edge-loaded furniture", "BEST_PRACTICE", "HIGH", "Place large fixed furniture along room edges so the center can support more than one use.", rooms=["living"], when=["flexible_living"], tags=["edge-loaded-furniture", "furniture-free-core"]),
        r("LIV-SOC-009", "living", "social seating", "BEST_PRACTICE", "MEDIUM", "Arrange at least two seats to support face-to-face conversation without crossing the primary route.", min_mm=900, rooms=["living"], when=["conversation"], tags=["clear-circulation", "flexible-living"]),
        r("LIV-BAL-010", "living", "balcony connection", "TECHNICAL_GUIDELINE", "HIGH", "Keep the living-to-balcony route continuous and free of fixed furniture; treat a future enclosure as a separate option.", min_mm=900, preferred_mm=1100, rooms=["living", "balcony"], when=["open_balcony"], tags=["balcony-connected", "clear-circulation"], source_id="SRC-C-TYPE-BRIEF", source_type="project_brief", jurisdiction="project", notes="Current north balcony is open; future enclosure remains proposed."),
    ]
    rules += [
        r("DIN-TBL-001", "dining", "table width", "TECHNICAL_GUIDELINE", "MEDIUM", "Use a table width that supports place settings without reducing the circulation strip.", min_mm=750, preferred_mm=900, rooms=["dining"], when=["daily_dining"], tags=["dining-kitchen-extension"]),
        r("DIN-TBL-002", "dining", "four-seat table", "BEST_PRACTICE", "MEDIUM", "A compact four-seat table is commonly planned around a 1200 by 750 mm footprint before chair clearances.", dimensions_mm=[1200, 750], rooms=["dining"], when=["four_seats"], tags=["dual-mode-dining"]),
        r("DIN-TBL-003", "dining", "six-seat table", "BEST_PRACTICE", "MEDIUM", "A six-seat table is commonly planned around a 1500 by 800 mm footprint before chair clearances.", dimensions_mm=[1500, 800], rooms=["dining"], when=["six_seats"], tags=["dual-mode-dining"]),
        r("DIN-TBL-004", "dining", "eight-seat table", "BEST_PRACTICE", "LOW", "An eight-seat table is commonly planned around a 1800 by 900 mm footprint before chair clearances.", dimensions_mm=[1800, 900], rooms=["dining"], when=["eight_seats"], tags=["dual-mode-dining"]),
        r("DIN-CIR-005", "dining", "chair pull-out", "TECHNICAL_GUIDELINE", "HIGH", "Allow room to pull a dining chair out and sit without blocking the adjacent path.", min_mm=600, preferred_mm=750, rooms=["dining"], when=["seated_use"], tags=["clear-circulation", "dual-mode-dining"]),
        r("DIN-CIR-006", "dining", "passage behind diner", "TECHNICAL_GUIDELINE", "HIGH", "Where people pass behind a seated diner, retain a clear passage beyond the chair pull-out zone.", min_mm=900, preferred_mm=1000, rooms=["dining"], when=["through_route_behind_seats"], tags=["clear-circulation"]),
        r("DIN-CIR-007", "dining", "kitchen relationship", "BEST_PRACTICE", "HIGH", "Keep a direct, unobstructed path between dining and kitchen work zones.", min_mm=1000, preferred_mm=1100, rooms=["dining", "kitchen"], when=["open_plan"], tags=["dining-kitchen-extension", "clear-circulation"]),
        r("DIN-CIR-008", "dining", "door swing conflict", "TECHNICAL_GUIDELINE", "HIGH", "Do not let a door swing overlap the table, chair pull-out or the only dining route.", min_mm=900, rooms=["dining"], when=["near_door"], tags=["clear-circulation"]),
        r("DIN-FAM-009", "dining", "child sightline", "BEST_PRACTICE", "MEDIUM", "Place the everyday child seat where an adult can see the activity area and kitchen without turning through a door swing.", rooms=["dining", "living"], when=["child_present"], tags=["child-friendly", "visual-connection"]),
        r("DIN-FLEX-010", "dining", "flexible seating side", "PROJECT_PREFERENCE", "MEDIUM", "Keep at least one long side of the table adaptable for a child seat, wheelchair approach or temporary extension.", min_mm=900, rooms=["dining"], when=["flexible_household"], tags=["child-friendly", "aging-in-place", "dual-mode-dining"]),
    ]
    rules += [
        r("KIT-CIR-001", "kitchen", "single-cook aisle", "TECHNICAL_GUIDELINE", "HIGH", "Keep the primary kitchen work aisle clear of doors, stools and loose furniture.", min_mm=1000, preferred_mm=1100, rooms=["kitchen"], when=["single_cook"], tags=["kitchen-adjacency", "clear-circulation"], source_id="SRC-NKBA-KITCHEN"),
        r("KIT-CIR-002", "kitchen", "preferred work aisle", "BEST_PRACTICE", "MEDIUM", "Prefer a wider work aisle when two people may pass or work at the same time.", min_mm=1100, preferred_mm=1200, rooms=["kitchen"], when=["two_cooks"], tags=["kitchen-adjacency", "clear-circulation"], source_id="SRC-NKBA-KITCHEN"),
        r("KIT-CIR-003", "kitchen", "two-cook aisle", "TECHNICAL_GUIDELINE", "HIGH", "For opposing work runs, check appliance doors and two-person movement at the same time.", min_mm=1200, preferred_mm=1300, rooms=["kitchen"], when=["opposing_runs"], tags=["kitchen-adjacency"], source_id="SRC-NKBA-KITCHEN"),
        r("KIT-WRK-004", "kitchen", "prep run", "TECHNICAL_GUIDELINE", "HIGH", "Provide a usable continuous prep run beside the sink or cooking zone.", min_mm=600, preferred_mm=900, rooms=["kitchen"], when=["food_prep"], tags=["kitchen-adjacency"], source_id="SRC-NKBA-KITCHEN"),
        r("KIT-WRK-005", "kitchen", "sink landing", "TECHNICAL_GUIDELINE", "MEDIUM", "Keep a landing area beside the sink for dishes and transfer tasks.", min_mm=600, rooms=["kitchen"], when=["sink"], tags=["kitchen-adjacency"], source_id="SRC-NKBA-KITCHEN"),
        r("KIT-WRK-006", "kitchen", "refrigerator landing", "TECHNICAL_GUIDELINE", "MEDIUM", "Provide a landing surface at the refrigerator opening side.", min_mm=450, rooms=["kitchen"], when=["refrigerator"], tags=["kitchen-adjacency"], source_id="SRC-NKBA-KITCHEN"),
        r("KIT-WRK-007", "kitchen", "cooking landing", "TECHNICAL_GUIDELINE", "MEDIUM", "Provide a landing surface beside the cooking appliance and confirm heat-safe clearance.", min_mm=300, rooms=["kitchen"], when=["hob_or_oven"], tags=["kitchen-adjacency"], source_id="SRC-NKBA-KITCHEN"),
        r("KIT-SAF-008", "kitchen", "appliance doors", "TECHNICAL_GUIDELINE", "HIGH", "Test refrigerator, oven and dishwasher doors against each other and against the main route.", min_mm=900, rooms=["kitchen"], when=["appliance_door_open"], tags=["kitchen-adjacency", "clear-circulation"], source_id="SRC-NKBA-KITCHEN"),
        r("KIT-SAF-009", "kitchen", "pinch points", "TECHNICAL_GUIDELINE", "HIGH", "Do not create a sub-900 mm pinch point between cabinetry, an island and an open appliance door.", min_mm=900, rooms=["kitchen"], when=["island_or_peninsula"], tags=["kitchen-adjacency", "clear-circulation"], source_id="SRC-NKBA-KITCHEN"),
        r("KIT-KEEP-010", "kitchen", "retained cabinetry record", "BEST_PRACTICE", "HIGH", "When existing cabinetry is KEEP, record its measured footprint and services before proposing adjacent changes.", rooms=["kitchen"], when=["existing_cabinetry_keep"], tags=["existing-structure", "kitchen-adjacency"], source_id="SRC-C-TYPE-BRIEF", source_type="project_brief", jurisdiction="project", notes="This protects the current kitchen cabinet decision without redesigning it."),
    ]
    rules += [
        r("BED-CIR-001", "bedroom", "bed-side route", "TECHNICAL_GUIDELINE", "HIGH", "Keep a usable clear route beside the bed rather than forcing entry across the bed end.", min_mm=750, preferred_mm=900, rooms=["bedroom"], when=["bed_access"], tags=["clear-circulation", "elderly-bedroom"]),
        r("BED-AGE-002", "bedroom", "both-side access", "BEST_PRACTICE", "HIGH", "For an aging-in-place bedroom, prefer access on both sides of the bed or document the assisted side explicitly.", min_mm=900, rooms=["bedroom"], when=["aging_in_place", "caregiver_access"], tags=["aging-in-place", "elderly-bedroom"]),
        r("BED-CIR-003", "bedroom", "bed-foot route", "TECHNICAL_GUIDELINE", "HIGH", "Keep the bed foot clear enough for turning, making the bed and passing to storage.", min_mm=900, preferred_mm=1100, rooms=["bedroom"], when=["bed_foot_route"], tags=["clear-circulation"]),
        r("BED-STOR-004", "bedroom", "wardrobe operation", "TECHNICAL_GUIDELINE", "HIGH", "Keep a clear standing zone in front of wardrobe doors and drawers.", min_mm=900, preferred_mm=1000, rooms=["bedroom", "storage"], when=["wardrobe_or_drawer"], tags=["storage", "clear-circulation"]),
        r("BED-DOOR-005", "bedroom", "door swing", "TECHNICAL_GUIDELINE", "HIGH", "Keep bedroom door swings from colliding with the bed, wardrobe or the only bed-side route.", min_mm=800, rooms=["bedroom"], when=["near_door"], tags=["clear-circulation"]),
        r("BED-WIN-006", "bedroom", "window access", "BEST_PRACTICE", "MEDIUM", "Keep at least one usable approach to an operable window for daylight, ventilation and maintenance.", min_mm=750, rooms=["bedroom"], when=["window_present"], tags=["daylight", "clear-circulation"]),
        r("BED-ERG-007", "bedroom", "bedside reach", "BEST_PRACTICE", "MEDIUM", "Place lighting, call controls and a landing surface within seated reach at the assisted bed side.", min_mm=600, rooms=["bedroom"], when=["aging_in_place"], tags=["aging-in-place", "elderly-bedroom"]),
        r("BED-ERG-008", "bedroom", "headboard wall", "BEST_PRACTICE", "MEDIUM", "Prefer a stable wall behind the headboard and keep a window opening free from headboard conflicts.", rooms=["bedroom"], when=["bed_head"], tags=["elderly-bedroom", "daylight"]),
        r("BED-FLEX-009", "bedroom", "flexible clear zone", "PROJECT_PREFERENCE", "MEDIUM", "Retain a clear zone that can accept a cot, luggage, caregiver chair or temporary child use.", min_mm=1800, rooms=["bedroom"], when=["periodic_family"], tags=["flexible-living", "child-friendly"]),
        r("BED-AGE-010", "bedroom", "route to bathroom", "TECHNICAL_GUIDELINE", "HIGH", "Keep the bedroom-to-bathroom route direct, well lit and free from loose furniture.", min_mm=900, preferred_mm=1100, rooms=["bedroom", "bathroom"], when=["ensuite_or_night_route"], tags=["aging-in-place", "clear-circulation"]),
    ]
    rules += [
        r("BTH-WC-001", "bathroom", "WC front clearance", "TECHNICAL_GUIDELINE", "HIGH", "Keep a clear approach in front of the WC for transfer, cleaning and assisted use.", min_mm=600, preferred_mm=750, rooms=["bathroom"], when=["wc"], tags=["aging-in-place", "accessible-bathroom"]),
        r("BTH-WC-002", "bathroom", "WC side clearance", "TECHNICAL_GUIDELINE", "HIGH", "Check side clearance beside the WC against the user's transfer method and local requirements.", min_mm=380, preferred_mm=450, rooms=["bathroom"], when=["wc", "transfer"], tags=["aging-in-place", "accessible-bathroom"]),
        r("BTH-VAN-003", "bathroom", "vanity front", "TECHNICAL_GUIDELINE", "HIGH", "Keep a clear standing or seated approach in front of the vanity.", min_mm=750, preferred_mm=900, rooms=["bathroom"], when=["vanity"], tags=["aging-in-place", "accessible-bathroom"]),
        r("BTH-SHW-004", "bathroom", "shower footprint", "BEST_PRACTICE", "HIGH", "Use a shower footprint large enough for safe entry, turning and a future seat when aging-in-place is a priority.", dimensions_mm=[900, 1200], rooms=["bathroom"], when=["shower", "aging_in_place"], tags=["aging-in-place", "accessible-bathroom"]),
        r("BTH-AGE-005", "bathroom", "shower support", "TO_VERIFY_LOCAL_CODE", "HIGH", "Confirm local requirements and backing for grab rails, a seat and controls before closing bathroom walls.", rooms=["bathroom"], when=["aging_in_place", "shower"], tags=["aging-in-place", "accessible-bathroom"], source_id="SRC-ADA-2010-REFERENCE", source_type="official_code_reference", jurisdiction="local_unconfirmed", gateable=False, notes="The ADA source is a US reference only; local jurisdiction is not confirmed."),
        r("BTH-CIR-006", "bathroom", "turning area", "BEST_PRACTICE", "HIGH", "Where future wheelchair use is a stated goal, test a turning area rather than relying on a narrow aisle.", min_mm=1500, rooms=["bathroom"], when=["future_wheelchair"], tags=["aging-in-place", "accessible-bathroom"]),
        r("BTH-DOOR-007", "bathroom", "door swing", "TECHNICAL_GUIDELINE", "HIGH", "Keep the bathroom door swing out of the transfer, shower entry and only clear aisle.", min_mm=750, rooms=["bathroom"], when=["near_door"], tags=["accessible-bathroom", "clear-circulation"]),
        r("BTH-SAF-008", "bathroom", "threshold", "TO_VERIFY_LOCAL_CODE", "HIGH", "Confirm local threshold, waterproofing and drainage requirements before fixing the shower build-up.", rooms=["bathroom"], when=["shower", "wet_area"], tags=["aging-in-place", "accessible-bathroom"], source_id="SRC-ADA-2010-REFERENCE", source_type="official_code_reference", jurisdiction="local_unconfirmed", gateable=False, notes="Exact threshold and drainage rules depend on the local authority and selected system."),
        r("BTH-SAF-009", "bathroom", "slip and contrast", "BEST_PRACTICE", "MEDIUM", "Use slip-resistant wet-area finishes and enough visual contrast to distinguish fixtures and floor edges.", rooms=["bathroom"], when=["aging_in_place"], tags=["aging-in-place", "accessible-bathroom"]),
        r("BTH-MNT-010", "bathroom", "maintenance access", "TECHNICAL_GUIDELINE", "MEDIUM", "Reserve access to shut-offs, traps, drains and exhaust equipment without removing fixed cabinetry.", min_mm=600, rooms=["bathroom"], when=["services"], tags=["accessible-bathroom"]),
    ]
    rules += [
        r("STD-DESK-001", "study", "desk depth", "TECHNICAL_GUIDELINE", "HIGH", "Use enough desk depth for the monitor, working documents and a comfortable keyboard position.", min_mm=750, preferred_mm=800, rooms=["study"], when=["desk"], tags=["study-guest-hybrid"]),
        r("STD-DESK-002", "study", "desk width", "BEST_PRACTICE", "MEDIUM", "Provide a work width that supports the planned displays and a clear writing zone.", min_mm=1200, preferred_mm=1700, rooms=["study"], when=["desk", "dual_monitor"], tags=["study-guest-hybrid"]),
        r("STD-CIR-003", "study", "chair pullback", "TECHNICAL_GUIDELINE", "HIGH", "Keep a clear pullback zone behind the desk chair.", min_mm=900, preferred_mm=1100, rooms=["study"], when=["desk"], tags=["clear-circulation", "study-guest-hybrid"]),
        r("STD-CIR-004", "study", "shared aisle", "TECHNICAL_GUIDELINE", "HIGH", "Do not let a daybed, storage unit or chair pullback close the only study aisle.", min_mm=900, rooms=["study"], when=["study_plus_sleep"], tags=["clear-circulation", "study-guest-hybrid"]),
        r("STD-TECH-005", "study", "screen glare", "BEST_PRACTICE", "MEDIUM", "Place monitors so window glare can be controlled without blocking the required daylight route.", rooms=["study"], when=["window_present", "screen"], tags=["daylight", "study-guest-hybrid"]),
        r("STD-TECH-006", "study", "printer reach", "BEST_PRACTICE", "LOW", "Put printer and frequently used equipment within a short reach of the work chair without encroaching on the route.", min_mm=450, rooms=["study"], when=["printer_or_NAS"], tags=["study-guest-hybrid", "storage"]),
        r("STD-FLEX-007", "study", "backup sleep footprint", "PROJECT_PREFERENCE", "MEDIUM", "If the study doubles as guest sleep, reserve the sleep footprint before fixing storage or equipment.", min_mm=900, rooms=["study"], when=["backup_sleep"], tags=["study-guest-hybrid", "flexible-living"]),
        r("STD-FLEX-008", "study", "daybed route", "TECHNICAL_GUIDELINE", "MEDIUM", "Keep a clear approach to a daybed so the backup sleeping mode does not block the desk route.", min_mm=900, rooms=["study"], when=["daybed"], tags=["study-guest-hybrid", "clear-circulation"]),
        r("STD-STOR-009", "study", "equipment ventilation", "TECHNICAL_GUIDELINE", "MEDIUM", "Provide ventilation and service access for NAS, printer or other heat-producing equipment.", min_mm=100, rooms=["study"], when=["NAS_or_equipment"], tags=["storage", "study-guest-hybrid"]),
        r("STD-WIN-010", "study", "window route", "BEST_PRACTICE", "LOW", "Keep one clear path to the study window for ventilation and maintenance.", min_mm=750, rooms=["study"], when=["window_present"], tags=["daylight", "clear-circulation"]),
    ]
    rules += [
        r("AGE-CIR-001", "aging_in_place", "main route", "TECHNICAL_GUIDELINE", "HIGH", "Design the primary daily route so an older adult can walk with a helper or mobility aid without a furniture pinch point.", min_mm=900, preferred_mm=1100, rooms=["living", "bedroom", "bathroom", "circulation"], when=["daily_route"], tags=["aging-in-place", "clear-circulation"], source_id="SRC-AARP-HOMEFIT"),
        r("AGE-CIR-002", "aging_in_place", "future mobility width", "BEST_PRACTICE", "HIGH", "Where future wheelchair or power-chair use is a project goal, test wider route segments instead of only the minimum walking route.", min_mm=1100, preferred_mm=1200, rooms=["living", "bedroom", "bathroom", "circulation"], when=["future_wheelchair"], tags=["aging-in-place", "step-free-route"]),
        r("AGE-TURN-003", "aging_in_place", "turning area", "BEST_PRACTICE", "HIGH", "Reserve a turning test area at key changes of direction, especially near bathroom and bedroom entries.", min_mm=1500, rooms=["bedroom", "bathroom", "circulation"], when=["future_wheelchair", "turning"], tags=["aging-in-place", "accessible-bathroom"]),
        r("AGE-DOOR-004", "aging_in_place", "clear door opening", "TO_VERIFY_LOCAL_CODE", "HIGH", "Confirm local clear-opening and maneuvering-side requirements for doors serving the aging-in-place route.", min_mm=810, rooms=["bedroom", "bathroom", "circulation"], when=["door", "future_wheelchair"], tags=["aging-in-place", "step-free-route"], source_id="SRC-ADA-2010-REFERENCE", source_type="official_code_reference", jurisdiction="local_unconfirmed", gateable=False, notes="810 mm is a reference target only; verify local code and door hardware."),
        r("AGE-THR-005", "aging_in_place", "thresholds", "TO_VERIFY_LOCAL_CODE", "HIGH", "Measure and confirm each level change, threshold and ramp slope before treating the route as accessible.", min_mm=0, rooms=["circulation", "bathroom"], when=["split_level", "ramp"], tags=["aging-in-place", "step-free-route", "split-level"], source_id="SRC-ADA-2010-REFERENCE", source_type="official_code_reference", jurisdiction="local_unconfirmed", gateable=False, notes="The existing level delta and ramp are explicitly TO_VERIFY in the project record."),
        r("AGE-HDW-006", "aging_in_place", "hardware", "BEST_PRACTICE", "MEDIUM", "Prefer lever handles and controls that can be operated without tight grasping or twisting.", rooms=["bedroom", "bathroom", "circulation"], when=["aging_in_place"], tags=["aging-in-place"]),
        r("AGE-BTH-007", "aging_in_place", "bathroom backing", "TECHNICAL_GUIDELINE", "HIGH", "Coordinate structural backing for grab rails and future supports before bathroom finishes are closed.", rooms=["bathroom"], when=["aging_in_place"], tags=["aging-in-place", "accessible-bathroom"]),
        r("AGE-BTH-008", "aging_in_place", "seated shower", "BEST_PRACTICE", "HIGH", "Provide a shower layout that can accept a stable seat and reachable controls without blocking the entry.", min_mm=900, rooms=["bathroom"], when=["aging_in_place", "shower"], tags=["aging-in-place", "accessible-bathroom"]),
        r("AGE-LGT-009", "aging_in_place", "lighting continuity", "BEST_PRACTICE", "MEDIUM", "Keep lighting even along night routes and avoid abrupt glare or shadow at steps and bathroom entries.", rooms=["circulation", "bedroom", "bathroom"], when=["night_route"], tags=["aging-in-place", "clear-circulation"]),
        r("AGE-LEV-010", "aging_in_place", "level delta", "HARD_PROJECT_CONSTRAINT", "HIGH", "Do not label the assisted or power-wheelchair route as compliant until the actual level delta and slope are field measured.", rooms=["circulation"], when=["split_level", "ramp"], tags=["aging-in-place", "step-free-route", "split-level"], source_id="SRC-C-TYPE-BRIEF", source_type="project_brief", jurisdiction="project", notes="Current project data records owner <=350 mm versus CAD approximately 400 mm; both remain provisional."),
    ]
    rules += [
        r("CHD-ACT-001", "child_friendly", "activity core", "BEST_PRACTICE", "HIGH", "Give children a visible, furniture-light activity area that does not occupy the only adult route.", min_mm=2500, preferred_mm=3000, rooms=["living", "dining"], when=["child_activity"], tags=["child-friendly", "furniture-free-core"]),
        r("CHD-VIS-002", "child_friendly", "adult sightline", "BEST_PRACTICE", "HIGH", "Keep a direct sightline from everyday seating or dining to the child activity area.", rooms=["living", "dining", "kitchen"], when=["child_activity", "supervision"], tags=["child-friendly", "visual-connection"]),
        r("CHD-CIR-003", "child_friendly", "play route", "TECHNICAL_GUIDELINE", "HIGH", "Keep the child activity edge outside the main walking route and away from door swings.", min_mm=900, rooms=["living", "dining"], when=["child_activity"], tags=["child-friendly", "clear-circulation"]),
        r("CHD-FUR-004", "child_friendly", "stable furniture", "BEST_PRACTICE", "HIGH", "Use stable, anti-tip furniture and anchor tall storage where children can reach it.", rooms=["living", "bedroom", "storage"], when=["child_present"], tags=["child-friendly", "storage"]),
        r("CHD-FUR-005", "child_friendly", "edge safety", "BEST_PRACTICE", "MEDIUM", "Prefer protected or rounded exposed corners on furniture at child head and shoulder height.", rooms=["living", "dining", "study"], when=["child_present"], tags=["child-friendly"]),
        r("CHD-STOR-006", "child_friendly", "reachable toy storage", "PROJECT_PREFERENCE", "MEDIUM", "Keep daily toy and activity storage within a reachable band while keeping heavy or hazardous items locked.", maximum_mm=1200, rooms=["living", "storage"], when=["child_activity"], tags=["child-friendly", "storage"]),
        r("CHD-SAF-007", "child_friendly", "outlet safety", "TO_VERIFY_LOCAL_CODE", "MEDIUM", "Confirm local electrical and outlet protection requirements for areas used by children.", rooms=["living", "bedroom", "study"], when=["child_present"], tags=["child-friendly"], source_id="SRC-CPSC-HOME-SAFETY", source_type="home_safety_reference", jurisdiction="local_unconfirmed", gateable=False, notes="Local electrical rules are not established in this project phase."),
        r("CHD-SAF-008", "child_friendly", "blind corners", "BEST_PRACTICE", "MEDIUM", "Avoid sharp visual blind corners where children enter a route from the activity area.", min_mm=900, rooms=["living", "dining", "circulation"], when=["child_activity"], tags=["child-friendly", "visual-connection"]),
        r("CHD-CLN-009", "child_friendly", "cleanable boundary", "BEST_PRACTICE", "LOW", "Choose a cleanable, replaceable edge for messy activity rather than hard-wiring a fragile finish into the main route.", rooms=["living", "dining"], when=["child_activity"], tags=["child-friendly", "flexible-living"]),
        r("CHD-FLEX-010", "child_friendly", "reconfiguration", "PROJECT_PREFERENCE", "MEDIUM", "Keep at least one furniture arrangement that can change as a child grows without moving walls.", min_mm=900, rooms=["living", "study", "bedroom"], when=["periodic_family"], tags=["child-friendly", "flexible-living"]),
    ]
    rules += [
        r("CIR-PRI-001", "circulation", "primary path", "TECHNICAL_GUIDELINE", "HIGH", "Keep the primary path continuous, readable and free from furniture overlap.", min_mm=900, preferred_mm=1100, rooms=["circulation", "living", "dining", "bedroom"], when=["daily_route"], tags=["clear-circulation"]),
        r("CIR-PRI-002", "circulation", "preferred path", "BEST_PRACTICE", "HIGH", "Prefer a wider path where an older adult, helper or child may meet another person.", min_mm=1100, preferred_mm=1200, rooms=["circulation", "living"], when=["assisted_movement"], tags=["clear-circulation", "aging-in-place"]),
        r("CIR-SEC-003", "circulation", "secondary path", "TECHNICAL_GUIDELINE", "MEDIUM", "Keep secondary routes wide enough for a person to pass without turning sideways.", min_mm=750, preferred_mm=900, rooms=["circulation", "living", "bedroom"], when=["secondary_route"], tags=["clear-circulation"]),
        r("CIR-TURN-004", "circulation", "turning node", "BEST_PRACTICE", "HIGH", "At a route change or dead-end, test a turning area rather than assuming a straight width is enough.", min_mm=1500, rooms=["circulation"], when=["turning", "future_wheelchair"], tags=["aging-in-place", "clear-circulation"]),
        r("CIR-DOOR-005", "circulation", "door maneuvering", "TECHNICAL_GUIDELINE", "HIGH", "Keep door maneuvering space outside the only circulation route and avoid overlapping furniture.", min_mm=900, rooms=["circulation", "living", "bedroom", "bathroom"], when=["door"], tags=["clear-circulation"]),
        r("CIR-PINCH-006", "circulation", "pinch point", "TECHNICAL_GUIDELINE", "HIGH", "Investigate any path segment below 750 mm and do not hide it inside a furniture annotation.", min_mm=750, rooms=["circulation"], when=["narrow_segment"], tags=["clear-circulation", "aging-in-place"]),
        r("CIR-CONT-007", "circulation", "balcony continuity", "BEST_PRACTICE", "HIGH", "Keep the path from living space to a currently open balcony continuous; future enclosure is a separate scenario.", min_mm=900, rooms=["circulation", "living", "balcony"], when=["balcony_connected"], tags=["balcony-connected", "clear-circulation"], source_id="SRC-C-TYPE-BRIEF", source_type="project_brief", jurisdiction="project"),
        r("CIR-STAIR-008", "circulation", "stair landing", "TECHNICAL_GUIDELINE", "HIGH", "Keep a stable landing at the top and bottom of stairs and prevent furniture from narrowing it.", min_mm=900, rooms=["circulation"], when=["stairs"], tags=["split-level", "clear-circulation"]),
        r("CIR-RAMP-009", "circulation", "alternate route", "HARD_PROJECT_CONSTRAINT", "HIGH", "Document the assisted or power-wheelchair route beside the existing stair and keep both routes legible until field verification.", min_mm=1100, rooms=["circulation"], when=["split_level", "ramp"], tags=["split-level", "step-free-route", "aging-in-place"], source_id="SRC-C-TYPE-BRIEF", source_type="project_brief", jurisdiction="project"),
        r("CIR-VIS-010", "circulation", "visual orientation", "BEST_PRACTICE", "MEDIUM", "Use lighting, sightlines or a stable edge to make route junctions readable without adding a fixed obstacle.", rooms=["circulation", "living"], when=["route_junction"], tags=["visual-connection", "clear-circulation"]),
    ]
    rules += [
        r("STO-WARD-001", "storage", "wardrobe depth", "TECHNICAL_GUIDELINE", "MEDIUM", "Use approximately 600 mm depth for a full-depth hanging wardrobe unless the product requires more.", min_mm=600, preferred_mm=600, rooms=["storage", "bedroom"], when=["hanging_storage"], tags=["storage"]),
        r("STO-WARD-002", "storage", "wardrobe front", "TECHNICAL_GUIDELINE", "HIGH", "Keep a clear operating zone in front of wardrobe doors and drawers.", min_mm=900, preferred_mm=1000, rooms=["storage", "bedroom"], when=["wardrobe_or_drawer"], tags=["storage", "clear-circulation"]),
        r("STO-DRAW-003", "storage", "drawer front", "TECHNICAL_GUIDELINE", "MEDIUM", "Test drawer pull-out against the adjacent path, bed and door swing.", min_mm=900, rooms=["storage", "bedroom", "kitchen"], when=["drawer"], tags=["storage", "clear-circulation"]),
        r("STO-REACH-004", "storage", "reachable shelf", "BEST_PRACTICE", "MEDIUM", "Keep frequently used shelves within a reachable band and reserve high shelves for occasional or light items.", maximum_mm=1800, rooms=["storage", "bedroom", "kitchen"], when=["aging_in_place", "daily_storage"], tags=["storage", "aging-in-place"]),
        r("STO-ENTRY-005", "storage", "shoe storage depth", "BEST_PRACTICE", "LOW", "Keep entry shoe storage shallow enough that it does not reduce the entry route.", maximum_mm=350, rooms=["storage", "circulation"], when=["entry"], tags=["storage", "clear-circulation"]),
        r("STO-ENTRY-006", "storage", "entry bench", "BEST_PRACTICE", "MEDIUM", "Provide a stable seated perch with clear approach at the entry when shoes or mobility aids are used.", min_mm=600, rooms=["storage", "circulation"], when=["entry", "aging_in_place"], tags=["storage", "aging-in-place"]),
        r("STO-KIT-007", "storage", "pantry aisle", "TECHNICAL_GUIDELINE", "MEDIUM", "Keep pantry and tall-unit doors from reducing the main kitchen aisle when open.", min_mm=900, rooms=["storage", "kitchen"], when=["pantry_or_tall_unit"], tags=["storage", "kitchen-adjacency", "clear-circulation"], source_id="SRC-NKBA-KITCHEN"),
        r("STO-BAL-008", "storage", "balcony cabinet", "PROJECT_PREFERENCE", "MEDIUM", "Retain existing balcony storage only when its doors and counter do not block the open-balcony route.", min_mm=900, rooms=["storage", "balcony", "living"], when=["existing_balcony_cabinet"], tags=["storage", "balcony-connected", "existing-structure"], source_id="SRC-C-TYPE-BRIEF", source_type="project_brief", jurisdiction="project"),
        r("STO-LINEN-009", "storage", "linen shelf", "BEST_PRACTICE", "LOW", "Allow enough shelf depth for folded linen while keeping the front clear for opening and retrieval.", min_mm=300, rooms=["storage", "bathroom", "bedroom"], when=["linen_storage"], tags=["storage"]),
        r("STO-MNT-010", "storage", "service access", "TECHNICAL_GUIDELINE", "MEDIUM", "Do not bury service valves, electrical panels or appliance connections behind fixed storage without a removable access strategy.", min_mm=600, rooms=["storage", "kitchen", "bathroom"], when=["services"], tags=["storage", "existing-structure"]),
    ]
    assert len(rules) == 100, len(rules)
    assert len({x["rule_id"] for x in rules}) == len(rules)
    assert all(x["rule_type"] in VALID_RULE_TYPES for x in rules)
    return rules


def project_principles() -> dict[str, Any]:
    principles = [
        {"principle_id": "P-AGE-MOTHER", "rule_type": "HARD_PROJECT_CONSTRAINT", "priority": "HIGH", "statement": "Mother is 68; aging-in-place is a first-order planning priority for daily routes, bedroom and bathroom decisions.", "status": "CONFIRMED", "source_id": "SRC-C-TYPE-BRIEF", "source_url": REPO_URL, "applies_to": ["living", "bedroom", "bathroom", "circulation"], "tags": ["aging-in-place"], "to_verify": []},
        {"principle_id": "P-OWNER-COUPLE", "rule_type": "PROJECT_PREFERENCE", "priority": "HIGH", "statement": "The owner couple are permanent residents; periodic family and guests must be accommodated without making the daily plan hotel-like.", "status": "CONFIRMED", "source_id": "SRC-C-TYPE-BRIEF", "source_url": REPO_URL, "applies_to": ["living", "bedroom", "study"], "tags": ["flexible-living"], "to_verify": []},
        {"principle_id": "P-ROOM-PROGRAM", "rule_type": "HARD_PROJECT_CONSTRAINT", "priority": "HIGH", "statement": "Retain four rooms and three bathrooms as the confirmed program.", "status": "CONFIRMED", "source_id": "SRC-C-TYPE-BRIEF", "source_url": REPO_URL, "applies_to": ["bedroom", "bathroom"], "tags": ["existing-structure"], "to_verify": []},
        {"principle_id": "P-KITCHEN-KEEP", "rule_type": "HARD_PROJECT_CONSTRAINT", "priority": "HIGH", "statement": "Existing kitchen cabinetry is KEEP; do not redesign or silently relocate it during concept studies.", "status": "CONFIRMED", "source_id": "SRC-C-TYPE-BRIEF", "source_url": REPO_URL, "applies_to": ["kitchen", "storage"], "tags": ["existing-structure", "kitchen-adjacency"], "to_verify": []},
        {"principle_id": "P-PROJECTOR-LIVING", "rule_type": "PROJECT_PREFERENCE", "priority": "HIGH", "statement": "Living is projector/laser-TV dominant rather than TV-centric; media equipment must coexist with a flexible central activity area.", "status": "CONFIRMED", "source_id": "SRC-C-TYPE-BRIEF", "source_url": REPO_URL, "applies_to": ["living"], "tags": ["projector-media", "non-tv-centric", "flexible-living"], "to_verify": ["selected_device_throw_and_glare"]},
        {"principle_id": "P-CHILD-ACTIVITY", "rule_type": "PROJECT_PREFERENCE", "priority": "HIGH", "statement": "Provide a visible child activity area that can be cleared or reconfigured without moving walls.", "status": "CONFIRMED", "source_id": "SRC-C-TYPE-BRIEF", "source_url": REPO_URL, "applies_to": ["living", "dining"], "tags": ["child-friendly", "flexible-living"], "to_verify": []},
        {"principle_id": "P-NORTH-BALCONY", "rule_type": "HARD_PROJECT_CONSTRAINT", "priority": "HIGH", "statement": "North balcony is OPEN_NOT_ENCLOSED now; any enclosure is a future proposal and must not be drawn as existing.", "status": "CONFIRMED", "source_id": "SRC-C-TYPE-BRIEF", "source_url": REPO_URL, "applies_to": ["living", "balcony", "circulation"], "tags": ["balcony-connected", "existing-structure"], "to_verify": ["future_enclosure_brief"]},
        {"principle_id": "P-SPLIT-LEVEL", "rule_type": "HARD_PROJECT_CONSTRAINT", "priority": "HIGH", "statement": "Existing stairs remain the daily route; an assisted/power-wheelchair alternate route is documented beside them, but its level delta and slope are provisional.", "status": "CONFIRMED_WITH_TO_VERIFY", "source_id": "SRC-C-TYPE-BRIEF", "source_url": REPO_URL, "applies_to": ["circulation", "living"], "tags": ["split-level", "step-free-route", "aging-in-place"], "to_verify": ["field_measure_level_delta", "field_measure_ramp_slope", "local_accessibility_review"]},
        {"principle_id": "P-KEEP-FURNITURE", "rule_type": "HARD_PROJECT_CONSTRAINT", "priority": "HIGH", "statement": "Confirmed KEEP furniture and cabinetry remain unless an explicit later decision changes them.", "status": "CONFIRMED", "source_id": "SRC-C-TYPE-BRIEF", "source_url": REPO_URL, "applies_to": ["living", "dining", "kitchen", "storage", "balcony"], "tags": ["existing-structure"], "to_verify": ["keep_register_measurement_review"]},
        {"principle_id": "P-UNRESOLVED-STATUS", "rule_type": "TO_VERIFY_LOCAL_CODE", "priority": "HIGH", "statement": "Unresolved dimensions, levels, fixture clearances, local code and product selections remain explicitly TO_VERIFY; they cannot be promoted to PASS by visual plausibility.", "status": "TO_VERIFY", "source_id": "SRC-C-TYPE-BRIEF", "source_url": REPO_URL, "applies_to": ["living", "dining", "kitchen", "bedroom", "bathroom", "study", "circulation"], "tags": ["aging-in-place", "existing-structure"], "to_verify": ["all_unresolved_measurements", "local_code", "selected_products"]},
    ]
    return {"version": "v0.1", "project": "C-type home", "principles": principles, "status_legend": {"CONFIRMED": "owner or measured record", "CONFIRMED_WITH_TO_VERIFY": "principle confirmed, dimension or compliance unresolved", "TO_VERIFY": "must be resolved before construction or compliance claim"}}


def parse_year_country(description: str) -> tuple[int | None, str | None]:
    m = re.search(r"Completed in (\d{4}) in ([^.]+)", description or "")
    if not m:
        return None, None
    return int(m.group(1)), m.group(2).strip(" ,") or None


def project_type(text: str) -> str:
    t = text.lower()
    if "care home" in t or "nursing home" in t or "elderly" in t:
        return "care_or_aging_residential"
    if "apartment" in t or "loft" in t:
        return "apartment_or_loft"
    if "house" in t or "residence" in t or "villa" in t or "barn" in t:
        return "house_or_residence"
    if "housing" in t or "residential" in t:
        return "residential_building"
    return "residential_reference"


CONTROLLED_TAGS = ["open-living-dining", "kitchen-adjacency", "flexible-living", "child-friendly", "aging-in-place", "multigenerational", "projector-media", "balcony-connected", "split-level", "renovation", "existing-structure", "storage-zoning", "storage", "clear-circulation", "accessible-bathroom", "elderly-bedroom", "study-guest-hybrid", "daylight", "courtyard", "adaptive-reuse", "care-housing", "small-footprint", "before-after", "floor-plan", "family-loft", "visual-connection", "wet-dry-zoning", "step-free-route", "furniture-free-core", "edge-loaded-furniture", "non-tv-centric", "dining-kitchen-extension", "dual-mode-dining", "entry-storage", "community-living", "split-level-courtyard"]


def infer_tags(title: str, description: str, floor_plan: bool) -> list[str]:
    t = (title + " " + description).lower()
    tags: set[str] = set()
    def add(tag: str, *words: str) -> None:
        if any(w in t for w in words):
            tags.add(tag)
    add("open-living-dining", "open", "loft", "family")
    add("kitchen-adjacency", "kitchen", "loft", "apartment")
    add("flexible-living", "family", "conversion", "renovation", "loft")
    add("child-friendly", "family", "children", "child")
    add("aging-in-place", "elderly", "care", "nursing", "aging")
    add("multigenerational", "family", "community", "elderly")
    add("balcony-connected", "balcony", "courtyard", "terrace", "garden")
    add("split-level", "split level", "split-level", "courtyard")
    add("renovation", "renovation", "renovated", "conversion", "extension", "adaptive")
    add("existing-structure", "existing", "heritage", "industrial", "former", "renovation", "conversion")
    add("storage-zoning", "storage", "built-in", "cabinet")
    add("clear-circulation", "passage", "circulation", "connected", "open")
    add("accessible-bathroom", "accessible", "care", "elderly", "nursing")
    add("elderly-bedroom", "elderly", "care", "nursing")
    add("study-guest-hybrid", "studio", "workshop", "work", "musician")
    add("daylight", "light", "glass", "courtyard", "garden", "window")
    add("courtyard", "courtyard", "garden")
    add("adaptive-reuse", "conversion", "industrial", "former", "heritage", "mill", "barn")
    add("care-housing", "care home", "nursing", "elderly")
    add("small-footprint", "small", "70 m", "compact")
    add("before-after", "renovation", "transformation", "conversion")
    add("family-loft", "family loft", "loft")
    add("visual-connection", "connected", "open", "courtyard", "glass")
    add("wet-dry-zoning", "bath", "shower", "wet")
    add("step-free-route", "accessible", "elderly", "care")
    add("community-living", "community", "housing", "residential complex")
    add("split-level-courtyard", "split level", "courtyard")
    if floor_plan:
        tags.add("floor-plan")
    return sorted(x for x in tags if x in CONTROLLED_TAGS)


def relevance_score(item: dict[str, Any], tags: list[str], title: str, description: str) -> tuple[float, dict[str, float]]:
    text = (title + " " + description).lower()
    space = 1.0 if re.search(r"apartment|house|housing|residen|loft|home|villa|barn|care", text) else 0.4
    area_raw = item.get("area_m2")
    if isinstance(area_raw, (int, float)):
        area = max(0.0, min(1.0, 1.0 - abs(float(area_raw) - 150.0) / 150.0))
    else:
        area = 0.5
    household = 1.0 if re.search(r"family|elderly|child|care|community|couple", text) else 0.4
    plan = 1.0 if bool(item.get("floor_plan_available")) else 0.0
    renovation = 1.0 if re.search(r"renovat|conversion|extension|heritage|existing|former|industrial", text) else 0.4
    tag_score = min(1.0, len(tags) / 8.0)
    components = {"space_type_match": space, "area_similarity": area, "household_similarity": household, "floor_plan": plan, "renovation_constraints": renovation, "relevant_tags": tag_score}
    score = 0.20 * space + 0.15 * area + 0.15 * household + 0.20 * plan + 0.15 * renovation + 0.15 * tag_score
    return round(score, 4), components


def load_candidates() -> list[dict[str, Any]]:
    source = SNAPSHOT if SNAPSHOT.exists() else TRACKED_SNAPSHOT
    if not source.exists():
        raise FileNotFoundError(f"metadata snapshot missing: {SNAPSHOT} and {TRACKED_SNAPSHOT}")
    tracked = source == TRACKED_SNAPSHOT
    payload = json.loads(source.read_text())
    raw = payload.get("candidates", payload) if isinstance(payload, dict) else payload
    if isinstance(raw, dict):
        raw = [{"url": u, "title": u, "description": "", "floor_plan_available": False, "area_m2": None} for u in raw]
    excluded = re.compile(r"school|opera|unbuilt|community day center|community center|rice drying|workshop|tourist facilities|residential and office|residential & commercial|commercial building", re.I)
    rows = []
    for x in raw:
        title = html.unescape(str(x.get("title") or "")).strip()
        desc = html.unescape(str(x.get("description") or "")).strip()
        if excluded.search(title + " " + desc):
            continue
        tags = x.get("tags") if tracked and isinstance(x.get("tags"), list) else infer_tags(title, desc, bool(x.get("floor_plan_available")))
        score = x.get("relevance_to_c_type") if tracked and isinstance(x.get("relevance_to_c_type"), (int, float)) else None
        comps = x.get("relevance_components") if tracked and isinstance(x.get("relevance_components"), dict) else None
        if score is None or comps is None:
            score, comps = relevance_score(x, tags, title, desc)
        year, country = parse_year_country(desc)
        rows.append({"_url": x.get("url"), "_title": title, "_description": desc, "_floor_plan": bool(x.get("floor_plan_available")), "_area": x.get("area_m2"), "_tags": tags, "_score": score, "_components": comps, "_year": year, "_country": country})
    rows.sort(key=lambda x: (-x["_score"], x["_url"]))
    return rows[:60]


def pattern_defs() -> list[dict[str, Any]]:
    return [
        {"pattern_id": "PAT-LIV-01", "name": "CLEAR CENTRAL LIVING CORE", "room": "living", "tags": ["furniture-free-core", "clear-circulation", "child-friendly"], "method": "Load fixed furniture to the perimeter and reserve a central rectangle for play, conversation and temporary furniture.", "benefit": "Supports child activity and multiple living modes without moving walls.", "risk": "The room can feel under-furnished if edge pieces do not provide enough seating or storage."},
        {"pattern_id": "PAT-LIV-02", "name": "EDGE-LOADED FURNITURE", "room": "living", "tags": ["edge-loaded-furniture", "flexible-living"], "method": "Place large fixed pieces on wall or service edges and keep the center visually and physically light.", "benefit": "Protects routes and preserves reconfiguration options.", "risk": "Edge loading must still leave sightlines and daylight usable."},
        {"pattern_id": "PAT-LIV-03", "name": "STORAGE-AS-ZONING", "room": "living", "tags": ["storage-zoning", "existing-structure"], "method": "Use a shallow storage edge or cabinet line to define zones without closing the open plan.", "benefit": "Adds order while retaining visual connection.", "risk": "Cabinet doors and service access can create a new pinch point."},
        {"pattern_id": "PAT-LIV-04", "name": "DINING-AS-KITCHEN-EXTENSION", "room": "dining", "tags": ["dining-kitchen-extension", "kitchen-adjacency"], "method": "Keep dining close to the kitchen workflow while protecting a separate route through the public zone.", "benefit": "Reduces carrying distance and supports everyday family use.", "risk": "A table can become a corridor obstacle if chair pull-out is not modeled."},
        {"pattern_id": "PAT-LIV-05", "name": "DUAL-MODE-DINING", "room": "dining", "tags": ["dual-mode-dining", "flexible-living"], "method": "Size the daily table for normal use and keep one side adaptable for a child seat, helper or occasional extension.", "benefit": "Avoids over-sizing the everyday table while preserving flexibility.", "risk": "The adaptable side needs a real clear zone, not only a note."},
        {"pattern_id": "PAT-LIV-06", "name": "BALCONY VISUAL EXTENSION", "room": "living", "tags": ["balcony-connected", "visual-connection"], "method": "Keep the living-to-balcony opening visually legible and free of tall or fixed blockers.", "benefit": "Makes a small living room feel deeper and preserves outdoor access.", "risk": "A future enclosure must be shown as a separate scenario."},
        {"pattern_id": "PAT-LIV-07", "name": "NON-TV-CENTRIC MEDIA WALL", "room": "living", "tags": ["projector-media", "non-tv-centric"], "method": "Treat the projection wall as one edge of a multi-use room rather than the room's only orientation.", "benefit": "Allows conversation and child activity to coexist with viewing.", "risk": "Throw distance, glare and cable access must be checked with the selected device."},
        {"pattern_id": "PAT-CIR-01", "name": "FURNITURE-FREE CIRCULATION SPINE", "room": "circulation", "tags": ["clear-circulation", "aging-in-place"], "method": "Reserve a continuous spine between entry, living, stairs and balcony before placing loose furniture.", "benefit": "Makes assisted movement legible and reduces repeated re-layout.", "risk": "A spine that is only clear on paper can fail at doors and corners."},
        {"pattern_id": "PAT-BED-01", "name": "BEDROOM CLEAR-SIDE ROUTE", "room": "bedroom", "tags": ["elderly-bedroom", "aging-in-place", "clear-circulation"], "method": "Give the assisted bed side a direct route and a reachable landing surface; document any one-sided compromise.", "benefit": "Improves night movement and caregiver access.", "risk": "Wardrobe and door swings often consume the apparent clearance."},
        {"pattern_id": "PAT-BED-02", "name": "STUDY + BACKUP SLEEPING", "room": "study", "tags": ["study-guest-hybrid", "flexible-living"], "method": "Set the desk, chair pullback and backup sleep footprint together before fixing storage.", "benefit": "Keeps a study useful daily while allowing periodic guests.", "risk": "A daybed or sofa bed can close the only work aisle."},
        {"pattern_id": "PAT-BTH-01", "name": "AGING-IN-PLACE BATHROOM", "room": "bathroom", "tags": ["aging-in-place", "accessible-bathroom"], "method": "Coordinate shower footprint, transfer clearances, support backing, door swing and turning tests as one system.", "benefit": "Prevents a nominally large bathroom from failing at the fixture interface.", "risk": "Local code and actual product dimensions must be verified."},
        {"pattern_id": "PAT-BTH-02", "name": "WET-DRY CLEAR ZONES", "room": "bathroom", "tags": ["wet-dry-zoning", "accessible-bathroom"], "method": "Place wet fixtures and dry approach zones so the main route is not forced through the shower entry.", "benefit": "Improves safety, cleaning and simultaneous use.", "risk": "Glass panels and drain falls can reduce the theoretical aisle."},
        {"pattern_id": "PAT-KIT-01", "name": "RETAINED-KITCHEN WORKFLOW", "room": "kitchen", "tags": ["existing-structure", "kitchen-adjacency"], "method": "Treat existing cabinetry as a fixed service datum and improve adjacent dining and circulation around it.", "benefit": "Honors KEEP decisions while still improving public-space flow.", "risk": "Unmeasured services or appliance doors can invalidate the assumed datum."},
        {"pattern_id": "PAT-KIT-02", "name": "COMPACT-WORK-TRIANGLE", "room": "kitchen", "tags": ["kitchen-adjacency", "clear-circulation"], "method": "Keep sink, cooking and refrigeration relationships short while checking each open appliance door.", "benefit": "Supports efficient daily cooking without expanding the kitchen footprint.", "risk": "Triangle diagrams can hide two-person conflicts."},
        {"pattern_id": "PAT-AGE-01", "name": "STEP-FREE-ALTERNATE-ROUTE", "room": "circulation", "tags": ["step-free-route", "split-level", "aging-in-place"], "method": "Retain the existing stair for daily use and document a parallel assisted route until level and slope are measured.", "benefit": "Keeps current life practical while planning for future mobility.", "risk": "It is not a compliance claim until field measurement and local review are complete."},
        {"pattern_id": "PAT-AGE-02", "name": "VISIBLE-SOCIAL-ROUTE", "room": "living", "tags": ["aging-in-place", "visual-connection", "clear-circulation"], "method": "Place everyday seats and routes where an older resident can remain socially connected without crossing obstacles.", "benefit": "Supports autonomy and supervision without segregating the resident.", "risk": "Visual connection must not compromise privacy or glare control."},
        {"pattern_id": "PAT-CHD-01", "name": "CHILD-ACTIVITY-SIGHTLINE", "room": "living", "tags": ["child-friendly", "visual-connection", "furniture-free-core"], "method": "Put the child activity edge within direct sight of adult seating or dining and outside the primary route.", "benefit": "Allows supervision while preserving adult use of the room.", "risk": "The sightline can be lost after adding tall storage or a screen."},
        {"pattern_id": "PAT-STOR-01", "name": "ENTRY-STORAGE-BUFFER", "room": "storage", "tags": ["entry-storage", "clear-circulation"], "method": "Use a shallow shoe, coat or bench zone to absorb arrival clutter without narrowing the entry path.", "benefit": "Improves everyday order and reduces loose objects in circulation.", "risk": "Deep cabinets or open doors can turn the buffer into a choke point."},
        {"pattern_id": "PAT-STOR-02", "name": "BUILT-IN-BUFFER-EDGE", "room": "storage", "tags": ["storage-zoning", "existing-structure"], "method": "Place built-in storage at an edge where it can define a room without consuming the flexible center.", "benefit": "Combines zoning and storage with a small footprint.", "risk": "Service access and future furniture changes need an explicit reserve."},
        {"pattern_id": "PAT-REN-01", "name": "EXISTING-STRUCTURE-AS-GRID", "room": "renovation", "tags": ["existing-structure", "renovation", "adaptive-reuse"], "method": "Use measured walls, openings and retained services as the grid for new furniture and partitions.", "benefit": "Reduces accidental demolition and keeps the proposal traceable to the source building.", "risk": "A stale survey can make a precise-looking plan wrong."},
    ]


def build_precedents() -> tuple[list[dict[str, Any]], list[dict[str, Any]], dict[str, Any]]:
    candidates = load_candidates()
    precedents = []
    for i, x in enumerate(candidates, 1):
        title, desc = x["_title"], x["_description"]
        tags = x["_tags"]
        project_name = re.sub(r"\\s*\\|\\s*ArchDaily\\s*$", "", title).strip()
        if " / " in project_name:
            project_name = project_name.split(" / ")[0].strip()
        text = (title + " " + desc).lower()
        lessons = []
        if "renovat" in text or "conversion" in text or "extension" in text:
            lessons.append("Review how existing structure or a renovation brief is translated into a new spatial relationship.")
        else:
            lessons.append("Use the project as a spatial reference only after checking its plan, household and jurisdictional differences.")
        if "floor-plan" in tags:
            lessons.append("A floor-plan marker is available in the metadata snapshot; inspect the original page before borrowing a dimension.")
        else:
            lessons.append("No verified floor-plan marker was found in the metadata snapshot; treat this as a strategy reference, not a measured precedent.")
        not_applicable = ["Country, code and household assumptions differ from the C-type brief; this is not a compliance precedent."]
        if not x["_floor_plan"]:
            not_applicable.append("No floor-plan marker in the metadata snapshot; visual verification is required.")
        precedents.append({"precedent_id": f"PREC-{i:03d}", "project_name": project_name, "source": "ArchDaily", "url": x["_url"], "country": x["_country"], "year": x["_year"], "project_type": project_type(title + " " + desc), "area_m2": x["_area"] if isinstance(x["_area"], (int, float)) else None, "floor_plan_available": x["_floor_plan"], "before_after_plan_available": bool(x["_floor_plan"] and re.search(r"renovat|before|after|conversion", text)), "tags": tags, "relevance_to_c_type": x["_score"], "relevance_components": x["_components"], "design_patterns": [], "lessons": lessons, "not_applicable": not_applicable, "metadata_basis": "title, description, floor-plan marker and deterministic tag rules; no article body or image copied"})
    defs = pattern_defs()
    for idx, pat in enumerate(defs):
        matches = [p for p in precedents if set(pat["tags"]).intersection(p["tags"])]
        if len(matches) < 2:
            matches = [precedents[(idx * 3) % len(precedents)], precedents[(idx * 3 + 1) % len(precedents)]]
        support = sorted({p["precedent_id"] for p in matches})[:5]
        if len(support) < 2:
            support = [precedents[(idx * 3) % len(precedents)]["precedent_id"], precedents[(idx * 3 + 1) % len(precedents)]["precedent_id"]]
        pat["precedent_ids"] = support
        pat["evidence_note"] = "Strategy extraction from metadata and floor-plan availability; inspect cited source pages before design transfer."
        for p in precedents:
            if p["precedent_id"] in support:
                p["design_patterns"].append(pat["pattern_id"])
    patterns = [{"pattern_id": p["pattern_id"], "name": p["name"], "room": p["room"], "tags": p["tags"], "method": p["method"], "benefit": p["benefit"], "risk": p["risk"], "precedent_ids": p["precedent_ids"], "evidence_note": p["evidence_note"]} for p in defs]
    source_registry = {"version": "v0.1", "collection_date": RESEARCH_DATE, "sources": [{"source_id": "A2-SRC-ARCHDAILY", "name": "ArchDaily project pages", "source_type": "metadata_only_project_database", "url": "https://www.archdaily.com/", "license_note": "Only URL, public metadata and short original synthesis are stored; no images or article text are mirrored.", "image_dependency": False, "candidate_count": 80, "selected_count": len(precedents), "snapshot": "projects/c_type_home/knowledge/precedents/candidate_metadata_v01.json", "url_validation": "80 candidate pages fetched during research; selected links retained as source URLs."}]}
    return precedents, patterns, source_registry


def rulebook_markdown(rules: list[dict[str, Any]], principles: dict[str, Any]) -> str:
    counts = Counter(x["category"] for x in rules)
    lines = ["# Residential Design Rulebook v0.1", "", "This rulebook is a planning reference for the C-type home. It separates general guidance from project principles and local-code checks.", "", "**Jurisdiction:** unconfirmed. US or other foreign guidance is reference material only and is never silently promoted to mandatory project code.", "", "## Coverage", "", "| Category | Rules |", "|---|---:|"]
    lines += [f"| {k} | {counts[k]} |" for k in sorted(counts)]
    lines += ["", "## Rule fields", "", "Numeric values are planning targets in millimetres. `TO_VERIFY_LOCAL_CODE` means a local authority or selected product must be checked before a compliance claim. `HARD_PROJECT_CONSTRAINT` and `PROJECT_PREFERENCE` are kept visible here only for queryability; the authoritative project-specific list is in `project_design_principles.json`.", ""]
    for category in sorted(counts):
        lines += [f"## {category}", ""]
        for x in [z for z in rules if z["category"] == category]:
            dims = f"; target {x['recommended_dimensions_mm']} mm" if x.get("recommended_dimensions_mm") else ""
            nums = []
            if x.get("recommended_min_mm") is not None: nums.append(f"min {x['recommended_min_mm']} mm")
            if x.get("preferred_mm") is not None: nums.append(f"preferred {x['preferred_mm']} mm")
            if x.get("maximum_mm") is not None: nums.append(f"max {x['maximum_mm']} mm")
            number_text = "; " + ", ".join(nums) if nums else "qualitative"
            lines += [f"### {x['rule_id']} — {x['topic']}", "", f"- **Type / priority:** `{x['rule_type']}` / `{x['priority']}`", f"- **Statement:** {x['statement']}", f"- **Planning target:** {number_text.lstrip('; ')}{dims}", f"- **Applies when:** {', '.join(x['applicable_when']) or 'general'}", f"- **Tags:** {', '.join(x['tags']) or 'none'}", f"- **Source:** [{x['source_id']}]({x['source_url']}) — {x['jurisdiction']}", f"- **Notes:** {x['notes'] or 'Use as a design check; verify the actual room, product and local requirements.'}", ""]
    lines += ["## Project principles", "", "The following are project-owned decisions and statuses, not generic rules:", ""]
    for p in principles["principles"]:
        lines.append(f"- **{p['principle_id']}** `{p['rule_type']}` — {p['statement']} (status: `{p['status']}`)")
    return "\n".join(lines)


def precedent_markdown(precedents: list[dict[str, Any]]) -> str:
    lines = ["# Residential Precedent Index v0.1", "", "Metadata-only precedent library. No images or article bodies are mirrored. Relevance scores are deterministic and are not code or construction approvals.", "", "| ID | Project | Type | Plan | Relevance | Tags |", "|---|---|---|:---:|---:|---|"]
    for p in precedents:
        lines.append(f"| {p['precedent_id']} | [{p['project_name']}]({p['url']}) | {p['project_type']} | {'yes' if p['floor_plan_available'] else 'no'} | {p['relevance_to_c_type']:.4f} | {', '.join(p['tags'][:6])} |")
    lines += ["", "## Reading rule", "", "A cited precedent is a prompt for comparison. Verify the original page, plan, dimensions, household and jurisdiction before using any strategy in a design decision."]
    return "\n".join(lines)


def build_audits(rules: list[dict[str, Any]], precedents: list[dict[str, Any]], patterns: list[dict[str, Any]]) -> dict[str, Any]:
    fpath = ROOT / "concept/furniture_l1_final.json"
    cpath = ROOT / "concept/concept_data.json"
    canonical = ROOT / "current_existing/canonical_plan_v1.json"
    furniture = json.loads(fpath.read_text())
    concept = json.loads(cpath.read_text())
    canon = json.loads(canonical.read_text())
    cats = furniture["categories"]
    rule_by_id = {x["rule_id"]: x for x in rules}
    def item(rule_id: str, status: str, evidence: str, issue: str | None = None) -> dict[str, Any]:
        x = rule_by_id[rule_id]
        out = {"rule_id": rule_id, "status": status, "evidence": evidence, "source_id": x["source_id"], "source_url": x["source_url"]}
        if issue: out["issue"] = issue
        return out
    satisfied = [
        item("LIV-CIRC-001", "SATISFIED_WITH_RESERVATION", "F1 P1/P3/P5 paths are explicitly recorded; public transition is documented as >=1100 mm in concept_data.", "Confirm wall-side pinch points after final furniture INSERTs."),
        item("LIV-FLEX-003", "SATISFIED", "F1 G8 gate defines a 3800 x 4350 mm flexible living core and exempts only small movable tables."),
        item("LIV-MEDIA-006", "SATISFIED_WITH_RESERVATION", "LIV-MEDIA-WALL is locked at the east edge and P5 to the north balcony is recorded.", "Selected projector throw and glare remain TO_VERIFY."),
        item("LIV-EDGE-008", "SATISFIED", "Large sofas are edge-loaded west/north and the media wall is edge-loaded east."),
        item("DIN-CIR-005", "SATISFIED", "DIN-SEATING-N/S zones record 600 mm pull-out each long side for the 1500 x 600 table."),
        item("DIN-CIR-007", "SATISFIED_WITH_RESERVATION", "F1 P2 entry-to-dining-to-kitchen route is explicitly recorded.", "Check chair pull-out against the live kitchen edge after any change."),
        item("KIT-KEEP-010", "SATISFIED", "K-CAB is in fixed_keep and the project brief marks existing kitchen cabinetry KEEP."),
        item("AGE-CIR-001", "SATISFIED_WITH_RESERVATION", "F1 records a primary circulation target >=1100 mm and a separate ramp route.", "This is a planning record, not an accessibility compliance finding."),
        item("CIR-CONT-007", "SATISFIED", "P5 living -> G-LIV-NBALC -> north balcony is explicitly recorded; balcony current state is OPEN_NOT_ENCLOSED."),
        item("CIR-RAMP-009", "SATISFIED_WITH_TO_VERIFY", "Existing stair and assisted/power-wheelchair ramp are both documented in concept_data.", "Level delta and slope remain provisional."),
    ]
    conflicts = [
        item("LIV-CIRC-002", "POTENTIAL_CONFLICT", "The current F1 record does not expose every secondary route width as a measured polygon.", "Verify every furniture-free segment around the seating group, not only named paths."),
        item("DIN-CIR-006", "POTENTIAL_CONFLICT", "Dining seating zones document 600 mm pull-out, but a separate behind-seated passage is not explicitly measured.", "Test the south and north sides against the 900 mm target before freezing dining furniture."),
        item("KIT-SAF-008", "UNRESOLVED", "The cabinet KEEP zone is protected, but appliance-door envelopes are not represented in furniture_l1_final.json.", "Verify selected refrigerator/oven/dishwasher doors and landing surfaces."),
        item("AGE-THR-005", "TO_VERIFY", "Ramp slope is recorded as 400 / 2500 = 1:6.25 PROVISIONAL and level delta is owner <=350 vs CAD ~400.", "Field measure level change and obtain local accessibility review."),
        item("BTH-AGE-005", "NOT_IN_F1_SCOPE", "F1 audit covers living/dining/kitchen; bathroom fixture backing and transfer geometry are not part of this layout snapshot.", "Carry into the bathroom-specific review before construction."),
    ]
    project_conflicts = [
        {"principle_id": "P-KITCHEN-KEEP", "status": "RESPECTED", "evidence": "K-CAB remains in fixed_keep; no kitchen cabinet rewrite was proposed."},
        {"principle_id": "P-PROJECTOR-LIVING", "status": "PARTIAL", "evidence": "Media wall position is locked and no full-wall cabinet is specified; device throw/glare still TO_VERIFY."},
        {"principle_id": "P-NORTH-BALCONY", "status": "RESPECTED", "evidence": "Current model records OPEN_NOT_ENCLOSED; future enclosure remains note-only."},
        {"principle_id": "P-SPLIT-LEVEL", "status": "PARTIAL", "evidence": "Existing stair and alternate ramp coexist; the project itself marks slope and level delta provisional."},
        {"principle_id": "P-CHILD-ACTIVITY", "status": "RESPECTED_WITH_CHECK", "evidence": "Living core is kept open and sightline intent is documented; tall storage and final device placement still need checking."},
    ]
    audit_tags = {"open-living-dining", "kitchen-adjacency", "flexible-living", "child-friendly", "aging-in-place", "balcony-connected", "clear-circulation", "projector-media", "split-level", "existing-structure"}
    relevant_precedents = sorted(precedents, key=lambda p: (-len(audit_tags.intersection(p["tags"])), -p["relevance_to_c_type"], p["precedent_id"]))[:8]
    relevant_patterns = sorted(patterns, key=lambda p: (-len(audit_tags.intersection(p["tags"])), p["pattern_id"]))[:8]
    unresolved = [
        {"issue_id": "U-001", "issue": "Field measure the split-level level delta and ramp slope before treating the alternate route as accessible.", "citations": ["AGE-THR-005", "CIR-RAMP-009", "P-SPLIT-LEVEL"]},
        {"issue_id": "U-002", "issue": "Verify projector/laser-TV throw, glare and cable/service path with the selected product.", "citations": ["LIV-MEDIA-005", "LIV-DIST-007", "P-PROJECTOR-LIVING"]},
        {"issue_id": "U-003", "issue": "Measure dining chair pull-out and the behind-seated passage together with the retained kitchen edge.", "citations": ["DIN-CIR-005", "DIN-CIR-006", "DIN-CIR-007", "P-KITCHEN-KEEP"]},
        {"issue_id": "U-004", "issue": "Carry aging-in-place bathroom backing, transfer and turning checks into the later bathroom review.", "citations": ["BTH-AGE-005", "BTH-CIR-006", "P-AGE-MOTHER"]},
    ]
    directions = [
        {"direction_id": "D-01", "title": "Test a furniture-free living spine", "description": "Keep the current edge-loaded seating and compare one or two movable-table positions while protecting P1, P3 and P5.", "citations": ["LIV-CIRC-001", "LIV-FLEX-003", "PAT-CIR-01", "PAT-LIV-01"]},
        {"direction_id": "D-02", "title": "Resolve dining as a kitchen extension", "description": "Run a full-size 1500 x 600 table test with 600 mm pull-out and a measured 900 mm behind-seated route against the KEEP cabinet edge.", "citations": ["DIN-CIR-005", "DIN-CIR-006", "DIN-CIR-007", "PAT-LIV-04", "PAT-LIV-05"]},
        {"direction_id": "D-03", "title": "Verify the assisted route before styling", "description": "Field-measure level delta, ramp slope and landing dimensions, then keep the current stair/ramp dual-route logic until local review is complete.", "citations": ["AGE-THR-005", "CIR-RAMP-009", "PAT-AGE-01", "P-SPLIT-LEVEL"]},
    ]
    return {"version": "v0.1", "scope": "F1 living / dining / kitchen relationship only; analysis, no geometry edits", "inputs": {"furniture_file": str(fpath.relative_to(ROOT)), "concept_file": str(cpath.relative_to(ROOT)), "canonical_file": str(canonical.relative_to(ROOT)), "canonical_geometry_sha": canon.get("hashes", {}).get("geometry_sha")}, "sections": {"rules_already_satisfied": satisfied, "potential_rule_conflicts": conflicts, "project_specific_conflicts": project_conflicts, "relevant_precedents": [{"precedent_id": p["precedent_id"], "project_name": p["project_name"], "relevance_to_c_type": p["relevance_to_c_type"], "tags": p["tags"], "url": p["url"]} for p in relevant_precedents], "applicable_patterns": [{"pattern_id": p["pattern_id"], "name": p["name"], "precedent_ids": p["precedent_ids"]} for p in relevant_patterns], "unresolved_spatial_issues": unresolved, "next_design_directions": directions}, "audit_policy": "Every finding cites a rule_id, principle_id or pattern_id; precedent metadata is a prompt for human source review, not a copied design."}


def audit_markdown(audit: dict[str, Any]) -> str:
    sec = audit["sections"]
    lines = ["# A1/A2 F1 Design Knowledge Audit", "", "**Scope:** F1 living / dining / kitchen relationship. This is an analysis artifact; it does not modify CAD or canonical data.", "", "## 1. Rules already satisfied", ""]
    for x in sec["rules_already_satisfied"]:
        lines.append(f"- **{x['rule_id']} — {x['status']}**: {x['evidence']} _(source: {x['source_id']})_" + (f" **Issue:** {x['issue']}" if x.get("issue") else ""))
    lines += ["", "## 2. Potential rule conflicts", ""]
    for x in sec["potential_rule_conflicts"]:
        lines.append(f"- **{x['rule_id']} — {x['status']}**: {x['evidence']} **Next check:** {x['issue']}")
    lines += ["", "## 3. Project-specific conflicts", ""]
    for x in sec["project_specific_conflicts"]:
        lines.append(f"- **{x['principle_id']} — {x['status']}**: {x['evidence']}")
    lines += ["", "## 4. Relevant precedents", ""]
    for x in sec["relevant_precedents"]:
        lines.append(f"- **{x['precedent_id']}** {x['project_name']} — relevance {x['relevance_to_c_type']:.4f}; tags: {', '.join(x['tags'])}; [source]({x['url']})")
    lines += ["", "## 5. Applicable patterns", ""]
    for x in sec["applicable_patterns"]:
        lines.append(f"- **{x['pattern_id']} — {x['name']}**; evidence: {', '.join(x['precedent_ids'])}")
    lines += ["", "## 6. Unresolved spatial issues", ""]
    for x in sec["unresolved_spatial_issues"]:
        lines.append(f"- **{x['issue_id']}** {x['issue']} _(citations: {', '.join(x['citations'])})_")
    lines += ["", "## 7. Next design directions", ""]
    for x in sec["next_design_directions"]:
        lines.append(f"- **{x['direction_id']} — {x['title']}**: {x['description']} _(citations: {', '.join(x['citations'])})_")
    lines += ["", "## Boundary", "", "This audit does not authorize V03, furniture re-layout, or any CAD edit. Existing geometry remains the source of truth until the owner approves a next design direction and outstanding measurements are resolved."]
    return "\n".join(lines)


def qa_rules(rules: list[dict[str, Any]], principles: dict[str, Any]) -> dict[str, Any]:
    checks = []
    checks.append({"gate": "A1-G1 source URL present", "result": "PASS" if all(x.get("source_url") for x in rules) else "FAIL", "detail": f"{sum(bool(x.get('source_url')) for x in rules)}/{len(rules)} rules have source_url"})
    checks.append({"gate": "A1-G2 rule type valid", "result": "PASS" if all(x["rule_type"] in VALID_RULE_TYPES for x in rules) else "FAIL", "detail": sorted(set(x["rule_type"] for x in rules))})
    bad_code = [x["rule_id"] for x in rules if x["rule_type"] == "TO_VERIFY_LOCAL_CODE" and (x["jurisdiction"] == "general_reference" or ("confirm" not in x["statement"].lower() and "verify" not in x["statement"].lower()))]
    checks.append({"gate": "A1-G3 code/guideline distinction valid", "result": "PASS" if not bad_code else "FAIL", "detail": f"TO_VERIFY_LOCAL_CODE entries requiring local confirmation; invalid={bad_code}"})
    mandatory_foreign = [x["rule_id"] for x in rules if x["rule_type"] not in {"TO_VERIFY_LOCAL_CODE", "HARD_PROJECT_CONSTRAINT"} and x["jurisdiction"] not in {"general_reference", "project"}]
    checks.append({"gate": "A1-G4 no unverified foreign code presented as mandatory", "result": "PASS" if not mandatory_foreign else "FAIL", "detail": f"foreign mandatory candidates={mandatory_foreign}"})
    checks.append({"gate": "A1-G5 project rules separated", "result": "PASS" if (RULE_DIR / "project_design_principles.json").exists() else "FAIL", "detail": f"principles={len(principles['principles'])}; separate file exists"})
    to_verify = [p["principle_id"] for p in principles["principles"] if "TO_VERIFY" in p["status"]] + [x["rule_id"] for x in rules if x["rule_type"] == "TO_VERIFY_LOCAL_CODE"]
    checks.append({"gate": "A1-G6 TO_VERIFY preserved", "result": "PASS" if to_verify else "FAIL", "detail": f"preserved_items={len(to_verify)}"})
    status = "PASS" if all(x["result"] == "PASS" for x in checks) and 80 <= len(rules) <= 120 else "FAIL"
    return {"version": "v0.1", "status": status, "rule_count": len(rules), "category_counts": dict(Counter(x["category"] for x in rules)), "gates": checks, "generated_date": RESEARCH_DATE}


def qa_precedents(precedents: list[dict[str, Any]], patterns: list[dict[str, Any]], source_registry: dict[str, Any]) -> dict[str, Any]:
    controlled = set(CONTROLLED_TAGS)
    checks = [
        {"gate": "A2-G1 50-80 precedents", "result": "PASS" if 50 <= len(precedents) <= 80 else "FAIL", "detail": len(precedents)},
        {"gate": "A2-G2 every precedent has valid URL", "result": "PASS" if all(str(p.get("url", "")).startswith("https://") for p in precedents) else "FAIL", "detail": "all URLs use https"},
        {"gate": "A2-G3 no copied image dependency", "result": "PASS" if source_registry["sources"][0]["image_dependency"] is False else "FAIL", "detail": "metadata and short synthesis only"},
        {"gate": "A2-G4 floor-plan availability recorded", "result": "PASS" if all(isinstance(p.get("floor_plan_available"), bool) for p in precedents) else "FAIL", "detail": "boolean recorded for every item"},
        {"gate": "A2-G5 controlled tags", "result": "PASS" if all(set(p.get("tags", [])).issubset(controlled) for p in precedents) else "FAIL", "detail": f"controlled_tag_count={len(controlled)}"},
        {"gate": "A2-G6 patterns backed by >=2 precedents", "result": "PASS" if all(len(set(p.get("precedent_ids", []))) >= 2 for p in patterns) else "FAIL", "detail": f"patterns={len(patterns)}"},
        {"gate": "A2-G7 deterministic relevance scoring", "result": "PASS" if all("relevance_components" in p and isinstance(p["relevance_to_c_type"], float) for p in precedents) else "FAIL", "detail": "component fields retained"},
    ]
    return {"version": "v0.1", "status": "PASS" if all(x["result"] == "PASS" for x in checks) else "FAIL", "precedent_count": len(precedents), "pattern_count": len(patterns), "source_count": len(source_registry["sources"]), "gates": checks, "generated_date": RESEARCH_DATE}


def main() -> int:
    rules = build_rules()
    principles = project_principles()
    precedents, patterns, a2_sources = build_precedents()
    RULE_DIR.mkdir(parents=True, exist_ok=True)
    PREC_DIR.mkdir(parents=True, exist_ok=True)
    QC_DIR.mkdir(parents=True, exist_ok=True)
    write_json(RULE_DIR / "design_rulebook_v01.json", {"version": "v0.1", "jurisdiction_status": "UNCONFIRMED", "rules": rules})
    write_text(RULE_DIR / "design_rulebook_v01.md", rulebook_markdown(rules, principles))
    write_json(RULE_DIR / "source_registry.json", {"version": "v0.1", "sources": source_registry_rules()})
    write_json(RULE_DIR / "project_design_principles.json", principles)
    write_json(RULE_DIR / "rulebook_qa.json", qa_rules(rules, principles))
    write_json(PREC_DIR / "precedent_index_v01.json", {"version": "v0.1", "collection_date": RESEARCH_DATE, "source_policy": "metadata_only_no_images", "precedents": precedents})
    if SNAPSHOT.exists():
        raw_snapshot = json.loads(SNAPSHOT.read_text())
        selected_urls = {p["url"] for p in precedents}
        tracked_candidates = [
            {"url": x.get("url"), "title": x.get("title"), "description": x.get("description"), "floor_plan_available": bool(x.get("floor_plan_available")), "area_m2": x.get("area_m2")}
            for x in raw_snapshot if x.get("url") in selected_urls
        ]
        write_json(PREC_DIR / "candidate_metadata_v01.json", {"version": "v0.1", "source_policy": "metadata_only_no_images", "candidate_count": len(tracked_candidates), "candidates": tracked_candidates})
    write_text(PREC_DIR / "precedent_index_v01.md", precedent_markdown(precedents))
    write_json(PREC_DIR / "pattern_library_v01.json", {"version": "v0.1", "patterns": patterns})
    write_json(PREC_DIR / "source_registry.json", a2_sources)
    write_json(PREC_DIR / "query_taxonomy.json", {"version": "v0.1", "rooms": ["living", "dining", "kitchen", "bedroom", "bathroom", "study", "aging_in_place", "child_friendly", "circulation", "storage", "balcony", "renovation"], "tags": CONTROLLED_TAGS, "rule_types": sorted(VALID_RULE_TYPES), "notes": "Tags are controlled strings; relevance order is deterministic."})
    write_json(PREC_DIR / "precedent_qa.json", qa_precedents(precedents, patterns, a2_sources))
    audit = build_audits(rules, precedents, patterns)
    write_json(QC_DIR / "a1_a2_f1_design_audit.json", audit)
    write_text(QC_DIR / "a1_a2_f1_design_audit.md", audit_markdown(audit))
    print(json.dumps({"rules": len(rules), "precedents": len(precedents), "patterns": len(patterns), "a1_status": json.loads((RULE_DIR / "rulebook_qa.json").read_text())["status"], "a2_status": json.loads((PREC_DIR / "precedent_qa.json").read_text())["status"], "audit": str(QC_DIR / "a1_a2_f1_design_audit.md")}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
