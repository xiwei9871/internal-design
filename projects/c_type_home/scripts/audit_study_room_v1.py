import bpy,json
from pathlib import Path
from mathutils import Vector
R=Path(__file__).resolve().parents[1]/'design/study_room_v1'
SRC='/Users/xiwei/interior_design/projects/c_type_home/design/living_fitness_reading_review_20261006/OPTION_A_R4_SUNROOM_INTEGRATED_LAUNDRY_REVIEW_14.blend'
bpy.ops.wm.open_mainfile(filepath=SRC);bpy.context.view_layer.update()
rows=[]
# Named study furniture, its current door host and bay-window; no house scan.
names=[o.name for o in bpy.data.objects if o.name.startswith(('R3_STUDY_','R3_TEA_','V4_W-STUDY','VIEW_WALL_V4_W-STUDY','V4_D-STUDY','VIEW_WALL_V4_D-STUDY'))]
names+=['VIEW_WALL_W_wall_md_0056','VIEW_WALL_W_wall_md_0057','VIEW_WALL_W_wall_md_0004','FLOOR_UPPER','B11_Rectangle024','B11_Rectangle025','B11_Rectangle026','R3_STUDY_HOST']
for n in names:
 o=bpy.data.objects.get(n)
 if not o:continue
 if o.type=='MESH':
  c=[o.matrix_world@v.co for v in o.data.vertices]
 else:c=[o.matrix_world@Vector(v) for v in o.bound_box]
 if not c:c=[o.matrix_world.translation]
 rows.append({'name':n,'type':o.type,'bounds':[[min(v[i] for v in c) for i in range(3)],[max(v[i] for v in c) for i in range(3)]],'parent':o.parent.name if o.parent else None,'active':not o.hide_render and not o.hide_viewport,'vertices':len(o.data.vertices) if o.type=='MESH' else 0})
(R/'STUDY_BOUNDED_OBJECTS.json').write_text(json.dumps(rows,ensure_ascii=False,indent=2))
print('BOUNDED',len(rows),json.dumps([r for r in rows if r['active']],ensure_ascii=False))

