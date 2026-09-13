from pathlib import Path
import hashlib
import json
import re
import sys

TARGET_VERSION = "32.64"


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
# V32.64 — STRONGER CLEAN STARTUP / STALE PART REPLAY PROTECTION
# ----------------------------------------------------------------------
text, count = re.subn(
    r'APP_VERSION\s*=\s*"32\.63"',
    'APP_VERSION = "32.64"',
    text,
    count=1,
)
if count != 1:
    raise RuntimeError("Could not update APP_VERSION 32.63 -> 32.64")

# v32.63 used a 10-second startup guard. The real browser extension can replay
# old PART/open requests later than that, so stale links still reappeared.
# v32.64 keeps a normal manual/update launch protected for 120 seconds when the
# request has no freshness timestamp. If an extension supplies a timestamp, a
# genuinely fresh request is accepted immediately while old timestamps remain
# rejected. Chrome-triggered launches stay exempt.
old_guard = '''_STARTUP_PART_REPLAY_GUARD_SECONDS = 10.0\n'''
new_guard = '''_STARTUP_PART_REPLAY_GUARD_SECONDS = 120.0\n'''
if old_guard not in text:
    raise RuntimeError("v32.63 startup replay guard anchor missing")
text = text.replace(old_guard, new_guard, 1)

old_func = '''def _browser_request_is_stale_startup_part(payload, action):\n    if str(action or "").strip().lower() not in {"open", "part"}:\n        return False\n\n    if BROWSER_LAUNCH_MODE:\n        return False\n\n    # Prefer an explicit request timestamp when an extension supplies one.\n    # Accept common seconds or milliseconds epoch formats.\n    for key in ("timestamp", "sent_at", "created_at", "ts"):\n        raw = payload.get(key) if isinstance(payload, dict) else None\n        if raw in (None, ""):\n            continue\n        try:\n            stamp = float(raw)\n            if stamp > 10_000_000_000:\n                stamp /= 1000.0\n            if stamp > 1_000_000_000 and time.time() - stamp > 30.0:\n                return True\n        except Exception:\n            pass\n\n    try:\n        return (\n            time.monotonic() - _Z2SE_STARTED_MONOTONIC\n            < _STARTUP_PART_REPLAY_GUARD_SECONDS\n        )\n    except Exception:\n        return False\n'''

new_func = '''def _browser_request_is_stale_startup_part(payload, action):\n    if str(action or "").strip().lower() not in {"open", "part"}:\n        return False\n\n    if BROWSER_LAUNCH_MODE:\n        return False\n\n    # A timestamp is authoritative when supplied. Fresh browser clicks are\n    # accepted immediately; stale queued/replayed requests are rejected.\n    found_timestamp = False\n    for key in ("timestamp", "sent_at", "created_at", "ts"):\n        raw = payload.get(key) if isinstance(payload, dict) else None\n        if raw in (None, ""):\n            continue\n        try:\n            stamp = float(raw)\n            if stamp > 10_000_000_000:\n                stamp /= 1000.0\n            if stamp > 1_000_000_000:\n                found_timestamp = True\n                age = time.time() - stamp\n                if age > 30.0:\n                    return True\n                if age >= -10.0:\n                    return False\n        except Exception:\n            pass\n\n    # Current V15 requests do not always carry a timestamp. During a normal\n    # manual/update launch, treat those timestamp-less PART/open messages as\n    # startup replays for a long quiet window. This is intentionally limited\n    # to open/part; full-download bridge requests are not blocked.\n    if not found_timestamp:\n        try:\n            return (\n                time.monotonic() - _Z2SE_STARTED_MONOTONIC\n                < _STARTUP_PART_REPLAY_GUARD_SECONDS\n            )\n        except Exception:\n            return False\n\n    return False\n'''

if old_func not in text:
    raise RuntimeError("v32.63 replay-classifier anchor missing")
text = text.replace(old_func, new_func, 1)

# Make the log explicitly identify the stronger v32.64 rule for diagnosis.
text = text.replace(
    '"🧹 Clean Startup: ignored stale Browser Bridge PART/open replay: "',
    '"🧹 Clean Startup v32.64: ignored stale Browser Bridge PART/open replay: "',
    1,
)

app_path.write_text(text, encoding="utf-8")

manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
manifest["product"] = "Z2SE Media Downloader"
manifest["version"] = TARGET_VERSION
manifest["created_by"] = "GitHub Actions / v32.64 stronger stale PART replay protection"
manifest["files"] = [
    {"path": "app.py", "sha256": sha256_file(app_path), "size": app_path.stat().st_size},
    {"path": "z2se_updater.pyw", "sha256": sha256_file(updater_path), "size": updater_path.stat().st_size},
]
manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")

print("Prepared Z2SE v32.64 stronger PART replay guard")
print("app.py", app_path.stat().st_size, sha256_file(app_path))
print("z2se_updater.pyw", updater_path.stat().st_size, sha256_file(updater_path))
