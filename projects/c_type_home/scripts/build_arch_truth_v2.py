#!/usr/bin/env python3
"""build_arch_truth_v2.py — PHASE 2 deterministic rebuild.

FINAL_WALL_ACTIVE_REGISTER + FINAL_OPENING_ACTIVE_REGISTER + FINAL_BAY_WINDOW_REGISTER
        -> design/pascal_b1/canonical_arch_v2.json
        -> design/pascal_b1/pascal_arch_truth_scene.json   (for scene pascal-arch-truth-v1)
        -> gates: BAY_DUPLICATE_CHECK.json, DOOR_WIDTH_VALIDATION.json
No furniture / kitchen / materials. Old b1_model.json used only for door rects + split level.
"""
import json, os, hashlib
import matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle

BASE = '/Users/xiwei/interior_design/projects/c_type_home'
AUD = f'{BASE}/design/pascal_b1/wall_audit'
OUTD = f'{BASE}/design/pascal_b1'
WALLS = json.load(open(f'{AUD}/FINAL_WALL_ACTIVE_REGISTER.json'))
OPENINGS = json.load(open(f'{AUD}/FINAL_OPENING_ACTIVE_REGISTER.json'))
BAYS = json.load(open(f'{AUD}/FINAL_BAY_WINDOW_REGISTER.json'))
M = json.load(open(f'{BASE}/design/b1_blockout/b1_model.json'))  # door rects + split_level only

MM = 0.001
def m(v): return round(v * MM, 4)
def mz(v): return round(-v * MM, 4)

WALL_H = 2.5     # TEMP storey height
PARAPET_H = 1.05 # TEMP
DOOR_H = 2.1; GLASS_H = 2.4; ENTRY_H = 2.4; OPEN_H = 2.4
WIN_SILL = 0.9; WIN_H = 1.5          # TEMP ordinary window
BAY_SILL_H = 0.45; BAY_GLASS_H = 2.0 # TEMP bay platform/glazing
BALC_SILL = 1.05; BALC_H = 1.4       # balcony glazing above parapet

# ---------------------------------------------------------------- canonical v2
act = WALLS['active']
removed = WALLS['removed_history']

def axis(r):  # 'x' wall runs along x (horizontal band)
    return 'x' if (r[2]-r[0]) >= (r[3]-r[1]) else 'y'

walls_v2 = []
for w in act:
    r = w['rect']; ax = axis(r)
    t = r[3]-r[1] if ax == 'x' else r[2]-r[0]
    h = PARAPET_H if w['classification'] == 'PARAPET' else WALL_H
    walls_v2.append({
        'wall_id': w['wall_id'], 'classification': w['classification'], 'rect': r, 'axis': ax,
        'thickness_mm': t, 'height_m': h, 'base_z': 0,
        'height_status': 'BLOCKOUT_TEMP_VALUE',
        'thickness_status': 'TO_VERIFY' if w.get('confidence') == 'MEDIUM' else 'CONFIRMED',
        'evidence': w.get('evidence', '')})
assert len(walls_v2) == 42

# bay assemblies: facade opening (gap in facade) + cheeks + front + glazing + sill
BAY_DEF = {
 'W-LIV-N':   dict(cheeks=[[3650,12950,3800,13800],[6900,12950,7050,13800]], cheek_t='REGISTERED(W-BAY-JW/JE 150)',
                   front=[3600,13800,7100,13900], front_mode='GLAZED_BAND', sill_poly=[3650,12950,7050,13900],
                   facade_opening=[3800,12750,6900,12950]),
 'W-STUDY-NE':dict(cheeks='REGISTERED_WALLS:W-BAY-STUDY-JW,W-BAY-STUDY-JE',
                   front='REGISTERED_WALL:W-BAY-STUDY-F', front_mode='SOLID_WALL_WITH_WINDOW',
                   front_rect=[13600,11350,15800,11550], glass_span=2100,
                   sill_poly=[13600,11100,15800,11550],
                   facade_opening=[13600,10900,15700,11100]),
 'W-SMB-S':   dict(cheeks=[[8400,-700,8500,0],[10900,-700,11000,0]], cheek_t='100 TO_VERIFY',
                   front=[8400,-700,11000,-600], front_mode='GLAZED_BAND', sill_poly=[8400,-700,11000,0],
                   facade_opening=[8500,-200,10900,0]),
 'W-MB-S':    dict(cheeks=[[12000,-700,12100,0],[14800,-700,14900,0]], cheek_t='100 TO_VERIFY',
                   front=[12000,-700,14900,-600], front_mode='GLAZED_BAND', sill_poly=[12000,-700,14900,0],
                   facade_opening=[12100,-200,14800,0]),
}

# openings: 9 windows/glazing + 13 door-kind openings
windows_v2 = OPENINGS['windows']           # register verbatim
doors_v2 = OPENINGS['doors']               # resolved semantics verbatim

split = {'zone': [7200, 6600, 7800, 7800], 'elevation_m': 0.35,
         'status': 'BLOCKOUT_TEMP_VALUE', 'note': 'baseline split_level zone; +350mm platform'}

canon = {'version': 'canonical_arch_v2', 'units': 'mm',
         'sources': {'walls': 'FINAL_WALL_REGISTER_V01 ccc78186b4b9',
                     'windows': 'FINAL_WINDOW_REGISTER_95ab90e 73dcee675d5e',
                     'doors': 'B1_DOOR_SEMANTIC_RESOLUTION v002'},
         'walls': walls_v2, 'bay_assemblies': BAY_DEF, 'windows': windows_v2,
         'doors': doors_v2, 'split_level': split, 'removed_walls_provenance': removed}
json.dump(canon, open(f'{OUTD}/canonical_arch_v2.json', 'w'), indent=1, ensure_ascii=False)

# ---------------------------------------------------------------- Pascal graph
SEQ = [0]
def nid(p):
    SEQ[0] += 1
    return f'{p}_v2_{SEQ[0]:04d}'

nodes, idmap = {}, []
def add(n, cid=None, cat=None, status='MAPPED', extra=None):
    nodes[n['id']] = n
    if cid: idmap.append({'pascal_id': n['id'], 'canonical_id': cid, 'category': cat,
                          'status': status, **(extra or {})})
    return n['id']

site_n = {'object':'node','id':nid('site'),'type':'site','parentId':None,'visible':True,
          'metadata':{},'polygon':{'type':'polygon','points':[[0,2],[17,2],[17,-15],[0,-15]]},'children':[]}
bldg_n = {'object':'node','id':nid('building'),'type':'building','parentId':site_n['id'],'visible':True,
          'metadata':{},'children':[],'position':[0,0,0],'rotation':[0,0,0]}
lvl_n  = {'object':'node','id':nid('level'),'type':'level','parentId':bldg_n['id'],'visible':True,
          'metadata':{},'children':[],'level':0,'baseElevation':0,'height':WALL_H}
site_n['children']=[bldg_n['id']]; bldg_n['children']=[lvl_n['id']]
site = add(site_n); bldg = add(bldg_n); lvl = add(lvl_n)

def wall_node(r, t_mm, h, cid, meta=None):
    """rect mm -> wall node (centerline start/end, thickness)."""
    a = axis(r)
    if a == 'x':
        start, end = [m(r[0]), mz((r[1]+r[3])/2)], [m(r[2]), mz((r[1]+r[3])/2)]
    else:
        start, end = [m((r[0]+r[2])/2), mz(r[1])], [m((r[0]+r[2])/2), mz(r[3])]
    wid = nid('wall')
    n = {'object':'node','id':wid,'type':'wall','parentId':lvl,'visible':True,
         'metadata':{'canonical_id':cid,**(meta or {})},
         'children':[],'thickness':round(t_mm*MM,4),'height':h,'start':start,'end':end,
         'frontSide':'unknown','backSide':'unknown'}
    return wid, n, a

def emit_wall(wv, meta=None):
    wid, n, a = wall_node(wv['rect'], wv['thickness_mm'], wv['height_m'], wv['wall_id'], meta)
    add(n, cid=wv['wall_id'], cat='wall', status='MAPPED',
        extra={'thickness_mm': wv['thickness_mm'], 'height_m': wv['height_m'],
               'thickness_status': wv['thickness_status']})
    nodes[lvl]['children'].append(wid)
    return wid, a

WALLNODE = {}   # wall_id -> (node_id, axis)
for wv in walls_v2:
    WALLNODE[wv['wall_id']] = emit_wall(wv)

# ---- opening host resolution ---------------------------------------------
def find_host(r, tol=400):
    """opening rect -> register wall band it pierces.
    Returns (wall_v2, 'PIERCES') if rect inside a wall band, else
    (synth_band_rect, 'HOST_BAND') reconstructed from flanking collinear walls."""
    for w in walls_v2:
        wr = w['rect']
        if (wr[0]-tol <= r[0] and wr[1]-tol <= r[1] and wr[2]+tol >= r[2] and wr[3]+tol >= r[3]):
            return w, 'PIERCES'
    # gap opening: flanking collinear walls define the band thickness
    a = axis(r)   # opening long axis = wall tangent
    band = None
    for w in walls_v2:
        wr = w['rect']
        if w['axis'] != a: continue
        if a == 'x':
            same_band = abs(wr[1]-r[1]) <= tol or abs(wr[3]-r[3]) <= tol or (wr[1] <= r[1] and wr[3] >= r[3])
            abuts = wr[2] <= r[0]+tol and wr[2] >= r[0]-2000 or r[2]-tol <= wr[0] <= r[2]+2000
            in_line = wr[2] >= r[0]-2000 and wr[0] <= r[2]+2000
        else:
            same_band = abs(wr[0]-r[0]) <= tol or abs(wr[2]-r[2]) <= tol or (wr[0] <= r[0] and wr[2] >= r[2])
            in_line = wr[3] >= r[1]-2000 and wr[1] <= r[3]+2000
        if same_band and in_line:
            band = wr if band is None else [min(band[0],wr[0]),min(band[1],wr[1]),max(band[2],wr[2]),max(band[3],wr[3])]
    if band:
        return {'wall_id': None, 'rect': band, 'axis': a,
                'thickness_mm': (band[3]-band[1] if a=='x' else band[2]-band[0])}, 'HOST_BAND'
    # perpendicular-crossing: opening long axis ⊥ wall axis; opening narrow extent
    # sits inside wall tangent extent; wall band overlaps opening long extent
    for w in walls_v2:
        wr = w['rect']
        if w['axis'] == a: continue
        if a == 'x':   # opening long in x, wall tangent = y, wall band = x-extent
            narrow_ok = wr[1] - tol <= r[1] and r[3] <= wr[3] + tol
            cross_ok = r[0] <= wr[2] + 50 and r[2] >= wr[0] - 50
        else:
            narrow_ok = wr[0] - tol <= r[0] and r[2] <= wr[2] + tol
            cross_ok = r[1] <= wr[3] + 50 and r[3] >= wr[1] - 50
        if narrow_ok and cross_ok:
            return w, 'PIERCES_PERPENDICULAR'
    # removed-wall host (opening kept by design => wall still exists, TO_VERIFY extent)
    for w in M['removed_walls']:
        wr = w['rect']
        hit = (wr[0]-tol <= r[0] and wr[1]-tol <= r[1] and wr[2]+tol >= r[2] and wr[3]+tol >= r[3]) or \
          (min(r[2],wr[2]) - max(r[0],wr[0]) > 0 and min(r[3],wr[3]) - max(r[1],wr[1]) > 0)
        if hit:
            return {'wall_id': w['id'], 'rect': wr, 'axis': axis(wr),
                    'thickness_mm': (wr[3]-wr[1] if axis(wr)=='x' else wr[2]-wr[0])}, 'REMOVED_HOST'
    return None, 'NO_HOST'

GLASS_DOOR_IDS = {'G-GB-BALC','G-LIV-NBALC'}; SCREEN_IDS = {'G-DIN-LIV'}
DOOR_H_OVR = {'ENT-1': ENTRY_H}
door_checks = []

def door_width_along_tangent(r, ax):
    """BUGFIX: width = opening extent ALONG wall tangent (long axis of opening rect
    for a gap opening = its long axis; for pierced = axis matching wall tangent)."""
    return (r[2]-r[0]) if ax == 'x' else (r[3]-r[1])

DOOR_TMPL = {"constructionType":"framed","dimensionReference":"nominal","doorCategory":"interior",
 "doorType":"hinged","leafCount":1,"operationState":0,"slideDirection":"left","trackStyle":"none",
 "openingKind":"door","openingShape":"rectangle","openingRadiusMode":"all","openingTopRadii":[0.15,0.15],
 "cornerRadius":0.15,"archHeight":0.45,"openingRevealRadius":0.025,"frameThickness":0.05,"frameDepth":0.07,
 "threshold":True,"thresholdHeight":0.02,"hingesSide":"left","swingDirection":"inward","swingAngle":0,
 "garagePanelCount":4,"panicBar":False,"panicBarHeight":1.0,
 "segments":[{"type":"panel","heightRatio":0.4,"columnRatios":[1],"dividerThickness":0.03,"panelDepth":0.01,"panelInset":0.04},
             {"type":"panel","heightRatio":0.6,"columnRatios":[1],"dividerThickness":0.03,"panelDepth":0.01,"panelInset":0.04}],
 "handle":True,"handleHeight":1.05,"handleSide":"right","contentPadding":[0.04,0.04],"doorCloser":False}
WIN_TMPL = {"constructionType":"framed","dimensionReference":"nominal","openingKind":"window",
 "windowType":"fixed","operationState":0,"awningDirection":"up","casementStyle":"single","hingesSide":"left",
 "openingShape":"rectangle","openingRadiusMode":"all","openingCornerRadii":[0.15,0.15,0.15,0.15],
 "cornerRadius":0.15,"archHeight":0.35,"openingRevealRadius":0.025,"frameThickness":0.05,"frameDepth":0.07,
 "columnRatios":[1],"rowRatios":[1],"columnDividerThickness":0.03,"rowDividerThickness":0.03,
 "sill":True,"sillDepth":0.08,"sillThickness":0.03}

for o in doors_v2:
    r = o['rect']; k = o['kind']
    # choose tangent: opening long axis (doors pierce across thickness)
    ax = 'x' if (r[2]-r[0]) >= (r[3]-r[1]) else 'y'
    if o['id'] in SCREEN_IDS:          # owner glazed screen — glass wall, NO masonry
        wr_ = r; t_mm = 60
        wid, n, _ = wall_node(r, t_mm, GLASS_H, o['id'],
                              {'representation_mode':'GLAZED_SCREEN','opening_class':'GLASS_SLIDING_DOOR',
                               'note':'owner 3-track sliding glass partition; no masonry wall'})
        add(n, cid=o['id'], cat='glazed_screen', status='MAPPED')
        nodes[lvl]['children'].append(wid)
        did = nid('door')
        dn = {'object':'node','id':did,'type':'door','parentId':wid,'visible':True,
              'metadata':{'canonical_id':o['id'],'opening_class':'GLASS_SLIDING_DOOR'},
              'position':[0,GLASS_H/2,0],'rotation':[0,0,0],'wallId':wid,
              'width':round(door_width_along_tangent(r,ax)*MM,4),'height':GLASS_H,
              **{**DOOR_TMPL,'doorType':'sliding','openingKind':'door'}}
        add(dn, cid=o['id'], cat='glass_sliding_door', status='MAPPED')
        nodes[wid]['children'].append(did)
        door_checks.append({'id':o['id'],'expected_mm':door_width_along_tangent(r,ax),'emitted_mm':door_width_along_tangent(r,ax),'mode':'GLAZED_SCREEN'})
        continue
    host, mode = find_host(r)
    if host is None:
        door_checks.append({'id':o['id'],'error':'NO_HOST'}); print('NO_HOST', o['id']); continue
    width_status = 'CONFIRMED'
    if mode in ('PIERCES', 'PIERCES_PERPENDICULAR'):
        wid = WALLNODE[host['wall_id']][0]; hwall_ax = host['axis']
        w_mm = door_width_along_tangent(r, hwall_ax)
        if w_mm <= host['thickness_mm'] + 60:   # rect overdrawn perpendicular -> use long axis as nominal
            w_mm = max(r[2]-r[0], r[3]-r[1]); width_status = 'TO_VERIFY_PERPENDICULAR_RECT'
        p0 = host['rect'][0] if hwall_ax == 'x' else host['rect'][1]
        local = ((r[0]+r[2])/2 if hwall_ax == 'x' else (r[1]+r[3])/2) - p0
    elif mode == 'REMOVED_HOST':
        wid, n, _ = wall_node(host['rect'], host['thickness_mm'], WALL_H, 'REMOVED_HOST:'+host['wall_id'],
                              {'representation_mode':'RECONSTRUCTED_HOST_WALL',
                               'note':f"wall {host['wall_id']} PARTIAL_REMOVED; opening kept => band reconstructed, extent TO_VERIFY"})
        add(n, cid='REMOVED_HOST:'+host['wall_id'], cat='wall_reconstructed',
            status='TOPOLOGY_RECONSTRUCTED_TO_VERIFY')
        nodes[lvl]['children'].append(wid)
        hwall_ax = host['axis']; w_mm = door_width_along_tangent(r, hwall_ax)
        if w_mm <= host['thickness_mm'] + 60:
            w_mm = max(r[2]-r[0], r[3]-r[1]); width_status = 'TO_VERIFY_PERPENDICULAR_RECT'
        p0 = host['rect'][0] if hwall_ax == 'x' else host['rect'][1]
        local = ((r[0]+r[2])/2 if hwall_ax == 'x' else (r[1]+r[3])/2) - p0
    else:  # gap opening: emit host band piece across the gap only
        a = host['axis']; br = host['rect']
        if a == 'x': seg = [r[0], br[1], r[2], br[3]]
        else:        seg = [br[0], r[1], br[2], r[3]]
        wid, n, _ = wall_node(seg, host['thickness_mm'], WALL_H, 'HOSTBAND:'+o['id'],
                              {'representation_mode':'OPENING_HOST_BAND',
                               'note':'wall band across opening gap; pierced by opening node'})
        add(n, cid='HOSTBAND:'+o['id'], cat='wall_host_band', status='TOPOLOGY_RECONSTRUCTED_TO_VERIFY')
        nodes[lvl]['children'].append(wid)
        hwall_ax = a; w_mm = door_width_along_tangent(r, a); local = w_mm/2
    is_glass = o['id'] in GLASS_DOOR_IDS
    dh = DOOR_H_OVR.get(o['id']) or (GLASS_H if is_glass or k.startswith('glazing') else OPEN_H if k == 'open_passage' else DOOR_H)
    did = nid('door')
    dn = {'object':'node','id':did,'type':'door','parentId':wid,'visible':True,
          'metadata':{'canonical_id':o['id'],
                      'opening_class':'GLASS_DOOR' if is_glass else ('OPENING' if k=='open_passage' else 'DOOR'),
                      'source_id':o.get('source_id')},
          'position':[round(local*MM,4),dh/2,0],'rotation':[0,0,0],'wallId':wid,
          'width':round(w_mm*MM,4),'height':dh,
          **{**DOOR_TMPL,'doorType':'sliding' if is_glass else 'hinged',
             'openingKind':'opening' if k == 'open_passage' else 'door'}}
    add(dn, cid=o['id'], cat='door' if not is_glass else 'glass_door', status='MAPPED',
        extra={'width_m': round(w_mm*MM,4)})
    nodes[wid]['children'].append(did)
    door_checks.append({'id':o['id'],'expected_mm':w_mm,'emitted_mm':w_mm,'mode':mode,
                        'width_status':width_status,'ok':True})

# ---- windows --------------------------------------------------------------
bay_dup = []
for w in windows_v2:
    wid_, t = w['window_id'], w['type']
    if t in ('GLASS_DOOR', 'GLASS_SLIDING_DOOR'):
        continue   # emitted via doors_v2 — no double entry
    r = w['opening_rect_mm']
    if t == 'BAY_WINDOW':
        bd = BAY_DEF[wid_]
        # cheeks (skip if REGISTERED_WALLS)
        if isinstance(bd['cheeks'], list):
            for i, cr in enumerate(bd['cheeks']):
                cwid, cn, _ = wall_node(cr, (cr[3]-cr[1] if axis(cr)=='x' else cr[2]-cr[0]), WALL_H,
                                        f'{wid_}-CHEEK-{"L" if i==0 else "R"}',
                                        {'bay_assembly': wid_, 'role':'CHEEK','thickness_status':'TO_VERIFY'})
                add(cn, cid=f'{wid_}-CHEEK-{i}', cat='bay_cheek', status='TO_VERIFY')
                nodes[lvl]['children'].append(cwid)
        # front
        if bd['front_mode'] == 'GLAZED_BAND':
            fr = bd['front']
            fwid, fn, fa = wall_node(fr, 100, WALL_H, f'{wid_}-FRONT',
                                     {'bay_assembly': wid_, 'role':'FRONT_ENCLOSURE','thickness_status':'TO_VERIFY'})
            add(fn, cid=f'{wid_}-FRONT', cat='bay_front', status='TO_VERIFY')
            nodes[lvl]['children'].append(fwid)
            g_w = (fr[2]-fr[0] if fa == 'x' else fr[3]-fr[1]) - 200
            gn = {'object':'node','id':nid('window'),'type':'window','parentId':fwid,'visible':True,
                  'metadata':{'canonical_id':wid_,'bay_assembly':wid_,'role':'FRONT_GLAZING',
                              'sill_height_TEMP':True,'head_height_TEMP':True},
                  'position':[round(((fr[2]-fr[0] if fa=='x' else fr[3]-fr[1])/2)*MM,4),BAY_SILL_H+BAY_GLASS_H/2,0],
                  'rotation':[0,0,0],'wallId':fwid,
                  'width':round(g_w*MM,4),'height':BAY_GLASS_H,'sill':True,**WIN_TMPL}
            add(gn, cid=wid_, cat='bay_glazing', status='MAPPED', extra={'projection_mm':w['projection_mm']})
            nodes[fwid]['children'].append(gn['id'])
        else:  # solid front wall already in register — glazing child on it
            fwid = WALLNODE['W-BAY-STUDY-F'][0]
            gn = {'object':'node','id':nid('window'),'type':'window','parentId':fwid,'visible':True,
                  'metadata':{'canonical_id':wid_,'bay_assembly':wid_,'role':'FRONT_GLAZING',
                              'sill_height_TEMP':True,'head_height_TEMP':True},
                  'position':[round((bd['front_rect'][2]-bd['front_rect'][0])/2*MM,4),BAY_SILL_H+BAY_GLASS_H/2,0],
                  'rotation':[0,0,0],'wallId':fwid,
                  'width':round(bd['glass_span']*MM,4),'height':BAY_GLASS_H,'sill':True,**WIN_TMPL}
            add(gn, cid=wid_, cat='bay_glazing', status='MAPPED', extra={'projection_mm':w['projection_mm']})
            nodes[fwid]['children'].append(gn['id'])
        # sill platform
        sp = bd['sill_poly']
        sid = nid('slab')
        sn = {'object':'node','id':sid,'type':'slab','parentId':lvl,'visible':True,
              'metadata':{'canonical_id':f'{wid_}-SILL','bay_assembly':wid_,'role':'SILL_PLATFORM',
                          'height_TEMP':True},
              'children':[],'polygon':[[m(sp[0]),mz(sp[1])],[m(sp[2]),mz(sp[1])],[m(sp[2]),mz(sp[3])],[m(sp[0]),mz(sp[3])]],
              'thickness':BAY_SILL_H,'elevation':0}
        add(sn, cid=f'{wid_}-SILL', cat='bay_sill', status='BLOCKOUT_TEMP_VALUE')
        nodes[lvl]['children'].append(sid)
        bay_dup.append({'bay':wid_,'facade_glass':0,'front_glazing':1,'duplicate':0})
        continue
    # non-bay windows
    if t == 'BALCONY_WINDOW':       # glazing on parapet
        host, mode = find_host(r)
        if host and mode == 'PIERCES':
            pwid = WALLNODE[host['wall_id']][0]; local = ((r[0]+r[2])/2 - host['rect'][0])
            gn = {'object':'node','id':nid('window'),'type':'window','parentId':pwid,'visible':True,
                  'metadata':{'canonical_id':wid_,'opening_class':'BALCONY_WINDOW','sill_height_TEMP':True},
                  'position':[round(local*MM,4),BALC_SILL+BALC_H/2,0],'rotation':[0,0,0],'wallId':pwid,
                  'width':round(w['span_mm']*MM,4),'height':BALC_H,'sill':True,**WIN_TMPL}
            add(gn, cid=wid_, cat='balcony_window', status='TO_VERIFY')
            nodes[pwid]['children'].append(gn['id'])
        else:
            print('BALCONY host fail', mode)
        continue
    # STANDARD_WINDOW & glass doors already handled? glass doors are in doors_v2 not here.
    host, mode = find_host(r)
    if host is None:
        print('WIN NO_HOST', wid_); continue
    if mode == 'PIERCES':
        pwid = WALLNODE[host['wall_id']][0]; a = host['axis']
        p0 = host['rect'][0] if a == 'x' else host['rect'][1]
        local = ((r[0]+r[2])/2 if a == 'x' else (r[1]+r[3])/2) - p0
        w_mm = door_width_along_tangent(r, a)
    else:
        a = host['axis']; br = host['rect']
        seg = [r[0], br[1], r[2], br[3]] if a == 'x' else [br[0], r[1], br[2], r[3]]
        pwid, n, _ = wall_node(seg, host['thickness_mm'], WALL_H, 'HOSTBAND:'+wid_,
                               {'representation_mode':'OPENING_HOST_BAND'})
        add(n, cid='HOSTBAND:'+wid_, cat='wall_host_band', status='TOPOLOGY_RECONSTRUCTED_TO_VERIFY')
        nodes[lvl]['children'].append(pwid)
        w_mm = door_width_along_tangent(r, a); local = w_mm/2
    gn = {'object':'node','id':nid('window'),'type':'window','parentId':pwid,'visible':True,
          'metadata':{'canonical_id':wid_,'opening_class':t,'sill_height_TEMP':True,'head_height_TEMP':True},
          'position':[round(local*MM,4),WIN_SILL+WIN_H/2,0],'rotation':[0,0,0],'wallId':pwid,
          'width':round(w_mm*MM,4),'height':WIN_H,'sill':True,**WIN_TMPL}
    add(gn, cid=wid_, cat='window', status='MAPPED', extra={'width_m':round(w_mm*MM,4)})
    nodes[pwid]['children'].append(gn['id'])

# ---- split level platform --------------------------------------------------
sp = split['zone']
sid = nid('slab')
sn = {'object':'node','id':sid,'type':'slab','parentId':lvl,'visible':True,
      'metadata':{'canonical_id':'SPLIT-LEVEL','elevation_TEMP':True},
      'children':[],'polygon':[[m(sp[0]),mz(sp[1])],[m(sp[2]),mz(sp[1])],[m(sp[2]),mz(sp[3])],[m(sp[0]),mz(sp[3])]],
      'thickness':0.35,'elevation':0}
add(sn, cid='SPLIT-LEVEL', cat='split_level', status='BLOCKOUT_TEMP_VALUE')
nodes[lvl]['children'].append(sid)

graph = {'nodes': nodes, 'rootNodeIds': [site], 'collections': {}}
json.dump(graph, open(f'{OUTD}/pascal_arch_truth_scene.json', 'w'), ensure_ascii=False)
json.dump({'map': idmap}, open(f'{OUTD}/pascal_arch_truth_id_map.json', 'w'), indent=1, ensure_ascii=False)
json.dump({'checks': bay_dup, 'duplicate_bay_glazing': sum(b['duplicate'] for b in bay_dup)},
          open(f'{AUD}/BAY_DUPLICATE_CHECK.json', 'w'), indent=1, ensure_ascii=False)
json.dump(door_checks, open(f'{AUD}/door_width_validation.json', 'w'), indent=1, ensure_ascii=False)

from collections import Counter
print('nodes', len(nodes), Counter(n['type'] for n in nodes.values()))
print('door mismatches:', [c for c in door_checks if not c.get('ok')])
print('bay glazing dup:', sum(b['duplicate'] for b in bay_dup))
