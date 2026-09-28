import json
import subprocess
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent

class ReleasePatchTests(unittest.TestCase):
    def test_patch_against_v3302_payload(self):
        fixture = Path("/tmp/z2se-v3302/Z2SE_UPDATE.zip")
        if not fixture.is_file():
            self.skipTest("v33.02 release fixture is not available")
        with tempfile.TemporaryDirectory() as directory:
            work = Path(directory)
            with zipfile.ZipFile(fixture) as archive:
                archive.extractall(work / "payload")
            result = subprocess.run(
                [sys.executable, str(ROOT / "release_patch.py"), "33.03"],
                cwd=work, text=True, stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT, check=False,
            )
            self.assertEqual(result.returncode, 0, result.stdout)
            app = (work / "payload" / "app.py").read_text(encoding="utf-8")
            self.assertIn('APP_VERSION = "33.03"', app)
            stop = app[app.index("def _v3296_stop_embedded_preview"):]
            stop = stop[:stop.index("def _v3299_preview_worker")]
            self.assertIn("process.wait(timeout=0.75)", stop)
            self.assertIn("process.kill()", stop)
            self.assertIn("stream.close()", stop)
            clear = app[app.index("def clear_download_list"):]
            clear = clear[:clear.index("def clear_bulk")]
            self.assertIn("_v3296_stop_embedded_preview()", clear)
            quit_block = app[app.index("def really_quit_app"):]
            quit_block = quit_block[:quit_block.index("def hide_mini_to_own_tray")]
            self.assertIn("_v3296_stop_embedded_preview()", quit_block)
            compile(app, "app.py", "exec")
            manifest = json.loads((work / "payload" / "update_manifest.json").read_text(encoding="utf-8"))
            self.assertEqual(manifest["version"], "33.03")
            self.assertEqual(manifest["files"][0]["size"], (work / "payload" / "app.py").stat().st_size)

if __name__ == "__main__":
    unittest.main()
