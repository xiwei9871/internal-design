import importlib.util
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / ".codex/skills/archviz-interior-workflow/scripts/artifact_guard.py"
spec = importlib.util.spec_from_file_location("artifact_guard", SCRIPT)
guard = importlib.util.module_from_spec(spec)
if SCRIPT.exists():
    spec.loader.exec_module(guard)


class ArtifactGuardTests(unittest.TestCase):
    def test_byte_budget_uses_encoded_allowance(self):
        with tempfile.TemporaryDirectory() as folder:
            image=Path(folder)/"input.png"
            with image.open("wb") as handle: handle.truncate(20*1024*1024)
            with self.assertRaises(ValueError): guard.preflight([image], "", 24*1024*1024)

    def test_snapshot_reports_changed_and_missing_files(self):
        with tempfile.TemporaryDirectory() as folder:
            a=Path(folder)/"a.png";b=Path(folder)/"b.blend"
            a.write_bytes(b"original");b.write_bytes(b"geometry")
            manifest=guard.snapshot([a,b])
            self.assertTrue(guard.verify(manifest)["unchanged"])
            a.write_bytes(b"changed");b.unlink()
            result=guard.verify(manifest)
            self.assertFalse(result["unchanged"])
            self.assertEqual({f["status"] for f in result["files"]},{"CHANGED","MISSING"})

    def test_derivative_preserves_originals_and_rejects_overwrite(self):
        from PIL import Image
        with tempfile.TemporaryDirectory() as folder:
            image=Path(folder)/"source.png";output=Path(folder)/"review.jpg"
            Image.new("RGB",(1920,1080),"white").save(image)
            before=image.read_bytes()
            result=guard.sheet([image,image],output,1600,82,2)
            self.assertLessEqual(max(result["size"]),1600)
            self.assertEqual(image.read_bytes(),before)
            with self.assertRaises(FileExistsError):guard.sheet([image],output,1600,82,2)
            with self.assertRaises(FileExistsError):guard.sheet([image],image,1600,82,2)

    def test_preflight_never_reads_image_content_or_outputs_secret(self):
        with tempfile.TemporaryDirectory() as folder:
            image=Path(folder)/"ref.jpg";image.write_bytes(b"unread pixels")
            report=guard.preflight([image],"private prompt",24*1024*1024)
            self.assertEqual(report["image_bytes"],13)
            self.assertNotIn("private prompt",str(report))
            self.assertNotIn("unread pixels",str(report))


if __name__=="__main__":unittest.main()
