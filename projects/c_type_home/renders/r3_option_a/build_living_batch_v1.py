"""Five camera / Workbench clay exports only. No Cycles or material development."""
import bpy,json,hashlib,runpy,shutil
from pathlib import Path
from mathutils import Vector
ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'renders/r3_option_a/living_batch_v1'
SOURCE=ROOT/'design/secondary_bath_options/r3/OPTION_A_SLIDING_R3.blend'
H=runpy.run_path(str(ROOT/'design/kitchen_frozen_v1/freeze_kitchen.py'),run_name='state_helpers')
CAMERAS=[
 dict(id='A1',name='主视角',pos=[7.15,8.25,1.55],target=[4.85,11.45,1.20],lens=28,story='两组独立沙发、茶几与北侧外挑飘窗；贵妃椅与休闲平台多在机位侧后方，不强行带入。'),
 dict(id='A2',name='反向视角',pos=[3.35,12.65,1.55],target=[6.25,8.85,1.00],lens=28,story='从窗边反看会客区、电视柜一侧与内部公共区；北侧飘窗在相机后方，不得在前方另造大窗。'),
 dict(id='A3',name='会客区近景',pos=[6.80,9.15,1.52],target=[4.90,10.75,.78],lens=32,story='茶几、沙发布艺及地毯近景；参考图裁切范围外的窗与门不得凭空补进画面。'),
 dict(id='A4',name='公共区域联动',pos=[7.13,12.65,1.58],target=[5.55,6.15,1.15],lens=24,story='由客厅反看公共区域，保留可见开放通道、曲线平台和错层；不要补回旧斜门。'),
 dict(id='A5',name='窗边飘窗氛围',pos=[7.05,11.55,1.55],target=[5.85,13.45,1.05],lens=32,story='窗边、外挑平台和双人沙发一角；平台与沙发的高低及遮挡关系按模型，不新造高台或固定窗边柜。'),
]
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def write(n,d):(OUT/n).write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n')
def geo_states():
 return {n:{k:v for k,v in s.items() if k in ['type','geometry_sha256','authored_transform','parent','modifiers']} for n,s in H['snapshot']().items()}
def mat(n,c):
 m=bpy.data.materials.new(n);m.diffuse_color=(*c,1);return m
def main():
 for p in ['working/cameras','working/previews','working/prompts','exports/clay','exports/ai_outputs','exports/contact_sheets','exports/final_selected','logs']:(OUT/p).mkdir(parents=True,exist_ok=True)
 master=json.loads((SOURCE.parent/'OPTION_A_MANIFEST.json').read_text());assert sha(SOURCE)==master['model_sha256']
 branch=OUT/'working/living_batch_v1.blend';assert not branch.exists(),'Preserve existing branch'
 shutil.copy2(SOURCE,branch);shutil.copy2('/Users/xiwei/.codex/attachments/4c6a0b92-79d1-4f32-8259-d59bb3ee8134/Pasted text.txt',OUT/'USER_BATCH_TASK_BRIEF.txt')
 bpy.ops.wm.open_mainfile(filepath=str(branch));bpy.context.view_layer.update();before=geo_states();write('working/R3_SOURCE_GEOMETRY_STATES.json',before)
 wall=mat('LIVING_BATCH_CLAY_ARCH',(.87,.88,.86));floor=mat('LIVING_BATCH_CLAY_FLOOR',(.74,.75,.73));furn=mat('LIVING_BATCH_CLAY_FURNITURE',(.70,.72,.70));frame=mat('LIVING_BATCH_CLAY_FRAME',(.30,.35,.36));gl=mat('LIVING_BATCH_CLAY_GLAZING',(.84,.90,.92));gl.diffuse_color=(.84,.90,.92,.16)
 excluded=[]
 for o in bpy.data.objects:
  if o.type!='MESH':continue
  if any(c.name in ['05_HUMAN_DESIGN_GUIDE','06_FUTURE_DESIGN_OPTIONS'] for c in o.users_collection):
   if not o.hide_render:excluded.append(o.name)
   o.hide_render=True;continue
  if o.hide_render or o.hide_viewport:continue
  o.data=o.data.copy()
  for i,m in enumerate(list(o.data.materials)):
   mn=m.name.upper() if m else '';name=o.name.upper()
   if 'GLASS' in mn or 'GLASS' in name:new=gl
   elif 'FRAME' in mn or 'METAL' in mn or any(k in name for k in ['JAMB','MULLION','RAIL','TRACK']):new=frame
   elif name.startswith(('FLOOR_','SITE_GROUND')):new=floor
   elif 'WALL' in mn or 'CEILING' in name or name.startswith(('R3_HOUSE_WALLS','V5_CORNER_PATCH')):new=wall
   else:new=furn
   o.data.materials[i]=new
  if not o.data.materials:o.data.materials.append(wall)
 col=bpy.data.collections.new('LIVING_BATCH_V1_CAMERAS');bpy.context.scene.collection.children.link(col)
 for row in CAMERAS:
  data=bpy.data.cameras.new('LIVING_BATCH_'+row['id']);o=bpy.data.objects.new(data.name,data);col.objects.link(o);o.location=row['pos'];o.rotation_euler=(Vector(row['target'])-o.location).to_track_quat('-Z','Y').to_euler();data.lens=row['lens'];data.sensor_width=36;data.clip_start=.03;data.clip_end=100;row['camera']=o.name;row['eye_height_above_ffl_m']=row['pos'][2];row['clay_path']=str(OUT/'exports/clay'/('living_'+row['id']+'_clay_v1.png'))
 after=geo_states()
 for n,s in before.items():assert after[n]==s,n
 s=bpy.context.scene;s.camera=bpy.data.objects[CAMERAS[0]['camera']];s.render.engine='BLENDER_WORKBENCH';s.render.resolution_x=1536;s.render.resolution_y=1024;s.render.resolution_percentage=100;s.render.image_settings.file_format='PNG';s.render.image_settings.color_mode='RGB';s.view_settings.view_transform='Standard'
 sh=s.display.shading;sh.light='STUDIO';sh.color_type='MATERIAL';sh.show_shadows=False;sh.show_cavity=True;sh.cavity_type='BOTH';sh.background_type='WORLD';s.world.color=(.95,.95,.93);s.display.render_aa='32'
 bpy.ops.wm.save_as_mainfile(filepath=str(branch))
 rows=[]
 for row in CAMERAS:
  s.camera=bpy.data.objects[row['camera']];s.render.filepath=row['clay_path'];bpy.ops.render.render(write_still=True)
  rows.append(dict(**row,clay_sha256=sha(row['clay_path']),resolution=[1536,1024],engine='WORKBENCH',wall_cuts=[],source_saved=False))
 assert sha(SOURCE)==master['model_sha256']
 write('working/cameras/LIVING_CAMERA_REGISTER.json',rows)
 write('logs/GEOMETRY_LOCK_QA.json',dict(status='PASS',source=str(SOURCE),source_sha256=sha(SOURCE),working_branch=str(branch),working_sha256=sha(branch),locked_source_objects=len(before),geometry_and_major_furniture_poses='UNCHANGED',new_cameras=5,cycles_used=False,source_model_modified=False,render_only_reference_guides_excluded=excluded))
 # Actual source furniture bounds, for view-specific notes and future review.
 objs=[]
 for o in bpy.data.objects:
  if o.type=='MESH' and not o.hide_render and o.name.startswith(('B11_Rectangle','B11_Circle')):
   vs=[o.matrix_world@v.co for v in o.data.vertices]
   if not vs:continue
   lo=[min(v[i] for v in vs) for i in range(3)];hi=[max(v[i] for v in vs) for i in range(3)]
   if lo[0]<8.5 and hi[0]>2.5 and lo[1]<13.2 and hi[1]>4.4:objs.append(dict(name=o.name,lo=lo,hi=hi))
 write('working/cameras/ACTUAL_PUBLIC_AREA_FURNITURE_BOUNDS.json',objs)
 print(json.dumps(dict(camera_clay='PASS',cameras=5,locked_objects=len(before),master_preserved=True,branch=str(branch)),ensure_ascii=False))
if __name__=='__main__':main()
