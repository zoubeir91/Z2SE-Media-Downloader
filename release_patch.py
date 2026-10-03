from pathlib import Path
import ast
import hashlib
import json
import sys

version = sys.argv[1]
assert version == "33.13"
app_path = Path("payload/app.py")
text = app_path.read_text(encoding="utf-8-sig")


def replace_once(old, new):
    global text
    assert text.count(old) == 1, (old[:220], text.count(old))
    text = text.replace(old, new, 1)


replace_once('APP_VERSION = "33.12"', 'APP_VERSION = "33.13"')

# v33.12 correctly force-cancelled the selected job, but update_tree_status()
# marshals through gui_call. The deletion dialog could therefore run its
# terminal-state guard before the queued UI update changed En pause to Stopped.
# This path already runs on Tk's UI thread, so commit the terminal row state
# synchronously before continuing to the normal removal dialog.
old_cancel_then_delete = '''        for item_id in active_items:
            index = _job_index_for_item(item_id)
            if index is not None:
                cancel_download_job(index)
'''

new_cancel_then_delete = '''        for item_id in active_items:
            index = _job_index_for_item(item_id)
            if index is not None:
                cancel_download_job(index)

            # Release the row immediately for Retirer / file deletion. The
            # background process-tree reaper continues independently.
            _set_tree_status_and_cleanup(
                item_id,
                tr_dynamic("Stopped"),
            )
'''

replace_once(old_cancel_then_delete, new_cancel_then_delete)

ast.parse(text)
app_path.write_text(text, encoding="utf-8")
app_hash = hashlib.sha256(app_path.read_bytes()).hexdigest()
manifest_path = Path("payload/update_manifest.json")
manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
manifest["version"] = version
manifest["created_by"] = (
    "v33.13 commits the force-cancelled row state synchronously so Retirer "
    "cannot loop back to the old active-download warning"
)
manifest["files"][0]["sha256"] = app_hash
manifest["files"][0]["size"] = app_path.stat().st_size
manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
print("VERIFIED v33.13 app.py sha256", app_hash)
