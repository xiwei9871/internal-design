"""Owner-selected detailed PRESENTATION derivative. No source writeback."""
import bpy, json, math, hashlib, struct, random
from pathlib import Path
from mathutils import Vector
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'design/living_dining_detail_v1'; OUT.mkdir(exist_ok=True)
BASE=ROOT/'design/sunroom_stepped_storage_v1/SUNROOM_STEPPED_STORAGE_V1.blend'
BASE_SHA='cde068f138c74abdc158012377579882399a48866fdc0acc261d23ff5f98cc68'
PRES=ROOT/'renders/whole_house_final_study_v1/production_batch_v1/WHOLE_HOUSE_PRODUCTION_V1.blend'
assert hashlib.sha256(BASE.read_bytes()).hexdigest()==BASE_SHA
bpy.ops.wm.open_mainfile(filepath=str(BASE)); scene=bpy.context.scene
random.seed(109); scene.unit_settings.system='METRIC'
registry=json.loads((BASE.parent/'spatial-canvas.bindings.full.json').read_text())
allowed={b['native_id'] for b in registry['bindings']}
def fingerprint(o):
 h=hashlib.sha256()
 for v in o.data.vertices:h.update(struct.pack('<fff',*v.co))
 for p in o.data.polygons:h.update(struct.pack('<'+'I'*len(p.vertices),*p.vertices))
 return h.hexdigest(),tuple(v for row in o.matrix_world for v in row)
before={n:fingerprint(bpy.data.objects[n]) for n in allowed}
with bpy.data.libraries.load(str(PRES),link=False) as (a,b):
 b.materials=[n for n in a.materials if n.startswith('RENDER_')]
 b.worlds=[n for n in a.worlds if n=='RENDER_DAYLIGHT_WORLD']
 b.objects=[n for n in a.objects if n.startswith(('CAM_living_','CAM_dining_','LIGHT_','DAYLIGHT_','PRESENTATION_'))]
rendercol=bpy.data.collections.new('LD_CONTEXT_PRESENTATION'); scene.collection.children.link(rendercol)
for o in b.objects:
 if o and not o.users_collection:rendercol.objects.link(o)
scene.world=b.worlds[0]
def matfind(n):return bpy.data.materials.get('RENDER_'+n)
wood=matfind('WHITE_ASH'); fabric=matfind('IVORY_LINEN'); wall=matfind('WARM_OFF_WHITE')
metal=matfind('BRUSHED_NICKEL'); floor=matfind('PALE_WOOD_FLOOR')
def mat(n,c,rough=.65,metallic=0):
 m=bpy.data.materials.new('LD_'+n);m.use_nodes=True;m.diffuse_color=(*c,1)
 p=m.node_tree.nodes.get('Principled BSDF');p.inputs['Base Color'].default_value=(*c,1);p.inputs['Roughness'].default_value=rough;p.inputs['Metallic'].default_value=metallic;return m
wood=wood.copy();wood.name='LD_PALE_ASH_SATIN';wood.diffuse_color=(.63,.55,.43,1)
p=wood.node_tree.nodes.get('Principled BSDF');p.inputs['Coat Weight'].default_value=.08;p.inputs['Coat Roughness'].default_value=.4
for n in wood.node_tree.nodes:
 if n.type=='MIX_RGB':n.inputs[0].default_value=.72;n.inputs[2].default_value=(.65,.57,.45,1)
fabric=fabric.copy();fabric.name='LD_OATMEAL_WOVEN';fabric.diffuse_color=(.72,.67,.57,1)
fabric.node_tree.nodes.get('Principled BSDF').inputs['Sheen Weight'].default_value=.18
for n in fabric.node_tree.nodes:
 if n.type=='MIX_RGB':n.inputs[0].default_value=.82;n.inputs[2].default_value=(.70,.65,.55,1)
def explicit_scanned(material,folder,color,repeat):
 ns=material.node_tree.nodes;ls=material.node_tree.links;ns.clear();out=ns.new('ShaderNodeOutputMaterial');p=ns.new('ShaderNodeBsdfPrincipled');ls.new(p.outputs[0],out.inputs[0]);p.inputs['Roughness'].default_value=.65
 coord=ns.new('ShaderNodeUVMap');coord.uv_map='RenderMeters';scale=ns.new('ShaderNodeVectorMath');scale.operation='MULTIPLY';scale.inputs[1].default_value=(repeat,repeat,repeat);ls.new(coord.outputs[0],scale.inputs[0])
 manifest=json.loads((ROOT/'renders/whole_house_final_study_v1/assets'/folder/'asset-manifest.json').read_text())
 for f in manifest['files']:
  t=ns.new('ShaderNodeTexImage');t.image=bpy.data.images.load(f['path'],check_existing=True);t.image.colorspace_settings.name='sRGB' if f['map']=='diffuse' else 'Non-Color';ls.new(scale.outputs[0],t.inputs[0])
  if f['map']=='diffuse':
   gray=ns.new('ShaderNodeRGBToBW');ls.new(t.outputs[0],gray.inputs[0]);ramp=ns.new('ShaderNodeValToRGB');ramp.color_ramp.elements[0].position=.12;ramp.color_ramp.elements[1].position=.9
   ramp.color_ramp.elements[0].position=.20 if folder=='ash' else .12;ramp.color_ramp.elements[1].position=.65 if folder=='ash' else .9
   ramp.color_ramp.elements[0].color=(*(v*.48 if folder=='ash' else v*.65 for v in color),1);ramp.color_ramp.elements[1].color=(*color,1);ls.new(gray.outputs[0],ramp.inputs[0]);ls.new(ramp.outputs[0],p.inputs['Base Color'])
  elif f['map']=='normal':
   normal=ns.new('ShaderNodeNormalMap');normal.uv_map='RenderMeters';normal.inputs['Strength'].default_value=.22 if folder=='ash' else .4;ls.new(t.outputs[0],normal.inputs['Color']);ls.new(normal.outputs[0],p.inputs['Normal'])
  else:
   ramp=ns.new('ShaderNodeMapRange');ramp.inputs['To Min'].default_value=.42 if folder=='ash' else .78;ramp.inputs['To Max'].default_value=.66 if folder=='ash' else 1;ls.new(t.outputs[0],ramp.inputs['Value']);ls.new(ramp.outputs[0],p.inputs['Roughness'])
 p.inputs['Sheen Weight'].default_value=.25 if folder=='linen' else 0
explicit_scanned(wood,'ash',(.72,.64,.50),1.2)
explicit_scanned(fabric,'linen',(.8,.74,.63),3.5)
explicit_scanned(floor,'ash',(.78,.70,.56),1.2)
ns=floor.node_tree.nodes;ls=floor.node_tree.links;p=next(n for n in ns if n.type=='BSDF_PRINCIPLED');coord=ns.new('ShaderNodeUVMap');coord.uv_map='RenderMeters';brick=ns.new('ShaderNodeTexBrick');ls.new(coord.outputs[0],brick.inputs['Vector']);brick.inputs['Scale'].default_value=1;brick.inputs['Brick Width'].default_value=1.2;brick.inputs['Row Height'].default_value=.18;brick.inputs['Mortar Size'].default_value=.0007;brick.inputs['Mortar Smooth'].default_value=.0003
bump=ns.new('ShaderNodeBump');bump.inputs['Distance'].default_value=.001;bump.inputs['Strength'].default_value=.18
if p.inputs['Normal'].is_linked:ls.new(p.inputs['Normal'].links[0].from_socket,bump.inputs['Normal'])
ls.new(brick.outputs['Fac'],bump.inputs['Height']);ls.new(bump.outputs[0],p.inputs['Normal'])
for m,scale,distance,strength in [(fabric,650,.00035,.32),(wood,8,.00018,.14)]:
 ns=m.node_tree.nodes;ls=m.node_tree.links;p=ns.get('Principled BSDF') or next(n for n in ns if n.type=='BSDF_PRINCIPLED');c=ns.new('ShaderNodeTexCoord');noise=ns.new('ShaderNodeTexNoise');noise.inputs['Scale'].default_value=scale;noise.inputs['Detail'].default_value=2;ls.new(c.outputs['Object'],noise.inputs['Vector']);bump=ns.new('ShaderNodeBump');bump.inputs['Distance'].default_value=distance;bump.inputs['Strength'].default_value=strength
 if p.inputs['Normal'].is_linked:ls.new(p.inputs['Normal'].links[0].from_socket,bump.inputs['Normal'])
 ls.new(noise.outputs['Fac'],bump.inputs['Height']);ls.new(bump.outputs[0],p.inputs['Normal'])
seam=mat('SEAM_LINEN',(.49,.44,.36),.95);shade=mat('CLEANABLE_IVORY_ENAMEL',(.78,.75,.66),.38)
def uvmeters(o):
 me=o.data;uv=me.uv_layers.get('RenderMeters') or me.uv_layers.new(name='RenderMeters');me.uv_layers.active=uv;uv.active_render=True
 for p in me.polygons:
  ax=max(range(3),key=lambda i:abs(p.normal[i]));axes=[i for i in range(3) if i!=ax]
  for li in p.loop_indices:
   v=o.matrix_world@me.vertices[me.loops[li].vertex_index].co;uv.data[li].uv=(v[axes[0]],v[axes[1]])
def choose(o,old):
 t=(o.name+' '+old).upper()
 if 'MIRROR' in t and 'FRAME' not in t:return matfind('MIRROR')
 if 'GLASS' in t or o.name.startswith('G_wall_g'):return matfind('CLEAR_GLASS')
 if o.name.startswith(('VIEW_WALL','CEILING','G_wall')) or 'PIER_SITE' in t:return wall
 if 'FLOOR' in t:return floor
 if any(x in t for x in ['METAL','HANDLE','NICKEL','FRAME','TAP']):return metal
 if any(x in t for x in ['FABRIC','CUSHION','LINEN','PADDED','BED_RUNNER']):return fabric
 if any(x in t for x in ['STONE','COUNTER','WORKTOP','SILL_PLATFORM']):return matfind('QUIET_CREAM_STONE')
 if any(x in t for x in ['BASIN','CERAMIC','WC_','TOILET']):return matfind('CERAMIC')
 if any(x in t for x in ['APPLIANCE','CONTROL','HOB','BURNER','FRIDGE']):return matfind('DARK_APPLIANCE')
 return wood
for o in list(scene.objects):
 if o.type=='LIGHT' and not o.name.startswith(('LIGHT_','DAYLIGHT_')):o.hide_render=True
 if o.type!='MESH' or o.name.startswith('PRESENTATION_'):continue
 visible=o.name in allowed or o.name.startswith('CEILING_');o.hide_render=not visible;o.hide_viewport=not visible;o.hide_set(not visible)
 if not visible:continue
 o.data=o.data.copy();old=[m.name if m else '' for m in o.data.materials];mats=[choose(o,m) for m in old] or [wood]
 o.data.materials.clear()
 for m in mats:o.data.materials.append(m)
 for f in o.data.polygons:f.material_index=min(f.material_index,len(mats)-1)
 uvmeters(o)
for n in ['VIEW_WALL_W_wall_md_0036','NORTH_WINDOW_FITNESS_RESERVE_NOT_EQUIPMENT','PLATE_AC_ZONE','PLATE_GAP20_TO_VERIFY','STUDY_V1_CONTEXT_FLOOR','READING_3205A_PADDED_BENCH']:
 if n in bpy.data.objects:bpy.data.objects[n].hide_render=True
col=bpy.data.collections.new('LD_SELECTED_DETAILED_FURNITURE');scene.collection.children.link(col)
groups={}
def assembly(n,source=None):
 o=bpy.data.objects.new('LD_'+n,None);col.objects.link(o);o['source_object']=source or 'OWNER_SELECTED_ADDITION';groups[n]=o;return o
group=None
def finish(o,n,m):
 o.name='LD_'+n
 for c in list(o.users_collection):c.objects.unlink(o)
 col.objects.link(o);o.data.materials.append(m)
 if group:o.parent=group
 for p in o.data.polygons:p.use_smooth=True
 uvmeters(o);return o
def box(n,loc,size,m=wood,r=.004):
 bpy.ops.mesh.primitive_cube_add(size=1,location=loc);o=bpy.context.object;o.dimensions=size
 bpy.ops.object.transform_apply(location=False,rotation=False,scale=True);finish(o,n,m)
 if r:
  b=o.modifiers.new('Real edge radius','BEVEL');b.width=min(r,min(size)*.45);b.segments=5
  b=o.modifiers.new('Surface normals','WEIGHTED_NORMAL');b.keep_sharp=True
 return o
def rod(n,a,b,r=.022,m=wood,r2=None):
 a,b=Vector(a),Vector(b);v=b-a
 bpy.ops.mesh.primitive_cone_add(vertices=40,radius1=r,radius2=r2 or r,depth=v.length,location=(a+b)/2);o=bpy.context.object;o.rotation_euler=v.to_track_quat('Z','Y').to_euler();finish(o,n,m)
 be=o.modifiers.new('Rounded ends','BEVEL');be.width=.002;be.segments=3;return o
def line(n,pts,r=.001,m=seam,closed=False):
 c=bpy.data.curves.new(n,'CURVE');c.dimensions='3D';c.resolution_u=2;c.bevel_depth=r;c.bevel_resolution=3
 s=c.splines.new('POLY');s.points.add(len(pts)-1)
 for p,v in zip(s.points,pts):p.co=(*v,1)
 s.use_cyclic_u=closed;o=bpy.data.objects.new('LD_'+n,c);col.objects.link(o);c.materials.append(m)
 if group:o.parent=group
 return o
def cushion(n,lo,hi,material=fabric):
 lo,hi=Vector(lo),Vector(hi);size=hi-lo;center=(lo+hi)/2
 o=box(n,center,size,material,min(.06,min(size)*.31))
 bpy.context.view_layer.objects.active=o
 for mod in list(o.modifiers):bpy.ops.object.modifier_apply(modifier=mod.name)
 sub=o.modifiers.new('Upholstery surface','SUBSURF');sub.levels=2
 bpy.ops.object.modifier_apply(modifier=sub.name)
 # Localized tuck/compression near the seams, without repeated broad waves.
 for v in o.data.vertices:
  q=v.co;nx=q.x/(size.x*.5);ny=q.y/(size.y*.5);nz=q.z/(size.z*.5)
  if nz>.45:
   q.z+=.006*math.exp(-((nx/.70)**4+(ny/.7)**4))
   q.z-=.0025*math.exp(-((nx-.75)/.2)**2-((ny+.35)/.55)**2)
   q.z-=.002*math.exp(-((nx+.5)/.35)**2-((ny-.7)/.2)**2)
 # Exact existing envelope remains the constraint after smoothing.
 for i in range(3):
  mn=min(v.co[i] for v in o.data.vertices);mx=max(v.co[i] for v in o.data.vertices)
  for v in o.data.vertices:v.co[i]=(v.co[i]-mn)/(mx-mn)*size[i]-size[i]/2
 uvmeters(o)
 # Tailored seam follows rounded rectangle on the upper cushion boundary.
 rad=min(.045,size.x*.15,size.y*.15);pts=[]
 for cx,cy,start in [(size.x/2-rad,size.y/2-rad,0),(-size.x/2+rad,size.y/2-rad,90),(-size.x/2+rad,-size.y/2+rad,180),(size.x/2-rad,-size.y/2+rad,270)]:
  for i in range(13):
   t=math.radians(start+i*90/12);pts.append((center.x+cx+rad*math.cos(t),center.y+cy+rad*math.sin(t),center.z+size.z*.25))
 line(n+'_piping',pts,.00085,closed=True);return o
def connected_components(o):
 me=o.data;adj=[[] for _ in me.vertices]
 for edge in me.edges:a,b=edge.vertices;adj[a].append(b);adj[b].append(a)
 seen=set();parts=[]
 for start in range(len(adj)):
  if start in seen:continue
  queue=[start];seen.add(start);ids=[]
  while queue:
   a=queue.pop();ids.append(a)
   for b in adj[a]:
    if b not in seen:seen.add(b);queue.append(b)
  points=[o.matrix_world@me.vertices[i].co for i in ids];parts.append({'bounds':[[min(v[i] for v in points) for i in range(3)],[max(v[i] for v in points) for i in range(3)]]})
 return {'name':o.name,'parts':parts}
components=[connected_components(bpy.data.objects['B11_Rectangle046_CATALOG_00_00'])]
group=assembly('L_SOFA','B11_Rectangle046_CATALOG_00_00')
sofa=next(o for o in components if 'Rectangle046' in o['name'])
for i,p in enumerate(sofa['parts']):
 lo,hi=map(Vector,p['bounds']);size=hi-lo
 if i in [3,4,5,9,10,11]:cushion('Sofa_upholstery_%02d'%i,lo,hi)
 elif i in [0,1,2]:
  box('Sofa_ash_platform_%02d'%i,((lo.x+hi.x)/2,(lo.y+hi.y)/2,.261),(size.x,size.y,.048),r=.006)
  for y in [lo.y+.11,hi.y-.11]:box('Sofa_support_rail_%02d'%i,((lo.x+hi.x)/2,y,.205),(size.x-.14,.042,.1),r=.003)
 elif i>=12:rod('Sofa_foot_%02d'%i,((lo.x+hi.x)/2,(lo.y+hi.y)/2,0),((lo.x+hi.x)/2,(lo.y+hi.y)/2,.24),.031,r2=.027)
 elif i in [6,7]:
  box('Sofa_arm_top_%02d'%i,((lo.x+hi.x)/2,(lo.y+hi.y)/2,.568),(size.x,size.y,.024),r=.008)
  for x in [lo.x+.055,hi.x-.055]:rod('Sofa_arm_support_%d'%i,(x,(lo.y+hi.y)/2,.27),(x,(lo.y+hi.y)/2,.558),.02)
 elif i==8:
  box('Sofa_back_rail',(3.48,9.6,.565),(.055,2.94,.06),r=.005)
  for y in [8.18,9.0,9.4,10,10.5,11.02]:rod('Sofa_back_support',(3.48,y,.25),(3.48,y,.59),.019)
group=assembly('WINDOW_CHAISE','B11_Rectangle048_CATALOG_00_00')
chaise=bpy.data.objects['B11_Rectangle048_CATALOG_00_00']
# Preserve the catalog-derived recline rather than replacing its profile with a box.
def inclined_panel(n,a,b,width,thick,m):
 a,b=Vector(a),Vector(b);v=b-a;o=box(n,(a+b)/2,(v.length,width,thick),m,min(.013,thick*.3));o.rotation_euler.y=-math.atan2(v.z,v.x);return o
inclined_panel('Chaise_seat_ash_deck',(5.065,11.505,.341),(6.32,11.505,.341),.858,.04,wood)
inclined_panel('Chaise_reclined_back_deck',(4.74,11.505,.750),(5.08,11.505,.345),.858,.035,wood)
cushion('Chaise_seat_pad',(5.085,11.11,.362),(6.32,11.90,.429))
# Model back upholstery in its local supported orientation before tilting.
o=cushion('Chaise_back_pad',(-.247,-.395,-.038),(.247,.395,.038));
o.location=(4.952,11.505,.563);o.rotation_euler.y=math.radians(50)
pipe=bpy.data.objects['LD_Chaise_back_pad_piping'];pipe.location=o.location;pipe.rotation_euler=o.rotation_euler
for y in [11.075,11.935]:
 rod('Chaise_ash_arm',(5.085,y,.57),(6.235,y,.57),.018)
 for x in [5.125,6.205]:rod('Chaise_arm_upright',(x,y,.343),(x,y,.566),.015)
 rod('Chaise_side_reclined_rail',(4.745,y,.773),(5.085,y,.343),.018)
for y in [11.15,11.86]:
 rod('Chaise_splayed_back_leg',(4.99,y,.011),(5.18,y,.341),.022,r2=.026)
 rod('Chaise_splayed_front_leg',(6.335,y,.011),(6.165,y,.341),.022,r2=.026)
for x in [5.18,6.165]:rod('Chaise_cross_support',(x,11.11,.32),(x,11.90,.32),.025)
group=assembly('COFFEE_TABLE','B11_Rectangle049_CATALOG_00_00')
cx,cy=5.3,9.99
box('Coffee_tabletop',(cx,cy,.384),(.55,1,.032),r=.009)
box('Coffee_lower_shelf',(cx,cy,.11),(.47,.92,.024),r=.004)
for x in [cx-.235,cx+.235]:
 for y in [cy-.46,cy+.46]:box('Coffee_leg',(x,y,.184),(.032,.032,.368),r=.003)
for y in [cy-.46,cy+.46]:box('Coffee_apron',(cx,y,.34),(.438,.025,.055),r=.003)
group=assembly('EAST_LOW_CABINET','B11_Rectangle004_CATALOG_00_00')
x0,x1,y0,y1=7.398,7.696875,8.634937,11.523844
box('Console_top',((x0+x1)/2,(y0+y1)/2,.464),(.298875,y1-y0,.032),r=.006)
box('Console_lower_shelf',((x0+x1)/2,(y0+y1)/2,.103),(.275,y1-y0-.06,.026),r=.003)
box('Console_back',(x1-.01,(y0+y1)/2,.267),(.018,y1-y0-.055,.334),r=.002)
for y in [y0+.017,y0+(y1-y0)/3,y0+2*(y1-y0)/3,y1-.017]:
 box('Console_support',((x0+x1)/2,y,.254),(.27,.026,.388),r=.003)
for y in [y0+.1,y1-.1]:
 for x in [x0+.04,x1-.04]:rod('Console_foot',(x,y,0),(x,y,.105),.022)
def capsule(n,c,length,width,thick,m):
 swap=length<width
 if swap:length,width=width,length
 r=width/2;half=(length-width)/2;verts=[]
 for z in [-thick/2,thick/2]:
  for side,start in [(half,-90),(-half,90)]:
   for i in range(65):
    t=math.radians(start+i*180/64);xx=side+r*math.cos(t);yy=r*math.sin(t);verts.append((c[0]+(yy if swap else xx),c[1]+(xx if swap else yy),c[2]+z))
 N=len(verts)//2;faces=[tuple(reversed(range(N))),tuple(range(N,2*N))]+[(i,(i+1)%N,(i+1)%N+N,i+N) for i in range(N)]
 me=bpy.data.meshes.new(n);me.from_pydata(verts,[],faces);me.update();o=bpy.data.objects.new(n,me);col.objects.link(o);o.data.materials.append(m);o.parent=group;uvmeters(o)
 be=o.modifiers.new('Eased table edge','BEVEL');be.width=.0035;be.segments=4;be=o.modifiers.new('Table normals','WEIGHTED_NORMAL');return o
group=assembly('RACETRACK_DINING_TABLE','B11_Rectangle050_CATALOG_00_00')
tx,ty=3.827625,3.464406
capsule('LD_Dining_racetrack_top',(tx,ty,.731),1.6,.8,.038,wood)
# End-centered narrow supports clear the four long-side seating lanes.
for x in [tx-.48,tx+.48]:
 capsule('LD_Dining_oval_pedestal',(x,ty,.352),.20,.16,.704,wood)
 capsule('LD_Dining_support_foot',(x,ty,.014),.23,.38,.028,wood)
box('Dining_under_top_spine',(tx,ty,.686),(1.10,.065,.052),r=.008)
for i,(x,y,sign) in enumerate([(3.427625,3.744406,1),(4.227625,3.744406,1),(3.427625,3.184406,-1),(4.227625,3.184406,-1)]):
 group=assembly('DINING_CHAIR_%d'%i,'B11_Circle%03d_CATALOG_00_00'%(10+i))
 # Real catalog baseline: narrow ash chair, upholstered seat and curved wood back.
 for sx in [-1,1]:
  rod('Chair_front_leg',(x+sx*.174,y-sign*.176,0),(x+sx*.155,y-sign*.146,.46),.02,r2=.023)
  rod('Chair_back_post',(x+sx*.174,y+sign*.176,0),(x+sx*.164,y+sign*.169,.822),.019,r2=.02)
  box('Chair_side_rail',(x+sx*.153,y,.43),(.025,.325,.045),r=.004)
 box('Chair_front_rail',(x,y-sign*.146,.43),(.322,.025,.045),r=.004)
 cushion('Chair_seat',(x-.17,y-.156,.447),(x+.17,y+.156,.49))
 # Curved back panel, complete edge thickness, slight recline.
 verts=[]
 for z in [.65,.846]:
  for depth in [-.008,.008]:
   for j in range(33):
    xx=-.174+.348*j/32; yy=y+sign*(.159+.019*(1-(xx/.174)**2)+.018*(z-.65)/.196+depth);verts.append((x+xx,yy,z))
 faces=[]
 for j in range(32):faces.extend([(j,j+1,66+j+1,66+j),(33+j,99+j,99+j+1,33+j+1),(j,33+j,33+j+1,j+1),(66+j,66+j+1,99+j+1,99+j)])
 faces.extend([(0,66,99,33),(32,65,131,98)])
 me=bpy.data.meshes.new('Chair_curved_back');me.from_pydata(verts,[],faces);me.update();o=bpy.data.objects.new('LD_Chair_curved_back',me);col.objects.link(o);o.parent=group;me.materials.append(wood);uvmeters(o)
 b=o.modifiers.new('Soft back perimeter','BEVEL');b.width=.003;b.segments=4;b=o.modifiers.new('Back normals','WEIGHTED_NORMAL')
group=assembly('SELECTED_RUG')
def patternmat(n,file,rough=1):
 m=mat(n,(.7,.65,.55),rough);nodes=m.node_tree.nodes;links=m.node_tree.links;t=nodes.new('ShaderNodeTexImage');t.image=bpy.data.images.load(str(OUT/'textures'/file));links.new(t.outputs['Color'],nodes.get('Principled BSDF').inputs['Base Color']);return m
rugmat=patternmat('RUG_WOVEN_ORIGINAL','rug_original.png');p=rugmat.node_tree.nodes.get('Principled BSDF');p.inputs['Sheen Weight'].default_value=.3
noise=rugmat.node_tree.nodes.new('ShaderNodeTexNoise');noise.inputs['Scale'].default_value=700;bump=rugmat.node_tree.nodes.new('ShaderNodeBump');bump.inputs['Distance'].default_value=.0006;bump.inputs['Strength'].default_value=.22;rugmat.node_tree.links.new(noise.outputs['Fac'],bump.inputs['Height']);rugmat.node_tree.links.new(bump.outputs[0],p.inputs['Normal'])
o=box('Selected_geometric_rug',(5.63,9.93,.009),(2.85,2.65,.014),rugmat,r=.008)
uv=o.data.uv_layers.active
for poly in o.data.polygons:
 for li in poly.loop_indices:
  v=o.data.vertices[o.data.loops[li].vertex_index].co;uv.data[li].uv=(v.x/2.85+.5,v.y/2.65+.5)
group=assembly('EAST_WALL_SELECTED_ART')
artmat=patternmat('ORIGINAL_ABSTRACT_PAINTING','art_original.png',.86)
o=box('Art_canvas',(7.705,10.04,1.72),(.028,1.5,1.2),artmat,r=.002)
for poly in o.data.polygons:
 for li in poly.loop_indices:
  v=o.data.vertices[o.data.loops[li].vertex_index].co;o.data.uv_layers.active.data[li].uv=(v.y/1.5+.5,v.z/1.2+.5)
for y in [9.275,10.805]:box('Art_ash_vertical',(7.686,y,1.72),(.038,.022,1.244),r=.002)
for z in [1.109,2.331]:box('Art_ash_horizontal',(7.686,10.04,z),(.038,1.552,.022),r=.002)
group=assembly('SELECTED_LINEN_CURTAINS')
curtain=fabric.copy();curtain.name='LD_LIGHT_FLAX_CURTAIN';curtain.node_tree.nodes.get('Principled BSDF').inputs['Sheen Weight'].default_value=.35
rod('Curtain_rail',(3.17,12.94,2.70),(7.50,12.94,2.70),.012,metal)
for start,width in [(3.18,.61),(6.95,.54)]:
 verts=[];faces=[];nx,nz=96,96
 for j in range(nz+1):
  t=j/nz;z=2.64-2.60*t
  for i in range(nx+1):
   u=i/nx;fold=math.cos(2*math.pi*6*u);amp=.042+.023*t
   x=start+u*width+(u-.5)*.016*t*t;y=12.90+amp*fold+.008*t*math.sin(7*u+3*t)
   # Header pinching and gravity-driven fan-out; raised hem avoids floor pooling.
   z1=z+.005*t**8*math.cos(2*math.pi*6*u)+.003*t*t*math.sin(11*u)
   verts.append((x,y,z1))
 for j in range(nz):
  for i in range(nx):a=j*(nx+1)+i;faces.append((a,a+1,a+nx+2,a+nx+1))
 me=bpy.data.meshes.new('Pleated_linen');me.from_pydata(verts,[],faces);me.update();o=bpy.data.objects.new('LD_Curtain_supported_pleats',me);col.objects.link(o);o.parent=group;me.materials.append(curtain);uvmeters(o)
 for p in me.polygons:p.use_smooth=True
 sol=o.modifiers.new('Woven cloth thickness','SOLIDIFY');sol.thickness=.0012
 line('Curtain_stitched_hem',verts[-(nx+1):],.0012,fabric)
 for i in range(7):rod('Curtain_header_hook',(start+width*i/6,12.94,2.64),(start+width*i/6,12.94,2.70),.0025,metal)
group=assembly('CLEANABLE_DOME_PENDANT')
# Ellipsoidal open dome with modeled double wall; not a capped solid sphere.
verts=[];rings=40;segments=128
for layer in [0,1]:
 for j in range(rings+1):
  t=.035+(math.pi/2-.035)*j/rings;r=(.355-layer*.004)*math.sin(t);z=1.89+(.28-layer*.004)*math.cos(t)
  for i in range(segments):a=2*math.pi*i/segments;verts.append((tx+r*math.cos(a),ty+r*.91*math.sin(a),z))
faces=[];N=(rings+1)*segments
for layer in [0,1]:
 for j in range(rings):
  for i in range(segments):a=layer*N+j*segments+i;b=layer*N+j*segments+(i+1)%segments;f=(a,b,b+segments,a+segments);faces.append(f if layer==0 else tuple(reversed(f)))
for j in [0,rings]:
 for i in range(segments):a=j*segments+i;b=j*segments+(i+1)%segments;faces.append((a,a+N,b+N,b))
me=bpy.data.meshes.new('Closed_thickness_open_dome');me.from_pydata(verts,[],faces);me.update();o=bpy.data.objects.new('LD_Cleanable_dome_shell',me);col.objects.link(o);o.parent=group;me.materials.append(shade)
for p in me.polygons:p.use_smooth=True
uvmeters(o);rod('Pendant_rod',(tx,ty,2.16),(tx,ty,2.76),.0035,metal);rod('Pendant_canopy',(tx,ty,2.748),(tx,ty,2.775),.058,shade)
bulb=mat('OPAL_DIFFUSER',(.92,.88,.76),.3);p=bulb.node_tree.nodes.get('Principled BSDF');p.inputs['Emission Color'].default_value=(1,.82,.62,1);p.inputs['Emission Strength'].default_value=2
bpy.ops.mesh.primitive_uv_sphere_add(segments=48,ring_count=24,radius=.048,location=(tx,ty,1.968));finish(bpy.context.object,'Pendant_opal_bulb',bulb)
d=bpy.data.lights.new('LD_Pendant_3000K','AREA');d.energy=38;d.shape='DISK';d.size=.18;d.color=(1,.84,.67);o=bpy.data.objects.new(d.name,d);col.objects.link(o);o.location=(tx,ty,1.89);o.parent=group
replace=['B11_Rectangle046_CATALOG_00_00','B11_Rectangle048_CATALOG_00_00','B11_Rectangle049_CATALOG_00_00','B11_Rectangle004_CATALOG_00_00','B11_Rectangle050_CATALOG_00_00']+['B11_Circle%03d_CATALOG_00_00'%i for i in range(10,14)]
for n in replace:bpy.data.objects[n].hide_render=True;bpy.data.objects[n].hide_viewport=True;bpy.data.objects[n].hide_set(True)
# Inherited lights neutralized consistently; no orange global wash.
for o in scene.objects:
 if o.type=='LIGHT' and o.name.startswith('LIGHT_'):o.data.color=(1,.95,.88);o.data.energy*=.18
 if o.type=='LIGHT' and o.name.startswith('DAYLIGHT_'):o.data.color=(1,.98,.94);o.data.energy*=.7
worldnodes=scene.world.node_tree.nodes
worldnodes.get('Background').inputs['Strength'].default_value=.22
links=scene.world.node_tree.links
env=next(n for n in worldnodes if n.type=='TEX_ENVIRONMENT')
lp=next(n for n in worldnodes if n.type=='LIGHT_PATH')
outnode=next(n for n in worldnodes if n.type=='OUTPUT_WORLD')
old=outnode.inputs[0].links[0].from_socket
sky=worldnodes.new('ShaderNodeBackground');sky.name='LD Neutral exterior presentation';sky.inputs[0].default_value=(.70,.79,.86,1);sky.inputs[1].default_value=.65
ray=worldnodes.new('ShaderNodeMath');ray.operation='MAXIMUM';links.new(lp.outputs['Is Camera Ray'],ray.inputs[0]);links.new(lp.outputs['Is Transmission Ray'],ray.inputs[1])
mix=worldnodes.new('ShaderNodeMixShader');links.new(ray.outputs[0],mix.inputs[0]);links.new(old,mix.inputs[1]);links.new(sky.outputs[0],mix.inputs[2]);links.new(mix.outputs[0],outnode.inputs[0])
d=bpy.data.lights.new('LD_Sun_through_actual_windows','SUN');d.energy=2.2;d.angle=math.radians(4);d.color=(1,.96,.87);o=bpy.data.objects.new(d.name,d);col.objects.link(o);o.rotation_euler=Vector((-.12,-1,-.52)).to_track_quat('-Z','Y').to_euler()
def camera(n,eye,target,lens):
 d=bpy.data.cameras.new(n);o=bpy.data.objects.new(n,d);col.objects.link(o);o.location=eye;o.rotation_euler=(Vector(target)-o.location).to_track_quat('-Z','Y').to_euler();d.lens=lens;d.sensor_width=36;d.clip_start=.025;return o
camera('LD_CAM_living_DETAIL',(6.83,8.76,1.28),(4.16,9.59,.5),46)
camera('LD_CAM_dining_DETAIL',(4.96,4.06,1.30),(3.82,3.47,.70),38)
cam=bpy.data.objects['CAM_dining_VIEW_01'];cam.location=(5.28,4.32,1.55);v=Vector((3.78,3.40,1.55))-cam.location;cam.rotation_euler=v.to_track_quat('-Z','Y').to_euler();cam.data.lens=17;cam.data.shift_y=-.075
cam=bpy.data.objects['LD_CAM_dining_DETAIL'];cam.location=(5.28,4.1,1.27);cam.rotation_euler=(Vector((3.85,3.45,.62))-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.lens=30
for o in scene.objects:
 if o.type=='CAMERA':o.data.dof.use_dof=False
scene.render.threads_mode='FIXED';scene.render.threads=2;scene.render.resolution_x=1920;scene.render.resolution_y=1080;scene.render.resolution_percentage=100
scene.render.image_settings.file_format='PNG';scene.view_settings.view_transform='AgX';scene.view_settings.look='AgX - Medium High Contrast';scene.view_settings.exposure=.25
scene.cycles.samples=128;scene.cycles.use_denoising=True;scene.cycles.denoiser='OPENIMAGEDENOISE';scene.cycles.denoising_use_gpu=True;scene.cycles.adaptive_threshold=.018;scene.cycles.max_bounces=10;scene.cycles.transmission_bounces=8;scene.cycles.sample_clamp_indirect=3
pref=bpy.context.preferences.addons['cycles'].preferences;pref.compute_device_type='METAL';pref.get_devices()
for d in pref.devices:d.use=d.type=='METAL'
scene.cycles.device='GPU';scene.render.engine='CYCLES';scene.camera=bpy.data.objects['CAM_living_VIEW_01']
scene['authority']='PRESENTATION_DETAILED_OWNER_SELECTION_CANDIDATE';scene['source_sha256']=BASE_SHA;scene['no_ground_truth_writeback']=True
for n,f in before.items():assert fingerprint(bpy.data.objects[n])==f,n
assert hashlib.sha256(BASE.read_bytes()).hexdigest()==BASE_SHA
bpy.ops.file.pack_all();destination=OUT/'LIVING_DINING_DETAIL_V1.blend';bpy.ops.wm.save_as_mainfile(filepath=str(destination))
audit={'status':'PASS','source_sha256':BASE_SHA,'source_file':str(BASE),'all_registered_source_meshes_and_world_transforms_unchanged':len(before),'retained_hidden_source_furniture':replace,'derivative':str(destination),'derivative_sha256':hashlib.sha256(destination.read_bytes()).hexdigest(),'dining_table_mm':[1600,800,750],'coffee_table_mm':[550,1000,400],'chair_count':4,'pendant_material':'wipeable enamel candidate; SKU unconfirmed','pattern_authority':'original code-created reference-inspired artwork and rug','no_dining_art':True,'no_creative_living_elements':True,'devices':[{'name':d.name,'type':d.type,'use':d.use} for d in pref.devices]}
(OUT/'BUILD_AUDIT.json').write_text(json.dumps(audit,ensure_ascii=False,indent=2)+'\n')
print('LD_BUILD_PASS',len(col.objects),destination)
