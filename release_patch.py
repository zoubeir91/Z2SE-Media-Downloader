from pathlib import Path
import hashlib
import json
import re
import sys

TARGET_VERSION = "32.53"


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

text, count = re.subn(
    r'APP_VERSION\s*=\s*"32\.52"',
    'APP_VERSION = "32.53"',
    text,
    count=1,
)
if count != 1:
    raise RuntimeError("Could not update APP_VERSION 32.52 -> 32.53")

# Needed to decode Facebook's captured efg metadata and recover video_id.
if "import base64\n" not in text:
    anchor = "import hashlib\n"
    if anchor not in text:
        raise RuntimeError("import anchor missing")
    text = text.replace(anchor, anchor + "import base64\n", 1)

# Let the existing completion dialog be reused by Browser Bridge without
# touching the unrelated Single Download mini panel.
old_dialog_head = '''def _show_single_download_complete(path):\n    """Centered IDM-style completion dialog with immediate file actions."""\n    try:\n        _cleanup_mini_progress_ui()\n    except Exception:\n        pass\n\n    path = _normalize_output_path(path)\n'''
new_dialog_head = '''def _show_single_download_complete(path, cleanup_mini=True):\n    """Centered IDM-style completion dialog with immediate file actions."""\n    if cleanup_mini:\n        try:\n            _cleanup_mini_progress_ui()\n        except Exception:\n            pass\n\n    path = _normalize_output_path(path)\n'''
if old_dialog_head not in text:
    raise RuntimeError("Completion dialog anchor missing")
text = text.replace(old_dialog_head, new_dialog_head, 1)

# Browser completion: close that job's compact window and show the same
# Open file / Open folder / Cancel dialog using the exact registered path.
browser_finished_anchor = '''def browser_job_finished(index, result, code):\n'''
browser_helper = '''def _show_browser_download_complete(index, path):\n    try:\n        _destroy_job_progress_window(index)\n    except Exception:\n        pass\n\n    _show_single_download_complete(path, cleanup_mini=False)\n\n\ndef browser_job_finished(index, result, code):\n'''
if browser_finished_anchor not in text:
    raise RuntimeError("browser_job_finished anchor missing")
text = text.replace(browser_finished_anchor, browser_helper, 1)

old_done = '''    if result == "done":\n        bulk_job_progress[index] = 100.0\n        update_tree_field(index, "progress", "100.0%")\n        update_tree_field(index, "eta", "")\n        update_tree_status(index, "Done ✅")\n\n    elif result == "stopped":\n'''
new_done = '''    completion_path = ""\n\n    if result == "done":\n        completion_path = _normalize_output_path(_browser_registered_output(index))\n        bulk_job_progress[index] = 100.0\n        update_tree_field(index, "progress", "100.0%")\n        update_tree_field(index, "eta", "")\n        update_tree_status(index, "Done ✅")\n\n    elif result == "stopped":\n'''
if old_done not in text:
    raise RuntimeError("Browser done-status anchor missing")
text = text.replace(old_done, new_done, 1)

# Show completion actions immediately for a successful browser job.
old_batch_tail = '''    else:\n        set_status(\n            f"تحميلات المتصفح: {done} / {total} — {active} خدامين"\n        )\n\n\n\n# ============================================================\n# V28 — REAL HLS ENGINE\n'''
new_batch_tail = '''    else:\n        set_status(\n            f"تحميلات المتصفح: {done} / {total} — {active} خدامين"\n        )\n\n    if result == "done" and completion_path and os.path.isfile(completion_path):\n        gui_call(\n            _show_browser_download_complete,\n            index,\n            completion_path,\n        )\n\n\n\n# ============================================================\n# V28 — REAL HLS ENGINE\n'''
if old_batch_tail not in text:
    raise RuntimeError("Browser completion insertion anchor missing")
text = text.replace(old_batch_tail, new_batch_tail, 1)

# Facebook Browser Bridge optimization. The extension often sends the page as
# facebook.com/ while the captured CDN request carries the real video_id in
# base64url-encoded efg metadata. Recover it and go straight to one canonical
# broad-format extraction instead of generic page -> canonical -> format retry.
worker_anchor = '''def browser_download_job_worker(job):\n'''
worker_helpers = r'''def _facebook_video_id_from_captured_media(primary_url, media_candidates=None):
    urls = _browser_media_candidate_urls(primary_url, media_candidates or [])

    for value in urls:
        try:
            parsed = urlparse(value)
            params = parse_qs(parsed.query)
            for raw in params.get("efg", []):
                token = str(raw or "").strip()
                if not token:
                    continue
                token += "=" * ((4 - len(token) % 4) % 4)
                decoded = base64.urlsafe_b64decode(token.encode("ascii")).decode("utf-8", "replace")
                data = json.loads(decoded)
                video_id = str(data.get("video_id") or "").strip()
                if video_id.isdigit():
                    return video_id
        except Exception:
            pass

    return ""


def browser_download_job_worker(job):
'''
if worker_anchor not in text:
    raise RuntimeError("Browser worker anchor missing")
text = text.replace(worker_anchor, worker_helpers, 1)

# PO Token is YouTube-specific; Browser Bridge Facebook/etc should never wait
# for it before starting extraction.
old_browser_pot = '''    try:\n        ensure_pot_fast()\n\n        parsed = urlparse(page_url)\n        host = parsed.hostname or "site"\n'''
new_browser_pot = '''    try:\n        if _single_url_needs_pot_provider(page_url):\n            ensure_pot_fast()\n        else:\n            log("Browser download: skipping YouTube PO Token startup for non-YouTube URL ⚡")\n\n        parsed = urlparse(page_url)\n        host = parsed.hostname or "site"\n'''
if old_browser_pot not in text:
    raise RuntimeError("Browser PO Token anchor missing")
text = text.replace(old_browser_pot, new_browser_pot, 1)

old_initial_download = '''        code, result = download_with_repair(\n            url=page_url,\n            quality=quality,\n            mode="full",\n            start="",\n            end="",\n            progress_callback=None,\n            stats_callback=stats_callback,\n            job_label=label,\n            media_format=media_format,\n        )\n'''
new_initial_download = '''        facebook_video_id = ""\n        if "facebook." in str(host).lower() or str(host).lower() in {"fb.com", "fb.watch"}:\n            facebook_video_id = _facebook_video_id_from_captured_media(\n                normalized_media_url,\n                media_candidates,\n            )\n\n        if facebook_video_id:\n            canonical_fb_url = f"https://www.facebook.com/watch/?v={facebook_video_id}"\n            log(\n                f"[{label}] ⚡ Facebook Fast Resolver: video id {facebook_video_id} "\n                "-> direct canonical broad-format extraction"\n            )\n            update_tree_status(index, "Downloading")\n            code, _saw_403, stopped, _saw_format_problem = run_download_once(\n                url=canonical_fb_url,\n                quality=quality,\n                mode="full",\n                start="",\n                end="",\n                output_prefix="",\n                progress_callback=None,\n                stats_callback=stats_callback,\n                job_label=label,\n                fast_extract=False,\n                media_format=media_format,\n                output_name=None,\n                referer=page_url,\n                broad_format=True,\n            )\n            result = "stopped" if stopped else ("done" if code == 0 else "error")\n        else:\n            code, result = download_with_repair(\n                url=page_url,\n                quality=quality,\n                mode="full",\n                start="",\n                end="",\n                progress_callback=None,\n                stats_callback=stats_callback,\n                job_label=label,\n                media_format=media_format,\n            )\n'''
if old_initial_download not in text:
    raise RuntimeError("Initial browser download anchor missing")
text = text.replace(old_initial_download, new_initial_download, 1)

app_path.write_text(text, encoding="utf-8")

manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
manifest["product"] = "Z2SE Media Downloader"
manifest["version"] = TARGET_VERSION
manifest["created_by"] = "GitHub Actions / v32.53 Facebook Browser fast path + browser completion dialog"
manifest["files"] = [
    {"path": "app.py", "sha256": sha256_file(app_path), "size": app_path.stat().st_size},
    {"path": "z2se_updater.pyw", "sha256": sha256_file(updater_path), "size": updater_path.stat().st_size},
]
manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")

print("Prepared Z2SE v32.53 Facebook Browser fast path + completion UX")
print("app.py", app_path.stat().st_size, sha256_file(app_path))
print("z2se_updater.pyw", updater_path.stat().st_size, sha256_file(updater_path))
