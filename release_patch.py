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

# V32.68: improve only the download-list readability. Keep the balanced-dark
# palette and downloader engine untouched. Some historical row tags can carry
# old dark foreground colors, so make the Treeview default stronger and force
# all existing row tags to readable semantic colors after the tree is built.
text = text.replace(
    'foreground="#e4edf7", rowheight=34, borderwidth=0,',
    'foreground="#f2f6fb", rowheight=34, borderwidth=0,',
    1,
)

contrast_helper = '''\n# V32.68 — DOWNLOAD LIST HIGH-CONTRAST ROWS\ndef _v3268_fix_download_list_contrast():\n    try:\n        # Historical versions used several tag names. Preserve their meaning,\n        # but never allow near-background text in the premium dark theme.\n        semantic = {\n            "done": "#59df91", "completed": "#59df91", "success": "#59df91",\n            "error": "#ff8193", "failed": "#ff8193", "failure": "#ff8193",\n            "active": "#67b7ff", "downloading": "#67b7ff", "running": "#67b7ff",\n            "paused": "#f2c96d", "waiting": "#f2c96d", "queued": "#f2c96d",\n            "pending": "#f2c96d",\n        }\n        for tag in bulk_tree.tag_names():\n            key = str(tag).lower()\n            color = semantic.get(key)\n            if color is None:\n                if any(word in key for word in ("error", "fail")):\n                    color = "#ff8193"\n                elif any(word in key for word in ("done", "complete", "success", "term")):\n                    color = "#59df91"\n                elif any(word in key for word in ("pause", "wait", "queue", "pending", "attente")):\n                    color = "#f2c96d"\n                elif any(word in key for word in ("download", "active", "run", "progress")):\n                    color = "#67b7ff"\n                else:\n                    color = "#e7eef7"\n            try:\n                bulk_tree.tag_configure(tag, foreground=color)\n            except Exception:\n                pass\n    except Exception:\n        pass\n\ntry:\n    _v3268_fix_download_list_contrast()\nexcept Exception:\n    pass\n\n'''

# Place the fix after download tree construction, before normal runtime startup.
anchor = '# V32.18: migrate/relink legacy history'
if anchor not in text:
    raise RuntimeError("Download-list runtime anchor missing")
text = text.replace(anchor, contrast_helper + '\n' + anchor, 1)

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
