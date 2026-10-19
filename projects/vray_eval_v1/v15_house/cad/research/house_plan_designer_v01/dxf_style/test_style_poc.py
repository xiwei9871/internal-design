#!/usr/bin/env python3
"""STYLE_POC 完整性回归测试 — Gate 任务C/D。
断言: 实体0缺失0变更, DEVINSRC/DEVINDIM XDATA 逐实体保留, DEVINPOC 1005 可解析,
DIMENSION 值不变, 冻结层一致, 两图轴线坐标一致。
运行: python -m unittest test_style_poc -v
"""
import unittest, ezdxf

CAD = '/Users/xiwei/interior_design/projects/vray_eval_v1/v15_house/cad'
OUT = CAD + '/research/house_plan_designer_v01/dxf_style'
PAIRS = [('A102', 'A102_WALL_DIFF_POC_V3.dxf', 'A102_STYLE_POC.dxf'),
         ('A103', 'A103_CONSTRUCTION_POC_V7.dxf', 'A103_STYLE_POC.dxf')]
ADDED_LAYERS = {'AXIS', 'AXIS-NUM', 'A-DOOR-NUM', 'A-WIN-NUM'}


def sig(e):
    t = e.dxftype()
    if t == 'LINE': return (t, tuple(e.dxf.start), tuple(e.dxf.end))
    if t == 'LWPOLYLINE':
        return (t, tuple(tuple(round(x, 3) for x in p[:2]) for p in e.get_points('xy')), e.closed)
    if t == 'INSERT': return (t, e.dxf.name, tuple(e.dxf.insert))
    if t in ('TEXT', 'MTEXT'): return (t, getattr(e.dxf, 'text', ''), tuple(e.dxf.insert))
    if t == 'CIRCLE': return (t, tuple(e.dxf.center), e.dxf.radius)
    if t == 'ARC': return (t, tuple(e.dxf.center), e.dxf.radius, e.dxf.start_angle, e.dxf.end_angle)
    if t == 'HATCH': return (t, e.dxf.pattern_name or '')
    if t == 'DIMENSION':
        return (t, e.dxf.get('defpoint'), e.dxf.get('defpoint2'),
                e.dxf.get('defpoint3'), e.dxf.get('text'))
    if t == 'POLYLINE':
        return (t, tuple((round(v.dxf.location.x, 3), round(v.dxf.location.y, 3))
                         for v in e.vertices))
    return (t,)


class TestStylePOC(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.d = {}
        for tag, src, poc in PAIRS:
            cls.d[tag] = (ezdxf.readfile(f'{CAD}/{src}'), ezdxf.readfile(f'{OUT}/{poc}'))

    def test_no_missing_no_changed(self):
        for tag, (a, b) in self.d.items():
            ea = {e.dxf.handle: e for e in a.modelspace()}
            eb = {e.dxf.handle: e for e in b.modelspace()}
            self.assertEqual(set(ea) - set(eb), set(), f'{tag} missing')
            diffs = [h for h in set(ea) & set(eb) if sig(ea[h]) != sig(eb[h])]
            self.assertEqual(diffs, [], f'{tag} changed: {diffs[:5]}')

    def test_xdata_preserved(self):
        for tag, (a, b) in self.d.items():
            for app in ('DEVINSRC', 'DEVINDIM'):
                na = sum(1 for e in a.modelspace() if e.has_xdata(app))
                nb = sum(1 for e in b.modelspace() if e.has_xdata(app))
                self.assertEqual(na, nb, f'{tag} {app}: {na}->{nb}')

    def test_devinpoc_handles_resolve(self):
        n = 0
        for tag, (a, b) in self.d.items():
            for e in b.modelspace():
                if e.has_xdata('DEVINPOC'):
                    for code, v in e.get_xdata('DEVINPOC'):
                        if code == 1005:
                            n += 1
                            self.assertIn(v, b.entitydb, f'{tag} broken handle ref')
        self.assertGreater(n, 0)

    def test_dim_values_unchanged(self):
        for tag, (a, b) in self.d.items():
            da = sorted(round(e.get_measurement() or 0, 1)
                        for e in a.modelspace().query('DIMENSION'))
            db = sorted(round(e.get_measurement() or 0, 1)
                        for e in b.modelspace().query('DIMENSION'))
            self.assertEqual(da, db, f'{tag} DIM changed')

    def test_frozen_layers(self):
        for tag, (a, b) in self.d.items():
            fa = sorted(l.dxf.name for l in a.layers if l.is_frozen())
            fb = sorted(l.dxf.name for l in b.layers if l.is_frozen())
            self.assertEqual(fa, fb, f'{tag} frozen changed')

    def test_shared_axis_coordinates(self):
        """两图 AXIS 线坐标必须完全一致（Gate B1 根因修复）"""
        axes = {}
        for tag, (a, b) in self.d.items():
            axes[tag] = sorted(
                round(e.dxf.start.x if abs(e.dxf.start.x - e.dxf.end.x) < 1
                      else e.dxf.start.y, 1)
                for e in b.modelspace().query('LINE') if e.dxf.get('layer') == 'AXIS')
        self.assertEqual(axes['A102'], axes['A103'],
                         f"轴线不一致: {axes['A102']} vs {axes['A103']}")

    def test_added_entities_only_annotation_layers(self):
        for tag, (a, b) in self.d.items():
            sa = {e.dxf.handle for e in a.modelspace()}
            new = [e for e in b.modelspace() if e.dxf.handle not in sa]
            bad = [e for e in new
                   if e.dxf.get('layer') not in ADDED_LAYERS and e.dxf.get('layer') != '0']
            self.assertEqual(bad, [], f'{tag} unexpected new entities: '
                             f'{[(e.dxftype(), e.dxf.get("layer")) for e in bad][:5]}')


if __name__ == '__main__':
    unittest.main(verbosity=2)
