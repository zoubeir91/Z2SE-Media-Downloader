from pathlib import Path
import hashlib
import json
import re
import sys

TARGET_VERSION = "32.58"


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
# V32.58 — FACEBOOK VISIBLE-VIDEO BINDING / STALE CDN CAPTURE PROTECTION
# ----------------------------------------------------------------------
text, count = re.subn(
    r'APP_VERSION\s*=\s*"32\.57"',
    'APP_VERSION = "32.58"',
    text,
    count=1,
)
if count != 1:
    raise RuntimeError("Could not update APP_VERSION 32.57 -> 32.58")

# Facebook home/feed pages keep network requests from multiple videos alive.
# Bind captured Facebook efg metadata to the visible player's duration instead
# of blindly trusting the first video_id in the network capture list.
old_helper_pattern = re.compile(
    r'def _facebook_video_id_from_captured_media\(primary_url, media_candidates=None\):\n.*?\n\n\ndef browser_download_job_worker\(job\):',
    re.S,
)
new_helper = r'''def _facebook_capture_metadata(value):
    try:
        parsed = urlparse(str(value or "").strip())
        params = parse_qs(parsed.query)

        for raw in params.get("efg", []):
            token = str(raw or "").strip()
            if not token:
                continue

            token += "=" * ((4 - len(token) % 4) % 4)
            decoded = base64.urlsafe_b64decode(
                token.encode("ascii")
            ).decode("utf-8", "replace")
            data = json.loads(decoded)

            video_id = str(data.get("video_id") or "").strip()
            if not video_id.isdigit():
                continue

            try:
                duration = float(data.get("duration_s") or 0.0)
            except Exception:
                duration = 0.0

            return {
                "video_id": video_id,
                "duration": duration,
                "tag": str(data.get("vencode_tag") or "").lower(),
            }
    except Exception:
        pass

    return None


def _facebook_page_is_generic_feed(page_url):
    try:
        parsed = urlparse(str(page_url or ""))
        host = (parsed.hostname or "").lower()
        path = (parsed.path or "").strip("/").lower()
        query = parse_qs(parsed.query)

        if not ("facebook." in host or host in {"fb.com", "fb.watch"}):
            return False

        if not path:
            return True

        if path == "watch" and not str(query.get("v", [""])[0]).strip():
            return True

        if path in {"reels", "watch", "videos"}:
            return True
    except Exception:
        pass

    return False


def _facebook_video_id_from_captured_media(
    primary_url,
    media_candidates=None,
    expected_duration=0.0,
    page_url="",
    job_label="",
):
    urls = _browser_media_candidate_urls(primary_url, media_candidates or [])
    entries = []

    for order, value in enumerate(urls):
        meta = _facebook_capture_metadata(value)
        if not meta:
            continue
        meta["order"] = order
        entries.append(meta)

    if not entries:
        return ""

    try:
        expected_duration = float(expected_duration or 0.0)
    except Exception:
        expected_duration = 0.0

    generic_feed = _facebook_page_is_generic_feed(page_url)

    if expected_duration >= 2.0:
        tolerance = max(2.5, expected_duration * 0.12)
        matching = [
            item for item in entries
            if item.get("duration", 0.0) > 0.0
            and abs(item["duration"] - expected_duration) <= tolerance
        ]

        if matching:
            matching.sort(
                key=lambda item: (
                    abs(item["duration"] - expected_duration),
                    item["order"],
                )
            )
            chosen = matching[0]

            if job_label:
                log(
                    f"[{job_label}] 🎯 Facebook visible-video match: "
                    f"id={chosen['video_id']} • captured≈{chosen['duration']:.1f}s "
                    f"• player≈{expected_duration:.1f}s"
                )

            return chosen["video_id"]

        if generic_feed:
            if job_label:
                durations = sorted({
                    round(float(item.get("duration", 0.0)), 1)
                    for item in entries
                    if float(item.get("duration", 0.0)) > 0.0
                })
                log(
                    f"[{job_label}] 🛡 Facebook stale-capture guard: "
                    f"player≈{expected_duration:.1f}s but captured durations={durations}; "
                    "refusing wrong video id."
                )
            return ""

    if not generic_feed:
        return entries[0]["video_id"]

    if job_label:
        log(
            f"[{job_label}] 🛡 Facebook feed capture has no reliable player "
            "duration; canonical fast resolver disabled for this click."
        )
    return ""


def browser_download_job_worker(job):'''
text, helper_count = old_helper_pattern.subn(new_helper, text, count=1)
if helper_count != 1:
    raise RuntimeError("Facebook capture helper anchor missing")

old_call = '''            facebook_video_id = _facebook_video_id_from_captured_media(\n                normalized_media_url,\n                media_candidates,\n            )\n'''
new_call = '''            facebook_video_id = _facebook_video_id_from_captured_media(\n                normalized_media_url,\n                media_candidates,\n                expected_duration=page_duration,\n                page_url=page_url,\n                job_label=label,\n            )\n'''
if old_call not in text:
    raise RuntimeError("Facebook fast-resolver call anchor missing")
text = text.replace(old_call, new_call, 1)

# On a generic Facebook feed, if the captures cannot be bound to the clicked
# player, never guess from a stale page-global CDN request.
old_else = '''        else:\n            code, result = download_with_repair(\n                url=page_url,\n                quality=quality,\n                mode="full",\n                start="",\n                end="",\n                progress_callback=None,\n                stats_callback=stats_callback,\n                job_label=label,\n                media_format=media_format,\n            )\n'''
new_else = '''        else:\n            facebook_generic_unbound = (\n                ("facebook." in str(host).lower() or str(host).lower() in {"fb.com", "fb.watch"})\n                and _facebook_page_is_generic_feed(page_url)\n            )\n\n            if facebook_generic_unbound:\n                log(\n                    f"[{label}] 🛡 Facebook visible-video safety stop: "\n                    "no trustworthy capture matched this clicked player; "\n                    "wrong-video fallback blocked."\n                )\n                code, result = 996, "error"\n            else:\n                code, result = download_with_repair(\n                    url=page_url,\n                    quality=quality,\n                    mode="full",\n                    start="",\n                    end="",\n                    progress_callback=None,\n                    stats_callback=stats_callback,\n                    job_label=label,\n                    media_format=media_format,\n                )\n'''
if old_else not in text:
    raise RuntimeError("Facebook initial fallback anchor missing")
text = text.replace(old_else, new_else, 1)

# v32.54 inserts a Facebook guard immediately before the Universal Resolver,
# so patch the resolver URL assignment itself instead of depending on the exact
# surrounding block shape.
resolver_comment_pos = text.find("# V32.45 UNIVERSAL RESOLVER")
if resolver_comment_pos < 0:
    raise RuntimeError("Universal Resolver comment missing")

resolver_assign = '''            resolver_urls = _browser_media_candidate_urls(\n                normalized_media_url,\n                media_candidates,\n            )\n'''
resolver_assign_pos = text.find(resolver_assign, resolver_comment_pos)
if resolver_assign_pos < 0:
    raise RuntimeError("Universal Resolver URL assignment missing")

safe_resolver_assign = '''            facebook_generic_unbound = bool(\n                ("facebook." in str(host).lower() or str(host).lower() in {"fb.com", "fb.watch"})\n                and _facebook_page_is_generic_feed(page_url)\n                and not facebook_video_id\n            )\n\n            resolver_urls = (\n                []\n                if facebook_generic_unbound\n                else _browser_media_candidate_urls(\n                    normalized_media_url,\n                    media_candidates,\n                )\n            )\n\n            if facebook_generic_unbound:\n                log(\n                    f"[{label}] 🛡 Universal Resolver skipped: Facebook "\n                    "feed capture is not bound to the clicked video."\n                )\n'''
text = (
    text[:resolver_assign_pos]
    + safe_resolver_assign
    + text[resolver_assign_pos + len(resolver_assign):]
)

app_path.write_text(text, encoding="utf-8")

manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
manifest["product"] = "Z2SE Media Downloader"
manifest["version"] = TARGET_VERSION
manifest["created_by"] = "GitHub Actions / v32.58 Facebook visible-video binding + stale capture protection"
manifest["files"] = [
    {"path": "app.py", "sha256": sha256_file(app_path), "size": app_path.stat().st_size},
    {"path": "z2se_updater.pyw", "sha256": sha256_file(updater_path), "size": updater_path.stat().st_size},
]
manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")

print("Prepared Z2SE v32.58 Facebook visible-video binding fix")
print("app.py", app_path.stat().st_size, sha256_file(app_path))
print("z2se_updater.pyw", updater_path.stat().st_size, sha256_file(updater_path))
