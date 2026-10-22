"""One complete custom-construction seat/back study; no whole-house writeback.

Reference-led macro surfaces follow owner catalog1020/1006 and selectedA.
Blender native sculpt stroke was probed separately and crashes headlessly;
localized static crease edits are explicit, not claimed native brush strokes.
"""
import bpy,hashlib,json,math,sys
from pathlib import Path
from mathutils import Vector,Matrix
from mathutils.bvhtree import BVHTree

ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'design/sofa_soft_pilot_v6';SOURCE=ROOT/'design/lookdev_v5/LIVING_DINING_LOOKDEV_V5.blend'
args=sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else [];detail='detail' in args
assert hashlib.sha256(SOURCE.read_bytes()).hexdigest()=='94661776fe34a45b73b540765ca6391a63e34a0940b5b84d461abd8b4657cd76'
bpy.ops.wm.read_factory_settings(use_empty=True);scene=bpy.context.scene;scene.unit_settings.system='METRIC'
with bpy.data.libraries.load(str(SOURCE),link=False) as(a,b):
    b.materials=['V5_NATURAL_ASH_PLANKS_OIL','V5_NATURAL_FLAX_COTTON']
    b.objects=['V4_Sofa_seat_middle','V4_Sofa_back_1','V4_Sofa_seat_middle_sewn_welt','V4_Sofa_back_1_sewn_welt']
wood,cloth=b.materials
old=bpy.data.collections.new('V5_COMPARISON_PAIR');new=bpy.data.collections.new('V6_CUSTOM_PAIR');hidden=bpy.data.collections.new('V6_CONSTRUCTION_CUTAWAY');stage=bpy.data.collections.new('V6_STUDIO')
for c in [old,new,hidden,stage]:scene.collection.children.link(c)
hidden.hide_render=True;hidden.hide_viewport=True
# Transform whole existing pair rigidly: sofaY -> studyX, sofaX -> studyY.
transform=Matrix(((0,1,0,-9.595),(-1,0,0,4.016),(0,0,1,0),(0,0,0,1)))
def hierarchy_matrix(o):
    # Appended objects have not yet evaluated their original parent graph.
    # Build the saved hierarchy transform explicitly, then apply a rigid rotation.
    local=o.matrix_basis.copy()
    return hierarchy_matrix(o.parent)@o.matrix_parent_inverse@local if o.parent else local
for o in b.objects:
    world=hierarchy_matrix(o);old.objects.link(o);o.hide_render=False;o.hide_viewport=False;o.hide_set(False);o.parent=None;o.matrix_world=transform@world;o.name='V6_BASELINE_'+o.name
def material(name,color,rough=.8):
    m=bpy.data.materials.new(name);m.use_nodes=True;m.diffuse_color=(*color,1);p=m.node_tree.nodes.get('Principled BSDF');p.inputs['Base Color'].default_value=(*color,1);p.inputs['Roughness'].default_value=rough;return m
weltmat=material('V6_FLAX_SEWN_WELT',(.32,.27,.20),.94);foam=material('V6_FOAM_CORE_CUTAWAY',(.70,.61,.42));fiber=material('V6_SOFT_WRAP_CUTAWAY',(.82,.78,.66));floor=material('V6_STUDIO_FLOOR',(.19,.205,.21),.9)
def mesh(name,verts,faces,mat,col=new):
    me=bpy.data.meshes.new(name);me.from_pydata(verts,[],faces);me.update();o=bpy.data.objects.new(name,me);col.objects.link(o);me.materials.append(mat)
    for f in me.polygons:f.use_smooth=True
    return o
def box(name,loc,size,mat,col=new,bevel=.008):
    bpy.ops.mesh.primitive_cube_add(size=1,location=loc);o=bpy.context.object;o.name=name;o.dimensions=size;bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
    for c in list(o.users_collection):c.objects.unlink(o)
    col.objects.link(o);o.data.materials.append(mat);b=o.modifiers.new('Manufactured edge radius','BEVEL');b.width=bevel;b.segments=4;o.modifiers.new('Surface normals','WEIGHTED_NORMAL')
    uv=o.data.uv_layers.new(name='ProductMeters');uv.active_render=True
    for f in o.data.polygons:
        axis=max(range(3),key=lambda i:abs(f.normal[i]));axes=[i for i in range(3) if i!=axis];extent=[max(v.co[i] for v in o.data.vertices)-min(v.co[i] for v in o.data.vertices) for i in axes];axes=sorted(axes,key=lambda i:-(max(v.co[i] for v in o.data.vertices)-min(v.co[i] for v in o.data.vertices)))
        for li in f.loop_indices:
            v=o.data.vertices[o.data.loops[li].vertex_index].co;uv.data[li].uv=(v[axes[0]],v[axes[1]])
    return o
def path(name,points,radius,mat=weltmat,col=new):
    data=bpy.data.curves.new(name,'CURVE');data.dimensions='3D';data.bevel_depth=radius;data.bevel_resolution=3;s=data.splines.new('POLY');s.points.add(len(points)-1)
    for p,co in zip(s.points,points):p.co=(*co,1)
    s.use_cyclic_u=True;o=bpy.data.objects.new(name,data);col.objects.link(o);data.materials.append(mat);return o
def rounded_xy(u,v,w,d,r):
    x=u*w/2;y=v*d/2;cx=w/2-r;cy=d/2-r
    if abs(x)>cx and abs(y)>cy:
        dx=abs(x)-cx;dy=abs(y)-cy;length=math.hypot(dx,dy)
        if length>r:x=math.copysign(cx+dx/length*r,x);y=math.copysign(cy+dy/length*r,y)
    return x,y
def localized_crease(x,y,start,end,width,depth):
    a=Vector(start);b=Vector(end);q=Vector((x,y));ab=b-a;t=(q-a).dot(ab)/ab.length_squared
    if t<=0 or t>=1:return 0
    distance=(q-(a+t*ab)).length
    # Same height-alpha principle as the researched localized Draw technique.
    # A crease is an inward valley with low shoulders, anchored to a real seam.
    core=math.exp(-.5*(distance/width)**2);shoulder=.23*math.exp(-.5*(distance/(width*2.8))**2)
    return depth*math.sin(math.pi*t)**.75*(-core+shoulder)
seatcreases=[((-.45,-.365),(-.34,-.185),.008,.006),((.45,-.37),(.34,-.17),.008,.005),((-.28,-.405),(-.225,-.27),.006,.0035),((.24,-.405),(.195,-.24),.007,.004),((-.445,.31),(-.30,.20),.010,.004)]
backcreases=[((-.455,-.175),(-.29,-.06),.007,.009),((.455,-.18),(.32,-.055),.007,.007),((-.43,.19),(-.32,.10),.006,.006),((.40,.185),(.285,.105),.007,.005),((-.20,-.20),(-.17,-.08),.006,.005),((.19,-.20),(.15,-.085),.006,.0045)]
def panels(name,w,d,edge_low,edge_high,crown,bottom_crown,kind):
    N=80;verts=[];faces=[];r=.065 if kind=='seat' else .078
    for layer in [0,1]:
        for j in range(N+1):
            for i in range(N+1):
                u=2*i/N-1;v=2*j/N-1;x,y=rounded_xy(u,v,w,d,r)
                f=max(0,1-abs(u)**3)**.60*max(0,1-abs(v)**3)**.62
                if kind=='seat':
                    # Foam core supports a gently crowned soft jacket; no knife-edge pillow.
                    edge=max(abs(u),abs(v));rounding=max(0,(edge-.80)/.20)**2
                    z=edge_high+crown*f if layer else edge_low-bottom_crown+bottom_crown*rounding
                    if layer:z-=.009*math.exp(-((x-.07)/.28)**2-((y-.11)/.24)**2)
                    if detail and layer:z+=sum(localized_crease(x,y,*c) for c in seatcreases)
                else:
                    # Filled back: broad lobes, bottom support compression and quieter top corners.
                    volume=f*(1-.09*v+.035*u)
                    z=edge_high+crown*volume if layer else edge_low-bottom_crown*volume
                    if layer:
                        z-=.009*math.exp(-((x+.05)/.24)**2-((y+.155)/.065)**2)
                        if detail:z+=sum(localized_crease(x,y,*c) for c in backcreases)
                verts.append((x,y,z))
    stride=(N+1)**2
    for layer in [0,1]:
        for j in range(N):
            for i in range(N):
                a=layer*stride+j*(N+1)+i;f=(a,a+1,a+N+2,a+N+1);faces.append(f if layer else tuple(reversed(f)))
    ring=list(range(N+1))+[j*(N+1)+N for j in range(1,N+1)]+[N*(N+1)+i for i in range(N-1,-1,-1)]+[j*(N+1) for j in range(N-1,0,-1)]
    # Boxing is a distinct visible fabric band connecting top and bottom sewn panels.
    band_rings=[ring]
    for t in [.18,.5,.82]:
        indices=[]
        for idx in ring:
            a=Vector(verts[idx]);b=Vector(verts[idx+stride]);p=a.lerp(b,t);p.x*=1+.008*math.sin(math.pi*t);p.y*=1+.008*math.sin(math.pi*t);indices.append(len(verts));verts.append(tuple(p))
        band_rings.append(indices)
    band_rings.append([idx+stride for idx in ring])
    for a,b in zip(band_rings,band_rings[1:]):
        for i in range(len(ring)):j=(i+1)%len(ring);faces.append((a[i],a[j],b[j],b[i]))
    o=mesh(name,verts,faces,cloth)
    uv=o.data.uv_layers.new(name='ProductMeters');uv.active_render=True
    for f in o.data.polygons:
        # Coordinate-derived millimetre-scale weave, separate boxing from broad panels.
        side=any(idx>=2*stride for idx in f.vertices)
        for li in f.loop_indices:
            co=o.data.vertices[o.data.loops[li].vertex_index].co
            uv.data[li].uv=(co.x,co.z) if side and abs(f.normal.y)>abs(f.normal.x) else ((co.y,co.z) if side else (co.x,co.y))
    seams=[]
    for label,indices in [('bottom',ring),('top',[idx+stride for idx in ring])]:seams.append(path(name+'_'+label+'_welt',[verts[idx] for idx in indices],.00115))
    o['construction']='foam core / soft wrap / cotton-linen boxing' if kind=='seat' else 'channel-filled feather/fiber bag and sewn cover; static exterior representation'
    o['source']='owner catalog1020 form,p8whiteash/foam/linen/down+fiber;custom candidate'
    return o,seams
seat,seats=panels('V6_SEAT_COMPLETE_COVER',1.025,.891,.292,.434,.060,.007,'seat')
back,backs=panels('V6_BACK_COMPLETE_COVER',1.027,.365,-.037,.042,.102,.062,'back')
# Local backXY is across/up; localZ points forward. Slight lean against timber support.
rotation=Matrix(((1,0,0),(0,.258819,-.965926),(0,.965926,.258819)))
for o in [back]+backs:o.rotation_euler=rotation.to_euler();o.location=(0,.485,.607)
bpy.context.view_layer.update()
# Position the whole filled back on the real seat surface; do not squash its loft.
tree=BVHTree.FromPolygons([v.co for v in seat.data.vertices],[tuple(f.vertices) for f in seat.data.polygons])
gaps=[]
for v in back.data.vertices:
    p=back.matrix_world@v.co
    if v.co.y<-.10:
        hit=tree.ray_cast(Vector((p.x,p.y,2)),Vector((0,0,-1)))
        if hit[0] is not None:gaps.append(p.z-hit[0].z)
support_shift=.0008-min(gaps)
for o in [back]+backs:o.location.z+=support_shift
bpy.context.view_layer.update()
# Rear filling compresses locally against the unchanged timber rail, rather than
# floating in front of it or passing through it. Front crown stays untouched.
inverse=back.matrix_world.inverted();rear_compression=0
for v in back.data.vertices:
    p=back.matrix_world@v.co;dz=abs(p.z-.587)
    if p.y>.5495 and dz<.053:
        t=max(0,min(1,(dz-.038)/.015));weight=1-t*t*(3-2*t);delta=(p.y-.5495)*weight;p.y-=delta;v.co=inverse@p;rear_compression=max(rear_compression,delta)
box('V6_FOAM_CORE', (0,0,.367),(1.00,.86,.145),foam,hidden,.040)
box('V6_SOFT_JACKET', (0,0,.393),(1.018,.884,.170),fiber,hidden,.047)
for i,x in enumerate([-.33,0,.33]):
    o=box('V6_BACK_FILL_CHANNEL_'+str(i),(0,0,0),(.32,.36,.17),fiber,hidden,.035);o.parent=back;o.location=(x,0,.012)
# One corresponding whole support segment, reproducing V5 timber rather than a new unrelated frame.
supports=[]
supports.append(box('V6_SEAT_ASH_DECK',(0,0,.264),(1.045,1.08,.042),wood))
supports.append(box('V6_BACK_LOWER_RAIL',(0,.581,.354),(1.045,.045,.049),wood))
supports.append(box('V6_BACK_TOP_RAIL',(0,.581,.587),(1.045,.062,.065),wood))
for x in [-.46,.46]:
    supports.append(box('V6_SUPPORT_LEG',(x,-.45,.13),(.058,.058,.26),wood))
    supports.append(box('V6_REAR_SUPPORT_LEG',(x,.46,.13),(.058,.058,.26),wood))
for x in [-.46,.46]:supports.append(box('V6_FRAME_SIDE_RAIL',(x,0,.219),(.044,1.045,.087),wood))
for i in range(5):supports.append(box('V6_BACK_SUPPORT_SLAT',(-.46+i*.23,.60,.463),(.023,.020,.22),wood,bevel=.003))
# Clone the support unchanged into baseline for a controlled pair comparison.
for o in supports:
    c=o.copy();c.data=o.data;old.objects.link(c);c.name='V6_BASELINE_'+o.name
lightworld=bpy.data.worlds.new('V6_STUDIO_WORLD');lightworld.use_nodes=True;lightworld.node_tree.nodes['Background'].inputs['Color'].default_value=(.7,.7,.7,1);lightworld.node_tree.nodes['Background'].inputs['Strength'].default_value=.35;scene.world=lightworld
box('V6_FLOOR',(0,0,-.04),(20,20,.08),floor,stage,0)
def area(name,loc,power,size,color):
    d=bpy.data.lights.new(name,'AREA');d.energy=power;d.shape='DISK';d.size=size;d.color=color;o=bpy.data.objects.new(name,d);stage.objects.link(o);o.location=loc;o.rotation_euler=(Vector((0,0,.4))-o.location).to_track_quat('-Z','Y').to_euler()
area('V6_KEY',(-2,-2,3),420,2.5,(1,.96,.9));area('V6_FILL',(2,-1,2),180,2,(.92,.96,1));area('V6_RIM',(0,2,2.2),220,2,(1,1,1))
def camera(name,eye,target,lens):
    d=bpy.data.cameras.new(name);o=bpy.data.objects.new(name,d);stage.objects.link(o);o.location=eye;o.rotation_euler=(Vector(target)-o.location).to_track_quat('-Z','Y').to_euler();d.lens=lens;d.clip_start=.01
    return o
camera('V6_FRONT',(0,-2.65,1.10),(0,0,.44),54)
camera('V6_SIDE',(2.70,.01,1.05),(0,.01,.44),54)
camera('V6_THREE_QUARTER',(1.95,-2.15,1.35),(0,.02,.43),54)
scene.camera=bpy.data.objects['V6_THREE_QUARTER'];scene.view_settings.view_transform='AgX';scene.view_settings.look='AgX - Medium High Contrast';scene.view_settings.exposure=0
scene.render.resolution_x=1500;scene.render.resolution_y=1200;scene.render.resolution_percentage=100;scene.render.image_settings.file_format='PNG';scene.render.threads_mode='FIXED';scene.render.threads=2
old.hide_render=True;old.hide_viewport=True
for area in bpy.context.screen.areas:
    if area.type=='VIEW_3D':area.spaces.active.region_3d.view_perspective='CAMERA'
for image in bpy.data.images:
    if image.source=='FILE' and not image.packed_file and Path(bpy.path.abspath(image.filepath)).exists():image.pack()
bpy.context.view_layer.update()
def actualbounds(obs):
    dg=bpy.context.evaluated_depsgraph_get();points=[]
    for o in obs:
        e=o.evaluated_get(dg);me=e.to_mesh();points.extend(e.matrix_world@v.co for v in me.vertices);e.to_mesh_clear()
    return [[min(v[i] for v in points) for i in range(3)],[max(v[i] for v in points) for i in range(3)]]
bounds=actualbounds([seat,back]);dest=OUT/('SOFA_SEAT_BACK_DETAIL_V6.blend' if detail else 'SOFA_SEAT_BACK_MACRO_V6.blend');bpy.ops.wm.save_as_mainfile(filepath=str(dest))
report={'stage':'detail' if detail else 'macro','source_sha256':hashlib.sha256(SOURCE.read_bytes()).hexdigest(),'output':str(dest),'output_sha256':hashlib.sha256(dest.read_bytes()).hexdigest(),'pair_bounds_m':bounds,'seat_bounds_m':actualbounds([seat]),'back_bounds_m':actualbounds([back]),'seat_back_support_shift_mm':support_shift*1000,'seat_back_minimum_vertex_support_gap_mm':.8,'back_rail_maximum_soft_compression_mm':rear_compression*1000,'old_whole_sofa_height_m':.7,'trial_height_conflict_mm':max(0,bounds[1][2]-.7)*1000,'wood_source':'V5 unchanged native material','fabric_source':'V5 unchanged native4Klinen','method':'panel/crownedfill/boxing construction + reference-localized static crease edits;not nativebrush','native_brush_probe':'assetactivated;headless sculpt brush_stroke crashedSIGSEGV;no successfulstrokeclaim','custom_dimensions_status':'trial proportions informed bycatalog/selectedA;not exactchosenSKU/fabrication','model_writeback':False,'whole_house_propagation':False}
(OUT/('DETAIL_AUDIT.json' if detail else 'MACRO_AUDIT.json')).write_text(json.dumps(report,indent=2)+'\n');print('V6_PAIR_READY',report['stage'],json.dumps(bounds))
