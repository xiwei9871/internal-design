import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1] / "projects/c_type_home"
LIB = ROOT / "assets/cad_library"
MANIFEST = LIB / "manifests/block_manifest.json"
QA = LIB / "manifests/qa_report.json"
COMPILED = LIB / "compiled/residential_plan_blocks_v01.dxf"


class A03CadLibraryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not MANIFEST.exists() or not QA.exists():
            raise AssertionError("run build_cad_library_v01.py first")
        cls.manifest = json.loads(MANIFEST.read_text())
        cls.qa = json.loads(QA.read_text())

    def test_selected_count_and_no_design_scaling(self):
        self.assertEqual(len(self.manifest["blocks"]), 20)
        self.assertTrue(all(item["geometry_scaled"] is False for item in self.manifest["blocks"]))
        self.assertTrue(all(item["design_geometry_rescaled"] is False for item in self.manifest["blocks"]))
        self.assertTrue(all("unit_conversion_applied" in item for item in self.manifest["blocks"]))

    def test_normalized_units_and_bbox_contract(self):
        for item in self.manifest["blocks"]:
            self.assertEqual(item["normalized_units"], "mm")
            self.assertLessEqual(item["bbox_delta_mm"], 0.01)
            self.assertEqual(item["xref"], False)
            self.assertEqual(item["ole"], False)
            self.assertEqual(item["proxy"], False)
            self.assertEqual(item["qa_status"], "PASS")

    def test_base_points_and_named_blocks_are_deterministic(self):
        ids = [item["id"] for item in self.manifest["blocks"]]
        self.assertEqual(len(ids), len(set(ids)))
        for item in self.manifest["blocks"]:
            self.assertEqual(item["normalized_base_point_mm"], [0.0, 0.0])
            self.assertTrue(item["base_point_convention"])
            self.assertTrue((LIB / item["normalized_file"]).exists())

    def test_compiled_library_and_previews_exist(self):
        self.assertTrue(COMPILED.exists())
        self.assertEqual(self.qa["status"], "PASS")
        self.assertTrue((LIB / "previews/contact_sheet_v01.png").exists())


if __name__ == "__main__":
    unittest.main()
