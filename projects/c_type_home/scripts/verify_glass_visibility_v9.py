"""Fresh-open preservation and actual EEVEE/exterior presentation flags."""
import bpy,json,hashlib,struct
from pathlib import Path
R=Path(__file__).resolve().parents[1];D=R/'design/glass_visibility_v9';a=json.loads((D/'BUILD_AUDIT.json').read_text());assert hashlib.sha256(Path(a['source']).read_bytes()).hexdigest()==a['source_sha256'];assert hashlib.sha256(Path(a['output']).read_bytes()).hexdigest()==a['sha256']
bpy.ops.wm.open_mainfile(filepath=a['output']);s=bpy.context.scene;assert s.eevee.use_raytracing and s.eevee.ray_tracing_method=='SCREEN'
view={'active':bpy.context.window.view_layer.name,'ceiling_hidden':all(bpy.data.objects[n].hide_get(view_layer=s.view_layers['OVERVIEW_CEILING_HIDDEN']) for n in ['V7_CEILING_LOW','V7_CEILING_HIGH','V7_CEILING_450MM_TRANSITION'])}
assert view['active']=='OVERVIEW_CEILING_HIDDEN' and view['ceiling_hidden']
for col in bpy.data.collections:col.hide_viewport=False
for o in bpy.data.objects:o.hide_viewport=False;o.hide_set(False)
bpy.context.view_layer.update()
def meshhash(o):
 h=hashlib.sha256()
 if o.type=='MESH':
  for v in o.data.vertices:h.update(struct.pack('<fff',*v.co))
  for f in o.data.polygons:h.update(struct.pack('<'+'I'*len(f.vertices),*f.vertices))
 return h.hexdigest()
assert set(a['before'])=={o.name for o in bpy.data.objects}
for n,b in a['before'].items():
 o=bpy.data.objects[n];assert meshhash(o)==b['mesh'] and [list(v) for v in o.matrix_world]==b['matrix'] and o.hide_render==b['hide_render'],n
 if o.type=='MESH':assert [m.name if m else None for m in o.data.materials]==b['materials'],n
 if o.type=='LIGHT':assert o.data.energy==b['light_energy'],n
for n,rough in [('V8_COLORLESS_CLEAR_ARCHITECTURAL_GLASS',.015),('V8_COLORLESS_PRIVACY_FROSTED_GLASS',.68)]:
 m=bpy.data.materials[n];p=m.node_tree.nodes.get('Principled BSDF');assert m.use_raytrace_refraction and m.thickness_mode=='SLAB';assert abs(p.inputs['Roughness'].default_value-rough)<1e-6;assert list(p.inputs['Base Color'].default_value)==[1,1,1,1];assert abs(p.inputs['IOR'].default_value-1.45)<1e-6
strengths={n.name:n.inputs['Strength'].default_value for n in s.world.node_tree.nodes if n.type=='BACKGROUND'}
assert abs(strengths['Background']-.22)<1e-6
for n in ['Background.001','LD Neutral exterior presentation']:assert abs(strengths[n]-3.6)<1e-6
protected=json.loads((R/'design/whole_house_model_v1/PRESERVATION.json').read_text())['files']
for f in protected:assert hashlib.sha256(Path(f['path']).read_bytes()).hexdigest()==f['sha256']
r={'status':'PASS_PRESERVATION_AND_VIEW_RENDER_SETTINGS','sha256':a['sha256'],'source_objects_geometry_pose_slots_unchanged':len(a['before']),'lights_unchanged':True,'eevee_raytrace_and_material_refraction':True,'privacy_frost_surface_unchanged':True,'world_strengths':strengths,'view':view,'protected_sources':len(protected),'final_visual_acceptance':False}
(D/'VERIFICATION.json').write_text(json.dumps(r,indent=2)+'\n');print('VERIFY_V9',json.dumps(r))
