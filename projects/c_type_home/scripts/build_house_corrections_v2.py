"""Owner-directed actual room corrections, whole catalog construction and native finishes."""
import bpy,json,hashlib,sys,math,struct
from pathlib import Path
from mathutils import Vector,Matrix
R=Path(__file__).resolve().parents[1];D=R/'design/whole_house_model_v2';D.mkdir(exist_ok=True)
S=R/'design/whole_house_model_v1/assembly/WHOLE_HOUSE_REVIEW_SUPPORTED_V2.blend';O=D/'WHOLE_HOUSE_CORRECTED_V2.blend'
assert hashlib.sha256(S.read_bytes()).hexdigest()=='7e07cad0852ef3347fb24f8f37280e214355e30b1021d4c2e85c81b05dea9eac'
if O.exists():raise SystemExit('Preserved output exists')
bpy.ops.wm.open_mainfile(filepath=str(S));s=bpy.context.scene;sys.path.insert(0,str(R/'scripts'))
from whole_house_finish_parts_v1 import Parts
col=bpy.data.collections.new('WHOLE_HOUSE_OWNER_CORRECTIONS_V2');s.collection.children.link(col)
wood=bpy.data.materials['V5_NATURAL_ASH_PLANKS_OIL'];linen=bpy.data.materials['V5_NATURAL_FLAX_COTTON']
class ProductParts(Parts):
 def finish(self,o,name,mat):
  o=super().finish(o,name,mat);o.name='HOUSE_V2_'+name;return o
 def assembly(self,name,reference):
  o=super().assembly(name,reference);o.name='HOUSE_V2_'+name;return o
 def soft(self,name,c,size,mat=None):
  o=super().soft(name,c,size,mat);o.name='HOUSE_V2_'+name;return o
P=ProductParts(col,wood,linen);hidden=[];changes=[];records=[]
def hide(n):
 o=bpy.data.objects.get(n)
 if o:o.hide_render=True;o.hide_viewport=True;o.hide_set(True);hidden.append(n)
def prefixhide(pre):
 for o in list(s.objects):
  if o.name.startswith(pre):hide(o.name)
def assign(o,mat):
 o.data=o.data.copy();o.data.materials.clear();o.data.materials.append(mat)
 if o.type=='MESH':P.uv(o)
 changes.append({'object':o.name,'material':mat.name})
def mat(n,color,rough=.5,metal=0,trans=0):
 m=bpy.data.materials.new('HOUSE_V2_'+n);m.use_nodes=True;m.diffuse_color=(*color,1);p=m.node_tree.nodes.get('Principled BSDF');p.inputs['Base Color'].default_value=(*color,1);p.inputs['Roughness'].default_value=rough;p.inputs['Metallic'].default_value=metal;p.inputs['Transmission Weight'].default_value=trans;p.inputs['IOR'].default_value=1.45;return m
white=mat('WHITE_ENAMEL',(.78,.78,.75),.27);black=mat('BLACK_GLAZED_DOOR',(.006,.008,.011),.08,0,.18);paper=mat('IVORY_PAPER',(.60,.57,.50),.94);ink=mat('DARK_PRINT',(.022,.025,.024),.9)
frost=mat('SECONDARY_FROSTED_GLASS',(.9,.92,.9),.43,0,1)
for n in ['R3_SHOWER_GLASS_0','R3_SHOWER_GLASS_1','R3_SHOWER_GLASS_2']:assign(bpy.data.objects[n],frost)
# Semantic named door frames/casings only: handles and hinges keep real metal.
for o in list(s.objects):
 if o.type!='MESH' or o.hide_render:continue
 if (o.name.startswith('V4_D-') and any(t in o.name for t in ['_CASING_','_JAMB_','_FRAME_HEAD'])) or o.name in ['R4_DOOR_FRAME_EAST','R4_DOOR_FRAME_HEAD','R4_DOOR_FRAME_WEST']:assign(o,wood)
for i in [0,1]:
 for n in [f'B11_Rectangle040_BODY_{i}',f'SUNROOM_LAUNDRY_CONTROL_{i}']:assign(bpy.data.objects[n],white)
 for n in [f'B11_Rectangle040_DOOR_{i}',f'SUNROOM_LAUNDRY_DOOR_BEZEL_{i}',f'SUNROOM_LAUNDRY_DOOR_WINDOW_{i}',f'SUNROOM_LAUNDRY_DISPLAY_{i}']:assign(bpy.data.objects[n],black)
 # Real visible controls based on inherited600x600x850 frontload mechanism.
 P.assembly('LAUNDRY_CONTROLS_'+str(i),'source front-load unit; selected reference white casing/black glazed hatch, SKU pending')
 P.rod('Laundry_selector_'+str(i),(8.44,11.788,.738+i*.85),(8.44,11.800,.738+i*.85),.020,white)
 for j in range(3):P.box('Laundry_button_'+str(i)+'_'+str(j),(8.55+j*.025,11.790,.735+i*.85),(.014,.006,.009),black,.002)
def bedside(room,model,cx,cy,z=.45):
 w,d,h=(.45,.40,.48) if model=='2110' else (.42,.40,.46)
 P.assembly(room+'_BEDSIDE_'+model,'owner-selected catalog '+model+' whole drawer carcass, four splayed legs; underside joinery inferred')
 # LocalX depth along roomX, width alongY; fronts toward negativeX.
 x0=cx-d/2;x1=cx+d/2;y0=cy-w/2;y1=cy+w/2;t=.018;bottom=.13 if model=='2110' else .265;top=h
 for yy in [y0+t/2,y1-t/2]:P.box(room+'_case_side',(cx,yy,z+(bottom+top)/2),(d,t,top-bottom),r=.004)
 for zz in [bottom+t/2,top-t/2]:P.box(room+'_case_panel',(cx,cy,z+zz),(d-t*2,w-t*2,t),r=.004)
 P.box(room+'_case_back',(x1-t/2,cy,z+(bottom+top)/2),(t,w-t*2,top-bottom-t*2),r=.002)
 n=2 if model=='2110' else 1;front_height=(top-bottom-.012)/n
 for i in range(n):
  cz=z+bottom+.006+(i+.5)*front_height
  P.box(room+'_drawer_face',(x0+.007,cy,cz),(.018,w-.030,front_height-.007),r=.004)
  P.box(room+'_drawer_floor',(cx-.008,cy,cz-front_height/2+.022),(d-.050,w-.062,.010),r=.001)
  if model=='2110':
   # Small rounded wood inset pulls, two distinct drawers rather than a flat cube.
   P.box(room+'_recess_pull_shadow',(x0-.003,cy,cz),(.004,.095,.018),ink,r=.005)
   P.box(room+'_recess_pull_lip',(x0-.009,cy,cz-.008),(.015,.080,.012),wood,r=.005)
  else:P.rod(room+'_dark_finger_pull',(x0-.004,cy,cz),(x0-.008,cy,cz),.007,ink)
 for signx in [-1,1]:
  for signy in [-1,1]:
   # Bottom tips stay inside actual published envelope.
   a=(cx+signx*(d/2-.040),cy+signy*(w/2-.038),z);b=(cx+signx*(d/2-.063),cy+signy*(w/2-.062),z+bottom+.020)
   P.rod(room+'_splayed_leg',a,b,.014,wood,.022)
 records.append({'kind':'bedside','room':room,'model':model,'dimensions_w_d_h_mm':[w*1000,d*1000,h*1000],'center_xy':[cx,cy]})
prefixhide('HOUSE_V1_BW1_COUPLE_BEDSIDE');prefixhide('HOUSE_V1_BW1_MOTHER_BEDSIDE')
for name,model,positions in [('MOTHER','2110',[(14.90,1.04),(14.90,3.19)]),('COUPLE','2116',[(11.02,.83),(11.02,3.34)])]:
 for i,(x,y) in enumerate(positions):bedside(name+'_'+str(i),model,x,y)
# Mother dressing table: actual catalog2206-0.8, not squeezed1000mm variant.
prefixhide('HOUSE_V1_Mother_vanity');hide('BW1_MOTHER_MIRROR_FRAME');hide('BW1_MOTHER_MIRROR')
P.assembly('MOTHER_VANITY_2206','catalog page17 2206-0.8 800x413x813H; drawer carcass, tapered legs, lift mirror from photograph; exact mirror dimensions inferred')
cx,cy,z=11.875,.730,.45;depth=.413;width=.8;x0=cx-depth/2;x1=cx+depth/2;y0=cy-width/2;y1=cy+width/2
P.box('Vanity_case_bottom',(cx,cy,z+.590),(depth,width,.018),r=.003)
for yy in [y0+.009,y1-.009]:P.box('Vanity_case_side',(cx,yy,z+.693),(depth,.018,.190),r=.004)
P.box('Vanity_case_top',(cx,cy,z+.800),(depth,width,.026),r=.006)
P.box('Vanity_back',(x1-.009,cy,z+.693),(.018,width-.036,.190),r=.003)
for yy,ww in [(cy-.12,.53),(cy+.29,.16)]:
 P.box('Vanity_drawer',(x1-.002,yy,z+.693),(.020,ww,.166),r=.004)
 P.box('Vanity_pull',(x1+.010,yy,z+.724),(.012,ww*.45,.010),r=.003)
for xx in [x0+.050,x1-.050]:
 for yy in [y0+.055,y1-.055]:P.rod('Vanity_leg',(xx,yy,z),(cx+(xx-cx)*.84,cy+(yy-cy)*.84,z+.610),.017,wood,.025)
# Hinged rectangular mirror rises from tabletop, one coherent product.
mirror=bpy.data.materials['RENDER_MIRROR'];mx=x0+.044;mz=z+.813+.245
P.box('Vanity_mirror_glass',(mx+.018,cy-.07,mz),(.004,.46,.41),mirror,0)
for zz in [mz-.225,mz+.225]:P.box('Vanity_mirror_wood',(mx,cy-.07,zz),(.024,.51,.023),r=.004)
for yy in [cy-.07-.244,cy-.07+.244]:P.box('Vanity_mirror_wood',(mx,yy,mz),(.024,.023,.45),r=.004)
records.append({'kind':'vanity','model':'2206-0.8','body_dimensions_mm':[800,413,813],'mirror_height_above_table_mm':470,'mirror_dimensions_status':'photo inferred','floor_m':.45})
# Selected2016 bed: frame outer dimensions include headboard; no platform-box reuse.
def bed2016(room,head_x,cy,matt_width):
 length=2.09;outer=matt_width+.13;floor=.45;x0=head_x-length;x1=head_x;y0=cy-outer/2;y1=cy+outer/2
 P.assembly(room+'_BED_2016','owner selected2016 catalogp15; whole wood headboard/frame/legs/slats, mattress2000mm; joinery hidden faces inferred')
 # Perimeter: lower/slender apron rests on four fully grounded structural posts.
 for yy in [y0+.034,y1-.034]:P.box(room+'_side_rail',((x0+x1)/2,yy,floor+.255),(length-.070,.067,.160),r=.009)
 P.box(room+'_foot_rail',(x0+.035,cy,floor+.255),(.070,outer-.07,.16),r=.009)
 P.box(room+'_head_rail',(x1-.035,cy,floor+.275),(.065,outer-.07,.13),r=.008)
 for xx in [x0+.10,x1-.065]:
  for yy in [y0+.065,y1-.065]:P.rod(room+'_leg',(xx-.018 if xx<x1-.1 else xx,yy,floor),(xx,yy,floor+.285),.022,wood,.029)
 for i in range(16):P.box(room+'_slat',(x0+.10+i*.122,cy,floor+.282),(.085,matt_width+.018,.019),r=.002)
 P.box(room+'_center_support',((x0+x1)/2,cy,floor+.258),(length-.18,.035,.05),r=.004)
 P.rod(room+'_center_leg',((x0+x1)/2,cy,floor),((x0+x1)/2,cy,floor+.285),.025)
 for yy in [y0+.030,y1-.030]:P.box(room+'_head_post',(x1-.032,yy,floor+.660),(.060,.060,.64),r=.008)
 P.box(room+'_head_panel',(x1-.041,cy,floor+.720),(.030,outer-.095,.44),r=.007)
 P.box(room+'_head_top',(x1-.036,cy,floor+.956),(.065,outer,.048),r=.009)
 # True mattress footprint, support on final slat tops. Rounded stitched layers.
 top=floor+.2915;mx=x0+.035+1.00;th=.22
 mattress=P.box(room+'_mattress',(mx,cy,top+th/2),(2.0,matt_width,th),linen,.030)
 for zz in [top+.017,top+th-.017]:
  pts=[(mx-1+.025,cy-matt_width/2+.010,zz),(mx+1-.025,cy-matt_width/2+.010,zz),(mx+1-.010,cy+matt_width/2-.025,zz),(mx-1+.010,cy+matt_width/2-.010,zz)];P.curve(room+'_mattress_seam',pts,.0015,linen,True)
 # Reuse project panel/crown/drop approach, cover built around actual top/edge.
 nx,ny=72,54;vs=[];fs=[]
 for j in range(ny+1):
  v=2*j/ny-1;yy=v*(matt_width/2+.038)
  for i in range(nx+1):
   u=2*i/nx-1;xx=u*1.025;edge=max(abs(xx)/.98,abs(yy)/(matt_width/2-.018));drop=.135*min(1,max(0,(edge-.96)/.11))**.7
   zz=top+th+.009-drop+.003*math.sin(xx*20+yy*3)*max(0,min(1,(edge-.86)*5))
   vs.append((mx+xx,cy+yy,zz))
 for j in range(ny):
  for i in range(nx):k=j*(nx+1)+i;fs.append((k,k+1,k+nx+2,k+nx+1))
 me=bpy.data.meshes.new(room+'_duvet');me.from_pydata(vs,[],fs);me.update();o=bpy.data.objects.new('HOUSE_V2_'+room+'_duvet',me);col.objects.link(o);me.materials.append(linen);P.uv(o)
 for f in me.polygons:f.use_smooth=True
 so=o.modifiers.new('Sewn cloth thickness','SOLIDIFY');so.thickness=.002;so.offset=1
 for yy in ([cy-.39,cy+.39] if matt_width>1.4 else [cy]):P.soft(room+'_pillow',(x1-.42,yy,top+th+.08),(.49,.62,.14))
 records.append({'kind':'bed','room':room,'model':'2016','outer_l_w_h_mm':[2090,round(outer*1000),980],'mattress_w_l_mm':[round(matt_width*1000),2000],'bounds_plan_m':[[x0,y0],[x1,y1]],'slat_top_m':top})
 return [o for o in col.objects if o.name.startswith('HOUSE_V2_'+room+'_')]
prefixhide('HOUSE_V1_COUPLE_');bed2016('COUPLE',11.267,2.087,1.8)
# Latest owner decision:1200x2000 standard bed, original east-head orientation.
# Entire2090x1330 frame, not legacy1800long schematic bed.
for n in ['B11_Rectangle017_CATALOG_00_00','BW1_GUEST_THIN_HEADBOARD','BW1_GUEST_SOFT_HEADREST','BW1_GUEST_BED_RUNNER','BW1_GUEST_CLOUD_WALL_LIGHT','BW1_GUEST_DESK','BW1_GUEST_ART_BLOCK_0','BW1_GUEST_ART_BLOCK_1','BW1_GUEST_ART_BLOCK_2']:hide(n)
bed2016('GUEST',12.82,8.695,1.2)
P.assembly('GUEST_DESK_2201','catalogp17 2201 real desk1200x450x760; leg/trestle and actual drawer proportions from photograph')
cx,cy,z=12.595,10.18,.45
P.box('Guest_desk_top',(cx,cy,z+.745),(.45,1.2,.030),r=.006)
for yy in [cy-.50,cy+.50]:
 for xx in [cx-.17,cx+.17]:P.box('Guest_desk_leg',(xx,yy,z+.36),(.048,.047,.72),r=.005)
 P.box('Guest_desk_foot',(cx,yy,z+.025),(.45,.061,.05),r=.006)
P.box('Guest_desk_rear_beam',(cx+.17,cy,z+.54),(.037,1.02,.075),r=.005)
P.box('Guest_desk_drawer',(cx-.017,cy,z+.665),(.40,.59,.120),r=.004)
P.box('Guest_desk_front_seam',(cx-.22,cy,z+.675),(.012,.58,.003),ink,r=.001)
records.append({'kind':'desk','model':'2201','dimensions_mm':[1200,450,760],'bounds_plan_m':[[12.37,9.58],[12.82,10.78]],'source':'owner catalogp17'})
# Reading at accepted position: retain whole dimensions but restore manufactured
# edge radii and real paper/cloth-covered book structure instead of wood blocks.
for o in list(s.objects):
 if o.name.startswith(('READING_5015_','READING_DISPLAY_')) and o.type=='MESH':
  b=o.modifiers.new('V2 timber edge ease','BEVEL');b.width=.0025;b.segments=4;o.modifiers.new('V2 joinery normals','WEIGHTED_NORMAL')
prefixhide('READING_BOOK_');P.assembly('READING_BOOKS','real bound books: cloth board, paper block, endpapers, spine and printed title; no external licensed jacket art')
colors=[(.19,.22,.17),(.35,.30,.23),(.23,.27,.29),(.44,.39,.30),(.22,.21,.18),(.45,.40,.34)]
for i in range(6):
 y=8.41+i*.047;h=.19+(i%3)*.012;w=.030+(i%2)*.005;cover=mat('BOOK_COVER_'+str(i),colors[i],.85);base=1.291
 P.box('Book_page_block_'+str(i),(7.555,y,base+h/2),(.215,w-.003,h-.006),paper,.001)
 for yy in [y-w/2,y+w/2]:P.box('Book_cover_'+str(i),(7.550,yy,base+h/2),(.226,.002,h),cover,.001)
 P.box('Book_spine_'+str(i),(7.436,y,base+h/2),(.006,w+.002,h),cover,.002)
 for k in range(9):P.box('Book_page_edge_'+str(i)+'_'+str(k),(7.665,y,base+.018+k*(h-.036)/9),(.001,w-.003,.00045),paper,0)
 for k in range(2):P.box('Book_spine_print_'+str(i)+'_'+str(k),(7.432,y,base+h*.68+k*.018),(.001,w*.65,.002),paper,0)
# North sofa whole custom timber structure in source1450x750 space, catalog
# white-ash family evidence; nativeV10 shape knowledge in TWO custom bags.
hide('SUNROOM_COMPACT_TWO_SEAT_SOFA');P.assembly('NORTH_SOFA','catalog ash two-seater family + selected north Faithful; custom1450x750 whole construction; V10 core/jacket and filled back, not resized purchasedSKU')
x0,x1,y0,y1=8.89,10.34,11.14,11.89
for x in [x0+.045,x1-.045]:
 for y in [y0+.050,y1-.050]:P.rod('North_sofa_leg',(x,y,0),(x,y,.285),.023)
for y in [y0+.041,y1-.041]:P.box('North_sofa_apron',((x0+x1)/2,y,.241),(1.37,.045,.075),r=.006)
P.box('North_sofa_deck',((x0+x1)/2,(y0+y1)/2,.285),(1.36,.66,.035),r=.004)
for x in [x0+.026,x1-.026]:P.box('North_sofa_arm',(x,11.495,.545),(.049,.62,.043),r=.012);P.rod('North_arm_post',(x,11.80,.28),(x,11.80,.565),.019)
for x in [x0+.039,x1-.039]:P.rod('North_back_post',(x,11.18,.285),(x,11.18,.778),.020)
P.box('North_back_rail',((x0+x1)/2,11.172,.735),(1.39,.037,.066),r=.008)
with bpy.data.libraries.load(str(R/'design/sofa_fill_form_v10/delivery/SOFA_DIFFERENTIATED_FILL_V10.blend'),link=False) as (a,b):b.objects=['V10_SEAT_COMPLETE_COVER','V10_BACK_COMPLETE_COVER']
protos=b.objects
for j,cx in enumerate([9.257,9.973]):
 for proto in protos:
  # Evaluated pilot preserves full seam/crown geometry. Custom panel widths
  # follow reference-constrained compact sofa, independent of catalog SKU.
  if proto.name not in col.objects:col.objects.link(proto)
  proto.hide_viewport=False;proto.hide_set(False);bpy.context.view_layer.update();e=proto.evaluated_get(bpy.context.evaluated_depsgraph_get());me=bpy.data.meshes.new_from_object(e)
  pts=[e.matrix_world@v.co for v in me.vertices];lo=[min(p[i] for p in pts) for i in range(3)];hi=[max(p[i] for p in pts) for i in range(3)]
  seat='SEAT' in proto.name;target_size=(.686,.56,.17) if seat else (.686,.145,.34);target_center=Vector((cx,11.54,.387 if seat else .642))
  for vertex,p in zip(me.vertices,pts):
   q=Vector(((p[0]-(lo[0]+hi[0])/2)/(hi[0]-lo[0])*target_size[0],(p[1]-(lo[1]+hi[1])/2)/(hi[1]-lo[1])*target_size[1],(p[2]-(lo[2]+hi[2])/2)/(hi[2]-lo[2])*target_size[2]))
   q.y=-q.y;vertex.co=q+target_center+Vector((0,0 if seat else -.258,0))
  obj=bpy.data.objects.new('HOUSE_V2_North_'+('seat_' if seat else 'back_')+str(j),me);col.objects.link(obj);me.materials.clear();me.materials.append(linen);P.uv(obj)
  obj['construction']='static V10 shape adapted for same custom complete north sofa; no foam mechanics claim'
for proto in protos:bpy.data.objects.remove(proto,do_unlink=True)
# Lighting selected from actual3-room same-camera laboratory: restore practical
# brightness and modest existing daylight without changing exposure/materials.
lights=[]
for o in s.objects:
 if o.type=='LIGHT' and o.name.startswith('LIGHT_'):
  before=o.data.energy;o.data.energy=max(before,65 if any(t in o.name for t in ['hallway','bath']) else 45);lights.append({'name':o.name,'before':before,'after':o.data.energy})
for n in ['DAYLIGHT_northliving','DAYLIGHT_northstudy','DAYLIGHT_northsunroom','DAYLIGHT_southbed']:o=bpy.data.objects[n];before=o.data.energy;o.data.energy*=1.3;lights.append({'name':n,'before':before,'after':o.data.energy})
s.view_settings.exposure=.15;s.view_settings.look='AgX - Medium High Contrast'
def camera(n,eye,target,lens=30):
 d=bpy.data.cameras.new(n);o=bpy.data.objects.new(n,d);s.collection.objects.link(o);o.location=eye;o.rotation_euler=(Vector(target)-o.location).to_track_quat('-Z','Y').to_euler();d.lens=lens;d.clip_start=.01
camera('HOUSE_V2_MASTER_WHOLE',(14.30,4.94,1.97),(14.10,6.02,1.55),24)
camera('HOUSE_V2_NORTH_SOFA',(11.00,12.51,1.38),(9.49,11.55,.50),38)
camera('HOUSE_V2_VANITY_WHOLE',(13.00,1.83,1.55),(11.89,.73,1.08),32)
s['owner_corrections_v2']='actual furniture/finish corrections; guest1200x2000 head east, selected after1500wardrobe collision';bpy.ops.wm.save_as_mainfile(filepath=str(O))
report={'source':str(S),'source_sha256':hashlib.sha256(S.read_bytes()).hexdigest(),'output':str(O),'output_sha256':hashlib.sha256(O.read_bytes()).hexdigest(),'hidden_replaced':hidden,'material_changes':changes,'catalog_products':records,'light_changes':lights,'guest_status':'1200x2000 east head; door fit to be verified against finalgeometry','native_materials':[wood.name,linen.name],'image2_requests':0,'source_writeback':False,'structural_inference':'hidden joints, mirror dimensions and custom north frame inferred from catalog/source; not certified exact factory replica'}
(D/'BUILD_AUDIT.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n');print('CORRECTIONS_V2',report['output_sha256'],len(changes),len(hidden))
