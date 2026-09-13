from pathlib import Path
import hashlib
import json
import re
import sys

TARGET_VERSION = "32.65"


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

# ----------------------------------------------------------------------
# V32.65 — FORCE CLEAN MANUAL EDITOR AFTER STARTUP RESTORE
# ----------------------------------------------------------------------
text, count = re.subn(
    r'APP_VERSION\s*=\s*"32\.64"',
    'APP_VERSION = "32.65"',
    text,
    count=1,
)
if count != 1:
    raise RuntimeError("Could not update APP_VERSION 32.64 -> 32.65")

# Field evidence showed the restored rows contain 00:00:00 -> 00:10:00.
# Browser PART requests leave From/To empty, so the recurring rows are coming
# from startup state restoration rather than Browser Bridge replay. Keep the
# real download history/queue restoration, but always reset the manual editor
# to one blank row afterwards on normal manual/update startup.
startup_anchor = '''# V32.21: upgrade older history rows to exact file links whenever the match\n# is unambiguous.\nrelink_legacy_history_files()\n'''
startup_replacement = startup_anchor + '''\n# V32.65: manual input rows are drafts, not download history. Never restore\n# old PART URLs/times into the editor after a normal restart or app update.\nif not BROWSER_LAUNCH_MODE:\n    try:\n        clear_bulk()\n        log("🧹 Clean Editor v32.65: startup draft/PART rows cleared.")\n    except Exception as exc:\n        log(f"Clean Editor v32.65 warning: {exc}")\n'''
if startup_anchor not in text:
    raise RuntimeError("Startup history/relink anchor missing")
text = text.replace(startup_anchor, startup_replacement, 1)

app_path.write_text(text, encoding="utf-8")

manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
manifest["product"] = "Z2SE Media Downloader"
manifest["version"] = TARGET_VERSION
manifest["created_by"] = "GitHub Actions / v32.65 force-clean manual editor after startup restore"
manifest["files"] = [
    {"path": "app.py", "sha256": sha256_file(app_path), "size": app_path.stat().st_size},
    {"path": "z2se_updater.pyw", "sha256": sha256_file(updater_path), "size": updater_path.stat().st_size},
]
manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")

print("Prepared Z2SE v32.65 clean manual editor startup")
print("app.py", app_path.stat().st_size, sha256_file(app_path))
print("z2se_updater.pyw", updater_path.stat().st_size, sha256_file(updater_path))
