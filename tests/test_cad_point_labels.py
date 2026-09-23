import sys
import unittest
from pathlib import Path
from shapely.geometry import Polygon,box
from shapely.ops import unary_union

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'construction'))
import cad_common as cad
from build_a302_electrical import POINTS


class PointLabelTests(unittest.TestCase):
    def test_electrical_labels_are_clear_of_walls_and_each_other(self):
        self.assertTrue(hasattr(cad,'draw_point_labels'))
        doc=cad.new_doc();cad.draw_walls(doc.modelspace());cad.draw_room_labels(doc.modelspace())
        records=[(f'E{i:02d}',px,py) for i,(px,py,*_) in enumerate(POINTS,1)]
        placed=cad.draw_point_labels(doc.modelspace(),records,'A-ELEC')
        self.assertEqual(len(placed),40)
        walls=unary_union([Polygon([cad.m(*p) for p in w['polygon']]) for w in cad.DATA['walls']])
        boxes=[box(*p['bbox']) for p in placed]
        for i,rect in enumerate(boxes):
            self.assertEqual(rect.intersection(walls).area,0)
            for other in boxes[i+1:]: self.assertEqual(rect.intersection(other).area,0)
        self.assertEqual(len(doc.modelspace().query('SOLID[layer=="A-MASK"]')),40)


if __name__=='__main__':
    unittest.main()
