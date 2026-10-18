#!/usr/bin/env python3
"""A103_CONSTRUCTION_POC_V7: registry驱动 + 施工差集绘制 + 图层颜色/线宽规整.
geometry_v05 仅供几何/身份/锚点; wall_state_registry 决定工程状态.
用法: make_a103_poc_v6.py [geometry.json] [out.dxf] [base.dxf]"""
import json, hashlib, sys, shutil
from pathlib import Path
import ezdxf

CAD = Path(__file__).resolve().parent
ROOT = CAD.parents[3]
GEO_NAME = sys.argv[1] if len(sys.argv) > 1 else 'geometry_v05.json'
OUT = CAD / (sys.argv[2] if len(sys.argv) > 2 else 'A103_CONSTRUCTION_POC_V7.dxf')
BASE = Path(sys.argv[3]) if len(sys.argv) > 3 else CAD / 'A103_平面布置图.dxf'
GEO = json.loads((CAD / 'derived' / GEO_NAME).read_text())
REG = json.loads((CAD/'derived'/'wall_state_registry.json').read_text())
NC = json.loads((CAD/'derived'/'new_construction_v1.json').read_text())
NC_ROW = {r['object']: r for r in NC['rows']}
REG103 = {}   # object -> a103_role (按 part 键)
for _e in REG['entries']: REG103[_e['object']] = _e['a103_role']

def sha256(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()

def preflight():
    """每次生成前对真实文件重算 SHA —— 不信任 JSON 缓存状态"""
    errs = []
    for a in GEO['anchors'] + GEO['managed_entities']:
        ident = a.get('id') or '+'.join(a.get('objects', []))
        f = a.get('source_file'); want = a.get('source_file_sha256') or a.get('source_sha')
        if not f or not want: errs.append(f"{ident}: missing source hash"); continue
        p = Path(f)
        if not p.exists(): errs.append(f"{ident}: source missing {f}"); continue
        if sha256(p) != want:
            errs.append(f"{ident}: source CHANGED after extraction ({f})")
    for did, d in GEO.get('derived_data', {}).items():
        if sha256(d['file']) != d['sha256']:
            errs.append(f'STALE_DERIVED_DATA: {did} file changed')
        par = d.get('parent_sha256')
        if par:
            # 衍生物的父源必须等于当前源 sha
            srcs = [a.get('source_file_sha256') or a.get('source_sha')
                    for a in GEO['anchors'] + GEO['managed_entities']]
            if par not in srcs:
                errs.append(f'STALE_DERIVED_DATA: {did} parent hash {par[:12]} not among live sources')
    for tag, spec in GEO['dims'].items():
        ids = {a['id'] for a in GEO['anchors']}
        if spec['a'] not in ids or spec['b'] not in ids:
            errs.append(f'dim {tag}: missing anchor {spec["a"]}/{spec["b"]}')
    return errs

errs = preflight()
if errs:
    (CAD/'derived'/('qa_block_'+GEO_NAME)).write_text(json.dumps({'status':'BLOCK','errors':errs},indent=1))
    print('BLOCK:', *errs, sep='\n  '); sys.exit(1)

A = {a['id']: (a['x'], a['y']) for a in GEO['anchors']}
if OUT.resolve() == BASE.resolve():
    sys.exit('BLOCK: OUT == BASE, refuse to overwrite source drawing')
shutil.copy(BASE, OUT)
doc = ezdxf.readfile(OUT); msp = doc.modelspace()
doc.appids.new('DEVINSRC'); doc.appids.new('DEVINDIM')

# --- 图层 ---
for name, color in (('A-DIMS-LEGACY', 8), ('A-DIMS', 3)):
    if name not in doc.layers: doc.layers.new(name, dxfattribs={'color': color})
for e in msp:
    if e.dxf.layer == 'A-DIMS' and e.dxftype() in ('LINE', 'TEXT', 'MTEXT', 'LWPOLYLINE'):
        e.dxf.layer = 'A-DIMS-LEGACY'
for _ln,_c in (('A-DESIGN',5),('A-DIMS',3),('A-FIXT',8),('A-REVIEW',30),
               ('A-CONFLICT',6),('A-WALL',7)):
    if _ln in doc.layers: doc.layers.get(_ln).dxf.color = _c
for _ln,_w in (('A-WALL',50),('A-DESIGN',30),('A-REVIEW',25),('A-CONFLICT',40),
               ('A-STRUCT-UNDERLAY',13),('A-FURN',13),('A-FIXT',18),('A-DIMS',18)):
    if _ln in doc.layers:
        try: doc.layers.get(_ln).dxf.lineweight = _w
        except Exception: pass
doc.layers.get('A-DIMS-LEGACY').dxf.flags = 1
for lname in ('A-UNCERTAIN', 'A-SOURCE-REF', 'A-ROOM'):
    if lname in doc.layers: doc.layers.get(lname).dxf.flags = 1
doc.layers.get('A-DIMS').dxf.flags = 0

def ebbox(e):
    if e.dxftype() == 'LWPOLYLINE':
        pts = list(e.get_points('xy'))
        xs = [p[0] for p in pts]; ys = [p[1] for p in pts]
        return min(xs), min(ys), max(xs), max(ys)
    return None

def overlap(b1, b2):
    ix = max(0, min(b1[2], b2[2]) - max(b1[0], b2[0]))
    iy = max(0, min(b1[3], b2[3]) - max(b1[1], b2[1]))
    a1 = (b1[2]-b1[0]) * (b1[3]-b1[1]); a2 = (b2[2]-b2[0]) * (b2[3]-b2[1])
    inter = ix * iy
    return inter / max(min(a1, a2), 1)

# --- 管理实体: XDATA 绑定 + 按源轮廓重建 ---
candidates = {}
for e in msp:
    if e.dxftype() == 'LWPOLYLINE' and e.dxf.layer in ('A-WALL', 'A-DESIGN'):
        b = ebbox(e)
        if b: candidates.setdefault(e.dxf.layer, []).append((e, b))
managed_report = {'adopted': 0, 'created': 0, 'unmatched_source': []}
CONFLICT_OBJS=set()
for c in GEO.get('conflicts',[]):
    CONFLICT_OBJS.add(c['a']); CONFLICT_OBJS.add(c['b'])
if 'A-CONFLICT' not in doc.layers:
    doc.layers.new('A-CONFLICT', dxfattribs={'color':6})  # 品红: 冲突候选, 可见待裁
DEMOL = 'A-DEMO'
if DEMOL not in doc.layers:
    doc.layers.new(DEMOL, dxfattribs={'color': 1})
doc.layers.get(DEMOL).dxf.flags = 1          # 拆除段冻结记录: A103 只画装修后构件
if 'A-REVIEW' not in doc.layers:
    doc.layers.new('A-REVIEW', dxfattribs={'color': 30})
if 'A-DUP' not in doc.layers:
    doc.layers.new('A-DUP', dxfattribs={'color': 8})
doc.layers.get('A-DUP').dxf.flags = 1     # 重画保留墙的模型副本: 冻结避免重复线
if 'A-STRUCT-UNDERLAY' not in doc.layers:
    doc.layers.new('A-STRUCT-UNDERLAY', dxfattribs={'color': 8})
for spec in GEO['managed_entities']:
    names = spec['objects']
    primary = names[0]
    if not spec.get('parts') and not spec.get('demolished_parts'):
        managed_report['unmatched_source'].append(primary); continue
    # --- 每个 part 一个实体 (MultiPolygon 保留, 不再坍缩) ---
    conflict = primary in CONFLICT_OBJS and spec['design_status'] != 'EXISTING_RETAINED'
    bound_any = False
    for pi, part in enumerate(spec['parts']):
        draw_layer = spec['layer']
        k = primary if len(spec['parts'])==1 else f'{primary}#p{pi}'
        r = REG103.get(k)
        if r in ('SUPPRESS','SUPPRESS_HOLD'): draw_layer = 'A-DEMO'
        elif r == 'SUPPRESS_DUPLICATE': draw_layer = 'A-DUP'
        elif r == 'DRAW_REVIEW_LAYER': draw_layer = 'A-REVIEW'
        elif r in ('DRAW_NEW','DRAW_NEW_PART'):
            draw_layer = 'A-REVIEW' if any(
                e['object']==k and e.get('overlap_class') for e in REG['entries']) \
                else 'A-DESIGN'
        if conflict: draw_layer = 'A-CONFLICT'
        pts = [(float(x), float(y)) for x, y in part['exterior']]
        pbb = (min(p[0] for p in pts), min(p[1] for p in pts),
               max(p[0] for p in pts), max(p[1] for p in pts))
        target = None
        # 1) XDATA 绑定: 对象组名 + part 序号
        xkey = f'{primary}#p{pi}'
        for e, b in candidates.get(spec['layer'], []):
            try:
                xd = e.get_xdata('DEVINSRC')
                if xd and xd[0][1] == xkey: target = e; break
            except ezdxf.DXFValueError: pass
        # 2) bbox 重叠认领 (仅 part0 允许认领养旧底图实体)
        if target is None and pi == 0:
            best, match = 0, None
            for cand in candidates.get(spec['layer'], []):
                ov = overlap(pbb, cand[1])
                if ov > best: best, match = ov, cand
            if best > 0.5:
                target = match[0]
                candidates[spec['layer']].remove(match)
        if target is not None:
            target.set_points(pts, format='xy'); target.closed = True
            if target.dxf.layer != draw_layer: target.dxf.layer = draw_layer
            managed_report['adopted'] += 1
        else:
            target = msp.add_lwpolyline(pts, close=True, dxfattribs={'layer': draw_layer})
            managed_report['created'] += 1
        target.set_xdata('DEVINSRC', [(1000, xkey)] + [(1000, n) for n in names]
                         + [(1000, spec['design_status'])]
                         + ([(1000, f'cut:{spec["cut_height"]}')] if spec.get('cut_height') else []))
        for hi, hole in enumerate(part.get('holes', [])):
            he = msp.add_lwpolyline([(float(x), float(y)) for x, y in hole], close=True,
                                    dxfattribs={'layer': draw_layer})
            he.set_xdata('DEVINSRC', [(1000, f'{xkey}h{hi}'), (1000, spec['design_status'])])
        bound_any = True
        # DRAW_NEW_PART: 仅重画NC差集新段(完整轮廓已被上面画了, 改为新建层差集段)
        if r == 'DRAW_NEW_PART' and draw_layer in ('A-DESIGN','A-REVIEW') and k in NC_ROW:
            target.dxf.layer = 'A-STRUCT-UNDERLAY'
            for npts in NC_ROW[k]['new_geoms']:
                ne = msp.add_lwpolyline([(float(x),float(y)) for x,y in npts],
                    close=True, dxfattribs={'layer':draw_layer})
                ne.set_xdata('DEVINSRC',[(1000,k+'#NEWSEG'),(1000,'SPLIT_PARTIAL_NEW')])
    # --- 拆除段实体: A-DEMO 冻结登记 ---
    for dp in spec.get('demolished_parts', []):
        e = msp.add_lwpolyline([(float(x), float(y)) for x, y in dp], close=True,
                               dxfattribs={'layer': DEMOL})
        e.set_xdata('DEVINSRC', [(1000, f'{primary}#DEMOLISHED'), (1000, 'EXISTING_DEMOLISHED')])
        managed_report['created'] += 1

# --- 未绑定可见墙线处置: 全部被管理实体覆盖>50% → 删除(已替代); 否则→A-UNCERTAIN ---
def ent_bbox_pts(e):
    pts=[(float(p[0]),float(p[1])) for p in e.get_points('xy')]
    return pts
from shapely.geometry import Polygon as _P
bound_polys=[]
for e in msp:
    if e.dxftype()=='LWPOLYLINE' and e.dxf.layer in ('A-WALL','A-DESIGN'):
        try:
            if e.get_xdata('DEVINSRC'):
                bound_polys.append(_P(ent_bbox_pts(e)))
        except ezdxf.DXFValueError: pass
legacy_ledger=[]
for lay in ('A-WALL','A-DESIGN'):
    for e,b in candidates.get(lay,[]):
        try:
            if e.get_xdata('DEVINSRC'): continue
        except ezdxf.DXFValueError: pass
        ep=_P(ent_bbox_pts(e))
        cover=max((bp.intersection(ep).area/max(ep.area,1) for bp in bound_polys if bp.intersects(ep)),default=0)
        residual=max((ep.difference(bp).area for bp in bound_polys if bp.intersects(ep)),default=ep.area)
        info={'handle':e.dxf.handle,'bbox':[round(v) for v in ep.bounds],
              'coverage':round(cover,3),'residual_mm2':round(residual)}
        if cover>0.98 and residual<5000:
            info['disposition']='DELETED_superseded_equivalent'; e.destroy()
        else:
            e.dxf.layer='A-UNCERTAIN'
            e.set_xdata('DEVINSRC',[(1000,'LEGACY_UNBOUND'),(1000,'UNVERIFIED')])
            info['disposition']='MOVED_to_A-UNCERTAIN_residual_kept'
        legacy_ledger.append(info)
managed_report['legacy_unbound']=legacy_ledger

# --- 原生标注 (XDATA 标记 dim→锚点对) ---
DS = 'STD-ARCH'
if DS not in doc.dimstyles:
    doc.dimstyles.new(DS, dxfattribs={'dimtxsty': 'HZTXT', 'dimtxt': 180, 'dimasz': 140,
                                      'dimexo': 300, 'dimexe': 200, 'dimdec': 0, 'dimtad': 1})
LAY = {'south_total': -1600, 'kitchen_face': -1000, 'master_clear': -1600,
       'mother_clear': -1000, 'living_window': 14200, 'balcony_north': 14200,
       'west_total': 700, 'stair_depth': 5050, 'bath2_depth': 8700,
       'kitchen_open': 5450, 'stair_width': 4300, 'bath2_width': 4300,
       'bath2_envelope_w': 4300, 'bath2_net_w': 4800}
for tag, spec in GEO['dims'].items():
    p1, p2 = A[spec['a']], A[spec['b']]
    if spec['axis'] == 'x':
        off = LAY.get(tag, min(p1[1], p2[1]) - 800); base, ang = ((p1[0]+p2[0])/2, off), 0
    else:
        off = LAY.get(tag, min(p1[0], p2[0]) - 800); base, ang = (off, (p1[1]+p2[1])/2), 90
    val = abs(p2[0]-p1[0]) if spec['axis']=='x' else abs(p2[1]-p1[1])
    d = msp.add_linear_dim(base=base, p1=p1, p2=p2, angle=ang, dimstyle=DS,
                           dxfattribs={'layer': 'A-DIMS'})
    ent = d.dimension
    d.render(); d.commit()
    ent.set_xdata('DEVINDIM', [(1000, tag),(1000, spec['a']),(1000, spec['b']),
                               (1000, spec['axis']),(1040, round(val,1))])


# --- 补充施工定位标注 (dims_extra, 坐标直算) ---
import json as _j
EXTRA_DIMS = _j.loads((CAD/'derived'/'dims_extra.json').read_text())['dims']
for _d in EXTRA_DIMS:
    p1,p2 = tuple(_d['p1']),tuple(_d['p2'])
    if _d['axis']=='x':
        base,ang=((p1[0]+p2[0])/2,_d['lay']),0
    else:
        base,ang=(_d['lay'],(p1[1]+p2[1])/2),90
    _dd=msp.add_linear_dim(base=base,p1=p1,p2=p2,angle=ang,dimstyle=DS,
                           dxfattribs={'layer':'A-DIMS'})
    _dd.render(); _dd.commit()
    _dd.dimension.set_xdata('DEVINDIM',[(1000,_d['tag']),
        (1000,f"geo:{p1[0]},{p1[1]}"),(1000,f"geo:{p2[0]},{p2[1]}"),
        (1000,_d['axis']),(1040,round(_d['value'],1))])

# --- 门/窗 INSERT (真实洞口, XDATA handle) ---
def mk_door():
    if 'SYM-DOOR-LEAF' in [b.name for b in doc.blocks]: doc.blocks.delete('SYM-DOOR-LEAF')
    b = doc.blocks.new('SYM-DOOR-LEAF')
    b.add_line((0, 0), (0, 1000), dxfattribs={'layer': 'A-DOOR'})
    b.add_arc((0, 0), 1000, 0, 90, dxfattribs={'layer': 'A-DOOR'})
    b.add_attdef('SRC_ID', insert=(0, -200), height=150)
mk_door()
for op in GEO['door_openings']:
    x0, y0, x1, y1 = op['rect']; L = op['opening_len']
    pos, rot = ((x0, y0), -90) if op['orient'] == 'V' else ((x0, y1), 0)
    ins = msp.add_blockref('SYM-DOOR-LEAF', pos,
        dxfattribs={'layer': 'A-DOOR', 'xscale': L / 1000, 'rotation': rot})
    ins.add_attrib('SRC_ID', f"dxf_handle:{op['handle']}|{op['design_status']}|swing:{op['swing']}",
                   dxfattribs={'invisible': True})
    ins.set_xdata('DEVINSRC', [(1000, f"dxf:{op['handle']}")])
if 'SYM-WIN-SPAN' in [b.name for b in doc.blocks]: doc.blocks.delete('SYM-WIN-SPAN')
wb = doc.blocks.new('SYM-WIN-SPAN')
for yy in (-80, 0, 80): wb.add_line((0, yy), (1000, yy), dxfattribs={'layer': 'A-WINDOW'})
wb.add_attdef('SRC_ID', insert=(0, -300), height=150)
wl = abs(A['LWIN-E'][0] - A['LWIN-W'][0])
ins = msp.add_blockref('SYM-WIN-SPAN', (A['LWIN-W'][0], 13500),
                       dxfattribs={'layer': 'A-WINDOW', 'xscale': wl / 1000})
ins.add_attrib('SRC_ID', 'fcstd:W_BAY_F', dxfattribs={'invisible': True})
ins.set_xdata('DEVINSRC', [(1000, 'W_BAY_F')])

# --- 纸空间 A1 图框 (Layout1) ---
lay = doc.layout('Layout1') if 'Layout1' in doc.layouts else doc.layouts.new('Layout1')
for e in list(lay):
    if e.dxftype() in ('LWPOLYLINE', 'TEXT', 'MTEXT') : e.destroy()
for _e in list(lay):
    if _e.dxftype()=='VIEWPORT': _e.destroy()
lay.add_lwpolyline([(0,0),(841,0),(841,594),(0,594)], close=True, dxfattribs={'layer': 'A-FRAME' if 'A-FRAME' in doc.layers else '0'})
lay.add_lwpolyline([(560,20),(821,20),(821,80),(560,80)], close=True)
tb = lay.add_text('V15 平面布置图 A103 — POC V7 | 1:50 | A1 | mm', height=9)
tb.dxf.insert = (566, 55)
tb2 = lay.add_text('源: wall_state_registry.json + geometry_v05.json | registry驱动状态', height=6)
tb2.dxf.insert = (566, 35)
vp = lay.add_viewport(center=(420,320), size=(780,520),
                      view_center_point=((0+16500)/2,(-200+14200)/2),
                      view_height=520*50)
vp.dxf.status = 1

doc.saveas(OUT)
import json as _j
(CAD/'derived'/'adjudication_ledger_v05.json').write_text(_j.dumps(
    {'legacy_unbound':legacy_ledger,
     'merge_review':[{'objects':s['objects'],'reviews':s['merge_review']}
                     for s in GEO['managed_entities'] if s.get('merge_review')],
     'anomalies':GEO.get('anomalies',[]),
     'conflicts':GEO.get('conflicts',[]),
     'managed_report':managed_report}, ensure_ascii=False, indent=1))
print('generated', OUT.name, '| entities:',
      managed_report['adopted'], '+', managed_report['created'],
      '| dims:', len(GEO['dims']), '| doors:', len(GEO['door_openings']))
