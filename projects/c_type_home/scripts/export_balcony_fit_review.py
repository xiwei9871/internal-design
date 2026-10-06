"""Project-scoped presentation export: zoning everywhere, glass/aluminum only at north balcony."""
import sys,json,argparse
from pathlib import Path
import bpy
sys.path.insert(0,'/Users/xiwei/Documents/ChatGPT/Spatial-Canvas/adapters/blender')
import export_proxy
from common import write_json
ordinary=export_proxy.assign_flat_colors
def presentation(mesh,entity,cache,owned,counts,mode,source):
    name=entity['native_object_id']
    if name.startswith(('WAVE_WALL_HANDRAIL','WAVE_HANDRAIL_')):
        return ordinary(mesh,entity,cache,owned,counts,'source-flat',source)
    if not name.startswith(('NORTH_BALCONY_GLASS_','NORTH_BALCONY_FRAME_')):
        return ordinary(mesh,entity,cache,owned,counts,mode,source)
    is_glass=name.startswith('NORTH_BALCONY_GLASS_')
    key='balcony_glass' if is_glass else 'balcony_aluminum'
    material=cache.get(key)
    if material is None:
        material=bpy.data.materials.new(key)
        material.use_nodes=True;shader=material.node_tree.nodes.get('Principled BSDF')
        color=(.45,.70,.78,.32) if is_glass else (.055,.065,.075,1)
        material.diffuse_color=color;shader.inputs['Base Color'].default_value=color
        shader.inputs['Alpha'].default_value=color[3]
        shader.inputs['Roughness'].default_value=.22 if is_glass else .4
        material.use_backface_culling=False
        if is_glass:material.surface_render_method='DITHERED'
        owned.append(material);cache[key]=material
    mesh.materials.clear();mesh.materials.append(material)
    for face in mesh.polygons:face.material_index=0
    counts[key]=counts.get(key,0)+1
export_proxy.assign_flat_colors=presentation
argv=sys.argv[sys.argv.index('--')+1:]
p=argparse.ArgumentParser();p.add_argument('--output',required=True);p.add_argument('--bindings',required=True)
args=p.parse_args(argv)
registry=json.loads(Path(args.bindings).read_text())
opts=argparse.Namespace(output=args.output,bindings=args.bindings,scope='full',room_id=None,global_ids=None,collection=None,color_mode='zoning-flat',source_resource_id=registry['source_resource_id'],source_revision=registry['source_revision'])
manifest=export_proxy.export_proxy(opts)
manifest['extensions']['spatial_canvas.presentation'].update(opaque=False,profile='zoning-with-north-balcony-glass-and-aluminum',glass_alpha=.32,texture_free=True)
manifest['extensions']['spatial_canvas.review']={'status':'HUMAN_REVIEW','correction':'Frame-derived glazing bounds; east bay meets corner post. Stair350mm run; second500mm living shift,total1000mm. Upper planar landing restored; south pier clearance.','parent_source_resource_id':'c_type_r4','parent_source_revision':'r4','parent_source_sha256':'d109c7efcfa2b2b2565e4c073ee0cdf5282b23c01122bc9c1bbe7b8791ac3afb'}
write_json(Path(args.output)/'interaction_proxy.manifest.json',manifest)
print('EXPORTED',manifest['source_revision'],manifest['entity_count'])
