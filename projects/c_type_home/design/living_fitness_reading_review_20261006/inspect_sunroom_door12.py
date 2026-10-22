import bpy,json
from pathlib import Path
from mathutils import Vector
r=Path(__file__).parent
bpy.ops.wm.open_mainfile(filepath=str(r/'OPTION_A_R4_BALCONY_SUNROOM_REVIEW_11.blend'))
bpy.context.view_layer.update()
names=['V4_GUEST_B11_G-GB-BALC_HOST_GLASS0','V4_GUEST_B11_G-GB-BALC_HOST_GLASS1','VIEW_WALL_W_wall_md_0054','VIEW_WALL_W_wall_md_0055','B11_Rectangle040_BODY_0','SUNROOM_LAUNDRY_FOLDING_BASE','SUNROOM_LAUNDRY_SHALLOW_UPPER','SUNROOM_SUN_SEAT_BASE']
rows=[]
for n in names:
 o=bpy.data.objects[n];p=[o.matrix_world@v.co for v in o.data.vertices];rows.append({'name':n,'bounds':[[min(v[i] for v in p) for i in range(3)],[max(v[i] for v in p) for i in range(3)]]})
print(json.dumps(rows));(r/'SUNROOM_DOOR12_BOUNDS.json').write_text(json.dumps(rows,indent=2))
