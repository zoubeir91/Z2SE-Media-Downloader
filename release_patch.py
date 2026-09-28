from pathlib import Path
import ast
import hashlib
import json
import sys

version = sys.argv[1]
assert version == "33.04"
app_path = Path("payload/app.py")
text = app_path.read_text(encoding="utf-8-sig")

def replace_once(old, new):
    global text
    assert text.count(old) == 1, (old[:180], text.count(old))
    text = text.replace(old, new, 1)

replace_once('APP_VERSION = "33.03"', 'APP_VERSION = "33.04"')

# Bulk Recycle Bin action: release any embedded preview before Windows tries
# to move the selected files, then retry once for a just-released handle.
replace_once(
    '''    failed_paths = {}

    for normalized, path in unique_files.items():
        ok, error = _move_file_to_recycle_bin(
            path
        )

        if not ok:
''',
    '''    try:
        _v3296_stop_embedded_preview()
        v3271_preview_enabled["path"] = None
    except Exception:
        pass

    failed_paths = {}

    for normalized, path in unique_files.items():
        ok, error = _move_file_to_recycle_bin(path)
        if not ok:
            # Antivirus/Explorer can observe the old handle for a fraction of
            # a second after FFmpeg exits. One bounded retry is safe here.
            time.sleep(0.15)
            ok, error = _move_file_to_recycle_bin(path)

        if not ok:
''',
)

# Single-file context action follows the same stop-before-delete ordering.
replace_once(
    '''    if not confirmed:
        return

    ok, error = _move_file_to_recycle_bin(path)

    if not ok:
''',
    '''    if not confirmed:
        return

    try:
        _v3296_stop_embedded_preview()
        v3271_preview_enabled["path"] = None
    except Exception:
        pass

    ok, error = _move_file_to_recycle_bin(path)
    if not ok:
        time.sleep(0.15)
        ok, error = _move_file_to_recycle_bin(path)

    if not ok:
''',
)

ast.parse(text)
app_path.write_text(text, encoding="utf-8")
app_hash = hashlib.sha256(app_path.read_bytes()).hexdigest()
manifest_path = Path("payload/update_manifest.json")
manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
manifest["version"] = version
manifest["created_by"] = (
    "v33.04 stops embedded preview before both single and bulk Recycle Bin "
    "operations and retries once after releasing Windows media handles"
)
manifest["files"][0]["sha256"] = app_hash
manifest["files"][0]["size"] = app_path.stat().st_size
manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
print("VERIFIED v33.04 app.py sha256", app_hash)
