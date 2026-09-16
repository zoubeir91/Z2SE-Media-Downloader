from pathlib import Path
import ast
import hashlib
import json
import re
import sys

TARGET_VERSION = "32.78"


def sha256_file(path):
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()

version = str(sys.argv[1] if len(sys.argv) > 1 else "").strip()
if version != TARGET_VERSION:
    raise SystemExit(f"This patch prepares only v{TARGET_VERSION}; got {version!r}")

app_path = Path("payload/app.py")
updater_path = Path("payload/z2se_updater.pyw")
manifest_path = Path("payload/update_manifest.json")
for required in (app_path, updater_path, manifest_path):
    if not required.is_file():
        raise FileNotFoundError(required)

text = app_path.read_text(encoding="utf-8-sig")
text, count = re.subn(r'APP_VERSION\s*=\s*"32\.77"', 'APP_VERSION = "32.78"', text, count=1)
if count != 1:
    raise RuntimeError("Could not update APP_VERSION 32.77 -> 32.78")

# v32.78 UI polish requested after v32.77:
# - keep the empty-state helper only while the downloads table is actually empty
# - shrink the premium top navigation icons slightly without changing their style
# - preserve the completed-media preview/play behavior from v32.71+

# The premium v32.76 icon renderer creates a 64px PhotoImage and draws it at 32,32.
# Reduce it to 54px and center it in a smaller 58px canvas. Keep all artwork/glow intact.
text = text.replace('def _v3276_make_nav_icon(kind, active=False, size=64):',
                    'def _v3276_make_nav_icon(kind, active=False, size=54):', 1)
text = text.replace('_v3276_make_nav_icon(kind, active=active, size=64)',
                    '_v3276_make_nav_icon(kind, active=active, size=54)', 1)
text = text.replace('width=64,\n        height=64,', 'width=58,\n        height=58,', 1)
text = text.replace('canvas.create_image(32, 32, image=photo)',
                    'canvas.create_image(29, 29, image=photo)', 1)

# Empty-state overlay: existing builds already have the visual helper. Its bug is that
# it can remain visible over real rows. Find its container from the known French text,
# then add one authoritative visibility synchronizer based on downloads_tree children.
marker = 'Aucun téléchargement'
pos = text.find(marker)
if pos < 0:
    raise RuntimeError("Could not locate empty-download state")

# Discover the Tk widget variable that owns the empty-state block by looking backwards
# for the nearest Frame/Label assignment used as parent around the marker.
window = text[max(0, pos - 7000):pos + 2500]
parents = re.findall(r'([A-Za-z_]\w*)\s*=\s*(?:tk\.|ttk\.)?(?:Frame|LabelFrame)\(', window)
if not parents:
    raise RuntimeError("Could not identify empty-state container")
empty_var = parents[-1]

# Inject a small sync helper immediately after the empty-state construction region.
# We do not destroy it: when the table becomes empty again it can be shown again.
insert_at = text.find('\n\n', pos)
if insert_at < 0:
    raise RuntimeError("Could not locate empty-state insertion point")
helper = f'''\n\n# v32.78: empty helper is visible only when there are no download rows.\ndef _v3278_sync_empty_download_state(event=None):\n    try:\n        has_rows = bool(downloads_tree.get_children())\n        if has_rows:\n            if {empty_var}.winfo_manager():\n                {empty_var}.place_forget()\n        else:\n            if not {empty_var}.winfo_manager():\n                {empty_var}.place(relx=0.5, rely=0.56, anchor="center")\n    except Exception:\n        pass\n\n'''
text = text[:insert_at] + helper + text[insert_at:]

# Treeview emits these events whenever rows are inserted/deleted/moved by Tk.
# Bind a lightweight sync and schedule one initial check after the UI is fully built.
bind_anchor = 'downloads_tree.bind("<<TreeviewSelect>>"'
bind_pos = text.find(bind_anchor)
if bind_pos >= 0:
    line_end = text.find('\n', bind_pos)
    text = text[:line_end+1] + 'downloads_tree.bind("<<TreeviewOpen>>", _v3278_sync_empty_download_state, add="+")\n' + text[line_end+1:]

# More reliable than depending on selection: poll only while UI is alive. This catches
# programmatic insert/delete operations from worker callbacks without touching downloader code.
loop_anchor = helper.rstrip() + '\n'
loop_repl = helper.rstrip() + '''\n\ndef _v3278_empty_state_watch():\n    try:\n        _v3278_sync_empty_download_state()\n        root.after(350, _v3278_empty_state_watch)\n    except Exception:\n        pass\n\nroot.after(150, _v3278_empty_state_watch)\n'''
text = text.replace(loop_anchor, loop_repl + '\n', 1)

# Keep versioned diagnostics current.
text = text.replace('Clean Editor v32.77:', 'Clean Editor v32.78:', 1)
text = text.replace('Clean Editor v32.77 warning:', 'Clean Editor v32.78 warning:', 1)
text = text.replace('Download details v32.77 warning:', 'Download details v32.78 warning:', 1)

ast.parse(text)
app_path.write_text(text, encoding="utf-8")
manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
manifest["product"] = "Z2SE Media Downloader"
manifest["version"] = TARGET_VERSION
manifest["created_by"] = "GitHub Actions / v32.78 smaller premium nav + row-aware empty state + functional completed-media preview preserved"
manifest["files"] = [
    {"path":"app.py","sha256":sha256_file(app_path),"size":app_path.stat().st_size},
    {"path":"z2se_updater.pyw","sha256":sha256_file(updater_path),"size":updater_path.stat().st_size},
]
manifest_path.write_text(json.dumps(manifest, indent=2)+"\n", encoding="utf-8")
print("Prepared Z2SE v32.78 UI polish")
