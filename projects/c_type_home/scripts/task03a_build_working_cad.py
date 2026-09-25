#!/usr/bin/env python3
"""Task03A RC4 — versioned CAD-native pipeline.

Chain: measured_working.dxf (immutable survey conversion)
         -> cad/design_v01_existing_sync.dxf  (full copy + confirmed corrections)
         -> cad/design_v02_f1_l1.dxf         (copy of V01 + F1.1 furniture)

Rules:
- measured DWG/DXF are read-only evidence. V01 inherits EVERY source entity;
  nothing is deleted — superseded/demolished entities move to audit layers.
- canonical JSON = semantic truth (expected geometry, status, evidence);
  the DXF = graphical truth. Gates compare the two.
- every registered element (window/door/cabinet/furniture) gets an ELEM_TAG
  block insert carrying attribs (ELEM_ID, VER, STATUS) — machine-checkable.
"""
import ezdxf, json, hashlib, shutil
from pathlib import Path
from ezdxf import bbox

ROOT = Path(__file__).resolve().parent.parent
CAD = ROOT / 'cad'
CAD.mkdir(exist_ok=True)
SRC_DWG = ROOT / 'source' / '世纪欣园FF.dwg'
MEAS_SRC = ROOT / 'current_existing' / 'measured_working.dxf'
MEAS = CAD / 'measured_working.dxf'
V01 = CAD / 'design_v01_existing_sync.dxf'
V02 = CAD / 'design_v02_f1_l1.dxf'

M = json.load(open(ROOT / 'current_existing' / 'current_existing_v1.json'))
CANON = json.load(open(ROOT / 'current_existing' / 'canonical_plan_v1.json'))
KREG = json.load(open(ROOT / 'current_existing' / 'kitchen_cabinet_register.json'))['cabinets']
CD = json.load(open(ROOT / 'concept' / 'concept_data.json'))
F1J = json.load(open(ROOT / 'concept' / 'furniture_l1_final.json'))

# task01 model coords -> measured DXF absolute coords
# task01 = abs - OX - DX  =>  abs = task01 + OX + DX
AX, AY = 1299472.0 - 1300.0, -297794.0 + 1336.0   # = (1298172, -296458)
def to_abs(p): return (p[0] + AX, p[1] + AY)
def rect_abs(r): return (r[0] + AX, r[1] + AY, r[2] + AX, r[3] + AY)
def rect_norm(r): return (r[0] - AX, r[1] - AY, r[2] - AX, r[3] - AY)

def sha(p): return hashlib.sha256(open(p, 'rb').read()).hexdigest()

REGISTRY = []          # cad_change_registry entries
_seq = [0]
def reg(change_type, src_handle, src_layer, src_geom, reason, evidence,
        owner_conf, status, repl_handle=None, version='V01'):
    _seq[0] += 1
    REGISTRY.append({
        'change_id': f'RC4-{_seq[0]:03d}', 'version': version,
        'source_handle': src_handle, 'source_layer': src_layer,
        'source_geometry': src_geom, 'change_type': change_type,
        'reason': reason, 'evidence': evidence,
        'owner_confirmation': owner_conf, 'status': status,
        'replacement_handle': repl_handle})

# ---------- layers
LAYERS = {  # name: (color, linetype)
 'A-WALL-DEMO':        (8,   'DASHED'),   # real demolition — audit geometry kept
 'A-SURVEY-SUPERSEDED':(6,   'DASHED'),   # survey stale/overridden by owner correction
 'A-SURVEY-HATCH':     (9,   'CONTINUOUS'),  # cosmetic wall fills — audit only, never presentation
 'A-WALL-EXST-CORR':   (1,   'CONTINUOUS'),  # corrected current walls
 'A-PARP-EXST':        (210, 'CONTINUOUS'),  # parapet/railing — never on a wall layer
 'A-OPEN-EXST':        (3,   'CONTINUOUS'),  # door/opening extents
 'A-GLAZ-EXST':        (4,   'CONTINUOUS'),  # registry glazing (windows + glass doors)
 'A-CAB-EXST-BASE':    (34,  'CONTINUOUS'),
 'A-CAB-EXST-TALL':    (30,  'CONTINUOUS'),
 'A-CAB-EXST-WALL':    (33,  'DASHED'),
 'A-EQPM-EXST':        (30,  'DASHED'),
 'A-ELEM-TAG':         (6,   'CONTINUOUS'),
 'A-FURN-PROP':        (41,  'CONTINUOUS'),
 'A-FURN-EXST-KEEP':   (42,  'CONTINUOUS'),
 'A-ACCESS-RAMP':      (5,   'CONTINUOUS'),
 'A-ACCESS-STAIR':     (5,   'DASHED'),
 'A-QC-ZONE':          (140, 'DASHDOT'),
 'A-TEXT':             (250, 'CONTINUOUS'),  # ACI7 renders white on light bg
 'A-NOTE':             (8,   'CONTINUOUS'),
}
def ensure_layers(doc):
    lt = doc.linetypes
    if 'DASHDOT' not in lt:
        doc.linetypes.add('DASHDOT', pattern='A,12,-3,3,-3')
    for name, (col, ltype) in LAYERS.items():
        if name not in doc.layers:
            doc.layers.add(name)
        lay = doc.layers.get(name)
        lay.dxf.color = col
        if ltype in doc.linetypes:
            lay.dxf.linetype = ltype

def ensure_tag_block(doc):
    if 'ELEM_TAG' in doc.blocks:
        return
    b = doc.blocks.new('ELEM_TAG')
    b.add_circle((0, 0), 40)
    b.add_line((-70, 0), (70, 0))
    b.add_line((0, -70), (0, 70))

def tag(msp, elem_id, version, status, xy, extra=None):
    """semantic marker: ELEM_TAG insert with attribs — gates find elements by this."""
    ins = msp.add_blockref('ELEM_TAG', xy, dxfattribs={'layer': 'A-ELEM-TAG'})
    ins.add_attrib('ELEM_ID', elem_id)
    ins.add_attrib('VER', version)
    ins.add_attrib('STATUS', status)
    if extra:
        for k, v in extra.items():
            ins.add_attrib(k, str(v)[:255])
    return ins

def draw_rect(msp, layer, r, abs_=True):
    x1, y1, x2, y2 = rect_abs(r) if not abs_ else r
    e = msp.add_lwpolyline([(x1, y1), (x2, y1), (x2, y2), (x1, y2)],
                           close=True, dxfattribs={'layer': layer})
    return e

def draw_cross_label(msp, txt, r):
    x1, y1, x2, y2 = rect_abs(r)
    msp.add_text(txt, height=160, dxfattribs={'layer': 'A-TEXT', 'style': 'HT'}
                 ).set_placement(((x1 + x2) / 2 - 400, (y1 + y2) / 2))

# ================================================================ STEP 0 source freeze
print('== source freeze ==')
if not MEAS.exists() or sha(MEAS) != sha(MEAS_SRC):
    shutil.copy2(MEAS_SRC, MEAS)
src_doc = ezdxf.readfile(str(MEAS))
msps = src_doc.modelspace()
from collections import Counter
tc = Counter(e.dxftype() for e in msps)
lc = Counter(e.dxf.layer for e in msps)
source_freeze = {
    'source_dwg': 'source/世纪欣园FF.dwg', 'source_dwg_sha256': sha(SRC_DWG),
    'measured_dxf': 'cad/measured_working.dxf', 'measured_dxf_sha256': sha(MEAS),
    'dxf_version': src_doc.dxfversion, 'insunits': src_doc.header.get('$INSUNITS'),
    'entity_count': sum(tc.values()), 'entity_type_counts': dict(tc),
    'layer_count': len(lc), 'layer_entity_counts': dict(lc),
    'conversion_tool': 'dwg2dxf (LibreDWG)', 'conversion_tool_version': 'recorded in TASK01 era; binary version TO_VERIFY',
}
print(f"  entities={source_freeze['entity_count']} layers={source_freeze['layer_count']}")

# ================================================================ STEP 1 V01 = full copy
src_doc.saveas(str(V01))                     # open measured -> save as V01
parent_sha_at_copy = sha(MEAS)
doc = ezdxf.readfile(str(V01))
msp = doc.modelspace()
ensure_layers(doc); ensure_tag_block(doc)

# ---------- wall disposition pass: move covered source entities to audit layers
WALLS = M['walls']
def cover_ratio(ebbox, wr):
    """share of entity extent inside wall rect (task01 space).
    Wall entities are thin: use line-length coverage for zero-thickness
    bboxes, area coverage otherwise."""
    ex = (ebbox.extmin.x - AX, ebbox.extmin.y - AY,
          ebbox.extmax.x - AX, ebbox.extmax.y - AY)
    ew, eh = ex[2] - ex[0], ex[3] - ex[1]
    if eh < 1:  # horizontal line — covered only if its y lies inside rect
        if not (wr[1] <= ex[1] <= wr[3] or wr[1] <= ex[3] <= wr[3]):
            return 0.0
        dx = min(ex[2], wr[2]) - max(ex[0], wr[0])
        return max(0.0, dx) / max(ew, 1e-6)
    if ew < 1:  # vertical line
        if not (wr[0] <= ex[0] <= wr[2] or wr[0] <= ex[2] <= wr[2]):
            return 0.0
        dy = min(ex[3], wr[3]) - max(ex[1], wr[1])
        return max(0.0, dy) / max(eh, 1e-6)
    dx = min(ex[2], wr[2]) - max(ex[0], wr[0]); dy = min(ex[3], wr[3]) - max(ex[1], wr[1])
    if dx <= 0 or dy <= 0:
        return 0.0
    return dx * dy / (ew * eh)

superseded_wall_ids = set()
demo_n = sup_n = 0
for e in list(msp):
    if e.dxf.layer != 'S-S.WALL':
        continue
    try:
        eb = bbox.extents([e])
    except Exception:
        continue
    best, bestc = None, 0.0
    for w in WALLS:
        c = cover_ratio(eb, w['rect_mm'])
        if c > bestc:
            best, bestc = w, c
    if best is None or bestc < 0.3:
        continue
    disp = best['disposition']
    if disp == 'EXISTING':
        continue
    geom = f"bbox_task01={[round(v) for v in (eb.extmin.x-AX, eb.extmin.y-AY, eb.extmax.x-AX, eb.extmax.y-AY)]}"
    if disp.startswith('DEMOLISHED'):
        e.dxf.layer = 'A-WALL-DEMO'; demo_n += 1
        reg('DEMOLITION', e.dxf.handle, 'S-S.WALL', geom,
            f"{best['id']} demolished/opened per owner confirmation",
            best.get('evidence', 'owner confirmation + measured coverage'), True, 'APPLIED')
    else:  # PARTIAL_REMOVED_* / owner-confirmed open segments -> survey was stale
        e.dxf.layer = 'A-SURVEY-SUPERSEDED'; sup_n += 1
        superseded_wall_ids.add(best['id'].split('-OPEN')[0].rstrip('-').rstrip())
        reg('SURVEY_SUPERSEDED', e.dxf.handle, 'S-S.WALL', geom,
            f"{best['id']}: survey drew wall where reality is open/absent",
            'owner-confirmed open passage + canonical wall record', True, 'APPLIED')
# wall fill hatches are cosmetic survey fills — park on audit layer so the
# presentation profile can never paint fill across demolished/open zones
for e in list(msp):
    if e.dxf.layer == 'S-S.WALL' and e.dxftype() == 'HATCH':
        e.dxf.layer = 'A-SURVEY-HATCH'
        reg('SURVEY_SUPERSEDED', e.dxf.handle, 'S-S.WALL', 'wall-fill hatch',
            'cosmetic survey fill; canonical EXISTING/CORR linework is truth',
            'cosmetic entity — not geometry evidence', True, 'APPLIED')
print(f'  walls: demo={demo_n} superseded={sup_n}')

# ---------- corrected / added current-condition walls
# redraw canonical EXISTING walls that the survey did not draw
# (owner corrections, e.g. kitchen corner closure, retained mbath segment after
# a superseded line was moved, walls absent from S-S.WALL)
def linework_cover(wr):
    """1D union coverage of a wall rect by real linework (LINE/LWPOLYLINE —
    HATCH excluded: fills are cosmetic, not wall evidence)."""
    x1, y1, x2, y2 = wr
    cands = []
    for e in msp:
        if e.dxf.layer != 'S-S.WALL' or e.dxftype() in ('HATCH', 'DIMENSION', 'TEXT', 'MTEXT'):
            continue
        try:
            eb = bbox.extents([e])
        except Exception:
            continue
        cands.append((eb.extmin.x - AX, eb.extmin.y - AY,
                      eb.extmax.x - AX, eb.extmax.y - AY))
    if (x2 - x1) >= (y2 - y1):
        ivs = sorted((max(x1, r[0]), min(x2, r[2])) for r in cands
                     if not (r[3] <= y1 - 1 or r[1] >= y2 + 1))
        span = x2 - x1
    else:
        ivs = sorted((max(y1, r[1]), min(y2, r[3])) for r in cands
                     if not (r[2] <= x1 - 1 or r[0] >= x2 + 1))
        span = y2 - y1
    tot, cur_s, cur_e = 0.0, None, None
    for s, e_ in ivs:
        if s >= e_:
            continue
        if cur_s is None:
            cur_s, cur_e = s, e_
        elif s <= cur_e:
            cur_e = max(cur_e, e_)
        else:
            tot += cur_e - cur_s; cur_s, cur_e = s, e_
    if cur_s is not None:
        tot += cur_e - cur_s
    return tot / max(span, 1)

corr_n = 0
for w in WALLS:
    if w['disposition'] != 'EXISTING':
        continue
    needs = (w['measured_coverage'] < 0.5 or linework_cover(w['rect_mm']) < 0.5)
    base = w['id'].rsplit('-', 1)[0]
    if w['id'].rsplit('-', 1)[-1] in ('MBATH', 'TV', 'FOYER') or base in superseded_wall_ids:
        needs = True
    if not needs:
        continue
    # dispatch by canonical type: parapet/railing is NOT a wall
    lay = 'A-PARP-EXST' if w.get('type') == 'railing_parapet' else 'A-WALL-EXST-CORR'
    e = draw_rect(msp, lay, w['rect_mm'], abs_=False)
    owner_conf = ('owner' in str(w.get('evidence', '')).lower()
                  or 'OWNER_CONFIRMED' in w['disposition'])
    reg('EXISTING_CORRECTION', None, lay, f"rect_task01={w['rect_mm']}",
        f"{w['id']} canonical current {w.get('type','wall')} not (fully) present "
        f"in survey (coverage={w['measured_coverage']}) — drawn as corrected linework",
        w.get('evidence', 'canonical_plan_v1'), owner_conf, 'APPLIED',
        repl_handle=e.dxf.handle)
    corr_n += 1
print(f'  corrected walls drawn: {corr_n}')

# ---------- openings: draw extents + semantic tags (14 doors)
for o in M['openings']:
    draw_rect(msp, 'A-OPEN-EXST', o['rect_mm'], abs_=False)
    r = o['rect_mm']; c = to_abs(((r[0]+r[2])/2, (r[1]+r[3])/2))
    tag(msp, o['id'], 'V01', 'EXISTING', c, {'KIND': o.get('kind', 'door')})

# ---------- windows / glass doors: the frozen 9-record registry
for w in M['windows']:
    wid = w.get('window_id') or w.get('name')
    r = w['opening_rect_mm']
    draw_rect(msp, 'A-GLAZ-EXST', r, abs_=False)
    ra = rect_abs(r)
    if (ra[2]-ra[0]) >= (ra[3]-ra[1]):   # horizontal glazing = 3 lines
        for i in (0.25, 0.5, 0.75):
            y = ra[1] + (ra[3]-ra[1]) * i
            msp.add_line((ra[0], y), (ra[2], y), dxfattribs={'layer': 'A-GLAZ-EXST'})
    else:
        for i in (0.25, 0.5, 0.75):
            x = ra[0] + (ra[2]-ra[0]) * i
            msp.add_line((x, ra[1]), (x, ra[3]), dxfattribs={'layer': 'A-GLAZ-EXST'})
    bay = w.get('bay')
    if bay:
        for j in bay['jambs']:
            draw_rect(msp, 'A-GLAZ-EXST', j, abs_=False)
        draw_rect(msp, 'A-GLAZ-EXST', bay['front'], abs_=False)
    tag(msp, wid, 'V01', w.get('measurement_status', 'CONFIRMED'),
        to_abs(((r[0]+r[2])/2, (r[1]+r[3])/2)),
        {'KIND': w.get('window_type') or w.get('type', '')})

# ---------- kitchen cabinets as real CAD entities
CAB_LAYER = {'base_cabinet_run': 'A-CAB-EXST-BASE', 'base_cabinet_sink_leg': 'A-CAB-EXST-BASE',
             'tall_cabinet': 'A-CAB-EXST-TALL', 'wall_cabinet_run': 'A-CAB-EXST-WALL'}
for c in KREG:
    lay = CAB_LAYER.get(c['kind'], 'A-EQPM-EXST')
    draw_rect(msp, lay, c['rect_mm'], abs_=False)
    r = c['rect_mm']
    tag(msp, c['id'], 'V01', f"{c.get('dimension_status','?')}/{c.get('placement_status','?')}",
        to_abs(((r[0]+r[2])/2, (r[1]+r[3])/2)), {'KIND': c['kind'], 'PARENT': c.get('parent', '')})
    reg('EXISTING_ENRICHMENT', None, lay, f"rect_task01={c['rect_mm']}",
        f"existing kitchen cabinet {c['id']} projected from cabinet PDF into CAD",
        '世纪欣园3-1-901_cabinet_plan.pdf + kitchen_cabinet_register — PDF-derived, not owner-verified',
        False, 'APPLIED')

# ---------- existing keep items + room labels
for k in M.get('keep_items', []):
    draw_rect(msp, 'A-FURN-EXST-KEEP', k['rect_mm'], abs_=False)
    r = k['rect_mm']
    tag(msp, k['id'], 'V01', 'EXISTING_KEEP', to_abs(((r[0]+r[2])/2, (r[1]+r[3])/2)))
ROOMS = [('FLEX FAMILY ROOM 客厅', 4200, 10600), ('DINING 餐厅', 4000, 2200),
         ('KITCHEN 厨房', 6200, 2500), ('LIFE BALC 生活阳台', 2600, 1500),
         ('MASTER BED 主卧', 12500, 2800), ('SEC MASTER BED 次主卧', 9000, 2800),
         ('SEC MASTER BATH 次主卫', 9200, 5600), ('MASTER BATH 主卫', 14200, 5500),
         ('STUDY 书房', 14000, 10000), ('GUEST BED 客卧', 11750, 9900),
         ('GUEST BATH 客卫', 8200, 9600), ('N BALCONY 北阳台', 9800, 12200),
         ('LANDING/FOYER 平台', 8000, 6800)]
def mtext(txt, xy, h=300, layer='A-TEXT'):
    # inline font code + explicit column width: renderer drops MTEXT that
    # lacks a resolved font or a defined rect width
    mt = msp.add_mtext(f'{{\\fSimSun|b0|i0|c134|p2;{txt}}}',
                       dxfattribs={'layer': layer, 'style': 'HT'})
    mt.dxf.char_height = h
    mt.dxf.width = max(h * len(txt) * 0.7, 500)
    mt.set_location(to_abs(xy))
    return mt

for t, x, y in ROOMS:
    mtext(t, (x, y))
mtext('EXISTING 3-STEP TRANSITION — exact level delta TO_VERIFY', (5900, 8050), 160)

doc.saveas(str(V01))
v01_sha = sha(V01)
v01_entities = sum(1 for _ in ezdxf.readfile(str(V01)).modelspace())
print(f'  V01 saved: {v01_entities} entities, sha={v01_sha[:16]}')

# ================================================================ STEP 2 V02 = V01 + F1.1
shutil.copy2(V01, V02)
doc = ezdxf.readfile(str(V02))
msp = doc.modelspace()
ensure_layers(doc); ensure_tag_block(doc)

# furniture blocks (geometry at real size, origin at rect min corner)
def furn_block(name, w, h):
    if name in doc.blocks:
        return
    b = doc.blocks.new(name)
    b.add_lwpolyline([(0, 0), (w, 0), (w, h), (0, h)], close=True)

L1_IDS = {it['id']: it for c in F1J['categories'].values() for it in c
          if isinstance(it, dict)}
BLK = {'LIV-SOFA-3': 'FURN_SOFA_3', 'LIV-SOFA-2': 'FURN_SOFA_2',
       'LIV-LOUNGE': 'FURN_LOUNGE', 'LIV-SIDE-TABLE': 'FURN_SIDE_TABLE',
       'LIV-COFFEE-MOV': 'FURN_COFFEE_TABLE', 'DIN-TABLE': 'FURN_TABLE_RECT',
       'ENTRY-SHOE-CAB': 'FURN_GENERIC', 'ENTRY-BENCH': 'FURN_GENERIC',
       'LBALC-CAB': 'FURN_GENERIC', 'NB-WD': 'FURN_GENERIC', 'NB-TEA': 'FURN_GENERIC'}
for fid, f in L1_IDS.items():
    if fid in ('RAMP', 'STAIR-EXISTING', 'LIV-MEDIA-WALL', 'K-CAB'):
        continue
    r = f['rect']; w_, h_ = r[2]-r[0], r[3]-r[1]
    bname = BLK.get(fid, 'FURN_GENERIC')
    lay = f['layer'] if f['layer'] in LAYERS else 'A-FURN-PROP'
    if bname == 'FURN_GENERIC':          # generic block is per-instance size -> plain rect
        draw_rect(msp, lay, r, abs_=False)
        ins = tag(msp, fid, 'V02', f['layer'], to_abs((r[0], r[1])),
                  {'DIMS': f"{w_}x{h_}"})
    else:
        furn_block(bname, w_, h_)
        ins = msp.add_blockref(bname, to_abs((r[0], r[1])), dxfattribs={'layer': lay})
        ins.add_attrib('ELEM_ID', fid); ins.add_attrib('VER', 'V02')
        ins.add_attrib('STATUS', f['layer']); ins.add_attrib('DIMS', f"{w_}x{h_}")
    reg('EXISTING_ENRICHMENT' if lay == 'A-FURN-EXST-KEEP' else 'PROPOSED_DESIGN',
        None, lay, f"rect_task01={r}",
        f"F1.1 furniture {fid} placed", 'furniture_l1_final.json @ d144789', True,
        'APPLIED', repl_handle=ins.dxf.handle, version='V02')

# media wall reference
mw = L1_IDS['LIV-MEDIA-WALL']['rect']
draw_rect(msp, 'A-NOTE', mw, abs_=False)
tag(msp, 'LIV-MEDIA-WALL', 'V02', 'REFERENCE_UNDECIDED', to_abs((mw[0], mw[1])),
    {'OPTS': 'A clean / B floating stone'})
# ramp
rp = L1_IDS['RAMP']['rect']
ra = rect_abs(rp)
for i in range(11):
    x = ra[0] + (ra[2]-ra[0]) * i / 10
    msp.add_line((x, ra[1]), (x, ra[3]), dxfattribs={'layer': 'A-ACCESS-RAMP'})
draw_rect(msp, 'A-ACCESS-RAMP', rp, abs_=False)
tag(msp, 'RAMP', 'V02', 'ASSISTED_POWER_WHEELCHAIR_PROVISIONAL',
    to_abs(((rp[0]+rp[2])/2, (rp[1]+rp[3])/2)), {'DIMS': '2500x1100', 'SLOPE': '1:6.25'})
mtext('RAMP 2500x1100 slope 1:6.25 — ASSISTED/POWER-WHEELCHAIR (provisional)',
      (rp[0], rp[3] + 150), 140)
# stair tag (entities inherited from survey S-楼梯)
st = L1_IDS['STAIR-EXISTING']['rect']
draw_rect(msp, 'A-ACCESS-STAIR', st, abs_=False)
tag(msp, 'STAIR-EXISTING', 'V02', 'EXISTING', to_abs(((st[0]+st[2])/2, (st[1]+st[3])/2)),
    {'NOTE': 'existing 3-step transition'})
# seating zones + K-CAB zone as QC geometry (hidden in presentation)
for zn, r in CD['l1_seating'].items():
    if isinstance(r, list):
        draw_rect(msp, 'A-QC-ZONE', r, abs_=False)
        tag(msp, zn, 'V02', 'CLEARANCE_ZONE', to_abs(((r[0]+r[2])/2, (r[1]+r[3])/2)))
draw_rect(msp, 'A-QC-ZONE', L1_IDS['K-CAB']['rect'], abs_=False)

doc.saveas(str(V02))
v02_sha = sha(V02)
v02_entities = sum(1 for _ in ezdxf.readfile(str(V02)).modelspace())
print(f'  V02 saved: {v02_entities} entities, sha={v02_sha[:16]}')

# ================================================================ manifest + registry
manifest = {'project': 'c_type_home', 'coordinate_note':
            'cad/ DXFs in measured-absolute coords; task01 = abs - (1298172, -296458)',
            'versions': [
    {'version': 'MEASURED', 'file': 'cad/measured_working.dxf',
     'sha256': sha(MEAS), 'immutable': True,
     'source': 'dwg2dxf conversion of source/世纪欣园FF.dwg'},
    {'version': 'V01', 'file': 'cad/design_v01_existing_sync.dxf',
     'parent': 'MEASURED', 'parent_sha256': parent_sha_at_copy,
     'sha256': v01_sha, 'immutable': True, 'scope': 'confirmed existing corrections (frozen base RC3.1)'},
    {'version': 'V02', 'file': 'cad/design_v02_f1_l1.dxf',
     'parent': 'V01', 'parent_sha256': v01_sha,
     'sha256': v02_sha, 'immutable': True, 'scope': 'F1.1 level-1 furniture'},
]}
manifest.update({'source_freeze': source_freeze})
json.dump(manifest, open(CAD / 'cad_version_manifest.json', 'w'),
          ensure_ascii=False, indent=1)
json.dump(REGISTRY, open(CAD / 'cad_change_registry.json', 'w'),
          ensure_ascii=False, indent=1)
print(f'  registry: {len(REGISTRY)} changes')
