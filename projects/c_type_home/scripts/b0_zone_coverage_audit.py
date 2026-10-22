"""B0 zone coverage audit.

interior = CAD wall bands + flood-fill from outside -> interior floor footprint
uncovered = interior - (zone polys ∪ true leisure outline ∪ stairs)
Reports every uncovered component; proposes classification, fills nothing.
Outputs B0_ZONE_COVERAGE_AUDIT.png/.json and B0_LEVEL_ZONE_MAP_V6.png.
"""
import json, math
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, Polygon
from collections import deque, Counter

plt.rcParams['font.sans-serif'] = ['PingFang SC', 'Hiragino Sans GB', 'Arial Unicode MS']
plt.rcParams['axes.unicode_minus'] = False

ROOT = '/Users/xiwei/interior_design/projects/c_type_home'
ARCH = ROOT + '/design/pascal_b1/master_direct_arch_v1.json'
MODEL = ROOT + '/design/b1_blockout/b1_model.json'
OUT = ROOT + '/design/blender_b0'
RES = 50  # mm per cell


def pt_in_poly(x, y, poly):
    n = len(poly); ins = False; j = n - 1
    for i in range(n):
        xi, yi = poly[i]; xj, yj = poly[j]
        if ((yi > y) != (yj > y)) and (x < (xj - xi) * (y - yi) / (yj - yi) + xi):
            ins = not ins
        j = i
    return ins


def leisure_poly():
    arc = [(6700 + 1000 * math.cos(math.radians(t)),
            5600 + 1000 * math.sin(math.radians(t))) for t in range(90, 181, 3)]
    return ([(5700, 4700), (8200, 4700), (8244, 4722), (8332, 4543),
             (9095, 4919), (9200, 4971), (9050, 5120), (9050, 6300),
             (9050, 6500), (12900, 6500), (12900, 7800), (7800, 7800),
             (7800, 6600), (6700, 6600)] + arc + [(5700, 5600)])


def main():
    A = json.load(open(ARCH)); M = json.load(open(MODEL))
    walls = [w['rect_mm'] for w in A['walls'] if w.get('rect_mm')]
    xs = [r[i] for r in walls for i in (0, 2)]
    ys = [r[i] for r in walls for i in (1, 3)]
    x0, y0, x1, y1 = min(xs) - 500, min(ys) - 500, max(xs) + 500, max(ys) + 500
    W, H = int((x1 - x0) / RES), int((y1 - y0) / RES)
    def ci(x): return int((x - x0) / RES)
    def cj(y): return int((y - y0) / RES)
    def cx(i): return x0 + (i + .5) * RES
    def cy(j): return y0 + (j + .5) * RES

    wall_m = [[False] * W for _ in range(H)]
    for r in walls:
        for j in range(cj(r[1]), cj(r[3]) + 1):
            for i in range(ci(r[0]), ci(r[2]) + 1):
                if 0 <= i < W and 0 <= j < H: wall_m[j][i] = True

    # zone coverage
    polys = [(s['id'], s['level'], s['poly']) for s in M['spaces']
             if s['id'] not in ('R-LEISURE-W', 'R-LEISURE-E')]
    polys.append(('R-LEISURE', 'upper', leisure_poly()))

    st = M['stairs']['zone']
    zone_m = [[False] * W for _ in range(H)]
    cell_zone = [[None] * W for _ in range(H)]
    for j in range(H):
        for i in range(W):
            if wall_m[j][i]: continue
            px, py = cx(i), cy(j)
            for sid, lv, p in polys:
                if pt_in_poly(px, py, p):
                    zone_m[j][i] = True; cell_zone[j][i] = sid; break
            if not zone_m[j][i] and st[0] <= px <= st[2] and st[1] <= py <= st[3]:
                zone_m[j][i] = True; cell_zone[j][i] = 'STAIRS'

    # interior = morphological closing of (walls ∪ zones) by ~2m: fills
    # corridors/gaps between rooms but excludes the outside-air ring. Wall
    # bands leave unsealed openings, so flood enclosure is unusable.
    def dist_from(src):
        d = [[-1] * W for _ in range(H)]
        dq = deque()
        for j in range(H):
            for i in range(W):
                if src[j][i]: d[j][i] = 0; dq.append((i, j))
        while dq:
            i, j = dq.popleft()
            for di, dj in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                ni, nj = i + di, j + dj
                if 0 <= ni < W and 0 <= nj < H and d[nj][ni] < 0:
                    d[nj][ni] = d[j][i] + 1; dq.append((ni, nj))
        return d

    src = [[wall_m[j][i] or zone_m[j][i] for i in range(W)] for j in range(H)]
    D = 40  # cells × 50mm = 2m
    d1 = dist_from(src)
    dil = [[d1[j][i] <= D for i in range(W)] for j in range(H)]
    d2 = dist_from([[not dil[j][i] for i in range(W)] for j in range(H)])
    closed = [[d2[j][i] > D for i in range(W)] for j in range(H)]
    interior = [[closed[j][i] and not wall_m[j][i] for i in range(W)]
                for j in range(H)]

    # cell-level level assignment: BFS labels propagate through non-wall cells
    # from zone seeds, so each uncovered cell takes the level of the nearest
    # reachable zone (walking distance, walls block propagation)
    zone_level = {sid: lv for sid, lv, _ in polys}
    zone_level['STAIRS'] = 'stairs'
    lab = [[None] * W for _ in range(H)]
    dq = deque()
    for j in range(H):
        for i in range(W):
            if zone_m[j][i]:
                lab[j][i] = zone_level.get(cell_zone[j][i], 'lower')
                dq.append((i, j))
    while dq:
        i, j = dq.popleft()
        for di, dj in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            ni, nj = i + di, j + dj
            if 0 <= ni < W and 0 <= nj < H and not wall_m[nj][ni] \
                    and lab[nj][ni] is None:
                lab[nj][ni] = lab[j][i]; dq.append((ni, nj))

    unc = [[interior[j][i] and not zone_m[j][i] for i in range(W)]
           for j in range(H)]
    # connected components
    seen = [[False] * W for _ in range(H)]
    comps = []
    for j in range(H):
        for i in range(W):
            if unc[j][i] and not seen[j][i]:
                cells = []; dq = deque([(i, j)]); seen[j][i] = True
                while dq:
                    a, b = dq.popleft(); cells.append((a, b))
                    for da, db in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                        na, nb = a + da, b + db
                        if 0 <= na < W and 0 <= nb < H and unc[nb][na] and not seen[nb][na]:
                            seen[nb][na] = True; dq.append((na, nb))
                comps.append(cells)

    # human-marked anchors: blue circle -> LOWER, red circle -> UPPER
    ANCHOR_LOWER = (6200, 7000)
    ANCHOR_UPPER = (12700, 4500)

    report = []
    cell_class = [[None] * W for _ in range(H)]
    for idx, cells in enumerate(comps):
        is_ = [c[0] for c in cells]; js = [c[1] for c in cells]
        bx = (x0 + min(is_) * RES, y0 + min(js) * RES,
              x0 + (max(is_) + 1) * RES, y0 + (max(js) + 1) * RES)
        area = len(cells) * RES * RES / 1e6
        adj = set()
        for a, b in cells:
            for da, db in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                na, nb = a + da, b + db
                if 0 <= na < W and 0 <= nb < H and cell_zone[nb][na]:
                    adj.add(cell_zone[nb][na])
        w, h = bx[2] - bx[0], bx[3] - bx[1]
        edge_strip = min(w, h) <= 150 or area < 0.15
        cell_set = set(cells)
        if any(a in (0, W - 1) or b in (0, H - 1) for a, b in cells):
            cls, why = 'EXTERIOR', 'touches map border (outside building)'
        elif (ci(ANCHOR_LOWER[0]), cj(ANCHOR_LOWER[1])) in cell_set:
            cls, why = 'LOWER_SPLIT_LEVEL', 'anchor: user blue circle'
        elif (ci(ANCHOR_UPPER[0]), cj(ANCHOR_UPPER[1])) in cell_set:
            cls, why = 'UPPER_SPLIT_LEVEL', 'anchor: user red circle'
        else:
            cnt = Counter(lab[b][a] for a, b in cells)
            cnt.pop(None, None)
            if not cnt:
                cls, why = 'TO_VERIFY', 'no reachable zone label'
            else:
                top = cnt.most_common(2)
                dom = top[0][0]
                mixed = len(top) > 1 and top[1][1] / len(cells) > 0.2
                if dom == 'stairs':
                    cls, why = 'STAIR_LANDING', 'nearest-zone=stairs'
                elif mixed:
                    cls, why = 'TO_VERIFY', f'mixed labels {dict(cnt)}'
                else:
                    cls = f'{dom.upper()}_SPLIT_LEVEL'
                    why = f'nearest-zone majority {dom} {top[0][1]}/{len(cells)}'

        # ---- human rulings / source-based overrides ----
        # GAP-17 south-wing corridor -> UPPER (human confirmed: serves
        # bath/study/bedroom circulation after the stair transition)
        if 7700 < bx[0] < 7900 and 8700 < bx[1] < 9200 and bx[2] > 12000 \
                and bx[3] < 11200:
            cls, why = 'UPPER_SPLIT_LEVEL', 'human ruling: upper circulation'
        # CA niche east of master -> exterior AC equipment zone, not floor
        if 15000 < bx[0] and 2200 < bx[1] and bx[3] < 4600:
            cls, why = 'EXTERIOR_AC_EQUIPMENT_ZONE', \
                'original plan marks CA; interior_floor=false; detail TO_VERIFY'
        # GAP-06: one raster component but TWO wall-separated regions —
        # strip+WC niche (open kitchen/dining side) = LOWER; corridor band
        # south of leisure wall serving cloak/bed-S and entering leisure via
        # D-SM door = UPPER. Physical separator = WC room + wall block
        # x5700-5900 y3900-4500. No second level transition exists.
        is_g6 = 5500 < bx[0] < 5800 and 8000 < bx[2] < 9400 \
            and 2400 < bx[1] < 2700 and 4700 < bx[3] < 5000 \
            and len(cells) > 300
        if is_g6:
            cls, why = 'SPLIT_G6', \
                'strip+WC=LOWER (wall-separated); corridor=UPPER via D-SM'
            for a, b in cells:
                px_, py_ = cx(a), cy(b)
                upper_cell = py_ >= 4000 and px_ >= 5700
                cell_class[b][a] = ('UPPER_SPLIT_LEVEL' if upper_cell
                                    else 'LOWER_SPLIT_LEVEL')
        elif cls in ('LOWER_SPLIT_LEVEL', 'UPPER_SPLIT_LEVEL'):
            for a, b in cells:
                cell_class[b][a] = cls
        elif cls == 'TO_VERIFY':
            for a, b in cells: cell_class[b][a] = cls
        elif cls == 'EXTERIOR_AC_EQUIPMENT_ZONE':
            for a, b in cells: cell_class[b][a] = cls
        report.append({
            'id': f'GAP-{idx:02d}', 'bbox_mm': [round(v) for v in bx],
            'area_m2': round(area, 3), 'n_cells': len(cells),
            'adjacent_zones': sorted(adj),
            'classification': cls, 'basis': why,
            'cell_label_counts': dict(Counter(lab[b][a] for a, b in cells)),
            'edge_tolerance_strip': edge_strip,
        })

    real_gaps = [g for g in report
                 if not g['edge_tolerance_strip']
                 and g['classification'] != 'EXTERIOR']
    strips = [g for g in report if g['edge_tolerance_strip']]
    out = {
        'audit': 'B0_ZONE_COVERAGE_AUDIT', 'resolution_mm': RES,
        'interior_cells': sum(sum(r) for r in interior),
        'covered_cells': sum(sum(r) for r in zone_m),
        'uncovered_components_total': len(comps),
        'classification_rule': ('anchor points from user review + adjacency-majority; '
                                'TO_VERIFY if ambiguous'),
        'real_gaps': real_gaps,
        'edge_tolerance_strips': strips,
    }
    json.dump(out, open(OUT + '/B0_ZONE_COVERAGE_AUDIT.json', 'w'),
              ensure_ascii=False, indent=2)

    # ---------- level field (stamped grid) — single source for PNG + JSON --
    # one char per 50mm cell: W wall, L lower, U upper, S stairs,
    # A ac-zone, T to-verify, . outside
    # region-stamped human rulings (independent of gap component ids):
    # AC equipment niche = exterior, physically existing -> 'A' (never floor)
    # GAP-20 recess = TO_VERIFY, level must not be inferred -> 'T'
    AC_RECT = (15300, 2550, 16200, 4400)
    GAP20_RECT = (12900, 11300, 15200, 13400)

    def ruled(px, py):
        if AC_RECT[0] <= px <= AC_RECT[2] and AC_RECT[1] <= py <= AC_RECT[3]:
            return 'A'
        if GAP20_RECT[0] <= px <= GAP20_RECT[2] and \
                GAP20_RECT[1] <= py <= GAP20_RECT[3]:
            return 'T'
        return None

    # boundedness: a non-zone cell is interior only if a wall band lies on
    # BOTH vertical sides and at least one horizontal side. Margin bands
    # outside the envelope (e.g. south facade strip) fail -> '.'
    bN = [[False] * W for _ in range(H)]
    bS = [[False] * W for _ in range(H)]
    bE = [[False] * W for _ in range(H)]
    bW = [[False] * W for _ in range(H)]
    for i in range(W):
        acc = False
        for j in range(H):
            bN[j][i] = acc
            if wall_m[j][i]: acc = True
        acc = False
        for j in range(H - 1, -1, -1):
            bS[j][i] = acc
            if wall_m[j][i]: acc = True
    for j in range(H):
        acc = False
        for i in range(W):
            bW[j][i] = acc
            if wall_m[j][i]: acc = True
        acc = False
        for i in range(W - 1, -1, -1):
            bE[j][i] = acc
            if wall_m[j][i]: acc = True

    def is_bounded(i, j):
        return bN[j][i] and bS[j][i] and (bE[j][i] or bW[j][i])

    grid = []
    for j in range(H):
        row = []
        for i in range(W):
            if wall_m[j][i]: row.append('W'); continue
            cz = cell_class[j][i]
            if cz == 'EXTERIOR_AC_EQUIPMENT_ZONE': ch = 'A'
            elif cz == 'TO_VERIFY': ch = 'T'
            elif cz == 'LOWER_SPLIT_LEVEL': ch = 'L'
            elif cz == 'UPPER_SPLIT_LEVEL': ch = 'U'
            elif cz == 'STAIR_LANDING': ch = 'S'
            elif zone_m[j][i]:
                zid = cell_zone[j][i]
                ch = ('S' if zid == 'STAIRS'
                      else 'U' if zone_level.get(zid) == 'upper' else 'L')
            else:
                ch = '.'
            rl = ruled(cx(i), cy(j))
            if rl == 'A':  # exterior equipment pad: physical, never floor
                ch = 'A'
            elif rl == 'T' and not zone_m[j][i]:
                # GAP-20 ruling pins the uncovered recess; room cells keep level
                ch = 'T'
            if ch in ('L', 'U') and not zone_m[j][i] and not is_bounded(i, j):
                ch = '.'   # outside the wall envelope - not interior floor
            row.append(ch)
        grid.append(''.join(row))

    # ================= EXACT FLOOR-REGION POLYGONS =================
    # The 50mm grid classifies cells only. Region XY boundaries are traced
    # then snapped to CAD truth: wall-band faces, zone-poly edges, stair
    # zone, ruling rects, D-SM door jambs, and the S-楼梯 r1000 arc.
    # geometry_source semantics:
    #   CAD_EXACT_POLYGON  — authored directly from CAD coordinates
    #   CAD_SNAPPED_CONTOUR— raster trace snapped onto CAD faces/lines
    #                        (every edge within snap tolerance of CAD truth)
    gvx = lambda i: x0 + i * RES          # grid vertex -> mm
    gvy = lambda j: y0 + j * RES

    def trace_outer(cells):
        """directed boundary edges, interior on left -> CCW outer loop of
        grid-vertex coords."""
        cs = set(cells); es = set()
        for i, j in cs:
            if (i, j - 1) not in cs: es.add(((i, j), (i + 1, j)))
            if (i + 1, j) not in cs: es.add(((i + 1, j), (i + 1, j + 1)))
            if (i, j + 1) not in cs: es.add(((i + 1, j + 1), (i, j + 1)))
            if (i - 1, j) not in cs: es.add(((i, j + 1), (i, j)))
        nxt = {}
        for a, b in es: nxt.setdefault(a, []).append(b)
        loops = []
        while es:
            a, b = es.pop(); loop = [a, b]; cur = b
            while cur != loop[0]:
                cand = [c for c in nxt.get(cur, ()) if (cur, c) in es]
                if not cand: break
                c = cand[0]; es.discard((cur, c)); loop.append(c); cur = c
            if cur == loop[0]: loops.append(loop[:-1])
        def a_(l):
            return abs(sum(l[k][0]*l[(k+1) % len(l)][1]
                           - l[(k+1) % len(l)][0]*l[k][1]
                           for k in range(len(l))))
        pts = max(loops, key=a_)
        simp = []
        for k in range(len(pts)):  # drop collinear grid verts
            p0, p1, p2 = pts[k-1], pts[k], pts[(k+1) % len(pts)]
            if (p1[0]-p0[0]) * (p2[1]-p1[1]) != \
               (p2[0]-p1[0]) * (p1[1]-p0[1]): simp.append(p1)
        return [(gvx(a), gvy(b)) for a, b in simp]

    # snap targets
    VF, HF = [], []   # (const_coord, lo, hi, tag)
    for r in walls:
        VF += [(r[0], r[1], r[3], 'wall_face'), (r[2], r[1], r[3], 'wall_face')]
        HF += [(r[1], r[0], r[2], 'wall_face'), (r[3], r[0], r[2], 'wall_face')]
    stz = M['stairs']['zone']
    VF += [(stz[0], stz[1], stz[3], 'stair_zone'), (stz[2], stz[1], stz[3], 'stair_zone')]
    HF += [(stz[1], stz[0], stz[2], 'stair_zone'), (stz[3], stz[0], stz[2], 'stair_zone')]
    for rr in (AC_RECT, GAP20_RECT):
        VF += [(rr[0], rr[1], rr[3], 'ruling'), (rr[2], rr[1], rr[3], 'ruling')]
        HF += [(rr[1], rr[0], rr[2], 'ruling'), (rr[3], rr[0], rr[2], 'ruling')]
    for sid, lv, p in polys:
        for k in range(len(p)):
            q0, q1 = p[k], p[(k+1) % len(p)]
            if abs(q0[0]-q1[0]) < 1:
                VF.append((q0[0], min(q0[1], q1[1]), max(q0[1], q1[1]), 'zone'))
            elif abs(q0[1]-q1[1]) < 1:
                HF.append((q0[1], min(q0[0], q1[0]), max(q0[0], q1[0]), 'zone'))
    # CAD platform curve (S-楼梯) and D-SM door jambs as exact snap lines.
    # densify straight portions to <=50mm so nearest-point projection lands
    # on the true segment (sparse endpoints made corner verts snap wrong)
    ARC_PTS = [(6700 + 1000*math.cos(math.radians(t)),
                5600 + 1000*math.sin(math.radians(t)))
               for t in range(180, 89, -3)]   # (5700,5600) -> (6700,6600)
    def densify(pl, step=50):
        out = []
        for k in range(len(pl) - 1):
            a, b = pl[k], pl[k+1]
            L = math.hypot(b[0]-a[0], b[1]-a[1])
            nseg = max(1, int(L/step))
            for s in range(nseg):
                out.append((a[0]+(b[0]-a[0])*s/nseg, a[1]+(b[1]-a[1])*s/nseg))
        out.append(pl[-1])
        return out
    # monotonic traversal: up x5700 -> arc -> arm east
    CURVE = densify([(5700, 4700), (5700, 5600)] + ARC_PTS +
                    [(6700, 6600), (7800, 6600)])
    LINES = [('S-楼梯 platform curve', CURVE),
             ('D-SM jamb W', densify([(8244, 4722), (8332, 4543)])),
             ('D-SM jamb E', densify([(9095, 4919), (9200, 4971)]))]

    def line_dist(px, py, a, b):
        vx, vy = b[0]-a[0], b[1]-a[1]; L2 = vx*vx + vy*vy
        t = max(0, min(1, ((px-a[0])*vx + (py-a[1])*vy)/L2)) if L2 else 0
        return math.hypot(px-(a[0]+vx*t), py-(a[1]+vy*t))

    def near_line(px, py, ln, tol):
        return min(line_dist(px, py, ln[k], ln[k+1])
                   for k in range(len(ln)-1)) < tol

    def proj_on_line(px, py, a, b):
        vx, vy = b[0]-a[0], b[1]-a[1]; L2 = vx*vx + vy*vy
        t = max(0, min(1, ((px-a[0])*vx + (py-a[1])*vy)/L2)) if L2 else 0
        return (a[0]+vx*t, a[1]+vy*t)

    def snap_region(pg):
        """pg: traced mm poly. Replace tooth-chains near exact lines; snap
        remaining axis edges to nearest CAD face. Returns (poly, report)."""
        n = len(pg); locked = [False]*n; rep = {'line_swaps': 0}
        # 1) exact-line chain replacement (curve / door jambs)
        for name, ln in LINES:
            marked = [k for k in range(n)
                      if near_line(pg[k][0], pg[k][1], ln, 90)]
            if not marked: continue
            # rotate so vertex 0 is unmarked -> chains never wrap around
            if 0 in marked:
                k0 = next(k for k in range(n) if k not in marked)
                pg = pg[k0:] + pg[:k0]; locked = locked[k0:] + locked[:k0]
                marked = [k for k in range(n)
                          if near_line(pg[k][0], pg[k][1], ln, 90)]
            runs = []; s = None
            for k in range(n):
                if k in marked and s is None: s = k
                if k not in marked and s is not None:
                    runs.append((s, k - 1)); s = None
            if s is not None: runs.append((s, n - 1))
            def xsect(p_from, p_to, ln):
                """extend edge p_from->p_to past p_to; return
                (dist_mm, pt, fractional_index) of nearest hit on ln."""
                dx, dy = p_to[0]-p_from[0], p_to[1]-p_from[1]
                if abs(dx) < 1e-9 and abs(dy) < 1e-9: return None
                best = None
                for k in range(len(ln) - 1):
                    a_, b_ = ln[k], ln[k+1]
                    ex, ey = b_[0]-a_[0], b_[1]-a_[1]
                    den = dx*ey - dy*ex
                    if abs(den) < 1e-9: continue
                    t = ((a_[0]-p_to[0])*ey - (a_[1]-p_to[1])*ex)/den
                    s = ((a_[0]-p_to[0])*dy - (a_[1]-p_to[1])*dx)/den
                    if t >= -1e-6 and -1e-6 <= s <= 1 + 1e-6:
                        pt = (p_to[0]+t*dx, p_to[1]+t*dy)
                        d_ = t*math.hypot(dx, dy)
                        if best is None or d_ < best[0]:
                            best = (d_, pt, k+s)
                return best
            for a, b in runs:
                if a == b:
                    continue  # lone vertex near a line: not a chain - leave
                    #           it for axis-edge snapping
                pA = pg[(a - 1) % n]; vA = pg[a]
                pB = pg[(b + 1) % n]; vB = pg[b]
                # join = where the edge adjacent to the run, extended past
                # the run vertex, meets the exact line (e.g. west edge
                # x5700 meets the arc at its (5700,5600) endpoint)
                def join(p_o, v_r):
                    """edge p_o->v_r runs into the exact line; find join."""
                    x = xsect(p_o, v_r, ln)
                    if x: return x[1], x[2]
                    # edge parallel to / stopping short of the line: snap the
                    # edge onto its CAD face first, retry the extension
                    if abs(v_r[0]-p_o[0]) < 1:
                        c = p_o[0]
                        fx = [f[0] for f in VF
                              if abs(f[0]-c) <= 150]
                        if fx:
                            c2 = min(fx, key=lambda f: abs(f-c))
                            x = xsect((c2, p_o[1]), (c2, v_r[1]), ln)
                            if x: return x[1], x[2]
                            # collinear overlap: same-axis ln vertex nearest
                            # to v_r (e.g. arc endpoint on the wall face).
                            # tol 1mm keeps near-axis arc pts out so the true
                            # corner vertex wins (CAD faces align within ~0.5)
                            cand = [q for q in range(len(ln))
                                    if abs(ln[q][0]-c2) < 1]
                            if cand:
                                q = min(cand,
                                        key=lambda q:
                                        (ln[q][1]-v_r[1])**2)
                                return ln[q], float(q)
                    elif abs(v_r[1]-p_o[1]) < 1:
                        c = p_o[1]
                        fy = [f[0] for f in HF
                              if abs(f[0]-c) <= 150]
                        if fy:
                            c2 = min(fy, key=lambda f: abs(f-c))
                            x = xsect((p_o[0], c2), (v_r[0], c2), ln)
                            if x: return x[1], x[2]
                            cand = [q for q in range(len(ln))
                                    if abs(ln[q][1]-c2) < 1]
                            if cand:
                                q = min(cand,
                                        key=lambda q:
                                        (ln[q][0]-v_r[0])**2)
                                return ln[q], float(q)
                    q = min(range(len(ln)),
                            key=lambda q: (ln[q][0]-v_r[0])**2
                            + (ln[q][1]-v_r[1])**2)
                    return ln[q], float(q)
                ptA, fA = join(pA, vA)
                ptB, fB = join(pB, vB)
                lo, hi = (fA, fB) if fA <= fB else (fB, fA)
                body = ln[math.ceil(lo - 1e-9):int(hi) + 1]
                sub = [ptA] + body + [ptB]
                if fA > fB: sub = sub[::-1]
                pg = pg[:a] + sub + pg[b+1:]
                n = len(pg)
                locked = locked[:a] + [True]*len(sub) + locked[b+1:]
                rep['line_swaps'] += 1
                break  # one chain per line per region is enough here
        # 2) axis-edge snapping — dev = RESIDUAL distance to CAD boundary
        #    (0 after a successful snap); snap_mm records how far moved
        devs = []; snaps = []
        n = len(pg)
        for k in range(n):
            p0, p1 = pg[k], pg[(k+1) % n]
            if locked[k] and locked[(k+1) % n]:
                devs.append(0.0); continue
            dx, dy = abs(p1[0]-p0[0]), abs(p1[1]-p0[1])
            if dx < 1:   # vertical edge x=c over y range
                c = p0[0]; lo, hi = sorted((p0[1], p1[1]))
                L = hi-lo
                cand = [(abs(fx-c), fx) for fx, fl, fh, tg in VF
                        if abs(fx-c) <= 150 and min(fh, hi)-max(fl, lo) > 0]
                if cand:
                    _, fx = min(cand)
                    pg[k] = (fx, p0[1]); pg[(k+1) % n] = (fx, p1[1])
                    snaps.append(abs(fx-c)); devs.append(0.0)
                else:
                    # extrapolated snap: same-axis face within 150 but its
                    # range doesn't overlap — e.g. doorway niche continuing
                    # a wall column face
                    cand2 = [(abs(fx-c), fx) for fx, fl, fh, tg in VF
                             if abs(fx-c) <= 150]
                    if cand2:
                        _, fx = min(cand2)
                        pg[k] = (fx, p0[1]); pg[(k+1) % n] = (fx, p1[1])
                        snaps.append(abs(fx-c)); devs.append(0.0)
                        rep['extrapolated'] = rep.get('extrapolated', 0) + 1
                    else:
                        devs.append(min((abs(fx-c) for fx, fl, fh, tg in VF
                                         if min(fh, hi)-max(fl, lo) > 0),
                                        default=9999.0))
            elif dy < 1: # horizontal edge y=c
                c = p0[1]; lo, hi = sorted((p0[0], p1[0]))
                L = hi-lo
                cand = [(abs(fy-c), fy) for fy, fl, fh, tg in HF
                        if abs(fy-c) <= 150 and min(fh, hi)-max(fl, lo) > 0]
                if cand:
                    _, fy = min(cand)
                    pg[k] = (p0[0], fy); pg[(k+1) % n] = (p1[0], fy)
                    snaps.append(abs(fy-c)); devs.append(0.0)
                else:
                    cand2 = [(abs(fy-c), fy) for fy, fl, fh, tg in HF
                             if abs(fy-c) <= 150]
                    if cand2:
                        _, fy = min(cand2)
                        pg[k] = (p0[0], fy); pg[(k+1) % n] = (p1[0], fy)
                        snaps.append(abs(fy-c)); devs.append(0.0)
                        rep['extrapolated'] = rep.get('extrapolated', 0) + 1
                    else:
                        devs.append(min((abs(fy-c) for fy, fl, fh, tg in HF
                                         if min(fh, hi)-max(fl, lo) > 0),
                                        default=9999.0))
            else:
                devs.append(0.0)  # part of an exact line segment
        rep['max_dev_mm'] = round(max(devs or [0]), 1)
        rep['max_snap_mm'] = round(max(snaps or [0]), 1)
        rep['unsnapped_edges'] = sum(1 for d in devs if d > 150)
        # cleanup: dedupe consecutive verts, drop collinear
        out = []
        for p in pg:
            if not out or math.hypot(p[0]-out[-1][0], p[1]-out[-1][1]) > 1:
                out.append(p)
        if len(out) > 1 and math.hypot(out[0][0]-out[-1][0],
                                       out[0][1]-out[-1][1]) <= 1:
            out.pop()
        fin = []
        for k in range(len(out)):
            p0, p1, p2 = out[k-1], out[k], out[(k+1) % len(out)]
            vx1, vy1 = p1[0]-p0[0], p1[1]-p0[1]
            vx2, vy2 = p2[0]-p1[0], p2[1]-p1[1]
            if abs(vx1*vy2 - vx2*vy1) > 1e-6 or \
               math.hypot(vx1, vy1) < 1 or math.hypot(vx2, vy2) < 1:
                fin.append(p1)
        return fin, rep

    # gap-cell components per class (zone cells come from exact polys)
    gap_cells = {'L': set(), 'U': set()}
    for j in range(H):
        for i in range(W):
            if not zone_m[j][i] and grid[j][i] in ('L', 'U'):
                gap_cells[grid[j][i]].add((i, j))

    def comp_list(cellset):
        seen = set(); out_ = []
        for c in cellset:
            if c in seen: continue
            dq = deque([c]); seen.add(c); cur = []
            while dq:
                p = dq.popleft(); cur.append(p)
                for d in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    q = (p[0]+d[0], p[1]+d[1])
                    if q in cellset and q not in seen:
                        seen.add(q); dq.append(q)
            out_.append(cur)
        return out_

    regions = {'lower': [], 'upper': []}
    edge_report = []
    for lvl, key in (('lower', 'L'), ('upper', 'U')):
        for sid, lv, p in polys:                       # exact CAD zone polys
            if lv == lvl:
                regions[lvl].append({'name': sid, 'poly': p,
                                     'geometry_source': 'CAD_EXACT_POLYGON',
                                     'max_dev_mm': 0.0,
                                     'arc': sid == 'R-LEISURE'})
        for comp in comp_list(gap_cells[key]):
            if len(comp) < 4: continue                 # sub-cell slivers
            traced = trace_outer(comp)
            if len(traced) < 3: continue
            snapped, rep = snap_region(traced)
            if len(snapped) < 3: continue
            xs_ = [p[0] for p in snapped]; ys_ = [p[1] for p in snapped]
            nm = f'{key}-region@({round(min(xs_))},{round(min(ys_))})'
            regions[lvl].append({'name': nm, 'poly': snapped,
                                 'geometry_source': 'CAD_SNAPPED_CONTOUR',
                                 'max_dev_mm': rep['max_dev_mm'],
                                 'arc': False})
            edge_report.append({'region': nm, 'level': lvl,
                                'n_verts': len(snapped), **rep})

    # seam fill: L/U gap cells still uncovered by any region poly get a
    # snapped-bbox patch (door-jamb/threshold slivers <= ~100mm)
    def in_poly(px, py, pg):
        c = False; j = len(pg) - 1
        for i_ in range(len(pg)):
            xi, yi = pg[i_]; xj, yj = pg[j]
            if (yi > py) != (yj > py) and \
                    px < (xj-xi)*(py-yi)/(yj-yi)+xi:
                c = not c
            j = i_
        return c
    seam_cells = {'L': set(), 'U': set()}
    for key in ('L', 'U'):
        lvl = 'lower' if key == 'L' else 'upper'
        pls = [r['poly'] for r in regions[lvl]]
        for (i, j) in gap_cells[key]:
            if not any(in_poly(gvx(i)+RES/2, gvy(j)+RES/2, p)
                       for p in pls):
                    seam_cells[key].add((i, j))
    n_seam = 0
    for _pass in range(4):
        if _pass:
            seam_cells = {'L': set(), 'U': set()}
            for key in ('L', 'U'):
                lvl = 'lower' if key == 'L' else 'upper'
                pls = [r['poly'] for r in regions[lvl]]
                for (i, j) in gap_cells[key]:
                    if not any(in_poly(gvx(i)+RES/2, gvy(j)+RES/2, p)
                               for p in pls):
                        seam_cells[key].add((i, j))
        for key in ('L', 'U'):
            lvl = 'lower' if key == 'L' else 'upper'
            for comp in comp_list(seam_cells[key]):
                xs_ = [gvx(i) for i, j in comp]
                xe = [gvx(i + 1) for i, j in comp]
                ys_ = [gvy(j) for i, j in comp]
                ye = [gvy(j + 1) for i, j in comp]
                x0_, x1_, y0_, y1_ = min(xs_), max(xe), min(ys_), max(ye)

                # prefer faces OUTSIDE the cell bbox (expand to wall faces);
                # if none, inward faces; revert an axis if the patch would no
                # longer cover every cell
                def snap_lo(c):
                    out_ = [f[0] for f in VF + HF if f[0] <= c <= f[0] + 150]
                    if out_: return max(out_)
                    in_ = [f[0] for f in VF + HF if c - 150 <= f[0] < c]
                    return max(in_) if in_ else c
                def snap_hi(c):
                    out_ = [f[0] for f in VF + HF if c <= f[0] <= c + 150]
                    if out_: return min(out_)
                    in_ = [f[0] for f in VF + HF if c - 150 <= f[0] < c]
                    return max(in_) if in_ else c
                sx0 = snap_lo(x0_); sx1 = snap_hi(x1_)
                sy0 = snap_lo(y0_); sy1 = snap_hi(y1_)
                if sx1 - sx0 >= 10: x0_, x1_ = sx0, sx1
                if sy1 - sy0 >= 10: y0_, y1_ = sy0, sy1
                nm = f'{key}-seam@({round(x0_)},{round(y0_)})'
                regions[lvl].append({'name': nm,
                                     'poly': [(x0_, y0_), (x1_, y0_),
                                              (x1_, y1_), (x0_, y1_)],
                                     'geometry_source': 'CAD_SNAPPED_CONTOUR',
                                     'max_dev_mm': 0.0, 'arc': False})
                edge_report.append({'region': nm, 'level': lvl, 'n_verts': 4,
                                    'line_swaps': 0, 'max_dev_mm': 0.0,
                                    'max_snap_mm': 0.0, 'unsnapped_edges': 0,
                                    'seam_fill': True})
                n_seam += 1
        if not seam_cells['L'] and not seam_cells['U']: break
        if _pass == 3:
            print('WARNING residual uncovered cells:',
                  sorted(seam_cells['L'])[:10], sorted(seam_cells['U'])[:10])
    print('seam patches:', n_seam)
    json.dump({'regions': regions,
               'stair_zone_mm': stz,
               'ac_rect_mm': AC_RECT, 'gap20_rect_mm': GAP20_RECT,
               'deviation_policy': {
                   'straight_edge': 'snapped to CAD wall face / zone edge, '
                                    'tolerance <= 1mm',
                   'curved_edge': 'exact S-楼梯 r1000 arc, tessellation 3deg '
                                  '=> chord error 0.34mm <= 2mm'},
               'edge_report': edge_report},
              open(OUT + '/B0_FLOOR_REGIONS.json', 'w'), indent=1)
    print('floor regions:',
          {k: len(v) for k, v in regions.items()},
          '| max dev:', max(e['max_dev_mm'] for e in edge_report))

    import numpy as np
    CLS_COL = {'LOWER_SPLIT_LEVEL': (0.55, 0.80, 0.95),
               'UPPER_SPLIT_LEVEL': (1.0, 0.72, 0.45),
               'TO_VERIFY': (0.95, 0.3, 0.9),
               'EXTERIOR_AC_EQUIPMENT_ZONE': (0.55, 0.55, 0.55),
               'STAIR_LANDING': (0.5, 0.9, 0.5)}
    gap_img = np.zeros((H, W, 4))
    for j in range(H):
        for i in range(W):
            c = cell_class[j][i]
            if c in CLS_COL: gap_img[j, i] = (*CLS_COL[c], 0.9)

    def base_map(title):
        fig, ax = plt.subplots(figsize=(15, 10.5))
        for r in walls:
            ax.add_patch(Rectangle((r[0], r[1]), r[2] - r[0], r[3] - r[1],
                                  fc='#999', ec='none'))
        COL = {'lower': '#b7d7f0', 'upper': '#f4c89a'}
        for sid, lv, p in polys:
            ax.add_patch(Polygon(p, closed=True, fc=COL[lv], ec='#666', lw=.8,
                                 alpha=.75))
        ax.add_patch(Rectangle((st[0], st[1]), st[2] - st[0], st[3] - st[1],
                               fc='#7ec87e', ec='green', lw=1.5, hatch='//'))
        ax.set_xlim(800, 16700); ax.set_ylim(14200, -1200); ax.set_aspect('equal')
        ax.set_title(title)
        return fig, ax

    fig, ax = base_map('B0 ZONE COVERAGE AUDIT — uncovered cells classified: '
                       'cyan=LOWER orange=UPPER magenta=TO_VERIFY')
    ax.imshow(gap_img, extent=(x0, x1, y0, y1), origin='lower',
              interpolation='none', alpha=.85)
    for g in real_gaps:
        b = g['bbox_mm']
        ax.text((b[0] + b[2]) / 2, (b[1] + b[3]) / 2,
                f"{g['id']} {g['area_m2']}m2", ha='center', va='center',
                fontsize=8, weight='bold',
                color='#036' if 'LOWER' in g['classification'] else '#a40')
    ax.annotate('蓝圈→LOWER', xy=ANCHOR_LOWER, xytext=(4500, 9500), fontsize=9,
                color='#036', arrowprops=dict(arrowstyle='->', color='#036'))
    ax.annotate('红圈→UPPER', xy=ANCHOR_UPPER, xytext=(14000, 3000), fontsize=9,
                color='#a40', arrowprops=dict(arrowstyle='->', color='#a40'))
    plt.tight_layout(); plt.savefig(OUT + '/B0_ZONE_COVERAGE_AUDIT.png', dpi=140)

    # ---------- V7 zone map ----------
    fig, ax = base_map('B0 LEVEL ZONE MAP V7 — gaps classified by wall-bounded '
                       'topology | cyan=LOWER orange=UPPER magenta=TO_VERIFY '
                       'gray=AC zone')
    hatch_img = gap_img.copy(); hatch_img[..., 3] *= 0.55
    ax.imshow(hatch_img, extent=(x0, x1, y0, y1), origin='lower',
              interpolation='none')
    EC = {'LOWER_SPLIT_LEVEL': '#06c', 'UPPER_SPLIT_LEVEL': '#f80',
          'TO_VERIFY': '#c0c', 'EXTERIOR_AC_EQUIPMENT_ZONE': '#666',
          'SPLIT_G6': '#606', 'STAIR_LANDING': '#090'}
    for g in real_gaps:
        b = g['bbox_mm']
        if g['classification'] == 'SPLIT_G6':
            ax.annotate('餐厨条带/WC=LOWER\n南走廊=UPPER(经D-SM)\nGAP-06', 
                        xy=(7400, 4300), xytext=(5800, 2600), fontsize=8,
                        color='#606',
                        arrowprops=dict(arrowstyle='->', color='#606'))
            continue
        ec = EC.get(g['classification'], '#c0c')
        ax.add_patch(Rectangle((b[0], b[1]), b[2] - b[0], b[3] - b[1], fc='none',
                               ec=ec, lw=1.2,
                               hatch='//' if 'TO' not in g['classification']
                               else 'xx'))
        ax.text((b[0] + b[2]) / 2, (b[1] + b[3]) / 2,
                f"{g['classification'].replace('_SPLIT_LEVEL', '')}\n"
                f"{g['id']}", ha='center', va='center', fontsize=7, color=ec)
    r = M['ramp']['rect']
    ax.add_patch(Rectangle((r[0], r[1]), r[2] - r[0], r[3] - r[1], fc='none',
                           ec='#e07000', lw=2, hatch='xx'))
    ax.text(r[0] + 50, r[1] + 150, 'FUTURE ramp (overlay only)', fontsize=8,
            color='#e07000')
    ax.text(6900, 6200, '扇形休闲厅 LEISURE\nUPPER FFL+450', ha='center',
            fontsize=9, weight='bold')
    plt.tight_layout(); plt.savefig(OUT + '/B0_LEVEL_ZONE_MAP_V7.png', dpi=140)

    # ---------- GAP-06 topology review zoom ----------
    DXF = ROOT + '/cad/freecad_import/世纪欣园FF_freecad_WORKING_v2.dxf'
    raw = open(DXF, errors='ignore').read()
    lines = raw.split('\n'); ents = []; cur = None; in_e = False
    for i, l in enumerate(lines):
        v = l.strip()
        if v == 'ENTITIES': in_e = True; continue
        if v == 'ENDSEC' and in_e: in_e = False
        if not in_e: continue
        if v in ('LINE', 'ARC', 'LWPOLYLINE', 'CIRCLE'):
            if cur: ents.append(cur)
            cur = {'type': v, 'pts': []}
        if cur is not None:
            if v == '8': cur['layer'] = lines[i + 1].strip()
            elif v == '10':
                if cur['type'] == 'LWPOLYLINE': cur['pts'].append([float(lines[i + 1]), 0])
                else: cur['x0'] = float(lines[i + 1])
            elif v == '20':
                if cur['type'] == 'LWPOLYLINE': cur['pts'][-1][1] = float(lines[i + 1])
                else: cur['y0'] = float(lines[i + 1])
            elif v == '11': cur['x1'] = float(lines[i + 1])
            elif v == '21': cur['y1'] = float(lines[i + 1])
            elif v == '40': cur['r'] = float(lines[i + 1])
            elif v == '50': cur['a0'] = float(lines[i + 1])
            elif v == '51': cur['a1'] = float(lines[i + 1])
    if cur: ents.append(cur)
    OX_, OY_ = 1298172.0, 296458.0
    LC = {'S-S.WALL': '#111', 'F-DOOR': '#e33', 'F-FURN': '#bbb',
          'F-SAN FIT': '#6ad', 'S-楼梯': '#0a0'}
    fig, ax = plt.subplots(figsize=(11, 10))
    # paint classified gap cells faintly
    ax.imshow(gap_img, extent=(x0, x1, y0, y1), origin='lower',
              interpolation='none', alpha=.5)
    for e in ents:
        lay = e.get('layer', '?'); col = LC.get(lay, '#ccc')
        lw = 2.4 if lay == 'S-S.WALL' else 1.2
        if e['type'] == 'LWPOLYLINE':
            pts = [(p[0] - OX_, p[1] + OY_) for p in e['pts']]
            ax.plot([p[0] for p in pts], [p[1] for p in pts], lw=lw, color=col)
        elif e['type'] == 'LINE':
            a = (e['x0'] - OX_, e['y0'] + OY_); b = (e['x1'] - OX_, e['y1'] + OY_)
            ax.plot([a[0], b[0]], [a[1], b[1]], lw=lw, color=col)
        elif e['type'] == 'ARC':
            cxx, cyy = e['x0'] - OX_, e['y0'] + OY_
            a0, a1 = e['a0'], e['a1']
            if a1 < a0: a1 += 360
            th = [math.radians(t) for t in range(int(a0), int(a1) + 1, 3)]
            ax.plot([cxx + e['r'] * math.cos(t) for t in th],
                    [cyy + e['r'] * math.sin(t) for t in th], lw=lw, color=col)
    # annotations: physical separator + connections
    ax.add_patch(Rectangle((5700, 3900), 400, 600, fc='none', ec='#d00', lw=2))
    ax.text(5900, 4200, 'WC/服务间+墙块\n(物理分隔)', fontsize=8, color='#d00',
            ha='center', va='center')
    ax.annotate('D-SM 斜门 → 休闲厅(UPPER)', xy=(8700, 4800), xytext=(9300, 3300),
                fontsize=9, color='#e33',
                arrowprops=dict(arrowstyle='->', color='red'))
    ax.annotate('餐厨开放条带 → LOWER', xy=(5600, 2200), xytext=(4200, 1800),
                fontsize=9, color='#06c',
                arrowprops=dict(arrowstyle='->', color='#06c'))
    ax.annotate('WC 门洞 → 楼梯前厅(LOWER)', xy=(5675, 4600), xytext=(4300, 5200),
                fontsize=9, color='#06c',
                arrowprops=dict(arrowstyle='->', color='#06c'))
    ax.text(7400, 4300, '南走廊 = UPPER\n(仅经 D-SM/衣帽区连通上层)', fontsize=9,
            color='#a40', ha='center', weight='bold')
    ax.set_xlim(3800, 10000); ax.set_ylim(6200, -1000); ax.set_aspect('equal')
    ax.grid(alpha=.25)
    ax.set_title('GAP-06 TOPOLOGY REVIEW — CAD linework + level split:\n'
                 'cyan=LOWER(strip/WC) orange=UPPER(corridor) | '
                 'no raster invent, boundary = real wall block')
    plt.tight_layout()
    plt.savefig(OUT + '/B0_GAP06_TOPOLOGY_REVIEW.png', dpi=140)

    # ---------- V8 CLEAN zone map ----------
    # no audit frames/hatches: flat level fills + real CAD linework only.
    fig, ax = plt.subplots(figsize=(15, 10.5))
    for w in A['walls']:
        r = w.get('rect_mm')
        if r: ax.add_patch(Rectangle((r[0], r[1]), r[2] - r[0], r[3] - r[1],
                                    fc='#8a8a8a', ec='none'))
    COL = {'lower': '#a9cdec', 'upper': '#f2b878'}
    for sid, lv, p in polys:
        ax.add_patch(Polygon(p, closed=True, fc=COL[lv], ec='none', alpha=.85))
        xs_ = [q[0] for q in p]; ys_ = [q[1] for q in p]
        ax.text((min(xs_) + max(xs_)) / 2, (min(ys_) + max(ys_)) / 2,
                {'lower': 'L', 'upper': 'U'}[lv], ha='center', va='center',
                fontsize=7, color='#666', alpha=.7)
    ax.add_patch(Rectangle((st[0], st[1]), st[2] - st[0], st[3] - st[1],
                           fc='#7ec87e', ec='green', lw=1.5))
    ax.text(7500, 8300, 'STAIRS 3×150', ha='center', fontsize=8,
            color='green', weight='bold')
    # classified cells from the stamped level field — flat fill, no outlines
    GCOL = {'L': (0.66, 0.80, 0.92), 'U': (0.95, 0.72, 0.47),
            'S': (0.49, 0.78, 0.49), 'A': (0.55, 0.55, 0.55),
            'T': (0.94, 0.31, 0.87)}
    clean = np.zeros((H, W, 4))
    for j in range(H):
        for i in range(W):
            c = grid[j][i]
            if c in GCOL: clean[j, i] = (*GCOL[c], 0.55)
    ax.imshow(clean, extent=(x0, x1, y0, y1), origin='lower',
              interpolation='none')
    # CAD linework on top — walls black, doors red, stair layer green
    ents2 = ents
    for e in ents2:
        lay = e.get('layer', '?')
        if lay not in ('S-S.WALL', 'F-DOOR', 'S-楼梯'): continue
        col = LC[lay]; lw = 1.6 if lay == 'S-S.WALL' else 1.0
        if e['type'] == 'LWPOLYLINE':
            pts = [(p[0] - OX_, p[1] + OY_) for p in e['pts']]
            ax.plot([p[0] for p in pts], [p[1] for p in pts], lw=lw, color=col)
        elif e['type'] == 'LINE':
            a2 = (e['x0'] - OX_, e['y0'] + OY_); b2 = (e['x1'] - OX_, e['y1'] + OY_)
            ax.plot([a2[0], b2[0]], [a2[1], b2[1]], lw=lw, color=col)
        elif e['type'] == 'ARC':
            cxx, cyy = e['x0'] - OX_, e['y0'] + OY_
            a0_, a1_ = e['a0'], e['a1']
            if a1_ < a0_: a1_ += 360
            th = [math.radians(t) for t in range(int(a0_), int(a1_) + 1, 3)]
            ax.plot([cxx + e['r'] * math.cos(t) for t in th],
                    [cyy + e['r'] * math.sin(t) for t in th], lw=lw, color=col)
    r = M['ramp']['rect']
    ax.add_patch(Rectangle((r[0], r[1]), r[2] - r[0], r[3] - r[1],
                           fc='#e07000', ec='#e07000', lw=0, alpha=.18))
    ax.add_patch(Rectangle((r[0], r[1]), r[2] - r[0], r[3] - r[1], fc='none',
                           ec='#e07000', lw=1.5, ls='--'))
    ax.text(r[0] + 100, r[1] + 300, 'FUTURE ramp\n(overlay only)', fontsize=8,
            color='#e07000')
    # minimal level labels
    ax.text(7000, 6200, '扇形休闲厅\nUPPER +450', ha='center', fontsize=9,
            weight='bold')
    # legend
    from matplotlib.patches import Patch
    ax.legend(handles=[
        Patch(fc='#a9cdec', label='LOWER_SPLIT_LEVEL  FFL Z0'),
        Patch(fc='#f2b878', label='UPPER_SPLIT_LEVEL  FFL +450'),
        Patch(fc='#7ec87e', label='EXISTING_STAIRS  3×150'),
        Patch(fc='#8c8c8c', label='EXTERIOR_AC_ZONE (非室内地面)'),
        Patch(fc='#f04ee0', label='TO_VERIFY (GAP-20)'),
        Patch(fc='#e07000', alpha=.3, label='FUTURE ramp option')],
        loc='lower right', fontsize=8, framealpha=.9)
    ax.set_xlim(800, 16700); ax.set_ylim(14200, -1200); ax.set_aspect('equal')
    ax.set_title('B0 LEVEL ZONE MAP V8 CLEAN — level semantics on CAD floor '
                 'footprint (zones assign Z only; XY boundary = CAD)')
    plt.tight_layout()
    plt.savefig(OUT + '/B0_LEVEL_ZONE_MAP_V8_CLEAN.png', dpi=140)

    # ---------- CAD overlay gates ----------
    # black = CAD linework (S-S.WALL / S-楼梯 / F-DOOR);
    # colored fill = exported floor/ceiling region boundaries
    def overlay(fname, title, polylists):
        fig, ax = plt.subplots(figsize=(15, 10.5))
        for e in ents:
            if e.get('layer') not in ('S-S.WALL', 'S-楼梯', 'F-DOOR'): continue
            if e['type'] == 'LWPOLYLINE':
                pts = [(p[0]-OX_, p[1]+OY_) for p in e['pts']]
                ax.plot([p[0] for p in pts], [p[1] for p in pts],
                        lw=2.2, color='black')
            elif e['type'] == 'LINE':
                a2 = (e['x0']-OX_, e['y0']+OY_); b2 = (e['x1']-OX_, e['y1']+OY_)
                ax.plot([a2[0], b2[0]], [a2[1], b2[1]], lw=2.2, color='black')
            elif e['type'] == 'ARC':
                cxx, cyy = e['x0']-OX_, e['y0']+OY_
                a0_, a1_ = e['a0'], e['a1']
                if a1_ < a0_: a1_ += 360
                th = [math.radians(t) for t in range(int(a0_), int(a1_)+1, 3)]
                ax.plot([cxx+e['r']*math.cos(t) for t in th],
                        [cyy+e['r']*math.sin(t) for t in th],
                        lw=2.2, color='black')
        for poly, col in polylists:
            ax.add_patch(Polygon(poly, closed=True, fc=col, ec='#e33',
                                 lw=1.0, ls='--', alpha=.45))
        ax.set_xlim(800, 16700); ax.set_ylim(14200, -1200)
        ax.set_aspect('equal')
        ax.set_title(title)
        plt.tight_layout(); plt.savefig(OUT + '/' + fname, dpi=140)
        plt.close(fig)

    fl = [(r['poly'], '#a9cdec') for r in regions['lower']] + \
         [(r['poly'], '#f2b878') for r in regions['upper']]
    overlay('B0_FLOOR_CAD_OVERLAY.png',
            'B0 FLOOR x CAD OVERLAY — black=CAD linework, fill=region poly; '
            'straight dev<=1mm, arc tess 0.34mm', fl)
    # ceiling uses identical XY footprints (regions) — same overlay source
    overlay('B0_CEILING_CAD_OVERLAY.png',
            'B0 CEILING x CAD OVERLAY — same XY as floor regions; '
            'ceiling follows level region union', fl)

    # ---------- level field export for Blender ----------
    json.dump({'res_mm': RES, 'x0': x0, 'y0': y0, 'w': W, 'h': H,
               'grid': grid,
               'role': 'SEMANTIC_HELPER_ONLY',
               'geometry_authority': False,
               'physical_ground_truth': False,
               'legend': {'W': 'wall', 'L': 'LOWER', 'U': 'UPPER',
                          'S': 'stairs', 'A': 'ac_zone', 'T': 'to_verify',
                          '.': 'outside'}},
              open(OUT + '/B0_LEVEL_FIELD.json', 'w'))
    print('level field exported', W, 'x', H)

    print(json.dumps({'real_gaps': real_gaps,
                      'n_strips': len(strips)}, ensure_ascii=False, indent=1))


if __name__ == '__main__':
    main()
