import bpy,json,runpy,hashlib
from pathlib import Path
from mathutils import Vector
ROOT=Path(__file__).resolve().parents[2]
SRC=ROOT/'design/bedroom_door_r4/OPTION_A_SLIDING_R4.blend'
OUT=ROOT/'renders/r3_option_a/living_batch_v2_door'
OLD=ROOT/'renders/r3_option_a/living_batch_v1'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
 for p in ['working/cameras','working/prompts','working/previews','exports/clay','exports/ai_outputs','exports/contact_sheets','logs']:(OUT/p).mkdir(parents=True,exist_ok=True)
 m=json.loads((SRC.parent/'R4_OPTION_A_MANIFEST.json').read_text());assert sha(SRC)==m['model_sha256']
 bpy.ops.wm.open_mainfile(filepath=str(SRC));bpy.context.view_layer.update();before={o.name:(list(o.location),list(o.rotation_euler),list(o.scale)) for o in bpy.data.objects}
 cams=json.loads((OLD/'working/cameras/LIVING_CAMERA_REGISTER.json').read_text())
 # Render the affected original reverse/public views, and one direct door view
 # whose physical camera sees the door clearly instead of relying on AI guesses.
 selected=[dict(r) for r in cams if r['id'] in ['A2','A4']]
 selected.append(dict(id='D1',name='次主卧直门与公共区',pos=[6.9,7.10,2.00],target=[8.59,4.61,1.58],lens=28,story='从上层公共区看次主卧入口，视高为上层地坪+.1.55m。门洞东西向，木门为普通门，门框门套和门上墙完整，朝南向卧室内开。北侧卫生间完整西墙在门右侧，严禁把该门画成开放无门通道或恢复成斜门。'))
 col=bpy.data.collections.new('R4_DOOR_CORRECTION_RENDER_CAMERAS');bpy.context.scene.collection.children.link(col)
 mats={}
 for n,c in [('ARCH',(.87,.88,.86,1)),('FLOOR',(.74,.75,.73,1)),('FURN',(.70,.72,.70,1)),('FRAME',(.30,.35,.36,1)),('GLASS',(.84,.90,.92,.16)),('DOOR',(.62,.60,.56,1))]:
  mm=bpy.data.materials.new('R4_CLAY_'+n);mm.diffuse_color=c;mats[n]=mm
 for o in bpy.data.objects:
  if o.type!='MESH':continue
  if any(c.name in ['05_HUMAN_DESIGN_GUIDE','06_FUTURE_DESIGN_OPTIONS'] for c in o.users_collection):o.hide_render=True;continue
  if o.hide_render or o.hide_viewport:continue
  o.data=o.data.copy()
  for i,mm in enumerate(list(o.data.materials)):
   mn=mm.name.upper() if mm else '';name=o.name.upper()
   if name=='R4_BEDROOM_DOOR_LEAF':new=mats['DOOR']
   elif 'GLASS' in mn or 'GLASS' in name:new=mats['GLASS']
   elif 'FRAME' in mn or 'METAL' in mn or any(k in name for k in ['JAMB','MULLION','RAIL','TRACK']):new=mats['FRAME']
   elif name.startswith(('FLOOR_','SITE_GROUND')) or 'UPPER_FLOOR' in name:new=mats['FLOOR']
   elif 'WALL' in mn or 'CEILING' in name or name.startswith(('R3_HOUSE_WALLS','V5_CORNER_PATCH','R4_DOOR_WEST','R4_DOOR_COMPLETE','R4_WEST_PARTITION')):new=mats['ARCH']
   else:new=mats['FURN']
   o.data.materials[i]=new
  if not o.data.materials:o.data.materials.append(mats['ARCH'])
 for r in selected:
  d=bpy.data.cameras.new('R4_CORRECTED_'+r['id']);o=bpy.data.objects.new(d.name,d);col.objects.link(o);o.location=r['pos'];o.rotation_euler=(Vector(r['target'])-o.location).to_track_quat('-Z','Y').to_euler();d.lens=r['lens'];d.sensor_width=36;d.clip_start=.03;d.clip_end=100;r['camera']=o.name;r['clay_path']=str(OUT/'exports/clay'/('living_'+r['id']+'_door_corrected_clay_v2.png'))
 s=bpy.context.scene;s.camera=bpy.data.objects[selected[0]['camera']];s.render.engine='BLENDER_WORKBENCH';s.render.resolution_x=1536;s.render.resolution_y=1024;s.render.resolution_percentage=100;s.render.image_settings.file_format='PNG';s.render.image_settings.color_mode='RGB';s.view_settings.view_transform='Standard';sh=s.display.shading;sh.light='STUDIO';sh.color_type='MATERIAL';sh.show_shadows=False;sh.show_cavity=True;sh.cavity_type='BOTH';s.display.render_aa='32'
 branch=OUT/'working/living_door_corrected_v2.blend';bpy.ops.wm.save_as_mainfile(filepath=str(branch))
 for r in selected:
  s.camera=bpy.data.objects[r['camera']];s.render.filepath=r['clay_path'];bpy.ops.render.render(write_still=True);r['clay_sha256']=sha(r['clay_path'])
 for n,t in before.items():
  o=bpy.data.objects[n];assert t==(list(o.location),list(o.rotation_euler),list(o.scale)),n
 (OUT/'working/cameras/CORRECTED_CAMERA_REGISTER.json').write_text(json.dumps(selected,ensure_ascii=False,indent=2)+'\n')
 (OUT/'logs/SOURCE_PRESERVATION.json').write_text(json.dumps(dict(source=str(SRC),source_sha256=sha(SRC),geometry_source='R4_USER_CORRECTED_EW_INWARD_DOOR',original_geometry_and_pose_unchanged=True,render_branch=str(branch)),ensure_ascii=False,indent=2)+'\n')
 print(json.dumps(dict(clay='PASS',views=[r['id'] for r in selected],door_restored=True)))
if __name__=='__main__':main()
