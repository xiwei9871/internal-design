"""Ephemeral loose-furniture overlays over immutable R4. Saves PNG/JSON only, no blend writeback."""
import bpy,json,hashlib,runpy,sys,math
from pathlib import Path
from mathutils import Vector,Matrix
OUT=Path(__file__).resolve().parent;sys.path.insert(0,str(OUT))
from layout_spec import ROOT,SRC,SOURCE_SHA,BASE_CAMERAS,PRIORITY,OPTIONAL,LAYOUTS
H=runpy.run_path(str(ROOT/'design/kitchen_frozen_v1/freeze_kitchen.py'),run_name='geometry_helpers')
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
def dump(p,d):Path(p).write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n')
def state():return {n:{k:v for k,v in d.items() if k in ['type','geometry_sha256','authored_transform','parent','modifiers']} for n,d in H['snapshot']().items()}
def bounds(objects):
 pts=[o.matrix_world@Vector(c) for o in objects if o.type=='MESH' for c in o.bound_box]
 return [[min(v[i] for v in pts) for i in range(3)],[max(v[i] for v in pts) for i in range(3)]]
def parts(root):return [bpy.data.objects[root]]+list(bpy.data.objects[root].children_recursive)
def hide(root):
 for o in parts(root):o.hide_render=True;o.hide_set(True)
def move(root,center,angle=0):
 os=parts(root);lo,hi=bounds(os);old=Vector([(lo[i]+hi[i])/2 for i in range(3)]);new=Vector([*center,old.z]);o=bpy.data.objects[root];o.matrix_world=Matrix.Translation(new)@Matrix.Rotation(math.radians(angle),4,'Z')@Matrix.Translation(-old)@o.matrix_world;bpy.context.view_layer.update()
def material(n,c):m=bpy.data.materials.new(n);m.diffuse_color=c;return m
def box(name,loc,size,mat,bevel=.02):
 bpy.ops.mesh.primitive_cube_add(size=1,location=loc);o=bpy.context.object;o.name='LP_'+name;o.dimensions=size;bpy.ops.object.transform_apply(location=False,rotation=False,scale=True);o.data.materials.append(mat)
 if bevel:b=o.modifiers.new('proxy softened edge','BEVEL');b.width=bevel;b.segments=3
 return o
def cylinder(name,loc,scale,mat):
 bpy.ops.mesh.primitive_cylinder_add(vertices=48,radius=1,depth=1,location=loc);o=bpy.context.object;o.name='LP_'+name;o.scale=scale;o.data.materials.append(mat);bpy.ops.object.transform_apply(location=False,rotation=False,scale=True);b=o.modifiers.new('proxy edge','BEVEL');b.width=.008;b.segments=2;return o
def oval_table(name,center,diam,height,mat,legs):
 x,y=center;cylinder(name+'_top',[x,y,height-.018],[diam[0]/2,diam[1]/2,.035],mat)
 for i,(dx,dy) in enumerate([(-.25,-.23),(.25,-.23),(0,.26)]):box(name+'_leg'+str(i),[x+dx*diam[0],y+dy*diam[1],(height-.035)/2],[.055,.055,height-.035],legs,.014)
def chair(name,center,angle,mats):
 x,y=center;created=[]
 for suffix,loc,size,mat in [('seat',[x,y,.42],[.75,.76,.15],mats['FURN']),('back',[x,y-.34,.67],[.75,.12,.47],mats['FURN']),('armL',[x-.39,y,.53],[.055,.70,.055],mats['WOOD']),('armR',[x+.39,y,.53],[.055,.70,.055],mats['WOOD'])]:created.append(box(name+suffix,loc,size,mat,.04))
 for dx in [-.30,.30]:
  for dy in [-.27,.27]:created.append(box(name+str(dx)+str(dy),[x+dx,y+dy,.18],[.055,.055,.36],mats['WOOD'],.008))
 T=Matrix.Translation(Vector([x,y,0]));R=Matrix.Rotation(math.radians(angle),4,'Z')
 for o in created:o.matrix_world=T@R@T.inverted()@o.matrix_world
 return created
def lsofa(m):
 # West leg: registered 2300x900 zone; north return within approved loose-furniture exploration only.
 box('L_west_base',[3.851,10.366,.20],[.90,2.30,.23],m['FURN'],.08);box('L_west_back',[3.50,10.366,.62],[.20,2.30,.40],m['FURN'],.07)
 box('L_north_base',[4.73,11.066,.20],[2.54,.90,.23],m['FURN'],.08);box('L_north_back',[4.73,11.42,.62],[2.54,.20,.40],m['FURN'],.07)
 for j,y in enumerate([9.62,10.37,11.11]):box('L_west_cushion'+str(j),[3.91,y,.40],[.68,.71,.17],m['FURN'],.07)
 for j,x in enumerate([4.62,5.36]):box('L_return_cushion'+str(j),[x,11.00,.40],[.70,.68,.17],m['FURN'],.07)
 box('L_south_arm',[3.85,9.28,.49],[.9,.13,.30],m['FURN'],.05);box('L_east_arm',[5.91,11.05,.49],[.14,.9,.30],m['FURN'],.05)
 for x,y in [(3.54,9.45),(4.16,9.45),(3.54,11.34),(5.79,10.78),(5.79,11.33)]:box('L_foot'+str(x)+str(y),[x,y,.055],[.06,.06,.11],m['WOOD'],.008)
def floorlamp(center,m):
 x,y=center;cylinder('lampbase',[x,y,.035],[.13,.13,.07],m['FRAME']);cylinder('lampstem',[x,y,.72],[.012,.012,1.44],m['FRAME']);cylinder('lampshade',[x+.06,y,1.43],[.14,.14,.13],m['ARCH'])
extra='extra' in sys.argv
correct_c='correct_c' in sys.argv
views=(PRIORITY+OPTIONAL) if correct_c else OPTIONAL if extra else PRIORITY
allreg=json.loads((OUT/'reports/CAMERA_REGISTER.json').read_text()) if extra or correct_c else []
if correct_c:allreg=[r for r in allreg if r['layout']!='C']
locks=json.loads((OUT/'reports/ARCHITECTURE_LOCK.json').read_text()) if correct_c else []
if correct_c:locks=[l for l in locks if l['layout']!='C']
assert sha(SRC)==SOURCE_SHA
for key,layout in LAYOUTS.items():
 if correct_c and key!='C':continue
 bpy.ops.wm.open_mainfile(filepath=str(SRC));bpy.context.view_layer.update();before=state();allowed_roots=['B11_Rectangle046','B11_Rectangle047','B11_Rectangle048','B11_Rectangle049','B11_Circle'];allowed={o.name for r in allowed_roots for o in parts(r)}
 # Geometry and authored transforms of every inherited object outside the allowed loose-furniture subtree stay identical.
 mats={k:material('LP_CLAY_'+k,v) for k,v in {'ARCH':(.88,.88,.86,1),'FURN':(.74,.75,.73,1),'WOOD':(.58,.61,.56,1),'STONE':(.83,.84,.81,1),'FRAME':(.27,.32,.33,1),'GLASS':(.83,.90,.92,.16),'FLOOR':(.77,.77,.74,1)}.items()}
 for o in bpy.data.objects:
  if o.type!='MESH':continue
  if any(c.name in ['05_HUMAN_DESIGN_GUIDE','06_FUTURE_DESIGN_OPTIONS','90_FUTURE_DESIGN_OPTIONS','91_ACCESSIBILITY_OPTIONS','COL_B11_REVIEW_MARKERS'] for c in o.users_collection):o.hide_render=True;continue
  if o.hide_render or o.hide_viewport:continue
  o.data=o.data.copy()
  for i,m in enumerate(list(o.data.materials)):
   n=o.name.upper();mn=m.name.upper() if m else ''
   typ='GLASS' if 'GLASS' in n or 'GLASS' in mn else 'FRAME' if 'FRAME' in mn or 'METAL' in mn or any(k in n for k in ['JAMB','RAIL','MULLION','TRACK']) else 'FLOOR' if n.startswith(('FLOOR_','SITE_GROUND')) or 'UPPER_FLOOR' in n else 'ARCH' if 'WALL' in mn or 'CEILING' in n or any(k in n for k in ['WALL','CORNER_PATCH']) else 'FURN';o.data.materials[i]=mats[typ]
 hide('B11_Circle');hide('B11_Rectangle049')
 if key in ['A','B']:move('B11_Rectangle048',layout['chaise_center'])
 if key=='A':move('B11_Rectangle047',layout['two_center'],180)
 if key=='B':hide('B11_Rectangle047');chair('B_inner_chair',layout['chair_center'],layout['chair_angle'],mats)
 if key=='C':
  for r in ['B11_Rectangle046','B11_Rectangle047','B11_Rectangle048']:hide(r)
  lsofa(mats);chair('C_window_reclining_chair',layout['chair_center'],layout['chair_angle'],mats)
 cx,cy=layout['table_center'];oval_table(key+'_main_table',[cx,cy],[.98,.62],.37,mats['STONE'],mats['WOOD']);oval_table(key+'_satellite_table',[cx+.47,cy+.22],[.57,.52],.44,mats['STONE'],mats['WOOD'])
 for j,c in enumerate(layout['side_centers']):oval_table(key+'_side'+str(j),c,[.42,.42],.51,mats['WOOD'],mats['WOOD'])
 floorlamp([4.35,12.53],mats)
 after=state();protected={n:s for n,s in before.items() if n not in allowed}
 for n,s in protected.items():assert after[n]==s,'unauthorized inherited change '+n
 lockhash=hashlib.sha256(json.dumps(protected,sort_keys=True).encode()).hexdigest();locks.append(dict(layout=key,source_sha256=SOURCE_SHA,protected_object_count=len(protected),protected_geometry_and_authored_pose='PASS_UNCHANGED',protected_state_sha256=lockhash,allowed_loose_roots=allowed_roots,allowed_source_object_names=sorted(allowed),new_proxy_names=[o.name for o in bpy.data.objects if o.name.startswith('LP_')],saved_blend=False,master_modified=False,freecad_writeback=False))
 s=bpy.context.scene;s.render.engine='BLENDER_WORKBENCH';s.render.resolution_x=1536;s.render.resolution_y=1024;s.render.resolution_percentage=100;s.render.image_settings.file_format='PNG';s.render.image_settings.color_mode='RGB';s.view_settings.view_transform='Standard';sh=s.display.shading;sh.light='STUDIO';sh.color_type='MATERIAL';sh.show_shadows=False;sh.show_cavity=True;sh.cavity_type='BOTH';s.display.render_aa='32'
 collection=bpy.data.collections.new('LP_TEMP_CAMERAS');s.collection.children.link(collection)
 for basecam in [c for c in BASE_CAMERAS if c['id'] in views]:
  cam=dict(basecam)
  if cam['id']=='L5':cam['target']=[5.45,12.15,.70]
  d=bpy.data.cameras.new('LP_'+key+'_'+cam['id']);o=bpy.data.objects.new(d.name,d);collection.objects.link(o);o.location=cam['pos'];o.rotation_euler=(Vector(cam['target'])-o.location).to_track_quat('-Z','Y').to_euler();d.lens=cam['lens'];d.sensor_width=36;d.clip_start=.03;d.clip_end=100;s.camera=o;path=OUT/'reference'/('living_layout'+key+'_'+layout['slug']+'_'+cam['id']+'_reference.png');s.render.filepath=str(path);bpy.ops.render.render(write_still=True);allreg.append(dict(layout=key,slug=layout['slug'],camera=cam['id'],pos=cam['pos'],target=cam['target'],lens=cam['lens'],visible=cam['visible'],hidden=cam['hidden'],reference=str(path),reference_sha256=sha(path),source_sha256=SOURCE_SHA,furniture_layer='UNSELECTED_TEMPORARY_LOOSE_LAYOUT',architecture='UNCHANGED_R4',base_camera_target=basecam['target'],camera_adjustment='L5 target only retargeted downward to new window seating; position/lens unchanged' if cam['id']=='L5' else 'NONE'));print('REFERENCE_DONE '+key+' '+cam['id'],flush=True)
 assert sha(SRC)==SOURCE_SHA
 dump(OUT/'reports/CAMERA_REGISTER.json',allreg);dump(OUT/'reports/ARCHITECTURE_LOCK.json',locks)
print(json.dumps(dict(status='PASS_R4_ARCHITECTURE_LOCK',references=len(allreg),layouts=3,master_unchanged=sha(SRC)==SOURCE_SHA,saved_blend=False)))
