from pathlib import Path
import ast
import hashlib
import json
import sys

version = sys.argv[1]
assert version == "33.14"
app_path = Path("payload/app.py")
text = app_path.read_text(encoding="utf-8-sig")


def replace_once(old, new):
    global text
    assert text.count(old) == 1, (old[:240], text.count(old))
    text = text.replace(old, new, 1)


replace_once('APP_VERSION = "33.13"', 'APP_VERSION = "33.14"')
replace_once('import hashlib\nimport shutil\n', 'import hashlib\nimport shutil\nimport glob\n')

old_resolver = '''def resolve_working_tool(command_name, local_candidate):
    """
    Prefer the Windows-installed FFmpeg/FFprobe (winget PATH entry).
    Fall back to the old local exe only if it is actually executable.

    This specifically avoids WinError 4551 when Windows Application
    Control blocks the old downloaded ffmpeg.exe beside the project.
    """
    candidates = []

    # 1) System / winget installation from PATH
    system_path = shutil.which(command_name)
    if system_path:
        candidates.append(system_path)

    # 2) Old project-local binary as fallback only
    if local_candidate:
        candidates.append(local_candidate)

    seen = set()

    for candidate in candidates:
        try:
            candidate = os.path.abspath(candidate)
        except Exception:
            pass

        key = os.path.normcase(str(candidate))

        if key in seen:
            continue

        seen.add(key)

        if _tool_runs(candidate):
            return candidate

    return None
'''

new_resolver = '''def _winget_media_tool_candidates(command_name):
    """Find current Gyan FFmpeg tools even when Winget left a stale PATH."""
    if os.name != "nt":
        return []

    local_appdata = os.environ.get("LOCALAPPDATA", "")
    if not local_appdata:
        return []

    packages_root = os.path.join(
        local_appdata,
        "Microsoft",
        "WinGet",
        "Packages",
    )
    patterns = [
        os.path.join(
            packages_root,
            "Gyan.FFmpeg*",
            "**",
            command_name + ".exe",
        ),
        os.path.join(
            packages_root,
            "*FFmpeg*",
            "**",
            command_name + ".exe",
        ),
    ]
    found = []
    seen = set()

    for pattern in patterns:
        try:
            matches = glob.glob(pattern, recursive=True)
        except Exception:
            matches = []

        for path in matches:
            key = os.path.normcase(os.path.abspath(path))
            if key in seen or not os.path.isfile(path):
                continue
            seen.add(key)
            found.append(path)

    # Prefer the newest installed package/version.
    found.sort(
        key=lambda path: os.path.getmtime(path) if os.path.exists(path) else 0,
        reverse=True,
    )
    return found


def resolve_working_tool(command_name, local_candidate):
    """
    Resolve an executable tool, tolerating stale Winget PATH entries and
    versioned package directories that change after an update.
    """
    candidates = []

    system_path = shutil.which(command_name)
    if system_path:
        candidates.append(system_path)

    candidates.extend(_winget_media_tool_candidates(command_name))

    if local_candidate:
        candidates.append(local_candidate)

    seen = set()

    for candidate in candidates:
        try:
            candidate = os.path.abspath(candidate)
        except Exception:
            pass

        key = os.path.normcase(str(candidate))
        if key in seen:
            continue
        seen.add(key)

        if _tool_runs(candidate):
            return candidate

    return None
'''

replace_once(old_resolver, new_resolver)

old_media_globals = '''FFMPEG_DIR = (
    os.path.dirname(FFMPEG)
    if FFMPEG
    else BASE_DIR
)
'''

new_media_globals = '''FFMPEG_DIR = (
    os.path.dirname(FFMPEG)
    if FFMPEG
    else BASE_DIR
)

_media_tool_refresh_lock = threading.Lock()


def refresh_media_tools_if_needed(force=False):
    """Repair FFmpeg/FFprobe paths if Winget changed them while Z²SE ran."""
    global FFMPEG, FFPROBE, FFMPEG_DIR

    ffmpeg_ok = bool(FFMPEG and _tool_runs(FFMPEG))
    ffprobe_ok = bool(FFPROBE and _tool_runs(FFPROBE))
    if not force and ffmpeg_ok and ffprobe_ok:
        return True

    with _media_tool_refresh_lock:
        ffmpeg = resolve_working_tool("ffmpeg", LOCAL_FFMPEG)
        ffprobe = resolve_working_tool("ffprobe", LOCAL_FFPROBE)

        # A valid sibling from the same package is preferable and avoids
        # accidentally mixing versions.
        if ffmpeg:
            sibling_probe = os.path.join(os.path.dirname(ffmpeg), "ffprobe.exe")
            if _tool_runs(sibling_probe):
                ffprobe = sibling_probe
        elif ffprobe:
            sibling_ffmpeg = os.path.join(os.path.dirname(ffprobe), "ffmpeg.exe")
            if _tool_runs(sibling_ffmpeg):
                ffmpeg = sibling_ffmpeg

        FFMPEG = ffmpeg
        FFPROBE = ffprobe
        FFMPEG_DIR = os.path.dirname(ffmpeg) if ffmpeg else BASE_DIR

    return bool(FFMPEG and FFPROBE)
'''

replace_once(old_media_globals, new_media_globals)

# Revalidate immediately before every native yt-dlp command. This also repairs
# an installation that Winget upgraded while the app remained open.
replace_once(
    '''def build_command(
    url,
    quality,
    mode="full",
    start="",
    end="",
    output_prefix="",
    fast_extract=True,
    media_format="MP4",
    output_name=None,
    referer=None,
    broad_format=False,
    youtube_client=None,
):
    command = [''',
    '''def build_command(
    url,
    quality,
    mode="full",
    start="",
    end="",
    output_prefix="",
    fast_extract=True,
    media_format="MP4",
    output_name=None,
    referer=None,
    broad_format=False,
    youtube_client=None,
):
    refresh_media_tools_if_needed()
    command = [''',
)

replace_once(
    '''def build_cache_download_command(
    url,
    quality,
    cache_key,
    fast_extract=True,
    media_format="MP4",
    youtube_client=None,
):
    media_format = str(media_format or "MP4").upper()

    command = [''',
    '''def build_cache_download_command(
    url,
    quality,
    cache_key,
    fast_extract=True,
    media_format="MP4",
    youtube_client=None,
):
    refresh_media_tools_if_needed()
    media_format = str(media_format or "MP4").upper()

    command = [''',
)

# Browser/Resolver paths call FFmpeg directly, so repair before any candidate
# probing or download begins.
replace_once(
    '''def browser_download_job_worker(job):
    global browser_active_jobs

    browser_worker_started_at = time.perf_counter()''',
    '''def browser_download_job_worker(job):
    global browser_active_jobs

    refresh_media_tools_if_needed()
    browser_worker_started_at = time.perf_counter()''',
)

ast.parse(text)
app_path.write_text(text, encoding="utf-8")
app_hash = hashlib.sha256(app_path.read_bytes()).hexdigest()
manifest_path = Path("payload/update_manifest.json")
manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
manifest["version"] = version
manifest["created_by"] = (
    "v33.14 repairs stale Winget FFmpeg paths by discovering the current "
    "versioned package and revalidating both FFmpeg and FFprobe at runtime"
)
manifest["files"][0]["sha256"] = app_hash
manifest["files"][0]["size"] = app_path.stat().st_size
manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
print("VERIFIED v33.14 app.py sha256", app_hash)
