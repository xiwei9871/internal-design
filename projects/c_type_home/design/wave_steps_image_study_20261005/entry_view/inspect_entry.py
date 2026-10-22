import bpy,json,sys
from mathutils import Vector
from pathlib import Path
sys.path.insert(0,'/Users/xiwei/.codex/worktrees/c-type-kitchen-pier/interior_design/projects/c_type_home/scripts')
from restore_kitchen_divider_pier import bounds
records=[]
for o in bpy.context.scene.objects:
 if o.type=='CAMERA':records.append({'camera':o.name,'location':list(o.location),'rotation':list(o.rotation_euler),'lens':o.data.lens})
 elif o.type=='MESH' and o.visible_get():
  b=bounds(o)
  if b[1][0]<3.1 and b[0][1]<8.3 and b[1][1]>4.3:
   records.append({'name':o.name,'bounds':b,'props':dict(o.items())})
for n in ['R4_UPPER_FLOOR_CONTINUOUS_STRAIGHT_THRESHOLD','STEP_0','STEP_1','STEP_2']:
 o=bpy.data.objects[n];records.append({'selected':n,'bounds':bounds(o)})
p=Path(__file__).parent/'ENTRY_INSPECTION.json';p.write_text(json.dumps(records,ensure_ascii=False,default=str,indent=2));print(json.dumps(records,ensure_ascii=False,default=str))
