import hashlib
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
QC = ROOT / "projects/c_type_home/qc/f1r_public_zone"


class F1R02DiningTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.report = json.loads((QC / "F1R_02_metrics.json").read_text())
        cls.audit = (QC / "F1R_02_design_audit.md").read_text()

    def test_two_orientations_and_three_candidates(self):
        candidates = self.report["candidates"]
        self.assertEqual(len(candidates), 3)
        self.assertEqual({c["rotation"] for c in candidates}, {0, 90})
        self.assertEqual(self.report["search"]["grid_mm"], 50)
        self.assertGreater(self.report["search"]["feasible_candidates_by_orientation"]["0"], 0)
        self.assertGreater(self.report["search"]["feasible_candidates_by_orientation"]["90"], 0)

    def test_candidates_use_actual_a0_and_meet_stated_screen(self):
        for candidate in self.report["candidates"]:
            m = candidate["metrics"]
            self.assertEqual(m["status"], "FEASIBLE_CANDIDATE")
            self.assertTrue(m["bbox_qa"])
            self.assertEqual(len(m["chairs_actual_bboxes_mm"]), 4)
            self.assertGreaterEqual(m["seated_envelope_from_table_edge_mm"], 600)
            self.assertGreaterEqual(m["table_to_keep_kitchen_gap_mm"], 1000)
            self.assertGreaterEqual(m["g_din_liv_transition_clear_mm"], 900)
            self.assertTrue(m["p2_path_clear"])
            self.assertTrue(m["all_named_paths_clear"])
            self.assertFalse(m["overlaps"])
            self.assertEqual(m["table_to_chair_near_edge_gap_mm"], 100)
            self.assertGreater(m["extra_pullout_travel_available_mm"], 0)

    def test_850_balcony_door_is_no_worsening_limitation(self):
        item = self.report["existing_limitation"]
        self.assertEqual(item["id"], "G-LIV-NBALC")
        self.assertEqual(item["clear_width_mm"], 850)
        self.assertEqual(item["classification"], "EXISTING_CONFIRMED_LIMITATION")
        self.assertEqual(item["rule"], "NO_WORSENING")

    def test_living_and_formal_cad_inputs_are_frozen(self):
        self.assertEqual(set(self.report["frozen_living_ids"]), {"LIV-SOFA-3", "LIV-SOFA-2", "LIV-LOUNGE", "LIV-MEDIA-WALL"})
        self.assertFalse(self.report.get("formal_cad_writeback", False))
        path_map = {
            "furniture_l1_final.json": ROOT / "projects/c_type_home/concept/furniture_l1_final.json",
            "canonical_plan_v1.json": ROOT / "projects/c_type_home/current_existing/canonical_plan_v1.json",
            "window_register.json": ROOT / "projects/c_type_home/current_existing/window_register.json",
            "design_legend_manifest_v01.json": ROOT / "projects/c_type_home/assets/cad_library/standard/manifests/design_legend_manifest_v01.json",
        }
        for name, path in path_map.items():
            self.assertEqual(hashlib.sha256(path.read_bytes()).hexdigest(), self.report["input_hashes"][name])
        self.assertIn("No candidate is written to formal CAD", self.audit)
        for index in range(1, 4):
            self.assertTrue((QC / f"F1R_02_candidate_{index}.png").exists())


if __name__ == "__main__":
    unittest.main()
