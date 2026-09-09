from pathlib import Path
import hashlib
import json
import re
import sys

TARGET_VERSION = "32.52"


def sha256_file(path):
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


version = str(sys.argv[1] if len(sys.argv) > 1 else "").strip()
if version != TARGET_VERSION:
    raise SystemExit(f"This patch prepares only v{TARGET_VERSION}; got {version!r}")

app_path = Path("payload/app.py")
updater_path = Path("payload/z2se_updater.pyw")
manifest_path = Path("payload/update_manifest.json")

for required in (app_path, updater_path, manifest_path):
    if not required.is_file():
        raise FileNotFoundError(required)

text = app_path.read_text(encoding="utf-8-sig")

# ----------------------------------------------------------------------
# V32.52 — FASTER NON-YOUTUBE START + COMPLETION ACTION DIALOG
# ----------------------------------------------------------------------
text, count = re.subn(
    r'APP_VERSION\s*=\s*"32\.51"',
    'APP_VERSION = "32.52"',
    text,
    count=1,
)
if count != 1:
    raise RuntimeError("Could not update APP_VERSION 32.51 -> 32.52")

# Track the authoritative final path for Single Download too. Historically
# register_current_job_output_path() only persisted paths for indexed queue jobs.
paths_anchor = 'job_output_paths = {}\njob_output_paths_lock = threading.Lock()\n'
paths_replacement = paths_anchor + 'single_output_path = ""\n'
if paths_anchor not in text:
    raise RuntimeError("Single output path anchor missing")
text = text.replace(paths_anchor, paths_replacement, 1)

old_register = '''def register_current_job_output_path(path):\n    index = _current_job_index()\n\n    if index is not None:\n        register_job_output_path(\n            index,\n            path,\n        )\n'''
new_register = '''def register_current_job_output_path(path):\n    global single_output_path\n\n    path = _normalize_output_path(path)\n    if not path:\n        return\n\n    index = _current_job_index()\n\n    if index is not None:\n        register_job_output_path(\n            index,\n            path,\n        )\n    elif single_running:\n        # Single downloads have no queue index, but yt-dlp still reports the\n        # exact final filepath through the same after_move hook.\n        single_output_path = path\n'''
if old_register not in text:
    raise RuntimeError("register_current_job_output_path anchor missing")
text = text.replace(old_register, new_register, 1)

single_anchor = '''def single_worker(url, quality, mode, start, end):\n    global single_running\n\n    live_slot_acquired = False\n'''
helper_and_worker = r'''def _single_url_needs_pot_provider(url):
    """PO Token is a YouTube-specific dependency; skip it for Facebook/etc."""
    try:
        host = (urlparse(str(url or "")).hostname or "").lower().strip(".")
    except Exception:
        host = ""

    return bool(
        host == "youtu.be"
        or host == "youtube.com"
        or host.endswith(".youtube.com")
        or host == "youtube-nocookie.com"
        or host.endswith(".youtube-nocookie.com")
    )


def _show_single_download_complete(path):
    """Centered IDM-style completion dialog with immediate file actions."""
    try:
        _cleanup_mini_progress_ui()
    except Exception:
        pass

    path = _normalize_output_path(path)
    file_exists = bool(path and os.path.isfile(path))
    folder = os.path.dirname(path) if path else DOWNLOADS
    if not folder or not os.path.isdir(folder):
        folder = DOWNLOADS

    dialog = tk.Toplevel(root)
    dialog.title(tr_dynamic("Download completed ✅"))
    dialog.resizable(False, False)
    dialog.configure(bg="#ffffff")

    width = 470
    height = 205
    try:
        x = max(0, (dialog.winfo_screenwidth() - width) // 2)
        y = max(0, (dialog.winfo_screenheight() - height) // 2)
        dialog.geometry(f"{width}x{height}+{x}+{y}")
    except Exception:
        dialog.geometry(f"{width}x{height}")

    body = tk.Frame(dialog, bg="#ffffff")
    body.pack(fill="both", expand=True, padx=22, pady=18)

    tk.Label(
        body,
        text="Téléchargement terminé ✅",
        font=("Segoe UI", 13, "bold"),
        fg="#172033",
        bg="#ffffff",
    ).pack(anchor="w")

    filename = os.path.basename(path) if path else ""
    tk.Label(
        body,
        text=(filename if filename else "Le téléchargement est terminé."),
        font=("Segoe UI", 9),
        fg="#596579",
        bg="#ffffff",
        anchor="w",
        justify="left",
        wraplength=420,
    ).pack(fill="x", pady=(8, 18))

    buttons = tk.Frame(body, bg="#ffffff")
    buttons.pack(fill="x", side="bottom")

    def close_dialog():
        try:
            dialog.destroy()
        except Exception:
            pass

    def open_file():
        if not file_exists:
            messagebox.showwarning(
                "Z²SE",
                "Le fichier téléchargé est introuvable.",
                parent=dialog,
            )
            return
        try:
            os.startfile(path)
            close_dialog()
        except Exception as exc:
            messagebox.showerror("Z²SE", str(exc), parent=dialog)

    def open_folder():
        try:
            os.startfile(folder)
            close_dialog()
        except Exception as exc:
            messagebox.showerror("Z²SE", str(exc), parent=dialog)

    tk.Button(
        buttons,
        text="Ouvrir le fichier",
        command=open_file,
        state=("normal" if file_exists else "disabled"),
        font=("Segoe UI", 9, "bold"),
        padx=12,
        pady=7,
    ).pack(side="left")

    tk.Button(
        buttons,
        text="Ouvrir le dossier",
        command=open_folder,
        font=("Segoe UI", 9, "bold"),
        padx=12,
        pady=7,
    ).pack(side="left", padx=(8, 0))

    tk.Button(
        buttons,
        text="Annuler",
        command=close_dialog,
        font=("Segoe UI", 9),
        padx=12,
        pady=7,
    ).pack(side="right")

    dialog.protocol("WM_DELETE_WINDOW", close_dialog)
    try:
        dialog.lift()
        dialog.attributes("-topmost", True)
        dialog.focus_force()
        dialog.after(900, lambda: dialog.attributes("-topmost", False) if dialog.winfo_exists() else None)
    except Exception:
        pass


def single_worker(url, quality, mode, start, end):
    global single_running
    global single_output_path

    live_slot_acquired = False
    completion_dialog_needed = False
    completed_output_path = ""
    single_output_path = ""
'''
if single_anchor not in text:
    raise RuntimeError("single_worker anchor missing")
text = text.replace(single_anchor, helper_and_worker, 1)

# Do not make Facebook/Instagram/TikTok wait for the YouTube PO Token provider.
old_pot = '''        ensure_pot_fast()\n\n        log("")\n        log("=" * 60)\n        log("SINGLE DOWNLOAD")\n'''
new_pot = '''        if _single_url_needs_pot_provider(url):\n            ensure_pot_fast()\n        else:\n            log("Single download: skipping YouTube PO Token startup for non-YouTube URL ⚡")\n\n        log("")\n        log("=" * 60)\n        log("SINGLE DOWNLOAD")\n'''
if old_pot not in text:
    raise RuntimeError("Single PO Token startup anchor missing")
text = text.replace(old_pot, new_pot, 1)

old_done = '''        if result == "done":\n            set_single_progress(100)\n            set_status("تم التحميل ✅")\n            tray_set_title("Ready")\n            tray_notify("التحميل سالا بنجاح ✅")\n            log("✅ Single download completed.")\n'''
new_done = '''        if result == "done":\n            set_single_progress(100)\n            set_status("تم التحميل ✅")\n            tray_set_title("Ready")\n            tray_notify("التحميل سالا بنجاح ✅")\n            completed_output_path = _normalize_output_path(single_output_path)\n            completion_dialog_needed = True\n            log("✅ Single download completed.")\n'''
if old_done not in text:
    raise RuntimeError("Single completion anchor missing")
text = text.replace(old_done, new_done, 1)

old_finally = '''        single_running = False\n        gui_call(\n            single_download_button.configure,\n            state="normal",\n        )\n\n        try:\n            with browser_queue_condition:\n'''
new_finally = '''        single_running = False\n        gui_call(\n            single_download_button.configure,\n            state="normal",\n        )\n\n        if completion_dialog_needed:\n            gui_call(\n                _show_single_download_complete,\n                completed_output_path,\n            )\n\n        try:\n            with browser_queue_condition:\n'''
if old_finally not in text:
    raise RuntimeError("Single finally anchor missing")
text = text.replace(old_finally, new_finally, 1)

app_path.write_text(text, encoding="utf-8")

manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
manifest["product"] = "Z2SE Media Downloader"
manifest["version"] = TARGET_VERSION
manifest["created_by"] = "GitHub Actions / v32.52 faster Facebook startup + completion actions"
manifest["files"] = [
    {
        "path": "app.py",
        "sha256": sha256_file(app_path),
        "size": app_path.stat().st_size,
    },
    {
        "path": "z2se_updater.pyw",
        "sha256": sha256_file(updater_path),
        "size": updater_path.stat().st_size,
    },
]
manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")

print("Prepared Z2SE v32.52 Facebook startup + completion dialog")
print("app.py", app_path.stat().st_size, sha256_file(app_path))
print("z2se_updater.pyw", updater_path.stat().st_size, sha256_file(updater_path))
