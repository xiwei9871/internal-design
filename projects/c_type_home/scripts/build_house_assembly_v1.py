"""Owner-confirmed all-room candidate from the latest integrated house.

Existing authority stays untouched. New custom furniture uses source footprints,
real/catalog construction and approved appearance, never AI-derived dimensions.
"""
import bpy,json,hashlib,math,sys,struct
from pathlib import Path
from mathutils import Vector,Matrix
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'design/whole_house_model_v1';RUN=OUT/'assembly';RUN.mkdir(exist_ok=True)
SOURCE=ROOT/'design/lookdev_v5/LIVING_DINING_LOOKDEV_V5.blend';DEST=RUN/'WHOLE_HOUSE_ASSEMBLED_V1.blend'
assert hashlib.sha256(SOURCE.read_bytes()).hexdigest()=='94661776fe34a45b73b540765ca6391a63e34a0940b5b84d461abd8b4657cd76'
if DEST.exists():raise SystemExit('Preserved assembly exists; use a new output version.')
bpy.ops.wm.open_mainfile(filepath=str(SOURCE));scene=bpy.context.scene
sys.path.insert(0,str(ROOT/'scripts'));from whole_house_finish_parts_v1 import Parts
col=bpy.data.collections.new('WHOLE_HOUSE_SELECTED_ROOM_OBJECTS_V1');scene.collection.children.link(col)
wood=bpy.data.materials['V5_NATURAL_ASH_PLANKS_OIL'];cloth=bpy.data.materials['V5_NATURAL_FLAX_COTTON'];P=Parts(col,wood,cloth)
def material(name,color,rough=.8):
 m=bpy.data.materials.new('HOUSE_V1_'+name);m.use_nodes=True;m.diffuse_color=(*color,1);p=m.node_tree.nodes.get('Principled BSDF');p.inputs['Base Color'].default_value=(*color,1);p.inputs['Roughness'].default_value=rough;return m
ivory=material('IVORY_CERAMIC',(.65,.62,.55),.6);green=cloth.copy();green.name='HOUSE_V1_MUTED_SAGE_LINEN'
for n in green.node_tree.nodes:
 if n.type=='MIX_RGB' and n.blend_type=='MULTIPLY':n.inputs[2].default_value=(.19,.23,.17,1)
green.diffuse_color=(.19,.23,.17,1)
changes=[];hidden=[];room_new={};bounds_before={};states={}
def meshhash(me):
 h=hashlib.sha256()
 for v in me.vertices:h.update(struct.pack('<fff',*v.co))
 for f in me.polygons:h.update(struct.pack('<'+'I'*len(f.vertices),*f.vertices))
 return h.hexdigest()
def visible(o):return not o.hide_render and not any(c.hide_render for c in o.users_collection)
# Hidden sources need evaluated matrices, but restore their presentation status.
visibility={o.name:(o.hide_render,o.hide_viewport,o.hide_get()) for o in scene.objects}
collection_vis={c.name:(c.hide_render,c.hide_viewport) for c in bpy.data.collections}
for c in bpy.data.collections:c.hide_viewport=False
for o in scene.objects:o.hide_viewport=False;o.hide_set(False)
bpy.context.view_layer.update()
def bounds(o):
 e=o.evaluated_get(bpy.context.evaluated_depsgraph_get());me=e.to_mesh();pts=[e.matrix_world@v.co for v in me.vertices];e.to_mesh_clear();return [[min(p[i] for p in pts) for i in range(3)],[max(p[i] for p in pts) for i in range(3)]]
for o in scene.objects:
 states[o.name]={'type':o.type,'matrix':[v for row in o.matrix_world for v in row],'geometry':meshhash(o.data) if o.type=='MESH' else None,'materials':[m.name if m else None for m in o.data.materials] if hasattr(o.data,'materials') else []}
 if o.type in ['MESH','CURVE']:bounds_before[o.name]=bounds(o)
for n,(hr,hv,hs) in visibility.items():o=bpy.data.objects[n];o.hide_render=hr;o.hide_viewport=hv;o.hide_set(hs)
for n,(hr,hv) in collection_vis.items():bpy.data.collections[n].hide_render=hr;bpy.data.collections[n].hide_viewport=hv
def hide(name):
 o=bpy.data.objects.get(name)
 if o:o.hide_render=True;o.hide_viewport=True;o.hide_set(True);hidden.append(name)
def assign(o,m):
 if o.type not in ['MESH','CURVE']:return
 o.data=o.data.copy()
 for i in range(len(o.data.materials)):o.data.materials[i]=m
 if not o.data.materials:o.data.materials.append(m)
 if o.type=='MESH':P.uv(o)
 changes.append({'kind':'material','object':o.name,'material':m.name})
# Apply complete native wood/cloth to existing furniture rather than uniform tint.
for o in list(scene.objects):
 if o.type not in ['MESH','CURVE'] or not visible(o):continue
 names=[m.name if m else '' for m in o.data.materials]
 if any(n.startswith(('AM2_WHITE_ASH','STEPPED_PALE','RENDER_WHITE_ASH')) for n in names) and not('FLOOR' in o.name or 'STEP_' in o.name):
  o.data=o.data.copy()
  for i,m in enumerate(o.data.materials):
   if m and m.name.startswith(('AM2_WHITE_ASH','STEPPED_PALE','RENDER_WHITE_ASH')):o.data.materials[i]=wood
  if o.type=='MESH':P.uv(o)
  changes.append({'kind':'material','object':o.name,'material':wood.name})
 elif any(n.startswith('AM2_SOFA') for n in names):assign(o,cloth)
# Approved 75 cameras inherited from production; exact names, saved matrices/shift.
reg=json.loads((ROOT/'renders/whole_house_final_study_v1/00_MANIFEST/CAMERA_REGISTER_REVIEW_V3.json').read_text())
for c in reg['cameras']:
 cam=bpy.data.objects.get(c['camera_name'])
 if not cam:d=bpy.data.cameras.new(c['camera_name']);cam=bpy.data.objects.new(c['camera_name'],d);col.objects.link(cam)
 cam.matrix_world=Matrix(c['matrix_world']);cam.data.lens=c['lens_mm'];cam.data.shift_y=c.get('shift_y',0);cam.data.clip_start=.01
# Kitchen exact window stays geometry-locked, with dark powdercoated frame finish.
dark=bpy.data.materials.get('RENDER_DARK_APPLIANCE') or material('POWDERCOAT',(.04,.045,.04),.55)
for n in ['B11_SITE_KITCHEN_WINDOW_JAMB_0','B11_SITE_KITCHEN_WINDOW_JAMB_1','B11_SITE_KITCHEN_WINDOW_MULLION_1','B11_SITE_KITCHEN_WINDOW_RAIL_0','B11_SITE_KITCHEN_WINDOW_RAIL_1']:
 assign(bpy.data.objects[n],dark)
# Reading assembly rigidly relocated to opposing guest-bath exterior wall, x7.75.
# Shelf occupies x7.37..7.69,y8.19..9.01, beyond the stair landing, away from handrail.
origin=Vector((7.3301,4.8901,0));target=Vector((7.530,8.600,0));R=Matrix.Rotation(math.pi/2,4,'Z');T=Matrix.Translation(target)@R@Matrix.Translation(-origin)
for o in list(scene.objects):
 if o.name.startswith(('READING_5015_','READING_DISPLAY_','READING_BOOK_')):
  bpy.context.view_layer.update();world=o.matrix_world.copy();o.parent=None;o.matrix_world=T@world;changes.append({'kind':'rigid_relocation','object':o.name,'matrix':[list(r) for r in o.matrix_world]})
# Wooden grip/post finish; preserve concealed brackets and their fixing function.
for o in list(scene.objects):
 if o.name in ['WAVE_WALL_HANDRAIL_900','WAVE_HANDRAIL_LOWER_POST','WAVE_HANDRAIL_LOWER_RETURN','WAVE_HANDRAIL_UPPER_RETURN']:assign(o,wood)
room_new['reading_transition']='shelf physically relocated to guest-bath exterior/art wall; original3steps; ash grip/post retained'
# V10 full construction surfaces, rigidly installed in the custom L-sofa frame.
P.assembly('LIVING_SOFA_V10_INSTALL','owner catalog p4/p8 + V10 differentiated seat/back; custom house assembly')
SOFA=ROOT/'design/sofa_fill_form_v10/delivery/SOFA_DIFFERENTIATED_FILL_V10.blend'
with bpy.data.libraries.load(str(SOFA),link=False) as (x,y):y.objects=['V10_SEAT_COMPLETE_COVER','V10_BACK_COMPLETE_COVER','V10_SEAT_COMPLETE_COVER_bottom_welt','V10_SEAT_COMPLETE_COVER_top_welt','V10_BACK_COMPLETE_COVER_bottom_welt','V10_BACK_COMPLETE_COVER_top_welt']
protos=y.objects;worlds={o.name:o.matrix_basis.copy() for o in protos}
for j,sy in enumerate([8.575,9.610,10.645]):
 M=Matrix(((0,-1,0,4.016),(1,0,0,sy),(0,0,1,0),(0,0,0,1)))
 for proto in protos:
  isseat='SEAT' in proto.name
  if j==0 and isseat:continue
  obj=proto.copy();obj.data=proto.data.copy();obj.name='HOUSE_V1_SOFA_'+str(j)+'_'+proto.name;col.objects.link(obj);obj.parent=None;obj.matrix_world=M@worlds[proto.name];obj.hide_render=False;obj.hide_viewport=False;obj.hide_set(False)
  obj['whole_custom_product_reference']='catalogp4/p8,V10; original frame unchanged';obj['source_asset']=str(SOFA)
  if obj.type=='MESH':obj.data.materials.clear();obj.data.materials.append(cloth)
 for old in ([f'V4_Sofa_back_{j}',f'V4_Sofa_back_{j}_sewn_welt']+(['V4_Sofa_seat_middle','V4_Sofa_seat_middle_sewn_welt'] if j==1 else ['V4_Sofa_seat_north','V4_Sofa_seat_north_sewn_welt'] if j==2 else [])):hide(old)
# Existing chaise module needs its own longer seat; retain true footprint and use
# the same supported core/jacket shape with a durable affine custom panel rebuild.
proto=next(o for o in protos if o.name=='V10_SEAT_COMPLETE_COVER');obj=proto.copy();obj.data=proto.data.copy();obj.name='HOUSE_V1_SOFA_CHAISE_COMPLETE';col.objects.link(obj);obj.parent=None;obj.matrix_world=Matrix.Identity(4)
for v in obj.data.vertices:v.co.x=v.co.x*1.49+4.351;v.co.y=v.co.y*1.14+8.559
obj.data.materials.clear();obj.data.materials.append(cloth);obj.hide_render=False;obj.hide_viewport=False;hide('V4_Sofa_chaise_upholstery');hide('V4_Sofa_chaise_upholstery_sewn_welt')
obj['construction']='same custom core/jacket panel enlarged to existing chaise footprint; not distorted purchased SKU'
for proto in protos:bpy.data.objects.remove(proto,do_unlink=True)
room_new['living']='inherited chosen table/rug/art/curtains; V10 upholstery in original complete frame; top now ~806mm, report height change'
room_new['dining']='inherit actual1600x800racetrack, fourcatalog6010Achairs and oval/enamel pendant; no new wallart'
# Rounded custom dressing desk in the actual900x450 footprint, top floor+750mm.
P.assembly('MOTHER_CREATIVE_VANITY','owner approved Creative VIEW05 U-shaped rounded wood desk; existing900x450 source footprint')
hide('BW1_MOTHER_VANITY')
P.box('Mother_vanity_top',(11.875,.730,1.18),(.450,.900,.040),r=.017)
for y in [.305,1.155]:P.box('Mother_vanity_support',(11.875,y,.815),(.420,.046,.730),r=.018)
P.box('Mother_vanity_drawer',(12.066,.730,1.115),(.028,.77,.085),r=.007)
P.box('Mother_vanity_underbeam',(11.720,.730,1.110),(.025,.805,.075),r=.005)
assign(bpy.data.objects['BW1_MOTHER_MIRROR_FRAME'],wood)
P.bottle('Mother_vanity_ceramic',(11.86,.42,1.20),.13,.035,ivory)
room_new['mother_bedroom']='Creative custom grounded floating bed, suspended side shelves, rounded U-shaped vanity fromC05'
# Bed family: grounded recessed supports and supported mattress/bedding, same
# whole footprint/capacity as source, not pressure-generated block rescaling.
def bed(room,source,head,headrest,capacity):
 a,b=bounds_before[source];x0,y0,z0=a;x1,y1,z1=b;cx,cy=(x0+x1)/2,(y0+y1)/2;w=x1-x0;d=y1-y0
 P.assembly(room+'_BED_SYSTEM','owner catalog wood-bed family + approved'+room+'Creative; metric footprint/capacity inherited'+str(capacity))
 hide(source);hide(head);hide(headrest)
 P.box(room+'_platform',(cx,cy,z0+.18),(w,d,.045),r=.021)
 for x in [x0+.17,x1-.17]:
  for y in [y0+.15,y1-.15]:P.rod(room+'_grounded_leg',(x,y,z0),(x,y,z0+.16),.037)
 P.soft(room+'_mattress',(cx,cy,z0+.36),(w-.08,d-.06,.29))
 # Ivory bedcover with broad restrained sag and actual side drop, not a thin board.
 nx,ny=64,48;verts=[];faces=[]
 for j in range(ny+1):
  v=2*j/ny-1
  for i in range(nx+1):
   u=2*i/nx-1;edge=max(abs(u),abs(v));z=z0+.50-.24*max(0,(edge-.88)/.12)**.7+.006*math.sin(u*5+v*2)*max(0,1-edge)
   verts.append((cx+u*(w-.025)/2,cy+v*(d-.012)/2,z))
 for j in range(ny):
  for i in range(nx):k=j*(nx+1)+i;faces.append((k,k+1,k+nx+2,k+nx+1))
 me=bpy.data.meshes.new(room+'cover');me.from_pydata(verts,[],faces);me.update();o=bpy.data.objects.new('HOUSE_V1_'+room+'_bedcover',me);col.objects.link(o);me.materials.append(cloth);P.uv(o)
 for f in me.polygons:f.use_smooth=True
 so=o.modifiers.new('Fabric thickness','SOLIDIFY');so.thickness=.003;sub=o.modifiers.new('Fabric surface','SUBSURF');sub.levels=1
 P.box(room+'_headrail',(x1-.01,cy,z0+.66),(.05,d+.02,.37),r=.018)
 for y in [cy-d*.24,cy+d*.24]:
  o=P.soft(room+'_linen_head_pad',(x1-.049,y,z0+.68),(d*.42,.30,.08));o.rotation_euler=(math.pi/2,0,math.pi/2)
 for y in [cy-d*.23,cy+d*.23]:P.soft(room+'_pillow',(x1-.40,y,z0+.57),(.46,d*.40,.14))
 # Thin soft sage runner over cover center, with open perimeter and real cloth thickness.
 P.soft(room+'_sage_runner',(cx-.26,cy,z0+.515),(.52,d-.06,.012),green)
bed('MOTHER','B11_Rectangle013_CATALOG_00_00','BW1_MOTHER_THIN_HEADBOARD','BW1_MOTHER_SOFT_HEADREST',1500)
bed('COUPLE','B11_Rectangle012_CATALOG_00_00','BW1_COUPLE_THIN_HEADBOARD','BW1_COUPLE_SOFT_HEADREST',1800)
for n in ['BW1_MOTHER_BED_RUNNER','BW1_COUPLE_BED_RUNNER']:hide(n)
P.assembly('MOTHER_BEDSIDE','creative wall shelf over existing bedside footprint; anchored wood support')
for n in ['BW1_MOTHER_BEDSIDE','BW1_MOTHER_BEDSIDE_N']:
 a,b=bounds_before[n];hide(n);cx,cy=(a[0]+b[0])/2,(a[1]+b[1])/2;P.box(n+'_shelf',(cx,cy,.97),(b[0]-a[0],b[1]-a[1],.034),r=.01);P.box(n+'_rear_attachment',(b[0]-.04,cy,.925),(.07,b[1]-a[1]-.08,.11),r=.007)
P.assembly('COUPLE_ROUND_BEDSIDE','creative round ash bedside; existing source footprint/height, complete grounded legs')
for n in ['BW1_COUPLE_BEDSIDE_N','BW1_COUPLE_BEDSIDE_S']:
 a,b=bounds_before[n];hide(n);cx,cy=(a[0]+b[0])/2,(a[1]+b[1])/2;r=min(b[0]-a[0],b[1]-a[1])/2
 P.rod(n+'_round_top',(cx,cy,1.00),(cx,cy,1.03),r)
 for angle in [0,2.094,4.189]:x=cx+r*.65*math.cos(angle);y=cy+r*.65*math.sin(angle);P.rod(n+'_leg',(x,y,.45),(x,y,1.0),.017)
room_new['couple_bedroom']='Creative low rounded platform, true1800capacity, round bedside, inset linen headpads'
# Study: keep proper work table and chair, add fixed art in actual1550mm bookcase gap.
P.art('STUDY_GAP_ART',(15.744,8.855,1.96),1.00,.60,'X',ROOT/'design/whole_house_model_v1/references/study_landscape_crop.jpg')
for n in ['STUDY_V1_DAILY_SEAT']+[f'STUDY_V1_BACK_CUSHION_{i}' for i in range(3)]:assign(bpy.data.objects[n],cloth if 'SEAT' in n else green)
room_new['study']='source desk/bookcase/daybed preserved, fixed landscape art between actual shelves, sage backpads/linen seat'
# Primary bath Creative: current plumbing and slab retained, new ribbed floating
# drawer front and supported open towel shelf within same source cabinet bounds.
P.assembly('MASTER_BATH_JOINERY','Creative selected ribbed-front ash cabinet, existing basin/counter plumbing retained;18mm carcass')
for n in ['CBM_master_LOWER_DOOR_0','CBM_master_LOWER_DOOR_1']:hide(n)
for x0,x1 in [(13.157,13.72),(13.757,14.32)]:
 P.box('Master_drawer_front',((x0+x1)/2,5.789,1.065),(x1-x0,.018,.350),r=.003)
 for i in range(int((x1-x0)/.020)):
  x=x0+.012+i*.020;P.rod('Master_drawer_rib',(x,5.775,.90),(x,5.775,1.225),.006)
P.box('Master_open_shelf',(13.738,6.022,.705),(1.18,.43,.023),r=.004)
for x in [13.166,14.309]:P.box('Master_shelf_side',(x,6.025,.970),(.022,.44,.552),r=.004)
P.towel('Master_folded_towel',(13.80,6.01,.737),(.30,.20,.040))
assign(bpy.data.objects['CBM_MASTER_MIRROR_FRAME'],wood)
room_new['master_bath']='ribbed floating drawer/open towel shelf, same basin/tap/toilet/shower openings'
# Designer families use real construction source and surface-supported accessories.
for rid,prefix,z in [('secondary_bath','CBM_secondary',1.30),('guest_bath','CBM_guest',1.30)]:
 P.assembly(rid+'_FUNCTIONAL_STYLING','source plumbing/cabinet geometry + selected Designer sparse towels/ceramic; no added basin')
 if rid=='secondary_bath':c=(10.29,6.075,z);assign(bpy.data.objects['CBM_SECONDARY_MIRROR_FRAME'],wood)
 else:c=(8.30,9.04,z);assign(bpy.data.objects['CBM_GUEST_MIRROR_FRAME'],wood)
 P.bottle(rid+'_soap',c,.13,.025,ivory);P.towel(rid+'_towel',(c[0],c[1]-.12,z+.025),(.15,.10,.030));room_new[rid]='Designer material, native cabinet, fixed mirror and sparse functional accessories'
# Designer service balcony and entry; place accessories only on existing surfaces.
P.assembly('SERVICE_BALCONY_STYLING','source utility/storage cabinets, custom baskets/books resting on actual counter')
P.box('Utility_storage_bin',(2.35,1.035,.99),(.26,.28,.16),wood,r=.008);P.towel('Utility_folded_linen',(2.66,1.07,.918),(.25,.16,.04));room_new['service_balcony']='Designer existing storage/table/window and task styling; no added appliances'
P.assembly('ENTRY_DESIGNER_STYLING','source shoe cabinet and three-step geometry, Designer quiet art and ceramic')
P.bottle('Entry_ceramic',(3.20,4.93,1.007),.16,.042,ivory);P.art('ENTRY_QUIET_ART',(3.25,4.719,1.85),.45,.55,'Y',ROOT/'design/whole_house_model_v1/references/study_landscape_crop.jpg');room_new['entry']='Designer cabinet/art; shared3stairs, living seating remains ash/linen across view05'
P.art('HALLWAY_QUIET_ART',(10.88,6.588,1.93),.36,.52,'Y',ROOT/'design/whole_house_model_v1/references/study_landscape_crop.jpg');room_new['hallway']='Designer quiet wall art and existing joinery, no projecting floor furniture'
room_new['guest_bedroom']='Faithful existing1200single-bed/workroom layout, corrected native wood/flax materials'
room_new['north_sunroom']='Faithful revised1800-2100open350deep,2100-2600closed600deep inherited exactly; no old upper restoration'
# All new assemblies are owner-reference proposals, no automatic purchase or site dimensions.
dec=json.loads((ROOT/'render_config/whole_house_model_v1/ROOM_DECISIONS.json').read_text())
scene['room_decisions_json']=json.dumps(dec,ensure_ascii=False);scene['whole_house_stage']='ACTUAL_ROOM_GEOMETRY_AND_MATERIALS_CANDIDATE';scene['image2_requests']=0
scene.camera=bpy.data.objects['CAM_living_VIEW_01'];scene.render.threads_mode='FIXED';scene.render.threads=2
for image in bpy.data.images:
 if image.source=='FILE' and not image.packed_file and Path(bpy.path.abspath(image.filepath)).exists():image.pack()
bpy.context.view_layer.update();bpy.ops.wm.save_as_mainfile(filepath=str(DEST))
report={'status':'ROOM_ASSEMBLY_CANDIDATE','source':str(SOURCE),'source_sha256':hashlib.sha256(SOURCE.read_bytes()).hexdigest(),'output':str(DEST),'output_sha256':hashlib.sha256(DEST.read_bytes()).hexdigest(),'original_states':states,'original_bounds':bounds_before,'material_changes':changes,'hidden_replaced':hidden,'created_count':len(P.created),'created_objects':[o.name for o in P.created],'room_changes':room_new,'reading_relocation_matrix':[list(r) for r in T],'sofa_pilot_source':str(SOFA),'model_height_change':'living sofa V10 from700 to~806mm, explicit authorized appearance propagation; furniture fit review required','exact_sku_approved':False,'source_writeback':False,'image2_requests':0}
(RUN/'BUILD_AUDIT.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n');print('ACTUAL_HOUSE_ASSEMBLY_READY',report['output_sha256'],report['created_count'],list(room_new))
