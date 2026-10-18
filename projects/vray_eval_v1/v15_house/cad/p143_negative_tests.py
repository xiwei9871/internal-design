#!/usr/bin/env python3
"""P1.4.3 破坏性负向测试 — 篡改副本注入 joint_acceptance_v2.qa(), 必须检出.
全部作用于 derived/p143_tests/ 副本, 不接触正式 DXF."""
import sys, shutil, json
from pathlib import Path
import ezdxf
from shapely.geometry import Polygon
sys.path.insert(0,'.')
from joint_acceptance_v2 import parse, qa

CAD = Path(__file__).resolve().parent
TD = CAD/'derived'/'p143_tests'; TD.mkdir(exist_ok=True)
A102 = CAD/'A102_WALL_DIFF_POC_V3.dxf'
A103 = CAD/'A103_CONSTRUCTION_POC_V7.dxf'

def tamper(src, dst, fn):
    shutil.copy(src, dst)
    doc = ezdxf.readfile(dst); fn(doc); doc.saveas(dst)

def t_del_dim_xdata(doc):
    for e in doc.modelspace():
        if e.dxftype()=='DIMENSION':
            try: e.discard_xdata('DEVINDIM')
            except ezdxf.DXFValueError: pass
            return
def t_move_dim_value(doc):
    for e in doc.modelspace():
        if e.dxftype()=='DIMENSION':
            try:
                xd=e.get_xdata('DEVINDIM')
                xd=[(c, (v+100.0) if c==1040 else v) for c,v in xd]
                e.set_xdata('DEVINDIM', xd)
            except ezdxf.DXFValueError: pass
            return
def t_move_wall(doc):
    for e in doc.modelspace():
        if e.dxftype()=='LWPOLYLINE' and e.dxf.layer=='A-WALL':
            try:
                xd=e.get_xdata('DEVINSRC')
                if xd and xd[0][1]=='W_EXT_S#p0':
                    pts=[(p[0]+100,p[1]) for p in e.get_points('xy')]
                    e.set_points(pts, format='xy')
                    return
            except ezdxf.DXFValueError: pass
def t_del_conflict(doc):
    for e in doc.modelspace():
        if e.dxftype()=='LWPOLYLINE' and e.dxf.layer=='A-CONFLICT':
            e.destroy(); return
def t_demo_to_approved(doc):
    for e in doc.modelspace():
        if e.dxftype()=='LWPOLYLINE' and e.dxf.layer=='A-WALL-HOLD':
            try:
                xd=e.get_xdata('DEVINSRC')
                if xd and 'W_EXT_N_BAL#demol0' in [v[1] for v in xd]:
                    e.dxf.layer='A-WALL-DEMO-DESIGN'
                    return
            except ezdxf.DXFValueError: pass

def t_insert_phantom_wall(doc):
    # A103插入一段模型中不存在的新隔墙 -> QJ9 extra 必须检出
    e = doc.modelspace().add_lwpolyline(
        [(6000,6000),(6400,6000),(6400,6200),(6000,6200)], close=True,
        dxfattribs={'layer':'A-DESIGN'})
    e.set_xdata('DEVINSRC',[(1000,'PHANTOM_INJECTED'),(1000,'ACTUAL_NEW_PART')])
def t_delete_small_walls(doc):
    # 删除多个小墙段(各<20000mm²): 单片都低于阈值, 必须靠累计检出
    small = sorted(
        [e for e in doc.modelspace()
         if e.dxftype()=='LWPOLYLINE' and e.dxf.layer in
            ('A-DESIGN','A-WALL','A-STAIR','A-SOFFIT','A-MISC-NEW')],
        key=lambda e: Polygon([(p[0],p[1]) for p in e.get_points('xy')]).area
                      if len(list(e.get_points('xy')))>=3 else 0)
    for e in small[:6]: e.destroy()

tests = [
    ('N1_A102_dim_xdata_removed', t_del_dim_xdata, '102', 'QJ5'),
    ('N2_A103_dim_value+100',    t_move_dim_value,'103', 'QJ5'),
    ('N3_A103_wall_moved_100mm', t_move_wall,     '103', 'QJ6'),
    ('N4_A103_conflict_deleted', t_del_conflict,  '103', 'QJ4'),
    ('N5_A102_hold_as_approved', t_demo_to_approved,'102','QJ2'),
    ('N6_A103_phantom_wall',     t_insert_phantom_wall,'103','QJ9'),
    ('N7_A103_small_walls_deleted', t_delete_small_walls,'103','QJ9'),
]
base102, base103 = parse(A102), parse(A103)
fails = []
for name, fn, which, expect_key in tests:
    dst = TD/f'{name}.dxf'
    tamper(A102 if which=='102' else A103, dst, fn)
    res = qa(parse(dst) if which=='102' else base102,
             parse(dst) if which=='103' else base103)
    detected = not all(v for k,v in res.items() if isinstance(v,bool))
    print(('PASS' if detected else 'FAIL'), name,
          '| verdict:', res['verdict'],
          '| detail:', {k:v for k,v in res.items() if v is False or
                        (k in ('QJ4_conflict_missing','QJ5_dim_errs','QJ6_wall_geom_parity','QJ3_detail') and v)})
    if not detected: fails.append(name)
print(f'\n{len(tests)-len(fails)}/{len(tests)} detected')
sys.exit(1 if fails else 0)
