import json
import subprocess
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path


ROOT = Path(__file__).resolve().parent


class ReleasePatchTests(unittest.TestCase):
    def test_patch_against_v3297_payload(self):
        fixture = Path("/tmp/z2se-v3297/Z2SE_UPDATE.zip")
        if not fixture.is_file():
            self.skipTest("v32.97 release fixture is not available")

        with tempfile.TemporaryDirectory() as directory:
            work = Path(directory)
            with zipfile.ZipFile(fixture) as archive:
                archive.extractall(work / "payload")

            result = subprocess.run(
                [sys.executable, str(ROOT / "release_patch.py"), "32.98"],
                cwd=work,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                check=False,
            )
            self.assertEqual(result.returncode, 0, result.stdout)

            app = (work / "payload" / "app.py").read_text(encoding="utf-8")
            self.assertIn('APP_VERSION = "32.98"', app)
            self.assertIn("browser_speed_ema = None", app)
            self.assertIn("VLC.mp4", app)
            self.assertIn("Preview click received", app)
            self.assertIn('v3270_preview.bind("<ButtonRelease-1>"', app)
            self.assertNotIn('extractor_args = "youtube:player_client=mweb"\n        if fast_extract:', app)
            compile(app, "app.py", "exec")

            manifest = json.loads(
                (work / "payload" / "update_manifest.json").read_text(encoding="utf-8")
            )
            self.assertEqual(manifest["version"], "32.98")
            self.assertEqual(
                manifest["files"][0]["size"],
                (work / "payload" / "app.py").stat().st_size,
            )


if __name__ == "__main__":
    unittest.main()
