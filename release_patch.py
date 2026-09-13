from pathlib import Path
import ast
import hashlib
import json
import re
import sys

TARGET_VERSION = "32.72"


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
text, count = re.subn(r'APP_VERSION\s*=\s*"32\.71"', 'APP_VERSION = "32.72"', text, count=1)
if count != 1:
    raise RuntimeError("Could not update APP_VERSION 32.71 -> 32.72")

# Premium top navigation: icons are drawn with Tk Canvas primitives, so there
# is no dependency on emoji/Unicode icon fonts and no mojibake on Windows.
menu_pattern = re.compile(
    r'def _make_top_menu_button\(label, menu\):\n.*?\n    return button\n',
    re.S,
)
menu_replacement = r'''def _v3272_draw_nav_icon(canvas, kind, color):
    c = color
    if kind == "file":
        canvas.create_rectangle(7, 9, 25, 24, outline=c, width=2)
        canvas.create_line(7, 9, 13, 9, 15, 6, 24, 6, 25, 9, fill=c, width=2)
    elif kind == "downloads":
        canvas.create_rectangle(5, 8, 27, 23, outline=c, width=2)
        canvas.create_line(16, 5, 16, 17, fill=c, width=2)
        canvas.create_line(11, 13, 16, 18, 21, 13, fill=c, width=2)
    elif kind == "tools":
        canvas.create_oval(7, 5, 15, 13, outline=c, width=2)
        canvas.create_oval(17, 17, 25, 25, outline=c, width=2)
        canvas.create_line(13, 11, 20, 19, fill=c, width=3)
        canvas.create_line(19, 6, 25, 12, fill=c, width=2)
    elif kind == "language":
        canvas.create_oval(5, 5, 27, 27, outline=c, width=2)
        canvas.create_oval(11, 5, 21, 27, outline=c, width=1)
        canvas.create_line(5, 16, 27, 16, fill=c, width=1)
    else:
        canvas.create_oval(9, 4, 23, 18, outline=c, width=2)
        canvas.create_line(16, 18, 16, 22, fill=c, width=2)
        canvas.create_oval(15, 25, 17, 27, fill=c, outline=c)


def _make_top_menu_button(label, menu):
    key = str(label).strip().lower()
    if "télé" in key or "download" in key:
        kind = "downloads"
    elif "outil" in key or "tool" in key:
        kind = "tools"
    elif "lang" in key:
        kind = "language"
    elif "aide" in key or "help" in key:
        kind = "help"
    else:
        kind = "file"
    active = kind == "downloads"
    tile = tk.Frame(menu_strip, bg=UI_TOP, cursor="hand2", padx=7, pady=2)
    tile.pack(side="left", padx=5, fill="y")
    icon = tk.Canvas(tile, width=32, height=30, bg=UI_TOP, highlightthickness=0, bd=0, cursor="hand2")
    icon.pack(pady=(1, 0))
    _v3272_draw_nav_icon(icon, kind, UI_ACCENT if active else UI_TOP_MUTED)
    caption = tk.Label(
        tile,
        text=label,
        font=("Segoe UI Semibold", 8),
        fg=(UI_ACCENT if active else UI_TOP_TEXT),
        bg=UI_TOP,
        cursor="hand2",
    )
    caption.pack(pady=(0, 4))
    if active:
        underline = tk.Frame(tile, height=2, bg=UI_ACCENT)
        underline.pack(fill="x", padx=4)

    def _popup_menu(event=None):
        try:
            menu.tk_popup(tile.winfo_rootx(), tile.winfo_rooty() + tile.winfo_height())
        finally:
            try:
                menu.grab_release()
            except Exception:
                pass
        return "break"

    for widget in (tile, icon, caption):
        widget.bind("<Button-1>", _popup_menu, add="+")
    return tile
'''
text, count = menu_pattern.subn(lambda m: menu_replacement, text, count=1)
if count != 1:
    raise RuntimeError("Could not replace v32.71 top navigation")

# Give the premium icon navigation enough vertical breathing room while
# keeping the header compact.
text = text.replace('height=76,', 'height=88,', 1)

# Make the new-download card feel less legacy without changing its behavior.
text = text.replace(
    'text="AJOUTER DES TÉLÉCHARGEMENTS",',
    'text="NOUVEAU TÉLÉCHARGEMENT",',
    1,
)

text = text.replace('Clean Editor v32.71: startup draft/PART rows cleared.', 'Clean Editor v32.72: startup draft/PART rows cleared.', 1)
text = text.replace('Clean Editor v32.71 warning:', 'Clean Editor v32.72 warning:', 1)
text = text.replace('Download details v32.71 warning:', 'Download details v32.72 warning:', 1)

ast.parse(text)
app_path.write_text(text, encoding="utf-8")

manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
manifest["product"] = "Z2SE Media Downloader"
manifest["version"] = TARGET_VERSION
manifest["created_by"] = "GitHub Actions / v32.72 premium Canvas icon navigation"
manifest["files"] = [
    {"path": "app.py", "sha256": sha256_file(app_path), "size": app_path.stat().st_size},
    {"path": "z2se_updater.pyw", "sha256": sha256_file(updater_path), "size": updater_path.stat().st_size},
]
manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")

print("Prepared Z2SE v32.72 premium Canvas icon navigation")
print("app.py", app_path.stat().st_size, sha256_file(app_path))
