"""Owner finish rules plus grounded, wall-centred reading assembly, derived only."""
import bpy, json, hashlib, struct
from pathlib import Path
from mathutils import Vector

R=Path(__file__).resolve().parents[1];D=R/'design/finishes_v11'
S=R/'design/reading_wall_v10/WHOLE_HOUSE_READING_CLEANUP_V10.blend'
O=D/'WHOLE_HOUSE_FINISHES_READING_V11.blend'
SHA='3a53903a90bc55fa2e3dcbdbc77fd662827946390f3d98b024299f69161dfc29'
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
assert sha(S)==SHA and not O.exists()
protected=json.loads((R/'design/whole_house_model_v1/PRESERVATION.json').read_text())['files']
for f in protected:assert sha(f['path'])==f['sha256'],f['path']
bpy.ops.wm.open_mainfile(filepath=str(S));s=bpy.context.scene
hides={o.name:(o.hide_viewport,{l.name:o.hide_get(view_layer=l) for l in s.view_layers}) for o in bpy.data.objects}
for c in bpy.data.collections:c.hide_viewport=False
for o in bpy.data.objects:o.hide_viewport=False;o.hide_set(False)
bpy.context.view_layer.update()
def meshhash(o):
    h=hashlib.sha256()
    if o.type=='MESH':
        for v in o.data.vertices:h.update(struct.pack('<fff',*v.co))
        for f in o.data.polygons:h.update(struct.pack('<'+'I'*len(f.vertices),*f.vertices))
    return h.hexdigest()
before={o.name:{'mesh':meshhash(o),'matrix':[list(r) for r in o.matrix_world], 'hide_render':o.hide_render, 'materials':[m.name if m else None for m in o.data.materials] if o.type=='MESH' else [], 'light_energy':o.data.energy if o.type=='LIGHT' else None} for o in bpy.data.objects}
col=bpy.data.collections.new('V11_OWNER_SURFACE_FINISHES');s.collection.children.link(col)
def material(n,c,rough):
    m=bpy.data.materials.new(n);m.use_nodes=True;m.diffuse_color=(*c,1)
    p=m.node_tree.nodes.get('Principled BSDF');p.inputs['Base Color'].default_value=(*c,1);p.inputs['Roughness'].default_value=rough;p.inputs['Metallic'].default_value=0
    return m,p
wood,p=material('V11_UNIFIED_PALE_ASH_FLOOR',(.42,.325,.215),.46)
tile,p2=material('V11_OWNER_WHITE_SUBTLE_MARBLE_600x1200',(.84,.83,.81),.38)
wall,p3=material('V11_WARM_WHITE_LATEX',(.78,.76,.71),.86)
for m,p,path in [(wood,p,D/'assets/pale_ash_floor_1200x1080.jpg'),(tile,p2,D/'assets/owner_subtle_marble_1200x600.jpg')]:
    t=m.node_tree.nodes.new('ShaderNodeTexImage');t.image=bpy.data.images.load(str(path),check_existing=True);t.image.pack()
    uv=m.node_tree.nodes.new('ShaderNodeUVMap');uv.uv_map='V11_FinishUV';m.node_tree.links.new(uv.outputs[0],t.inputs['Vector']);m.node_tree.links.new(t.outputs['Color'],p.inputs['Base Color'])
    m['reference_manifest']=str(D/'assets/manifest.json')
# Reuse the existing wall microtexture, rather than introducing decorative relief.
ns=wall.node_tree.nodes;ls=wall.node_tree.links;t=ns.new('ShaderNodeTexNoise');t.inputs['Scale'].default_value=150
b=ns.new('ShaderNodeBump');b.inputs['Distance'].default_value=.00015;b.inputs['Strength'].default_value=.13;ls.new(t.outputs['Fac'],b.inputs['Height']);ls.new(b.outputs[0],p3.inputs['Normal'])
def uv(o,repeat):
    me=o.data;layer=me.uv_layers.get('V11_FinishUV') or me.uv_layers.new(name='V11_FinishUV');me.uv_layers.active=layer
    for l in me.uv_layers:l.active_render=(l==layer)
    for f in me.polygons:
        n=o.matrix_world.to_3x3()@f.normal;ax=max(range(3),key=lambda k:abs(n[k]));axes=[k for k in range(3) if k!=ax]
        for li in f.loop_indices:
            v=o.matrix_world@me.vertices[me.loops[li].vertex_index].co;layer.data[li].uv=(v[axes[0]]/repeat[0],v[axes[1]]/repeat[1])
changes=[]
def assign(o,m,repeat=None):
    o.data=o.data.copy();o.data.materials.clear();o.data.materials.append(m)
    for p in o.data.polygons:p.material_index=0
    if repeat:uv(o,repeat)
    changes.append({'object':o.name,'material':m.name})
wet={'kitchen','master_bath','secondary_bath','guest_bath','north_sunroom'}
wall_objects=[]
for o in list(s.objects):
    if o.type!='MESH' or o.hide_render:continue
    if o.name.startswith(('PRESENTATION_FLOOR_','PRESENTATION_TILE_')):
        room=o.name.split('_',2)[2];m=tile if room in wet else wood;assign(o,m,(1.2,.6) if m==tile else (1.2,1.08));o['owner_finish_room']=room
    elif o.name in ['FLOOR_LOWER','R4_UPPER_FLOOR_CONTINUOUS_STRAIGHT_THRESHOLD','FLOOR_UPPER_SEAM_2','FLOOR_UPPER_SEAM_3','STEP_0','STEP_1','STEP_2']:
        assign(o,wood,(1.2,1.08))
    elif o.name=='R3_BATH_FLOOR':assign(o,tile,(1.2,.6))
    elif o.name.startswith('VIEW_WALL_') or any(m and m.name=='AM2_WARM_IVORY_WALL' for m in o.data.materials):
        # Only genuine architecture wall finish, never furniture containing WALL.
        assign(o,wall);wall_objects.append(o)
# Tile skins use clipped EXISTING vertical faces; no new walls or filled openings.
# Current floor patches define finish extents. They are not promoted to semantic GT.
plan=json.loads((R/'renders/whole_house_final_study_v1/00_MANIFEST/WHOLE_HOUSE_ROOM_MANIFEST_V1.json').read_text())
wetwalls=[r for r in plan['rooms'] if r['room_id'] in wet-{'north_sunroom'}]
def clip(poly,axis,edge,keep_greater):
    out=[]
    if not poly:return out
    for a,b in zip(poly,poly[1:]+poly[:1]):
        ia=(a[axis]>=edge-1e-7) if keep_greater else (a[axis]<=edge+1e-7)
        ib=(b[axis]>=edge-1e-7) if keep_greater else (b[axis]<=edge+1e-7)
        if ia:out.append(a)
        if ia!=ib:
            f=(edge-a[axis])/(b[axis]-a[axis]);out.append(a+(b-a)*f)
    return out
skins=[]
for r in wetwalls:
    x0,y0,x1,y1=r['bounds_xy'];z0=r['floor_z'];vs=[];faces=[];sources=[]
    for o in wall_objects:
        for f in o.data.polygons:
            n=(o.matrix_world.to_3x3()@f.normal).normalized()
            if abs(n.z)>.01:continue
            points=[o.matrix_world@o.data.vertices[i].co for i in f.vertices]
            # A point10mm inward must fall inside the actual finish rectangle.
            center=sum(points,Vector())/len(points);probe=center+n*.01
            # Clip first so long faces extending beyond a room remain eligible.
            poly=points
            for axis,lo,hi in [(0,x0-.0001,x1+.0001),(1,y0-.0001,y1+.0001),(2,z0,3.25 if z0>.1 else 2.8)]:
                poly=clip(poly,axis,lo,True);poly=clip(poly,axis,hi,False)
            if len(poly)<3:continue
            c=sum(poly,Vector())/len(poly);q=c+n*.01
            if not (x0+.001<q.x<x1-.001 and y0+.001<q.y<y1-.001):continue
            area=sum((poly[i]-poly[0]).cross(poly[i+1]-poly[0]).length/2 for i in range(1,len(poly)-1))
            if area<1e-6:continue
            start=len(vs);vs.extend([tuple(p+n*.0008) for p in poly]);faces.append(tuple(range(start,start+len(poly))));sources.append(o.name)
    assert faces,'No interior tile faces '+r['room_id']
    me=bpy.data.meshes.new('V11_TILE_SKIN_'+r['room_id']);me.from_pydata(vs,[],faces);me.update();o=bpy.data.objects.new(me.name,me);col.objects.link(o);me.materials.append(tile);uv(o,(1.2,.6));o['authority']='DERIVED_FINISH_SKIN_FROM_EXISTING_FACES';o['source_walls']=json.dumps(sorted(set(sources)));skins.append({'object':o.name,'faces':len(faces),'source_walls':sorted(set(sources))})
# Floor-standing rack centred on the usable wall between south door trim and north end.
a=json.loads((R/'design/reading_wall_v10/BUILD_AUDIT.json').read_text());roots=[bpy.data.objects[n] for n in a['root_objects']]
target_y=(4.8390627+6.50724983215332)/2
delta=Vector((0,target_y-5.30,.4505-.955))
for o in roots:o.location+=delta
bpy.context.view_layer.update()
def bbox(o):
    e=o.evaluated_get(bpy.context.evaluated_depsgraph_get());me=e.to_mesh();vs=[e.matrix_world@v.co for v in me.vertices];e.to_mesh_clear();return [[min(v[i] for v in vs) for i in range(3)],[max(v[i] for v in vs) for i in range(3)]]
cab=bbox(bpy.data.objects['READING_5015_SHORT_SLIDING_CABINET'])
assert abs(cab[0][2]-.4505)<1e-5
assert cab[0][1]-4.8390627>.42
# Old short bench remains hidden; retain source object for recoverability.
bench=bpy.data.objects['READING_3205A_PADDED_BENCH'];assert bench.hide_render
for n,(hv,layerhides) in hides.items():
    o=bpy.data.objects[n];o.hide_viewport=hv
    for l in s.view_layers:o.hide_set(layerhides[l.name],view_layer=l)
s['V11_OWNER_FINISH_RULES']='Tile: kitchen,3baths,north sunroom; all other floors unified pale ash. Warm-white latex walls except kitchen/baths600x1200mm subtle owner marble.'
s['V11_READING_RACK']='Floor standing at450.5mm, centred in usable wall; complete assembly and books retained; south door opens inward.'
bpy.context.window.view_layer=s.view_layers['OVERVIEW_CEILING_HIDDEN']
bpy.ops.wm.save_as_mainfile(filepath=str(O))
record={'source':str(S),'source_sha256':SHA,'output':str(O),'sha256':sha(O),'before':before,'finish_assignments':changes,'created_tile_skins':skins,'reading_moved_objects':a['moved_objects'],'reading_extra_translation_m':list(delta),'cabinet_bounds_m':cab,'rack_floor_m':.4505,'cabinet_bottom_above_structural_FFL_mm':.5,'usable_wall_y_m':[4.8390627,6.50724983215332],'cabinet_south_to_door_trim_mm':(cab[0][1]-4.8390627)*1000,'cabinet_north_to_wall_end_mm':(6.50724983215332-cab[1][1])*1000,'hidden_duplicate_bench':bench.name,'protected_sources':protected,'wet_floor_rooms':sorted(wet),'tile_size_mm':[600,1200],'tile_reference':'Owner Image3 texture and Image4 laid appearance; vendor/slip rating not selected','all_original_geometry_unchanged':True,'no_image2':True,'status':'HUMAN_REVIEW'}
(D/'BUILD_AUDIT.json').write_text(json.dumps(record,indent=2)+'\n')
assert sha(S)==SHA
for f in protected:assert sha(f['path'])==f['sha256']
print('FINISHES_V11',record['sha256'],'cabinet',cab,'door_gap_mm',record['cabinet_south_to_door_trim_mm'],'skins',[(x['object'],x['faces']) for x in skins])
