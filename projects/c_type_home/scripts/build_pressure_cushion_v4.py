"""Closed, sewn-edge cloth pressure form study following Blender official method."""
import bpy,math,json,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'design/product_rebuild_v4';CACHE=OUT/'pressure_cache';CACHE.mkdir(exist_ok=True)
bpy.ops.wm.read_factory_settings(use_empty=True);scene=bpy.context.scene;scene.unit_settings.system='METRIC';scene.gravity=(0,0,0)
N=28;W=.92;D=.76;T=.035
verts=[];faces=[]
for layer in [0,1]:
 for j in range(N+1):
  for i in range(N+1):
   x=W*(i/N-.5);y=D*(j/N-.5);z=(T/2 if layer else -T/2)
   verts.append((x,y,z))
stride=(N+1)*(N+1)
for layer in [0,1]:
 for j in range(N):
  for i in range(N):
   a=layer*stride+j*(N+1)+i;f=(a,a+1,a+N+2,a+N+1);faces.append(f if layer else tuple(reversed(f)))
ring=[i for i in range(N+1)]+[j*(N+1)+N for j in range(1,N+1)]+[N*(N+1)+i for i in range(N-1,-1,-1)]+[j*(N+1) for j in range(N-1,0,-1)]
for i,a in enumerate(ring):
 b=ring[(i+1)%len(ring)];faces.append((a,b,b+stride,a+stride))
me=bpy.data.meshes.new('Closed upholstery sewn sheets');me.from_pydata(verts,[],faces);me.update();o=bpy.data.objects.new('PRESSURE_CUSHION_PROTOTYPE',me);scene.collection.objects.link(o)
vg=o.vertex_groups.new(name='Sewn perimeter');vg.add(ring+[i+stride for i in ring],1,'REPLACE')
cl=o.modifiers.new('Cloth pressure','CLOTH');s=cl.settings;s.quality=7;s.mass=.3;s.tension_stiffness=25;s.compression_stiffness=25;s.shear_stiffness=10;s.bending_stiffness=.6;s.tension_damping=8;s.compression_damping=8;s.shear_damping=5;s.air_damping=5;s.vertex_group_mass=vg.name;s.pin_stiffness=1;s.use_pressure=True;s.uniform_pressure_force=3;s.pressure_factor=1
cl.collision_settings.use_self_collision=False
cl.point_cache.frame_start=1;cl.point_cache.frame_end=42
scene.frame_start=1;scene.frame_end=42;bpy.context.view_layer.objects.active=o;o.select_set(True)
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'PRESSURE_CUSHION_SETUP.blend'))
t=time.time()
# Cache each increasing frame; derived static form is the deliverable, not a dynamic simulation claim.
checkpoints=[]
for f in range(1,43):
 scene.frame_set(f);bpy.context.view_layer.update()
 evaluated=o.evaluated_get(bpy.context.evaluated_depsgraph_get())
 mesh=evaluated.to_mesh()
 if f in [1,21,42]:checkpoints.append({'frame':f,'height_m':max(v.co.z for v in mesh.vertices)-min(v.co.z for v in mesh.vertices),'center_top_z_m':mesh.vertices[stride+(N//2)*(N+1)+N//2].co.z})
 evaluated.to_mesh_clear()
dg=bpy.context.evaluated_depsgraph_get();eval=o.evaluated_get(dg);final=bpy.data.meshes.new_from_object(eval);finished=bpy.data.objects.new('PRESSURE_GENERATED_STATIC_CUSHION',final);scene.collection.objects.link(finished);o.hide_render=True;o.hide_viewport=True
for p in final.polygons:p.use_smooth=True
sub=finished.modifiers.new('Fabric surface refinement','SUBSURF');sub.levels=1
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'PRESSURE_CUSHION_FORM.blend'))
report={'method':'Blender official closed cloth pressure, pinned sewn perimeter','frames_evaluated':[1,21,42],'checkpoints':checkpoints,'duration_seconds':round(time.time()-t,2),'pressure':3,'mass':.3,'sheet_size_m':[W,D,T],'vertices':len(final.vertices),'static_bounds':[[min(v.co[i] for v in final.vertices) for i in range(3)],[max(v.co[i] for v in final.vertices) for i in range(3)]],'deliverable':'static model shaping prototype; not physical foam simulation or persistent animated-cache certification'}
(OUT/'PRESSURE_FORM_REPORT.json').write_text(json.dumps(report,indent=2));print('PRESSURE_FORM_GENERATED',json.dumps(report))
