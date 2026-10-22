"""Root-cause repair: EEVEE refraction + calibrated exterior presentation exposure."""
import bpy,json,hashlib,struct
from pathlib import Path
R=Path(__file__).resolve().parents[1];D=R/'design/glass_visibility_v9';S=R/'design/glass_privacy_v8/WHOLE_HOUSE_GLASS_PRIVACY_DELIVERY_V8.blend';O=D/'WHOLE_HOUSE_GLASS_VISIBILITY_V9.blend'
assert hashlib.sha256(S.read_bytes()).hexdigest()=='e9b3e3d4766f161e2b7f6450475c8d0f8af4c59469709747356ad7f744e58928';assert not O.exists()
bpy.ops.wm.open_mainfile(filepath=str(S));s=bpy.context.scene
hides={o.name:(o.hide_viewport,o.hide_get()) for o in bpy.data.objects}
for c in bpy.data.collections:c.hide_viewport=False
for o in bpy.data.objects:o.hide_viewport=False;o.hide_set(False)
bpy.context.view_layer.update()
def state(o):
 h=hashlib.sha256()
 if o.type=='MESH':
  for v in o.data.vertices:h.update(struct.pack('<fff',*v.co))
  for f in o.data.polygons:h.update(struct.pack('<'+'I'*len(f.vertices),*f.vertices))
 return {'mesh':h.hexdigest(),'matrix':[list(v) for v in o.matrix_world],'hide_render':o.hide_render,'materials':[m.name if m else None for m in o.data.materials] if o.type=='MESH' else [],'light_energy':o.data.energy if o.type=='LIGHT' else None}
before={o.name:state(o) for o in bpy.data.objects}
for n,(hv,hg) in hides.items():bpy.data.objects[n].hide_viewport=hv;bpy.data.objects[n].hide_set(hg)
world=s.world.copy();world.name='V9_DAYLIGHT_EXTERIOR_PRESENTATION';s.world=world;world_before={n.name:n.inputs['Strength'].default_value for n in world.node_tree.nodes if n.type=='BACKGROUND'}
# V7/V8 already separate visible exterior from diffuse illumination; correct the underexposed visible/transmission branch only.
for name in ['Background.001','LD Neutral exterior presentation']:world.node_tree.nodes[name].inputs['Strength'].default_value=3.6
assert abs(world.node_tree.nodes['Background'].inputs['Strength'].default_value-.22)<1e-6
s.eevee.use_raytracing=True;s.eevee.ray_tracing_method='SCREEN'
for name in ['V8_COLORLESS_CLEAR_ARCHITECTURAL_GLASS','V8_COLORLESS_PRIVACY_FROSTED_GLASS']:
 m=bpy.data.materials[name];m.use_raytrace_refraction=True;m.thickness_mode='SLAB';m.node_tree.nodes.get('Material Output').inputs['Thickness'].default_value=.008
 m['V9_preview_fix']='EEVEE raytraced transmission + SLAB 8mm preview thickness approximation; Cycles uses retained actual geometry. No tint/IOR/roughness change.'
s['V9_GLASS_VISIBILITY']='Material Preview now supports refraction; visible/transmitted illustrative outdoor HDRI exposure calibrated +2.585 stops. Diffuse world energy and authored lights unchanged. Privacy frosted glass retained.'
bpy.context.window.view_layer=s.view_layers['OVERVIEW_CEILING_HIDDEN'];bpy.ops.wm.save_as_mainfile(filepath=str(O))
a={'source':str(S),'source_sha256':hashlib.sha256(S.read_bytes()).hexdigest(),'output':str(O),'sha256':hashlib.sha256(O.read_bytes()).hexdigest(),'before':before,'world_before':world_before,'world_after':{n.name:n.inputs['Strength'].default_value for n in world.node_tree.nodes if n.type=='BACKGROUND'},'eevee':{'raytracing':True,'method':'SCREEN','material_refraction':True,'thickness_mode':'SLAB','preview_thickness_m':.008},'glass_surface':'all V8 colorless, IOR1.45, clear roughness.015 / frosted.68 retained; only EEVEE preview flags/output thickness changed','privacy':'16 V8 privacy panes retained; wooden bathroom entries unchanged','diffuse_lighting':'world .22, individual lights and camera exposure unchanged','background_source':'existing Poly Haven kiara_3_morning CC0, illustrative exterior not site photography','controls':['CONTROL_COMPARE.jpg','PRESENTATION_COMPARE.jpg','eevee_trace_off.png','eevee_trace_on.png','outdoor_2_4.png','outdoor_3_6.png'],'official_docs':['https://docs.blender.org/manual/en/latest/render/eevee/render_settings/raytracing.html','https://docs.blender.org/manual/en/latest/render/eevee/material_settings.html'],'image2_requests':0,'status':'BUILT_PENDING_FINAL_REVIEW'}
(D/'BUILD_AUDIT.json').write_text(json.dumps(a,indent=2)+'\n');print('GLASS_VISIBILITY_V9',a['sha256'])
