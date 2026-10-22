#!/usr/bin/env python3
"""build_master_direct_v1.py — MASTER linework -> Pascal (validation-grade).

Walls   : face-paired bands from PRE_BLENDER_MASTER_V2 S-S.WALL
Doors   : XY from MASTER F-DOOR swing arcs (hinge+radius); id/type from
          resolved door semantics by nearest position
Openings: 9 verified entries (95ab90e) hang on bands; gap openings get a
          HOST_BAND wall piece reconstructed from flanking bands.
Output  : master_direct_arch_v1.json + pascal graph -> pascal-master-direct-arch-v1
"""
import json
from collections import Counter
import matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle

BASE = '/Users/xiwei/interior_design/projects/c_type_home'
AUD = f'{BASE}/design/pascal_b1/wall_audit'
OUTD = f'{BASE}/design/pascal_b1'
DX, DY = -1298172.0, 296458.0
MM = 0.001
def m(v): return round(v*MM, 4)
def mz(v): return round(-v*MM, 4)

WALL_H, PARAPET_H = 2.5, 1.05
DOOR_H, GLASS_H, ENTRY_H, OPEN_H = 2.1, 2.4, 2.4, 2.4
BAY_SILL_H, BAY_GLASS_H = 0.45, 2.0
BALC_SILL, BALC_H = 1.05, 1.4
WIN_SILL, WIN_H = 0.9, 1.5

_bands_doc = json.load(open(f'{OUTD}/master_direct_arch_v1_walls.json'))
bands = _bands_doc['walls']
PIERS = _bands_doc.get('piers', [])
FDG = json.load(open(f'{AUD}/F_DOOR_GEOMETRY.json'))
WREG = json.load(open(f'{BASE}/design/s2_current_design_v1/FINAL_WINDOW_REGISTER_95ab90e.json'))['windows']
OPEN = json.load(open(f'{AUD}/FINAL_OPENING_ACTIVE_REGISTER.json'))
OLDW = json.load(open(f'{AUD}/FINAL_WALL_ACTIVE_REGISTER.json'))

parapet_rects = [w['rect'] for w in OLDW['active'] if w['classification'] == 'PARAPET']
def height_of(w):
    r = w['rect']; cx, cy = (r[0]+r[2])/2, (r[1]+r[3])/2
    for pr in parapet_rects:
        if pr[0]-80 <= cx <= pr[2]+80 and pr[1]-80 <= cy <= pr[3]+80:
            return PARAPET_H, 'PARAPET'
    return WALL_H, 'STOREY'

# ---------- doors from F-DOOR swing arcs ------------------------------------
groups = {}
for n, v in FDG.items():
    for e in v['edges']:
        if 'center' in e:
            c = (round(e['center'][0]+DX), round(e['center'][1]+DY))
            groups.setdefault(c, []).append(
                {'r': round(e['radius']),
                 'ends': [(round(p[0]+DX), round(p[1]+DY)) for p in e['pts']]})

def band_near(ba, coord, span, tol=450):
    """nearest band with axis ba ('y'=wall along x, 'x'=along y)
    whose strip coordinate is within tol of coord and overlaps span."""
    best, bd = None, 1e9
    for w in bands:
        if w['axis'] != ba: continue
        r = w['rect']
        c = (r[1]+r[3])/2 if ba == 'y' else (r[0]+r[2])/2
        u0, u1 = (r[0], r[2]) if ba == 'y' else (r[1], r[3])
        if not (u0-300 <= span[1] and span[0] <= u1+300): continue
        d = abs(c-coord)
        if d < bd: best, bd = w, d
    return best if bd <= tol else None

sem = OPEN['doors']
def sem_match(px, py):
    best, bd = None, 1e9
    for d in sem:
        r = d['rect']; cc = ((r[0]+r[2])/2, (r[1]+r[3])/2)
        dd = ((cc[0]-px)**2 + (cc[1]-py)**2)**.5
        if dd < bd: best, bd = d, dd
    return best if bd < 1500 else None

doors_fc = []
for c, arcs in groups.items():
    cnt = Counter(tuple(e) for a in arcs for e in a['ends'])
    rest = cnt.most_common(1)[0][0]
    dx, dy = rest[0]-c[0], rest[1]-c[1]
    # leaf rest direction = wall tangent; band axis is the PERPENDICULAR coord
    tangent = 'x' if abs(dx) >= abs(dy) else 'y'
    ba = 'y' if tangent == 'x' else 'x'        # band['axis']: 'y'=runs along x
    w_mm = arcs[0]['r']
    coord = c[0] if tangent == 'y' else c[1]   # band strip coord (perp to tangent)
    u = sorted([c[1], rest[1]]) if tangent == 'y' else sorted([c[0], rest[0]])
    pt = (c[0], (u[0]+u[1])/2) if tangent == 'y' else ((u[0]+u[1])/2, c[1])
    s = sem_match(pt[0], pt[1])
    doors_fc.append({'axis': tangent, 'band_axis': ba, 'span': u, 'band_coord': coord,
                     'width_mm': w_mm, 'host': None,
                     'sem_id': s['id'] if s else None,
                     'kind': s['kind'] if s else 'door_unmatched',
                     'hinge': list(c), 'rest': list(rest)})

# ---------- Pascal graph -----------------------------------------------------
SEQ = [0]
def nid(p):
    SEQ[0] += 1; return f'{p}_md_{SEQ[0]:04d}'
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
lvl_n = {'object':'node','id':nid('level'),'type':'level','parentId':bldg_n['id'],'visible':True,
         'metadata':{},'children':[],'level':0,'baseElevation':0,'height':WALL_H}
site_n['children'] = [bldg_n['id']]; bldg_n['children'] = [lvl_n['id']]
site = add(site_n); bldg = add(bldg_n); lvl = add(lvl_n)

def wall_node_rect(rect, t_mm, h, cid, meta=None, ax=None):
    """ax: 'x' = wall runs along x, 'y' = along y. Defaults to longer side.
    Callers should pass the band's declared axis so the emitted centerline
    matches the extractor's intent (WB008_AXIS_NORMALIZATION)."""
    if ax is None:
        ax = 'x' if (rect[2]-rect[0]) >= (rect[3]-rect[1]) else 'y'
    if ax == 'x':
        st, en = [m(rect[0]), mz((rect[1]+rect[3])/2)], [m(rect[2]), mz((rect[1]+rect[3])/2)]
    else:
        st, en = [m((rect[0]+rect[2])/2), mz(rect[1])], [m((rect[0]+rect[2])/2), mz(rect[3])]
    wid = nid('wall')
    n = {'object':'node','id':wid,'type':'wall','parentId':lvl,'visible':True,
         'metadata':{'canonical_id':cid,'source':'S-S.WALL face-pair',**(meta or {})},
         'children':[],'thickness':round(t_mm*MM,4),'height':h,
         'start':st,'end':en,'frontSide':'unknown','backSide':'unknown'}
    return wid, n, ax

def band_ax(b):
    """band axis 'y' = strip varies in y = wall runs along x."""
    return 'x' if b['axis'] == 'y' else 'y'

def wall_node(w, h, cid, meta=None):
    return wall_node_rect(w['rect'], w['thickness'], h, cid, meta, ax=band_ax(w))

WB = {}
for w in bands:
    h, cls = height_of(w)
    wid, n, _ = wall_node(w, h, w['id'], {'wall_class': cls, 'height_status': 'BLOCKOUT_TEMP_VALUE'})
    add(n, cid=w['id'], cat='wall', extra={'thickness_mm': w['thickness'], 'class': cls})
    nodes[lvl]['children'].append(wid)
    WB[w['id']] = (wid, w)

# junction piers recovered from PIER_JAMB_DETAIL linework
for i, p in enumerate(PIERS):
    wid, n, _ = wall_node_rect(p['rect'], min(p['rect'][2]-p['rect'][0], p['rect'][3]-p['rect'][1]),
                               WALL_H, f'PIER-{i:02d}',
                               {'wall_class': 'PIER', 'source': 'S-S.WALL junction linework',
                                'height_status': 'BLOCKOUT_TEMP_VALUE',
                                'evidence': p['evidence']})
    add(n, cid=f'PIER-{i:02d}', cat='wall_pier')
    nodes[lvl]['children'].append(wid)

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

def emit_door(wid, w, local_mm, w_mm, dh, cid, klass, meta=None):
    did = nid('door')
    dn = {'object':'node','id':did,'type':'door','parentId':wid,'visible':True,
          'metadata':{'canonical_id':cid,'opening_class':klass,**(meta or {})},
          'position':[round(local_mm*MM,4),dh/2,0],'rotation':[0,0,0],'wallId':wid,
          'width':round(w_mm*MM,4),'height':dh,
          **{**DOOR_TMPL,'doorType':'sliding' if klass in ('GLASS_DOOR','GLASS_SLIDING_DOOR') else 'hinged',
             'openingKind':'opening' if klass == 'OPENING' else 'door'}}
    add(dn, cid=cid, cat='door')
    nodes[wid]['children'].append(did)
    return did

def host_or_gap(ax, rect, tol=400):
    """band containing rect, else reconstruct band piece from flanking bands.
    ax = band axis: 'y'=wall along x, 'x'=along y."""
    ba = ax
    for w in bands:
        r = w['rect']
        if w['axis'] != ba: continue
        # tangent: band must actually cover the opening span (50 slack);
        # strip: rect may be off-center up to tol
        if ba == 'y':
            in_tan = r[0]-50 <= rect[0] and r[2]+50 >= rect[2]
            in_strip = r[1]-tol <= rect[1] and r[3]+tol >= rect[3]
        else:
            in_tan = r[1]-50 <= rect[1] and r[3]+50 >= rect[3]
            in_strip = r[0]-tol <= rect[0] and r[2]+tol >= rect[2]
        if in_tan and in_strip:
            return w, rect, 'PIERCES'
    # nearest collinear band sharing the strip.
    rc = (rect[1]+rect[3])/2 if ba == 'y' else (rect[0]+rect[2])/2
    o0, o1 = (rect[0], rect[2]) if ba == 'y' else (rect[1], rect[3])
    best, bd = None, 1e9
    for w in bands:
        if w['axis'] != ba: continue
        r = w['rect']
        sc = (r[1]+r[3])/2 if ba == 'y' else (r[0]+r[2])/2
        u0, u1 = (r[0], r[2]) if ba == 'y' else (r[1], r[3])
        d = abs(sc-rc)
        abut = (u1 >= o0-2500 and u0 <= o1+2500)
        if abut and d < bd: best, bd = w, d
    if not best or bd > tol: return None, None, 'NO_HOST'
    r0 = best['rect']
    t = (r0[3]-r0[1]) if ba == 'y' else (r0[2]-r0[0])
    if ba == 'y': piece = [rect[0], r0[1], rect[2], r0[3]]
    else:         piece = [r0[0], rect[1], r0[2], rect[3]]
    return {'id': 'HOSTBAND', 'rect': piece, 'axis': ba, 'thickness': round(t)}, piece, 'HOST_BAND'

# ---- doors ------------------------------------------------------------------
hostbands_used = []
VERIFIED_IDS = {w['window_id'] for w in WREG}
for d in doors_fc:
    if d['sem_id'] in VERIFIED_IDS:
        print('skip arc door (emitted via registry):', d['sem_id']); continue
    rect = ([d['span'][0], d['band_coord']-100, d['span'][1], d['band_coord']+100]
            if d['axis'] == 'x' else
            [d['band_coord']-100, d['span'][0], d['band_coord']+100, d['span'][1]])
    hb, piece, mode = host_or_gap(d['band_axis'], rect)
    if not hb: print('NO_HOST door', d); continue
    if mode == 'PIERCES':
        wid, w = WB[hb['id']]
    else:
        wid, n, _ = wall_node_rect(piece, hb['thickness'], WALL_H,
                                   'HOSTBAND:'+str(d['hinge']),
                                   {'representation_mode': 'OPENING_HOST_BAND',
                                    'role': 'PASCAL_OPENING_HOST_HELPER',
                                    'physical_ground_truth': False,
                                    'note': 'band across gap, pierced by door'},
                                   ax=band_ax(hb))
        add(n, cid='HOSTBAND:'+str(d['hinge']), cat='wall_host_band')
        nodes[lvl]['children'].append(wid)
        hostbands_used.append(hb)
        w = hb
    r = w['rect']; p0 = r[0] if w['axis'] == 'y' else r[1]
    local = ((d['span'][0]+d['span'][1])/2) - p0
    k = d['kind']
    emit_door(wid, w, local, d['width_mm'],
              ENTRY_H if d['sem_id'] == 'ENT-1' else (OPEN_H if k == 'open_passage' else DOOR_H),
              d['sem_id'] or 'UNMATCHED:'+str(d['hinge']),
              'OPENING' if k == 'open_passage' else 'DOOR',
              {'source': 'F-DOOR swing arc', 'host_mode': mode, 'arc_hinge': d['hinge']})

# ---- 9 verified openings ----------------------------------------------------
bay_emitted = {}
for w in WREG:
    oid, t = w['window_id'], w['type']; r = w['opening_rect_mm']
    rax = 'x' if (r[2]-r[0]) >= (r[3]-r[1]) else 'y'   # opening long axis = wall tangent
    rba = 'y' if rax == 'x' else 'x'                  # band axis: 'y'=wall along x
    if t == 'GLASS_DOOR' or (t == 'BALCONY_WINDOW') or t == 'STANDARD_WINDOW':
        hb, piece, mode = host_or_gap(rba, r)
        if not hb: print('NO_HOST', oid); continue
        if mode == 'PIERCES':
            wid, wn = WB[hb['id']]
        else:
            t_mm = hb['thickness']
            wid, n, _ = wall_node_rect(piece, t_mm,
                                       PARAPET_H if t == 'GLASS_DOOR' else WALL_H,
                                       'HOSTBAND:'+oid,
                                       {'representation_mode': 'OPENING_HOST_BAND',
                                        'role': 'PASCAL_OPENING_HOST_HELPER',
                                        'physical_ground_truth': False},
                                       ax=band_ax(hb))
            add(n, cid='HOSTBAND:'+oid, cat='wall_host_band')
            nodes[lvl]['children'].append(wid)
            hostbands_used.append(hb)
            wn = hb
        wr = wn['rect']; ax = wn['axis']
        u0 = (r[0] if ax == 'y' else r[1]); u1 = (r[2] if ax == 'y' else r[3])
        w_mm = u1-u0
        p0 = wr[0] if ax == 'y' else wr[1]
        local = ((u0+u1)/2) - p0
        if t == 'GLASS_DOOR':
            emit_door(wid, wn, local, w_mm, GLASS_H, oid, 'GLASS_DOOR',
                      {'registry': '95ab90e'})
        else:
            sill = BALC_SILL if t == 'BALCONY_WINDOW' else WIN_SILL
            hh = BALC_H if t == 'BALCONY_WINDOW' else WIN_H
            gn = {'object':'node','id':nid('window'),'type':'window','parentId':wid,'visible':True,
                  'metadata':{'canonical_id':oid,'opening_class':t,'registry':'95ab90e'},
                  'position':[round(local*MM,4),sill+hh/2,0],'rotation':[0,0,0],'wallId':wid,
                  'width':round(w_mm*MM,4),'height':hh,'sill':True,**WIN_TMPL}
            add(gn, cid=oid, cat='window')
            nodes[wid]['children'].append(gn['id'])
    elif t == 'GLASS_SLIDING_DOOR':
        wid, n, _ = wall_node_rect(r, 60, GLASS_H, oid,
                                   {'representation_mode':'GLAZED_SCREEN',
                                    'opening_class':'GLASS_SLIDING_DOOR',
                                    'note':'owner 3-track sliding glass partition; no masonry wall'})
        add(n, cid=oid, cat='glazed_screen')
        nodes[lvl]['children'].append(wid)
        emit_door(wid, {'rect': r, 'axis': 'x'}, (r[2]-r[0])/2, r[2]-r[0],
                  GLASS_H, oid, 'GLASS_SLIDING_DOOR', {'registry': '95ab90e'})
    elif t == 'BAY_WINDOW':
        proj = w['projection_mm']
        bay_emitted[oid] = {'projection_mm': proj}
        south = r[1] < 5000
        # front band: parallel band beyond facade opening by ~proj
        target = (r[1]-proj) if south else (r[3]+proj)
        cands = [b for b in bands if b['axis'] == 'y'
                 and (r[0]-600 <= (b['rect'][0]+b['rect'][2])/2 <= r[2]+600)
                 and abs((b['rect'][1]+b['rect'][3])/2 - target) < 500]
        if not cands:
            # try V-axis bays (side projection)
            cands = [b for b in bands if b['axis'] == 'x'
                     and abs((b['rect'][0]+b['rect'][2])/2 - (r[0]-proj if r[0]<8000 else r[2]+proj)) < 500]
        fb = min(cands, key=lambda b: abs((b['rect'][1]+b['rect'][3])/2 - target)) if cands else None
        if not fb: print('NO_BAY_FRONT', oid); continue
        wid, wn = WB[fb['id']]; fr = fb['rect']
        g_w = (r[2]-r[0])
        local = ((r[0]+r[2])/2) - fr[0]
        gn = {'object':'node','id':nid('window'),'type':'window','parentId':wid,'visible':True,
              'metadata':{'canonical_id':oid,'bay_assembly':oid,'role':'FRONT_GLAZING',
                          'sill_height_TEMP':True,'head_height_TEMP':True,'registry':'95ab90e'},
              'position':[round(local*MM,4),BAY_SILL_H+BAY_GLASS_H/2,0],'rotation':[0,0,0],
              'wallId':wid,'width':round(g_w*MM,4),'height':BAY_GLASS_H,'sill':True,**WIN_TMPL}
        add(gn, cid=oid, cat='bay_glazing',
            extra={'projection_mm': proj, 'front_band': fb['id']})
        bay_emitted[oid]['front_band'] = fb['id']
        bay_emitted[oid]['front_band_rect'] = fr
        nodes[wid]['children'].append(gn['id'])
        # sill slab between facade opening and front band
        sp = [min(r[0], fr[0]), min(r[1]-60, fr[1]), max(r[2], fr[2]), max(r[3]+60, fr[3])]
        sid = nid('slab')
        sn = {'object':'node','id':sid,'type':'slab','parentId':lvl,'visible':True,
              'metadata':{'canonical_id':f'{oid}-SILL','bay_assembly':oid,'role':'SILL_PLATFORM',
                          'height_TEMP':True},
              'children':[],
              'polygon':[[m(sp[0]),mz(sp[1])],[m(sp[2]),mz(sp[1])],[m(sp[2]),mz(sp[3])],[m(sp[0]),mz(sp[3])]],
              'thickness':BAY_SILL_H,'elevation':0}
        add(sn, cid=f'{oid}-SILL', cat='bay_sill', status='BLOCKOUT_TEMP_VALUE')
        nodes[lvl]['children'].append(sid)

# consolidated derived model: physical geometry + opening semantics, provenance-tagged
model = {
 'model': 'master_direct_arch_v1',
 'physical_source': '世纪欣园FF_PRE_BLENDER_MASTER_V2.FCStd (S-S.WALL + F-DOOR linework)',
 'semantic_source': 'FINAL_WINDOW_REGISTER_95ab90e (9 verified openings)',
 'units': 'mm',
 'walls': [{'band_id': b['id'], 'rect_mm': b['rect'], 'axis': b['axis'],
            'thickness_mm': b['thickness'], 'centerline_mm': b['centerline'],
            'register_state': 'S-S.WALL_FACE_PAIR'} for b in bands]
        + [{'band_id': h['id'], 'rect_mm': h['rect'], 'axis': h['axis'],
            'thickness_mm': h['thickness'],
            'register_state': 'HOST_BAND_RECONSTRUCTED',
            'role': 'PASCAL_OPENING_HOST_HELPER', 'physical_ground_truth': False}
           for h in hostbands_used]
        + [{'band_id': f'PIER-{i:02d}', 'rect_mm': p['rect'], 'axis': 'pier',
            'thickness_mm': min(p['rect'][2]-p['rect'][0], p['rect'][3]-p['rect'][1]),
            'register_state': 'S-S.WALL_JUNCTION_PIER', 'evidence': p['evidence']}
           for i, p in enumerate(PIERS)],
 'doors': [{'sem_id': d['sem_id'], 'span_mm': d['span'], 'band_axis': d['band_axis'],
            'band_coord_mm': d['band_coord'], 'width_mm': d['width_mm'],
            'hinge_mm': d['hinge'], 'kind': d['kind'], 'source': 'F-DOOR swing arc'}
           for d in doors_fc],
 'openings': [{'window_id': w['window_id'], 'type': w['type'],
               'opening_rect_mm': w['opening_rect_mm'], 'host_wall_id': w.get('host_wall_id'),
               'bay_assembly': w.get('bay_assembly')} for w in WREG],
 'bays': bay_emitted,
}
json.dump(model, open(f'{OUTD}/master_direct_arch_v1.json', 'w'), indent=1, ensure_ascii=False)

graph = {'nodes': nodes, 'rootNodeIds': [site], 'collections': {}}
json.dump(graph, open(f'{OUTD}/pascal_master_direct_scene.json', 'w'), indent=1)
json.dump({'map': idmap}, open(f'{OUTD}/pascal_master_direct_idmap.json', 'w'), indent=1, ensure_ascii=False)
print('nodes:', len(nodes),
      'walls:', sum(1 for n in nodes.values() if n['type']=='wall'),
      'doors:', sum(1 for n in nodes.values() if n['type']=='door'),
      'windows:', sum(1 for n in nodes.values() if n['type']=='window'),
      'slabs:', sum(1 for n in nodes.values() if n['type']=='slab'))
print('doors_fc:', [(d['sem_id'], d['host'], d['width_mm']) for d in doors_fc])
json.dump({'doors_extracted': doors_fc}, open(f'{OUTD}/F_DOOR_EXTRACTION.json','w'), indent=1, ensure_ascii=False)
