from pathlib import Path
import ast
import hashlib
import json
import sys


version = sys.argv[1]
assert version == "32.96"

app_path = Path("payload/app.py")
text = app_path.read_text(encoding="utf-8-sig")


def replace_once(old, new):
    global text
    assert text.count(old) == 1, (old[:120], text.count(old))
    text = text.replace(old, new, 1)


replace_once('APP_VERSION = "32.95"', 'APP_VERSION = "32.96"')

# A plain YouTube 403 usually means the signed googlevideo URL expired. Try a
# fresh default extraction immediately, before the expensive engine/provider
# maintenance path. Only repair tools if this quick path also fails.
old_recovery = '''    profile = _get_download_error_profile()
    needs_engine_repair = bool(
        code != 0
        and (
            saw_403
            or profile.get("saw_403")
            or profile.get("saw_pot_problem")
            or profile.get("saw_auth_problem")
        )
    )
'''
new_recovery = '''    profile = _get_download_error_profile()

    # V32.96 FAST 403 REFRESH:
    # Do not make the user wait for yt-dlp update + Deno/provider repair when
    # the common failure is only an expired signed media URL. Re-extract with
    # the provider-independent default client first. Matching .part bytes are
    # retained by v32.94 and resume automatically.
    quick_403_refresh = bool(
        code != 0
        and is_youtube_page_url(url)
        and (saw_403 or profile.get("saw_403"))
        and not profile.get("saw_rate_limit")
        and not should_stop_current_job()
    )
    if quick_403_refresh:
        prefix = f"[{job_label}] " if job_label else ""
        log(prefix + "⚡ HTTP 403: refreshing media URL immediately (heavy repair deferred)...")
        code, saw_403, stopped, saw_format_problem = run_download_once(
            url=url,
            quality=quality,
            mode=mode,
            start=start,
            end=end,
            output_prefix=output_prefix,
            progress_callback=progress_callback,
            stats_callback=stats_callback,
            job_label=job_label,
            fast_extract=False,
            media_format=media_format,
            output_name=output_name,
            referer=referer,
            youtube_client="default",
        )
        if stopped:
            return code, "stopped"
        profile = _get_download_error_profile()

    needs_engine_repair = bool(
        code != 0
        and (
            saw_403
            or profile.get("saw_403")
            or profile.get("saw_pot_problem")
            or profile.get("saw_auth_problem")
        )
    )
'''
replace_once(old_recovery, new_recovery)

old_open = '''def _v3271_open_preview(event=None):
    path = None
    try:
        selection = list(bulk_tree.selection())
        if selection:
            path = _find_download_file_for_row(selection[0])
    except Exception:
        path = None

    if not path:
        path = v3271_preview_enabled.get("path")

    path = str(path or "").strip()
    if not path or not os.path.isfile(path):
        try:
            messagebox.showinfo(
                "Z²SE",
                "Le fichier vidéo n’est pas encore disponible ou a été déplacé.",
            )
        except Exception:
            pass
        return "break"

    try:
        os.startfile(os.path.normpath(path))
        log("▶ Preview opened: " + os.path.basename(path))
    except Exception as exc:
        try:
            messagebox.showerror("Z²SE", f"Impossible d’ouvrir le fichier.\\n\\n{exc}")
        except Exception:
            pass
    return "break"
'''

new_open = '''# V32.96 — real in-panel playback through the user's installed VLC.
# This calls libVLC directly, so no extra Python package is required. If VLC
# is absent or cannot initialize, the existing external-player behavior stays
# available as a safe fallback.
v3296_vlc = {
    "dll": None,
    "dll_dir_handle": None,
    "instance": None,
    "player": None,
    "media": None,
    "path": None,
    "failed": False,
}


def _v3296_vlc_directory():
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


def _v3296_prepare_vlc():
    if os.name != "nt" or v3296_vlc.get("failed"):
        return False
    if v3296_vlc.get("instance"):
        return True
    try:
        folder = _v3296_vlc_directory()
        if not folder:
            return False
        os.environ["VLC_PLUGIN_PATH"] = os.path.join(folder, "plugins")
        if hasattr(os, "add_dll_directory"):
            v3296_vlc["dll_dir_handle"] = os.add_dll_directory(folder)
        dll = ctypes.CDLL(os.path.join(folder, "libvlc.dll"))

        dll.libvlc_new.argtypes = [ctypes.c_int, ctypes.POINTER(ctypes.c_char_p)]
        dll.libvlc_new.restype = ctypes.c_void_p
        dll.libvlc_media_new_path.argtypes = [ctypes.c_void_p, ctypes.c_char_p]
        dll.libvlc_media_new_path.restype = ctypes.c_void_p
        dll.libvlc_media_player_new_from_media.argtypes = [ctypes.c_void_p]
        dll.libvlc_media_player_new_from_media.restype = ctypes.c_void_p
        dll.libvlc_media_player_set_hwnd.argtypes = [ctypes.c_void_p, ctypes.c_void_p]
        dll.libvlc_media_player_play.argtypes = [ctypes.c_void_p]
        dll.libvlc_media_player_play.restype = ctypes.c_int
        dll.libvlc_media_player_pause.argtypes = [ctypes.c_void_p]
        dll.libvlc_media_player_stop.argtypes = [ctypes.c_void_p]
        dll.libvlc_media_player_is_playing.argtypes = [ctypes.c_void_p]
        dll.libvlc_media_player_is_playing.restype = ctypes.c_int
        dll.libvlc_audio_set_volume.argtypes = [ctypes.c_void_p, ctypes.c_int]
        dll.libvlc_media_player_release.argtypes = [ctypes.c_void_p]
        dll.libvlc_media_release.argtypes = [ctypes.c_void_p]

        options = (ctypes.c_char_p * 3)(
            b"--no-video-title-show",
            b"--quiet",
            b"--no-metadata-network-access",
        )
        instance = dll.libvlc_new(3, options)
        if not instance:
            raise RuntimeError("libVLC instance unavailable")
        v3296_vlc["dll"] = dll
        v3296_vlc["instance"] = instance
        log("🎬 Embedded VLC preview ready.")
        return True
    except Exception as exc:
        v3296_vlc["failed"] = True
        try:
            log("Embedded VLC unavailable; external fallback kept: " + str(exc))
        except Exception:
            pass
        return False


def _v3296_stop_embedded_preview():
    dll = v3296_vlc.get("dll")
    player = v3296_vlc.get("player")
    media = v3296_vlc.get("media")
    try:
        if dll and player:
            dll.libvlc_media_player_stop(player)
    except Exception:
        pass
    try:
        if dll and player:
            dll.libvlc_media_player_release(player)
    except Exception:
        pass
    try:
        if dll and media:
            dll.libvlc_media_release(media)
    except Exception:
        pass
    v3296_vlc["player"] = None
    v3296_vlc["media"] = None
    v3296_vlc["path"] = None


def _v3296_play_inside(path):
    video_exts = {".mp4", ".mkv", ".webm", ".mov", ".avi", ".m4v", ".ts"}
    if Path(path).suffix.lower() not in video_exts or not _v3296_prepare_vlc():
        return False
    try:
        dll = v3296_vlc["dll"]
        normalized = os.path.normcase(os.path.abspath(path))
        player = v3296_vlc.get("player")
        if player and v3296_vlc.get("path") == normalized:
            if dll.libvlc_media_player_is_playing(player):
                dll.libvlc_media_player_pause(player)
                log("⏸ Embedded preview paused.")
            else:
                dll.libvlc_media_player_play(player)
                log("▶ Embedded preview resumed.")
            return True

        _v3296_stop_embedded_preview()
        encoded = os.path.abspath(path).encode("utf-8")
        media = dll.libvlc_media_new_path(v3296_vlc["instance"], encoded)
        if not media:
            return False
        player = dll.libvlc_media_player_new_from_media(media)
        if not player:
            dll.libvlc_media_release(media)
            return False
        v3270_preview.update_idletasks()
        dll.libvlc_media_player_set_hwnd(
            player,
            ctypes.c_void_p(int(v3270_preview.winfo_id())),
        )
        dll.libvlc_audio_set_volume(player, 80)
        if dll.libvlc_media_player_play(player) < 0:
            dll.libvlc_media_player_release(player)
            dll.libvlc_media_release(media)
            return False
        v3296_vlc["player"] = player
        v3296_vlc["media"] = media
        v3296_vlc["path"] = normalized
        log("▶ Embedded preview playing: " + os.path.basename(path))
        return True
    except Exception as exc:
        _v3296_stop_embedded_preview()
        log("Embedded preview error; opening externally: " + str(exc))
        return False


def _v3271_open_preview(event=None):
    path = None
    try:
        selection = list(bulk_tree.selection())
        if selection:
            path = _find_download_file_for_row(selection[0])
    except Exception:
        path = None

    if not path:
        path = v3271_preview_enabled.get("path")

    path = str(path or "").strip()
    if not path or not os.path.isfile(path):
        try:
            messagebox.showinfo(
                "Z²SE",
                "Le fichier vidéo n’est pas encore disponible ou a été déplacé.",
            )
        except Exception:
            pass
        return "break"

    if _v3296_play_inside(path):
        return "break"

    try:
        os.startfile(os.path.normpath(path))
        log("▶ External preview fallback: " + os.path.basename(path))
    except Exception as exc:
        try:
            messagebox.showerror("Z²SE", f"Impossible d’ouvrir le fichier.\\n\\n{exc}")
        except Exception:
            pass
    return "break"
'''
replace_once(old_open, new_open)

replace_once(
    '''v3270_tip = tk.Label(
    details_panel,
    text="▶ Cliquez sur l’aperçu pour lire le fichier terminé.\\nDouble-cliquez sur une ligne pour les détails.",''',
    '''v3270_tip = tk.Label(
    details_panel,
    text="▶ Cliquez pour lire / mettre en pause dans Z²SE.\\nDouble-cliquez sur une ligne pour ouvrir le fichier.",''',
)

# Stop the old in-panel player before drawing another selected video's frame.
replace_once(
    '''        v3271_preview_enabled["path"] = media_path
        try:
            v3270_preview.configure(cursor=("hand2" if media_path else "arrow"))''',
    '''        old_preview_path = v3271_preview_enabled.get("path")
        if str(old_preview_path or "") != str(media_path or ""):
            _v3296_stop_embedded_preview()
        v3271_preview_enabled["path"] = media_path
        try:
            v3270_preview.configure(cursor=("hand2" if media_path else "arrow"))''',
)

ast.parse(text)
app_path.write_text(text, encoding="utf-8")

app_hash = hashlib.sha256(app_path.read_bytes()).hexdigest()
manifest_path = Path("payload/update_manifest.json")
manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
manifest["version"] = version
manifest["created_by"] = (
    "v32.96 plays finished videos inside the details preview via installed libVLC "
    "and refreshes YouTube 403 URLs before expensive provider maintenance"
)
manifest["files"][0]["sha256"] = app_hash
manifest["files"][0]["size"] = app_path.stat().st_size
manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")

print("VERIFIED v32.96 app.py sha256", app_hash)
