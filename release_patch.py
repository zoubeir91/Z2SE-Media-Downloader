from pathlib import Path
import hashlib
import json
import re
import sys

TARGET_VERSION = "32.55"


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
# V32.55 — YOUTUBE GVS/PO-TOKEN-AWARE 403 RECOVERY + REAL BROWSER TIMING
# ----------------------------------------------------------------------
text, count = re.subn(
    r'APP_VERSION\s*=\s*"32\.54"',
    'APP_VERSION = "32.55"',
    text,
    count=1,
)
if count != 1:
    raise RuntimeError("Could not update APP_VERSION 32.54 -> 32.55")

# Current yt-dlp guidance notes that YouTube GVS requests can return HTTP 403
# when the client/PO Token combination is no longer valid. Treat a YouTube 403
# as a PO/provider-class failure too, so the existing Smart Recovery path uses
# the provider/client recovery logic instead of seeing it as a generic network
# failure only.
old_403 = '''            low = line.lower()\n            if "403" in low and (\n                "forbidden" in low\n                or "http error 403" in low\n            ):\n                saw_403 = True\n'''
new_403 = '''            low = line.lower()\n            if "403" in low and (\n                "forbidden" in low\n                or "http error 403" in low\n            ):\n                saw_403 = True\n\n                try:\n                    host = (urlparse(str(url or "")).hostname or "").lower()\n                except Exception:\n                    host = ""\n\n                if (\n                    host == "youtu.be"\n                    or host == "youtube.com"\n                    or host.endswith(".youtube.com")\n                    or "googlevideo.com" in host\n                ):\n                    # YouTube now commonly ties GVS access to a video-specific\n                    # PO Token/client context. Classifying this here lets the\n                    # already-existing Smart Recovery choose its PO/client\n                    # fallbacks immediately instead of treating it as a plain\n                    # HTTP failure.\n                    if not saw_pot_problem:\n                        prefix = f"[{job_label}] " if job_label else ""\n                        log(\n                            prefix\n                            + "🧠 YouTube GVS 403 detected -> PO Token/client recovery profile"\n                        )\n                    saw_pot_problem = True\n'''
if old_403 not in text:
    raise RuntimeError("YouTube 403 classification anchor missing")
text = text.replace(old_403, new_403, 1)

# Measure Browser Bridge delay from the beginning of the browser worker, not
# merely from the yt-dlp subprocess launch. This captures provider checks,
# resolver work, queue/slot startup and extraction before the first actual
# transfer, which is the delay users perceive in the progress window.
worker_anchor = '''def browser_download_job_worker(job):\n    global browser_active_jobs\n\n    index = job["index"]\n'''
worker_replacement = '''def browser_download_job_worker(job):\n    global browser_active_jobs\n\n    browser_worker_started_at = time.perf_counter()\n    browser_first_transfer_logged = False\n\n    index = job["index"]\n'''
if worker_anchor not in text:
    raise RuntimeError("Browser worker timing anchor missing")
text = text.replace(worker_anchor, worker_replacement, 1)

stats_head = '''    def stats_callback(\n        percent=None,\n        speed=None,\n        eta=None,\n        size=None,\n        title=None,\n    ):\n        # Direct stream URLs often call themselves "chunks", "manifest",\n'''
stats_replacement = '''    def stats_callback(\n        percent=None,\n        speed=None,\n        eta=None,\n        size=None,\n        title=None,\n    ):\n        nonlocal browser_first_transfer_logged\n\n        if not browser_first_transfer_logged:\n            transfer_started = False\n            try:\n                transfer_started = percent is not None and float(percent) > 0.0\n            except Exception:\n                transfer_started = False\n\n            if not transfer_started:\n                speed_text = str(speed or "").strip().lower()\n                transfer_started = bool(\n                    speed_text\n                    and speed_text not in {"—", "unknown", "stream", "done"}\n                )\n\n            if transfer_started:\n                browser_first_transfer_logged = True\n                try:\n                    elapsed = time.perf_counter() - browser_worker_started_at\n                    log(\n                        f"[B{index:03d}] ⏱ Browser total startup -> first transfer: "\n                        f"{elapsed:.2f}s"\n                    )\n                except Exception:\n                    pass\n\n        # Direct stream URLs often call themselves "chunks", "manifest",\n'''
if stats_head not in text:
    raise RuntimeError("Browser stats timing anchor missing")
text = text.replace(stats_head, stats_replacement, 1)

app_path.write_text(text, encoding="utf-8")

manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
manifest["product"] = "Z2SE Media Downloader"
manifest["version"] = TARGET_VERSION
manifest["created_by"] = "GitHub Actions / v32.55 YouTube GVS-aware recovery + browser startup timing"
manifest["files"] = [
    {"path": "app.py", "sha256": sha256_file(app_path), "size": app_path.stat().st_size},
    {"path": "z2se_updater.pyw", "sha256": sha256_file(updater_path), "size": updater_path.stat().st_size},
]
manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")

print("Prepared Z2SE v32.55 YouTube GVS recovery diagnostics + real browser timing")
print("app.py", app_path.stat().st_size, sha256_file(app_path))
print("z2se_updater.pyw", updater_path.stat().st_size, sha256_file(updater_path))
