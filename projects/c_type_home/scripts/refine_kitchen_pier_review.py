"""User refinement of the displayed review-2: pier thinner 50mm, AC +300mm only."""
import bpy,bmesh,json,hashlib,sys
from pathlib import Path
from mathutils import Matrix,Vector
sys.path.insert(0,str(Path(__file__).parent))
from restore_kitchen_divider_pier import object_state,bounds,sha
root=Path('/Users/xiwei/interior_design/projects/c_type_home/design/kitchen_divider_r4_review')
source=root/'OPTION_A_R4_PIER_AND_ANGLED_AC_REVIEW.blend'
output=root/'OPTION_A_R4_PIER_THINNER_AC_RAISED_REVIEW.blend'
if output.exists():raise RuntimeError('New output path required')
source_sha=sha(source)
bpy.ops.wm.open_mainfile(filepath=str(source))
prior={o.name:object_state(o) for o in bpy.context.scene.objects}
wall=bpy.data.objects['KITCHEN_DIVIDER_PIER_SITE_REVIEW'];old=bounds(wall)
# Keep the island-side plane X5.9 and island notch Y1.43. Retreat the utility side.
left=old[0][0]
for v in wall.data.vertices:
 if abs(v.co.x-left)<1e-5:v.co.x+=.05
wall.data.update()
ac=bpy.data.objects['B11_K-UTILITY-WALL-AC'];allowed={o.name for o in [ac,*ac.children_recursive]}
ac.matrix_world=Matrix.Translation((0,0,.3))@ac.matrix_world
bpy.context.view_layer.update()
body=bpy.data.objects['B11_K-UTILITY_AC_BODY'];ac_bounds=bounds(body)
# An optional reduction is unnecessary: raised body top is below inherited 2.8m ceiling.
if ac_bounds[1][2]>2.8+1e-5:raise RuntimeError('AC no longer fits below inherited ceiling')
changed=allowed|{wall.name}
assert all(object_state(bpy.data.objects[n])==s for n,s in prior.items() if n not in changed)
assert all(object_state(bpy.data.objects[n])['mesh']==prior[n]['mesh'] for n in allowed)
new=bounds(wall);assert abs((old[1][0]-old[0][0])-(new[1][0]-new[0][0])-.05)<1e-5
assert abs(new[1][0]-old[1][0])<1e-5 and abs(new[1][1]-old[1][1])<1e-5
bm=bmesh.new();bm.from_mesh(wall.data);assert not any(e.is_boundary or not e.is_manifold for e in bm.edges);bm.free()
bpy.ops.wm.save_as_mainfile(filepath=str(output))
assert sha(source)==source_sha
r4=root.parent/'bedroom_door_r4/OPTION_A_SLIDING_R4.blend'
assert sha(r4)=='d109c7efcfa2b2b2565e4c073ee0cdf5282b23c01122bc9c1bbe7b8791ac3afb'
report={'status':'HUMAN_REVIEW','base_review':str(source),'base_sha256':source_sha,'output':str(output),'output_sha256':sha(output),'wall_before_m':old,'wall_after_m':new,'thickness_reduction_m':.05,'ac_z_translation_m':.3,'ac_bounds_after_m':ac_bounds,'ac_size_reduced':False,'other_objects_unchanged':True,'frozen_r4_unchanged':True,'note':'No further HVAC fit/installation design requested; keep existing review yaw, X/Y and all dimensions.'}
(root/'THINNER_PIER_RAISED_AC_QA.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report))
