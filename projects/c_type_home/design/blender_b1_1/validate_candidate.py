"""Independent fresh-process checks of the B1 candidate, never save the scene."""
import bpy
import hashlib
import json
import math
from pathlib import Path
from mathutils import Vector

ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent
MODEL = OUT / 'B1_1_DESIGN_MODEL_V1.blend'

def signature(o):
    h = hashlib.sha256()
    if o.type == 'MESH':
        for v in o.data.vertices:
            h.update((','.join(format(c, '.9g') for c in v.co) + ';').encode())
        for p in o.data.polygons:
            h.update((','.join(str(v) for v in p.vertices) + ';').encode())
    else:
        h.update(o.type.encode())
    return h.hexdigest()

def bounds(objects):
    points = [o.matrix_world @ Vector(v) for o in objects if o.type == 'MESH' for v in o.bound_box]
    return [[min(p[i] for p in points) for i in range(3)],
            [max(p[i] for p in points) for i in range(3)]]

def check():
    assert MODEL.is_file(), 'Requested B1.1 candidate has not been built'
    bpy.ops.wm.open_mainfile(filepath=str(MODEL))
    # Disabled collections retain authored transforms but skip matrix evaluation.
    # Enable only inside this read-only validation process; never save this state.
    for name in ['05_HUMAN_DESIGN_GUIDE','90_FUTURE_DESIGN_OPTIONS','91_ACCESSIBILITY_OPTIONS','03_EXISTING_CEILING']:
        bpy.data.collections[name].hide_viewport=False
    bpy.context.view_layer.update()
    snap = json.loads((OUT/'SOURCE_SCENE_SNAPSHOT.json').read_text())['branch']['objects']
    preserved, changed = [], []
    for record in snap:
        obj = bpy.data.objects.get(record['name'])
        ok = obj is not None and signature(obj) == record['geometry_signature']
        if ok:
            ok = max(abs(obj.matrix_world[i][j]-record['matrix'][i][j])
                     for i in range(4) for j in range(4)) < 1e-7
        (preserved if ok else changed).append(record['name'])
    assert not changed, 'Inherited geometry/transform changed: ' + ', '.join(changed)
    manifest = json.loads((ROOT/'design/blender_b0/B0_FREEZE_MANIFEST.json').read_text())
    frozen = []
    for key, expected in manifest['sha256'].items():
        actual = hashlib.sha256((ROOT/manifest['files'][key]).read_bytes()).hexdigest()
        frozen.append(dict(key=key, expected=expected, actual=actual, match=actual==expected))
    assert all(c['match'] for c in frozen), 'B0_INTEGRITY = FAIL; stop'
    register = json.loads((OUT/'B1_1_ASSET_REGISTER.json').read_text())
    checks = []
    for entry in register['items']:
        if not entry.get('verify_envelope', False):
            continue
        objects = [bpy.data.objects[n] for n in entry['body_objects']]
        got = bounds(objects)
        target = entry['target_bounds_m']
        delta = max(abs(got[i][j]-target[i][j]) for i in range(2) for j in range(3))
        checks.append(dict(source_name=entry['source_name'], max_bounds_error_mm=delta*1000,
                           pass_check=delta <= 0.001, actual_bounds_m=got, target_bounds_m=target))
    assert checks and all(c['pass_check'] for c in checks), 'Furniture world envelope differs from source'
    orient = []
    for entry in register['items']:
        if entry.get('actual_front_world') is not None and entry.get('orientation_status')=='REGISTER_MATCH':
            v = entry['actual_front_world']
            ang = math.degrees(math.atan2(v[1],v[0])) % 360
            expected = entry['facing_deg'] % 360
            error = abs((ang-expected+180)%360-180)
            orient.append(dict(source_name=entry['source_name'],actual_deg=ang,expected_deg=expected,error_deg=error))
    assert all(c['error_deg']<0.001 for c in orient), 'Furniture front differs from orientation register'
    invalid=[]; new_triangles=0
    depsgraph=bpy.context.evaluated_depsgraph_get()
    for obj in bpy.data.objects:
        if obj.type!='MESH' or not obj.name.startswith('B11_'):
            continue
        for v in obj.data.vertices:
            if not all(math.isfinite(c) for c in v.co):
                invalid.append(obj.name)
                break
        ev=obj.evaluated_get(depsgraph); mesh=ev.to_mesh();mesh.calc_loop_triangles()
        new_triangles+=len(mesh.loop_triangles);ev.to_mesh_clear()
    assert not invalid, 'Non-finite generated geometry'
    assert new_triangles<2000000, 'Review geometry exceeds contracted density'
    assert sum(1 for o in bpy.data.objects if o.name.startswith('GLZ_'))==9
    assert abs(math.degrees(bpy.data.objects['LEAF_D107'].rotation_euler.z)-26.3)<0.01
    assert len(register['bay_assemblies'])==4
    for col in ['90_FUTURE_DESIGN_OPTIONS','91_ACCESSIBILITY_OPTIONS']:
        assert bpy.data.collections[col].hide_render, 'Future options exposed in default review'
    assert bpy.context.scene['B1_1_DESIGN_MODEL']=='HUMAN_REVIEW'
    result=dict(status='PASS',scope='INTEGRITY_AND_DECLARED_DIMENSIONAL_GATES_ONLY',
                inherited_objects_preserved=len(preserved),frozen_files=frozen,
                furniture_envelopes=checks,orientation_checks=orient,
                evaluated_new_triangles=new_triangles,invalid_coordinates=invalid,
                known_visual_or_design_issues=register['decisions_required'],
                model_sha256=hashlib.sha256(MODEL.read_bytes()).hexdigest())
    (OUT/'B1_1_FRESH_OPEN_VALIDATION.json').write_text(json.dumps(result,ensure_ascii=False,indent=2))
    print(json.dumps({k:result[k] for k in ['status','scope','inherited_objects_preserved','evaluated_new_triangles','model_sha256']},indent=2))

if __name__ == '__main__':
    check()
