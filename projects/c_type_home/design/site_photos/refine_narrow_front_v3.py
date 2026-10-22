"""Align the narrow cabinet top row with fridge overhead fronts; divide lower part in three."""
import bpy
import hashlib
import json
from pathlib import Path
from mathutils import Vector

OUT=Path(__file__).resolve().parent
ROOT=OUT.parents[1]
SOURCE=OUT/'B1_1_SITE_CORRECTED_V2.blend'
MODEL=OUT/'B1_1_SITE_CORRECTED_V3.blend'
source_hash=hashlib.sha256(SOURCE.read_bytes()).hexdigest()
freeze=json.loads((ROOT/'design/blender_b0/B0_FREEZE_MANIFEST.json').read_text())
for key,expected in freeze['sha256'].items():
    assert hashlib.sha256((ROOT/freeze['files'][key]).read_bytes()).hexdigest()==expected
bpy.ops.wm.open_mainfile(filepath=str(SOURCE));bpy.context.view_layer.update()
root=bpy.data.objects['B11_K-NARROW-OUTER-320']
prefix=root.name+'_'
def mutable(name):
    return name.startswith(prefix) and any(name[len(prefix):].startswith(part) for part in ['FRONT_','RECESSED_PULL_','SHELF_'])
def signature(o):
    h=hashlib.sha256()
    if o.type=='MESH':
        for v in o.data.vertices:h.update((','.join(format(c,'.9g') for c in v.co)+';').encode())
        for f in o.data.polygons:h.update((','.join(str(v) for v in f.vertices)+';').encode())
    else:h.update(o.type.encode())
    return h.hexdigest()
def authored_pose(o):
    return dict(location=list(o.location),rotation=list(o.rotation_euler),scale=list(o.scale),parent=o.parent.name if o.parent else None)
protected={o.name:dict(signature=signature(o),pose=authored_pose(o)) for o in bpy.data.objects if not mutable(o.name)}
def bounds(objects):
    p=[o.matrix_world@Vector(v) for o in objects for v in o.bound_box]
    return [[min(v[i] for v in p) for i in range(3)],[max(v[i] for v in p) for i in range(3)]]

envelope_before=bounds([o for o in root.children_recursive if o.type=='MESH'])
overhead_fronts=[o for o in bpy.data.objects if o.name.startswith('B11_K-FRIDGE-OVERHEAD_FRONT_')]
reference=bounds(overhead_fronts)
top_front_min=reference[0][2];top_front_max=reference[1][2]
gap=.002
base=.080
top_split=top_front_min-gap
step=(top_split-base)/3
levels=[base,base+step,base+2*step,top_split]
for o in list(root.children_recursive):
    if mutable(o.name):bpy.data.objects.remove(o,do_unlink=True)
col=root.users_collection[0]
x0,x1=envelope_before[0][0],envelope_before[1][0]
y0,y1=envelope_before[0][1],envelope_before[1][1]
t=.018
M_FRONT=bpy.data.materials['B11_REVIEW_FRONT'];M_BODY=bpy.data.materials['B11_REVIEW_BODY'];M_METAL=bpy.data.materials['B11_REVIEW_METAL']
new_parts=[]
def box(label,lo,hi,mat):
    bpy.ops.mesh.primitive_cube_add(size=1,location=[(lo[i]+hi[i])/2 for i in range(3)])
    o=bpy.context.object;o.name=prefix+label;o.dimensions=[hi[i]-lo[i] for i in range(3)]
    bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
    for c in list(o.users_collection):c.objects.unlink(o)
    col.objects.link(o);o.parent=root;o.data.materials.append(mat);o.color=mat.diffuse_color
    b=o.modifiers.new('Review panel edges','BEVEL');b.width=.0015;b.segments=2
    o.modifiers.new('Review normals','WEIGHTED_NORMAL')
    o['physical_ground_truth']=False;o['authority']='CURRENT_HUMAN_CONFIRMED_DOOR_ROW_RELATION'
    new_parts.append(o);return o
for n,(a,b) in enumerate(zip(levels,levels[1:])):
    box(f'FRONT_{n}',[x0+gap,y0,a+gap],[x1-gap,y0+t,b-gap],M_FRONT)
    box(f'RECESSED_PULL_{n}',[x0+.025,y0+.001,a+.025],[x1-.025,y0+.004,a+.035],M_METAL)
    if n:box(f'SHELF_{n}',[x0+t,y0+t,a-t],[x1-t,y1-t,a],M_BODY)
box('FRONT_3',[x0+gap,y0,top_front_min],[x1-gap,y0+t,top_front_max],M_FRONT)
box('RECESSED_PULL_3',[x0+.025,y0+.001,top_front_min+.025],[x1-.025,y0+.004,top_front_min+.035],M_METAL)
box('SHELF_3',[x0+t,y0+t,top_split-t],[x1-t,y1-t,top_split],M_BODY)
root['front_partition_count']=4;root['top_row_alignment']='MATCH_FRIDGE_OVERHEAD_FRONT_LOWER_AND_UPPER_EDGES'
root['lower_three_rows']='EQUAL_REVIEW_SUBDIVISION';root['top_front_z_m']=[top_front_min,top_front_max]
bpy.context.view_layer.update()
after=bounds([o for o in root.children_recursive if o.type=='MESH'])
assert max(abs(after[i][j]-envelope_before[i][j]) for i in range(2) for j in range(3))<1e-5
for name,record in protected.items():
    o=bpy.data.objects[name]
    assert signature(o)==record['signature'],'Unrelated geometry changed '+name
    assert authored_pose(o)==record['pose'],'Unrelated authored pose changed '+name
top=bounds([bpy.data.objects[prefix+'FRONT_3']])
low=[bounds([bpy.data.objects[prefix+f'FRONT_{n}']]) for n in range(3)]
heights=[(b[1][2]-b[0][2])*1000 for b in low]
assert abs(top[0][2]-top_front_min)<1e-5 and abs(top[1][2]-top_front_max)<1e-5
assert max(heights)-min(heights)<.01
assert hashlib.sha256(SOURCE.read_bytes()).hexdigest()==source_hash
for key,expected in freeze['sha256'].items():
    assert hashlib.sha256((ROOT/freeze['files'][key]).read_bytes()).hexdigest()==expected
register=dict(status='HUMAN_REVIEW',authority='USER: top row parallel/aligned to overhead; other three near equal',
    cabinet=root.name,front_count=4,reference_objects=[o.name for o in overhead_fronts],
    top_front_bounds_m=top,reference_front_bounds_m=reference,lower_front_heights_mm=heights,
    partition_z_m=levels,unchanged_envelope_m=after,unrelated_objects_preserved=len(protected),
    source_sha256=source_hash,new_parts=[o.name for o in new_parts],B0_INTEGRITY='PASS')
bpy.context.scene['B1_SITE_CORRECTION']='HUMAN_REVIEW'
bpy.context.scene['latest_refinement']='NARROW_FRONT_FOUR_ROWS; TOP_MATCHES_FRIDGE_OVERHEAD; LOWER_THREE_EQUAL'
bpy.ops.wm.save_as_mainfile(filepath=str(MODEL))
register['model_sha256']=hashlib.sha256(MODEL.read_bytes()).hexdigest()
(OUT/'NARROW_FRONT_REFINEMENT_V03.json').write_text(json.dumps(register,ensure_ascii=False,indent=2))
print(json.dumps({k:register[k] for k in ['front_count','lower_front_heights_mm','unrelated_objects_preserved','B0_INTEGRITY','model_sha256']},indent=2))
