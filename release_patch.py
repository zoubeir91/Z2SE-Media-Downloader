from pathlib import Path
import ast
import hashlib
import json
import re
import sys

TARGET_VERSION = "32.71"


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
text, count = re.subn(r'APP_VERSION\s*=\s*"32\.70"', 'APP_VERSION = "32.71"', text, count=1)
if count != 1:
    raise RuntimeError("Could not update APP_VERSION 32.70 -> 32.71")

# v32.71: Windows-safe top navigation. 32.70 used Unicode glyphs that rendered
# as mojibake on some Windows/font configurations. Use clean text navigation
# with a compact active marker instead; this is deliberately boring/reliable.
menu_pattern = re.compile(
    r'def _make_top_menu_button\(label, menu\):\n.*?\n    return button\n',
    re.S,
)
menu_replacement = '''def _make_top_menu_button(label, menu):
    active = label == tr("Downloads")
    button = tk.Menubutton(
        menu_strip,
        text=label,
        font=("Segoe UI Semibold", 9),
        fg=(UI_ACCENT if active else UI_TOP_TEXT),
        bg=UI_TOP,
        activeforeground="#ffffff",
        activebackground=UI_TOP_SOFT,
        bd=0,
        relief="flat",
        padx=18,
        pady=12,
        cursor="hand2",
        menu=menu,
        justify="center",
    )
    button.pack(side="left", padx=2)
    if active:
        try:
            button.configure(highlightthickness=1, highlightbackground=UI_ACCENT, highlightcolor=UI_ACCENT)
        except Exception:
            pass

    def _popup_menu(event=None):
        try:
            menu.tk_popup(
                button.winfo_rootx(),
                button.winfo_rooty() + button.winfo_height(),
            )
        finally:
            try:
                menu.grab_release()
            except Exception:
                pass
        return "break"

    button.bind("<Button-1>", _popup_menu, add="+")
    return button
'''
text, count = menu_pattern.subn(lambda m: menu_replacement, text, count=1)
if count != 1:
    raise RuntimeError("Could not replace v32.70 navigation")

# v32.71: make the right-side media preview genuinely clickable. For a
# completed job we resolve its title against the download folder and open the
# newest matching media file with the Windows default player. For unfinished
# jobs the preview is intentionally disabled.
preview_anchor = 'v3270_preview.create_text(18, 16, anchor="nw", text="Z²SE  •  MEDIA", fill=UI_MUTED, font=("Segoe UI Semibold", 9))\n'
if preview_anchor not in text:
    raise RuntimeError("Preview anchor missing")
preview_extra = r'''

v3271_preview_enabled = {"path": None}


def _v3271_clean_stem(value):
    try:
        stem = Path(str(value or "")).stem.lower()
    except Exception:
        stem = str(value or "").lower()
    return re.sub(r"[^\w]+", " ", stem, flags=re.UNICODE).strip()


def _v3271_resolve_media(title):
    try:
        folder = Path(DOWNLOADS)
        if not folder.exists():
            return None
        wanted = _v3271_clean_stem(title)
        media_exts = {".mp4", ".mkv", ".webm", ".mov", ".avi", ".mp3", ".m4a", ".wav", ".flac", ".ogg", ".opus"}
        candidates = [p for p in folder.iterdir() if p.is_file() and p.suffix.lower() in media_exts]
        exact = [p for p in candidates if _v3271_clean_stem(p.name) == wanted]
        pool = exact
        if not pool and wanted:
            pool = [p for p in candidates if wanted in _v3271_clean_stem(p.name) or _v3271_clean_stem(p.name) in wanted]
        if not pool:
            return None
        return max(pool, key=lambda p: p.stat().st_mtime)
    except Exception:
        return None


def _v3271_open_preview(event=None):
    path = v3271_preview_enabled.get("path")
    if not path:
        try:
            root.bell()
        except Exception:
            pass
        return "break"
    try:
        os.startfile(str(path))
    except Exception as exc:
        try:
            messagebox.showerror("Z²SE", f"Impossible d’ouvrir le fichier.\n\n{exc}")
        except Exception:
            pass
    return "break"


v3270_preview.bind("<Button-1>", _v3271_open_preview, add="+")
'''
text = text.replace(preview_anchor, preview_anchor + preview_extra, 1)

# Update the details refresh so the preview communicates whether it can open.
status_anchor = '        v3270_detail_status.set(status)\n        low = status.lower()\n'
if status_anchor not in text:
    raise RuntimeError("Details status anchor missing")
status_extra = '''        v3270_detail_status.set(status)\n        low = status.lower()\n        is_done = any(k in low for k in ("done", "termin", "saved", "complete"))\n        media_path = _v3271_resolve_media(values[1]) if is_done else None\n        v3271_preview_enabled["path"] = media_path\n        try:\n            v3270_preview.configure(cursor=("hand2" if media_path else "arrow"))\n        except Exception:\n            pass\n'''
text = text.replace(status_anchor, status_extra, 1)

# Remove the misleading old instruction: clicking the preview now opens a
# completed file; double-clicking a row still opens the full technical sheet.
text = text.replace(
    'text="Double-cliquez sur une ligne pour ouvrir la fiche complète.",',
    'text="Cliquez sur ▶ pour ouvrir un fichier terminé. Double-cliquez sur une ligne pour la fiche complète.",',
    1,
)

text = text.replace('Clean Editor v32.70: startup draft/PART rows cleared.', 'Clean Editor v32.71: startup draft/PART rows cleared.', 1)
text = text.replace('Clean Editor v32.70 warning:', 'Clean Editor v32.71 warning:', 1)
text = text.replace('Download details v32.70 warning:', 'Download details v32.71 warning:', 1)

ast.parse(text)
app_path.write_text(text, encoding="utf-8")

manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
manifest["product"] = "Z2SE Media Downloader"
manifest["version"] = TARGET_VERSION
manifest["created_by"] = "GitHub Actions / v32.71 Windows-safe navigation and functional preview"
manifest["files"] = [
    {"path": "app.py", "sha256": sha256_file(app_path), "size": app_path.stat().st_size},
    {"path": "z2se_updater.pyw", "sha256": sha256_file(updater_path), "size": updater_path.stat().st_size},
]
manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")

print("Prepared Z2SE v32.71 navigation and preview fixes")
print("app.py", app_path.stat().st_size, sha256_file(app_path))
