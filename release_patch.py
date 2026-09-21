from pathlib import Path
import ast
import hashlib
import json
import sys


version = sys.argv[1]
assert version == "32.98"

app_path = Path("payload/app.py")
text = app_path.read_text(encoding="utf-8-sig")


def replace_once(old, new):
    global text
    assert text.count(old) == 1, (old[:160], text.count(old))
    text = text.replace(old, new, 1)


replace_once('APP_VERSION = "32.97"', 'APP_VERSION = "32.98"')

# A healthy PO provider must be a recovery tool, not a reason to force mweb
# for every normal YouTube download. mweb increasingly returns segmented HLS,
# which caused the repeated per-fragment speed resets visible in the user's log.
replace_once(
    '''    elif pot_ready:
        extractor_args = "youtube:player_client=mweb"
        if fast_extract:
            extractor_args += ";skip=hls,dash,translated_subs"

        command += [
            "--extractor-args",
            extractor_args,
        ]

    elif fast_extract:
''',
    '''    elif pot_ready:
        # V32.98: prefer yt-dlp's normal direct client first. The existing
        # Smart Recovery path still tries mweb+PO if the direct URL fails.
        if fast_extract:
            command += [
                "--extractor-args",
                "youtube:skip=hls,dash,translated_subs",
            ]

    elif fast_extract:
''',
)

# Browser-captured HLS/DASH emits a fresh instantaneous rate for every small
# fragment. Smooth only the UI number; raw engine values remain in the log.
replace_once(
    '''    browser_worker_started_at = time.perf_counter()
    browser_first_transfer_logged = False
''',
    '''    browser_worker_started_at = time.perf_counter()
    browser_first_transfer_logged = False
    browser_speed_ema = None
''',
)

replace_once(
    '''        nonlocal browser_first_transfer_logged

        if not browser_first_transfer_logged:
''',
    '''        nonlocal browser_first_transfer_logged
        nonlocal browser_speed_ema

        # V32.98 stable browser speed: yt-dlp restarts its instantaneous
        # estimator at every media fragment. An exponential moving average
        # represents the real sustained transfer much more like IDM.
        raw_speed = str(speed or "").strip()
        match = re.fullmatch(
            r"([0-9.]+)\\s*(KiB|MiB|GiB|KB|MB|GB)/s",
            raw_speed,
            re.IGNORECASE,
        )
        if match:
            try:
                value = float(match.group(1))
                unit = match.group(2).lower()
                if unit in {"kib", "kb"}:
                    value *= 1024.0
                elif unit in {"mib", "mb"}:
                    value *= 1024.0 * 1024.0
                else:
                    value *= 1024.0 * 1024.0 * 1024.0
                if browser_speed_ema is None:
                    browser_speed_ema = value
                else:
                    # Ignore one-fragment startup collapse without hiding a
                    # sustained slowdown. Normal samples converge quickly.
                    alpha = 0.10 if value < browser_speed_ema * 0.35 else 0.22
                    browser_speed_ema += alpha * (value - browser_speed_ema)
                speed = bytes_to_human(browser_speed_ema) + "/s"
            except Exception:
                pass

        if not browser_first_transfer_logged:
''',
)

# Find VLC when Windows registered only the executable/default association,
# not InstallDir/Path. This is common with winget and custom-drive installs.
old_registry = '''            registry_keys = (
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
'''
new_registry = '''            registry_keys = (
                (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\\VideoLAN\\VLC", "InstallDir"),
                (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\\WOW6432Node\\VideoLAN\\VLC", "InstallDir"),
                (winreg.HKEY_CURRENT_USER, r"SOFTWARE\\VideoLAN\\VLC", "InstallDir"),
                (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\App Paths\\vlc.exe", "Path"),
                (winreg.HKEY_CURRENT_USER, r"SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\App Paths\\vlc.exe", "Path"),
                (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\App Paths\\vlc.exe", ""),
                (winreg.HKEY_CURRENT_USER, r"SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\App Paths\\vlc.exe", ""),
                (winreg.HKEY_CLASSES_ROOT, r"Applications\\vlc.exe\\shell\\Open\\command", ""),
                (winreg.HKEY_CLASSES_ROOT, r"VLC.mp4\\shell\\Open\\command", ""),
            )
            for hive, key_name, value_name in registry_keys:
                try:
                    with winreg.OpenKey(hive, key_name) as key:
                        value = str(winreg.QueryValueEx(key, value_name)[0] or "").strip()
                        if not value:
                            continue
                        exe_match = re.match(r'^"([^"]+\\\\vlc\\.exe)"', value, re.I)
                        if exe_match:
                            candidates.append(os.path.dirname(exe_match.group(1)))
                        elif value.lower().endswith("vlc.exe"):
                            candidates.append(os.path.dirname(value.strip('"')))
                        else:
                            candidates.append(value.strip('"'))
                except OSError:
                    pass
'''
replace_once(old_registry, new_registry)

# Never fail silently at the exact interaction the user is testing.
replace_once(
    '''        folder = _v3296_vlc_directory()
        if not folder:
            return False
''',
    '''        folder = _v3296_vlc_directory()
        if not folder:
            log("🎬 Preview click received, but libvlc.dll was not found on this PC.")
            return False
        log("🎬 VLC found for embedded preview: " + folder)
''',
)

replace_once(
    '''def _v3271_open_preview(event=None):
    path = None
''',
    '''def _v3271_open_preview(event=None):
    try:
        log("🎬 Preview click received.")
    except Exception:
        pass
    path = None
''',
)

# Bind both press and keyboard activation. bind() replaces any stale binding
# left by a prior hot update; Return/Space make the control testable too.
replace_once(
    '''v3270_preview.bind("<Button-1>", _v3271_open_preview, add="+")
''',
    '''v3270_preview.bind("<ButtonRelease-1>", _v3271_open_preview)
v3270_preview.bind("<Return>", _v3271_open_preview)
v3270_preview.bind("<space>", _v3271_open_preview)
''',
)

ast.parse(text)
app_path.write_text(text, encoding="utf-8")

app_hash = hashlib.sha256(app_path.read_bytes()).hexdigest()
manifest_path = Path("payload/update_manifest.json")
manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
manifest["version"] = version
manifest["created_by"] = (
    "v32.98 prefers direct YouTube extraction, smooths fragment speed in the UI, "
    "and expands embedded VLC discovery and click diagnostics"
)
manifest["files"][0]["sha256"] = app_hash
manifest["files"][0]["size"] = app_path.stat().st_size
manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")

print("VERIFIED v32.98 app.py sha256", app_hash)
