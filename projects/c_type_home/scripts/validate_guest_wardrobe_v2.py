"""Independent review2 east-facing wardrobe leaf sweep, no source writes."""
import bpy, json, math
from pathlib import Path
from mathutils import Vector, Matrix
from mathutils.bvhtree import BVHTree
R=Path(__file__).resolve().parents[1]/'design/bedrooms_wood_v1'
reg=json.loads((R/'spatial-canvas.bindings.full.json').read_text())
bpy.ops.wm.open_mainfile(filepath=reg['source_locator']);bpy.context.view_layer.update()
def tree(o,M=None):
 M=o.matrix_world if M is None else M
 return BVHTree.FromPolygons([M@v.co for v in o.data.vertices],[list(p.vertices) for p in o.data.polygons],epsilon=1e-6)
targets={n:tree(bpy.data.objects[n]) for n in ['B11_Rectangle017_CATALOG_00_00','BW1_GUEST_DESK','BW1_GUEST_DESK_CHAIR']}
hits=[];leaves=[b['native_id'] for b in reg['bindings'] if b['native_id'].startswith('B11_Rectangle045_FRONT_')]
assert len(leaves)==3
for n in leaves:
 o=bpy.data.objects[n];c=[o.matrix_world@Vector(v) for v in o.bound_box]
 xmin,ymin,zmin=[min(v[i] for v in c) for i in range(3)];xmax,ymax,zmax=[max(v[i] for v in c) for i in range(3)]
 for side,y,sign in [('south',ymin,-1),('north',ymax,1)]:
  p=Vector((xmax,y,zmin))
  for angle in range(0,91,5):
   M=Matrix.Translation(p)@Matrix.Rotation(sign*math.radians(angle),4,'Z')@Matrix.Translation(-p)@o.matrix_world
   t=tree(o,M)
   for name,target in targets.items():
    if t.overlap(target):hits.append([n,side,angle,name])
assert not hits,hits
(R/'GUEST_WARDROBE_SWEEP_EVIDENCE.json').write_text(json.dumps({'status':'PASS','source_revision':reg['source_revision'],'source_sha256':reg['source_sha256'],'leaf_count':3,'hinge_axis':'Z; both Y-ends of each east-facing leaf','sample_step_degrees':5,'hits':hits},indent=2)+'\n')
print('GUEST_THREE_DOOR_SWEEP_PASS',len(leaves),'both Y-end hinges0..90deg')
