from pathlib import Path
import json
import sys
import unittest

EXP = Path("/Users/xiwei/interior_design/projects/c_type_home/experiments/design_skill_benchmark_v02")
sys.path.insert(0, str(EXP / "scripts"))

class D02FrameworkTests(unittest.TestCase):
    def test_cad_tool_has_no_arm_layout_coordinates(self):
        source = (EXP / "scripts/cad_tool.py").read_text()
        self.assertNotIn("ARM_SPECS", source)
        self.assertNotIn("trial_r01", source)
        self.assertNotIn("trial_r02", source)
        self.assertNotRegex(source, r"[\"\']x[\"\']\s*:\s*[-+]?\d{3,}")
        self.assertNotRegex(source, r"[\"\']y[\"\']\s*:\s*[-+]?\d{3,}")

    def test_command_log_causality_rejects_early_r02(self):
        from cad_tool import validate_iteration_causality
        bad = [
            {"timestamp":"2026-01-01T00:00:02Z","iteration":"r02","action":"move"},
            {"timestamp":"2026-01-01T00:00:03Z","iteration":"r01","action":"render"},
            {"timestamp":"2026-01-01T00:00:04Z","iteration":"r01","action":"geometry_report"},
        ]
        self.assertFalse(validate_iteration_causality(bad)["pass"])

    def test_command_log_causality_accepts_feedback_before_r02(self):
        from cad_tool import validate_iteration_causality
        good = [
            {"timestamp":"2026-01-01T00:00:01Z","iteration":"r01","action":"insert"},
            {"timestamp":"2026-01-01T00:00:02Z","iteration":"r01","action":"render"},
            {"timestamp":"2026-01-01T00:00:03Z","iteration":"r01","action":"geometry_report"},
            {"timestamp":"2026-01-01T00:00:04Z","iteration":"r01","action":"agent_review"},
            {"timestamp":"2026-01-01T00:00:05Z","iteration":"r02","action":"move"},
        ]
        self.assertTrue(validate_iteration_causality(good)["pass"])

    def test_packager_requires_real_agent_evidence(self):
        from package_d02 import validate_session_evidence
        result = validate_session_evidence("STUDIO")
        self.assertTrue(result["pass"])
        self.assertTrue(result["real_agent_action"])
        self.assertTrue(result["feedback_causality"])

    def test_packager_rejects_missing_review(self):
        from package_d02 import validate_session_evidence
        result = validate_session_evidence("CTRL")
        self.assertTrue(result["pass"])

    def test_blind_report_hides_arm_mapping(self):
        report = (EXP / "reports/d02_report.md").read_text()
        for token in ("CTRL", "ARCH", "STUDIO", "REROOM"):
            self.assertNotIn(token, report)
        self.assertTrue((EXP / "blind_review/arm_mapping.secret.json").exists())

if __name__ == "__main__":
    unittest.main()
