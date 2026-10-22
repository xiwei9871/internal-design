import bpy,json
from pathlib import Path
from mathutils import Vector
OUT=Path(__file__).resolve().parent
bpy.ops.wm.open_mainfile(filepath=str(OUT/'OPTION_A_SLIDING_R4.blend'));bpy.context.view_layer.update();rows=[]
for o in bpy.data.objects:
 if o.type!='MESH' or o.hide_render or o.hide_viewport:continue
 vs=[o.matrix_world@v.co for v in o.data.vertices]
 if not vs:continue
 lo=[min(v[i] for v in vs) for i in range(3)];hi=[max(v[i] for v in vs) for i in range(3)]
 if lo[0]>9.3 or hi[0]<8.05 or lo[1]>4.86 or hi[1]<4.35 or lo[2]>.56 or hi[2]<.40:continue
 faces=[]
 for f in o.data.polygons:
  points=[o.matrix_world@o.data.vertices[i].co for i in f.vertices]
  if min(p.x for p in points)>9.3 or max(p.x for p in points)<8.05 or min(p.y for p in points)>4.86 or max(p.y for p in points)<4.35:continue
  if not any(.40<=p.z<=.56 for p in points):continue
  faces.append(dict(index=f.index,vertices=[list(p) for p in points],normal=list(f.normal)))
 rows.append(dict(name=o.name,lo=lo,hi=hi,faces=faces))
(OUT/'THRESHOLD_ACTUAL_GEOMETRY_DEBUG.json').write_text(json.dumps(rows,ensure_ascii=False,indent=2)+'\n')
o=bpy.data.objects['FLOOR_UPPER']
(OUT/'UPPER_FLOOR_FULL_SOURCE.json').write_text(json.dumps(dict(name=o.name,faces=[dict(index=f.index,vertices=[list(o.matrix_world@o.data.vertices[i].co) for i in f.vertices],normal=list(f.normal)) for f in o.data.polygons]),ensure_ascii=False)+'\n')
print(json.dumps([dict(name=r['name'],lo=r['lo'],hi=r['hi'],local_faces=len(r['faces'])) for r in rows],ensure_ascii=False))
