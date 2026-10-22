import bpy,json
from mathutils import Vector
from pathlib import Path
r=Path(__file__).parent
bpy.ops.wm.open_mainfile(filepath=str(r/'OPTION_A_R4_THREE_STEP_READING_FITNESS_REVIEW_5.blend'))
names=['B11_G-DIN-LIV_HOST_GLASS2','B11_G-DIN-LIV_HOST_GLASS0','B11_G-DIN-LIV_HOST_GLASS1','READING_5015_SHORT_SLIDING_CABINET','FLOOR_LOWER']
rows=[]
for n in names:
 o=bpy.data.objects[n];pts=[o.matrix_world@v.co for v in o.data.vertices]
 rows.append({'name':n,'bounds':[[min(p[i] for p in pts) for i in range(3)],[max(p[i] for p in pts) for i in range(3)]]})
print(json.dumps(rows))
