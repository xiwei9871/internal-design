# Read-only: orientation of WCs, wardrobe door mechanism, step nosing visibility. Never saves.
import bpy, json, sys, math, re
from mathutils import Vector
out = sys.argv[sys.argv.index('--') + 1]
def rc(scene):
    ok, st = {scene.collection}, [scene.collection]
    while st:
        c = st.pop()
        for ch in c.children:
            if not ch.hide_render and ch not in ok: ok.add(ch); st.append(ch)
    return ok
RC = rc(bpy.context.scene); vis = lambda o: not o.hide_render and any(c in RC for c in o.users_collection)
res = {}
for n in ('R3_WC_LATEST', 'B11_Rectangle034_CATALOG_00_00', 'B11_Rectangle008_CATALOG_00_00'):
    o = bpy.data.objects[n]; me = o.data; mw = o.matrix_world
    vs = [mw @ v.co for v in me.vertices]
    # bowl front = side with lowest max-height (seat lip) vs tank side = tallest
    zs = sorted(v.z for v in vs); zmax = zs[-1]
    tall = [v for v in vs if v.z > zmax - 0.08]
    cx = sum(v.x for v in vs) / len(vs); cy = sum(v.y for v in vs) / len(vs)
    tx = sum(v.x for v in tall) / len(tall); ty = sum(v.y for v in tall) / len(tall)
    res[n] = {'rot_z_deg': round(math.degrees(mw.to_euler().z), 1), 'centroid': [round(cx * 1000), round(cy * 1000)],
              'tank_centroid': [round(tx * 1000), round(ty * 1000)],
              'faces_toward': 'from tank to centroid', 'dir': [round((cx - tx) * 1000), round((cy - ty) * 1000)]}
pat = re.compile(r'^(B11_Rectangle015|B11_Rectangle045|R3_WARDROBE)')
doors = {}
for o in bpy.data.objects:
    if pat.match(o.name) and vis(o) and re.search(r'DOOR|FRONT|SLID|TRACK|HINGE|LEAF', o.name.upper()):
        ws = [o.matrix_world @ Vector(c) for c in o.bound_box]
        doors.setdefault(o.name.split('_')[0] + '_' + o.name.split('_')[1], []).append(
            [o.name, [round(min(v.x for v in ws) * 1000), round(min(v.y for v in ws) * 1000), round(max(v.x for v in ws) * 1000),
                      round(max(v.y for v in ws) * 1000)]])
res['wardrobe_parts'] = doors
res['nosing'] = [[o.name, vis(o), [c.name for c in o.users_collection]] for o in bpy.data.objects if 'NOSING' in o.name.upper()]
json.dump(res, open(out, 'w'), ensure_ascii=False, indent=1); print('VERIFY_OK')
