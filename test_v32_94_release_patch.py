import json
import subprocess
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent

class ReleasePatchTests(unittest.TestCase):
    def test_patch_against_v3301_payload(self):
        fixture = Path("/tmp/z2se-v3301/Z2SE_UPDATE.zip")
        if not fixture.is_file():
            self.skipTest("v33.01 release fixture is not available")
        with tempfile.TemporaryDirectory() as directory:
            work = Path(directory)
            with zipfile.ZipFile(fixture) as archive:
                archive.extractall(work / "payload")
            result = subprocess.run(
                [sys.executable, str(ROOT / "release_patch.py"), "33.02"],
                cwd=work, text=True, stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT, check=False,
            )
            self.assertEqual(result.returncode, 0, result.stdout)
            app = (work / "payload" / "app.py").read_text(encoding="utf-8")
            self.assertIn('APP_VERSION = "33.02"', app)
            self.assertIn("before_dl:__VD_FORMATS__%(requested_formats)j", app)
            self.assertIn("download:__VD_PROGRESS__%(info.format_id)s", app)
            self.assertIn("unified_phase_downloaded", app)
            self.assertIn("global_downloaded = int(sum(unified_phase_downloaded.values()))", app)
            self.assertIn("max(0, known_total - global_downloaded) / unified_speed_ema", app)
            compile(app, "app.py", "exec")
            manifest = json.loads((work / "payload" / "update_manifest.json").read_text(encoding="utf-8"))
            self.assertEqual(manifest["version"], "33.02")
            self.assertEqual(manifest["files"][0]["size"], (work / "payload" / "app.py").stat().st_size)

if __name__ == "__main__":
    unittest.main()
