"""Fresh-open source preservation, floor policy, grounded shelf and door collision checks."""
import bpy,json,hashlib,struct,math
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
R=Path(__file__).resolve().parents[1];D=R/'design/finishes_v11';a=json.loads((D/'BUILD_AUDIT.json').read_text());sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
assert sha(a['output'])==a['sha256'] and sha(a['source'])==a['source_sha256']
bpy.ops.wm.open_mainfile(filepath=a['output']);s=bpy.context.scene
assert bpy.context.window.view_layer.name=='OVERVIEW_CEILING_HIDDEN'
assert all(bpy.data.objects[n].hide_get(view_layer=s.view_layers['OVERVIEW_CEILING_HIDDEN']) for n in ['V7_CEILING_LOW','V7_CEILING_HIGH','V7_CEILING_450MM_TRANSITION'])
for c in bpy.data.collections:c.hide_viewport=False
for o in bpy.data.objects:o.hide_viewport=False;o.hide_set(False)
bpy.context.view_layer.update()
def mh(o):
    h=hashlib.sha256()
    if o.type=='MESH':
        for v in o.data.vertices:h.update(struct.pack('<fff',*v.co))
        for f in o.data.polygons:h.update(struct.pack('<'+'I'*len(f.vertices),*f.vertices))
    return h.hexdigest()
changed={x['object'] for x in a['finish_assignments']};moved=set(a['reading_moved_objects']);issues=[]
for n,b in a['before'].items():
    o=bpy.data.objects[n]
    if mh(o)!=b['mesh']:issues.append((n,'mesh'))
    if n not in moved and [list(r) for r in o.matrix_world]!=b['matrix']:issues.append((n,'matrix'))
    if o.hide_render!=b['hide_render']:issues.append((n,'visibility'))
    if o.type=='MESH' and n not in changed and [m.name if m else None for m in o.data.materials]!=b['materials']:issues.append((n,'materials'))
    if o.type=='LIGHT' and o.data.energy!=b['light_energy']:issues.append((n,'light'))
assert not issues,issues[:12]
assert not (moved&changed),'Furniture appearance must remain unchanged'
floor_mats={}
for o in s.objects:
    if o.name.startswith(('PRESENTATION_FLOOR_','PRESENTATION_TILE_')):
        room=o.name.split('_',2)[2];expect='V11_OWNER_WHITE_SUBTLE_MARBLE_600x1200' if room in a['wet_floor_rooms'] else 'V11_UNIFIED_PALE_ASH_FLOOR'
        assert o.data.materials[0].name==expect,o.name;floor_mats[room]=expect
for n in ['FLOOR_LOWER','R4_UPPER_FLOOR_CONTINUOUS_STRAIGHT_THRESHOLD','STEP_0','STEP_1','STEP_2']:
    assert bpy.data.objects[n].data.materials[0].name=='V11_UNIFIED_PALE_ASH_FLOOR'
for x in a['created_tile_skins']:assert bpy.data.objects[x['object']].data.materials[0].name=='V11_OWNER_WHITE_SUBTLE_MARBLE_600x1200'
bench=bpy.data.objects[a['hidden_duplicate_bench']];assert bench.hide_render
def bvh(o):
    e=o.evaluated_get(bpy.context.evaluated_depsgraph_get());me=e.to_mesh();vs=[e.matrix_world@v.co for v in me.vertices];fs=[list(f.vertices) for f in me.polygons];e.to_mesh_clear()
    return BVHTree.FromPolygons(vs,fs),[min(v[i] for v in vs) for i in range(3)],[max(v[i] for v in vs) for i in range(3)]
rack=[(n,*bvh(bpy.data.objects[n])) for n in sorted(moved) if bpy.data.objects[n].type=='MESH']
collisions=[]
for o in s.objects:
    if o.type!='MESH' or o.hide_render or o.name in moved:continue
    vs=[o.matrix_world@Vector(v) for v in o.bound_box];lo=[min(v[i] for v in vs) for i in range(3)];hi=[max(v[i] for v in vs) for i in range(3)]
    if hi[0]<8.6 or lo[0]>9.1 or hi[1]<5.2 or lo[1]>6.2 or hi[2]<.45 or lo[2]>2.05:continue
    tree,lo,hi=bvh(o)
    for n,t,a0,a1 in rack:
        if all(a1[k]>lo[k]+.0001 and a0[k]<hi[k]-.0001 for k in range(3)) and t.overlap(tree):collisions.append((n,o.name))
assert not collisions,collisions[:12]
hinge=bpy.data.objects['R4_BEDROOM_INWARD_HINGE_ROOT'];original=hinge.rotation_euler.copy();door=bpy.data.objects['R4_BEDROOM_DOOR_LEAF'];door_checks=[]
for deg in [0,30,60,90]:
    hinge.rotation_euler.z=original.z+math.radians(deg);bpy.context.view_layer.update();t,lo,hi=bvh(door);hits=[]
    for n,tree,a0,a1 in rack:
        if all(a1[k]>lo[k]+.0001 and a0[k]<hi[k]-.0001 for k in range(3)) and tree.overlap(t):hits.append(n)
    assert not hits,(deg,hits);door_checks.append({'angle_degrees':deg,'intersections':0})
hinge.rotation_euler=original;bpy.context.view_layer.update()
for n,rough in [('V8_COLORLESS_CLEAR_ARCHITECTURAL_GLASS',.015),('V8_COLORLESS_PRIVACY_FROSTED_GLASS',.68)]:
    m=bpy.data.materials[n];p=m.node_tree.nodes.get('Principled BSDF');assert m.use_raytrace_refraction and m.thickness_mode=='SLAB';assert abs(p.inputs['Roughness'].default_value-rough)<1e-6;assert list(p.inputs['Base Color'].default_value)==[1,1,1,1]
for f in a['protected_sources']:assert sha(f['path'])==f['sha256']
# Actual stair contour section across new shelf width, not a stair bounding box.
tree,_,_=bvh(bpy.data.objects['STEP_2']);rows=[];cab=a['cabinet_bounds_m']
for y in [cab[0][1],(cab[0][1]+cab[1][1])/2,cab[1][1]]:
    hit=tree.ray_cast(Vector((9.04,y,.449)),Vector((-1,0,0)),4)
    rows.append({'y_m':y,'cabinet_to_step_horizontal_mm':(cab[0][0]-hit[0].x)*1000 if hit[0] else None})
v={'status':'PASS_TECHNICAL_AND_POLICY_CHECKS','source_sha256':a['sha256'],'original_objects_geometry_unchanged':len(a['before']),'only_whole_reading_assembly_moved':len(moved),'unexpected_changes':issues,'protected_source_count':len(a['protected_sources']),'floor_materials':floor_mats,'cabinet_bottom_FFL_offset_mm':a['cabinet_bottom_above_structural_FFL_mm'],'cabinet_to_south_trim_mm':a['cabinet_south_to_door_trim_mm'],'door_leaf_samples':door_checks,'obstacle_intersections':collisions,'actual_stair_sections':rows,'glass_settings_preserved':True,'final_visual_acceptance':False}
(D/'VERIFICATION.json').write_text(json.dumps(v,indent=2)+'\n');print('VERIFY_V11',json.dumps(v))
