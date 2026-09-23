import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'construction'))
import cad_common as cad
from build_a401_elevations import elem, frame
from build_a402_details import band


class CadGeometryTests(unittest.TestCase):
    def test_rectangles_keep_height_when_shifted(self):
        for draw in (elem, band):
            for y in (-800, 450, 1950):
                with self.subTest(draw=draw.__name__, y=y):
                    doc = cad.new_doc()
                    draw(doc.modelspace(), 120, -40, 20, y, 600, 75, '')
                    pts = list(doc.modelspace().query('LWPOLYLINE'))[0].get_points()
                    self.assertEqual([p[1] for p in pts], [-40+y, -40+y, -40+y+75, -40+y+75])

    def test_ceiling_line_is_actual_finished_height(self):
        doc = cad.new_doc()
        frame(doc.modelspace(), 0, 500, 3000, 'test', h=2600)
        lines = doc.modelspace().query('LINE[layer=="A-CEIL"]')
        self.assertEqual(lines[0].dxf.start.y, 3100)

    def test_used_linetypes_audit_cleanly(self):
        doc = cad.new_doc()
        elem(doc.modelspace(), 0, 0, 0, 500, 600, 50, '', dashed=True)
        self.assertIn('DASHED', doc.linetypes)
        self.assertIn('CENTER', doc.linetypes)
        audit = doc.audit()
        self.assertEqual((len(audit.errors), len(audit.fixes)), (0, 0))

    def test_shared_sliding_door_has_no_swing_arc(self):
        doc = cad.new_doc()
        cad.draw_doors(doc.modelspace())
        self.assertEqual(len(doc.modelspace().query('ARC')), 6)
        self.assertEqual(cad.DATA['doors'][-1]['type'], 'pocket_sliding')
        self.assertGreater(len(doc.modelspace().query('LWPOLYLINE[layer=="A-DOOR"]')), 0)


if __name__ == '__main__':
    unittest.main()
