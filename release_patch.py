from pathlib import Path
import ast
import hashlib
import json
import re
import sys

TARGET_VERSION = "32.79"


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
text, count = re.subn(r'APP_VERSION\s*=\s*"32\.78"', 'APP_VERSION = "32.79"', text, count=1)
if count != 1:
    raise RuntimeError("Could not update APP_VERSION 32.78 -> 32.79")

# v32.78's generic container discovery hid the wrong widget. Remove that whole
# experimental block and replace it with a direct, geometry-independent solution.
start = text.find('# v32.78: empty helper is visible only when there are no download rows.')
if start >= 0:
    end = text.find('root.after(150, _v3278_empty_state_watch)', start)
    if end >= 0:
        end = text.find('\n', end)
        text = text[:start] + text[end + 1:]
text = text.replace('downloads_tree.bind("<<TreeviewOpen>>", _v3278_sync_empty_download_state, add="+")\n', '', 1)

# Directly identify every widget belonging to the centered empty-state by walking
# upward from the label itself. At runtime we hide/show the top-most descendant whose
# parent is the downloads area. This avoids relying on a guessed Python variable name.
marker = 'Aucun téléchargement'
pos = text.find(marker)
if pos < 0:
    raise RuntimeError("Could not locate empty-download state")

# Locate the actual Label variable containing the marker.
line_start = text.rfind('\n', 0, pos) + 1
line_end = text.find('\n', pos)
marker_line = text[line_start:line_end]
m = re.search(r'([A-Za-z_]\w*)\s*=\s*(?:tk\.|ttk\.)?Label\(', marker_line)
empty_label_var = m.group(1) if m else None
if not empty_label_var:
    # Multi-line Label construction: inspect a short region before the text.
    before = text[max(0, pos-800):pos]
    labels = re.findall(r'([A-Za-z_]\w*)\s*=\s*(?:tk\.|ttk\.)?Label\(', before)
    if not labels:
        raise RuntimeError("Could not identify Aucun téléchargement label")
    empty_label_var = labels[-1]

insert_at = text.find('\n\n', pos)
if insert_at < 0:
    raise RuntimeError("Could not locate insertion point after empty state")

helper = f'''\n\n# v32.79: authoritative empty-state visibility.\n_v3279_empty_widgets = []\ntry:\n    _w = {empty_label_var}\n    _parent = _w.master\n    # The helper is a centered overlay. Capture its siblings in the same overlay parent\n    # (icon, title, subtitle and VIDEO/AUDIO/PART/HLS badges), but never tree/table widgets.\n    for _child in _parent.winfo_children():\n        _v3279_empty_widgets.append(_child)\nexcept Exception:\n    pass\n\ndef _v3279_set_empty_visible(show):\n    for _w in list(_v3279_empty_widgets):\n        try:\n            mgr = _w.winfo_manager()\n            if show:\n                if not mgr:\n                    # Restore widgets using their last place geometry when available.\n                    info = getattr(_w, "_v3279_place_info", None)\n                    if info:\n                        _w.place(**info)\n            else:\n                if mgr == "place":\n                    _w._v3279_place_info = _w.place_info()\n                    _w.place_forget()\n                elif mgr == "pack":\n                    _w.pack_forget()\n                elif mgr == "grid":\n                    _w.grid_remove()\n        except Exception:\n            pass\n\ndef _v3279_empty_state_watch():\n    try:\n        _v3279_set_empty_visible(not bool(downloads_tree.get_children()))\n        root.after(150, _v3279_empty_state_watch)\n    except Exception:\n        pass\n\nroot.after(100, _v3279_empty_state_watch)\n'''
text = text[:insert_at] + helper + text[insert_at:]

# Icons: v32.78 only reduced the inner generated image. The screenshot proves the
# navigation still feels too large because the surrounding canvas/tile stayed tall.
# Make the visible artwork clearly smaller (44px), canvas 50px and reduce vertical padding.
text = text.replace('def _v3276_make_nav_icon(kind, active=False, size=54):',
                    'def _v3276_make_nav_icon(kind, active=False, size=44):', 1)
text = text.replace('_v3276_make_nav_icon(kind, active=active, size=54)',
                    '_v3276_make_nav_icon(kind, active=active, size=44)', 1)
text = text.replace('width=58,\n        height=58,', 'width=50,\n        height=50,', 1)
text = text.replace('canvas.create_image(29, 29, image=photo)',
                    'canvas.create_image(25, 25, image=photo)', 1)
# Reduce top menu height and padding only where the premium nav values exist.
text = text.replace('height=126', 'height=108', 1)
text = text.replace('pady=(8, 5)', 'pady=(4, 3)', 1)

# Keep versioned diagnostics current.
text = text.replace('Clean Editor v32.78:', 'Clean Editor v32.79:', 1)
text = text.replace('Clean Editor v32.78 warning:', 'Clean Editor v32.79 warning:', 1)
text = text.replace('Download details v32.78 warning:', 'Download details v32.79 warning:', 1)

ast.parse(text)
app_path.write_text(text, encoding="utf-8")
manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
manifest["product"] = "Z2SE Media Downloader"
manifest["version"] = TARGET_VERSION
manifest["created_by"] = "GitHub Actions / v32.79 direct empty-overlay fix + genuinely smaller premium navigation"
manifest["files"] = [
    {"path":"app.py","sha256":sha256_file(app_path),"size":app_path.stat().st_size},
    {"path":"z2se_updater.pyw","sha256":sha256_file(updater_path),"size":updater_path.stat().st_size},
]
manifest_path.write_text(json.dumps(manifest, indent=2)+"\n", encoding="utf-8")
print("Prepared Z2SE v32.79 direct UI fix")
