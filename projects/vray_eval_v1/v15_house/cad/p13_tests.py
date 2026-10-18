#!/usr/bin/env python3
"""P1.3 回归测试 (隔离工作区 derived/p13_tests/)
T-A FC墙移→几何+标注同步 | T-B Blender移→墙线+标注同步 | T-C 提取后篡改→BLOCK
T-D 缺锚→BLOCK | T-E 产物新鲜度 | 生产文件哈希不变"""
import json, shutil, subprocess, sys, time, hashlib, os
from pathlib import Path
import ezdxf

CAD = Path(__file__).resolve().parent
ROOT = CAD.parents[3]
PY = sys.executable
FCMD = '/Applications/FreeCAD.app/Contents/Resources/bin/freecadcmd'
T = CAD / 'derived' / 'p13_tests'; T.mkdir(exist_ok=True)
FC_SRC = ROOT / 'projects/c_type_home/cad/C型_原始户型数字化基准模型.FCStd'
BL_SRC = ROOT / 'projects/vray_eval_v1/v15_house/V15_WORK.blend'
BASE = CAD / 'A103_平面布置图.dxf'
RESULTS = {}
PROD_HASH = {p: hashlib.sha256(p.read_bytes()).hexdigest() for p in (FC_SRC, BL_SRC, BASE)}

def run(cmd, **kw):
    r = subprocess.run(cmd, capture_output=True, text=True, cwd=CAD, **kw)
    return r

def get_dim(dxf, tag):
    for e in ezdxf.readfile(dxf).modelspace():
        if e.dxftype() == 'DIMENSION':
            try:
                xd = e.get_xdata('DEVINDIM')
                if xd and xd[0][1] == tag: return e.get_measurement()
            except ezdxf.DXFValueError: pass
    return None

def get_wall_bbox(dxf, name):
    for e in ezdxf.readfile(dxf).modelspace():
        if e.dxftype() == 'LWPOLYLINE':
            try: xd = [v for c, v in e.get_xdata('DEVINSRC') if c == 1000]
            except ezdxf.DXFValueError: xd = []
            if name in xd:
                pts = list(e.get_points('xy'))
                xs=[p[0] for p in pts]; ys=[p[1] for p in pts]
                return [min(xs), min(ys), max(xs), max(ys)]
    return None

sys.path.insert(0, str(CAD))
import extract_anchors_v04 as X

# ============ T-A: FC 墙移 → 几何+标注 ============
print('=== T-A: FC W_BALC_S +100 ===')
fc_t = T/'TEST_FC.FCStd'; shutil.copy(FC_SRC, fc_t)
X.extract(out_name='geometry_p13a.json',
          fc_dump=T/'fc_raw_a.json', bl_dump=CAD/'derived'/'blender_geom_raw.json')
r = run([PY,'make_a103_poc_v4.py','geometry_p13a.json',str(T/'A_base.dxf')])
assert r.returncode == 0, r.stdout[-400:]
base_dim = get_dim(T/'A_base.dxf','south_total'); base_wall = get_wall_bbox(T/'A_base.dxf','W_BALC_S')
code = f"""
import FreeCAD as App
doc = App.openDocument({str(fc_t)!r})
doc.getObject('W_BALC_S').Placement.Base.x += 100
doc.recompute(); doc.save()
"""
r = run([FCMD,'-c',code]); assert r.returncode==0, r.stderr[-300:]
X.extract(fcstd_override=fc_t, out_name='geometry_p13a2.json',
          fc_dump=T/'fc_raw_a2.json', bl_dump=CAD/'derived'/'blender_geom_raw.json')
r = run([PY,'make_a103_poc_v4.py','geometry_p13a2.json',str(T/'A_moved.dxf')])
assert r.returncode == 0, r.stdout[-400:]
new_dim = get_dim(T/'A_moved.dxf','south_total'); new_wall = get_wall_bbox(T/'A_moved.dxf','W_BALC_S')
wm = new_wall and abs(new_wall[0]-base_wall[0]-100)<1
dm = new_dim and abs(base_dim-new_dim-100)<1
RESULTS['T-A_fc_geom_dim_sync']='PASS' if wm and dm else 'FAIL'
print(f'  dim {base_dim}->{new_dim} wall.xmin {base_wall[0]}->{new_wall and new_wall[0]} -> {RESULTS["T-A_fc_geom_dim_sync"]}')

# ============ T-B: Blender 墙移 → 墙线 + 关联 DIMENSION 同步 ============
print('=== T-B: Blender VIEW_WALL_R3_WEST_PARTITION +100 -> bath2_net_w ===')
bl_t = T/'TEST_MODEL.blend'; shutil.copy(BL_SRC, bl_t)
X.extract(out_name='geometry_p13b0.json',
          fc_dump=T/'fc_raw_b.json', bl_dump=T/'bl_raw_b0.json')
r = run([PY,'make_a103_poc_v4.py','geometry_p13b0.json',str(T/'B_base.dxf')])
assert r.returncode == 0, r.stdout[-400:]
b_dim = get_dim(T/'B_base.dxf','bath2_net_w')
b_wall = get_wall_bbox(T/'B_base.dxf','VIEW_WALL_R3_WEST_PARTITION')
mv = T/'move_part.py'
mv.write_text('''import bpy
o = bpy.data.objects['VIEW_WALL_R3_WEST_PARTITION']
for v in o.data.vertices: v.co.x += 0.1
o.data.update()
bpy.ops.wm.save_as_mainfile(filepath=bpy.data.filepath)
print('MOVED partition +0.1m')''')
r = run(['/opt/homebrew/bin/blender','-b',str(bl_t),'-P',str(mv)])
assert r.returncode==0 and 'MOVED' in r.stdout, r.stdout[-300:]
X.extract(blend_override=bl_t, out_name='geometry_p13b1.json',
          fc_dump=T/'fc_raw_b.json', bl_dump=T/'bl_raw_b1.json')
r = run([PY,'make_a103_poc_v4.py','geometry_p13b1.json',str(T/'B_moved.dxf')])
assert r.returncode == 0, r.stdout[-400:]
n_dim = get_dim(T/'B_moved.dxf','bath2_net_w')
n_wall = get_wall_bbox(T/'B_moved.dxf','VIEW_WALL_R3_WEST_PARTITION')
wm = n_wall and b_wall and abs(n_wall[2]-b_wall[2]-100)<1
dm = n_dim and b_dim and abs(b_dim-n_dim-100)<1
RESULTS['T-B_bl_geom_dim_sync']='PASS' if wm and dm else 'FAIL'
print(f'  dim {b_dim}->{n_dim} wall.xmax {b_wall and b_wall[2]}->{n_wall and n_wall[2]} -> {RESULTS["T-B_bl_geom_dim_sync"]}')

# ============ T-C: 提取后篡改源 → BLOCK ============
print('=== T-C: tamper after extract ===')
fc_c = T/'TEST_FC_C.FCStd'; shutil.copy(FC_SRC, fc_c)
X.extract(fcstd_override=fc_c, out_name='geometry_p13c.json',
          fc_dump=T/'fc_raw_c.json', bl_dump=CAD/'derived'/'blender_geom_raw.json')
with open(fc_c,'ab') as f: f.write(b'TAMPERED')
r = run([PY,'make_a103_poc_v4.py','geometry_p13c.json',str(T/'C.dxf')])
RESULTS['T-C_stale_block']='PASS' if r.returncode!=0 and 'BLOCK' in r.stdout else 'FAIL'
print(f'  rc={r.returncode} -> {RESULTS["T-C_stale_block"]}')

# ============ T-D: 缺锚 → BLOCK ============
print('=== T-D: missing anchor ===')
g = json.loads((CAD/'derived'/'geometry_v04.json').read_text())
g['anchors'] = [a for a in g['anchors'] if a['id'] != 'S-SPAN-W']
(CAD/'derived'/'geometry_p13d.json').write_text(json.dumps(g))
r = run([PY,'make_a103_poc_v4.py','geometry_p13d.json',str(T/'D.dxf')])
RESULTS['T-D_missing_anchor']='PASS' if r.returncode!=0 and 'missing anchor' in r.stdout else 'FAIL'
print(f'  rc={r.returncode} -> {RESULTS["T-D_missing_anchor"]}')

# ============ T-E: 产物新鲜度 + 生产文件未变 ============
t0 = time.time()-3600
fresh = all((T/f).exists() and (T/f).stat().st_mtime > t0 for f in
            ('A_moved.dxf','B_moved.dxf'))
prod_ok = all(hashlib.sha256(p.read_bytes()).hexdigest()==h for p,h in PROD_HASH.items())
RESULTS['T-E_fresh_outputs_prod_untouched']='PASS' if fresh and prod_ok else 'FAIL'
print(f'  fresh={fresh} prod_untouched={prod_ok} -> {RESULTS["T-E_fresh_outputs_prod_untouched"]}')

(T/'p13_test_results.json').write_text(json.dumps(RESULTS,indent=1))
print('\n', json.dumps(RESULTS,indent=1))
