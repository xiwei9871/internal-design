"""Physical cover-drape study around retained V6 foam/filled-envelope macroform.

The solver is a bounded visual form aid, not foam/feather constitutive mechanics.
Original V6 is retained; approved wood/fabric, studio and dimensions are controlled.
"""
import bpy,hashlib,json,math,time,sys
from pathlib import Path
from mathutils import Vector

ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'design/sofa_soft_pilot_v7';SOURCE=ROOT/'design/sofa_soft_pilot_v6/SOFA_SEAT_BACK_DETAIL_V6.blend'
args=sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else [];variant=args[0] if args else 'solve1';RUN=OUT/variant;RUN.mkdir(exist_ok=True)
if (RUN/'SOLVE_AUDIT.json').exists():
    raise SystemExit('Preserved solve already exists; choose a new output directory/version, do not overwrite its cache.')
refined=variant=='solve2'
assert hashlib.sha256(SOURCE.read_bytes()).hexdigest()=='06150245b3fee8442a530aab9fd82766f152093159251bb8d849efb4372f367c'
bpy.ops.wm.open_mainfile(filepath=str(SOURCE));scene=bpy.context.scene;scene.frame_start=1;scene.frame_end=55;scene.gravity=(0,0,-9.81)
baseline=bpy.data.collections['V6_CUSTOM_PAIR'];baseline.name='V6_COMPARISON_PAIR';baseline.hide_render=True;baseline.hide_viewport=True
candidate=bpy.data.collections.new('V7_RELAXED_PAIR');scene.collection.children.link(candidate)
physics=bpy.data.collections.new('V7_FILL_COLLIDERS');scene.collection.children.link(physics);physics.hide_render=True
for o in list(baseline.objects):
    c=o.copy();c.data=o.data.copy();c.name=o.name.replace('V6_','V7_',1);candidate.objects.link(c);c.hide_render=False;c.hide_viewport=False;c.hide_set(False)
seat=bpy.data.objects['V7_SEAT_COMPLETE_COVER'];back=bpy.data.objects['V7_BACK_COMPLETE_COVER']
for o in [seat,back]:
    bpy.ops.object.select_all(action='DESELECT');o.select_set(True);bpy.context.view_layer.objects.active=o;bpy.ops.object.transform_apply(location=False,rotation=True,scale=True)
# Collision inner envelope retains the distinct seat and back filling silhouettes.
colliders=[]
for o,kind in [(seat,'seat'),(back,'back')]:
    core=o.copy();core.data=o.data.copy();physics.objects.link(core);core.name='V7_'+kind.upper()+'_SUPPORTED_INNER_FILL';core.hide_render=True;core.hide_viewport=False
    lo=[min(v.co[i] for v in core.data.vertices) for i in range(3)];hi=[max(v.co[i] for v in core.data.vertices) for i in range(3)];center=Vector([(lo[i]+hi[i])*.5 for i in range(3)])
    if kind=='seat':
        for v in core.data.vertices:
            v.co.x*=.986 if refined else .975;v.co.y*=.986 if refined else .972
            # Soft wrapping reserve above foam, with its underside held on timber.
            t=max(0,min(1,(v.co.z-.307)/(.4905-.307)));v.co.z-=(.007 if refined else .011)*t
    else:
        for v in core.data.vertices:
            v.co=center+(v.co-center)*(.97 if refined else .91)
    core.modifiers.new('Internal fill collision','COLLISION');core.collision.thickness_outer=.001;core.collision.thickness_inner=.001;core.collision.cloth_friction=8
    colliders.append(core)
for name in ['V7_SEAT_ASH_DECK','V7_BACK_TOP_RAIL']:
    o=bpy.data.objects[name];o.modifiers.new('Timber contact collision','COLLISION');o.collision.thickness_outer=.001;o.collision.thickness_inner=.001;o.collision.cloth_friction=12
originals={};solvers=[]
for o,kind in [(seat,'seat'),(back,'back')]:
    originals[o.name]=[v.co.copy() for v in o.data.vertices]
    pin=o.vertex_groups.new(name='SupportedCoverPin');ease=o.vertex_groups.new(name='PatternEaseNearSeams')
    if kind=='seat':
        for v in o.data.vertices:
            z=v.co.z;edge=max(abs(v.co.x)/.5125,abs(v.co.y)/.4455)
            if z<.307:pin.add([v.index],1,'REPLACE')
            elif edge>.985:pin.add([v.index],1 if refined else .38,'REPLACE')
            # More slack near sewn perimeter; middle stays comparatively smooth.
            ease.add([v.index],max(0,min(1,(edge-.64)/.34)),'REPLACE')
    else:
        # Pin the contact band, allow upper corners and soft front to fall gently.
        points=[o.matrix_world@v.co for v in o.data.vertices];lowest=min(p.z for p in points)
        for v,p in zip(o.data.vertices,points):
            if p.z<lowest+.026:pin.add([v.index],1,'REPLACE')
            elif p.y>.549 and abs(p.z-.587)<.037:pin.add([v.index],1,'REPLACE')
            elif p.z<lowest+.065:pin.add([v.index],.65,'REPLACE')
            edge=max(abs(p.x)/.5135,abs(p.z-.625)/.1825)
            if refined and edge>.98:pin.add([v.index],.8,'REPLACE')
            ease.add([v.index],max(0,min(1,(edge-.60)/.40)),'REPLACE')
    cl=o.modifiers.new('Actual supported cloth cover relaxation','CLOTH');s=cl.settings
    s.quality=10 if refined else 8;s.mass=.05;s.tension_stiffness=25;s.compression_stiffness=6 if refined else 1.5;s.shear_stiffness=18;s.bending_stiffness=.65 if refined else .08
    s.tension_damping=8;s.compression_damping=8;s.shear_damping=8;s.bending_damping=5;s.air_damping=4
    s.vertex_group_mass=pin.name;s.pin_stiffness=1;s.vertex_group_shrink=ease.name;s.shrink_min=0 if refined else -.003;s.shrink_max=-.006 if refined else -.018
    s.use_internal_springs=False;s.use_pressure=False;s.effector_weights.gravity=.15 if refined else .22
    cc=cl.collision_settings;cc.use_collision=True;cc.distance_min=.001;cc.collision_quality=4;cc.use_self_collision=False
    cl.point_cache.frame_start=1;cl.point_cache.frame_end=55;cl.point_cache.use_disk_cache=True
    solvers.append((o,cl))
scene.frame_set(1);bpy.context.view_layer.update();setup=RUN/'CLOTH_COVER_SETUP_V7.blend';bpy.ops.wm.save_as_mainfile(filepath=str(setup))
t=time.time();bakes=[]
for o,cl in solvers:
    bpy.context.view_layer.objects.active=o
    with bpy.context.temp_override(point_cache=cl.point_cache):bpy.ops.ptcache.bake(bake=True)
    bakes.append({'object':o.name,'is_baked':cl.point_cache.is_baked,'frame_start':cl.point_cache.frame_start,'frame_end':cl.point_cache.frame_end,'cache_info':cl.point_cache.info})
# Inspect actual cached geometry at onset/settle and preserve static forms / UVs.
checkpoints=[]
for frame in [1,18,35,55]:
    scene.frame_set(frame);bpy.context.view_layer.update();deps=bpy.context.evaluated_depsgraph_get();objects=[]
    for o,cl in solvers:
        e=o.evaluated_get(deps);me=e.to_mesh();delta=[(v.co-a).length for v,a in zip(me.vertices,originals[o.name])];world=[e.matrix_world@v.co for v in me.vertices]
        objects.append({'object':o.name,'moved_vertices':sum(d>1e-5 for d in delta),'max_displacement_mm':max(delta)*1000,'rms_displacement_mm':math.sqrt(sum(d*d for d in delta)/len(delta))*1000,'world_bounds_m':[[min(p[i] for p in world) for i in range(3)],[max(p[i] for p in world) for i in range(3)]]});e.to_mesh_clear()
    checkpoints.append({'frame':frame,'objects':objects})
# Retain setup with its baked caches, not just an unproven modifier on the object.
bpy.ops.wm.save_as_mainfile(filepath=str(setup))
for o,cl in solvers:
    e=o.evaluated_get(bpy.context.evaluated_depsgraph_get());me=bpy.data.meshes.new_from_object(e);o.data=me;o.modifiers.remove(cl)
    # Welt is attached to the final fabric edge, no ideal rectangle left floating.
    N=80;stride=(N+1)**2;ring=list(range(N+1))+[j*(N+1)+N for j in range(1,N+1)]+[N*(N+1)+i for i in range(N-1,-1,-1)]+[j*(N+1) for j in range(N-1,0,-1)]
    for suffix,indices in [('bottom',ring),('top',[i+stride for i in ring])]:
        welt=bpy.data.objects[o.name+'_'+suffix+'_welt'];spline=welt.data.splines[0];inv=welt.matrix_world.inverted()
        for point,idx in zip(spline.points,indices):point.co=(*(inv@(o.matrix_world@me.vertices[idx].co)),1)
physics.hide_render=True;physics.hide_viewport=True
for o in colliders:o.hide_render=True
dest=RUN/'SOFA_RELAXED_COVER_V7.blend';bpy.ops.wm.save_as_mainfile(filepath=str(dest))
cache_files=list(RUN.glob('blendcache_*/*'))
report={'stage':'SUPPORTED_CLOTH_STATIC_CANDIDATE','source':str(SOURCE),'source_sha256':hashlib.sha256(SOURCE.read_bytes()).hexdigest(),'output':str(dest),'output_sha256':hashlib.sha256(dest.read_bytes()).hexdigest(),'setup':str(setup),'bakes':bakes,'cache_files':len(cache_files),'checkpoints':checkpoints,'runtime_seconds':round(time.time()-t,2),'effective_gravity_m_s2':9.81*(.15 if refined else .22),'ease_range':[0,-.006] if refined else [-.003,-.018],'cloth_pressure':False,'method':'supportedoutercover drapedoverinnerfill;actualbakedcloth,staticdelivery','scope_limit':'not actualfoam/feathermechanics;notwholehouseinstallation','material_light_camera_changes':False}
(RUN/'SOLVE_AUDIT.json').write_text(json.dumps(report,indent=2)+'\n');print('V7_COVER_SOLVE_READY',report['runtime_seconds'],json.dumps(checkpoints[-1]))
