import sys
import unittest
from pathlib import Path

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'construction'))
import cad_common as cad
import build_a401_elevations as elevations


class KitchenElevationTests(unittest.TestCase):
    def draw(self,side):
        self.assertTrue(hasattr(elevations,'kitchen_elevation'))
        doc=cad.new_doc()
        elevations.kitchen_elevation(doc.modelspace(),0,0,side)
        return doc.modelspace()

    def test_all_kitchen_elevations_use_wet_ceiling(self):
        for side in ('north','west','east'):
            msp=self.draw(side)
            self.assertEqual(msp.query('LINE[layer=="A-CEIL"]')[0].dxf.start.y,2400)

    def test_north_window_keeps_shared_extents_and_flags_sill_conflict(self):
        msp=self.draw('north')
        window=msp.query('LWPOLYLINE[layer=="A-WINDOW"]')[0]
        points=window.get_points()
        self.assertAlmostEqual(min(p[0] for p in points),(515-415)*cad.MM)
        self.assertAlmostEqual(max(p[0] for p in points),(790-415)*cad.MM)
        self.assertEqual((min(p[1] for p in points),max(p[1] for p in points)),(850,2100))
        self.assertTrue(any('窗台850' in t.dxf.text and '待' in t.dxf.text for t in msp.query('TEXT')))

    def test_hob_projects_exact_source_x_span_at_counter_height(self):
        msp=self.draw('north')
        line=msp.query('LINE[layer=="A-FIXT"]')[0]
        self.assertAlmostEqual(line.dxf.start.x,(530-415)*cad.MM)
        self.assertAlmostEqual(line.dxf.end.x,(530+85-415)*cad.MM)
        self.assertEqual(line.dxf.start.y,900)

    def test_west_sink_projects_y_reversed_from_south_edge(self):
        msp=self.draw('west')
        line=msp.query('LINE[layer=="A-FIXT"]')[0]
        self.assertAlmostEqual(line.dxf.start.x,(310-238-54)*cad.MM)
        self.assertAlmostEqual(line.dxf.end.x,(310-238)*cad.MM)
        self.assertEqual(line.dxf.start.y,900)

    def test_east_window_keeps_shared_vertical_and_source_span(self):
        msp=self.draw('east')
        points=msp.query('LWPOLYLINE[layer=="A-WINDOW"]')[0].get_points()
        self.assertAlmostEqual(max(p[0] for p in points)-min(p[0] for p in points),153*cad.MM)
        self.assertEqual((min(p[1] for p in points),max(p[1] for p in points)),(850,2100))


if __name__=='__main__':
    unittest.main()
