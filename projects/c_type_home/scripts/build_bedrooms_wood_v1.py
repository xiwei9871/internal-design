"""Editable three-bedroom review, bounded furniture edits over the accepted house."""
import bpy, math, json, uuid, hashlib, struct
from pathlib import Path
from mathutils import Vector, Matrix
from mathutils.bvhtree import BVHTree
ROOT=Path(__file__).resolve().parents[1];R=ROOT/'design/bedrooms_wood_v1'
SRC=ROOT/'design/study_room_v1/STUDY_ROOM_DAYBED_V1.blend'
REV='bedrooms-wood-v1-review-2'
TRUTHS={
 '/Users/xiwei/interior_design/projects/c_type_home/design/bedroom_door_r4/OPTION_A_SLIDING_R4.blend':'d109c7efcfa2b2b2565e4c073ee0cdf5282b23c01122bc9c1bbe7b8791ac3afb',
 '/Users/xiwei/interior_design/projects/c_type_home/design/blender_b0/B0_EXISTING_AS_IS.blend':'717e6dc4a3d4fb6325512236f5c235ded702376309456028129bf0889548efcb',
 str(SRC):'3606aeb73b8bf845796346b46a6567877bca0f4cd4672678e82206a12e20236d'}
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
assert all(sha(p)==h for p,h in TRUTHS.items())
bpy.ops.wm.open_mainfile(filepath=str(SRC));bpy.context.view_layer.update()
base=json.loads((ROOT/'design/study_room_v1/spatial-canvas.bindings.full.json').read_text())
audit=json.loads((R/'EXISTING_BOUNDED_AUDIT.json').read_text())
def state(o):
 h=hashlib.sha256()
 if o.type=='MESH':
  for v in o.data.vertices:h.update(struct.pack('<fff',*v.co))
  for f in o.data.polygons:h.update(struct.pack('<'+'I'*len(f.vertices),*f.vertices))
 return {'geometry':h.hexdigest(),'matrix':[float(v) for row in o.matrix_world for v in row],
  'hidden':[o.hide_render,o.hide_viewport,o.hide_get()], 'parent':o.parent.name if o.parent else None,
  'materials':[m.name if m else None for m in o.data.materials] if o.type=='MESH' else None,
  'properties':str(sorted(o.items())),'collections':sorted(c.name for c in o.users_collection)}
before={o.name:state(o) for o in bpy.context.scene.objects}
def bb(o):
 c=[o.matrix_world@Vector(v) for v in o.bound_box]
 return [[min(v[i] for v in c) for i in range(3)],[max(v[i] for v in c) for i in range(3)]]
retired=[b['native_id'] for b in base['bindings'] if b['native_id'].startswith((
 'B11_Rectangle011','B11_Rectangle014','B11_Rectangle023','B11_Rectangle051','B11_Rectangle052','B11_Circle009'))]
retired+=['B11_Rectangle045_FRONT_0','B11_Rectangle045_PULL_0']
for n in retired:
 o=bpy.data.objects[n];o.hide_render=True;o.hide_viewport=True;o.hide_set(True)
col=bpy.data.collections.new('COL_BEDROOMS_WOOD_V1');bpy.context.scene.collection.children.link(col)
new=[];zones={};parts={}
def material(n,c):
 m=bpy.data.materials.new('BW1_'+n);m.diffuse_color=(*c,1);m.use_nodes=True
 s=m.node_tree.nodes.get('Principled BSDF');s.inputs['Base Color'].default_value=(*c,1);s.inputs['Roughness'].default_value=.85
 return m
wood=material('PALE_ASH',(.68,.55,.39));ivory=material('IVORY',(.84,.81,.73))
cloth=material('LINEN',(.74,.70,.62));blue=material('MIST_BLUE',(.34,.52,.57))
green=material('SAGE',(.40,.52,.43));dark=material('HARDWARE',(.24,.27,.25));mirror=material('MIRROR_REVIEW',(.61,.72,.75))
def record(o,kind,zone):
 for c in list(o.users_collection):c.objects.unlink(o)
 col.objects.link(o);new.append((o,kind,zone));zones[o.name]=zone;return o
def box(n,a,b,m,kind='furniture',zone='couple',bev=.006):
 bpy.ops.mesh.primitive_cube_add(size=1,location=[(a[i]+b[i])/2 for i in range(3)])
 o=bpy.context.object;o.name='BW1_'+n;o.scale=[b[i]-a[i] for i in range(3)]
 bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
 if bev:
  mod=o.modifiers.new('Rounded edges','BEVEL');mod.width=bev;mod.segments=3;bpy.ops.object.modifier_apply(modifier=mod.name)
 o.data.materials.append(m);return record(o,kind,zone)
def join(n,objs,kind,zone):
 bpy.ops.object.select_all(action='DESELECT')
 for o in objs:o.select_set(True)
 bpy.context.view_layer.objects.active=objs[0];bpy.ops.object.join();o=bpy.context.object;o.name='BW1_'+n
 new[:]=[(a,b,c) for a,b,c in new if a not in objs];new.append((o,kind,zone));zones[o.name]=zone;return o
def rod(n,a,b,r,m,kind,zone):
 a,b=Vector(a),Vector(b);v=b-a
 bpy.ops.mesh.primitive_cylinder_add(vertices=16,radius=r,depth=v.length,location=(a+b)/2)
 o=bpy.context.object;o.name='BW1_'+n;o.rotation_euler=v.to_track_quat('Z','Y').to_euler();o.data.materials.append(m)
 for f in o.data.polygons:f.use_smooth=len(f.vertices)==4
 return record(o,kind,zone)
def chair(n,x,y,zone):
 # Faces east/west-wall desk: the user sits facing +X; seat450x450, chair back west.
 ps=[box(n+'_SEAT',(x,y,.87),(x+.45,y+.45,.925),cloth,zone=zone,bev=.02),
 box(n+'_BACK',(x,y,.96),(x+.045,y+.45,1.28),wood,zone=zone,bev=.022)]
 for lx in [x+.055,x+.365]:
  for ly in [y+.045,y+.365]:ps.append(rod(n+'_LEG',(lx,ly,.45),(lx,ly,.875),.017,wood,'chair',zone))
 # Back posts actually meet seat and backrest; no floating upholstered block.
 for ly in [y+.045,y+.40]:ps.append(rod(n+'_BACK_POST',(x+.025,ly,.89),(x+.025,ly,1.13),.014,wood,'chair',zone))
 return join(n,ps,'chair',zone)
def cabinet(n,a,b,zone,open_top=False):
 x0,y0,z0=a;x1,y1,z1=b;t=.018
 ps=[box(n+'_BOTTOM',(x0,y0,z0+.07),(x1,y1,z0+.088),wood,zone=zone),
 box(n+'_TOP',(x0,y0,z1-t),(x1,y1,z1),wood,zone=zone),
 box(n+'_BACK',(x0,y0,z0+.088),(x0+t,y1,z1-t),ivory,zone=zone)]
 for y in [y0,y1-t]:ps.append(box(n+'_SIDE',(x0,y,z0+.088),(x1,y+t,z1-t),wood,zone=zone))
 for z in [z0+(z1-z0)*.44,z0+(z1-z0)*.72]:ps.append(box(n+'_SHELF',(x0+t,y0+t,z),(x1,y1-t,z+t),wood,zone=zone))
 for y in [y0+.025,y1-.065]:
  ps.append(box(n+'_FOOT',(x0+.03,y,z0),(x1-.03,y+.04,z0+.07),wood,zone=zone))
 # Closed lower band, actual shelf divisions above; door(front +X) stores small items.
 ps.append(box(n+'_DOOR',(x1,y0+.025,z0+.10),(x1+.016,y1-.025,z0+(z1-z0)*.43),wood,zone=zone))
 ps.append(rod(n+'_PULL',(x1+.024,y0+.08,z0+.30),(x1+.024,y0+.16,z0+.30),.008,dark,'handle',zone))
 return join(n,ps,'storage',zone)
def transform_bounds(n,new_a,new_b):
 o=bpy.data.objects[n];old=bb(o);inv=o.matrix_world.inverted();o.data=o.data.copy()
 for v in o.data.vertices:
  w=o.matrix_world@v.co
  w=Vector([new_a[i]+(w[i]-old[0][i])/(old[1][i]-old[0][i])*(new_b[i]-new_a[i]) for i in range(3)])
  v.co=inv@w
 o.data.update();return o
# Couple:1800 width measured over bedframe proxy;200mm south,100mm east.
couple=transform_bounds('B11_Rectangle012_CATALOG_00_00',(9.166625,1.187156,.45),(11.266625,2.987156,1.0))
mother=transform_bounds('B11_Rectangle013_CATALOG_00_00',(13.072875,1.645531,.45),(15.172875,3.145531,1.0))
# Guest maintains1800x1200,140mm east closes the removed thick headboard setback.
guest=transform_bounds('B11_Rectangle017_CATALOG_00_00',(11.018375,8.019843,.45),(12.818375,9.219843,1.0))
edited={couple.name,mother.name,guest.name}
# Guestwardrobe:retainnorthanchor/three500mmdoorleaves; remove southern500mm bay.
for n in ['B11_Rectangle045_BACK','B11_Rectangle045_BASE','B11_Rectangle045_PLINTH',
 'B11_Rectangle045_SHELF','B11_Rectangle045_TOP']:
 a,b=bb(bpy.data.objects[n]);a[1]+=.5;transform_bounds(n,a,b);edited.add(n)
n='B11_Rectangle045_L';a,b=bb(bpy.data.objects[n]);a[1]+=.5;b[1]+=.5;transform_bounds(n,a,b);edited.add(n)
for bed in [couple,mother,guest]:
 bed.data.materials.clear();bed.data.materials.append(cloth)
 for f in bed.data.polygons:f.material_index=0
for tag,bed,zone,headx,sidecolor in [('COUPLE',couple,'couple',11.34,cloth),('MOTHER',mother,'mother',15.235,cloth),('GUEST',guest,'guest',12.857,blue)]:
 a,b=bb(bed);y0,y1=a[1],b[1]
 margin=0 if zone=='guest' else .025
 h=box(tag+'_THIN_HEADBOARD',(headx,y0-margin,.53),(headx+.024,y1+margin,1.47),wood,'headboard',zone)
 ps=[box(tag+'_SOFT_HEADREST',(headx-.030,y0+.03,.95),(headx,y1-.03,1.43),sidecolor,'soft_headrest',zone,.014)]
 # Existing catalog bed already includes pillows; do not add a secondstack.
 box(tag+'_BED_RUNNER',(a[0]+.14,y0+.04,1.001),(a[0]+.58,y1-.04,1.016),sidecolor,'textile',zone,.007)
parts['mother_bedside']=cabinet('MOTHER_BEDSIDE',(14.68,1.14,.45),(15.10,1.54,1.03),'mother')
parts['couple_bedside_n']=cabinet('COUPLE_BEDSIDE_N',(10.84,3.04,.45),(11.22,3.38,1.03),'couple')
parts['couple_bedside_s']=cabinet('COUPLE_BEDSIDE_S',(10.84,.77,.45),(11.22,1.10,1.03),'couple')
# MotherSW:900-long vanity along west wall,450deep. Existing TV cabinet untouched.
ps=[box('VANITY_TOP',(11.65,.28,1.176),(12.10,1.18,1.20),wood,zone='mother',bev=.012),
 box('VANITY_DRAWER',(11.67,.31,1.08),(12.08,.58,1.175),wood,zone='mother')]
for x in [11.70,12.04]:
 for y in [.34,1.11]:ps.append(rod('VANITY_LEG',(x,y,.45),(x,y,1.176),.016,wood,'desk','mother'))
parts['vanity']=join('MOTHER_VANITY',ps,'vanity','mother')
box('MOTHER_MIRROR_FRAME',(11.635,.46,1.31),(11.66,1.05,1.86),wood,'mirror','mother')
box('MOTHER_MIRROR',(11.661,.49,1.34),(11.665,1.02,1.83),mirror,'mirror','mother',.005)
# Chair helper faces+X. Rotate mother chair180deg about its center to face west.
parts['vanity_chair']=chair('MOTHER_VANITY_CHAIR',12.13,.50,'mother')
o=parts['vanity_chair'];pivot=Vector((12.355,.725,.45))
o.matrix_world=Matrix.Translation(pivot)@Matrix.Rotation(math.pi,4,'Z')@Matrix.Translation(-pivot)@o.matrix_world
# CoupleSW:shallow open/closed900x280x1050;TV/viewingwallmiddle stays clear.
parts['couple_shelf']=cabinet('COUPLE_SHALLOW_SHELF',(8.10,.40,.45),(8.364,1.30,1.50),'couple')
for i in range(3):box('COUPLE_BOOK_'+str(i),(8.18,.48+i*.075,1.225),(8.36,.53+i*.075,1.44),green,'book','couple',.002)
# Continuous1640mmworktop, with40x130mmfrontcornernotcharoundexistingbalconyrightcasing.
outline=[(12.33,9.24),(12.88,9.24),(12.88,10.88),(12.46,10.88),(12.46,10.84),(12.33,10.84)]
verts=[(x,y,z) for z in [1.176,1.20] for x,y in outline];k=len(outline)
faces=[tuple(range(k-1,-1,-1)),tuple(range(k,2*k))]+[(i,(i+1)%k,(i+1)%k+k,i+k) for i in range(k)]
mesh=bpy.data.meshes.new('Continuous guest tabletop with casing notch');mesh.from_pydata(verts,[],faces);mesh.update()
o=bpy.data.objects.new('BW1_GUEST_DESK_TOP',mesh);bpy.context.scene.collection.objects.link(o);o.data.materials.append(wood)
record(o,'desk','guest');bpy.context.view_layer.objects.active=o
mod=o.modifiers.new('Rounded desktop','BEVEL');mod.width=.009;mod.segments=3;bpy.ops.object.modifier_apply(modifier=mod.name)
ps=[o]
for x in [12.38,12.82]:
 for y in [9.30,10.81]:ps.append(rod('GUEST_DESK_LEG',(x,y,.45),(x,y,1.176),.018,wood,'desk','guest'))
ps.append(box('GUEST_DESK_DRAWER',(12.35,10.40,1.08),(12.84,10.68,1.175),ivory,zone='guest'))
parts['guest_desk']=join('GUEST_DESK',ps,'desk','guest')
parts['guest_chair']=chair('GUEST_DESK_CHAIR',11.84,9.96,'guest')
# Real perforated panel inYZplane; eachcell has eight-sided through-hole.
verts=[];faces=[];x0,x1=12.848,12.866;cell=.06;y0,z0=9.61,1.32
for iy in range(17):
 for iz in range(9):
  cy=y0+(iy+.5)*cell;cz=z0+(iz+.5)*cell
  outer=[(-.5,-.5),(0,-.5),(.5,-.5),(.5,0),(.5,.5),(0,.5),(-.5,.5),(-.5,0)]
  start=len(verts)
  for x in [x0,x1]:
   verts.extend((x,cy+u*cell,cz+v*cell) for u,v in outer)
   for i in range(8):
    angle=(-135+i*45)*math.pi/180;verts.append((x,cy+.0055*math.cos(angle),cz+.0055*math.sin(angle)))
  for i in range(8):
   j=(i+1)%8
   faces.extend([(start+i,start+j,start+8+j,start+8+i),
    (start+16+i,start+24+i,start+24+j,start+16+j),
    (start+8+i,start+8+j,start+24+j,start+24+i),
    (start+i,start+16+i,start+16+j,start+j)])
mesh=bpy.data.meshes.new('Pegboard holes');mesh.from_pydata(verts,[],faces);mesh.update()
o=bpy.data.objects.new('BW1_GUEST_PEGBOARD',mesh);col.objects.link(o);o.data.materials.append(ivory)
new.append((o,'pegboard','guest'));zones[o.name]='guest'
# House-shaped display frame:two slopedroofrails, shelf and uprights; visually open.
ps=[box('GUEST_DISPLAY_SHELF',(12.64,9.72,1.94),(12.88,10.59,1.963),wood,zone='guest'),
 box('GUEST_DISPLAY_LEFT',(12.72,9.72,1.96),(12.88,9.744,2.24),wood,zone='guest'),
 box('GUEST_DISPLAY_RIGHT',(12.72,10.566,1.96),(12.88,10.59,2.24),wood,zone='guest'),
 rod('GUEST_ROOF',(12.84,9.732,2.24),(12.84,10.155,2.48),.016,wood,'display','guest'),
 rod('GUEST_ROOF',(12.84,10.155,2.48),(12.84,10.578,2.24),.016,wood,'display','guest')]
parts['guest_display']=join('GUEST_HOUSE_DISPLAY',ps,'display_shelf','guest')
for i in range(4):box('GUEST_BOOK_'+str(i),(12.65,9.80+i*.052,1.964),(12.84,9.838+i*.052,2.16),blue if i%2 else green,'book','guest',.002)
for i in range(3):
 box('GUEST_ART_BLOCK_'+str(i),(12.49+i*.04,10.23,1.202),(12.53+i*.04,10.275,1.26+i*.015),blue if i%2 else wood,'toy','guest',.004)
# Generic cloud wall light; original outline, no licensedcharacterornewwallopening.
poly=[(-.23,0),(.23,0),(.24,.035),(.22,.09),(.17,.13),(.115,.115),(.08,.19),(.025,.23),(-.055,.22),(-.11,.16),(-.16,.17),(-.205,.14),(-.245,.09),(-.255,.04)]
verts=[(x,8.61+y,1.81+z) for x in [12.845,12.868] for y,z in poly];n=len(poly)
faces=[tuple(range(n-1,-1,-1)),tuple(range(n,2*n))]+[(i,(i+1)%n,(i+1)%n+n,i+n) for i in range(n)]
mesh=bpy.data.meshes.new('Cloud outline');mesh.from_pydata(verts,[],faces);mesh.update()
o=bpy.data.objects.new('BW1_GUEST_CLOUD_WALL_LIGHT',mesh);col.objects.link(o);o.data.materials.append(ivory)
new.append((o,'wall_light','guest'));zones[o.name]='guest'
mod=o.modifiers.new('Soft cloud rim','BEVEL');mod.width=.008;mod.segments=4;bpy.context.view_layer.objects.active=o;bpy.ops.object.modifier_apply(modifier=mod.name)
bpy.context.view_layer.update()
# Actualtriangle intersections against named wallparts and guest/bedroom door frames.
treecache={}
def tree(o):
 if o.name not in treecache:treecache[o.name]=BVHTree.FromPolygons([o.matrix_world@v.co for v in o.data.vertices],[list(f.vertices) for f in o.data.polygons],epsilon=1e-6)
 return treecache[o.name]
walls=sum(audit['wall_groups'].values(),[])
arch=sorted(set(walls+[r['name'] for r in audit['rows'] if r['name'].startswith(('V4_D-','R4_BEDROOM_DOOR','V4_GUEST_'))]))
collision=[]
for o,typ,zone in new:
 for n in arch:
  a=bpy.data.objects.get(n)
  if a and a.type=='MESH' and not(a.hide_render or a.hide_viewport) and tree(o).overlap(tree(a)):collision.append([o.name,n])
assert not collision,collision
# Wardrobe leaf sweeps computed from registered frontpanels, both hingechoices.
sweeps=[]
for pre,targets in [('R3_WARDROBE_FRONT_',[couple,parts['couple_bedside_n']]),('B11_Rectangle015_FRONT_',[mother]),
 ('B11_Rectangle045_FRONT_',[guest,parts['guest_desk'],parts['guest_chair']])]:
 for b in base['bindings']:
  if not b['native_id'].startswith(pre) or b['native_id'] in retired:continue
  leaf=bpy.data.objects[b['native_id']];a,c=bb(leaf)
  hinges=[('left',Vector((a[0],a[1],a[2])),-1),('right',Vector((c[0],a[1],a[2])),1)]
  if pre=='B11_Rectangle045_FRONT_':
   hinges=[('south',Vector((c[0],a[1],a[2])),-1),('north',Vector((c[0],c[1],a[2])),1)]
  for side,pivot,sign in hinges:
   for angle in range(0,91,5):
    M=Matrix.Translation(pivot)@Matrix.Rotation(sign*math.radians(angle),4,'Z')@Matrix.Translation(-pivot)@leaf.matrix_world
    lt=BVHTree.FromPolygons([M@v.co for v in leaf.data.vertices],[list(f.vertices) for f in leaf.data.polygons],epsilon=1e-6)
    for o in targets:
     if lt.overlap(tree(o)):sweeps.append([leaf.name,side,angle,o.name])
assert not sweeps,sweeps
# Guestentry85cm leaf;assume interior hingeleft andright tocheck conservative sweeps.
entry=bpy.data.objects['V4_D-GUEST-ROOM_LEAF_0'];a,c=bb(entry);entryhits=[]
for side,px in [('left',a[0]),('right',c[0])]:
 for angle in range(0,91,5):
  pivot=Vector((px,a[1],a[2]));sign=1 if side=='left' else -1
  M=Matrix.Translation(pivot)@Matrix.Rotation(sign*math.radians(angle),4,'Z')@Matrix.Translation(-pivot)@entry.matrix_world
  lt=BVHTree.FromPolygons([M@v.co for v in entry.data.vertices],[list(f.vertices) for f in entry.data.polygons],epsilon=1e-6)
  for o in [guest,parts['guest_desk'],parts['guest_chair']]:
   if lt.overlap(tree(o)):entryhits.append([side,angle,o.name])
assert not entryhits,entryhits
assert abs(bb(couple)[1][1]-bb(couple)[0][1]-1.8)<1e-5
assert abs(bb(mother)[1][1]-bb(mother)[0][1]-1.5)<1e-5
assert abs(bb(guest)[1][1]-bb(guest)[0][1]-1.2)<1e-5
couplegap=3.9080936908721924-bb(couple)[1][1];mothergap=3.8469998836517334-bb(mother)[1][1]
assert couplegap>=.50 and mothergap>=.50
for n,s in before.items():
 now=state(bpy.data.objects[n])
 if n in retired:assert all(now[k]==s[k] for k in s if k!='hidden'),n
 elif n not in edited:assert now==s,n
triangles=sum(sum(len(f.vertices)-2 for f in o.data.polygons) for o,_,_ in new)
assert triangles<50000,triangles
for o,typ,zone in new:
 o['design_role']=typ;o['design_room']=zone;o['authority']='DERIVED_DESIGN_MODEL'
 o['global_id']='ent_'+uuid.uuid5(uuid.NAMESPACE_URL,'c_type_home:bedroomswoodv1:'+o.name).hex
reg={k:v for k,v in base.items() if k!='bindings'}
reg.update(source_resource_id='c_type_bedrooms_wood_v1',source_revision=REV,registry_revision=REV,
 source_locator=str(R/'BEDROOMS_WOOD_V2.blend'),source_authority='frozen')
reg['bindings']=[b for b in base['bindings'] if b['native_id'] not in retired]
roomkeys={'mother':'candidate_R-MASTER','couple':'candidate_R-BED-S','guest':'candidate_R-STUDY'}
for o,typ,zone in new:reg['bindings'].append({'entity_id':o['global_id'],'adapter':'blender','native_id':o.name,
 'semantic_type':typ,'room_id':roomkeys[zone],'authority_level':'HUMAN_DESIGN_GUIDE'})
bpy.ops.wm.save_as_mainfile(filepath=reg['source_locator']);reg['source_sha256']=sha(reg['source_locator'])
(R/'spatial-canvas.bindings.full.json').write_text(json.dumps(reg,ensure_ascii=False,indent=2)+'\n')
layout={'status':'HUMAN_REVIEW','revision':REV,'parent_source':str(SRC),'parent_sha256':TRUTHS[str(SRC)],
 'source':reg['source_locator'],'source_sha256':reg['source_sha256'],'retired_native_ids':retired,'edited_native_ids':sorted(edited),
 'rooms':{'mother':{'bed_size_m':[2.1,1.5],'bed_translation_m':[.13,0,0],'tv_cabinet_retained':True,'vanity_size_m':[.9,.45,.75]},
 'couple':{'bed_size_m':[2.1,1.8],'bed_translation_m':[.10,-.20,0],'tv_cabinet_removed':True,'shallow_shelf_size_m':[.9,.28,1.05]},
 'guest':{'bed_size_m':[1.8,1.2],'bed_translation_m':[.14,0,0],'desk_size_m':[1.64,.55,.75],'bunk_added':False,
 'wardrobe_size_m':[1.5,.5,2.2],'wardrobe_door_count':3,'wardrobe_south_end_retracted_m':.5,
 'desk_full_run':'bededge to northwall;20mminstallationgapsatends',
 'desk_existing_door_casing_notch_m':[.13,.04],
 'adult_bed_length_note':'Inherited1800mm length preserved; future purchasedbedproductlength remains user review.',
 'features':['perforated_board','house_outline_display','cloud_wall_light','replaceable_books_and_toys']}},
 'evidence':{'new_furniture_triangles':triangles,'frozen_hashes':TRUTHS,'source_object_fingerprints_unchanged_outside_scope':True,
 'wall_door_intersections':collision,'wardrobe_frontpanel_0to90deg_sweeps_both_hinge_options':sweeps,'guest_entry_sweeps':entryhits},
 'clearances_m':{'couple_wardrobe_to_bed':couplegap,'mother_wardrobe_to_bed':mothergap,
 'mother_tv_to_bedfoot':bb(mother)[0][0]-12.1068754196167,
 'guest_central_route_chair_parked':bb(parts['guest_chair'])[0][0]-10.418125,
 'guest_central_route_chair_pulled250mm':bb(parts['guest_chair'])[0][0]-.25-10.418125,
 'guest_entry_clear_width':.85,'guest_desk_north_to_balcony_track':10.965-bb(parts['guest_desk'])[1][1]},
 'clearance_method':'World-axis furniture envelopes and evaluated triangle surface intersection/leaf sweeps; model review, notcodecertification.',
 'architecture_unchanged':True,'all_other_accepted_rooms_preserved':True,'textures':False,'cycles':False}
(R/'BEDROOMS_LAYOUT_REVIEW.json').write_text(json.dumps(layout,ensure_ascii=False,indent=2)+'\n')
assert all(sha(p)==h for p,h in TRUTHS.items())
print('BEDROOM_BUILD_PASS',len(reg['bindings']),json.dumps(layout['clearances_m']),triangles)
