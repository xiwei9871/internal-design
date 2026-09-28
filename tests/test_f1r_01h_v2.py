import hashlib
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
QC = ROOT / "projects/c_type_home/qc/f1r_public_zone"


class F1R01HGeometricClearanceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.metrics = json.loads((QC / "F1R_01H_metrics_v2.json").read_text())
        cls.audit = (QC / "F1R_01H_design_audit_v2.md").read_text()

    def test_geometry_method_and_block_bbox(self):
        self.assertEqual(self.metrics["method"], "geometric_free_space_v2")
        self.assertTrue(self.metrics["qa"]["actual_dxf_block_geometry_rendered"])
        self.assertTrue(self.metrics["qa"]["transformed_bbox_all_within_1mm"])
        self.assertTrue(self.metrics["qa"]["reference_envelopes_kept_separate"])
        self.assertTrue(self.metrics["formal_cad_writeback"] is False)

    def test_actual_measurements_are_separate_from_targets(self):
        c = self.metrics["clearances"]
        self.assertEqual(c["entry_to_living_actual_min_mm"], 2280)
        self.assertEqual(c["living_to_stair_actual_min_mm"], 1200)
        self.assertEqual(c["living_to_north_balcony_actual_min_mm"], 850)
        self.assertEqual(c["dining_chair_pullout_actual_min_mm"], 150.0)
        self.assertEqual(c["behind_seated_passage_actual_min_mm"], 180.0)
        self.assertEqual(c["table_to_keep_kitchen_actual_min_mm"], 700.0)
        self.assertIn("sampled cross-sections", c["sampling_method"])
        self.assertIn("reference envelopes", self.audit)

    def test_actual_clear_rectangle_is_rendered(self):
        rect = self.metrics["actual_largest_clear_rectangle_mm"]
        self.assertEqual(rect, [5600.0, 7800, 7700, 10800.0])
        self.assertIn("2100.0 × 3000.0 mm", self.audit)
        self.assertTrue((QC / "F1R_01H_clearance_overlay_v2.png").exists())


if __name__ == "__main__":
    unittest.main()
