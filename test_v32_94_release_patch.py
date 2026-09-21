import json
import subprocess
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path


ROOT = Path(__file__).resolve().parent


class ReleasePatchTests(unittest.TestCase):
    def test_patch_against_v3296_payload(self):
        fixture = Path("/tmp/z2se-v3296/Z2SE_UPDATE.zip")
        if not fixture.is_file():
            self.skipTest("v32.96 release fixture is not available")

        with tempfile.TemporaryDirectory() as directory:
            work = Path(directory)
            with zipfile.ZipFile(fixture) as archive:
                archive.extractall(work / "payload")

            result = subprocess.run(
                [sys.executable, str(ROOT / "release_patch.py"), "32.97"],
                cwd=work,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                check=False,
            )
            self.assertEqual(result.returncode, 0, result.stdout)

            app = (work / "payload" / "app.py").read_text(encoding="utf-8")
            self.assertIn('APP_VERSION = "32.97"', app)
            self.assertIn("progress_stream_totals = {}", app)
            self.assertIn("v3297_video_host.winfo_id()", app)
            self.assertIn('r"SOFTWARE\\VideoLAN\\VLC"', app)
            self.assertIn("if is_done:\n            pct = 100.0", app)
            compile(app, "app.py", "exec")

            manifest = json.loads(
                (work / "payload" / "update_manifest.json").read_text(encoding="utf-8")
            )
            self.assertEqual(manifest["version"], "32.97")
            self.assertEqual(
                manifest["files"][0]["size"],
                (work / "payload" / "app.py").stat().st_size,
            )


if __name__ == "__main__":
    unittest.main()
