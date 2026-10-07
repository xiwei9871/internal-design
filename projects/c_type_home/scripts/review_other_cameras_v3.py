"""Review and repair only obviously repetitive/empty non-living camera candidates."""
import bpy,json,hashlib,math
from pathlib import Path
from mathutils import Vector
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'renders/whole_house_final_study_v1';M=OUT/'00_MANIFEST';DEST=OUT/'camera_review_v3';DEST.mkdir(exist_ok=True,parents=True)
reg=json.loads((M/'CAMERA_REGISTER_V1.json').read_text());original=json.loads(json.dumps(reg));source=Path(reg['source_design']);assert hashlib.sha256(source.read_bytes()).hexdigest()==reg['source_sha256']
bpy.ops.wm.open_mainfile(filepath=reg['render_scene']);scene=bpy.context.scene
# Only views that were visibly repetitive or too close in the existing contact sheets.
changes={
 ('dining','VIEW_01'):{'eye':[5.3, 4.25, 1.55],'target':[3.65, 3.4, 1.05],'lens_mm':22,'intent':'Dining group from clear kitchen-side circulation; avoid foreground door mullion'},
 ('dining','VIEW_05'):{'eye':[5.15,2.65,1.55],'target':[3.85,3.65,1.05],'lens_mm':22,'intent':'Dining, storage and passage toward living'},
 ('dining','VIEW_03'):{'eye':[5.35,3.05,1.55],'target':[3.55,3.55,0.95],'lens_mm':24,'intent':'Dining reverse: table, living opening and kitchen edge'},
 ('service_balcony','VIEW_03'):{'eye':[2.05,1.35,1.55],'target':[4.95,1.40,1.05],'lens_mm':22,'intent':'Service strip toward kitchen: utility tall cabinet, glazing and working aisle'},
 ('service_balcony','VIEW_05'):{'eye':[5.35,1.45,1.45],'target':[2.25,1.40,1.0],'lens_mm':22,'intent':'Reverse service run: glazing, worktop and appliance zone'},
 ('entry','VIEW_03'):{'eye':[3.75, 5.25, 1.55],'target':[5.8, 7.2, 1.0],'lens_mm':24,'intent':'Entry toward living, stairs and circulation from a clear floor position'},
 ('entry','VIEW_05'):{'eye':[3.2, 5.8, 1.55],'target':[5.8, 10.8, 1.1],'lens_mm':25,'intent':'Entry-to-living depth with furnishings beyond threshold'},
 ('hallway','VIEW_03'):{'eye':[10.25,7.15,2.0],'target':[12.75,7.15,1.5],'lens_mm':28,'intent':'Full hallway axis and door sequence'},
 ('hallway','VIEW_05'):{'eye':[10.55,7.15,2.0],'target':[8.45,7.15,1.5],'lens_mm':28,'intent':'Reverse hallway axis toward stairs and living'},
 ('mother_bedroom','VIEW_03'):{'eye':[12.65, 0.7, 2],'target':[14.3, 3.65, 1.5],'lens_mm':24,'intent':'Bed-side passage toward full wardrobe and bedroom entrance'},
 ('mother_bedroom','VIEW_05'):{'eye':[13.4, 0.7, 1.95],'target':[11.95, 0.9, 1.25],'lens_mm':24,'intent':'Vanity and adjacent console instead of a mirror-only crop'},
 ('couple_bedroom','VIEW_03'):{'eye':[8.75, 0.75, 2],'target':[9.8, 4.35, 1.5],'lens_mm':24,'intent':'Wardrobe, bathroom opening and bed-side clearance'},
 ('couple_bedroom','VIEW_05'):{'eye':[8.85,0.55,1.95],'target':[10.45,2.8,1.2],'lens_mm':28,'intent':'Reverse couple bedroom: bed and window/door relationship'},

 ('kitchen','VIEW_03'):{'eye':[6.55,2.95,1.55],'target':[7.1,1.05,1.25],'lens_mm':24,'intent':'Kitchen depth and island/working aisle, rather than duplicate cooktop crop'},
 ('study','VIEW_04'):{'eye':[13.5,9.8,2.0],'target':[14.7,10.95,1.35],'lens_mm':24,'intent':'Full daybed and storage drawers in window context'},
 ('guest_bedroom','VIEW_02'):{'eye':[11.3, 9.55, 2],'target':[10.25, 10.35, 1.65],'lens_mm':22,'intent':'Wardrobe with sunroom threshold and nearby bed/entry context'},
 ('guest_bedroom','VIEW_05'):{'eye':[10.65,9.4,2.0],'target':[12.15,8.7,1.3],'lens_mm':24,'intent':'Complete single-bed and headboard/desk relationship'},
 ('master_bath','VIEW_02'):{'eye':[15.85,5.55,1.9],'target':[14.1,5.9,1.45],'lens_mm':22,'intent':'Dry/wet separation, toilet and vanity from shower side'},
 ('master_bath','VIEW_04'):{'eye':[15.75,5.25,1.85],'target':[13.8,5.95,1.3],'lens_mm':20,'intent':'From shower side toward vanity, toilet and glass partition'},
 ('master_bath','VIEW_05'):{'eye':[14.75,5.15,1.9],'target':[13.7,6.15,1.65],'lens_mm':24,'intent':'Mirror/storage plus full countertop context'},
 ('secondary_bath','VIEW_02'):{'eye':[11.0,6.13,1.9],'target':[9.8,5.15,1.45],'lens_mm':20,'intent':'Wet area toward vanity and bedroom entry'},
 ('secondary_bath','VIEW_05'):{'eye':[10.6,5.2,1.9],'target':[9.75,6.2,1.65],'lens_mm':22,'intent':'Round mirror and open storage with countertop context'},
 ('guest_bath','VIEW_04'):{'eye':[9.22,10.50,1.9],'target':[8.75,8.6,1.35],'lens_mm':22,'intent':'Shower threshold toward toilet, vanity and entry'},
 ('guest_bath','VIEW_05'):{'eye':[9.38,9.3,1.9],'target':[8.3,8.95,1.65],'lens_mm':24,'intent':'Vanity/mirror/storage as a coherent group'},
 ('north_sunroom','VIEW_03'):{'eye':[8.35,12.7,1.55],'target':[10.05,11.55,1.1],'lens_mm':24,'intent':'Sunroom sofa, freezer/storage and guest-room opening across aisle'},
 ('north_sunroom','VIEW_05'):{'eye':[10.6,12.8,1.55],'target':[12.3,12.05,0.95],'lens_mm':24,'intent':'Freezer, cabinet, worktop and guest-room opening relationship'},
}
for c in reg['cameras']:
 key=(c['room_id'],c['view_id'])
 if key in changes:
  old={k:c.get(k) for k in ['eye','target','lens_mm','kind']};c.update(changes[key]);v=Vector(c['target'])-Vector(c['eye']);c['shift_y']=max(-.23,min(.23,v.z/math.hypot(v.x,v.y)*c['lens_mm']/36));c['controlled_verticals']=True;c['camera_review_status']='AWAITING_HUMAN_REVIEW';c['previous_candidate']=old
 else:
  assert c==next(x for x in original['cameras'] if x['camera_name']==c['camera_name']),key
living=json.loads((OUT/'living/camera_review_v2/CAMERA_REGISTER.json').read_text())
for i,c in enumerate(reg['cameras']):
 if c['room_id']=='living':reg['cameras'][i]=next(x for x in living['cameras'] if x['camera_name']==c['camera_name'])
checks=[]
for c in reg['cameras']:
 if (c['room_id'],c['view_id']) not in changes:continue
 cam=bpy.data.objects[c['camera_name']];cam.location=c['eye'];v=Vector(c['target'])-cam.location;v.z=0;cam.rotation_euler=v.to_track_quat('-Z','Y').to_euler();cam.data.lens=c['lens_mm'];cam.data.shift_y=c['shift_y'];cam.data.dof.use_dof=False;bpy.context.view_layer.update()
 # A vertical ray must hit a presentation/source floor below the camera.
 deps=bpy.context.evaluated_depsgraph_get();hit,loc,normal,index,obj,matrix=scene.ray_cast(deps,Vector(c['eye']),Vector((0,0,-1)),distance=5)
 checks.append({'room_id':c['room_id'],'view_id':c['view_id'],'floor_hit':hit,'floor_object':obj.name if hit else None,'floor_z':loc.z if hit else None,'standing_height':c['eye'][2]-loc.z if hit else None,'eye':c['eye'],'target':c['target']})
 c['quaternion']=list(cam.rotation_euler.to_quaternion());c['sensor_width_mm']=cam.data.sensor_width;c['horizontal_fov_deg']=math.degrees(cam.data.angle_x)
hidden_glass=[]
for o in scene.objects:
 if o.type=='MESH' and ('GLASS' in o.name.upper() or o.name.startswith('G_wall_g')):hidden_glass.append((o,o.hide_render));o.hide_render=True
scene.render.engine='BLENDER_WORKBENCH';scene.render.resolution_x=960;scene.render.resolution_y=540;scene.render.resolution_percentage=100;scene.render.threads=2;scene.render.threads_mode='FIXED';scene.display.shading.light='STUDIO';scene.display.shading.studio_light='paint.sl';scene.display.shading.color_type='MATERIAL';scene.display.shading.show_shadows=True;scene.display.shading.show_cavity=True;scene.display.shading.cavity_type='BOTH';scene.display.shading.show_specular_highlight=False
for c in reg['cameras']:
 key=(c['room_id'],c['view_id'])
 if key in changes:
  scene.camera=bpy.data.objects[c['camera_name']];path=DEST/f'{c["room_id"]}_{c["view_id"]}_preview.png';scene.render.filepath=str(path)
  if key in {('master_bath', 'VIEW_04')} or not path.exists():bpy.ops.render.render(write_still=True)
reg['render_scene']=str(DEST/'WHOLE_HOUSE_CAMERA_REVIEW_V3.blend');reg['revision']='whole-house-camera-review-3';reg['camera_review_lessons']='render_config/CAMERA_REVIEW_LESSONS_V1.md';reg['changed_views']=[{'room_id':r,'view_id':v,'intent':x['intent']} for (r,v),x in changes.items()]
for o,previous in hidden_glass:o.hide_render=previous
for c in reg['cameras']:
 cam=bpy.data.objects[c['camera_name']];cam.location=c['eye'];v=Vector(c['target'])-cam.location
 if c.get('controlled_verticals'):v.z=0
 cam.rotation_euler=v.to_track_quat('-Z','Y').to_euler();cam.data.lens=c['lens_mm'];cam.data.shift_y=c.get('shift_y',0)
 bpy.context.view_layer.update();c['matrix_world']=[list(row) for row in cam.matrix_world]
scene['authority']='PRESENTATION_ONLY_CAMERA_REVIEW';scene['source_design_sha256']=reg['source_sha256'];bpy.ops.wm.save_as_mainfile(filepath=reg['render_scene'])
(M/'CAMERA_REGISTER_REVIEW_V3.json').write_text(json.dumps(reg,ensure_ascii=False,indent=2));(DEST/'CAMERA_POSITION_CHECK.json').write_text(json.dumps(checks,ensure_ascii=False,indent=2));(DEST/'CHANGED_VIEWS.json').write_text(json.dumps(reg['changed_views'],ensure_ascii=False,indent=2))
assert hashlib.sha256(source.read_bytes()).hexdigest()==reg['source_sha256']
print('WHOLE_HOUSE_CAMERA_REVIEW_V3',len(changes),checks,flush=True)
