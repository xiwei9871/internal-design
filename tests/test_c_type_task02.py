"""Task 02 — semantics & constraints gate tests (T02-A .. T02-O)."""
import hashlib
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PROJ = ROOT / 'projects' / 'c_type_home'
sys.path.insert(0, str(PROJ / 'scripts'))
import geo_common  # noqa: E402

GEO = geo_common.load_geometry()
SEM = PROJ / 'semantics'
QC = PROJ / 'qc'
IFC_T01 = PROJ / 'ifc' / 'C型_原始户型数字化基准模型.ifc'
IFC_T02 = PROJ / 'ifc' / 'C型_现状语义约束模型.ifc'

SPACE_SEM = json.loads((SEM / 'space_semantics.json').read_text('utf-8'))
ELEM_SEM = json.loads((SEM / 'element_semantics.json').read_text('utf-8'))
GRAPH = json.loads((SEM / 'adjacency_graph.json').read_text('utf-8'))
CONS = json.loads((SEM / 'constraint_register.json').read_text('utf-8'))[
    'constraints']
SCHED = json.loads((SEM / 'room_schedule.json').read_text('utf-8'))
BASELINE = json.loads(
    (SEM / 'task01_baseline_hashes.json').read_text('utf-8'))

GSPACE_IDS = {s['id'] for s in GEO['spaces']}
NODE_IDS = {n['id'] for n in GRAPH['nodes']}


def sha256(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def pset_props(el, name):
    out = {}
    for rel in el.IsDefinedBy or []:
        ps = rel.RelatingPropertyDefinition
        if getattr(ps, 'Name', None) == name:
            for p in ps.HasProperties:
                v = getattr(p, 'NominalValue', None)
                out[p.Name] = v.wrappedValue if v is not None else None
    return out


class T02A_Task01Immutability(unittest.TestCase):
    def test_frozen_hashes_unchanged(self):
        for rel, want in BASELINE['frozen_files'].items():
            self.assertEqual(sha256(PROJ / rel), want,
                             f'{rel} mutated — Task01 is frozen')


class T02BC_SpaceSemantics(unittest.TestCase):
    def test_every_geometry_space_has_semantic_record(self):
        sem_ids = [s['space_id'] for s in SPACE_SEM['spaces']]
        self.assertEqual(sorted(sem_ids), sorted(GSPACE_IDS))

    def test_semantic_space_references_valid_geometry(self):
        for s in SPACE_SEM['spaces']:
            self.assertIn(s['geometry_ref'], GSPACE_IDS, s['space_id'])

    def test_duplicate_bedroom_labels_keep_source_label(self):
        beds = [s for s in SPACE_SEM['spaces']
                if s['source_label_zh'] == '卧室']
        self.assertEqual(len(beds), 2)
        self.assertNotEqual(beds[0]['space_id'], beds[1]['space_id'])
        for b in beds:
            self.assertNotIn(b['canonical_role'],
                             ('child_room', 'elder_room', 'guest_room'))

    def test_space_record_fields(self):
        req = {'space_id', 'geometry_ref', 'source_label_zh',
               'canonical_role', 'area_m2', 'perimeter_m',
               'source_confidence', 'touches_exterior_envelope',
               'exterior_openings', 'wet_service_class',
               'design_change_status', 'field_verification_required'}
        for s in SPACE_SEM['spaces']:
            self.assertTrue(req.issubset(s), s['space_id'])
            self.assertIn(s['wet_service_class'],
                          ('DRY', 'WET', 'SERVICE', 'SEMI_WET', 'UNKNOWN'))


class T02DE_ElementSpaceBinding(unittest.TestCase):
    def test_doors_resolve_or_unresolved(self):
        valid = NODE_IDS | {'UNRESOLVED'}
        self.assertEqual(len(ELEM_SEM['doors']), len(GEO['doors']))
        for d in ELEM_SEM['doors']:
            self.assertIn(d['side_a_space'], valid, d['element_id'])
            self.assertIn(d['side_b_space'], valid, d['element_id'])

    def test_windows_resolve_or_unresolved(self):
        valid = GSPACE_IDS | {'UNRESOLVED'}
        self.assertEqual(len(ELEM_SEM['windows']), len(GEO['windows']))
        for w in ELEM_SEM['windows']:
            for sid in w['interior_space_ids']:
                self.assertIn(sid, valid, w['element_id'])

    def test_d13_remains_sliding_candidate(self):
        d13 = next(d for d in ELEM_SEM['doors']
                   if d['element_id'] == 'D-13')
        self.assertEqual(d13['door_type'], 'sliding_door_candidate')

    def test_d01_entry_reaches_external_node(self):
        d01 = next(d for d in ELEM_SEM['doors']
                   if d['element_id'] == 'D-01')
        self.assertIn('EXTERNAL_COMMON_AREA',
                      (d01['side_a_space'], d01['side_b_space']))


class T02F_StructuralUnknown(unittest.TestCase):
    def test_no_structural_inference(self):
        for grp in ('walls', 'columns', 'ac_bays'):
            for e in ELEM_SEM[grp]:
                self.assertEqual(e.get('structural_role'), 'UNKNOWN',
                                 e['element_id'])
        for s in SPACE_SEM['spaces']:
            self.assertEqual(s['design_change_status'], 'UNKNOWN')


class T02GH_ConstraintRegister(unittest.TestCase):
    def test_all_task01_issues_mapped(self):
        mapped = {c.get('source_issue_ref') for c in CONS}
        for iid in GEO['unresolved_issue_ids']:
            self.assertIn(iid, mapped)
        # issues documented in unresolved_issues.md beyond the geo list
        for iid in ('ISSUE-011', 'ISSUE-012', 'ISSUE-013'):
            self.assertIn(iid, mapped)

    def test_constraint_completeness(self):
        req = {'constraint_id', 'category', 'subject_refs', 'description',
               'evidence', 'confidence', 'severity_for_future_design',
               'verification_required', 'verification_method', 'status'}
        sevs = {'BLOCKING', 'HIGH', 'MEDIUM', 'LOW', 'INFORMATIONAL'}
        for c in CONS:
            self.assertTrue(req.issubset(c), c['constraint_id'])
            self.assertIn(c['severity_for_future_design'], sevs)
            self.assertTrue(c['evidence'], c['constraint_id'])

    def test_resolved_issues_not_active_blockers(self):
        for c in CONS:
            if c.get('source_issue_ref') in ('ISSUE-002', 'ISSUE-007',
                                             'ISSUE-008'):
                self.assertNotEqual(c['status'], 'ACTIVE',
                                    c['constraint_id'])


class T02IJ_Graph(unittest.TestCase):
    def test_graph_node_refs_valid(self):
        for e in GRAPH['adjacency_edges'] + GRAPH['circulation_edges']:
            self.assertIn(e['space_a'], NODE_IDS)
            self.assertIn(e['space_b'], NODE_IDS)

    def test_circulation_components(self):
        # all spaces reachable (kitchen only via balcony is an
        # observation, not a disconnect)
        self.assertEqual(GRAPH['component_count'], 1)
        self.assertEqual(len(GRAPH['nodes']),
                         len(GSPACE_IDS) + 2)  # +external +unmodeled zone

    def test_adjacency_differs_from_circulation(self):
        self.assertGreater(len(GRAPH['adjacency_edges']),
                           len({(e['space_a'], e['space_b'])
                                for e in GRAPH['circulation_edges']}))


class T02K_RoomSchedule(unittest.TestCase):
    def test_areas_match_geometry(self):
        from shapely.geometry import Polygon
        gpolys = {s['id']: Polygon(s['polygon_mm']) for s in GEO['spaces']}
        for room in SCHED['rooms']:
            want = round(gpolys[room['space_id']].area / 1e6, 2)
            self.assertEqual(room['area_m2'], want, room['space_id'])


class T02LMN_IFC(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        import ifcopenshell
        cls.m2 = ifcopenshell.open(str(IFC_T02))

    def test_semantic_psets_queryable(self):
        spaces = self.m2.by_type('IfcSpace')
        self.assertEqual(len(spaces), len(GSPACE_IDS))
        for el in spaces:
            props = pset_props(el, 'Pset_Task02SpaceSemantics')
            for k in ('SpaceID', 'SourceLabelZh', 'CanonicalRole',
                      'WetServiceClass', 'TouchesExterior'):
                self.assertIn(k, props, el.Name)
        for el in self.m2.by_type('IfcWall'):
            props = pset_props(el, 'Pset_Task02ElementSemantics')
            for k in ('ExistingLocationClass', 'StructuralRole',
                      'VerificationBeforeModification'):
                self.assertIn(k, props, el.Name)
            self.assertEqual(props['StructuralRole'], 'UNKNOWN')

    def test_ifc_geometry_unchanged(self):
        import ifcopenshell
        import ifcopenshell.geom
        m1 = ifcopenshell.open(str(IFC_T01))

        def bounds(model, name_index):
            st = ifcopenshell.geom.settings()
            st.set('use-world-coords', True)
            out = {}
            for el in model.by_type(name_index):
                sh = ifcopenshell.geom.create_shape(st, el)
                v = sh.geometry.verts
                xs, ys, zs = v[0::3], v[1::3], v[2::3]
                out[el.Name] = (min(xs) * 1000, min(ys) * 1000,
                                min(zs) * 1000, max(xs) * 1000,
                                max(ys) * 1000, max(zs) * 1000)
            return out
        for typ in ('IfcWall', 'IfcColumn', 'IfcOpeningElement',
                    'IfcDoor', 'IfcWindow'):
            b1 = bounds(m1, typ)
            b2 = bounds(self.m2, typ)
            self.assertEqual(set(b1), set(b2), typ)
            for name in b1:
                for x, y in zip(b1[name], b2[name]):
                    self.assertLessEqual(
                        abs(x - y), 0.1, f'{typ}:{name} moved')

    def test_no_furniture_or_design_objects(self):
        for typ in ('IfcFurniture', 'IfcSanitaryTerminal',
                    'IfcDistributionFlowElement', 'IfcLightFixture'):
            self.assertEqual(len(self.m2.by_type(typ)), 0, typ)
        # semantics files must not introduce furniture objects either
        for s in SPACE_SEM['spaces']:
            self.assertNotIn('furniture', json.dumps(s).lower())


if __name__ == '__main__':
    unittest.main()
