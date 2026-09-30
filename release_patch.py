from pathlib import Path
import ast, hashlib, json, sys

version = sys.argv[1]
assert version == "33.09"
app_path = Path("payload/app.py")
text = app_path.read_text(encoding="utf-8-sig")

def replace_once(old, new):
    global text
    assert text.count(old) == 1, (old[:180], text.count(old))
    text = text.replace(old, new, 1)

replace_once('APP_VERSION = "33.08"', 'APP_VERSION = "33.09"')

replace_once(
    '''single_output_path = ""

# V32.22''',
    '''single_output_path = ""

# V33.09 — active streams for non-destructive Live Preview.
live_preview_sources = {}
live_preview_sources_lock = threading.Lock()

# V32.22''',
)

replace_once(
    '''    video_url = source["video_url"]
    audio_url = source.get(
        "audio_url"
    )

    verified_height''',
    '''    video_url = source["video_url"]
    audio_url = source.get(
        "audio_url"
    )

    # Never open the unfinished destination. Keep the resolved inputs so an
    # independent short preview can run without pausing the real download.
    live_index = _current_job_index()
    if live_index is not None and str(media_format or "MP4").upper() == "MP4":
        with live_preview_sources_lock:
            live_preview_sources[int(live_index)] = {
                "video_url": str(video_url or ""),
                "audio_url": str(audio_url or ""),
                "referer": str(referer or ""),
                "title": str(output_name or "Video"),
            }

    verified_height''',
)

# An external audio rendition is not optional. If it cannot be read, fail the
# job instead of producing a green "Done" row with a silent MP4/MP3.
replace_once(
    '''        # If an external audio group exists, use it directly.
        if audio_url:
            command += [
                "-map", "1:a:0?",
            ]''',
    '''        # If an external audio group exists, it must be present.
        if audio_url:
            command += [
                "-map", "1:a:0",
            ]''',
)
replace_once(
    '''        if audio_url:
            command += [
                "-map", "1:a:0?",
            ]
        else:
            command += [
                "-map", "0:a:0?",
            ]

        command += [
            "-c", "copy",''',
    '''        if audio_url:
            command += [
                "-map", "1:a:0",
            ]
        else:
            command += [
                "-map", "0:a:0?",
            ]

        command += [
            "-c", "copy",''',
)

helpers = r'''

# V33.09 — IDM-style test during an active HLS download. The final MP4 has no
# closing index yet, so create a separate finalized 15-second video+audio sample.
v3309_live_preview = {"request": 0, "building": False, "index": None}

def _v3309_selected_job_index():
    try:
        selection = list(bulk_tree.selection())
        if not selection:
            return None
        for index, item_id in list(bulk_tree_ids.items()):
            if item_id == selection[0]:
                return int(index)
    except Exception:
        pass
    return None

def _v3309_live_source(index):
    if index is None:
        return None
    try:
        with live_preview_sources_lock:
            value = live_preview_sources.get(int(index))
            return dict(value) if value else None
    except Exception:
        return None

def _v3309_draw_live_status(label):
    try:
        v3270_preview.delete("all")
        width = max(260, int(v3270_preview.winfo_width() or 320))
        v3270_preview.create_text(
            width // 2, 47, text="▶  LIVE PREVIEW", fill="#13cfff",
            font=("Segoe UI Semibold", 11),
        )
        v3270_preview.create_text(
            width // 2, 75, text=str(label), fill="#d7e8f7",
            font=("Segoe UI", 9),
        )
    except Exception:
        pass

def _v3309_finish_live_preview(index, request_id, sample_path, error_text=""):
    if request_id != v3309_live_preview.get("request"):
        return
    v3309_live_preview["building"] = False
    if _v3309_selected_job_index() != index:
        return
    if sample_path and os.path.isfile(sample_path) and os.path.getsize(sample_path) > 4096:
        v3271_preview_enabled["path"] = sample_path
        log("✅ Live Preview ready with video + audio: " + os.path.basename(sample_path))
        _v3295_request_video_preview(sample_path)
        _v3296_play_inside(sample_path)
        return
    _v3295_draw_preview_placeholder("Z²SE  •  LIVE PREVIEW ERROR")
    log("❌ Live Preview could not be created" + ((": " + error_text) if error_text else "."))
    try:
        messagebox.showerror(
            "Z²SE Live Preview",
            "Impossible de créer l’aperçu maintenant. Le téléchargement principal continue normalement.",
        )
    except Exception:
        pass

def _v3309_start_live_preview(index):
    source = _v3309_live_source(index)
    if not source or not source.get("video_url"):
        return False
    if v3309_live_preview.get("building"):
        _v3309_draw_live_status("Préparation en cours…")
        return True

    v3309_live_preview["request"] = int(v3309_live_preview.get("request") or 0) + 1
    request_id = v3309_live_preview["request"]
    v3309_live_preview.update({"building": True, "index": int(index)})
    _v3296_stop_embedded_preview()
    _v3309_draw_live_status("Vidéo + son • 15 secondes…")
    log("🎬 Live Preview: preparing an independent 15-second video + audio sample…")

    def worker():
        sample_path, error_text = "", ""
        try:
            cache_dir = os.path.join(CACHE_DIR, "_live_preview")
            os.makedirs(cache_dir, exist_ok=True)
            identity = "|".join((str(index), source.get("video_url", ""), source.get("audio_url", "")))
            sample_path = os.path.join(
                cache_dir,
                hashlib.sha256(identity.encode("utf-8", errors="ignore")).hexdigest() + ".mp4",
            )
            if not os.path.isfile(sample_path) or os.path.getsize(sample_path) < 4096:
                partial_path = sample_path + ".building"
                try:
                    if os.path.isfile(partial_path):
                        os.unlink(partial_path)
                except Exception:
                    pass
                headers = (
                    "User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/152.0.0.0 Safari/537.36\\r\\n"
                )
                if source.get("referer"):
                    headers += "Referer: " + source["referer"] + "\\r\\n"
                command = [
                    FFMPEG, "-hide_banner", "-loglevel", "error", "-y",
                    "-headers", headers, "-i", source["video_url"],
                ]
                if source.get("audio_url"):
                    command += ["-headers", headers, "-i", source["audio_url"]]
                command += ["-t", "15", "-map", "0:v:0"]
                command += ["-map", "1:a:0"] if source.get("audio_url") else ["-map", "0:a:0?"]
                command += [
                    "-c", "copy", "-avoid_negative_ts", "make_zero",
                    "-movflags", "+faststart", "-f", "mp4", partial_path,
                ]
                creationflags = subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0
                completed = subprocess.run(
                    command, env=build_tool_env(), stdout=subprocess.DEVNULL,
                    stderr=subprocess.PIPE, timeout=75, creationflags=creationflags,
                )
                if completed.returncode != 0:
                    error_text = completed.stderr.decode("utf-8", errors="replace")[-500:].strip()
                    sample_path = ""
                elif os.path.isfile(partial_path) and os.path.getsize(partial_path) > 4096:
                    os.replace(partial_path, sample_path)
                else:
                    sample_path = ""
        except Exception as exc:
            error_text, sample_path = str(exc), ""
        try:
            root.after(0, lambda: _v3309_finish_live_preview(
                int(index), request_id, sample_path, error_text,
            ))
        except Exception:
            pass

    threading.Thread(target=worker, daemon=True).start()
    return True
'''

replace_once("\n\ndef _v3271_open_preview(event=None):", helpers + "\n\ndef _v3271_open_preview(event=None):")

replace_once(
    '''        if not path:
            log("Preview click: no valid cached or exact media path was found.")
            try:
                messagebox.showinfo("Z²SE", "Le fichier vidéo n’est pas encore disponible ou a été déplacé.")
            except Exception:
                pass
            return "break"
''',
    '''        if not path:
            live_index = _v3309_selected_job_index()
            if _v3309_start_live_preview(live_index):
                return "break"
            log("Preview click: no finished file or active stream is available yet.")
            try:
                messagebox.showinfo(
                    "Z²SE",
                    "L’aperçu sera disponible dès que le flux vidéo démarre. Le téléchargement continue normalement.",
                )
            except Exception:
                pass
            return "break"
''',
)

replace_once(
    '''            v3270_preview.configure(cursor=("hand2" if media_path else "arrow"))''',
    '''            live_ready = bool(_v3309_live_source(_v3309_selected_job_index()))
            v3270_preview.configure(cursor=("hand2" if (media_path or live_ready) else "arrow"))''',
)

# The details pane refreshes every second. Preserve the live sample/status while
# the selected active row owns it instead of resetting the canvas to placeholder.
replace_once(
    '''        old_preview_path = v3271_preview_enabled.get("path")
        if str(old_preview_path or "") != str(media_path or ""):
''',
    '''        selected_live_index = _v3309_selected_job_index()
        owns_live_preview = (
            not is_done
            and selected_live_index is not None
            and int(v3309_live_preview.get("index") or -1) == int(selected_live_index)
        )
        if owns_live_preview and v3309_live_preview.get("building"):
            try:
                v3270_preview.configure(cursor="hand2")
            except Exception:
                pass
            return
        if owns_live_preview:
            live_sample = str(v3271_preview_enabled.get("path") or "")
            if live_sample and os.path.isfile(live_sample):
                media_path = live_sample

        old_preview_path = v3271_preview_enabled.get("path")
        if str(old_preview_path or "") != str(media_path or ""):
''',
)

ast.parse(text)
app_path.write_text(text, encoding="utf-8")
app_hash = hashlib.sha256(app_path.read_bytes()).hexdigest()
manifest_path = Path("payload/update_manifest.json")
manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
manifest["version"] = version
manifest["created_by"] = "v33.09 adds non-destructive Live Preview with separate Forja video and audio streams"
manifest["files"][0]["sha256"] = app_hash
manifest["files"][0]["size"] = app_path.stat().st_size
manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
print("VERIFIED v33.09 app.py sha256", app_hash)
