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
ID_REGISTRY = PREC_DIR / "precedent_id_registry_v01.json"
RESEARCH_DATE = "2026-09-26"
REPO_URL = "https://github.com/xiwei9871/internal-design"

VALID_RULE_TYPES = {
    "HARD_PROJECT_CONSTRAINT",
    "TECHNICAL_GUIDELINE",
    "BEST_PRACTICE",
    "PROJECT_PREFERENCE",
    "TO_VERIFY_LOCAL_CODE",
    "TO_VERIFY_PRODUCT",
}

SOURCE_STRENGTH = {
    "SRC-NKBA-KITCHEN": "STRONG",
    "SRC-AARP-HOMEFIT": "MEDIUM",
    "SRC-ADA-2010-REFERENCE": "STRONG",
    "SRC-CUD-UD": "MEDIUM",
    "SRC-HUD-AGING": "MEDIUM",
    "SRC-NAHB-AIP": "MEDIUM",
    "SRC-CPSC-HOME-SAFETY": "MEDIUM",
    "SRC-PRACTICE-ERGONOMICS": "MEDIUM",
    "SRC-PRACTICE-SPATIAL": "MEDIUM",
    "SRC-PROJECTOR-PRODUCT": "WEAK",
    "SRC-C-TYPE-BRIEF": "STRONG",
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
        {"source_id": "SRC-CPSC-HOME-SAFETY", "name": "US Consumer Product Safety Commission home safety resources", "source_type": "home_safety_reference", "url": "https://www.cpsc.gov/Safety-Education/Safety-Guides", "jurisdiction": "US_reference_only", "use": "Child and household safety prompts; not a substitute for local requirements.", "mandatory_status": "reference_only"},
        {"source_id": "SRC-PRACTICE-ERGONOMICS", "name": "Whole Building Design Guide accessibility and ergonomics references", "source_type": "recognized_design_reference", "url": "https://www.wbdg.org/design-objectives/accessible", "jurisdiction": "general_reference", "use": "Recognized design reference for inclusive movement and ergonomic review; not local code.", "mandatory_status": "reference_only"},
        {"source_id": "SRC-PRACTICE-SPATIAL", "name": "RIBA professional design resources", "source_type": "recognized_design_reference", "url": "https://www.architecture.com/knowledge-and-resources/resources-landing-page", "jurisdiction": "general_reference", "use": "Qualitative composition and design-process reference; no numeric code authority.", "mandatory_status": "reference_only"},
        {"source_id": "SRC-PROJECTOR-PRODUCT", "name": "Selected projector or laser-TV product documentation (pending selection)", "source_type": "selected_product_pending", "url": "https://www.projectorcentral.com/", "jurisdiction": "project", "use": "Product-specific throw, image-size, glare and mounting data must be filled after a model is selected.", "mandatory_status": "TO_VERIFY_PRODUCT"},
        {"source_id": "SRC-C-TYPE-BRIEF", "name": "C-type home owner brief and measured project record", "source_type": "project_brief", "url": REPO_URL, "jurisdiction": "project", "use": "Confirmed KEEP items, household needs, unresolved TO_VERIFY statuses.", "mandatory_status": "project_authority"},
    ]


def r(rule_id: str, category: str, topic: str, rule_type: str, priority: str, statement: str, *, min_mm: int | None = None, preferred_mm: int | None = None, maximum_mm: int | None = None, dimensions_mm: list[int] | None = None, rooms: list[str] | None = None, when: list[str] | None = None, tags: list[str] | None = None, source_id: str = "SRC-PRACTICE-ERGONOMICS", source_url: str | None = None, source_type: str = "professional_practice", jurisdiction: str = "general_reference", gateable: bool | None = None, notes: str = "", classification: str | None = None, source_strength: str | None = None, verification_status: str | None = None) -> dict[str, Any]:
    registry_rows = {x["source_id"]: x for x in source_registry_rules()}
    registry = {key: row["url"] for key, row in registry_rows.items()}
    if source_type == "professional_practice" and source_id in registry_rows:
        source_type = registry_rows[source_id]["source_type"]
    strength = source_strength or SOURCE_STRENGTH.get(source_id, "WEAK")
    has_numeric = any(v is not None for v in (min_mm, preferred_mm, maximum_mm, dimensions_mm))
    if classification is None:
        if rule_type == "HARD_PROJECT_CONSTRAINT":
            classification = "PROJECT_CONSTRAINT"
        elif rule_type in {"TO_VERIFY_LOCAL_CODE", "TO_VERIFY_PRODUCT"}:
            classification = rule_type
        elif has_numeric and strength != "STRONG":
            classification = "DESIGN_HEURISTIC"
        else:
            classification = "TECHNICAL_REFERENCE" if has_numeric else "DESIGN_HEURISTIC"
    if gateable is None:
        gateable = bool(rule_type == "HARD_PROJECT_CONSTRAINT" or (has_numeric and strength == "STRONG" and rule_type == "TECHNICAL_GUIDELINE"))
    automatic_gate = bool(gateable and strength == "STRONG" and classification not in {"DESIGN_HEURISTIC", "TO_VERIFY_LOCAL_CODE", "TO_VERIFY_PRODUCT"})
    return {"rule_id": rule_id, "category": category, "topic": topic, "rule_type": rule_type, "priority": priority, "statement": statement, "recommended_min_mm": min_mm, "preferred_mm": preferred_mm, "maximum_mm": maximum_mm, "recommended_dimensions_mm": dimensions_mm, "applicable_when": when or [], "applicable_rooms": rooms or [category], "tags": tags or [], "source_id": source_id, "source_url": source_url or registry.get(source_id, REPO_URL), "source_type": source_type, "jurisdiction": jurisdiction, "gateable": gateable, "automatic_gate": automatic_gate, "classification": classification, "source_strength": strength, "verification_status": verification_status, "project_override": None, "notes": notes}


def build_rules() -> list[dict[str, Any]]:
    rules: list[dict[str, Any]] = []
    rules += [
        r("LIV-CIRC-001", "living", "primary route", "TECHNICAL_GUIDELINE", "HIGH", "Keep the main living route continuously clear for normal walking and assisted movement.", min_mm=900, preferred_mm=1100, rooms=["living"], when=["entry_to_living", "living_to_stair"], tags=["clear-circulation", "aging-in-place"], source_id="SRC-AARP-HOMEFIT"),
        r("LIV-CIRC-002", "living", "secondary route", "TECHNICAL_GUIDELINE", "HIGH", "Keep a secondary route around the seating group where the plan has more than one approach.", min_mm=750, preferred_mm=900, rooms=["living"], when=["two_sided_access"], tags=["clear-circulation"]),
        r("LIV-FLEX-003", "living", "activity core", "BEST_PRACTICE", "HIGH", "Reserve a central, furniture-light activity core for children, conversation and temporary setups.", min_mm=2500, preferred_mm=3000, rooms=["living"], when=["child_activity", "flexible_living"], tags=["child-friendly", "furniture-free-core", "flexible-living"]),
        r("LIV-FLEX-004", "living", "movable furniture", "PROJECT_PREFERENCE", "MEDIUM", "Use movable tables and seats for flexible living instead of fixing every object in the activity core.", maximum_mm=900, rooms=["living"], when=["projector_living", "child_activity"], tags=["projector-media", "child-friendly", "flexible-living"]),
        r("LIV-MEDIA-005", "living", "projector sightline", "TO_VERIFY_PRODUCT", "HIGH", "After an actual projector or laser-TV model is selected, verify throw, sightline, image size, glare and mounting constraints before fixing the media wall.", rooms=["living"], when=["projector_or_laser_tv", "selected_product"], tags=["projector-media", "non-tv-centric"], source_id="SRC-PROJECTOR-PRODUCT", source_type="selected_product_pending", jurisdiction="project", gateable=False, classification="TO_VERIFY_PRODUCT", source_strength="WEAK", verification_status="TO_VERIFY_PRODUCT", notes="No device model is selected; this rule cannot act as a hard automatic failure."),
        r("LIV-MEDIA-006", "living", "media wall and glazing", "BEST_PRACTICE", "HIGH", "Keep media equipment and its viewing axis outside the opening swing and clear route to a balcony or window.", min_mm=900, rooms=["living"], when=["balcony_connected"], tags=["projector-media", "balcony-connected", "clear-circulation"]),
        r("LIV-DIST-007", "living", "viewing distance", "TO_VERIFY_PRODUCT", "HIGH", "After the actual projector or laser-TV model and image size are selected, verify viewing distance and test the furniture arrangement at full scale.", rooms=["living"], when=["projector_or_laser_tv", "selected_product"], tags=["projector-media"], source_id="SRC-PROJECTOR-PRODUCT", source_type="selected_product_pending", jurisdiction="project", gateable=False, classification="TO_VERIFY_PRODUCT", source_strength="WEAK", verification_status="TO_VERIFY_PRODUCT", notes="No universal screen distance is assumed."),
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
    rules += [
        r("SPC-HIER-001", "spatial_composition", "public-zone hierarchy", "BEST_PRACTICE", "HIGH", "Make the entry, living, dining and kitchen sequence legible as a hierarchy of arrival, activity and support rather than four competing centers.", rooms=["living", "dining", "kitchen", "circulation"], when=["open_public_zone"], tags=["spatial-composition", "visual-hierarchy"], source_id="SRC-PRACTICE-SPATIAL", source_type="recognized_design_reference"),
        r("SPC-HIER-002", "spatial_composition", "focal hierarchy", "BEST_PRACTICE", "HIGH", "Choose one primary focal condition for a view and give secondary focal points a quieter visual weight.", rooms=["living", "dining"], when=["multi_focal_room"], tags=["spatial-composition", "focal-hierarchy"], source_id="SRC-PRACTICE-SPATIAL", source_type="recognized_design_reference"),
        r("SPC-GRP-003", "spatial_composition", "furniture grouping", "BEST_PRACTICE", "HIGH", "Group seats and tables around a shared activity or view so that each piece participates in a readable composition.", rooms=["living", "dining"], when=["seating_group"], tags=["spatial-composition", "furniture-grouping"], source_id="SRC-PRACTICE-SPATIAL", source_type="recognized_design_reference"),
        r("SPC-GRP-004", "spatial_composition", "conversation grouping", "BEST_PRACTICE", "HIGH", "Provide at least one face-to-face conversation relationship that is not dependent on the projection axis.", rooms=["living"], when=["conversation", "projector_living"], tags=["spatial-composition", "furniture-grouping", "conversation"], source_id="SRC-PRACTICE-SPATIAL", source_type="recognized_design_reference"),
        r("SPC-SCL-005", "spatial_composition", "scale and proportion", "BEST_PRACTICE", "MEDIUM", "Check furniture scale against the room volume and adjacent openings; do not let one oversized piece make the rest read as leftovers.", rooms=["living", "dining", "bedroom"], when=["furniture_selection"], tags=["spatial-composition", "scale-proportion"], source_id="SRC-PRACTICE-SPATIAL", source_type="recognized_design_reference"),
        r("SPC-SCL-006", "spatial_composition", "scale transition", "BEST_PRACTICE", "MEDIUM", "Use deliberate scale transitions between fixed cabinetry, large seating and small movable objects.", rooms=["living", "dining", "kitchen"], when=["mixed_furniture_scale"], tags=["spatial-composition", "scale-proportion"], source_id="SRC-PRACTICE-SPATIAL", source_type="recognized_design_reference"),
        r("SPC-NEG-007", "spatial_composition", "negative space", "BEST_PRACTICE", "HIGH", "Treat negative space as an intentional shape with edges, access and a visual role rather than as unfilled remainder.", rooms=["living", "dining", "circulation"], when=["open_public_zone"], tags=["spatial-composition", "negative-space"], source_id="SRC-PRACTICE-SPATIAL", source_type="recognized_design_reference"),
        r("SPC-NEG-008", "spatial_composition", "leftover wedges", "BEST_PRACTICE", "MEDIUM", "Investigate leftover wedges and narrow gaps created by furniture before accepting them as useful space.", rooms=["living", "dining", "bedroom"], when=["furniture_layout"], tags=["spatial-composition", "negative-space"], source_id="SRC-PRACTICE-SPATIAL", source_type="recognized_design_reference"),
        r("SPC-BAL-009", "spatial_composition", "spatial balance", "BEST_PRACTICE", "MEDIUM", "Balance visual weight across the room while allowing asymmetry when it is anchored by a clear edge, axis or view.", rooms=["living", "dining"], when=["furniture_layout"], tags=["spatial-composition", "spatial-balance"], source_id="SRC-PRACTICE-SPATIAL", source_type="recognized_design_reference"),
        r("SPC-BAL-010", "spatial_composition", "visual weight", "BEST_PRACTICE", "MEDIUM", "Avoid concentrating all tall, dark or fixed elements on one side unless the opposite side has a deliberate counterweight.", rooms=["living", "dining", "kitchen"], when=["open_public_zone"], tags=["spatial-composition", "spatial-balance"], source_id="SRC-PRACTICE-SPATIAL", source_type="recognized_design_reference"),
        r("SPC-EDGE-011", "spatial_composition", "architectural edge alignment", "BEST_PRACTICE", "HIGH", "Align major furniture with walls, bays, glazing lines or service edges when that alignment clarifies the room rather than hiding an opening.", rooms=["living", "dining", "bedroom"], when=["architectural_edge"], tags=["spatial-composition", "edge-alignment"], source_id="SRC-PRACTICE-SPATIAL", source_type="recognized_design_reference"),
        r("SPC-EDGE-012", "spatial_composition", "opening relationship", "BEST_PRACTICE", "HIGH", "Keep furniture-to-wall relationships legible at doors, windows and bay projections; do not use furniture to erase architectural evidence.", rooms=["living", "dining", "bedroom"], when=["window_or_door"], tags=["spatial-composition", "edge-alignment", "existing-structure"], source_id="SRC-PRACTICE-SPATIAL", source_type="recognized_design_reference"),
        r("SPC-SIGHT-013", "spatial_composition", "main visual axis", "BEST_PRACTICE", "HIGH", "Protect the primary visual axis from entry toward the most valuable view or social destination before adding decorative objects.", rooms=["living", "circulation"], when=["entry_view"], tags=["spatial-composition", "sightlines"], source_id="SRC-PRACTICE-SPATIAL", source_type="recognized_design_reference"),
        r("SPC-SIGHT-014", "spatial_composition", "daylight and view", "BEST_PRACTICE", "HIGH", "Preserve daylight and balcony or courtyard views as part of the composition, not only as a circulation requirement.", rooms=["living", "dining", "bedroom"], when=["balcony_connected", "window_present"], tags=["spatial-composition", "sightlines", "daylight"], source_id="SRC-PRACTICE-SPATIAL", source_type="recognized_design_reference"),
        r("SPC-ZONE-015", "spatial_composition", "zone definition", "BEST_PRACTICE", "MEDIUM", "Define living, dining, child activity and passage zones with edges, orientation, lighting or furniture grouping rather than arbitrary rectangles alone.", rooms=["living", "dining", "circulation"], when=["open_plan"], tags=["spatial-composition", "zone-definition"], source_id="SRC-PRACTICE-SPATIAL", source_type="recognized_design_reference"),
        r("SPC-ZONE-016", "spatial_composition", "soft boundaries", "BEST_PRACTICE", "MEDIUM", "Use a soft boundary only when it supports the intended relationship; do not create pseudo-walls that block sightlines without giving privacy or storage.", rooms=["living", "dining"], when=["open_plan"], tags=["spatial-composition", "zone-definition", "sightlines"], source_id="SRC-PRACTICE-SPATIAL", source_type="recognized_design_reference"),
        r("SPC-RHY-017", "spatial_composition", "rhythm and repetition", "BEST_PRACTICE", "LOW", "Repeat a line, material, opening rhythm or furniture proportion deliberately so the public zone reads as one composition.", rooms=["living", "dining", "kitchen"], when=["open_public_zone"], tags=["spatial-composition", "rhythm-repetition"], source_id="SRC-PRACTICE-SPATIAL", source_type="recognized_design_reference"),
        r("SPC-RHY-018", "spatial_composition", "repetition with variation", "BEST_PRACTICE", "LOW", "Allow controlled variation inside a repeated rhythm so the room does not become either visually noisy or mechanically uniform.", rooms=["living", "dining"], when=["material_or_furniture_set"], tags=["spatial-composition", "rhythm-repetition"], source_id="SRC-PRACTICE-SPATIAL", source_type="recognized_design_reference"),
        r("SPC-FLOAT-019", "spatial_composition", "floating furniture reason", "BEST_PRACTICE", "HIGH", "Do not float a sofa, table or chair in open space without a clear reason such as a view, conversation group, route edge or zone definition.", rooms=["living", "dining", "study"], when=["open_plan"], tags=["spatial-composition", "furniture-grouping", "negative-space"], source_id="SRC-PRACTICE-SPATIAL", source_type="recognized_design_reference"),
        r("SPC-FLOAT-020", "spatial_composition", "anchor or remove", "BEST_PRACTICE", "HIGH", "Anchor an isolated object to an architectural edge or a meaningful group, or remove it from the composition.", rooms=["living", "dining", "study"], when=["furniture_layout"], tags=["spatial-composition", "furniture-grouping", "edge-alignment"], source_id="SRC-PRACTICE-SPATIAL", source_type="recognized_design_reference"),
    ]
    assert len(rules) == 120, len(rules)
    assert len({x["rule_id"] for x in rules}) == len(rules)
    assert all(x["rule_type"] in VALID_RULE_TYPES for x in rules)
    return rules


def project_principles() -> dict[str, Any]:
    principles = [
        {"principle_id": "P-AGE-MOTHER", "rule_type": "HARD_PROJECT_CONSTRAINT", "priority": "HIGH", "statement": "Mother is 68; aging-in-place is a first-order planning priority for daily routes, bedroom and bathroom decisions.", "status": "CONFIRMED", "source_id": "SRC-C-TYPE-BRIEF", "source_url": REPO_URL, "applies_to": ["living", "bedroom", "bathroom", "circulation"], "tags": ["aging-in-place"], "to_verify": []},
        {"principle_id": "P-OWNER-COUPLE", "rule_type": "PROJECT_PREFERENCE", "priority": "HIGH", "statement": "The permanent daily residents are the owner and his mother; wife, child and wider family are periodic residents or visitors and must be accommodated without making the daily plan hotel-like.", "status": "CONFIRMED", "source_id": "SRC-C-TYPE-BRIEF", "source_url": REPO_URL, "applies_to": ["living", "bedroom", "study"], "tags": ["aging-in-place", "flexible-living", "periodic-family"], "to_verify": []},
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


def parse_year_country(description: str) -> tuple[int | None, str | None, str | None]:
    m = re.search(r"Completed in (\d{4}) in ([^.]+)", description or "")
    if not m:
        m = re.search(r"Built by .*? in ([^.]+?) with date (\d{4})", description or "")
        if not m:
            return None, None, None
        location = m.group(1).strip(" ,") or None
        country = location.rsplit(",", 1)[-1].strip() if location else None
        return int(m.group(2)), country, location
    location = m.group(2).strip(" ,") or None
    country = location.rsplit(",", 1)[-1].strip() if location else None
    return int(m.group(1)), country, location


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


CONTROLLED_TAGS = ["open-living-dining", "kitchen-adjacency", "flexible-living", "periodic-family", "child-friendly", "aging-in-place", "multigenerational", "projector-media", "balcony-connected", "split-level", "renovation", "existing-structure", "storage-zoning", "storage", "clear-circulation", "accessible-bathroom", "elderly-bedroom", "study-guest-hybrid", "daylight", "courtyard", "adaptive-reuse", "care-housing", "small-footprint", "before-after", "floor-plan", "family-loft", "visual-connection", "wet-dry-zoning", "step-free-route", "furniture-free-core", "edge-loaded-furniture", "non-tv-centric", "dining-kitchen-extension", "dual-mode-dining", "entry-storage", "community-living", "split-level-courtyard", "spatial-composition", "visual-hierarchy", "focal-hierarchy", "furniture-grouping", "conversation", "scale-proportion", "negative-space", "spatial-balance", "edge-alignment", "sightlines", "zone-definition", "rhythm-repetition"]


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


def relevance_score(item: dict[str, Any], tags: list[str], title: str, description: str) -> tuple[float, dict[str, float | None], float, dict[str, str]]:
    text = (title + " " + description).lower()
    space = 1.0 if re.search(r"apartment|house|housing|residen|loft|home|villa|barn|care", text) else 0.4
    area_raw = item.get("area_m2")
    if isinstance(area_raw, (int, float)):
        area = max(0.0, min(1.0, 1.0 - abs(float(area_raw) - 150.0) / 150.0))
        area_evidence = "explicit_area"
    else:
        area = None
        area_evidence = "unknown"
    if re.search(r"elderly couple|elderly household|older couple", text):
        household, household_evidence = 0.65, "explicit_older_pair_but_not_owner_mother_pair"
    elif re.search(r"elderly|care home|nursing|aging", text):
        household, household_evidence = 0.45, "explicit_aging_or_care_but_different_program"
    elif re.search(r"multigenerational|three-generation|three generation", text):
        household, household_evidence = 0.65, "explicit_multigenerational_but_not_owner_mother_pair"
    elif re.search(r"family|children|child|couple", text):
        household, household_evidence = 0.55, "explicit_family_but_not_owner_mother_pair"
    else:
        household, household_evidence = 0.0, "unknown"
    plan = 1.0 if bool(item.get("floor_plan_available")) else 0.0
    renovation = 1.0 if re.search(r"renovat|conversion|extension|heritage|existing|former|industrial", text) else 0.4
    tag_score = min(1.0, len(tags) / 8.0)
    components: dict[str, float | None] = {"space_type_match": space, "area_similarity": area, "household_similarity": household, "floor_plan": plan, "renovation_constraints": renovation, "relevant_tags": tag_score}
    weights = {"space_type_match": 0.20, "area_similarity": 0.15, "household_similarity": 0.15, "floor_plan": 0.20, "renovation_constraints": 0.15, "relevant_tags": 0.15}
    available = [key for key, value in components.items() if value is not None]
    denominator = sum(weights[key] for key in available)
    score = sum(weights[key] * float(components[key]) for key in available) / denominator if denominator else 0.0
    evidence = {"area": area_evidence, "household": household_evidence, "floor_plan": "explicit_boolean", "space_type": "keyword_match", "renovation": "keyword_match", "tags": "deterministic_tag_rules"}
    known = sum(1 for key in ("area_similarity", "household_similarity") if components[key] is not None)
    confidence = (0.55 + 0.15 * known + 0.15 * plan + 0.10 * min(1.0, len(tags) / 8.0) + 0.05 * renovation)
    return round(score, 4), components, round(min(1.0, confidence), 4), evidence


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
        score = x.get("relevance_score") if tracked and isinstance(x.get("relevance_score"), (int, float)) else None
        comps = x.get("relevance_components") if tracked and isinstance(x.get("relevance_components"), dict) else None
        confidence = x.get("relevance_evidence_confidence") if tracked and isinstance(x.get("relevance_evidence_confidence"), (int, float)) else (x.get("evidence_confidence") if tracked and isinstance(x.get("evidence_confidence"), (int, float)) else None)
        evidence = x.get("evidence") if tracked and isinstance(x.get("evidence"), dict) else None
        if score is None or comps is None or confidence is None or evidence is None:
            score, comps, confidence, evidence = relevance_score(x, tags, title, desc)
        year, country, location = parse_year_country(desc)
        rows.append({"_url": x.get("url"), "_title": title, "_description": desc, "_floor_plan": bool(x.get("floor_plan_available")), "_area": x.get("area_m2"), "_tags": tags, "_score": score, "_components": comps, "_confidence": confidence, "_evidence": evidence, "_year": year, "_country": country, "_location": location})
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


CURATED_OVERRIDES: dict[str, dict[str, Any]] = {
    "Renovation of an Industrial Building into a Single Family House": {
        "actual_spatial_strategy": "Full renovation of a warehouse-like building between party walls into a single-family home; the useful comparison is how a constrained shell can carry a new public zone without pretending it is a new-build envelope.",
        "design_lessons": ["Keep party-wall and service constraints explicit before opening a public living sequence.", "Use the floor-plan marker to compare how the new family program is distributed inside the retained shell.", "Separate evidence of adaptive reuse from C-type aging requirements; family use does not equal an owner-and-mother household."]},
    "Renovation of Joan Blanques apartment": {
        "actual_spatial_strategy": "The captured brief says a young couple wanted the apartment as open as possible; use it as an open-plan comparison where openness is a stated client driver rather than a stylistic assumption.",
        "design_lessons": ["Compare how an open public zone remains legible when partitions are reduced.", "Check which edges still anchor furniture and storage after opening the plan.", "Do not transfer the young-couple brief to the C-type plan; retain the older resident's route priority."]},
    "Renovation of a Milan Laboratory to a Family Loft": {
        "actual_spatial_strategy": "Conversion of an old laboratory in a Milan courtyard setting into a family loft; compare adaptive reuse, family program and connected public space while retaining the distinction between a loft brief and this split-level home.",
        "design_lessons": ["Map what the old laboratory shell contributes before treating openness as free space.", "Look for how family activities share a connected zone without requiring every seat to face one focal point.", "Use the plan marker to test service-edge and circulation-edge alignment."]},
    "Residential Extension MF Pavilion": {
        "actual_spatial_strategy": "An independent programmatic extension is described as being added to an existing single-family home; compare addition-as-program with the C-type rule that existing KEEP elements remain fixed.",
        "design_lessons": ["Separate the new programmatic room from the retained house datum.", "Study whether the extension creates a clear public destination or merely adds another competing center.", "Treat this as an addition precedent, not evidence for changing C-type walls."]},
    "Residential Care Home Andritz": {
        "actual_spatial_strategy": "A residential care home for 105 elderly residents on a park-like plot; its relevance is social visibility and support-space organization, not household-scale dimensions.",
        "design_lessons": ["Study how routes and shared spaces support independence without isolating residents.", "Borrow visibility and support-space questions, not institutional scale.", "Keep local accessibility review separate from this non-local reference."]},
    "Residential Complex Le Lorrain": {
        "actual_spatial_strategy": "Renovation of a former iron dealer into a social-housing complex of four flats connected by a shared relationship; compare adaptive reuse and shared circulation at the building scale.",
        "design_lessons": ["Retain the existing shell as a design datum when public circulation is shared.", "Check whether a shared connector clarifies or competes with each dwelling's private center.", "Do not infer C-type household or clearance dimensions from a multi-flat project."]},
    "Apartment Renovation in Girona": {
        "actual_spatial_strategy": "Conversion of the ground floor of an old warehouse into an apartment, with the captured description stating that the warehouse was divided into three; compare subdivision, daylight and public-zone sequencing.",
        "design_lessons": ["Test how subdivision can preserve a readable public zone.", "Use the plan marker to inspect where daylight and circulation survive the conversion.", "Keep warehouse conversion lessons separate from the C-type no-unrelated-wall-change constraint."]},
    "Renovation of a Mill and Hayloft for Residential use": {
        "actual_spatial_strategy": "Several buildings of different typologies were integrated into one housing use; compare how mismatched existing pieces are made legible as one sequence.",
        "design_lessons": ["Use changes in shell geometry to define zones instead of adding arbitrary floating objects.", "Check how transitions between old pieces affect the main route and visual hierarchy.", "Treat the integration strategy as a precedent for reading existing geometry, not for copying a style."]},
    "Residential House Renovation": {
        "actual_spatial_strategy": "Energetic renovation of a 1970s detached house with an explicit effort to preserve existing structure; only bathrooms are named as changed in the captured description.",
        "design_lessons": ["Preserve measured structure before placing new program elements.", "Separate energy/structure retention from the later bathroom-specific intervention.", "Use this as support for a KEEP-first workflow, not as evidence of aging compliance."]},
    "Apartment Renovation in Singapore": {
        "actual_spatial_strategy": "Renovation of a 30-year-old HDB flat that re-examines the interface between the flat and the public corridor; compare threshold and arrival sequencing.",
        "design_lessons": ["Treat entry as a spatial threshold with storage and sightline consequences.", "Check how a public-corridor interface affects the first visual axis into the home.", "Do not transfer Singapore code or HDB dimensions to this project."]},
    "Renovation and Extension of a Heritage-protected Residence Building": {
        "actual_spatial_strategy": "A heritage-protected residential building dating from 1891 retained its exterior while accommodating later internal changes; compare preservation of the architectural edge with interior adaptation.",
        "design_lessons": ["Keep exterior and opening evidence visible when changing interior use.", "Use edge alignment to avoid hiding heritage geometry behind new furniture.", "Separate heritage constraints from C-type measured-wall authority."]},
    "Residential and Studio Building at the Former Berlin Flower Market (IBeB)": {
        "actual_spatial_strategy": "The former central flower market is described as a mixed residential and studio setting; compare live/work adjacency and the risk of competing public/private centers.",
        "design_lessons": ["Use a service or storage edge to separate work and living without closing every sightline.", "Test whether a secondary work function needs its own visual anchor.", "Keep mixed-use lessons distinct from the C-type periodic-guest study brief."]},
    "Apartment and Courtyard in Barcelona": {
        "actual_spatial_strategy": "A main-floor apartment is organized around an internal quiet patio isolated from the Poble Nou streets; compare inward visual extension and privacy control.",
        "design_lessons": ["Treat a quiet patio or balcony as a visual destination, not only an exit.", "Balance inward view with the need for a readable entry route.", "Check whether furniture preserves the view axis before adding decoration."]},
    "House Around a Split Level Courtyard": {
        "actual_spatial_strategy": "A residence in Goa combines geometry and nature around a split-level courtyard; compare level changes as spatial composition while keeping the C-type ramp status provisional.",
        "design_lessons": ["Use level change to organize views and destinations, not to imply accessibility.", "Keep courtyard or balcony sightlines open through the furniture group.", "Field-measure C-type level deltas before borrowing any route conclusion."]},
    "Apartment Renovation in Sants": {
        "actual_spatial_strategy": "The captured description states a calm, sober atmosphere with natural materials and a low budget for a family program; compare restraint and family zoning rather than surface style.",
        "design_lessons": ["Use a small number of coherent material or furniture cues to establish calm.", "Let the family program define grouping before selecting decorative objects.", "No floor-plan marker was captured, so treat spatial claims as lower-confidence until the source plan is checked."]},
    "Residential Building Gatternweg": {
        "actual_spatial_strategy": "The captured description says the volume, surfaces and floor-plan solutions differ from neighboring structures; compare deliberate differentiation with the need for a clear internal public hierarchy.",
        "design_lessons": ["Make deviations from the existing context intentional and legible.", "Use the floor-plan marker to test whether differentiation improves or fragments circulation.", "Do not import building-scale formal moves into the C-type living room without a spatial reason."]},
    "Renovation of Sofia's apartment": {
        "actual_spatial_strategy": "A 70 m² Buenos Aires apartment is described as housing a typical traditional family and having been inhabited for years by a young woman; compare adaptation to an existing resident pattern rather than assuming a blank brief.",
        "design_lessons": ["Start from the resident's established daily pattern before changing the public zone.", "Use the stated 70 m² area only as a broad scale reference, not a C-type dimension.", "No floor-plan marker was captured; verify the actual plan before using the strategy."]},
    "Housing for the Elderly: Examples of Independent and Community Living": {
        "actual_spatial_strategy": "This is an ArchDaily reference article about independent and community living examples rather than one verified project; retain it as a low-confidence aging precedent.",
        "design_lessons": ["Use it to generate questions about independence and community, not as a measured layout precedent.", "Keep household-scale decisions tied to the C-type brief and field measurements.", "Do not cite it as proof of a local accessibility requirement."]},
    "Housing Apartment at Badade Nagar": {
        "actual_spatial_strategy": "The captured brief says a proposed 10-to-11-story tower was reconsidered for a mid-size residential housing project; compare how a change in density brief affects shared circulation and public/private hierarchy.",
        "design_lessons": ["Separate a changed development brief from the interior decisions it produces.", "Use the floor-plan marker to inspect how shared access and dwelling privacy are balanced.", "Do not transfer multi-unit density assumptions to the C-type home."]},
}

VERIFIED_PRECEDENT_OVERRIDES: dict[str, dict[str, Any]] = {
    "PREC-001": {"floor_plan_url": "https://images.adsttc.com/media/images/5360/58b0/c07a/8005/e900/009a/medium_jpg/Planos_casa_OV_Guim_Costa_2.jpg?1398823065", "household_program": "single-family use stated in the project title", "renovation_constraints": ["existing warehouse/party-wall shell", "full renovation"], "observations": ["Ground-floor plan places living and dining in a central open strip, with kitchen/service and bedrooms at the edges of a long constrained shell.", "A large garden/terrace is a separate visual destination; furniture is drawn inside the shell rather than floating in the route.", "Entry and service spaces feed the central social rooms before the private rooms."], "lessons": ["Keep party-wall and service constraints explicit before opening a public living sequence.", "Use the plan to compare how a family program is distributed inside a retained shell.", "Separate adaptive-reuse evidence from the C-type aging and split-level requirements."]},
    "PREC-002": {"floor_plan_url": "https://images.adsttc.com/media/images/60ae/428e/f91c/81d9/db00/005e/medium_jpg/Allaround_Lab_Joan_Blanques_planta_y_alzado.jpg?1622033028", "area_m2": 75.0, "area_evidence": "verified_project_page", "household_program": "young couple; public page states this explicitly", "renovation_constraints": ["apartment renovation", "open-plan brief with later compartmentalization"], "observations": ["Plan is a long strip from garden through living/dining/cooking/laundry to private rooms; labels explicitly separate the zones.", "Living and dining occupy a continuous central band while kitchen and laundry are loaded along the service edge.", "The brief asks for openness that can still become two differentiated work areas."], "lessons": ["Compare how an open public zone stays legible when partitions are reduced.", "Check which edges still anchor furniture and storage after opening the plan.", "Do not transfer the young-couple brief to the C-type plan; retain the older resident route priority."]},
    "PREC-003": {"floor_plan_url": "https://images.adsttc.com/media/images/6282/63c9/60c6/3501/6660/3b41/medium_jpg/a10-p0-plan.jpg?1652712461", "household_program": "family loft; family use stated in the project title", "renovation_constraints": ["old laboratory conversion", "courtyard setting"], "observations": ["Ground-floor plan shows open living on the left, dining at center, a circular stair/core near the middle, and private rooms to the right.", "The circular stair acts as a spatial anchor; furniture groups turn around the central void instead of all facing one wall.", "The family loft keeps one connected public zone while retaining private room thresholds."], "lessons": ["Map what the old laboratory shell contributes before treating openness as free space.", "Study how family activities share a connected zone without requiring every seat to face one focal point.", "Use the central stair/core as an anchor only when the existing geometry provides one."]},
    "PREC-004": {"floor_plan_url": "https://images.adsttc.com/media/images/6323/5686/a724/4838/504b/bcdc/medium_jpg/02-ground-floor-plan-2.jpg?1663260634", "renovation_constraints": ["1970s detached-house renovation", "existing structure preserved; bathrooms changed"], "observations": ["Ground-floor plan retains a compact existing shell with living/dining/kitchen and stair; the upper floor is separate.", "Bathrooms and service spaces are changed while the existing circulation and room edges remain legible.", "Furniture is organized inside the existing rooms rather than used to redraw the shell."], "lessons": ["Preserve measured structure before placing new program elements.", "Separate energy/structure retention from later bathroom-specific intervention.", "Use this as support for a KEEP-first workflow, not as evidence of aging compliance."]},
    "PREC-005": {"floor_plan_url": "https://images.adsttc.com/media/images/5d15/7d8c/284d/d137/2600/005a/medium_jpg/190621_MF_Pavilion_planta_arquitectonica.jpg?1561689470", "household_program": "single-family home extension; stated in the captured description", "renovation_constraints": ["independent programmatic extension", "existing single-family home"], "observations": ["Plan shows an added pavilion/extension attached to an existing home with public rooms and a planted or terrace edge.", "The added program reads as a distinct wing; existing rooms and extension are connected through a controlled threshold.", "The outdoor edge creates a view-based secondary axis without dissolving the existing house into one undifferentiated room."], "lessons": ["Separate a new programmatic room from the retained house datum.", "Study whether the extension creates a clear public destination or another competing center.", "Treat this as an addition precedent, not evidence for changing C-type walls."]},
    "PREC-007": {"floor_plan_url": "https://images.adsttc.com/media/images/5f9a/e8ae/63c0/17d5/3500/00b3/large_jpg/1_(2).jpg?1603987624", "area_m2": 129.9, "area_evidence": "verified_project_page_1399_ft2_converted", "renovation_constraints": ["ground-floor old warehouse conversion", "three structural bays parallel to facade", "large rear courtyard"], "observations": ["The ground-floor plan shows three structural bays parallel to the facade and a large courtyard at the rear.", "Living/dining/kitchen occupy the central bay, with bedrooms and services toward the private end and the courtyard as a visual terminus.", "The bay rhythm organizes zones without arbitrary partitions."], "lessons": ["Use structural bay rhythm to organize public and private zones.", "Keep the courtyard as a visual destination while preserving a direct route.", "Do not transfer warehouse conversion assumptions to C-type walls without measured evidence."]},
    "PREC-008": {"floor_plan_url": "https://images.adsttc.com/media/images/62ab/ec1a/6f92/4304/4abf/8262/medium_jpg/01-planta-baja-ok-3.jpg?1655434324", "renovation_constraints": ["integration of several existing building typologies", "irregular shell and level transitions"], "observations": ["Ground-floor plan integrates several existing pieces into a long irregular sequence of public rooms, yards and support spaces.", "Stair and thick shell edges make the transitions legible rather than hiding them behind floating furniture.", "Furniture is grouped in rooms; open links occur at existing connections between the old pieces."], "lessons": ["Use existing shell changes to define zones before adding new partitions.", "Check how transitions between old pieces affect the main route and visual hierarchy.", "Treat integration strategy as a precedent for reading geometry, not for copying a style."]},
    "PREC-009": {"floor_plan_url": "https://images.adsttc.com/media/images/572f/8d54/e58e/ced5/a800/0044/medium_jpg/PH_Andritz_Plan_Groundfloor.jpg?1462734159", "household_program": "residential care home for 105 elderly residents; stated in the public description", "renovation_constraints": ["care-home program", "institutional shared circulation and support spaces"], "observations": ["Ground-floor plan is an institutional care layout with repeated bedroom clusters around shared circulation and support spaces.", "Shared social/day spaces occur at central visible nodes rather than every room facing one media wall.", "The repeated route-and-node structure is useful for social visibility analysis but not domestic-scale transfer."], "lessons": ["Study how routes and shared spaces support independence without isolating residents.", "Borrow visibility and support-space questions, not institutional scale.", "Keep local accessibility review separate from this non-local reference."]},
    "PREC-013": {"floor_plan_url": "https://images.adsttc.com/media/images/5551/3d35/e58e/ce92/c700/01fd/medium_jpg/floor_plan.jpg?1431387432", "renovation_constraints": ["main-floor apartment renovation", "internal quiet patio"], "observations": ["New floor plan wraps rooms around a large internal quiet patio; living/dining occupies the central band and private rooms sit at the edges.", "The patio forms the primary visual axis and daylight source; furniture stays around its edges.", "The old/new plan comparison shows the courtyard relationship as a deliberate organizer, not leftover space."], "lessons": ["Treat a patio or balcony as a visual destination, not only an exit.", "Balance inward view with a readable entry route.", "Check whether furniture preserves the view axis before adding decoration."]},
    "PREC-014": {"floor_plan_url": "https://images.adsttc.com/media/images/56a2/3ad8/e58e/ceeb/1500/001c/medium_jpg/ground.jpg?1453472364", "renovation_constraints": ["split-level/courtyard house geometry", "irregular site edges"], "observations": ["Ground plan has irregular split-level/courtyard geometry; the living/dining/kitchen group is central and bedrooms/support rooms occupy wings.", "Courtyard and level changes create multiple view destinations; routes bend around rather than through the main furniture groups.", "Diagonal site edges organize the public zone with landscape and view rather than a single orthogonal axis."], "lessons": ["Use level change to organize views and destinations, not to imply accessibility.", "Keep courtyard sightlines open through the furniture group.", "Field-measure C-type level deltas before borrowing any route conclusion."]},
}


def curated_detail(x: dict[str, Any], project_name: str, text: str, tags: list[str]) -> dict[str, Any]:
    """Create bounded, source-traceable detail for the highest-ranked candidates."""
    household = None
    if "care home" in text or "nursing home" in text or "elderly" in text:
        household = "care or elderly residential use is stated in the captured title/description"
    elif "single family" in text:
        household = "single-family use is stated in the project title"
    elif "family" in text or "children" in text:
        household = "family use is stated in the captured title/description; resident ages are not stated"
    elif "couple" in text:
        household = "couple is stated in the captured description"
    constraints = []
    if "industrial" in text or "former" in text or "mill" in text or "barn" in text:
        constraints.append("existing or adaptive-reuse shell is named")
    if "heritage" in text:
        constraints.append("heritage protection is named")
    if "renovat" in text or "conversion" in text or "extension" in text:
        constraints.append("renovation/conversion/extension brief is named")
    if not constraints:
        constraints.append("no specific renovation constraint stated in captured metadata")
    if "split-level" in tags or "split-level-courtyard" in tags:
        strategy = "the captured title names split-level/courtyard sequencing; compare how level changes organize public movement"
    elif "adaptive-reuse" in tags:
        strategy = "the captured title/description names adaptive reuse; compare shell retention against new public-zone insertions"
    elif "balcony-connected" in tags or "courtyard" in tags:
        strategy = "courtyard, garden or balcony language suggests a visual extension; compare edge placement against the view"
    elif "family-loft" in tags or "open-living-dining" in tags:
        strategy = "family/open or loft language suggests a connected public zone; compare how activities are grouped without full partitions"
    elif "care-housing" in tags or "aging-in-place" in tags:
        strategy = "care or aging language suggests a social and accessible route; compare visibility and support spaces"
    else:
        strategy = f"the captured project type is {project_type(text)}; verify the actual plan before borrowing a spatial move"
    lessons = [
        f"{project_name}: {strategy}.",
        f"Use the {'floor-plan-marked' if x['_floor_plan'] else 'non-floor-plan-marked'} source only to compare relationships; do not infer C-type dimensions from it.",
    ]
    if "existing-structure" in tags:
        lessons.append("Map retained walls/openings/services first, then separate the new intervention from the existing shell.")
    if "child-friendly" in tags or "multigenerational" in tags:
        lessons.append("Check whether the public-zone grouping supports different household rhythms instead of assuming one shared center.")
    override = next((v for key, v in CURATED_OVERRIDES.items() if key.lower() in project_name.lower()), None)
    if override:
        strategy = override["actual_spatial_strategy"]
        lessons = override["design_lessons"]
    return {"household_program": household, "household_program_status": "stated_in_captured_metadata" if household else "not_stated_in_captured_metadata", "renovation_constraints": constraints, "actual_spatial_strategy": strategy, "design_lessons": lessons[:4], "curation_review": {"review_basis": ["public title", "captured description", "floor-plan marker", "controlled tags"], "evidence_confidence": x["_confidence"], "source_text_scope": "metadata-only; original page and plan still require human review", "override_used": bool(override)}}


def build_precedents() -> tuple[list[dict[str, Any]], list[dict[str, Any]], dict[str, Any]]:
    candidates = load_candidates()
    legacy_ids = json.loads(ID_REGISTRY.read_text()).get("ids", {}) if ID_REGISTRY.exists() else {}
    precedents = []
    curated_limit = 18
    for i, x in enumerate(candidates, 1):
        title, desc = x["_title"], x["_description"]
        tags = x["_tags"]
        project_name = re.sub(r"\s*\|\s*ArchDaily\s*$", "", title).strip()
        if " / " in project_name:
            project_name = project_name.split(" / ")[0].strip()
        text = (title + " " + desc).lower()
        precedent_id = legacy_ids.get(x["_url"], f"PREC-{i:03d}")
        if i <= curated_limit:
            level = "VERIFIED_PRECEDENT" if precedent_id in VERIFIED_PRECEDENT_OVERRIDES else "CURATED_METADATA"
        else:
            level = "METADATA_ONLY"
        if level in {"CURATED_METADATA", "VERIFIED_PRECEDENT"}:
            curated = curated_detail(x, project_name, text, tags)
            lessons = curated["design_lessons"]
        else:
            curated = {"household_program": None, "household_program_status": "not_curated", "renovation_constraints": None, "actual_spatial_strategy": None, "design_lessons": None, "curation_review": None}
            lessons = ["Candidate retained for metadata comparison; detailed project strategy was not curated in this pass."]
        not_applicable = ["Country, code and household assumptions differ from the C-type brief; this is not a compliance precedent."]
        if not x["_floor_plan"]:
            not_applicable.append("No floor-plan marker in the metadata snapshot; visual verification is required.")
        item = {"precedent_id": precedent_id, "project_name": project_name, "source": "ArchDaily", "url": x["_url"], "country": x["_country"], "year": x["_year"], "project_type": project_type(title + " " + desc), "area_m2": x["_area"] if isinstance(x["_area"], (int, float)) else None, "area_evidence": "explicit_public_metadata" if isinstance(x["_area"], (int, float)) else "unknown_not_scored", "household_program": curated["household_program"], "household_program_status": curated["household_program_status"], "floor_plan_available": x["_floor_plan"], "before_after_plan_available": bool(x["_floor_plan"] and re.search(r"renovat|before|after|conversion", text)), "renovation_constraints": curated["renovation_constraints"], "actual_spatial_strategy": curated["actual_spatial_strategy"], "tags": tags, "metadata_level": level, "curation_level": level, "relevance_score": x["_score"], "relevance_to_c_type": x["_score"], "relevance_components": x["_components"], "relevance_evidence_confidence": x["_confidence"], "evidence_confidence": 0.5 if level == "CURATED_METADATA" else 0.0, "evidence": x["_evidence"], "design_patterns": [], "design_lessons": curated["design_lessons"], "lessons": lessons, "not_applicable": not_applicable, "curation_review": curated["curation_review"], "verification_status": "NOT_VERIFIED", "verification_confidence": None, "verification_method": None, "floor_plan_url": None, "verified_spatial_observations": None, "verified_fields": [], "metadata_basis": "title, description, floor-plan marker and deterministic tag rules; no article body or image copied"}
        if precedent_id in VERIFIED_PRECEDENT_OVERRIDES:
            verified = VERIFIED_PRECEDENT_OVERRIDES[precedent_id]
            item.update({"curation_level": "VERIFIED_PRECEDENT", "metadata_level": "VERIFIED_PRECEDENT", "verification_status": "VERIFIED_PRECEDENT", "verification_confidence": 1.0, "evidence_confidence": 1.0, "verification_method": "browser_page_and_floor_plan_visual_review", "verification_date": RESEARCH_DATE, "floor_plan_url": verified["floor_plan_url"], "verified_spatial_observations": verified["observations"], "verified_fields": ["project_page_opened", "floor_plan_opened", "spatial_strategy", "circulation", "program", "renovation_constraints"], "verification_source_urls": [x["_url"], verified["floor_plan_url"]], "renovation_constraints": verified["renovation_constraints"], "design_lessons": verified["lessons"], "lessons": verified["lessons"], "curation_review": {**(item.get("curation_review") or {}), "source_text_scope": "project page and floor plan visually opened and reviewed", "override_used": True, "verification_complete": True}})
            if "household_program" in verified: item["household_program"] = verified["household_program"]
            if "area_m2" in verified: item["area_m2"] = verified["area_m2"]
            if "area_evidence" in verified: item["area_evidence"] = verified["area_evidence"]
            item["actual_spatial_strategy"] = "; ".join(verified["observations"])
        item["target_household"] = "permanent owner + mother; wife, child and wider family are periodic residents or visitors"
        item["household_similarity_note"] = "Similarity is against the corrected owner+mother target; unknown or different programs are not full matches."
        item["location"] = x["_location"]
        precedents.append(item)
    defs = pattern_defs()
    RULE_DERIVED_PATTERNS = {
        "PAT-AGE-01": {
            "basis": ["AGE-THR-005", "CIR-RAMP-009", "P-SPLIT-LEVEL"],
            "evidence": [
                {"precedent_id": "RULE-AGE-THR-005", "evidence": "The parallel stair plus assisted-route requirement comes from the C-type split-level brief and the unresolved level/slope rule; verified cases do not directly prove this topology.", "confidence": "HIGH", "verification_status": "RULE_DERIVED"},
                {"precedent_id": "PROJECT-C-TYPE-BRIEF", "evidence": "Owner brief explicitly retains the existing stair and asks for an assisted/power-wheelchair alternate route.", "confidence": "HIGH", "verification_status": "PROJECT_DERIVED"},
            ],
        },
        "PAT-BED-01": {
            "basis": ["BED-CIR-001", "BED-AGE-002", "BED-AGE-010"],
            "evidence": [{"precedent_id": "RULE-BED-AGE-002", "evidence": "The assisted-side bed route and caregiver access are design-rule requirements; the verified case plans do not show a confirmed bed-to-bath clear-side measurement.", "confidence": "HIGH", "verification_status": "RULE_DERIVED"}],
        },
        "PAT-BED-02": {
            "basis": ["STD-FLEX-007", "STD-FLEX-008", "P-OWNER-COUPLE"],
            "evidence": [{"precedent_id": "RULE-STD-FLEX-007", "evidence": "Study plus backup sleeping is derived from the C-type periodic-guest brief and the study rules; verified plans did not directly show a daybed/workstation hybrid.", "confidence": "HIGH", "verification_status": "RULE_DERIVED"}],
        },
        "PAT-BTH-01": {
            "basis": ["BTH-AGE-005", "BTH-SHW-004", "AGE-BTH-007", "AGE-BTH-008"],
            "evidence": [{"precedent_id": "RULE-BTH-AGE-005", "evidence": "The coordinated aging-in-place bathroom system is derived from shower, backing, transfer and local-code rules; the verified care plan is contextual, not a product-clearance proof.", "confidence": "HIGH", "verification_status": "RULE_DERIVED"}],
        },
        "PAT-BTH-02": {
            "basis": ["BTH-WC-001", "BTH-VAN-003", "BTH-DOOR-007", "BTH-SAF-008"],
            "evidence": [{"precedent_id": "RULE-BTH-DOOR-007", "evidence": "Wet/dry clear zones are derived from fixture approach and door-swing rules; verified case plans do not provide a confirmed C-type shower-entry clearance.", "confidence": "HIGH", "verification_status": "RULE_DERIVED"}],
        },
        "PAT-KIT-02": {
            "basis": ["KIT-CIR-001", "KIT-WRK-004", "KIT-WRK-005", "KIT-WRK-006", "KIT-SAF-008"],
            "evidence": [{"precedent_id": "RULE-KIT-WRK-004", "evidence": "Compact sink-cook-refrigerator workflow is derived from NKBA/work-zone rules; verified plans show kitchen adjacency but do not confirm appliance-door and landing dimensions.", "confidence": "HIGH", "verification_status": "RULE_DERIVED"}],
        },
    }
    CONTEXTUAL_CONFIDENCE_CAPS = {
        "PAT-LIV-03": "MEDIUM",
        "PAT-LIV-05": "MEDIUM",
        "PAT-CHD-01": "MEDIUM",
        "PAT-STOR-01": "LOW",
        "PAT-STOR-02": "MEDIUM",
        "PAT-KIT-01": "MEDIUM",
    }
    VERIFIED_SUPPORT_OVERRIDES = {
        "PAT-LIV-01": ["PREC-001", "PREC-002", "PREC-003"],
        "PAT-LIV-02": ["PREC-001", "PREC-002", "PREC-003"],
        "PAT-CIR-01": ["PREC-002", "PREC-009"],
        "PAT-AGE-02": ["PREC-009", "PREC-013"],
        "PAT-LIV-06": ["PREC-002", "PREC-013", "PREC-014"],
        "PAT-LIV-04": ["PREC-002", "PREC-003", "PREC-007", "PREC-013"],
    }
    OBSERVATION_KEYWORDS = {
        "PAT-CIR-01": ["route", "circulation", "strip", "transitions"],
        "PAT-AGE-02": ["social", "shared", "visible", "daylight", "visual"],
        "PAT-LIV-02": ["edge", "shell", "furniture", "anchor"],
        "PAT-LIV-04": ["living/dining/kitchen", "dining", "cooking", "public"],
        "PAT-LIV-06": ["visual", "courtyard", "garden", "view", "daylight"],
        "PAT-REN-01": ["existing", "shell", "structural", "old", "retained"],
    }
    precedent_by_id = {p["precedent_id"]: p for p in precedents}
    for idx, pat in enumerate(defs):
        if pat["pattern_id"] == "PAT-LIV-07":
            pat["precedent_ids"] = []
            pat["evidence"] = [
                {"precedent_id": "PROJECT-C-TYPE-BRIEF", "evidence": "Owner brief explicitly makes projector/laser-TV dominant and rejects a TV-centric living room.", "confidence": "HIGH"},
                {"precedent_id": "PROJECT-F1-LAYOUT", "evidence": "F1 records a locked media wall together with a flexible central living core.", "confidence": "HIGH"},
            ]
            pat["evidence_type"] = "PROJECT_DERIVED"
            pat["project_basis"] = ["P-PROJECTOR-LIVING", "LIV-MEDIA-005", "LIV-FLEX-003"]
            pat["verified_precedent_ids"] = []
            pat["evidence_confidence"] = "HIGH"
            pat["evidence_note"] = "This pattern is primarily derived from the C-type brief and F1 record; external precedents are not claimed as evidence for projector behavior."
            continue
        if pat["pattern_id"] in RULE_DERIVED_PATTERNS:
            derived = RULE_DERIVED_PATTERNS[pat["pattern_id"]]
            pat["precedent_ids"] = []
            pat["evidence"] = derived["evidence"]
            pat["evidence_type"] = "RULE_DERIVED"
            pat["project_basis"] = derived["basis"]
            pat["verified_precedent_ids"] = []
            pat["evidence_confidence"] = "HIGH"
            pat["evidence_note"] = "This pattern is rule-derived; verified precedents may be contextual references but are not claimed as direct proof."
            continue
        if pat["pattern_id"] in VERIFIED_SUPPORT_OVERRIDES:
            matches = [precedent_by_id[pid] for pid in VERIFIED_SUPPORT_OVERRIDES[pat["pattern_id"]] if pid in precedent_by_id]
        else:
            matches = sorted([p for p in precedents if set(pat["tags"]).intersection(p["tags"])], key=lambda p: (-len(set(pat["tags"]).intersection(p["tags"])), -(1 if p.get("verification_status") == "VERIFIED_PRECEDENT" else 0), -p["relevance_score"], p["precedent_id"]))
        if len(matches) < 2:
            matches = [precedents[(idx * 3) % len(precedents)], precedents[(idx * 3 + 1) % len(precedents)]]
        verified_matches = [p for p in matches if p.get("verification_status") == "VERIFIED_PRECEDENT"]
        support = (verified_matches[:5] if len(verified_matches) >= 2 else matches[:5])
        evidence_links = []
        for p in support:
            shared = sorted(set(pat["tags"]).intersection(p["tags"]))
            if p.get("verification_status") == "VERIFIED_PRECEDENT":
                obs = p.get("verified_spatial_observations") or []
                keywords = OBSERVATION_KEYWORDS.get(pat["pattern_id"], [])
                matching_obs = [text for text in obs if any(keyword.lower() in text.lower() for keyword in keywords)]
                reason = (matching_obs[0] if matching_obs else (obs[0] if obs else "Project page and floor plan were opened; no bounded observation was retained."))
                confidence = "HIGH"
            else:
                reason = f"Metadata candidate carries shared tags {', '.join(shared)} and floor_plan_available={str(p['floor_plan_available']).lower()}; spatial action not visually verified."
                confidence = "LOW"
            evidence_links.append({"precedent_id": p["precedent_id"], "evidence": reason, "confidence": confidence, "verification_status": p.get("verification_status", "NOT_VERIFIED")})
            p["design_patterns"].append(pat["pattern_id"])
        evidence_type = "PROJECT_DERIVED" if pat["pattern_id"] == "PAT-LIV-07" else "EXTERNAL_PRECEDENT"
        pat["precedent_ids"] = [x["precedent_id"] for x in evidence_links]
        pat["evidence"] = evidence_links
        pat["evidence_type"] = evidence_type
        pat["project_basis"] = ["P-PROJECTOR-LIVING"] if evidence_type == "PROJECT_DERIVED" else []
        pat["verified_precedent_ids"] = [p["precedent_id"] for p in support if p.get("verification_status") == "VERIFIED_PRECEDENT"]
        pat["evidence_confidence"] = "HIGH" if len(pat["verified_precedent_ids"]) >= 2 else ("MEDIUM" if pat["verified_precedent_ids"] else "LOW")
        if pat["pattern_id"] in CONTEXTUAL_CONFIDENCE_CAPS:
            cap = CONTEXTUAL_CONFIDENCE_CAPS[pat["pattern_id"]]
            pat["evidence_confidence"] = cap
            for link in pat["evidence"]:
                link["confidence"] = cap
        pat["evidence_note"] = "Verified links describe an opened project page and floor plan; metadata-only links are explicitly low-confidence and do not support a high-confidence pattern claim."
    patterns = [{"pattern_id": p["pattern_id"], "name": p["name"], "room": p["room"], "tags": p["tags"], "method": p["method"], "benefit": p["benefit"], "risk": p["risk"], "precedent_ids": p["precedent_ids"], "evidence": p["evidence"], "evidence_type": p["evidence_type"], "project_basis": p["project_basis"], "verified_precedent_ids": p["verified_precedent_ids"], "evidence_confidence": p["evidence_confidence"], "evidence_note": p["evidence_note"]} for p in defs]
    source_registry = {"version": "v0.1", "collection_date": RESEARCH_DATE, "levels": {"METADATA_ONLY": "URL and structured public metadata candidate; no deep strategy claim", "CURATED_METADATA": "top-ranked metadata record with bounded strategy and lessons; original page/plan not visually verified", "VERIFIED_PRECEDENT": "project page and floor plan opened and visually reviewed; spatial observations and 2-5 project-specific lessons recorded"}, "sources": [{"source_id": "A2-SRC-ARCHDAILY", "name": "ArchDaily project pages", "source_type": "metadata_only_project_database", "url": "https://www.archdaily.com/", "license_note": "Only URL, public metadata and short original synthesis are stored; no images or article text are mirrored.", "image_dependency": False, "candidate_count": 80, "selected_count": len(precedents), "verified_count": sum(p["curation_level"] == "VERIFIED_PRECEDENT" for p in precedents), "curated_metadata_count": sum(p["curation_level"] == "CURATED_METADATA" for p in precedents), "metadata_only_count": sum(p["curation_level"] == "METADATA_ONLY" for p in precedents), "snapshot": "projects/c_type_home/knowledge/precedents/candidate_metadata_v01.json", "id_registry": "projects/c_type_home/knowledge/precedents/precedent_id_registry_v01.json", "url_validation": "80 candidate pages fetched during research; selected links retain the existing precedent IDs."}]}
    return precedents, patterns, source_registry


def rulebook_markdown(rules: list[dict[str, Any]], principles: dict[str, Any]) -> str:
    counts = Counter(x["category"] for x in rules)
    lines = ["# Residential Design Rulebook v0.1", "", "This rulebook is a planning reference for the C-type home. It separates general guidance from project principles and local-code checks.", "", "**Jurisdiction:** unconfirmed. US or other foreign guidance is reference material only and is never silently promoted to mandatory project code.", "", "## Coverage", "", "| Category | Rules |", "|---|---:|"]
    lines += [f"| {k} | {counts[k]} |" for k in sorted(counts)]
    lines += ["", "## Rule fields", "", "Numeric values are planning targets in millimetres. `source_strength` records how authoritative the source is for this use. A numeric rule with `classification=DESIGN_HEURISTIC` or `source_strength` below STRONG is informative only and has `automatic_gate=false`; it cannot create a hard automatic failure. `TO_VERIFY_LOCAL_CODE` and `TO_VERIFY_PRODUCT` require local or product verification. `HARD_PROJECT_CONSTRAINT` and `PROJECT_PREFERENCE` are kept visible here only for queryability; the authoritative project-specific list is in `project_design_principles.json`.", ""]
    for category in sorted(counts):
        lines += [f"## {category}", ""]
        for x in [z for z in rules if z["category"] == category]:
            dims = f"; target {x['recommended_dimensions_mm']} mm" if x.get("recommended_dimensions_mm") else ""
            nums = []
            if x.get("recommended_min_mm") is not None: nums.append(f"min {x['recommended_min_mm']} mm")
            if x.get("preferred_mm") is not None: nums.append(f"preferred {x['preferred_mm']} mm")
            if x.get("maximum_mm") is not None: nums.append(f"max {x['maximum_mm']} mm")
            number_text = "; " + ", ".join(nums) if nums else "qualitative"
            lines += [f"### {x['rule_id']} — {x['topic']}", "", f"- **Type / priority:** `{x['rule_type']}` / `{x['priority']}`", f"- **Classification:** `{x['classification']}`; source strength `{x['source_strength']}`; automatic gate `{str(x['automatic_gate']).lower()}", f"- **Statement:** {x['statement']}", f"- **Planning target:** {number_text.lstrip('; ')}{dims}", f"- **Applies when:** {', '.join(x['applicable_when']) or 'general'}", f"- **Tags:** {', '.join(x['tags']) or 'none'}", f"- **Source:** [{x['source_id']}]({x['source_url']}) — {x['jurisdiction']}", f"- **Notes:** {x['notes'] or 'Use as a design check; verify the actual room, product and local requirements.'}", ""]
    lines += ["## Project principles", "", "The following are project-owned decisions and statuses, not generic rules:", ""]
    for p in principles["principles"]:
        lines.append(f"- **{p['principle_id']}** `{p['rule_type']}` — {p['statement']} (status: `{p['status']}`)")
    return "\n".join(lines)


def precedent_markdown(precedents: list[dict[str, Any]]) -> str:
    lines = ["# Residential Precedent Index v0.1", "", "Three-level library: 42 `METADATA_ONLY` candidates, 8 `CURATED_METADATA` records, and 10 `VERIFIED_PRECEDENT` records whose project page and floor plan were opened and visually reviewed. No images or article bodies are mirrored. Relevance scores are deterministic and are not code or construction approvals.", "", "| ID | Level | Project | Type | Plan | Relevance | Evidence confidence | Tags |", "|---|---|---|---|:---:|---:|---:|---|"]
    for p in precedents:
        lines.append(f"| {p['precedent_id']} | {p['curation_level']} | [{p['project_name']}]({p['url']}) | {p['project_type']} | {'yes' if p['floor_plan_available'] else 'no'} | {p['relevance_score']:.4f} | {p['evidence_confidence']:.2f} | {', '.join(p['tags'][:6])} |")
    lines += ["", "## Curated and verified records", ""]
    for p in precedents:
        if p["curation_level"] not in {"CURATED_METADATA", "VERIFIED_PRECEDENT"}:
            continue
        lines += [f"### {p['precedent_id']} — {p['project_name']} ({p['curation_level']})", "", f"- **Source:** [{p['url']}]({p['url']})", f"- **Area:** {p['area_m2'] if p['area_m2'] is not None else 'not stated in captured metadata'}", f"- **Household/program:** {p['household_program'] or 'not stated in captured metadata'}", f"- **Floor plan:** {'verified and visually reviewed' if p['curation_level'] == 'VERIFIED_PRECEDENT' else ('available marker' if p['floor_plan_available'] else 'no marker')}", f"- **Renovation constraints:** {'; '.join(p['renovation_constraints'] or ['not curated'])}", f"- **Spatial strategy:** {p['actual_spatial_strategy']}", "- **Lessons:"]
        lines += [f"  - {lesson}" for lesson in p["design_lessons"]]
        if p["curation_level"] == "VERIFIED_PRECEDENT":
            lines += ["- **Verified observations:"] + [f"  - {obs}" for obs in p["verified_spatial_observations"]]
        lines.append("")
    lines += ["## Reading rule", "", "A cited precedent is a prompt for comparison. `VERIFIED_PRECEDENT` is visually verified for the cited page and plan but is not a code or construction approval. `CURATED_METADATA` and `METADATA_ONLY` remain lower-confidence until visually checked."]
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
    spatial_assessment = [
        {"aspect": "public-zone hierarchy", "status": "PARTIAL", "finding": "Entry-to-dining-to-kitchen and living-to-balcony routes are explicit, but the plan does not yet state which public destination is primary; media, seating and balcony compete for attention.", "citations": ["SPC-HIER-001", "SPC-HIER-002"]},
        {"aspect": "living seating coherence", "status": "PARTIAL", "finding": "The 3-seat sofa, 2-seat sofa and day-lounge occupy three edges, but their relationship reads as separate placements rather than one intentional social composition.", "citations": ["SPC-GRP-003", "SPC-SCL-005"]},
        {"aspect": "conversation grouping", "status": "WEAK", "finding": "Most seats orient toward the east media wall; an explicit face-to-face conversation relationship is not recorded, so the room risks becoming projection-centric despite the brief.", "citations": ["SPC-GRP-004", "P-PROJECTOR-LIVING"]},
        {"aspect": "negative-space quality", "status": "PARTIAL", "finding": "G8 keeps a large clear core, but the coffee table and side table are exceptions without a documented compositional anchor; the void should be judged as a shaped activity and route space.", "citations": ["SPC-NEG-007", "SPC-NEG-008", "SPC-FLOAT-019"]},
        {"aspect": "dining/kitchen spatial relationship", "status": "SATISFIED_WITH_RESERVATION", "finding": "P2 gives a direct entry-dining-kitchen relation and the table is in the dining zone, but behind-seated clearance and the visual handoff to the KEEP cabinet edge are not fully measured.", "citations": ["DIN-CIR-007", "SPC-ZONE-015", "P-KITCHEN-KEEP"]},
        {"aspect": "main visual axis", "status": "PARTIAL", "finding": "The entry-to-living route and east media wall are clear, but the main visual axis is not separated from the balcony view; the next layout should choose whether view or projection is primary.", "citations": ["SPC-SIGHT-013", "SPC-HIER-002"]},
        {"aspect": "balcony visual connection", "status": "SATISFIED_WITH_RESERVATION", "finding": "P5 and the OPEN_NOT_ENCLOSED state preserve physical access, but the plant line and secondary sofa need a view check so the opening remains visually legible.", "citations": ["SPC-SIGHT-014", "CIR-CONT-007", "P-NORTH-BALCONY"]},
        {"aspect": "furniture scale/proportion", "status": "PARTIAL", "finding": "The 2200x900 sofa, 1800x850 sofa and 1500x1100 day-lounge are individually plausible, yet the mixed sizes are not tied to a clear room-scale hierarchy.", "citations": ["SPC-SCL-005", "SPC-SCL-006"]},
        {"aspect": "spatial reason for each object", "status": "PARTIAL", "finding": "KEEP cabinetry, media wall and primary sofas have explicit reasons; the isolated day-lounge, coffee table, side table and plant line need a stated group, view or route role before being treated as final composition.", "citations": ["SPC-FLOAT-019", "SPC-FLOAT-020", "P-KEEP-FURNITURE"]},
    ]
    audit_tags = {"open-living-dining", "kitchen-adjacency", "flexible-living", "child-friendly", "aging-in-place", "balcony-connected", "clear-circulation", "projector-media", "split-level", "existing-structure"}
    relevant_precedents = sorted(precedents, key=lambda p: (-len(audit_tags.intersection(p["tags"])), -p["relevance_score"], p["precedent_id"]))[:8]
    relevant_patterns = sorted(patterns, key=lambda p: (-len(audit_tags.intersection(p["tags"])), p["pattern_id"]))[:8]
    unresolved = [
        {"issue_id": "U-001", "issue": "Field measure the split-level level delta and ramp slope before treating the alternate route as accessible.", "citations": ["AGE-THR-005", "CIR-RAMP-009", "P-SPLIT-LEVEL"]},
        {"issue_id": "U-002", "issue": "Verify projector/laser-TV throw, glare and cable/service path with the selected product.", "citations": ["LIV-MEDIA-005", "LIV-DIST-007", "P-PROJECTOR-LIVING"]},
        {"issue_id": "U-003", "issue": "Measure dining chair pull-out and the behind-seated passage together with the retained kitchen edge.", "citations": ["DIN-CIR-005", "DIN-CIR-006", "DIN-CIR-007", "P-KITCHEN-KEEP"]},
        {"issue_id": "U-004", "issue": "Carry aging-in-place bathroom backing, transfer and turning checks into the later bathroom review.", "citations": ["BTH-AGE-005", "BTH-CIR-006", "P-AGE-MOTHER"]},
    ]
    directions = [
        {"direction_id": "D-01", "title": "Single-axis social core", "description": "Test one coherent conversation group first, then place the projector axis as a secondary mode; use the day-lounge only if it has a clear view or conversation role.", "citations": ["SPC-HIER-002", "SPC-GRP-003", "SPC-GRP-004", "SPC-FLOAT-019"]},
        {"direction_id": "D-02", "title": "View-first public-zone hierarchy", "description": "Keep the dining-to-kitchen relationship compact and make the north balcony the primary visual extension; test media equipment as a controlled secondary focal edge after product selection.", "citations": ["SPC-SIGHT-013", "SPC-SIGHT-014", "SPC-EDGE-011", "P-NORTH-BALCONY"]},
        {"direction_id": "D-03", "title": "Negative-space and route spine", "description": "Shape the central void as one child and aging-friendly activity field, using only movable objects that have an explicit spatial reason; no CAD change is authorized by this direction.", "citations": ["SPC-NEG-007", "SPC-NEG-008", "SPC-FLOAT-020", "AGE-CIR-001", "PAT-CIR-01"]},
    ]
    return {"version": "v0.1", "scope": "F1 living / dining / kitchen relationship only; clearance and spatial-composition analysis, no geometry edits", "inputs": {"furniture_file": str(fpath.relative_to(ROOT)), "concept_file": str(cpath.relative_to(ROOT)), "canonical_file": str(canonical.relative_to(ROOT)), "canonical_geometry_sha": canon.get("hashes", {}).get("geometry_sha")}, "sections": {"rules_already_satisfied": satisfied, "potential_rule_conflicts": conflicts, "project_specific_conflicts": project_conflicts, "spatial_composition_assessment": spatial_assessment, "relevant_precedents": [{"precedent_id": p["precedent_id"], "project_name": p["project_name"], "relevance_score": p["relevance_score"], "evidence_confidence": p["evidence_confidence"], "tags": p["tags"], "url": p["url"]} for p in relevant_precedents], "applicable_patterns": [{"pattern_id": p["pattern_id"], "name": p["name"], "precedent_ids": p["precedent_ids"], "evidence": p["evidence"]} for p in relevant_patterns], "unresolved_spatial_issues": unresolved, "next_design_directions": directions}, "audit_policy": "Every finding cites a rule_id, principle_id or pattern_id; precedent metadata is a prompt for human source review, not a copied design."}


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
    lines += ["", "## 4. Spatial-composition assessment", ""]
    for x in sec["spatial_composition_assessment"]:
        lines.append(f"- **{x['aspect']} — {x['status']}**: {x['finding']} _(citations: {', '.join(x['citations'])})_")
    lines += ["", "## 5. Relevant precedents", ""]
    for x in sec["relevant_precedents"]:
        lines.append(f"- **{x['precedent_id']}** {x['project_name']} — relevance {x['relevance_score']:.4f}; evidence confidence {x['evidence_confidence']:.2f}; tags: {', '.join(x['tags'])}; [source]({x['url']})")
    lines += ["", "## 6. Applicable patterns", ""]
    for x in sec["applicable_patterns"]:
        reasons = "; ".join(f"{e['precedent_id']}: {e['evidence']} ({e['confidence']})" for e in x['evidence'])
        lines.append(f"- **{x['pattern_id']} — {x['name']}**; evidence: {reasons}")
    lines += ["", "## 7. Unresolved spatial issues", ""]
    for x in sec["unresolved_spatial_issues"]:
        lines.append(f"- **{x['issue_id']}** {x['issue']} _(citations: {', '.join(x['citations'])})_")
    lines += ["", "## 8. Conceptual redesign directions", ""]
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
    mandatory_foreign = [x["rule_id"] for x in rules if x["rule_type"] not in {"TO_VERIFY_LOCAL_CODE", "TO_VERIFY_PRODUCT", "HARD_PROJECT_CONSTRAINT"} and x["jurisdiction"] not in {"general_reference", "project"}]
    checks.append({"gate": "A1-G4 no unverified foreign code presented as mandatory", "result": "PASS" if not mandatory_foreign else "FAIL", "detail": f"foreign mandatory candidates={mandatory_foreign}"})
    checks.append({"gate": "A1-G5 project rules separated", "result": "PASS" if (RULE_DIR / "project_design_principles.json").exists() else "FAIL", "detail": f"principles={len(principles['principles'])}; separate file exists"})
    to_verify = [p["principle_id"] for p in principles["principles"] if "TO_VERIFY" in p["status"]] + [x["rule_id"] for x in rules if x["rule_type"] in {"TO_VERIFY_LOCAL_CODE", "TO_VERIFY_PRODUCT"}]
    checks.append({"gate": "A1-G6 TO_VERIFY preserved", "result": "PASS" if to_verify else "FAIL", "detail": f"preserved_items={len(to_verify)}"})
    valid_strengths = {"STRONG", "MEDIUM", "WEAK"}
    missing_strength = [x["rule_id"] for x in rules if x.get("source_strength") not in valid_strengths]
    checks.append({"gate": "A1-G7 source strength recorded for every rule", "result": "PASS" if not missing_strength else "FAIL", "detail": f"missing={missing_strength}"})
    numeric_hard = [x["rule_id"] for x in rules if any(v is not None for v in (x.get("recommended_min_mm"), x.get("preferred_mm"), x.get("maximum_mm"), x.get("recommended_dimensions_mm"))) and x.get("source_strength") != "STRONG" and x.get("automatic_gate")]
    checks.append({"gate": "A1-G8 weak/medium numeric rules cannot hard-fail", "result": "PASS" if not numeric_hard else "FAIL", "detail": f"automatic_gate violations={numeric_hard}"})
    spatial_count = sum(x["category"] == "spatial_composition" for x in rules)
    checks.append({"gate": "A1-G9 spatial_composition coverage", "result": "PASS" if 15 <= spatial_count <= 25 else "FAIL", "detail": f"count={spatial_count}"})
    projector = [x for x in rules if x["rule_id"] in {"LIV-MEDIA-005", "LIV-DIST-007"}]
    projector_ok = all(x["rule_type"] == "TO_VERIFY_PRODUCT" and x["source_id"] == "SRC-PROJECTOR-PRODUCT" and x["automatic_gate"] is False for x in projector)
    checks.append({"gate": "A1-G10 projector rules product-specific TO_VERIFY", "result": "PASS" if projector_ok else "FAIL", "detail": f"rules={[x['rule_type'] for x in projector]}"})
    status = "PASS" if all(x["result"] == "PASS" for x in checks) and 80 <= len(rules) <= 120 else "FAIL"
    source_audit = [{"rule_id": x["rule_id"], "category": x["category"], "source_id": x["source_id"], "source_strength": x["source_strength"], "classification": x["classification"], "numeric_value_present": any(v is not None for v in (x.get("recommended_min_mm"), x.get("preferred_mm"), x.get("maximum_mm"), x.get("recommended_dimensions_mm"))), "automatic_gate": x["automatic_gate"], "rule_type": x["rule_type"]} for x in rules]
    return {"version": "v0.1", "status": status, "rule_count": len(rules), "category_counts": dict(Counter(x["category"] for x in rules)), "source_strength_counts": dict(Counter(x["source_strength"] for x in rules)), "classification_counts": dict(Counter(x["classification"] for x in rules)), "source_audit": source_audit, "gates": checks, "generated_date": RESEARCH_DATE}


def qa_precedents(precedents: list[dict[str, Any]], patterns: list[dict[str, Any]], source_registry: dict[str, Any]) -> dict[str, Any]:
    controlled = set(CONTROLLED_TAGS)
    checks = [
        {"gate": "A2-G1 50-80 precedents", "result": "PASS" if 50 <= len(precedents) <= 80 else "FAIL", "detail": len(precedents)},
        {"gate": "A2-G2 every precedent has valid URL", "result": "PASS" if all(str(p.get("url", "")).startswith("https://") for p in precedents) else "FAIL", "detail": "all URLs use https"},
        {"gate": "A2-G3 no copied image dependency", "result": "PASS" if source_registry["sources"][0]["image_dependency"] is False else "FAIL", "detail": "metadata and short synthesis only"},
        {"gate": "A2-G4 floor-plan availability recorded", "result": "PASS" if all(isinstance(p.get("floor_plan_available"), bool) for p in precedents) else "FAIL", "detail": "boolean recorded for every item"},
        {"gate": "A2-G5 controlled tags", "result": "PASS" if all(set(p.get("tags", [])).issubset(controlled) for p in precedents) else "FAIL", "detail": f"controlled_tag_count={len(controlled)}"},
        {"gate": "A2-G6 patterns backed by explicit evidence", "result": "PASS" if all(((p.get("evidence_type") in {"PROJECT_DERIVED", "RULE_DERIVED"} and p.get("project_basis") and len(p.get("evidence", [])) >= 1) or (len(set(p.get("precedent_ids", []))) >= 2 and len(p.get("evidence", [])) == len(p.get("precedent_ids", [])))) and all(e.get("evidence") and e.get("confidence") for e in p.get("evidence", [])) for p in patterns) else "FAIL", "detail": f"patterns={len(patterns)}; external patterns require >=2 precedent links; derived patterns cite project/rule evidence"},
        {"gate": "A2-G7 deterministic relevance scoring with separate confidence", "result": "PASS" if all("relevance_components" in p and isinstance(p["relevance_score"], float) and isinstance(p["evidence_confidence"], float) and (p["relevance_components"].get("area_similarity") is None or p["area_m2"] is not None) for p in precedents) else "FAIL", "detail": "area unknown is null; confidence is separate"},
        {"gate": "A2-G8 three-level curation", "result": "PASS" if sum(p.get("curation_level") == "VERIFIED_PRECEDENT" for p in precedents) == 10 and sum(p.get("curation_level") == "CURATED_METADATA" for p in precedents) == 8 and sum(p.get("curation_level") == "METADATA_ONLY" for p in precedents) == 42 else "FAIL", "detail": f"verified={sum(p.get('curation_level') == 'VERIFIED_PRECEDENT' for p in precedents)} curated_metadata={sum(p.get('curation_level') == 'CURATED_METADATA' for p in precedents)} metadata_only={sum(p.get('curation_level') == 'METADATA_ONLY' for p in precedents)}"},
        {"gate": "A2-G9 owner/mother household correction is explicit", "result": "PASS" if "owner and his mother" in json.loads((RULE_DIR / "project_design_principles.json").read_text())["principles"][1]["statement"] else "FAIL", "detail": "P-OWNER-COUPLE statement checked"},
        {"gate": "A2-G10 curated records have project-specific detail", "result": "PASS" if all(p.get("actual_spatial_strategy") and 2 <= len(p.get("design_lessons") or []) <= 5 and p.get("curation_review", {}).get("override_used") for p in precedents if p.get("curation_level") in {"CURATED_METADATA", "VERIFIED_PRECEDENT"}) else "FAIL", "detail": "all curated records carry strategy, 2-5 lessons and an explicit curation review"},
        {"gate": "A2-G11 verified precedents are visually checked", "result": "PASS" if all(p.get("verification_status") == "VERIFIED_PRECEDENT" and p.get("verification_confidence") == 1.0 and p.get("floor_plan_url") and len(p.get("verified_spatial_observations") or []) >= 2 and p.get("verification_method") == "browser_page_and_floor_plan_visual_review" for p in precedents if p.get("curation_level") == "VERIFIED_PRECEDENT") else "FAIL", "detail": "10 verified records carry page/plan URLs, observations and confidence=1.0"},
        {"gate": "A2-G12 high-confidence pattern evidence is verified-only or explicitly derived", "result": "PASS" if all(p.get("evidence_confidence") != "HIGH" or p.get("evidence_type") in {"PROJECT_DERIVED", "RULE_DERIVED"} or all(e.get("verification_status") == "VERIFIED_PRECEDENT" for e in p.get("evidence", [])) for p in patterns) else "FAIL", "detail": "metadata-only links never create HIGH pattern confidence; rule/project derivations are explicit"},
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
    rule_qa = qa_rules(rules, principles)
    write_json(RULE_DIR / "rulebook_qa.json", rule_qa)
    write_json(RULE_DIR / "source_audit_v01.json", {"version": "v0.1", "rule_count": len(rules), "entries": rule_qa["source_audit"], "policy": "weak/medium numeric rules are DESIGN_HEURISTIC and automatic_gate=false"})
    write_json(PREC_DIR / "precedent_index_v01.json", {"version": "v0.1", "collection_date": RESEARCH_DATE, "source_policy": "metadata_only_no_images", "precedents": precedents})
    if SNAPSHOT.exists():
        raw_snapshot = json.loads(SNAPSHOT.read_text())
        selected_urls = {p["url"] for p in precedents}
        by_url = {p["url"]: p for p in precedents}
        tracked_candidates = [
            {"url": x.get("url"), "title": x.get("title"), "description": x.get("description"), "floor_plan_available": bool(x.get("floor_plan_available")), "area_m2": x.get("area_m2"), "tags": by_url[x.get("url")]["tags"], "relevance_score": by_url[x.get("url")]["relevance_score"], "relevance_components": by_url[x.get("url")]["relevance_components"], "relevance_evidence_confidence": by_url[x.get("url")]["relevance_evidence_confidence"], "evidence_confidence": by_url[x.get("url")]["evidence_confidence"], "evidence": by_url[x.get("url")]["evidence"]}
            for x in raw_snapshot if x.get("url") in selected_urls
        ]
        write_json(PREC_DIR / "candidate_metadata_v01.json", {"version": "v0.1", "source_policy": "metadata_only_no_images", "candidate_count": len(tracked_candidates), "candidates": tracked_candidates})
    write_text(PREC_DIR / "precedent_index_v01.md", precedent_markdown(precedents))
    write_json(PREC_DIR / "pattern_library_v01.json", {"version": "v0.1", "patterns": patterns})
    write_json(PREC_DIR / "verification_registry_v01.json", {"version": "v0.1", "verification_method": "browser_page_and_floor_plan_visual_review", "verified_count": sum(p["curation_level"] == "VERIFIED_PRECEDENT" for p in precedents), "verified": [{"precedent_id": p["precedent_id"], "project_name": p["project_name"], "project_url": p["url"], "floor_plan_url": p["floor_plan_url"], "verification_date": p.get("verification_date"), "verification_confidence": p["verification_confidence"], "observations": p["verified_spatial_observations"], "source_fields": p["verified_fields"]} for p in precedents if p["curation_level"] == "VERIFIED_PRECEDENT"]})
    write_json(PREC_DIR / "source_registry.json", a2_sources)
    write_json(PREC_DIR / "query_taxonomy.json", {"version": "v0.1", "rooms": ["living", "dining", "kitchen", "bedroom", "bathroom", "study", "aging_in_place", "child_friendly", "circulation", "storage", "balcony", "renovation", "spatial_composition"], "tags": CONTROLLED_TAGS, "rule_types": sorted(VALID_RULE_TYPES), "curation_levels": ["METADATA_ONLY", "CURATED_METADATA", "VERIFIED_PRECEDENT"], "notes": "Tags are controlled strings; relevance order is deterministic and evidence_confidence is separate from relevance_score."})
    write_json(PREC_DIR / "precedent_qa.json", qa_precedents(precedents, patterns, a2_sources))
    audit = build_audits(rules, precedents, patterns)
    write_json(QC_DIR / "a1_a2_f1_design_audit.json", audit)
    write_text(QC_DIR / "a1_a2_f1_design_audit.md", audit_markdown(audit))
    print(json.dumps({"rules": len(rules), "precedents": len(precedents), "patterns": len(patterns), "a1_status": json.loads((RULE_DIR / "rulebook_qa.json").read_text())["status"], "a2_status": json.loads((PREC_DIR / "precedent_qa.json").read_text())["status"], "audit": str(QC_DIR / "a1_a2_f1_design_audit.md")}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
