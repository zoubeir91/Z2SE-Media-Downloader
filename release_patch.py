from pathlib import Path
import hashlib
import json
import re
import sys

TARGET_VERSION = "32.51"


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

# V32.51 — bgutil 2.0.0 already binds to localhost by default. Its CLI does
# not support --host, so remove the unsupported argument introduced in 32.50.
text, count = re.subn(
    r'APP_VERSION\s*=\s*"32\.50"',
    'APP_VERSION = "32.51"',
    text,
    count=1,
)
if count != 1:
    raise RuntimeError("Could not update APP_VERSION 32.50 -> 32.51")

old_command = '''                    "../src/main.ts",\n                    "--host",\n                    "127.0.0.1",\n'''
new_command = '''                    "../src/main.ts",\n'''
if old_command not in text:
    raise RuntimeError("Could not locate the v32.50 unsupported --host argument")
text = text.replace(old_command, new_command, 1)

# Keep the security wording accurate: localhost is provided by bgutil 2.0.0's
# secure default rather than by a Z2SE CLI override.
text = text.replace(
    'log("PO Token provider v2.0.0 بدا وخدام على localhost فقط ✅")',
    'log("PO Token provider v2.0.0 بدا وخدام بالـ localhost الآمن الافتراضي ✅")',
    1,
)

app_path.write_text(text, encoding="utf-8")

manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
manifest["product"] = "Z2SE Media Downloader"
manifest["version"] = TARGET_VERSION
manifest["created_by"] = "GitHub Actions / v32.51 bgutil startup compatibility fix"
manifest["files"] = [
    {
        "path": "app.py",
        "sha256": sha256_file(app_path),
        "size": app_path.stat().st_size,
    },
    {
        "path": "z2se_updater.pyw",
        "sha256": sha256_file(updater_path),
        "size": updater_path.stat().st_size,
    },
]
manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")

print("Prepared Z2SE v32.51 bgutil startup fix")
print("app.py", app_path.stat().st_size, sha256_file(app_path))
print("z2se_updater.pyw", updater_path.stat().st_size, sha256_file(updater_path))
