#!/usr/bin/env python3
"""A103_CONSTRUCTION_POC_V3: 几何+标注同源重建 (live SHA 预检 + XDATA 溯源绑定)
用法: make_a103_poc_v3.py [geometry.json] [out.dxf] [base.dxf]"""
import json, hashlib, sys
from pathlib import Path
import ezdxf

CAD = Path(__file__).resolve().parent
ROOT = CAD.parents[3]
GEO_NAME = sys.argv[1] if len(sys.argv) > 1 else 'geometry_v03.json'
OUT = CAD / (sys.argv[2] if len(sys.argv) > 2 else 'A103_CONSTRUCTION_POC_V3.dxf')
BASE = Path(sys.argv[3]) if len(sys.argv) > 3 else CAD / 'A103_平面布置图.dxf'
GEO = json.loads((CAD / 'derived' / GEO_NAME).read_text())

def sha256(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()

def preflight():
    """每次生成前对真实文件重算 SHA —— 不信任 JSON 缓存状态"""
    errs = []
    for a in GEO['anchors'] + GEO['managed_entities']:
        f = a['source_file'] if 'source_file' in a else None
        want = a.get('source_file_sha256') or a.get('source_sha')
        if not f or not want: errs.append(f"{a.get('id') or a.get('object')}: missing source hash"); continue
        p = Path(f)
        if not p.exists(): errs.append(f"{a.get('id') or a.get('object')}: source missing {f}"); continue
        if sha256(p) != want:
            errs.append(f"{a.get('id') or a.get('object')}: source CHANGED after extraction ({f})")
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
    (CAD / 'qa_report_v03.json').write_text(json.dumps({'status': 'BLOCK', 'errors': errs}, indent=1))
    print('BLOCK:', *errs, sep='\n  '); sys.exit(1)

A = {a['id']: (a['x'], a['y']) for a in GEO['anchors']}
shutil_ok = OUT != BASE
import shutil; shutil.copy(BASE, OUT)
doc = ezdxf.readfile(OUT); msp = doc.modelspace()
doc.appids.new('DEVINSRC'); doc.appids.new('DEVINDIM')

# --- 图层 ---
for name, color in (('A-DIMS-LEGACY', 8), ('A-DIMS', 3)):
    if name not in doc.layers: doc.layers.new(name, dxfattribs={'color': color})
for e in msp:
    if e.dxf.layer == 'A-DIMS' and e.dxftype() in ('LINE', 'TEXT', 'MTEXT', 'LWPOLYLINE'):
        e.dxf.layer = 'A-DIMS-LEGACY'
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
for spec in GEO['managed_entities']:
    if not spec.get('outline'): managed_report['unmatched_source'].append(spec['object']); continue
    target = None
    # 1) 已有 XDATA 绑定
    for e, b in candidates.get(spec['layer'], []):
        try:
            xd = e.get_xdata('DEVINSRC')
            if xd and xd[0][1] == spec['object']: target = e; break
        except ezdxf.DXFValueError: pass
    # 2) 按 bbox 重叠认领
    if target is None:
        best, match = 0, None
        for cand in candidates.get(spec['layer'], []):
            ov = overlap(spec['bbox'], cand[1])
            if ov > best: best, match = ov, cand
        if best > 0.5:
            target = match[0]
            candidates[spec['layer']].remove(match)   # 一实体一对象, 不再被抢
    pts = [(float(x), float(y)) for x, y in spec['outline']]
    if target is not None:
        target.set_points(pts, format='xy'); target.closed = True
        managed_report['adopted'] += 1
        try:
            prior = [v for c, v in target.get_xdata('DEVINSRC') if c == 1000]
        except ezdxf.DXFValueError:
            prior = []
        names = prior if prior else []
    else:
        target = msp.add_lwpolyline(pts, close=True, dxfattribs={'layer': spec['layer']})
        managed_report['created'] += 1   # 新建实体已绑定, 不入候选池
    existing = []
    try: existing = [v for c, v in target.get_xdata('DEVINSRC') if c == 1000]
    except ezdxf.DXFValueError: pass
    xnames = existing + [spec['object']] if spec['object'] not in existing else existing
    target.set_xdata('DEVINSRC', [(1000, n) for n in xnames] + [(1000, spec['design_status'])])

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
    d = msp.add_linear_dim(base=base, p1=p1, p2=p2, angle=ang, dimstyle=DS,
                           dxfattribs={'layer': 'A-DIMS'})
    ent = d.dimension
    d.render(); d.commit()
    ent.set_xdata('DEVINDIM', [(1000, tag)])

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
lay.add_lwpolyline([(0,0),(841,0),(841,594),(0,594)], close=True, dxfattribs={'layer': 'A-FRAME' if 'A-FRAME' in doc.layers else '0'})
lay.add_lwpolyline([(560,20),(821,20),(821,80),(560,80)], close=True)
tb = lay.add_text('V15 平面布置图 A103 — POC V3 | 1:50 | A1 | mm', height=9)
tb.dxf.insert = (566, 55)
tb2 = lay.add_text('源: geometry_v03.json (对象级溯源) | qa_report_v03.json', height=6)
tb2.dxf.insert = (566, 35)

doc.saveas(OUT)
print('generated', OUT.name, '| managed adopted+created:',
      managed_report['adopted'], '+', managed_report['created'],
      '| dims:', len(GEO['dims']), '| doors:', len(GEO['door_openings']))
