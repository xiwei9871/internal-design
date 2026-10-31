#!/usr/bin/env python3
"""A201 天花布置图 CD_V01 -> work/A201_天花布置图.dxf + data/lighting_points.{json,csv}.
Ceiling zones follow the OWNER scheme (P0.3.2: step x=8000 from y=4700 to 10900, east along
y=10900 to x=13100), not the model's ceiling outline. Model ceilings are only compared (DIFF)."""
import csv, json
from shapely.geometry import LineString, Point, box
from shapely.ops import unary_union, polylabel

from cd_common import (Base, NAMES, WET, BATHS, OWNER, WORK, DATA, H_TXT, H_SMALL, H_TINY,
                       layer, text, outline, hatch, label_point, notes, polys, union_tris, high_region)

DROP = OWNER['drop']
CCT = {'kitchen': 4000, 'master_bath': 4000, 'secondary_bath': 4000, 'guest_bath': 4000,
       'service_balcony': 4000, 'study': 4000, 'north_sunroom': 3500}      # others 3000
SPACING = {'kitchen': 1200, 'study': 1200}                                  # others 1400


def ceiling_zones(b):
    """Return per-floor-zone ceiling record: soffit, finished, clear height, drop status."""
    hi = high_region()
    step = LineString(OWNER['step_path'])
    out = {}
    for key, z in b.zones.items():
        for part_i, p in enumerate(polys(z['geom'])):
            for side, g in (('HIGH', p.intersection(hi)), ('LOW', p.difference(hi))):
                for q in polys(g.buffer(0)):
                    if q.area < 0.05e6: continue
                    soffit = OWNER['soffit_high'] if side == 'HIGH' else OWNER['soffit_low']
                    floor = z['level']
                    if key == 'stair' or (side == 'LOW' and floor == OWNER['floor_high']):
                        fin, status = soffit, 'NO_DROP_ORIGINAL_SOFFIT; clear height SITE_VERIFY_REQUIRED'
                    else:
                        fin, status = soffit - DROP, 'DROP_150; void capacity SITE_VERIFY_REQUIRED'
                    clear = None if floor is None else fin - floor
                    out[f'{key}#{side}{part_i}'] = {'zone': key, 'side': side, 'geom': q, 'soffit': soffit,
                                                    'finished': fin, 'floor': floor, 'clear': clear,
                                                    'material': '铝扣板' if key in WET else '石膏板',
                                                    'status': status}
    return out, step


def grid_points(p, s):
    inner = p.buffer(-450)
    if inner.is_empty:
        c = polylabel(p, tolerance=20); return [(c.x, c.y)]
    x0, y0, x1, y1 = inner.bounds
    nx, ny = max(1, round((x1 - x0) / s) + 1), max(1, round((y1 - y0) / s) + 1)
    pts = [(x0 + (x1 - x0) * (i + 0.5) / nx if nx == 1 else x0 + (x1 - x0) * i / (nx - 1),
            y0 + (y1 - y0) * (j + 0.5) / ny if ny == 1 else y0 + (y1 - y0) * j / (ny - 1))
           for i in range(nx) for j in range(ny)]
    pts = [q for q in pts if p.buffer(-400).contains(Point(q))]
    if not pts:
        c = polylabel(p, tolerance=20); pts = [(c.x, c.y)]
    return pts


def lighting(b, cz, step, panels):
    pts, skipped = [], []
    beds = [box(*o['b'][:4]).buffer(150) for o in b.find_objects(r'mattress')]

    def add(room, lay, typ, x, y, z, mount, cct, beam=None, lumen=None, src='layout', note='', **kw):
        pts.append({'id': f'L{len(pts)+1:03d}', 'room': room, 'room_name': NAMES.get(room, room),
                    'layer': lay, 'type': typ, 'x': round(x), 'y': round(y), 'z_abs': round(z), 'mount': mount,
                    'cct_k': cct, 'beam_deg': beam, 'lumen': lumen, 'circuit': f'C-{room}-{lay}',
                    'switch_id': f'SW-{room}', 'source': src, 'status': 'OWNER_REVIEW', 'note': note, **kw})
    for k, c in cz.items():
        room, p = c['zone'], c['geom']
        if room == 'stair': continue
        cct = CCT.get(room, 3000)
        if c['finished'] == c['soffit']:            # no drop: surface spot, never recessed
            x, y = label_point(p)
            add(room, 'base', 'SURFACE_SPOT', x, y, c['finished'], 'surface', cct, 36, 500,
                note='原顶无吊顶, 明装; 净高 SITE_VERIFY_REQUIRED')
            continue
        for x, y in grid_points(p, SPACING.get(room, 1400)):
            q = Point(x, y)
            why = None
            if q.distance(step) < 350: why = 'within 350 of ceiling step'
            elif any(q.distance(Point(a)) < 300 for a in panels): why = 'within 300 of access panel'
            elif any(bd.contains(q) for bd in beds): why = 'above bed (glare)'
            if why: skipped.append({'room': room, 'x': round(x), 'y': round(y), 'why': why}); continue
            wet = room in BATHS
            add(room, 'base', 'DOWNLIGHT_IP44' if wet else 'DOWNLIGHT', x, y, c['finished'], 'recessed',
                cct, 60, 600 if wet else 500)
    # task lights from real objects
    for o in b.find_objects(r'^CBM_(guest|master)_MIRROR_LIGHT$'):
        bb = o['b']; room = 'guest_bath' if 'guest' in o['n'] else 'master_bath'
        add(room, 'task', 'MIRROR_LIGHT', (bb[0] + bb[2]) / 2, (bb[1] + bb[3]) / 2, bb[4], 'wall', 4000,
            src=f'model:{o["n"]}')
    for o in b.find_objects(r'^CBM_SECONDARY_MIRROR$'):
        bb = o['b']
        add('secondary_bath', 'task', 'MIRROR_LIGHT', (bb[0] + bb[2]) / 2, bb[1] - 20, bb[5] + 60, 'wall', 4000,
            src=f'proposed above model:{o["n"]}', note='模型无镜前灯, 按镜子位置补')
    for o in b.find_objects(r'^V4_Dining_enamel_dome$'):
        bb = o['b']
        add('living', 'task', 'PENDANT', (bb[0] + bb[2]) / 2, (bb[1] + bb[3]) / 2, OWNER['soffit_low'] - DROP,
            'pendant', 3000, src=f'model:{o["n"]}', note=f'灯体底 z={bb[4]}')
    for o in b.find_objects(r'^STUDY_V1_MOVABLE_DESK$'):
        bb = o['b']
        add('study', 'task', 'DOWNLIGHT', (bb[0] + bb[2]) / 2, (bb[1] + bb[3]) / 2,
            OWNER['soffit_high'] - DROP, 'recessed', 4000, 36, 600, src=f'over model:{o["n"]}')
    for o in b.find_objects(r'^B11_K-RUN-E_COUNTER$'):
        bb = o['b']
        for y in (1100, 2000, 2900):
            add('kitchen', 'task', 'DOWNLIGHT', bb[0] + 250, y, OWNER['soffit_low'] - DROP, 'recessed', 4000, 36, 500,
                src=f'over model:{o["n"]}')
    # accent: step-line cove + stair riser lights
    for a, c2 in zip(OWNER['step_path'][:-1], OWNER['step_path'][1:]):
        seg = LineString([a, c2]).intersection(b.interior)
        for s in polys(seg.buffer(1)):
            mid = s.centroid
            add('hallway' if a[0] == c2[0] else 'north_sunroom', 'accent', 'LED_STRIP_COVE', mid.x, mid.y,
                OWNER['soffit_high'] - DROP, 'cove', 3000, note='跌级立板内暗藏灯带',
                path=[[round(v) for v in s.bounds[:2]], [round(v) for v in s.bounds[2:]]])
    for k, lvl in b.step_levels.items():
        g = union_tris(b.ext['stair'][k]['tris'])
        nxt = {'STEP_0': 'STEP_1', 'STEP_1': 'STEP_2'}.get(k)
        tread = g.difference(union_tris(b.ext['stair'][nxt]['tris'])) if nxt else g
        x, y = label_point(tread.intersection(b.interior))
        add('stair', 'accent', 'STEP_LIGHT', x, y, lvl + 150, 'wall', 3000,
            note='踏步侧墙/踢面低位灯, 防眩; 位置 SITE_VERIFY_REQUIRED')
    return pts, skipped


def access_panels(b):
    """One 450x450 panel per wet room (water valves above ceiling) + corridor junction."""
    out = []
    for key in ('kitchen', 'master_bath', 'secondary_bath', 'guest_bath'):
        z = b.zones.get(key)
        if not z: continue
        p = max(polys(z['geom']), key=lambda q: q.area)
        c = p.buffer(-500).representative_point() if not p.buffer(-500).is_empty else p.representative_point()
        out.append((round(c.x), round(c.y), key))
    out.append((10500, 7200, 'hallway'))
    return out


SYM = {'DOWNLIGHT': 'A-LITE-BASE', 'DOWNLIGHT_IP44': 'A-LITE-BASE', 'SURFACE_SPOT': 'A-LITE-BASE',
       'MIRROR_LIGHT': 'A-LITE-TASK', 'PENDANT': 'A-LITE-TASK', 'LED_STRIP_COVE': 'A-LITE-ACCENT',
       'STEP_LIGHT': 'A-LITE-ACCENT'}


def draw_light(msp, p):
    x, y, t, lay = p['x'], p['y'], p['type'], SYM[p['type']]
    if t in ('DOWNLIGHT', 'DOWNLIGHT_IP44'):
        msp.add_circle((x, y), 90, dxfattribs={'layer': lay})
        msp.add_line((x - 130, y), (x + 130, y), dxfattribs={'layer': lay})
        msp.add_line((x, y - 130), (x, y + 130), dxfattribs={'layer': lay})
        if t == 'DOWNLIGHT_IP44': msp.add_circle((x, y), 130, dxfattribs={'layer': lay})
    elif t == 'SURFACE_SPOT':
        msp.add_lwpolyline([(x - 110, y - 110), (x + 110, y - 110), (x + 110, y + 110), (x - 110, y + 110)],
                           close=True, dxfattribs={'layer': lay})
        msp.add_circle((x, y), 70, dxfattribs={'layer': lay})
    elif t == 'PENDANT':
        msp.add_circle((x, y), 200, dxfattribs={'layer': lay})
        msp.add_line((x - 140, y - 140), (x + 140, y + 140), dxfattribs={'layer': lay})
        msp.add_line((x - 140, y + 140), (x + 140, y - 140), dxfattribs={'layer': lay})
    elif t == 'MIRROR_LIGHT':
        msp.add_lwpolyline([(x - 250, y - 40), (x + 250, y - 40), (x + 250, y + 40), (x - 250, y + 40)],
                           close=True, dxfattribs={'layer': lay})
    elif t == 'STEP_LIGHT':
        msp.add_lwpolyline([(x - 60, y - 60), (x + 60, y - 60), (x, y + 80)], close=True, dxfattribs={'layer': lay})
    elif t == 'LED_STRIP_COVE' and p.get('path'):
        (ax, ay), (bx, by) = p['path']
        off = 60
        if abs(bx - ax) < abs(by - ay):
            msp.add_line((ax + off, ay), (ax + off, by), dxfattribs={'layer': lay})
            msp.add_line((ax + off + 50, ay), (ax + off + 50, by), dxfattribs={'layer': lay})
        else:
            msp.add_line((ax, ay - off), (bx, ay - off), dxfattribs={'layer': lay})
            msp.add_line((ax, ay - off - 50), (bx, ay - off - 50), dxfattribs={'layer': lay})


def draw_section(msp, x0, y0):
    """Schematic section through the split level at y≈6000 (W->E), 1:50 in model units."""
    L = 'A-CEIL-SECT'
    sx = lambda x: x0 + (x - 5000)                # plan x 5000..14000 -> sheet
    sz = lambda z: y0 + z
    F, S = OWNER, None
    # floors
    msp.add_line((sx(5000), sz(0)), (sx(5660), sz(0)), dxfattribs={'layer': L})
    for xs, z in ((5660, 150), (6010, 300), (6360, 450)):
        msp.add_lwpolyline([(sx(xs), sz(z - 150)), (sx(xs), sz(z)), (sx(xs + 350), sz(z))], dxfattribs={'layer': L})
    msp.add_line((sx(6710), sz(450)), (sx(14000), sz(450)), dxfattribs={'layer': L})
    # soffits (original slab underside)
    msp.add_line((sx(5000), sz(F['soffit_low'])), (sx(8000), sz(F['soffit_low'])), dxfattribs={'layer': L})
    msp.add_line((sx(8000), sz(F['soffit_high'])), (sx(14000), sz(F['soffit_high'])), dxfattribs={'layer': L})
    msp.add_line((sx(8000), sz(F['soffit_low'])), (sx(8000), sz(F['soffit_high'])), dxfattribs={'layer': L})
    # finished ceilings
    fl, fh = F['soffit_low'] - DROP, F['soffit_high'] - DROP
    for a, b2, z in ((5000, 5660, fl), (8000, 14000, fh)):
        msp.add_line((sx(a), sz(z)), (sx(b2), sz(z)), dxfattribs={'layer': 'A-CEIL-STEP'})
    text(msp, sx(6700), sz(F['soffit_low'] + 120), '楼梯上方原顶 +2.800, 不吊顶; 上区地面+0.450处净高2350 SITE_VERIFY', H_TINY, L)
    text(msp, sx(5300), sz(fl - 160), f'吊顶 +{fl/1000:.3f}', H_TINY, L, 'LEFT')
    text(msp, sx(10500), sz(fh - 160), f'吊顶 +{fh/1000:.3f} (净高 {fh-450})', H_TINY, L)
    text(msp, sx(10500), sz(F['soffit_high'] + 120), f'原顶 +{F["soffit_high"]/1000:.3f}  吊顶空间 {DROP}', H_TINY, L)
    text(msp, sx(8000) + 120, sz(3020), 'x=8000 跌级 450 立板', H_TINY, L, 'LEFT')
    text(msp, sx(5800), sz(-260), '±0.000', H_TINY, L); text(msp, sx(12000), sz(450 - 260), '+0.450', H_TINY, L)
    for i, (xs, z) in enumerate(((5660, 150), (6010, 300), (6360, 450))):
        text(msp, sx(xs + 175), sz(z + 120), f'+{z/1000:.3f}', H_TINY * 0.8, L)
    text(msp, sx(9500), sz(-650), '剖面示意 1-1 (y≈6000, 西→东), 1:50', H_SMALL, L)


def main():
    b = Base()
    cz, step = ceiling_zones(b)
    panels_full = access_panels(b)
    panels = [(x, y) for x, y, _ in panels_full]
    pts, skipped = lighting(b, cz, step, panels)
    doc = b.new_sheet()
    msp = doc.modelspace()
    for n, c, lw in (('A-CEIL-ZONE', 7, 25), ('A-CEIL-STEP', 1, 50), ('A-CEIL-NODROP', 8, 13),
                     ('A-CEIL-LEVL', 7, 18), ('A-CEIL-ACCESS', 5, 25), ('A-LITE-BASE', 2, 18),
                     ('A-LITE-TASK', 30, 18), ('A-LITE-ACCENT', 6, 25), ('A-CEIL-SECT', 7, 25),
                     ('A-NOTE', 7, 18), ('A-REVIEW', 6, 25), ('A-FLOR-LEVL', 7, 18)):
        layer(doc, n, c, lw)
    for k, c in cz.items():
        outline(msp, c['geom'], 'A-CEIL-ZONE')
        if c['finished'] == c['soffit']:
            hatch(msp, c['geom'], 'A-CEIL-NODROP', 'ANSI37', scale=12)
    # step line: owner path clipped to interior
    sl = LineString(OWNER['step_path']).intersection(b.interior.buffer(1))
    for s in ([sl] if sl.geom_type == 'LineString' else getattr(sl, 'geoms', [])):
        if s.geom_type == 'LineString' and s.length > 50:
            msp.add_lwpolyline(list(s.coords), dxfattribs={'layer': 'A-CEIL-STEP'})
    text(msp, 7880, 8200, '跌级线 x=8000 (450立板)', H_TINY, 'A-CEIL-STEP', 'LEFT', 90)
    for x, y, key in panels_full:
        msp.add_lwpolyline([(x - 225, y - 225), (x + 225, y - 225), (x + 225, y + 225), (x - 225, y + 225)],
                           close=True, dxfattribs={'layer': 'A-CEIL-ACCESS'})
        msp.add_line((x - 225, y - 225), (x + 225, y + 225), dxfattribs={'layer': 'A-CEIL-ACCESS'})
    for p in pts: draw_light(msp, p)
    # zone labels (one per floor zone, largest ceiling part)
    from make_a202 import label_block
    done = set()
    for k, c in sorted(cz.items(), key=lambda kv: -kv[1]['geom'].area):
        if c['zone'] in done or c['zone'] == 'stair': continue
        done.add(c['zone'])
        cl = f"净高 {c['clear']}" if c['clear'] is not None else ''
        label_block(msp, c['geom'], [(NAMES.get(c['zone'], c['zone']), H_TXT),
                                     (f"吊顶 +{c['finished']/1000:.3f} {c['material']}" if c['finished'] != c['soffit']
                                      else f"原顶 +{c['soffit']/1000:.3f} 不吊顶", H_SMALL), (cl, H_SMALL)],
                    avoid=None)
    draw_section(msp, 17400, -9200)
    return b, doc, cz, pts, skipped, panels_full


def model_ceiling_diff(b):
    """Owner scheme vs model ceiling meshes (CEILING_LOWER/UPPER): areas assigned to the other level."""
    C = b.ext['ceiling']
    lo = union_tris(C['CEILING_LOWER']['tris']); hi_m = union_tris(C['CEILING_UPPER']['tris'])
    hi = high_region()
    rows = []
    for name, g in (('model HIGH(3250) where owner says LOW', hi_m.difference(hi)),
                    ('model LOW(2800) where owner says HIGH', lo.intersection(hi))):
        for q in polys(g.intersection(b.interior)):
            if q.area > 0.05e6:
                rows.append({'diff': name, 'area_m2': round(q.area / 1e6, 3), 'bounds': [round(v) for v in q.bounds],
                             'action': 'CAD follows owner scheme; model unchanged'})
    return rows


def finish(b, doc, cz, pts, skipped, panels):
    msp = doc.modelspace()
    WORK.mkdir(exist_ok=True); DATA.mkdir(exist_ok=True)
    diffs = model_ceiling_diff(b)
    nodrop = [c for c in cz.values() if c['finished'] == c['soffit']]
    lx, ly = 17400, 13600
    yy = notes(msp, lx, ly, 'A201 天花布置说明 (CD_V01 初步设计)', [
        f'1. 原顶: 下区 +{OWNER["soffit_low"]/1000:.3f}, 上区 +{OWNER["soffit_high"]/1000:.3f}; 吊顶统一下返 {DROP}',
        f'2. 完成面: 下区 +{(OWNER["soffit_low"]-DROP)/1000:.3f}, 上区 +{(OWNER["soffit_high"]-DROP)/1000:.3f}; 两区净高 2650',
        '3. 跌级: x=8000 (y4700-10900) + y=10900 东延至 x13100, 450 立板, 暗藏灯带 (P0.3.2)',
        f'4. 斜线区 = 上区地面(+0.450)位于下区原顶下, 净高 2350, 不吊顶, 明装灯 ({sum(c["geom"].area for c in nodrop)/1e6:.2f}m²)',
        '5. 卫生间/厨房/阳台 铝扣板, 其余 石膏板; 检修口 450x450 (阀门/接线处)',
        f'6. 灯具 {len(pts)} 个, 3000-4000K, 基础/任务/氛围分层; 坐标见 lighting_points.json/csv',
        '7. 吊顶内管线空间、龙骨、梁位须现场核验 (SITE_VERIFY_REQUIRED); 150 下返不代表管线可全部安装',
        '8. 楼梯区不吊顶; 逐踏步净高须现场复核',
        f'9. 与模型天花轮廓差异 {len(diffs)} 处, CAD 按业主方案, 见 a201_ceiling_zones.json'])
    yy = notes(msp, lx, yy - 300, '图例', [])
    legend = (('DOWNLIGHT', '嵌入筒灯'), ('DOWNLIGHT_IP44', '防潮筒灯 IP44'), ('SURFACE_SPOT', '明装射灯(原顶)'),
              ('PENDANT', '吊灯'), ('MIRROR_LIGHT', '镜前灯'), ('STEP_LIGHT', '踏步灯'))
    for i, (t, s2) in enumerate(legend):
        y = yy - 200 - i * 450
        draw_light(msp, {'x': lx + 300, 'y': y, 'type': t})
        text(msp, lx + 800, y, s2, H_SMALL, 'A-NOTE', 'MIDDLE_LEFT')
    y = yy - 200 - len(legend) * 450
    msp.add_line((lx, y), (lx + 600, y), dxfattribs={'layer': 'A-CEIL-STEP'})
    text(msp, lx + 800, y, '跌级线 450 + 暗藏灯带', H_SMALL, 'A-NOTE', 'MIDDLE_LEFT')
    y -= 450
    msp.add_lwpolyline([(lx + 75, y - 225), (lx + 525, y - 225), (lx + 525, y + 225), (lx + 75, y + 225)],
                       close=True, dxfattribs={'layer': 'A-CEIL-ACCESS'})
    text(msp, lx + 800, y, '检修口 450x450', H_SMALL, 'A-NOTE', 'MIDDLE_LEFT')
    text(msp, 8250, -1500, 'A201 天花布置图  1:50  CD_V01  PRELIMINARY_DESIGN / SITE_VERIFY_REQUIRED', 300, 'A-NOTE')
    out = WORK / 'A201_天花布置图.dxf'
    doc.saveas(out)
    (DATA / 'lighting_points.json').write_text(json.dumps(
        {'units': 'mm', 'z': 'absolute (lower floor ±0)', 'cct_range_k': [3000, 4000],
         'points': pts, 'skipped_grid_points': skipped}, ensure_ascii=False, indent=1))
    keys = ['id', 'room', 'room_name', 'layer', 'type', 'x', 'y', 'z_abs', 'mount', 'cct_k', 'beam_deg',
            'lumen', 'circuit', 'switch_id', 'source', 'status', 'note']
    with open(DATA / 'lighting_points.csv', 'w', newline='', encoding='utf-8-sig') as f:
        w = csv.DictWriter(f, fieldnames=keys, extrasaction='ignore', lineterminator='\n'); w.writeheader(); w.writerows(pts)
    (DATA / 'a201_ceiling_zones.json').write_text(json.dumps({
        'owner_scheme': {k: v for k, v in OWNER.items()},
        'zones': [{'id': k, 'zone': c['zone'], 'side': c['side'], 'soffit': c['soffit'], 'finished': c['finished'],
                   'floor': c['floor'], 'clear': c['clear'], 'material': c['material'], 'status': c['status'],
                   'area_m2': round(c['geom'].area / 1e6, 3), 'bounds': [round(v) for v in c['geom'].bounds]}
                  for k, c in cz.items()],
        'access_panels': [{'x': x, 'y': y, 'room': r} for x, y, r in panels],
        'model_vs_owner_diff': diffs}, ensure_ascii=False, indent=1))
    zones = {'zones': [{'id': k, 'polygon': list(c['geom'].exterior.coords),
                        'holes': [list(h.coords) for h in c['geom'].interiors]} for k, c in cz.items()],
             'interior': [list(s['geom'].exterior.coords) for s in b.spaces if s['kind'] == 'ROOM']}
    (DATA / 'a201_zones.json').write_text(json.dumps(zones))
    print('A201 saved', out.name, 'lights', len(pts), 'skipped', len(skipped), 'diffs', len(diffs),
          'nodrop_m2', round(sum(c['geom'].area for c in nodrop) / 1e6, 2))
    return out


if __name__ == '__main__':
    finish(*main())
