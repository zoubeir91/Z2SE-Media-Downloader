from pathlib import Path
import ast
import hashlib
import json
import sys

version = sys.argv[1]
assert version == "33.07"
app_path = Path("payload/app.py")
text = app_path.read_text(encoding="utf-8-sig")

def replace_once(old, new):
    global text
    assert text.count(old) == 1, (old[:180], text.count(old))
    text = text.replace(old, new, 1)

replace_once('APP_VERSION = "33.06"', 'APP_VERSION = "33.07"')

replace_once(
    '''    current_url = str(manifest_url or "").strip()
    last_result = None
    inherited_bandwidth = 0
''',
    '''    current_url = str(manifest_url or "").strip()
    last_result = None
    inherited_bandwidth = 0
    inherited_audio_url = None
''',
)

replace_once(
    '''        if current_bandwidth > 0:
            inherited_bandwidth = current_bandwidth

        # Real media playlist: EXTINF duration is now known.
''',
    '''        if current_bandwidth > 0:
            inherited_bandwidth = current_bandwidth

        current_audio_url = str(
            result.get("audio_url")
            or ""
        ).strip()

        if current_audio_url:
            inherited_audio_url = current_audio_url

        # Real media playlist: EXTINF duration is now known.
''',
)

return_patch = '''            if not result.get("audio_url") and inherited_audio_url:
                result["audio_url"] = inherited_audio_url

'''
needle = '''            if not int(result.get("bandwidth") or 0):
                result["bandwidth"] = inherited_bandwidth

'''
assert text.count(needle) == 2, text.count(needle)
text = text.replace(needle, needle + return_patch, 2)

replace_once(
    '''    if not int(last_result.get("bandwidth") or 0):
        last_result["bandwidth"] = inherited_bandwidth

    last_result["resolved_manifest_url"] = current_url
''',
    '''    if not int(last_result.get("bandwidth") or 0):
        last_result["bandwidth"] = inherited_bandwidth

    if not last_result.get("audio_url") and inherited_audio_url:
        last_result["audio_url"] = inherited_audio_url

    last_result["resolved_manifest_url"] = current_url
''',
)

ast.parse(text)
app_path.write_text(text, encoding="utf-8")
app_hash = hashlib.sha256(app_path.read_bytes()).hexdigest()
manifest_path = Path("payload/update_manifest.json")
manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
manifest["version"] = version
manifest["created_by"] = (
    "v33.07 preserves external HLS audio tracks while resolving nested "
    "Forja video playlists, restoring sound in downloaded episodes"
)
manifest["files"][0]["sha256"] = app_hash
manifest["files"][0]["size"] = app_path.stat().st_size
manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
print("VERIFIED v33.07 app.py sha256", app_hash)
