import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PROJ = ROOT / 'projects' / 'c_type_home'
sys.path.insert(0, str(PROJ / 'scripts'))
import geo_common  # noqa: E402
import validate as task_validate  # noqa: E402

GEO = geo_common.load_geometry()
DIMS = geo_common.load_dimensions()
DIMMAP = json.loads(
    (PROJ / 'data' / 'dimension_map.json').read_text(encoding='utf-8'))
DXF = PROJ / 'cad' / 'C型_原始户型数字化基准图.dxf'
IFC = PROJ / 'ifc' / 'C型_原始户型数字化基准模型.ifc'
FCSTD = PROJ / 'cad' / 'C型_原始户型数字化基准模型.FCStd'
FREECADCMD = '/Applications/FreeCAD.app/Contents/Resources/bin/freecadcmd'

WALLS = {w['id']: w for w in GEO['walls']}
OPENINGS = {o['id']: o for k in ('doors', 'windows') for o in GEO[k]}


def wall_by_id(wid):
    return WALLS.get(wid)


def measure_opening(op):
    a, b = op['opening_along_mm']
    return b - a


class SchemaTests(unittest.TestCase):
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


class ModelMeasurementGateTests(unittest.TestCase):
    """T01-3: real model measurement vs source dimensions."""

    @classmethod
    def setUpClass(cls):
        cls.meas = task_validate.model_measurements(GEO)

    def test_every_mapped_segment_measured(self):
        for r in self.meas['records']:
            self.assertIn('measured_mm', r)
            self.assertIn('error_mm', r)
            self.assertTrue(r['geometry_refs'], r['dim_id'])

    def test_high_confidence_segments_within_1mm(self):
        for r in self.meas['records']:
            if r['confidence'] == 'HIGH':
                self.assertLessEqual(abs(r['error_mm']), 1.0,
                                     f"{r['dim_id']}: {r['error_mm']}mm")

    def test_high_chain_accumulated_within_2mm(self):
        chains = {}
        for r in self.meas['records']:
            chains.setdefault(r['dim_id'].split('#')[0], []).append(r)
        for cid, rs in chains.items():
            acc = sum(r['error_mm'] for r in rs if r['confidence'] == 'HIGH')
            self.assertLessEqual(abs(acc), 2.0, f"{cid}: {acc}mm")

    def test_high_confidence_windows_remeasurable(self):
        expected = {'WIN-N1': 3100, 'WIN-S1': 2200, 'WIN-S2': 2500}
        for w in GEO['windows']:
            if w['id'] in expected:
                self.assertEqual(measure_opening(w), expected[w['id']],
                                 w['id'])

    def test_high_confidence_wall_positions_on_dim_anchors(self):
        anchors = set(GEO['anchors_x_mm'])
        w = wall_by_id('W-EXT-W')
        self.assertTrue(any(abs(w['rect_mm'][0] - a) <= 100 or
                            abs(w['rect_mm'][2] - a) <= 100
                            for a in anchors))


class GeometryValidityTests(unittest.TestCase):
    """Shapely-backed validity via geometry_audit."""

    @classmethod
    def setUpClass(cls):
        cls.audit = task_validate.geometry_audit(GEO)

    def test_audit_passes(self):
        self.assertTrue(self.audit['pass'], self.audit['problems'])

    def test_no_invalid_or_degenerate_polygons(self):
        kinds = {p['kind'] for p in self.audit['problems']}
        self.assertNotIn('invalid_polygon', kinds)
        self.assertNotIn('non_positive_area', kinds)
        self.assertNotIn('duplicate_geometry', kinds)

    def test_no_suspect_wall_overlap(self):
        for ov in self.audit['wall_overlaps']:
            self.assertFalse(ov['suspect'], ov['pair'])

    def test_space_polygons_shapely_valid(self):
        from shapely.geometry import Polygon
        for sp in GEO['spaces']:
            p = Polygon(sp['polygon_mm'])
            self.assertTrue(p.is_valid, sp['id'])
            self.assertGreater(p.area, 0, sp['id'])

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
                lo, hi = (x1, x2) if (x2 - x1) >= (y2 - y1) else (y1, y2)
                self.assertGreaterEqual(a, lo - 500, o['id'])
                self.assertLessEqual(b, hi + 500, o['id'])

    def test_extents_reasonable(self):
        ex = GEO['model_extents_mm']
        self.assertEqual(ex['x'], [1300, 16500])
        self.assertEqual(ex['y'], [-750, 14200])


class DxfTests(unittest.TestCase):
    def test_dxf_reopen_and_units(self):
        import ezdxf
        doc = ezdxf.readfile(DXF)
        self.assertEqual(doc.header.get('$INSUNITS'), 4)
        self.assertGreater(len(list(doc.modelspace())), 0)

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


class FreecadTests(unittest.TestCase):
    """T01-6: reopen FCStd via freecadcmd and verify exact object counts."""

    @classmethod
    def setUpClass(cls):
        cls.have_fc = Path(FREECADCMD).exists()
        if cls.have_fc and FCSTD.exists():
            cls.info = cls._inspect()
        else:
            cls.info = None

    @staticmethod
    def _inspect():
        script = (
            "import FreeCAD as App, json\n"
            f"doc = App.openDocument({str(FCSTD)!r})\n"
            "out = {}\n"
            "for o in doc.Objects:\n"
            "    did = getattr(o, 'DesignID', o.Name)\n"
            "    out[o.Name] = {\n"
            "        'DesignID': did,\n"
            "        'Confidence': getattr(o, 'Confidence', None),\n"
            "        'NeedsFieldVerification': getattr(o, 'NeedsFieldVerification', None),\n"
            "        'HostWallID': getattr(o, 'HostWallID', None)}\n"
            "print('FCINFO=' + json.dumps(out))\n"
        )
        with tempfile.NamedTemporaryFile('w', suffix='.py',
                                         delete=False) as f:
            f.write(script)
            path = f.name
        res = subprocess.run([FREECADCMD, path], capture_output=True,
                             text=True, timeout=300)
        for line in res.stdout.splitlines():
            if line.startswith('FCINFO='):
                return json.loads(line[7:])
        raise RuntimeError('freecadcmd inspection failed: '
                           + res.stdout[-500:] + res.stderr[-500:])

    def test_fcstd_object_counts_match_contract(self):
        if self.info is None:
            self.skipTest('freecadcmd or FCStd unavailable')
        want = (len(GEO['walls']) + len(GEO.get('columns', [])) +
                len(GEO['doors']) + len(GEO['windows']))
        self.assertEqual(len(self.info), want)
        ids = {v['DesignID'] for v in self.info.values()}
        for w in GEO['walls']:
            self.assertIn(w['id'], ids)
        for o in GEO['doors']:
            self.assertIn(o['id'], ids)
        for o in GEO['windows']:
            self.assertIn(o['id'], ids)

    def test_fcstd_provenance_props_present(self):
        if self.info is None:
            self.skipTest('freecadcmd or FCStd unavailable')
        for name, meta in self.info.items():
            self.assertIsNotNone(meta['Confidence'], name)
            self.assertIsNotNone(meta['NeedsFieldVerification'], name)
        for o in GEO['doors'] + GEO['windows']:
            match = [v for v in self.info.values()
                     if v['DesignID'] == o['id']]
            self.assertEqual(match[0]['HostWallID'],
                             o['host_wall_id'], o['id'])


class IfcTests(unittest.TestCase):
    """T01-7: real void/fill relationships and pset verification."""

    @classmethod
    def setUpClass(cls):
        import ifcopenshell
        cls.model = ifcopenshell.open(str(IFC))

    def test_schema_and_hierarchy(self):
        self.assertEqual(self.model.schema, 'IFC4')
        self.assertEqual(len(self.model.by_type('IfcProject')), 1)
        self.assertEqual(len(self.model.by_type('IfcSite')), 1)
        self.assertEqual(len(self.model.by_type('IfcBuilding')), 1)
        self.assertEqual(len(self.model.by_type('IfcBuildingStorey')), 1)

    def test_object_counts(self):
        self.assertEqual(len(self.model.by_type('IfcWall')),
                         len(GEO['walls']))
        self.assertEqual(len(self.model.by_type('IfcSpace')),
                         len(GEO['spaces']))
        self.assertEqual(len(self.model.by_type('IfcDoor')),
                         len(GEO['doors']))
        self.assertEqual(len(self.model.by_type('IfcWindow')),
                         len(GEO['windows']))

    def test_opening_and_relation_counts(self):
        n_open = len(GEO['doors']) + len(GEO['windows'])
        self.assertEqual(len(self.model.by_type('IfcOpeningElement')),
                         n_open)
        self.assertEqual(len(self.model.by_type('IfcRelVoidsElement')),
                         n_open)
        self.assertEqual(len(self.model.by_type('IfcRelFillsElement')),
                         n_open)

    def test_every_opening_has_exactly_one_host_wall(self):
        rels = self.model.by_type('IfcRelVoidsElement')
        by_opening = {}
        for r in rels:
            by_opening.setdefault(r.RelatedOpeningElement.id(),
                                  []).append(r)
        for op in self.model.by_type('IfcOpeningElement'):
            host_rels = by_opening.get(op.id(), [])
            self.assertEqual(len(host_rels), 1, op.Name)
            self.assertTrue(
                host_rels[0].RelatingBuildingElement.is_a('IfcWall'))

    def test_every_fill_linked(self):
        fills = self.model.by_type('IfcRelFillsElement')
        linked = {r.RelatedBuildingElement.id()
                  for r in fills}
        for el in (self.model.by_type('IfcDoor') +
                   self.model.by_type('IfcWindow')):
            self.assertIn(el.id(), linked, el.Name)

    def test_project_pset_field_verified_false(self):
        proj = self.model.by_type('IfcProject')[0]
        props = {}
        for rel in proj.IsDefinedBy:
            pset = rel.RelatingPropertyDefinition
            if getattr(pset, 'Name', None) == 'SourcePlanReconstruction':
                for p in pset.HasProperties:
                    props[p.Name] = getattr(p, 'NominalValue',
                                            None).wrappedValue \
                        if hasattr(p, 'NominalValue') else None
        self.assertEqual(props.get('FieldVerified'), False)
        self.assertEqual(props.get('SourceStatus'),
                         'Source Plan Reconstruction')

    # --- RC2: actual generated-geometry bounding boxes vs contract ---

    def _world_bounds_mm(self, el):
        """AABB of the element's generated geometry in mm (world coords)."""
        import ifcopenshell.geom
        st = ifcopenshell.geom.settings()
        st.set("use-world-coords", True)
        sh = ifcopenshell.geom.create_shape(st, el)
        v = sh.geometry.verts
        xs, ys, zs = v[0::3], v[1::3], v[2::3]
        # ifcopenshell.geom returns file length units converted to meters
        return (min(xs) * 1000, min(ys) * 1000, min(zs) * 1000,
                max(xs) * 1000, max(ys) * 1000, max(zs) * 1000)

    def test_ifc_wall_geometry_bounds_match_contract(self):
        for el in self.model.by_type('IfcWall'):
            w = wall_by_id(el.Name)
            self.assertIsNotNone(w, el.Name)
            x1, y1, x2, y2 = w['rect_mm']
            bx1, by1, _, bx2, by2, _ = self._world_bounds_mm(el)
            for got, want, tag in ((bx1, x1, 'x1'), (by1, y1, 'y1'),
                                   (bx2, x2, 'x2'), (by2, y2, 'y2')):
                self.assertLessEqual(
                    abs(got - want), 1.0,
                    f"{el.Name} {tag}: got {got:.1f} want {want}")

    def test_ifc_opening_geometry_bounds_match_contract(self):
        for op_el in self.model.by_type('IfcOpeningElement'):
            oid = op_el.Name.removesuffix('-OPENING')
            op = OPENINGS[oid]
            host = wall_by_id(op['host_wall_id'])
            x1, y1, x2, y2 = geo_common.opening_world_rect(op, host)
            bx1, by1, _, bx2, by2, _ = self._world_bounds_mm(op_el)
            for got, want, tag in ((bx1, x1, 'x1'), (by1, y1, 'y1'),
                                   (bx2, x2, 'x2'), (by2, y2, 'y2')):
                self.assertLessEqual(
                    abs(got - want), 1.0,
                    f"{op_el.Name} {tag}: got {got:.1f} want {want}")

    def test_ifc_door_window_panels_and_pset(self):
        """RC2: fills carry visualization-only panel geometry + flags."""
        def pset_props(el):
            props = {}
            for rel in el.IsDefinedBy:
                ps = rel.RelatingPropertyDefinition
                if getattr(ps, 'Name', None) == 'SourcePlanReconstruction':
                    for p in ps.HasProperties:
                        props[p.Name] = getattr(
                            p, 'NominalValue', None).wrappedValue \
                            if hasattr(p, 'NominalValue') else None
            return props
        for el in (self.model.by_type('IfcDoor') +
                   self.model.by_type('IfcWindow')):
            self.assertIsNotNone(el.Representation, el.Name)
            props = pset_props(el)
            self.assertEqual(props.get('VisualizationOnly'), True, el.Name)
            self.assertEqual(props.get('HeightIsSourceData'), False,
                             el.Name)
            # panel must sit inside its opening XY span (opening is the
            # full wall thickness; panel is ~40mm centered)
            op_el = next(o for o in self.model.by_type('IfcOpeningElement')
                         if o.Name == el.Name + '-OPENING')
            ob = self._world_bounds_mm(op_el)
            fb = self._world_bounds_mm(el)
            self.assertGreaterEqual(fb[0], ob[0] - 1, el.Name)
            self.assertGreaterEqual(fb[1], ob[1] - 1, el.Name)
            self.assertLessEqual(fb[3], ob[3] + 1, el.Name)
            self.assertLessEqual(fb[4], ob[4] + 1, el.Name)


class ProvenanceTests(unittest.TestCase):
    def test_low_confidence_flagged(self):
        unresolved = PROJ / 'qc' / 'unresolved_issues.md'
        self.assertTrue(unresolved.exists())
        for _, o in geo_common.all_objects(GEO):
            if o.get('confidence') in ('LOW', 'UNKNOWN'):
                self.assertTrue(
                    o.get('needs_field_verification', True) or
                    'note' in o, o['id'])

    def test_provenance_spot_check(self):
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
