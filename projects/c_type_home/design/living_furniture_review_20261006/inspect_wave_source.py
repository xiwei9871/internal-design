import bpy,json
from pathlib import Path
src='/Users/xiwei/interior_design/projects/c_type_home/design/living_furniture_review_20261006/OPTION_A_R4_LIVING_FURNITURE_REVIEW.blend'
bpy.ops.wm.open_mainfile(filepath=src)
names=['FLOOR_LOWER','R4_UPPER_FLOOR_CONTINUOUS_STRAIGHT_THRESHOLD','STEP_0','STEP_1','STEP_2','FASCIA_PLATFORM_CURVE']
wall_names=['VIEW_WALL_W_wall_md_0026','VIEW_WALL_W_wall_md_0062','VIEW_WALL_W_wall_md_0061','VIEW_WALL_DOOR_V2_NBALC_SOLID_ABOVE_DOOR','VIEW_WALL_W_wall_md_0055']
rows=[]
for o in bpy.context.scene.objects:
 if any(n in o.name for n in names) or o.name in wall_names:
  cs=[o.matrix_world@__import__('mathutils').Vector(c) for c in o.bound_box];rows.append({'name':o.name,'type':o.type,'hide':o.hide_viewport,'dims':list(o.dimensions),'loc':list(o.location),'min':[min(v[i] for v in cs) for i in range(3)],'max':[max(v[i] for v in cs) for i in range(3)],'props':{k:str(o[k]) for k in o.keys() if k in ['global_id','native_id','semantic_type']}})
Path('/Users/xiwei/interior_design/projects/c_type_home/design/living_furniture_review_20261006/SOURCE_INSPECT.json').write_text(json.dumps(rows,indent=2))
print(json.dumps(rows))
