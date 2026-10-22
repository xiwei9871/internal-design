"""Fresh-open A/B verification; adapt prior tested sofa invariant checks."""
import bpy,hashlib,json,struct
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'design/sofa_material_pilot_v9';RUN=OUT/'surface_test'
a=json.loads((RUN/'RENDER_MANIFEST.json').read_text())
protected=json.loads((OUT/'PRESERVATION.json').read_text())['files']
for item in protected:assert hashlib.sha256(Path(item['path']).read_bytes()).hexdigest()==item['sha256'],item['path']

def mesh_hash(mesh):
    h=hashlib.sha256()
    for v in mesh.vertices:h.update(struct.pack('<fff',*v.co))
    for f in mesh.polygons:h.update(struct.pack('<'+'I'*len(f.vertices),*f.vertices))
    for uv in mesh.uv_layers:
        for p in uv.data:h.update(struct.pack('<ff',*p.uv))
    if mesh.shape_keys:
        for key in mesh.shape_keys.key_blocks:
            h.update(key.name.encode());h.update(struct.pack('<f',key.value))
            for p in key.data:h.update(struct.pack('<fff',*p.co))
    return h.hexdigest()
def val(v):
    if isinstance(v,(float,int,str,bool)):return v
    try:return list(v)
    except TypeError:return str(v)
def shader(mat,ignore_sheen=False):
    tree=mat.node_tree
    return {'nodes':[(n.name,n.bl_idname,[(i.name,val(i.default_value)) for i in n.inputs if hasattr(i,'default_value') and not(ignore_sheen and n.type=='BSDF_PRINCIPLED' and i.name in ['Sheen Weight','Sheen Roughness'])],getattr(getattr(n,'image',None),'name',None),getattr(n,'operation',None),getattr(n,'blend_type',None)) for n in tree.nodes],'links':[(l.from_node.name,l.from_socket.name,l.to_node.name,l.to_socket.name) for l in tree.links]}
def snapshot(path):
    bpy.ops.wm.open_mainfile(filepath=str(path))
    for c in bpy.data.collections:c.hide_viewport=False
    for o in bpy.data.objects:o.hide_viewport=False;o.hide_set(False)
    bpy.context.view_layer.update();scene=bpy.context.scene;dg=bpy.context.evaluated_depsgraph_get();objects={}
    for o in bpy.data.objects:
        item={'type':o.type,'matrix':[v for row in o.matrix_world for v in row]}
        if o.type=='MESH':
            item['mesh']=mesh_hash(o.data);e=o.evaluated_get(dg);me=e.to_mesh();item['evaluated_mesh']=mesh_hash(me);pts=[e.matrix_world@v.co for v in me.vertices];item['bounds']=[[min(p[i] for p in pts) for i in range(3)],[max(p[i] for p in pts) for i in range(3)]];e.to_mesh_clear()
        elif o.type=='CURVE':item['curve']=[o.data.bevel_depth,o.data.bevel_resolution,[[list(p.co) for p in s.points] for s in o.data.splines]]
        elif o.type=='CAMERA':item['camera']=[o.data.lens,o.data.clip_start,o.data.clip_end]
        elif o.type=='LIGHT':item['light']=[o.data.energy,o.data.size,list(o.data.color)]
        if hasattr(o.data,'materials'):item['materials']=[m.name for m in o.data.materials]
        objects[o.name]=item
    world={'nodes':[(n.name,[(i.name,val(i.default_value)) for i in n.inputs if hasattr(i,'default_value')]) for n in scene.world.node_tree.nodes],'links':[(l.from_node.name,l.to_node.name) for l in scene.world.node_tree.links]}
    return {'objects':objects,'materials':{m.name:shader(m) for m in bpy.data.materials if m.node_tree},'world':world,'view':[scene.view_settings.view_transform,scene.view_settings.look,scene.view_settings.exposure,scene.view_settings.gamma]}

source=snapshot(a['source']);original_sheen_free=shader(bpy.data.materials['V5_NATURAL_FLAX_COTTON'],True)
candidate=snapshot(a['candidate'])
assert set(candidate['objects'])-set(source['objects'])=={'V9_FABRIC_CLOSEUP'},'unexpected added object'
assert not(set(source['objects'])-set(candidate['objects'])),'missing source object'
for name,item in source['objects'].items():
    current=dict(candidate['objects'][name])
    if name in ['V7_SEAT_COMPLETE_COVER','V7_BACK_COMPLETE_COVER']:
        assert current['materials']==['V9_MICROFIBER_SURFACE_TEST'],name
        current['materials']=item['materials']
    assert item==current,('geometry/UV/shape/transform/light/camera changed',name)
for name,mat in source['materials'].items():assert candidate['materials'][name]==mat,('original material changed',name)
assert set(candidate['materials'])-set(source['materials'])=={'V9_MICROFIBER_SURFACE_TEST'}
new=bpy.data.materials['V9_MICROFIBER_SURFACE_TEST']
assert shader(new,True)==original_sheen_free,'unexpected shader change'
p=next(n for n in new.node_tree.nodes if n.type=='BSDF_PRINCIPLED')
assert abs(p.inputs['Sheen Weight'].default_value-.5)<1e-6
assert abs(p.inputs['Sheen Roughness'].default_value-.8)<1e-6
assert source['world']==candidate['world'],'world changed'
assert source['view']==candidate['view'],'color management changed'
assert hashlib.sha256(Path(a['candidate']).read_bytes()).hexdigest()==a['candidate_sha256']
missing=[im.name for im in bpy.data.images if im.source=='FILE' and not im.packed_file and not Path(bpy.path.abspath(im.filepath)).exists()];assert not missing,missing
report={'status':'PASS_MATERIAL_ONLY','source_sha256':a['source_sha256'],'candidate_sha256':a['candidate_sha256'],'protected_files':len(protected),'source_objects_unchanged':len(source['objects']),'meshes_unchanged':sum(o['type']=='MESH' for o in source['objects'].values()),'mesh_uv_shape_key_transforms_light_world_camera_grade_changes':0,'new_camera':'V9_FABRIC_CLOSEUP, same definition for A/B','changed_slots':['V7_SEAT_COMPLETE_COVER','V7_BACK_COMPLETE_COVER'],'changed_shader_inputs':['Sheen Weight:0.2->0.5','Sheen Roughness:0.5->0.8'],'same_color_maps_physical_scale':True,'packed_images':sum(bool(im.packed_file) for im in bpy.data.images),'missing_images':missing,'seat_bounds_m':candidate['objects']['V7_SEAT_COMPLETE_COVER']['bounds'],'back_bounds_m':candidate['objects']['V7_BACK_COMPLETE_COVER']['bounds'],'filling_mechanics_changed':False,'owner_accepted':False}
(RUN/'VERIFICATION.json').write_text(json.dumps(report,indent=2)+'\n');print('V9_VERIFY',json.dumps(report))
