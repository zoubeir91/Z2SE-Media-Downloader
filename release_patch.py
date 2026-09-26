from pathlib import Path
import ast
import hashlib
import json
import sys

version = sys.argv[1]
assert version == "33.00"
app_path = Path("payload/app.py")
text = app_path.read_text(encoding="utf-8-sig")

def replace_once(old, new):
    global text
    assert text.count(old) == 1, (old[:160], text.count(old))
    text = text.replace(old, new, 1)

replace_once('APP_VERSION = "32.99"', 'APP_VERSION = "33.00"')

old_handler = '''def _v3271_open_preview(event=None):
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
            messagebox.showerror("Z²SE", f"Impossible d’ouvrir le fichier.\\n\\n{exc}")
        except Exception:
            pass
    return "break"
'''

new_handler = '''def _v3271_open_preview(event=None):
    try:
        log("🎬 Preview click received.")
        path = str(v3271_preview_enabled.get("path") or "").strip()
        if path and os.path.isfile(path):
            log("🎬 Preview path ready: " + os.path.basename(path))
        else:
            path = ""
            selection = list(bulk_tree.selection())
            if selection:
                exact = _exact_path_for_row(selection[0])
                if exact and os.path.isfile(exact):
                    path = str(exact)
                    v3271_preview_enabled["path"] = path
                    log("🎬 Preview exact path restored: " + os.path.basename(path))
        if not path:
            log("Preview click: no valid cached or exact media path was found.")
            try:
                messagebox.showinfo("Z²SE", "Le fichier vidéo n’est pas encore disponible ou a été déplacé.")
            except Exception:
                pass
            return "break"
        log("🎬 Starting embedded FFmpeg preview.")
        if _v3296_play_inside(path):
            return "break"
        try:
            os.startfile(os.path.normpath(path))
            log("▶ External preview fallback: " + os.path.basename(path))
        except Exception as exc:
            log("External preview fallback error: " + str(exc))
            try:
                messagebox.showerror("Z²SE", f"Impossible d’ouvrir le fichier.\\n\\n{exc}")
            except Exception:
                pass
        return "break"
    except Exception as exc:
        try:
            log("Preview click error: " + repr(exc))
        except Exception:
            pass
        return "break"
'''

replace_once(old_handler, new_handler)
ast.parse(text)
app_path.write_text(text, encoding="utf-8")

app_hash = hashlib.sha256(app_path.read_bytes()).hexdigest()
manifest_path = Path("payload/update_manifest.json")
manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
manifest["version"] = version
manifest["created_by"] = (
    "v33.00 prevents preview clicks from blocking in recursive file lookup "
    "and adds complete stage-by-stage preview diagnostics"
)
manifest["files"][0]["sha256"] = app_hash
manifest["files"][0]["size"] = app_path.stat().st_size
manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
print("VERIFIED v33.00 app.py sha256", app_hash)
