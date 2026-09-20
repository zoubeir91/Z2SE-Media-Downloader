from pathlib import Path
import ast
import hashlib
import json
import sys


version = sys.argv[1]
assert version == "32.95"

app_path = Path("payload/app.py")
text = app_path.read_text(encoding="utf-8-sig")


def replace_once(old, new):
    global text
    assert text.count(old) == 1, (old[:120], text.count(old))
    text = text.replace(old, new, 1)


replace_once('APP_VERSION = "32.94"', 'APP_VERSION = "32.95"')

old_preview = '''v3270_preview.pack(fill="x", padx=14, pady=(0, 10))
v3270_preview.create_polygon(145, 34, 145, 84, 190, 59, fill=UI_ACCENT, outline="")
v3270_preview.create_text(18, 16, anchor="nw", text="Z²SE  •  MEDIA", fill=UI_MUTED, font=("Segoe UI Semibold", 9))


v3271_preview_enabled = {"path": None}
'''

new_preview = '''v3270_preview.pack(fill="x", padx=14, pady=(0, 10))

v3271_preview_enabled = {"path": None}
v3295_preview_state = {"request": 0, "photo": None}


def _v3295_draw_preview_placeholder(label="Z²SE  •  MEDIA"):
    """Draw the fallback only while no playable video thumbnail exists."""
    try:
        v3270_preview.delete("all")
        width = max(260, int(v3270_preview.winfo_width() or 0))
        height = 118
        v3270_preview.create_text(
            18, 16, anchor="nw", text=label, fill=UI_MUTED,
            font=("Segoe UI Semibold", 9),
        )
        center_x = width // 2
        center_y = height // 2 + 2
        v3270_preview.create_polygon(
            center_x - 13, center_y - 23,
            center_x - 13, center_y + 23,
            center_x + 27, center_y,
            fill=UI_ACCENT, outline="",
        )
        v3295_preview_state["photo"] = None
    except Exception:
        pass


def _v3295_placeholder_if_current(request_id, media_path):
    if request_id != v3295_preview_state.get("request"):
        return
    if str(media_path) != str(v3271_preview_enabled.get("path") or ""):
        return
    _v3295_draw_preview_placeholder()


def _v3295_show_video_frame(frame_path, media_path, request_id):
    """Create Tk image on the GUI thread and crop it to fill the preview."""
    if request_id != v3295_preview_state.get("request"):
        return
    if str(media_path) != str(v3271_preview_enabled.get("path") or ""):
        return
    try:
        if Image is None or ImageTk is None:
            _v3295_draw_preview_placeholder()
            return
        width = max(260, int(v3270_preview.winfo_width() or 0))
        height = 118
        with Image.open(frame_path) as source:
            image = source.convert("RGB")
            scale = max(width / max(1, image.width), height / max(1, image.height))
            resized = image.resize(
                (max(width, int(image.width * scale)), max(height, int(image.height * scale))),
                Image.Resampling.LANCZOS,
            )
            left = max(0, (resized.width - width) // 2)
            top = max(0, (resized.height - height) // 2)
            image = resized.crop((left, top, left + width, top + height))
            photo = ImageTk.PhotoImage(image)

        v3270_preview.delete("all")
        v3270_preview.create_image(width // 2, height // 2, image=photo)
        # Dark translucent-looking play disc keeps the control readable over
        # bright and dark thumbnails without hiding the real video frame.
        v3270_preview.create_oval(
            width // 2 - 27, height // 2 - 27,
            width // 2 + 27, height // 2 + 27,
            fill="#071523", outline="#dff7ff", width=1, stipple="gray50",
        )
        v3270_preview.create_polygon(
            width // 2 - 7, height // 2 - 15,
            width // 2 - 7, height // 2 + 15,
            width // 2 + 18, height // 2,
            fill="#ffffff", outline="",
        )
        v3270_preview.create_text(
            12, 10, anchor="nw", text="Z²SE  •  VIDEO",
            fill="#ffffff", font=("Segoe UI Semibold", 8),
        )
        v3295_preview_state["photo"] = photo
    except Exception as exc:
        _v3295_draw_preview_placeholder()
        try:
            log("Video preview render warning: " + str(exc))
        except Exception:
            pass


def _v3295_request_video_preview(media_path):
    """Extract one cached video frame in the background; never freeze the UI."""
    v3295_preview_state["request"] += 1
    request_id = v3295_preview_state["request"]
    path = str(media_path or "").strip()
    video_exts = {".mp4", ".mkv", ".webm", ".mov", ".avi", ".m4v", ".ts"}

    if not path or not os.path.isfile(path):
        _v3295_draw_preview_placeholder()
        return
    if Path(path).suffix.lower() not in video_exts:
        _v3295_draw_preview_placeholder("Z²SE  •  AUDIO")
        return
    if Image is None or ImageTk is None or not FFMPEG or not os.path.isfile(FFMPEG):
        _v3295_draw_preview_placeholder()
        return

    _v3295_draw_preview_placeholder("Z²SE  •  CHARGEMENT…")

    def worker():
        try:
            stat = os.stat(path)
            identity = f"{os.path.normcase(path)}|{stat.st_size}|{stat.st_mtime_ns}"
            cache_name = hashlib.sha256(identity.encode("utf-8", errors="ignore")).hexdigest() + ".jpg"
            cache_dir = os.path.join(CACHE_DIR, "_preview_frames")
            os.makedirs(cache_dir, exist_ok=True)
            frame_path = os.path.join(cache_dir, cache_name)

            if not os.path.isfile(frame_path) or os.path.getsize(frame_path) < 500:
                creationflags = subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0
                base = [
                    FFMPEG, "-hide_banner", "-loglevel", "error", "-y",
                    "-ss", "1", "-i", path, "-frames:v", "1",
                    "-vf", "scale=640:-2", "-q:v", "3", frame_path,
                ]
                result = subprocess.run(
                    base, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                    timeout=20, creationflags=creationflags,
                )
                if result.returncode != 0 or not os.path.isfile(frame_path):
                    fallback = [
                        FFMPEG, "-hide_banner", "-loglevel", "error", "-y",
                        "-i", path, "-frames:v", "1",
                        "-vf", "scale=640:-2", "-q:v", "3", frame_path,
                    ]
                    subprocess.run(
                        fallback, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                        timeout=20, creationflags=creationflags,
                    )

            if os.path.isfile(frame_path) and os.path.getsize(frame_path) >= 500:
                root.after(
                    0,
                    lambda: _v3295_show_video_frame(frame_path, path, request_id),
                )
            else:
                root.after(
                    0,
                    lambda: _v3295_placeholder_if_current(request_id, path),
                )
        except Exception as exc:
            try:
                log("Video preview extraction warning: " + str(exc))
            except Exception:
                pass
            try:
                root.after(
                    0,
                    lambda: _v3295_placeholder_if_current(request_id, path),
                )
            except Exception:
                pass

    threading.Thread(target=worker, daemon=True).start()


_v3295_draw_preview_placeholder()
'''

replace_once(old_preview, new_preview)

replace_once(
    '''        try:
            v3270_preview.configure(cursor=("hand2" if media_path else "arrow"))
        except Exception:
            pass
        color = UI_ACCENT''',
    '''        try:
            v3270_preview.configure(cursor=("hand2" if media_path else "arrow"))
        except Exception:
            pass
        _v3295_request_video_preview(media_path)
        color = UI_ACCENT''',
)

ast.parse(text)
app_path.write_text(text, encoding="utf-8")

app_hash = hashlib.sha256(app_path.read_bytes()).hexdigest()
manifest_path = Path("payload/update_manifest.json")
manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
manifest["version"] = version
manifest["created_by"] = (
    "v32.95 shows a cached real video frame in the right-hand details preview, "
    "with asynchronous FFmpeg extraction and a clickable play overlay"
)
manifest["files"][0]["sha256"] = app_hash
manifest["files"][0]["size"] = app_path.stat().st_size
manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")

print("VERIFIED v32.95 app.py sha256", app_hash)
