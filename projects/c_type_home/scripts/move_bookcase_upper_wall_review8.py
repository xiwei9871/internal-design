"""Owner correction: existing bookcase on upper landing at exact opaque wall, clear sliding door."""
import bpy,json,sys
from pathlib import Path
from mathutils import Vector,Matrix
from mathutils.bvhtree import BVHTree
sys.path.insert(0,str(Path(__file__).parent))
from restore_kitchen_divider_pier import sha,object_state,bounds
r=Path('/Users/xiwei/interior_design/projects/c_type_home/design/living_fitness_reading_review_20261006')
source=r/'OPTION_A_R4_SEATING_SOUTH_1M_REVIEW_7.blend'
output=r/'OPTION_A_R4_BOOKCASE_UPPER_WALL_REVIEW_8.blend'
expected='eec08addcab7a805756a201a1ec61d7ac6508dfcd27cdb61c5d3e1c2f8dbd354'
assert sha(source)==expected
bpy.ops.wm.open_mainfile(filepath=str(source))
prior={o.name:object_state(o) for o in bpy.context.scene.objects}
group=[o for o in bpy.context.scene.objects if o.name.startswith(('READING_5015_','READING_DISPLAY_SIDE_POST','READING_BOOK_'))]
assert len(group)==10
cab=bpy.data.objects['READING_5015_SHORT_SLIDING_CABINET'];lo,hi=bounds(cab)
wall_name='VIEW_WALL_W_wall_md_0044';wall=bpy.data.objects[wall_name];wlo,whi=bounds(wall)
width=hi[0]-lo[0];depth=hi[1]-lo[1]
# Align within solid wall span, leave60mm at its east end, and30mm behind freestanding unit.
target_hit_x=7.393119968136012
center_x=min(target_hit_x,whi[0]-.06-width/2)
back_y=whi[1]+.03
old_center=Vector(((lo[0]+hi[0])/2,(lo[1]+hi[1])/2,lo[2]))
new_center=Vector((center_x,back_y+depth/2,.45))
translation=new_center-old_center
before={o.name:bounds(o) for o in group}
for o in group:o.matrix_world=Matrix.Translation(translation)@o.matrix_world
bpy.context.view_layer.update()
after={o.name:bounds(o) for o in group}
for name,state in prior.items():
    now=object_state(bpy.data.objects[name])
    if name not in after:assert now==state,name
    else:assert all(now[k]==state[k] for k in state if k!='matrix'),name
newlo,newhi=bounds(cab)
assert abs(newlo[2]-.45)<1e-5
assert newlo[0]>=wlo[0] and newhi[0]<=whi[0]-.0599
assert abs(newlo[1]-back_y)<1e-5
# Verify every cabinet footprint corner lies on the actual +450mm upper mesh, not a tread or void.
upper=bpy.data.objects['R4_UPPER_FLOOR_CONTINUOUS_STRAIGHT_THRESHOLD']
floor_checks=[]
for x in [newlo[0]+.006,newhi[0]-.006]:
    for y in [newlo[1]+.006,newhi[1]-.006]:
        hit,p,n,face=upper.ray_cast(upper.matrix_world.inverted()@Vector((x,y,1)),Vector((0,0,-1)))
        assert hit and abs(p.z-.45)<1e-5,(x,y)
        floor_checks.append([x,y,p.z])
def tree(o):
    return BVHTree.FromPolygons([tuple(o.matrix_world@v.co) for v in o.data.vertices],[list(p.vertices) for p in o.data.polygons],epsilon=1e-7)
names=['VIEW_WALL_W_wall_md_0044','B11_G-DIN-LIV_HOST_GLASS2','STEP_0','STEP_1','STEP_2','WAVE_WALL_HANDRAIL_900','WAVE_HANDRAIL_LOWER_POST','WAVE_HANDRAIL_UPPER_RETURN','READING_3205A_PADDED_BENCH']
idx=json.loads((r.parent/'wall_identity_r4_review/WALL_PART_INDEX.json').read_text())
for part in idx['parts']:
    a,b=part['world_bounds']
    if b[0]>=newlo[0] and a[0]<=newhi[0] and b[1]>=newlo[1] and a[1]<=newhi[1] and a[2]<2:
        names.append(part['native_id'])
collisions=[]
for o in group:
    for name in set(names):
        if tree(o).overlap(tree(bpy.data.objects[name])):collisions.append([o.name,name])
assert not collisions,collisions
registry=json.loads((r/'spatial-canvas.bindings.review7.json').read_text())
registry.update(registry_revision='18-bookcase-upper-solid-wall',source_revision='r4-bookcase-upper-wall-review-8',source_locator=str(output))
bpy.ops.wm.save_as_mainfile(filepath=str(output));registry['source_sha256']=sha(output)
(r/'spatial-canvas.bindings.review8.json').write_text(json.dumps(registry,ensure_ascii=False,indent=2)+'\n')
saved={o.name:object_state(o) for o in bpy.context.scene.objects}
bpy.ops.wm.open_mainfile(filepath=str(output));assert all(object_state(bpy.data.objects[n])==state for n,state in saved.items())
assert sha(source)==expected
frozen=Path('/Users/xiwei/interior_design/projects/c_type_home/design/bedroom_door_r4/OPTION_A_SLIDING_R4.blend')
assert sha(frozen)=='d109c7efcfa2b2b2565e4c073ee0cdf5282b23c01122bc9c1bbe7b8791ac3afb'
report={'status':'HUMAN_REVIEW','source':str(source),'source_sha256':expected,'output':str(output),'output_sha256':sha(output),'target_wall_native_id':wall_name,'target_wall_global_id':'ent_292295d05e83519f93bf6c9fed39d766','bookcase_base_z_m':.45,'wall_back_gap_m':.03,'east_end_clearance_m':.06,'translation_source_xyz_m':list(translation),'before':before,'after':after,'moved_native_ids':list(after),'actual_upper_floor_corner_checks':floor_checks,'all_other_object_states_unchanged':True,'no_surface_intersections':True,'sliding_door_panel_unchanged_and_cabinet_removed_from_its_front':True,'source_review7_and_frozen_r4_unchanged':True,'fresh_reopen_verified':True}
(r/'BOOKCASE_UPPER_WALL_REVIEW8_QA.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({k:v for k,v in report.items() if k not in ['before','after']},ensure_ascii=False))
