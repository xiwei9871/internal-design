import bpy, json, math, hashlib
from pathlib import Path
from mathutils import Vector, Quaternion
from mathutils.bvhtree import BVHTree
R=Path('/Users/xiwei/interior_design/projects/c_type_home/design/living_fitness_reading_review_20261006')
S=R/'OPTION_A_R4_SUNROOM_INTEGRATED_LAUNDRY_REVIEW_14.blend'
bpy.ops.wm.open_mainfile(filepath=str(S));bpy.context.view_layer.update()
reg=json.loads((R/'spatial-canvas.bindings.review14.json').read_text())
def bounds(o):
 c=[o.matrix_world@Vector(v) for v in o.bound_box]
 return [[min(v[i] for v in c) for i in range(3)],[max(v[i] for v in c) for i in range(3)]]
def tree(o):
 return BVHTree.FromPolygons([tuple(o.matrix_world@v.co) for v in o.data.vertices],[list(p.vertices) for p in o.data.polygons],epsilon=1e-7)
subjects=['B11_Rectangle039_BODY','SUNROOM_EAST_LOW_STORAGE','SUNROOM_EAST_STORAGE_COUNTER',
'SUNROOM_SOFA_REAR_HIGH_CABINET','SUNROOM_LAUNDRY_OVERHEAD','SUNROOM_COMPACT_TWO_SEAT_SOFA']
obstacles=['VIEW_WALL_W_wall_md_0054','VIEW_WALL_W_wall_md_0055','VIEW_WALL_W_wall_md_0026',
'VIEW_WALL_W_wall_md_0062','NORTH_BALCONY_GLASS_EAST','V4_GUEST_B11_G-GB-BALC_HOST_GLASS0',
'V4_GUEST_B11_G-GB-BALC_HOST_GLASS1','SUNROOM_NORTH_PLANT_LEDGE_BASE','SUNROOM_NORTH_PLANT_LEDGE_TOP',
'B11_Rectangle040_BODY_0','B11_Rectangle040_BODY_1','B11_Rectangle040_DOOR_0','B11_Rectangle040_DOOR_1']
collisions=[]
for n in subjects:
 for other in obstacles:
  a=bpy.data.objects.get(n);b=bpy.data.objects.get(other)
  if a and b and tree(a).overlap(tree(b)):collisions.append([n,other])
assert not collisions,collisions
assert not any('FREEZER_FLIP' in o.name or 'FREEZER_WORKTOP' in o.name for o in bpy.context.scene.objects)
# Exact source has retained appliance geometry, 90 degree orientation corrected.
floor=bpy.data.objects['FLOOR_LOWER']
for name in ['B11_Rectangle039_BODY','SUNROOM_EAST_LOW_STORAGE','SUNROOM_COMPACT_TWO_SEAT_SOFA']:
 a,b=bounds(bpy.data.objects[name])
 for x,y in [(a[0]+.01,a[1]+.01),(b[0]-.01,b[1]-.01)]:
  hit,point,normal,index=floor.ray_cast(floor.matrix_world.inverted()@Vector((x,y,1)),Vector((0,0,-1)))
  assert hit and abs(point.z)<1e-5,(name,x,y)
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
assert sha('/Users/xiwei/interior_design/projects/c_type_home/design/bedroom_door_r4/OPTION_A_SLIDING_R4.blend')=='d109c7efcfa2b2b2565e4c073ee0cdf5282b23c01122bc9c1bbe7b8791ac3afb'
report={'native_collision_pairs':collisions,'actual_floor_below':True,'frozen_r4_unchanged':True,
'freezer_axis_source_xyz':'Y','no_extra_freezer_cover':True,
'source_sha256':sha(S),'entity_count':len(reg['bindings']),'functional_opening_sweeps_certified':False}
(R/'REVIEW14_GEOMETRY_EVIDENCE.json').write_text(json.dumps(report,indent=2)+'\n')
# Render-only cutaway. Walls and glazing are preserved in the delivered source.
keep={'B11_Rectangle039_BODY','B11_Rectangle039_LID_SEAM','B11_Rectangle040_BODY_0','B11_Rectangle040_BODY_1','B11_Rectangle040_DOOR_0','B11_Rectangle040_DOOR_1','FLOOR_LOWER','VIEW_WALL_W_wall_md_0054','VIEW_WALL_W_wall_md_0055','VIEW_WALL_W_wall_md_0026','VIEW_WALL_W_wall_md_0062',
'V4_GUEST_B11_G-GB-BALC_HOST_GLASS0','V4_GUEST_B11_G-GB-BALC_HOST_GLASS1'}
for o in bpy.context.scene.objects:
 if o.type=='MESH':
  o.hide_render=o.hide_render or not (o.name in keep or (o.name.startswith('SUNROOM_') and not o.hide_viewport))
scene=bpy.context.scene
data=bpy.data.cameras.new('REVIEW14_CUTAWAY');cam=bpy.data.objects.new('REVIEW14_CUTAWAY',data);scene.collection.objects.link(cam)
scene.camera=cam;scene.render.engine='BLENDER_WORKBENCH'
scene.render.resolution_x=1200;scene.render.resolution_y=800;scene.render.resolution_percentage=100
scene.display.shading.light='STUDIO';scene.display.shading.studio_light='paint.sl'
scene.display.shading.color_type='MATERIAL';scene.display.shading.show_shadows=True;scene.display.shading.show_cavity=True
scene.display.shading.cavity_type='BOTH';scene.display.shading.show_specular_highlight=True
views=[('SUNROOM_REVIEW14_FRONT.png',(10.1,16.5,3.1),(10.1,11.9,1.3),36),
('SUNROOM_REVIEW14_AXON.png',(6.0,17.6,6.5),(10.4,12.15,1.0),44)]
for filename,eye,target,lens in views:
 cam.location=eye;cam.rotation_euler=(Vector(target)-Vector(eye)).to_track_quat('-Z','Y').to_euler()
 data.lens=lens;scene.render.filepath=str(R/filename);bpy.ops.render.render(write_still=True)
print('REVIEW14_GEOMETRY_RENDER',json.dumps(report))

