"""Differentiate supported foam/jacket seat and loose filled back forms.

Owner catalog + researched manufacturer construction informs this custom study.
Static reference-constrained shaping, not calibrated foam/feather simulation.
"""
import bpy,hashlib,json,math,sys
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'design/sofa_fill_form_v10'
args=sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else [];variant=args[0] if args else 'form1';RUN=OUT/variant;RUN.mkdir(exist_ok=True)
refined=variant!='form1'
finished=variant=='delivery'
dest=RUN/'SOFA_DIFFERENTIATED_FILL_V10.blend'
if dest.exists():raise SystemExit('Preserved version exists; use a new output version.')
SOURCE=ROOT/'design/sofa_soft_pilot_v8/render_diagnosis/V7_SAME_MESH_DIRECTIONAL_LIGHT_V8.blend'
assert hashlib.sha256(SOURCE.read_bytes()).hexdigest()=='cbed4cc4b34c9ebe5fc1bf8a388a860d620493b7f8bd609770499b967c37862f'
bpy.ops.wm.open_mainfile(filepath=str(SOURCE));scene=bpy.context.scene
base=bpy.data.collections['V7_RELAXED_PAIR'];base.name='V7_COMPARISON_PAIR';base.hide_render=True;base.hide_viewport=True
candidate=bpy.data.collections.new('V10_FILL_FORM_PAIR');scene.collection.children.link(candidate)
guides=bpy.data.collections.new('V10_CONSTRUCTION_GUIDE');scene.collection.children.link(guides)
frame_map=[]
for old in list(base.objects):
    if 'COMPLETE_COVER' in old.name:continue
    obj=old.copy();obj.data=old.data.copy();obj.name=old.name.replace('V7_','V10_',1);candidate.objects.link(obj);obj.hide_render=False;obj.hide_viewport=False;obj.hide_set(False)
    frame_map.append({'source':old.name,'candidate':obj.name})
cloth=bpy.data.materials['V5_NATURAL_FLAX_COTTON'];weltmat=bpy.data.materials['V6_FLAX_SEWN_WELT']
N=96
def smooth(t):
    t=max(0,min(1,t));return t*t*(3-2*t)
def outline(u,v,w,d,k):return u*w/2*math.sqrt(1-k*v*v/2),v*d/2*math.sqrt(1-k*u*u/2)
def crease(x,y,start,end,width,depth):
    a,b,q=Vector(start),Vector(end),Vector((x,y));ab=b-a;t=(q-a).dot(ab)/ab.length_squared
    if not 0<t<1:return 0
    distance=(q-a-t*ab).length
    return depth*math.sin(math.pi*t)**.75*(-math.exp(-.5*(distance/width)**2)+.23*math.exp(-.5*(distance/(width*2.8))**2))
# Same four local seam families as V7; reduce sharp dents, do not add wrinkles.
SEAT_FOLDS=[((-.35,-.445),(-.29,-.27),.016,.004),((.24,-.445),(.21,-.31),.018,.0035),((-.512,-.20),(-.38,-.135),.015,.003),((.512,.09),(.385,.13),.017,.003)]
BACK_FOLDS=[((-.31,-.182),(-.245,-.035),.025,.008),((.18,-.182),(.145,-.07),.026,.006),((-.48,.145),(-.37,.06),.024,.005),((.50,.12),(.40,.045),.024,.0045)]
def profile(u,v,kind):
    x,y=outline(u,v,1.025 if kind=='seat' else 1.027,.891 if kind=='seat' else .365,.20 if kind=='seat' else .38)
    edge=max(abs(u),abs(v))
    if kind=='seat':
        # Core keeps the central area supported; jacket rolls over a shorter rim.
        f=max(0,1-abs(u)**4)**.62*max(0,1-abs(v)**4)**.62
        high=.416+.069*f-.0025*math.exp(-((x+.08)/.28)**2-((y-.04)/.26)**2)
        high-=.004*math.exp(-((x+.34)/.16)**2)*smooth((edge-.65)/.35)
        high+=sum(crease(x,y,*c) for c in SEAT_FOLDS)
        low=.285+.022*smooth((edge-.55)/.45)
    else:
        # Filled bag: broad rounded mass, unequal channel loft, quiet sewn edges.
        f=max(0,1-u*u)**.48*max(0,1-v*v)**.56
        mass=1+.08*math.exp(-((x+.23)/.22)**2)+.035*math.exp(-((x-.27)/.23)**2)
        mass*=1+.075*math.exp(-((v+.20)/.65)**2)
        high=.029+.116*f*mass+sum(crease(x,y,*c) for c in BACK_FOLDS)
        low=-.027-.071*f
    return x,y,low,high
def make_cover(name,kind):
    vertices=[];coords=[];faces=[]
    for layer in [0,1]:
        for j in range(N+1):
            for i in range(N+1):
                u,v=2*i/N-1,2*j/N-1;x,y,low,high=profile(u,v,kind);scale=.989 if layer==0 else .983
                p=Vector((x*scale,y*scale,high if layer else low))
                if kind=='back':
                    top=math.exp(-((v-1)/.29)**2)
                    p.y-=top*(.008*(abs(x)/.5135)**3+.005*math.exp(-((x-.28)/.18)**2))
                vertices.append(tuple(p));coords.append((x,y))
    stride=(N+1)**2
    for layer in [0,1]:
        for j in range(N):
            for i in range(N):
                a=layer*stride+j*(N+1)+i;face=(a,a+1,a+N+2,a+N+1);faces.append(face if layer else tuple(reversed(face)))
    ring=list(range(N+1))+[j*(N+1)+N for j in range(1,N+1)]+[N*(N+1)+i for i in range(N-1,-1,-1)]+[j*(N+1) for j in range(N-1,0,-1)]
    rings=[ring]
    # Lower contact surface must follow convex seat curvature between vertices.
    # The first five boxing rings passed vertex gaps but sliced the seat in faces.
    for t in ([i/16 for i in range(1,16)] if refined else [.12,.28,.5,.72,.88]):
        ids=[]
        for idx in ring:
            a,b=Vector(vertices[idx]),Vector(vertices[idx+stride]);p=a.lerp(b,t);x,y=coords[idx]
            p.x+=x*.022*math.sin(math.pi*t);p.y+=y*.022*math.sin(math.pi*t)
            ids.append(len(vertices));vertices.append(tuple(p));coords.append((x,y))
        rings.append(ids)
    rings.append([i+stride for i in ring])
    for a,b in zip(rings,rings[1:]):
        for i in range(len(ring)):
            j=(i+1)%len(ring);faces.append((a[i],a[j],b[j],b[i]))
    mesh=bpy.data.meshes.new(name);mesh.from_pydata(vertices,[],faces);mesh.update();obj=bpy.data.objects.new(name,mesh);candidate.objects.link(obj);mesh.materials.append(cloth)
    for face in mesh.polygons:face.use_smooth=True
    uv=mesh.uv_layers.new(name='ProductMeters');uv.active_render=True
    for face in mesh.polygons:
        side=any(i>=2*stride for i in face.vertices)
        for li in face.loop_indices:
            p=mesh.vertices[mesh.loops[li].vertex_index].co
            uv.data[li].uv=(p.x,p.z) if side and abs(face.normal.y)>abs(face.normal.x) else ((p.y,p.z) if side else (p.x,p.y))
    obj['construction']='supported polyurethane foam core with soft jacket' if kind=='seat' else 'channel-filled fiber/feather bag; broad support compression'
    obj['reference']='owner catalog p4/p8 + OWNER_RELAXED_COVER.png + Vanguard construction examples'
    obj['method']='reference-constrained static exterior; not physical foam/down solver'
    return obj,ring,stride
seat,sring,sstride=make_cover('V10_SEAT_COMPLETE_COVER','seat');back,bring,bstride=make_cover('V10_BACK_COMPLETE_COVER','back')
back.matrix_world=bpy.data.objects['V7_BACK_COMPLETE_COVER'].matrix_basis.copy();bpy.context.view_layer.update()
def geometry(obj):
    e=obj.evaluated_get(bpy.context.evaluated_depsgraph_get());me=e.to_mesh();p=[e.matrix_world@v.co for v in me.vertices];f=[tuple(face.vertices) for face in me.polygons];e.to_mesh_clear();return p,f
def points(obj):return geometry(obj)[0]
def tree(obj):
    p,f=geometry(obj);return BVHTree.FromPolygons(p,f)
st=tree(seat);inv=back.matrix_world.inverted();support_deltas=[]
contact_clearance=.0018 if refined else .0012
# Conform only the lower filled bag; the upper bag elevation is not translated.
for vertex in back.data.vertices:
    local=vertex.co.copy();p=back.matrix_world@local
    weight=smooth((-local.y/(.365/2)-.62)/.32)
    if p.z<.56:
        # Extend the rear contact boundary smoothly for the short rim that lies
        # behind the seat: do not let an unprojected rear tail hang down 45mm.
        probe=Vector((p.x,min(p.y,.430) if refined else p.y,2))
        hit=st.ray_cast(probe,Vector((0,0,-1)))
        if hit[0] is not None:
            delta=hit[0].z+contact_clearance-p.z
            if delta>0:p.z+=delta
            elif weight>0:p.z+=max(-.045,delta)*weight
            support_deltas.append(p.z-(back.matrix_world@local).z)
    vertex.co=inv@p
# Locally wrap the retained rear timber contact, never move the wood rail.
for vertex in back.data.vertices:
    p=back.matrix_world@vertex.co;dz=abs(p.z-.587)
    if p.y>.5495 and dz<.053:p.y-=(p.y-.5495)*(1-smooth((dz-.038)/.015))
    vertex.co=inv@p
back.data.update();bpy.context.view_layer.update()
if finished:
    for obj in [seat,back]:
        mod=obj.modifiers.new('Finished sewn panel rollover','SUBSURF');mod.subdivision_type='CATMULL_CLARK';mod.levels=1;mod.render_levels=1
    bpy.context.view_layer.update()
def seam(obj,ring,stride):
    surface=tree(obj) if finished else None
    for label,ids in [('bottom',ring),('top',[i+stride for i in ring])]:
        name=obj.name+'_'+label+'_welt';data=bpy.data.curves.new(name,'CURVE');data.dimensions='3D';data.bevel_depth=.00115;data.bevel_resolution=3
        spline=data.splines.new('POLY');spline.points.add(len(ids)-1);spline.use_cyclic_u=True
        for p,i in zip(spline.points,ids):
            point=obj.matrix_world@obj.data.vertices[i].co
            if surface:
                # The evaluated subdivision changes vertex ordering. Transfer
                # the durable sewing path to the actual finished surface by
                # nearest-surface projection, rather than assuming index identity.
                nearest=surface.find_nearest(point)
                assert nearest[0] is not None and nearest[3]<.006,('seam transfer too far',obj.name,label,nearest[3])
                point=nearest[0]
            p.co=(*point,1)
        obj2=bpy.data.objects.new(name,data);candidate.objects.link(obj2);data.materials.append(weltmat)
for obj,r,s in [(seat,sring,sstride),(back,bring,bstride)]:seam(obj,r,s)
def mat(name,color):
    m=bpy.data.materials.new(name);m.use_nodes=True;m.diffuse_color=(*color,1);p=m.node_tree.nodes.get('Principled BSDF');p.inputs['Base Color'].default_value=(*color,1);p.inputs['Roughness'].default_value=.9;return m
foam=mat('V10_FOAM_GUIDE',(.67,.49,.22));wrap=mat('V10_SOFT_WRAP_GUIDE',(.83,.73,.49));fill=mat('V10_BACK_FILL_GUIDE',(.71,.77,.67))
bpy.ops.mesh.primitive_cube_add(size=1,location=(0,0,.364));core=bpy.context.object;core.name='V10_SUPPORTED_FOAM_CORE_GUIDE';core.dimensions=(.950,.785,.130);bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
for c in list(core.users_collection):c.objects.unlink(core)
guides.objects.link(core);core.data.materials.append(foam);bevel=core.modifiers.new('Soft core edge guide','BEVEL');bevel.width=.025;bevel.segments=6;core.modifiers.new('Guide normals','WEIGHTED_NORMAL')
core['status']='custom trial construction guide, not manufacturer section or approved foam firmness'
envelope=seat.copy();envelope.data=seat.data.copy();envelope.name='V10_SOFT_JACKET_ENVELOPE_GUIDE';guides.objects.link(envelope);envelope.data.materials.clear();envelope.data.materials.append(wrap)
boolean=envelope.modifiers.new('Soft jacket around foam guide','BOOLEAN');boolean.operation='DIFFERENCE';boolean.solver='EXACT';boolean.object=core
for i,x in enumerate([-.30,0,.30]):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=48,ring_count=24,radius=1,location=(0,0,0));o=bpy.context.object;o.name='V10_BACK_FILL_CHANNEL_GUIDE_'+str(i)
    for c in list(o.users_collection):c.objects.unlink(o)
    guides.objects.link(o);o.data.materials.append(fill);o.matrix_world=back.matrix_world.copy();o.location=back.matrix_world@Vector((x,-.01,.01));o.scale=(.145,.115,.060)
    for f in o.data.polygons:f.use_smooth=True
    o['status']='illustrative filling channel, not actual manufacturing shape'
guides.hide_render=True;guides.hide_viewport=True;scene.camera=bpy.data.objects['V6_THREE_QUARTER']
def bounds(obj):
    p=points(obj);return [[min(v[i] for v in p) for i in range(3)],[max(v[i] for v in p) for i in range(3)]]
bpy.ops.wm.save_as_mainfile(filepath=str(dest))
report={'source':str(SOURCE),'source_sha256':hashlib.sha256(SOURCE.read_bytes()).hexdigest(),'output':str(dest),'output_sha256':hashlib.sha256(dest.read_bytes()).hexdigest(),'variant':variant,'seat_bounds_m':bounds(seat),'back_bounds_m':bounds(back),'frame_map':frame_map,'core_guide_dimensions_mm':[950,785,130],'nominal_boxing_mm':109,'source_v6_boxing_mm':142,'seam_family_count':{'seat':4,'back':4},'contact_clearance_mm':contact_clearance*1000,'boxing_rings':15 if refined else 5,'finished_subdivision_level':1 if finished else 0,'support_conform_min_max_mm':[min(support_deltas)*1000,max(support_deltas)*1000],'back_whole_object_translation_mm':0,'method':'differentiated core/jacket versus filled-bag mass; static lower support conformation; restrained original seam families','same_shaders_studio':True,'physical_mechanics_certified':False,'internal_dimensions_manufacturing_approved':False,'owner_accepted':False,'whole_house_propagation':False,'image2_requests':0}
(RUN/'BUILD_AUDIT.json').write_text(json.dumps(report,indent=2)+'\n');print('V10_FILL_FORM_READY',json.dumps(report))
