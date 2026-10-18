#!/usr/bin/env python3
"""geometry_v03: 实时双源提取 (freecadcmd + blender -b) + 语义分级 + 管理实体轮廓"""
import json, hashlib, subprocess, sys
from pathlib import Path
import ezdxf
from shapely.geometry import Polygon, MultiPolygon
from shapely.ops import unary_union, polygonize
from shapely.geometry import LineString, MultiPoint
from shapely import concave_hull

CAD = Path(__file__).resolve().parent
ROOT = CAD.parents[3]
MANIFEST = CAD / 'CONSTRUCTION_INPUT_MANIFEST.json'
FCMD = '/Applications/FreeCAD.app/Contents/Resources/bin/freecadcmd'
BLENDER = '/opt/homebrew/bin/blender'
DER = CAD / 'derived'; DER.mkdir(exist_ok=True)

def sha256(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()

def load_manifest():
    return {i['id']: i for i in json.loads(MANIFEST.read_text())['inputs']}

def src_status(items):
    st = {}
    for iid, it in items.items():
        p = ROOT / it['path']
        cur = sha256(p) if p.exists() else 'MISSING'
        st[iid] = {'path': it['path'], 'recorded': it['sha256'], 'current': cur,
                   'state': 'FRESH' if cur == it['sha256'] else 'STALE_OR_MISSING'}
    return st

# ---------- FreeCAD 对象 dump (含底面有序轮廓) ----------
def dump_fc(fc_path: Path, out_json: Path):
    """只取 bbox+verts (已验证稳定) —— Edges 访问会触发内核崩溃"""
    out_json.unlink(missing_ok=True)
    code = f'''
import FreeCAD as App, json
doc = App.openDocument({str(fc_path)!r})
out = []
for o in doc.Objects:
    if hasattr(o, 'Shape') and o.Shape.Vertexes:
        bb = o.Shape.BoundBox
        verts = [[round(v.Point.x, 2), round(v.Point.y, 2)] for v in o.Shape.Vertexes]
        out.append({{'name': o.Name, 'label': o.Label,
                    'bbox': [round(bb.XMin,2), round(bb.YMin,2), round(bb.XMax,2), round(bb.YMax,2)],
                    'verts': verts}})
json.dump(out, open({str(out_json)!r}, 'w'), ensure_ascii=False)
'''
    r = subprocess.run([FCMD, '-c', code], capture_output=True, text=True, timeout=300)
    if not out_json.exists():
        print(r.stdout[-1500:], r.stderr[-800:]); sys.exit('fc dump failed')

# ---------- Blender 对象 dump ----------
def dump_blender(blend_path: Path, out_json: Path):
    r = subprocess.run([BLENDER, '-b', str(blend_path), '-P', str(CAD/'blender_dump_geom.py'),
                        '--', str(out_json)], capture_output=True, text=True, timeout=600)
    if not out_json.exists():
        print(r.stdout[-1500:], r.stderr[-800:]); sys.exit('blender dump failed')

def union_outline(tris):
    """三角形 XY 面片 → 并集外轮廓 (取最大多边形)"""
    polys = []
    for t in tris:
        p = Polygon(t)
        if p.is_valid and p.area > 1: polys.append(p)
    if not polys: return None
    u = unary_union(polys)
    if isinstance(u, MultiPolygon): u = max(u.geoms, key=lambda g: g.area)
    if isinstance(u, Polygon):
        return [[round(x, 1), round(y, 1)] for x, y in u.exterior.coords[:-1]]
    return None

# ---------- 提取 ----------
def extract(fcstd_override=None, blend_override=None, out_name='geometry_v03.json',
            fc_dump=None, bl_dump=None):
    items = load_manifest(); st = src_status(items)
    fc_path = Path(fcstd_override) if fcstd_override else ROOT / items['baseline_fcstd']['path']
    bl_path = Path(blend_override) if blend_override else \
        ROOT / items.get('v15_work_blend', {'path': 'projects/vray_eval_v1/v15_house/V15_WORK.blend'})['path']
    fc_sha, bl_sha = sha256(fc_path), sha256(bl_path) if bl_path.exists() else 'MISSING'
    fc_raw = fc_dump or DER / 'fc_objects_raw.json'
    bl_raw = bl_dump or DER / 'blender_geom_raw.json'
    dump_fc(fc_path, fc_raw)
    if bl_dump is None:                 # 生产路径始终实时 dump
        dump_blender(bl_path, bl_raw)
    elif not Path(bl_raw).exists():     # 测试传路径但未生成 -> 从其 blend 实 dump
        dump_blender(bl_path, bl_raw)
    objs = {o['name']: o for o in json.loads(Path(fc_raw).read_text())}
    blobs = json.loads(Path(bl_raw).read_text())
    # 衍生数据登记 (来源 hash 关联)
    derived_reg = {
        'fc_objects_raw':  {'file': str(fc_raw), 'sha256': sha256(fc_raw), 'parent_sha256': fc_sha},
        'blender_geom_raw': {'file': str(bl_raw), 'sha256': sha256(bl_raw), 'parent_sha256': bl_sha},
    }
    AN = []
    def A(aid, x, y, src, oid, sub, role, ds, vs, ev):
        AN.append({'id': aid, 'x': round(x, 2), 'y': round(y, 2), 'source_file': src['path'],
                   'source_file_sha256': src['sha'], 'source_revision': src['sha'][:12],
                   'source_object_id': oid, 'subelement_reference': sub, 'geometry_role': role,
                   'design_status': ds, 'verification_status': vs, 'evidence': ev})
    rev_fc = {'path': str(fc_path), 'sha': fc_sha}
    rev_bl = {'path': str(bl_path), 'sha': bl_sha}
    def fc_ext(aid, name, axis, mm, role='wall_face'):
        vs = objs[name]['verts']
        tgt = (min if mm == 'min' else max)(v[axis] for v in vs)
        idx = next(i for i, v in enumerate(vs) if v[axis] == tgt)
        A(aid, vs[idx][0], vs[idx][1], rev_fc, name, f'Shape.Vertexes[{idx}]', role,
          'EXISTING', 'OBJECT_IDENTIFIED', f'fcstd:{name}.{chr(120+axis)}{mm}')
    fc_specs = [('S-SPAN-W','W_BALC_S',0,'min'),('S-SPAN-E','W_EXT_E1',0,'max'),
                ('W-SPAN-S','W_BALC_S',1,'min'),('W-SPAN-N','W_EXT_N_BAL',1,'max'),
                ('KIT-W-FACE','W_INT_X5800',0,'min'),('KIT-E-FACE','W_INT_X7900_L',0,'min'),
                ('MBED-W-FACE','W_INT_X7900_L',0,'max'),('MBED-E-FACE','W_INT_X11500',0,'min'),
                ('MOT-W-FACE','W_INT_X11500',0,'max'),('MOT-E-FACE','W_EXT_E1',0,'min'),
                ('LWIN-W','W_BAY_F',0,'min'),('LWIN-E','W_BAY_F',0,'max'),
                ('BALC-N-W','W_EXT_N_BAL',0,'min'),('BALC-N-E','W_EXT_N_BAL',0,'max'),
                ('BATH2E-FACE','W_INT_X11500',0,'min')]
    for spec in fc_specs: fc_ext(*spec)
    # Blender 锚点
    def bl_ext(aid, name, xs, ys, role, vs_='OBJECT_IDENTIFIED'):
        b = blobs[name]['bbox']
        x = b[0] if xs == 'W' else b[2]; y = b[1] if ys == 'S' else b[3]
        A(aid, x, y, rev_bl, name, f'bbox.corner({xs}{ys})', role, 'PROPOSED', vs_,
          f'blender:{name} bbox {xs}{ys}')
    # 台阶包络 (STEP_*/WAVE_STEP_* 真轮廓极值)
    steps = {k: v for k, v in blobs.items()
             if k.startswith(('STEP_', 'WAVE_STEP')) and 'RAMP' not in k}
    env = {}
    for n, d in steps.items():
        for i, t in enumerate(d['tris_xy']):
            for x, y in t:
                for tag, val, cmp in (('W', x, -1), ('E', x, 1), ('S', y, -1), ('N', y, 1)):
                    if tag not in env or cmp * val > cmp * env[tag][0]:
                        env[tag] = (val, n, x, y)
    for tag in 'WESN':
        v, n, x, y = env[tag]
        A('STAIR-' + tag, x, y, rev_bl, n, f'mesh_extremum({tag})', 'step_extremum',
          'PROPOSED', 'FIELD_VERIFY', f'blender:{n} {tag}-extremum — 台阶尺寸待现场复尺')
    # 次卫隔墙对象
    if 'R3_COMPLETE_PARTITION_WALLS' in blobs:
        for tag, xs, ys in (('W','W','S'),('E','E','S'),('S','W','S'),('N','W','N')):
            bl_ext('BATH2-' + tag, 'R3_COMPLETE_PARTITION_WALLS', xs, ys, 'partition_face')
    if 'VIEW_WALL_R3_WEST_PARTITION' in blobs:
        bl_ext('BATH2-NET-W', 'VIEW_WALL_R3_WEST_PARTITION', 'E', 'S', 'partition_inner_face')
    if 'VIEW_WALL_R3_SOUTH_POCKET_PARTITION' in blobs:
        bl_ext('BATH2-NET-S', 'VIEW_WALL_R3_SOUTH_POCKET_PARTITION', 'W', 'N', 'partition_inner_face')
    # 厨房洞口: 残墙顶 ↔ 北墙底 (同墙带)
    if 'KITCHEN_DIVIDER_PIER_SITE_REVIEW' in blobs:
        bl_ext('KOPEN-S', 'KITCHEN_DIVIDER_PIER_SITE_REVIEW', 'W', 'N', 'opening_edge', 'FIELD_VERIFY')
    if 'W_wall_md_0010' in blobs:
        bl_ext('KOPEN-N', 'W_wall_md_0010', 'W', 'S', 'opening_edge', 'FIELD_VERIFY')
    # ---------- 管理实体 (对象→图纸墙线, 供生成器重建) ----------
    managed = []
    def in_plan(b):
        return 0 <= b[0] <= 17000 and -800 <= b[1] <= 16000 and 0 <= b[2] <= 17000 and -800 <= b[3] <= 16000
    for n, o in objs.items():
        if not n.startswith(('W_', 'COL_')) or not o.get('verts'): continue
        ol = None
        try:
            h = concave_hull(MultiPoint(o['verts']), ratio=0.0)
            if h.geom_type == 'Polygon' and h.area > 1:
                ol = [[round(x,2),round(y,2)] for x,y in h.exterior.coords[:-1]]
        except Exception: pass
        if ol and len(ol) >= 3 and in_plan(o['bbox']):
            obx = [p[0] for p in ol]; oby = [p[1] for p in ol]
            managed.append({'object': n, 'source_file': str(fc_path),
                            'source_file_sha256': fc_sha, 'source': 'fcstd',
                            'design_status': 'EXISTING', 'layer': 'A-WALL',
                            'outline': ol, 'bbox': o['bbox'],
                            'outline_bbox': [min(obx),min(oby),max(obx),max(oby)]})
    WALLISH = ('WALL', 'PARTITION', 'PIER', 'POCKET', 'DIVIDER', 'HOST_WALL', 'RETURN_WALL')
    for n, d in blobs.items():
        if n.startswith('VIEW_WALL_W_wall_md_'): continue          # 视图副本去重
        wallish = n.startswith('W_wall') or any(k in n for k in WALLISH)
        stepish = n.startswith(('STEP_', 'WAVE_STEP'))
        if not (wallish or stepish) or 'RAMP' in n: continue
        if 'ROLLED_BACK' in n or '_OLD' in n or n.endswith('_BAK'): continue   # 被取代变体
        if not in_plan(d['bbox']): continue                         # 原点资产剔除
        ol = union_outline(d['tris_xy'])
        if not ol: continue
        layer = 'A-DESIGN' if stepish else 'A-WALL'
        obx = [p[0] for p in ol]; oby = [p[1] for p in ol]
        managed.append({'object': n, 'source_file': str(bl_path),
                        'source_file_sha256': bl_sha, 'source': 'blender',
                        'design_status': 'PROPOSED', 'layer': layer,
                        'outline': ol, 'bbox': d['bbox'],
                        'outline_bbox': [min(obx),min(oby),max(obx),max(oby)]})
    # 基准 DXF 门洞
    ddoc = ezdxf.readfile(ROOT / items['baseline_dxf']['path'])
    openings = []
    for e in ddoc.modelspace():
        if e.dxf.layer == 'A-DOOR' and e.dxftype() == 'LWPOLYLINE':
            pts = [(p[0], p[1]) for p in e.get_points('xy')]
            xs = [p[0] for p in pts]; ys = [p[1] for p in pts]
            w, h = max(xs) - min(xs), max(ys) - min(ys)
            openings.append({'handle': e.dxf.handle,
                'rect': [min(xs), min(ys), max(xs), max(ys)],
                'opening_len': round(max(w, h)), 'wall_thk': round(min(w, h)),
                'orient': 'H' if w >= h else 'V', 'design_status': 'EXISTING',
                'swing': 'UNKNOWN_UNVERIFIED'})
    out = {'version': 'v03', 'generated_by': 'extract_anchors_v03.py', 'units': 'mm',
           'sources': st, 'derived_data': derived_reg,
           'anchors': AN, 'door_openings': openings, 'managed_entities': managed,
           'dims': {
             'south_total':    {'a': 'S-SPAN-W', 'b': 'S-SPAN-E', 'axis': 'x'},
             'west_total':     {'a': 'W-SPAN-S', 'b': 'W-SPAN-N', 'axis': 'y'},
             'kitchen_face':   {'a': 'KIT-W-FACE', 'b': 'KIT-E-FACE', 'axis': 'x'},
             'master_clear':   {'a': 'MBED-W-FACE', 'b': 'MBED-E-FACE', 'axis': 'x'},
             'mother_clear':   {'a': 'MOT-W-FACE', 'b': 'MOT-E-FACE', 'axis': 'x'},
             'living_window':  {'a': 'LWIN-W', 'b': 'LWIN-E', 'axis': 'x'},
             'balcony_north':  {'a': 'BALC-N-W', 'b': 'BALC-N-E', 'axis': 'x'},
             'stair_width':    {'a': 'STAIR-W', 'b': 'STAIR-E', 'axis': 'x'},
             'stair_depth':    {'a': 'STAIR-S', 'b': 'STAIR-N', 'axis': 'y'},
             'bath2_envelope_w': {'a': 'BATH2-W', 'b': 'BATH2-E', 'axis': 'x'},
             'bath2_net_w':    {'a': 'BATH2-NET-W', 'b': 'BATH2E-FACE', 'axis': 'x'},
             'kitchen_open':   {'a': 'KOPEN-S', 'b': 'KOPEN-N', 'axis': 'y'},
           }}
    (DER / out_name).write_text(json.dumps(out, ensure_ascii=False, indent=1))
    stale = [k for k, v in st.items() if v['state'] != 'FRESH']
    print(f'anchors={len(AN)} managed={len(managed)} openings={len(openings)} dims={len(out["dims"])} stale={stale}')
    return out

if __name__ == '__main__':
    extract()
