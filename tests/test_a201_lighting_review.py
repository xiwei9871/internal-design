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
