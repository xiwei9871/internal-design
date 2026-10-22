"""Sequential furniture/mirror successor; source-proportion review, not fabrication."""
import bpy,bmesh,json,hashlib,uuid,math,struct
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
ROOT=Path(__file__).resolve().parents[1];R=ROOT/'design/console_bath_mirrors_review'
PARENT=ROOT/'design/secondary_bath850_review'
REG=json.loads((PARENT/'spatial-canvas.bindings.full.json').read_text());SRC=Path(REG['source_locator'])
REV='console400-three-bath-mirrors-review-1';OUT=R/'CONSOLE400_THREE_BATH_MIRRORS.blend'
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
TRUTHS={str(SRC):'4e94f187a7a6c67697aa6c939ac6e88f58c8ca129830e628f7229522d4ce37bc',
 '/Users/xiwei/interior_design/projects/c_type_home/design/bedroom_door_r4/OPTION_A_SLIDING_R4.blend':'d109c7efcfa2b2b2565e4c073ee0cdf5282b23c01122bc9c1bbe7b8791ac3afb',
 '/Users/xiwei/interior_design/projects/c_type_home/design/blender_b0/B0_EXISTING_AS_IS.blend':'717e6dc4a3d4fb6325512236f5c235ded702376309456028129bf0889548efcb'}
assert all(sha(p)==h for p,h in TRUTHS.items())
bpy.ops.wm.open_mainfile(filepath=str(SRC));bpy.context.view_layer.update()
def state(o):
 h=hashlib.sha256()
 if o.type=='MESH':
  for v in o.data.vertices:h.update(struct.pack('<fff',*v.co))
  for f in o.data.polygons:h.update(struct.pack('<'+'I'*len(f.vertices),*f.vertices))
 return (h.hexdigest(),tuple(float(v) for row in o.matrix_world for v in row),str(sorted(o.items())),
  (o.hide_render,o.hide_viewport,o.hide_get()),tuple(m.name if m else None for m in o.data.materials) if o.type=='MESH' else (),o.parent.name if o.parent else None)
before={o.name:state(o) for o in bpy.context.scene.objects}
retired=[b['native_id'] for b in REG['bindings'] if b['native_id'].startswith(('BW1_COUPLE_SHALLOW_SHELF','BW1_COUPLE_BOOK_'))]
for n in retired:o=bpy.data.objects[n];o.hide_render=True;o.hide_viewport=True;o.hide_set(True)
col=bpy.data.collections.new('COL_CONSOLE_BATH_MIRRORS');bpy.context.scene.collection.children.link(col)
new=[];edited=[];roomobjects={};groups={}
def mat(n,c,rough=.85,metal=0):
 m=bpy.data.materials.new('CBM_'+n);m.diffuse_color=(*c,1);m.use_nodes=True
 s=m.node_tree.nodes.get('Principled BSDF');s.inputs['Base Color'].default_value=(*c,1);s.inputs['Roughness'].default_value=rough;s.inputs['Metallic'].default_value=metal;return m
wood=mat('PALE_ASH',(.69,.56,.40));white=mat('WARM_WHITE',(.85,.84,.79));mirror=mat('MIRROR_REVIEW',(.58,.70,.73),.08,.75)
rim=mat('BRUSHED_NICKEL',(.52,.53,.49),.32,.65);green=mat('SAGE',(.39,.50,.43));linen=mat('LINEN',(.75,.72,.63));dark=mat('DARK_HARDWARE',(.24,.28,.27))
def regnew(o,typ,room):
 for c in list(o.users_collection):c.objects.unlink(o)
 col.objects.link(o);o['design_role']=typ;o['review_room']=room;o['authority']='DERIVED_DESIGN_MODEL';o['global_id']='ent_'+uuid.uuid5(uuid.NAMESPACE_URL,'c_type_home:consolebathmirrors:'+o.name).hex
 new.append((o,typ,room));roomobjects.setdefault(room,[]).append(o.name);return o
def mesh(n,vs,fs,m,typ,room):
 me=bpy.data.meshes.new(n+'_mesh');me.from_pydata(vs,[],fs);me.update()
 bm=bmesh.new();bm.from_mesh(me);bmesh.ops.recalc_face_normals(bm,faces=bm.faces);bm.to_mesh(me);bm.free()
 o=bpy.data.objects.new('CBM_'+n,me);bpy.context.scene.collection.objects.link(o);o.data.materials.append(m);return regnew(o,typ,room)
def box(n,a,b,m,typ,room,bevel=.004):
 bpy.ops.mesh.primitive_cube_add(size=1,location=[(a[i]+b[i])/2 for i in range(3)])
 o=bpy.context.object;o.name='CBM_'+n;o.scale=[b[i]-a[i] for i in range(3)];bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
 if bevel:
  q=o.modifiers.new('Soft edges','BEVEL');q.width=bevel;q.segments=3;bpy.ops.object.modifier_apply(modifier=q.name)
 o.data.materials.append(m);return regnew(o,typ,room)
def cylinder(n,center,r0,r1,height,m,typ,room):
 bpy.ops.mesh.primitive_cone_add(vertices=48,radius1=r0,radius2=r1,depth=height,location=center)
 o=bpy.context.object;o.name='CBM_'+n;o.data.materials.append(m)
 for p in o.data.polygons:p.use_smooth=len(p.vertices)==4
 return regnew(o,typ,room)
def join(n,ps,typ,room):
 oldnames=[p.name for p in ps]
 bpy.ops.object.select_all(action='DESELECT')
 for p in ps:p.select_set(True)
 bpy.context.view_layer.objects.active=ps[0];bpy.ops.object.join();o=bpy.context.object;o.name='CBM_'+n
 new[:]=[(a,b,c) for a,b,c in new if a not in ps];new.append((o,typ,room));roomobjects[room]=[x for x in roomobjects[room] if x not in oldnames]+[o.name]
 o['global_id']='ent_'+uuid.uuid5(uuid.NAMESPACE_URL,'c_type_home:consolebathmirrors:'+o.name).hex;return o
def bounds(o):
 vs=[o.matrix_world@v.co for v in o.data.vertices];return [[min(v[i] for v in vs) for i in range(3)],[max(v[i] for v in vs) for i in range(3)]]
def recolor(o,m):
 o.data=o.data.copy();o.data.materials.clear();o.data.materials.append(m)
 for f in o.data.polygons:f.material_index=0
 edited.append(o.name)
# 1. Bedroom:2000x400x400,centreY2.087156. Naturalfrontedge never exceeds400mm envelope.
y0,y1=1.087156,3.087156
outline=[(8.05,y0),(8.45,y0)]
for k in range(1,40):
 y=y0+(y1-y0)*k/40;front=8.438+.010*math.sin(k*.63)+.001*math.sin(k*1.7);outline.append((front,y))
outline.extend([(8.45,y1),(8.05,y1)]);N=len(outline)
top=mesh('COUPLE_CONSOLE_TOP',[(x,y,z) for z in [.815,.85] for x,y in outline],
 [tuple(range(N-1,-1,-1)),tuple(range(N,2*N))]+[(i,(i+1)%N,(i+1)%N+N,i+N) for i in range(N)],wood,'console','couple')
bpy.context.view_layer.objects.active=top;q=top.modifiers.new('Natural edge softness','BEVEL');q.width=.003;q.segments=3;bpy.ops.object.modifier_apply(modifier=q.name)
ps=[]
for x in [8.105,8.34]:ps.append(box('CONSOLE_PORTAL_POST',(x,y0+.19,.45),(x+.045,y0+.245,.815),wood,'support','couple'))
ps.append(box('CONSOLE_PORTAL_BRACE',(8.105,y0+.19,.770),(8.385,y0+.245,.815),wood,'support','couple'))
join('COUPLE_CONSOLE_PORTAL',ps,'support','couple')
cylinder('COUPLE_CONSOLE_PEDESTAL',(8.255,y1-.25,.6325),.13,.10,.365,wood,'support','couple')
# Shallowhollowdrawer,fronttowardsbed;removabledisplaypiece,notfinaljoinerydetail.
ps=[box('DRAWER_BOTTOM',(8.10,y0+.38,.690),(8.43,y0+.87,.708),wood,'drawer','couple'),
 box('DRAWER_FRONT',(8.43,y0+.38,.690),(8.448,y0+.87,.814),wood,'drawer','couple'),
 box('DRAWER_BACK',(8.10,y0+.38,.708),(8.118,y0+.87,.814),white,'drawer','couple')]
for y in [y0+.38,y0+.852]:ps.append(box('DRAWER_SIDE',(8.118,y,.708),(8.43,y+.018,.814),wood,'drawer','couple'))
join('COUPLE_CONSOLE_DRAWER',ps,'drawer','couple')
for i in range(3):box('CONSOLE_BOOK_'+str(i),(8.17,y0+.98+i*.04,.852),(8.39,y0+1.012+i*.04,1.045+i*.018),green if i%2 else linen,'book','couple',.002)
cylinder('CONSOLE_VASE_BODY',(8.25,y1-.36,.94),.058,.045,.18,white,'vase','couple')
cylinder('CONSOLE_VASE_NECK',(8.25,y1-.36,1.047),.024,.024,.034,white,'vase','couple')
# Palehorizontalartplate,1200x600,onlyreviewcomposition;projectioncanusefuture retractablescreen.
box('COUPLE_ART_FRAME',(8.013,1.487156,1.39),(8.037,2.687156,1.99),wood,'artwork','couple')
box('COUPLE_ART_PAPER',(8.037,1.505156,1.408),(8.040,2.669156,1.972),white,'artwork','couple',.001)
mesh('COUPLE_ART_LOW_LANDSCAPE',[(8.041,1.51,1.41),(8.041,1.87,1.57),(8.041,2.16,1.49),(8.041,2.46,1.66),(8.041,2.665,1.50),(8.041,2.665,1.41)],[(0,1,2,3,4,5)],linen,'artwork','couple')
print('SEQUENCE_1_BEDROOM_BUILT')
# Vanitylocalu(width),v(outwardfromwall),zabsolute;sourcefloor450mm,existingcountertop1300mm.
configs={'master':{'u0':13.1385,'u1':14.3385,'wall':6.3999,'normal':'south','cab':'B11_Rectangle035_DIMENSIONAL_BODY','mirror_center':13.5985,'mirror_width':.88,'storage':[14.0885,14.3385]},
 'secondary':{'u0':9.228,'u1':10.428,'wall':6.4499,'normal':'south','cab':None,'mirror_center':9.828,'mirror_width':.65,'storage':[10.185,10.405]},
 'guest':{'u0':8.0123,'u1':9.2123,'wall':8.0001,'normal':'east','cab':'B11_Rectangle030_DIMENSIONAL_BODY','mirror_center':8.5023,'mirror_width':.90,'storage':[9.025,9.245]}}
def xyz(c,u,v,z):return (u,c['wall']-v,z) if c['normal']=='south' else (c['wall']+v,u,z)
def localbox(c,n,a,b,m,typ,room,bev=.004):
 a=xyz(c,*a);b=xyz(c,*b);return box(n,[min(a[i],b[i]) for i in range(3)],[max(a[i],b[i]) for i in range(3)],m,typ,room,bev)
def shape(c,n,poly,v0,v1,m,typ,room):
 nn=len(poly);vs=[xyz(c,u,v,z) for v in [v0,v1] for u,z in poly]
 return mesh(n,vs,[tuple(range(nn-1,-1,-1)),tuple(range(nn,2*nn))]+[(i,(i+1)%nn,(i+1)%nn+nn,i+nn) for i in range(nn)],m,typ,room)
def roundedrect(cx,cz,w,h,r):
 pts=[]
 for ux,zz,start in [(cx+w/2-r,cz+h/2-r,0),(cx-w/2+r,cz+h/2-r,90),(cx-w/2+r,cz-h/2+r,180),(cx+w/2-r,cz-h/2+r,270)]:
  for k in range(9):
   t=math.radians(start+k*90/8);pts.append((ux+r*math.cos(t),zz+r*math.sin(t)))
 return pts
def upper(c,room):
 u0,u1=c['storage'];v0,v1=.003,.145;z0,z1=1.49,2.25;t=.014
 ps=[localbox(c,room+'_UPPER_BACK',(u0,v0,z0),(u1,v0+.012,z1),white,'storage',room)]
 for u in [u0,u1-t]:ps.append(localbox(c,room+'_UPPER_SIDE',(u,v0,z0),(u+t,v1,z1),wood,'storage',room))
 for z in [z0,z0+.25,z0+.50,z1-t]:ps.append(localbox(c,room+'_UPPER_SHELF',(u0+t,v0+.012,z),(u1-t,v1,z+t),wood,'storage',room))
 join(room.upper()+'_UPPER_STORAGE',ps,'storage',room)
 for i in range(2):
  u=u0+.07+i*.09;v=.06
  loc=xyz(c,u,v,z0+.014+.05);cylinder(room+'_BOTTLE_'+str(i),loc,.018,.018,.10,white if i else green,'toiletry',room)
for sequence,room in enumerate(['master','secondary','guest'],2):
 c=configs[room];cabname=c['cab']
 # Genericexistingcabinet footprint retained,topbecomesplainwhite,frontash doors.
 if cabname:
  o=bpy.data.objects[cabname];recolor(o,wood);old=bounds(o);inv=o.matrix_world.inverted()
  for v in o.data.vertices:
   w=o.matrix_world@v.co;w.z=.45+(w.z-.45)*(.825/.85);v.co=inv@w
  o.data.update()
  ca,cb=bounds(o);uv0,uv1=c['u0'],c['u1']
  front=(c['wall']-ca[1]) if c['normal']=='south' else cb[0]-c['wall'];back=(c['wall']-cb[1]) if c['normal']=='south' else ca[0]-c['wall']
  localbox(c,room+'_COUNTERTOP',(uv0,back,1.275),(uv1,front,1.3),white,'countertop',room,.004)
  for i in range(2):
   a=uv0+i*.60+.018;b=uv0+(i+1)*.60-.018
   localbox(c,room+'_LOWER_DOOR_'+str(i),(a,front,.56),(b,front+.014,1.25),wood,'cabinet_door',room,.003)
  # Basin/rim reviewbody keptwithin currentcounterfootprint: bool recessintocounterandbase.
  centre=(uv0+uv1)/2
  if room=='master':vcentre=(front+back)/2;uw,vw=.50,.31
  else:vcentre=(front+back)/2;uw,vw=.50,.33
  cuts=[]
  for n in [cabname,'CBM_'+room+'_COUNTERTOP']:
   target=bpy.data.objects[n]
   a=xyz(c,centre-uw/2,vcentre-vw/2,1.15);b=xyz(c,centre+uw/2,vcentre+vw/2,1.35)
   bpy.ops.mesh.primitive_cube_add(size=1,location=[(a[i]+b[i])/2 for i in range(3)]);cut=bpy.context.object;cut.scale=[abs(b[i]-a[i]) for i in range(3)];bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
   q=target.modifiers.new('Basin recess','BOOLEAN');q.object=cut;q.operation='DIFFERENCE';q.solver='EXACT';bpy.context.view_layer.objects.active=target;bpy.ops.object.modifier_apply(modifier=q.name);bpy.data.objects.remove(cut,do_unlink=True)
  ps=[localbox(c,room+'_BASIN_BOTTOM',(centre-uw/2,vcentre-vw/2,1.16),(centre+uw/2,vcentre+vw/2,1.172),white,'basin',room,.003)]
  for u in [centre-uw/2,centre+uw/2-.012]:ps.append(localbox(c,room+'_BASIN_SIDE',(u,vcentre-vw/2,1.172),(u+.012,vcentre+vw/2,1.304),white,'basin',room,.003))
  for v in [vcentre-vw/2,vcentre+vw/2-.012]:ps.append(localbox(c,room+'_BASIN_SIDE',(centre-uw/2+.012,v,1.172),(centre+uw/2-.012,v+.012,1.304),white,'basin',room,.003))
  join(room.upper()+'_BASIN',ps,'basin',room)
  # Simple mixerfixture,no plumbingrerouting inferred.
  localbox(c,room+'_TAP_STEM',(centre-.018,back+.035,1.30),(centre+.018,back+.07,1.47),rim,'tap',room,.01)
  localbox(c,room+'_TAP_SPOUT',(centre-.018,back+.05,1.45),(centre+.018,vcentre-.045,1.48),rim,'tap',room,.008)
 else:
  for b in REG['bindings']:
   if b['native_id'].startswith('R3_VANITY'):
    o=bpy.data.objects[b['native_id']];recolor(o,white if b['native_id'].endswith(('TOP','BASIN_REVIEW')) else rim if 'PULL' in b['native_id'] else wood)
  # Turntheinheritedflatbasinreviewplateintoareadablebowl atits same registeredcentre.
  centre=9.828;vcentre=.2747;uw,vw=.48,.28;target=bpy.data.objects['R3_VANITY_TOP']
  a=xyz(c,centre-uw/2,vcentre-vw/2,1.15);b=xyz(c,centre+uw/2,vcentre+vw/2,1.35)
  bpy.ops.mesh.primitive_cube_add(size=1,location=[(a[i]+b[i])/2 for i in range(3)]);cut=bpy.context.object;cut.scale=[abs(b[i]-a[i]) for i in range(3)];bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
  q=target.modifiers.new('Same-centre basin recess','BOOLEAN');q.object=cut;q.operation='DIFFERENCE';q.solver='EXACT';bpy.context.view_layer.objects.active=target;bpy.ops.object.modifier_apply(modifier=q.name);bpy.data.objects.remove(cut,do_unlink=True)
  ps=[localbox(c,'SECONDARY_BOWL_BOTTOM',(centre-uw/2,vcentre-vw/2,1.16),(centre+uw/2,vcentre+vw/2,1.172),white,'basin',room,.003)]
  for u in [centre-uw/2,centre+uw/2-.012]:ps.append(localbox(c,'SECONDARY_BOWL_SIDE',(u,vcentre-vw/2,1.172),(u+.012,vcentre+vw/2,1.304),white,'basin',room,.003))
  for v in [vcentre-vw/2,vcentre+vw/2-.012]:ps.append(localbox(c,'SECONDARY_BOWL_SIDE',(centre-uw/2+.012,v,1.172),(centre+uw/2-.012,v+.012,1.304),white,'basin',room,.003))
  built=join('SECONDARY_BASIN_TEMP',ps,'basin',room);existing=bpy.data.objects['R3_VANITY_BASIN_REVIEW'];existing.data=built.data.copy();existing.matrix_world=built.matrix_world.copy()
  new[:]=[(a,b,z) for a,b,z in new if a!=built];roomobjects[room]=[n for n in roomobjects[room] if n!=built.name];bpy.data.objects.remove(built,do_unlink=True)
  localbox(c,'secondary_TAP_STEM',(centre-.018,.065,1.30),(centre+.018,.10,1.47),rim,'tap',room,.01)
  localbox(c,'secondary_TAP_SPOUT',(centre-.018,.085,1.45),(centre+.018,vcentre-.045,1.48),rim,'tap',room,.008)
 if room=='secondary':
  poly=[(c['mirror_center']+.325*math.cos(k*2*math.pi/96),1.91+.325*math.sin(k*2*math.pi/96)) for k in range(96)]
  inner=[(c['mirror_center']+.313*math.cos(k*2*math.pi/96),1.91+.313*math.sin(k*2*math.pi/96)) for k in range(96)]
 else:
  poly=roundedrect(c['mirror_center'],1.91,c['mirror_width'],.70,.04)
  inner=roundedrect(c['mirror_center'],1.91,c['mirror_width']-.024,.676,.028)
 shape(c,room.upper()+'_MIRROR_FRAME',poly,.004,.026,rim,'mirror_frame',room)
 shape(c,room.upper()+'_MIRROR',inner,.026,.029,mirror,'mirror',room)
 upper(c,room)
 # Thin topbar fixture follows reference restrainedillumination; noactuallightingcertification.
 if room!='secondary':localbox(c,room+'_MIRROR_LIGHT',(c['mirror_center']-.30,.022,2.31),(c['mirror_center']+.30,.05,2.326),white,'light_fixture',room,.004)
 print('SEQUENCE_'+str(sequence)+'_'+room.upper()+'_BUILT')
bpy.context.view_layer.update()
# Geometricchecks: boundingdata useactualvertices,unmodifiedobjectfingerprints remain equal.
for n,s in before.items():
 now=state(bpy.data.objects[n])
 if n in retired:assert all(now[i]==s[i] for i in range(len(s)) if i!=3),n
 elif n not in edited:assert now==s,n
cabfoot=min((bpy.data.objects['B11_Rectangle012_CATALOG_00_00'].matrix_world@v.co).x for v in bpy.data.objects['B11_Rectangle012_CATALOG_00_00'].data.vertices)
tail=cabfoot-max((top.matrix_world@v.co).x for v in top.data.vertices);assert tail>.71
audit=json.loads((R/'VANITY_BOUNDED_AUDIT.json').read_text());arch=set(sum(audit['wall_groups'].values(),[]))
arch.update(r['name'] for r in audit['rows'] if r['name'].startswith(('V4_D','R3_SLIDING')))
def tree(o):return BVHTree.FromPolygons([o.matrix_world@v.co for v in o.data.vertices],[list(f.vertices) for f in o.data.polygons],epsilon=1e-6)
hits=[]
for o,typ,room in new:
 for n in arch:
  q=bpy.data.objects.get(n)
  if q and q.type=='MESH' and tree(o).overlap(tree(q)):hits.append([o.name,n])
assert not hits,hits
tris=sum(sum(len(p.vertices)-2 for p in o.data.polygons) for o,t,r in new);assert tris<60000,tris
reg={k:v for k,v in REG.items() if k!='bindings'};reg.update(source_resource_id='c_type_console_bath_mirrors',source_revision=REV,registry_revision=REV,source_locator=str(OUT),source_authority='frozen')
reg['bindings']=[b for b in REG['bindings'] if b['native_id'] not in retired]
rooms={'couple':'candidate_R-BED-S','master':'candidate_R-BATH-M','secondary':'candidate_R-CLOAK','guest':'candidate_R-BATH-P'}
for o,typ,room in new:
 reg['bindings'].append({'entity_id':o['global_id'],'adapter':'blender','native_id':o.name,'semantic_type':typ,'room_id':rooms[room],'authority_level':'HUMAN_DESIGN_GUIDE'})
bpy.ops.wm.save_as_mainfile(filepath=str(OUT));reg['source_sha256']=sha(OUT);(R/'spatial-canvas.bindings.full.json').write_text(json.dumps(reg,ensure_ascii=False,indent=2)+'\n')
report={'status':'HUMAN_REVIEW','revision':REV,'source':str(OUT),'source_sha256':reg['source_sha256'],'parent_source':str(SRC),'parent_sha256':TRUTHS[str(SRC)],
 'retired_native_ids':retired,'edited_native_ids':edited,'frozen_hashes':TRUTHS,'rooms':roomobjects,
 'console_size_m':[2,.4,.4],'console_bedtail_clear_m':tail,'bath_configs':configs,'native_architecture_collision_pairs':hits,
 'new_triangles':tris,'authority_note':'Derivedgeometry/style,noarchitectural/plumbingmoves;mirrorproxycolor notreflectionrender',
 'unrelated_fingerprints_equal':True,'textures':False,'cycles':False}
(R/'CONSOLE_BATH_MIRRORS_REVIEW.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n');assert all(sha(p)==h for p,h in TRUTHS.items())
print('CONSOLE_BATH_BUILD_PASS',len(reg['bindings']),tris,'bedtail',tail)
