from pathlib import Path
import ast
import hashlib
import json
import sys


version = sys.argv[1]
assert version == "32.99"

app_path = Path("payload/app.py")
text = app_path.read_text(encoding="utf-8-sig")


def replace_once(old, new):
    global text
    assert text.count(old) == 1, (old[:160], text.count(old))
    text = text.replace(old, new, 1)


replace_once('APP_VERSION = "32.98"', 'APP_VERSION = "32.99"')

start_marker = "# V32.96 — real in-panel playback through the user's installed VLC."
end_marker = 'v3270_preview.bind("<space>", _v3271_open_preview)\n'
start = text.index(start_marker)
end = text.index(end_marker, start) + len(end_marker)

new_preview = r'''# V32.99 — dependable in-panel playback through Z2SE's verified FFmpeg.
# libVLC depended on how VLC was installed on each PC. This decoder uses the
# FFmpeg path already found by Z2SE, paints frames directly on the Tk canvas,
# and uses ffplay (when present) as a hidden audio companion.
v3296_vlc = {
    "player": None,
    "audio": None,
    "path": None,
    "paused": False,
    "request": 0,
    "photo": None,
}


def _v3299_process_pause(process, pause=True):
    if os.name != "nt" or process is None or process.poll() is not None:
        return False
    handle = None
    try:
        access = 0x0800  # PROCESS_SUSPEND_RESUME
        kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
        ntdll = ctypes.WinDLL("ntdll")
        kernel32.OpenProcess.argtypes = [ctypes.c_uint32, ctypes.c_bool, ctypes.c_uint32]
        kernel32.OpenProcess.restype = ctypes.c_void_p
        kernel32.CloseHandle.argtypes = [ctypes.c_void_p]
        handle = kernel32.OpenProcess(access, False, int(process.pid))
        if not handle:
            return False
        function = ntdll.NtSuspendProcess if pause else ntdll.NtResumeProcess
        function.argtypes = [ctypes.c_void_p]
        function.restype = ctypes.c_long
        return function(handle) == 0
    except Exception:
        return False
    finally:
        try:
            if handle:
                kernel32.CloseHandle(handle)
        except Exception:
            pass


def _v3299_show_frame(raw_frame, process, media_path):
    if process is not v3296_vlc.get("player"):
        return
    if str(media_path) != str(v3296_vlc.get("path") or ""):
        return
    try:
        if Image is None or ImageTk is None:
            return
        image = Image.frombytes("RGB", (320, 118), raw_frame)
        photo = ImageTk.PhotoImage(image)
        v3270_preview.delete("all")
        width = max(260, int(v3270_preview.winfo_width() or 320))
        v3270_preview.create_image(width // 2, 59, image=photo)
        v3296_vlc["photo"] = photo
    except Exception as exc:
        log("FFmpeg preview frame warning: " + str(exc))


def _v3296_stop_embedded_preview():
    v3296_vlc["request"] = int(v3296_vlc.get("request") or 0) + 1
    for key in ("player", "audio"):
        process = v3296_vlc.get(key)
        try:
            if process is not None and process.poll() is None:
                process.terminate()
        except Exception:
            pass
    v3296_vlc["player"] = None
    v3296_vlc["audio"] = None
    v3296_vlc["path"] = None
    v3296_vlc["paused"] = False
    v3296_vlc["photo"] = None


def _v3299_preview_worker(process, media_path, request_id):
    frame_bytes = 320 * 118 * 3
    try:
        while (
            request_id == v3296_vlc.get("request")
            and process is v3296_vlc.get("player")
            and process.poll() is None
        ):
            data = process.stdout.read(frame_bytes)
            if not data or len(data) != frame_bytes:
                break
            try:
                root.after(
                    0,
                    lambda frame=data, proc=process, path=media_path:
                        _v3299_show_frame(frame, proc, path),
                )
            except Exception:
                break
    except Exception as exc:
        try:
            log("FFmpeg embedded preview worker warning: " + str(exc))
        except Exception:
            pass


def _v3296_play_inside(path):
    video_exts = {".mp4", ".mkv", ".webm", ".mov", ".avi", ".m4v", ".ts"}
    normalized = os.path.normcase(os.path.abspath(str(path or "")))
    if Path(normalized).suffix.lower() not in video_exts:
        log("FFmpeg preview skipped: selected file is not a video.")
        return False
    if Image is None or ImageTk is None:
        log("FFmpeg preview unavailable: Pillow/ImageTk is missing.")
        return False
    if not FFMPEG or not os.path.isfile(FFMPEG):
        log("FFmpeg preview unavailable: FFmpeg executable was not found.")
        return False

    current = v3296_vlc.get("player")
    if current is not None and v3296_vlc.get("path") == normalized:
        pause = not bool(v3296_vlc.get("paused"))
        changed = _v3299_process_pause(current, pause)
        audio = v3296_vlc.get("audio")
        if audio is not None:
            _v3299_process_pause(audio, pause)
        if changed:
            v3296_vlc["paused"] = pause
            log("⏸ Embedded FFmpeg preview paused." if pause else "▶ Embedded FFmpeg preview resumed.")
            return True
        _v3296_stop_embedded_preview()

    try:
        _v3296_stop_embedded_preview()
        creationflags = subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0
        command = [
            FFMPEG,
            "-hide_banner", "-loglevel", "error", "-re", "-i", normalized,
            "-an", "-vf",
            "scale=320:118:force_original_aspect_ratio=decrease,pad=320:118:(ow-iw)/2:(oh-ih)/2:black",
            "-r", "15", "-f", "rawvideo", "-pix_fmt", "rgb24", "pipe:1",
        ]
        process = subprocess.Popen(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            stdin=subprocess.DEVNULL,
            creationflags=creationflags,
        )
        v3296_vlc["request"] = int(v3296_vlc.get("request") or 0) + 1
        request_id = v3296_vlc["request"]
        v3296_vlc["player"] = process
        v3296_vlc["path"] = normalized
        v3296_vlc["paused"] = False

        ffplay = os.path.join(FFMPEG_DIR, "ffplay.exe" if os.name == "nt" else "ffplay")
        if os.path.isfile(ffplay):
            try:
                v3296_vlc["audio"] = subprocess.Popen(
                    [ffplay, "-nodisp", "-autoexit", "-loglevel", "quiet", "-volume", "80", normalized],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    stdin=subprocess.DEVNULL,
                    creationflags=creationflags,
                )
            except Exception as exc:
                log("Embedded preview audio warning: " + str(exc))

        threading.Thread(
            target=_v3299_preview_worker,
            args=(process, normalized, request_id),
            daemon=True,
        ).start()
        log("▶ Embedded FFmpeg preview playing: " + os.path.basename(normalized))
        return True
    except Exception as exc:
        _v3296_stop_embedded_preview()
        log("Embedded FFmpeg preview error: " + str(exc))
        return False


def _v3271_open_preview(event=None):
    try:
        log("🎬 Preview click received.")
    except Exception:
        pass
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
        log("Preview click: finished media path was not found.")
        try:
            messagebox.showinfo("Z²SE", "Le fichier vidéo n’est pas encore disponible ou a été déplacé.")
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
            messagebox.showerror("Z²SE", f"Impossible d’ouvrir le fichier.\n\n{exc}")
        except Exception:
            pass
    return "break"


v3270_preview.bind("<ButtonRelease-1>", _v3271_open_preview)
v3270_preview.bind("<Return>", _v3271_open_preview)
v3270_preview.bind("<space>", _v3271_open_preview)
'''

text = text[:start] + new_preview + text[end:]

# Update the selected row's basic details and progress before thumbnail/player
# work. Any preview exception can no longer leave a completed item at 0%.
old_refresh = '''        while len(values) < 9:
            values.append("")
        v3270_detail_title.set(str(values[1] or "Téléchargement"))
'''
new_refresh = '''        while len(values) < 9:
            values.append("")
        status = str(values[8] or "—")
        low = status.lower()
        is_done = any(k in low for k in ("done", "termin", "saved", "complete"))
        try:
            pct = float(str(values[4]).replace("%", "").strip() or 0)
        except Exception:
            pct = 0.0
        pct = 100.0 if is_done else max(0.0, min(100.0, pct))
        v3270_detail_percent.set(pct)
        v3270_detail_percent_text.set(f"{pct:.1f}%")
        v3270_detail_title.set(str(values[1] or "Téléchargement"))
'''
replace_once(old_refresh, new_refresh)

# The old block redefines the same state later; keep one authoritative value.
replace_once(
    '''        status = str(values[8] or "—")
        v3270_detail_status.set(status)
        low = status.lower()
        is_done = any(k in low for k in ("done", "termin", "saved", "complete"))
''',
    '''        v3270_detail_status.set(status)
''',
)

ast.parse(text)
app_path.write_text(text, encoding="utf-8")

app_hash = hashlib.sha256(app_path.read_bytes()).hexdigest()
manifest_path = Path("payload/update_manifest.json")
manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
manifest["version"] = version
manifest["created_by"] = (
    "v32.99 replaces libVLC preview with direct FFmpeg canvas playback and "
    "synchronizes completed detail progress before preview work"
)
manifest["files"][0]["sha256"] = app_hash
manifest["files"][0]["size"] = app_path.stat().st_size
manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")

print("VERIFIED v32.99 app.py sha256", app_hash)
