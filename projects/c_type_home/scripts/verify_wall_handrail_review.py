import bpy,json,hashlib,math,sys
from pathlib import Path
from mathutils import Vector
sys.path.insert(0,str(Path(__file__).parent))
from restore_kitchen_divider_pier import object_state
r=Path('/Users/xiwei/interior_design/projects/c_type_home/design/living_furniture_review_20261006')
source=r/'OPTION_A_R4_LIVING_WAVE35_ALUMINUM_FIT_REVIEW_2.blend';output=r/'OPTION_A_R4_WAVE35_HANDRAIL_REVIEW_3.blend'
bpy.ops.wm.open_mainfile(filepath=str(source));prior={o.name:object_state(o) for o in bpy.context.scene.objects}
bpy.ops.wm.open_mainfile(filepath=str(output))
assert all(object_state(bpy.data.objects[n])==state for n,state in prior.items())
qa=json.loads((r/'HANDRAIL_REVIEW_3_QA.json').read_text())
wall=bpy.data.objects[qa['native_wall_id']];wall_y=max((wall.matrix_world@v.co).y for v in wall.data.vertices)
rail=bpy.data.objects['WAVE_WALL_HANDRAIL_900'];v=[rail.matrix_world@p.co for p in rail.data.vertices]
gap=min(p.y for p in v)-wall_y;assert abs(gap-.05)<1e-5,gap
points=qa['curve_points_source_xyz'];assert abs(math.degrees(math.atan2(points[2][2]-points[1][2],points[2][0]-points[1][0]))-qa['slope_degrees'])<1e-6
for a,b in [(points[0],points[1]),(points[2],points[3])]:assert abs(b[0]-a[0]-.3)<1e-6 and abs(a[2]-b[2])<1e-6
floor=bpy.data.objects['FLOOR_LOWER'];post=bpy.data.objects['WAVE_HANDRAIL_LOWER_POST']
location=post.location;start=Vector((location.x,location.y,1))
hit,point,normal,face=floor.ray_cast(floor.matrix_world.inverted()@start,Vector((0,0,-1)))
assert hit and abs(point.z)<1e-5,'Lower post must rest on actual lower floor'
frozen=Path('/Users/xiwei/interior_design/projects/c_type_home/design/bedroom_door_r4/OPTION_A_SLIDING_R4.blend')
assert hashlib.sha256(frozen.read_bytes()).hexdigest()=='d109c7efcfa2b2b2565e4c073ee0cdf5282b23c01122bc9c1bbe7b8791ac3afb'
bpy.ops.wm.read_factory_settings(use_empty=True);bpy.ops.import_scene.gltf(filepath=str(r/'proxy_handrail_3/interaction_proxy.glb'))
entities={o.get('native_object_id'):o for o in bpy.context.scene.objects if o.get('global_id')}
assert len(entities)==1001
assert 'WAVE_WALL_HANDRAIL_900' in entities
report={'existing_object_states_unchanged':True,'actual_wall_grip_clearance_m':gap,'slope_deg':qa['slope_degrees'],'extensions_m':.3,'lower_post_on_actual_lower_floor':True,'fresh_glb_entities':len(entities),'frozen_r4_unchanged':True}
(r/'HANDRAIL_FINAL_QA.json').write_text(json.dumps(report,indent=2));print('HANDRAIL_FINAL_QA_PASS',json.dumps(report))
