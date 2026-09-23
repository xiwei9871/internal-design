"""Shared, dependency-free A14 design contract. Pixel provenance is retained."""
from pathlib import Path
import hashlib
import json
import math

ROOT = Path(__file__).resolve().parent
DESIGN_PATH = ROOT / 'design' / 'approved_v14.json'


def load_design():
    return json.loads(DESIGN_PATH.read_text(encoding='utf-8'))


def design_hash():
    return hashlib.sha256(DESIGN_PATH.read_bytes()).hexdigest()


def world_mm(px, py):
    data = load_design()
    scale = data['metres_per_pixel'] * 1000
    ox, oy = data['origin_source_px']
    return ((px - ox) * scale, (oy - py) * scale)


def door_leaf_rect(door):
    """Render sliding doors closed until the pocket construction is verified."""
    hx, hy = door['hinge']
    lx, ly = door['closed'] if door['type'] == 'pocket_sliding' else door['leaf']
    thickness_px = door['leaf_thickness_mm'] / (load_design()['metres_per_pixel'] * 1000)
    return [min(hx, lx), min(hy, ly), max(abs(hx-lx), thickness_px), max(abs(hy-ly), thickness_px)]


def opening_reference_mm(door):
    return math.dist(door['hinge'], door['closed']) * load_design()['metres_per_pixel'] * 1000


def opening_infill_rect(segment,thickness_mm=120):
    x1,y1,x2,y2=segment
    thickness=thickness_mm/(load_design()['metres_per_pixel']*1000)
    if abs(x2-x1)>=abs(y2-y1):
        return [min(x1,x2),(y1+y2)/2-thickness/2,abs(x2-x1),thickness]
    return [(x1+x2)/2-thickness/2,min(y1,y2),thickness,abs(y2-y1)]
