import bpy,json,hashlib,math
from pathlib import Path
from mathutils import Vector
r=Path(__file__).parent
source=Path('/Users/xiwei/interior_design/projects/c_type_home/design/dining_chairs_r4_review/OPTION_A_R4_DINING_CHAIRS_ALIGNED_REVIEW.blend')
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
assert sha(source)=='e2f3f107eb6619ae28a363e0e4e36019cdae94c89aabe9ac4b8c0c07b14b14ac'
before={str(source):sha(source),str(source.parent.parent/'bedroom_door_r4/OPTION_A_SLIDING_R4.blend'):sha(source.parent.parent/'bedroom_door_r4/OPTION_A_SLIDING_R4.blend')}
bpy.ops.wm.open_mainfile(filepath=str(source))
scene=bpy.context.scene
for o in scene.objects:
 if o.type=='MESH':o.hide_render=not o.visible_get()
# Just inside confirmed R4 entrance opening; all scene edits are in-memory render state only.
position=Vector((3.08,5.99,1.60));target=Vector((7.65,6.70,1.0))
camdata=bpy.data.cameras.new('STUDY_ENTRY_CAMERA');cam=bpy.data.objects.new('STUDY_ENTRY_CAMERA',camdata);scene.collection.objects.link(cam)
cam.location=position;cam.rotation_euler=(target-position).to_track_quat('-Z','Y').to_euler();camdata.lens=21;camdata.clip_start=.03;camdata.clip_end=100;scene.camera=cam
scene.render.engine='BLENDER_WORKBENCH';scene.render.resolution_x=1448;scene.render.resolution_y=1086;scene.render.resolution_percentage=100
scene.display.shading.light='STUDIO';scene.display.shading.studio_light='paint.sl';scene.display.shading.color_type='MATERIAL';scene.display.shading.show_shadows=True;scene.display.shading.show_cavity=True;scene.display.shading.cavity_type='BOTH';scene.display.shading.show_specular_highlight=True;scene.display.shading.background_type='WORLD';scene.world.color=(.8,.8,.8)
scene.render.image_settings.file_format='PNG';scene.render.filepath=str(r/'ENTRY_BASE_MODEL.png');bpy.ops.render.render(write_still=True)
assert all(sha(Path(p))==v for p,v in before.items())
(r/'ENTRY_CAMERA.json').write_text(json.dumps({'status':'READ_ONLY_CAMERA_STUDY','source':str(source),'source_sha256':sha(source),'entry_evidence':'R4 V4_ENT-1_LEAF_0/1 and casing source bounds; jamb X2.9,Y5.44-6.54. Camera just inside opening.','position_m':list(position),'target_m':list(target),'lens_mm':21,'frame':'c_type_world','up':'Z','source_models_unchanged':True,'camera_only_scene_changes_not_saved':True,'baseline_render':'ENTRY_BASE_MODEL.png'},indent=2)+'\n')
print('Entry camera render complete; source unchanged.')
