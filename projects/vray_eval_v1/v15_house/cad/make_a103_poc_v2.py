#!/usr/bin/env python3
"""A103_CONSTRUCTION_POC_V2: 对象级溯源原生标注 (相对路径, 生成前 hash 校验)"""
import json, hashlib, shutil, sys
from pathlib import Path
import ezdxf

CAD = Path(__file__).resolve().parent
ROOT = CAD.parents[3]
GEO = json.loads((CAD / 'derived' / (sys.argv[1] if len(sys.argv) > 1 else 'geometry_v02.json')).read_text())
OUT = CAD / (sys.argv[2] if len(sys.argv) > 2 else 'A103_CONSTRUCTION_POC_V2.dxf')

def sha256(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()

def preflight():
    """生成前校验: 所有引用源 FRESH, 锚点全部有对象级 source"""
    errs = []
    for iid, s in GEO['sources'].items():
        if s['state'] != 'FRESH':
            errs.append(f'STALE source {iid}: {s["path"]}')
    for a in GEO['anchors']:
        if not a.get('source_object_id') or a.get('source_file_sha256') == 'MISSING':
            errs.append(f'anchor {a["id"]} lacks object source')
        if a.get('source_file_sha256') != GEO['sources'].get('baseline_fcstd', {}).get('current') \
           and a['source_file'].endswith('.FCStd') and a['source_file_sha256'] != sha256(a['source_file']):
            errs.append(f'anchor {a["id"]} fcstd hash drift')
    return errs

errs = preflight()
if errs:
    (CAD / 'qa_report_v02.json').write_text(json.dumps({'status': 'BLOCK', 'errors': errs}, indent=1))
    sys.exit('BLOCK: ' + '; '.join(errs))

A = {a['id']: (a['x'], a['y']) for a in GEO['anchors']}
shutil.copy(CAD / 'A103_平面布置图.dxf', OUT)
doc = ezdxf.readfile(OUT); msp = doc.modelspace()

# --- 图层治理: 旧标注→A-DIMS-LEGACY(冻结), 原生→A-DIMS ---
for name, color in (('A-DIMS-LEGACY', 8), ('A-DIMS', 3), ('A-UNVERIFIED-REG', 1)):
    if name not in doc.layers: doc.layers.new(name, dxfattribs={'color': color})
for e in msp:
    if e.dxf.layer == 'A-DIMS' and e.dxftype() in ('LINE', 'TEXT', 'MTEXT', 'LWPOLYLINE'):
        e.dxf.layer = 'A-DIMS-LEGACY'
doc.layers.get('A-DIMS-LEGACY').dxf.flags = 1   # frozen
for lname in ('A-UNCERTAIN', 'A-SOURCE-REF', 'A-ROOM'):
    if lname in doc.layers: doc.layers.get(lname).dxf.flags = 1
doc.layers.get('A-DIMS').dxf.flags = 0

DS = 'STD-ARCH'
if DS not in doc.dimstyles:
    doc.dimstyles.new(DS, dxfattribs={'dimtxsty': 'HZTXT', 'dimtxt': 180, 'dimasz': 140,
                                      'dimexo': 300, 'dimexe': 200, 'dimdec': 0, 'dimtad': 1})
# --- 原生标注 (全部进 A-DIMS) ---
def dim(tag, a1, a2, axis, off):
    p1, p2 = A[a1], A[a2]
    if axis == 'x':
        base = ((p1[0] + p2[0]) / 2, off); ang = 0
    else:
        base = (off, (p1[1] + p2[1]) / 2); ang = 90
    d = msp.add_linear_dim(base=base, p1=p1, p2=p2, angle=ang, dimstyle=DS,
                           dxfattribs={'layer': 'A-DIMS'})
    d.render()
    d.commit()
    return {'tag': tag, 'handle': d.dimension.dxf.handle, 'expected': abs(p2[0]-p1[0]) if axis=='x' else abs(p2[1]-p1[1])}
LAY = {'south_total': -1600, 'kitchen_face': -1000, 'master_clear': -1600,
       'mother_clear': -1000, 'living_window': 14200, 'balcony_north': 14200,
       'west_total': 700, 'stair_depth': 5050, 'bath2_depth': 8700,
       'kitchen_open': 5450, 'stair_width': 4300, 'bath2_width': 4300}
DIMMAP = []
for tag, spec in GEO['dims'].items():
    if spec['axis'] == 'x':
        off = LAY.get(tag, min(A[spec['a']][1], A[spec['b']][1]) - 800)
    else:
        off = LAY.get(tag, min(A[spec['a']][0], A[spec['b']][0]) - 800)
    DIMMAP.append(dim(tag, spec['a'], spec['b'], spec['axis'], off))
(CAD / 'derived' / ('dimmap_' + OUT.stem + '.json')).write_text(json.dumps(DIMMAP, indent=1))

# --- 门窗符号 (真实洞口尺寸参数化) ---
def mk_door():
    if 'SYM-DOOR-LEAF' in [b.name for b in doc.blocks]: doc.blocks.delete('SYM-DOOR-LEAF')
    b = doc.blocks.new('SYM-DOOR-LEAF')
    b.add_line((0, 0), (0, 1000), dxfattribs={'layer': 'A-DOOR'})
    b.add_arc((0, 0), 1000, 0, 90, dxfattribs={'layer': 'A-DOOR'})
    b.add_attdef('SRC_ID', insert=(0, -200), height=150)
mk_door()
for op in GEO['door_openings']:
    x0, y0, x1, y1 = op['rect']; L = op['opening_len']
    if op['orient'] == 'V':
        ins = msp.add_blockref('SYM-DOOR-LEAF', (x0, y0),
                               dxfattribs={'layer': 'A-DOOR', 'xscale': L / 1000, 'rotation': -90})
    else:
        ins = msp.add_blockref('SYM-DOOR-LEAF', (x0, y1),
                               dxfattribs={'layer': 'A-DOOR', 'xscale': L / 1000, 'rotation': 0})
    ins.add_attrib('SRC_ID', f"dxf_handle:{op['handle']}", dxfattribs={'invisible': True})
# 客厅北飘窗: 参数化三线窗
if 'SYM-WIN-SPAN' in [b.name for b in doc.blocks]: doc.blocks.delete('SYM-WIN-SPAN')
wb = doc.blocks.new('SYM-WIN-SPAN')
for yy in (-80, 0, 80): wb.add_line((0, yy), (1000, yy), dxfattribs={'layer': 'A-WINDOW'})
wb.add_attdef('SRC_ID', insert=(0, -300), height=150)
wl = abs(A['LWIN-E'][0] - A['LWIN-W'][0])
ins = msp.add_blockref('SYM-WIN-SPAN', (A['LWIN-W'][0], 13500),
                       dxfattribs={'layer': 'A-WINDOW', 'xscale': wl / 1000})
ins.add_attrib('SRC_ID', 'fcstd:W_BAY_F', dxfattribs={'invisible': True})
doc.saveas(OUT)
print('generated', OUT.name, '| dims:', len(GEO['dims']), '| doors:', len(GEO['door_openings']))
