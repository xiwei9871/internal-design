"""Read the V7 presentation chain without altering source or live Blender."""
import bpy,hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'design/sofa_soft_pilot_v8'
SOURCE=ROOT/'design/sofa_soft_pilot_v7/local_final/SOFA_RELAXED_COVER_V7.blend'
bpy.ops.wm.open_mainfile(filepath=str(SOURCE));bpy.context.view_layer.update()
scene=bpy.context.scene;material=bpy.data.materials['V5_NATURAL_FLAX_COTTON']
def value(v):
    if isinstance(v,(float,int,str,bool)):return v
    try:return list(v)
    except TypeError:return str(v)
nodes=[]
for n in material.node_tree.nodes:
    nodes.append({'name':n.name,'type':n.bl_idname,'inputs':{i.name:value(i.default_value) for i in n.inputs if hasattr(i,'default_value')},'operation':getattr(n,'operation',None),'image':getattr(getattr(n,'image',None),'name',None)})
report={'source':str(SOURCE),'sha256':hashlib.sha256(SOURCE.read_bytes()).hexdigest(),'material':material.name,'nodes':nodes,'links':[(l.from_node.name,l.from_socket.name,l.to_node.name,l.to_socket.name) for l in material.node_tree.links],'world_nodes':[{'name':n.name,'inputs':{i.name:value(i.default_value) for i in n.inputs if hasattr(i,'default_value')}} for n in scene.world.node_tree.nodes],'lights':[{'name':o.name,'location':list(o.location),'power':o.data.energy,'size':o.data.size,'color':list(o.data.color)} for o in scene.objects if o.type=='LIGHT'],'color_management':{'view':scene.view_settings.view_transform,'look':scene.view_settings.look,'exposure':scene.view_settings.exposure},'workbench':{'light':scene.display.shading.light,'cavity':scene.display.shading.show_cavity,'cavity_type':scene.display.shading.cavity_type}}
(OUT/'V7_RENDER_CHAIN.json').write_text(json.dumps(report,indent=2)+'\n')
p=next(n for n in material.node_tree.nodes if n.type=='BSDF_PRINCIPLED')
print('V7_RENDER_CHAIN',json.dumps({'principled':nodes[[n['name'] for n in nodes].index(p.name)],'lights':report['lights'],'color_management':report['color_management'],'normal_and_mapping':[n for n in nodes if n['type'] in ['ShaderNodeNormalMap','ShaderNodeBump','ShaderNodeMapping','ShaderNodeMath','ShaderNodeMixRGB']]}))
