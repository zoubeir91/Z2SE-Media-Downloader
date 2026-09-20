from pathlib import Path
import ast
import hashlib
import json
import sys


version = sys.argv[1]
assert version == "32.94"

app_path = Path("payload/app.py")
text = app_path.read_text(encoding="utf-8-sig")


def replace_once(old, new):
    global text
    assert text.count(old) == 1, (old[:120], text.count(old))
    text = text.replace(old, new, 1)


replace_once('APP_VERSION = "32.93"', 'APP_VERSION = "32.94"')

# A 403 retry re-extracts the page and receives a fresh media URL. Explicit
# continuation preserves a matching .part file across that new invocation;
# bounded exponential delay avoids hammering YouTube during transient denial.
download_retry_block = '''        "--retries", "10",
        "--fragment-retries", "10",
        "--ffmpeg-location", FFMPEG_DIR,'''
resumable_retry_block = '''        "--retries", "10",
        "--fragment-retries", "10",
        "--retry-sleep", "http:exp=1:20",
        "--retry-sleep", "fragment:exp=1:20",
        "--continue",
        "--part",
        "--ffmpeg-location", FFMPEG_DIR,'''
replace_once(download_retry_block, resumable_retry_block)

cache_retry_block = '''        "--retries", "10",
        "--fragment-retries", "10",
        "--socket-timeout", "20",
        "--ffmpeg-location", FFMPEG_DIR,'''
cache_resumable_retry_block = '''        "--retries", "10",
        "--fragment-retries", "10",
        "--retry-sleep", "http:exp=1:20",
        "--retry-sleep", "fragment:exp=1:20",
        "--continue",
        "--part",
        "--socket-timeout", "20",
        "--ffmpeg-location", FFMPEG_DIR,'''
replace_once(cache_retry_block, cache_resumable_retry_block)

replace_once(
    'log(prefix + "Smart Recovery: retrying with normal extraction...")',
    'log(prefix + "Smart Recovery: fresh media URL requested; resuming matching .part data...")',
)
replace_once(
    '+ "Smart Recovery: trying YouTube web_safari fallback..."',
    '+ "Smart Recovery: refreshing URL with YouTube web_safari; preserving .part data..."',
)
replace_once(
    '"Smart Recovery clients: mweb+PO -> default -> web_safari",',
    '"Smart Recovery clients: mweb+PO -> default -> web_safari",\n'
    '        "HTTP recovery: fresh media URL + resumable .part + exponential backoff",\n'
    '        "PO provider: native yt-dlp plugin framework (bgutil 2.0.0)",',
)

ast.parse(text)
app_path.write_text(text, encoding="utf-8")

app_hash = hashlib.sha256(app_path.read_bytes()).hexdigest()
manifest_path = Path("payload/update_manifest.json")
manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
manifest["version"] = version
manifest["created_by"] = (
    "v32.94 refreshes expired YouTube media URLs and resumes matching .part "
    "downloads with bounded exponential retry backoff; native bgutil provider preserved"
)
manifest["files"][0]["sha256"] = app_hash
manifest["files"][0]["size"] = app_path.stat().st_size
manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")

print("VERIFIED v32.94 app.py sha256", app_hash)
