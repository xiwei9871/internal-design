import bpy,json
from pathlib import Path
from mathutils import Vector
r=Path(__file__).parent
bpy.ops.wm.open_mainfile(filepath=str(r/'OPTION_A_R4_LONG_SIDE_CABINET_CHAISE_SOUTH_REVIEW_10.blend'))
bpy.context.view_layer.update()
names=['B11_Rectangle039_BODY','B11_Rectangle039_LID_SEAM','B11_Rectangle040_BODY_0','B11_Rectangle040_DOOR_0','B11_Rectangle040_BODY_1','B11_Rectangle040_DOOR_1','B11_Rectangle007_JAMB_0','B11_Rectangle007_JAMB_1','B11_Rectangle007_GLASS_0','B11_Rectangle007_GLASS_1','B11_Rectangle007_GLASS_2','DOOR_V2_NBALC_SINGLE_GLASS','DOOR_V2_NBALC_FRAME_NORTH_JAMB','DOOR_V2_NBALC_FRAME_SOUTH_JAMB','DOOR_V2_NBALC_HANDLE_LEVER','VIEW_WALL_W_wall_md_0054','VIEW_WALL_W_wall_md_0055','VIEW_WALL_W_wall_md_0062','VIEW_WALL_W_wall_md_0026','FLOOR_LOWER']
rows=[]
for name in names:
 o=bpy.data.objects[name];pts=[o.matrix_world@v.co for v in o.data.vertices]
 rows.append({'name':name,'bounds':[[min(p[i] for p in pts) for i in range(3)],[max(p[i] for p in pts) for i in range(3)]],'parent':o.parent.name if o.parent else None,'children':[x.name for x in o.children]})
(r/'BALCONY_NAMED_BOUNDS.json').write_text(json.dumps(rows,indent=2));print(json.dumps(rows))
