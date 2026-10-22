"""Fresh reopen: assert V8 is the same V7 object, material and camera chain."""
import bpy,hashlib,json,struct
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'design/sofa_soft_pilot_v8';RUN=OUT/'render_diagnosis'
a=json.loads((RUN/'DIAGNOSIS_MANIFEST.json').read_text())
protected=json.loads((OUT/'PRESERVATION.json').read_text())['files']
for item in protected:
    assert hashlib.sha256(Path(item['path']).read_bytes()).hexdigest()==item['sha256'],item['path']

def mesh_hash(mesh):
    h=hashlib.sha256()
    for v in mesh.vertices:h.update(struct.pack('<fff',*v.co))
    for face in mesh.polygons:h.update(struct.pack('<'+'I'*len(face.vertices),*face.vertices))
    for uv in mesh.uv_layers:
        for p in uv.data:h.update(struct.pack('<ff',*p.uv))
    if mesh.shape_keys:
        for key in mesh.shape_keys.key_blocks:
            h.update(key.name.encode());h.update(struct.pack('<f',key.value))
            for p in key.data:h.update(struct.pack('<fff',*p.co))
    return h.hexdigest()

def value(v):
    if isinstance(v,(float,int,str,bool)):return v
    try:return list(v)
    except TypeError:return str(v)

def nodes(tree,world=False):
    return {'nodes':[(n.name,n.bl_idname,[(i.name,value(i.default_value)) for i in n.inputs if hasattr(i,'default_value') and not(world and n.type=='BACKGROUND' and i.name=='Strength')],getattr(getattr(n,'image',None),'name',None),getattr(n,'operation',None),getattr(n,'blend_type',None)) for n in tree.nodes],'links':[(l.from_node.name,l.from_socket.name,l.to_node.name,l.to_socket.name) for l in tree.links]}

def snapshot(path):
    bpy.ops.wm.open_mainfile(filepath=str(path))
    # Evaluate hidden baseline/parent graphs before comparing world transforms.
    for c in bpy.data.collections:c.hide_viewport=False
    for o in bpy.data.objects:o.hide_viewport=False;o.hide_set(False)
    bpy.context.view_layer.update();scene=bpy.context.scene
    records={};dg=bpy.context.evaluated_depsgraph_get()
    for o in bpy.data.objects:
        item={'type':o.type,'matrix':[v for row in o.matrix_world for v in row]}
        if o.type=='MESH':
            item['raw_hash']=mesh_hash(o.data);e=o.evaluated_get(dg);me=e.to_mesh();item['evaluated_hash']=mesh_hash(me);p=[e.matrix_world@v.co for v in me.vertices];item['bounds_m']=[[min(v[i] for v in p) for i in range(3)],[max(v[i] for v in p) for i in range(3)]];e.to_mesh_clear()
        elif o.type=='CURVE':
            item['curve']={'bevel_depth':o.data.bevel_depth,'resolution':o.data.bevel_resolution,'splines':[[list(p.co) for p in s.points] for s in o.data.splines]}
        elif o.type=='CAMERA':item['camera']=[o.data.lens,o.data.clip_start,o.data.clip_end]
        if hasattr(o.data,'materials'):item['materials']=[m.name for m in o.data.materials]
        records[o.name]=item
    return {'objects':records,'materials':{m.name:nodes(m.node_tree) for m in bpy.data.materials if m.node_tree},'world':nodes(scene.world.node_tree,True),'view':[scene.view_settings.view_transform,scene.view_settings.look,scene.view_settings.exposure,scene.view_settings.gamma],'lights':{o.name:{'matrix':[v for row in o.matrix_world for v in row],'power':o.data.energy,'size':o.data.size,'color':list(o.data.color)} for o in scene.objects if o.type=='LIGHT'},'world_strength':scene.world.node_tree.nodes['Background'].inputs['Strength'].default_value}

source=snapshot(a['source']);candidate=snapshot(a['candidate'])
assert source['objects'].keys()==candidate['objects'].keys(),'object membership changed'
for name,original in source['objects'].items():
    current=candidate['objects'][name]
    if name=='V6_KEY':
        assert {k:v for k,v in original.items() if k!='matrix'}=={k:v for k,v in current.items() if k!='matrix'},name
    else:assert current==original,('object/shape/UV/matrix changed',name)
assert source['materials']==candidate['materials'],'shader changed'
assert source['world']==candidate['world'],'world other than strength changed'
assert source['view']==candidate['view'],'color management changed'
for name in source['lights']:
    assert source['lights'][name]['color']==candidate['lights'][name]['color'],'light color changed'
    expected={'V6_KEY':320,'V6_FILL':55,'V6_RIM':80}[name]
    assert abs(candidate['lights'][name]['power']-expected)<1e-5,name
assert abs(candidate['world_strength']-.18)<1e-6
assert abs(candidate['lights']['V6_KEY']['size']-1)<1e-6
assert hashlib.sha256(Path(a['candidate']).read_bytes()).hexdigest()==a['candidate_sha256']
missing=[im.name for im in bpy.data.images if im.source=='FILE' and not im.packed_file and not Path(bpy.path.abspath(im.filepath)).exists()]
assert not missing,missing
previous=json.loads((ROOT/'design/sofa_soft_pilot_v7/local_final/VERIFICATION.json').read_text())
assert previous['sha256']==a['source_sha256'] and previous['status']=='PASS_TECHNICAL_ONLY'
report={'status':'PASS_UNCHANGED_GEOMETRY_AND_MATERIALS','source_sha256':a['source_sha256'],'candidate_sha256':a['candidate_sha256'],'protected_files':len(protected),'scene_objects':len(source['objects']),'meshes_unchanged':sum(o['type']=='MESH' for o in source['objects'].values()),'raw_evaluated_mesh_uv_shape_key_transform_changes':0,'curve_camera_shader_color_management_changes':0,'allowed_changes':['key light position/rotation/size/power','fill and rim powers','world strength','render engine/settings'],'lights_before':source['lights'],'lights_after':candidate['lights'],'world_strength_before':source['world_strength'],'world_strength_after':candidate['world_strength'],'packed_images':sum(bool(im.packed_file) for im in bpy.data.images),'missing_images':missing,'seat_bounds_m':candidate['objects']['V7_SEAT_COMPLETE_COVER']['bounds_m'],'back_bounds_m':candidate['objects']['V7_BACK_COMPLETE_COVER']['bounds_m'],'prior_static_support_checks_reused':'V7 unchanged evaluated geometry; no intersections, ~0.8mm back-seat gap, seat bottom285mm','owner_accepted':False,'physical_site_illumination_calibrated':False}
(RUN/'VERIFICATION.json').write_text(json.dumps(report,indent=2)+'\n');print('V8_RENDER_VERIFY',json.dumps(report))
