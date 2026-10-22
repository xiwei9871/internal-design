"""master_v2_to_pascal.py — deterministic MASTER_V2 → Pascal SceneGraph converter.

Input : design/b1_blockout/b1_model.json  (verified extraction of PRE_BLENDER_MASTER_V2
          + canonical architecture + formalization layer, canonical mm coordinates)
Output: design/pascal_b1/pascal_full_scene.json   (Pascal SceneGraph {nodes, rootNodeIds})
        design/pascal_b1/pascal_full_id_map.json  (canonical/FCStd → Pascal node map)

Rules (per owner directive):
- Pascal catalog supplies ONLY item type/placeholder visual; actual footprint is carried
  by item.scale so effective dims == MASTER_V2 dims, plus metadata.actual_project_size.
- No human re-drawing: same input hash -> same output.
- Heights without field evidence stay BLOCKOUT_TEMP_VALUE.
"""
import json, os, math, hashlib

BASE = '/Users/xiwei/interior_design/projects/c_type_home'
MODEL = f'{BASE}/design/b1_blockout/b1_model.json'
OUTD = f'{BASE}/design/pascal_b1'
os.makedirs(OUTD, exist_ok=True)

M = json.load(open(MODEL))
MM = 0.001
def m(v): return round(v * MM, 4)   # canonical mm -> m, no re-origin (keep source coords)
def mz(v): return round(-v * MM, 4)  # canonical +y(north) -> Pascal -z: Pascal's
                                    # "align view to north" places -Z up-screen.
                                    # z=+y renders the whole plan north-down (mirrored).

# MODE: 'blocks' (furniture as block nodes, no catalog) | 'items' (catalog assets)
# SKIP_ITEMS: architecture-only scene
import sys
MODE = 'blocks'
SKIP_ITEMS = '--arch-only' in sys.argv
if '--items' in sys.argv: MODE = 'items'
OUT_SUFFIX = {'blocks': 'blocks', 'items': 'full'}[MODE]

WALL_H = 2.5      # TEMP nominal storey height (blockout)
PARAPET_H = 1.05  # TEMP

# approved per-item dimensions (HUMAN_APPROVED_WITH_TO_VERIFY) — label -> (height_m, base_z_m, sem_type)
_FDIM = {}
try:
    _fr = json.load(open(f'{BASE}/design/b1_blockout/furniture_3d_dimension_register_v01.json'))['items']
    for _e in _fr:
        _FDIM[_e['label']] = (_e['height'] * 0.001, _e['base_z'] * 0.001, _e.get('semantic_type', ''))
except Exception:
    pass
# kitchen cabinets: PDF shop drawing is the authority (supersedes generic K-* register)
_KC3D = {}
try:
    for _e in json.load(open(os.path.join(OUTD, 'KITCHEN_CABINET_3D_REGISTER_V01.json')))['cabinets']:
        _KC3D[_e['cabinet_id']] = _e
except Exception:
    pass

SEQ = [0]
def nid(prefix):
    SEQ[0] += 1
    return f'{prefix}_v1_{SEQ[0]:04d}'

nodes, idmap = {}, []

def add(node, canonical_id=None, fcstd=None, category=None, room=None, status='MAPPED', extra=None):
    nodes[node['id']] = node
    if canonical_id or fcstd:
        idmap.append({'pascal_id': node['id'], 'canonical_id': canonical_id, 'fcstd': fcstd,
                      'label': node.get('label') or node.get('asset', {}).get('name') or '',
                      'category': category, 'room': room, 'status': status,
                      **(extra or {})})
    return node['id']

# ---------------- site / building / level ----------------
site = add({'object':'node','id':nid('site'),'type':'site','parentId':None,'visible':True,
            'metadata':{},'polygon':{'type':'polygon','points':[[0,2],[17,2],[17,-15],[0,-15]]},'children':[]})
bldg = add({'object':'node','id':nid('building'),'type':'building','parentId':site,'visible':True,
            'metadata':{},'children':[],'position':[0,0,0],'rotation':[0,0,0]})
lvl  = add({'object':'node','id':nid('level'),'type':'level','parentId':bldg,'visible':True,
            'metadata':{},'children':[],'level':0,'baseElevation':0,'height':WALL_H})
nodes[site]['children'] = [bldg]; nodes[bldg]['children'] = [lvl]

# ---------------- wall line merging ----------------
# group segments by (orientation, line coordinate, thickness)
def wall_key(r):
    horiz = (r[3]-r[1]) <= (r[2]-r[0])
    if horiz: return ('h', round((r[1]+r[3])/2), r[3]-r[1])
    return ('v', round((r[0]+r[2])/2), r[2]-r[0])

lines = {}
for w in M['walls'] + M['parapets']:
    k = wall_key(w['rect'])
    lines.setdefault(k, []).append(w)

# opening/window rects indexed by band for host matching.
# G-* glass doors exist in BOTH registries; the door record wins (dedupe by id).
_open_ids = {o['id'] for o in M['openings']}
holes = [{'id':o['id'],'kind':'door','rect':o['rect']} for o in M['openings']] + \
        [{'id':w['id'],'kind':'window','rect':w['rect']} for w in M['windows']
         if w['id'] not in _open_ids]

def hole_on_line(hole_rect, k):
    """hole's cross-band center coincides with this wall line."""
    c = k[1]; band = k[2]/2 + 150
    hc = (hole_rect[0]+hole_rect[2])/2 if k[0]=='v' else (hole_rect[1]+hole_rect[3])/2
    return abs(hc - c) <= band

# Assign each hole to its best host line BEFORE splitting: parallel wall lines
# 200mm apart can both satisfy hole_on_line; the right host is the line where
# the hole span bridges a gap between segments, else max span overlap.
seg_union = {}
for k, segs in lines.items():
    ax = 0 if k[0] == 'h' else 1
    seg_union[k] = sorted((s['rect'][ax], s['rect'][ax+2]) for s in segs)

# canonical_id of opening -> wall segment id that must host it, for rects whose
# drawn extent doesn't sit inside the wall band (e.g. over-wide measured zones).
HOST_OVERRIDE = {'D-CONN-MB-SMB': 'W-INT-X11500'}
seg2line = {}
for k, segs in lines.items():
    for s in segs:
        seg2line.setdefault(s['id'].split('#')[0], k)

BRIDGE_TOL = 75  # mm a hole may be short of a gap end and still bridge it
hole_best = {}
for gi, h in enumerate(holes):
    if h['id'] in HOST_OVERRIDE:
        k = seg2line.get(HOST_OVERRIDE[h['id']])
        hole_best[gi] = k
        # drawn rect is over-wide across the wall band; along-wall span =
        # rect's long axis, centred on the rect centre -> hole pierces the wall.
        ax2 = 0 if k[0] == 'h' else 1
        c = (h['rect'][ax2] + h['rect'][ax2+2]) / 2
        L = max(h['rect'][2]-h['rect'][0], h['rect'][3]-h['rect'][1])
        h['eff_span'] = (c - L/2, c + L/2)
        h['host_override'] = HOST_OVERRIDE[h['id']]
        continue
    best, bs = None, -1
    for k in lines:
        if not hole_on_line(h['rect'], k):
            continue
        ax = 0 if k[0] == 'h' else 1
        sp = (h['rect'][ax], h['rect'][ax+2])
        rng = seg_union[k]
        ov = sum(max(0, min(sp[1], b) - max(sp[0], a)) for a, b in rng)
        brid = any(sp[0] <= rng[i][1]+BRIDGE_TOL and sp[1] >= rng[i+1][0]-BRIDGE_TOL
                   for i in range(len(rng)-1))
        score = ov + (10**6 if brid else 0)
        if score > bs:
            bs, best = score, k
    if best is not None:
        hole_best[gi] = best

def holes_on_line(k):
    ax = 0 if k[0]=='h' else 1
    out = []
    for gi, h in enumerate(holes):
        if hole_best.get(gi) == k:
            out.append({'gid': gi, 'rec': h,
                        'span': h.get('eff_span') or (h['rect'][ax], h['rect'][ax+2])})
    return out

def spans_with_holes(k, segs):
    """Split a line group's segments into walls. A gap between consecutive
    segments joins them into one wall ONLY if covered by a hole record;
    otherwise it's a real void -> separate wall.
    Returns list of (p0,p1,[hole,...])."""
    ax = 0 if k[0]=='h' else 1
    rng = sorted((s['rect'][ax], s['rect'][ax+2]) for s in segs)
    hs = holes_on_line(k)
    claimed = set()
    walls = []
    cur = list(rng[0]); cur_holes = []
    for a, b in rng[1:]:
        gap = (cur[1], a)
        cover = [h for h in hs
                 if h['gid'] not in claimed
                 and h['span'][0] <= gap[0]+BRIDGE_TOL and h['span'][1] >= gap[1]-BRIDGE_TOL]
        if cover:
            for h in cover:
                claimed.add(h['gid']); cur_holes.append(h)
            cur[1] = b
        else:
            walls.append((cur[0], cur[1], cur_holes)); cur = [a,b]; cur_holes = []
    walls.append((cur[0], cur[1], cur_holes))
    # holes embedded INSIDE a segment (not in a gap): attribute by overlap
    for h in hs:
        if h['gid'] in claimed: continue
        for (p0,p1,hl) in walls:
            if h['span'][0] < p1 and h['span'][1] > p0:
                claimed.add(h['gid']); hl.append(h); break
    return walls, claimed

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

GLASS_IDS = {'G-LIV-NBALC','G-GB-BALC','G-DIN-LIV'}
DOOR_H = {'ENT-1':2.2}
GLASS_H = 2.4  # TEMP
WIN_H = 1.8; WIN_SILL = 0.6  # TEMP

claimed_holes = set()
for k, segs in sorted(lines.items(), key=lambda kv: kv[0]):
    th = m(k[2])
    horiz = k[0]=='h'
    is_parapet = all(s in M['parapets'] or any(s is p for p in M['parapets']) for s in segs)
    h = PARAPET_H if is_parapet else WALL_H
    wl, claimed_here = spans_with_holes(k, segs)
    claimed_holes |= claimed_here
    for p0, p1, hole_recs in wl:
        c = m(k[1])
        start = [m(p0), mz(k[1])] if horiz else [m(k[1]), mz(p0)]
        end   = [m(p1), mz(k[1])] if horiz else [m(k[1]), mz(p1)]
        ids = '+'.join(sorted(s['id'].split('#')[0] for s in segs if s['rect'][(0 if horiz else 1)] < p1 and s['rect'][(2 if horiz else 3)] > p0))
        wid = nid('wall')
        node = {'object':'node','id':wid,'type':'wall','parentId':lvl,'visible':True,
                'metadata':{'canonical_ids':ids,'merged_from':len(segs)},
                'children':[],'thickness':th,'height':h,'start':start,'end':end,
                'frontSide':'unknown','backSide':'unknown'}
        add(node, canonical_id=ids, category='wall_parapet' if is_parapet else 'wall',
            status='MAPPED', extra={'centerline':[start,end],'thickness_m':th})
        wall_len = p1 - p0
        ax = 0 if horiz else 1
        for hrec2 in hole_recs:
            hrec = hrec2['rec']
            c0, c1 = hrec.get('eff_span') or (hrec['rect'][ax], hrec['rect'][ax+2])
            c0 = max(c0, p0); c1 = min(c1, p1)
            w_mm = c1 - c0
            if w_mm <= 50: continue
            local = (c0 + c1)/2 - p0
            if hrec['kind'] == 'door':
                is_glass = hrec['id'] in GLASS_IDS
                dh = DOOR_H.get(hrec['id'], GLASS_H if is_glass else 2.1)
                did = nid('door')
                dn = {'object':'node','id':did,'type':'door','parentId':wid,'visible':True,
                      'metadata':{'canonical_id':hrec['id'],
                                  'opening_class':'GLASS_DOOR' if is_glass else 'DOOR',
                                  'height_TEMP': True,
                                  **({'host_override':hrec['host_override'],
                                      'note':'opening rect over-wide across wall band; '
                                             'width reconstructed from long axis — TO_VERIFY'}
                                     if hrec.get('host_override') else {})},
                      'position':[round(local*MM,4), dh/2, 0],'rotation':[0,0,0],'wallId':wid,
                      'width':round(w_mm*MM,4),'height':dh,
                      **{**DOOR_TMPL,'doorType':'sliding' if is_glass else 'hinged',
                         'openingKind':'opening' if hrec['id'].startswith('OPEN-') else 'door'}}
                add(dn, canonical_id=hrec['id'], category='glass_door' if is_glass else 'door',
                    status='MAPPED', extra={'width_m':round(w_mm*MM,4)})
                node['children'].append(did)
            else:
                widn = nid('window')
                ws, wh = WIN_SILL, WIN_H
                clamped = ws + wh > h   # host too low (e.g. glazed band on parapet)
                if clamped: ws, wh = 0.0, h
                wn = {'object':'node','id':widn,'type':'window','parentId':wid,'visible':True,
                      'metadata':{'canonical_id':hrec['id'],'sill_height_TEMP':True,'head_height_TEMP':True,
                                  **({'glazing_fit':'CLAMPED_TO_HOST_WALL','host_wall_h_m':h} if clamped else {})},
                      'position':[round(local*MM,4), ws + wh/2, 0],'rotation':[0,0,0],'wallId':wid,
                      'width':round(w_mm*MM,4),'height':wh,**{**WIN_TMPL,'sill':ws>0}}
                add(wn, canonical_id=hrec['id'], category='window',
                    status='REPRESENTATION_LIMITATION' if clamped else 'MAPPED',
                    extra={'width_m':round(w_mm*MM,4)})
                node['children'].append(widn)

# ---- orphan holes: reconstruct host from PARTIAL_REMOVED walls, else glazed screen ----
_removed = M.get('removed_walls', [])
def removed_host_for(r):
    """A retained opening inside a PARTIAL_REMOVED_TO_VERIFY wall means the wall
    still stands around the opening — the removed part IS the niche/passage.
    Return that wall record so the hole gets a real host."""
    horiz = (r[3]-r[1]) <= (r[2]-r[0])
    hc = (r[1]+r[3])/2 if horiz else (r[0]+r[2])/2
    for w in _removed:
        if 'PARTIAL_REMOVED' not in w['disp']: continue
        wr = w['rect']
        wh = (wr[3]-wr[1]) <= (wr[2]-wr[0])
        if wh != horiz: continue
        wc = (wr[1]+wr[3])/2 if horiz else (wr[0]+wr[2])/2
        wt = (wr[3]-wr[1] if horiz else wr[2]-wr[0])/2
        if abs(hc-wc) <= wt + 50:
            ov = min(r[2] if horiz else r[3], wr[2] if horiz else wr[3]) - \
                 max(r[0] if horiz else r[1], wr[0] if horiz else wr[1])
            if ov > 0: return w
    return None

for i, h in enumerate(holes):
    if i in claimed_holes: continue
    r = h['rect']
    horiz = (r[3]-r[1]) <= (r[2]-r[0])
    ax = 0 if horiz else 1
    host = removed_host_for(r)
    if host:  # wall reconstructed from canonical removed_walls (PARTIAL_REMOVED)
        wr = host['rect']
        th_m = m(wr[3]-wr[1] if horiz else wr[2]-wr[0])
        if horiz:
            start, end = [m(wr[0]), mz((wr[1]+wr[3])/2)], [m(wr[2]), mz((wr[1]+wr[3])/2)]
        else:
            start, end = [m((wr[0]+wr[2])/2), mz(wr[1])], [m((wr[0]+wr[2])/2), mz(wr[3])]
        rep_mode = 'RECONSTRUCTED_HOST_WALL'
        host_id, note = host['id'], f"wall restored from removed_walls[{host['id']}] " \
            f"disposition={host['disp']}; opening pierces it — extent TO_VERIFY"
    else:     # genuinely wall-less: owner-added glazed screen / open edge
        th_m = m(r[3]-r[1] if horiz else r[2]-r[0])
        if horiz:
            start, end = [m(r[0]), mz((r[1]+r[3])/2)], [m(r[2]), mz((r[1]+r[3])/2)]
        else:
            start, end = [m((r[0]+r[2])/2), mz(r[1])], [m((r[0]+r[2])/2), mz(r[3])]
        rep_mode = 'GLAZED_SCREEN' if h['id'] in GLASS_IDS else 'SYNTHESIZED_HOST_WALL'
        host_id = h['id']
        note = ('owner-added glass partition; no masonry wall exists at this line'
                if rep_mode == 'GLAZED_SCREEN' else
                'no source wall segment on this line; wall synthesized to host the opening')
    wid = nid('wall')
    node = {'object':'node','id':wid,'type':'wall','parentId':lvl,'visible':True,
            'metadata':{'canonical_id':host_id,'representation_mode':rep_mode,'note':note},
            'children':[],'thickness':th_m,'height':WALL_H,'start':start,'end':end,
            'frontSide':'unknown','backSide':'unknown'}
    add(node, canonical_id=host_id,
        category='wall_reconstructed' if host else 'wall_synthesized',
        status='TOPOLOGY_RECONSTRUCTED_TO_VERIFY' if host else 'REPRESENTATION_LIMITATION',
        extra={'centerline':[start,end],'thickness_m':th_m})
    w_mm = (wr if host else r)[ax+2] - (wr if host else r)[ax]
    wall_len = w_mm
    p0 = (wr if host else r)[ax]
    local = ((r[ax]+r[ax+2])/2) - p0
    if h['kind']=='door':
        is_glass = h['id'] in GLASS_IDS
        dh = DOOR_H.get(h['id'], GLASS_H if is_glass else 2.1)
        did = nid('door')
        dn = {'object':'node','id':did,'type':'door','parentId':wid,'visible':True,
              'metadata':{'canonical_id':h['id'],'opening_class':'GLASS_DOOR' if is_glass else 'DOOR','height_TEMP':True},
              'position':[round(local*MM,4),dh/2,0],'rotation':[0,0,0],'wallId':wid,
              'width':round(w_mm*MM,4),'height':dh,
              **{**DOOR_TMPL,'doorType':'sliding' if is_glass else 'hinged',
                 'openingKind':'opening' if h['id'].startswith('OPEN-') else 'door'}}
        add(dn, canonical_id=h['id'], category='glass_door' if is_glass else 'door',
            status='MAPPED', extra={'width_m':round(w_mm*MM,4)})
        node['children'].append(did)
    else:
        widn = nid('window')
        wn = {'object':'node','id':widn,'type':'window','parentId':wid,'visible':True,
              'metadata':{'canonical_id':h['id'],'sill_height_TEMP':True,'head_height_TEMP':True},
              'position':[round(local*MM,4), WIN_SILL+WIN_H/2, 0],'rotation':[0,0,0],'wallId':wid,
              'width':round(w_mm*MM,4),'height':WIN_H,**WIN_TMPL}
        add(wn, canonical_id=h['id'], category='window', status='MAPPED',
            extra={'width_m':round(w_mm*MM,4)})
        node['children'].append(widn)
    nodes[lvl]['children'].append(wid)

# ---- bay windows: glazed front band from canonical 'bay.front' rect ----
for w in M['windows']:
    bay = w.get('bay')
    if not bay or 'front' not in bay: continue
    fr = bay['front']
    horiz = (fr[3]-fr[1]) <= (fr[2]-fr[0])
    if horiz: start, end = [m(fr[0]), mz((fr[1]+fr[3])/2)], [m(fr[2]), mz((fr[1]+fr[3])/2)]
    else: start, end = [m((fr[0]+fr[2])/2), mz(fr[1])], [m((fr[0]+fr[2])/2), mz(fr[3])]
    th_m = m((fr[3]-fr[1]) if horiz else (fr[2]-fr[0]))
    wid = nid('wall')
    node = {'object':'node','id':wid,'type':'wall','parentId':lvl,'visible':True,
            'metadata':{'canonical_id':w['id']+'-BAY-FRONT','representation_mode':'BAY_FRONT_GLAZED',
                        'note':'bay front band synthesized as thin wall + full-width window'},
            'children':[],'thickness':th_m,'height':WALL_H,'start':start,'end':end,
            'frontSide':'unknown','backSide':'unknown'}
    add(node, canonical_id=w['id']+'-BAY-FRONT', category='wall_bay_front',
        status='REPRESENTATION_LIMITATION')
    ax = 0 if horiz else 1
    w_mm = fr[ax+2]-fr[ax]
    widn = nid('window')
    wn = {'object':'node','id':widn,'type':'window','parentId':wid,'visible':True,
          'metadata':{'canonical_id':w['id']+'-BAY-FRONT','sill_height_TEMP':True},
          'position':[round(w_mm/2*MM,4), WIN_SILL+WIN_H/2, 0],'rotation':[0,0,0],'wallId':wid,
          'width':round(w_mm*MM,4),'height':WIN_H,**WIN_TMPL}
    add(wn, canonical_id=w['id']+'-BAY-FRONT', category='window', status='REPRESENTATION_LIMITATION')
    node['children'].append(widn)
    nodes[lvl]['children'].append(wid)

# ---------------- zones (rooms + balconies + wet zones + split-level annotations) ----------------
ZONE_DEFAULTS = {'autoFromWalls':False,'boundaryWallIds':[],'spaceRole':'generic','roomNumber':'',
                 'enclosureStatus':'auto','floorFinish':'','wallFinish':'','ceilingFinish':'',
                 'ceilingHeight':2.7,'occupancy':'','clearDimensionPolicy':'none'}  # ceilingHeight TEMP
def zone_node(name, poly_m, metadata, color='#3b82f6', spaceRole='generic'):
    return {'object':'node','id':nid('zone'),'type':'zone','name':name,'parentId':lvl,'visible':True,
            'metadata':metadata,'polygon':[[m(x),mz(y)] for x,y in poly_m],
            **{**ZONE_DEFAULTS,'color':color,'spaceRole':spaceRole}}
for s in M['spaces']:
    zid = add(zone_node(s['id'], s['poly'],
         {'canonical_id':s['id'],'name':s.get('name',''),'split_level':s.get('level'),
          'elevation_TEMP_mm':350 if s.get('level')=='upper' else 0}),
        canonical_id=s['id'], category='zone_room', room=s['id'])
    nodes[lvl]['children'].append(zid)
for b in M['balconies']:
    zid = add(zone_node(b['id'], b['poly'],
         {'canonical_id':b['id'],'open':b.get('open'),'name':b['id']}, color='#22c55e'),
        canonical_id=b['id'], category='zone_balcony')
    nodes[lvl]['children'].append(zid)
# split-level steps + ramp as annotation zones
st = M['stairs']
for i,(x0,y0,x1,y1,z) in enumerate(st['steps']):
    zid = add(zone_node(f'STEP-{i+1}', [[x0,y0],[x1,y0],[x1,y1],[x0,y1]],
         {'canonical_id':f'STEP-{i+1}','kind':'SPLIT_LEVEL_STEP','riser_mm':z,
          'status':'BLOCKOUT_TEMP_VALUE'}, color='#f59e0b'),
        canonical_id=f'STEP-{i+1}', category='zone_annotation', status='TEMP_GEOMETRY')
    nodes[lvl]['children'].append(zid)
zid = add(zone_node('RAMP-FUTURE', [[M['ramp']['rect'][0],M['ramp']['rect'][1]],[M['ramp']['rect'][2],M['ramp']['rect'][1]],
        [M['ramp']['rect'][2],M['ramp']['rect'][3]],[M['ramp']['rect'][0],M['ramp']['rect'][3]]],
     {'canonical_id':'RAMP-FUTURE','kind':'WHEELCHAIR_RAMP_PLACEHOLDER','status':'BLOCKOUT_TEMP_VALUE'},
     color='#f59e0b'),
    canonical_id='RAMP-FUTURE', category='zone_annotation', status='TEMP_GEOMETRY')
nodes[lvl]['children'].append(zid)

# ---------------- furniture / fixtures ----------------
# catalog: (catalog_id, [cat_w, cat_h, cat_d])  — visual placeholder ONLY
CAT = {
 '三人位':('sofa',[2.5,0.8,1.5]), '双人位':('sofa',[2.5,0.8,1.5]), '贵妃椅':('livingroom-chair',[1.5,0.8,1.5]),
 '茶几':('coffee-table',[2.0,0.4,1.5]), '角几':('bedside-table',[0.5,0.5,0.5]),
 '餐桌':('dining-table',[2.5,0.8,1.0]), '餐椅':('dining-chair',[0.5,1.0,0.5]),
 '餐椅003':('dining-chair',[0.5,1.0,0.5]), '餐椅004':('dining-chair',[0.5,1.0,0.5]),
 '洗衣机+烘干机（叠放）':('washing-machine',[1.0,1.0,1.0]), '3kg洗衣机':('washing-machine',[0.45,0.5,0.45]),
 '冰柜':('freezer',[1.0,2.0,1.0]), '电视柜（或者悬浮电视墙）':('tv-stand',[2.0,0.4,0.5]),
}
DEFAULT_CAT = ('bedside-table',[0.5,0.5,0.5])
ACCEPTED = {'主卫马桶','次主卫马桶','主卧电视柜','双人位'}
REGION = {'湿区'}
UPPER_ZONES = {s['id'] for s in M['spaces'] if s.get('level')=='upper'}

def cat_for(label):
    for k,v in CAT.items():
        if k == label or label.startswith(k): return v
    if '马桶' in label: return ('toilet',[1.0,0.9,1.0])
    if '洗手' in label or '台盆' in label: return ('bathroom-sink',[2.0,1.0,1.5])
    if '湿区' in label: return ('shower-square',[1.0,2.0,1.0])
    if '床' in label and '背' not in label: return ('double-bed',[2.0,0.8,2.5])
    if '书柜' in label: return ('bookshelf',[1.5,2.0,0.4])
    if '衣柜' in label or '柜' in label: return ('closet',[2.0,2.5,1.0])
    if '书桌' in label or '桌' in label or '茶台' in label: return ('table',[1.8,0.75,0.8])
    if '椅' in label or '凳' in label: return ('stool',[0.5,1.0,0.5])
    if '厨' in label: return ('kitchen-counter',[2.0,0.8,1.0])
    if '打印机' in label: return ('computer',[0.5,0.4,0.4])
    if 'nas' in label.lower(): return ('computer',[0.3,0.3,0.3])
    return DEFAULT_CAT

for f in M['furniture']:
    if SKIP_ITEMS: break
    r = f['rect']
    wa, da = (r[2]-r[0])*MM, (r[3]-r[1])*MM
    cx, cz = (r[0]+r[2])/2*MM, (r[1]+r[3])/2*MM
    cid, cdims = cat_for(f['label'])
    reg_h, reg_z, reg_sem = _FDIM.get(f['label'], (None, 0.0, None))
    scale = [round(wa/cdims[0],4), round(reg_h/cdims[1],4) if reg_h else 1.0, round(da/cdims[2],4)]
    y = (0.35 if f.get('zone') in UPPER_ZONES else 0.0) + reg_z
    if f['label'] == '3kg洗衣机':
        y += 0.75  # WALL_MOUNTED candidate
    sem = reg_sem or ('WALL_MOUNTED_COMPACT_WASHER_CANDIDATE' if f['label']=='3kg洗衣机' else \
          'STUDY_WORKSTATION' if f['label']=='茶台' else None)
    status = ('HUMAN_ACCEPTED_AS_DRAWN' if f['label'] in ACCEPTED else
              'REGION_BOUNDARY' if any(k in f['label'] for k in REGION) else
              'USER_MANUAL_CORRECTION' if f['label'] in {'次卧小床1.2','次卧衣柜','床背板','窄书桌'} else 'MAPPED')
    meta = {'fcstd_obj':f['obj'],'label':f['label'],'room_zone':f.get('zone'),
            'actual_project_size_m':[round(wa,4),round(da,4)],
            'catalog_nominal_size_m':cdims,'source':'MASTER_V2',
            'review_status':status, **({'semantics':sem} if sem else {})}
    if MODE == 'blocks':
        # pure blockout: unit-cube GLB scaled to MASTER_V2 footprint;
        # height from furniture_3d_dimension_register (approved) else catalog nominal TEMP.
        iid = nid('item')
        node = {'object':'node','id':iid,'type':'item','parentId':lvl,'visible':True,
                'metadata':{**meta,'blockout':True,'height_TEMP':reg_h is None},
                'position':[round(cx,4),y,round(-cz,4)],'rotation':[0,0,0],
                'scale':[round(wa,4), round(reg_h,4) if reg_h else cdims[1], round(da,4)],'children':[],
                'asset':{'id':'blockout-box','category':'blockout','name':f['label'],'source':'library',
                         'src':'/items/blockout-box/model.glb','thumbnail':'',
                         'dimensions':[1,1,1],'tags':[],'offset':[0,0,0],
                         'rotation':[0,0,0],'scale':[1,1,1]}}
    else:
        iid = nid('item')
        node = {'object':'node','id':iid,'type':'item','parentId':lvl,'visible':True,
                'metadata':meta,
                'position':[round(cx,4),y,round(-cz,4)],'rotation':[0,0,0],'scale':scale,'children':[],
                'asset':{'id':cid,'category':'furniture','name':f['label'],'source':'library',
                         'src':f'/items/{cid}/model.glb','thumbnail':f'/items/{cid}/thumbnail.webp',
                         'dimensions':cdims,'tags':[],'offset':[0,0,0],
                         'rotation':[0,0,0],'scale':[1,1,1]}}
    add(node, canonical_id=f['label'], fcstd=f['obj'], category='furniture_region' if status=='REGION_BOUNDARY' else 'furniture',
        room=f.get('zone'), status=status, extra={'actual_size_m':[round(wa,4),round(da,4)],'catalog':cid})
    nodes[lvl]['children'].append(iid)

# kitchen cabinets — authority: cabinet shop-drawing PDF (KITCHEN_CABINET_3D_REGISTER_V01).
# Generic canonical kitchen_cabinets entries are superseded; emit one node per register record
# with true per-type height + base_z (wall cabinets wall-mounted, fridge 1700, overhead cab).
for kc in _KC3D.values():
    if SKIP_ITEMS: break
    r = kc['rect']; wa, da = (r[2]-r[0])*MM, (r[3]-r[1])*MM
    h_m = kc['height']*MM; z_m = kc['base_z']*MM
    meta = {'canonical_id':kc['cabinet_id'],'room_zone':'R-KITCHEN','cabinet_type':kc['type'],
            'actual_project_size_m':[round(wa,4),round(h_m,4),round(da,4)],
            'source':f"cabinet_plan.pdf p{kc['source_page']}",
            'source_dimension':kc.get('source_dimension',''),'confidence':kc['confidence'],
            'review_status':'PDF_SHOP_DRAWING' if kc['confidence']=='HIGH' else 'PDF_TO_VERIFY'}
    pos = [round((r[0]+r[2])/2*MM,4), round(z_m,4), round(-(r[1]+r[3])/2*MM,4)]
    if MODE == 'blocks':
        iid = nid('item')
        node = {'object':'node','id':iid,'type':'item','parentId':lvl,'visible':True,
                'metadata':{**meta,'blockout':True,'height_TEMP':kc['confidence']!='HIGH'},
                'position':pos,'rotation':[0,0,0],
                'scale':[round(wa,4), round(h_m,4), round(da,4)],'children':[],
                'asset':{'id':'blockout-box','category':'blockout','name':kc['cabinet_id'],'source':'library',
                         'src':'/items/blockout-box/model.glb','thumbnail':'',
                         'dimensions':[1,1,1],'tags':[],'offset':[0,0,0],
                         'rotation':[0,0,0],'scale':[1,1,1]}}
    else:
        iid = nid('item')
        node = {'object':'node','id':iid,'type':'item','parentId':lvl,'visible':True,
                'metadata':meta,
                'position':pos,
                'rotation':[0,0,0],'scale':[round(wa/0.6,4),round(h_m/0.9,4),round(da/0.6,4)],'children':[],
                'asset':{'id':'kitchen-counter','category':'kitchen','name':kc['cabinet_id'],'source':'library',
                         'src':'/items/kitchen-counter/model.glb','thumbnail':'/items/kitchen-counter/thumbnail.webp',
                         'dimensions':[0.6,0.9,0.6],'tags':[],'offset':[0,0,0],
                         'rotation':[0,0,0],'scale':[1,1,1]}}
    add(node, canonical_id=kc['cabinet_id'], category='kitchen_cabinet',
        status='PDF_SHOP_DRAWING' if kc['confidence']=='HIGH' else 'PDF_TO_VERIFY')
    nodes[lvl]['children'].append(iid)

# ---------------- floor slabs (blockout, TEMP thickness) ----------------
if not SKIP_ITEMS or True:
    for s in M['spaces'] + M['balconies']:
        elev = 0.35 if s.get('level') == 'upper' else 0.0
        sid = nid('slab')
        node = {'object':'node','id':sid,'type':'slab','parentId':lvl,'visible':True,
                'metadata':{'canonical_id':s['id'],'blockout':True,'thickness_TEMP':True,
                            'elevation_TEMP':elev>0},
                'children':[],'polygon':[[m(x),mz(y)] for x,y in s['poly']],
                'thickness':0.12,'elevation':elev}
        add(node, canonical_id=s['id'], category='slab_floor', status='TEMP_GEOMETRY')
        nodes[lvl]['children'].append(sid)

graph = {'nodes': nodes, 'rootNodeIds': [site], 'collections': {}, 'materials': {}}
tag = 'arch' if SKIP_ITEMS else OUT_SUFFIX
scene_path = f'{OUTD}/pascal_{tag}_scene.json'
json.dump(graph, open(scene_path,'w'), ensure_ascii=False)
json.dump({'scene_sha': hashlib.sha256(open(scene_path,'rb').read()).hexdigest()[:16],
           'node_count': len(nodes), 'map': idmap},
          open(f'{OUTD}/pascal_{tag}_id_map.json','w'), ensure_ascii=False, indent=1)
print('wrote', scene_path)
print('nodes', len(nodes), '| mapped', len(idmap), '| walls', sum(1 for n in nodes.values() if n['type']=='wall'),
      '| doors', sum(1 for n in nodes.values() if n['type']=='door'),
      '| windows', sum(1 for n in nodes.values() if n['type']=='window'),
      '| zones', sum(1 for n in nodes.values() if n['type']=='zone'),
      '| slabs', sum(1 for n in nodes.values() if n['type']=='slab'),
      '| blocks', sum(1 for n in nodes.values() if n['type']=='block'),
      '| items', sum(1 for n in nodes.values() if n['type']=='item'))
