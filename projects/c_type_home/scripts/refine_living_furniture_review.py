"""Owner-requested light round side table + chaise/two-seat sofa swap in a new review only."""
import bpy,bmesh,math,json,sys
from pathlib import Path
from mathutils import Matrix,Vector
sys.path.insert(0,str(Path(__file__).parent))
from restore_kitchen_divider_pier import object_state,bounds,sha
project=Path('/Users/xiwei/interior_design/projects/c_type_home')
source=project/'design/wall_identity_r4_review/OPTION_A_R4_NATIVE_WALL_PARTS_REVIEW.blend'
root=project/'design/living_furniture_review_20261006';root.mkdir(parents=True,exist_ok=True)
output=root/'OPTION_A_R4_LIVING_FURNITURE_REVIEW.blend'
assert not output.exists() and sha(source)=='564ae8b36caea702d4ea556619f153bbe84e1ee04398f123a38f047bca2cedd6'
frozen=json.loads((project/'design/wall_identity_r4_review/WALL_PARTS_QA.json').read_text())['frozen_files_unchanged']
frozen[str(source)]={'sha256':sha(source),'size':source.stat().st_size,'mtime_ns':str(source.stat().st_mtime_ns)}
def source_check():
 for path,v in frozen.items():
  p=Path(path);assert sha(p)==v['sha256'] and p.stat().st_size==v['size'] and str(p.stat().st_mtime_ns)==v['mtime_ns'],path
source_check();bpy.ops.wm.open_mainfile(filepath=str(source))
prior={o.name:object_state(o) for o in bpy.context.scene.objects}
table=bpy.data.objects['B11_Circle_CATALOG_00_00']
sofa=bpy.data.objects['B11_Rectangle047_CATALOG_00_00'];chaise=bpy.data.objects['B11_Rectangle048_CATALOG_00_00']
before={o.name:bounds(o) for o in [table,sofa,chaise]}
center=lambda o:Vector([(bounds(o)[0][i]+bounds(o)[1][i])/2 for i in range(3)])
sc=center(sofa);cc=center(chaise)
# The north bay chair retains its west-head / east-foot orientation.
chaise.parent.matrix_world=Matrix.Translation(Vector((sc.x-cc.x,sc.y-cc.y,0)))@chaise.parent.matrix_world
# Former chaise station is south of the coffee table: face the sofa north into the seating group.
sofa.parent.matrix_world=Matrix.Translation(Vector((cc.x,cc.y,0)))@Matrix.Rotation(math.pi,4,'Z')@Matrix.Translation(Vector((-sc.x,-sc.y,0)))@sofa.parent.matrix_world
bpy.context.view_layer.update()
lo,hi=before[table.name];cx=(lo[0]+hi[0])/2;cy=(lo[1]+hi[1])/2;floor=lo[2]
verts=[];faces=[];smooth=[]
def ring_part(rings,segments):
 offset=len(verts)
 for x,y,z,radius in rings:
  for k in range(segments):
   a=2*math.pi*k/segments;verts.append((cx+x+radius*math.cos(a),cy+y+radius*math.sin(a),floor+z))
 faces.append(tuple(offset+k for k in reversed(range(segments))));smooth.append(False)
 for row in range(len(rings)-1):
  for k in range(segments):
   faces.append((offset+row*segments+k,offset+row*segments+(k+1)%segments,offset+(row+1)*segments+(k+1)%segments,offset+(row+1)*segments+k));smooth.append(True)
 faces.append(tuple(offset+(len(rings)-1)*segments+k for k in range(segments)));smooth.append(False)
# Ø480mm/H480mm from owner image;18mm gently rounded top and open3-leg structure.
ring_part([(0,0,.462,.237),(0,0,.465,.240),(0,0,.477,.240),(0,0,.480,.237)],96)
ring_part([(0,0,.437,.058),(0,0,.462,.064)],48)
for k in range(3):
 a=math.radians(30+120*k)
 ring_part([(.180*math.cos(a),.180*math.sin(a),0,.014),(.086*math.cos(a),.086*math.sin(a),.452,.020)],32)
inverse=table.matrix_world.inverted()
mesh=bpy.data.meshes.new('LIVING_ROUND_SIDE_TABLE_480_REVIEW');mesh.from_pydata([inverse@Vector(p) for p in verts],[],faces);mesh.update()
for poly,shade in zip(mesh.polygons,smooth):poly.use_smooth=shade
bm=bmesh.new();bm.from_mesh(mesh);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));assert all(e.is_manifold for e in bm.edges);volume=bm.calc_volume(signed=False);bm.to_mesh(mesh);bm.free();assert volume>0
material=bpy.data.materials.new('LIVING_ROUND_SIDE_TABLE_PALE_ASH');material.diffuse_color=(.68,.53,.36,1);material.use_nodes=True
shader=material.node_tree.nodes.get('Principled BSDF');shader.inputs['Base Color'].default_value=(.68,.53,.36,1);shader.inputs['Roughness'].default_value=.65
mesh.materials.append(material);table.data=mesh
table['previous_native_asset_path']=table.get('native_asset_path','')
if 'native_asset_path' in table:del table['native_asset_path']
table['design_reference']='Owner image1202 round table;diameter480mm,height480mm;thin18mm top,three splayed wood legs'
table['review_status']='HUMAN_REVIEW'
bpy.context.view_layer.update()
after={o.name:bounds(o) for o in [table,sofa,chaise]}
assert abs(after[table.name][1][0]-after[table.name][0][0]-.48)<1e-5
assert abs(after[table.name][1][2]-after[table.name][0][2]-.48)<1e-5
for o,target in [(chaise,sc),(sofa,cc)]:
 now=center(o);assert abs(now.x-target.x)<1e-5 and abs(now.y-target.y)<1e-5
 assert abs(bounds(o)[0][2]-before[o.name][0][2])<1e-5
 assert object_state(o)['mesh']==prior[o.name]['mesh']
allowed={table.name}
for o in [sofa.parent,chaise.parent]:allowed.update(x.name for x in [o,*o.children_recursive])
assert set(prior)=={o.name for o in bpy.context.scene.objects}
for name,state in prior.items():
 now=object_state(bpy.data.objects[name])
 if name not in allowed:assert now==state,name
 elif name!=table.name:assert all(now[k]==state[k] for k in state if k!='matrix'),name
def overlap(a,b):
 aa,bb=bounds(a),bounds(b);return [min(aa[1][i],bb[1][i])-max(aa[0][i],bb[0][i]) for i in range(3)]
protected=[bpy.data.objects[n] for n in ['B11_Rectangle046_CATALOG_00_00','B11_Rectangle049_CATALOG_00_00']]
for i,o in enumerate([table,sofa,chaise]):
 for p in protected+[table,sofa,chaise][:i]:
  assert not all(v>1e-5 for v in overlap(o,p)),(o.name,p.name)
bpy.ops.wm.save_as_mainfile(filepath=str(output));saved={o.name:object_state(o) for o in bpy.context.scene.objects}
bpy.ops.wm.open_mainfile(filepath=str(output));assert all(object_state(bpy.data.objects[n])==v for n,v in saved.items());source_check()
report={'status':'HUMAN_REVIEW','source':str(source),'source_sha256':sha(source),'output':str(output),'output_sha256':sha(output),'selected_native_ids':['B11_Circle_CATALOG_00_00','B11_Rectangle047_CATALOG_00_00','B11_Rectangle048_CATALOG_00_00'],'before':before,'after':after,'table_dimensions_m':[.48,.48,.48],'table_top_thickness_m':.018,'table_leg_count':3,'sofa_yaw_change_degrees':180,'chaise_north_window_station':list(sc),'other_objects_unchanged':True,'seat_meshes_scale_floor_height_unchanged':True,'living_furniture_aabb_intersections':False,'fresh_reopen_verified':True,'frozen_files_unchanged':frozen,'stair_scope':'pending explicit clarification;current3-step/stair/floor geometry unchanged'}
(root/'LIVING_FURNITURE_QA.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n');print(json.dumps(report,ensure_ascii=False))
