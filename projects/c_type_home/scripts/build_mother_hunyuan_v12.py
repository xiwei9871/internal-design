"""Reuse the owner's complete Hunyuan bed in the mother room at its true size."""
import bpy,json,hashlib,struct
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
R=Path(__file__).resolve().parents[1];D=R/'design/mother_hunyuan_v12';D.mkdir(exist_ok=True)
S=R/'design/finishes_v11/WHOLE_HOUSE_FINISHES_READING_V11.blend';O=D/'WHOLE_HOUSE_MOTHER_HUNYUAN_V12.blend';SHA='222fdb8ac11230319052c9f9a1974bbce54564981ba427c45607a410854af613'
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();assert sha(S)==SHA and not O.exists()
bpy.ops.wm.open_mainfile(filepath=str(S));s=bpy.context.scene
hides={o.name:(o.hide_viewport,{l.name:o.hide_get(view_layer=l) for l in s.view_layers}) for o in bpy.data.objects};cols={c.name:c.hide_viewport for c in bpy.data.collections}
for c in bpy.data.collections:c.hide_viewport=False
for o in bpy.data.objects:o.hide_viewport=False;o.hide_set(False)
bpy.context.view_layer.update()
def mh(o):
    h=hashlib.sha256()
    if o.type=='MESH':
        for v in o.data.vertices:h.update(struct.pack('<fff',*v.co))
        for f in o.data.polygons:h.update(struct.pack('<'+'I'*len(f.vertices),*f.vertices))
    return h.hexdigest()
before={o.name:{'mesh':mh(o),'matrix':[list(r) for r in o.matrix_world],'hide_render':o.hide_render,'materials':[m.name if m else None for m in o.data.materials] if o.type=='MESH' else []} for o in bpy.data.objects}
oldbed=[o for o in s.objects if o.name.startswith('HOUSE_V1_MOTHER_')]
hidden=[]
for o in oldbed:
    if not o.hide_render:hidden.append(o.name)
    o.hide_render=True
source=bpy.data.objects['HUNYUAN_V3_COUPLE_BED'];bed=source.copy();bed.data=source.data.copy();bed.name='HUNYUAN_V12_MOTHER_BED';s.collection.objects.link(bed)
# Identical rotation and scale: translate to the old head position/centre, with
# the same1800mm mattress reference and2130x1910x1070mm whole bed envelope.
bed.location+=Vector((15.1879-11.267,2.1955-2.087,.0005));bed['reference']='Owner Hunyuan3D complete bed; copied intact from HUNYUAN_V3_COUPLE_BED';bed['mattress_reference_mm']=[1800,2000]
def bb(o):
    e=o.evaluated_get(bpy.context.evaluated_depsgraph_get());me=e.to_mesh();vs=[e.matrix_world@v.co for v in me.vertices];e.to_mesh_clear();return [[min(v[i] for v in vs) for i in range(3)],[max(v[i] for v in vs) for i in range(3)]]
bpy.context.view_layer.update();bounds=bb(bed)
# The new full bed is wider than the old1.5m placeholder; retain the chosen2110
# bedside products intact and move them by translation to leave50mm each side.
standmoves=[];moved=set()
for index,target_center_y in [(0,bounds[0][1]-.05-.225),(1,bounds[1][1]+.05+.225)]:
    root=bpy.data.objects['HOUSE_V2_MOTHER_'+str(index)+'_BEDSIDE_2110'];dy=target_center_y-[1.04,3.19][index];root.location.y+=dy
    # Existing splayed feet projected3.2mm below floor. Translate whole real
    # product up to finished floor; preserve leg geometry and overall dimensions.
    root.location.z+=.0032
    moved.add(root.name);moved.update(o.name for o in root.children_recursive);standmoves.append({'root':root.name,'delta_y_m':dy,'delta_z_m':.0032,'target_center_y_m':target_center_y})
bpy.context.view_layer.update()
def tree(o):
    e=o.evaluated_get(bpy.context.evaluated_depsgraph_get());me=e.to_mesh();vs=[e.matrix_world@v.co for v in me.vertices];fs=[list(f.vertices) for f in me.polygons];e.to_mesh_clear();return BVHTree.FromPolygons(vs,fs),[[min(v[i] for v in vs) for i in range(3)],[max(v[i] for v in vs) for i in range(3)]]
targets=[bed]+[bpy.data.objects[n] for n in moved if bpy.data.objects[n].type=='MESH'];targettrees=[(o.name,*tree(o)) for o in targets];near=[];collisions=[]
for o in s.objects:
    if o.type!='MESH' or o.hide_render or o in targets:continue
    vs=[o.matrix_world@Vector(v) for v in o.bound_box];lo=[min(v[i] for v in vs) for i in range(3)];hi=[max(v[i] for v in vs) for i in range(3)]
    if hi[0]<13 or lo[0]>15.3 or hi[1]<.75 or lo[1]>3.75 or hi[2]<.45 or lo[2]>1.55:continue
    t,b=tree(o);near.append(o.name)
    for n,t2,b2 in targettrees:
        if all(b2[1][k]>b[0][k]+.003 and b2[0][k]<b[1][k]-.003 for k in range(3)) and t2.overlap(t):collisions.append((n,o.name))
assert not collisions,collisions[:12]
assert mh(source)==mh(bed) and list(source.scale)==list(bed.scale) and list(source.rotation_euler)==list(bed.rotation_euler)
for n,(hv,layerhides) in hides.items():
    o=bpy.data.objects[n];o.hide_viewport=hv
    for l in s.view_layers:o.hide_set(layerhides[l.name],view_layer=l)
for c,h in cols.items():bpy.data.collections[c].hide_viewport=h
for o in oldbed:
    o.hide_viewport=True
    for l in s.view_layers:o.hide_set(True,view_layer=l)
bed.hide_render=False;bed.hide_viewport=False
for l in s.view_layers:bed.hide_set(False,view_layer=l)
bpy.context.window.view_layer=s.view_layers['OVERVIEW_CEILING_HIDDEN'];bpy.ops.wm.save_as_mainfile(filepath=str(O))
a={'source':str(S),'source_sha256':SHA,'output':str(O),'sha256':sha(O),'before':before,'new_bed':bed.name,'donor_bed':source.name,'same_complete_mesh':mh(bed),'same_material_slots':[m.name for m in bed.data.materials],'bed_bounds_m':bounds,'whole_bed_dimensions_mm':[round((bounds[1][i]-bounds[0][i])*1000,3) for i in range(3)],'mattress_reference_mm':[1800,2000],'head_orientation':'east, unchanged','hidden_old_bed_objects':hidden,'hidden_old_bed_all':[o.name for o in oldbed],'bedside_translations':standmoves,'moved_bedside_objects':sorted(moved),'nearby_checked_objects':near,'obstacle_intersections':collisions,'bed_foot_to_west_wall_horizontal_mm':(bounds[0][0]-11.6)*1000,'south_bed_side_to_wall_mm':(bounds[0][1]-.2)*1000,'north_bed_side_to_wall_mm':(4.5-bounds[1][1])*1000,'bedside_gap_mm':50,'source_preserved':True,'guest_room_unchanged':True,'no_image2':True,'status':'HUMAN_REVIEW'}
(D/'BUILD_AUDIT.json').write_text(json.dumps(a,indent=2)+'\n');assert sha(S)==SHA;print('MOTHER_HUNYUAN_V12',a['sha256'],'bounds',bounds,'standmoves',standmoves)
