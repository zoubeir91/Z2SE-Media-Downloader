from pathlib import Path
import hashlib
import json
import re
import sys

TARGET_VERSION = "32.59"


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
# V32.59 — YOUTUBE FAST START + FASTER AUTO PART DECISION
# ----------------------------------------------------------------------
text, count = re.subn(
    r'APP_VERSION\s*=\s*"32\.58"',
    'APP_VERSION = "32.59"',
    text,
    count=1,
)
if count != 1:
    raise RuntimeError("Could not update APP_VERSION 32.58 -> 32.59")

# The v32.58 runtime journal proves that Browser Bridge spends ~35-40 seconds
# before yt-dlp itself starts transferring. Startup checks already own provider
# health and Smart Recovery refreshes PO/client state only after a real access
# failure, so repeating ensure_pot_fast() before every healthy YouTube browser
# job is pure latency. Remove only the browser-worker preflight call; recovery
# behavior remains untouched.
browser_start = text.find("def browser_download_job_worker(job):")
if browser_start < 0:
    raise RuntimeError("Browser worker anchor missing")
browser_end = text.find("\ndef queue_browser_download(", browser_start)
if browser_end < 0:
    raise RuntimeError("Browser worker end anchor missing")
browser_block = text[browser_start:browser_end]

browser_pot_old = '''        if _single_url_needs_pot_provider(page_url):\n            ensure_pot_fast()\n        else:\n            log("Browser download: skipping YouTube PO Token startup for non-YouTube URL ⚡")\n'''
browser_pot_new = '''        if _single_url_needs_pot_provider(page_url):\n            log(\n                "Browser YouTube: startup PO preflight skipped ⚡ "\n                "(startup health + failure-triggered Smart Recovery active)"\n            )\n        else:\n            log("Browser download: skipping YouTube PO Token startup for non-YouTube URL ⚡")\n'''
if browser_pot_old not in browser_block:
    raise RuntimeError("Browser per-download PO preflight anchor missing")
browser_block = browser_block.replace(browser_pot_old, browser_pot_new, 1)
text = text[:browser_start] + browser_block + text[browser_end:]

# Single Download had the same unconditional preflight in older builds. Keep
# the provider warm at application startup and let the existing Smart Recovery
# path repair it only when a real 403/PO/auth failure occurs.
single_start = text.find("def single_worker(")
if single_start >= 0:
    single_end = text.find("\ndef ", single_start + 8)
    if single_end < 0:
        single_end = len(text)
    single_block = text[single_start:single_end]
    single_old = "        ensure_pot_fast()\n"
    if single_old in single_block:
        single_block = single_block.replace(
            single_old,
            '        log("Single download: startup PO preflight skipped ⚡")\n',
            1,
        )
        text = text[:single_start] + single_block + text[single_end:]

# AUTO PART was deliberately requiring Turbo to beat the realtime section
# estimate by 22% before choosing it. In the supplied 10-minute PART test it
# estimated SECTION≈315s and native FULL≈256s, yet still chose SECTION and ran
# around 2x realtime. For an "AUTO FASTEST" mode that is too conservative.
# Choose Turbo whenever it is predicted to be at least ~8% faster. Tiny clips
# from huge sources still remain on SECTION when full-cache is clearly slower.
old_part_threshold = "< section_est_seconds * 0.78"
if text.count(old_part_threshold) != 1:
    raise RuntimeError("AUTO PART strategy threshold anchor missing")
text = text.replace(old_part_threshold, "< section_est_seconds * 0.92", 1)

# Update the nearby documentation so diagnostics describe the real policy.
text = text.replace(
    "Full-cache is chosen only when its estimated completion time is clearly\n    better. For tiny clips from huge videos, section mode remains available.",
    "Full-cache is chosen when its estimated completion time is meaningfully\n    faster. For tiny clips from huge videos, section mode remains available.",
    1,
)

app_path.write_text(text, encoding="utf-8")

manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
manifest["product"] = "Z2SE Media Downloader"
manifest["version"] = TARGET_VERSION
manifest["created_by"] = "GitHub Actions / v32.59 YouTube fast-start + faster AUTO PART strategy"
manifest["files"] = [
    {"path": "app.py", "sha256": sha256_file(app_path), "size": app_path.stat().st_size},
    {"path": "z2se_updater.pyw", "sha256": sha256_file(updater_path), "size": updater_path.stat().st_size},
]
manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")

print("Prepared Z2SE v32.59 YouTube startup/PART speed fixes")
print("app.py", app_path.stat().st_size, sha256_file(app_path))
print("z2se_updater.pyw", updater_path.stat().st_size, sha256_file(updater_path))
