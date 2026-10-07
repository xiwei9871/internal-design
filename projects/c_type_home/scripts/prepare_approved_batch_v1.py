"""Apply a reproducible presentation contract to approved cameras, without source changes."""
import bpy,json,math,hashlib,struct
from pathlib import Path
from mathutils import Vector
ROOT=Path(__file__).resolve().parents[1];OLD=ROOT/'renders/whole_house_final_study_v1';OUT=OLD/'production_batch_v1';OUT.mkdir(exist_ok=True);M=OUT/'00_MANIFEST';M.mkdir(exist_ok=True)
reg=json.loads((OLD/'00_MANIFEST/CAMERA_REGISTER_REVIEW_V3.json').read_text());std=json.loads((ROOT/'render_config/WHOLE_HOUSE_RENDER_STANDARD_V1.json').read_text());src=Path(reg['source_design']);assert hashlib.sha256(src.read_bytes()).hexdigest()==reg['source_sha256']
bpy.ops.wm.open_mainfile(filepath=reg['render_scene']);s=bpy.context.scene
fingerprints={o.name:(list(float(v) for row in o.matrix_world for v in row),[tuple(v.co) for v in o.data.vertices]) for o in s.objects if o.type=='MESH'}
def rgb_temp(k):
 # Standard approximate Planckian CCT converted from sRGB to scene-linear RGB.
 t=k/100;red=255 if t<=66 else 329.698727446*(t-60)**-.1332047592;green=99.4708025861*math.log(t)-161.1195681661 if t<=66 else 288.1221695283*(t-60)**-.0755148492;blue=255 if t>=66 else 0 if t<=19 else 138.5177312231*math.log(t-10)-305.0447927307
 def lin(x):
  x=max(0,min(255,x))/255;return x/12.92 if x<=.04045 else ((x+.055)/1.055)**2.4
 return tuple(lin(x) for x in (red,green,blue))
for o in s.objects:
 if o.type=='LIGHT' and not o.hide_render:
  if o.name.startswith('LIGHT_'):o.data.energy*=std['lighting']['ambient_fraction'];o.data.color=(1,.80,.61);o['cct_kelvin']=2900
  elif o.name.startswith('DAYLIGHT_'):o.data.energy*=std['lighting']['daylight_area_fraction'];o.data.color=(.86,.92,1);o['cct_kelvin']=6000
  o.visible_camera=False;o.visible_transmission=False;o.visible_glossy=False
sun=bpy.data.lights.new('RENDER_SUN_AFternoon_5500K','SUN');sun.energy=std['lighting']['sun']['energy'];sun.angle=math.radians(5);sun.color=rgb_temp(5500);o=bpy.data.objects.new(sun.name,sun);s.collection.objects.link(o)
az=math.radians(225);el=math.radians(35);toward=Vector((math.sin(az)*math.cos(el),math.cos(az)*math.cos(el),math.sin(el)));o.rotation_euler=(-toward).to_track_quat('-Z','Y').to_euler();o['cct_kelvin']=5500
for n in s.world.node_tree.nodes:
 if n.type=='BACKGROUND' and n.name=='Background':n.inputs['Strength'].default_value=.45
for m in bpy.data.materials:
 if not m.use_nodes:continue
 bs=m.node_tree.nodes.get('Principled BSDF')
 if not bs:continue
 n=m.name
 rough=.5 if 'TILE' in n else .8 if 'OFF_WHITE' in n else .42 if 'STONE' in n else .55 if 'ASH' in n or 'WOOD_FLOOR' in n else .78 if 'LINEN' in n else None
 if rough is not None:
  inp=bs.inputs['Roughness']
  for link in list(inp.links):m.node_tree.links.remove(link)
  inp.default_value=rough
s.render.engine='CYCLES';s.render.resolution_x=1920;s.render.resolution_y=1080;s.render.resolution_percentage=100;s.render.image_settings.file_format='PNG';s.render.image_settings.color_mode='RGB';s.render.image_settings.color_depth='8';s.render.threads_mode='FIXED';s.render.threads=2;s.cycles.samples=256;s.cycles.adaptive_threshold=.01;s.cycles.max_bounces=8;s.cycles.diffuse_bounces=4;s.cycles.transmission_bounces=6;s.cycles.sample_clamp_indirect=3;s.cycles.use_denoising=True;s.cycles.denoiser='OPENIMAGEDENOISE'
s.view_settings.view_transform='AgX';s.view_settings.look='AgX - Medium High Contrast';s.view_settings.exposure=.5;s.view_settings.gamma=1;s.view_settings.use_white_balance=True;s.view_settings.white_balance_temperature=5200;s.view_settings.white_balance_tint=0
prefs=bpy.context.preferences.addons['cycles'].preferences;prefs.compute_device_type='METAL';prefs.get_devices()
for d in prefs.devices:d.use=d.type=='METAL'
s.cycles.device='GPU'
for c in reg['cameras']:
 cam=bpy.data.objects[c['camera_name']];cam.location=c['eye'];v=Vector(c['target'])-cam.location
 if c.get('controlled_verticals'):v.z=0
 cam.rotation_euler=v.to_track_quat('-Z','Y').to_euler();cam.data.lens=c['lens_mm'];cam.data.sensor_width=36;cam.data.shift_y=c.get('shift_y',0);cam.data.dof.use_dof=False;bpy.context.view_layer.update();c['matrix_world']=[list(row) for row in cam.matrix_world];c['quaternion']=list(cam.rotation_euler.to_quaternion());c['sensor_width_mm']=36;c['source_revision']='console400-three-bath-mirrors-review-1';c['approval_status']='USER_APPROVED';c['exposure_ev']=.5
for n,(matrix,verts) in fingerprints.items():
 obj=bpy.data.objects[n];assert matrix==list(float(v) for row in obj.matrix_world for v in row) and verts==[tuple(v.co) for v in obj.data.vertices],n
s['authority']='PRESENTATION';s['source_sha256']=reg['source_sha256'];s['render_standard_id']=std['standard_id'];reg['render_scene']=str(OUT/'WHOLE_HOUSE_PRODUCTION_V1.blend');bpy.ops.file.pack_all();bpy.ops.wm.save_as_mainfile(filepath=reg['render_scene']);(M/'CAMERA_REGISTER.json').write_text(json.dumps(reg,ensure_ascii=False,indent=2));(M/'RENDER_STANDARD.json').write_text(json.dumps(std,ensure_ascii=False,indent=2));(M/'GEOMETRY_FIDELITY.json').write_text(json.dumps({'all_mesh_vertices_and_transforms_unchanged':True,'mesh_count':len(fingerprints),'source_sha256':reg['source_sha256']},indent=2))
assert hashlib.sha256(src.read_bytes()).hexdigest()==reg['source_sha256'];print('PRODUCTION_PREPARED',reg['render_scene'],flush=True)
