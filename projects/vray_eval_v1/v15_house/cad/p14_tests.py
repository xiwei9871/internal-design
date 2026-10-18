#!/usr/bin/env python3
"""P1.4.1 回归测试: 开放折线不得产生虚假结构面.
全部在内存构造合成 ezdxf 文档, 不接触任何源文件."""
import sys
sys.path.insert(0, '.')
import ezdxf
from three_source_mapping import extract_structural, AX, AY

def doc_with(*entities):
    d = ezdxf.new('R2010'); d.layers.add('S-S.WALL')
    m = d.modelspace()
    for kind, args in entities:
        if kind == 'LINE':
            m.add_line((args[0]+AX,args[1]+AY),(args[2]+AX,args[3]+AY),
                       dxfattribs={'layer':'S-S.WALL'})
        elif kind == 'LWP':
            pts, closed = args
            m.add_lwpolyline([(x+AX,y+AY) for x,y in pts], close=closed,
                             dxfattribs={'layer':'S-S.WALL'})
        elif kind == 'HATCH':
            paths, closed = args
            h = m.add_hatch(dxfattribs={'layer':'S-S.WALL'})
            for ring in paths:
                h.paths.add_polyline_path([(x+AX,y+AY) for x,y in ring],
                                          is_closed=closed)
    return d

def covered(ext, x, y):
    from shapely.geometry import Point
    return ext['union'].covers(Point(x,y))

results = []
def check(name, cond, note=''):
    results.append((name, bool(cond), note)); print(('PASS' if cond else 'FAIL'), name, note)

# T1: 开放4点折线(复刻307C40形状) -> 内部区域不得被覆盖
d = doc_with(('LWP', ([(7880,11100),(7880,13820),(13020,13820),(13020,11100)], False)))
e = extract_structural(d.modelspace())
check('T1 open_LWP_no_face', not covered(e, 10000, 13400),
      '开放U形折线内部无结构面')

# T2: 同形但闭合 -> 有面(200厚墙带应被 anomaly 拦截? 该面 2720厚>1200 且面大 -> 剔)
d = doc_with(('LWP', ([(7880,11100),(7880,13820),(13020,13820),(13020,11100)], True)))
e = extract_structural(d.modelspace())
check('T2 closed_giant_face_anomaly',
      not covered(e, 10000, 13400) and
      any(a['reason']=='LARGE_FACE_NOT_WALL' for a in e['anomalies']),
      '闭合跨房间大面被 LARGE_FACE_NOT_WALL 剔除')

# T3: 正常200厚闭合墙带 -> 有面且无异常
d = doc_with(('LWP', ([(7880,13400),(7880,13600),(13020,13600),(13020,13400)], True)))
e = extract_structural(d.modelspace())
check('T3 wall_band_face', covered(e, 10000, 13500), '200mm墙带闭合成面')

# T4: 开放折线 + 一条真实LINE补口 -> 线网闭合, 有面
d = doc_with(
    ('LWP', ([(1000,1000),(1000,1200),(3000,1200),(3000,1000)], False)),
    ('LINE', (3000,1000,1000,1000)))
e = extract_structural(d.modelspace())
check('T4 open_LWP_plus_LINE_ring', covered(e, 2000, 1100),
      '开放折线+真边闭合 -> 线网成环')

# T5: 4条LINE围合 -> 有面
d = doc_with(('LINE',(5000,5000,5200,5000)),('LINE',(5200,5000,5200,7000)),
             ('LINE',(5200,7000,5000,7000)),('LINE',(5000,7000,5000,5000)))
e = extract_structural(d.modelspace())
check('T5 LINE_ring', covered(e, 5100, 6000), 'LINE环面')

# T6: HATCH闭合路径 -> 有面(剪力墙填充)
d = doc_with(('HATCH', ([[(7800,7800),(8600,7800),(8600,8600),(7800,8600)]], True)))
e = extract_structural(d.modelspace())
check('T6 HATCH_closed', covered(e, 8200, 8200), 'HATCH填充面')

# T7: HATCH开放路径 -> 不独立成面
d = doc_with(('HATCH', ([[(9000,9000),(9000,9200),(11000,9200)]], False)))
e = extract_structural(d.modelspace())
check('T7 HATCH_open_no_face', not covered(e, 10000, 9100), '开放HATCH不成面')

# T8: 蝴蝶结自交闭合折线 -> 修复或剔除, 且记 anomaly
d = doc_with(('LWP', ([(0,0),(2000,0),(0,200),(2000,200)], True)))
e = extract_structural(d.modelspace())
check('T8 self_intersect_flagged',
      any('SELF_INTERSECT' in a['reason'] for a in e['anomalies']),
      '自交环被标记')

# T9: 真实文件端到端 — W_EXT_N_BAL 拆除矩形内不得有结构覆盖
import json
from shapely.geometry import Polygon
ext_real = extract_structural(ezdxf.readfile(
    '/Users/xiwei/interior_design/projects/c_type_home/cad/structure_only_source_sync.dxf'
).modelspace())
demo = Polygon([(7900,13400),(13000,13400),(13000,13600),(7900,13600)])
r = demo.intersection(ext_real['union']).area / demo.area
check('T9 N_BAL_demo_real_file', r < 0.05, f'实测结构覆盖={r:.3f}')

failed = [n for n,ok,_ in results if not ok]
print(f'\n{len(results)-len(failed)}/{len(results)} PASS')
sys.exit(1 if failed else 0)
