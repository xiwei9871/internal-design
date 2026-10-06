"""Three-step successor, book storage/bench and north-window fitness reserve."""
import bpy,bmesh,json,math,uuid,sys
from pathlib import Path
from mathutils import Vector
sys.path.insert(0,str(Path(__file__).parent))
from restore_kitchen_divider_pier import sha,object_state,bounds
old=Path('/Users/xiwei/interior_design/projects/c_type_home/design/living_furniture_review_20261006')
root=old.parent/'living_fitness_reading_review_20261006'
source=old/'OPTION_A_R4_L_SOFA_REVIEW_4.blend'
output=root/'OPTION_A_R4_THREE_STEP_READING_FITNESS_REVIEW_5.blend'
assert sha(source)=='6775691eaaac0d57261eb2e00929bbb753f54687bfa5bf3ff44cc8955ba0ca8c'
bpy.ops.wm.open_mainfile(filepath=str(source))
prior={o.name:object_state(o) for o in bpy.context.scene.objects}
geom=json.loads((root/'THREE_STEP_GEOMETRY.json').read_text())
allowed=set(geom['objects'])
new=[]
def mesh_object(name,vertices,faces,material=None):
    me=bpy.data.meshes.new(name+'_REVIEW5');me.from_pydata(vertices,[],faces);me.update()
    bm=bmesh.new();bm.from_mesh(me);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(me);bm.free()
    o=bpy.data.objects.get(name)
    if o is None:o=bpy.data.objects.new(name,me);bpy.context.scene.collection.objects.link(o);new.append(o)
    else:o.data=me
    if material:me.materials.append(material)
    return o
def material(name,color):
    m=bpy.data.materials.get(name) or bpy.data.materials.new(name);m.use_nodes=True;m.diffuse_color=(*color,1)
    m.node_tree.nodes.get('Principled BSDF').inputs['Base Color'].default_value=(*color,1)
    m.node_tree.nodes.get('Principled BSDF').inputs['Roughness'].default_value=.7
    return m
oak=material('READING_PALE_ASH',(.57,.40,.24))
cushion=material('READING_BENCH_WARM_GREY',(.44,.44,.39))
dark=material('READING_BRACKET_DARK',(.13,.15,.14))
wood=bpy.data.materials['R4_WAVE_STEP_PALE_WOOD']
for name,data in geom['objects'].items():
    existing=bpy.data.objects[name];m=wood if name.startswith('STEP_') else (existing.data.materials[0] if existing.data.materials else None)
    mesh_object(name,data['vertices'],data['faces'],m)
retired={'WAVE_STEP_3_ARRIVAL','B11_Rectangle048_CATALOG_00_00'}
for name in retired:
    o=bpy.data.objects[name];o.hide_render=True;o.hide_viewport=True;o.hide_set(True)
allowed.update(retired)
# Move no sofa toward the lower landing: only1150mm remains at its south end.
def box(name,lo,hi,m,bevel=0):
    bpy.ops.mesh.primitive_cube_add(size=1,location=[(lo[i]+hi[i])/2 for i in range(3)])
    o=bpy.context.object;o.name=name;o.scale=[hi[i]-lo[i] for i in range(3)]
    bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
    if bevel:
        mod=o.modifiers.new('Rounded edges','BEVEL');mod.width=bevel;mod.segments=4
        bpy.ops.object.modifier_apply(modifier=mod.name)
    o.data.materials.append(m);new.append(o);return o
# Actual5015 short sliding cabinet820x320x340; keep cabinet hollow and doors articulated.
cx0,cx1=7.40,7.72;cy0,cy1=8.95,9.77
pieces=[]
pieces.append(box('READING_5015_BASE',(cx0,cy0,0),(cx1,cy1,.018),oak))
pieces.append(box('READING_5015_TOP',(cx0,cy0,.322),(cx1,cy1,.340),oak))
for y in [cy0,cy1-.018]:pieces.append(box('READING_5015_END',(cx0,y,.018),(cx1,y+.018,.322),oak))
pieces.append(box('READING_5015_BACK',(cx1-.012,cy0,.018),(cx1,cy1,.322),oak))
for j in range(2):
    pieces.append(box('READING_5015_SLIDING_DOOR',(cx0,cy0+.018+j*.392,.021),(cx0+.015,cy0+.018+(j+1)*.392-.004,.319),oak,.003))
def join_as(name,parts):
    bpy.ops.object.select_all(action='DESELECT')
    for o in parts:o.select_set(True)
    bpy.context.view_layer.objects.active=parts[0];bpy.ops.object.join();o=bpy.context.object;o.name=name
    new[:]=[x for x in new if x not in parts]
    new.append(o);return o
cab=join_as('READING_5015_SHORT_SLIDING_CABINET',pieces)
# Bespoke vertical composition uses the exact820x320x45 short shelves (catalogp21).
for k,z in enumerate([.74,1.10,1.46]):
    box('READING_5015_SHORT_SHELF_'+str(k),(cx0,cy0,z),(cx1,cy1,z+.045),oak,.004)
for y in [cy0,cy1-.04]:
    box('READING_DISPLAY_SIDE_POST',(cx1-.04,y,.34),(cx1,y+.04,1.54),oak)
#3205A padded bench1350x400x450, beside storage; no shelves above the seated head.
parts=[]
parts.append(box('READING_3205A_TOP',(7.35,9.82,.365),(7.75,11.17,.405),oak,.015))
parts.append(box('READING_3205A_PAD',(7.35,9.82,.405),(7.75,11.17,.45),cushion,.018))
for y in [9.89,11.04]:
    for x in [7.40,7.66]:parts.append(box('READING_3205A_LEG',(x,y,0),(x+.04,y+.04,.365),oak,.004))
parts.append(box('READING_3205A_STRETCHER',(7.53,9.91,.16),(7.57,11.07,.20),oak))
bench=join_as('READING_3205A_PADDED_BENCH',parts)
# A few visible book spines, all within shelf bay, never placed on treads.
for k,(height,color) in enumerate([(.23,(.24,.32,.30)),(.20,(.48,.28,.18)),(.25,(.55,.50,.39)),(.22,(.29,.35,.46))]):
    box('READING_BOOK_'+str(k),(7.43,9.06+k*.075,.785),(7.65,9.115+k*.075,.785+height),material('READING_BOOK_MAT_'+str(k),color),.001)
# Honest north-window reserve outline2.4x1.2m, not a fictional fitness machine.
green=material('NORTH_FITNESS_PROPOSED_OUTLINE',(.14,.40,.31));reserveparts=[]
for lo,hi in [((4.75,11.70,.003),(7.15,11.715,.011)),((4.75,12.885,.003),(7.15,12.90,.011)),((4.75,11.70,.003),(4.765,12.90,.011)),((7.135,11.70,.003),(7.15,12.90,.011))]:
    reserveparts.append(box('NORTH_FITNESS_RESERVE_EDGE',lo,hi,green))
reserve=join_as('NORTH_WINDOW_FITNESS_RESERVE_NOT_EQUIPMENT',reserveparts)
reserve['design_status']='Candidate2.4x1.2m station;owner equipment dimensions and operating clearance required'
# Rebuild exact original rail and supports for three150mm rises; keep their stable nativeIDs.
wall_y=4.70009994506836;rail_y=wall_y+.07;radius=.02;angle=math.atan(.15/.35)
def interp(line,y):
    for (x0,y0),(x1,y1) in zip(line,line[1:]):
        if y0<=y<=y1:return x0+(x1-x0)*(y-y0)/(y1-y0)
first=interp(geom['front_lines'][0],rail_y);floor_x=first-.35;last=first+2*.35
z0=.9-radius*math.cos(angle);z1=1.35-radius*math.cos(angle)
points=[(floor_x-.30,rail_y,z0),(floor_x,rail_y,z0),(last,rail_y,z1),(last+.30,rail_y,z1)]
curve=bpy.data.curves.new('THREE_STEP_RAIL','CURVE');curve.dimensions='3D';curve.bevel_depth=radius;curve.bevel_resolution=5;curve.use_fill_caps=True
sp=curve.splines.new('POLY');sp.points.add(3)
for p,v in zip(sp.points,points):p.co=(*v,1)
temp=bpy.data.objects.new('TEMP_RAIL',curve);bpy.context.scene.collection.objects.link(temp)
bpy.ops.object.select_all(action='DESELECT');temp.select_set(True);bpy.context.view_layer.objects.active=temp;bpy.ops.object.convert(target='MESH')
rail=bpy.data.objects['WAVE_WALL_HANDRAIL_900'];rail.data=temp.data.copy();rail.data.materials.append(bpy.data.materials['HANDRAIL_PALE_ASH']);bpy.data.objects.remove(temp,do_unlink=True);allowed.add(rail.name)
def cylinder_replace(name,a,b,rad):
    a,b=Vector(a),Vector(b);delta=b-a
    o=bpy.data.objects[name];oldmat=o.data.materials[0] if o.data.materials else dark
    bpy.ops.mesh.primitive_cylinder_add(vertices=32,radius=rad,depth=delta.length,location=(a+b)/2);t=bpy.context.object
    o.data=t.data.copy();o.matrix_world=t.matrix_world;o.rotation_euler=delta.to_track_quat('Z','Y').to_euler();o.data.materials.append(oldmat);bpy.data.objects.remove(t,do_unlink=True);allowed.add(name)
for tag,p in [('LOWER',points[0]),('UPPER',points[-1])]:cylinder_replace('WAVE_HANDRAIL_'+tag+'_RETURN',p,(p[0],p[1],p[2]-.1),radius)
cylinder_replace('WAVE_HANDRAIL_LOWER_POST',(floor_x-.15,rail_y,.02),(floor_x-.15,rail_y,z0-radius),.015)
def height(x):return z0 if x<floor_x else z1 if x>last else z0+(x-floor_x)*.15/.35
for i,x in enumerate([5.98,6.24,6.65]):
    z=height(x)-radius-.035
    o=bpy.data.objects['WAVE_HANDRAIL_WALL_PLATE_'+str(i)];o.location=(x,wall_y+.004,z);allowed.add(o.name)
    cylinder_replace('WAVE_HANDRAIL_BRACKET_ARM_'+str(i),(x,wall_y+.008,z),(x,rail_y,z),.007)
    cylinder_replace('WAVE_HANDRAIL_BRACKET_UP_'+str(i),(x,rail_y,z),(x,rail_y,height(x)-radius),.007)
bpy.context.view_layer.update()
for name,state in prior.items():
    if name not in allowed:assert object_state(bpy.data.objects[name])==state,name
registry=json.loads((old/'spatial-canvas.bindings.l-sofa-4.json').read_text())
registry['bindings']=[b for b in registry['bindings'] if b['native_id'] not in retired]
for o in new:
    typ='fitness_reserve' if o==reserve else 'book' if o.name.startswith('READING_BOOK_') else 'bench' if o==bench else 'display_storage'
    registry['bindings'].append({'entity_id':'ent_'+uuid.uuid5(uuid.NAMESPACE_URL,'c_type_home:review5:'+o.name).hex,'adapter':'blender','native_id':o.name,'semantic_type':typ,'room_id':'unassigned','authority_level':'HUMAN_DESIGN_GUIDE'})
registry.update(registry_revision='15-three-step-reading-fitness-review',source_revision='r4-three-step-reading-fitness-review-5',source_locator=str(output))
bpy.ops.wm.save_as_mainfile(filepath=str(output));registry['source_sha256']=sha(output)
(root/'spatial-canvas.bindings.json').write_text(json.dumps(registry,ensure_ascii=False,indent=2)+'\n')
report={'status':'HUMAN_REVIEW','output':str(output),'source':str(source),'source_sha256':sha(source),'output_sha256':sha(output),'stair_count':3,'rise_m':.15,'tread_m':.35,'upper_flat_gain_x_m':.35,'rail_slope_degrees':math.degrees(angle),'reading_storage_catalog':'5015 short cabinet820x320x340 and shelves820x320x45;p21','reading_bench_catalog':'3205A1350x400x450;p26','gym_reserve_m':[2.4,1.2],'gym_is_equipment':False,'north_window_chaise_hidden_in_review_only':True,'sofa_and_coffee_not_shifted':'1150mm south station separation retained','frozen_source_unchanged':sha(source)=='6775691eaaac0d57261eb2e00929bbb753f54687bfa5bf3ff44cc8955ba0ca8c','all_unrelated_states_unchanged':True}
(root/'REVIEW5_QA.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n');print(json.dumps(report,ensure_ascii=False))
