"""R4-only geometry references. First phase opens R4 and exports only A1."""
import bpy,json,hashlib,runpy,shutil,sys,math
from pathlib import Path
from mathutils import Vector
OUT=Path(__file__).resolve().parent;ROOT=OUT.parents[2]
SRC=ROOT/'design/bedroom_door_r4/OPTION_A_SLIDING_R4.blend'
BRANCH=OUT/'00_reference/R4_LIVING_AI_REFERENCE_V1.blend'
H=runpy.run_path(str(ROOT/'design/kitchen_frozen_v1/freeze_kitchen.py'),run_name='snapshot_helpers')
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
CAMERAS=[
 dict(id='A1',name='HERO',pos=[7.15,8.25,1.55],target=[4.85,11.45,1.20],lens=28,eye_height=1.55,visible='两组主要座位、中央茶几、北侧外挑飘窗',hidden='门口、错层平台、台阶和media墙在机位背后/侧后，不凭空出现在前方'),
 dict(id='A2',name='REVERSE',pos=[3.35,12.65,1.55],target=[6.25,8.85,1.00],lens=28,eye_height=1.55,visible='原低media柜、三阶台阶、曲线错层平台、后方已补回的东西向普通木门与右侧公共区玻璃开口',hidden='北侧飘窗在相机背后，前方不得新增采光大窗'),
 dict(id='A3',name='SEATING DETAIL',pos=[6.80,9.15,1.52],target=[4.90,10.75,.78],lens=32,eye_height=1.52,visible='会客区与茶几裁切近景、局部窗沿',hidden='只按输入裁切显示家具，不缩小家具以求完整；不添画面外新窗或门'),
 dict(id='A4',name='PUBLIC SPACE LINK',pos=[7.13,12.65,1.58],target=[5.55,6.15,1.15],lens=24,eye_height=1.58,visible='三阶台阶、曲线错层平台、上下地坪、餐区玻璃开口与客厅活动家具',hidden='次主卧直门在左后被实墙遮挡，仅可能露细边，不能挪到前景墙上或画出前景门把手；旧斜门停用'),
 dict(id='A5',name='BAY WINDOW MOOD',pos=[7.05,11.55,1.55],target=[5.85,13.45,1.05],lens=32,eye_height=1.55,visible='北侧玻璃分格、外挑低平台、窗前双人座位一角',hidden='不把低平台抬高为固定高柜，不新增窗边固定柜，不改窗框分格或外挑深度'),
]
def write(n,d):(OUT/n).write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n')
def lock():return {n:{k:v for k,v in s.items() if k in ['type','geometry_sha256','authored_transform','parent','modifiers']} for n,s in H['snapshot']().items()}
def material(n,c):m=bpy.data.materials.new(n);m.diffuse_color=c;return m
def camera(col,row):
 d=bpy.data.cameras.new('R4_LIVING_'+row['id']);o=bpy.data.objects.new(d.name,d);col.objects.link(o);o.location=row['pos'];o.rotation_euler=(Vector(row['target'])-o.location).to_track_quat('-Z','Y').to_euler();d.lens=row['lens'];d.sensor_width=36;d.clip_start=.03;d.clip_end=100;return o
def render(row):
 s=bpy.context.scene;s.camera=bpy.data.objects['R4_LIVING_'+row['id']];s.render.filepath=str(OUT/'00_reference'/('living_'+row['id']+'_reference.png'));bpy.ops.render.render(write_still=True)
 return dict(**row,camera=s.camera.name,source_model=str(SRC),source_sha256=sha(SRC),reference=s.render.filepath,reference_sha256=sha(s.render.filepath),lens_mm=row['lens'],resolution=[1536,1024],geometry_source='ONLY_R4',wall_cuts=[],engine='WORKBENCH')
def preflight():
 for d in ['00_reference','01_faithful','02_designer','03_creative','04_contact_sheets','05_prompts','06_reports','06_reports/logs','06_reports/proxies']:(OUT/d).mkdir(parents=True,exist_ok=True)
 manifest=json.loads((SRC.parent/'R4_OPTION_A_MANIFEST.json').read_text());assert sha(SRC)==manifest['model_sha256'];assert not BRANCH.exists()
 shutil.copy2(SRC,BRANCH);shutil.copy2('/Users/xiwei/.codex/attachments/af4bbdff-8fe6-447d-9c52-9cc9b962a0da/Pasted text.txt',OUT/'06_reports/USER_TASK_BRIEF.txt')
 bpy.ops.wm.open_mainfile(filepath=str(BRANCH));bpy.context.view_layer.update();states=lock();write('06_reports/R4_SOURCE_GEOMETRY_LOCK.json',states)
 write('R4_LIVING_PREFLIGHT.json',dict(status='PASS_OPENED_R4',source_path=str(SRC),SHA256=sha(SRC),object_count=len(bpy.data.objects),collection_count=len(bpy.data.collections),blender=bpy.app.version_string,working_copy=str(BRANCH),model_authority='CURRENT_R4_OPTION_A',R3_policy='HISTORICAL_ONLY_NO_IMPORT',reference_phase='A1_MINIMAL_API_TEST_FIRST',mother_modified=False))
 mats={k:material('R4_REFERENCE_'+k,c) for k,c in {'ARCH':(.88,.88,.86,1),'FURN':(.71,.73,.71,1),'FLOOR':(.77,.77,.74,1),'FRAME':(.27,.32,.33,1),'GLASS':(.83,.90,.92,.16)}.items()}
 guides=[]
 for o in bpy.data.objects:
  if o.type!='MESH':continue
  if any(c.name in ['05_HUMAN_DESIGN_GUIDE','06_FUTURE_DESIGN_OPTIONS'] for c in o.users_collection):
   if not o.hide_render:guides.append(o.name)
   o.hide_render=True;continue
  if o.hide_render or o.hide_viewport:continue
  o.data=o.data.copy()
  for i,m in enumerate(list(o.data.materials)):
   name=o.name.upper();mn=m.name.upper() if m else ''
   if 'GLASS' in name or 'GLASS' in mn:new=mats['GLASS']
   elif 'FRAME' in mn or 'METAL' in mn or any(x in name for x in ['JAMB','RAIL','MULLION','TRACK']):new=mats['FRAME']
   elif name.startswith(('FLOOR_','SITE_GROUND')) or 'UPPER_FLOOR' in name:new=mats['FLOOR']
   elif 'WALL' in mn or 'CEILING' in name or name.startswith(('R3_HOUSE_WALL','V5_CORNER_PATCH','R4_DOOR_WEST','R4_DOOR_COMPLETE','R4_WEST_PARTITION')):new=mats['ARCH']
   else:new=mats['FURN']
   o.data.materials[i]=new
  if not o.data.materials:o.data.materials.append(mats['ARCH'])
 col=bpy.data.collections.new('COL_R4_LIVING_EXPLORATION_CAMERAS');bpy.context.scene.collection.children.link(col);camera(col,CAMERAS[0])
 s=bpy.context.scene;s.camera=bpy.data.objects['R4_LIVING_A1'];s.render.engine='BLENDER_WORKBENCH';s.render.resolution_x=1536;s.render.resolution_y=1024;s.render.resolution_percentage=100;s.render.image_settings.file_format='PNG';s.render.image_settings.color_mode='RGB';s.view_settings.view_transform='Standard';sh=s.display.shading;sh.light='STUDIO';sh.color_type='MATERIAL';sh.show_shadows=False;sh.show_cavity=True;sh.cavity_type='BOTH';s.display.render_aa='32'
 now=lock()
 for n,r in states.items():assert now[n]==r,n
 bpy.ops.wm.save_as_mainfile(filepath=str(BRANCH));row=render(CAMERAS[0]);write('00_reference/R4_CAMERA_REGISTER.json',[row]);assert sha(SRC)==manifest['model_sha256']
 write('06_reports/REFERENCE_STATE.json',dict(locked_objects=len(states),physical_design_geometry_and_poses='PASS_UNCHANGED',nonphysical_guides_excluded=guides,cycles_used=False,only_A1_prepared=True))
 print(json.dumps(dict(preflight='PASS',objects=len(states),collections=len(bpy.data.collections),A1_reference=row['reference']),ensure_ascii=False))
def remaining():
 # Explicit success gate: do not prepare the downstream cameras before API test.
 test=json.loads((OUT/'06_reports/A1_API_TEST.json').read_text());assert test['status']=='GENERATED'
 pref=json.loads((OUT/'R4_LIVING_PREFLIGHT.json').read_text());assert sha(SRC)==pref['SHA256'];bpy.ops.wm.open_mainfile(filepath=str(BRANCH));states=json.loads((OUT/'06_reports/R4_SOURCE_GEOMETRY_LOCK.json').read_text());now=lock()
 for n,r in states.items():assert now[n]==r,n
 col=bpy.data.collections['COL_R4_LIVING_EXPLORATION_CAMERAS'];rows=json.loads((OUT/'00_reference/R4_CAMERA_REGISTER.json').read_text())
 for r in CAMERAS[1:]:camera(col,r)
 bpy.ops.wm.save_as_mainfile(filepath=str(BRANCH))
 for r in CAMERAS[1:]:rows.append(render(r))
 write('00_reference/R4_CAMERA_REGISTER.json',rows)
 bpy.ops.wm.open_mainfile(filepath=str(BRANCH));now=lock()
 for n,r in states.items():assert now[n]==r,n
 assert sha(SRC)==pref['SHA256'];write('06_reports/REFERENCE_GEOMETRY_QA.json',dict(status='PASS_FRESH_OPEN',source_sha256=sha(SRC),source_objects_locked=len(states),new_camera_count=5,lens_range_mm=[24,32],eye_height_range_m=[1.52,1.58],all_references_R4_derived=True,source_unchanged=True,branch_sha256=sha(BRANCH)))
 print(json.dumps(dict(references='PASS',count=5,only_R4=True)))
if __name__=='__main__':globals()[sys.argv[sys.argv.index('--')+1]]()
