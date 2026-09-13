from pathlib import Path
import ast
import hashlib
import json
import re
import sys

TARGET_VERSION = "32.74"


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
text, count = re.subn(r'APP_VERSION\s*=\s*"32\.73"', 'APP_VERSION = "32.74"', text, count=1)
if count != 1:
    raise RuntimeError("Could not update APP_VERSION 32.73 -> 32.74")

# v32.74 — cleaner modern navigation icons.  Everything is drawn with Tk
# Canvas primitives so Windows never has to rely on emoji/icon fonts.
icon_pattern = re.compile(
    r'def _v3272_draw_nav_icon\(canvas, kind, color\):\n.*?(?=\n\ndef _make_top_menu_button)',
    re.S,
)
icon_replacement = r'''def _v3272_draw_nav_icon(canvas, kind, color):
    c = color
    soft = "#2a6f9f"
    if kind == "file":
        # modern folder
        canvas.create_polygon(6, 11, 13, 11, 16, 8, 29, 8, 31, 12, 31, 26, 6, 26,
                              outline=c, fill="", width=2, joinstyle="round")
        canvas.create_line(7, 14, 30, 14, fill=soft, width=1)
    elif kind == "downloads":
        # download arrow into a tray
        canvas.create_line(19, 5, 19, 20, fill=c, width=3, capstyle="round")
        canvas.create_line(13, 14, 19, 20, 25, 14, fill=c, width=3,
                           capstyle="round", joinstyle="round")
        canvas.create_line(8, 25, 30, 25, fill=c, width=2, capstyle="round")
        canvas.create_line(8, 25, 8, 21, fill=soft, width=2)
        canvas.create_line(30, 25, 30, 21, fill=soft, width=2)
    elif kind == "tools":
        # contemporary sliders/settings symbol
        canvas.create_line(7, 9, 31, 9, fill=c, width=2, capstyle="round")
        canvas.create_line(7, 17, 31, 17, fill=c, width=2, capstyle="round")
        canvas.create_line(7, 25, 31, 25, fill=c, width=2, capstyle="round")
        canvas.create_oval(12, 6, 18, 12, outline=c, fill="#102a42", width=2)
        canvas.create_oval(22, 14, 28, 20, outline=c, fill="#102a42", width=2)
        canvas.create_oval(10, 22, 16, 28, outline=c, fill="#102a42", width=2)
    elif kind == "language":
        # globe
        canvas.create_oval(7, 5, 31, 29, outline=c, width=2)
        canvas.create_arc(12, 5, 26, 29, start=90, extent=180, style="arc", outline=c, width=1)
        canvas.create_arc(12, 5, 26, 29, start=270, extent=180, style="arc", outline=c, width=1)
        canvas.create_line(8, 17, 30, 17, fill=c, width=1)
    else:
        # help/info — intentionally simple and crisp
        canvas.create_oval(8, 5, 30, 27, outline=c, width=2)
        canvas.create_arc(13, 9, 25, 20, start=0, extent=205, style="arc", outline=c, width=2)
        canvas.create_line(19, 18, 19, 21, fill=c, width=2, capstyle="round")
        canvas.create_oval(18, 24, 20, 26, fill=c, outline=c)
'''
text, count = icon_pattern.subn(lambda m: icon_replacement, text, count=1)
if count != 1:
    raise RuntimeError("Could not replace Canvas navigation icons")

# Refine the tile itself: cyan active state, subtle blue inactive icons, a
# cleaner 38px icon canvas and no red accent anywhere.
text, count = re.subn(
    r'    active = kind == "downloads"\n    tile = tk\.Frame\(menu_strip, bg=UI_TOP, cursor="hand2", padx=7, pady=2\)\n    tile\.pack\(side="left", padx=5, fill="y"\)\n    icon = tk\.Canvas\(tile, width=32, height=30, bg=UI_TOP, highlightthickness=0, bd=0, cursor="hand2"\)\n    icon\.pack\(pady=\(1, 0\)\)\n    _v3272_draw_nav_icon\(icon, kind, UI_ACCENT if active else UI_TOP_MUTED\)',
    '    active = kind == "downloads"\n    tile_bg = "#0d2b44" if active else UI_TOP\n    tile = tk.Frame(menu_strip, bg=tile_bg, cursor="hand2", padx=10, pady=3)\n    tile.pack(side="left", padx=4, fill="y")\n    icon = tk.Canvas(tile, width=38, height=34, bg=tile_bg, highlightthickness=0, bd=0, cursor="hand2")\n    icon.pack(pady=(1, 0))\n    _v3272_draw_nav_icon(icon, kind, "#41c7ff" if active else "#8bb8d8")',
    text,
    count=1,
)
if count != 1:
    raise RuntimeError("Could not modernize navigation tile")

text = text.replace(
    'font=("Segoe UI Semibold", 8),\n        fg=(UI_ACCENT if active else UI_TOP_TEXT),\n        bg=UI_TOP,',
    'font=("Segoe UI Semibold", 9),\n        fg=("#6ad8ff" if active else UI_TOP_TEXT),\n        bg=tile_bg,',
    1,
)
text = text.replace(
    'underline = tk.Frame(tile, height=2, bg=UI_ACCENT)',
    'underline = tk.Frame(tile, height=3, bg="#35bdff")',
    1,
)

# v32.74 — make the right-side preview use Z2SE's authoritative row/file
# mapping first.  Title matching remains only as a fallback for old history.
old_media_line = '        media_path = _v3271_resolve_media(values[1]) if is_done else None\n'
new_media_block = '''        media_path = None\n        if is_done:\n            try:\n                media_path = _find_download_file_for_row(selection[0])\n            except Exception:\n                media_path = None\n            if not media_path:\n                media_path = _v3271_resolve_media(values[1])\n'''
if old_media_line not in text:
    raise RuntimeError("Preview refresh anchor missing")
text = text.replace(old_media_line, new_media_block, 1)

open_pattern = re.compile(
    r'def _v3271_open_preview\(event=None\):\n.*?\n    return "break"\n\n\nv3270_preview\.bind',
    re.S,
)
open_replacement = r'''def _v3271_open_preview(event=None):
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
            messagebox.showerror("Z²SE", f"Impossible d’ouvrir le fichier.\n\n{exc}")
        except Exception:
            pass
    return "break"


v3270_preview.bind'''
text, count = open_pattern.subn(lambda m: open_replacement, text, count=1)
if count != 1:
    raise RuntimeError("Could not harden preview click handler")

# Keep visible version-specific diagnostics consistent.
text = text.replace('Clean Editor v32.73: startup draft/PART rows cleared.', 'Clean Editor v32.74: startup draft/PART rows cleared.', 1)
text = text.replace('Clean Editor v32.73 warning:', 'Clean Editor v32.74 warning:', 1)
text = text.replace('Download details v32.73 warning:', 'Download details v32.74 warning:', 1)

ast.parse(text)
app_path.write_text(text, encoding="utf-8")

manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
manifest["product"] = "Z2SE Media Downloader"
manifest["version"] = TARGET_VERSION
manifest["created_by"] = "GitHub Actions / v32.74 modern navigation + reliable completed-media preview"
manifest["files"] = [
    {"path": "app.py", "sha256": sha256_file(app_path), "size": app_path.stat().st_size},
    {"path": "z2se_updater.pyw", "sha256": sha256_file(updater_path), "size": updater_path.stat().st_size},
]
manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")

print("Prepared Z2SE v32.74 modern navigation and reliable preview")
print("app.py", app_path.stat().st_size, sha256_file(app_path))
