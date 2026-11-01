#!/usr/bin/env python3
"""A201 天花布置图 V2 候选 (lighting review) -> work/A201_天花布置图_V2候选.dxf.
Same ceiling zones / step line / panels / section as make_a201.py; lights from
data/lighting_points_v2.json. Never writes A201_天花布置图.dxf or lighting_points.json."""
import json
from shapely.geometry import box

import make_a201 as A
from cd_common import WORK, DATA, OWNER, H_SMALL, H_TINY, text, notes, layer

V2 = json.loads((DATA / 'lighting_points_v2.json').read_text())
OUT = WORK / 'A201_天花布置图_V2候选.dxf'

A.SYM.update({'NIGHT_UNDERBED_SENSOR': 'A-LITE-NIGHT', 'NIGHT_WALL_LOW': 'A-LITE-NIGHT',
              'WALL_READING': 'A-LITE-TASK', 'LED_UNDER_CABINET': 'A-LITE-TASK', 'SHOWER_LIGHT': 'A-LITE-BASE'})
_draw = A.draw_light


def draw_light(msp, p):
    x, y, t = p['x'], p['y'], p['type']
    lay = A.SYM.get(t, 'A-LITE-BASE')
    if t in ('NIGHT_UNDERBED_SENSOR', 'NIGHT_WALL_LOW'):
        msp.add_lwpolyline([(x - 90, y - 90), (x + 90, y - 90), (x + 90, y + 90), (x - 90, y + 90)], close=True,
                           dxfattribs={'layer': lay})
        msp.add_line((x - 90, y - 90), (x + 90, y + 90), dxfattribs={'layer': lay})
    elif t == 'WALL_READING':
        msp.add_circle((x, y), 80, dxfattribs={'layer': lay})
        msp.add_lwpolyline([(x - 130, y - 130), (x + 130, y - 130), (x, y + 150)], close=True, dxfattribs={'layer': lay})
    elif t == 'LED_UNDER_CABINET' and p.get('path'):
        (ax, ay), (bx, by) = p['path']
        for d in (-25, 25):
            msp.add_line((ax + d, ay), (bx + d, by), dxfattribs={'layer': lay, 'linetype': 'DASHED'})
    elif t == 'MIRROR_LIGHT' and p.get('orient') == 'V':
        msp.add_lwpolyline([(x - 40, y - 250), (x + 40, y - 250), (x + 40, y + 250), (x - 40, y + 250)], close=True,
                           dxfattribs={'layer': lay})
    elif t == 'SHOWER_LIGHT':
        _draw(msp, {**p, 'type': 'DOWNLIGHT_IP44'})
        msp.add_circle((x, y), 170, dxfattribs={'layer': 'A-REVIEW'})
    else:
        _draw(msp, p)
    if p.get('action') in ('MOVE', 'ADD', 'CONVERT'):
        TAGS.append((p['id'], x, y))


TAGS = []
UNTAGGED = []
A.draw_light = draw_light
A.lighting = lambda b, cz, step, panels: (V2['points'], [])


def place_tags(msp):
    """Put each ID tag at the first of 8 offsets whose box clears every existing text."""
    from ezdxf import bbox as _bb
    occ = []
    for e in msp.query('TEXT'):
        b = _bb.extents([e])
        if b.has_data: occ.append(box(b.extmin.x, b.extmin.y, b.extmax.x, b.extmax.y))
    h = H_TINY * 0.8
    for tid, x, y in TAGS:
        w = len(tid) * h * 0.75
        offs = [(160, 150), (160, -250), (-160 - w, 150), (-160 - w, -250), (0, 300), (0, -400), (300, 0), (-300 - w, 0)]
        offs += [(dx * k, dy * k) for k in (2, 3) for dx, dy in offs[:4]]
        for dx, dy in offs:
            r = box(x + dx, y + dy, x + dx + w, y + dy + h)
            if not any(r.intersects(o) for o in occ):
                text(msp, x + dx, y + dy, tid, h, 'A-LITE-TAG', 'LEFT')
                occ.append(r)
                break
        else:
            UNTAGGED.append(tid)        # no clear spot: ID stays in lighting_points_v2.csv only


def main():
    b, doc, cz, pts, skipped, panels = A.main()
    layer(doc, 'A-LITE-NIGHT', 6, 25)
    layer(doc, 'A-LITE-TAG', 6, 13)
    layer(doc, 'A-LITE-REMOVED', 8, 13, 'DASHED')
    msp = doc.modelspace()
    place_tags(msp)
    removed = [r for r in __import__('csv').DictReader(open(DATA / 'lighting_changes.csv', encoding='utf-8-sig'))
               if r['action'] in ('REMOVE', 'MOVE', 'CONVERT')]
    for r in removed:                       # ghost of the V1 position
        x, y = json.loads(r['from'])
        msp.add_circle((x, y), 90, dxfattribs={'layer': 'A-LITE-REMOVED'})
        msp.add_line((x - 110, y - 110), (x + 110, y + 110), dxfattribs={'layer': 'A-LITE-REMOVED'})
    lx, ly = 17400, 13600
    yy = notes(msp, lx, ly, 'A201 V2 候选: 灯光优化 (FUNCTIONAL_DESIGN_REVIEW, 未经业主确认)', [
        '1. 基于 A201 V1 (94 点) 按房间审查: 保留 73、重新分组 8、移动 8、合并 1、取消 4、新增 13 -> 103 点',
        '2. 移动原因: 衣柜/冰箱上柜/阳光房高柜/卧榻正上方, 次主卫淋浴区内',
        '3. 厨房台面: 取消吊柜上方 3 盏, 改吊柜底灯带 (原灯被吊柜遮挡)',
        '4. 母亲夜间路线: 床下感应 -> 门旁 -> 前过道 -> 主卫门内, 低位 3000K, 感应+定时',
        '5. 新增床头阅读灯 5、梳妆镜前灯 1; 客厅/卧室电视墙与沙发墙单独调光',
        '6. 灰色虚线 x 圈 = V1 原位置; 品红编号 = 新增/移动点',
        '7. 未提供 IES/LDT 配光数据: 不判定照度、眩光达标; 淋浴区灯具分区由电气确认',
        '8. 坐标与控制分组见 lighting_points_v2.json/csv; 正式 A201 未覆盖'])
    text(msp, lx + 300, yy - 300, '□╳ 夜灯(低位)   ○△ 床头阅读灯   ═ 吊柜下灯带', H_SMALL, 'A-NOTE', 'LEFT')
    doc.saveas(OUT)
    print('A201 V2 candidate saved', OUT.name, 'points', len(V2['points']), 'ghosts', len(removed), 'untagged', UNTAGGED)
    return OUT


if __name__ == '__main__':
    main()
