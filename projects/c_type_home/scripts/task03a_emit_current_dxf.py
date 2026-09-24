#!/usr/bin/env python3
"""Emit current_existing_v1.dxf from current_existing_v1.json (task01 coords).
Layers per taskbook §17. Existing geometry only — no proposal geometry."""
import ezdxf, json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
M = json.load(open(ROOT / 'current_existing' / 'current_existing_v1.json'))

LAYERS = {
    'A-WALL-EXST-KEEP':   7,   # white
    'A-WALL-OWNER-NOOPEN': 1,  # red — owner-declared structural
    'A-WALL-EXST-REMOVE': 8,   # grey — demolished/absent
    'A-WALL-NEW':         5,
    'A-DOOR-EXST-KEEP':   3,
    'A-DOOR-NEW':         4,
    'A-GLAZ-EXST-KEEP':   6,
    'A-FURN-EXST-KEEP':   30,
    'A-FURN-PROP':        2,
    'A-FIXT-PLUMB':       4,
    'A-ACCESS-RAMP':      3,
    'A-ACCESS-STAIR':     3,
    'A-LEVEL':            140,
    'A-DIMS':             8,
    'A-NOTE':             7,
    'A-QC':               1,
}
doc = ezdxf.new('R2010', setup=True)
doc.header['$INSUNITS'] = 4
for name, col in LAYERS.items():
    if name not in doc.layers:
        doc.layers.add(name, color=col)
msp = doc.modelspace()

def rect(lay, r, hatch=False):
    x1, y1, x2, y2 = r
    pl = msp.add_lwpolyline([(x1, y1), (x2, y1), (x2, y2), (x1, y2)],
                            dxfattribs={'layer': lay}, close=True)
    return pl

for w in M['walls']:
    if w['disposition'] == 'EXISTING':
        lay = 'A-WALL-OWNER-NOOPEN' if 'NO_DEMOLITION' in w['wall_class'] else 'A-WALL-EXST-KEEP'
        rect(lay, w['rect_mm'])
    else:
        rect('A-WALL-EXST-REMOVE', w['rect_mm'])   # ghost: demolished/absent

for o in M['openings']:
    lay = {'sliding_glass_3track': 'A-GLAZ-EXST-KEEP',
           'glazing_door_double': 'A-GLAZ-EXST-KEEP',
           'open_passage': 'A-NOTE'}.get(o['kind'], 'A-DOOR-EXST-KEEP')
    rect(lay, o['rect_mm'])
    cx = (o['rect_mm'][0] + o['rect_mm'][2]) / 2; cy = (o['rect_mm'][1] + o['rect_mm'][3]) / 2
    msp.add_text(o['id'], height=160, dxfattribs={'layer': 'A-NOTE'}).set_placement((cx, cy))

for k in M['keep_items']:
    rect('A-FURN-EXST-KEEP', k['rect_mm'])
    msp.add_text(k['id'], height=140, dxfattribs={'layer': 'A-NOTE'}).set_placement(
        (k['rect_mm'][0] + 60, k['rect_mm'][1] + 60))

# split level: stair zone + level boundary note
st = M['split_level']
rect('A-ACCESS-STAIR', st['zone_mm'])
# tread lines inside stair zone (2 risers)
zx1, zy1, zx2, zy2 = st['zone_mm']
for i in range(3):
    x = zx1 + (zx2 - zx1) * i / 2
    msp.add_line((x, zy1), (x, zy2), dxfattribs={'layer': 'A-ACCESS-STAIR'})
msp.add_text('L1->L2 2 RISERS ~400mm TO_VERIFY', height=140,
             dxfattribs={'layer': 'A-LEVEL'}).set_placement((zx1 - 200, zy2 + 200))

doc.saveas(str(ROOT / 'current_existing' / 'current_existing_v1.dxf'))
print('dxf written')
