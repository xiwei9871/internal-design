import json
import sys
import unittest
from pathlib import Path

CD = Path(__file__).resolve().parents[1] / 'projects/c_type_home/cad/construction_docs'
sys.path.insert(0, str(CD))
from lighting_review import context, checks  # noqa: E402


class LightingReviewTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.v1, cls.ctx = context()
        cls.v2 = json.loads((CD / 'data/lighting_points_v2.json').read_text())['points']

    def test_detector_finds_known_v1_conflicts(self):
        codes = {(p['id'], c) for p in self.v1 for _, c, _ in checks(p, self.ctx)}
        self.assertIn(('L088', 'TASK_LIGHT_ABOVE_WALL_CABINET'), codes)
        self.assertIn(('L029', 'OVER_FULL_HEIGHT_STORAGE'), codes)
        self.assertIn(('L040', 'OVER_BED'), codes)
        self.assertIn(('L033', 'IN_SHOWER_FOOTPRINT'), codes)

    def test_v2_has_no_fail(self):
        fails = [(p['id'], c) for p in self.v2 for s, c, _ in checks(p, self.ctx) if s == 'FAIL']
        self.assertEqual(fails, [])

    def test_every_v1_point_traced(self):
        import csv
        acted = {r['id'] for r in csv.DictReader(open(CD / 'data/lighting_changes.csv', encoding='utf-8-sig'))}
        self.assertFalse({p['id'] for p in self.v1} - acted)

    def test_mother_night_route_covered(self):
        rooms = {p['room'] for p in self.v2 if p['layer'] == 'night'}
        self.assertTrue({'mother_bedroom', 'vestibule', 'master_bath'} <= rooms)

    def test_new_points_marked_proposed_and_cct_in_range(self):
        for p in self.v2:
            if p['action'] != 'KEEP': self.assertEqual(p['status'], 'PROPOSED', p['id'])
            self.assertTrue(3000 <= p['cct_k'] <= 4000, p['id'])

    def test_v1_file_untouched_by_review(self):
        v1 = json.loads((CD / 'data/lighting_points.json').read_text())['points']
        self.assertEqual(len(v1), 94)
        self.assertNotIn('action', v1[0])


if __name__ == '__main__':
    unittest.main()


class ReviewFixTests(unittest.TestCase):
    """Review 5727633216 P1-A..D."""
    @classmethod
    def setUpClass(cls):
        import csv
        cls.rows = list(csv.DictReader(open(CD / 'data/lighting_compare.csv', encoding='utf-8-sig')))
        cls.v2 = json.loads((CD / 'data/lighting_points_v2.json').read_text())['points']
        cls.qa = json.loads((CD / 'qa/a201_v2_lighting_qa.json').read_text())
        cls.report = (CD.parents[3] / 'docs/design_review_a201_v01/A201_LIGHTING_REVIEW.md').read_text()

    def test_p1a_report_summary_matches_csv(self):
        t = {k: sum(int(r[k]) for r in self.rows) for k in ('v1_base', 'v2_base', 'v1_total', 'v2_total')}
        self.assertIn(f"基础光 {t['v1_base']} → {t['v2_base']}", self.report)
        self.assertIn(f"合计 {t['v1_total']} → {t['v2_total']}", self.report)
        summ = json.loads((CD / 'data/lighting_summary.json').read_text())['totals']
        self.assertEqual(summ['v1_base'], t['v1_base'])

    def test_p1b_night_route_is_coverage_plus_distances_not_continuity(self):
        nr = self.qa['night_route']
        self.assertEqual(nr['status'], 'PLAN_DISTANCE_ONLY')
        self.assertTrue(nr['segments'])
        self.assertIn('NOT measured continuity', self.qa['scope'])
        for p in self.v2:
            if p['layer'] == 'night': self.assertIn('PROPOSED', p.get('control', ''))

    def test_p1c_no_physical_circuit_claimed(self):
        for p in self.v2:
            self.assertIsNone(p['physical_circuit_id'], p['id'])
            self.assertTrue(p['circuit'].startswith('SCHEMATIC/TBD:'), p['id'])
            self.assertTrue(p['switch_id'].startswith('SCHEMATIC/TBD:'), p['id'])

    def test_p1d_shower_points_zone_pending_and_waiver_is_exact(self):
        z = {p['id']: p.get('electrical_zone') for p in self.v2}
        self.assertEqual(z['L023'], 'ELECTRICAL_ZONE_PENDING')
        self.assertEqual(z['L033'], 'ELECTRICAL_ZONE_PENDING')
        for f in self.qa['flags']:
            self.assertEqual((f['id'], f['code']), ('L023', 'IN_SHOWER_FOOTPRINT'))
            self.assertTrue(f['waiver'])
