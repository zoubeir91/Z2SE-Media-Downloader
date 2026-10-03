from pathlib import Path
import ast
import hashlib
import json
import sys

version = sys.argv[1]
assert version == "33.12"
app_path = Path("payload/app.py")
text = app_path.read_text(encoding="utf-8-sig")


def replace_once(old, new):
    global text
    assert text.count(old) == 1, (old[:220], text.count(old))
    text = text.replace(old, new, 1)


replace_once('APP_VERSION = "33.11"', 'APP_VERSION = "33.12"')

# Delete used to reject a paused/active row before it could reach v33.11's
# force-cancel path. Confirm once, force-cancel, then continue to the normal
# safe list/file deletion dialog.
old_delete_guard = '''    if any(
        not _mini_is_terminal_status(
            _item_status(item_id)
        )
        for item_id in items
    ):
        messagebox.showinfo(
            tr("Delete download"),
            tr("One or more selected downloads are still active. Stop or cancel them first."),
        )
        return "break"
'''

new_delete_guard = '''    active_items = [
        item_id
        for item_id in items
        if not _mini_is_terminal_status(
            _item_status(item_id)
        )
    ]

    if active_items:
        confirmed = messagebox.askyesno(
            tr("Delete download"),
            (
                "هاد التحميل مازال خدام ولا واقف مؤقتاً. "
                "نحبسوه بالقوة ونكملو المسح؟"
                if len(active_items) == 1
                else
                f"كاينين {len(active_items)} تحميلات خدامين ولا واقفين مؤقتاً. "
                "نحبسوهم بالقوة ونكملو المسح؟"
            ),
            icon="warning",
        )

        if not confirmed:
            return "break"

        for item_id in active_items:
            index = _job_index_for_item(item_id)
            if index is not None:
                cancel_download_job(index)
'''

replace_once(old_delete_guard, new_delete_guard)

ast.parse(text)
app_path.write_text(text, encoding="utf-8")
app_hash = hashlib.sha256(app_path.read_bytes()).hexdigest()
manifest_path = Path("payload/update_manifest.json")
manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
manifest["version"] = version
manifest["created_by"] = (
    "v33.12 lets Delete force-cancel paused, active, or stuck downloads first, "
    "then immediately continue with safe list/file removal"
)
manifest["files"][0]["sha256"] = app_hash
manifest["files"][0]["size"] = app_path.stat().st_size
manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
print("VERIFIED v33.12 app.py sha256", app_hash)
