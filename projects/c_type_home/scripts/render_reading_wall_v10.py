"""Before/after wall placement and actual floor cross-section checks."""
import bpy,json
from pathlib import Path
from mathutils import Vector,Quaternion
from mathutils.bvhtree import BVHTree
R=Path(__file__).resolve().parents[1];D=R/'design/reading_wall_v10';a=json.loads((D/'BUILD_AUDIT.json').read_text());O=D/'review';O.mkdir(exist_ok=True)
def setup(src):
 bpy.ops.wm.open_mainfile(filepath=src);s=bpy.context.scene
 for layer in s.view_layers:layer.use=layer.name=='INTERIOR_CLOSED_CEILING'
 bpy.context.window.view_layer=s.view_layers['INTERIOR_CLOSED_CEILING'];s.render.engine='CYCLES';s.render.resolution_x=1600;s.render.resolution_y=900;s.render.resolution_percentage=100;s.render.threads_mode='FIXED';s.render.threads=2;s.cycles.samples=96;s.cycles.adaptive_threshold=.02;s.cycles.use_denoising=True;s.cycles.denoising_use_gpu=True;s.cycles.denoising_quality='HIGH';s.cycles.denoising_prefilter='ACCURATE';s.render.image_settings.file_format='PNG'
 p=bpy.context.preferences.addons['cycles'].preferences;p.compute_device_type='METAL';p.get_devices()
 for dev in p.devices:dev.use=dev.type=='METAL'
 s.cycles.device='GPU';return s
for label,src in [('before',a['source']),('after',a['output'])]:
 s=setup(src);cam=bpy.data.objects.new('READING_V10_WALL_CAMERA',bpy.data.cameras.new('READING_V10_WALL_CAMERA'));s.collection.objects.link(cam);cam.location=(7.3,6.2,2.05);cam.rotation_euler=(Vector((9.02,5.3,1.62))-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.lens=30;cam.data.clip_start=.01;s.camera=cam;dest=O/(label+'.png');assert not dest.exists();s.render.filepath=str(dest);bpy.ops.render.render(write_still=True);print('READING_VIEW',label,flush=True)
# Reproduce owner's exact overhead camera as a geometry placement check.
packet=json.loads((D/'OWNER_TARGET_PACKET.json').read_text());v=packet['view']['data'];q=Quaternion((v['quaternion'][3],*v['quaternion'][:3]));basis=Quaternion((2**-.5,2**-.5,0,0))
cam.location=(v['position'][0],-v['position'][2],v['position'][1]);cam.rotation_euler=(basis@q).to_euler();cam.data.type='PERSP';cam.data.lens=50;cam.data.sensor_fit='VERTICAL';cam.data.sensor_height=2*50*__import__('math').tan(__import__('math').radians(v['fov_degrees'])/2)
s.render.resolution_x=1000;s.render.resolution_y=1015;s.render.engine='BLENDER_WORKBENCH';s.display.shading.light='STUDIO';s.display.shading.color_type='MATERIAL';s.display.shading.show_cavity=True;s.display.shading.cavity_type='BOTH';s.world.color=(.15,.15,.15);s.view_settings.view_transform='Standard';s.view_settings.look='None'
for n in ['V7_CEILING_LOW','V7_CEILING_HIGH','V7_CEILING_450MM_TRANSITION']:bpy.data.objects[n].hide_render=True
s.render.filepath=str(O/'owner_view_after.png');assert not Path(s.render.filepath).exists();bpy.ops.render.render(write_still=True)
# Cross sections of actual top-step mesh, rather than its broad AABB.
shelf_front=a['cabinet_bounds_m'][0][0];step=bpy.data.objects['STEP_2'];e=step.evaluated_get(bpy.context.evaluated_depsgraph_get());me=e.to_mesh();verts=[e.matrix_world@p.co for p in me.vertices];tris=[list(f.vertices) for f in me.polygons];e.to_mesh_clear();tree=BVHTree.FromPolygons(verts,tris);rows=[]
for y in [4.89,5.05,5.30,5.50,5.71]:
 hit=tree.ray_cast(Vector((9.04,y,.449)),Vector((-1,0,0)),4)
 rows.append({'y_m':y,'top_step_outer_x_m':hit[0].x if hit[0] else None,'cabinet_to_actual_step_horizontal_gap_mm':(shelf_front-hit[0].x)*1000 if hit[0] else None})
(D/'CIRCULATION_SECTIONS.json').write_text(json.dumps({'sections':rows,'note':'Horizontal section of top step at z449mm; not a person-motion/safety certification'},indent=2)+'\n');print('SECTIONS',json.dumps(rows))
