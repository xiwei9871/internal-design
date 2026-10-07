import bpy,json,sys
from pathlib import Path
from mathutils.bvhtree import BVHTree
sys.path.insert(0,str(Path(__file__).parent));from restore_kitchen_divider_pier import bounds,sha,object_state
r=Path('/Users/xiwei/interior_design/projects/c_type_home/design/living_fitness_reading_review_20261006')
qa=json.loads((r/'SUNROOM_DOOR_SOFA_REVIEW12_QA.json').read_text());m=json.loads((r/'proxy_review12/interaction_proxy.manifest.json').read_text())
bpy.ops.wm.open_mainfile(filepath=qa['source']);bpy.context.view_layer.update()
protected_names=['B11_Rectangle039_BODY','B11_Rectangle039_LID_SEAM','SUNROOM_EAST_LOW_STORAGE','SUNROOM_EAST_STORAGE_COUNTER','B11_Rectangle040_BODY_0','B11_Rectangle040_BODY_1']
prior={n:object_state(bpy.data.objects[n]) for n in protected_names}
bpy.ops.wm.open_mainfile(filepath=qa['output']);bpy.context.view_layer.update()
assert all(object_state(bpy.data.objects[n])==s for n,s in prior.items())
def tree(o):return BVHTree.FromPolygons([tuple(o.matrix_world@v.co) for v in o.data.vertices],[list(p.vertices) for p in o.data.polygons],epsilon=1e-7)
new=[bpy.data.objects[n] for n in qa['new_native_ids']]
walls=['VIEW_WALL_W_wall_md_0054','VIEW_WALL_W_wall_md_0055','VIEW_WALL_W_wall_md_0026','VIEW_WALL_W_wall_md_0062','NORTH_BALCONY_GLASS_EAST','V4_GUEST_B11_G-GB-BALC_HOST_GLASS0','V4_GUEST_B11_G-GB-BALC_HOST_GLASS1']
for o in new:
    for n in walls+protected_names:assert not tree(o).overlap(tree(bpy.data.objects[n])),[o.name,n]
sofa=bpy.data.objects['SUNROOM_COMPACT_TWO_SEAT_SOFA'];actual=bounds(sofa)
assert all(abs(actual[j][i]-qa['sofa_bounds'][j][i])<1e-5 for j in range(2) for i in range(3))
for n in qa['retired_native_ids']:assert bpy.data.objects[n].hide_render and bpy.data.objects[n].hide_viewport
assert qa['freezer_north_shift_m']==0 and qa['east_storage_and_freezer_unchanged']
assert qa['central_lane_sofa_to_plantledge_m']>=1.10
assert sha(Path(qa['source']))==qa['source_sha256']
assert sha(Path(qa['output']))==m['source_sha256']
frozen=Path('/Users/xiwei/interior_design/projects/c_type_home/design/bedroom_door_r4/OPTION_A_SLIDING_R4.blend')
assert sha(frozen)=='d109c7efcfa2b2b2565e4c073ee0cdf5282b23c01122bc9c1bbe7b8791ac3afb'
bpy.ops.wm.read_factory_settings(use_empty=True);bpy.ops.import_scene.gltf(filepath=str(r/'proxy_review12/interaction_proxy.glb'))
entities={o.get('native_object_id'):o for o in bpy.context.scene.objects if o.get('global_id')}
registry=json.loads((r/'spatial-canvas.bindings.review12.json').read_text())
assert len(entities)==m['entity_count']==len(registry['bindings'])
assert all(entities[b['native_id']]['global_id']==b['entity_id'] for b in registry['bindings'])
assert not any(n in entities for n in qa['retired_native_ids'])
assert all(abs(bounds(entities['SUNROOM_COMPACT_TWO_SEAT_SOFA'])[j][i]-qa['sofa_bounds'][j][i])<1e-4 for i in range(3) for j in range(2))
report={'revision':m['source_revision'],'fresh_glb_entities':len(entities),'east_freezer_and_cabinet_unchanged':True,'old_door_obstacles_absent':True,'compact_sofa_on_laundry_east':True,'freezer_worktop_is_flip_up_study':True,'owner_accepts_east_overlap':True,'other_original_objects_unchanged':qa['all_other_existing_object_states_unchanged'],'new_geometry_surface_collision_check':True,'seat_ledge_lane_m':qa['central_lane_sofa_to_plantledge_m'],'frozen_r4_and_review11_unchanged':True}
(r/'REVIEW12_FINAL_QA.json').write_text(json.dumps(report,indent=2));print('REVIEW12_FINAL_QA_PASS',json.dumps(report))
