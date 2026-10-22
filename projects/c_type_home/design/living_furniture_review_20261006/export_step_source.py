import bpy,json,sys
from pathlib import Path
from mathutils import Vector
sys.path.insert(0,'/Users/xiwei/.codex/worktrees/c-type-kitchen-pier/interior_design/projects/c_type_home/scripts')
from restore_kitchen_divider_pier import bounds
rows=[]
for name,level in [('R4_UPPER_FLOOR_CONTINUOUS_STRAIGHT_THRESHOLD',.45),('FLOOR_LOWER',0)]:
 o=bpy.data.objects[name];faces=[]
 for f in o.data.polygons:
  pts=[o.matrix_world@o.data.vertices[i].co for i in f.vertices]
  if max(abs(p.z-level) for p in pts)<1e-5 and f.normal.z>.9:faces.append([list(p) for p in pts])
 rows.append({'name':name,'faces':faces,'bounds':bounds(o)})
for o in bpy.context.scene.objects:
 if o.type=='MESH' and o.visible_get() and (o.name.startswith(('STEP_','B11_STEP_','B11_LEISURE_CURVE_TRIM')) or o.name=='FASCIA_PLATFORM_CURVE'):
  rows.append({'name':o.name,'bounds':bounds(o),'vertices':len(o.data.vertices)})
Path(__file__).with_suffix('.json').write_text(json.dumps(rows,indent=2));print(json.dumps([{k:v for k,v in row.items() if k!='faces'} for row in rows]))
