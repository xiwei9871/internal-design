"""Fresh-open invariants and actual closed-shell support geometry."""
import bpy,bmesh,hashlib,json,struct,sys
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'design/sofa_fill_form_v10'
args=sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else [];RUN=OUT/(args[0] if args else 'form1')
a=json.loads((RUN/'BUILD_AUDIT.json').read_text())
protected=json.loads((OUT/'PRESERVATION.json').read_text())['files']
for item in protected:assert hashlib.sha256(Path(item['path']).read_bytes()).hexdigest()==item['sha256'],item['path']
def mesh_hash(me):
    h=hashlib.sha256()
    for v in me.vertices:h.update(struct.pack('<fff',*v.co))
    for f in me.polygons:h.update(struct.pack('<'+'I'*len(f.vertices),*f.vertices))
    for uv in me.uv_layers:
        for p in uv.data:h.update(struct.pack('<ff',*p.uv))
    if me.shape_keys:
        for key in me.shape_keys.key_blocks:
            h.update(key.name.encode());h.update(struct.pack('<f',key.value))
            for p in key.data:h.update(struct.pack('<fff',*p.co))
    return h.hexdigest()
def val(v):
    if isinstance(v,(float,int,str,bool)):return v
    try:return list(v)
    except TypeError:return str(v)
def shader(tree):
    return {'nodes':[(n.name,n.bl_idname,[(i.name,val(i.default_value)) for i in n.inputs if hasattr(i,'default_value')],getattr(getattr(n,'image',None),'name',None),getattr(n,'operation',None),getattr(n,'blend_type',None)) for n in tree.nodes],'links':[(l.from_node.name,l.from_socket.name,l.to_node.name,l.to_socket.name) for l in tree.links]}
def evaluate_all():
    for c in bpy.data.collections:c.hide_viewport=False
    for o in bpy.data.objects:o.hide_viewport=False;o.hide_set(False)
    bpy.context.view_layer.update()
def record(o):
    r={'type':o.type,'matrix':[v for row in o.matrix_world for v in row]}
    if o.type=='MESH':r['mesh_uv_keys']=mesh_hash(o.data)
    elif o.type=='CURVE':r['curve']=[o.data.bevel_depth,o.data.bevel_resolution,[[list(p.co) for p in s.points] for s in o.data.splines]]
    elif o.type=='LIGHT':r['light']=[o.data.energy,o.data.size,list(o.data.color)]
    elif o.type=='CAMERA':r['camera']=[o.data.lens,o.data.clip_start,o.data.clip_end]
    if hasattr(o.data,'materials'):r['materials']=[m.name for m in o.data.materials]
    return r
bpy.ops.wm.open_mainfile(filepath=a['source']);evaluate_all();source={o.name:record(o) for o in bpy.data.objects};materials={m.name:shader(m.node_tree) for m in bpy.data.materials if m.node_tree};world=shader(bpy.context.scene.world.node_tree);view=[bpy.context.scene.view_settings.view_transform,bpy.context.scene.view_settings.look,bpy.context.scene.view_settings.exposure,bpy.context.scene.view_settings.gamma]
assert hashlib.sha256(Path(a['output']).read_bytes()).hexdigest()==a['output_sha256']
bpy.ops.wm.open_mainfile(filepath=a['output'])
guide_collection=bpy.data.collections['V10_CONSTRUCTION_GUIDE'];guide_hidden=guide_collection.hide_render and guide_collection.hide_viewport;assert guide_hidden
evaluate_all()
for name,r in source.items():assert record(bpy.data.objects[name])==r,('baseline altered',name)
for item in a['frame_map']:assert record(bpy.data.objects[item['candidate']])==source[item['source']],('frame altered',item)
for name,s in materials.items():assert shader(bpy.data.materials[name].node_tree)==s,('shader altered',name)
assert shader(bpy.context.scene.world.node_tree)==world,'world altered'
assert [bpy.context.scene.view_settings.view_transform,bpy.context.scene.view_settings.look,bpy.context.scene.view_settings.exposure,bpy.context.scene.view_settings.gamma]==view,'color management altered'
def geometry(obj):
    e=obj.evaluated_get(bpy.context.evaluated_depsgraph_get());me=e.to_mesh();p=[e.matrix_world@v.co for v in me.vertices];faces=[tuple(f.vertices) for f in me.polygons]
    bm=bmesh.new();bm.from_mesh(me)
    stats={'vertices':len(me.vertices),'faces':len(me.polygons),'nonmanifold_edges':sum(len(edge.link_faces)!=2 for edge in bm.edges),'zero_edges':sum(edge.calc_length()<1e-7 for edge in bm.edges),'tiny_faces':sum(f.calc_area()<1e-12 for f in bm.faces),'signed_volume_m3':bm.calc_volume(signed=True),'bounds_m':[[min(v[i] for v in p) for i in range(3)],[max(v[i] for v in p) for i in range(3)]]}
    bm.free();e.to_mesh_clear();return p,BVHTree.FromPolygons(p,faces),stats
shells={};errors=[]
for name in ['V10_SEAT_COMPLETE_COVER','V10_BACK_COMPLETE_COVER']:
    o=bpy.data.objects[name];p,t,s=geometry(o);shells[name]=s
    assert not any(s[k] for k in ['nonmanifold_edges','zero_edges','tiny_faces']) and s['signed_volume_m3']>0,(name,s)
    assert [m.name for m in o.data.materials]==['V5_NATURAL_FLAX_COTTON']
sp,st,_=geometry(bpy.data.objects['V10_SEAT_COMPLETE_COVER']);bp,bt,_=geometry(bpy.data.objects['V10_BACK_COMPLETE_COVER'])
intersections=st.overlap(bt)
if intersections:errors.append('seat/back surface intersections: '+str(len(intersections)))
timber_intersections=[];supported_deck_contacts=[]
for item in a['frame_map']:
    obj=bpy.data.objects[item['candidate']];tree=geometry(obj)[1]
    overlap=st.overlap(tree)
    if overlap:
        if obj.name=='V10_SEAT_ASH_DECK' and min(p.z for p in sp)>=.285-1e-6:
            supported_deck_contacts.append({'timber':obj.name,'coplanar_contact_pairs':len(overlap),'seat_below_deck_top':False})
        else:timber_intersections.append({'soft':'seat','timber':obj.name})
    if bt.overlap(tree):timber_intersections.append({'soft':'back','timber':obj.name})
if timber_intersections:errors.append('soft/timber surface intersections: '+str(timber_intersections))
gaps=[]
for p in bp:
    if p.z<.56:
        hit=st.ray_cast(Vector((p.x,p.y,2)),Vector((0,0,-1)))
        if hit[0] is not None:gaps.append(p.z-hit[0].z)
if not gaps or not(-.001<min(gaps)<.003):errors.append('back support gap outside gate: '+str(min(gaps) if gaps else None))
if abs(min(p.z for p in sp)-.285)>.001:errors.append('seat/deck support gap')
N=96;stride=97**2;ring=list(range(97))+[j*97+96 for j in range(1,97)]+[96*97+i for i in range(95,-1,-1)]+[j*97 for j in range(95,0,-1)]
seam_errors=[]
for name in ['V10_SEAT_COMPLETE_COVER','V10_BACK_COMPLETE_COVER']:
    obj=bpy.data.objects[name];pts,surface,_=geometry(obj)
    for label,ids in [('bottom',ring),('top',[i+stride for i in ring])]:
        welt=bpy.data.objects[name+'_'+label+'_welt'];error=max(surface.find_nearest(welt.matrix_world@Vector(p.co[:3]))[3] for p in welt.data.splines[0].points);seam_errors.append(error);assert error<1e-6,(name,label,error)
seat_top=shells['V10_SEAT_COMPLETE_COVER']['bounds_m'][1][2];top=shells['V10_BACK_COMPLETE_COVER']['bounds_m'][1][2]
if abs(seat_top-.482527614)>.010:errors.append('seat crown differs from V7 >10mm')
if abs(top-.809930801)>.010:errors.append('pair top differs from V7 >10mm')
missing=[im.name for im in bpy.data.images if im.source=='FILE' and not im.packed_file and not Path(bpy.path.abspath(im.filepath)).exists()];assert not missing
report={'status':'FAIL' if errors else 'PASS_TECHNICAL_ONLY','errors':errors,'output_sha256':a['output_sha256'],'protected_files':len(protected),'baseline_objects_preserved':len(source),'frame_copies_preserved':len(a['frame_map']),'source_shaders_camera_light_world_grade_preserved':True,'guides_hidden_by_default':guide_hidden,'shells':shells,'seat_back_surface_intersection_pairs':len(intersections),'soft_timber_surface_intersections':timber_intersections,'declared_seat_deck_contacts':supported_deck_contacts,'minimum_back_to_seat_vertex_gap_mm':min(gaps)*1000 if gaps else None,'seat_bottom_to_deck_gap_mm':(min(p.z for p in sp)-.285)*1000,'max_seam_attachment_error_m':max(seam_errors),'packed_images':sum(bool(im.packed_file) for im in bpy.data.images),'missing_images':missing,'seat_crown_mm':seat_top*1000,'total_height_mm':top*1000,'old700mm_conflict_mm':top*1000-700,'not_approved':['appearance','procurement SKU','final seat height','foam/down mechanics','house installation']}
(RUN/'VERIFICATION.json').write_text(json.dumps(report,indent=2)+'\n');print('V10_VERIFY',json.dumps(report))
assert not errors,errors
