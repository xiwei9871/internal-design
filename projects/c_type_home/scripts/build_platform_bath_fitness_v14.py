"""Owner-authorized V14 candidate: wall art, platform rail, compact bath and real-size rower."""
import bpy,json,hashlib,struct,sys,math
from pathlib import Path
from mathutils import Vector
R=Path(__file__).resolve().parents[1];D=R/'design/platform_bath_fitness_v14';S=R/'design/fridge_finish_v13/WHOLE_HOUSE_FRIDGE_FINISH_DELIVERY_V13.blend';O=D/'WHOLE_HOUSE_PLATFORM_BATH_FITNESS_V14.blend';sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();assert sha(S)=='cfabc7215452f4c2e9ddba3b7ab7c2f063c14c460ba773b1fc340ee0745f31c7' and not O.exists();bpy.ops.wm.open_mainfile(filepath=str(S));s=bpy.context.scene
hides={o.name:(o.hide_viewport,{l.name:o.hide_get(view_layer=l) for l in s.view_layers}) for o in bpy.data.objects};cols={c.name:c.hide_viewport for c in bpy.data.collections}
for c in bpy.data.collections:c.hide_viewport=False
for o in bpy.data.objects:o.hide_viewport=False;o.hide_set(False)
bpy.context.view_layer.update()
def mh(o):
 h=hashlib.sha256()
 if o.type=='MESH':
  for v in o.data.vertices:h.update(struct.pack('<fff',*v.co))
  for f in o.data.polygons:h.update(struct.pack('<'+'I'*len(f.vertices),*f.vertices))
 return h.hexdigest()
before={o.name:{'mesh':mh(o),'matrix':[list(r) for r in o.matrix_world],'render':o.hide_render,'mats':[m.name if m else None for m in o.data.materials] if hasattr(o.data,'materials') else []} for o in bpy.data.objects}
col=bpy.data.collections.new('V14_OWNER_LOCAL_REVIEW');s.collection.children.link(col);wood=bpy.data.materials['V7_CATALOG_PALE_NATURAL_ASH'];metal=bpy.data.materials['RENDER_BRUSHED_NICKEL'];glass=bpy.data.materials['V8_COLORLESS_PRIVACY_FROSTED_GLASS'];sys.path.insert(0,str(R/'scripts'));from whole_house_finish_parts_v1 import Parts
P=Parts(col,wood,None);hidden=[];moved=[];edited=[]
def hide(o):
 o.hide_render=True;hidden.append(o.name)
# Move the entire existing framed artwork onto its actual wall, maintain print/size.
art=bpy.data.objects['HOUSE_V1_STUDY_GAP_ART'];art.location+=Vector((16.1999-.002-15.754,.14 and 0,.14));moved=[art.name]+[o.name for o in art.children_recursive]
# Continue source gripping height (900mm above450mm platform),350mm horizontal.
hide(bpy.data.objects['WAVE_HANDRAIL_UPPER_RETURN']);x=6.460157871;y=4.7701;z=1.331117
pts=[(x,y,z),(x+.33,y,z)]
for i in range(1,9):
 t=(math.pi/2)*i/8;pts.append((x+.33+.02*math.sin(t),y-.02+.02*math.cos(t),z))
pts.append((x+.35,4.7041,z));P.curve('V14_PLATFORM_RAIL_EXTENSION_350',pts,.02,wood)
# New support near extension end uses existing bracket construction proportions.
P.box('V14_RAIL_WALL_PLATE',(x+.24,4.7041,z-.067),(.07,.008,.08),metal,.002);P.rod('V14_RAIL_SUPPORT_ARM',(x+.24,4.7081,z-.067),(x+.24,y,z-.067),.007,metal);P.rod('V14_RAIL_SUPPORT_UP',(x+.24,y,z-.067),(x+.24,y,z-.02),.007,metal)
# Cabinet width1000, preserve panel thickness, basin size and real object height.
x0=9.228;oldx1=10.428;newx1=10.228
for o in list(s.objects):
 if not o.name.startswith('R3_VANITY_') or o.type!='MESH':continue
 n=o.name;o.data=o.data.copy();inv=o.matrix_world.inverted()
 if 'BASIN' in n:o.location.x-=.1;moved.append(n);continue
 if n.endswith('_R'):o.location.x-=.2;moved.append(n);continue
 if n.endswith('_L'):continue
 if '_PULL_' in n:o.location.x-=.05 if n.endswith('_0') else .15;moved.append(n);continue
 if 'FRONT_' in n:
  vs=[o.matrix_world@v.co for v in o.data.vertices];lo=min(v.x for v in vs);hi=max(v.x for v in vs);index=int(n.rsplit('_',1)[1]);newlo=x0+.002+index*.5;newhi=x0+(index+1)*.5-.002
 else:
  vs=[o.matrix_world@v.co for v in o.data.vertices];lo=min(v.x for v in vs);hi=max(v.x for v in vs);newlo=lo;newhi=hi-.2
 for v in o.data.vertices:
  co=o.matrix_world@v.co;co.x=newlo+(co.x-lo)*(newhi-newlo)/(hi-lo);v.co=inv@co
 P.uv(o);edited.append(n)
for n in ['CBM_SECONDARY_MIRROR','CBM_SECONDARY_MIRROR_FRAME','CBM_SECONDARY_UPPER_STORAGE']:
 bpy.data.objects[n].location.x-=.1 if 'MIRROR' in n else .2;moved.append(n)
# Complete950x950 chamfered enclosure, corner door~636mm, inward opening.
for o in list(s.objects):
 if o.name.startswith('R3_SHOWER_'):hide(o)
xe=11.3999;yn=6.4502;xw=xe-.95;ys=yn-.95;cut=.45
poly=[(xw,yn),(xw,ys+cut),(xw+cut,ys),(xe,ys),(xe,yn)]
vs=[(x,y,.452) for x,y in poly]+[(x,y,.47) for x,y in poly];faces=[tuple(range(4,-1,-1)),tuple(range(5,10))]+[(i,(i+1)%5,(i+1)%5+5,i+5) for i in range(5)];me=bpy.data.meshes.new('V14_SHOWER_950_TRAY');me.from_pydata(vs,[],faces);me.update();tray=bpy.data.objects.new(me.name,me);col.objects.link(tray);me.materials.append(bpy.data.materials['RENDER_CERAMIC']);P.created.append(tray)
def pane(n,a,b):
 a,b=Vector(a),Vector(b);v=b-a;length=v.length;P.box(n,((a.x+b.x)/2,(a.y+b.y)/2,1.46),(length,.008,1.98),glass,0);o=P.created[-1];o.rotation_euler.z=math.atan2(v.y,v.x);return o
A=(xw,ys+cut,0);B=(xw+cut,ys,0)
pane('V14_SHOWER_WEST_FIXED',(xw,yn,0),A);pane('V14_SHOWER_SOUTH_FIXED',B,(xe,ys,0));door=pane('V14_SHOWER_INWARD_DOOR',A,B)
hinge=bpy.data.objects.new('V14_SHOWER_DOOR_HINGE',None);col.objects.link(hinge);hinge.location=(A[0],A[1],.47);world=door.matrix_world.copy();door.parent=hinge;door.matrix_world=world;door['open_direction']='inward counterclockwise0..90deg';door['construction_status']='custom enclosure dimension study; vendor hinge/load specification pending'
for i,(xx,yy) in enumerate([poly[0],poly[1],poly[2],poly[3]]):P.box('V14_SHOWER_POST_'+str(i),(xx,yy,1.46),(.018,.018,1.98),metal,.002)
for i in range(3):
 aa,bb=poly[i],poly[i+1]
 for zz,lab in [(.479,'LOW'),(2.441,'HIGH')]:P.rod('V14_SHOWER_'+lab+'_FRAME_'+str(i),(*aa,zz),(*bb,zz),.006,metal)
P.box('V14_SHOWER_HANDLE',(B[0]-.055,B[1]+.035,1.47),(.012,.018,.15),metal,.002);P.box('V14_SHOWER_DRAIN',(11.17,6.14,.472),(.09,.09,.004),metal,.001)
# Real Concept2 RowErg physical footprint2440x610; proxy silhouette not detailed asset.
def mat(n,c,r=.7):
 m=bpy.data.materials.new(n);m.use_nodes=True;m.diffuse_color=(*c,1);p=m.node_tree.nodes.get('Principled BSDF');p.inputs['Base Color'].default_value=(*c,1);p.inputs['Roughness'].default_value=r;return m
black=mat('V14_ROWER_MATTE_BLACK',(.035,.04,.045));al=mat('V14_ROWER_ALUMINUM',(.30,.32,.34),.4);safety=mat('V14_ROWER_USE_ZONE',(.29,.48,.37))
# AxisY along west wall; use rectangle x3.10..4.32,y10.05..12.79. Physicalx3.405..4.015,y10.20..12.64.
P.assembly('V14_CONCEPT2_ROWErg_PLACEHOLDER','Official Concept2 specifications:2440x610mm, seat360mm; recommended use2740x1220mm. Product-shaped footprint proxy, not procurement mesh.')
cx=3.71;ylo=10.20;yhi=12.64
P.box('V14_ROWER_MONORAIL',(cx,11.04,.25),(.10,1.70,.10),al,.01);P.box('V14_ROWER_REAR_FOOT',(cx,ylo+.02,.05),(.61,.04,.10),black,.01);P.box('V14_ROWER_FRONT_FOOT',(cx,12.36,.06),(.61,.16,.12),black,.01)
P.box('V14_ROWER_SEAT',(cx,10.96,.33),(.31,.26,.06),black,.025);P.box('V14_ROWER_FOOTBOARD_L',(cx-.12,11.92,.30),(.17,.30,.07),black,.02);P.box('V14_ROWER_FOOTBOARD_R',(cx+.12,11.92,.30),(.17,.30,.07),black,.02)
P.rod('V14_ROWER_FLYWHEEL',(cx-.11,12.39,.39),(cx+.11,12.39,.39),.25,black);P.rod('V14_ROWER_MONITOR_ARM',(cx,12.42,.55),(cx,12.47,.94),.017,al);P.box('V14_ROWER_PM5',(cx,12.46,.96),(.18,.05,.16),black,.01);P.rod('V14_ROWER_HANDLE',(cx-.22,11.93,.65),(cx+.22,11.93,.65),.016,black)
# Reference outline on floor in a separate object; don't use a filled obstruction.
P.group=None;zone=[(3.10,10.05,.006),(4.32,10.05,.006),(4.32,12.79,.006),(3.10,12.79,.006)];P.curve('V14_ROWER_2740x1220_USE_ZONE',zone,.004,safety,True)
new=[o.name for o in bpy.data.objects if o.name not in before]
for n,(hv,lh) in hides.items():
 o=bpy.data.objects[n];o.hide_viewport=hv
 for l in s.view_layers:o.hide_set(lh[l.name],view_layer=l)
for n,h in cols.items():bpy.data.collections[n].hide_viewport=h
for n in hidden:
 o=bpy.data.objects[n];o.hide_viewport=True
 for l in s.view_layers:o.hide_set(True,view_layer=l)
bpy.context.window.view_layer=s.view_layers['OVERVIEW_CEILING_HIDDEN'];bpy.ops.wm.save_as_mainfile(filepath=str(O))
a={'source':str(S),'source_sha256':sha(S),'output':str(O),'sha256':sha(O),'before':before,'moved_objects':sorted(set(moved)),'edited_objects':edited,'hidden_objects':hidden,'new_objects':new,'art_translation_m':[.4439,0,.14],'art_center_above_FFL_mm':1650,'art_back_wall_gap_mm':2,'handrail_extension_mm':350,'handrail_horizontal_gripping_top_above_platform_mm':901,'handrail_reference':'https://www.access-board.gov/ada/chapter/ch05/#50510-handrail-extensions;305mm top extension and return; design reference not local certification','vanity_width_mm':1000,'shower_envelope_mm':[950,950],'shower_diagonal_door_mm':math.sqrt(2)*450,'shower_nominal_post_clear_mm':math.sqrt(2)*450-18,'toilet_moved':False,'shower_product_status':'evidence-backed custom dimension study; actual hinge, seals, clear opening, plumbing and waterproof build-up require product/site confirmation','rower_product':'Concept2 RowErg standard legs','rower_source':'https://shop.concept2.com/rowergs/298-model-d-with-pm5.html','rower_body_mm':[2440,610],'rower_use_mm':[2740,1220],'rower_use_bounds_xy_m':[3.10,10.05,4.32,12.79],'rower_status':'footprint fit test, no procurement selection','protected_sources':json.loads((R/'design/whole_house_model_v1/PRESERVATION.json').read_text())['files'],'status':'BUILT_PENDING_GEOMETRY_VALIDATION','no_image2':True}
(D/'BUILD_AUDIT.json').write_text(json.dumps(a,indent=2)+'\n');print('V14_BUILT',a['sha256'],len(new))

