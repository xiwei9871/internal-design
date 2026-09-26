import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1] / "projects/c_type_home"
REPORT = ROOT / "qc/structure_only_cad_report.json"


class StructureOnlyCadTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not REPORT.exists():
            raise AssertionError(
                "structure-only CAD report is missing; run build_structure_only_cad.py"
            )
        cls.report = json.loads(REPORT.read_text())

    def test_source_wall_entities_are_retained_exactly(self):
        match = self.report["wall_match"]
        self.assertEqual(match["missing"], [])
        self.assertEqual(match["extra"], [])
        self.assertEqual(match["geometry_mismatches"], [])
        self.assertLessEqual(match["max_coordinate_delta_mm"], 0.01)

    def test_no_furniture_or_leisure_overlay_remains(self):
        self.assertEqual(self.report["residual_furniture_entities"], [])
        self.assertEqual(self.report["residual_leisure_overlay_entities"], [])
        self.assertGreaterEqual(len(self.report["deleted_entities"]), 1)

    def test_green_box_source_wall_checks_pass(self):
        checks = self.report["green_box_checks"]
        self.assertEqual({item["name"] for item in checks}, {
            "upper_horizontal", "right_vertical", "life_balcony"
        })
        self.assertTrue(all(item["source_wall_linework"] for item in checks))

    def test_standard_window_keeps_surrounding_wall(self):
        item = self.report["standard_window_check"]
        self.assertEqual(item["window_id"], "W-KIT-S")
        self.assertEqual(item["opening_rect_mm"], [6100, -200, 7100, 0])
        self.assertTrue(item["surrounding_wall_linework"])


if __name__ == "__main__":
    unittest.main()
