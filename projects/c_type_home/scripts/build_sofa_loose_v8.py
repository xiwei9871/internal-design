"""Rebuild relaxed complete seat/back covers from the owner's close-up.

Reference-guided static exterior, not a gas/foam/feather mechanics claim.
Reuses the documented panel/boxing construction and local fold method, while
replacing the long rigid boxing and normal-only dents that failed in V6/V7.
"""
import bpy, hashlib, json, math, sys
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'design/sofa_soft_pilot_v8'
args=sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else []
variant=args[0] if args else 'form1'
refined=variant=='form2'
RUN=OUT/variant;RUN.mkdir(exist_ok=True)
if (RUN/'SOFA_LOOSE_COVER_V8.blend').exists():
    raise SystemExit('Preserved version exists; choose a new version directory.')
SOURCE=ROOT/'design/sofa_soft_pilot_v7/local_final/SOFA_RELAXED_COVER_V7.blend'
assert hashlib.sha256(SOURCE.read_bytes()).hexdigest()=='5bb0f004a9501bff61a017975cf65c8205f46e3af3a39d9a83c91096db46ec4f'
bpy.ops.wm.open_mainfile(filepath=str(SOURCE));scene=bpy.context.scene
base=bpy.data.collections['V7_RELAXED_PAIR'];base.name='V7_COMPARISON_PAIR'
base.hide_render=True;base.hide_viewport=True
candidate=bpy.data.collections.new('V8_LOOSE_PAIR');scene.collection.children.link(candidate)
for old in list(base.objects):
    if 'COMPLETE_COVER' in old.name:
        continue
    obj=old.copy();obj.data=old.data.copy();obj.name=old.name.replace('V7_','V8_',1)
    candidate.objects.link(obj);obj.hide_render=False;obj.hide_viewport=False;obj.hide_set(False)
cloth=bpy.data.materials['V5_NATURAL_FLAX_COTTON']
weltmat=bpy.data.materials['V6_FLAX_SEWN_WELT']
N=128

def smooth(t):
    t=max(0,min(1,t));return t*t*(3-2*t)

def outline(u,v,w,d,k):
    # Homeomorphic squircle grid: no clamped coincident corner vertices.
    return u*w/2*math.sqrt(1-k*v*v/2),v*d/2*math.sqrt(1-k*u*u/2)

def fold(x,y,start,end,width,depth,bend):
    a,b,q=Vector(start),Vector(end),Vector((x,y));ab=b-a
    t=(q-a).dot(ab)/ab.length_squared
    if not 0<t<1:return 0,Vector((0,0))
    normal=Vector((-ab.y,ab.x)).normalized()
    center=a+ab*t+normal*(bend*math.sin(math.pi*t))
    signed=(q-center).dot(normal)
    envelope=math.sin(math.pi*t)**.55
    # Fabric fold has a ridge, an adjacent shallow valley and tangential gather.
    ridge=math.exp(-.5*((signed-width*.40)/width)**2)
    valley=math.exp(-.5*((signed+width*.85)/(width*.75))**2)
    h=depth*envelope*(ridge-.82*valley)
    tangent=normal*(depth*.30*envelope*math.exp(-.5*(signed/(width*1.8))**2))
    return h,tangent

SEAT_FOLDS=[
    ((-.35,-.47),(-.29,-.21),.021,.008,.025),
    ((-.065,-.47),(-.09,-.30),.014,.0045,-.014),
    ((.32,-.47),(.24,-.22),.022,.008,-.020),
    ((-.55,-.13),(-.25,-.08),.020,.008,.014),
    ((-.55,.235),(-.36,.15),.025,.006,-.012),
    ((.55,.14),(.30,.085),.018,.008,.015),
    ((-.26,.47),(-.205,.26),.022,.006,.016),
    ((.16,.47),(.11,.30),.018,.005,-.010),
]
BACK_FOLDS=[
    ((-.56,.145),(-.14,.09),.016,.009,.022),
    ((-.56,.078),(-.18,.065),.020,.010,-.015),
    ((-.56,.015),(.03,-.012),.018,.011,.016),
    ((.56,.13),(.18,.11),.022,.009,-.019),
    ((.56,.052),(.10,.019),.020,.011,.011),
    ((.56,-.041),(.085,-.089),.018,.010,-.020),
    ((-.24,.215),(-.19,.08),.016,.007,.010),
    ((.235,.215),(.27,.075),.018,.008,-.012),
    ((-.18,-.215),(-.14,-.075),.020,.009,.014),
    ((.32,-.215),(.245,-.08),.021,.009,-.011),
]

def wrinkles(x,y,kind):
    hs=0;shift=Vector((0,0))
    for stroke in SEAT_FOLDS if kind=='seat' else BACK_FOLDS:
        parameters=list(stroke)
        if refined:
            parameters[2]*=1.22 if kind=='back' else 1.10
            parameters[3]*=.72 if kind=='back' else .85
        h,t=fold(x,y,*parameters);hs+=h;shift+=t
    return hs,shift

def profile(u,v,kind):
    x,y=outline(u,v,1.025 if kind=='seat' else 1.027,.891 if kind=='seat' else .380,.25 if kind=='seat' else .30)
    e=max(abs(u),abs(v))
    f=max(0,1-u*u)**.60*max(0,1-v*v)**.57
    h,shift=wrinkles(x,y,kind)
    if kind=='seat':
        # Preserve total loft, redistribute it from rigid sidewall to soft wrap.
        sag=-.007*math.exp(-((x+.09)/.27)**2-((y-.04)/.25)**2)
        variation=.004*math.exp(-((x-.25)/.19)**2-((y+.08)/.23)**2)
        edge_sag=-.009*math.exp(-((x+.32)/.17)**2)*smooth((e-.65)/.35)
        high=.386+.107*f+sag+variation+edge_sag+h
        low=.285+.027*smooth((e-.60)/.40)
    else:
        # Filled back remains full; cover lies in uneven, transverse loose folds.
        lobes=1+.105*math.exp(-((x+.27)/.20)**2)+.075*math.exp(-((x-.26)/.22)**2)-.05*math.exp(-(x/.12)**2)
        high=.021+.120*f*lobes+h
        low=-.021-.079*f
    return x,y,low,high,shift

def make_cover(name,kind):
    vertices=[];faces=[];coords=[]
    for layer in [0,1]:
        for j in range(N+1):
            for i in range(N+1):
                u,v=2*i/N-1,2*j/N-1;x,y,low,high,shift=profile(u,v,kind)
                scale=.985 if layer==0 else .975
                # Rim gathering and cover give, spread across the full local patch.
                xyz=Vector((x*scale+shift.x*(.3 if layer==0 else 1),y*scale+shift.y*(.3 if layer==0 else 1),high if layer else low))
                if kind=='back':
                    # Uneven soft upper shoulder, rather than an exact straight rim.
                    xyz.y-=.007*math.exp(-((y-.19)/.055)**2)*(abs(x)/.5135)**2
                vertices.append(tuple(xyz));coords.append((x,y))
    stride=(N+1)**2
    for layer in [0,1]:
        for j in range(N):
            for i in range(N):
                a=layer*stride+j*(N+1)+i;f=(a,a+1,a+N+2,a+N+1)
                faces.append(f if layer else tuple(reversed(f)))
    ring=list(range(N+1))+[j*(N+1)+N for j in range(1,N+1)]+[N*(N+1)+i for i in range(N-1,-1,-1)]+[j*(N+1) for j in range(N-1,0,-1)]
    rings=[ring]
    for t in [.10,.22,.36,.50,.64,.78,.90]:
        ids=[]
        for idx in ring:
            a,b=Vector(vertices[idx]),Vector(vertices[idx+stride]);p=a.lerp(b,t)
            x,y=coords[idx]
            bulge=.028*math.sin(math.pi*t)
            p.x+=x*bulge;p.y+=y*bulge
            ids.append(len(vertices));vertices.append(tuple(p));coords.append((x,y))
        rings.append(ids)
    rings.append([i+stride for i in ring])
    for a,b in zip(rings,rings[1:]):
        for i in range(len(ring)):
            j=(i+1)%len(ring);faces.append((a[i],a[j],b[j],b[i]))
    mesh=bpy.data.meshes.new(name);mesh.from_pydata(vertices,[],faces);mesh.update()
    obj=bpy.data.objects.new(name,mesh);candidate.objects.link(obj);mesh.materials.append(cloth)
    for face in mesh.polygons:face.use_smooth=True
    uv=mesh.uv_layers.new(name='ProductMeters')
    for face in mesh.polygons:
        side=any(i>=2*stride for i in face.vertices)
        for li in face.loop_indices:
            p=mesh.vertices[mesh.loops[li].vertex_index].co
            uv.data[li].uv=(p.x,p.z) if side and abs(face.normal.y)>abs(face.normal.x) else ((p.y,p.z) if side else (p.x,p.y))
    obj['construction']='foam-core seat with softer wrapping and relaxed cover' if kind=='seat' else 'filled back bag with relaxed sewn cover'
    obj['method']='static complete panel/convex boxing + 3D reference-guided folds; no simulation claim'
    obj['reference']='OWNER_RELAXED_COVER.png + owner ash catalog p4/p8; no exact SKU'
    obj['panel_grid']=N
    return obj,ring,stride

seat,sring,sstride=make_cover('V8_SEAT_COMPLETE_COVER','seat')
back,bring,bstride=make_cover('V8_BACK_COMPLETE_COVER','back')
back.matrix_world=bpy.data.objects['V7_BACK_COMPLETE_COVER'].matrix_basis.copy()
bpy.context.view_layer.update()
def world_points(obj):return [obj.matrix_world@v.co for v in obj.data.vertices]
def tree(obj):return BVHTree.FromPolygons(world_points(obj),[tuple(f.vertices) for f in obj.data.polygons])
st=tree(seat);bp=world_points(back)
def support_gap(offset):
    gaps=[]
    for p in bp:
        if p.z<.57:
            hit=st.ray_cast(Vector((p.x,p.y+offset,2)),Vector((0,0,-1)))
            if hit[0] is not None:gaps.append(p.z-hit[0].z)
    assert gaps,'back has no seat support'
    return min(gaps)
forward=0
if refined:
    # Place the same complete back bag farther onto the curved supporting seat,
    # retaining its original top elevation instead of dropping the whole bag.
    lo,hi=-.070,0
    assert support_gap(lo)<.001<support_gap(hi),'support-placement bracket'
    for _ in range(22):
        mid=(lo+hi)*.5
        if support_gap(mid)>.001:hi=mid
        else:lo=mid
    forward=(lo+hi)*.5
    back.location.y+=forward
shift=.001-support_gap(forward);back.location.z+=shift;bpy.context.view_layer.update()
inv=back.matrix_world.inverted()
for vertex in back.data.vertices:
    p=back.matrix_world@vertex.co;dz=abs(p.z-.587)
    if p.y>.5495 and dz<.053:
        p.y-=(p.y-.5495)*(1-smooth((dz-.038)/.015));vertex.co=inv@p
back.data.update()
def seam(obj,ring,stride):
    points=world_points(obj)
    for label,ids in [('bottom',ring),('top',[i+stride for i in ring])]:
        name=obj.name+'_'+label+'_welt';data=bpy.data.curves.new(name,'CURVE');data.dimensions='3D';data.bevel_depth=.00115;data.bevel_resolution=3
        spline=data.splines.new('POLY');spline.points.add(len(ids)-1);spline.use_cyclic_u=True
        for p,i in zip(spline.points,ids):p.co=(*points[i],1)
        welt=bpy.data.objects.new(name,data);candidate.objects.link(welt);data.materials.append(weltmat)
for o,r,s in [(seat,sring,sstride),(back,bring,bstride)]:seam(o,r,s)
def bounds(obj):
    p=world_points(obj);return [[min(v[i] for v in p) for i in range(3)],[max(v[i] for v in p) for i in range(3)]]
scene.camera=bpy.data.objects['V6_THREE_QUARTER']
dest=RUN/'SOFA_LOOSE_COVER_V8.blend';bpy.ops.wm.save_as_mainfile(filepath=str(dest))
report={'source':str(SOURCE),'source_sha256':hashlib.sha256(SOURCE.read_bytes()).hexdigest(),'output':str(dest),'output_sha256':hashlib.sha256(dest.read_bytes()).hexdigest(),'variant':variant,'method':'new complete panel/curved boxing construction; ridge-valley folds and tangent gather; static reference-led exterior','seat_bounds_m':bounds(seat),'back_bounds_m':bounds(back),'seat_nominal_boxing_mm':74,'v6_nominal_boxing_mm':142,'back_support_shift_mm':shift*1000,'back_forward_adjustment_mm':forward*1000,'fold_width_multiplier':1.22 if refined else 1,'back_fold_depth_multiplier':.72 if refined else 1,'same_timber_materials_studio':True,'actual_simulation':False,'owner_accepted':False,'whole_house_propagation':False,'image2_requests':0}
(RUN/'BUILD_AUDIT.json').write_text(json.dumps(report,indent=2)+'\n');print('V8_BUILD_READY',json.dumps(report))
