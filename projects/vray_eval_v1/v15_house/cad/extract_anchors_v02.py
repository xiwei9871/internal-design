#!/usr/bin/env python3
"""geometry_v02 锚点提取: FCStd对象/DXF handle/Blender对象 三级溯源"""
import json, hashlib, subprocess, sys
from pathlib import Path
import ezdxf

CAD = Path(__file__).resolve().parent
ROOT = CAD.parents[3]                       # interior_design repo root
MANIFEST = CAD / 'CONSTRUCTION_INPUT_MANIFEST.json'
FCMD = '/Applications/FreeCAD.app/Contents/Resources/bin/freecadcmd'

def sha256(p: Path) -> str:
    h = hashlib.sha256(); h.update(p.read_bytes()); return h.hexdigest()

def load_manifest():
    m = json.loads(MANIFEST.read_text())
    return {i['id']: i for i in m['inputs']}

def src_status(items):
    """重算每个输入源 SHA256, 与 manifest 比对"""
    st = {}
    for iid, it in items.items():
        p = ROOT / it['path']
        cur = sha256(p) if p.exists() else 'MISSING'
        st[iid] = {'path': it['path'], 'recorded': it['sha256'], 'current': cur,
                   'state': 'FRESH' if cur == it['sha256'] else 'STALE_OR_MISSING'}
    return st

def dump_fc_objects(fcstd_path: Path, out_json: Path):
    """freecadcmd 子进程导出对象 bbox+顶点"""
    code = f'''
import FreeCAD as App, json
doc = App.openDocument({str(fcstd_path)!r})
out = []
for o in doc.Objects:
    if hasattr(o, 'Shape') and o.Shape.Edges:
        bb = o.Shape.BoundBox
        verts = [[round(v.Point.x,2), round(v.Point.y,2)] for v in o.Shape.Vertexes]
        out.append({{'name': o.Name, 'label': o.Label,
                    'bbox': [round(bb.XMin,2), round(bb.YMin,2), round(bb.XMax,2), round(bb.YMax,2)],
                    'verts': verts}})
json.dump(out, open({str(out_json)!r}, 'w'), ensure_ascii=False)
'''
    r = subprocess.run([FCMD, '-c', code], capture_output=True, text=True, timeout=300)
    if not out_json.exists():
        print(r.stdout[-2000:], r.stderr[-2000:]); sys.exit('freecad dump failed')

ANCHORS = []  # 收集器
def A(aid, x, y, srcfile, src_id, sub, role, ds, vs, ev):
    ANCHORS.append({'id': aid, 'x': round(x, 2), 'y': round(y, 2),
        'source_file': srcfile['path'], 'source_file_sha256': srcfile['current'],
        'source_revision': srcfile['current'][:12], 'source_object_id': src_id,
        'subelement_reference': sub, 'geometry_role': role,
        'design_status': ds, 'verification_status': vs, 'evidence': ev})

def fc_anchor(aid, objs, name, pick, role, rev):
    """在 FC 对象顶点集中取极值顶点作锚点"""
    o = next(o for o in objs if o['name'] == name)
    idx, (x, y) = max(enumerate(o['verts']), key=pick) if pick.__name__.startswith('max') else \
                  min(enumerate(o['verts']), key=pick)
    A(aid, x, y, rev, name, f'Shape.Vertexes[{idx}]', role, 'EXISTING', 'VERIFIED_OBJECT',
      f'fcstd:{name} vertex extremum')

def extract(fcstd_override=None, out_name='geometry_v02.json'):
    items = load_manifest(); st = src_status(items)
    fc_path = ROOT / items['baseline_fcstd']['path'] if fcstd_override is None else Path(fcstd_override)
    rev_fc = {'path': str(fc_path), 'current': sha256(fc_path)}
    raw = CAD / 'derived' / 'fc_objects_raw.json'
    dump_fc_objects(fc_path, raw)
    objs = json.loads(raw.read_text())
    byname = {o['name']: o for o in objs}

    def ext(name, fn):
        vs = byname[name]['verts']; return fn(vs)

    # --- S1 FreeCAD 既有结构锚点 ---
    fc_specs = [
        ('S-SPAN-W', 'W_BALC_S', lambda vs: min(vs, key=lambda v: v[0])[0], 'xmin'),
        ('S-SPAN-E', 'W_EXT_E1', lambda vs: max(vs, key=lambda v: v[0])[0], 'xmax'),
        ('W-SPAN-S', 'W_BALC_S', lambda vs: min(vs, key=lambda v: v[1])[1], 'ymin'),
        ('W-SPAN-N', 'W_EXT_N_BAL', lambda vs: max(vs, key=lambda v: v[1])[1], 'ymax'),
        ('KIT-W-FACE', 'W_INT_X5800', lambda vs: min(vs, key=lambda v: v[0])[0], 'xmin'),
        ('KIT-E-FACE', 'W_INT_X7900_L', lambda vs: min(vs, key=lambda v: v[0])[0], 'xmin'),
        ('MBED-W-FACE', 'W_INT_X7900_L', lambda vs: max(vs, key=lambda v: v[0])[0], 'xmax'),
        ('MBED-E-FACE', 'W_INT_X11500', lambda vs: min(vs, key=lambda v: v[0])[0], 'xmin'),
        ('MOT-W-FACE', 'W_INT_X11500', lambda vs: max(vs, key=lambda v: v[0])[0], 'xmax'),
        ('MOT-E-FACE', 'W_EXT_E1', lambda vs: min(vs, key=lambda v: v[0])[0], 'xmin'),
        ('LWIN-W', 'W_BAY_F', lambda vs: min(vs, key=lambda v: v[0])[0], 'xmin'),
        ('LWIN-E', 'W_BAY_F', lambda vs: max(vs, key=lambda v: v[0])[0], 'xmax'),
        ('BALC-N-W', 'W_EXT_N_BAL', lambda vs: min(vs, key=lambda v: v[0])[0], 'xmin'),
        ('BALC-N-E', 'W_EXT_N_BAL', lambda vs: max(vs, key=lambda v: v[0])[0], 'xmax'),
        ('COR-S-W', 'W_INT_Y4500_a', lambda vs: min(vs, key=lambda v: v[0])[0], 'xmin'),
        ('COR-S-E', 'W_INT_Y4500_b', lambda vs: max(vs, key=lambda v: v[0])[0], 'xmax'),
    ]
    for aid, name, fn, tag in fc_specs:
        vs = byname[name]['verts']
        tgt = fn(vs)
        idx = next(i for i, v in enumerate(vs) if abs((v[0] if tag[0] == 'x' else v[1]) - tgt) < 0.01)
        v = vs[idx]
        A(aid, v[0], v[1], rev_fc, name, f'Shape.Vertexes[{idx}]', 'wall_face/envelope',
          'EXISTING', 'VERIFIED_OBJECT', f'fcstd:{name}.{tag}')

    # --- S3 Blender 设计对象锚点 ---
    bl = items['v15_work_blend'] if 'v15_work_blend' in items else {'path': 'projects/vray_eval_v1/v15_house/V15_WORK.blend', 'sha256': ''}
    rev_bl = {'path': bl['path'], 'current': sha256(ROOT / bl['path']) if (ROOT / bl['path']).exists() else 'MISSING'}
    mw = json.loads((CAD / 'model_walls3.json').read_text())
    st_ = json.loads((CAD / 'stair_footprints.json').read_text())
    walls = {w['n']: w['b'] for w in mw['thin']}
    def bl_anchor(aid, obj, b, xs, ys, role):
        cx = {'W': b[0], 'E': b[2]}[xs]; cy = {'S': b[1], 'N': b[3]}[ys]
        A(aid, cx, cy, rev_bl, obj, f'bbox.corner({xs}{ys})', role, 'PROPOSED',
          'VERIFIED_OBJECT', f'blender:{obj} {xs}{ys}')
    # 波浪台阶包络: 每极值由取得它的对象承载
    names = [k for k in st_ if k.startswith(('WAVE_STEP','STEP_')) and 'RAMP' not in k]
    env = {}
    for n in names:
        for i, (x, y) in enumerate(st_[n]):
            for tag, v, key in (('W', x, 0), ('E', x, 2), ('S', y, 1), ('N', y, 3)):
                cur = env.get(tag)
                if cur is None or (key == 0 and v < cur[0]) or (key == 2 and v > cur[0]) or (key == 1 and v < cur[0]) or (key == 3 and v > cur[0]):
                    env[tag] = (v, n, i, x, y)
    for tag in 'WESN':
        v, n, i, x, y = env[tag]
        A(f'STAIR-{tag}', x, y, rev_bl, n, f'footprint.vertex[{i}]', 'step_extremum',
          'PROPOSED', 'VERIFIED_OBJECT', f'blender:{n} extremum {tag}')
    # 次卫隔墙 (R3 对象组)
    if 'R3_COMPLETE_PARTITION_WALLS' in walls:
        b = walls['R3_COMPLETE_PARTITION_WALLS']
        for tag, xs, ys in (('W','W','S'),('E','E','S'),('S','W','S'),('N','W','N')):
            bl_anchor('BATH2-'+tag, 'R3_COMPLETE_PARTITION_WALLS', b, xs, ys, 'partition_face')
    # 厨房洞口: 残墙顶 ↔ 北墙底
    if 'KITCHEN_DIVIDER_PIER_SITE_REVIEW' in walls:
        b = walls['KITCHEN_DIVIDER_PIER_SITE_REVIEW']
        A('KOPEN-S', b[0], b[3], rev_bl, 'KITCHEN_DIVIDER_PIER_SITE_REVIEW', 'bbox.corner(NW-top)',
          'opening_edge', 'PROPOSED', 'VERIFIED_OBJECT', 'blender pier ymax')
    if 'W_wall_md_0010' in walls:
        b = walls['W_wall_md_0010']
        A('KOPEN-N', b[0], b[1], rev_bl, 'W_wall_md_0010', 'bbox.corner(SW)',
          'opening_edge', 'EXISTING', 'VERIFIED_OBJECT', 'blender stub ymin')

    # --- S2 DXF 门洞实体 (handle) ---
    rev_dxf = {'path': items['baseline_dxf']['path'], 'current': st['baseline_dxf']['current']}
    ddoc = ezdxf.readfile(ROOT / items['baseline_dxf']['path'])
    openings = []
    for e in ddoc.modelspace():
        if e.dxf.layer == 'A-DOOR' and e.dxftype() == 'LWPOLYLINE':
            pts = [(p[0], p[1]) for p in e.get_points('xy')]
            xs = [p[0] for p in pts]; ys = [p[1] for p in pts]
            w, h = max(xs) - min(xs), max(ys) - min(ys)
            openings.append({'handle': e.dxf.handle, 'rect': [min(xs), min(ys), max(xs), max(ys)],
                             'opening_len': round(max(w, h)), 'wall_thk': round(min(w, h)),
                             'orient': 'H' if w >= h else 'V'})
    out = {'version': 'v02', 'generated_by': 'extract_anchors_v02.py',
           'units': 'mm', 'sources': st, 'anchors': ANCHORS,
           'door_openings': openings,
           'dims': {
             'south_total':   {'a': 'S-SPAN-W', 'b': 'S-SPAN-E', 'axis': 'x'},
             'west_total':    {'a': 'W-SPAN-S', 'b': 'W-SPAN-N', 'axis': 'y'},
             'kitchen_face':  {'a': 'KIT-W-FACE', 'b': 'KIT-E-FACE', 'axis': 'x'},
             'master_clear':  {'a': 'MBED-W-FACE', 'b': 'MBED-E-FACE', 'axis': 'x'},
             'mother_clear':  {'a': 'MOT-W-FACE', 'b': 'MOT-E-FACE', 'axis': 'x'},
             'living_window': {'a': 'LWIN-W', 'b': 'LWIN-E', 'axis': 'x'},
             'balcony_north': {'a': 'BALC-N-W', 'b': 'BALC-N-E', 'axis': 'x'},
             'stair_width':   {'a': 'STAIR-W', 'b': 'STAIR-E', 'axis': 'x'},
             'stair_depth':   {'a': 'STAIR-S', 'b': 'STAIR-N', 'axis': 'y'},
             'bath2_width':   {'a': 'BATH2-W', 'b': 'BATH2-E', 'axis': 'x'},
             'bath2_depth':   {'a': 'BATH2-S', 'b': 'BATH2-N', 'axis': 'y'},
             'kitchen_open':  {'a': 'KOPEN-S', 'b': 'KOPEN-N', 'axis': 'y'},
           }}
    (CAD / 'derived' / out_name).write_text(json.dumps(out, ensure_ascii=False, indent=1))
    stale = [k for k, v in st.items() if v['state'] != 'FRESH']
    print(f'anchors={len(ANCHORS)} openings={len(openings)} dims={len(out["dims"])} stale={stale}')
    return out

if __name__ == '__main__':
    extract()
