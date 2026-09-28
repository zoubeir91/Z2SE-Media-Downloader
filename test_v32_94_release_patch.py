import json
import subprocess
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent

class ReleasePatchTests(unittest.TestCase):
    def test_patch_against_v3303_payload(self):
        fixture = Path("/tmp/z2se-v3303/Z2SE_UPDATE.zip")
        if not fixture.is_file():
            self.skipTest("v33.03 release fixture is not available")
        with tempfile.TemporaryDirectory() as directory:
            work = Path(directory)
            with zipfile.ZipFile(fixture) as archive:
                archive.extractall(work / "payload")
            result = subprocess.run(
                [sys.executable, str(ROOT / "release_patch.py"), "33.04"],
                cwd=work, text=True, stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT, check=False,
            )
            self.assertEqual(result.returncode, 0, result.stdout)
            app = (work / "payload" / "app.py").read_text(encoding="utf-8")
            self.assertIn('APP_VERSION = "33.04"', app)
            bulk_delete = app[app.index("def delete_selected_files_from_pc"):]
            bulk_delete = bulk_delete[:bulk_delete.index("def delete_selected_with_keyboard_v15")]
            self.assertLess(bulk_delete.index("_v3296_stop_embedded_preview()"), bulk_delete.index("_move_file_to_recycle_bin(path)"))
            self.assertIn("time.sleep(0.15)", bulk_delete)
            single_delete = app[app.index("def context_delete_file_from_pc"):]
            single_delete = single_delete[:single_delete.index("def context_properties")]
            self.assertLess(single_delete.index("_v3296_stop_embedded_preview()"), single_delete.index("_move_file_to_recycle_bin(path)"))
            self.assertIn("time.sleep(0.15)", single_delete)
            compile(app, "app.py", "exec")
            manifest = json.loads((work / "payload" / "update_manifest.json").read_text(encoding="utf-8"))
            self.assertEqual(manifest["version"], "33.04")
            self.assertEqual(manifest["files"][0]["size"], (work / "payload" / "app.py").stat().st_size)

if __name__ == "__main__":
    unittest.main()
