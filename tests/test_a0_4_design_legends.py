import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1] / "projects/c_type_home"
LIB = ROOT / "assets/cad_library/standard"
MANIFEST = LIB / "manifests/design_legend_manifest_v01.json"
QA = LIB / "manifests/design_legend_qa_v01.json"


EXPECTED = {
    "BED_1800x2100_PLAN", "BED_1500x2000_PLAN", "BED_900x2000_PLAN",
    "SOFA_3S_2200x900_PLAN", "SOFA_2S_1800x850_PLAN", "LOUNGE_CHAIR_900x900_PLAN",
    "DESK_1700x800_PLAN", "DINING_TABLE_1500x600_PLAN", "DINING_CHAIR_450x500_PLAN",
    "WC_STD_450x700_PLAN", "VANITY_600x500_PLAN", "VANITY_900x500_PLAN",
    "SHOWER_900x1200_PLAN", "WARDROBE_D600_PLAN", "WASHER_600x650_PLAN", "DRYER_600x650_PLAN",
}


class A04DesignLegendTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not MANIFEST.exists() or not QA.exists():
            raise AssertionError("run build_design_legends_v01.py first")
        cls.manifest = json.loads(MANIFEST.read_text())
        cls.qa = json.loads(QA.read_text())

    def test_expected_ids_and_lineage(self):
        items = {item["id"]: item for item in self.manifest["legends"]}
        self.assertEqual(set(items), EXPECTED)
        for item in items.values():
            self.assertTrue(item["derived_from"])
            self.assertTrue(item["design_geometry_rescaled"])
            self.assertFalse(item["unit_conversion_applied"])

    def test_target_bbox_and_compiled_qa(self):
        for item in self.manifest["legends"]:
            target = item["design_target_bbox_mm"]
            actual = item["normalized_bbox_mm"]
            actual_dimensions = [actual[2] - actual[0], actual[3] - actual[1]]
            self.assertLessEqual(max(abs(a - b) for a, b in zip(target, actual_dimensions)), 0.01)
            self.assertTrue((LIB / item["normalized_file"]).exists())
        self.assertEqual(self.qa["status"], "PASS")
        self.assertTrue((LIB / "compiled/residential_design_legends_v01.dxf").exists())
        self.assertTrue((LIB / "previews/contact_sheet_v01.png").exists())

    def test_no_source_or_design_geometry_confusion(self):
        for item in self.manifest["legends"]:
            self.assertIn("source_bbox_mm", item)
            self.assertIn("scale_x", item)
            self.assertIn("scale_y", item)
            self.assertIn("geometry_scaled", item)
            self.assertTrue(item["geometry_scaled"])


if __name__ == "__main__":
    unittest.main()
