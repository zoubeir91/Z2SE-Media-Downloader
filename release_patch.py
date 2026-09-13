from pathlib import Path
import hashlib
import json
import re
import sys

TARGET_VERSION = "32.67"


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

# V32.67 — BALANCED PREMIUM DARK
text, count = re.subn(r'APP_VERSION\s*=\s*"32\.66"', 'APP_VERSION = "32.67"', text, count=1)
if count != 1:
    raise RuntimeError("Could not update APP_VERSION 32.66 -> 32.67")

# Lift the v32.66 palette by roughly 10-15% while preserving the premium navy identity.
palette = {
    '#07111f': '#0b1726',
    '#0c1929': '#122238',
    '#071522': '#0a1a2a',
    '#10263d': '#18324d',
    '#1f3a57': '#2b4968',
    '#1687f8': '#238df5',
    '#edf5ff': '#f1f6fc',
    '#8fa8c5': '#a4b8cf',
    '#43d77d': '#49d982',
    '#f4f8ff': '#f6f9fd',
    '#94aac2': '#a9bbcf',
    '#11233a': '#172d47',
    '#dce9f8': '#e4edf7',
    '#183452': '#21415f',
    '#1b3b5e': '#264968',
    '#627890': '#748ba4',
    '#2a97ff': '#3299f7',
    '#0875de': '#147bdc',
    '#2a1c28': '#34232f',
    '#ffb8c2': '#ffc1ca',
    '#452333': '#512d3d',
    '#55273a': '#603247',
    '#a9bed7': '#b8c9dc',
    '#132740': '#1b3551',
    '#0a1524': '#101f32',
    '#eef6ff': '#f3f7fc',
    '#11243a': '#19314b',
    '#9eb6d0': '#b1c4d8',
    '#0b1727': '#112137',
    '#b9cbe0': '#c8d6e6',
    '#12243a': '#1a314b',
    '#153b63': '#20507e',
    '#102238': '#172f49',
    '#0d1b2d': '#14263c',
    '#173a60': '#224d77',
}
for old, new in palette.items():
    text = text.replace(old, new)

text = text.replace(
    '# V32.66 — PREMIUM BASIC UI REFRESH',
    '# V32.66/32.67 — PREMIUM BASIC UI + BALANCED DARK',
    1,
)
text = text.replace(
    'Clean Editor v32.66: startup draft/PART rows cleared.',
    'Clean Editor v32.67: startup draft/PART rows cleared.',
    1,
)
text = text.replace(
    'Clean Editor v32.66 warning:',
    'Clean Editor v32.67 warning:',
    1,
)

app_path.write_text(text, encoding="utf-8")

manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
manifest["product"] = "Z2SE Media Downloader"
manifest["version"] = TARGET_VERSION
manifest["created_by"] = "GitHub Actions / v32.67 balanced premium dark UI"
manifest["files"] = [
    {"path": "app.py", "sha256": sha256_file(app_path), "size": app_path.stat().st_size},
    {"path": "z2se_updater.pyw", "sha256": sha256_file(updater_path), "size": updater_path.stat().st_size},
]
manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")

print("Prepared Z2SE v32.67 balanced premium dark UI")
print("app.py", app_path.stat().st_size, sha256_file(app_path))
print("z2se_updater.pyw", updater_path.stat().st_size, sha256_file(updater_path))
