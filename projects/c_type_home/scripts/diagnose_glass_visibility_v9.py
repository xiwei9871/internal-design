"""Read-only controlled tests separating glass transport from environment/viewport causes."""
import bpy,json,time,hashlib,math
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
R=Path(__file__).resolve().parents[1];D=R/'design/glass_visibility_v9';D.mkdir(exist_ok=True)
S=R/'design/glass_privacy_v8/WHOLE_HOUSE_GLASS_PRIVACY_DELIVERY_V8.blend'
assert hashlib.sha256(S.read_bytes()).hexdigest()=='e9b3e3d4766f161e2b7f6450475c8d0f8af4c59469709747356ad7f744e58928'
bpy.ops.wm.open_mainfile(filepath=str(S));s=bpy.context.scene;w=s.world;report={'source':str(S),'source_sha256':hashlib.sha256(S.read_bytes()).hexdigest(),'world':{'name':w.name,'nodes':[],'links':[]},'cycles':{},'eevee':{},'viewport':[],'front_glass':[]}
for n in w.node_tree.nodes:
 report['world']['nodes'].append({'name':n.name,'type':n.type,'image':n.image.filepath if n.type=='TEX_ENVIRONMENT' and n.image else None,'inputs':{i.name:str(i.default_value) for i in n.inputs if hasattr(i,'default_value')}})
report['world']['links']=[(l.from_node.name,l.from_socket.name,l.to_node.name,l.to_socket.name) for l in w.node_tree.links]
for k in ['max_bounces','transmission_bounces','glossy_bounces','transparent_max_bounces','use_fast_gi','caustics_reflective','caustics_refractive']:
 if hasattr(s.cycles,k):report['cycles'][k]=getattr(s.cycles,k)
if hasattr(s,'eevee'):
 for k in ['use_raytracing','ray_tracing_method','use_fast_gi']:
  if hasattr(s.eevee,k):report['eevee'][k]=getattr(s.eevee,k)
for screen in bpy.data.screens:
 for area in screen.areas:
  if area.type=='VIEW_3D':
   sh=area.spaces.active.shading;report['viewport'].append({k:getattr(sh,k) for k in ['type','studio_light','use_scene_world','use_scene_lights','use_scene_world_render','use_scene_lights_render'] if hasattr(sh,k)})
for col in bpy.data.collections:col.hide_viewport=False
for o in bpy.data.objects:o.hide_viewport=False;o.hide_set(False)
bpy.context.view_layer.update()
for o in s.objects:
 if o.type=='MESH' and not o.hide_render and o.name.startswith('LIVING_FIX_BAY_') and 'GLASS' in o.name:
  e=o.evaluated_get(bpy.context.evaluated_depsgraph_get());me=e.to_mesh();vs=[e.matrix_world@v.co for v in me.vertices];lo=[min(v[i] for v in vs) for i in range(3)];hi=[max(v[i] for v in vs) for i in range(3)]
  faces=[list(f.vertices) for f in me.polygons];edgecounts={}
  for f in faces:
   for a,b in zip(f,f[1:]+f[:1]):k=tuple(sorted((a,b)));edgecounts[k]=edgecounts.get(k,0)+1
  report['front_glass'].append({'name':o.name,'bounds_m':[lo,hi],'triangles':len(me.polygons),'materials':[m.name for m in me.materials if m],'scale':list(o.scale),'boundary_edges':sum(v==1 for v in edgecounts.values()),'normal_sample':[list(f.normal) for f in list(me.polygons)[:8]]})
  e.to_mesh_clear()
# Window center ray from indoor to outdoors: report every intersected visible surface.
origin=Vector((5.35,12.6,1.5));direction=Vector((0,1,0));rayhits=[]
for o in s.objects:
 if o.type!='MESH' or o.hide_render:continue
 e=o.evaluated_get(bpy.context.evaluated_depsgraph_get());me=e.to_mesh();vs=[e.matrix_world@v.co for v in me.vertices];fs=[list(f.vertices) for f in me.polygons];e.to_mesh_clear()
 if not fs:continue
 bvh=BVHTree.FromPolygons(vs,fs);hit=bvh.ray_cast(origin,direction,10)
 if hit[0] is not None:rayhits.append({'name':o.name,'distance_m':hit[3],'location_m':list(hit[0])})
report['window_center_ray']=sorted(rayhits,key=lambda v:v['distance_m'])
(D/'DIAGNOSIS.json').write_text(json.dumps(report,indent=2)+'\n');print('GLASS_DIAG',json.dumps({k:report[k] for k in ['cycles','eevee','viewport','window_center_ray']}),flush=True)
# Fixed render controls. Keep lights and cameras; baseline and no-glass first.
for layer in s.view_layers:layer.use=layer.name=='INTERIOR_CLOSED_CEILING'
bpy.context.window.view_layer=s.view_layers['INTERIOR_CLOSED_CEILING'];s.render.engine='CYCLES';s.render.resolution_x=1200;s.render.resolution_y=675;s.render.resolution_percentage=100;s.render.threads_mode='FIXED';s.render.threads=2;s.cycles.samples=48;s.cycles.adaptive_threshold=.035;s.cycles.use_denoising=True;s.cycles.denoising_use_gpu=True;s.render.image_settings.file_format='PNG'
pref=bpy.context.preferences.addons['cycles'].preferences;pref.compute_device_type='METAL';pref.get_devices()
for d in pref.devices:d.use=d.type=='METAL'
s.cycles.device='GPU';s.camera=bpy.data.objects['CAM_living_VIEW_01']
glasses=[o for o in s.objects if o.type=='MESH' and not o.hide_render and any(m and m.name=='V8_COLORLESS_CLEAR_ARCHITECTURAL_GLASS' for m in o.data.materials)]
for name,hide in [('baseline',False),('no_clear_glass',True)]:
 for o in glasses:o.hide_render=hide
 f=D/(name+'.png');assert not f.exists();s.render.filepath=str(f);bpy.ops.render.render(write_still=True);print('CONTROL_SHOT',name,flush=True)
