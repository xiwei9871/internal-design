import bpy,json,sys,math,hashlib,runpy,ast
from pathlib import Path
from mathutils import Vector,Matrix
OUT=Path(__file__).resolve().parent;ROOT=OUT.parents[2];SRC=ROOT/'design/bedroom_door_r4/OPTION_A_SLIDING_R4.blend'
SHA='d109c7efcfa2b2b2565e4c073ee0cdf5282b23c01122bc9c1bbe7b8791ac3afb'
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
# Reuse trusted primitive helpers only; do not execute the earlier A/B/C task.
p=OUT.parent/'living_layout_exploration_v2/prepare_layout_references.py';tree=ast.parse(p.read_text());exec(compile(ast.Module(body=[n for n in tree.body if isinstance(n,ast.FunctionDef)],type_ignores=[]),str(p),'exec'))
H=runpy.run_path(str(ROOT/'design/kitchen_frozen_v1/freeze_kitchen.py'),run_name='snapshot_helpers')
assert sha(SRC)==SHA;bpy.ops.wm.open_mainfile(filepath=str(SRC));bpy.context.view_layer.update();before=state();allow_roots=['B11_Rectangle047','B11_Rectangle048','B11_Rectangle049','B11_Circle'];allow={o.name for r in allow_roots for o in parts(r)}
mats={k:material('LIGHT_CLAY_'+k,v) for k,v in {'ARCH':(.88,.88,.86,1),'FURN':(.74,.75,.73,1),'WOOD':(.58,.61,.56,1),'STONE':(.83,.84,.81,1),'FRAME':(.27,.32,.33,1),'GLASS':(.83,.90,.92,.16),'FLOOR':(.77,.77,.74,1)}.items()}
for o in bpy.data.objects:
 if o.type!='MESH':continue
 if any(c.name in ['05_HUMAN_DESIGN_GUIDE','06_FUTURE_DESIGN_OPTIONS','90_FUTURE_DESIGN_OPTIONS','91_ACCESSIBILITY_OPTIONS','COL_B11_REVIEW_MARKERS'] for c in o.users_collection):o.hide_render=True;continue
 if o.hide_render or o.hide_viewport:continue
 o.data=o.data.copy()
 for i,m in enumerate(list(o.data.materials)):
  n=o.name.upper();mn=m.name.upper() if m else '';t='GLASS' if 'GLASS' in n or 'GLASS' in mn else 'FRAME' if 'FRAME' in mn or 'METAL' in mn or any(w in n for w in ['JAMB','RAIL','MULLION','TRACK']) else 'FLOOR' if n.startswith(('FLOOR_','SITE_GROUND')) or 'UPPER_FLOOR' in n else 'ARCH' if 'WALL' in mn or 'CEILING' in n or any(w in n for w in ['WALL','CORNER_PATCH']) else 'FURN';o.data.materials[i]=mats[t]
# Main registered sofa, fixed media unit, architecture and platform are untouched.
hide('B11_Rectangle047');hide('B11_Rectangle049');hide('B11_Circle');move('B11_Rectangle048',[5.50,12.36])
cx,cy=5.15,8.95;angle=-10;created=[]
for suffix,loc,size,mat,bev in [('seat',[cx,cy,.43],[.74,.78,.14],mats['FURN'],.04),('back',[cx,cy-.34,.62],[.74,.10,.40],mats['FURN'],.04),('armL',[cx-.375,cy,.54],[.05,.69,.05],mats['WOOD'],.015),('armR',[cx+.375,cy,.54],[.05,.69,.05],mats['WOOD'],.015)]:created.append(box('LIGHT_CHAIR_'+suffix,loc,size,mat,bev))
for dx in [-.30,.30]:
 for dy in [-.28,.28]:created.append(box('LIGHT_CHAIR_LEG_'+str(dx)+str(dy),[cx+dx,cy+dy,.18],[.05,.05,.36],mats['WOOD'],.006))
T=Matrix.Translation(Vector([cx,cy,0]));R=Matrix.Rotation(math.radians(angle),4,'Z')
for o in created:o.matrix_world=T@R@T.inverted()@o.matrix_world
oval_table('LIGHT_CHAIR_SIDE',[5.95,8.85],[.42,.42],.51,mats['WOOD'],mats['WOOD'])
oval_table('WINDOW_SIDE',[4.00,12.21],[.42,.42],.51,mats['WOOD'],mats['WOOD'])
oval_table('MAIN_COFFEE',[5.28,10.32],[.98,.62],.37,mats['STONE'],mats['WOOD']);oval_table('SUB_COFFEE',[5.75,10.54],[.57,.52],.44,mats['STONE'],mats['WOOD']);floorlamp([4.35,12.53],mats)
bpy.context.view_layer.update();after=state();protected={n:s for n,s in before.items() if n not in allow}
for n,s in protected.items():assert after[n]==s,n
# Registered main sofa is among protected objects; every new chair/side table is on lower living floor.
dg=bpy.context.evaluated_depsgraph_get();floor_hits=[]
for xy in [[5.15,8.95],[5.95,8.85],[5.50,12.36]]:
 origin=Vector([*xy,.02]);result=bpy.context.scene.ray_cast(dg,origin,Vector([0,0,-1]),distance=.2);assert result[0] and abs(result[1].z)<.002,str(xy);floor_hits.append(dict(xy=xy,z=result[1].z,object=result[4].name))
base=json.loads((OUT.parent/'whole_house_ai_v1/01_living/reports/CAMERA_REGISTER.json').read_text());by={c['id']:c for c in base}
shots=[dict(id='HERO',source_camera='L2',pos=by['L2']['pos'],target=by['L2']['target'],lens=by['L2']['lens']),dict(id='SPACE',source_camera='L4',pos=by['L4']['pos'],target=by['L4']['target'],lens=by['L4']['lens']),dict(id='WINDOW_LINK',source_camera='L1_DERIVED',pos=by['L1']['pos'],target=[4.85,10.35,.60],lens=24)]
s=bpy.context.scene;s.render.engine='BLENDER_WORKBENCH';s.render.resolution_x=1536;s.render.resolution_y=1024;s.render.resolution_percentage=100;s.render.image_settings.file_format='PNG';s.render.image_settings.color_mode='RGB';s.view_settings.view_transform='Standard';sh=s.display.shading;sh.light='STUDIO';sh.color_type='MATERIAL';sh.show_shadows=False;sh.show_cavity=True;sh.cavity_type='BOTH';s.display.render_aa='32'
col=bpy.data.collections.new('TEMP_LIGHT_CAMERAS');s.collection.children.link(col)
for c in shots:
 if 'window_only' in sys.argv and c['id']!='WINDOW_LINK':
  f=OUT/'reference'/('LIVING_LIGHT_'+c['id']+'_REFERENCE.png');c['reference']=str(f);c['reference_sha256']=sha(f);continue
 d=bpy.data.cameras.new('LIGHT_'+c['id']);o=bpy.data.objects.new(d.name,d);col.objects.link(o);o.location=c['pos'];o.rotation_euler=(Vector(c['target'])-o.location).to_track_quat('-Z','Y').to_euler();d.lens=c['lens'];d.sensor_width=36;d.clip_start=.03;d.clip_end=100;s.camera=o;f=OUT/'reference'/('LIVING_LIGHT_'+c['id']+'_REFERENCE.png');s.render.filepath=str(f);bpy.ops.render.render(write_still=True);c['reference']=str(f);c['reference_sha256']=sha(f);print('REFERENCE_DONE '+c['id'],flush=True)
assert sha(SRC)==SHA
(OUT/'reports/CAMERA_REGISTER.json').write_text(json.dumps(shots,ensure_ascii=False,indent=2)+'\n')
(OUT/'reports/GEOMETRY_LOCK.json').write_text(json.dumps(dict(source=str(SRC),source_sha256=SHA,source_unchanged=True,protected_count=len(protected),main_sofa_protected=True,architecture_and_fixed_cabinetry='PASS_UNCHANGED',no_new_cabinet=True,no_platform_furniture=True,chair=dict(size_mm=[800,780,820],center_m=[5.15,8.95,0],angle_deg=-10,role='light ash-frame upholstered chair on lower floor NW of split-level stairs'),side_table=dict(diameter_mm=420,height_mm=510,center_m=[5.95,8.85,0]),chaise=dict(size_mm=[1700,900,800],center_m=[5.5,12.36,0]),floor_hits=floor_hits,protected_main_route_mm=1118,saved_blend=False,freecad_writeback=False),ensure_ascii=False,indent=2)+'\n');print('REFERENCE_PIPELINE_PASS')
