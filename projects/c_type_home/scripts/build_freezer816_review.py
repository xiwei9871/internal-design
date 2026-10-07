"""Manufacturer-envelope furniture successor, exactly four native objects edited."""
import bpy,json,hashlib,struct,math
from pathlib import Path
from mathutils import Vector, Matrix
from mathutils.bvhtree import BVHTree
ROOT=Path(__file__).resolve().parents[1];R=ROOT/'design/freezer816_review'
SRC=ROOT/'design/bedrooms_wood_v1/BEDROOMS_WOOD_V3.blend'
REG=ROOT/'design/bedrooms_wood_v1/spatial-canvas.bindings.full.json'
REV='freezer816-cabinet-review-1'
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
truths={str(SRC):'93891e0b9c60a9d769e8e65ec4d04d592ea11dee4b9d713966d8b1033b9ebd31',
 '/Users/xiwei/interior_design/projects/c_type_home/design/bedroom_door_r4/OPTION_A_SLIDING_R4.blend':'d109c7efcfa2b2b2565e4c073ee0cdf5282b23c01122bc9c1bbe7b8791ac3afb',
 '/Users/xiwei/interior_design/projects/c_type_home/design/blender_b0/B0_EXISTING_AS_IS.blend':'717e6dc4a3d4fb6325512236f5c235ded702376309456028129bf0889548efcb'}
assert all(sha(p)==h for p,h in truths.items())
bpy.ops.wm.open_mainfile(filepath=str(SRC));bpy.context.view_layer.update()
def fingerprint(o):
 h=hashlib.sha256()
 if o.type=='MESH':
  for v in o.data.vertices:h.update(struct.pack('<fff',*v.co))
  for f in o.data.polygons:h.update(struct.pack('<'+'I'*len(f.vertices),*f.vertices))
 return (h.hexdigest(),tuple(v for row in o.matrix_world for v in row),str(sorted(o.items())),
  tuple(m.name if m else None for m in o.data.materials) if o.type=='MESH' else (),
  o.hide_render,o.hide_viewport,o.hide_get(),o.parent.name if o.parent else None)
before={o.name:fingerprint(o) for o in bpy.context.scene.objects}
def bb(o):
 vs=[o.matrix_world@v.co for v in o.data.vertices]
 return [[min(v[i] for v in vs) for i in range(3)],[max(v[i] for v in vs) for i in range(3)]]
def affine(n,a,b):
 o=bpy.data.objects[n];old=bb(o);o.data=o.data.copy();inv=o.matrix_world.inverted()
 for v in o.data.vertices:
  w=o.matrix_world@v.co;v.co=inv@Vector([a[i]+(w[i]-old[0][i])/(old[1][i]-old[0][i])*(b[i]-a[i]) for i in range(3)])
 o.data.update();return o
names=['B11_Rectangle039_BODY','B11_Rectangle039_LID_SEAM','SUNROOM_EAST_LOW_STORAGE','SUNROOM_EAST_STORAGE_COUNTER']
old={n:bb(bpy.data.objects[n]) for n in names}
xa,xb=12.2499,12.7999;ya,yb=12.334,13.150
freezer=affine(names[0],(xa,ya,0),(xb,yb,.876))
# Lidseam follows the appliance scaling; preserve ID and producttop, no externalcover.
oa,ob=old[names[0]];sa,sb=old[names[1]]
mapco=lambda v:[(xa,ya,0)[i]+(v[i]-oa[i])/(ob[i]-oa[i])*(.55,.816,.876)[i] for i in range(3)]
seam=affine(names[1],mapco(sa),mapco(sb))
cabinet=affine(names[2],(12.14,11.23,.08),(12.74,12.214,.855))
counter=affine(names[3],(12.13,11.22,.855),(12.76,12.234,.89))
bpy.context.view_layer.update()
unrelated=[n for n,s in before.items() if n not in names and fingerprint(bpy.data.objects[n])!=s]
assert not unrelated,unrelated
assert len(before)==len(bpy.context.scene.objects)
fa,fb=bb(freezer);ca,cb=bb(counter)
for i,v in enumerate([.550,.816,.876]):assert abs(fb[i]-fa[i]-v)<1e-5
clearance={'rear_to_east_wall_m':12.8999-fb[0],'north_to_north_wall_m':13.3999-fb[1],
 'south_to_cabinet_counter_m':fa[1]-cb[1],'front_to_plant_ledge_m':fa[0]-12.06}
assert all(v>=.10-1e-5 for v in clearance.values()),clearance
def tree(o,M=None):
 M=o.matrix_world if M is None else M
 return BVHTree.FromPolygons([M@v.co for v in o.data.vertices],[list(p.vertices) for p in o.data.polygons],epsilon=1e-6)
obstacles=['VIEW_WALL_W_wall_md_0026','VIEW_WALL_W_wall_md_0062','VIEW_WALL_W_wall_md_0055',
 'NORTH_BALCONY_GLASS_EAST','NORTH_BALCONY_FRAME_EAST_SILL','NORTH_BALCONY_FRAME_EAST_HEAD',
 'SUNROOM_NORTH_PLANT_LEDGE_BASE','SUNROOM_NORTH_PLANT_LEDGE_TOP',
 'V4_GUEST_B11_G-GB-BALC_HOST_GLASS0','V4_GUEST_B11_G-GB-BALC_HOST_GLASS1']
obstacles+=[b['native_id'] for b in json.loads(REG.read_text())['bindings'] if b['native_id'].startswith('V4_GUEST_CASING_')]
trees={n:tree(bpy.data.objects[n]) for n in obstacles};hits=[]
for o in [freezer,cabinet,counter]:
 for n,t in trees.items():
  if tree(o).overlap(t):hits.append([o.name,n])
assert not hits,hits
floor=bpy.data.objects['FLOOR_LOWER'];inv=floor.matrix_world.inverted()
for o in [freezer,cabinet]:
 a,b=bb(o)
 for x,y in [(a[0]+.02,a[1]+.02),(b[0]-.02,b[1]-.02)]:
  ok,p,n,i=floor.ray_cast(inv@Vector((x,y,2)),Vector((0,0,-1)));assert ok and abs(p.z)<1e-4
# Approximate40mmproductlid with east/rear Y-axis hinge. This tests unobstructedtopspace,
# not certification of a mechanism absent fromthe productimage.
verts=[(x,y,z) for x in [xa,xb] for y in [ya,yb] for z in [.836,.876]]
faces=[(0,1,3,2),(4,6,7,5),(0,4,5,1),(2,3,7,6),(0,2,6,4),(1,5,7,3)]
pivot=Vector((xb,ya,.836));lid_hits=[]
for deg in range(0,91,5):
 M=Matrix.Translation(pivot)@Matrix.Rotation(math.radians(deg),4,'Y')@Matrix.Translation(-pivot)
 t=BVHTree.FromPolygons([M@Vector(v) for v in verts],faces,epsilon=1e-6)
 for n,q in trees.items():
  if t.overlap(q):lid_hits.append([deg,n])
assert not lid_hits,lid_hits
reg=json.loads(REG.read_text());reg.update(source_resource_id='c_type_freezer816_review',source_revision=REV,
 registry_revision=REV,source_locator=str(R/'FREEZER816_CABINET_REVIEW.blend'))
bpy.ops.wm.save_as_mainfile(filepath=reg['source_locator']);reg['source_sha256']=sha(reg['source_locator'])
(R/'spatial-canvas.bindings.full.json').write_text(json.dumps(reg,ensure_ascii=False,indent=2)+'\n')
report={'status':'HUMAN_REVIEW','revision':REV,'source':reg['source_locator'],'source_sha256':reg['source_sha256'],
 'parent_source':str(SRC),'parent_sha256':truths[str(SRC)],'manufacturer_reference':'owner image BD/BC-203KM(E),203L,top-opening;876mmwithhighadjustablefeet',
 'freezer_size_mm':[816,550,876],'source_axis_size_m':[.550,.816,.876],'freezer_long_axis':'Y/eastwallparallel',
 'cabinet_body_length_mm':984,'cabinet_body_before_mm':650,'cabinet_gain_mm':334,'counter_length_mm':1014,
 'changed_native_ids':names,'bounds':{n:bb(bpy.data.objects[n]) for n in names},'clearances':clearance,
 'intersections':hits,'lid_sweep_hits':lid_hits,'lid_sweep_assumption':'40mmthicklid,reareastYaxishinge0..90deg,notmanufacturercertification',
 'no_extra_freezer_cover':True,'unrelated_objects_fingerprint_equal':True,'floor_support_checked':True,'frozen_hashes':truths}
(R/'FREEZER816_REVIEW.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
assert all(sha(p)==h for p,h in truths.items())
print('FREEZER816_BUILD_PASS',json.dumps(clearance),'cabinet984/counter1014',len(reg['bindings']))
