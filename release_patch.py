from pathlib import Path
import hashlib
import json
import re
import sys

TARGET_VERSION = "32.68"


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
text, count = re.subn(r'APP_VERSION\s*=\s*"32\.67"', 'APP_VERSION = "32.68"', text, count=1)
if count != 1:
    raise RuntimeError("Could not update APP_VERSION 32.67 -> 32.68")

# V32.68 — DOWNLOAD LIST HIGH CONTRAST
# Keep the v32.67 balanced-dark palette. Only strengthen the list text and the
# existing semantic row tags. This deliberately avoids any fragile startup
# anchor so the patch remains safe across recent UI revisions.
text = text.replace(
    'foreground="#e4edf7", rowheight=34, borderwidth=0,',
    'foreground="#f2f6fb", rowheight=34, borderwidth=0,',
    1,
)

row_colors = {
    'bulk_tree.tag_configure("active", foreground="#17365d")':
        'bulk_tree.tag_configure("active", foreground="#67b7ff")',
    'bulk_tree.tag_configure("paused", foreground="#8a5a00")':
        'bulk_tree.tag_configure("paused", foreground="#f2c96d")',
    'bulk_tree.tag_configure("done", foreground="#16733c")':
        'bulk_tree.tag_configure("done", foreground="#59df91")',
    'bulk_tree.tag_configure("error", foreground="#a12622")':
        'bulk_tree.tag_configure("error", foreground="#ff8193")',
    'bulk_tree.tag_configure("cancelled", foreground="#666666")':
        'bulk_tree.tag_configure("cancelled", foreground="#aebdce")',
}
for old, new in row_colors.items():
    text = text.replace(old, new)

text = text.replace('Clean Editor v32.67: startup draft/PART rows cleared.', 'Clean Editor v32.68: startup draft/PART rows cleared.', 1)
text = text.replace('Clean Editor v32.67 warning:', 'Clean Editor v32.68 warning:', 1)

app_path.write_text(text, encoding="utf-8")

manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
manifest["product"] = "Z2SE Media Downloader"
manifest["version"] = TARGET_VERSION
manifest["created_by"] = "GitHub Actions / v32.68 high-contrast download list"
manifest["files"] = [
    {"path": "app.py", "sha256": sha256_file(app_path), "size": app_path.stat().st_size},
    {"path": "z2se_updater.pyw", "sha256": sha256_file(updater_path), "size": updater_path.stat().st_size},
]
manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")

print("Prepared Z2SE v32.68 high-contrast download list")
print("app.py", app_path.stat().st_size, sha256_file(app_path))
print("z2se_updater.pyw", updater_path.stat().st_size, sha256_file(updater_path))
