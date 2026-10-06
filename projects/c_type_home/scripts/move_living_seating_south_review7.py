"""Exact packet-selected three-object translation, source south=-Y; new derived review only."""
import bpy,json,sys
from pathlib import Path
from mathutils import Vector,Matrix
from mathutils.bvhtree import BVHTree
sys.path.insert(0,str(Path(__file__).parent))
from restore_kitchen_divider_pier import sha,object_state,bounds
r=Path('/Users/xiwei/interior_design/projects/c_type_home/design/living_fitness_reading_review_20261006')
source=r/'OPTION_A_R4_BOOKCASE_SHORT_RAIL_REVIEW_6.blend'
output=r/'OPTION_A_R4_SEATING_SOUTH_1M_REVIEW_7.blend'
expected='e428fbedc2aeaf6f35d530c4dd33bbb61057a70eaede4d99683f376883360e05'
assert sha(source)==expected
registry=json.loads((r/'spatial-canvas.bindings.review6.json').read_text())
selected={
 'B11_Rectangle046_CATALOG_00_00':'ent_d25c02916e634c6b810c2d13e29a9a62',
 'B11_Circle_CATALOG_00_00':'ent_d7c82245358e4d1dbc1dc644c11322e9',
 'B11_Rectangle049_CATALOG_00_00':'ent_58cf3a9dc50143578ee3d8cfd272c045'}
for name,gid in selected.items():assert any(b['native_id']==name and b['entity_id']==gid for b in registry['bindings'])
bpy.ops.wm.open_mainfile(filepath=str(source))
prior={o.name:object_state(o) for o in bpy.context.scene.objects}
objects=[bpy.data.objects[name] for name in selected]
before={o.name:bounds(o) for o in objects}
for o in objects:o.matrix_world=Matrix.Translation((0,-1,0))@o.matrix_world
bpy.context.view_layer.update()
after={o.name:bounds(o) for o in objects}
for name,state in prior.items():
    now=object_state(bpy.data.objects[name])
    if name not in selected:assert now==state,name
    else:
        assert all(now[k]==state[k] for k in state if k!='matrix'),name
        for side in range(2):
            assert abs(after[name][side][0]-before[name][side][0])<1e-5
            assert abs(after[name][side][1]-before[name][side][1]+1)<1e-5
            assert abs(after[name][side][2]-before[name][side][2])<1e-5
floor=bpy.data.objects['FLOOR_LOWER']
for o in objects:
    lo,hi=bounds(o)
    for x in [lo[0]+.03,hi[0]-.03]:
        for y in [lo[1]+.03,hi[1]-.03]:
            # Sofa envelope includes the empty L bay, but every tested point still lies on valid floor.
            hit,p,n,index=floor.ray_cast(floor.matrix_world.inverted()@Vector((x,y,1)),Vector((0,0,-1)))
            assert hit and abs(p.z)<1e-5,(o.name,x,y)
def tree(o):
    return BVHTree.FromPolygons([tuple(o.matrix_world@v.co) for v in o.data.vertices],[list(p.vertices) for p in o.data.polygons],epsilon=1e-7)
obstacle_names=['STEP_0','STEP_1','STEP_2','WAVE_WALL_HANDRAIL_900','WAVE_HANDRAIL_LOWER_POST','READING_3205A_PADDED_BENCH','READING_5015_SHORT_SLIDING_CABINET']
index=json.loads((r.parent/'wall_identity_r4_review/WALL_PART_INDEX.json').read_text())
# Narrow collision candidates from the existing wall identity index, never rediscover scene identity.
for part in index['parts']:
    lo,hi=part['world_bounds']
    if hi[0]>=3.3 and lo[0]<=5.7 and hi[1]>=7.9 and lo[1]<=11.84 and lo[2]<.8:
        obstacle_names.append(part['native_id'])
obstacles=[bpy.data.objects[n] for n in obstacle_names]
collisions=[]
for i,o in enumerate(objects):
    t=tree(o)
    for other in obstacles+objects[:i]:
        if t.overlap(tree(other)):collisions.append([o.name,other.name])
assert not collisions,collisions
registry.update(registry_revision='17-seating-south-1m-review',source_revision='r4-seating-south-1m-review-7',source_locator=str(output))
bpy.ops.wm.save_as_mainfile(filepath=str(output));registry['source_sha256']=sha(output)
(r/'spatial-canvas.bindings.review7.json').write_text(json.dumps(registry,ensure_ascii=False,indent=2)+'\n')
saved={o.name:object_state(o) for o in bpy.context.scene.objects}
bpy.ops.wm.open_mainfile(filepath=str(output));assert all(object_state(bpy.data.objects[n])==state for n,state in saved.items())
assert sha(source)==expected
frozen=Path('/Users/xiwei/interior_design/projects/c_type_home/design/bedroom_door_r4/OPTION_A_SLIDING_R4.blend')
assert sha(frozen)=='d109c7efcfa2b2b2565e4c073ee0cdf5282b23c01122bc9c1bbe7b8791ac3afb'
report={'status':'HUMAN_REVIEW','source':str(source),'source_sha256':expected,'output':str(output),'output_sha256':sha(output),'revision':registry['source_revision'],'selected_native_global_ids':selected,'translation_source_xyz_m':[0,-1,0],'translation_proxy_xyz_m':[0,0,1],'before':before,'after':after,'all_other_object_states_unchanged':True,'no_surface_intersections':True,'named_collision_candidates':obstacle_names,'actual_floor_below_moved_envelopes':True,'fresh_reopen_verified':True,'north_sofa_edge_before_y':before['B11_Rectangle046_CATALOG_00_00'][1][1],'north_sofa_edge_after_y':after['B11_Rectangle046_CATALOG_00_00'][1][1],'source_and_frozen_r4_unchanged':True}
(r/'SEATING_SOUTH_REVIEW7_QA.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({k:v for k,v in report.items() if k not in ['before','after','named_collision_candidates']},ensure_ascii=False))
