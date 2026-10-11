"""Fresh-open static form, frozen sources, invariants and rejected bake provenance."""
import bpy, bmesh, hashlib, json, math, struct
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'design/sofa_soft_pilot_v7'
RUN = OUT / 'local_final'
audit = json.loads((RUN/'SOLVE_AUDIT.json').read_text())
protected = json.loads((OUT/'PRESERVATION.json').read_text())['files']
for item in protected:
    assert hashlib.sha256(Path(item['path']).read_bytes()).hexdigest() == item['sha256'], item['path']

def mesh_hash(mesh):
    digest = hashlib.sha256()
    for v in mesh.vertices:
        digest.update(struct.pack('<fff',*v.co))
    for p in mesh.polygons:
        digest.update(struct.pack('<'+'I'*len(p.vertices),*p.vertices))
    for uv in mesh.uv_layers:
        for v in uv.data:
            digest.update(struct.pack('<ff',*v.uv))
    return digest.hexdigest()

def matrix(obj):
    return [v for row in obj.matrix_world for v in row]

def val(value):
    if isinstance(value,(float,int,str,bool)):
        return value
    try:
        return list(value)
    except TypeError:
        return str(value)

def nodes(tree):
    return {'nodes':[(n.name,n.bl_idname,[(i.name,val(i.default_value)) for i in n.inputs if hasattr(i,'default_value')],getattr(getattr(n,'image',None),'name',None),getattr(n,'operation',None),getattr(n,'blend_type',None)) for n in tree.nodes], 'links':[(l.from_node.name,l.from_socket.name,l.to_node.name,l.to_socket.name) for l in tree.links]}

def studio(scene):
    return {'objects':{o.name:{'matrix':matrix(o),'lens':o.data.lens} if o.type=='CAMERA' else {'matrix':matrix(o),'power':o.data.energy,'color':list(o.data.color),'size':o.data.size} for o in scene.objects if o.type in ['LIGHT','CAMERA']},'world':nodes(scene.world.node_tree),'view':[scene.view_settings.view_transform,scene.view_settings.look,scene.view_settings.exposure,scene.view_settings.gamma]}

bpy.ops.wm.open_mainfile(filepath=audit['source'])
bpy.context.view_layer.update()
baseline = {o.name:{'mesh':mesh_hash(o.data) if o.type=='MESH' else None,'matrix':matrix(o),'materials':[m.name for m in o.data.materials]} for o in bpy.data.collections['V6_CUSTOM_PAIR'].objects}
original_bounds = {}
for name in ['V6_SEAT_COMPLETE_COVER','V6_BACK_COMPLETE_COVER']:
    o=bpy.data.objects[name];p=[o.matrix_world@v.co for v in o.data.vertices]
    original_bounds[name] = [[min(v[i] for v in p) for i in range(3)],[max(v[i] for v in p) for i in range(3)]]
materials = {m.name:nodes(m.node_tree) for m in bpy.data.materials if m.use_nodes}
original_studio = studio(bpy.context.scene)

assert hashlib.sha256(Path(audit['output']).read_bytes()).hexdigest() == audit['output_sha256']
bpy.ops.wm.open_mainfile(filepath=audit['output'])
# Hidden collections have unevaluated matrix_world immediately after reopen.
# Evaluate the comparison graph before comparing saved transforms.
bpy.data.collections['V6_COMPARISON_PAIR'].hide_viewport=False
bpy.context.view_layer.update()
for name, expected in baseline.items():
    o=bpy.data.objects[name]
    assert matrix(o)==expected['matrix'],(name,'baseline transform')
    assert [m.name for m in o.data.materials]==expected['materials'],(name,'baseline materials')
    if o.type=='MESH':
        assert mesh_hash(o.data)==expected['mesh'],(name,'baseline mesh/uv')
for name, expected in materials.items():
    assert nodes(bpy.data.materials[name].node_tree)==expected,(name,'shader invariant')
assert studio(bpy.context.scene)==original_studio,'studio invariant'
for name in baseline:
    if name in ['V6_SEAT_COMPLETE_COVER','V6_BACK_COMPLETE_COVER'] or name.endswith('_welt'):
        continue
    o=bpy.data.objects[name.replace('V6_','V7_',1)]
    assert mesh_hash(o.data)==baseline[name]['mesh'],(name,'timber mesh')
    assert matrix(o)==baseline[name]['matrix'],(name,'timber transform')
    assert [m.name for m in o.data.materials]==baseline[name]['materials'],(name,'timber materials')

def geometry(o):
    e=o.evaluated_get(bpy.context.evaluated_depsgraph_get());me=e.to_mesh()
    points=[e.matrix_world@v.co for v in me.vertices];faces=[tuple(f.vertices) for f in me.polygons]
    bm=bmesh.new();bm.from_mesh(me)
    stats={'vertices':len(me.vertices),'faces':len(me.polygons),'open_edges':sum(len(edge.link_faces)!=2 for edge in bm.edges),'zero_edges':sum(edge.calc_length()<1e-7 for edge in bm.edges),'tiny_faces':sum(f.calc_area()<1e-12 for f in bm.faces),'signed_volume_m3':bm.calc_volume(signed=True),'bounds_m':[[min(p[i] for p in points) for i in range(3)],[max(p[i] for p in points) for i in range(3)]]}
    bm.free();e.to_mesh_clear()
    return points,BVHTree.FromPolygons(points,faces),stats

shells={}
for name in ['V7_SEAT_COMPLETE_COVER','V7_BACK_COMPLETE_COVER']:
    o=bpy.data.objects[name];p,t,stats=geometry(o)
    assert not any(stats[k] for k in ['open_edges','zero_edges','tiny_faces']),stats
    assert stats['signed_volume_m3']>0,stats
    assert not any(m.type=='CLOTH' for m in o.modifiers),'static candidate unexpectedly simulates'
    assert o.data.shape_keys and o.data.shape_keys.key_blocks[-1].value==1,'editable form missing'
    shells[name]=stats
sp,st,_=geometry(bpy.data.objects['V7_SEAT_COMPLETE_COVER'])
bp,bt,_=geometry(bpy.data.objects['V7_BACK_COMPLETE_COVER'])
intersections=st.overlap(bt)
assert not intersections,('seat/back intersections',len(intersections))
rail=geometry(bpy.data.objects['V7_BACK_TOP_RAIL'])[1]
assert not bt.overlap(rail),'back/rail intersections'
gaps=[]
for p in bp:
    if p.z<.56:
        hit=st.ray_cast(Vector((p.x,p.y,2)),Vector((0,0,-1)))
        if hit[0] is not None:gaps.append(p.z-hit[0].z)
assert -.001<min(gaps)<.003,('support gap',min(gaps))
assert abs(min(p.z for p in sp)-.285)<.001,'seat/deck contact'
for obj in [bpy.data.objects['V7_SEAT_COMPLETE_COVER'],bpy.data.objects['V7_BACK_COMPLETE_COVER']]:
    N=80;stride=81**2;ring=list(range(81))+[j*81+80 for j in range(1,81)]+[80*81+i for i in range(79,-1,-1)]+[j*81 for j in range(79,0,-1)]
    pts=geometry(obj)[0]
    for label,ids in [('bottom',ring),('top',[i+stride for i in ring])]:
        welt=bpy.data.objects[obj.name+'_'+label+'_welt']
        assert max((welt.matrix_world@Vector(p.co[:3])-pts[idx]).length for p,idx in zip(welt.data.splines[0].points,ids))<1e-6,'welt attachment'
missing=[im.name for im in bpy.data.images if im.source=='FILE' and not im.packed_file and not Path(bpy.path.abspath(im.filepath)).exists()]
assert not missing,missing
packed=sum(bool(im.packed_file) for im in bpy.data.images)
bounds_delta={name:[[round((shells[name]['bounds_m'][j][i]-original_bounds[name.replace('V7_','V6_',1)][j][i])*1000,3) for i in range(3)] for j in range(2)] for name in shells}
assert max(abs(d) for v in bounds_delta.values() for row in v for d in row)<12,'macro bounds deviation >12mm'

cache_checks=[]
for variant in ['solve1','solve2']:
    a=json.loads((OUT/variant/'SOLVE_AUDIT.json').read_text())
    bpy.ops.wm.open_mainfile(filepath=a['setup'])
    current={'variant':variant,'files':len(list((OUT/variant).glob('blendcache_*/*'))),'baked':[],'checkpoint_max_bounds_error_mm':0}
    assert current['files']==110,current
    for name in ['V7_SEAT_COMPLETE_COVER','V7_BACK_COMPLETE_COVER']:
        cloth=next(m for m in bpy.data.objects[name].modifiers if m.type=='CLOTH')
        assert cloth.point_cache.is_baked and cloth.point_cache.frame_start==1 and cloth.point_cache.frame_end==55,(variant,name,'cache')
        current['baked'].append(name)
    for frame in a['checkpoints']:
        bpy.context.scene.frame_set(frame['frame']);bpy.context.view_layer.update()
        for expected in frame['objects']:
            o=bpy.data.objects[expected['object']];e=o.evaluated_get(bpy.context.evaluated_depsgraph_get());me=e.to_mesh()
            pts=[e.matrix_world@v.co for v in me.vertices]
            box=[[min(p[i] for p in pts) for i in range(3)],[max(p[i] for p in pts) for i in range(3)]]
            error=max(abs(box[j][i]-expected['world_bounds_m'][j][i])*1000 for j in range(2) for i in range(3))
            delta=[(v.co-o.data.vertices[i].co).length for i,v in enumerate(me.vertices)]
            assert abs(max(delta)*1000-expected['max_displacement_mm'])<.01,(variant,frame['frame'],'deformation mismatch')
            assert error<.01,(variant,frame['frame'],'cache mismatch',error)
            current['checkpoint_max_bounds_error_mm']=max(current['checkpoint_max_bounds_error_mm'],error)
            e.to_mesh_clear()
    cache_checks.append(current)

report={'status':'PASS_TECHNICAL_ONLY','candidate':audit['output'],'sha256':audit['output_sha256'],'protected_files':len(protected),'v6_baseline_preserved':True,'timber_materials_camera_lights_color_preserved':True,'shells':shells,'bound_deltas_from_v6_mm':bounds_delta,'seat_back_surface_intersections':len(intersections),'back_rail_intersections':0,'minimum_back_seat_gap_mm':min(gaps)*1000,'seat_deck_gap_mm':(min(p.z for p in sp)-.285)*1000,'welt_attachment_max_error_m':1e-6,'packed_images':packed,'missing_images':missing,'rejected_simulation_fresh_open_checks':cache_checks,'final_is_static_editable_shape_keys':True,'appearance_status':'HUMAN_REVIEW; softness not accepted','housefit_status':'V6 814mm total / ~491mm crown were trial dimensions, not final procurement/ergonomic approval'}
(RUN/'VERIFICATION.json').write_text(json.dumps(report,indent=2)+'\n')
print('V7_VERIFY',json.dumps(report))
