from pathlib import Path
import ast
import hashlib
import json
import sys

version = sys.argv[1]
assert version == "33.03"
app_path = Path("payload/app.py")
text = app_path.read_text(encoding="utf-8-sig")

def replace_once(old, new):
    global text
    assert text.count(old) == 1, (old[:180], text.count(old))
    text = text.replace(old, new, 1)

replace_once('APP_VERSION = "33.02"', 'APP_VERSION = "33.03"')

old_stop = '''def _v3296_stop_embedded_preview():
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
'''

new_stop = '''def _v3296_stop_embedded_preview():
    # V33.03: release the media file synchronously. Merely calling terminate()
    # could leave ffmpeg/ffplay alive after a row was cleared or Z2SE quit.
    v3296_vlc["request"] = int(v3296_vlc.get("request") or 0) + 1
    processes = [v3296_vlc.get("player"), v3296_vlc.get("audio")]
    v3296_vlc["player"] = None
    v3296_vlc["audio"] = None
    v3296_vlc["path"] = None
    v3296_vlc["paused"] = False
    v3296_vlc["photo"] = None

    for process in processes:
        if process is None:
            continue
        try:
            if process.poll() is None:
                process.terminate()
                try:
                    process.wait(timeout=0.75)
                except subprocess.TimeoutExpired:
                    process.kill()
                    process.wait(timeout=0.75)
        except Exception:
            try:
                if process.poll() is None:
                    process.kill()
            except Exception:
                pass
        finally:
            for stream_name in ("stdout", "stderr", "stdin"):
                try:
                    stream = getattr(process, stream_name, None)
                    if stream is not None:
                        stream.close()
                except Exception:
                    pass
'''
replace_once(old_stop, new_stop)

# Clearing history also clears the preview and releases the selected file.
replace_once(
    '''def clear_download_list():
    if downloads_are_running():
''',
    '''def clear_download_list():
    if downloads_are_running():
''',
)
replace_once(
    '''        return

    for item in bulk_tree.get_children():
        bulk_tree.delete(item)
''',
    '''        return

    try:
        _v3296_stop_embedded_preview()
        v3271_preview_enabled["path"] = None
    except Exception:
        pass

    for item in bulk_tree.get_children():
        bulk_tree.delete(item)
''',
)

# A real Quit must reap the preview children before destroying Tk.
replace_once(
    '''    app_quitting = True
    try:
        persist_pending_queue()
''',
    '''    app_quitting = True
    try:
        _v3296_stop_embedded_preview()
    except Exception:
        pass
    try:
        persist_pending_queue()
''',
)

# Removing selected history can otherwise leave its preview process alive.
replace_once(
    '''def remove_selected_from_list():
    items = _selected_download_items()
''',
    '''def remove_selected_from_list():
    items = _selected_download_items()
''',
)
replace_once(
    '''    for item_id in items:
        row_file_paths.pop(
''',
    '''    try:
        _v3296_stop_embedded_preview()
        v3271_preview_enabled["path"] = None
    except Exception:
        pass

    for item_id in items:
        row_file_paths.pop(
''',
)

ast.parse(text)
app_path.write_text(text, encoding="utf-8")
app_hash = hashlib.sha256(app_path.read_bytes()).hexdigest()
manifest_path = Path("payload/update_manifest.json")
manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
manifest["version"] = version
manifest["created_by"] = (
    "v33.03 synchronously terminates and reaps embedded FFmpeg/ffplay preview "
    "processes on clear, row removal and full application quit"
)
manifest["files"][0]["sha256"] = app_hash
manifest["files"][0]["size"] = app_path.stat().st_size
manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
print("VERIFIED v33.03 app.py sha256", app_hash)
