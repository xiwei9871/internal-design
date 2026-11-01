import json
import unittest
from pathlib import Path

CD = Path(__file__).resolve().parents[1] / 'projects/c_type_home/cad/construction_docs'


class MepTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.q = json.loads((CD / 'qa/mep_qa.json').read_text())
        cls.pts = json.loads((CD / 'data/mep_points.json').read_text())['points']
        cls.v2 = json.loads((CD / 'data/lighting_points_v2.json').read_text())['points']

    def test_qa_pass_and_no_fail(self):
        self.assertEqual(self.q['result'], 'PASS')
        self.assertFalse([i for i in self.q['issues'] if i['severity'] == 'FAIL'])

    def test_nothing_claimed_as_decided(self):
        for p in self.pts:
            self.assertIn(p['status'], ('PROPOSED', 'TBD', 'OPTIONAL_TBD'), p['id'])
            self.assertIsNone(p.get('physical_circuit_id'), p['id'])

    def test_every_lighting_group_has_a_switch(self):
        groups = {p['control_group'] for p in self.v2}
        served = {g for p in self.pts if p['type'] == 'SWITCH' for g in p['serves']}
        self.assertEqual(groups - served, set())

    def test_mother_night_groups_have_sensor_and_manual(self):
        for g in ('mother_bedroom:NIGHT', 'vestibule:NIGHT', 'master_bath:NIGHT'):
            self.assertTrue(any(g in p.get('serves', []) for p in self.pts if p['type'] == 'SENSOR'), g)
            self.assertTrue(any(g in p.get('serves', []) for p in self.pts if p['type'] == 'SWITCH'), g)

    def test_drainage_out_of_scope_and_sources_tbd(self):
        self.assertIn('排水 (业主自行处理)', self.q['out_of_scope'])
        self.assertFalse(any(p['type'].startswith('DRAIN') for p in self.pts))
        src = json.loads((CD / 'data/mep_points.json').read_text())['sources']
        self.assertTrue(all(s['status'] in ('TBD', 'ASSUMED_TBD') for s in src))


if __name__ == '__main__':
    unittest.main()


import sys  # noqa: E402
sys.path.insert(0, str(CD))
from mep_topology import report as topo_report  # noqa: E402


class TopologyTests(unittest.TestCase):
    """PR #15 review 5727854850 P0: SOURCE must reach every terminal; small tolerance only."""
    @classmethod
    def setUpClass(cls):
        cls.routes = json.loads((CD / 'data/mep_routes.json').read_text())['segments']
        cls.pts = [p for p in json.loads((CD / 'data/mep_points.json').read_text())['points']
                   if p['system'] in ('POWER', 'DATA', 'COLD', 'HOT')]
        cls.q = json.loads((CD / 'qa/mep_qa.json').read_text())

    def test_every_terminal_reachable_from_source(self):
        r = topo_report(self.routes, self.pts)
        self.assertEqual(r['result'], 'PASS')
        for s in r['systems']:
            self.assertEqual(s['terminals_reachable'], s['terminals_total'], s['system'])
            self.assertEqual(s['segments_reachable'], s['segments_total'], s['system'])

    def test_120mm_gap_is_not_bridged(self):
        src = [{'system': 'DATA', 'kind': 'SOURCE', 'seg': [[0, 0], [1000, 0]]}]
        trunk = [{'system': 'DATA', 'kind': 'SPINE', 'seg': [[1120, 0], [1120, 2000]]}]
        r = topo_report(src + trunk, [{'id': 'T', 'system': 'DATA', 'x': 1120, 'y': 2000}], systems=('DATA',))
        self.assertEqual(r['result'], 'FAIL')
        self.assertEqual(r['systems'][0]['unreachable_terminals'], ['T'])

    def test_touching_corner_is_connected(self):
        segs = [{'system': 'HOT', 'kind': 'SOURCE', 'seg': [[0, 0], [1000, 0]]},
                {'system': 'HOT', 'kind': 'SPINE', 'seg': [[1000, 0], [1000, 2000]]},
                {'system': 'HOT', 'kind': 'BRANCH', 'seg': [[500, 1000], [1000, 1000]]}]
        r = topo_report(segs, [{'id': 'T', 'system': 'HOT', 'x': 500, 'y': 1000}], systems=('HOT',))
        self.assertEqual(r['result'], 'PASS')

    def test_qa_records_topology_and_boundaries(self):
        self.assertEqual(self.q['topology']['result'], 'PASS')
        self.assertIn('NOT_MODELLED', self.q['lighting_wiring'])
        self.assertIn('不是开孔数', self.q['wall_crossings']['note'])
        self.assertIn('二维平面交点', self.q['crossings_note'])
        walls = json.loads((CD / 'data/mep_routes.json').read_text())['wall_crossings']['locations']
        for L in walls:
            if L['class'] != 'NEW_PARTITION_DESIGN': self.assertTrue(L['status'].startswith('HOLD'), L['id'])

    def test_s42_and_emergency_calls_pending(self):
        p = {x['id']: x for x in json.loads((CD / 'data/mep_points.json').read_text())['points']}
        self.assertEqual(p['S42']['electrical_zone'], 'ELECTRICAL_ZONE_PENDING')
        for e in ('E01', 'E02'): self.assertIn('不构成有效紧急呼叫系统', p[e]['system_note'])
