"""V4 derivative: material-family correction and same-construction soft cover revision."""
import bpy,hashlib,json,math,struct
from pathlib import Path
from mathutils import Vector

ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'design/lookdev_v5';SOURCE=ROOT/'design/product_rebuild_v4/LIVING_DINING_PRODUCT_REBUILD_V4.blend'
assert hashlib.sha256(SOURCE.read_bytes()).hexdigest()=='c3e1060afa1c98ec64d9e8e15fdfaa0fbf3fb5af39aaebc452b553a96b8f3f39'
bpy.ops.wm.open_mainfile(filepath=str(SOURCE));scene=bpy.context.scene
def fingerprint(o):
    h=hashlib.sha256()
    for v in o.data.vertices:h.update(struct.pack('<fff',*v.co))
    for f in o.data.polygons:h.update(struct.pack('<'+'I'*len(f.vertices),*f.vertices))
    return {'sha256':h.hexdigest(),'matrix_world':[float(v) for row in o.matrix_world for v in row]}
baseline={o.name:fingerprint(o) for o in scene.objects if o.type=='MESH'}
original_wood=bpy.data.materials['V4_ASH_WAX_OIL_FROM_REAL_CATALOG'];wood=original_wood.copy();wood.name='V5_NATURAL_ASH_PLANKS_OIL'
maps=json.loads((OUT/'assets/ash_furniture_atlas/manifest.json').read_text())
nodes=wood.node_tree.nodes;links=wood.node_tree.links;p=next(n for n in nodes if n.type=='BSDF_PRINCIPLED')
mapping=next(n for n in nodes if n.type=='MAPPING');mapping.inputs['Scale'].default_value=(1/2.4,1/.8,1)
for role,input_name in [('color','Base Color'),('roughness','Roughness')]:
    tex=nodes.new('ShaderNodeTexImage');tex.name='V5_'+role;tex.image=bpy.data.images.load(maps['files'][role]['path'],check_existing=True);tex.image.colorspace_settings.name=maps['files'][role]['colorspace'];links.new(mapping.outputs[0],tex.inputs['Vector']);links.new(tex.outputs['Color'],p.inputs[input_name])
normal=next(n for n in nodes if n.type=='NORMAL_MAP');normal.inputs['Strength'].default_value=.1
tex=nodes.new('ShaderNodeTexImage');tex.name='V5_normal';tex.image=bpy.data.images.load(maps['files']['normal']['path']);tex.image.colorspace_settings.name='Non-Color';links.new(mapping.outputs[0],tex.inputs['Vector']);links.new(tex.outputs['Color'],normal.inputs['Color'])
for dis in [n for n in nodes if n.type=='DISPLACEMENT']:
    tex=nodes.new('ShaderNodeTexImage');tex.name='V5_height';tex.image=bpy.data.images.load(maps['files']['height']['path']);tex.image.colorspace_settings.name='Non-Color';links.new(mapping.outputs[0],tex.inputs['Vector']);links.new(tex.outputs['Color'],dis.inputs['Height']);dis.inputs['Scale'].default_value=.00004
# Oil-finished furniture keeps native IOR and uses the vendor surface maps; no glossy lacquer added.
wood.diffuse_color=(.31,.195,.102,1)
cloth=bpy.data.materials['V4_OATMEAL_LINEN_NATIVE'].copy();cloth.name='V5_NATURAL_FLAX_COTTON'
cp=next(n for n in cloth.node_tree.nodes if n.type=='BSDF_PRINCIPLED')
cp.inputs['Subsurface Weight'].default_value=0
for n in cloth.node_tree.nodes:
    if n.type=='MIX_RGB' and n.blend_type=='MULTIPLY':n.inputs[2].default_value=(.40,.34,.255,1)
cloth.diffuse_color=(.40,.34,.255,1)
wood_objects=[]
for o in scene.objects:
    if o.type=='MESH' and o.name.startswith('V4_'):
        for slot in o.material_slots:
            if slot.material==original_wood:slot.material=wood;wood_objects.append(o.name)
with bpy.data.libraries.load(str(OUT/'soft_form_v3/LOOSE_COTTON_FORMS.blend'),link=False) as(a,b):
    b.objects=['SEAT_LOOSE_COTTON_STATIC','BACK_LOOSE_COTTON_STATIC']
forms={o.name:o.data for o in b.objects}
changed=[]
def cover(name,size,kind):
    o=bpy.data.objects[name];form=forms[kind+'_LOOSE_COTTON_STATIC'];lo=[min(v.co[i] for v in form.vertices) for i in range(3)];hi=[max(v.co[i] for v in form.vertices) for i in range(3)]
    vertices=[];rad=min(.05,size[0]*.12,size[1]*.12)
    for v in form.vertices:
        q=Vector(tuple((v.co[i]-(hi[i]+lo[i])*.5)/(hi[i]-lo[i])*size[i] for i in range(3)))
        # Boxing thickness is preserved at the seam; reference seat covers are not knife edged.
        edge=max(abs(q.x)/(size[0]/2),abs(q.y)/(size[1]/2))
        if edge>.84:
            blend=min(1,(edge-.84)/.16)
            if q.z!=0:q.z=math.copysign((1-blend)*abs(q.z)+blend*max(abs(q.z),size[2]*.32),q.z)
        cx=size[0]/2-rad;cy=size[1]/2-rad
        if abs(q.x)>cx and abs(q.y)>cy:
            dx=abs(q.x)-cx;dy=abs(q.y)-cy;length=math.hypot(dx,dy)
            if length>rad:q.x=math.copysign(cx+dx/length*rad,q.x);q.y=math.copysign(cy+dy/length*rad,q.y)
        if kind=='BACK' and name.startswith('V4_Sofa_back'):q.z-=.04*q.y/(size[1]/2)
        vertices.append(tuple(q))
    me=bpy.data.meshes.new('V5_'+name+'_CottonCover');me.from_pydata(vertices,[],[tuple(f.vertices) for f in form.polygons]);me.update();me.materials.append(cloth);o.data=me
    for modifier in list(o.modifiers):o.modifiers.remove(modifier)
    for f in me.polygons:f.use_smooth=True
    # Pattern UVs precede deformation: preserve real yarn density through the cloth folds.
    uv=me.uv_layers.new(name='ProductMeters');uv.active_render=True
    N=28;stride=(N+1)**2
    for f in me.polygons:
        side=min(f.vertices)<stride<=max(f.vertices)
        if side:
            extent=[max(vertices[v][a] for v in f.vertices)-min(vertices[v][a] for v in f.vertices) for a in range(2)]
            axis=0 if extent[0]>=extent[1] else 1
        for li in f.loop_indices:
            vi=me.loops[li].vertex_index;idx=vi%stride;j,i=divmod(idx,N+1)
            uv.data[li].uv=(((i if axis==0 else j)/N-.5)*size[axis],(1 if vi>=stride else -1)*size[2]*.28) if side else ((i/N-.5)*size[0],(j/N-.5)*size[1])
    sub=o.modifiers.new('Cotton surface refinement','SUBSURF');sub.levels=1;sub.render_levels=2
    # Catmull-Clark rounds the sewn perimeter inward. Apply it, then restore the
    # documented local envelope so softness does not silently widen product gaps.
    bpy.context.view_layer.objects.active=o;o.select_set(True);bpy.ops.object.modifier_apply(modifier=sub.name)
    me=o.data
    lo=[min(v.co[i] for v in me.vertices) for i in range(3)];hi=[max(v.co[i] for v in me.vertices) for i in range(3)]
    for v in me.vertices:
        for i in range(3):v.co[i]=(v.co[i]-(lo[i]+hi[i])*.5)/(hi[i]-lo[i])*size[i]
    # Sewn welt follows the paired fabric edge, rather than the ideal undeformed rectangle.
    ring=list(range(N+1))+[j*(N+1)+N for j in range(1,N+1)]+[N*(N+1)+i for i in range(N-1,-1,-1)]+[j*(N+1) for j in range(N-1,0,-1)]
    welt=bpy.data.objects.get(name+'_sewn_welt')
    if welt:
        c=bpy.data.curves.new('V5_' + name+'_ActualSewnEdge','CURVE');c.dimensions='3D';c.bevel_depth=.0011;c.bevel_resolution=3;s=c.splines.new('POLY');s.points.add(len(ring)-1)
        for point,idx in zip(s.points,ring):
            point.co=(*((Vector(vertices[idx])+Vector(vertices[idx+stride]))*.5),1)
        s.use_cyclic_u=True;c.materials.append(welt.data.materials[0]);welt.data=c
    changed.append(name)
for name,size,kind in [
('V4_Sofa_chaise_upholstery',(1.555,1.032,.155),'SEAT'),('V4_Sofa_seat_middle',(.891,1.025,.155),'SEAT'),('V4_Sofa_seat_north',(.891,1.025,.155),'SEAT'),
('V4_Sofa_back_0',(1.027,.296,.214),'BACK'),('V4_Sofa_back_1',(1.027,.296,.214),'BACK'),('V4_Sofa_back_2',(1.027,.296,.214),'BACK'),
('V4_Chaise_full_seat',(1.151,.784,.112),'SEAT'),('V4_Chaise_full_back',(.616,.784,.094),'BACK')]:cover(name,size,kind)
# Seat pad material also follows the flax family; its already validated chair geometry stays unchanged.
for o in scene.objects:
    if o.type=='MESH' and o.name.startswith('V4_Chair_upholstered'):
        for slot in o.material_slots:
            if slot.material and slot.material.name=='V4_OATMEAL_LINEN_NATIVE':slot.material=cloth
for o in b.objects:bpy.data.objects.remove(o,do_unlink=True)
# Persist a controlled isolated material test inside a separate, disabled collection.
test=bpy.data.collections.new('V5_ISOLATED_LOOKDEV');scene.collection.children.link(test)
def plate(name,x,material):
    bpy.ops.mesh.primitive_cube_add(size=1,location=(x,0,.16));o=bpy.context.object;o.name=name;o.dimensions=(.75,.68,.038);bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
    for col in list(o.users_collection):col.objects.unlink(o)
    test.objects.link(o);o.data.materials.append(material)
    uv=o.data.uv_layers.new(name='ProductMeters');uv.active_render=True
    for face in o.data.polygons:
        for li in face.loop_indices:
            v=o.data.vertices[o.data.loops[li].vertex_index].co;uv.data[li].uv=(v.x,v.y)
    bevel=o.modifiers.new('Furniture eased edge','BEVEL');bevel.width=.005;bevel.segments=4
    return o
plate('V5_STUDY_WOOD_OLD',-.85,original_wood);plate('V5_STUDY_WOOD_NEW',.85,wood)
test.hide_render=True;test.hide_viewport=True
bpy.context.view_layer.update()
for n,state in baseline.items():
    if n not in changed:assert fingerprint(bpy.data.objects[n])==state,n
(OUT/'UNCHANGED_GEOMETRY.json').write_text(json.dumps({n:v for n,v in baseline.items() if n not in changed},indent=2)+'\n')
for image in bpy.data.images:
    if image.source=='FILE' and not image.packed_file:
        if Path(bpy.path.abspath(image.filepath)).exists():image.pack()
scene['v5_test']='Natural ash family, flax material and supported cotton cut-pattern correction; no owner acceptance implied'
dest=OUT/'LIVING_DINING_LOOKDEV_V5.blend';bpy.ops.wm.save_as_mainfile(filepath=str(dest))
report={'status':'BUILT_PENDING_VISUAL_REVIEW','source_sha256':hashlib.sha256(SOURCE.read_bytes()).hexdigest(),'output':str(dest),'output_sha256':hashlib.sha256(dest.read_bytes()).hexdigest(),'changed_soft_meshes':changed,'preserved_meshes':len(baseline)-len(changed),'wood_assigned_objects':wood_objects,'wood_maps':maps,'cloth_changes':'original native rough_linen maps retained;warm flax base;legacy5cm subsurface removed;patternUV','lighting_camera_color_management':'allV4roomsettingspreserved','whole_house_batch':False,'image2_requests':0}
(OUT/'BUILD_AUDIT.json').write_text(json.dumps(report,indent=2)+'\n');print('LOOKDEV_V5_READY',len(changed),len(wood_objects))
