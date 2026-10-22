import bpy,json,hashlib
from pathlib import Path
S=Path('/Users/xiwei/.codex/worktrees/c-type-study-daybed/interior_design/projects/c_type_home/design/glass_visibility_v9/WHOLE_HOUSE_GLASS_VISIBILITY_V9.blend');assert hashlib.sha256(S.read_bytes()).hexdigest()=='42beee4cb51bce1487edbe0003b226951986ca073b2d2e3b4ffec9305c80f9cf';bpy.ops.wm.open_mainfile(filepath=str(S))
for c in bpy.data.collections:c.hide_viewport=False
for o in bpy.data.objects:o.hide_viewport=False;o.hide_set(False)
bpy.context.view_layer.update();names=['VIEW_WALL_R3_WEST_PARTITION','VIEW_WALL_LIVING_FIX_GUEST_BATH_FULL_WALL'];selected=[]
for o in bpy.data.objects:
 if o.type=='MESH' and not o.hide_render and (o.name in names or o.name.startswith(('READING_5015_','READING_DISPLAY_','READING_BOOK_','HOUSE_V2_Book_','HOUSE_V1_READING_WALL_CLEAT','WAVE_','SHORT_THREE_STEP','STEP_','R4_BEDROOM_DOOR','R4_DOOR_FRAME','R3_'))):
  vs=[o.matrix_world@v.co for v in o.data.vertices];lo=[min(v[i] for v in vs) for i in range(3)];hi=[max(v[i] for v in vs) for i in range(3)]
  if o.name.startswith('R3_') and not (lo[0]<9.7 and hi[0]>7.8 and lo[1]<6.8 and hi[1]>4.2):continue
  selected.append({'name':o.name,'bounds':[lo,hi],'location':list(o.location),'parent':o.parent.name if o.parent else None,'collections':[c.name for c in o.users_collection]})
D=Path('/Users/xiwei/.codex/worktrees/c-type-study-daybed/interior_design/projects/c_type_home/design/reading_wall_v10');D.mkdir(exist_ok=True);(D/'TARGET_INSPECTION.json').write_text(json.dumps(selected,indent=2))
for o in selected:print(o['name'],[[round(v,4) for v in p] for p in o['bounds']],o['parent'])
