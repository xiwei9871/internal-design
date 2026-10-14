"""Restore established architectural shadow-ray light transport, retaining visible glass."""
import bpy,json,hashlib
from pathlib import Path
R=Path(__file__).resolve().parents[1];D=R/'design/glass_privacy_v8';a=json.loads((D/'BUILD_AUDIT.json').read_text());src=Path(a['output']);dest=D/'WHOLE_HOUSE_GLASS_PRIVACY_DELIVERY_V8.blend';assert not dest.exists()
assert hashlib.sha256(src.read_bytes()).hexdigest()==a['sha256'];bpy.ops.wm.open_mainfile(filepath=str(src))
for name in ['V8_COLORLESS_CLEAR_ARCHITECTURAL_GLASS','V8_COLORLESS_PRIVACY_FROSTED_GLASS']:
 m=bpy.data.materials[name];ns=m.node_tree.nodes;ls=m.node_tree.links;bsdf=ns.get('Principled BSDF');out=ns.get('Material Output')
 shadow=ns.new('ShaderNodeLightPath');shadow.name='Established architectural shadow ray pass';trans=ns.new('ShaderNodeBsdfTransparent');trans.inputs['Color'].default_value=(1,1,1,1)
 mix=ns.new('ShaderNodeMixShader');mix.name='Visible physical glazing / shadow light transport';ls.new(shadow.outputs['Is Shadow Ray'],mix.inputs[0]);ls.new(bsdf.outputs['BSDF'],mix.inputs[1]);ls.new(trans.outputs['BSDF'],mix.inputs[2]);ls.new(mix.outputs[0],out.inputs['Surface'])
 m['render_approximation']='Transparent shadow rays for interior daylight transport, reused from V7 glazing. Camera/reflection rays retain physical clear/frosted Principled surface; not certified photometry.'
bpy.context.window.view_layer=bpy.context.scene.view_layers['OVERVIEW_CEILING_HIDDEN'];bpy.ops.wm.save_as_mainfile(filepath=str(dest));a['pure_glass_transport_candidate']={'path':str(src),'sha256':a['sha256'],'result':'reject room brightness regression; established shadow-ray daylight transport removed inadvertently'};a['output']=str(dest);a['sha256']=hashlib.sha256(dest.read_bytes()).hexdigest();a['shadow_ray_transport']='V7-established white Transparent BSDF only for IsShadowRay; visible clear/frosted surface retained';(D/'BUILD_AUDIT.json').write_text(json.dumps(a,indent=2)+'\n');print('V8_LIGHT_TRANSPORT',a['sha256'])
