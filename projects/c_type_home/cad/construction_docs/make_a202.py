#!/usr/bin/env python3
"""A202 地面铺装图 CD_V01 -> work/A202_地面铺装图.dxf + data/a202_*.{csv,json}.
Zones: model floor meshes (cd_common.Base), clipped to the survey-enclosed interior.
Gaps are classified, never filled with guessed rectangles."""
import csv, json, math
from shapely.geometry import box, Point
from shapely.ops import unary_union

from cd_common import (Base, NAMES, WET, BATHS, OWNER, WORK, DATA, H_TXT, H_SMALL, H_TINY,
                       layer, text, outline, hatch, clip_lines, label_point, notes, polys, sha256,
                       A103, EXTRACT, HERE)

PLANK = 150                                    # drawn board pitch (spec width OWNER_REVIEW)
TILE_SPEC = {                                  # room -> (long, short, label); all OWNER_REVIEW
    'kitchen': (1200, 600, '600x1200 瓷砖'), 'north_sunroom': (1200, 600, '600x1200 瓷砖'),
    'service_balcony': (600, 300, '300x600 防滑砖'), 'master_bath': (600, 300, '300x600 防滑砖'),
    'secondary_bath': (600, 300, '300x600 防滑砖'), 'guest_bath': (600, 300, '300x600 防滑砖'),
}


def tile_layout(msp, key, g, spec):
    """Centre the grid on the zone; shift half a tile if an edge cut would be < 1/3 module."""
    x0, y0, x1, y1 = g.bounds
    long_x = (x1 - x0) >= (y1 - y0)
    mx, my = (spec[0], spec[1]) if long_x else (spec[1], spec[0])

    def axis(lo, hi, m):
        c = (lo + hi) / 2
        for org in (c, c + m / 2):             # joint on centre line, else tile centred
            first = (org - lo) % m or m
            last = (hi - org) % m or m
            if min(first, last) >= m / 3: return org, round(first), round(last)
        org = c
        return org, round((org - lo) % m or m), round((hi - org) % m or m)
    ox, cx0, cx1 = axis(x0, x1, mx)
    oy, cy0, cy1 = axis(y0, y1, my)
    n = clip_lines(msp, g, False, mx, ox, 'A-FLOR-TILE') + clip_lines(msp, g, True, my, oy, 'A-FLOR-TILE')
    msp.add_circle((ox, oy), 60, dxfattribs={'layer': 'A-FLOR-START'})
    msp.add_line((ox - 120, oy), (ox + 120, oy), dxfattribs={'layer': 'A-FLOR-START'})
    msp.add_line((ox, oy - 120), (ox, oy + 120), dxfattribs={'layer': 'A-FLOR-START'})
    return {'module': f'{mx}x{my}', 'long_axis': 'X' if long_x else 'Y', 'start': [round(ox), round(oy)],
            'cut_x_mm': [cx0, cx1], 'cut_y_mm': [cy0, cy1], 'lines': n}


def label_block(msp, g, lines, avoid=None):
    """Stack label lines at the zone's pole of inaccessibility, shrinking text to fit the room
    width and moving off the tile start point."""
    from shapely.ops import polylabel
    from shapely.geometry import Point as _Pt
    p = max(polys(g), key=lambda q: q.area)
    c = polylabel(p, tolerance=20)
    w = p.intersection(box(p.bounds[0], c.y - 10, p.bounds[2], c.y + 10)).length / 2 or (p.bounds[2] - p.bounds[0])
    hs = [min(h, 0.9 * w / max(len(t), 1)) for t, h in lines]
    vh = p.intersection(box(c.x - 10, p.bounds[1], c.x + 10, p.bounds[3])).length / 2 or (p.bounds[3] - p.bounds[1])
    k = min(1.0, 0.7 * vh / sum(h * 2.0 for h in hs))  # shrink so the block uses <= 70% of local height
    hs = [h * k for h in hs]
    pitch = [h * 2.0 for h in hs]
    total = sum(pitch)
    x, y = c.x, c.y
    if avoid is not None and abs(avoid[0] - x) < 900 and abs(avoid[1] - y) < total / 2 + 200:
        for dy in (total / 2 + 250, -(total / 2 + 250)):
            if p.buffer(-100).contains(_Pt(x, avoid[1] + dy)): y = avoid[1] + dy; break
    yy = y + total / 2
    for (t, _), h, pt in zip(lines, hs, pitch):
        if not t: continue
        text(msp, x, yy - pt / 2, t, h, 'A-FLOR-LEVL')
        yy -= pt


def hold_tag(msp, rect, holds, desc):
    """Small circled tag Hn at the opening; the sentence goes to the notes block."""
    n = len(holds) + 1
    x0, y0, x1, y1 = rect.bounds
    cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
    msp.add_circle((cx, cy), 150, dxfattribs={'layer': 'A-REVIEW'})
    text(msp, cx, cy, f'H{n}', H_TINY, 'A-REVIEW')
    holds.append({'tag': f'H{n}', 'at': [round(cx), round(cy)], 'desc': desc})


def door_sides(b, rect, horiz, off=320):
    x0, y0, x1, y1 = rect.bounds
    cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
    if horiz:
        d = (y1 - y0) / 2 + off; pts = [(cx, cy - d), (cx, cy + d)]
    else:
        d = (x1 - x0) / 2 + off; pts = [(cx - d, cy), (cx + d, cy)]
    return [b.zone_at(*p) for p in pts], (cx, cy)


def main():
    b = Base()
    doc = b.new_sheet()
    msp = doc.modelspace()
    for n, c, lw in (('A-FLOR-WOOD', 30, 13), ('A-FLOR-TILE', 4, 13), ('A-FLOR-ZONE', 7, 30),
                     ('A-FLOR-START', 6, 18), ('A-FLOR-THRS', 1, 25), ('A-FLOR-LEVL', 7, 18),
                     ('A-NOTE', 7, 18), ('A-REVIEW', 6, 25), ('A-FLOR-BAY', 8, 13)):
        layer(doc, n, c, lw)
    rows, tiles, checks, holds = [], {}, [], []

    for key, z in b.zones.items():
        g = z['geom']
        if g.is_empty: continue
        outline(msp, g, 'A-FLOR-ZONE')
        mat, spec_txt, status = z['mat'], '', z['status']
        if key in TILE_SPEC:
            if mat != 'TILE':
                checks.append(f'{NAMES[key]}: 模型材质 {mat}, 设计规格为瓷砖 -> 按瓷砖, OWNER_REVIEW')
            mat = 'TILE'
            tiles[key] = tile_layout(msp, key, g, TILE_SPEC[key])
            spec_txt = TILE_SPEC[key][2] + ' 居中排砖'
            status = f'{status}; spec OWNER_REVIEW'
        else:
            clip_lines(msp, g, False, PLANK, 0, 'A-FLOR-WOOD')
            spec_txt = '白蜡木地板 南北向' if key != 'stair' else '白蜡木踏步 踏面+踢面'
        lvl = z['level']
        lv = '±0.000' if lvl == 0 else (f'+{lvl/1000:.3f}' if lvl else '+0.150/+0.300/+0.450')
        if key != 'stair':
            start = tiles[key]['start'] if key in tiles else None
            label_block(msp, g, [(f'{NAMES.get(key, key)}', H_TXT), (f'{g.area/1e6:.2f}m²  完成面 {lv}', H_SMALL),
                                 (spec_txt, H_SMALL)], avoid=start)
        rows.append({'id': key, 'name': NAMES.get(key, key), 'material': mat, 'spec': spec_txt,
                     'level_mm': lvl, 'area_m2': round(g.area / 1e6, 3), 'parts': len(polys(g)),
                     'source': z['source'], 'status': status, **({'tile': tiles[key]} if key in tiles else {})})

    # stair treads: visible tread = STEP_i minus STEP_{i+1}
    S = {k: unary_union([__import__('shapely.geometry', fromlist=['Polygon']).Polygon(t[:3])
                         for t in v['tris']]) for k, v in b.ext['stair'].items()}
    for i, k in enumerate(('STEP_0', 'STEP_1', 'STEP_2')):
        tread = S[k].difference(S[f'STEP_{i+1}']) if i < 2 else S[k]
        tread = tread.intersection(b.interior)
        if tread.is_empty: continue
        from shapely.geometry import LineString as _LS
        yl = 5000 + i * 1100                       # stagger along the stair so wavy treads don't collide
        cut = tread.intersection(_LS([(tread.bounds[0] - 10, yl), (tread.bounds[2] + 10, yl)]))
        if cut.is_empty: x, y = label_point(tread)
        else: x, y = cut.centroid.x, yl
        text(msp, x, y, f'踏{i+1} +{b.step_levels[k]/1000:.3f}', H_TINY, 'A-FLOR-LEVL', rot=90)
    text(msp, 5500, 6250, '三级台阶 白蜡木踏面+踢面', H_SMALL, 'A-FLOR-LEVL', 'MIDDLE_RIGHT')

    # bay windows / reveals: not floor finish
    for s in b.spaces:
        if s['kind'] == 'ROOM': continue
        hatch(msp, s['geom'], 'A-FLOR-BAY', 'ANSI37', scale=10)
        x, y = label_point(s['geom'])
        text(msp, x, y, '飘窗台/窗洞 不计地面', H_TINY, 'A-FLOR-BAY')

    # thresholds at survey doors
    doors = []
    for rect in b.doors:
        x0, y0, x1, y1 = rect.bounds
        horiz = (x1 - x0) > (y1 - y0)
        sides, (cx, cy) = door_sides(b, rect, horiz)
        zs = [b.zones.get(s) if s else None for s in sides]
        rec = {'at': [round(cx), round(cy)], 'width': round(max(x1 - x0, y1 - y0)),
               'sides': [NAMES.get(s, s) if s else '户外' for s in sides]}
        if zs.count(None) == 2:
            rec['disposition'] = 'UNRESOLVED_HOLD'; doors.append(rec); continue
        mats = {z['mat'] if z else 'EXT' for z in zs}
        lvls = {z['level'] if z else 'EXT' for z in zs}
        bath = [s for s in sides if s in BATHS]
        if 'master_bath' in bath:
            outline(msp, rect, 'A-REVIEW')
            hold_tag(msp, rect, holds, '主卫(母亲适老)门口: 不设凸起门槛; 排水/挡水做法待定')
            rec['disposition'] = 'FLUSH_NO_RAISED_THRESHOLD; HOLD drainage/water-stop'
        elif len(mats) > 1 or len(lvls) > 1 or bath:
            hatch(msp, rect, 'A-FLOR-THRS', 'ANSI31', scale=6); outline(msp, rect, 'A-FLOR-THRS')
            text(msp, cx, cy + (300 if horiz else 0), f'门槛石 L{rec["width"]}', H_TINY, 'A-FLOR-THRS',
                 'MIDDLE_CENTER' if horiz else 'MIDDLE_LEFT')
            rec['disposition'] = 'THRESHOLD_STONE' + ('; flush + water-stop' if bath else '')
        else:
            rec['disposition'] = 'CONTINUOUS_NO_THRESHOLD'
        doors.append(rec)

    # model doors missing in A103: review only, never drawn as openings
    for md in b.model_doors():
        r = md['rect']
        outline(msp, r, 'A-REVIEW')
        cx, cy = r.centroid.x, r.centroid.y
        hold_tag(msp, r, holds, f'模型有门({md["name"]}), A103 无洞口: 墙按 A103 保留, 开洞待确认')
        doors.append({'at': [round(cx), round(cy)], 'model_object': md['name'],
                      'disposition': 'MODEL_ONLY_DOOR_HOLD (A103 wall kept; owner/site to confirm)'})
    return b, doc, rows, tiles, doors, checks, holds




def finish(b, doc, rows, tiles, doors, checks, holds):
    msp = doc.modelspace()
    WORK.mkdir(exist_ok=True); DATA.mkdir(exist_ok=True)
    wood = sum(r['area_m2'] for r in rows if r['material'] == 'WOOD')
    tile = sum(r['area_m2'] for r in rows if r['material'] == 'TILE')
    gap_rows = [r for r in b.records if r['type'] == 'INTERIOR_MISSING']
    lx, ly = 17400, 13600
    yy = notes(msp, lx, ly, 'A202 地面铺装说明 (CD_V01 初步设计)', [
        f'1. 木地板约 {wood:.1f}m²: 白蜡木, 全屋统一南北向; 板宽按选品(图示线距150)',
        f'2. 瓷砖约 {tile:.1f}m²: 厨房/阳光房 600x1200; 生活阳台/三卫 300x600 防滑砖 (规格 OWNER_REVIEW)',
        '3. 排砖: 各间居中, 边砖 >= 1/3 砖, 起铺点见图; 损耗另计',
        '4. 完成面: 下层 ±0.000, 上层 +0.450, 台阶 +0.150/+0.300/+0.450',
        '5. 门槛石: 材质或标高变化处及客卫/次主卫门洞; 主卫(母亲适老)门口不设凸起门槛',
        '6. 卫生间找坡/地漏/挡水做法由业主排水方案定 -> HOLD',
        '7. 分区来源: 模型 WHOLE_HOUSE_CORRECTED_SUPPORTED_V2 地面网格; 墙体: A103 V7 实测底图',
        f'8. 模型未覆盖的室内 {sum(r["area_m2"] for r in gap_rows):.2f}m² 按墙体围合补齐, 见 a202_gap_disposition.json',
        '9. 品红框 = 模型有门但 A103 无洞口, 墙体按 A103 保留, 待确认',
        '10. 面积为图面净面积, 下单以现场复尺为准 (SITE_VERIFY_REQUIRED)'])
    yy = notes(msp, lx, yy - 300, '图例', [])
    from shapely.geometry import box as _b
    for i, (lay, s) in enumerate((('A-FLOR-WOOD', '木地板'), ('A-FLOR-TILE', '瓷砖分缝'),
                                  ('A-FLOR-THRS', '门槛石'), ('A-FLOR-START', '起铺点'),
                                  ('A-REVIEW', '待确认 (HOLD)'), ('A-FLOR-BAY', '飘窗/窗洞, 不计地面'))):
        y = yy - 150 - i * 420
        sq = _b(lx, y - 150, lx + 600, y + 150)
        if lay == 'A-FLOR-THRS': hatch(msp, sq, lay, 'ANSI31', scale=6)
        elif lay == 'A-FLOR-BAY': hatch(msp, sq, lay, 'ANSI37', scale=10)
        elif lay == 'A-FLOR-START': msp.add_circle((lx + 300, y), 60, dxfattribs={'layer': lay})
        elif lay in ('A-FLOR-WOOD', 'A-FLOR-TILE'):
            for k in range(1, 4): msp.add_line((lx + k * 150, y - 150), (lx + k * 150, y + 150), dxfattribs={'layer': lay})
        outline(msp, sq, lay)
        text(msp, lx + 800, y, s, H_SMALL, 'A-NOTE', 'MIDDLE_LEFT')
    hold_lines = [f'{h["tag"]}  {h["desc"]}' for h in holds] + [f'- {c}' for c in checks]
    if hold_lines:
        notes(msp, lx, yy - 2900, 'HOLD / 待确认 (图中品红圈)', hold_lines)
    text(msp, 8250, -1500, 'A202 地面铺装图  1:50  CD_V01  PRELIMINARY_DESIGN / SITE_VERIFY_REQUIRED', 300, 'A-NOTE')
    out = WORK / 'A202_地面铺装图.dxf'
    doc.saveas(out)

    with open(DATA / 'a202_rooms.csv', 'w', newline='', encoding='utf-8-sig') as f:
        w = csv.writer(f, lineterminator='\n')
        w.writerow(['id', 'name', 'material', 'spec', 'level_mm', 'area_m2', 'status', 'source'])
        for r in rows:
            w.writerow([r['id'], r['name'], r['material'], r['spec'], r['level_mm'], r['area_m2'], r['status'], r['source']])
        w.writerow(['TOTAL_WOOD', '', 'WOOD', '', '', round(wood, 3), '', ''])
        w.writerow(['TOTAL_TILE', '', 'TILE', '', '', round(tile, 3), '', ''])
    gaps = {'interior_reference': 'A103 V7 walls + windows + doors, enclosed rings (no buffer closing)',
            'interior_m2': round(b.interior.area / 1e6, 3),
            'spaces': [{'kind': s['kind'], 'area_m2': round(s['geom'].area / 1e6, 3),
                        'bounds': [round(v) for v in s['geom'].bounds]} for s in b.spaces],
            'model_floor_outside_interior_m2': round(b.model_spill.area / 1e6, 3),
            'records': b.records,
            'poc_v01_gaps': POC_GAPS}
    (DATA / 'a202_gap_disposition.json').write_text(json.dumps(gaps, ensure_ascii=False, indent=1))
    (DATA / 'a202_tiles_doors.json').write_text(json.dumps({'tiles': tiles, 'doors': doors, 'holds': holds},
                                                           ensure_ascii=False, indent=1))
    zones = {'zones': [{'id': k, 'polygon': list(p.exterior.coords), 'holes': [list(h.coords) for h in p.interiors]}
                       for k, z in b.zones.items() for p in polys(z['geom'])],
             'interior': [list(s['geom'].exterior.coords) for s in b.spaces if s['kind'] == 'ROOM']}
    (DATA / 'a202_zones.json').write_text(json.dumps(zones))
    print('A202 saved', out.name, 'wood', round(wood, 2), 'tile', round(tile, 2), 'checks', checks)
    return out


# POC V01 reported 6 gaps (buffer-closed interior). Disposition after independent interior check:
POC_GAPS = [
    {'at': [4809, 109], 'area_m2': 0.867, 'class': 'EXTERIOR_OR_ALGO',
     'why': 'outside survey-enclosed interior; south of kitchen/balcony wall line'},
    {'at': [2540, 3754], 'area_m2': 1.049, 'class': 'EXTERIOR_OR_ALGO',
     'why': 'west of dining wall x=2700; produced by 3000mm buffer closing'},
    {'at': [12250, 5900], 'area_m2': 2.25, 'class': 'INTERIOR_MISSING',
     'why': 'enclosed by A103 walls between mother bedroom, master bath, study; model floor absent -> filled as vestibule'},
    {'at': [3296, 14142], 'area_m2': 1.136, 'class': 'EXTERIOR_OR_ALGO',
     'why': 'living-room bay window outside wall line; not floor finish'},
    {'at': [15730, 3474], 'area_m2': 0.637, 'class': 'EXTERIOR_OR_ALGO',
     'why': 'east of mother-bedroom wall; produced by buffer closing'},
    {'at': [13459, 12670], 'area_m2': 1.534, 'class': 'EXTERIOR_OR_ALGO',
     'why': 'study NE bay window / exterior; not floor finish'},
]


if __name__ == '__main__':
    finish(*main())
