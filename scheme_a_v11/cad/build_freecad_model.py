from __future__ import annotations

import json
import math
from pathlib import Path

import FreeCAD as App
import Mesh
import Part


ROOT = Path(__file__).resolve().parents[1]
V7 = ROOT.parent / "scheme_a_v7"
DATA = json.loads((V7 / "scheme_a_geometry.json").read_text(encoding="utf-8"))
SCALE_MM = DATA["metres_per_pixel"] * 1000.0
ORIGIN_X = 200.0
ORIGIN_Y = 1337.0
WALL_HEIGHT = 2700.0
WALL_THICKNESS = 120.0


def xy(px: float, py: float, z: float = 0.0) -> App.Vector:
    """Convert source PNG pixels to a bottom-left-origin millimetre model."""
    return App.Vector((px - ORIGIN_X) * SCALE_MM, (ORIGIN_Y - py) * SCALE_MM, z)


def polygon_prism(poly: list[list[float]], z0: float, z1: float) -> Part.Shape:
    points = [xy(x, y, z0) for x, y in poly]
    wire = Part.makePolygon(points + [points[0]])
    return Part.Face(wire).extrude(App.Vector(0, 0, z1 - z0))


def rect_box(rect_values: list[float], z0: float, z1: float) -> Part.Shape:
    x, y, w, h = rect_values
    p = xy(x, y + h, z0)
    return Part.makeBox(w * SCALE_MM, h * SCALE_MM, z1 - z0, p)


def add_props(obj, props: dict) -> None:
    for key, value in props.items():
        if isinstance(value, bool):
            obj.addProperty("App::PropertyBool", key, "Design").__setattr__(key, value)
        elif isinstance(value, (int, float)):
            obj.addProperty("App::PropertyLength", key, "Design")
            setattr(obj, key, float(value))
        else:
            obj.addProperty("App::PropertyString", key, "Design")
            setattr(obj, key, str(value))


def add_feature(doc, group, name, label, shape, color, props=None):
    obj = doc.addObject("PartDesign::Feature", name)
    obj.Label = label
    obj.Shape = shape
    view = getattr(obj, "ViewObject", None)
    if view is not None:
        view.ShapeColor = color
        view.LineColor = (0.18, 0.18, 0.16)
        view.DisplayMode = "Flat Lines"
    if props:
        add_props(obj, props)
    group.addObject(obj)
    return obj


def add_box(doc, group, name, label, rect_values, height, color, basis, z0=0.0, props=None):
    shape = rect_box(rect_values, z0, z0 + height)
    x, y, w, h = rect_values
    all_props = {
        "SourceRect": f"{x:g},{y:g},{w:g},{h:g} px",
        "Width": w * SCALE_MM,
        "Depth": h * SCALE_MM,
        "Height": height,
        "Basis": basis,
    }
    if props:
        all_props.update(props)
    return add_feature(doc, group, name, label, shape, color, all_props)


def add_layered_rect(doc, group, prefix, label, rect_values, layers, basis, colors):
    """Create a simple but inspectable furniture assembly from stacked boxes."""
    objs = []
    for index, (z0, z1, suffix) in enumerate(layers):
        color = colors[index % len(colors)]
        objs.append(add_box(doc, group, f"{prefix}_{index}", f"{label}·{suffix}", rect_values, z1 - z0, color, basis, z0))
    return objs


def add_window(doc, group, name, label, segment):
    x1, y1, x2, y2 = segment
    glass_thickness_px = 1.0  # about 10 mm at the A7 calibration
    if abs(x2 - x1) >= abs(y2 - y1):
        x = min(x1, x2)
        y = max(y1, y2)
        rect = [x, y - glass_thickness_px, abs(x2 - x1), glass_thickness_px]
    else:
        x = min(x1, x2)
        y = max(y1, y2)
        rect = [x - glass_thickness_px, y - abs(y2 - y1), glass_thickness_px, abs(y2 - y1)]
    shape = rect_box(rect, 850, 2100)
    return add_feature(
        doc,
        group,
        name.replace(" ", "_"),
        label,
        shape,
        (0.55, 0.78, 0.82),
        {"SourceSegment": f"{x1:g},{y1:g},{x2:g},{y2:g} px", "SillHeight": 850, "HeadHeight": 2100, "Basis": "A7 windows"},
    )


def add_door(doc, group, name, label, door):
    # A lightweight open leaf preserves the documented hinge and opening direction.
    hx, hy = door["hinge"]
    lx, ly = door["leaf"]
    x, y = min(hx, lx), min(hy, ly)
    w, h = max(abs(hx - lx), 35), max(abs(hy - ly), 35)
    rect = [x, y, w, h]
    return add_box(doc, group, name, label, rect, 2100, (0.66, 0.49, 0.29), "A7 door hinge/leaf", props={"Hinge": f"{hx:g},{hy:g} px", "Leaf": f"{lx:g},{ly:g} px"})


def add_bed(doc, group, prefix, label, rect_values):
    x, y, w, h = rect_values
    # Keep the source footprint exact; layer the visible parts so the render is legible.
    add_box(doc, group, prefix + "_frame", label + "·床架", rect_values, 220, (0.31, 0.18, 0.08), "A7 bed footprint", z0=80)
    mattress = [x + 7, y + 7, max(w - 14, 20), max(h - 14, 20)]
    add_box(doc, group, prefix + "_mattress", label + "·床垫", mattress, 260, (0.72, 0.66, 0.55), "A7 bed footprint", z0=300)
    # The source plan shows pillows at the right short end of each bed. Keep
    # the headboard on that end, against the room boundary, rather than across
    # the long side where it reads as a freestanding divider.
    head = [x + w - min(10, w * 0.08), y, min(10, w * 0.08), h]
    add_box(doc, group, prefix + "_headboard", label + "·薄型床头板", head, 620, (0.65, 0.45, 0.24), "A7 bed headboard; thin low panel", z0=300)
    duvet = [x + w * 0.08, y + h * 0.26, w * 0.84, h * 0.48]
    add_box(doc, group, prefix + "_duvet", label + "·被褥", duvet, 55, (0.46, 0.43, 0.38), "A7 bed footprint", z0=560)
    for i, px in enumerate((x + w * 0.56, x + w * 0.77)):
        pillow = [px, y + h * 0.10, w * 0.16, h * 0.15]
        add_box(doc, group, f"{prefix}_pillow_{i}", label + f"·枕头{i + 1}", pillow, 90, (0.82, 0.78, 0.68), "A7 bed footprint", z0=615)


def add_wardrobe(doc, group, prefix, label, rect_values):
    add_box(doc, group, prefix, label, rect_values, 2300, (0.68, 0.48, 0.25), "A7 custom wardrobe footprint")
    x, y, w, h = rect_values
    panel_w = max(w / 3, 10)
    for index in range(1, 3):
        panel = [x + panel_w * index - 3, y, 6, h]
        add_box(doc, group, f"{prefix}_panel_{index}", label + f"·分缝{index}", panel, 2250, (0.27, 0.15, 0.06), "custom wardrobe panel")


def add_chair(doc, group, prefix, rect_values):
    """Add a seat and an outer back so dining-chair orientation is readable."""
    x, y, w, h = rect_values
    add_box(doc, group, prefix + "_seat", "餐椅·座面", [x + 3, y + 3, w - 6, h - 6], 90, (0.50, 0.38, 0.24), "A7 dining chair envelope", z0=420)
    # The chairs above/below the table face toward its centre; put the back on
    # the outside edge of each rectangle, preserving the A7 footprint.
    outer_y = y if y < 870 else y + h - 8
    add_box(doc, group, prefix + "_back", "餐椅·靠背", [x + 3, outer_y, w - 6, 8], 380, (0.58, 0.43, 0.27), "A7 dining chair envelope", z0=510)


def add_sofa(doc, group, prefix, rect_values):
    """Build a directional sofa with seat, back and arms, not a featureless block."""
    x, y, w, h = rect_values
    add_box(doc, group, prefix + "_base", "客厅沙发·底座", rect_values, 360, (0.38, 0.34, 0.29), "A7 target 2200×900", z0=80)
    add_box(doc, group, prefix + "_seat", "客厅沙发·坐垫", [x + 8, y + 12, w - 16, h - 24], 170, (0.62, 0.59, 0.53), "A7 target 2200×900", z0=440)
    # The long right edge is the back side toward the room wall in the plan.
    add_box(doc, group, prefix + "_back", "客厅沙发·靠背", [x + w - 14, y + 12, 14, h - 24], 270, (0.52, 0.49, 0.44), "A7 target 2200×900", z0=600)
    for i, ay in enumerate((y + 10, y + h - 24)):
        add_box(doc, group, f"{prefix}_arm_{i}", "客厅沙发·扶手", [x + 4, ay, w - 18, 14], 230, (0.48, 0.44, 0.39), "A7 target 2200×900", z0=500)


def add_wc(doc, group, prefix, label, rect_values):
    """One-piece WC: tank against the left wall, bowl body projecting +X as a
    single connected volume.  No detached cylinder — the previous freestanding
    bowl column read as a stool in renders and is not on the plan."""
    x, y, w, h = rect_values
    ceramic = (0.92, 0.94, 0.91)
    basis = "TOTO/Kohler one-piece silhouette; tank on left wall, bowl front +X"
    # Tank: full-height one-piece cistern against the left wall.
    tank = [x + 4, y + 6, w * 0.34, h - 12]
    add_box(doc, group, prefix + "_tank", label + "·一体水箱", tank, 440, ceramic, basis, z0=380)
    # Bowl body: overlaps the tank front and projects toward +X so the whole
    # fixture reads as one connected piece, never a standalone column.
    bowl = [x + w * 0.30, y + 8, w * 0.58, h - 16]
    add_box(doc, group, prefix + "_bowl", label + "·盆体", bowl, 340, ceramic, basis, z0=60)
    # Rounded front cap fused to the bowl body for a bowl-like front edge.
    cap_center = xy(x + w * 0.30 + w * 0.58, y + h * 0.5, 60)
    cap = Part.makeCylinder((h - 16) * 0.5 * SCALE_MM, 340, cap_center, App.Vector(0, 0, 1))
    add_feature(doc, group, prefix + "_front", label + "·盆体前弧", cap, ceramic, {"Height": 340, "Basis": basis})
    # Seat/lid slab sits over the bowl body, not on top of the tank.
    lid = [x + w * 0.36, y + 10, w * 0.50, h - 20]
    add_box(doc, group, prefix + "_lid", label + "·缓降盖板", lid, 35, (0.86, 0.88, 0.85), "soft-close seat over bowl", z0=400)


def add_sanitary(doc, group, openings_group):
    bath_color = (0.92, 0.94, 0.91)
    stone_color = (0.72, 0.70, 0.64)
    brass_color = (0.56, 0.36, 0.12)
    # Bathtub body + inset, source rectangle is the A7 concept footprint.
    tub_rect = [224, 558, 153, 71]
    add_box(doc, group, "MainBath_Tub", "主卫·1500×700 浴缸", tub_rect, 520, bath_color, "A7 target 1500×700", z0=80)
    inner = [239, 570, 123, 47]
    add_box(doc, group, "MainBath_TubInner", "主卫·浴缸内盆", inner, 80, stone_color, "A7 target 1500×700", z0=560)
    # WC and basin envelopes use A7 furniture rectangles.
    for prefix, label, rect_values in [
        ("MainBath_WC", "主卫·坐便器", [224, 697, 71.28, 40.73]),
        ("SecondaryBath_WC", "次卫·坐便器", [428, 467, 71.28, 40.73]),
    ]:
        add_wc(doc, group, prefix, label, rect_values)
    for prefix, label, rect_values in [
        ("MainBath_Sink", "主卫·台盆", [224, 766, 50.92, 61.1]),
        ("SecondaryBath_Sink", "次卫·台盆", [428, 551, 50.92, 61.1]),
    ]:
        add_box(doc, group, prefix + "_cabinet", label + "·柜体", rect_values, 820, (0.68, 0.48, 0.25), "A7 sink envelope", z0=0)
        x, y, w, h = rect_values
        add_box(doc, group, prefix + "_basin", label + "·盆体", [x + 5, y + 5, w - 10, h - 10], 85, bath_color, "A7 sink envelope", z0=820)
        # small cylindrical tap as a distinct object for inspectability
        tap = Part.makeCylinder(16, 420, xy(x + w * 0.5, y + h * 0.2, 905), App.Vector(0, 0, 1))
        add_feature(doc, group, prefix + "_tap", label + "·龙头", tap, brass_color, {"Height": 420, "Basis": "TOTO/Kohler class placeholder"})
    # Shower trays and screens.
    for prefix, label, rect_values in [
        ("MainBath_Shower", "主卫·淋浴", [224, 558, 179, 104]),
        ("SecondaryBath_Shower", "次卫·淋浴", [428, 334, 152, 103]),
    ]:
        add_box(doc, group, prefix + "_tray", label + "·底盘", rect_values, 50, stone_color, "A7 shower envelope", z0=20)
        x, y, w, h = rect_values
        # The wet zone occupies the far end of each bathroom in the source
        # plan.  A transverse screen at its near edge separates it from the
        # WC/vanity dry zone; the previous longitudinal screen split the
        # shower itself and did not provide meaningful wet/dry separation.
        screen_rect = [x, y + h - 20, w, 20]
        # Glass belongs to the openings group so Blender can render it
        # translucent instead of as an opaque tiled partition.
        add_box(doc, openings_group, prefix + "_screen", label + "·透明玻璃屏", screen_rect, 2100, (0.55, 0.78, 0.80), "A7 shower screen", z0=0)


def add_service_wall(doc, group):
    add_box(doc, group, "Kitchen_BaseCabinet", "厨房·连续地柜", [415, 157, 364, 61], 860, (0.68, 0.48, 0.25), "A7 kitchen cabinet footprint")
    add_box(doc, group, "Kitchen_Countertop", "厨房·石材台面", [415, 157, 364, 13], 80, (0.72, 0.70, 0.64), "A7 kitchen cabinet footprint", z0=860)
    # The A7 plan has a return/continuous prep counter on the west side.  Do
    # not invent a full-width overhead cabinet across the aisle and window;
    # that previous block was the main reason the K render looked occluded.
    add_box(doc, group, "Kitchen_ReturnCabinet", "厨房·连续备餐台", [415, 219, 71, 91], 850, (0.68, 0.48, 0.25), "A7 kitchen return cabinet")
    add_box(doc, group, "Kitchen_Hob", "厨房·灶台", [530, 168, 85, 38], 35, (0.06, 0.07, 0.07), "A7 appliance envelope", z0=940)
    add_box(doc, group, "Kitchen_Sink", "厨房·水槽", [690, 165, 72, 43], 35, (0.92, 0.94, 0.91), "A7 appliance envelope", z0=940)
    # The corridor service wall is only about 2.3 m long.  Treat it as three
    # independent appliance columns along the wall (rather than stacking
    # unrelated appliances in one vertical tower): 1) refrigerator,
    # 2) steam oven + oven, 3) washer + dryer.  The plan footprints below are
    # the original A7 service-wall bays, so the passage width and position 3
    # remain unchanged.
    module_x, module_w = 592, 63
    # 234 px service-wall length = 2298 mm.  Retain the exact A7 wall bays;
    # after cabinet panels and installation clearances are counted there is
    # no functional 200 mm cabinet bay between the hot and laundry columns.
    # The refrigerator remains at the kitchen end (north), closest to the
    # kitchen worktop; the washer/dryer remains at the corridor end (south).
    fridge_y, fridge_h = 322, 91
    oven_y, oven_h = 413, 70
    laundry_y, laundry_h = 483, 73
    appliance_color = (0.28, 0.31, 0.31)
    cabinet_color = (0.60, 0.40, 0.20)
    front_color = (0.42, 0.45, 0.44)

    # Column 1: standalone thin refrigerator, with a top storage cabinet.
    fridge = [module_x, fridge_y, module_w, fridge_h]
    add_box(doc, group, "ServiceWall_Fridge", "走廊·薄型冰箱·靠厨房独立列", fridge, 1950, appliance_color,
            "A7 thin refrigerator target <=840W x 600D x 1950H mm; SKU pending",
            props={"ApplianceWidth": 840, "ApplianceDepth": 600, "ApplianceHeight": 1950, "Column": "Fridge_nearest_kitchen"})
    add_box(doc, group, "ServiceWall_FridgeTop", "走廊·冰箱上方高柜", [module_x, fridge_y, module_w, fridge_h], 450, cabinet_color,
            "Thin refrigerator bay; ceiling clearance reserved", z0=2000,
            props={"ClearanceToCeiling": 200})

    # Column 2: one built-in steam oven above one built-in oven.  Both use the
    # standard 595 x 595 mm appliance envelope, with storage above.
    oven = [module_x, oven_y, module_w, oven_h]
    add_box(doc, group, "ServiceWall_OvenTower", "走廊·蒸箱/烤箱独立列", oven, 2300, cabinet_color,
            "Siemens class built-in modules 595W x 548D x 595H mm",
            props={"ModuleWidth": 595, "ModuleDepth": 548, "SteamOvenHeight": 595, "OvenHeight": 595, "Column": "SteamOven+Oven"})
    add_box(doc, group, "ServiceWall_SteamOvenFront", "走廊·蒸箱面板", [module_x + module_w - 2, oven_y + 4, 2, oven_h - 8], 595, front_color,
            "595 mm steam-oven front; separate appliance column", z0=1250)
    add_box(doc, group, "ServiceWall_OvenFront", "走廊·烤箱面板", [module_x + module_w - 2, oven_y + 4, 2, oven_h - 8], 595, front_color,
            "595 mm built-in oven front; separate appliance column", z0=550)
    add_box(doc, group, "ServiceWall_OvenTop", "走廊·蒸烤列上方高柜", [module_x, oven_y, module_w, oven_h], 300, cabinet_color,
            "Residual ceiling storage above 2x built-in ovens", z0=2300,
            props={"ClearanceToCeiling": 100})

    # Column 3: front-loading washer and dryer stacked with a manufacturer
    # stacking kit.  The appliance pair occupies one 600 mm cabinet bay.
    laundry = [module_x, laundry_y, module_w, laundry_h]
    add_box(doc, group, "ServiceWall_WasherDryer", "走廊·洗衣机/烘干机叠放列", laundry, 1900, cabinet_color,
            "Siemens class stackable pair 600W x 600D; stacking kit required",
            props={"ModuleWidth": 600, "ModuleDepth": 600, "WasherHeight": 850, "DryerHeight": 850, "Column": "Washer+Dryer"})
    add_box(doc, group, "ServiceWall_WasherFront", "走廊·洗衣机面板", [module_x + module_w - 2, laundry_y + 4, 2, laundry_h - 8], 850, front_color,
            "Front-load washer visual front", z0=100)
    add_box(doc, group, "ServiceWall_DryerFront", "走廊·烘干机面板", [module_x + module_w - 2, laundry_y + 4, 2, laundry_h - 8], 850, front_color,
            "Front-load dryer visual front", z0=1000)
    add_box(doc, group, "ServiceWall_LaundryTop", "走廊·洗烘列上方高柜", [module_x, laundry_y, module_w, laundry_h], 500, cabinet_color,
            "600 mm appliance module; ceiling clearance reserved", z0=1950,
            props={"ClearanceToCeiling": 200})




def main() -> None:
    cad_dir = ROOT / "cad"
    cad_dir.mkdir(parents=True, exist_ok=True)
    doc = App.newDocument("SchemeA11_CAD_Base")
    groups = {
        "walls": doc.addObject("App::DocumentObjectGroup", "Walls"),
        "floors": doc.addObject("App::DocumentObjectGroup", "Floors"),
        "openings": doc.addObject("App::DocumentObjectGroup", "Openings"),
        "doors": doc.addObject("App::DocumentObjectGroup", "Doors"),
        "furniture": doc.addObject("App::DocumentObjectGroup", "Furniture"),
        "fixtures": doc.addObject("App::DocumentObjectGroup", "Fixtures"),
        "dimensions": doc.addObject("App::DocumentObjectGroup", "Parameters"),
    }
    groups["walls"].Label = "墙体（A7 PNG 锁定）"
    groups["floors"].Label = "地面与分区"
    groups["openings"].Label = "门窗洞口"
    groups["doors"].Label = "门扇（不透明木作）"
    groups["furniture"].Label = "家具与定制柜"
    groups["fixtures"].Label = "厨房家电与卫浴"
    groups["dimensions"].Label = "模型参数"

    # Source calibration and a human-readable parameter object.
    params = doc.addObject("App::FeaturePython", "ModelParameters")
    params.Label = "模型参数（mm）"
    for name, value in {
        "SourceScale": SCALE_MM,
        "WallHeight": WALL_HEIGHT,
        "NominalWallThickness": WALL_THICKNESS,
        "OriginSourceX": ORIGIN_X,
        "OriginSourceY": ORIGIN_Y,
    }.items():
        params.addProperty("App::PropertyLength", name, "Calibration")
        setattr(params, name, value)
    params.addProperty("App::PropertyString", "Source", "Calibration")
    params.Source = "A7 PNG geometry; CAD/DWG used only as structural reference"
    params.addProperty("App::PropertyString", "Status", "Calibration")
    params.Status = "施工级几何底模；现场复尺和机电条件待确认"
    groups["dimensions"].addObject(params)

    wall_color = (0.88, 0.87, 0.82)
    floor_color = (0.72, 0.55, 0.34)
    wet_floor = (0.62, 0.70, 0.68)
    # Walls are direct extrusions of the A7 wall polygons, so the source plan remains the authority.
    wall_objects = []
    for idx, entry in enumerate(DATA["walls"], start=1):
        obj = add_feature(
            doc,
            groups["walls"],
            f"Wall_{idx:03d}",
            entry["name"],
            polygon_prism(entry["polygon"], 0, WALL_HEIGHT),
            wall_color,
            {"SourcePolygon": json.dumps(entry["polygon"], ensure_ascii=False), "Height": WALL_HEIGHT, "Basis": "A7 PNG wall polygon"},
        )
        wall_objects.append(obj)
    add_feature(doc, groups["floors"], "WholeHomeFloor", "全屋地面·A7 外轮廓", polygon_prism(DATA["outer"], 0, 35), floor_color, {"Basis": "A7 outer polygon"})
    for idx, zone in enumerate(DATA["zones"], start=1):
        color = wet_floor if zone["material"] == "wet" else ((0.78, 0.69, 0.50) if zone["material"] == "tile" else floor_color)
        add_feature(doc, groups["floors"], f"ZoneFloor_{idx:02d}", zone["name"] + "·地面", polygon_prism(zone["polygon"], 35, 60), color, {"Zone": zone["name"], "Basis": "A7 zone polygon"})

    for idx, window in enumerate(DATA["windows"], start=1):
        add_window(doc, groups["openings"], f"Window_{idx:02d}", window["name"], window["segment"])
    for idx, door in enumerate(DATA["doors"], start=1):
        add_door(doc, groups["doors"], f"Door_{idx:02d}", door["name"], door)

    # Furnishings retain the exact A7 source rectangles and are intentionally decomposed into parts.
    add_bed(doc, groups["furniture"], "MasterBed", "夫妻主卧床", [551, 906, 214, 187])
    add_bed(doc, groups["furniture"], "ElderBed", "老人床", [945, 390, 215, 185])
    add_bed(doc, groups["furniture"], "ChildBed", "儿童床", [1244, 917, 214, 158])
    for prefix, label, rect_values in [
        ("DressingWardrobe", "衣帽区长柜", [224, 856, 60, 235]),
        ("MasterNorthWardrobe", "主卧北衣柜", [428, 667, 224, 60]),
        ("MasterWestWardrobe", "主卧西衣柜", [428, 727, 60, 145]),
        ("ElderWardrobe", "老人房衣柜", [799, 334, 52, 205]),
        ("ChildWardrobe", "儿童房衣柜", [1255, 785, 203, 63]),
    ]:
        add_wardrobe(doc, groups["furniture"], prefix, label, rect_values)
    # The window-side bookcase is a low side unit paired with the desk, not a
    # full-height partition; keeping it below eye level preserves daylight.
    add_box(doc, groups["furniture"], "ChildWindowBookcase", "儿童窗边低书柜", [1427, 1151, 31, 163], 1100, (0.68, 0.48, 0.25), "A7 target 300 mm deep low bookcase")
    add_box(doc, groups["furniture"], "MasterWindowDesk", "主卧窗边梳妆/阅读台", [489, 1268, 122, 46], 750, (0.68, 0.48, 0.25), "A7 target 1200×450")
    add_box(doc, groups["furniture"], "ChildWindowDesk", "儿童窗边学习桌", [1200, 1252, 183, 61], 750, (0.68, 0.48, 0.25), "A7 target 1800×600")
    add_box(doc, groups["furniture"], "DiningTable", "餐桌", [870, 824, 145, 82], 760, (0.68, 0.48, 0.25), "A7 target 1400×800")
    for idx, rect in enumerate(([888, 782, 38, 38], [953, 782, 38, 38], [888, 915, 38, 38], [953, 915, 38, 38]), start=1):
        add_chair(doc, groups["furniture"], f"DiningChair{idx}", rect)
    add_sofa(doc, groups["furniture"], "LivingSofa", [1020, 1090, 92, 224])
    add_box(doc, groups["furniture"], "LivingTvCabinet", "电视影音矮柜", [792, 1110, 35, 184], 500, (0.68, 0.48, 0.25), "A7 target 1800×350")
    add_box(doc, groups["furniture"], "LivingTvScreen", "客厅·55–65寸电视", [786, 1140, 12, 125], 900, (0.04, 0.05, 0.05), "A7 TV wall; target 55–65 inch", z0=650)
    add_box(doc, groups["furniture"], "LivingCoffeeTable", "客厅茶几", [920, 1195, 56, 91], 450, (0.68, 0.48, 0.25), "A7 target 900×550")
    add_box(doc, groups["furniture"], "LivingSideTable", "客厅沙发边几", [1047, 1038, 42, 42], 500, (0.68, 0.48, 0.25), "A7 target 500×500")
    add_box(doc, groups["furniture"], "DiningTallCabinet", "餐边食品/书籍高柜", [790, 770, 41, 202], 2300, (0.68, 0.48, 0.25), "A7 target 900×400")
    add_box(doc, groups["furniture"], "DiningSideboard", "餐边柜/充电收纳", [790, 972, 41, 92], 850, (0.68, 0.48, 0.25), "A7 target 900×400")

    add_service_wall(doc, groups["fixtures"])
    add_sanitary(doc, groups["fixtures"], groups["openings"])

    # Flat ceiling is modelled as a distinct, hideable object for interior camera work.
    add_feature(doc, groups["walls"], "FlatCeiling", "白色平吊顶（可隐藏）", polygon_prism(DATA["outer"], 2600, 2650), (0.96, 0.96, 0.94), {"Height": 50, "Basis": "brief: white flat ceiling"})

    doc.recompute()
    fcstd = cad_dir / "方案A11_CAD底模.FCStd"
    doc.recompute()
    doc.saveAs(str(fcstd))

    export_objects = []
    manifest_objects = []
    for obj in doc.Objects:
        if hasattr(obj, "Shape") and not obj.Shape.isNull():
            export_objects.append(obj)
            manifest_objects.append({"name": obj.Name, "label": obj.Label, "group": obj.getParentGroup().Name if obj.getParentGroup() else None})
    obj_path = cad_dir / "scheme_a11_cad_base.obj"
    Mesh.export(export_objects, str(obj_path))
    group_exports = {}
    for key, group in groups.items():
        group_objects = [
            obj
            for obj in group.Group
            if hasattr(obj, "Shape")
            and not obj.Shape.isNull()
            # Keep the ceiling in FCStd, but leave it out of the interior OBJ
            # so the camera views are not occluded by a single merged slab.
            and not (key == "walls" and obj.Name == "FlatCeiling")
        ]
        if not group_objects:
            continue
        group_path = cad_dir / f"scheme_a11_{key}.obj"
        Mesh.export(group_objects, str(group_path))
        group_exports[key] = str(group_path)
    manifest = {
        "schema": "scheme-a11-cad-base-v1",
        "source": str(V7 / "scheme_a_geometry.json"),
        "source_basis": DATA["source"],
        "source_scale_mm_per_pixel": SCALE_MM,
        "model_origin_source_px": [ORIGIN_X, ORIGIN_Y],
        "wall_height_mm": WALL_HEIGHT,
        "nominal_wall_thickness_mm": WALL_THICKNESS,
        "freecad_document": str(fcstd),
        "obj_export": str(obj_path),
        "obj_group_exports": group_exports,
        "object_count": len(export_objects),
        "objects": manifest_objects,
        "status": "施工级几何底模；家具和设备为设计外廓，现场复尺/SKU 待确认",
    }
    (cad_dir / "cad_manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"fcstd": str(fcstd), "obj": str(obj_path), "objects": len(export_objects)}, ensure_ascii=False))


if __name__ == "__main__":
    main()
