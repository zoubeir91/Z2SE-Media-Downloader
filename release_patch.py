from pathlib import Path
import hashlib
import json
import re
import sys

TARGET_VERSION = "32.56"


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
# V32.56 — PART RELIABILITY + NO MORE 100% -> 0% UI RESETS
# ----------------------------------------------------------------------
text, count = re.subn(
    r'APP_VERSION\s*=\s*"32\.55"',
    'APP_VERSION = "32.56"',
    text,
    count=1,
)
if count != 1:
    raise RuntimeError("Could not update APP_VERSION 32.55 -> 32.56")

# Browser Bridge page-duration metadata is not trustworthy enough to reject a
# file that yt-dlp has already completed and that ffprobe proves is real media.
# The old duration-ratio rejection was the reason normal YouTube jobs could
# finish video+audio, reach 100%, then unnecessarily enter Universal Resolver
# and do another recovery pass. Keep actual file/media validation, but stop
# using captured page duration as a hard gate.
old_duration_gate = "expected_duration=(0.0 if facebook_video_id else page_duration)"
duration_count = text.count(old_duration_gate)
if duration_count < 1:
    raise RuntimeError("Browser duration validation anchor missing")
text = text.replace(old_duration_gate, "expected_duration=0.0")

# yt-dlp often downloads separate VIDEO then AUDIO streams for an MP4. Raw
# progress naturally goes 0->100 for video and then 0->100 for audio. That is
# not a duplicate download, but showing those raw percentages makes Z2SE look
# like it restarted. Map the two phases onto one monotonic 0->100 timeline.
run_vars_old = '''    launched_at = time.perf_counter()\n    first_output_at = None\n    first_download_at = None\n'''
run_vars_new = '''    launched_at = time.perf_counter()\n    first_output_at = None\n    first_download_at = None\n\n    # V32.56: one visual timeline for yt-dlp's separate video/audio streams.\n    progress_stream_phase = 0\n    progress_last_raw_percent = None\n'''
if run_vars_old not in text:
    raise RuntimeError("run_download_once progress state anchor missing")
text = text.replace(run_vars_old, run_vars_new, 1)

progress_old = '''            percent_value = None\n            if percent_match:\n                try:\n                    percent_value = float(percent_match.group(1))\n                except Exception:\n                    percent_value = None\n\n            if percent_value is not None and progress_callback:\n                try:\n                    progress_callback(percent_value)\n                except Exception:\n                    pass\n'''
progress_new = '''            percent_value = None\n            if percent_match:\n                try:\n                    raw_percent = float(percent_match.group(1))\n                    percent_value = raw_percent\n\n                    if (\n                        mode == "full"\n                        and str(media_format or "MP4").upper() == "MP4"\n                    ):\n                        if (\n                            progress_last_raw_percent is not None\n                            and progress_last_raw_percent >= 95.0\n                            and raw_percent <= 5.0\n                        ):\n                            progress_stream_phase += 1\n\n                        progress_last_raw_percent = raw_percent\n\n                        if progress_stream_phase <= 0:\n                            # Main video stream occupies the first 94%.\n                            percent_value = min(94.0, max(0.0, raw_percent * 0.94))\n                        else:\n                            # Audio/additional stream(s) finish the transfer\n                            # without ever sending the UI backwards.\n                            percent_value = min(99.0, 94.0 + max(0.0, raw_percent) * 0.05)\n                except Exception:\n                    percent_value = None\n\n            if percent_value is not None and progress_callback:\n                try:\n                    progress_callback(percent_value)\n                except Exception:\n                    pass\n'''
if progress_old not in text:
    raise RuntimeError("run_download_once percent parser anchor missing")
text = text.replace(progress_old, progress_new, 1)

# TURBO PART cache used --throttled-rate 500K. On current YouTube this can
# deliberately trigger yt-dlp re-extraction while the temporary .fXXX stream
# is being assembled. The supplied journal shows exactly that sequence right
# before WinError 2 for a missing .f136.mp4. Do not force re-extraction merely
# because a short sample dips below 500K; normal retry/403 recovery remains.
cache_throttle_old = '''        "--http-chunk-size", "8M",\n        "--throttled-rate", "500K",\n\n        # Concurrent DASH/native fragments where available.\n        "-N", "16",\n'''
cache_throttle_new = '''        "--http-chunk-size", "8M",\n\n        # Concurrent DASH/native fragments where available. Eight workers is\n        # fast enough for PART cache acquisition while being less fragile on\n        # Windows/YouTube than the old 16-way + forced throttle re-extract.\n        "-N", "8",\n'''
if cache_throttle_old not in text:
    raise RuntimeError("TURBO cache throttle anchor missing")
text = text.replace(cache_throttle_old, cache_throttle_new, 1)

# The TURBO cache downloader has the same separate-video/audio raw progress
# behavior. Keep its UI monotonic too while reserving the last ~4% for local cut.
cache_vars_old = '''    stopped = False\n    title = ""\n    final_file = ""\n\n    command = build_cache_download_command(\n'''
cache_vars_new = '''    stopped = False\n    title = ""\n    final_file = ""\n    cache_progress_phase = 0\n    cache_last_raw_percent = None\n\n    command = build_cache_download_command(\n'''
if cache_vars_old not in text:
    raise RuntimeError("cache_download_once progress state anchor missing")
text = text.replace(cache_vars_old, cache_vars_new, 1)

cache_progress_old = '''            percent, speed, eta, size = parse_ytdlp_download_stats(line)\n\n            if percent is not None:\n                # Reserve the last 4% for the local cut.\n                overall = min(95.5, max(0.0, percent * 0.955))\n\n                if progress_callback:\n'''
cache_progress_new = '''            percent, speed, eta, size = parse_ytdlp_download_stats(line)\n\n            if percent is not None:\n                raw_percent = float(percent)\n\n                if (\n                    cache_last_raw_percent is not None\n                    and cache_last_raw_percent >= 95.0\n                    and raw_percent <= 5.0\n                ):\n                    cache_progress_phase += 1\n\n                cache_last_raw_percent = raw_percent\n\n                if cache_progress_phase <= 0:\n                    overall = min(90.0, max(0.0, raw_percent * 0.90))\n                else:\n                    overall = min(95.5, 90.0 + max(0.0, raw_percent) * 0.055)\n\n                if progress_callback:\n'''
if cache_progress_old not in text:
    raise RuntimeError("TURBO cache progress parser anchor missing")
text = text.replace(cache_progress_old, cache_progress_new, 1)

# The user's journal also exposed a stale updater JSON with a UTF-8 BOM.
# Reading it with utf-8-sig is backwards compatible and removes the noisy
# startup warning without touching the updater's data or security checks.
text = text.replace(
    'open(APP_UPDATE_CONFIG_FILE, "r", encoding="utf-8")',
    'open(APP_UPDATE_CONFIG_FILE, "r", encoding="utf-8-sig")',
)

app_path.write_text(text, encoding="utf-8")

manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
manifest["product"] = "Z2SE Media Downloader"
manifest["version"] = TARGET_VERSION
manifest["created_by"] = "GitHub Actions / v32.56 PART reliability + monotonic progress + browser verified-output guard"
manifest["files"] = [
    {"path": "app.py", "sha256": sha256_file(app_path), "size": app_path.stat().st_size},
    {"path": "z2se_updater.pyw", "sha256": sha256_file(updater_path), "size": updater_path.stat().st_size},
]
manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")

print("Prepared Z2SE v32.56 PART reliability + monotonic progress fixes")
print("app.py", app_path.stat().st_size, sha256_file(app_path))
print("z2se_updater.pyw", updater_path.stat().st_size, sha256_file(updater_path))
