from pathlib import Path
import ast, hashlib, json, sys

version = sys.argv[1]
assert version == "33.08"
app_path = Path("payload/app.py")
text = app_path.read_text(encoding="utf-8-sig")

def replace_once(old, new):
    global text
    assert text.count(old) == 1, (old[:180], text.count(old))
    text = text.replace(old, new, 1)

replace_once('APP_VERSION = "33.07"', 'APP_VERSION = "33.08"')

helper = r'''

def attach_forja_audio_track(resolved, selected_url, media_candidates, job_label=""):
    """Pair a captured Forja audio rendition with its video-only playlist."""
    if not isinstance(resolved, dict) or resolved.get("audio_url"):
        return resolved
    selected_text = str(resolved.get("video_url") or selected_url or "")
    episode_match = re.search(r"/SNRT/(\d+)/", selected_text, flags=re.IGNORECASE)
    if not episode_match:
        return resolved
    episode_id = episode_match.group(1)
    values = []
    for item in media_candidates or []:
        if isinstance(item, dict):
            values.extend((item.get("url"), item.get("originalUrl")))
        else:
            values.append(item)
    for value in values:
        candidate = normalize_sniffed_media_url(value)
        if not candidate or not is_hls_manifest_url(candidate):
            continue
        if "/audio_tracks/" not in candidate.lower():
            continue
        if not re.search(rf"/SNRT/{re.escape(episode_id)}/", candidate, flags=re.IGNORECASE):
            continue
        resolved["audio_url"] = candidate
        prefix = f"[{job_label}] " if job_label else ""
        log(prefix + "🔊 Forja external audio track paired with video.")
        return resolved
    return resolved
'''

replace_once("\n\ndef is_direct_media_url(url):", helper + "\n\ndef is_direct_media_url(url):")

replace_once(
    '''                    except Exception as exc:
                        log(f"[{label}] HLS candidate selection warning: {exc}")

                    code, result = download_hls_with_ffmpeg(
''',
    '''                    except Exception as exc:
                        log(f"[{label}] HLS candidate selection warning: {exc}")

                    if str(host).lower().endswith("forja.ma"):
                        resolved = attach_forja_audio_track(
                            resolved,
                            selected_url,
                            resolver_media_candidates,
                            job_label=label,
                        )

                    code, result = download_hls_with_ffmpeg(
''',
)

ast.parse(text)
app_path.write_text(text, encoding="utf-8")
app_hash = hashlib.sha256(app_path.read_bytes()).hexdigest()
manifest_path = Path("payload/update_manifest.json")
manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
manifest["version"] = version
manifest["created_by"] = "v33.08 pairs Forja video-only playlists with the captured audio rendition"
manifest["files"][0]["sha256"] = app_hash
manifest["files"][0]["size"] = app_path.stat().st_size
manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
print("VERIFIED v33.08 app.py sha256", app_hash)
