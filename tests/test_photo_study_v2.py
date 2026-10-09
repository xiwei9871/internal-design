import importlib.util
import sys
import tempfile
import unittest
from unittest.mock import patch
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parents[1] / "projects/c_type_home/scripts"
sys.path.insert(0, str(SCRIPTS))
import photo_study_v2 as study


class FaithfulPolicyTests(unittest.TestCase):
    def test_future_variants_use_own_room_not_kitchen_appearance(self):
        with tempfile.TemporaryDirectory() as folder, patch.object(study,"OUT",Path(folder)):
            for level in ["B_designer","C_creative"]:
                job=study.make_job("living","VIEW_01",level)
                self.assertNotIn(str(study.STYLE),job["refs"])
                self.assertIn(str(Path(folder)/"living/A_faithful/VIEW_01.png"),job["refs"])
                prompt=Path(job["prompt"]).read_text()
                self.assertNotIn("owner-liked corrected KITCHEN photo",prompt)
                self.assertIn("CHANGE LEDGER",prompt)

    def test_only_transient_failure_has_one_retry(self):
        self.assertTrue(study.retryable_failure("API request failed with HTTP 503", 0))
        self.assertFalse(study.retryable_failure("API request failed with HTTP 503", 1))
        for code in [400,401,403,413,422,429]:
            self.assertFalse(study.retryable_failure(f"HTTP {code}", 0))

    def test_policy_defers_designer_and_creative(self):
        self.assertEqual(study.select_levels(["A_faithful"], study.LEVELS), ["A_faithful"])
        with self.assertRaises(ValueError):
            study.select_levels(["A_faithful"], ["B_designer"])

    def test_cached_image_is_preserved_without_metadata(self):
        with tempfile.TemporaryDirectory() as folder:
            image = Path(folder) / "VIEW_01.png"
            image.write_bytes(b"original preserved")
            result = study.run_job({"output": str(image)})
            self.assertTrue(result["status"].startswith("CACHE"))
            self.assertEqual(image.read_bytes(), b"original preserved")

    def test_large_request_is_rejected_before_provider_call(self):
        with tempfile.TemporaryDirectory() as folder:
            image = Path(folder) / "input.png"
            with image.open("wb") as handle:
                handle.truncate(25 * 1024 * 1024)
            with self.assertRaises(ValueError):
                study.input_preflight([str(image)], "small prompt")

    def test_normal_request_records_size_without_serializing_images(self):
        with tempfile.TemporaryDirectory() as folder:
            image = Path(folder) / "input.png"
            image.write_bytes(b"small file")
            info = study.input_preflight([str(image)], "prompt")
            self.assertEqual(info["image_bytes"], 10)
            self.assertLess(info["estimated_encoded_bytes"], 24 * 1024 * 1024)


if __name__ == "__main__":
    unittest.main()
