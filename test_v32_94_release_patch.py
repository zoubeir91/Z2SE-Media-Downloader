import json
import subprocess
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path


ROOT = Path(__file__).resolve().parent


class ReleasePatchTests(unittest.TestCase):
    def test_patch_against_v3293_payload(self):
        fixture = Path("/tmp/z2se-v3293/Z2SE_UPDATE.zip")
        if not fixture.is_file():
            self.skipTest("v32.93 release fixture is not available")

        with tempfile.TemporaryDirectory() as directory:
            work = Path(directory)
            with zipfile.ZipFile(fixture) as archive:
                archive.extractall(work / "payload")

            result = subprocess.run(
                [sys.executable, str(ROOT / "release_patch.py"), "32.94"],
                cwd=work,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                check=False,
            )
            self.assertEqual(result.returncode, 0, result.stdout)

            app = (work / "payload" / "app.py").read_text(encoding="utf-8")
            self.assertIn('APP_VERSION = "32.94"', app)
            self.assertEqual(app.count('"--continue"'), 2)
            self.assertEqual(app.count('"--part"'), 2)
            self.assertEqual(app.count('"http:exp=1:20"'), 2)
            self.assertEqual(app.count('"fragment:exp=1:20"'), 2)
            self.assertNotIn("yt-dlp-get-pot", app)
            self.assertIn("native yt-dlp plugin framework (bgutil 2.0.0)", app)

            compile(app, "app.py", "exec")
            manifest = json.loads(
                (work / "payload" / "update_manifest.json").read_text(encoding="utf-8")
            )
            self.assertEqual(manifest["version"], "32.94")
            self.assertEqual(
                manifest["files"][0]["size"],
                (work / "payload" / "app.py").stat().st_size,
            )


if __name__ == "__main__":
    unittest.main()
