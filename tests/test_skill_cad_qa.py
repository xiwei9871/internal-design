import sys
import tempfile
import unittest
from pathlib import Path

import ezdxf

SCRIPTS = Path(__file__).resolve().parents[1] / '.codex/skills/interior-renovation-cad-docs/scripts'
sys.path.insert(0, str(SCRIPTS))
import dxf_sheet_qa as qa  # noqa: E402
import zone_qa  # noqa: E402

SQ = [[0, 0], [4000, 0], [4000, 3000], [0, 3000]]


def make_sheet(path, *, version='R2010', font='gbenor.shx', bigfont='gbcbig.shx',
               frame=True, viewport=False, cjk=True, outside=False):
    doc = ezdxf.new(version, setup=True)
    doc.header['$INSUNITS'] = 4
    st = doc.styles.get('Standard'); st.dxf.font = font; st.dxf.bigfont = bigfont
    msp = doc.modelspace()
    msp.add_lwpolyline([(0, 0), (10000, 0), (10000, 8000), (0, 8000)], close=True)
    if cjk: msp.add_text('客厅', height=175).set_placement((1000, 1000))
    if outside: msp.add_line((0, 0), (90000, 0))
    if frame:
        doc.layers.new('A-FRAME')
        x0, y0 = -10000, -10000
        msp.add_lwpolyline([(x0, y0), (x0 + 42050, y0), (x0 + 42050, y0 + 29700), (x0, y0 + 29700)],
                           close=True, dxfattribs={'layer': 'A-FRAME'})
    if viewport:
        doc.layouts.get('Layout1').add_viewport(center=(420, 297), size=(780, 520),
                                                view_center_point=(5000, 4000), view_height=26000)
    doc.saveas(path)


def status(r, name):
    return next(c['status'] for c in r['checks'] if c['check'] == name)


class DxfSheetQaTests(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())

    def run_qa(self, **kw):
        p = self.tmp / 'sheet.dxf'
        make_sheet(p, **kw)
        return qa.run(p)

    def test_conforming_sheet_passes(self):
        r = self.run_qa()
        self.assertEqual(r['result'], 'PASS', r['checks'])

    def test_r2018_fails_version(self):
        self.assertEqual(status(self.run_qa(version='R2018'), 'dxf_version'), 'FAIL')

    def test_absolute_font_path_fails(self):
        r = self.run_qa(font='/System/Library/Fonts/STHeiti Medium.ttc', bigfont='')
        self.assertEqual(status(r, 'font_paths_portable'), 'FAIL')
        self.assertEqual(status(r, 'cjk_text_styles'), 'FAIL')

    def test_hztxt_bigfont_is_not_cjk_capable(self):
        r = self.run_qa(font='txt.shx', bigfont='hztxt.shx')
        self.assertEqual(status(r, 'cjk_text_styles'), 'FAIL')

    def test_missing_frame_fails(self):
        self.assertEqual(status(self.run_qa(frame=False), 'frame_a1_scale'), 'FAIL')

    def test_content_outside_frame_fails(self):
        self.assertEqual(status(self.run_qa(outside=True), 'content_inside_frame'), 'FAIL')

    def test_paperspace_viewport_warns(self):
        r = self.run_qa(viewport=True)
        self.assertEqual(status(r, 'no_paperspace_viewports'), 'WARN')
        self.assertEqual(r['result'], 'PASS')

    def test_entity_count_mismatch_fails(self):
        src, out = self.tmp / 'src.dxf', self.tmp / 'out.dxf'
        make_sheet(src, frame=False)
        make_sheet(out, cjk=False)          # one entity fewer than src (frame excluded)
        r = qa.run(out, src=src)
        self.assertEqual(status(r, 'entities_preserved'), 'FAIL')


class ZoneQaTests(unittest.TestCase):
    def test_clean_partition_passes(self):
        z = [{'id': 'a', 'polygon': [[0, 0], [2000, 0], [2000, 3000], [0, 3000]]},
             {'id': 'b', 'polygon': [[2000, 0], [4000, 0], [4000, 3000], [2000, 3000]]}]
        r = zone_qa.run({'zones': z, 'interior': [SQ]})
        self.assertEqual(r['result'], 'PASS', r)
        self.assertAlmostEqual(r['total_m2'], 12.0, places=3)

    def test_overlap_detected(self):
        z = [{'id': 'a', 'polygon': [[0, 0], [2500, 0], [2500, 3000], [0, 3000]]},
             {'id': 'b', 'polygon': [[2000, 0], [4000, 0], [4000, 3000], [2000, 3000]]}]
        r = zone_qa.run({'zones': z})
        self.assertEqual(r['result'], 'FAIL')
        self.assertEqual(r['overlaps'][0]['area_m2'], 1.5)

    def test_gap_detected(self):
        z = [{'id': 'a', 'polygon': [[0, 0], [3000, 0], [3000, 3000], [0, 3000]]}]
        r = zone_qa.run({'zones': z, 'interior': [SQ]}, gap_tol_m2=0.05)
        self.assertEqual(r['result'], 'FAIL')
        self.assertEqual(r['gaps'][0]['area_m2'], 3.0)

    def test_small_gap_tolerated(self):
        z = [{'id': 'a', 'polygon': [[0, 0], [3990, 0], [3990, 3000], [0, 3000]]}]
        self.assertEqual(zone_qa.run({'zones': z, 'interior': [SQ]})['result'], 'PASS')


class SkillEntryTests(unittest.TestCase):
    ROOT = Path(__file__).resolve().parents[1]

    def test_claude_entries_resolve_to_codex_skills(self):
        codex = {p.name for p in (self.ROOT / '.codex/skills').iterdir() if (p / 'SKILL.md').is_file()}
        claude_dir = self.ROOT / '.claude/skills'
        claude = {p.name for p in claude_dir.iterdir()}
        self.assertEqual(codex, claude)
        for n in claude:
            p = claude_dir / n
            self.assertTrue(p.is_symlink(), n)
            self.assertEqual(p.resolve(), (self.ROOT / '.codex/skills' / n).resolve())

    def test_skill_frontmatter_has_name_and_description(self):
        for f in (self.ROOT / '.codex/skills').glob('*/SKILL.md'):
            head = f.read_text().split('---')[1]
            self.assertIn('name:', head, f)
            self.assertIn('description:', head, f)
            self.assertLess(len(f.read_text().splitlines()), 500, f)

    def test_no_render_segmentation_in_cad_skills(self):
        for n in ('interior-renovation-cad-docs', 'blender-plan-geometry-extraction'):
            txt = (self.ROOT / '.codex/skills' / n / 'SKILL.md').read_text()
            self.assertNotIn('Pixel-segment', txt)
            self.assertNotIn('material-paint orthographic top view', txt.replace('top renders', ''))
            self.assertIn('extract_plan_geometry.py', txt)


if __name__ == '__main__':
    unittest.main()
