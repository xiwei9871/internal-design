import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'construction'))
import cad_common as cad


class ServiceDetailTests(unittest.TestCase):
    def test_east_corridor_view_has_north_fridge_on_right(self):
        from build_a401_elevations import service_elevation
        from build_a403_service_wall import build_document
        a=cad.new_doc();service_elevation(a.modelspace(),0,0)
        for doc in (a,build_document()):
            boxes=list(doc.modelspace().query('LWPOLYLINE[layer=="A-FIXT"]'))
            widths=lambda r:max(p[0] for p in r.get_points())-min(p[0] for p in r.get_points())
            center=lambda r:(max(p[0] for p in r.get_points())+min(p[0] for p in r.get_points()))/2
            fridge=next(r for r in boxes if abs(widths(r)-840)<.01)
            washer=next(r for r in boxes if abs(widths(r)-598)<.01)
            self.assertGreater(center(fridge),center(washer))

    def test_detail_has_shared_bay_dimensions_and_real_views(self):
        self.assertTrue((Path(cad.__file__).parent/'build_a403_service_wall.py').exists())
        from build_a403_service_wall import build_document
        doc=build_document()
        self.assertGreaterEqual(len(doc.modelspace().query('DIMENSION')),10)
        dimensions=[d.get_measurement() for d in doc.modelspace().query('DIMENSION')]
        for bay in cad.DATA['design']['service_wall']['bays']:
            self.assertTrue(any(abs(d-bay['width_mm'])<.01 for d in dimensions))
        self.assertTrue(any(abs(d-2400)<.01 for d in dimensions))
        texts=[e.dxf.text for e in doc.modelspace().query('TEXT')]
        self.assertTrue(any('SKU' in t and '待' in t for t in texts))
        self.assertEqual((len(doc.audit().errors),len(doc.audit().fixes)),(0,0))


if __name__ == '__main__':
    unittest.main()
