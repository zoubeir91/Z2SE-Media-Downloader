import json
import subprocess
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent

class ReleasePatchTests(unittest.TestCase):
    def test_patch_against_v3299_payload(self):
        fixture = Path("/tmp/z2se-v3299/Z2SE_UPDATE.zip")
        if not fixture.is_file():
            self.skipTest("v32.99 release fixture is not available")
        with tempfile.TemporaryDirectory() as directory:
            work = Path(directory)
            with zipfile.ZipFile(fixture) as archive:
                archive.extractall(work / "payload")
            result = subprocess.run(
                [sys.executable, str(ROOT / "release_patch.py"), "33.00"],
                cwd=work, text=True, stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT, check=False,
            )
            self.assertEqual(result.returncode, 0, result.stdout)
            app = (work / "payload" / "app.py").read_text(encoding="utf-8")
            self.assertIn('APP_VERSION = "33.00"', app)
            handler = app[app.index("def _v3271_open_preview"):]
            handler = handler[:handler.index('v3270_preview.bind("<ButtonRelease-1>"')]
            self.assertIn('v3271_preview_enabled.get("path")', handler)
            self.assertIn("_exact_path_for_row", handler)
            self.assertNotIn("_find_download_file_for_row", handler)
            self.assertIn("Preview click error:", handler)
            self.assertLess(handler.index('v3271_preview_enabled.get("path")'), handler.index("_exact_path_for_row"))
            compile(app, "app.py", "exec")
            manifest = json.loads((work / "payload" / "update_manifest.json").read_text(encoding="utf-8"))
            self.assertEqual(manifest["version"], "33.00")
            self.assertEqual(manifest["files"][0]["size"], (work / "payload" / "app.py").stat().st_size)

if __name__ == "__main__":
    unittest.main()
