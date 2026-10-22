"""B1 BLOCKOUT builder — run inside Blender:
blender -b --python scripts/b1_build.py
Input: design/b1_blockout/b1_model.json  (canonical task01 mm)
Output: 世纪欣园_B1_BLOCKOUT_V003.blend + renders + fidelity/spatial reports
Scale: 1 BU = 1 mm shown as meters via unit scale; we model in meters (mm*0.001).
"""
import bpy, json, math, os
from mathutils import Vector

BASE = '/Users/xiwei/interior_design/projects/c_type_home'
M = json.load(open(f'{BASE}/design/b1_blockout/b1_model.json'))
OUTD = f'{BASE}/design/b1_blockout'
S = 0.001  # mm -> m

# ---------------- temp dimensions ledger ----------------
TEMP = {
    'ceiling_height_mm': 2800, 'door_height_mm': 2100, 'opening_lintel_bottom_mm': 2100,
    'window_sill_mm': 900, 'window_head_mm': 2400, 'glass_door_head_mm': 2400,
    'parapet_height_mm': 1100, 'bay_sill_mm': 600, 'bay_head_mm': 2400, 'bay_roof_mm': 2800,
    'balcony_glazing_head_mm': 2800, 'slab_thickness_mm': 150,
    'split_level_delta_mm': 350, 'stair_riser_mm': 175,
    'wardrobe_h': 2200, 'bookcase_h': 2000, 'low_bookcase_h': 900, 'shoe_cab_h': 1000,
    'bed_h': 500, 'headboard_h': 1100, 'nightstand_h': 500, 'desk_h': 720,
    'sofa_h': 800, 'chaise_h': 750, 'coffee_table_h': 450, 'side_table_h': 550,
    'dining_table_h': 720, 'chair_seat_h': 450, 'bench_h': 450, 'tv_console_h': 450,
    'kitchen_counter_h': 850, 'kitchen_tall_h': 2100, 'wc_h': 400, 'vanity_h': 800,
    'wetzone_glass_h': 2000, 'washer_3kg_h': 600, 'washer_dryer_stacked_h': 1700,
    'freezer_h': 850, 'device_h': 300, 'device_z': 900,
}

COLS = ['00_REFERENCE', '01_ARCH_EXISTING', '02_ARCH_NEW', '03_WINDOWS', '04_DOORS',
        '05_FURNITURE_LIVING', '06_FURNITURE_DINING', '07_FURNITURE_BEDROOM',
        '08_FURNITURE_STUDY', '09_BATH_FIXTURES', '10_KITCHEN', '11_LAUNDRY',
        '12_ACCESSIBILITY', '20_CAMERAS', '90_TO_VERIFY']

COL_COLOR = {
    '00_REFERENCE': (0.5, 0.5, 0.5, 1), '01_ARCH_EXISTING': (0.62, 0.60, 0.57, 1),
    '02_ARCH_NEW': (0.75, 0.55, 0.35, 1), '03_WINDOWS': (0.35, 0.65, 0.85, 0.45),
    '04_DOORS': (0.55, 0.40, 0.25, 1), '05_FURNITURE_LIVING': (0.75, 0.72, 0.60, 1),
    '06_FURNITURE_DINING': (0.68, 0.58, 0.42, 1), '07_FURNITURE_BEDROOM': (0.60, 0.65, 0.70, 1),
    '08_FURNITURE_STUDY': (0.50, 0.60, 0.55, 1), '09_BATH_FIXTURES': (0.65, 0.75, 0.78, 1),
    '10_KITCHEN': (0.72, 0.70, 0.55, 1), '11_LAUNDRY': (0.70, 0.72, 0.75, 1),
    '12_ACCESSIBILITY': (0.85, 0.65, 0.30, 1), '20_CAMERAS': (0, 0, 0, 1),
    '90_TO_VERIFY': (0.9, 0.25, 0.2, 1),
}

ZONE_COL = {
    'R-LIVING': '05_FURNITURE_LIVING', 'R-DINING': '06_FURNITURE_DINING',
    'R-BED-S': '07_FURNITURE_BEDROOM', 'R-MASTER': '07_FURNITURE_BEDROOM',
    'R-STUDY': '07_FURNITURE_BEDROOM', 'R-CLOAK': '09_BATH_FIXTURES',
    'R-BED-N': '08_FURNITURE_STUDY', 'R-BATH-M': '09_BATH_FIXTURES',
    'R-BATH-P': '09_BATH_FIXTURES', 'R-KITCHEN': '10_KITCHEN',
    'R-BALC-LIFE': '11_LAUNDRY', 'R-BALC-N': '11_LAUNDRY',
    'R-LEISURE-W': '05_FURNITURE_LIVING', 'R-LEISURE-E': '07_FURNITURE_BEDROOM',
}
UPPER_Z = TEMP['split_level_delta_mm']
UPPER_ROOMS = {s['id'] for s in M['spaces'] if s['level'] == 'upper'}

# ---------------- scene reset ----------------
bpy.ops.wm.read_factory_settings(use_empty=True)
scn = bpy.context.scene
scn.unit_settings.system = 'METRIC'
scn.unit_settings.scale_length = 0.001  # 1 BU displays as 1 mm

cols = {}
for c in COLS:
    nc = bpy.data.collections.new(c)
    scn.collection.children.link(nc)
    cols[c] = nc

def box(name, rect_mm, z0_mm, z1_mm, col, color=None, alpha=1.0):
    x0, y0, x1, y1 = [v * S for v in rect_mm]
    z0, z1 = z0_mm * S, z1_mm * S
    bpy.ops.mesh.primitive_cube_add(location=((x0+x1)/2, (y0+y1)/2, (z0+z1)/2))
    o = bpy.context.object
    o.name = name
    o.scale = ((x1-x0)/2, (y1-y0)/2, (z1-z0)/2)
    bpy.ops.object.transform_apply(scale=True)
    for c in o.users_collection: c.objects.unlink(o)
    cols[col].objects.link(o)
    o.color = color or COL_COLOR[col]
    o['source'] = 'canonical/FCStd'
    return o

def cyl(name, rect_mm, z0_mm, z1_mm, col):
    x0, y0, x1, y1 = [v * S for v in rect_mm]
    r = min(x1-x0, y1-y0) / 2
    bpy.ops.mesh.primitive_cylinder_add(radius=r, depth=(z1_mm-z0_mm)*S,
                                        location=((x0+x1)/2, (y0+y0)/2, (z0_mm+z1_mm)/2*S))
    o = bpy.context.object; o.name = name
    for c in o.users_collection: c.objects.unlink(o)
    cols[col].objects.link(o)
    o.color = COL_COLOR[col]
    return o

def plate(name, poly_mm, z0_mm, z1_mm, col):
    verts = [(x*S, y*S, z1_mm*S) for x, y in poly_mm]
    verts += [(x*S, y*S, z0_mm*S) for x, y in poly_mm]
    n = len(poly_mm)
    faces = [tuple(range(n))] + [tuple(range(n, 2*n))[::-1]]
    for i in range(n):
        j = (i+1) % n
        faces.append((i, j, n+j, n+i))
    me = bpy.data.meshes.new(name); me.from_pydata(verts, [], faces); me.update()
    o = bpy.data.objects.new(name, me); cols[col].objects.link(o)
    o.color = COL_COLOR[col]
    return o

def glass(name, rect_mm, z0, z1, col='03_WINDOWS'):
    o = box(name, rect_mm, z0, z1, col)
    o.color = (0.4, 0.7, 0.9, 0.35); o.display_type = 'TEXTURED'
    o['BLOCKOUT_TEMP_VALUE'] = 'glazing panel; sill/head heights TO_VERIFY'
    return o

# ---------------- wall helpers ----------------
def intervals_along(wrect, orect):
    """overlap interval of orect on wall's long axis."""
    wx0, wy0, wx1, yx1 = wrect
    horiz = (wx1 - wx0) >= (yx1 - wy0)
    if orect[2] <= wx0 or orect[0] >= wx1 or orect[3] <= wy0 or orect[1] >= yx1:
        return None
    if horiz:
        lo, hi = max(orect[0], wx0), min(orect[2], wx1)
        return ('x', lo, hi) if hi - lo > 1 else None
    lo, hi = max(orect[1], wy0), min(orect[3], yx1)
    return ('y', lo, hi) if hi - lo > 1 else None

GLASS_KINDS = {'glazing_door', 'glazing_door_double', 'sliding_glass_3track'}
hole_z = {}   # opening id -> (sill, head)
for o in M['openings']:
    hole_z[o['id']] = (0, TEMP['glass_door_head_mm'] if o['kind'] in GLASS_KINDS
                       else TEMP['door_height_mm'])
for w in M['windows']:
    hole_z['W:' + w['id']] = (0 if w['type'] in ('GLASS_DOOR', 'GLASS_SLIDING_DOOR')
                             else TEMP['window_sill_mm'], TEMP['window_head_mm'])

def build_wall(wrec, top):
    """segment wall rect around openings; returns list of piece rects + cut list."""
    r = wrec['rect']; horiz = (r[2]-r[0]) >= (r[3]-r[1])
    cuts = []
    for o in M['openings']:
        iv = intervals_along(r, o['rect'])
        if iv: cuts.append((iv[1], iv[2], o['id'], 'door'))
    for w in M['windows']:
        iv = intervals_along(r, w['rect'])
        if iv: cuts.append((iv[1], iv[2], 'W:' + w['id'], 'window'))
    cuts.sort()
    segs = []; cur = r[0] if horiz else r[1]
    for lo, hi, oid, kind in cuts:
        a, b = (r[0], r[2]) if horiz else (r[1], r[3])
        lo, hi = max(lo, a), min(hi, b)
        if lo - cur > 1:
            segs.append([cur, r[1], lo, r[3]] if horiz else [r[0], cur, r[2], lo])
        segs.append(('HOLE', [lo, r[1], hi, r[3]] if horiz else [r[0], lo, r[2], hi], oid, kind))
        cur = hi
    a, b = (r[0], r[2]) if horiz else (r[1], r[3])
    if b - cur > 1:
        segs.append([cur, r[1], b, r[3]] if horiz else [r[0], cur, r[2], b])
    i = 0
    for s in segs:
        if s[0] == 'HOLE':
            _, hr, oid, kind = s
            sill, head = hole_z.get(oid, (0, TEMP['door_height_mm']))
            if sill > 0:
                box(f"{wrec['id']}.{oid}.sill", hr, 0, sill, '01_ARCH_EXISTING')
            if head < top:
                box(f"{wrec['id']}.{oid}.lintel", hr, head, top, '01_ARCH_EXISTING')
        else:
            i += 1
            box(f"{wrec['id']}.seg{i}", s, 0, top, '01_ARCH_EXISTING')

# ---------------- architecture ----------------
WALL_TOP = TEMP['ceiling_height_mm']
for w in M['walls']:
    build_wall(w, WALL_TOP)
for p in M['parapets']:
    box(p['id'], p['rect'], 0, TEMP['parapet_height_mm'], '01_ARCH_EXISTING')

# floors per space
for s in M['spaces']:
    lvl = UPPER_Z if s['level'] == 'upper' else 0
    plate('FLOOR.' + s['id'], s['poly'], lvl - TEMP['slab_thickness_mm'], lvl, '01_ARCH_EXISTING')
for b in M['balconies']:
    plate('FLOOR.' + b['id'], b['poly'], -TEMP['slab_thickness_mm'], 0, '01_ARCH_EXISTING')

# steps + ramp
for i, (x0, y0, x1, y1, h) in enumerate(M['stairs']['steps']):
    box(f'STEP.{i+1}', [x0, y0, x1, y1], 0, h, '12_ACCESSIBILITY')
if M.get('ramp'):
    r = M['ramp']['rect']
    box('RAMP-FUTURE.placeholder', r, 0, 60, '12_ACCESSIBILITY')

# windows / glazing
for w in M['windows']:
    r = w['rect']; t = w['type']
    sill, head = hole_z['W:' + w['id']]
    if t == 'BAY_WINDOW':
        bay = w['bay']
        # sill box fills bay projection
        bx = [min(j[0] for j in bay['jambs']), bay['jambs'][0][3] if bay['jambs'][0][3] > r[1] else r[1],
              max(j[2] for j in bay['jambs']), bay['front'][3]]
        box(w['id'] + '.bay_sill', [bay['front'][0], min(bay['jambs'][0][1], r[3]), bay['front'][2], bay['front'][3]],
            0, TEMP['bay_sill_mm'], '01_ARCH_EXISTING')
        box(w['id'] + '.bay_head', [bay['front'][0], min(bay['jambs'][0][1], r[3]), bay['front'][2], bay['front'][3]],
            TEMP['bay_head_mm'], TEMP['bay_roof_mm'], '01_ARCH_EXISTING')
        for i, j in enumerate(bay['jambs']):
            glass(w['id'] + f'.jamb{i}', j, TEMP['bay_sill_mm'], TEMP['bay_head_mm'])
        glass(w['id'] + '.front', bay['front'], TEMP['bay_sill_mm'], TEMP['bay_head_mm'])
        glass(w['id'] + '.open', r, TEMP['bay_sill_mm'], TEMP['bay_head_mm'])
    elif t in ('GLASS_DOOR', 'GLASS_SLIDING_DOOR'):
        glass(w['id'] + '.panel', r, 0, TEMP['glass_door_head_mm'], '04_DOORS' if 'DOOR' in t else '03_WINDOWS')
    elif t == 'BALCONY_WINDOW':
        glass(w['id'] + '.glass', r, TEMP['parapet_height_mm'], TEMP['balcony_glazing_head_mm'])
    else:
        glass(w['id'] + '.glass', r, sill, head)

# door leaves (closed thin slabs) + mark TO_VERIFY doors
for o in M['openings']:
    if o['kind'] in GLASS_KINDS or o['kind'] == 'open_passage':
        continue
    r = o['rect']; horiz = (r[2]-r[0]) >= (r[3]-r[1])
    if horiz:  # opening runs along x: leaf = thin in y
        t = (r[3]-r[1]); yc = (r[1]+r[3])/2
        leaf = [r[0], yc-20, r[2], yc+20]
    else:
        xc = (r[0]+r[2])/2
        leaf = [xc-20, r[1], xc+20, r[3]]
    col = '90_TO_VERIFY' if 'TO_VERIFY' in o['status'] else '04_DOORS'
    d = box('DOOR.' + o['id'], leaf, 0, TEMP['door_height_mm'], col)
    d['opening_kind'] = o['kind']; d['status'] = o['status']

# kitchen cabinets (existing survey)
for c in M['kitchen_cabinets']:
    tall = 'TALL' in c['id'] or 'WALL' in c['id']
    box('KC.' + c['id'], c['rect'], 0, TEMP['kitchen_tall_h' if tall else 'kitchen_counter_h'], '10_KITCHEN')

# ---------------- furniture ----------------
def fh(lb):
    for k, v in [('衣柜', 'wardrobe_h'), ('书柜', 'bookcase_h'), ('矮书柜', 'low_bookcase_h'),
                 ('床头柜', 'nightstand_h'), ('床头占位', 'headboard_h'), ('床背板', 'headboard_h'),
                 ('电视柜', 'tv_console_h'), ('鞋柜', 'shoe_cab_h'),
                 ('三人位', 'sofa_h'), ('双人位', 'sofa_h'), ('贵妃椅', 'chaise_h'),
                 ('茶几', 'coffee_table_h'), ('角几', 'side_table_h'), ('餐桌', 'dining_table_h'),
                 ('餐椅', 'chair_seat_h'), ('凳', 'chair_seat_h'), ('椅', 'chair_seat_h'),
                 ('茶台', 'desk_h'), ('床', 'bed_h'),
                 ('马桶', 'wc_h'), ('洗手盆', 'vanity_h'), ('台盆', 'vanity_h'), ('湿区', 'wetzone_glass_h'),
                 ('叠放', 'washer_dryer_stacked_h'), ('3kg洗衣机', 'washer_3kg_h'), ('冰柜', 'freezer_h'),
                 ('打印机', 'device_h'), ('nas', 'device_h'),
                 ('橱柜', 'kitchen_counter_h')]:
        if k in lb: return TEMP[v]
    return 800

built = []
for f in M['furniture']:
    col = '90_TO_VERIFY' if f.get('unlabeled') else ZONE_COL.get(f['zone'], '90_TO_VERIFY')
    z0 = UPPER_Z if f['zone'] in UPPER_ROOMS else 0
    if f['label'] in ('打印机', 'nas'):
        z0 = TEMP['device_z'] + UPPER_Z
    h = fh(f['label'])
    wall_mount = f['label'] == '3kg洗衣机'
    if wall_mount:
        z0 = (UPPER_Z if f['zone'] in UPPER_ROOMS else 0) + 750   # WALL_MOUNTED candidate
        h = 500
    if f['shape'] == 'cyl':
        o = cyl('F.' + f['label'], f['rect'], z0, z0 + h, col)
    else:
        o = box('F.' + f['label'], f['rect'], z0, z0 + h, col)
    o['source_label'] = f['label']; o['source_obj'] = f['obj']
    o['xy_center_mm'] = [(f['rect'][0]+f['rect'][2])/2, (f['rect'][1]+f['rect'][3])/2]
    if wall_mount:
        o['semantics'] = 'WALL_MOUNTED_COMPACT_WASHER_CANDIDATE'
        o['status'] = 'SKU_TO_VERIFY|INSTALLATION_TO_VERIFY|MEP_TO_VERIFY'
    built.append((f['label'], f['rect'], col))

# ---------------- cameras ----------------
def poly_centroid(poly):
    a = 0; cx = cy = 0.0
    n = len(poly)
    for i in range(n):
        x1,y1 = poly[i]; x2,y2 = poly[(i+1)%n]
        t = x1*y2 - x2*y1; a += t; cx += (x1+x2)*t; cy += (y1+y2)*t
    a *= 0.5
    if abs(a) < 1: return (sum(p[0] for p in poly)/n, sum(p[1] for p in poly)/n)
    return (cx/(6*a), cy/(6*a))

def cam(name, loc_mm, tgt_mm, lens=30, ortho=None):
    cd = bpy.data.cameras.new(name); cd.lens = lens
    if ortho: cd.type = 'ORTHO'; cd.ortho_scale = ortho
    o = bpy.data.objects.new(name, cd); cols['20_CAMERAS'].objects.link(o)
    o.location = [v * S for v in loc_mm]
    d = Vector([t * S for t in tgt_mm]) - o.location
    o.rotation_euler = d.to_track_quat('-Z', 'Y').to_euler()
    return o

SOLID = [w['rect'] for w in M['walls']] + [f['rect'] for f in M['furniture']]

def pt_blocked(x, y, margin=80):
    for r in SOLID:
        if r[0]-margin < x < r[2]+margin and r[1]-margin < y < r[3]+margin:
            return True
    return False

def los_clear(p0, p1):
    dg = bpy.context.evaluated_depsgraph_get()
    o = Vector([v * S for v in p0]); t = Vector([v * S for v in p1])
    d = t - o
    if d.length < 1e-6: return True
    hit = scn.ray_cast(dg, o, d.normalized(), distance=d.length * 0.9)
    return not hit[0]

def room_cam(name, space_id, tgt_xy=None, eye=3100, look_z=250, lens=26):
    sp = next((s for s in M['spaces'] if s['id'] == space_id), None) or \
         next(b for b in M['balconies'] if b['id'] == space_id)
    cx, cy = poly_centroid(sp['poly'])
    lvl = UPPER_Z if sp.get('level') == 'upper' else 0
    tx, ty = tgt_xy or (cx, cy)
    tgt3 = (tx, ty, lvl + look_z)
    probes = [tgt3, (tx + 600, ty, lvl + 200), (tx, ty + 600, lvl + 200), (tx - 500, ty - 500, lvl + 150)]
    offs = [(0, 0)]
    for r_ in (500, 900, 1400, 2000):
        for a in range(8):
            offs.append((r_ * math.cos(a * math.pi / 4), r_ * math.sin(a * math.pi / 4)))
    best_score, px, py = -1, cx, cy
    for dx, dy in offs:
        qx, qy = cx + dx, cy + dy
        if pt_blocked(qx, qy): continue
        p0 = (qx, qy, lvl + eye)
        score = sum(los_clear(p0, q) for q in probes)
        if score == len(probes):
            best_score, px, py = score, qx, qy; break
        if score > best_score:
            best_score, px, py = score, qx, qy
    o = cam(name, [px, py, lvl + eye], list(tgt3), lens=lens)
    o['los_score'] = best_score
    return o

cam('CAM_AXON', [-5000, -9000, 16000], [9000, 6500, 0], ortho=19)
cam('CAM_PLAN_PERSPECTIVE', [9000, -9500, 13500], [9000, 7200, 0], lens=35)
room_cam('CAM_LIVING', 'R-LIVING', tgt_xy=(4500, 10200), eye=2900, lens=24)
room_cam('CAM_DINING', 'R-DINING', tgt_xy=(4300, 3400))
room_cam('CAM_KITCHEN', 'R-KITCHEN', tgt_xy=(7000, 1600), eye=2950)
room_cam('CAM_STUDY', 'R-BED-N', tgt_xy=(15000, 9200))
room_cam('CAM_GUEST', 'R-STUDY', tgt_xy=(11400, 9400))
room_cam('CAM_OWNER_BEDROOM', 'R-BED-S', tgt_xy=(10000, 2300))
room_cam('CAM_MOTHER_BEDROOM', 'R-MASTER', tgt_xy=(13600, 2200))
room_cam('CAM_OWNER_ENSUITE', 'R-CLOAK', tgt_xy=(10300, 5600), eye=2750, lens=22)
room_cam('CAM_MOTHER_BATH', 'R-BATH-M', tgt_xy=(14700, 5600), eye=2750, lens=22)
room_cam('CAM_GUEST_BATH', 'R-BATH-P', tgt_xy=(8900, 9500), eye=2750, lens=22)
cam('CAM_NORTH_BALCONY', [8300, 11300, 2600], [10800, 13300, 500], lens=30)
cam('CAM_SPLIT_LEVEL', [5800, 9200, 3100], [7700, 6900, 100], lens=32)

# ---------------- ground + render settings ----------------
scn.render.engine = 'BLENDER_WORKBENCH'
scn.display.shading.light = 'STUDIO'
scn.display.shading.color_type = 'OBJECT'
scn.display.shading.show_cavity = True
scn.display.shading.cavity_type = 'WORLD'
scn.render.resolution_x = 1280; scn.render.resolution_y = 960
scn.render.film_transparent = False
scn.world = bpy.data.worlds.new('W'); scn.world.color = (0.05, 0.05, 0.05)

bpy.ops.wm.save_as_mainfile(filepath=f'{OUTD}/世纪欣园_B1_BLOCKOUT_V003.blend')

# ---------------- renders ----------------
os.makedirs(f'{OUTD}/renders', exist_ok=True)
REND = {
    'CAM_AXON': 'B1_BLOCKOUT_AXON.png', 'CAM_PLAN_PERSPECTIVE': 'B1_BLOCKOUT_PLAN.png',
    'CAM_LIVING': 'B1_LIVING.png', 'CAM_DINING': 'B1_DINING_KITCHEN.png',
    'CAM_STUDY': 'B1_STUDY.png', 'CAM_GUEST': 'B1_GUEST.png',
    'CAM_OWNER_BEDROOM': 'B1_OWNER_BEDROOM.png', 'CAM_MOTHER_BEDROOM': 'B1_MOTHER_BEDROOM.png',
    'CAM_OWNER_ENSUITE': 'B1_OWNER_ENSUITE.png', 'CAM_MOTHER_BATH': 'B1_MOTHER_BATH.png',
    'CAM_GUEST_BATH': 'B1_GUEST_BATH.png', 'CAM_NORTH_BALCONY': 'B1_NORTH_BALCONY.png',
    'CAM_SPLIT_LEVEL': 'B1_SPLIT_LEVEL.png',
}
for cn, fn in REND.items():
    scn.camera = bpy.data.objects[cn]
    scn.render.filepath = f'{OUTD}/renders/{fn}'
    bpy.ops.render.render(write_still=True)

json.dump({'built_furniture': len(built), 'temp_dims': TEMP},
          open(f'{OUTD}/b1_build_log.json', 'w'), ensure_ascii=False, indent=1)
print('B1 BUILD DONE')
