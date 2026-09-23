import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'construction'))
import cad_common as cad


class CadExportTests(unittest.TestCase):
    def test_export_creates_exact_paper_pdf_png_and_clean_dxf(self):
        self.assertTrue((Path(cad.__file__).parent / 'paper_export.py').exists())
        from paper_export import export_sheet
        with tempfile.TemporaryDirectory() as folder:
            doc = cad.new_doc()
            cad.draw_walls(doc.modelspace())
            cad.draw_frame_and_title(doc.modelspace(),'验证','A101',['尺寸须复尺'])
            target=Path(folder)/'A101_test_preview.png'
            export_sheet(doc,target)
            self.assertTrue(target.exists())
            self.assertTrue(target.with_name('A101_test.pdf').exists())
            import pymupdf
            pdf=pymupdf.open(target.with_name('A101_test.pdf'))
            self.assertAlmostEqual(pdf[0].rect.width*25.4/72,594,places=2)
            self.assertAlmostEqual(pdf[0].rect.height*25.4/72,420,places=2)
            self.assertTrue(target.with_name('A101_test.dxf').exists())
            import ezdxf
            loaded=ezdxf.readfile(target.with_name('A101_test.dxf'))
            audit=loaded.audit()
            self.assertEqual((len(audit.errors),len(audit.fixes)),(0,0))
            self.assertEqual(loaded.layouts.get('A101').dxf.paper_width,594)


if __name__ == '__main__':
    unittest.main()
