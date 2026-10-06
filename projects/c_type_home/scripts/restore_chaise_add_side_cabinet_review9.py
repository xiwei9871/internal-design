"""Restore existing window chaise and add separate catalog-size shallow cabinet beside L chaise."""
import bpy,json,uuid,sys
from pathlib import Path
from mathutils import Matrix,Vector
from mathutils.bvhtree import BVHTree
sys.path.insert(0,str(Path(__file__).parent))
from restore_kitchen_divider_pier import sha,object_state,bounds
r=Path('/Users/xiwei/interior_design/projects/c_type_home/design/living_fitness_reading_review_20261006')
source=r/'OPTION_A_R4_BOOKCASE_UPPER_WALL_REVIEW_8.blend'
output=r/'OPTION_A_R4_UPPER_BOOKCASE_SIDE_CABINET_CHAISE_REVIEW_9.blend'
expected='d88554a8f5f2927d40e822667c7a16af2b48df0691dcfa8b8bf1070910f8f7cd'
assert sha(source)==expected
bpy.ops.wm.open_mainfile(filepath=str(source))
prior={o.name:object_state(o) for o in bpy.context.scene.objects}
chaise_name='B11_Rectangle048_CATALOG_00_00'
chaise=bpy.data.objects[chaise_name]
# Hidden children may have stale cached world matrices; protect authored local/parent transforms,
# then independently verify the actual restored world bounds in verify_upper_bookcase_chaise_review9.
authored_transform=(chaise.matrix_basis.copy(),chaise.matrix_parent_inverse.copy(),chaise.parent.name if chaise.parent else None)
chaise.hide_viewport=False;chaise.hide_render=False;chaise.hide_set(False)
template=bpy.data.objects['READING_5015_SHORT_SLIDING_CABINET']
cab=template.copy();cab.data=template.data.copy();cab.name='L_SOFA_5015_SHALLOW_SIDE_CABINET'
bpy.context.scene.collection.objects.link(cab)
lo,hi=bounds(cab);center=Vector([(lo[i]+hi[i])/2 for i in range(3)])
# Outside the south side of the L chaise; leave50mm from sofa, never put the unit at the stair.
newlo=[4.25,7.58,0];newhi=[5.07,7.90,.34]
destination=Vector([(newlo[i]+newhi[i])/2 for i in range(3)])
cab.matrix_world=Matrix.Translation(destination-center)@cab.matrix_world
cab['design_reference']='Owner-accepted5015 short sliding cabinet820x320x340 from ash catalogp21;standalone extra unit'
cab['review_status']='HUMAN_REVIEW'
if 'spatial_canvas_global_id' in cab:del cab['spatial_canvas_global_id']
bpy.context.view_layer.update()
got=bounds(cab)
assert all(abs(got[j][i]-[newlo,newhi][j][i])<1e-5 for i in range(3) for j in range(2))
for name,state in prior.items():
    now=object_state(bpy.data.objects[name])
    if name==chaise_name:
        assert now['mesh']==state['mesh'],name
        assert chaise.matrix_basis==authored_transform[0] and chaise.matrix_parent_inverse==authored_transform[1]
        assert (chaise.parent.name if chaise.parent else None)==authored_transform[2]
        assert all(now[k]==state[k] for k in ['parent','collections','materials','properties'])
    else:assert now==state,name
floor=bpy.data.objects['FLOOR_LOWER']
for x in [4.26,5.06]:
    for y in [7.59,7.89]:
        hit,p,n,i=floor.ray_cast(floor.matrix_world.inverted()@Vector((x,y,1)),Vector((0,0,-1)))
        assert hit and abs(p.z)<1e-5
def tree(o):return BVHTree.FromPolygons([tuple(o.matrix_world@v.co) for v in o.data.vertices],[list(p.vertices) for p in o.data.polygons],epsilon=1e-7)
check=['B11_Rectangle046_CATALOG_00_00','B11_Rectangle049_CATALOG_00_00','B11_Circle_CATALOG_00_00','STEP_0','STEP_1','STEP_2','READING_5015_SHORT_SLIDING_CABINET','READING_3205A_PADDED_BENCH']
for o in [cab,chaise]:
    for name in check:assert not tree(o).overlap(tree(bpy.data.objects[name])),[o.name,name]
assert not tree(cab).overlap(tree(chaise))
registry=json.loads((r/'spatial-canvas.bindings.review8.json').read_text())
original=json.loads((r.parent/'living_furniture_review_20261006'/'spatial-canvas.bindings.l-sofa-4.json').read_text())
chaise_binding=next(b for b in original['bindings'] if b['native_id']==chaise_name)
assert not any(b['entity_id']==chaise_binding['entity_id'] for b in registry['bindings'])
registry['bindings'].append(chaise_binding)
cab_gid='ent_'+uuid.uuid5(uuid.NAMESPACE_URL,'c_type_home:5015-side-cabinet:v1').hex
registry['bindings'].append({'entity_id':cab_gid,'adapter':'blender','native_id':cab.name,'semantic_type':'cabinet','room_id':'living','authority_level':'HUMAN_DESIGN_GUIDE'})
registry.update(registry_revision='19-upper-bookcase-side-cabinet-chaise',source_revision='r4-upper-bookcase-side-cabinet-chaise-review-9',source_locator=str(output))
bpy.ops.wm.save_as_mainfile(filepath=str(output));registry['source_sha256']=sha(output)
(r/'spatial-canvas.bindings.review9.json').write_text(json.dumps(registry,ensure_ascii=False,indent=2)+'\n')
saved={o.name:object_state(o) for o in bpy.context.scene.objects}
bpy.ops.wm.open_mainfile(filepath=str(output));assert all(object_state(bpy.data.objects[n])==state for n,state in saved.items())
assert sha(source)==expected
frozen=Path('/Users/xiwei/interior_design/projects/c_type_home/design/bedroom_door_r4/OPTION_A_SLIDING_R4.blend')
assert sha(frozen)=='d109c7efcfa2b2b2565e4c073ee0cdf5282b23c01122bc9c1bbe7b8791ac3afb'
report={'status':'HUMAN_REVIEW','output':str(output),'source':str(source),'output_sha256':sha(output),'chaise_restored_native_id':chaise_name,'chaise_restored_global_id':chaise_binding['entity_id'],'chaise_geometry_and_station_unchanged':True,'side_cabinet_native_id':'L_SOFA_5015_SHALLOW_SIDE_CABINET','side_cabinet_global_id':cab_gid,'side_cabinet_bounds':[newlo,newhi],'side_cabinet_size_m':[.82,.32,.34],'side_cabinet_to_sofa_gap_m':.05,'bookshelf_retained_on_upper_wall':True,'all_other_existing_object_states_unchanged':True,'no_intersections_with_named_furniture_or_steps':True,'fitness_outline_overlaps_restored_chaise_by_design':True,'fitness_equipment_fit_verified':False,'source_and_frozen_r4_unchanged':True,'fresh_reopen_verified':True}
(r/'SIDE_CABINET_CHAISE_REVIEW9_QA.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n');print(json.dumps(report,ensure_ascii=False))
