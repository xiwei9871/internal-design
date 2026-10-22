import bpy,json,hashlib
from pathlib import Path
from mathutils import Vector
source=Path('/Users/xiwei/interior_design/projects/c_type_home/design/bedroom_door_r4/OPTION_A_SLIDING_R4.blend')
out=Path('/Users/xiwei/interior_design/projects/c_type_home/design/kitchen_divider_r4_review')
before={'sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'size':source.stat().st_size,'mtime_ns':str(source.stat().st_mtime_ns)}
assert before['sha256']=='d109c7efcfa2b2b2565e4c073ee0cdf5282b23c01122bc9c1bbe7b8791ac3afb'
bpy.ops.wm.open_mainfile(filepath=str(source));deps=bpy.context.evaluated_depsgraph_get()
rows=[]
for obj in bpy.context.scene.objects:
 if obj.type!='MESH':continue
 ev=obj.evaluated_get(deps);verts=[ev.matrix_world@Vector(c) for c in ev.bound_box];lo=[min(v[i] for v in verts) for i in range(3)];hi=[max(v[i] for v in verts) for i in range(3)]
 target=obj.name in ['B11_K-ISLAND_CONNECTOR_COUNTER','B11_K-UTILITY_UPPER_DOOR_1']
 in_gap=lo[0]<5.94 and hi[0]>5.55 and lo[1]<1.6 and hi[1]>.45 and hi[2]>.98
 if not(target or in_gap):continue
 row={'name':obj.name,'bounds':[lo,hi],'visible':obj.visible_get(),'hide_render':obj.hide_render,'hide_set':obj.hide_get(),'collections':[{'name':c.name,'hide_render':c.hide_render,'hide_viewport':c.hide_viewport} for c in obj.users_collection],'properties':dict(obj.items())}
 rows.append(row)
assert hashlib.sha256(source.read_bytes()).hexdigest()==before['sha256'] and str(source.stat().st_mtime_ns)==before['mtime_ns']
(out/'r4-pier-inspection.json').write_text(json.dumps({'source':before,'objects':rows},ensure_ascii=False,indent=2,default=str)+'\n')
print(json.dumps({'objects':rows},ensure_ascii=False,default=str))
