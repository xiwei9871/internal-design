#!/usr/bin/env python3
"""A301 走顶路由示意 / A302 电气·控制·网络点位 / A303 给水点位 (CD_V01, SCHEMATIC).
Inputs: mep_points.py (PROPOSED / TBD), data/lighting_points_v2.json (logical control groups), A202 zones.
Outputs: work/A30x_*.dxf, data/mep_points.{json,csv}, data/mep_routes.json, qa/mep_qa.json.
Routes are schematic (not sized); sources, physical circuits, ceiling void and drops are TBD."""
import csv, json, math
from shapely.geometry import LineString, Point, box
from shapely.ops import unary_union

import mep_points as M
from cd_common import (Base, WORK, DATA, HERE, NAMES, OWNER, H_SMALL, H_TINY, layer, text, hatch, notes,
                       label_point)
from lighting_review import nodrop_zones

V2 = json.loads((DATA / 'lighting_points_v2.json').read_text())['points']
SYSL = {'POWER': ('M-ROUTE-POWER', 30), 'DATA': ('M-ROUTE-DATA', 4), 'COLD': ('M-ROUTE-COLD', 5), 'HOT': ('M-ROUTE-HOT', 1)}
BATHS = ('master_bath', 'secondary_bath', 'guest_bath')
UPPER_ROOMS = {'couple_bedroom', 'mother_bedroom', 'guest_bedroom', 'study', 'hallway', 'vestibule'} | set(BATHS)
SHOWERS = {'secondary_bath': box(10558, 5665, 11400, 6450), 'master_bath': box(15206, 4775, 16200, 6297),
           'guest_bath': box(8034, 9884, 9677, 10700)}       # tray / glass enclosures from model


ZONE_PENDING = {'S42': '距客卫淋浴区 594mm; 防溅型不替代 GB 55024 分区与保护, 电气确认前不作可施工位置'}


def drop_method(room, src, t):
    if t in ('AP', 'FAN'): return 'CEILING: 吊顶内安装, 无竖向下引'
    if t in ('FLOOR_BOX', 'DATA_FLOOR'): return 'TBD: 地面垫层/地插, 需现场确认垫层厚度'
    if t == 'water' and room in BATHS: return 'TBD: 卫浴墙面不开槽 -> 假墙/包管/台盆柜内; SITE_VERIFY_REQUIRED'
    if src and src not in ('-', 'owner TBD'): return 'PROPOSED: 沿家具/柜体背板下引, 不开槽'
    return 'TBD: 轻质隔墙空腔 / 明装线槽, 不开槽; SITE_VERIFY_REQUIRED'


def points():
    out = []
    for i, room, fx, kind, x, y, H, src in M.WATER:
        out.append(dict(id=i, sheet='A303', system=kind, type=f'WATER_{kind}', room=room, label=fx, x=x, y=y, H=H,
                        source=src, status=M.WATER_STATUS.get(i, 'PROPOSED'), drop=drop_method(room, src, 'water')))
    for i, room, t, x, y, H, src, note in M.POWER:
        q = dict(id=i, sheet='A302', system='DATA' if t in ('DATA', 'DATA_FLOOR', 'AP') else 'POWER', type=t,
                 room=room, label=note, x=x, y=y, H=H, source=src,
                 status='OPTIONAL_TBD' if 'OPTIONAL' in note else 'PROPOSED', drop=drop_method(room, src, t))
        if i in ZONE_PENDING:
            q['electrical_zone'] = 'ELECTRICAL_ZONE_PENDING'; q['zone_note'] = ZONE_PENDING[i]
        if t == 'EMERGENCY_CALL':
            q['system_note'] = '仅点位; 接收端/供电/失电处置未定, 不构成有效紧急呼叫系统'
        out.append(q)
    return out


def offset(pts, d):
    """Translate the whole polyline by (d, d). A uniform translation per system keeps every
    spine junction of the base network intact (per-segment x/y shifts broke corners: PR #15 P0)."""
    q = [(x + d, y + d) for x, y in pts]
    return list(zip(q[:-1], q[1:]))


def source_stub(start, d):
    """Orthogonal stub from the real source location to the translated network start."""
    if d == 0: return []
    (x, y) = start
    return [((x, y), (x + d, y)), ((x + d, y), (x + d, y + d))]


def attach(p, system):
    names = M.ROOM_SPINES.get(p['room']) or (M.UPPER_SPINES if p['room'] in UPPER_ROOMS else ['LOWER_N', 'LOWER_S'])
    best = None
    for n in names:
        for (a, b2) in offset(M.SPINES[n], M.SYSTEMS[system]):
            seg = LineString([a, b2])
            q = seg.interpolate(seg.project(Point(p['x'], p['y'])))
            d = q.distance(Point(p['x'], p['y']))
            if best is None or d < best[0]: best = (d, n, (q.x, q.y), abs(a[1] - b2[1]) < 1)
    _, n, (ax, ay), horiz = best
    path = [(ax, ay), (ax, p['y']), (p['x'], p['y'])] if horiz else [(ax, ay), (p['x'], ay), (p['x'], p['y'])]
    return n, [s for s in zip(path[:-1], path[1:]) if math.dist(*s) > 1]


def route_all(pts):
    used = {s: set() for s in SYSL}
    branches = []
    for p in pts:
        n, segs = attach(p, p['system'])
        used[p['system']] |= {n, *M.DEPENDS.get(n, [])}
        p['spine'] = n
        p['branch_mm'] = round(sum(math.dist(*s) for s in segs))
        branches += [{'system': p['system'], 'kind': 'BRANCH', 'to': p['id'], 'seg': s} for s in segs]
    trunks = []
    for s, ns in used.items():
        if not ns: continue
        for n in ns:
            trunks += [{'system': s, 'kind': 'SPINE', 'name': n, 'seg': g} for g in offset(M.SPINES[n], M.SYSTEMS[s])]
        link, d = M.SOURCE_LINKS[s], M.SYSTEMS[s]
        trunks = [{'system': s, 'kind': 'SOURCE', 'name': s, 'seg': g}
                  for g in source_stub(link[0], d) + offset(link, d)] + trunks
    return trunks + branches


def analyse(routes, b):
    water = [LineString(r['seg']) for r in routes if r['system'] in ('COLD', 'HOT')]
    elec = [LineString(r['seg']) for r in routes if r['system'] in ('POWER', 'DATA')]
    cross = []
    for w in water:
        for e in elec:
            i = w.intersection(e)
            for g in ([i] if i.geom_type == 'Point' else getattr(i, 'geoms', [])):
                if g.geom_type == 'Point' and all(math.dist((g.x, g.y), c) > 150 for c in cross):
                    cross.append((round(g.x), round(g.y)))
    step = LineString(OWNER['step_path'])
    steps = []
    for r in routes:
        i = LineString(r['seg']).intersection(step)
        if i.geom_type == 'Point' and all(math.dist((i.x, i.y), c) > 150 for c in steps):
            steps.append((round(i.x), round(i.y)))
    nod = unary_union(nodrop_zones({k: z['geom'] for k, z in b.zones.items()})).buffer(-10)
    in_nodrop = [r for r in routes if LineString(r['seg']).intersection(nod).length > 1]
    return cross, steps, in_nodrop, wall_crossings(routes)


def wall_polys():
    """A103 wall polygons by layer: A-STRUCT-UNDERLAY = developer structural evidence."""
    import ezdxf
    from shapely.geometry import Polygon
    from cd_common import A103
    out = {}
    for e in ezdxf.readfile(A103).modelspace().query('LWPOLYLINE'):
        pts = list(e.get_points('xy'))
        if len(pts) >= 3:
            g = Polygon(pts).buffer(0)
            if g.area > 1000: out.setdefault(e.dxf.layer, []).append(g)
    return {k: unary_union(v) for k, v in out.items()}


WALL_CLASS = [('A-STRUCT-UNDERLAY', 'STRUCTURAL_CANDIDATE'), ('A-DESIGN', 'NEW_PARTITION_DESIGN'),
              ('A-WALL', 'EXISTING_PROPERTY_UNKNOWN'), ('A-REVIEW', 'EXISTING_PROPERTY_UNKNOWN'),
              ('A-CONFLICT', 'EXISTING_PROPERTY_UNKNOWN')]


def wall_crossings(routes):
    """Raw route x wall intersections, then de-duplicated into penetration locations
    (all systems through the same wall within 400 mm = one location) and classified."""
    W = wall_polys()
    allw = unary_union([W[k] for k, _ in WALL_CLASS if k in W])
    raw, locs = 0, []
    for r in routes:
        i = LineString(r['seg']).intersection(allw)
        for g in ([i] if i.geom_type == 'LineString' else getattr(i, 'geoms', [])):
            if g.geom_type != 'LineString' or g.length < 50: continue
            raw += 1
            c = g.centroid
            cls = next((v for k, v in WALL_CLASS if k in W and W[k].buffer(5).intersects(g)), 'EXISTING_PROPERTY_UNKNOWN')
            hit = next((L for L in locs if math.dist(L['at'], (c.x, c.y)) < 400), None)
            if hit:
                hit['systems'] = sorted(set(hit['systems']) | {r['system']})
                order = [v for _, v in WALL_CLASS]
                if order.index(cls) < order.index(hit['class']): hit['class'] = cls
            else:
                locs.append({'id': f'X{len(locs)+1:02d}', 'at': (round(c.x), round(c.y)), 'class': cls,
                             'systems': [r['system']], 'wall_mm': round(g.length)})
    for L in locs:
        L['status'] = 'HOLD: STRUCTURAL_SITE_VERIFY_REQUIRED' if L['class'] != 'NEW_PARTITION_DESIGN' \
            else 'PROPOSED: 新建轻质隔墙预留套管, 现场确认'
    return {'raw_intersections': raw, 'locations': locs}


# ---------------- drawing ----------------
def sym(msp, p, lay):
    x, y, t = p['x'], p['y'], p['type']
    L = {'layer': lay}
    if t.startswith('WATER_'):
        msp.add_circle((x, y), 70, dxfattribs=L)
        if t == 'WATER_HOT': msp.add_line((x - 70, y - 70), (x + 70, y + 70), dxfattribs=L); msp.add_line((x - 70, y + 70), (x + 70, y - 70), dxfattribs=L)
    elif t in ('SOCKET', 'SOCKET_WET', 'SOCKET_16A_AC'):
        msp.add_circle((x, y), 80, dxfattribs=L); msp.add_line((x - 110, y), (x + 110, y), dxfattribs=L)
        if t == 'SOCKET_WET': msp.add_lwpolyline([(x - 120, y - 120), (x + 120, y - 120), (x + 120, y + 120), (x - 120, y + 120)], close=True, dxfattribs=L)
        if t == 'SOCKET_16A_AC': msp.add_line((x, y), (x, y + 110), dxfattribs=L)
    elif t == 'APPLIANCE':
        msp.add_lwpolyline([(x - 100, y - 80), (x + 100, y - 80), (x, y + 100)], close=True, dxfattribs=L)
    elif t in ('FLOOR_BOX', 'DATA', 'DATA_FLOOR'):
        msp.add_lwpolyline([(x - 90, y - 90), (x + 90, y - 90), (x + 90, y + 90), (x - 90, y + 90)], close=True, dxfattribs=L)
        msp.add_line((x, y - 90), (x, y + 90), dxfattribs=L)
        if t != 'DATA': msp.add_line((x - 90, y - 90), (x + 90, y + 90), dxfattribs=L)
    elif t == 'AP':
        msp.add_circle((x, y), 130, dxfattribs=L); msp.add_circle((x, y), 60, dxfattribs=L)
    elif t == 'FAN':
        msp.add_circle((x, y), 150, dxfattribs=L)
        msp.add_line((x - 100, y - 100), (x + 100, y + 100), dxfattribs=L); msp.add_line((x - 100, y + 100), (x + 100, y - 100), dxfattribs=L)
    elif t == 'EMERGENCY_CALL':
        msp.add_lwpolyline([(x, y - 110), (x + 110, y), (x, y + 110), (x - 110, y)], close=True, dxfattribs=L)
    elif t == 'SWITCH':
        msp.add_circle((x, y), 60, dxfattribs=L); msp.add_line((x, y), (x + 120, y + 120), dxfattribs=L)
    elif t == 'SENSOR':
        msp.add_circle((x, y), 100, dxfattribs=L); msp.add_line((x - 60, y), (x + 60, y), dxfattribs=L)


class Tags:
    """Place short labels at the first free offset around a symbol."""
    def __init__(self, msp):
        from ezdxf import bbox as bb
        self.msp, self.occ = msp, []
        for e in msp.query('TEXT'):
            x = bb.extents([e])
            if x.has_data: self.occ.append(box(x.extmin.x, x.extmin.y, x.extmax.x, x.extmax.y))
        self.missed = []

    def put(self, s, x, y, lay, h=H_TINY * 0.85):
        w = len(s) * h * 1.0 + 40          # generous: ezdxf text extents are wider than glyph count suggests
        offs = [(140, 120), (140, -230), (-140 - w, 120), (-140 - w, -230), (-w / 2, 230), (-w / 2, -340)]
        offs += [(dx * 2, dy * 2) for dx, dy in offs[:4]]
        for dx, dy in offs:
            r = box(x + dx, y + dy, x + dx + w, y + dy + h)
            if not any(r.intersects(o) for o in self.occ):
                text(self.msp, x + dx, y + dy, s, h, lay, 'LEFT'); self.occ.append(r); return True
        self.missed.append(s); return False


def sources(msp):
    for s in M.SOURCES:
        x, y = s['x'], s['y']
        msp.add_lwpolyline([(x - 200, y - 130), (x + 200, y - 130), (x + 200, y + 130), (x - 200, y + 130)], close=True,
                           dxfattribs={'layer': 'M-SOURCE-TBD'})
        msp.add_line((x - 200, y - 130), (x + 200, y + 130), dxfattribs={'layer': 'M-SOURCE-TBD'})


def room_names(msp, b):
    for k, z in b.zones.items():
        if k == 'stair': continue
        x, y = label_point(z['geom'])
        text(msp, x, y, NAMES.get(k, k), H_SMALL, 'A-ROOM-NAME')


# ---------------- assembly ----------------
LEVEL_LINE = LineString([(8000, -1000), (8000, 10900), (13100, 10900)])   # 2650 / 3100 ceiling step
PT_LAYER = {'WATER_COLD': 'P-COLD', 'WATER_HOT': 'P-HOT', 'DATA': 'E-DATA', 'DATA_FLOOR': 'E-DATA', 'AP': 'E-DATA',
            'EMERGENCY_CALL': 'E-ALARM', 'SWITCH': 'E-SWITCH', 'SENSOR': 'E-SENSOR'}
DROP_LAYER = {'CEILING': 'M-DROP-CEIL', 'PROPOSED': 'M-DROP-FURN', 'TBD: 卫浴': 'M-DROP-BATH', 'TBD: 地面': 'M-DROP-FLOOR'}
LAYERS = [('A-NOTE', 7, 18), ('A-ROOM-NAME', 8, 13), ('M-TAG', 6, 13), ('M-SOURCE-TBD', 6, 35),
          ('M-ROUTE-POWER', 30, 35, 'Continuous'), ('M-ROUTE-DATA', 4, 25, 'DASHED'), ('M-ROUTE-COLD', 5, 35, 'Continuous'),
          ('M-ROUTE-HOT', 1, 35, 'DASHED'), ('M-CROSS', 6, 25), ('M-PENETRATION-HOLD', 1, 35), ('M-PENETRATION', 3, 25), ('M-LEVEL', 6, 35), ('M-DROP-CEIL', 8, 18),
          ('M-DROP-FURN', 3, 18), ('M-DROP-TBD', 6, 18), ('M-DROP-BATH', 1, 18), ('M-DROP-FLOOR', 4, 18),
          ('E-POWER', 30, 25), ('E-DATA', 4, 25), ('E-SWITCH', 2, 25), ('E-SENSOR', 6, 25), ('E-ALARM', 1, 35),
          ('E-LITE-REF', 8, 13), ('P-COLD', 5, 30), ('P-HOT', 1, 30), ('P-SHOWER-REF', 8, 13)]


def drop_layer(d):
    for k, v in DROP_LAYER.items():
        if d.startswith(k): return v
    return 'M-DROP-TBD'


def controls():
    sw = [dict(id=i, sheet='A302', system='CONTROL', type='SWITCH', room=r, label=n, x=x, y=y, H=H, serves=s,
               status=st, source='lighting_points_v2 control_group', drop='PROPOSED: 墙面开关盒; 连线 SCHEMATIC/TBD',
               physical_circuit_id=None) for i, r, x, y, H, s, n, st in M.SWITCHES]
    sn = [dict(id=f"SN-{p['id']}", sheet='A302', system='CONTROL', type='SENSOR', room=p['room'],
               label='感应器(灯具一体或独立) PROPOSED', x=p['x'], y=p['y'] + 230, H=p['z_abs'], serves=[p['control_group']],
               status='PROPOSED', source=p['id'], drop='PROPOSED: 随夜灯', physical_circuit_id=None)
          for p in V2 if p['layer'] == 'night']
    return sw + sn


def new_doc(b, title):
    doc = b.new_sheet()
    for t in LAYERS: layer(doc, t[0], t[1], t[2], t[3] if len(t) > 3 else 'Continuous')
    room_names(doc.modelspace(), b)
    sources(doc.modelspace())
    text(doc.modelspace(), 8250, -1500, title, 300, 'A-NOTE')
    return doc


WALLX = {'locations': [], 'raw': 0, 'n': 0}


def a301(b, pts, routes, cross, levels):
    doc = new_doc(b, 'A301 吊顶内管线路由示意  1:50  CD_V01  SCHEMATIC / SITE_VERIFY_REQUIRED')
    msp = doc.modelspace()
    for r in routes:
        msp.add_line(*r['seg'], dxfattribs={'layer': SYSL[r['system']][0]})
    for p in pts:
        msp.add_circle((p['x'], p['y']), 60, dxfattribs={'layer': drop_layer(p['drop'])})
    for x, y in cross: msp.add_circle((x, y), 120, dxfattribs={'layer': 'M-CROSS'})
    for L in WALLX['locations']:
        x, y = L['at']
        msp.add_lwpolyline([(x, y - 140), (x + 140, y), (x, y + 140), (x - 140, y)], close=True,
                           dxfattribs={'layer': 'M-PENETRATION-HOLD' if L['status'].startswith('HOLD') else 'M-PENETRATION'})
    for x, y in levels:
        msp.add_lwpolyline([(x - 160, y - 160), (x + 160, y - 160), (x + 160, y + 160), (x - 160, y + 160)], close=True,
                           dxfattribs={'layer': 'M-LEVEL'})
    lx, ly = 17400, 13600
    yy = notes(msp, lx, ly, 'A301 吊顶内管线路由示意 (CD_V01, 示意, 非施工定案)', [
        '1. 强电/弱电/冷水/热水均走吊顶内, 不在墙面开槽; 线位为示意, 未定管径与根数',
        f'2. 吊顶下返 {OWNER["drop"]}: 吊顶内净空、龙骨、梁位未实测 -> SITE_VERIFY_REQUIRED, 不代表管线可全部装下',
        '3. 配电箱/弱电箱/给水入户/热水器位置未知, 图中品红框为 TBD 占位',
        '4. 水管在下、电线在上; 品红圆圈 = 水电交叉点, 需保持间距或套管 (由施工方定)',
        '5. 品红方框 = 穿越 2650/3100 吊顶高差 (x=8000 电视墙) 处, 需开孔或绕行, 结构许可待定',
        '6. 楼梯区与 x<8000 上区地面为原顶无吊顶, 管线不经过',
        '7. 竖向下引: 绿=沿家具/柜体背板; 红=卫浴假墙/包管 TBD; 青=地面垫层 TBD; 灰=吊顶内设备; 品红=隔墙空腔/明装线槽 TBD',
        '8. 排水: 业主自行处理, OUT_OF_SCOPE, 本图不表达',
        '9. 物理回路、开关接线、灯带驱动均为 TBD; 详见 A302',
        '10. 照明线路未建模: A201 V2 的 103 个灯具、20 个开关、5 个感应器的接线不在本图, 本图不代表全部线路',
        f'11. 穿墙: {WALLX["raw"]} 次线段-墙体相交, 去重后 {WALLX["n"]} 处位置; 不是开孔数. 红菱形 = 墙体属性未知/结构候选, 一律 HOLD',
        '    (STRUCTURAL_SITE_VERIFY_REQUIRED); 未经结构确认不得打孔. 绿菱形 = 新建轻质隔墙, 预留套管',
        f'12. {len(cross)} 处水电交叉仅为平面交点: 无 Z 向排布/管径/桥架/龙骨梁位实测, 是待协调点, 不证明可安装',
        '13. 管线长度和交叉数量基于假设的源头位置, 不能作为材料量'])
    for i, (lay, s) in enumerate((('M-ROUTE-POWER', '强电 (实线)'), ('M-ROUTE-DATA', '弱电/网络 (虚线)'),
                                  ('M-ROUTE-COLD', '冷水 (实线)'), ('M-ROUTE-HOT', '热水 (虚线)'))):
        y = yy - 300 - i * 380
        msp.add_line((lx, y), (lx + 700, y), dxfattribs={'layer': lay})
        text(msp, lx + 900, y, s, H_SMALL, 'A-NOTE', 'MIDDLE_LEFT')
    return doc


def a302(b, pts, ctl):
    doc = new_doc(b, 'A302 电气·照明控制·网络点位示意  1:50  CD_V01  PROPOSED / TBD')
    msp = doc.modelspace()
    for p in V2:
        msp.add_circle((p['x'], p['y']), 70, dxfattribs={'layer': 'E-LITE-REF'})
    items = [p for p in pts if p['sheet'] == 'A302'] + ctl
    for p in items: sym(msp, p, PT_LAYER.get(p['type'], 'E-POWER'))
    lx, ly = 17400, 13600
    yy = notes(msp, lx, ly, 'A302 电气·照明控制·网络点位 (CD_V01, 示意)', [
        '1. 点位按模型家具定位; 高度 H 为距本层完成地面 (上区 +450 起算); 全部 PROPOSED, 非施工定案',
        '2. 卫浴/厨房水槽/阳台插座为防溅型; 淋浴区内不设插座; 浴室分区由电气按 GB 55024 判定',
        '3. 开关只表示逻辑场景组 (control_group), 物理回路/双控接线/灯带驱动 TBD',
        '4. 夜灯: 感应控制 + 床头手动兜底, 可调低亮度 (PROPOSED); 床头灯: 壁装可调式 (PROPOSED)',
        '5. 母亲卧室床头、主卫厕位旁设紧急呼叫 (PROPOSED)',
        '6. 灶具/空调等大功率回路、配电箱容量 TBD; 配电箱/弱电箱位置 TBD',
        '7. 次主卫(H2)、客卧(H4)门位待定, 相关开关 TBD; 灰色小圆 = A201 V2 灯位参照',
        '8. S42 (客卫, 距淋浴 594mm) ELECTRICAL_ZONE_PENDING: 防溅型不替代分区与保护, 电气确认前不作可施工位置',
        '9. E01/E02 紧急呼叫仅为点位: 接收端、供电与失电处置未定, 不构成有效紧急呼叫系统'])
    rows = [f"{s['id']} {NAMES.get(s['room'], s['room'])}: {', '.join(g.split(':')[1] for g in s['serves'])}"
            for s in ctl if s['type'] == 'SWITCH']
    notes(msp, lx, yy - 300, '开关 -> 场景组', rows)
    tg = Tags(msp)
    for p in items:
        if p['type'] != 'SENSOR': tg.put(p['id'], p['x'], p['y'], 'M-TAG')
    return doc, tg.missed


def a303(b, pts):
    doc = new_doc(b, 'A303 给水点位示意 (冷热水)  1:50  CD_V01  PROPOSED / TBD')
    msp = doc.modelspace()
    for g in SHOWERS.values():
        msp.add_lwpolyline(list(g.exterior.coords)[:-1], close=True, dxfattribs={'layer': 'P-SHOWER-REF'})
    items = [p for p in pts if p['sheet'] == 'A303']
    for p in items: sym(msp, p, PT_LAYER[p['type']])
    lx, ly = 17400, 13600
    notes(msp, lx, ly, 'A303 给水点位 (CD_V01, 示意)', [
        '1. 只表达冷热水用水点; 排水由业主自行处理 -> OUT_OF_SCOPE / SITE_VERIFY_REQUIRED',
        '2. 点位按模型洁具定位; H 为出水口距本层完成地面; 全部 PROPOSED',
        '3. 给水入户、水表、总阀、热水器位置 TBD; 热水器假定在生活阳台',
        '4. 管材、管径、热水循环、减压与防结露由施工方深化',
        '5. 卫浴墙面不开槽: 出水点下引方式 TBD (假墙/包管/台盆柜内)',
        '6. ○ 冷水   ⊗ 热水   灰框 = 淋浴区 (模型托盘/玻璃)'])
    tg = Tags(msp)
    for p in items: tg.put(p['id'], p['x'], p['y'], 'M-TAG')
    return doc, tg.missed


def qa(b, pts, ctl, routes, cross, levels, in_nodrop, walls, missed):
    """walls: wall_crossings() result."""
    res = []
    for p in pts + ctl:
        z = b.zones.get(p['room'])
        if z is None or not z['geom'].buffer(350).contains(Point(p['x'], p['y'])):
            res.append(('FAIL', p['id'], 'OUT_OF_ROOM', p['room']))
        if p['status'] not in ('PROPOSED', 'TBD', 'OPTIONAL_TBD'):
            res.append(('FAIL', p['id'], 'STATUS_NOT_SCHEMATIC', p['status']))
        if p.get('physical_circuit_id') is not None:
            res.append(('FAIL', p['id'], 'PHYSICAL_CIRCUIT_CLAIMED', ''))
        if p['type'].startswith('SOCKET') or p['type'] in ('APPLIANCE', 'FLOOR_BOX'):
            for r, g in SHOWERS.items():
                if r != p['room']: continue          # walls separate other rooms' showers
                d = g.distance(Point(p['x'], p['y']))
                if d == 0: res.append(('FAIL', p['id'], 'SOCKET_IN_SHOWER', r))
                elif d < 600: res.append(('FLAG', p['id'], 'SOCKET_NEAR_SHOWER', f'{r} {round(d)}mm; 防溅型, 分区由电气判定'))
    groups = {p['control_group'] for p in V2}
    served = {g for s in ctl for g in s['serves']}
    for g in sorted(groups - served): res.append(('FAIL', g, 'CONTROL_GROUP_UNSERVED', ''))
    for g in sorted(served - groups): res.append(('FAIL', g, 'SWITCH_SERVES_UNKNOWN_GROUP', ''))
    for g in M.SENSOR_GROUPS:
        if not any(g in s['serves'] for s in ctl if s['type'] == 'SENSOR'): res.append(('FAIL', g, 'NIGHT_NO_SENSOR', ''))
        if not any(g in s['serves'] for s in ctl if s['type'] == 'SWITCH'): res.append(('FAIL', g, 'NIGHT_NO_MANUAL_FALLBACK', ''))
    for r in in_nodrop: res.append(('FAIL', r.get('to') or r.get('name'), 'ROUTE_IN_NO_DROP_ZONE', r['system']))
    for m in missed: res.append(('FLAG', m, 'TAG_NOT_PLACED', 'see mep_points.csv'))
    from mep_topology import report as topo_report
    topo = topo_report(routes, [p for p in pts if p['system'] in SYSL])
    for t in topo['systems']:
        if not t['source_found']: res.append(('FAIL', t['system'], 'NO_SOURCE_SEGMENT', ''))
        for u in t['unreachable_terminals']: res.append(('FAIL', u, 'TERMINAL_NOT_CONNECTED', t['system']))
    for p in pts:
        if p.get('electrical_zone') == 'ELECTRICAL_ZONE_PENDING':
            res.append(('FLAG', p['id'], 'ELECTRICAL_ZONE_PENDING', p.get('zone_note', '')))
    fails = [r for r in res if r[0] == 'FAIL']
    length = {s: round(sum(math.dist(*r['seg']) for r in routes if r['system'] == s) / 1000, 1) for s in SYSL}
    return {'result': 'PASS' if not fails else 'FAIL', 'level': 'SCHEMATIC',
            'issues': [dict(zip(('severity', 'id', 'code', 'detail'), r)) for r in res],
            'counts': {'water_points': sum(p['sheet'] == 'A303' for p in pts), 'power_data_points': sum(p['sheet'] == 'A302' for p in pts),
                       'switches': sum(c['type'] == 'SWITCH' for c in ctl), 'sensors': sum(c['type'] == 'SENSOR' for c in ctl),
                       'control_groups': len(groups)},
            'route_length_m_schematic': length, 'water_power_crossings': len(cross), 'level_change_crossings': levels,
            'topology': topo,
            'wall_crossings': {'raw_intersections': walls['raw_intersections'],
                               'locations': len(walls['locations']),
                               'by_class': dict(__import__('collections').Counter(L['class'] for L in walls['locations'])),
                               'note': 'raw = 线段与墙体相交次数, 不是开孔数; 位置已按 400mm 去重; 非新建隔墙一律 HOLD'},
            'crossings_note': '水电交叉为二维平面交点, 无 Z 向排布/管径/桥架/龙骨梁位实测, 仅为待协调点; 150 下返不代表四套管线可容纳',
            'lighting_wiring': 'NOT_MODELLED: A201 V2 的 103 个灯具、20 个开关、5 个感应器的接线未纳入 A301 路由',
            'site_verify': ['配电箱/弱电箱/给水入户/热水器位置', '吊顶内净空/龙骨/梁位', '物理回路与开关接线',
                            '竖向下引方式 (不开槽)', 'H2-H4 门位', '浴室电气分区', '地插垫层厚度'],
            'out_of_scope': ['排水 (业主自行处理)'],
            'scope': 'Schematic data QA only; no load, cable size, pipe size or ceiling-void fit verified'}


def main():
    b = Base()
    pts = points()
    ctl = controls()
    routes = route_all(pts)
    cross, _, in_nodrop, walls = analyse(routes, b)
    WALLX.update(locations=walls['locations'], raw=walls['raw_intersections'], n=len(walls['locations']))
    levels = []
    for r in routes:
        i = LineString(r['seg']).intersection(LEVEL_LINE)
        if i.geom_type == 'Point' and all(math.dist((i.x, i.y), c) > 400 for c in levels):
            levels.append((round(i.x), round(i.y)))
    WORK.mkdir(exist_ok=True)
    out = {}
    d1 = a301(b, pts, routes, cross, levels); out['A301'] = WORK / 'A301_吊顶管线路由示意.dxf'; d1.saveas(out['A301'])
    d2, m2 = a302(b, pts, ctl); out['A302'] = WORK / 'A302_电气照明控制网络点位.dxf'; d2.saveas(out['A302'])
    d3, m3 = a303(b, pts); out['A303'] = WORK / 'A303_给水点位.dxf'; d3.saveas(out['A303'])
    allp = pts + ctl
    (DATA / 'mep_points.json').write_text(json.dumps({'status': 'SCHEMATIC / PROPOSED / TBD', 'sources': M.SOURCES,
        'points': allp}, ensure_ascii=False, indent=1))
    keys = ['id', 'sheet', 'system', 'type', 'room', 'label', 'x', 'y', 'H', 'status', 'source', 'drop', 'spine', 'branch_mm', 'serves']
    with open(DATA / 'mep_points.csv', 'w', newline='', encoding='utf-8-sig') as f:
        w = csv.DictWriter(f, fieldnames=keys, extrasaction='ignore', lineterminator='\n'); w.writeheader()
        for p in allp: w.writerow({**p, 'serves': ';'.join(p.get('serves', []))})
    (DATA / 'mep_routes.json').write_text(json.dumps({'level': 'SCHEMATIC', 'segments': [
        {**{k: v for k, v in r.items() if k != 'seg'}, 'seg': [list(map(round, r['seg'][0])), list(map(round, r['seg'][1]))]}
        for r in routes], 'water_power_crossings': cross, 'level_change_crossings': levels,
        'wall_crossings': walls}, ensure_ascii=False))
    q = qa(b, pts, ctl, routes, cross, levels, in_nodrop, walls, m2 + m3)
    (HERE / 'qa').mkdir(exist_ok=True)
    (HERE / 'qa' / 'mep_qa.json').write_text(json.dumps(q, ensure_ascii=False, indent=1))
    print(json.dumps({k: q[k] for k in ('result', 'counts', 'route_length_m_schematic', 'water_power_crossings',
                                        'level_change_crossings', 'wall_crossings')}, ensure_ascii=False))
    for t in q['topology']['systems']:
        print(f"  topology {t['system']}: segs {t['segments_reachable']}/{t['segments_total']} "
              f"terminals {t['terminals_reachable']}/{t['terminals_total']}")
    for i in q['issues']: print(' ', i)
    return out


if __name__ == '__main__':
    main()
