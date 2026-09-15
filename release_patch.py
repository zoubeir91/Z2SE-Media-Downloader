from pathlib import Path
import ast
import hashlib
import json
import re
import sys

TARGET_VERSION = "32.77"


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
text, count = re.subn(r'APP_VERSION\s*=\s*"32\.76"', 'APP_VERSION = "32.77"', text, count=1)
if count != 1:
    raise RuntimeError("Could not update APP_VERSION 32.76 -> 32.77")

# v32.77 keeps the v32.76 premium navigation unchanged and focuses on
# YouTube resilience. Recent YouTube changes can expose SABR-only behavior
# for some clients/cookie contexts. Classify those messages as a recovery
# signal so Z2SE does not waste retries on the same failing route.
sabr_anchor = '''            low = line.lower()\n            if "403" in low and (\n'''
sabr_insert = '''            low = line.lower()\n\n            if (\n                "sabr" in low\n                and (\n                    "only" in low\n                    or "streaming" in low\n                    or "format" in low\n                    or "missing" in low\n                    or "not available" in low\n                )\n            ):\n                if not saw_pot_problem:\n                    prefix = f"[{job_label}] " if job_label else ""\n                    log(prefix + "🧠 YouTube SABR/client restriction detected -> Smart Recovery")\n                saw_pot_problem = True\n                saw_format_problem = True\n\n            if "403" in low and (\n'''
if sabr_anchor not in text:
    raise RuntimeError("Could not locate yt-dlp output classifier for SABR recovery")
text = text.replace(sabr_anchor, sabr_insert, 1)

# Add a targeted web_embedded + Safari UA route. This is deliberately a LAST
# fallback after Z2SE's normal/PO-token/web_safari paths, so it cannot disturb
# successful downloads. It addresses the current YouTube behavior where the
# embedded web client may expose HLS only when presented with Safari identity.
client_anchor = '''    if forced_youtube_client == "web_safari":\n        command += [\n            "--extractor-args",\n            "youtube:player_client=web_safari",\n        ]\n\n    elif forced_youtube_client == "default":\n'''
client_replace = '''    if forced_youtube_client == "web_safari":\n        command += [\n            "--extractor-args",\n            "youtube:player_client=web_safari",\n        ]\n\n    elif forced_youtube_client == "web_embedded_safari":\n        command += [\n            "--user-agent",\n            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.6 Safari/605.1.15",\n            "--extractor-args",\n            "youtube:player_client=web_embedded",\n        ]\n\n    elif forced_youtube_client == "default":\n'''
if client_anchor not in text:
    raise RuntimeError("Could not locate YouTube client command builder")
text = text.replace(client_anchor, client_replace, 1)

fallback_anchor = '''        if stopped:\n            return code, "stopped", None, title\n\n    if code != 0:\n        return code, "error", None, title\n'''
fallback_replace = '''        if stopped:\n            return code, "stopped", None, title\n\n    if (\n        code != 0\n        and is_youtube_page_url(url)\n        and not stop_all_event.is_set()\n    ):\n        log(prefix + "Smart Recovery: TURBO trying web_embedded + Safari fallback...")\n        result = cache_download_once(\n            url=url,\n            quality=quality,\n            cache_key=cache_key,\n            progress_callback=progress_callback,\n            stats_callback=stats_callback,\n            job_label=job_label,\n            fast_extract=False,\n            media_format=media_format,\n            youtube_client="web_embedded_safari",\n        )\n        (code, _, stopped, _, title2, final_file2) = result\n        title = title2 or title\n        final_file = final_file2 or final_file\n        if stopped:\n            return code, "stopped", None, title\n\n    if code != 0:\n        return code, "error", None, title\n'''
if fallback_anchor not in text:
    raise RuntimeError("Could not locate final TURBO Smart Recovery exit")
text = text.replace(fallback_anchor, fallback_replace, 1)

# Also recognize the same SABR condition in the normal downloader's output
# classifier when that classifier uses the same low=line.lower() pattern.
# One targeted replacement above is guaranteed; the normal path retains its
# existing 403/PO-token recovery and is left otherwise untouched.

text = text.replace('Clean Editor v32.76: startup draft/PART rows cleared.', 'Clean Editor v32.77: startup draft/PART rows cleared.', 1)
text = text.replace('Clean Editor v32.76 warning:', 'Clean Editor v32.77 warning:', 1)
text = text.replace('Download details v32.76 warning:', 'Download details v32.77 warning:', 1)

ast.parse(text)
app_path.write_text(text, encoding="utf-8")
manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
manifest["product"] = "Z2SE Media Downloader"
manifest["version"] = TARGET_VERSION
manifest["created_by"] = "GitHub Actions / v32.77 SABR-aware Smart Recovery + embedded Safari last fallback"
manifest["files"] = [
    {"path":"app.py","sha256":sha256_file(app_path),"size":app_path.stat().st_size},
    {"path":"z2se_updater.pyw","sha256":sha256_file(updater_path),"size":updater_path.stat().st_size},
]
manifest_path.write_text(json.dumps(manifest, indent=2)+"\n", encoding="utf-8")
print("Prepared Z2SE v32.77 SABR-aware YouTube Smart Recovery")
