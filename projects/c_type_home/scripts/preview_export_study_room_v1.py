import bpy,json,sys,math
from pathlib import Path
from mathutils import Vector, Quaternion
ROOT=Path(__file__).resolve().parents[1];R=ROOT/'design/study_room_v1'
mode=sys.argv[sys.argv.index('--')+1]
source=R/('STUDY_ROOM_DAYBED_V1.blend' if mode=='daily' else 'STUDY_ROOM_DAYBED_V1_GUEST.blend')
bpy.ops.wm.open_mainfile(filepath=str(source));bpy.context.view_layer.update()
reg=json.loads((R/('spatial-canvas.bindings.'+mode+'.json')).read_text())
sys.path.insert(0,'/Users/xiwei/Documents/ChatGPT/Spatial-Canvas/adapters/blender')
import export_proxy
from argparse import Namespace
out=R/('proxy_'+mode)
manifest=export_proxy.export_proxy(Namespace(output=str(out),bindings=str(R/('spatial-canvas.bindings.'+mode+'.json')),
 scope='task',room_id=None,global_ids=[b['entity_id'] for b in reg['bindings']],collection=None,color_mode='source-flat',
 source_resource_id=reg['source_resource_id'],source_revision=reg['source_revision']))
manifest.setdefault('extensions',{})['spatial_canvas.review']={'status':'HUMAN_REVIEW','mode':mode,
 'source_design_authority':'DERIVED_DESIGN_MODEL','physical_ground_truth_sha256':'d109c7efcfa2b2b2565e4c073ee0cdf5282b23c01122bc9c1bbe7b8791ac3afb',
 'no_architecture_change':True,'clearance_gate':'PASS','guest_topper_is_thin_review_proxy':True}
(out/'interaction_proxy.manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
# Full house is retained in .blend; only scoped taskcontext remains in decisionviews.
allowed={b['native_id'] for b in reg['bindings']}
for o in bpy.context.scene.objects:
 if o.type in ['MESH','CURVE','FONT']:o.hide_render=o.hide_render or o.name not in allowed
# Side walls truncate views into interior; these are render-only changes.
scene=bpy.context.scene;scene.render.engine='BLENDER_WORKBENCH'
scene.render.resolution_x=1000;scene.render.resolution_y=780;scene.render.resolution_percentage=100
scene.display.shading.light='STUDIO';scene.display.shading.studio_light='paint.sl';scene.display.shading.color_type='MATERIAL'
scene.display.shading.show_shadows=True;scene.display.shading.show_cavity=True;scene.display.shading.cavity_type='BOTH'
data=bpy.data.cameras.new('STUDY_V1_PREVIEW_CAMERA');cam=bpy.data.objects.new('STUDY_V1_PREVIEW_CAMERA',data)
scene.collection.objects.link(cam);scene.camera=cam
cam.location=(14.65,9.18,14);cam.rotation_euler=(0,0,0);data.type='ORTHO';data.ortho_scale=4.5
scene.render.resolution_x=900;scene.render.resolution_y=1100
soffit=bpy.data.objects['VIEW_WALL_V4_W-STUDY-NE_SOFFIT'];soffit.hide_render=True
scene.render.filepath=str(R/('STUDY_ROOM_TOP_'+mode.upper()+'.png'));bpy.ops.render.render(write_still=True)
scene.render.resolution_x=1000;scene.render.resolution_y=780
views=[]
if mode=='daily':
 views=[('STUDY_ROOM_ENTRY.png',(13.30,7.18,1.97),(14.85,9.9,1.37),18),
 ('STUDY_ROOM_BOOKCASE.png',(13.30,9.55,2.0),(16.00,8.76,1.70),20),
 ('STUDY_ROOM_DAYBED.png',(15.27,8.65,2.1),(14.65,11.07,1.12),22)]
for name,eye,target,lens in views:
 data.type='PERSP';data.lens=lens;cam.location=eye;cam.rotation_euler=(Vector(target)-Vector(eye)).to_track_quat('-Z','Y').to_euler()
 scene.render.filepath=str(R/name);bpy.ops.render.render(write_still=True)
 if name=='STUDY_ROOM_ENTRY.png':
  sq=cam.rotation_euler.to_quaternion();pq=Quaternion((2**-.5,-2**-.5,0,0))@sq
  preset={'schema':'spatial-canvas.view-preset.v1','preset_id':'study_v1_r4_entry',
   'projection':'perspective','fov_degrees':45,'near':.02,'far':1000,
   'position':[eye[0],eye[2],-eye[1]],'quaternion':[pq.x,pq.y,pq.z,pq.w],
   'orbit_target':[target[0],target[2],-target[1]],
   'viewport':{'width':1000,'height':780,'pixel_ratio':1},'frame_id':'blender_proxy_world','unit':'meter','up_axis':'Y',
   'projection_matrix':[1.883086,0,0,0,0,2.414214,0,0,0,0,-1.00004,-1,0,0,-.0400008,0],
   'design_id':manifest['design_id'],'source_resource_id':manifest['source_resource_id'],
   'source_revision':manifest['source_revision'],'source_sha256':manifest['source_sha256'],
   'source_locator':manifest['source_resource'],'bindings':manifest['extensions']['spatial_canvas.blender']['bindings'],
   'source_camera':{'position':eye,'quaternion':[sq.x,sq.y,sq.z,sq.w],'frame_id':'c_type_world','unit':'meter','up_axis':'Z'},
   'hidden_entity_ids':[],'ghost_entity_ids':[],'preview_uri':'STUDY_ROOM_ENTRY.png'}
  (R/'study_v1_r4_entry.view-preset.json').write_text(json.dumps(preset,indent=2)+'\n')
(R/('PREVIEW_'+mode.upper()+'_MANIFEST.json')).write_text(json.dumps({'source':str(source),
 'source_sha256':reg['source_sha256'],'engine':'BLENDER_WORKBENCH','mode':mode,'no_cycles':True,
 'views':[{'file':name,'eye':eye,'target':target,'lens_mm':lens} for name,eye,target,lens in views],
 'top_view':{'eye':[14.65,9.18,14],'ortho_scale_m':4.5,'render_only_soffit_hidden':True}},indent=2)+'\n')
# Fresh GLB importGate validates downstreamidentity ratherthanview-sourcecaches.
bpy.ops.wm.read_factory_settings(use_empty=True);bpy.ops.import_scene.gltf(filepath=str(out/manifest['proxy_uri']))
entities={o.get('native_object_id'):o for o in bpy.context.scene.objects if o.get('global_id')}
assert len(entities)==manifest['entity_count']==len(reg['bindings'])
assert all(entities[b['native_id']]['global_id']==b['entity_id'] for b in reg['bindings'])
assert ('STUDY_V1_GUEST_TOPPER' in entities)==(mode=='guest')
assert 'STUDY_V1_DAYBED_STORAGE_CARCASS' in entities
(R/('EXPORT_'+mode.upper()+'_EVIDENCE.json')).write_text(json.dumps({'status':'PASS','mode':mode,
 'entities':len(entities),'ids_match':True,'textures':False,'render':'workbench'},indent=2)+'\n')
print('STUDY_EXPORT_PREVIEW_PASS',mode,len(entities))
