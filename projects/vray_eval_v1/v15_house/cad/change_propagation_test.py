#!/usr/bin/env python3
"""端到端传播测试: FreeCAD对象几何变更 → 锚点 → DXF → DIMENSION 自动更新"""
import json, shutil, subprocess, sys, math
from pathlib import Path
import ezdxf

CAD = Path(__file__).resolve().parent
ROOT = CAD.parents[3]
FCMD = '/Applications/FreeCAD.app/Contents/Resources/bin/freecadcmd'
PY = str(ROOT / '.cadenv/bin/python') if (ROOT/'.cadenv/bin/python').exists() else sys.executable
TDIR = CAD / 'derived' / 'prop_test'; TDIR.mkdir(exist_ok=True)
FC_SRC = ROOT / 'projects/c_type_home/cad/C型_原始户型数字化基准模型.FCStd'
FC_TEST = TDIR / 'TEST_MODEL.FCStd'
SHIFT = 100.0

# 1. 基线: 提取+生成
subprocess.run([PY, str(CAD/'extract_anchors_v02.py')], check=True, cwd=CAD)
subprocess.run([PY, str(CAD/'make_a103_poc_v2.py')], check=True, cwd=CAD)
def south_total(dxf):
    doc = ezdxf.readfile(dxf)
    for e in doc.modelspace():
        if e.dxftype() == 'DIMENSION':
            p2, p3 = e.dxf.defpoint2, e.dxf.defpoint3
            if abs(p2.y - p3.y) < 900 and abs(e.get_measurement() - 14300) < 2000:
                return e.get_measurement()
base_val = south_total(CAD/'A103_CONSTRUCTION_POC_V2.dxf')
print('baseline south_total =', base_val)

# 2. FreeCAD 测试副本中移动 W_BALC_S +100mm (真实模型编辑)
shutil.copy(FC_SRC, FC_TEST)
code = f'''
import FreeCAD as App
doc = App.openDocument({str(FC_TEST)!r})
o = doc.getObject('W_BALC_S')
o.Placement.Base.x += {SHIFT}
doc.recompute(); doc.save()
print('moved W_BALC_S +{SHIFT}mm')
'''
r = subprocess.run([FCMD, '-c', code], capture_output=True, text=True, timeout=180)
assert 'moved' in r.stdout, r.stdout[-1000:] + r.stderr[-500:]

# 3. 用变更后的 FCStd 重提锚点 + 重生成
sys.path.insert(0, str(CAD))
import extract_anchors_v02
extract_anchors_v02.extract(fcstd_override=FC_TEST, out_name='geometry_prop_test.json')
subprocess.run([PY, str(CAD/'make_a103_poc_v2.py'), 'geometry_prop_test.json', 'A103_PROP_TEST.dxf'],
               check=True, cwd=CAD)
new_val = south_total(CAD/'A103_PROP_TEST.dxf')
print('after W_BALC_S+100mm: south_total =', new_val)

# 4. 断言
assert new_val is not None and base_val is not None
assert abs((base_val - new_val) - SHIFT) < 1.0, f'expected {SHIFT}mm shift, got {base_val-new_val}'
print(f'PASS: FreeCAD object change propagated to DXF dimension ({base_val} -> {new_val})')
(CAD/'derived'/'prop_test_result.json').write_text(json.dumps(
    {'test': 'change_propagation', 'object': 'W_BALC_S', 'shift_mm': SHIFT,
     'dim_before': base_val, 'dim_after': new_val, 'status': 'PASS'}, indent=1))
