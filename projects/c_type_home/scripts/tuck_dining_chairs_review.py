"""Tuck four packet-selected dining chairs in a separate immutable review snapshot."""
import bpy,json,sys,hashlib
from pathlib import Path
from mathutils import Vector,Matrix
from mathutils.bvhtree import BVHTree
sys.path.insert(0,str(Path(__file__).parent))
from restore_kitchen_divider_pier import object_state,bounds,sha
BASE_SHA='bffc60b456e81e30a29613e9b3ef07b6684a16700233c5a6673fab5bf49588ed'
project=Path('/Users/xiwei/interior_design/projects/c_type_home')
base=project/'design/kitchen_divider_r4_review/OPTION_A_R4_PIER_THINNER_AC_RAISED_REVIEW.blend'
root=project/'design/dining_chairs_r4_review';root.mkdir(parents=True,exist_ok=True)
output=root/'OPTION_A_R4_DINING_CHAIRS_ALIGNED_REVIEW.blend'
assert not output.exists() and sha(base)==BASE_SHA
frozen=json.loads((base.parent/'PIER_AND_AC_QA.json').read_text())['frozen_files_unchanged']
def frozen_check():
 for name,meta in frozen.items():
  p=Path(name);assert sha(p)==meta['sha256'] and p.stat().st_size==meta['size'] and str(p.stat().st_mtime_ns)==meta['mtime_ns'],name
frozen_check();bpy.ops.wm.open_mainfile(filepath=str(base))
prior={o.name:object_state(o) for o in bpy.context.scene.objects}
chairs=[bpy.data.objects[f'B11_Circle{i:03d}_CATALOG_00_00'] for i in range(10,14)]
parents=[o.parent for o in chairs];allowed={o.name for p in parents for o in [p,*p.children_recursive]}
assert len(allowed)==8
poses={p.name:p.matrix_world.copy() for p in parents};old={o.name:bounds(o) for o in chairs}
table=bpy.data.objects['B11_Rectangle050_CATALOG_00_00'];tb=bounds(table)
assert table.get('native_asset_path','').endswith('/dining-table/model.glb')
def tree(o):
 evaluated=o.evaluated_get(bpy.context.evaluated_depsgraph_get());mesh=evaluated.to_mesh()
 try:return BVHTree.FromPolygons([evaluated.matrix_world@v.co for v in mesh.vertices],[tuple(p.vertices) for p in mesh.polygons],epsilon=1e-6)
 finally:evaluated.to_mesh_clear()
table_tree=tree(table)
# Two stations at quarter and three-quarter table length, mirrored across center.
xstations=[tb[0][0]+(tb[1][0]-tb[0][0])*f for f in [.25,.75]]
chosen=None
for k in range(41):
 tuck=.12-k*.005
 for index,(chair,parent) in enumerate(zip(chairs,parents)):
  center=Vector([(old[chair.name][0][i]+old[chair.name][1][i])/2 for i in range(3)])
  target=Vector((xstations[index%2],tb[1][1]-tuck if index<2 else tb[0][1]+tuck,center.z))
  parent.matrix_world=Matrix.Translation(target-center)@poses[parent.name]
 bpy.context.view_layer.update()
 if not any(tree(o).overlap(table_tree) for o in chairs):chosen=tuck;break
assert chosen is not None,'Cannot tuck without table intersection'
assert chosen>0,'Chair seats must extend into table footprint'
for i,a in enumerate(chairs):
 for b in chairs[i+1:]:assert not tree(a).overlap(tree(b)),(a.name,b.name)
for n,s in prior.items():
 if n not in allowed:assert object_state(bpy.data.objects[n])==s,n
 else:
  current=object_state(bpy.data.objects[n]);assert all(current[k]==s[k] for k in s if k!='matrix'),n
new={o.name:bounds(o) for o in chairs}
for o in chairs:
 assert abs(new[o.name][0][2]-old[o.name][0][2])<1e-6
 assert all(abs((new[o.name][1][i]-new[o.name][0][i])-(old[o.name][1][i]-old[o.name][0][i]))<1e-5 for i in range(3))
bpy.ops.wm.save_as_mainfile(filepath=str(output))
# Independent reload of saved bytes verifies transforms and frozen sources.
after={o.name:object_state(o) for o in bpy.context.scene.objects}
bpy.ops.wm.open_mainfile(filepath=str(output));assert all(object_state(bpy.data.objects[n])==s for n,s in after.items())
frozen_check();assert sha(base)==BASE_SHA
report={'status':'HUMAN_REVIEW','base':str(base),'base_sha256':BASE_SHA,'output':str(output),'output_sha256':sha(output),'table':'B11_Rectangle050_CATALOG_00_00','table_bounds_m':tb,'before':old,'after':new,'chairs':list(old),'allowed_objects':sorted(allowed),'station_x_m':xstations,'center_inset_from_table_edge_m':chosen,'table_chair_surface_intersections':False,'chair_chair_surface_intersections':False,'chairs_geometry_scale_yaw_floor_height_preserved':True,'all_other_objects_unchanged':True,'fresh_reopen_verified':True,'frozen_files_unchanged':frozen}
(root/'DINING_CHAIRS_QA.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n');print(json.dumps(report,ensure_ascii=False))
