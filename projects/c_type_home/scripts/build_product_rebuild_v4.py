"""Whole-object rebuild from catalog construction; no hybrid placeholder upholstery."""
import bpy,math,json,hashlib,struct,random
from pathlib import Path
from mathutils import Vector,Matrix
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'design/product_rebuild_v4'
SOURCE=ROOT/'design/asset_model_v3/LIVING_KITCHEN_LIBRARY_V3.blend'
bpy.ops.wm.open_mainfile(filepath=str(SOURCE));scene=bpy.context.scene;random.seed(404)
# Restore the actual frozen ceiling in presentation. Earlier review hid its entire collection.
ceiling_collection=bpy.data.collections.get('03_EXISTING_CEILING')
if ceiling_collection:ceiling_collection.hide_render=False;ceiling_collection.hide_viewport=False
def show_ceiling_layer(lc):
 if lc.name=='03_EXISTING_CEILING':lc.exclude=False;lc.hide_viewport=False
 for child in lc.children:show_ceiling_layer(child)
show_ceiling_layer(bpy.context.view_layer.layer_collection)
original=[o for o in scene.objects if o.type=='MESH'];vis={o.name:(o.hide_render,o.hide_viewport,o.hide_get()) for o in original}
for o in original:o.hide_viewport=False;o.hide_set(False)
bpy.context.view_layer.update()
def fingerprint(o):
 h=hashlib.sha256()
 for v in o.data.vertices:h.update(struct.pack('<fff',*v.co))
 for p in o.data.polygons:h.update(struct.pack('<'+'I'*len(p.vertices),*p.vertices))
 return h.hexdigest(),[float(x) for row in o.matrix_world for x in row]
before={o.name:fingerprint(o) for o in original}
col=bpy.data.collections.new('V4_COMPLETE_PRODUCT_OBJECTS');scene.collection.children.link(col)
replaced=[]
def conceal(o):
 o.hide_render=True;o.hide_viewport=True;o.hide_set(True)
 if o.name not in replaced:replaced.append(o.name)
 for c in list(o.children):conceal(c)
for n in ['LD_L_SOFA','LD_WINDOW_CHAISE','LD_COFFEE_TABLE','LD_EAST_LOW_CABINET','LD_RACETRACK_DINING_TABLE','LD_CLEANABLE_DOME_PENDANT','LD_SELECTED_RUG','LD_EAST_WALL_SELECTED_ART','LD_SELECTED_LINEN_CURTAINS']+['LD_DINING_CHAIR_%d'%i for i in range(4)]:
 if n in bpy.data.objects:conceal(bpy.data.objects[n])
for o in list(scene.objects):
 if o.name.startswith(('V3_LD_Sofa','V3_LD_Chaise','V3_Chaise_back')):conceal(o)
wood=bpy.data.materials['V3_WHITE_ASH_NATIVE_OWNER_COLOR'].copy();wood.name='V4_ASH_WAX_OIL_FROM_REAL_CATALOG'
cloth=bpy.data.materials['V3_OATMEAL_LINEN_NATIVE_OWNER_COLOR'].copy();cloth.name='V4_OATMEAL_LINEN_NATIVE'
for m in [wood,cloth]:
 for n in m.node_tree.nodes:
  if n.type in ['NORMAL_MAP','TANGENT','UVMAP']:n.uv_map='ProductMeters'
 if hasattr(m,'displacement_method'):m.displacement_method='BUMP'
def material(n,c,rough=.6,metal=0):
 m=bpy.data.materials.new('V4_'+n);m.use_nodes=True;m.diffuse_color=(*c,1);p=m.node_tree.nodes.get('Principled BSDF');p.inputs['Base Color'].default_value=(*c,1);p.inputs['Roughness'].default_value=rough;p.inputs['Metallic'].default_value=metal;return m
seam=material('TAILORED_OATMEAL_SEAM',(.36,.31,.24),.93)
cane=material('NATURAL_CANING',(.42,.31,.18),.71)
enamel=material('CLEANABLE_IVORY_ENAMEL',(.71,.67,.57),.38)
nickel=material('BRUSHED_NICKEL_HARDWARE',(.37,.37,.34),.32,.85)
assemblies={};group=None;contact_pairs=[]
clear=bpy.data.materials.get('RENDER_CLEAR_GLASS')
if clear:
 clear=clear.copy();clear.name='V4_CLEAN_ARCHITECTURAL_GLASS'
 for node in clear.node_tree.nodes:
  if node.type=='BSDF_PRINCIPLED':node.inputs['Roughness'].default_value=.003
 for obj in original:
  if not obj.hide_render and ('LIVING_FIX_BAY' in obj.name or obj.name=='DOOR_V2_NBALC_SINGLE_GLASS' or 'DIN' in obj.name):
   for slot in obj.material_slots:
    if slot.material and 'CLEAR_GLASS' in slot.material.name:slot.material=clear
def assembly(n,reference):
 global group
 o=bpy.data.objects.new('V4_'+n,None);col.objects.link(o);o['real_product_reference']=reference;assemblies[n]=o;group=o;return o
def link(o,n,m):
 o.name='V4_'+n
 for c in list(o.users_collection):c.objects.unlink(o)
 col.objects.link(o)
 if group:o.parent=group
 if m:o.data.materials.append(m)
 return o
def uvmeters(o):
 me=o.data;uv=me.uv_layers.get('ProductMeters') or me.uv_layers.new(name='ProductMeters');me.uv_layers.active=uv;uv.active_render=True
 dims=[max(v.co[i] for v in me.vertices)-min(v.co[i] for v in me.vertices) for i in range(3)];long=max(range(3),key=lambda i:dims[i]);offset=(int(hashlib.sha256(o.name.encode()).hexdigest()[:6],16)%71)/19
 for p in me.polygons:
  ax=max(range(3),key=lambda i:abs(p.normal[i]));axes=[i for i in range(3) if i!=ax]
  if long in axes:axes=[long]+[i for i in axes if i!=long]
  for li in p.loop_indices:
   v=me.vertices[me.loops[li].vertex_index].co;uv.data[li].uv=(v[axes[0]]+offset,v[axes[1]]+offset*.27)
def box(n,c,size,m=wood,bevel=.004):
 bpy.ops.mesh.primitive_cube_add(size=1,location=c);o=bpy.context.object;o.dimensions=size;bpy.ops.object.transform_apply(location=False,rotation=False,scale=True);link(o,n,m)
 b=o.modifiers.new('Manufactured radiused edge','BEVEL');b.width=min(bevel,min(size)*.43);b.segments=5
 w=o.modifiers.new('Planar face normals','WEIGHTED_NORMAL');w.keep_sharp=True
 uvmeters(o);return o
def cylinder_between(n,a,b,r=.025,m=wood,r2=None):
 a,b=Vector(a),Vector(b);v=b-a;bpy.ops.mesh.primitive_cone_add(vertices=48,radius1=r,radius2=r2 or r,depth=v.length,location=(a+b)/2);o=bpy.context.object;o.rotation_euler=v.to_track_quat('Z','Y').to_euler();link(o,n,m)
 for p in o.data.polygons:p.use_smooth=True
 mod=o.modifiers.new('End easing','BEVEL');mod.width=.0018;mod.segments=3;uvmeters(o);return o
def beam(n,a,b,width,depth,m=wood):
 a,b=Vector(a),Vector(b);v=b-a;o=box(n,(a+b)/2,(v.length,width,depth),m,.005);o.rotation_euler=v.to_track_quat('X','Z').to_euler();return o
def curve(n,points,r=.001,m=seam,closed=False):
 c=bpy.data.curves.new(n,'CURVE');c.dimensions='3D';c.bevel_depth=r;c.bevel_resolution=3
 spline=c.splines.new('POLY');spline.points.add(len(points)-1)
 for p,v in zip(spline.points,points):p.co=(*v,1)
 spline.use_cyclic_u=closed;o=bpy.data.objects.new('V4_'+n,c);col.objects.link(o);c.materials.append(m)
 if group:o.parent=group
 return o
def physical_cloth_uv(o):
 bpy.ops.object.select_all(action='DESELECT');o.select_set(True);bpy.context.view_layer.objects.active=o
 uv=o.data.uv_layers.new(name='ProductMeters');o.data.uv_layers.active=uv;uv.active_render=True
 bpy.ops.object.mode_set(mode='EDIT');bpy.ops.mesh.select_all(action='SELECT');bpy.ops.uv.smart_project(angle_limit=math.radians(66),island_margin=.004);bpy.ops.object.mode_set(mode='OBJECT')
 o.data.update();uv=o.data.uv_layers.get('ProductMeters');a=0
 for p in o.data.polygons:
  vs=[uv.data[li].uv for li in p.loop_indices];a+=abs(sum(vs[i].x*vs[(i+1)%len(vs)].y-vs[(i+1)%len(vs)].x*vs[i].y for i in range(len(vs)))*.5)
 scale=math.sqrt(sum(p.area for p in o.data.polygons)/max(a,1e-9))
 for d in uv.data:d.uv*=scale
with bpy.data.libraries.load(str(OUT/'PRESSURE_CUSHION_FORM.blend'),link=False) as (a,b):
 b.objects=['PRESSURE_GENERATED_STATIC_CUSHION']
prototype=b.objects[0];proto=prototype.data
lo=[min(v.co[i] for v in proto.vertices) for i in range(3)];hi=[max(v.co[i] for v in proto.vertices) for i in range(3)]
def cushion(n,size,loc,mode='seat'):
 verts=[]
 for v in proto.vertices:
  q=Vector(tuple((v.co[i]-(hi[i]+lo[i])/2)/(hi[i]-lo[i])*size[i] for i in range(3)))
  # Radiused sewn corners follow a manufactured fabric panel, not a generic sharp box.
  rad=min(.042,size[0]*.12,size[1]*.12);cx=size[0]/2-rad;cy=size[1]/2-rad
  if abs(q.x)>cx and abs(q.y)>cy:
   dx=abs(q.x)-cx;dy=abs(q.y)-cy;length=math.hypot(dx,dy)
   if length>rad:q.x=math.copysign(cx+dx/length*rad,q.x);q.y=math.copysign(cy+dy/length*rad,q.y)
  if mode=='back':
   # Lower edge compression from seat support, two localized sewn-edge tucks.
   u=q.x/(size[0]/2);t=q.y/(size[1]/2)
   if q.z>0:
    q.z-=.003*math.exp(-((u-.72)/.18)**2-((t+.69)/.3)**2)
    q.z-=.0025*math.exp(-((u+.66)/.20)**2-((t-.6)/.23)**2)
  verts.append(tuple(q))
 me=bpy.data.meshes.new(n);me.from_pydata(verts,[],[tuple(p.vertices) for p in proto.polygons]);me.update();o=bpy.data.objects.new('V4_'+n,me);col.objects.link(o);o.parent=group;o.location=loc;me.materials.append(cloth)
 for p in me.polygons:p.use_smooth=True
 sub=o.modifiers.new('Soft stitched surface','SUBSURF');sub.levels=1
 bpy.context.view_layer.objects.active=o;o.select_set(True);bpy.ops.object.modifier_apply(modifier=sub.name)
 me=o.data
 # Restore requested construction dimensions after surface refinement.
 for i in range(3):
  mn=min(v.co[i] for v in me.vertices);mx=max(v.co[i] for v in me.vertices)
  for v in me.vertices:v.co[i]=(v.co[i]-mn)/(mx-mn)*size[i]-size[i]/2
 physical_cloth_uv(o)
 rad=min(.042,size[0]*.12,size[1]*.12);points=[]
 for cx,cy,t0 in [(size[0]/2-rad,size[1]/2-rad,0),(-size[0]/2+rad,size[1]/2-rad,90),(-size[0]/2+rad,-size[1]/2+rad,180),(size[0]/2-rad,-size[1]/2+rad,270)]:
  for i in range(17):
   t=math.radians(t0+i*90/16);points.append((cx+rad*math.cos(t),cy+rad*math.sin(t),0))
 piping=curve(n+'_sewn_welt',points,.0009,seam,True);piping.location=loc
 o['form_method']='same-product construction; closed cloth pressure prototype with sewn perimeter';return o,piping
assembly('LIVING_SOFA_COMPLETE','owner ash catalog p4/p8 + selected A; custom L sofa, not original SKU')
# Complete frame and support system for the custom 1800x3300 footprint.
deckA=box('Sofa_chaise_deck',(4.32,8.535,.264),(1.76,1.09,.042),bevel=.009)
deckB=box('Sofa_long_deck',(3.98,10.11,.264),(1.08,2.23,.042),bevel=.009)
for x,y in [(3.474,8.026),(5.105,8.026),(5.105,9.021),(3.474,9.021),(3.474,10.10),(4.43,10.10),(3.474,11.174),(4.43,11.174)]:
 cylinder_between('Sofa_real_ash_leg',(x,y,0),(x,y,.26),.029,r2=.033)
for x in [3.48,4.43]:
 box('Sofa_long_support_rail',(x,9.6,.219),(.044,3.17,.087),bevel=.003)
for y in [8.03,9.02]:
 box('Chaise_cross_support',(4.31,y,.219),(1.67,.043,.087),bevel=.003)
box('Sofa_back_top_rail',(3.435,9.595,.587),(.062,3.19,.065),bevel=.009)
box('Sofa_back_lower_rail',(3.435,9.595,.354),(.045,3.16,.049),bevel=.005)
for y in [8.03,9.05,10.10,11.16]:
 box('Sofa_back_frame_upright',(3.435,y,.448),(.055,.048,.32),bevel=.006)
# Back slats are part of real construction, restrained spacing behind supported upholstery.
for j in range(14):
 y=8.07+j*(3.06/13);box('Sofa_back_ash_slat',(3.435,y,.463),(.020,.023,.22),bevel=.003)
for y,width in [(7.98,1.71),(11.22,1.04)]:
 box('Sofa_arm_real_ash',(3.45+width/2,y,.566),(width,.058,.038),bevel=.011)
 for x in [3.474,3.45+width-.043]:
  box('Sofa_arm_frame_post',(x,y,.418),(.044,.045,.29),bevel=.006)
# Seat modules have 8-10mm sewn separations instead of preserving 60-70mm placeholder gaps.
seatdefs=[('Sofa_chaise_upholstery',(1.555,1.032,.155),(4.351,8.559,.3625)),('Sofa_seat_middle',(.891,1.025,.155),(4.016,9.595,.3625)),('Sofa_seat_north',(.891,1.025,.155),(4.016,10.63,.3625))]
for n,size,pos in seatdefs:
 o,p=cushion(n,size,pos);contact_pairs.append([o.name,deckA.name if 'chaise' in n else deckB.name])
rotation=Matrix(((0,0,1),(1,0,0),(0,1,0))).to_4x4()
for i,y in enumerate([8.575,9.61,10.645]):
 o,p=cushion('Sofa_back_%d'%i,(1.027,.296,.214),(3.56,y,.548),'back')
 for v in o.data.vertices:v.co.z-=.04*(v.co.y/(.296/2))
 o.rotation_euler=rotation.to_euler();p.rotation_euler=o.rotation_euler;p.location=o.location
 # Back sits on seat edge and leans against the entire timber frame.
 o['support']='seat top and rear timber rails'
assembly('WINDOW_CHAISE_COMPLETE','selected A + owner timber-frame upholstery construction; custom reclining chaise')
# Complete reclined seat/back chassis with structural contact at the bend.
backA=Vector((4.737,11.505,.735));backB=Vector((5.19,11.505,.303))
for y in [11.085,11.925]:
 beam('Chaise_reclined_side',(backA.x,y,backA.z),(backB.x,y,backB.z),.036,.040)
 beam('Chaise_seat_side',(5.19,y,.303),(6.326,y,.303),.036,.045)
 beam('Chaise_ash_arm',(5.23,y,.582),(6.19,y,.582),.038,.032)
 for x in [5.27,6.16]:beam('Chaise_arm_connection',(x,y,.307),(x,y,.582),.024,.025)
 beam('Chaise_rear_splayed_leg',(4.995,y,.012),(5.25,y,.301),.043,.043)
 beam('Chaise_front_splayed_leg',(6.323,y,.012),(6.16,y,.301),.043,.043)
for x in [5.19,5.47,5.78,6.08,6.30]:
 beam('Chaise_underseat_slat',(x,11.10,.305),(x,11.91,.305),.055,.027)
for t in [0,.25,.50,.75,1]:
 a=backA.lerp(backB,t);beam('Chaise_underback_slat',(a.x,11.10,a.z),(a.x,11.91,a.z),.055,.022)
o,p=cushion('Chaise_full_seat', (1.151,.784,.112),(5.758,11.505,.374))
vec=backB-backA;normal=Vector((-vec.z,0,vec.x)).normalized();center=(backA+backB)/2+normal*.050
o,p=cushion('Chaise_full_back',(.616,.784,.094),center,'back');o.rotation_euler.y=-math.atan2(vec.z,vec.x);p.rotation_euler=o.rotation_euler;p.location=o.location
assembly('COFFEE_TABLE_COMPLETE','selected A two-tier table; owner catalog p11 tabletop/frame construction; custom1000x550')
box('Coffee_solid_top',(5.30,9.99,.385),(.55,1,.030),bevel=.008)
box('Coffee_lower_solid_shelf',(5.30,9.99,.123),(.466,.916,.025),bevel=.005)
for x in [5.067,5.533]:
 for y in [9.536,10.444]:
  box('Coffee_mortise_leg',(x,y,.185),(.033,.033,.370),bevel=.004)
for x in [5.067,5.533]:box('Coffee_side_apron',(x,9.99,.341),(.021,.878,.060),bevel=.003)
for y in [9.536,10.444]:
 box('Coffee_end_apron',(5.30,y,.341),(.447,.024,.060),bevel=.003)
 box('Coffee_shelf_cross_support',(5.30,y,.097),(.45,.028,.028),bevel=.003)
assembly('EAST_CONSOLE_COMPLETE','selected A open low console; owner catalog p13 timber furniture joinery; custom original footprint')
x0,x1,y0,y1=7.398,7.696875,8.634937,11.523844;cy=(y0+y1)/2
box('Console_solid_ash_top',((x0+x1)/2,cy,.464),(.298875,y1-y0,.032),bevel=.005)
box('Console_solid_bottom_shelf',((x0+x1)/2,cy,.127),(.269,y1-y0-.055,.026),bevel=.004)
box('Console_back', (x1-.006,cy,.289),(.012,y1-y0-.05,.315),bevel=.0015)
for y in [y0+.015,y0+(y1-y0)/3,y0+2*(y1-y0)/3,y1-.015]:
 box('Console_panel_support',((x0+x1)/2,y,.278),(.273,.022,.340),bevel=.003)
for y in [y0+.12,(y0+y1)/2,y1-.12]:
 for x in [x0+.034,x1-.034]:box('Console_ash_foot',(x,y,.071),(.035,.037,.142),bevel=.005)
def capsule(n,c,length,width,height,mat=wood):
 N=128;rad=width/2;half=(length-width)/2;verts=[]
 for z in [-height/2,height/2]:
  for side,start in [(half,-90),(-half,90)]:
   for i in range(65):
    a=math.radians(start+i*180/64);verts.append((side+rad*math.cos(a),rad*math.sin(a),z))
 N=len(verts)//2;faces=[tuple(reversed(range(N))),tuple(range(N,2*N))]+[(i,(i+1)%N,(i+1)%N+N,i+N) for i in range(N)]
 me=bpy.data.meshes.new(n);me.from_pydata(verts,[],faces);me.update();o=bpy.data.objects.new('V4_'+n,me);col.objects.link(o);o.parent=group;o.location=c;me.materials.append(mat)
 b=o.modifiers.new('Racetrack perimeter easing','BEVEL');b.width=.003;b.segments=5;w=o.modifiers.new('Planar top normal','WEIGHTED_NORMAL');w.keep_sharp=True;uvmeters(o);return o
assembly('DINING_TABLE_COMPLETE','C selected racetrack + owner catalog p11 1119 twin-column construction; custom1600x800x750')
tx,ty=3.827625,3.464406
table=capsule('Dining_racetrack_38mm_top',(tx,ty,.731),1.6,.8,.038)
for x in [tx-.47,tx+.47]:
 # Closed elliptic timber columns and connected concealed feet, knee lanes kept clear.
 bpy.ops.mesh.primitive_cylinder_add(vertices=96,radius=1,depth=1,location=(x,ty,.348));o=bpy.context.object;o.scale=(.13,.175,.696);bpy.ops.object.transform_apply(location=False,rotation=False,scale=True);link(o,'Dining_elliptical_column',wood)
 for p in o.data.polygons:p.use_smooth=abs(p.normal.z)<.9
 b=o.modifiers.new('Column softened perimeter','BEVEL');b.width=.006;b.segments=5;uvmeters(o)
 foot=capsule('Dining_oval_weighted_foot',(x,ty,.015),.44,.29,.030);foot.rotation_euler.z=math.pi/2
 box('Dining_upper_bearing',(x,ty,.697),(.27,.43,.030),bevel=.008)
box('Dining_under_top_connector',(tx,ty,.691),(1.22,.078,.043),bevel=.008)
# Actual-size catalog chair trial; same four seats, pull out180mm to clear real support columns.
chaircenters=[(3.427625,3.924406,1),(4.227625,3.924406,1),(3.427625,3.004406,-1),(4.227625,3.004406,-1)]
for index,(cx,cy,sign) in enumerate(chaircenters):
 assembly('DINING_CHAIR_%d_COMPLETE'%index,'owner catalog p28 6010A560x560x850 + selected C; full product-style trial')
 def point(x,y,z):return (cx+x,cy+sign*y,z)
 for s in [-1,1]:
  beam('Chair_front_leg',point(s*.252,-.251,.0035),point(s*.218,-.202,.466),.043,.043)
  beam('Chair_back_leg',point(s*.247,.245,.0035),point(s*.209,.162,.459),.044,.043)
  beam('Chair_back_post',point(s*.209,.162,.449),point(s*.217,.252,.826),.031,.037)
  beam('Chair_seat_side_rail',point(s*.215,-.202,.435),point(s*.209,.162,.435),.029,.059)
  beam('Chair_arm',point(s*.238,-.214,.644),point(s*.238,.230,.644),.064,.027)
  beam('Chair_arm_front_support',point(s*.218,-.202,.449),point(s*.238,-.153,.631),.028,.031)
 beam('Chair_front_seat_rail',point(-.215,-.202,.435),point(.215,-.202,.435),.027,.058)
 beam('Chair_back_seat_rail',point(-.209,.162,.435),point(.209,.162,.435),.028,.058)
 box('Chair_foam_seat_support',point(0,-.017,.447),(.456,.414,.022),bevel=.008)
 o,p=cushion('Chair_upholstered_seat_%d'%index,(.456,.414,.055),point(0,-.017,.4765))
 # Continuous squared ash frame, cane tied into a real rebate within the four sides.
 for s in [-1,1]:beam('Chair_cane_frame_side',point(s*.223,.194,.592),point(s*.223,.256,.831),.031,.034)
 beam('Chair_cane_frame_top',point(-.223,.256,.833),point(.223,.256,.833),.036,.034)
 beam('Chair_cane_frame_bottom',point(-.223,.194,.592),point(.223,.194,.592),.031,.032)
 def cane_point(x,z,offset=0):
  y=.194+(z-.592)/(.241)*.062+offset;return point(x,y,z)
 # Real six-way woven strips; holes are actual geometry, not a photograph pasted on a panel.
 for j in range(31):
  x=-.203+j*.01355;pts=[cane_point(x,.608+k*.0147,.0008*math.sin(k*math.pi/2)) for k in range(15)];curve('Cane_vertical_%d_%d'%(index,j),pts,.0016,cane)
 for j in range(15):
  z=.608+j*.0147;pts=[cane_point(-.203+k*.01355,z,-.0008*math.sin(k*math.pi/2)) for k in range(31)];curve('Cane_horizontal_%d_%d'%(index,j),pts,.0016,cane)
 for slope in [-1,1]:
  for j in range(-15,32):
   pts=[]
   for k in range(15):
    z=.608+k*.0147;x=-.203+j*.01355+slope*k*.01355
    if -.203<=x<=.204:pts.append(cane_point(x,z,.0018*slope))
   if len(pts)>1:curve('Cane_diagonal_%d_%d_%d'%(index,slope,j),pts,.0011,cane)
assembly('DINING_PENDANT_COMPLETE','selected C round/oval mood; cleanable enamel dome with real shell/opening, SKU unconfirmed')
verts=[];faces=[];rings=40;segments=128;rx=.365;ry=.320
for layer in [0,1]:
 for j in range(rings+1):
  t=.028+(math.pi/2-.028)*j/rings
  for i in range(segments):
   a=math.tau*i/segments;verts.append(((rx-layer*.0035)*math.sin(t)*math.cos(a),(ry-layer*.0035)*math.sin(t)*math.sin(a),(.267-layer*.0035)*math.cos(t)))
N=(rings+1)*segments
for layer in [0,1]:
 for j in range(rings):
  for i in range(segments):
   a=layer*N+j*segments+i;b=layer*N+j*segments+(i+1)%segments;f=(a,b,b+segments,a+segments);faces.append(f if layer==0 else tuple(reversed(f)))
for j in [0,rings]:
 for i in range(segments):
  a=j*segments+i;b=j*segments+(i+1)%segments;faces.append((a,a+N,b+N,b))
me=bpy.data.meshes.new('Open enamel double-wall dome');me.from_pydata(verts,[],faces);me.update();o=bpy.data.objects.new('V4_Dining_enamel_dome',me);col.objects.link(o);o.parent=group;o.location=(tx,ty,1.87);me.materials.append(enamel)
for p in me.polygons:p.use_smooth=True
uvmeters(o)
cylinder_between('Pendant_top_canopy',(tx,ty,2.746),(tx,ty,2.778),.062,enamel)
cylinder_between('Pendant_suspension',(tx,ty,2.131),(tx,ty,2.750),.0035,nickel)
opal=material('OPAL_GLASS_LIGHT',(.89,.85,.74),.42);p=opal.node_tree.nodes.get('Principled BSDF');p.inputs['Emission Color'].default_value=(1,.84,.67,1);p.inputs['Emission Strength'].default_value=2
bpy.ops.mesh.primitive_uv_sphere_add(segments=48,ring_count=24,radius=.045,location=(tx,ty,1.95));link(bpy.context.object,'Pendant_supported_bulb',opal)
cylinder_between('Pendant_bulb_socket',(tx,ty,2.135),(tx,ty,1.989),.023,enamel)
d=bpy.data.lights.new('V4_Dining_warm_practical','AREA');d.energy=42;d.shape='DISK';d.size=.20;d.color=(1,.84,.66);o=bpy.data.objects.new(d.name,d);col.objects.link(o);o.location=(tx,ty,1.875);o.parent=group
assembly('SELECTED_SOFT_FINISHES','selected B only: curtain/rug/artwork, no lamp/throw pillows/blanket/props')
def imagematerial(n,file,rough):
 m=material(n,(.6,.5,.4),rough);ns=m.node_tree.nodes;ls=m.node_tree.links;t=ns.new('ShaderNodeTexImage');t.image=bpy.data.images.load(str(OUT/'textures'/file),check_existing=True);ls.new(t.outputs['Color'],ns.get('Principled BSDF').inputs['Base Color']);return m
art=imagematerial('ARTWORK_FROM_SELECTED_REFERENCE','selected_art_rectified.jpg',.88)
o=box('Selected_abstract_canvas',(7.704,10.04,1.72),(.028,1.5,1.2),art,.0015);uv=o.data.uv_layers.active
for p in o.data.polygons:
 for li in p.loop_indices:
  v=o.data.vertices[o.data.loops[li].vertex_index].co;uv.data[li].uv=(v.y/1.5+.5,v.z/1.2+.5)
for y in [9.275,10.805]:box('Art_ash_vertical_frame',(7.686,y,1.72),(.037,.022,1.244),bevel=.002)
for z in [1.109,2.331]:box('Art_ash_horizontal_frame',(7.686,10.04,z),(.037,1.552,.022),bevel=.002)
rugmat=imagematerial('RUG_WOVEN_SELECTED_PALETTE','geometric_rug_woven.jpg',.95);ns=rugmat.node_tree.nodes;ls=rugmat.node_tree.links;p=ns.get('Principled BSDF');p.inputs['Sheen Weight'].default_value=.22
coord=ns.new('ShaderNodeTexCoord');noise=ns.new('ShaderNodeTexNoise');noise.inputs['Scale'].default_value=900;ls.new(coord.outputs['Object'],noise.inputs['Vector']);b=ns.new('ShaderNodeBump');b.inputs['Distance'].default_value=.0008;b.inputs['Strength'].default_value=.25;ls.new(noise.outputs['Fac'],b.inputs['Height']);ls.new(b.outputs[0],p.inputs['Normal'])
o=box('Selected_flatwoven_rug',(5.63,9.93,.008),(2.85,2.65,.012),rugmat,.007);uv=o.data.uv_layers.active
for p in o.data.polygons:
 for li in p.loop_indices:
  v=o.data.vertices[o.data.loops[li].vertex_index].co;uv.data[li].uv=(v.x/2.85+.5,v.y/2.65+.5)
curtain=cloth.copy();curtain.name='V4_LIGHT_FLAX_DRAPERY'
ps=next(n for n in curtain.node_tree.nodes if n.type=='BSDF_PRINCIPLED');tint=next(n for n in curtain.node_tree.nodes if n.type=='MIX_RGB' and n.blend_type=='MULTIPLY');tint.inputs[2].default_value=(.64,.58,.48,1)
output=next(n for n in curtain.node_tree.nodes if n.type=='OUTPUT_MATERIAL');ns=curtain.node_tree.nodes;ls=curtain.node_tree.links;trans=ns.new('ShaderNodeBsdfTranslucent');ls.new(ps.inputs['Base Color'].links[0].from_socket,trans.inputs[0]);mix=ns.new('ShaderNodeMixShader');mix.inputs[0].default_value=.17;ls.new(ps.outputs[0],mix.inputs[1]);ls.new(trans.outputs[0],mix.inputs[2]);ls.new(mix.outputs[0],output.inputs['Surface'])
cylinder_between('Curtain_track',(3.16,12.95,2.70),(7.5,12.95,2.70),.009,nickel)
for panel,(start,width,count) in enumerate([(3.19,.60,12),(6.95,.54,11)]):
 verts=[];faces=[];nx=132;nz=100
 # Tailored header holds actual pleats; independent pleat depths break repeated rigid tubes.
 depths=[.027+random.random()*.012 for _ in range(count+1)]
 for j in range(nz+1):
  t=j/nz
  for i in range(nx+1):
   u=i/nx;cell=u*count;k=min(count-1,int(cell));s=cell-k;depth=depths[k]*(.80+.45*t)
   y=12.90+depth*math.cos(math.tau*s)+.004*t*t*math.sin(k*1.37+4*t)
   x=start+u*width+(u-.5)*.024*t*t;z=2.65-2.61*t+.005*t**9*math.sin(k*1.1+s*math.pi)
   verts.append((x,y,z))
 for j in range(nz):
  for i in range(nx):
   a=j*(nx+1)+i;faces.append((a,a+1,a+nx+2,a+nx+1))
 me=bpy.data.meshes.new('Tailored headed linen panel');me.from_pydata(verts,[],faces);me.update();o=bpy.data.objects.new('V4_Curtain_panel_%d'%panel,me);col.objects.link(o);o.parent=group;me.materials.append(curtain)
 for p in me.polygons:p.use_smooth=True
 uvmeters(o);s=o.modifiers.new('Cloth woven thickness','SOLIDIFY');s.thickness=.0008
 curve('Curtain_bottom_stitched_hem_%d'%panel,verts[-(nx+1):],.001,seam)
 for k in range(count+1):cylinder_between('Curtain_header_glider',(start+k*width/count,12.95,2.65),(start+k*width/count,12.95,2.70),.0025,nickel)
# Garden HDRI for illustrative background and subtle neutral bounce; no invented exterior geometry.
world=scene.world.copy();world.name='V4_PHYSICAL_WINDOW_DAYLIGHT_ILLUSTRATIVE_GARDEN';scene.world=world
ns=world.node_tree.nodes;ls=world.node_tree.links;envs=[n for n in ns if n.type=='TEX_ENVIRONMENT']
hdr=json.loads((OUT/'assets/garden_hdri/asset-manifest.json').read_text())['files'][0]['path']
for env in envs:
 env.image=bpy.data.images.load(hdr,check_existing=True);coord=ns.new('ShaderNodeTexCoord');mapping=ns.new('ShaderNodeMapping');mapping.inputs['Rotation'].default_value[2]=math.radians(120);ls.new(coord.outputs['Generated'],mapping.inputs[0]);ls.new(mapping.outputs[0],env.inputs['Vector'])
# Replace only camera/transmission neutral-background branches; illumination remains authored diffuse environment.
for n in ns:
 if n.type=='BACKGROUND':
  if n.name.startswith('LD Neutral') or not n.inputs['Color'].is_linked:
   ls.new(envs[0].outputs['Color'],n.inputs['Color']);n.inputs['Strength'].default_value=.6
sun=bpy.data.objects.get('LD_Sun_through_actual_windows')
if sun:sun.data.energy=2.4;sun.data.angle=math.radians(1.3);sun.data.color=(1,.94,.85);sun.rotation_euler=Vector((-.34,-1,-.30)).to_track_quat('-Z','Y').to_euler()
def camera(n,eye,target,lens,vertical=False):
 d=bpy.data.cameras.new(n);o=bpy.data.objects.new(n,d);col.objects.link(o);o.location=eye;v=Vector(target)-o.location
 if vertical:
  shift=v.z/max(math.hypot(v.x,v.y),.01)*lens/36;v.z=0;d.shift_y=shift
 o.rotation_euler=v.to_track_quat('-Z','Y').to_euler();d.lens=lens;d.sensor_width=36;d.clip_start=.025;return o
camera('V4_CAM_SOFA_COMPLETE',(6.73,8.15,1.42),(4.10,9.65,.44),39)
camera('V4_CAM_SOFA_BACK',(3.07,10.95,1.04),(3.94,9.56,.42),28)
camera('V4_CAM_DINING_COMPLETE',(5.28,4.33,1.6),(3.78,3.45,1.1),18,True)
camera('V4_CAM_DINING_DETAIL',(5.25,4.30,1.10),(3.76,3.43,.56),30)
camera('V4_CAM_CHAIR_COMPLETE',(5.08,4.37,1.15),(4.23,3.92,.51),49)
scene.render.engine='CYCLES';scene.render.resolution_x=1920;scene.render.resolution_y=1080;scene.render.resolution_percentage=100
scene.cycles.samples=128;scene.cycles.use_denoising=True;scene.cycles.denoising_quality='HIGH';scene.cycles.denoising_prefilter='ACCURATE';scene.cycles.denoising_use_gpu=True;scene.cycles.adaptive_threshold=.015
prefs=bpy.context.preferences.addons['cycles'].preferences;prefs.compute_device_type='METAL';prefs.get_devices()
for d in prefs.devices:d.use=d.type=='METAL'
scene.cycles.device='GPU';scene.render.threads_mode='FIXED';scene.render.threads=2;scene.view_settings.view_transform='AgX';scene.view_settings.look='AgX - Medium High Contrast';scene.view_settings.exposure=.15
scene.camera=bpy.data.objects['CAM_living_VIEW_01'];scene['rebuild_authority']='whole real-product construction prototypes; not procurement SKU';scene['background']='ILLUSTRATIVE PolyHaven garden, not surveyed exterior'
for n,f in before.items():assert fingerprint(bpy.data.objects[n])==f,n
for n,(h,vg,vl) in vis.items():
 if n in replaced:continue
 o=bpy.data.objects[n];o.hide_viewport=vg;o.hide_set(vl)
bpy.ops.file.pack_all();dest=OUT/'LIVING_DINING_PRODUCT_REBUILD_V4.blend';bpy.ops.wm.save_as_mainfile(filepath=str(dest))
report={'status':'BUILT_PENDING_VISUAL_REVIEW','source':str(SOURCE),'output':str(dest),'output_sha256':hashlib.sha256(dest.read_bytes()).hexdigest(),'all_existing_meshes_and_matrices_unchanged':len(before),'replaced_hidden_objects':replaced,'complete_assemblies':list(assemblies),'soft_form_method':'own closed cloth pressure prototype, not unrelated supplier cushions','seat_gap_mm':[8,10],'back_gap_mm':8,'sofa_constraint_mm':[1800,3300,700],'dining_table_mm':[1600,800,750],'chair_real_product_dimensions_mm':[560,560,850],'chair_center_changes_mm':[[0,180],[0,180],[0,-180],[0,-180]],'chair_centers':chaircenters,'art_texture':'selected B artwork rectified for appearance, no dimension inference','rug_texture':'original woven reconstruction of B palette','background':'illustrative garden HDRI','restored_ceiling_collection':'03_EXISTING_CEILING, existing geometry unchanged','product_status':'all custom except6010A-size chair trial; not final purchased items','contact_pairs':contact_pairs,'new_object_count':len(col.objects)}
(OUT/'BUILD_AUDIT.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n');(OUT/'PRESERVED_GEOMETRY.json').write_text(json.dumps(before))
print('V4_WHOLE_OBJECT_BUILD',len(col.objects),dest)
