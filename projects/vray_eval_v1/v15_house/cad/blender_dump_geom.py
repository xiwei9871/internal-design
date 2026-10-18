# 在 Blender 内运行: blender -b <blend> -P blender_dump_geom.py -- <out.json>
# 输出: 对象名 -> bbox/z/三角形XY + 剖切线段(1150/1650)
import bpy, json, sys
from mathutils import Vector
argv = sys.argv[sys.argv.index('--')+1:]
out_path = argv[0]
WANT = lambda n: n.startswith(('W_wall', 'VIEW_WALL', 'R3_', 'R4_', 'DOOR_V2',
    'D107_', 'KITCHEN_', 'STEP_', 'WAVE_STEP', 'G_wall', 'WAVE_WALL'))
CUTS = [1150.0, 1650.0]
def plane_segs(pts3, z):
    """三角形与 z=h 平面的交线段 (XY)"""
    xs = [(p[0], p[1], p[2]) for p in pts3]
    hits = []
    for i in range(3):
        j = (i+1) % 3
        z1, z2 = xs[i][2], xs[j][2]
        if (z1-z)*(z2-z) < 0 or (z1 == z and z2 != z):
            f = (z - z1) / (z2 - z1)
            if 0 <= f <= 1:
                hits.append((xs[i][0]+(xs[j][0]-xs[i][0])*f, xs[i][1]+(xs[j][1]-xs[i][1])*f))
    return hits
data = {}
dg = bpy.context.evaluated_depsgraph_get()
for o in bpy.data.objects:
    if o.type != 'MESH' or not WANT(o.name): continue
    oe = o.evaluated_get(dg); mw = oe.matrix_world
    me = oe.to_mesh(); me.calc_loop_triangles()
    tris = []; segs = {int(h): [] for h in CUTS}
    for t in me.loop_triangles:
        w3 = [mw @ me.vertices[vi].co for vi in t.vertices]
        w3 = [(p.x*1000, p.y*1000, p.z*1000) for p in w3]
        tris.append([[round(p[0],1), round(p[1],1)] for p in w3])
        for h in CUTS:
            hit = plane_segs(w3, h)
            if len(hit) == 2:
                segs[int(h)].append([[round(hit[0][0],1),round(hit[0][1],1)],
                                     [round(hit[1][0],1),round(hit[1][1],1)]])
    bb = [mw @ Vector(c) for c in o.bound_box]
    xs = [v.x*1000 for v in bb]; ys = [v.y*1000 for v in bb]; zs = [v.z*1000 for v in bb]
    data[o.name] = {'tris_xy': tris, 'segs': segs,
                    'bbox': [round(min(xs),1), round(min(ys),1), round(max(xs),1), round(max(ys),1)],
                    'z': [round(min(zs),1), round(max(zs),1)]}
    oe.to_mesh_clear()
json.dump(data, open(out_path, 'w'))
print('DUMPED', len(data), 'objects with section segs')
