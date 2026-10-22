"""Reference-guided padded-cover fallback after two rejected cloth solves.

Adapts the researched local height-alpha method, with broad fill settling and
seam restraint. Editable shape keys; no random all-surface wrinkle field.
"""
import bpy, hashlib, json, math
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'design/sofa_soft_pilot_v7/local_final'
OUT.mkdir(exist_ok=True)
if (OUT/'SOFA_RELAXED_COVER_V7.blend').exists():
    raise SystemExit('Preserved candidate already exists; use a new version directory for another build.')
SOURCE = ROOT / 'design/sofa_soft_pilot_v6/SOFA_SEAT_BACK_DETAIL_V6.blend'
assert hashlib.sha256(SOURCE.read_bytes()).hexdigest() == '06150245b3fee8442a530aab9fd82766f152093159251bb8d849efb4372f367c'
bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
scene = bpy.context.scene
base = bpy.data.collections['V6_CUSTOM_PAIR']
base.name = 'V6_COMPARISON_PAIR'
base.hide_render = True
base.hide_viewport = True
candidate = bpy.data.collections.new('V7_RELAXED_PAIR')
scene.collection.children.link(candidate)
for original in list(base.objects):
    obj = original.copy()
    obj.data = original.data.copy()
    obj.name = original.name.replace('V6_', 'V7_', 1)
    candidate.objects.link(obj)
    obj.hide_render = False
    obj.hide_viewport = False
    obj.hide_set(False)

N = 80
STRIDE = (N + 1) ** 2
RING = list(range(N + 1)) + [j * (N + 1) + N for j in range(1, N + 1)] + [N * (N + 1) + i for i in range(N - 1, -1, -1)] + [j * (N + 1) for j in range(N - 1, 0, -1)]

def crease(x, y, start, end, width, depth):
    a, b, q = Vector(start), Vector(end), Vector((x, y))
    ab = b - a
    t = (q - a).dot(ab) / ab.length_squared
    if not 0 < t < 1:
        return 0
    distance = (q - (a + t * ab)).length
    return depth * math.sin(math.pi * t) ** .75 * (-math.exp(-.5 * (distance / width) ** 2) + .23 * math.exp(-.5 * (distance / (width * 2.8)) ** 2))

OLD_SEAT = [((-.45,-.365),(-.34,-.185),.008,.006),((.45,-.37),(.34,-.17),.008,.005),((-.28,-.405),(-.225,-.27),.006,.0035),((.24,-.405),(.195,-.24),.007,.004),((-.445,.31),(-.30,.20),.010,.004)]
OLD_BACK = [((-.455,-.175),(-.29,-.06),.007,.009),((.455,-.18),(.32,-.055),.007,.007),((-.43,.19),(-.32,.10),.006,.006),((.40,.185),(.285,.105),.007,.005),((-.20,-.20),(-.17,-.08),.006,.005),((.19,-.20),(.15,-.085),.006,.0045)]
# Folds start at actual sewing edges and fade into the padded panel.
SEAT_FOLDS = [((-.35,-.445),(-.29,-.27),.016,.007),((.24,-.445),(.21,-.31),.018,.006),((-.512,-.20),(-.38,-.135),.015,.005),((.512,.09),(.385,.13),.017,.005)]
BACK_FOLDS = [((-.31,-.182),(-.245,-.035),.017,.016),((.18,-.182),(.145,-.07),.019,.011),((-.48,.145),(-.37,.06),.018,.009),((.50,.12),(.40,.045),.016,.008)]

def seat_delta(x, y):
    u, v = x / .5125, y / .4455
    edge = max(abs(u), abs(v))
    restraint = -.003 * math.exp(-((edge - .98) / .07) ** 2)
    # Soft wrap rolls above a restrained seam; center settles rather than grows.
    roll = .004 * math.exp(-((edge - .84) / .14) ** 2)
    settling = -.016 * math.exp(-((x + .09) / .25) ** 2 - ((y - .035) / .25) ** 2)
    broad = -.005 * math.exp(-((x - .24) / .18) ** 2 - ((y + .19) / .19) ** 2)
    return restraint + roll + settling + broad + sum(crease(x,y,*c) for c in SEAT_FOLDS) - sum(crease(x,y,*c) for c in OLD_SEAT)

def back_delta(x, y):
    edge = max(abs(x) / .5135, abs(y) / .1825)
    restraint = -.007 * math.exp(-((edge - .975) / .065) ** 2)
    shoulder = .006 * math.exp(-((edge - .81) / .10) ** 2)
    # Broad fill redistribution, not a periodic surface/noise texture.
    settle = -.013 * math.exp(-((x - .06) / .20) ** 2 - ((y + .025) / .125) ** 2)
    low = -.009 * math.exp(-((x + .12) / .30) ** 2 - ((y + .145) / .055) ** 2)
    return restraint + shoulder + settle + low + sum(crease(x,y,*c) for c in BACK_FOLDS) - sum(crease(x,y,*c) for c in OLD_BACK)

seat = bpy.data.objects['V7_SEAT_COMPLETE_COVER']
back = bpy.data.objects['V7_BACK_COMPLETE_COVER']
for obj, kind, field in [(seat,'seat',seat_delta),(back,'back',back_delta)]:
    obj.shape_key_add(name='Basis_V6_volume')
    key = obj.shape_key_add(name='V7_soft_fill_and_seam_restraint')
    for i, point in enumerate(key.data):
        p = point.co
        original_xy = (p.x, p.y)
        if STRIDE <= i < 2 * STRIDE:
            p.z += field(p.x, p.y)
        elif i >= 2 * STRIDE:
            # Boxing follows the top sewn edge continuously, bottom stays supported.
            t = [.18,.5,.82][(i - 2 * STRIDE) // len(RING)]
            idx = RING[(i - 2 * STRIDE) % len(RING)]
            top = obj.data.vertices[idx + STRIDE].co
            p.z += t * field(top.x, top.y)
        if kind == 'seat':
            # Restrain sewn rims inside the full boxing silhouette. A convex
            # fabric sidewall then reads as wrapped fill instead of a flat slab.
            edge = max(abs(original_xy[0])/.5125, abs(original_xy[1])/.4455)
            falloff = math.exp(-((edge-.99)/.12)**2)
            if i < STRIDE:
                tuck = .006
            elif i < 2*STRIDE:
                tuck = .012
            else:
                tuck = (.006*(1-t)+.012*t)*abs(2*t-1)**2
            p.x *= 1-tuck*falloff
            p.y *= 1-tuck*falloff
        if kind == 'back':
            # Small soft shoulder droop; no stretching of product footprint.
            top_weight = math.exp(-((p.y - .1825) / .055) ** 2)
            p.y -= .010 * top_weight * (abs(p.x) / .5135) ** 2
    key.value = 1
    obj['v7_method'] = 'reference-localized static shape key; cloth solve1/solve2 rejected'
    obj['v7_reference'] = 'owner catalog p4/p8 + selected A; foam wrap seat / filled back'

def evaluated_vertices(obj):
    evaluated = obj.evaluated_get(bpy.context.evaluated_depsgraph_get())
    mesh = evaluated.to_mesh()
    points = [evaluated.matrix_world @ v.co for v in mesh.vertices]
    faces = [tuple(f.vertices) for f in mesh.polygons]
    evaluated.to_mesh_clear()
    return points, faces

bpy.context.view_layer.update()
points, faces = evaluated_vertices(seat)
tree = BVHTree.FromPolygons(points, faces)
gaps = []
for p in evaluated_vertices(back)[0]:
    if p.z < .56:
        hit = tree.ray_cast(Vector((p.x,p.y,2)),Vector((0,0,-1)))
        if hit[0] is not None:
            gaps.append(p.z - hit[0].z)
shift = .0008 - min(gaps)
back.location.z += shift
bpy.context.view_layer.update()
# Re-establish rear local compression against the unchanged timber top rail.
inv = back.matrix_world.inverted()
for v in back.data.shape_keys.key_blocks[-1].data:
    p = back.matrix_world @ v.co
    dz = abs(p.z - .587)
    if p.y > .5495 and dz < .053:
        t = max(0,min(1,(dz - .038) / .015))
        p.y -= (p.y - .5495) * (1 - t*t*(3-2*t))
        v.co = inv @ p
bpy.context.view_layer.update()
for obj in [seat,back]:
    points = evaluated_vertices(obj)[0]
    for suffix,indices in [('bottom',RING),('top',[i+STRIDE for i in RING])]:
        welt = bpy.data.objects[obj.name+'_'+suffix+'_welt']
        inv = welt.matrix_world.inverted()
        for p,idx in zip(welt.data.splines[0].points,indices):
            p.co = (*(inv @ points[idx]),1)

def bounds(obj):
    p = evaluated_vertices(obj)[0]
    return [[min(v[i] for v in p) for i in range(3)],[max(v[i] for v in p) for i in range(3)]]

dest = OUT / 'SOFA_RELAXED_COVER_V7.blend'
bpy.ops.wm.save_as_mainfile(filepath=str(dest))
report = {'stage':'REFERENCE_LOCAL_FORM_CANDIDATE','source':str(SOURCE),'source_sha256':hashlib.sha256(SOURCE.read_bytes()).hexdigest(),'output':str(dest),'output_sha256':hashlib.sha256(dest.read_bytes()).hexdigest(),'seat_bounds_m':bounds(seat),'back_bounds_m':bounds(back),'back_support_shift_mm':shift*1000,'actual_simulation_used_for_final':False,'rejected_simulations':['solve1','solve2'],'method':'broad fill settling + restrained sewing perimeter + sparse seam-anchored folds; editable shape keys','material_light_camera_changes':False,'physical_certification':False,'whole_house_propagation':False}
(OUT/'SOLVE_AUDIT.json').write_text(json.dumps(report,indent=2)+'\n')
print('V7_LOCAL_FORM_READY',json.dumps(report))
