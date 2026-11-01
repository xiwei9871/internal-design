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
