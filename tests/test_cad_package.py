import sys
import unittest
import tempfile
import shutil
from unittest.mock import patch
from pathlib import Path

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'construction'))
import cad_common as cad


class PackageTests(unittest.TestCase):
    def assert_rejects_mutation(self,mutate,message):
        import ezdxf
        import build_all
        with tempfile.TemporaryDirectory() as folder:
            target=Path(folder)
            for p in cad.OUT.glob('A*'):
                if p.suffix in ('.dxf','.pdf','.json'): shutil.copy2(p,target/p.name)
            path=next(target.glob('A101*.dxf'))
            doc=ezdxf.readfile(path);mutate(doc);doc.saveas(path)
            with patch.object(build_all,'OUT',target):
                with self.assertRaisesRegex(ValueError,message):
                    build_all.verify_package()

    def test_rejects_metre_model_units_even_when_pdf_and_manifest_are_unchanged(self):
        self.assert_rejects_mutation(lambda d:setattr(d,'units',6),'model units')

    def test_rejects_a4_dxf_layout_even_when_pdf_is_a2(self):
        def mutate(doc):
            paper=doc.layouts.get('A101')
            paper.dxf.paper_width=297;paper.dxf.paper_height=210
        self.assert_rejects_mutation(mutate,'paper size')

    def test_rejects_unlocked_viewport_even_when_scale_is_correct(self):
        def mutate(doc):
            vp=next(v for v in doc.layouts.get('A101').query('VIEWPORT') if v.dxf.status>=2)
            vp.dxf.flags &= ~16384
        self.assert_rejects_mutation(mutate,'unlocked viewport')

    def test_rejects_inch_paper_units(self):
        self.assert_rejects_mutation(lambda d:setattr(d.layouts.get('A101').dxf,'plot_paper_units',0),'paper units')

    def test_existing_package_verified_without_audit_repairs(self):
        self.assertTrue((Path(cad.__file__).parent/'build_all.py').exists())
        from build_all import verify_package
        report=verify_package()
        self.assertEqual(len(report['sheets']),10)
        for s in report['sheets']:
            self.assertEqual(s['audit_errors'],0)
            self.assertEqual(s['audit_fixes'],0)
            self.assertEqual(s['undefined_linetypes'],[])
            self.assertEqual(s['paper_mm'],[594.0,420.0])
            self.assertEqual(s['design_sha256'],report['design_sha256'])


if __name__=='__main__':
    unittest.main()
