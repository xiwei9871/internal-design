"""Fresh-open checks for the human-confirmed north-row kitchen logic."""
import bpy
import hashlib
import json
import sys
from pathlib import Path
from mathutils import Vector

OUT=Path(__file__).resolve().parent
ROOT=OUT.parents[1]
model=OUT/'B1_1_SITE_CORRECTED_V1.blend'
if '--' in sys.argv:model=Path(sys.argv[sys.argv.index('--')+1]).resolve()
assert model.is_file(),'Kitchen logic candidate not built'
bpy.ops.wm.open_mainfile(filepath=str(model))
for col in bpy.data.collections:col.hide_viewport=False
bpy.context.view_layer.update()

def descendants(root):
    return [o for o in root.children_recursive if o.type=='MESH']
def bounds(objects):
    points=[o.matrix_world@Vector(p) for o in objects for p in o.bound_box]
    return [[min(p[i] for p in points) for i in range(3)],[max(p[i] for p in points) for i in range(3)]]

narrow=bpy.data.objects.get('B11_K-NARROW-OUTER-320')
assert narrow is not None,'Missing human-confirmed 320 mm outer narrow cabinet'
nb=bounds(descendants(narrow))
fb=bounds(descendants(bpy.data.objects['B11_K-FRIDGE']))
hb=bounds(descendants(bpy.data.objects['B11_K-FRIDGE-OVERHEAD']))
ib=bounds(descendants(bpy.data.objects['B11_K-TALL-L']))
assert nb[0][0]<nb[1][0]<=fb[0][0]+1e-5,'Narrow cabinet must be outside refrigerator nearest door'
assert fb[1][0]<=ib[0][0]+1e-5,'Refrigerator column must be outside high-cabinet/niche column'
assert abs((nb[1][0]-nb[0][0])-.320)<1e-5,'Narrow cabinet width must be 320 mm'
assert abs((nb[1][1]-nb[0][1])-.765)<1e-5,'Review narrow depth must be 765 mm (760–770 range)'
assert abs(nb[0][1]-fb[0][1])<1e-5,'Narrow and refrigerator fronts must be coplanar'
assert abs((fb[1][1]-fb[0][1])-.710)<1e-5
assert abs(4.5-fb[1][1]-.055)<1e-5,'Refrigerator rear socket allowance must be 55 mm'
assert abs(hb[0][0]-fb[0][0])<1e-5 and abs(hb[1][0]-fb[1][0])<1e-5,'Overhead must remain over refrigerator column'
snapshot=json.loads((ROOT/'design/blender_b1_1/SOURCE_SCENE_SNAPSHOT.json').read_text())['branch']['objects']
def signature(o):
    h=hashlib.sha256()
    if o.type=='MESH':
        for v in o.data.vertices:h.update((','.join(format(c,'.9g') for c in v.co)+';').encode())
        for p in o.data.polygons:h.update((','.join(str(v) for v in p.vertices)+';').encode())
    else:h.update(o.type.encode())
    return h.hexdigest()
for record in snapshot:
    o=bpy.data.objects[record['name']]
    assert signature(o)==record['geometry_signature'],record['name']+' inherited mesh changed'
    assert max(abs(o.matrix_world[i][j]-record['matrix'][i][j]) for i in range(4) for j in range(4))<1e-7,record['name']+' inherited pose changed'
manifest=json.loads((ROOT/'design/blender_b0/B0_FREEZE_MANIFEST.json').read_text())
for key,expected in manifest['sha256'].items():
    assert hashlib.sha256((ROOT/manifest['files'][key]).read_bytes()).hexdigest()==expected,'B0_INTEGRITY mismatch '+key
result=dict(status='PASS',B0_INTEGRITY='PASS',source_objects_preserved=len(snapshot),
    order_from_door=['K-NARROW-OUTER-320','K-FRIDGE_AND_OVERHEAD','K-TALL-L_INNER_NICHE'],
    narrow_width_mm=(nb[1][0]-nb[0][0])*1000,narrow_depth_mm=(nb[1][1]-nb[0][1])*1000,
    front_plane_error_mm=abs(nb[0][1]-fb[0][1])*1000,rear_socket_gap_mm=(4.5-fb[1][1])*1000,
    bounds_m=dict(narrow=nb,fridge=fb,overhead=hb,inner_niche=ib),
    model_sha256=hashlib.sha256(model.read_bytes()).hexdigest())
(OUT/'KITCHEN_LOGIC_QA.json').write_text(json.dumps(result,ensure_ascii=False,indent=2))
print(json.dumps(result,ensure_ascii=False,indent=2))
