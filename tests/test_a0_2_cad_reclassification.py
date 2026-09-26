import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1] / "projects/c_type_home"
REPORT = ROOT / "qc/a0_2_cad_sample_report.json"


class A02TechnicalClassificationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.report = json.loads(REPORT.read_text())
        cls.samples = cls.report["samples"]

    def test_classification_is_technical_only(self):
        self.assertEqual(self.report["classification_basis"], "technical_only")
        self.assertEqual(
            {s["license_gate"] for s in self.samples},
            {"CONFLICT", "UNKNOWN", "MIT"},
        )
        self.assertFalse(any(s["classification"] == "REJECT" for s in self.samples))

    def test_gsstnb_clean_plan_samples_are_normalize(self):
        gsstnb = [s for s in self.samples if s["repo"] == "GSStnb/dxfBlocks"]
        self.assertEqual(len(gsstnb), 14)
        self.assertTrue(all(s["plan_legend_suitable"] for s in gsstnb))
        self.assertTrue(all(s["classification"] == "NORMALIZE" for s in gsstnb))
        self.assertTrue(all(s["unit_scale_to_mm"] == 25.4 for s in gsstnb))

    def test_nominal_and_actual_geometry_fields_exist(self):
        for sample in self.samples:
            self.assertIn("nominal_product_geometry_mm", sample)
            self.assertIn("actual_drawn_bbox_mm", sample)
            self.assertIn("unit_confidence", sample)

    def test_uncreated_plausible_geometry_is_not_rejected_for_origin_or_units(self):
        candidates = [s for s in self.samples if s["repo"] == "uncreatednet/DXF-library"]
        self.assertEqual(len(candidates), 8)
        self.assertTrue(all(s["classification"] == "NORMALIZE" for s in candidates))


if __name__ == "__main__":
    unittest.main()
