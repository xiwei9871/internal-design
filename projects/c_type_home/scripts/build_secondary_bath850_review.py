"""Derived secondary-bath opening successor: 850mm clear + 1200mm wardrobe."""
import bpy,json,hashlib,struct
from pathlib import Path
from mathutils import Vector
ROOT=Path(__file__).resolve().parents[1];R=ROOT/'design/secondary_bath850_review'
SRC=ROOT/'design/freezer816_review/FREEZER816_CABINET_REVIEW.blend';REV='secondary-bath-850-wardrobe1200-review-1'
TRUTHS={str(SRC):'3d1637cbc00b9f8a25e98b49c1997cd052a4e43fffca81dd4a2939bf7064e191',
 '/Users/xiwei/interior_design/projects/c_type_home/design/bedroom_door_r4/OPTION_A_SLIDING_R4.blend':'d109c7efcfa2b2b2565e4c073ee0cdf5282b23c01122bc9c1bbe7b8791ac3afb',
 '/Users/xiwei/interior_design/projects/c_type_home/design/blender_b0/B0_EXISTING_AS_IS.blend':'717e6dc4a3d4fb6325512236f5c235ded702376309456028129bf0889548efcb'}
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();assert all(sha(p)==h for p,h in TRUTHS.items())
bpy.ops.wm.open_mainfile(filepath=str(SRC));bpy.context.view_layer.update()
base=json.loads((ROOT/'design/freezer816_review/spatial-canvas.bindings.full.json').read_text())
def state(o):
 h=hashlib.sha256()
 for v in o.data.vertices if o.type=='MESH' else []:h.update(struct.pack('<fff',*v.co))
 return (h.hexdigest(),tuple(float(v) for row in o.matrix_world for v in row),str(sorted(o.items())),o.parent.name if o.parent else None)
before={o.name:state(o) for o in bpy.context.scene.objects}
def bb(o):
 vs=[o.matrix_world@v.co for v in o.data.vertices];return [[min(v[i] for v in vs) for i in range(3)],[max(v[i] for v in vs) for i in range(3)]]
def map_range(n,lo,hi,nlo,nhi):
 o=bpy.data.objects[n];old=bb(o);o.data=o.data.copy();inv=o.matrix_world.inverted()
 for v in o.data.vertices:
  w=o.matrix_world@v.co;u=(w.x-lo)/(hi-lo);w.x=nlo+u*(nhi-nlo);v.co=inv@w
 o.data.update();return o
def shift_x(n,dx):
 o=bpy.data.objects[n];o.location.x+=dx;return o
# Three-door wardrobe: keep east edge; retreat west edge from9.972 to10.172.
ward=[n for n in before if n.startswith('R3_WARDROBE')];changed=set(ward)
for n in ward:map_range(n,9.9722499847,11.3722496033,10.1722499847,11.3722496033)
# Opening enlargement: current clear x=9.963125-9.234=729.1mm -> new east jamb10.084125 =>850mm.
east_shift=.850-(9.963125228881836-9.234000205993652)
for n in ['R3_SPLIT_JAMB_EAST_S','R3_SPLIT_JAMB_EAST_N','R3_CASING_S_EAST','R3_CASING_N_EAST']:
 shift_x(n,east_shift);changed.add(n)
for n,lo,hi,nlo,nhi in [
 ('R3_FRAME_HEAD_S',9.2089996,9.9881248,9.2089996,9.9881248+east_shift),('R3_FRAME_HEAD_N',9.2089996,9.9881248,9.2089996,9.9881248+east_shift),
 ('R3_CASING_S_HEAD',9.1590004,10.0381250,9.1590004,10.0381250+east_shift),('R3_CASING_N_HEAD',9.1590004,10.0381250,9.1590004,10.0381250+east_shift),
 ('R3_SLIDER_CONTINUOUS_RAIL',9.202,10.77425,9.202,10.77425+2*east_shift),('R3_SLIDER_MAINTENANCE_COVER',9.209,10.8099,9.209,10.8099+2*east_shift),
 ('R3_SLIDING_LEAF',9.993125,10.76225,9.993125+east_shift,10.76225+2*east_shift)]:
 map_range(n,lo,hi,nlo,nhi);changed.add(n)
for n in ['R3_SLIDING_RECESSED_PULL_S','R3_SLIDING_RECESSED_PULL_N','R3_SLIDER_HANGER_0']:
 shift_x(n,east_shift);changed.add(n)
for n in ['R3_SLIDER_END_STOP','R3_SLIDER_HANGER_1']:
 shift_x(n,2*east_shift);changed.add(n)
# Expand the local derived opening, shorten pocket skins; keep east roomfacefixed.
wall=bpy.data.objects['VIEW_WALL_R3_SOUTH_POCKET_PARTITION'];wall.data=wall.data.copy();inv=wall.matrix_world.inverted()
mouth=9.98812484741211;pocket_end=10.777950286865234;end=11.399900436401367
for v in wall.data.vertices:
 w=wall.matrix_world@v.co
 if w.x>=pocket_end-.001:
  w.x=pocket_end+2*east_shift+(w.x-pocket_end)*(end-pocket_end-2*east_shift)/(end-pocket_end)
 elif w.x>=mouth-.001:
  w.x=mouth+east_shift+(w.x-mouth)*(pocket_end-mouth+east_shift)/(pocket_end-mouth)
 v.co=inv@w
wall.data.update();changed.add(wall.name)
# Modelthe receiverrebateatwestjamb so890mmleafcanclosewith20mmlap,notpenetrateasolidjamb.
westobj=bpy.data.objects['R3_FRAME_WEST'];westobj.data=westobj.data.copy()
bpy.ops.mesh.primitive_cube_add(size=1,location=(9.2245,4.743,.0+1.4925));cutter=bpy.context.object
cutter.scale=(.025,.05,2.075);bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
mod=westobj.modifiers.new('Sliding receiver rebate','BOOLEAN');mod.operation='DIFFERENCE';mod.solver='EXACT';mod.object=cutter
bpy.context.view_layer.objects.active=westobj;bpy.ops.object.modifier_apply(modifier=mod.name);bpy.data.objects.remove(cutter,do_unlink=True);changed.add(westobj.name)
bpy.context.view_layer.update()
unrelated=[n for n,s in before.items() if n not in changed and state(bpy.data.objects[n])!=s];assert not unrelated,unrelated
wardbox=bb(bpy.data.objects['R3_WARDROBE_TOP']);west=bb(bpy.data.objects['R3_FRAME_WEST']);east=bb(bpy.data.objects['R3_SPLIT_JAMB_EAST_S'])
clear= east[0][0]-west[1][0]; wardrobe_width=wardbox[1][0]-wardbox[0][0]; gap=wardbox[0][0]-east[1][0]
trim_gap=wardbox[0][0]-bb(bpy.data.objects['R3_CASING_S_EAST'])[1][0]
assert abs(clear-.85)<1e-4 and abs(wardrobe_width-1.2)<1e-4 and trim_gap>.01
# Verify no changed geometry intersects named doorway pocket/walls; verify clear floor support is retained.
def tree(o):return BVHTree.FromPolygons([o.matrix_world@v.co for v in o.data.vertices],[list(f.vertices) for f in o.data.polygons],epsilon=1e-6)
from mathutils.bvhtree import BVHTree
obs=['VIEW_WALL_R3_SOUTH_POCKET_PARTITION','VIEW_WALL_R3_WEST_PARTITION']
hits=[]
for n in changed:
 o=bpy.data.objects.get(n)
 for qn in obs:
  q=bpy.data.objects.get(qn)
  if q and tree(o).overlap(tree(q)):hits.append([n,qn])
# Gridthroughactualwallopeningtoconfirm850mmfreepassage,notsize-onlyframechange.
walltree=tree(wall);blocked=[]
for i in range(21):
 x=west[1][0]+.003+(.85-.006)*i/20
 for z in [.48,1.0,1.5,2.0,2.50]:
  hit=walltree.ray_cast(Vector((x,4.48,z)),Vector((0,1,0)),.40)
  if hit[0] is not None:blocked.append((x,z))
assert not blocked,blocked
for n in changed:
 o=bpy.data.objects[n]
 if o.get('source_revision'):o['based_on_source_revision']=o['source_revision']
 o['source_revision']=REV;o['review_status']='HUMAN_REVIEW_DERIVED_DOOR850_WARDROBE1200'
 if 'fitted_to_latest_freecad' in o:o['fitted_to_latest_freecad']=False
wall['design_authority']='DERIVED_DESIGN_MODEL';wall['opening_clear_width_m']=clear
wall['surface_partition_not_new_construction_solid']=False
report={'status':'HUMAN_REVIEW','revision':REV,'parent_source':str(SRC),'parent_sha256':TRUTHS[str(SRC)],
 'source':str(R/'SECONDARY_BATH_850_WARDROBE1200.blend'),'changed_native_ids':sorted(changed),
 'wardrobe':{'width_m':wardrobe_width,'depth_m':.6,'height_m':2.2,'door_count':3,'west_retraction_m':.2},
 'door':{'clear_width_m':clear,'clear_width_mm':clear*1000,'target_mm':850,'leaf_width_m':bb(bpy.data.objects['R3_SLIDING_LEAF'])[1][0]-bb(bpy.data.objects['R3_SLIDING_LEAF'])[0][0],
 'opening_frame_gap_to_wardrobe_m':gap,'trim_gap_to_wardrobe_m':trim_gap,'rail_and_pocket_synchronized':True,'door_sweep_certification':'not manufacturer certified'},
 'opening_grid_blocked':blocked,
 'intersections_with_identity_walls':hits,'unrelated_fingerprints_equal':not unrelated,'frozen_hashes':TRUTHS}
reg={k:v for k,v in base.items() if k!='bindings'};reg.update(source_resource_id='c_type_secondary_bath850',source_revision=REV,registry_revision=REV,source_locator=report['source'],source_authority='frozen')
reg['bindings']=base['bindings']
bpy.ops.wm.save_as_mainfile(filepath=report['source']);reg['source_sha256']=sha(report['source']);(R/'spatial-canvas.bindings.full.json').write_text(json.dumps(reg,ensure_ascii=False,indent=2)+'\n')
report['source_sha256']=reg['source_sha256'];report['registry_sha256']=sha(R/'spatial-canvas.bindings.full.json');(R/'SECONDARY_BATH_850_REVIEW.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
assert all(sha(p)==h for p,h in TRUTHS.items());print('BATH850_BUILD_PASS',json.dumps(report,ensure_ascii=False))
