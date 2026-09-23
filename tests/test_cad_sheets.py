import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'construction'))
import cad_common as cad


class CadSheetTests(unittest.TestCase):
    def test_bed_pillows_follow_shared_east_head_axis(self):
        doc=cad.new_doc();cad.draw_furniture(doc.modelspace(),labels=False)
        for i,f in enumerate(cad.DATA['furniture'],1):
            if f['kind']!='bed': continue
            self.assertEqual(f['head_axis'],'+X')
            block=doc.blocks[f'FURN_{i:03d}']
            pillows=list(block.query('LWPOLYLINE'))[3:5]
            self.assertEqual(len(pillows),2)
            for pillow in pillows:
                center=sum(p[0] for p in pillow.get_points())/4
                self.assertGreater(center,f['rect'][2]*cad.MM*.7)

    def test_furniture_has_reusable_symbols_not_only_envelopes(self):
        doc = cad.new_doc()
        cad.draw_furniture(doc.modelspace(), labels=False)
        self.assertGreater(len(doc.modelspace().query('INSERT')), 20)
        self.assertTrue(any(len(block) > 3 for block in doc.blocks if block.name.startswith('FURN')))

    def test_plan_has_positioning_dimensions(self):
        self.assertTrue(hasattr(cad, 'draw_position_dims'))
        doc = cad.new_doc()
        cad.draw_position_dims(doc.modelspace())
        self.assertGreaterEqual(len(doc.modelspace().query('DIMENSION')), 12)
        desk=next(f for f in cad.DATA['furniture'] if f['id']=='FURN-039')
        self.assertTrue(any(abs(d.get_measurement()-desk['rect'][2]*cad.MM)<.01
                            for d in doc.modelspace().query('DIMENSION')))

    def test_paper_layout_is_a2_at_exact_scale(self):
        self.assertTrue(hasattr(cad, 'make_paper_layout'))
        doc = cad.new_doc()
        cad.draw_walls(doc.modelspace())
        paper = cad.make_paper_layout(doc, 'A101', '平面布置图', 50)
        self.assertEqual((paper.dxf.paper_width, paper.dxf.paper_height), (594, 420))
        viewport = [v for v in paper.query('VIEWPORT') if v.dxf.status >= 2][0]
        self.assertAlmostEqual(viewport.dxf.view_height / viewport.dxf.height, 50)
        self.assertEqual(doc.units, 4)
        self.assertEqual(len(doc.audit().fixes), 0)

    def test_service_wall_uses_shared_widths_and_appliance_heights(self):
        import build_a401_elevations as elevations
        self.assertTrue(hasattr(elevations, 'service_elevation'))
        doc = cad.new_doc()
        elevations.service_elevation(doc.modelspace(), 0, 0)
        rects = list(doc.modelspace().query('LWPOLYLINE[layer=="A-FIXT"]'))
        sizes = {(round(max(p[0] for p in r.get_points()) - min(p[0] for p in r.get_points())),
                  round(max(p[1] for p in r.get_points()) - min(p[1] for p in r.get_points()))) for r in rects}
        self.assertIn((595, 595), sizes)
        self.assertIn((598, 845), sizes)
        self.assertIn((840, 1950), sizes)

    def test_schedule_does_not_claim_structural_opening(self):
        import build_a501_schedules as schedules
        self.assertTrue(hasattr(schedules, 'door_rows'))
        rows = schedules.door_rows()
        self.assertIn('参考宽mm', rows[0])
        self.assertIn('暗藏推拉门', rows[-1])
        self.assertIn('洞口/暗藏侧待复核', rows[-1])

    def test_child_study_preserves_low_bookcase_and_plan_gap(self):
        import build_a401_elevations as elevations
        self.assertTrue(hasattr(elevations,'child_study_elevation'))
        doc=cad.new_doc()
        elevations.child_study_elevation(doc.modelspace(),0,0)
        rects=list(doc.modelspace().query('LWPOLYLINE[layer=="A-FURN"]'))
        heights=[max(p[1] for p in r.get_points())-min(p[1] for p in r.get_points()) for r in rects]
        self.assertIn(1100,heights)
        self.assertNotIn(2600,heights)
        self.assertGreater(min(p[0] for p in rects[1].get_points()),max(p[0] for p in rects[0].get_points()))

    def test_ceiling_heights_use_shared_dry_wet_contract(self):
        import build_a301_ceiling as ceiling
        self.assertTrue(hasattr(ceiling,'ceiling_height'))
        for room in ('厨房','主卫','次卫'):
            self.assertEqual(ceiling.ceiling_height(room),cad.DATA['design']['ceiling_mm']['wet'])
        for room in ('过道','玄关','主卧','客餐厅'):
            self.assertEqual(ceiling.ceiling_height(room),cad.DATA['design']['ceiling_mm']['dry'])


if __name__ == '__main__':
    unittest.main()
