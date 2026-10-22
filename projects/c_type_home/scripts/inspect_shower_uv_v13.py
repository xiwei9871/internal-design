import bpy,json
from pathlib import Path
from mathutils import Vector
R=Path(__file__).resolve().parents[1];D=R/'design/fridge_finish_v13';bpy.ops.wm.open_mainfile(filepath=str(D/'WHOLE_HOUSE_FRIDGE_FINISH_V13.blend'))
for c in bpy.data.collections:c.hide_viewport=False
for o in bpy.data.objects:o.hide_viewport=False;o.hide_set(False)
bpy.context.view_layer.update();a={}
for n in ['R3_SHOWER_TRAY','R3_SHOWER_GLASS_1','R3_SHOWER_POST_1','R3_SHOWER_POST_2','B11_K-FRIDGE-OVERHEAD_TOP','B11_K-TALL-L_UPPER_FRONT_0']:
 o=bpy.data.objects[n];pts=sorted(set(tuple(round(v,6) for v in (o.matrix_world@p.co)) for p in o.data.vertices));a[n]={'points':pts if 'SHOWER' in n else [],'uvs':[(l.name,l.active_render) for l in o.data.uv_layers],'parent':o.parent.name if o.parent else None,'constraints':[c.type for c in o.constraints],'dimensions':list(o.dimensions)}
m=bpy.data.materials['V7_CATALOG_PALE_NATURAL_ASH'];a['shader_uv_maps']=[{'name':n.name,'uv_map':n.uv_map} for n in m.node_tree.nodes if n.type=='UVMAP'];a['shader_images']=[n.image.filepath for n in m.node_tree.nodes if n.type=='TEX_IMAGE' and n.image];(D/'SHOWER_EXACT_POINTS_AND_UV.json').write_text(json.dumps(a,indent=2));print('UV_SHADER',a['shader_uv_maps']);print('UV_OVERHEAD',a['B11_K-FRIDGE-OVERHEAD_TOP']);print('SHOWER_TRAY',a['R3_SHOWER_TRAY']['points']);print('SHOWER_DOOR',a['R3_SHOWER_GLASS_1'])

