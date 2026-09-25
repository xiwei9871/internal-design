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
    'A-WIND-EXST-KEEP':   4,   # cyan — existing window glazing
    'A-WIND-TO-VERIFY':   6,   # magenta — ambiguous opening, field verify
    'A-GLAZ-PROP':        5,   # blue — proposed glazing (N balcony enclosure)
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
    cls = w['wall_class']
    if w['disposition'] == 'EXISTING':
        if 'NO_DEMOLITION' in cls or 'NO_OPEN' in cls:
            lay = 'A-WALL-OWNER-NOOPEN'
        elif 'REVIEW' in cls:
            lay = 'A-QC'
        else:
            lay = 'A-WALL-EXST-KEEP'
        rect(lay, w['rect_mm'])
    else:
        lay = 'A-QC' if 'CONFLICT' in cls else 'A-WALL-EXST-REMOVE'
        rect(lay, w['rect_mm'])   # ghost: demolished/absent; conflict walls on A-QC

for o in M['openings']:
    lay = {'sliding_glass_3track': 'A-GLAZ-EXST-KEEP',
           'glazing_door_double': 'A-GLAZ-EXST-KEEP',
           'open_passage': 'A-NOTE'}.get(o['kind'], 'A-DOOR-EXST-KEEP')
    rect(lay, o['rect_mm'])
    cx = (o['rect_mm'][0] + o['rect_mm'][2]) / 2; cy = (o['rect_mm'][1] + o['rect_mm'][3]) / 2
    msp.add_text(o['id'], height=160, dxfattribs={'layer': 'A-NOTE'}).set_placement((cx, cy))

# ---------------------------------------------------------------- RC2.2 windows
def glazing_lines(rect_, lay):
    """3-line window symbol inside the wall band of an opening."""
    x1, y1, x2, y2 = rect_
    if (x2 - x1) >= (y2 - y1):
        for i in (0.25, 0.5, 0.75):
            y = y1 + (y2 - y1) * i
            msp.add_line((x1, y), (x2, y), dxfattribs={'layer': lay})
    else:
        for i in (0.25, 0.5, 0.75):
            x = x1 + (x2 - x1) * i
            msp.add_line((x, y1), (x, y2), dxfattribs={'layer': lay})

for win in M.get('windows', []):
    vs = win['verification_status']
    lay = {'CONFIRMED': 'A-WIND-EXST-KEEP', 'MEASURED': 'A-WIND-EXST-KEEP',
           'TO_VERIFY': 'A-WIND-TO-VERIFY', 'PROPOSED': 'A-GLAZ-PROP'}[vs]
    r = win['opening_rect_mm']
    if win['window_type'] == 'PROPOSED_BALCONY_ENCLOSURE':
        # proposed glazing along parapet north face — dashed impression via thin line
        msp.add_line((r[0], r[3]), (r[2], r[3]), dxfattribs={'layer': lay})
        msp.add_text('PROPOSED enclosure (now OPEN)', height=140,
                     dxfattribs={'layer': lay}).set_placement((r[0], r[3] + 200))
        continue
    glazing_lines(r, lay)
    bay = win.get('bay')
    if bay:
        for j in bay['jambs']:
            rect(lay, j)
        rect(lay, bay['front'])
    cx, cy = (r[0] + r[2]) / 2, (r[1] + r[3]) / 2
    msp.add_text(win['window_id'], height=110,
                 dxfattribs={'layer': 'A-NOTE'}).set_placement((cx - 200, cy + 260))

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
msp.add_text('L1->L2 2 RISERS — delta LEVEL_TO_VERIFY (owner<=350 / CAD~400)', height=140,
             dxfattribs={'layer': 'A-LEVEL'}).set_placement((zx1 - 200, zy2 + 200))

doc.saveas(str(ROOT / 'current_existing' / 'current_existing_v1.dxf'))
print('dxf written')
