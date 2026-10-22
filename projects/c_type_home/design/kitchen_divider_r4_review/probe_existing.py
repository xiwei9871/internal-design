import bpy,json
from pathlib import Path
from mathutils import Vector
source='/Users/xiwei/interior_design/projects/c_type_home/design/bedroom_door_r4/OPTION_A_SLIDING_R4.blend'
bpy.ops.wm.open_mainfile(filepath=source)
shell=bpy.data.objects['R3_HOUSE_WALLS_D107_ROLLED_BACK'];shell_eval=shell.evaluated_get(bpy.context.evaluated_depsgraph_get())
rows=[]
for y in [.55,.85,1.10,1.20]:
 inv=shell_eval.matrix_world.inverted();hit,loc,normal,face=shell_eval.ray_cast(inv@Vector((5.75,y,4)),(inv.to_3x3()@Vector((0,0,-1))).normalized(),distance=6)
 rows.append({'x':5.75,'y':y,'top_ray_hits_existing_shell':hit,'hit_world':list(shell_eval.matrix_world@loc) if hit else None})
print(json.dumps(rows));Path('/Users/xiwei/interior_design/projects/c_type_home/design/kitchen_divider_r4_review/existing-rays.json').write_text(json.dumps(rows,indent=2)+'\n')
