"""One A1 clay reference from the explicitly requested immutable R3 Option A."""
import bpy,json,runpy,hashlib,shutil
from pathlib import Path
from mathutils import Vector
ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'renders/r3_option_a/living_a1_validation_v2';OUT.mkdir(exist_ok=True)
SOURCE=ROOT/'design/secondary_bath_options/r3/OPTION_A_SLIDING_R3.blend'
H=runpy.run_path(str(ROOT/'design/kitchen_frozen_v1/freeze_kitchen.py'),run_name='geometry_helpers')
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
expected=json.loads((SOURCE.parent/'OPTION_A_MANIFEST.json').read_text())['model_sha256'];assert sha(SOURCE)==expected
branch=OUT/'LIVINGROOM_A1_WORKING.blend';assert not branch.exists();shutil.copy2(SOURCE,branch)
bpy.ops.wm.open_mainfile(filepath=str(branch));bpy.context.view_layer.update()
def lock():return {n:{k:v for k,v in r.items() if k in ['type','geometry_sha256','authored_transform','parent','modifiers']} for n,r in H['snapshot']().items()}
before=lock();(OUT/'SOURCE_GEOMETRY_LOCK.json').write_text(json.dumps(before))
def mat(n,c):m=bpy.data.materials.new(n);m.diffuse_color=c;return m
wall=mat('A1_CLAY_ARCH',(.86,.87,.85,1));furn=mat('A1_CLAY_FURN',(.70,.72,.70,1));floor=mat('A1_CLAY_FLOOR',(.74,.75,.73,1));frame=mat('A1_CLAY_FRAME',(.27,.32,.33,1));glass=mat('A1_CLAY_GLASS',(.82,.89,.91,.17))
guides=[]
for o in bpy.data.objects:
 if o.type!='MESH':continue
 if any(c.name in ['05_HUMAN_DESIGN_GUIDE','06_FUTURE_DESIGN_OPTIONS'] for c in o.users_collection):
  if not o.hide_render:guides.append(o.name)
  o.hide_render=True;continue
 if o.hide_render or o.hide_viewport:continue
 o.data=o.data.copy()
 for i,mm in enumerate(list(o.data.materials)):
  mn=mm.name.upper() if mm else '';name=o.name.upper()
  if 'GLASS' in mn or 'GLASS' in name:new=glass
  elif 'FRAME' in mn or 'METAL' in mn or any(x in name for x in ['JAMB','MULLION','RAIL','TRACK']):new=frame
  elif name.startswith(('FLOOR_','SITE_GROUND')):new=floor
  elif 'WALL' in mn or 'CEILING' in name or name.startswith(('R3_HOUSE_WALLS','V5_CORNER_PATCH')):new=wall
  else:new=furn
  o.data.materials[i]=new
col=bpy.data.collections.new('A1_VALIDATION_ONLY');bpy.context.scene.collection.children.link(col)
data=bpy.data.cameras.new('LIVINGROOM_A1');cam=bpy.data.objects.new(data.name,data);col.objects.link(cam)
cam.location=(7.15,8.25,1.55);target=Vector((4.85,11.45,1.20));cam.rotation_euler=(target-cam.location).to_track_quat('-Z','Y').to_euler();data.lens=28;data.sensor_width=36;data.clip_start=.03;data.clip_end=100
after=lock()
for n,r in before.items():assert after[n]==r,n
s=bpy.context.scene;s.camera=cam;s.render.engine='BLENDER_WORKBENCH';s.render.resolution_x=1536;s.render.resolution_y=1024;s.render.resolution_percentage=100;s.render.image_settings.file_format='PNG';s.render.image_settings.color_mode='RGB';s.view_settings.view_transform='Standard';sh=s.display.shading;sh.light='STUDIO';sh.color_type='MATERIAL';sh.show_shadows=False;sh.show_cavity=True;sh.cavity_type='BOTH';s.display.render_aa='32'
bpy.ops.wm.save_as_mainfile(filepath=str(branch));base=OUT/'LIVINGROOM_A1_BASE_REFERENCE.png';s.render.filepath=str(base);bpy.ops.render.render(write_still=True)
# Reopen saved branch to verify the authored geometry lock before AI dispatch.
bpy.ops.wm.open_mainfile(filepath=str(branch));fresh=lock()
for n,r in before.items():assert fresh[n]==r,n
assert sha(SOURCE)==expected
meta=dict(status='CLAY_READY_GEOMETRY_LOCK_PASS',source=str(SOURCE),source_sha256=expected,branch=str(branch),branch_sha256=sha(branch),base=str(base),base_sha256=sha(base),camera=dict(position_m=[7.15,8.25,1.55],target_m=list(target),lens_mm=28,eye_height_m=1.55),source_objects_locked=len(before),resolution=[1536,1024],engine='WORKBENCH',cycles_used=False,source_unchanged=True,nonphysical_guides_excluded=guides,visible_geometry='two independent sofas, coffee table, side cabinet, projecting north bay',behind_camera='bedroom door, leisure platform and split-level stair area not visible',scope='ONLY_A1_THREE_VARIANTS_STOP_FOR_HUMAN_REVIEW')
(OUT/'A1_SOURCE_AND_CAMERA_MANIFEST.json').write_text(json.dumps(meta,ensure_ascii=False,indent=2)+'\n')
print(json.dumps(dict(clay='PASS',camera='A1_ONLY',source_objects_locked=len(before),base=str(base)),ensure_ascii=False))
