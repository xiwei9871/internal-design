import json
import hashlib
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
QC = ROOT / "projects/c_type_home/qc/f1r_public_zone"


class F1R01HTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.metrics = json.loads((QC / "F1R_01H_metrics.json").read_text())
        cls.audit = (QC / "F1R_01H_design_audit.md").read_text()

    def test_actual_blocks_and_concept_boundary(self):
        qa = self.metrics["qa"]
        self.assertTrue(qa["actual_dxf_block_geometry_rendered"])
        self.assertGreaterEqual(qa["a0_block_ref_count"], 8)
        self.assertTrue(qa["transformed_block_bbox_within_tolerance"])
        self.assertFalse(qa["formal_cad_writeback"])
        self.assertTrue(qa["central_clear_zone_reported_descriptively"])
        self.assertFalse(qa["negative_space_ratio_used_as_pass_fail"])

    def test_clearance_report_is_explicit(self):
        c = self.metrics["clearances"]
        self.assertEqual(self.metrics["path_blocker_count"], 0)
        self.assertEqual(c["entry_to_living_min_clear_width_mm"], 950)
        self.assertEqual(c["living_to_stair_min_clear_width_mm"], 600)
        self.assertEqual(c["living_to_north_balcony_min_clear_width_mm"], 850)
        self.assertEqual(c["dining_chair_pullout_mm"], 600)
        self.assertEqual(c["behind_seated_dining_passage_mm"], 600)
        self.assertIn("TO_VERIFY", self.audit)

    def test_review_outputs_exist_and_input_hashes_match(self):
        for name in ["F1R_01H_plan.png", "F1R_01H_clearance_overlay.png", "F1R_01H_metrics.json", "F1R_01H_design_audit.md"]:
            self.assertTrue((QC / name).exists(), name)
        mapping = {
            "furniture_l1_final.json": ROOT / "projects/c_type_home/concept/furniture_l1_final.json",
            "concept_data.json": ROOT / "projects/c_type_home/concept/concept_data.json",
            "canonical_plan_v1.json": ROOT / "projects/c_type_home/current_existing/canonical_plan_v1.json",
            "window_register.json": ROOT / "projects/c_type_home/current_existing/window_register.json",
            "design_legend_manifest_v01.json": ROOT / "projects/c_type_home/assets/cad_library/standard/manifests/design_legend_manifest_v01.json",
        }
        for name, path in mapping.items():
            self.assertEqual(hashlib.sha256(path.read_bytes()).hexdigest(), self.metrics["input_hashes"][name])


if __name__ == "__main__":
    unittest.main()
