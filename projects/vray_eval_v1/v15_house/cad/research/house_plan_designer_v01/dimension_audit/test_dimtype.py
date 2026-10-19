#!/usr/bin/env python3
"""dimtype 分类/测量方法单元测试 — Gate 任务A。
防止再次把 bit5(32)=块参照标志误当 ordinate 类型。
"""
import sys, math, types, unittest
sys.path.insert(0, '/Users/xiwei/interior_design/projects/vray_eval_v1/v15_house/cad/research/house_plan_designer_v01/dimension_audit')
from mini_dim_adapter import dim_base, is_ordinate, geometric_measure, BASE_NAMES


def fake_dim(dimtype, angle=0.0, p2=(0, 0, 0), p3=(0, 0, 0)):
    """构造最小 DIMENSION 替身（dxf 属性字典）"""
    class DXF:
        def __init__(self, d): self._d = d
        def get(self, k, default=None):
            v = self._d.get(k, default)
            if isinstance(v, tuple):
                return types.SimpleNamespace(x=v[0], y=v[1], z=v[2])
            return v
    e = types.SimpleNamespace()
    e.dxf = DXF({'dimtype': dimtype, 'angle': angle, 'defpoint2': p2, 'defpoint3': p3})
    return e


class TestDimtype(unittest.TestCase):
    def test_base_extraction(self):
        # bit5(32)=块参照标志 不是类型位
        for dt, base in [(0, 0), (1, 1), (2, 2), (6, 6), (7, 7),
                         (32, 0), (33, 1), (38, 6), (39, 7),
                         (70, 6), (134, 6), (128, 0), (16, 0), (48, 0), (96, 0), (160, 0)]:
            self.assertEqual(dim_base(dt), base, f'dimtype={dt}')

    def test_ordinate_flag(self):
        # 只有基础类型==6才是 ordinate；32 标志不改变类型
        self.assertFalse(is_ordinate(32))   # 之前 bug: dimtype&32 → 误判 ordinate
        self.assertFalse(is_ordinate(33))   # aligned+块标志
        self.assertTrue(is_ordinate(38))    # ordinate+块标志
        self.assertTrue(is_ordinate(70))    # ordinate+bit6
        self.assertTrue(is_ordinate(134))   # ordinate+bit7(纸空间)
        self.assertTrue(is_ordinate(6))

    def test_measured_file_all_linear(self):
        """measured_working 的 18 条全部 dimtype=32 → base0 线性旋转，非 ordinate"""
        self.assertEqual(BASE_NAMES[dim_base(32)], 'linear')
        self.assertFalse(is_ordinate(32))

    def test_linear_projection(self):
        # angle=90 的线性标注：投影在 Y 方向
        e = fake_dim(32, angle=90.0, p2=(1314571, -285457, 0), p3=(1314371, -289957, 0))
        g, m = geometric_measure(e)
        self.assertAlmostEqual(g, 4500.0, places=3)
        self.assertIn('linear', m)
        # angle=0 的线性标注：投影在 X 方向
        e = fake_dim(0, angle=0.0, p2=(0, 0, 0), p3=(3600, 200, 0))
        g, m = geometric_measure(e)
        self.assertAlmostEqual(g, 3600.0, places=3)

    def test_aligned_distance(self):
        e = fake_dim(33, p2=(0, 0, 0), p3=(3000, 4000, 0))
        g, m = geometric_measure(e)
        self.assertAlmostEqual(g, 5000.0, places=3)
        self.assertIn('aligned', m)

    def test_ordinate_no_span(self):
        e = fake_dim(38, p2=(100, 0, 0), p3=(5000, 0, 0))
        g, m = geometric_measure(e)
        self.assertIsNone(g)
        self.assertEqual(m, 'ordinate')


if __name__ == '__main__':
    unittest.main(verbosity=2)
