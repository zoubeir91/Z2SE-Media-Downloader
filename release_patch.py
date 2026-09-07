from pathlib import Path
import hashlib
import json
import os
import re
import sys

TARGET_VERSION = "32.46"


def replace_once(text, old, new, label):
    if old not in text:
        raise RuntimeError(f"Patch anchor missing: {label}")
    return text.replace(old, new, 1)


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
helpers_path = Path("v3246_helpers.txt")
worker_insert_path = Path("v3246_worker_insert.txt")

for required in (app_path, updater_path, manifest_path, helpers_path, worker_insert_path):
    if not required.is_file():
        raise FileNotFoundError(required)

text = app_path.read_text(encoding="utf-8-sig")

# Version bump.
text, count = re.subn(
    r'APP_VERSION\s*=\s*"32\.45"',
    'APP_VERSION = "32.46"',
    text,
    count=1,
)
if count != 1:
    raise RuntimeError("Could not update APP_VERSION 32.45 -> 32.46")

# Smart Meta resolver needs base64 for efg metadata and query-pair editing.
if not re.search(r"^import base64\s*$", text, flags=re.MULTILINE):
    text = replace_once(text, "import json\n", "import json\nimport base64\n", "import base64")

old_url_import = "from urllib.parse import urlparse, parse_qs, urlsplit, urlunsplit, urljoin"
new_url_import = "from urllib.parse import urlparse, parse_qs, parse_qsl, urlencode, urlsplit, urlunsplit, urljoin"
if new_url_import not in text:
    text = replace_once(text, old_url_import, new_url_import, "urllib.parse helpers")

# Insert deterministic self-healing Meta/Facebook helper layer before the
# existing generic browser candidate resolver.
helpers = helpers_path.read_text(encoding="utf-8").strip() + "\n\n"
if "def _fb_strip_range(" not in text:
    helper_anchor = "def _browser_media_candidate_urls(primary_url, media_candidates):"
    position = text.find(helper_anchor)
    if position < 0:
        raise RuntimeError("Meta helper insertion anchor missing")
    text = text[:position] + helpers + text[position:]

# Insert the smart Facebook recovery stage before the generic candidate loop.
worker_insert = worker_insert_path.read_text(encoding="utf-8").rstrip() + "\n"
if "V32.46 SMART META SELF-HEALING" not in text:
    resolver_anchor = (
        "            resolver_urls = _browser_media_candidate_urls(\n"
        "                normalized_media_url,\n"
        "                media_candidates,\n"
        "            )\n"
    )
    position = text.find(resolver_anchor)
    if position < 0:
        raise RuntimeError("Browser worker resolver anchor missing")
    text = text[:position] + worker_insert + text[position:]

# Let the extension send richer candidate sets when a page exposes many DASH
# fragments. The bridge remains local-only and still validates the payload.
text = text.replace(
    "if length <= 0 or length > 65536:",
    "if length <= 0 or length > 524288:",
    1,
)

# Keep more captured candidates available to the final generic resolver too.
text = text.replace("    return result[:12]\n", "    return result[:32]\n", 1)

# Small robustness fix seen in the user's v32.45 log: tolerate a UTF-8 BOM in
# JSON config files by reading with utf-8-sig where the update config is read.
text = text.replace(
    'with open(APP_UPDATE_CONFIG_FILE, "r", encoding="utf-8") as handle:',
    'with open(APP_UPDATE_CONFIG_FILE, "r", encoding="utf-8-sig") as handle:',
)

app_path.write_text(text, encoding="utf-8", newline="\n")

# Refresh manifest after the patch.
manifest = json.loads(manifest_path.read_text(encoding="utf-8-sig"))
manifest["version"] = TARGET_VERSION
manifest["created_by"] = "GitHub Actions / v32.46 Smart Self-Healing Meta Resolver"

file_map = {
    "app.py": app_path,
    "z2se_updater.pyw": updater_path,
}

entries = []
for name, path in file_map.items():
    entries.append(
        {
            "path": name,
            "sha256": sha256_file(path),
            "size": os.path.getsize(path),
        }
    )
manifest["files"] = entries
manifest_path.write_text(
    json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
    encoding="utf-8",
)

print(f"Prepared Z2SE v{TARGET_VERSION} Smart Self-Healing Meta Resolver")
