import hashlib
import importlib.util
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1] / 'projects/c_type_home'
SPEC = importlib.util.spec_from_file_location('rc42', ROOT / 'scripts/task03a_render_dxf.py')
R = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(R)

class FragmentContractTests(unittest.TestCase):
    def test_known_areas(self):
        wall = [0, 0, 100, 20]
        cases = [([], 2000), ([[0, 0, 100, 20]], 0),
                 ([[40, -5, 60, 25]], 1600),
                 ([[10, 0, 50, 20], [30, 0, 70, 20]], 800),
                 ([[20, 10, 80, 30]], 1400),
                 ([[0, 5, 100, 25]], 500)]
        for cuts, expected in cases:
            with self.subTest(cuts=cuts):
                fragments = R._fragment_rectangles(wall, cuts)
                self.assertEqual(sum(R._rect_area(f) for f in fragments), expected)
                self.assertEqual(R._cut_union_area(wall, cuts), 2000 - expected)
                for i, f in enumerate(fragments):
                    self.assertGreater(R._rect_area(f), 0)
                    for other in fragments[i + 1:] + cuts:
                        self.assertIsNone(R._clip(f, other))

    def test_independent_unit_grid(self):
        wall = [0, 0, 8, 6]
        original = {(x, y) for x in range(8) for y in range(6)}
        for offset in range(-2, 7):
            cuts = [[offset, 1, offset + 4, 4], [2, offset, 6, offset + 2]]
            expected = {p for p in original if not any(c[0] <= p[0] < c[2] and c[1] <= p[1] < c[3] for c in cuts)}
            actual = set()
            for f in R._fragment_rectangles(wall, cuts):
                cells = {(x, y) for x in range(f[0], f[2]) for y in range(f[1], f[3])}
                self.assertFalse(actual.intersection(cells))
                actual.update(cells)
            self.assertEqual(actual, expected)

    def test_canonical_is_not_mutated(self):
        snapshot = json.dumps(R.CANONICAL, sort_keys=True)
        R.wall_faces_report(ROOT / 'cad/design_v01_existing_sync.dxf')
        self.assertEqual(json.dumps(R.CANONICAL, sort_keys=True), snapshot)

    def test_dxf_byte_locks(self):
        expected = {
            'design_v01_existing_sync.dxf': '5210557086ce08d2ca40cb5b14be909ba83608e68b22bcfd151ed73904cf6c00',
            'design_v02_f1_l1.dxf': '4e9dd3d4faf137d5db06160843b5dfc024cfab9bfcf571db7911dd76ea0b1c1d',
        }
        for name, digest in expected.items():
            self.assertEqual(hashlib.sha256((ROOT / 'cad' / name).read_bytes()).hexdigest(), digest)

    def test_required_artist_hierarchy(self):
        self.assertTrue(hasattr(R, 'ZORDER'), 'Explicit artist categories are missing')
        keys = ['wall_fill', 'wall_outline', 'parapet', 'openings', 'glazing_doors', 'furniture', 'text']
        values = [R.ZORDER[k] for k in keys]
        self.assertEqual(values, sorted(set(values)))

    def test_all_fenestrations_and_parapets(self):
        for file in ['design_v01_existing_sync.dxf', 'design_v02_f1_l1.dxf']:
            data = R.wall_faces_report(ROOT / 'cad' / file)
            self.assertEqual(len(data['alignment']), 39)
            self.assertEqual(len(data['fenestration']), 9)
            self.assertEqual(len({f['id'] for f in data['fenestration']}), 9)
            self.assertEqual(sum(w['wall_type']=='railing_parapet' for w in data['walls']), 4)
            for w in data['walls']:
                self.assertEqual(w['area_error_mm2'], 0)
            for f in data['fenestration']:
                self.assertTrue(f['source_handles'])
                self.assertEqual(f['overlay_overlap_mm2'], 0)

    def test_cad_review_has_no_rc42_wall_face_overlay(self):
        name = '_test_rc42_cad_review_no_wall_faces'
        generated = [ROOT / 'qc' / f'{name}{suffix}'
                     for suffix in ('.png', '.pdf', '.render.json')]
        for path in generated:
            self.addCleanup(path.unlink, missing_ok=True)
        side = R.render(ROOT / 'cad/design_v01_existing_sync.dxf', 'CAD_REVIEW', name)
        self.assertEqual(side['wall_faces'], [])
        self.assertEqual(side['parapet_faces'], [])
        self.assertEqual(side['overlay_artists'], [])

if __name__ == '__main__':
    unittest.main()
