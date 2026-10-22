import bpy,json
from pathlib import Path
from mathutils import Vector
OUT=Path(__file__).resolve().parent/'r2'
OUT.mkdir(exist_ok=True)
BASE=OUT.parents[1]/'wall_corners_v5/HOUSE_BASE_GEOMETRY_V2_FROZEN.blend'
bpy.ops.wm.open_mainfile(filepath=str(BASE))
bpy.context.view_layer.update()
rows=[]
for o in bpy.data.objects:
 if o.type!='MESH':continue
 vs=[o.matrix_world@v.co for v in o.data.vertices]
 if not vs:continue
 lo=[min(v[i] for v in vs) for i in range(3)];hi=[max(v[i] for v in vs) for i in range(3)]
 if lo[0]<11.65 and hi[0]>8.8 and lo[1]<6.85 and hi[1]>3.75:
  rows.append(dict(name=o.name,lo=lo,hi=hi,hidden=[o.hide_render,o.hide_viewport,o.hide_get()],materials=[m.name for m in o.data.materials if m],collections=[c.name for c in o.users_collection],props={k:str(o[k]) for k in o.keys()},verts=len(vs)))
walls=[]
for o in bpy.data.objects:
 if o.type=='MESH' and (o.name=='V5_CONTINUOUS_WALL_SHELL' or o.name.startswith('V5_CORNER_PATCH_')):
  o.data.calc_loop_triangles();walls.append(dict(name=o.name,vertices=[list(o.matrix_world@v.co) for v in o.data.vertices],triangles=[list(t.vertices) for t in o.data.loop_triangles]))
(OUT/'BASE_INSPECTION.json').write_text(json.dumps(rows,ensure_ascii=False,indent=2))
(OUT/'BASE_WALLS.json').write_text(json.dumps(walls))
details={}
for o in bpy.data.objects:
 if o.type=='MESH' and ('D107' in o.name or o.name.startswith('B11_Rectangle038')):
  details[o.name]=[list(o.matrix_world@v.co) for v in o.data.vertices]
(OUT/'BASE_DETAIL_VERTICES.json').write_text(json.dumps(details))
print(json.dumps([r for r in rows if not r['hidden'][0] and (r['lo'][0]>8.7 or r['name'].startswith('V5'))],ensure_ascii=False))
