"""Read-only diagnosis: mapping direction, native shaders and upholstery form."""
import bpy, hashlib, json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
SOURCE=ROOT/'design/product_rebuild_v4/LIVING_DINING_PRODUCT_REBUILD_V4.blend'
OUT=ROOT/'design/lookdev_v5'
bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
def value(v):
    try:return list(v)
    except TypeError:return v if isinstance(v,(float,int,str,bool)) else str(v)
materials={}
for name in ['V4_ASH_WAX_OIL_FROM_REAL_CATALOG','V4_OATMEAL_LINEN_NATIVE']:
    m=bpy.data.materials[name];nodes=[]
    for n in m.node_tree.nodes:
        item={'name':n.name,'type':n.type,'label':n.label}
        if n.type=='TEX_IMAGE':item.update(image=n.image.name if n.image else None,path=n.image.filepath if n.image else None,size=list(n.image.size) if n.image else None,colorspace=n.image.colorspace_settings.name if n.image else None)
        if n.type in ['MAPPING','MIX_RGB','MAP_RANGE','MATH','BSDF_PRINCIPLED','BUMP','NORMAL_MAP','RGBTOBW','UVMAP']:
            item['inputs']={s.name:value(s.default_value) for s in n.inputs if hasattr(s,'default_value') and not s.is_linked}
            item['linked_inputs']={s.name:s.links[0].from_node.name+'.'+s.links[0].from_socket.name for s in n.inputs if s.is_linked}
        if hasattr(n,'uv_map'):item['uv_map']=n.uv_map
        nodes.append(item)
    materials[name]={'nodes':nodes,'links':[[l.from_node.name,l.from_socket.name,l.to_node.name,l.to_socket.name] for l in m.node_tree.links]}
objects={}
for name in ['V4_Dining_racetrack_top','V4_Coffee_solid_top','V4_Sofa_seat_middle','V4_Sofa_back_1']:
    o=bpy.data.objects.get(name)
    if not o:continue
    points=[v.co for v in o.data.vertices];bounds=[[min(v[i] for v in points) for i in range(3)],[max(v[i] for v in points) for i in range(3)]]
    objects[name]={'local_bounds_m':bounds,'world_dimensions_m':list(o.dimensions),'rotation_euler':list(o.rotation_euler),'vertex_count':len(points),'uv_layers':[u.name for u in o.data.uv_layers]}
    if o.data.uv_layers.active:
        face=max(o.data.polygons,key=lambda p:p.area)
        objects[name]['largest_face_normal']=list(face.normal)
        objects[name]['largest_face_xyz_uv']=[{'xyz':list(o.data.vertices[o.data.loops[li].vertex_index].co),'uv':list(o.data.uv_layers.active.data[li].uv)} for li in face.loop_indices[:8]]
(OUT/'V4_DIAGNOSIS.json').write_text(json.dumps({'source_sha256':hashlib.sha256(SOURCE.read_bytes()).hexdigest(),'materials':materials,'objects':objects},indent=2)+'\n')
print('DIAGNOSIS_SAVED',len(materials),len(objects))
