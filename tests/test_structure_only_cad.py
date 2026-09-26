import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1] / "projects/c_type_home"
REPORT = ROOT / "qc/structure_only_cad_report.json"
AUDIT = ROOT / "qc/lounge_entity_audit.json"


class StructureOnlyCadTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not REPORT.exists():
            raise AssertionError(
                "structure-only CAD report is missing; run build_structure_only_cad.py"
            )
        cls.report = json.loads(REPORT.read_text())
        if not AUDIT.exists():
            raise AssertionError("lounge entity audit is missing; run audit_lounge_entities.py")
        cls.audit = json.loads(AUDIT.read_text())

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

    def test_lounge_geometry_remaining_is_zero(self):
        self.assertEqual(self.report["lounge_geometry_remaining"], 0)

    def test_lounge_audit_candidates_are_explicit_and_source_backed(self):
        self.assertEqual(self.audit["missing_candidate_handles"], [])
        self.assertEqual(self.audit["approved_lounge_exclusion_handles"], [
            "30830F", "308310", "308311"
        ])
        candidates = {
            item["handle"]: item for item in self.audit["candidate_records"]
            if item["classification"] == "NON_STRUCTURAL_SOURCE_OVERLAY"
        }
        self.assertEqual(set(candidates), {"30830F", "308310", "308311"})
        self.assertEqual({item["layer"] for item in candidates.values()}, {"S-楼梯"})

    def test_explicit_excluded_handles_exactly_match_approved_lounge_set(self):
        registry = self.report["explicit_exclusion_registry"]
        lounge = next(
            item for item in registry
            if item["classification"] == "NON_STRUCTURAL_SOURCE_OVERLAY"
        )
        self.assertEqual(lounge["source_handles"], ["30830F", "308310", "308311"])

    def test_non_excluded_wall_entities_remain_exactly(self):
        match = self.report["wall_match"]
        self.assertEqual(match["missing"], [])
        self.assertEqual(match["extra"], [])
        self.assertEqual(match["geometry_mismatches"], [])
        self.assertEqual(match["max_coordinate_delta_mm"], 0.0)

    def test_windows_doors_columns_stairs_outside_lounge_unchanged(self):
        checks = self.report["outside_lounge_layer_checks"]
        for layer in ("S-S.WALL", "F-DOOR", "S-COLUMN", "S-楼梯"):
            with self.subTest(layer=layer):
                self.assertEqual(checks[layer]["missing"], [])
                self.assertEqual(checks[layer]["extra"], [])
                self.assertEqual(checks[layer]["geometry_mismatches"], [])
                self.assertLessEqual(checks[layer]["max_coordinate_delta_mm"], 0.01)

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
