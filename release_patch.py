from pathlib import Path
import hashlib
import json
import re
import sys

TARGET_VERSION = "32.57"


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
# V32.57 — EARLY VERIFIED-OUTPUT RESCUE + CLEANER YOUTUBE RESOLVER
# ----------------------------------------------------------------------
text, count = re.subn(
    r'APP_VERSION\s*=\s*"32\.56"',
    'APP_VERSION = "32.57"',
    text,
    count=1,
)
if count != 1:
    raise RuntimeError("Could not update APP_VERSION 32.56 -> 32.57")

# In v32.56 the late snapshot verifier could prove that yt-dlp had already
# created the correct playable file, but Browser Bridge only ran that proof
# AFTER Universal Resolver had already wasted time on captured googlevideo and
# telemetry URLs. Move the same proof directly in front of Resolver. If the
# fresh file is real/playable, register it and finish the job immediately.
old_block = '''        if (\n            result == "done"\n            and not _browser_validate_and_normalize_output(\n                index=index,\n                page_url=page_url,\n                preferred_title=(friendly_title or page_title),\n                media_format=media_format,\n                expected_duration=0.0,\n                stats_callback=stats_callback,\n                job_label=label,\n            )\n        ):\n            log(\n                f"[{label}] Page extractor produced no verified media "\n                "-> activating Universal Resolver..."\n            )\n            result = "error"\n            code = 997\n'''
new_block = '''        if result == "done":\n            browser_primary_verified = _browser_validate_and_normalize_output(\n                index=index,\n                page_url=page_url,\n                preferred_title=(friendly_title or page_title),\n                media_format=media_format,\n                expected_duration=0.0,\n                stats_callback=stats_callback,\n                job_label=label,\n            )\n\n            if not browser_primary_verified:\n                early_verified_output = _verify_new_finished_output(\n                    before_snapshot=output_snapshot_before,\n                    expected_title=(friendly_title or page_title),\n                    media_format=media_format,\n                    expected_duration=0.0,\n                )\n\n                if early_verified_output:\n                    register_job_output_path(index, early_verified_output)\n                    browser_primary_verified = _browser_validate_and_normalize_output(\n                        index=index,\n                        page_url=page_url,\n                        preferred_title=(friendly_title or page_title),\n                        media_format=media_format,\n                        expected_duration=0.0,\n                        stats_callback=stats_callback,\n                        job_label=label,\n                    )\n\n                    if browser_primary_verified:\n                        log(\n                            f"[{label}] ✅ Fresh playable output verified before Resolver; "\n                            "recovery skipped."\n                        )\n\n            if not browser_primary_verified:\n                log(\n                    f"[{label}] Page extractor produced no verified media "\n                    "-> activating Universal Resolver..."\n                )\n                result = "error"\n                code = 997\n'''
if old_block not in text:
    raise RuntimeError("Primary Browser validation block anchor missing")
text = text.replace(old_block, new_block, 1)

# Never feed YouTube analytics/telemetry endpoints into FFmpeg/yt-dlp as if
# they were media. They repeatedly produced 31-byte false-success files and
# youtube:tab retries in the supplied log, adding several seconds per job.
media_add_anchor = '''    def add(value):\n        value = normalize_sniffed_media_url(str(value or "").strip())\n        if not value or not value.startswith(("http://", "https://")):\n            return\n        key = value.strip()\n'''
media_add_replacement = '''    def add(value):\n        value = normalize_sniffed_media_url(str(value or "").strip())\n        if not value or not value.startswith(("http://", "https://")):\n            return\n\n        try:\n            parsed = urlparse(value)\n            host = (parsed.hostname or "").lower()\n            path = (parsed.path or "").lower()\n            if (\n                (host == "youtube.com" or host.endswith(".youtube.com"))\n                and (\n                    path.startswith("/api/stats/")\n                    or path.startswith("/youtubei/")\n                    or path.startswith("/ptracking")\n                    or path.startswith("/qoe")\n                )\n            ):\n                return\n        except Exception:\n            pass\n\n        key = value.strip()\n'''
if media_add_anchor not in text:
    raise RuntimeError("Browser media-candidate add() anchor missing")
text = text.replace(media_add_anchor, media_add_replacement, 1)

# Make the startup timing diagnostic actionable: split time waiting for a free
# Parallel slot from active resolver/extractor startup. Total click-to-transfer
# stays available, while the new lines show whether slowness is queueing or
# extraction/provider work.
slot_anchor = '''    with browser_queue_condition:\n        browser_active_jobs += 1\n\n    update_browser_batch_status()\n'''
slot_replacement = '''    browser_active_started_at = time.perf_counter()\n    try:\n        browser_queue_wait = browser_active_started_at - browser_worker_started_at\n        if browser_queue_wait >= 0.25:\n            log(f"[B{index:03d}] ⏱ Queue/slot wait: {browser_queue_wait:.2f}s")\n    except Exception:\n        pass\n\n    with browser_queue_condition:\n        browser_active_jobs += 1\n\n    update_browser_batch_status()\n'''
if slot_anchor not in text:
    raise RuntimeError("Browser live-slot timing anchor missing")
text = text.replace(slot_anchor, slot_replacement, 1)

old_timing_log = '''                    log(\n                        f"[B{index:03d}] ⏱ Browser total startup -> first transfer: "\n                        f"{elapsed:.2f}s"\n                    )\n'''
new_timing_log = '''                    active_elapsed = time.perf_counter() - browser_active_started_at\n                    log(\n                        f"[B{index:03d}] ⏱ Browser total startup -> first transfer: "\n                        f"{elapsed:.2f}s | active: {active_elapsed:.2f}s"\n                    )\n'''
if old_timing_log not in text:
    raise RuntimeError("Browser total timing log anchor missing")
text = text.replace(old_timing_log, new_timing_log, 1)

# v32.56's exact-string BOM fix did not match this build's updater config
# reader. Patch the read call more broadly but only in the function that emits
# the known updater-config warning.
warning_pos = text.find('App updater config read warning:')
if warning_pos >= 0:
    block_start = text.rfind('def ', 0, warning_pos)
    block_end = text.find('\ndef ', warning_pos)
    if block_start >= 0:
        if block_end < 0:
            block_end = len(text)
        block = text[block_start:block_end]
        block2 = block.replace('encoding="utf-8"', 'encoding="utf-8-sig"', 1)
        if block2 != block:
            text = text[:block_start] + block2 + text[block_end:]

app_path.write_text(text, encoding="utf-8")

manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
manifest["product"] = "Z2SE Media Downloader"
manifest["version"] = TARGET_VERSION
manifest["created_by"] = "GitHub Actions / v32.57 early browser output verification + resolver filtering"
manifest["files"] = [
    {"path": "app.py", "sha256": sha256_file(app_path), "size": app_path.stat().st_size},
    {"path": "z2se_updater.pyw", "sha256": sha256_file(updater_path), "size": updater_path.stat().st_size},
]
manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")

print("Prepared Z2SE v32.57 Browser verified-output/resolver fixes")
print("app.py", app_path.stat().st_size, sha256_file(app_path))
print("z2se_updater.pyw", updater_path.stat().st_size, sha256_file(updater_path))
