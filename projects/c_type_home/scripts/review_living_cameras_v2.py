"""Repair only living 03/05; retain approved camera records and immutable design."""
import bpy,json,hashlib,math
from pathlib import Path
from mathutils import Vector
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'renders/whole_house_final_study_v1';M=OUT/'00_MANIFEST';DEST=OUT/'living/camera_review_v2';DEST.mkdir(exist_ok=True,parents=True)
reg=json.loads((M/'CAMERA_REGISTER_V1.json').read_text());original=json.loads(json.dumps(reg));source=Path(reg['source_design']);assert hashlib.sha256(source.read_bytes()).hexdigest()==reg['source_sha256']
bpy.ops.wm.open_mainfile(filepath=reg['render_scene']);scene=bpy.context.scene
changes={'VIEW_03':{'kind':'DEPTH','eye':[3.25,12.6,1.55],'target':[6.3,6.6,1.05],'lens_mm':28,'intent':'From north-window west side toward seating, wave stairs and dining connection'},'VIEW_05':{'kind':'SECONDARY_HERO','eye':[5.3,4.9,1.55],'target':[5.2,10.6,1.05],'lens_mm':28,'intent':'From the lower stair approach toward seating group and north window; east cabinet behind camera is not forced into view'}}
for c in reg['cameras']:
 if c['room_id']=='living' and c['view_id'] in changes:
  c.update(changes[c['view_id']]);v=Vector(c['target'])-Vector(c['eye']);c['shift_y']=max(-.23,min(.23,v.z/math.hypot(v.x,v.y)*c['lens_mm']/36));c['controlled_verticals']=True;c['camera_review_status']='AWAITING_HUMAN_REVIEW'
 else:
  assert c==next(old for old in original['cameras'] if old['camera_name']==c['camera_name'])
checks=[]
for c in reg['cameras']:
 if c['room_id']!='living' or c['view_id'] not in changes:continue
 cam=bpy.data.objects[c['camera_name']];cam.location=c['eye'];v=Vector(c['target'])-cam.location;v.z=0;cam.rotation_euler=v.to_track_quat('-Z','Y').to_euler();cam.data.lens=c['lens_mm'];cam.data.shift_y=c['shift_y'];cam.data.dof.use_dof=False
 bpy.context.view_layer.update();c['quaternion']=list(cam.rotation_euler.to_quaternion());c['matrix_world']=[list(row) for row in cam.matrix_world];c['sensor_width_mm']=cam.data.sensor_width;c['horizontal_fov_deg']=math.degrees(cam.data.angle_x)
 hit,loc,normal,index,obj,matrix=scene.ray_cast(bpy.context.evaluated_depsgraph_get(),Vector(c['eye']),Vector((0,0,-1)),distance=3)
 checks.append({'view_id':c['view_id'],'floor_below_camera':obj.name if hit else None,'floor_z':loc.z if hit else None,'standing_height':c['eye'][2]-loc.z if hit else None,'downward_hit':hit})
reg['render_scene']=str(DEST/'LIVING_CAMERA_REVIEW_V2.blend');reg['revision']='living-camera-review-2';reg['preserved_views']=['VIEW_01','VIEW_02','VIEW_04'];reg['camera_standard']='Original accepted views retained; only 03/05 changed';scene['authority']='PRESENTATION_ONLY_CAMERA_REVIEW'
bpy.ops.wm.save_as_mainfile(filepath=reg['render_scene']);(DEST/'CAMERA_REGISTER.json').write_text(json.dumps(reg,ensure_ascii=False,indent=2));(DEST/'CAMERA_POSITION_CHECK.json').write_text(json.dumps(checks,indent=2))
# Export bounded plan silhouettes from currently visible authoritative/presentation geometry.
shapes=[]
for o in scene.objects:
 if o.type!='MESH' or o.hide_render:continue
 pts=[o.matrix_world@Vector(p) for p in o.bound_box];lo=[min(v[i] for v in pts) for i in range(3)];hi=[max(v[i] for v in pts) for i in range(3)]
 if hi[0]<2.7 or lo[0]>9 or hi[1]<4.4 or lo[1]>14:continue
 if o.name.startswith(('VIEW_WALL','STEP_','B11_Rectangle046','B11_Rectangle048','B11_Rectangle049','L_SOFA')):shapes.append({'name':o.name,'min':lo,'max':hi})
(DEST/'PLAN_BOUNDS.json').write_text(json.dumps({'shapes':shapes,'cameras':[c for c in reg['cameras'] if c['room_id']=='living']},indent=2))
scene.render.engine='BLENDER_WORKBENCH';scene.render.resolution_x=960;scene.render.resolution_y=540;scene.render.resolution_percentage=100;scene.render.threads_mode='FIXED';scene.render.threads=2
scene.display.shading.light='STUDIO';scene.display.shading.studio_light='paint.sl';scene.display.shading.color_type='MATERIAL';scene.display.shading.show_shadows=True;scene.display.shading.show_cavity=True;scene.display.shading.cavity_type='BOTH';scene.display.shading.show_specular_highlight=False
for o in scene.objects:
 if o.type=='MESH' and ('GLASS' in o.name.upper() or o.name.startswith('G_wall_g')):o.hide_render=True
for c in reg['cameras']:
 if c['room_id']=='living' and c['view_id'] in changes:
  if c['view_id']=='VIEW_03' and (DEST/'VIEW_03_preview.png').exists():continue
  scene.camera=bpy.data.objects[c['camera_name']];scene.render.filepath=str(DEST/(c['view_id']+'_preview.png'));bpy.ops.render.render(write_still=True)
assert hashlib.sha256(source.read_bytes()).hexdigest()==reg['source_sha256'];print('CAMERA_REVIEW_V2_RENDERED',checks,flush=True)
