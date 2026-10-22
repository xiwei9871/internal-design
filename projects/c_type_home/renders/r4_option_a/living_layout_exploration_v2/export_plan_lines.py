import bpy,json,hashlib
from mathutils import Vector
from pathlib import Path
OUT=Path(__file__).resolve().parent
SRC=OUT.parents[2]/'design/bedroom_door_r4/OPTION_A_SLIDING_R4.blend'
bpy.ops.wm.open_mainfile(filepath=str(SRC));bpy.context.view_layer.update()
lines=[];z=1.15;zone=[2.9,7.8,7.0,14.1]
for o in bpy.data.objects:
 if o.type!='MESH' or o.hide_render or o.hide_viewport:continue
 n=o.name.upper();mn=' '.join(m.name.upper() for m in o.data.materials if m)
 if not any(w in n or w in mn for w in ['WALL','DOOR','JAMB','MULLION','FRAME']):continue
 pts=[o.matrix_world@Vector(c) for c in o.bound_box]
 if max(v.x for v in pts)<zone[0] or min(v.x for v in pts)>zone[1] or max(v.y for v in pts)<zone[2] or min(v.y for v in pts)>zone[3] or min(v.z for v in pts)>z or max(v.z for v in pts)<z:continue
 obj=o.evaluated_get(bpy.context.evaluated_depsgraph_get());m=obj.to_mesh();vs=[o.matrix_world@v.co for v in m.vertices]
 for poly in m.polygons:
  ids=list(poly.vertices);inter=[]
  for a,b in zip(ids,ids[1:]+ids[:1]):
   va,vb=vs[a],vs[b]
   if (va.z-z)*(vb.z-z)<0:
    v=va+(vb-va)*((z-va.z)/(vb.z-va.z));inter.append([round(v.x,5),round(v.y,5)])
  if len(inter)==2:lines.append(dict(source=o.name,points=inter))
 obj.to_mesh_clear()
(OUT/'reports/R4_PLAN_SECTION_LINES.json').write_text(json.dumps(dict(source=str(SRC),source_sha256=hashlib.sha256(SRC.read_bytes()).hexdigest(),z=z,lines=lines),ensure_ascii=False)+'\n');print('section_line_count',len(lines))
