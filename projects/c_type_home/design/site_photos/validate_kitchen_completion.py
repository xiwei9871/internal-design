"""Fresh-process verification of the original island/new utility additions and preserved source geometry."""
import bpy
import hashlib
import json
import math
from pathlib import Path
from mathutils import Vector

OUT=Path(__file__).resolve().parent;ROOT=OUT.parents[1]
SOURCE=OUT/'B1_1_SITE_CORRECTED_V1.blend';MODEL=OUT/'B1_1_SITE_CORRECTED_V2.blend'
def signature(o):
    h=hashlib.sha256()
    if o.type=='MESH':
        for v in o.data.vertices:h.update((','.join(format(c,'.9g') for c in v.co)+';').encode())
        for p in o.data.polygons:h.update((','.join(str(v) for v in p.vertices)+';').encode())
    else:h.update(o.type.encode())
    return h.hexdigest()
def enable_evaluation():
    for c in bpy.data.collections:c.hide_viewport=False
    for o in bpy.data.objects:o.hide_viewport=False
    bpy.context.view_layer.update()
def bounds(root):
    points=[o.matrix_world@Vector(v) for o in root.children_recursive if o.type=='MESH' for v in o.bound_box]
    return [[min(p[i] for p in points) for i in range(3)],[max(p[i] for p in points) for i in range(3)]]
bpy.ops.wm.open_mainfile(filepath=str(SOURCE));enable_evaluation()
snap={o.name:dict(signature=signature(o),matrix=[list(row) for row in o.matrix_world]) for o in bpy.data.objects}
source_hash=hashlib.sha256(SOURCE.read_bytes()).hexdigest()
bpy.ops.wm.open_mainfile(filepath=str(MODEL));enable_evaluation()
for name,record in snap.items():
    o=bpy.data.objects[name];assert signature(o)==record['signature'],'Existing mesh changed: '+name
    assert max(abs(o.matrix_world[i][j]-record['matrix'][i][j]) for i in range(4) for j in range(4))<1e-7,'Existing pose changed: '+name
island=bounds(bpy.data.objects['B11_K-ISLAND-PDF-C'])
utility=bounds(bpy.data.objects['B11_K-UTILITY-TALL-600'])
ac=bounds(bpy.data.objects['B11_K-UTILITY-WALL-AC'])
assert abs((island[1][0]-island[0][0])-.467)<1e-5
assert abs((island[1][1]-island[0][1])-.800)<1e-5
assert abs(island[1][2]-.960)<1e-5
assert abs((utility[1][0]-utility[0][0])-.600)<1e-5
assert abs((utility[1][2]-utility[0][2])-2.000)<1e-5
assert ac[0][2]>utility[1][2],'AC not above new cabinet'
assert abs((ac[0][0]+ac[1][0])/2-(utility[0][0]+utility[1][0])/2)<1e-5
for o in bpy.data.collections['COL_SITE_KITCHEN_ISLAND_AND_UTILITY'].objects:
    if o.type!='MESH':continue
    assert all(math.isfinite(c) for v in o.data.vertices for c in v.co)
    assert all(p.area>1e-10 for p in o.data.polygons),'Degenerate new face '+o.name
manifest=json.loads((ROOT/'design/blender_b0/B0_FREEZE_MANIFEST.json').read_text())
for key,expected in manifest['sha256'].items():
    assert hashlib.sha256((ROOT/manifest['files'][key]).read_bytes()).hexdigest()==expected
assert hashlib.sha256(SOURCE.read_bytes()).hexdigest()==source_hash
qa=dict(status='PASS',B0_INTEGRITY='PASS',frozen_files_match=7,
    all_previous_objects_geometry_and_pose_preserved=len(snap),accepted_fridge_area_unchanged=True,
    island_dimensions_mm=[(island[1][1]-island[0][1])*1000,(island[1][0]-island[0][0])*1000,island[1][2]*1000],
    utility_dimensions_mm=[(utility[1][0]-utility[0][0])*1000,(utility[1][1]-utility[0][1])*1000,(utility[1][2]-utility[0][2])*1000],
    ac_above_cabinet=True,ac_review_bounds_m=ac,source_v1_sha256=source_hash,
    model_sha256=hashlib.sha256(MODEL.read_bytes()).hexdigest(),stage='HUMAN_REVIEW',
    review_assumptions=['utility depth500','AC generic dimensions/mount Z','rounded counter radius40','PDF-to-B1 island placement alignment'])
(OUT/'KITCHEN_COMPLETION_QA.json').write_text(json.dumps(qa,ensure_ascii=False,indent=2))
print(json.dumps(qa,ensure_ascii=False,indent=2))
