"""Fresh reopen: protected sources, closed shells and actual support geometry."""
import bpy,bmesh,hashlib,json,struct
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'design/sofa_soft_pilot_v6'
a=json.loads((OUT/'DETAIL_AUDIT.json').read_text());assert hashlib.sha256(Path(a['output']).read_bytes()).hexdigest()==a['output_sha256']
bpy.ops.wm.open_mainfile(filepath=a['output']);scene=bpy.context.scene;bpy.context.view_layer.update()
def vertices(o):return [o.matrix_world@v.co for v in o.data.vertices]
def tree(o):return BVHTree.FromPolygons(vertices(o),[tuple(f.vertices) for f in o.data.polygons])
objects={};shells=[]
for name in ['V6_SEAT_COMPLETE_COVER','V6_BACK_COMPLETE_COVER']:
    o=bpy.data.objects[name];bm=bmesh.new();bm.from_mesh(o.data)
    loose=[e.index for e in bm.edges if len(e.link_faces)!=2];zero=[e.index for e in bm.edges if e.calc_length()<1e-7];tiny=[f.index for f in bm.faces if f.calc_area()<1e-12]
    volume=bm.calc_volume(signed=True);bm.free();assert not loose,(name,'boundary',len(loose));assert not zero,(name,'zero edges',len(zero));assert not tiny,(name,'tiny faces',len(tiny));assert volume>0,(name,'volume',volume)
    objects[name]={'vertices':len(o.data.vertices),'faces':len(o.data.polygons),'open_edges':len(loose),'zero_length_edges':len(zero),'tiny_faces':len(tiny),'positive_volume_m3':volume};shells.append(o)
seat,back=shells;st=tree(seat);bt=tree(back);tri_pairs=st.overlap(bt)
assert not tri_pairs,('seat/back intersections',len(tri_pairs))
support=[]
for p in vertices(back):
    if p.z<.56:
        hit=st.ray_cast(Vector((p.x,p.y,2)),Vector((0,0,-1)))
        if hit[0] is not None:support.append(p.z-hit[0].z)
assert support and min(support)>-.001,min(support);assert min(support)<.003,min(support)
deck_top=.285;seatbottom=min(p.z for p in vertices(seat));assert abs(seatbottom-deck_top)<.001
wood=[o for o in scene.objects if o.name=='V6_BACK_TOP_RAIL'];rail_intersections=[o.name for o in wood if bt.overlap(tree(o))];assert not rail_intersections,rail_intersections
missing=[im.name for im in bpy.data.images if im.source=='FILE' and not im.packed_file and not Path(bpy.path.abspath(im.filepath)).exists()];assert not missing,missing
packed_images=sum(bool(im.packed_file) for im in bpy.data.images)
protected=json.loads((OUT/'PRESERVATION.json').read_text())['files']
for f in protected:assert hashlib.sha256(Path(f['path']).read_bytes()).hexdigest()==f['sha256'],f['path']
def mesh_hash(me):
    h=hashlib.sha256()
    for v in me.vertices:h.update(struct.pack('<fff',*v.co))
    for p in me.polygons:h.update(struct.pack('<'+'I'*len(p.vertices),*p.vertices))
    return h.hexdigest()
SOURCE=ROOT/'design/lookdev_v5/LIVING_DINING_LOOKDEV_V5.blend'
with bpy.data.libraries.load(str(SOURCE),link=False) as(x,y):y.objects=['V4_Sofa_seat_middle','V4_Sofa_back_1']
baseline_pass=[]
for source_obj,original_name in zip(y.objects,['V4_Sofa_seat_middle','V4_Sofa_back_1']):
    assert mesh_hash(source_obj.data)==mesh_hash(bpy.data.objects['V6_BASELINE_'+original_name].data),original_name
    baseline_pass.append(original_name);bpy.data.objects.remove(source_obj,do_unlink=True)
report={'status':'PASS','output_sha256':a['output_sha256'],'protected_files':len(protected),'v5_baseline_mesh_hashes_pass':baseline_pass,'shells':objects,'seat_back_surface_intersection_pairs':len(tri_pairs),'minimum_back_vertex_to_seat_gap_mm':min(support)*1000,'seat_bottom_to_wood_deck_gap_mm':(seatbottom-deck_top)*1000,'back_rail_triangle_intersections':rail_intersections,'missing_images':missing,'packed_images':packed_images,'trial_totalheight_mm':a['pair_bounds_m'][1][2]*1000,'height_conflict_with700mm':a['trial_height_conflict_mm'],'not_certified':'physicalpaddingmechanics;exactSKU;fabrication;housefit;ownerappearanceacceptance'}
(OUT/'VERIFICATION.json').write_text(json.dumps(report,indent=2)+'\n');print('V6_VERIFY_REPORT',json.dumps(report))
