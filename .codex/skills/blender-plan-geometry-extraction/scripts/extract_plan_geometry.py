# Read-only Blender plan-geometry extractor. Never saves the .blend.
#   blender -b <blend> -P extract_plan_geometry.py -- inventory <out.json>
#   blender -b <blend> -P extract_plan_geometry.py -- extract <config.json> <out.json>
# inventory: every render-visible mesh with bbox, materials, and horizontal face areas
#            (up-facing below 700mm = floor candidate, down-facing above 2200mm = ceiling candidate).
# extract:   triangles (XY + mean Z) of the horizontal faces of objects matched by the config
#            regexes {"floor": "...", "ceiling": "...", "stair": "...", "fixture": "..."}.
import bpy, json, re, sys
from mathutils import Vector

args = sys.argv[sys.argv.index('--') + 1:]
mode = args[0]
dg = bpy.context.evaluated_depsgraph_get()


def _render_collections(scene):
    """Collections that render: every collection on the path from the scene root is enabled."""
    ok, stack = {scene.collection}, [scene.collection]
    while stack:
        c = stack.pop()
        for ch in c.children:
            if not ch.hide_render and ch not in ok:
                ok.add(ch); stack.append(ch)
    return ok


RENDER_COLS = _render_collections(bpy.context.scene)


def visible(o):
    """Render-visible: object enabled and linked to at least one fully enabled collection chain."""
    return not o.hide_render and any(c in RENDER_COLS for c in o.users_collection)


def bbox(o):
    ws = [o.matrix_world @ Vector(c) for c in o.bound_box]
    return [round(min(v.x for v in ws) * 1000), round(min(v.y for v in ws) * 1000),
            round(max(v.x for v in ws) * 1000), round(max(v.y for v in ws) * 1000),
            round(min(v.z for v in ws) * 1000), round(max(v.z for v in ws) * 1000)]


def horiz(o, want_up, zmin, zmax, keep_tris):
    ev = o.evaluated_get(dg)
    me = ev.to_mesh(); me.calc_loop_triangles()
    mw = o.matrix_world; n3 = mw.to_3x3()
    area, tris = 0.0, []
    for t in me.loop_triangles:
        n = (n3 @ t.normal).normalized()
        if (n.z > 0.9) if want_up else (n.z < -0.9):
            w = [mw @ me.vertices[i].co for i in t.vertices]
            z = sum(v.z for v in w) / 3 * 1000
            if zmin <= z <= zmax:
                a = ((w[1] - w[0]).cross(w[2] - w[0])).length / 2
                area += a
                if keep_tris:
                    tris.append([[round(v.x * 1000, 1), round(v.y * 1000, 1)] for v in w] + [round(z)])
    ev.to_mesh_clear()
    return area, tris


meshes = [o for o in bpy.data.objects if o.type == 'MESH' and visible(o)]
import hashlib
with open(bpy.data.filepath, 'rb') as fh:
    _sha = hashlib.sha256(fh.read()).hexdigest()
out = {'blend': bpy.data.filepath, 'blend_sha256': _sha, 'blender_version': bpy.app.version_string,
       'extractor': 'extract_plan_geometry.py/2', 'n_mesh_visible': len(meshes)}
if mode == 'inventory':
    rows = []
    for o in meshes:
        fa, _ = horiz(o, True, -100, 700, False)
        ca, _ = horiz(o, False, 2200, 4000, False)
        rows.append({'n': o.name, 'b': bbox(o), 'col': o.users_collection[0].name,
                     'mats': [s.material.name for s in o.material_slots if s.material][:4],
                     'floor_m2': round(fa, 3), 'ceil_m2': round(ca, 3)})
    out['objects'] = rows
    json.dump(out, open(args[1], 'w'), ensure_ascii=False)
else:
    cfg = json.load(open(args[1]))
    pats = {k: re.compile(v) for k, v in cfg.items() if k in ('floor', 'ceiling', 'stair', 'fixture')}
    res = {k: {} for k in pats}
    for o in meshes:
        for k, p in pats.items():
            if not p.search(o.name): continue
            rec = {'mats': [s.material.name for s in o.material_slots if s.material], 'b': bbox(o)}
            if k in ('floor', 'stair'): rec['tris'] = horiz(o, True, -100, 700, True)[1]
            elif k == 'ceiling': rec['tris'] = horiz(o, False, 2200, 4000, True)[1]
            res[k][o.name] = rec
    out.update(res)
    json.dump(out, open(args[2], 'w'), ensure_ascii=False)
print('PLAN_EXTRACT_OK', mode, {k: len(v) for k, v in out.items() if isinstance(v, (list, dict))})
