#!/usr/bin/env python3
"""P1.2 四类回归测试 (隔离工作区 derived/p12_tests/)"""
import json, shutil, subprocess, sys
from pathlib import Path
import ezdxf

CAD = Path(__file__).resolve().parent
ROOT = CAD.parents[3]
PY = sys.executable
FCMD = '/Applications/FreeCAD.app/Contents/Resources/bin/freecadcmd'
BLENDER = '/opt/homebrew/bin/blender'
T = CAD / 'derived' / 'p12_tests'; T.mkdir(exist_ok=True)
FC_SRC = ROOT / 'projects/c_type_home/cad/C型_原始户型数字化基准模型.FCStd'
BL_SRC = ROOT / 'projects/vray_eval_v1/v15_house/V15_WORK.blend'
RESULTS = {}

def run(cmd, **kw):
    return subprocess.run(cmd, capture_output=True, text=True, cwd=CAD, **kw)

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
            try:
                xd = [v for c, v in e.get_xdata('DEVINSRC') if c == 1000]
            except ezdxf.DXFValueError: xd = []
            if name in xd:
                pts = list(e.get_points('xy'))
                xs = [p[0] for p in pts]; ys = [p[1] for p in pts]
                return [min(xs), min(ys), max(xs), max(ys)]
    return None

# ============ T-A: FreeCAD 墙移动 → 墙线+标注同步 ============
print('=== T-A: FC wall move -> geometry+dim sync ===')
fc_test = T / 'TEST_FC.FCStd'; shutil.copy(FC_SRC, fc_test)
# 基线
run([PY, 'extract_anchors_v03.py'])
run([PY, 'make_a103_poc_v3.py'])
base_dim = get_dim(CAD/'A103_CONSTRUCTION_POC_V3.dxf', 'south_total')
base_wall = get_wall_bbox(CAD/'A103_CONSTRUCTION_POC_V3.dxf', 'W_BALC_S')
print(' baseline: dim', base_dim, 'wall xmin', base_wall[0])
# 改 FC 对象
code = f'''
import FreeCAD as App
doc = App.openDocument({str(fc_test)!r})
doc.getObject('W_BALC_S').Placement.Base.x += 100
doc.recompute(); doc.save()
'''
r = run([FCMD, '-c', code])
sys.path.insert(0, str(CAD)); import extract_anchors_v03
extract_anchors_v03.extract(fcstd_override=fc_test, out_name='geometry_p12a.json',
                            bl_dump=CAD/'derived'/'blender_geom_raw.json')
run([PY, 'make_a103_poc_v3.py', 'geometry_p12a.json', str(T/'A103_TEST_FC.dxf')])
new_dim = get_dim(T/'A103_TEST_FC.dxf', 'south_total')
new_wall = get_wall_bbox(T/'A103_TEST_FC.dxf', 'W_BALC_S')
wall_moved = new_wall and abs(new_wall[0] - base_wall[0] - 100) < 1
dim_moved = new_dim and abs(base_dim - new_dim - 100) < 1
RESULTS['T-A_fc_wall_sync'] = 'PASS' if wall_moved and dim_moved else 'FAIL'
print(f' after+100mm: dim {new_dim} wall xmin {new_wall and new_wall[0]}')
print(f' wall_moved={wall_moved} dim_moved={dim_moved} -> {RESULTS["T-A_fc_wall_sync"]}')

# ============ T-B: Blender 对象移动 → 传播 ============
print('=== T-B: Blender object move -> propagation ===')
bl_test = T / 'TEST_MODEL.blend'
shutil.copy(BL_SRC, bl_test)
mv = T / 'move_r3.py'
mv.write_text('''import bpy
o = bpy.data.objects['R3_COMPLETE_PARTITION_WALLS']
for v in o.data.vertices: v.co.x += 0.1
o.data.update()
bpy.ops.wm.save_as_mainfile(filepath=bpy.data.filepath)
print('MOVED R3 mesh +0.1m')
''')
r = run([BLENDER, '-b', str(bl_test), '-P', str(mv)], timeout=600)
assert 'MOVED' in r.stdout, r.stdout[-500:]
base_b2 = get_dim(CAD/'A103_CONSTRUCTION_POC_V3.dxf', 'bath2_envelope_w')
extract_anchors_v03.extract(blend_override=bl_test, out_name='geometry_p12b.json',
                            fc_dump=CAD/'derived'/'fc_objects_raw.json',
                            bl_dump=T/'blender_geom_p12b.json')
run([PY, 'make_a103_poc_v3.py', 'geometry_p12b.json', str(T/'A103_TEST_BL.dxf')])
new_b2 = get_dim(T/'A103_TEST_BL.dxf', 'bath2_envelope_w')
new_bwall = get_wall_bbox(T/'A103_TEST_BL.dxf', 'R3_COMPLETE_PARTITION_WALLS')
RESULTS['T-B_blender_prop'] = 'PASS' if (new_b2 and abs(base_b2 - new_b2) < 1 and
                                       new_bwall and abs(new_bwall[0] - 9159) < 1) else 'FAIL'
print(f' bath2_envelope_w {base_b2}->{new_b2}; R3 west wall bbox {new_bwall and new_bwall[0]} -> {RESULTS["T-B_blender_prop"]}')

# ============ T-C: 提取后源变更 → 生成 BLOCK ============
print('=== T-C: source tampered AFTER extraction -> BLOCK ===')
fc_t = T / 'TEST_FC2.FCStd'; shutil.copy(FC_SRC, fc_t)
extract_anchors_v03.extract(fcstd_override=fc_t, out_name='geometry_p12c.json',
                            bl_dump=CAD/'derived'/'blender_geom_raw.json')
with open(fc_t, 'ab') as f: f.write(b'\x00' * 16)   # 篡改测试副本 (不动生产文件)
r = run([PY, 'make_a103_poc_v3.py', 'geometry_p12c.json', str(T/'A103_TEST_C.dxf')])
RESULTS['T-C_stale_block'] = 'PASS' if r.returncode != 0 and 'CHANGED' in r.stdout else 'FAIL'
print(' generator rc:', r.returncode, '->', RESULTS['T-C_stale_block'])
print(' ', (r.stdout or r.stderr).strip().split(chr(10))[0][:120])

# ============ T-D: 缺锚点 → BLOCK ============
print('=== T-D: missing anchor -> BLOCK ===')
g = json.loads((CAD/'derived'/'geometry_v03.json').read_text())
g2 = json.loads(json.dumps(g))
g2['anchors'] = [a for a in g2['anchors'] if a['id'] != 'S-SPAN-E']
(CAD/'derived'/'geometry_p12d.json').write_text(json.dumps(g2))
r = run([PY, 'make_a103_poc_v3.py', 'geometry_p12d.json', str(T/'A103_TEST_D.dxf')])
RESULTS['T-D_missing_anchor'] = 'PASS' if r.returncode != 0 and 'missing anchor' in r.stdout else 'FAIL'
print(' generator rc:', r.returncode, '->', RESULTS['T-D_missing_anchor'])

(T/'p12_test_results.json').write_text(json.dumps(RESULTS, indent=1))
print('\\n=== RESULTS ==='); [print(' ', k, v) for k, v in RESULTS.items()]
