"""Read source blend data; write only B1.1 inspection evidence."""
import bpy
import hashlib
import json
from pathlib import Path
from mathutils import Vector

ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent

def integrity():
    m = json.loads((ROOT / 'design/blender_b0/B0_FREEZE_MANIFEST.json').read_text())
    rows = []
    for key, expected in m['sha256'].items():
        path = ROOT / m['files'][key]
        actual = hashlib.sha256(path.read_bytes()).hexdigest()
        rows.append(dict(key=key, path=m['files'][key], expected=expected, actual=actual,
                         status='MATCH' if actual == expected else 'MISMATCH'))
    if any(r['status'] != 'MATCH' for r in rows):
        raise RuntimeError('B0_INTEGRITY = FAIL; STOP: ' + json.dumps(rows))
    return dict(B0_INTEGRITY='PASS', results=rows)

def plain(value):
    if hasattr(value, 'to_dict'):
        return value.to_dict()
    if hasattr(value, 'to_list'):
        return value.to_list()
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    return str(value)

def geometry_signature(o):
    h = hashlib.sha256()
    if o.type == 'MESH':
        for v in o.data.vertices:
            h.update((','.join(format(c, '.9g') for c in v.co) + ';').encode())
        for p in o.data.polygons:
            h.update((','.join(str(v) for v in p.vertices) + ';').encode())
    else:
        h.update(o.type.encode())
    return h.hexdigest()

def inspect(path):
    bpy.ops.wm.open_mainfile(filepath=str(path))
    objs = []
    for o in bpy.data.objects:
        coords = [o.matrix_world @ Vector(v) for v in o.bound_box] if o.type == 'MESH' else []
        objs.append(dict(name=o.name, type=o.type, collections=[c.name for c in o.users_collection],
                         location=list(o.location), rotation=list(o.rotation_euler), scale=list(o.scale),
                         dimensions=list(o.dimensions), matrix=[list(row) for row in o.matrix_world],
                         bounds=[[min(v[i] for v in coords) for i in range(3)],
                                 [max(v[i] for v in coords) for i in range(3)]] if coords else None,
                         properties={k:plain(v) for k,v in o.items()},
                         materials=[m.name if m else None for m in o.data.materials] if o.type=='MESH' else [],
                         geometry_signature=geometry_signature(o),
                         vertices=len(o.data.vertices) if o.type=='MESH' else 0,
                         polygons=len(o.data.polygons) if o.type=='MESH' else 0,
                         hidden_render=o.hide_render, hidden_viewport=o.hide_viewport))
    return dict(path=str(path), scene_properties={k:plain(v) for k,v in bpy.context.scene.items()},
                objects=objs, collections=[dict(name=c.name, hide_render=c.hide_render,
                hide_viewport=c.hide_viewport, objects=len(c.objects)) for c in bpy.data.collections])

report = integrity()
baseline = inspect(ROOT / 'design/blender_b0/B0_EXISTING_AS_IS.blend')
branch = inspect(ROOT / 'design/blender_b0/B1_RENOVATION_DESIGN.blend')
(OUT / 'B0_INTEGRITY_PREFLIGHT.json').write_text(json.dumps(report, indent=2))
(OUT / 'SOURCE_SCENE_SNAPSHOT.json').write_text(json.dumps(dict(baseline=baseline, branch=branch), ensure_ascii=False, indent=2))
print('B0_INTEGRITY = PASS')
print('COLLECTIONS ' + json.dumps(branch['collections'], ensure_ascii=False))
print('OBJECTS ' + json.dumps([{k:o[k] for k in ['name','collections','bounds','properties']} for o in branch['objects'] if o['type']=='MESH'], ensure_ascii=False))
