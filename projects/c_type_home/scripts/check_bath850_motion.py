"""Bounded geometric diagnosis and actual slide path check."""
import bpy,json
from pathlib import Path
from mathutils import Vector,Matrix
from mathutils.bvhtree import BVHTree
R=Path(__file__).resolve().parents[1]/'design/secondary_bath850_review'
reg=json.loads((R/'spatial-canvas.bindings.full.json').read_text());bpy.ops.wm.open_mainfile(filepath=reg['source_locator']);bpy.context.view_layer.update()
def tree(o,M=None):
 M=o.matrix_world if M is None else M
 return BVHTree.FromPolygons([M@v.co for v in o.data.vertices],[list(f.vertices) for f in o.data.polygons],epsilon=0)
leaf=bpy.data.objects['R3_SLIDING_LEAF'];wall=bpy.data.objects['VIEW_WALL_R3_SOUTH_POCKET_PARTITION']
pairs=tree(leaf).overlap(tree(wall));print('LEAF_WALL_PAIRS',len(pairs))
for a,b in pairs[:12]:
 vs=[wall.matrix_world@wall.data.vertices[i].co for i in wall.data.polygons[b].vertices]
 print('WALL_CONTACT_FACE',[[min(v[i] for v in vs),max(v[i] for v in vs)] for i in range(3)])
assert not pairs,pairs
def bounds(o):
 vs=[o.matrix_world@v.co for v in o.data.vertices];return [[min(v[i] for v in vs) for i in range(3)],[max(v[i] for v in vs) for i in range(3)]]
la,lb=bounds(leaf);west=bpy.data.objects['R3_FRAME_WEST'];eastS=bpy.data.objects['R3_SPLIT_JAMB_EAST_S'];eastN=bpy.data.objects['R3_SPLIT_JAMB_EAST_N']
obstacles={n:tree(bpy.data.objects[n]) for n in ['VIEW_WALL_R3_SOUTH_POCKET_PARTITION','VIEW_WALL_R3_WEST_PARTITION','R3_FRAME_WEST','R3_SPLIT_JAMB_EAST_S','R3_SPLIT_JAMB_EAST_N','R3_WARDROBE_BACK','R3_SLIDER_END_STOP']}
travel=la[0]-(bounds(west)[1][0]-.020);hits=[]
for k in range(21):
 M=Matrix.Translation((-travel*k/20,0,0))@leaf.matrix_world;t=tree(leaf,M)
 for n,q in obstacles.items():
  if t.overlap(q):hits.append([k,n])
assert not hits,hits
# Wardrobehinges0..90deg comparedagainstbedandnorthbedside; nofabricationcertification.
targets={n:tree(bpy.data.objects[n]) for n in ['B11_Rectangle012_CATALOG_00_00','BW1_COUPLE_BEDSIDE_N']};whits=[]
import math
for i in range(3):
 o=bpy.data.objects['R3_WARDROBE_FRONT_'+str(i)];a,b=bounds(o)
 for px,sign in [(a[0],-1),(b[0],1)]:
  p=Vector((px,a[1],a[2]))
  for deg in range(0,91,5):
   M=Matrix.Translation(p)@Matrix.Rotation(sign*math.radians(deg),4,'Z')@Matrix.Translation(-p)@o.matrix_world;t=tree(o,M)
   for n,q in targets.items():
    if t.overlap(q):whits.append([i,px,deg,n])
assert not whits,whits
report={'status':'PASS','source_sha256':reg['source_sha256'],'slide_travel_m':travel,'poses':21,'slide_collision_pairs':hits,'wardrobe_leaf_sweeps_hits':whits,
 'opening_clear_width_m':bounds(eastS)[0][0]-bounds(west)[1][0],'wardrobe_width_m':bounds(bpy.data.objects['R3_WARDROBE_TOP'])[1][0]-bounds(bpy.data.objects['R3_WARDROBE_TOP'])[0][0]}
(R/'BATH850_MOTION_EVIDENCE.json').write_text(json.dumps(report,indent=2)+'\n');print('BATH850_MOTION_PASS',json.dumps(report))
