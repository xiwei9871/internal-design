"""Deterministic bounded C-Type study successor; daily/guest workbench states."""
import bpy,json,hashlib,uuid,sys,math
from pathlib import Path
from mathutils import Vector,Matrix
from mathutils.bvhtree import BVHTree
ROOT=Path(__file__).resolve().parents[1]
R=ROOT/'design/study_room_v1';R.mkdir(parents=True,exist_ok=True)
SRC=Path('/Users/xiwei/interior_design/projects/c_type_home/design/living_fitness_reading_review_20261006/OPTION_A_R4_SUNROOM_INTEGRATED_LAUNDRY_REVIEW_14.blend')
R4=Path('/Users/xiwei/interior_design/projects/c_type_home/design/bedroom_door_r4/OPTION_A_SLIDING_R4.blend')
B0=Path('/Users/xiwei/interior_design/projects/c_type_home/design/blender_b0/B0_EXISTING_AS_IS.blend')
EXPECTED={'R4':'d109c7efcfa2b2b2565e4c073ee0cdf5282b23c01122bc9c1bbe7b8791ac3afb','B0':'717e6dc4a3d4fb6325512236f5c235ded702376309456028129bf0889548efcb'}
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
assert sha(R4)==EXPECTED['R4'] and sha(B0)==EXPECTED['B0']
bpy.ops.wm.open_mainfile(filepath=str(SRC));bpy.context.view_layer.update()
# Existing source snapshot covers all object states but does not rediscover rooms.
import struct
def object_state(obj):
    mesh=None
    if obj.type=='MESH':
        h=hashlib.sha256()
        for vertex in obj.data.vertices:h.update(struct.pack('<fff',*vertex.co))
        for face in obj.data.polygons:h.update(struct.pack('<'+str(len(face.vertices))+'I',*face.vertices))
        mesh=h.hexdigest()
    return {'mesh':mesh,'matrix':list(v for row in obj.matrix_world for v in row),'parent':obj.parent.name if obj.parent else None,
        'collections':sorted(c.name for c in obj.users_collection),'hide_render':obj.hide_render,'hide_viewport':obj.hide_viewport,'hidden':obj.hide_get(),
        'materials':[m.name if m else None for m in obj.data.materials] if obj.type=='MESH' else None,'properties':str(sorted(obj.items()))}

before={o.name:object_state(o) for o in bpy.context.scene.objects}
def bb(o):
 c=[o.matrix_world@Vector(v) for v in o.bound_box]
 return [[min(v[i] for v in c) for i in range(3)],[max(v[i] for v in c) for i in range(3)]]
def envelope(ns):
 boxes=[bb(bpy.data.objects[n]) for n in ns]
 return [[min(b[0][i] for b in boxes) for i in range(3)],[max(b[1][i] for b in boxes) for i in range(3)]]
rows=json.loads((R/'STUDY_BOUNDED_OBJECTS.json').read_text())
furn=[r['name'] for r in rows if r['active'] and r['name'].startswith('R3_STUDY_')]
tableparts=[r['name'] for r in rows if r['active'] and r['name'].startswith(('R3_TEA_APRON_',))]
retired=furn+tableparts
book=[n for n in furn if 'Rectangle024' in n]
desk_old='R3_STUDY_B11_Rectangle026_CATALOG_00_00'
# Named local architectural context, inherited meaningful wall boundaries.
idx=json.loads(Path('/Users/xiwei/interior_design/projects/c_type_home/design/wall_identity_r4_review/WALL_PART_INDEX.json').read_text())
localwalls=[r['native_id'] for r in idx['parts'] if r['world_bounds'][1][0]>13.05 and r['world_bounds'][0][0]<16.41 and r['world_bounds'][1][1]>6.5 and r['world_bounds'][0][1]<11.81]
arch=[r['name'] for r in rows if r['active'] and r['name'].startswith(('V4_D-STUDY','V4_W-STUDY','VIEW_WALL_V4'))]+localwalls
arch=sorted(set(n for n in arch if bpy.data.objects.get(n)))
tea=[r['name'] for r in rows if r['active'] and r['name'].startswith('R3_TEA_') and r['name'] not in tableparts]
sill=bb(bpy.data.objects['V4_W-STUDY-NE_SILL_PLATFORM'])
oldbook=envelope(book)
audit={'source':str(SRC),'source_sha256':sha(SRC),'frame':'c_type_world','unit':'meter','floor_z':.45,
 'room':{'usable_x':[13.1001,16.1999],'usable_y':[6.6001,10.8999],'usable_width_m':3.0998,'usable_length_m':4.2998},
 'bay_window':{'structural_sill_bounds':sill,'structural_length_m':sill[1][0]-sill[0][0],
 'structural_depth_m':sill[1][1]-sill[0][1],'finished_z_m':sill[1][2],
 'height_above_room_floor_m':sill[1][2]-.45,'continuous_clear_length_m':1.88,
 'clear_seating_depth_m':.65,'basis':'inner sill front11.05; usable glass-side boundary11.70; wallp iers permitx13.71..15.59',
 'front_to_existing_desk_m':sill[0][1]-bb(bpy.data.objects[desk_old])[1][1],
 'front_to_old_bookcase_north_m':sill[0][1]-oldbook[1][1]},
 'bookcase':{'bounds':oldbook,'width_m':oldbook[1][1]-oldbook[0][1],'depth_m':.45,'height_m':2.00,
 'grid_count':54,'grid_basis':'nine bays x six shelf tiers','wall_visual_coverage_pct':100*(4.2*2)/(4.2998*2.8),
 'upper_open_band_occupancy_pct':100},
 'desk':{'bounds':bb(bpy.data.objects[desk_old]),'size_m':[2.2,.8,.75],
 'current_bookcase_side_chair_zone_m':15.735874-15.071625,'tea_counter_gap_m':7.389718-7.092625,
 'chair_clearance_note':'original hostchair sits within table-bookcase664mm gap; longbench andtea-counterfront restrict movement'},
 'door':{'name':'V4_D-STUDY_LEAF_0','bounds':bb(bpy.data.objects['V4_D-STUDY_LEAF_0']),
 'clear_width_m':.85,'hinge_source_xy':[13.,6.7],'study_entry_sweep_radius_m':.85,
 'geometry_state':'closed inherited leaf; full0..90 degree furniture clearance envelope evaluated without modifyingdoor'},
 'authority_hash_before':EXPECTED}
(R/'STUDY_ROOM_EXISTING_AUDIT.json').write_text(json.dumps(audit,ensure_ascii=False,indent=2)+'\n')
for n in retired:
 o=bpy.data.objects[n];o.hide_viewport=True;o.hide_render=True;o.hide_set(True)
col=bpy.data.collections.new('COL_STUDY_ROOM_V1');bpy.context.scene.collection.children.link(col)
new=[]
def mat(n,c):
 m=bpy.data.materials.new(n);m.diffuse_color=(*c,1);return m
wood=mat('STUDY_V1_PALE_ASH',(.67,.53,.37));white=mat('STUDY_V1_OFFWHITE',(.84,.82,.75));cloth=mat('STUDY_V1_IVORY',(.78,.72,.61));green=mat('STUDY_V1_MUTED_GREEN',(.30,.43,.37));metal=mat('STUDY_V1_FRAME',(.25,.29,.28))
def box(n,a,b,m,t='furniture',bev=.006):
 bpy.ops.mesh.primitive_cube_add(size=1,location=[(a[i]+b[i])/2 for i in range(3)])
 o=bpy.context.object;o.name=n;o.scale=[b[i]-a[i] for i in range(3)]
 bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
 if bev:
  mod=o.modifiers.new('Soft edges','BEVEL');mod.width=bev;mod.segments=3
  bpy.ops.object.modifier_apply(modifier=mod.name)
 o.data.materials.append(m)
 for c in list(o.users_collection):c.objects.unlink(o)
 col.objects.link(o);new.append((o,t));return o
def join(n,parts,t):
 bpy.ops.object.select_all(action='DESELECT')
 for o in parts:o.select_set(True)
 bpy.context.view_layer.objects.active=parts[0];bpy.ops.object.join();o=bpy.context.object;o.name=n
 new[:]=[(a,b) for a,b in new if a not in parts];new.append((o,t));return o
# Fixed extension550mm ends at unmodified sill front11.05. Continuous top fits1880x1200.
x0,x1=13.71,15.59;y0,y1=10.50,11.70;z=.45
top=box('STUDY_V1_DAYBED_TIMBER_TOP',(x0,y0,.901),(x1,y1,.925),wood,'daybed',.005)
parts=[box('DB_BOTTOM',(x0,y0+.03,z+.08),(x1,10.89,z+.10),wood),
 box('DB_BACK',(x0,10.872,z+.10),(x1,10.89,.898),wood)]
for x in [x0,x0+(x1-x0)/3,x0+2*(x1-x0)/3,x1-.018]:
 parts.append(box('DB_PARTITION',(x,y0+.03,z+.10),(x+.018,10.89,.898),wood))
base=join('STUDY_V1_DAYBED_STORAGE_CARCASS',parts,'storage')
# Real hollow drawerboxes, with fronts and fingerpulls. Nominal running hardware is not fabricated.
drawers=[]
for i in range(3):
 a=x0+i*(x1-x0)/3+.023;b=x0+(i+1)*(x1-x0)/3-.023
 p=[box('D_BOTTOM',(a,y0+.023,.557),(b,10.872,.575),wood),
 box('D_FRONT',(a,y0,.557),(b,y0+.020,.879),wood),
 box('D_REAR',(a,10.854,.575),(b,10.872,.851),white),
 box('D_LEFT',(a,y0+.020,.575),(a+.012,10.854,.851),white),
 box('D_RIGHT',(b-.012,y0+.020,.575),(b,10.854,.851),white),
 box('D_HANDLE',(a+.10,y0-.008,.85),(b-.10,y0,.858),metal,bev=.001)]
 d=join('STUDY_V1_STORAGE_DRAWER_'+str(i+1),p,'drawer');drawers.append(d)
 d['opening_direction_source_xyz']=[0,-1,0];d['proposed_travel_m']=.45
# Store one three-fold topper indrawer1: packed600x400x240mm fits measured drawer interior.
topperpack=box('STUDY_V1_FOLDED_TOPPER_STORAGE',(x0+.038,10.54,.587),(x0+.605,10.86,.827),cloth,'stored_topper')
cushions=[box('STUDY_V1_DAILY_SEAT',(x0+.02,11.07,.924),(x1-.02,11.68,.989),cloth,'cushion',.025)]
for i in range(3):
 a=x0+.08+i*.59
 cushions.append(box('STUDY_V1_BACK_CUSHION_'+str(i),(a,11.54,.989),(a+.52,11.68,1.24),green,'cushion',.035))
guest=box('STUDY_V1_GUEST_TOPPER',(x0,y0,.925),(x1,y1,.955),cloth,'guest_mattress',.018)
guest.hide_render=True;guest.hide_viewport=True;guest.hide_set(True)
# Rear east wall composition:4000x380x800mm lowerclosed + asymmetric uppergroups.
cabx0,cabx1=15.78,16.16;cy0,cy1=6.68,10.68
parts=[box('BOOK_LOW_BOTTOM',(cabx0,cy0,.53),(cabx1,cy1,.548),wood),
box('BOOK_LOW_TOP',(cabx0,cy0,1.232),(cabx1,cy1,1.25),wood),
box('BOOK_LOW_BACK',(cabx1-.012,cy0,.548),(cabx1,cy1,1.232),white)]
for y in [cy0,7.38,8.28,9.18,10.06,cy1-.018]:
 parts.append(box('BOOK_LOW_DIV',(cabx0,y,.548),(cabx1,y+.018,1.232),white))
lower=join('STUDY_V1_BOOKCASE_LOWER_CARCASS',parts,'cabinet')
for i,(a,b) in enumerate(zip([6.70,7.40,8.30,9.20,10.08],[7.36,8.26,9.16,10.04,10.66])):
 front=box('STUDY_V1_BOOKCASE_LOWER_FRONT_'+str(i),(15.76,a,.554),(15.779,b,1.226),wood,'cabinet_door',.003)
 front['reserved_function']='ventilated printer/NAS servicebay (equipment notadded)' if i==0 else 'closedstorage'
 if i==0:
  for k in range(5):box('STUDY_V1_SERVICE_VENT_'+str(k),(15.757,a+.05,.68+k*.035),(15.760,b-.05,.689+k*.035),metal,'vent',.001)
# Upper band open footprint61.25%, intentionally blank1550mm wallspace between.
for gid,(a,b) in enumerate([(6.68,8.08),(9.63,10.68)]):
 ps=[box('UP_BACK',(16.13,a,1.35),(16.15,b,2.55),white),
 box('UP_LOW',(15.85,a,1.35),(16.15,b,1.368),wood),
 box('UP_TOP',(15.85,a,2.532),(16.15,b,2.55),wood)]
 for y in [a,b-.018]:ps.append(box('UP_SIDE',(15.85,y,1.368),(16.15,y+.018,2.532),wood))
 if gid==0:
  mid=a+.50;ps.append(box('UP_DIV',(15.85,mid,1.368),(16.15,mid+.018,2.532),wood))
  ps+= [box('UP_SHELF',(15.85,a,1.73),(16.13,mid,1.748),wood),
  box('UP_SHELF',(15.85,mid,2.10),(16.13,b,2.118),wood)]
 else:
  ps.append(box('UP_SHELF',(15.85,a,1.95),(16.13,b,1.968),wood))
 join('STUDY_V1_OPEN_SHELF_GROUP_'+str(gid),ps,'bookshelf')
# Four sparsebook proxies give scale rather than fillingthe shelves.
for i in range(4):box('STUDY_V1_BOOK_'+str(i),(15.90,6.82+i*.06,1.368),(16.10,6.86+i*.06,1.64+(i%2)*.03),green,'book',.002)
# Owner steering R4:2000x800 tea/worktable; single host enters from north; mainroute infrontwest.
deskps=[box('DESK_TOP',(14.21,7.58,1.176),(15.01,9.58,1.20),wood,bev=.012)]
for x in [14.25,14.95]:
 for y in [7.64,9.49]:deskps.append(box('DESK_LEG',(x,y,.45),(x+.025,y+.025,1.176),metal,bev=.004))
desk=join('STUDY_V1_MOVABLE_DESK',deskps,'desk')
chairps=[box('CHAIR_SEAT',(14.96,8.60,.87),(15.46,9.10,.93),cloth,bev=.025),
box('CHAIR_BACK',(15.38,8.60,.93),(15.46,9.10,1.34),green,bev=.025)]
for x in [15.00,15.39]:
 for y in [8.64,9.02]:chairps.append(box('CHAIR_LEG',(x,y,.45),(x+.025,y+.025,.87),metal,bev=.003))
chair=join('STUDY_V1_WORK_CHAIR',chairps,'chair')
# Owner removed optional stool; retain only STUDY_V1_WORK_CHAIR.
bpy.context.view_layer.update()
# Fixed furniture adjacency/checks plusdoorleaf swept0..90deg againstactualgeometry.
def tree(o,M=None):
 M=M or o.matrix_world
 return BVHTree.FromPolygons([tuple(M@v.co) for v in o.data.vertices],[list(p.vertices) for p in o.data.polygons],epsilon=1e-7)
fixedcheck=[top,base,desk,chair,lower]+[o for o,t in new if t in ['bookshelf','drawer','cabinet_door']]
collision=[]
for o in fixedcheck:
 for n in arch:
  q=bpy.data.objects[n]
  if q.type=='MESH' and tree(o).overlap(tree(q)):collision.append([o.name,n])
assert not collision,collision
leaf=bpy.data.objects['V4_D-STUDY_LEAF_0'];pivot=Vector((13.,6.7,.45))
swing_hits=[]
for angle in range(0,91,5):
 M=Matrix.Translation(pivot)@Matrix.Rotation(-math.radians(angle),4,'Z')@Matrix.Translation(-pivot)@leaf.matrix_world
 for o in [desk,chair,base,lower]:
  if tree(leaf,M).overlap(tree(o)):swing_hits.append([angle,o.name])
assert not swing_hits,swing_hits
# Protect every inherited object except exact furniture retirementlist.
for n,s in before.items():
 if n in retired:
  now=object_state(bpy.data.objects[n]);assert all(now[k]==s[k] for k in s if k not in ['hide_viewport','hide_render','hidden']),n
 else:assert object_state(bpy.data.objects[n])==s,n
inreg=json.loads(Path('/Users/xiwei/interior_design/projects/c_type_home/design/living_fitness_reading_review_20261006/spatial-canvas.bindings.review14.json').read_text())
existing={b['native_id']:b for b in inreg['bindings']}
selected=arch+tea+['FLOOR_UPPER_SEAM_2','FLOOR_UPPER_SEAM_3']
# Full floors can carry beyond room context; renderusesinheritedfloor,taskproxygetsreadonlyderivedcrop.
floor=box('STUDY_V1_CONTEXT_FLOOR',(13.10,6.60,.35),(16.20,10.90,.449),white,'context_floor')
floor['authority']='derived_presentation_only';selected=arch+tea
def visible(o,flag):
 o.hide_render=not flag;o.hide_viewport=not flag;o.hide_set(not flag)
def make_registry(rev,out):
 binds=[existing[n] for n in selected if n in existing and not bpy.data.objects[n].hide_render]
 for o,typ in new:
  if o.hide_render:continue
  binds.append({'entity_id':'ent_'+uuid.uuid5(uuid.NAMESPACE_URL,'c_type_home:studyv1:'+o.name).hex,'adapter':'blender','native_id':o.name,
  'semantic_type':typ,'room_id':'study','authority_level':'HUMAN_DESIGN_GUIDE'})
 d={k:v for k,v in inreg.items() if k!='bindings'}
 d.update(registry_revision=rev,source_resource_id='c_type_study_room_v1',source_revision=rev,source_locator=str(out),bindings=binds)
 bpy.ops.wm.save_as_mainfile(filepath=str(out));d['source_sha256']=sha(out)
 return d
daily=R/'STUDY_ROOM_DAYBED_V1.blend';dreg=make_registry('study-room-daybed-v1-r5-daily',daily)
(R/'spatial-canvas.bindings.daily.json').write_text(json.dumps(dreg,ensure_ascii=False,indent=2)+'\n')
# Same design, localdesk350mm south, chairparksunderdesk, single mainchair parksunder inGuest.
desk.location.y-=.35;chair.location.x-=.34;chair.location.y-=.35
for o in cushions:visible(o,False)
visible(topperpack,False);visible(guest,True)
bpy.context.view_layer.update()
guest_swing=[]
for angle in range(0,91,5):
 M=Matrix.Translation(pivot)@Matrix.Rotation(-math.radians(angle),4,'Z')@Matrix.Translation(-pivot)@leaf.matrix_world
 for o in [desk,chair,base,lower]:
  if tree(leaf,M).overlap(tree(o)):guest_swing.append([angle,o.name])
assert not guest_swing,guest_swing
guestout=R/'STUDY_ROOM_DAYBED_V1_GUEST.blend';greg=make_registry('study-room-daybed-v1-r5-guest',guestout)
(R/'spatial-canvas.bindings.guest.json').write_text(json.dumps(greg,ensure_ascii=False,indent=2)+'\n')
clearance={'daybed_1200_clearance_gate':'PASS','method':'model source-world AABB in explicitlynamed passage bands + actualmesh intersections + doorleaf5deg sweep; notcodecertification',
 'daily':{'daybed_to_desk_m':10.5-9.58,'desk_to_bookcase_front_m':15.76-15.01,'desk_to_chair_front_m':-.05,'south_counter_to_desk_m':7.58-7.106625,'north_host_entry_m':10.5-9.58,'foot_space_under_desk':True,'chair_footprint_m':[.50,.50],'chair_back_to_bookcase_m':15.76-15.46,'main_west_route_m':14.21-13.1001,
 'chair_operating_envelope_back_max_x':15.46,'rear_gap_is_not_through_route':True,'drawer_travel_m':.45,'open_drawer_to_desk_m':10.5-.45-9.58,
 'door_clear_width_m':.85,'door_sweep_hits':swing_hits},
 'guest':{'mattress_envelope_m':[1.88,1.20,.03],'daybed_to_desk_m':10.5-9.23,
 'main_route_m':14.21-13.1001,'door_clear_width_m':.85,'minimum_route_including_entry_m':.85,'door_sweep_hits':guest_swing},
 'door_bottleneck_note':'inherited850mm door controls whole-route minimum; mainwestpassage1110mm;300mm rearchairgap isoperationallowance notthroughroute',
 'drawer_opening_note':'450mm opening leaves470mm todeskfront; this is retrieval space, not the main route. Open-drawer standing ergonomics remains HUMAN_REVIEW.',
 'native_architecture_collision_pairs':collision,'authority_hash_after':{'R4':sha(R4),'B0':sha(B0)}}
layout={'status':'HUMAN_REVIEW','authority':'DERIVED_DESIGN_MODEL','source':str(SRC),'source_sha256':sha(SRC),
 'frozen_hashes':EXPECTED,'retired_furniture_native_ids':retired,'preserved_tea_service_native_ids':tea,
 'daybed':{'length_m':1.88,'total_depth_m':1.20,'fixed_extension_depth_m':.55,'platform_top_z_m':.925,
 'daily_seat_depth_m':.61,'visible_timber_depth_m':.57,'drawer_count':3,'drawer_internal_nominal_m':[.577,.331,.276],
 'topper_stored_nominal_m':[.567,.320,.240],'topper_product_note':'thin flexible30mm topper, compact foldedproxy requiresmanufacturerpackingverification','guest_topper_envelope_m':[1.88,1.20,.03],
 'storage_actual_depth_m':.39,'rear_wall_abutment_note':'extension is550mm overall;wallprojectionlimitsclosedcarcassdepthto390mm;top bridgesabovesillwithoutwallchange','structural_sill_unchanged':True},
 'bookcase':{'lower_envelope_m':[4.0,.38,.80],'upper_depth_m':.30,'upper_height_m':1.20,
 'open_band_occupancy_pct':61.25,'open_band_breathing_pct':38.75,'blank_wall_span_m':1.55,
 'old_total_wall_open_coverage_pct':audit['bookcase']['wall_visual_coverage_pct'],
 'new_total_wall_open_coverage_pct':100*(2.45*1.2)/(4.2998*2.8),
 'coverage_definition':'61.25% means horizontal occupancy ofnewupperband; whole-wallprojectedopenarea24.42%; compareold69.77%'},
 'desk':{'size_m':[2.0,.80,.75],'daily_bounds':[[14.21,7.58,.45],[15.01,9.58,1.20]],
 'guest_translation_m':[0,-.35,0],'guest_counter_gap_m':7.23-7.106625,'main_chair_count':1,'movable_stool_count':0,'owner_steering':'tea/worktable2000x800;singlehostentersfromnorth920mm;southcountergap473mm;chair500x500,300mmbackgap,50mmfronttucksundertable,westpassage1110mm'},
 'sofa_bed_added':False,'architecture_unchanged':True,'cycles_rendering_started':False}
(R/'STUDY_ROOM_LAYOUT_V1.json').write_text(json.dumps(layout,ensure_ascii=False,indent=2)+'\n')
(R/'STUDY_ROOM_CLEARANCE_V1.json').write_text(json.dumps(clearance,ensure_ascii=False,indent=2)+'\n')
print('STUDY_BUILD_PASS',len(dreg['bindings']),len(greg['bindings']),json.dumps(clearance))
