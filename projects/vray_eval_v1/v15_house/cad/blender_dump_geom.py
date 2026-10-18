# 在 Blender 内运行: blender -b <blend> -P blender_dump_geom.py -- <out.json>
# 输出: 墙/台阶对象名 -> bbox8 + 三角形XY面片
import bpy, json, sys
from mathutils import Vector
argv = sys.argv[sys.argv.index('--')+1:]
out_path = argv[0]
WANT = lambda n: n.startswith(('W_wall', 'VIEW_WALL', 'R3_', 'R4_', 'DOOR_V2',
    'D107_', 'KITCHEN_', 'STEP_', 'WAVE_STEP', 'G_wall', 'WAVE_WALL'))
data = {}
dg = bpy.context.evaluated_depsgraph_get()
for o in bpy.data.objects:
    if o.type != 'MESH' or not WANT(o.name): continue
    oe = o.evaluated_get(dg)
    mw = oe.matrix_world                     # evaluated 矩阵含 location 变更
    me = oe.to_mesh()
    tris = []
    me.calc_loop_triangles()
    for t in me.loop_triangles:
        pts = []
        for vi in t.vertices:
            w = mw @ me.vertices[vi].co
            pts.append([round(w.x*1000, 1), round(w.y*1000, 1)])
        tris.append(pts)
    bb = [mw @ Vector(c) for c in o.bound_box]
    xs = [v.x*1000 for v in bb]; ys = [v.y*1000 for v in bb]; zs = [v.z*1000 for v in bb]
    data[o.name] = {'tris_xy': tris,
                    'bbox': [round(min(xs),1), round(min(ys),1), round(max(xs),1), round(max(ys),1)],
                    'z': [round(min(zs),1), round(max(zs),1)]}
    oe.to_mesh_clear()
json.dump(data, open(out_path, 'w'))
print('DUMPED', len(data), 'objects')
