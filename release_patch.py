from pathlib import Path
import ast
import hashlib
import json
import sys


version = sys.argv[1]
assert version == "32.97"

app_path = Path("payload/app.py")
text = app_path.read_text(encoding="utf-8-sig")


def replace_once(old, new):
    global text
    assert text.count(old) == 1, (old[:140], text.count(old))
    text = text.replace(old, new, 1)


replace_once('APP_VERSION = "32.96"', 'APP_VERSION = "32.97"')

replace_once(
    '''    progress_stream_phase = 0
    progress_last_raw_percent = None
''',
    '''    progress_stream_phase = 0
    progress_last_raw_percent = None
    progress_stream_totals = {}
''',
)

old_size_parse = '''            size_match = re.search(
                r"\\bof\\s+~?\\s*([0-9.]+\\s*[KMGTPE]?i?B)",
                line,
                re.IGNORECASE
            )

            if stats_callback and (
                percent_value is not None
                or speed_match
                or eta_match
                or size_match
            ):
                try:
                    stats_callback(
                        percent=percent_value,
                        speed=speed_match.group(1) if speed_match else None,
                        eta=eta_match.group(1) if eta_match else None,
                        size=size_match.group(1) if size_match else None,
                    )
                except Exception:
                    pass
'''
new_size_parse = '''            size_match = re.search(
                r"\\bof\\s+~?\\s*([0-9.]+\\s*[KMGTPE]?i?B)",
                line,
                re.IGNORECASE
            )

            size_text = size_match.group(1) if size_match else None
            if (
                size_match
                and mode == "full"
                and str(media_format or "MP4").upper() == "MP4"
            ):
                try:
                    phase_total = _parse_human_size(size_match.group(1))
                    if phase_total > 0:
                        progress_stream_totals[progress_stream_phase] = phase_total
                        cumulative_total = sum(progress_stream_totals.values())
                        size_text = _human_file_size(cumulative_total)
                except Exception:
                    size_text = size_match.group(1)

            if stats_callback and (
                percent_value is not None
                or speed_match
                or eta_match
                or size_text
            ):
                try:
                    stats_callback(
                        percent=percent_value,
                        speed=speed_match.group(1) if speed_match else None,
                        eta=eta_match.group(1) if eta_match else None,
                        size=size_text,
                    )
                except Exception:
                    pass
'''
replace_once(old_size_parse, new_size_parse)

old_directory = '''def _v3296_vlc_directory():
    candidates = []
    for env_name in ("ProgramFiles", "ProgramFiles(x86)", "LOCALAPPDATA"):
        base = os.environ.get(env_name, "")
        if base:
            candidates.extend((
                os.path.join(base, "VideoLAN", "VLC"),
                os.path.join(base, "Programs", "VideoLAN", "VLC"),
            ))
    for folder in candidates:
        if os.path.isfile(os.path.join(folder, "libvlc.dll")):
            return folder
    return None
'''
new_directory = '''def _v3296_vlc_directory():
    candidates = []
    for env_name in ("ProgramFiles", "ProgramW6432", "ProgramFiles(x86)", "LOCALAPPDATA"):
        base = os.environ.get(env_name, "")
        if base:
            candidates.extend((
                os.path.join(base, "VideoLAN", "VLC"),
                os.path.join(base, "Programs", "VideoLAN", "VLC"),
            ))

    if os.name == "nt":
        try:
            import winreg
            registry_keys = (
                (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\\VideoLAN\\VLC", "InstallDir"),
                (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\\WOW6432Node\\VideoLAN\\VLC", "InstallDir"),
                (winreg.HKEY_CURRENT_USER, r"SOFTWARE\\VideoLAN\\VLC", "InstallDir"),
                (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\App Paths\\vlc.exe", "Path"),
                (winreg.HKEY_CURRENT_USER, r"SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\App Paths\\vlc.exe", "Path"),
            )
            for hive, key_name, value_name in registry_keys:
                try:
                    with winreg.OpenKey(hive, key_name) as key:
                        value = winreg.QueryValueEx(key, value_name)[0]
                        if value:
                            candidates.append(str(value).strip().strip('"'))
                except OSError:
                    pass
        except Exception:
            pass

        try:
            vlc_exe = shutil.which("vlc.exe") or shutil.which("vlc")
            if vlc_exe:
                candidates.append(os.path.dirname(vlc_exe))
        except Exception:
            pass

    seen = set()
    for folder in candidates:
        folder = os.path.normpath(os.path.expandvars(str(folder or "").strip()))
        key = os.path.normcase(folder)
        if not folder or key in seen:
            continue
        seen.add(key)
        if os.path.isfile(os.path.join(folder, "libvlc.dll")):
            return folder
    return None


v3297_video_host = tk.Frame(v3270_preview, bg="#000000", bd=0, highlightthickness=0)
v3297_video_host.bind("<Button-1>", lambda event: _v3271_open_preview(event), add="+")
'''
replace_once(old_directory, new_directory)

replace_once(
    '''    v3296_vlc["player"] = None
    v3296_vlc["media"] = None
    v3296_vlc["path"] = None
''',
    '''    v3296_vlc["player"] = None
    v3296_vlc["media"] = None
    v3296_vlc["path"] = None
    try:
        v3297_video_host.place_forget()
    except Exception:
        pass
''',
)

replace_once(
    '''        v3270_preview.update_idletasks()
        dll.libvlc_media_player_set_hwnd(
            player,
            ctypes.c_void_p(int(v3270_preview.winfo_id())),
        )
        dll.libvlc_audio_set_volume(player, 80)
''',
    '''        v3297_video_host.place(x=0, y=0, relwidth=1, relheight=1)
        v3297_video_host.lift()
        v3297_video_host.update_idletasks()
        dll.libvlc_media_player_set_hwnd(
            player,
            ctypes.c_void_p(int(v3297_video_host.winfo_id())),
        )
        dll.libvlc_audio_set_volume(player, 80)
''',
)

replace_once(
    '''        _v3295_request_video_preview(media_path)
        color = UI_ACCENT
''',
    '''        active_preview = bool(
            v3296_vlc.get("player")
            and v3296_vlc.get("path")
            and os.path.normcase(os.path.abspath(str(media_path or "")))
                == v3296_vlc.get("path")
        )
        if not active_preview:
            _v3295_request_video_preview(media_path)
        color = UI_ACCENT
''',
)

replace_once(
    '''        pct = max(0.0, min(100.0, pct))
        v3270_detail_percent.set(pct)
''',
    '''        pct = max(0.0, min(100.0, pct))
        if is_done:
            pct = 100.0
        v3270_detail_percent.set(pct)
''',
)

ast.parse(text)
app_path.write_text(text, encoding="utf-8")

app_hash = hashlib.sha256(app_path.read_bytes()).hexdigest()
manifest_path = Path("payload/update_manifest.json")
manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
manifest["version"] = version
manifest["created_by"] = (
    "v32.97 stabilizes embedded VLC playback, broadens VLC discovery, "
    "shows cumulative video+audio transfer size, and synchronizes completed details"
)
manifest["files"][0]["sha256"] = app_hash
manifest["files"][0]["size"] = app_path.stat().st_size
manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")

print("VERIFIED v32.97 app.py sha256", app_hash)
