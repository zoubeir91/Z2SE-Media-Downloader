import json
import subprocess
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path


ROOT = Path(__file__).resolve().parent


class ReleasePatchTests(unittest.TestCase):
    def test_patch_against_v3295_payload(self):
        fixture = Path("/tmp/z2se-v3295/Z2SE_UPDATE.zip")
        if not fixture.is_file():
            self.skipTest("v32.95 release fixture is not available")

        with tempfile.TemporaryDirectory() as directory:
            work = Path(directory)
            with zipfile.ZipFile(fixture) as archive:
                archive.extractall(work / "payload")

            result = subprocess.run(
                [sys.executable, str(ROOT / "release_patch.py"), "32.96"],
                cwd=work,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                check=False,
            )
            self.assertEqual(result.returncode, 0, result.stdout)

            app = (work / "payload" / "app.py").read_text(encoding="utf-8")
            self.assertIn('APP_VERSION = "32.96"', app)
            self.assertIn("def _v3296_play_inside", app)
            self.assertIn("libvlc_media_player_set_hwnd", app)
            self.assertIn("quick_403_refresh = bool(", app)
            self.assertLess(
                app.index("quick_403_refresh = bool("),
                app.index("needs_engine_repair = bool("),
            )

            compile(app, "app.py", "exec")
            manifest = json.loads(
                (work / "payload" / "update_manifest.json").read_text(encoding="utf-8")
            )
            self.assertEqual(manifest["version"], "32.96")
            self.assertEqual(
                manifest["files"][0]["size"],
                (work / "payload" / "app.py").stat().st_size,
            )


if __name__ == "__main__":
    unittest.main()
