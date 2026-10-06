"""Packet-located wall rail; source revision2 remains read-only."""
import bpy,json,hashlib,math,sys,uuid
from pathlib import Path
from mathutils import Vector
sys.path.insert(0,str(Path(__file__).parent))
from restore_kitchen_divider_pier import sha,object_state
r=Path('/Users/xiwei/interior_design/projects/c_type_home/design/living_furniture_review_20261006')
source=r/'OPTION_A_R4_LIVING_WAVE35_ALUMINUM_FIT_REVIEW_2.blend'
out=r/'OPTION_A_R4_WAVE35_HANDRAIL_REVIEW_3.blend'
assert sha(source)=='78d64077368b1a4952f44ed4877464e0cde51ffceeee40b2ae40727ebfc85d30'
bpy.ops.wm.open_mainfile(filepath=str(source));prior={o.name:object_state(o) for o in bpy.context.scene.objects}
wall=bpy.data.objects['VIEW_WALL_W_wall_md_0044']
wall_y=max((wall.matrix_world@v.co).y for v in wall.data.vertices)
radius=.020;gap=.050;rail_y=wall_y+gap+radius
angle=math.atan(.1125/.35)
offset=radius*math.cos(angle)
g=json.loads((r/'WAVE_STEP_GEOMETRY.json').read_text())
# Locate nosings at the handrail's actual lateral line rather than borrowing the wave endpoint.
def interpolate(line,y):
    for (x0,y0),(x1,y1) in zip(line,line[1:]):
        if y0<=y<=y1:return x0+(x1-x0)*(y-y0)/(y1-y0)
    raise ValueError(y)
first=interpolate(g['front_lines'][0],rail_y);last=first+3*.35
floor_x=first-.35
z0=.9-offset;z1=1.35-offset
points=[(floor_x-.30,rail_y,z0),(floor_x,rail_y,z0),(last,rail_y,z1),(last+.30,rail_y,z1)]
wood=bpy.data.materials.new('HANDRAIL_PALE_ASH');wood.diffuse_color=(.53,.35,.18,1)
metal=bpy.data.materials.new('HANDRAIL_BRUSHED_NICKEL');metal.diffuse_color=(.17,.19,.20,1)
for material,color in [(wood,(.53,.35,.18,1)),(metal,(.17,.19,.20,1))]:
    material.use_nodes=True
    shader=material.node_tree.nodes.get('Principled BSDF')
    shader.inputs['Base Color'].default_value=color
    shader.inputs['Roughness'].default_value=.65
new=[]
def track(o):
    o['review_status']='HUMAN_REVIEW';new.append(o);return o
curve=bpy.data.curves.new('WAVE_WALL_HANDRAIL_PATH','CURVE');curve.dimensions='3D';curve.resolution_u=16;curve.bevel_depth=radius;curve.bevel_resolution=5;curve.use_fill_caps=True
sp=curve.splines.new('POLY');sp.points.add(len(points)-1)
for p,co in zip(sp.points,points):p.co=(*co,1)
rail=track(bpy.data.objects.new('WAVE_WALL_HANDRAIL_900',curve));bpy.context.scene.collection.objects.link(rail);rail.data.materials.append(wood)
def cylinder(name,a,b,radius,material):
    a,b=Vector(a),Vector(b);delta=b-a
    bpy.ops.mesh.primitive_cylinder_add(vertices=32,radius=radius,depth=delta.length,location=(a+b)/2)
    o=bpy.context.object;o.name=name;o.rotation_euler=delta.to_track_quat('Z','Y').to_euler();o.data.materials.append(material)
    for p in o.data.polygons:p.use_smooth=len(p.vertices)==4
    return track(o)
def box(name,center,size,material):
    bpy.ops.mesh.primitive_cube_add(size=1,location=center);o=bpy.context.object;o.name=name;o.scale=size;o.data.materials.append(material)
    return track(o)
def height(x):
    if x<=floor_x:return z0
    if x>=last:return z1
    return z0+(x-floor_x)*.1125/.35
# Horizontal extensions terminate downwards100mm; lower end uses one floor post,
# because the original wall starts east of the lower rail extension.
for tag,p in [('LOWER',points[0]),('UPPER',points[-1])]:
    cylinder('WAVE_HANDRAIL_'+tag+'_RETURN',p,(p[0],p[1],p[2]-.10),radius,wood)
postx=floor_x-.15
cylinder('WAVE_HANDRAIL_LOWER_POST',(postx,rail_y,.02),(postx,rail_y,z0-radius),.015,metal)
box('WAVE_HANDRAIL_LOWER_BASE',(postx,rail_y,.012),(.10,.10,.024),metal)
for i,x in enumerate([5.98,6.42,6.95]):
    z=height(x)-radius-.035
    box('WAVE_HANDRAIL_WALL_PLATE_'+str(i),(x,wall_y+.004,z),(.07,.008,.08),metal)
    cylinder('WAVE_HANDRAIL_BRACKET_ARM_'+str(i),(x,wall_y+.008,z),(x,rail_y,z),.007,metal)
    cylinder('WAVE_HANDRAIL_BRACKET_UP_'+str(i),(x,rail_y,z),(x,rail_y,height(x)-radius),.007,metal)
# Convert only the new curve to a mesh for stable per-object producer binding.
bpy.ops.object.select_all(action='DESELECT');rail.select_set(True);bpy.context.view_layer.objects.active=rail
bpy.ops.object.convert(target='MESH')
bpy.context.view_layer.update()
assert all(object_state(bpy.data.objects[n])==v for n,v in prior.items())
registry=json.loads((r/'spatial-canvas.bindings.aluminum-fit-2.json').read_text())
for o in new:
    registry['bindings'].append({'entity_id':'ent_'+uuid.uuid5(uuid.NAMESPACE_URL,'c_type_home:handrail:v1:'+o.name).hex,'adapter':'blender','native_id':o.name,'semantic_type':'handrail' if o.name=='WAVE_WALL_HANDRAIL_900' else 'handrail_part','room_id':'unassigned','authority_level':'HUMAN_DESIGN_GUIDE'})
registry.update(registry_revision='13-wave-wall-handrail-review',source_revision='r4-living-wave35-aluminum-review-3',source_locator=str(out))
bpy.ops.wm.save_as_mainfile(filepath=str(out));registry['source_sha256']=sha(out)
(r/'spatial-canvas.bindings.handrail-3.json').write_text(json.dumps(registry,ensure_ascii=False,indent=2)+'\n')
report={'revision':registry['source_revision'],'source_sha256':registry['source_sha256'],'native_wall_id':wall.name,'diameter_m':.04,'wall_clearance_m':gap,'height_above_nosings_m':.9,'slope_degrees':math.degrees(angle),'horizontal_extensions_m':.3,'down_returns_m':.1,'lower_floor_post_required':True,'curve_points_source_xyz':points,'unchanged_existing_objects':True,'new_objects':[o.name for o in new],'standards_reference':'GB55019-2021 sections2.8.1,2.8.3,2.8.4;domestic single-side design reference,not certification of an accessible stair','standard_url':'https://cl.huaian.gov.cn/col/8349_118464/content/17144928/1715582990210UdXHUSlL.html'}
(r/'HANDRAIL_REVIEW_3_QA.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
assert sha(source)=='78d64077368b1a4952f44ed4877464e0cde51ffceeee40b2ae40727ebfc85d30'
print(json.dumps(report,ensure_ascii=False))
