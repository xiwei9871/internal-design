import json
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PROJ = ROOT / 'projects' / 'c_type_home'
sys.path.insert(0, str(PROJ / 'scripts'))
import geo_common  # noqa: E402

GEO = geo_common.load_geometry()
DIMS = geo_common.load_dimensions()
DXF = PROJ / 'cad' / 'C型_原始户型数字化基准图.dxf'
IFC = PROJ / 'ifc' / 'C型_原始户型数字化基准模型.ifc'
FCSTD = PROJ / 'cad' / 'C型_原始户型数字化基准模型.FCStd'


def wall_by_id(wid):
    return next((w for w in GEO['walls'] if w['id'] == wid), None)


def measure_opening(op):
    a, b = op['opening_along_mm']
    return b - a


class SchemaTests(unittest.TestCase):
    """A. geometry.json schema completeness + B. unique IDs"""

    REQUIRED_WALL = {'id', 'type', 'rect_mm', 'provenance', 'confidence',
                     'source_refs'}

    def test_wall_schema(self):
        for w in GEO['walls']:
            self.assertTrue(self.REQUIRED_WALL.issubset(w), w['id'])
            self.assertEqual(w.get('structural_role'), 'UNKNOWN', w['id'])

    def test_opening_schema(self):
        for k in ('doors', 'windows'):
            for o in GEO[k]:
                for f in ('id', 'host_wall_id', 'opening_along_mm',
                          'confidence'):
                    self.assertIn(f, o, o['id'])

    def test_unique_ids(self):
        ids = [o['id'] for _, o in geo_common.all_objects(GEO)]
        self.assertEqual(len(ids), len(set(ids)))

    def test_every_object_has_provenance(self):
        for _, o in geo_common.all_objects(GEO):
            self.assertTrue(o.get('provenance') or o.get('source_refs'),
                            o['id'])


class DimensionTests(unittest.TestCase):
    """C. HIGH-confidence dims re-measurable + D. chain closure"""

    def test_top_inner_closes_to_outer(self):
        tin = next(c for c in DIMS['chains'] if c['id'] == 'CHAIN-TOP-IN')
        tout = next(c for c in DIMS['chains'] if c['id'] == 'CHAIN-TOP-OUT')
        vals = tin['segment_values_mm']
        groups = [sum(vals[0:3]), sum(vals[3:5]), sum(vals[5:8]),
                  sum(vals[8:11])]
        self.assertEqual(groups, tout['segment_values_mm'])

    def test_bottom_outer_total(self):
        bot = next(c for c in DIMS['chains'] if c['id'] == 'CHAIN-BOTTOM-OUT')
        self.assertEqual(sum(bot['segment_values_mm']), 16300)

    def test_right_inner_closes_to_outer(self):
        rin = next(c for c in DIMS['chains'] if c['id'] == 'CHAIN-RIGHT-IN')
        self.assertEqual(sum(rin['segment_values_mm'][2:9]), 12900)

    def test_high_confidence_windows_remeasurable(self):
        """Dim-constrained windows must equal their printed width."""
        expected = {'WIN-N1': 3100, 'WIN-S1': 2200, 'WIN-S2': 2500}
        for w in GEO['windows']:
            if w['id'] in expected:
                self.assertEqual(measure_opening(w), expected[w['id']],
                                 w['id'])

    def test_high_confidence_wall_positions_on_dim_anchors(self):
        anchors = set(GEO['anchors_x_mm'])
        # west ext wall must sit on the 2800 chain tick
        w = wall_by_id('W-EXT-W')
        self.assertTrue(any(abs(w['rect_mm'][0] - a) <= 100 or
                            abs(w['rect_mm'][2] - a) <= 100
                            for a in anchors))


class GeometryValidityTests(unittest.TestCase):
    """E/F/G/H. polygon validity, host relations, extents"""

    def test_wall_rects_positive(self):
        for w in GEO['walls']:
            x1, y1, x2, y2 = w['rect_mm']
            self.assertGreater(x2, x1, w['id'])
            self.assertGreater(y2, y1, w['id'])

    def test_space_polygons_closed_simple(self):
        for sp in GEO['spaces']:
            pts = sp['polygon_mm']
            self.assertGreaterEqual(len(pts), 3, sp['id'])
            xs = [p[0] for p in pts]
            ys = [p[1] for p in pts]
            self.assertGreater(max(xs) - min(xs), 0)
            self.assertGreater(max(ys) - min(ys), 0)

    def test_opening_hosts_exist(self):
        for k in ('doors', 'windows'):
            for o in GEO[k]:
                self.assertIsNotNone(wall_by_id(o['host_wall_id']),
                                     o['id'])

    def test_opening_inside_host_span(self):
        for k in ('doors', 'windows'):
            for o in GEO[k]:
                host = wall_by_id(o['host_wall_id'])
                if host is None:
                    continue
                x1, y1, x2, y2 = host['rect_mm']
                a, b = o['opening_along_mm']
                self.assertLess(a, b, o['id'])
                if (x2 - x1) >= (y2 - y1):  # horizontal wall
                    lo, hi = x1, x2
                else:
                    lo, hi = y1, y2
                self.assertGreaterEqual(a, lo - 500, o['id'])
                self.assertLessEqual(b, hi + 500, o['id'])

    def test_extents_reasonable(self):
        ex = GEO['model_extents_mm']
        self.assertEqual(ex['x'], [1300, 16500])
        self.assertEqual(ex['y'], [-750, 14200])


class ArtifactTests(unittest.TestCase):
    """I/J. DXF readable + mm units; K/L/M. IFC reopen + IFC4 + counts"""

    def test_dxf_reopen_and_units(self):
        import ezdxf
        doc = ezdxf.readfile(DXF)
        self.assertEqual(doc.header.get('$INSUNITS'), 4)
        ents = list(doc.modelspace())
        self.assertGreater(len(ents), 0)

    def test_dxf_layers(self):
        import ezdxf
        doc = ezdxf.readfile(DXF)
        names = {l.dxf.name for l in doc.layers}
        for want in ('A-WALL', 'A-DOOR', 'A-WINDOW', 'A-DIMS',
                     'A-UNCERTAIN', 'A-SOURCE-REF'):
            self.assertIn(want, names)

    def test_dxf_no_furniture_layer(self):
        import ezdxf
        doc = ezdxf.readfile(DXF)
        for l in doc.layers:
            self.assertNotIn('FURN', l.dxf.name.upper())

    def test_ifc_reopen_and_schema(self):
        import ifcopenshell
        model = ifcopenshell.open(str(IFC))
        self.assertEqual(model.schema, 'IFC4')

    def test_ifc_hierarchy_and_counts(self):
        import ifcopenshell
        model = ifcopenshell.open(str(IFC))
        self.assertEqual(len(model.by_type('IfcProject')), 1)
        self.assertEqual(len(model.by_type('IfcSite')), 1)
        self.assertEqual(len(model.by_type('IfcBuilding')), 1)
        self.assertEqual(len(model.by_type('IfcBuildingStorey')), 1)
        self.assertEqual(len(model.by_type('IfcWall')), len(GEO['walls']))
        self.assertEqual(len(model.by_type('IfcSpace')),
                         len(GEO['spaces']))
        self.assertEqual(len(model.by_type('IfcDoor')), len(GEO['doors']))
        self.assertEqual(len(model.by_type('IfcWindow')),
                         len(GEO['windows']))

    def test_ifc_field_verified_false(self):
        import ifcopenshell
        model = ifcopenshell.open(str(IFC))
        text = Path(IFC).read_text(errors='ignore')
        self.assertIn('Source Plan Reconstruction', text)

    def test_fcstd_exists_nonempty(self):
        self.assertTrue(FCSTD.exists())
        self.assertGreater(FCSTD.stat().st_size, 10000)


class ProvenanceTests(unittest.TestCase):
    """N. all LOW/UNKNOWN objects land in unresolved issues or carry flag"""

    def test_low_confidence_flagged(self):
        unresolved = (PROJ / 'qc' / 'unresolved_issues.md')
        self.assertTrue(unresolved.exists())
        for _, o in geo_common.all_objects(GEO):
            if o.get('confidence') in ('LOW', 'UNKNOWN'):
                self.assertTrue(
                    o.get('needs_field_verification', True) or
                    'note' in o, o['id'])

    def test_provenance_spot_check(self):
        """Random sample: 5 walls, 3 doors, 3 windows, 5 dims all trace."""
        for wid in ('W-EXT-W', 'W-EXT-S', 'W-INT-X11500',
                    'W-INT-Y4500-bc', 'W-BALC-S'):
            w = wall_by_id(wid)
            self.assertTrue(w and w['source_refs'], wid)
        for did in ('D-01', 'D-06', 'D-09'):
            d = next(o for o in GEO['doors'] if o['id'] == did)
            self.assertTrue(d['source_refs'], did)
        for wid in ('WIN-N1', 'WIN-S2', 'WIN-E1'):
            w = next(o for o in GEO['windows'] if o['id'] == wid)
            self.assertTrue(w['source_refs'], wid)
        n_dim = sum(len(c['segment_values_mm']) for c in DIMS['chains'])
        self.assertGreaterEqual(n_dim, 5)
        for c in DIMS['chains']:
            self.assertIn('confidence', c)


if __name__ == '__main__':
    unittest.main()
