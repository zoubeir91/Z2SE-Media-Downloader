from pathlib import Path
import ast
import hashlib
import json
import re
import sys

TARGET_VERSION = "32.75"


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
text, count = re.subn(r'APP_VERSION\s*=\s*"32\.74"', 'APP_VERSION = "32.75"', text, count=1)
if count != 1:
    raise RuntimeError("Could not update APP_VERSION 32.74 -> 32.75")

# v32.75: premium large navigation matching the approved reference much more
# closely: large luminous icons, generous spacing, active rounded-looking tile
# treatment and a strong cyan underline. No red accent.
icon_pattern = re.compile(
    r'def _v3272_draw_nav_icon\(canvas, kind, color\):\n.*?(?=\n\ndef _make_top_menu_button)',
    re.S,
)
icon_replacement = r'''def _v3272_draw_nav_icon(canvas, kind, color):
    c = color
    glow = "#075c87"
    hi = "#a9eaff"
    if kind == "file":
        canvas.create_polygon(8, 23, 19, 23, 23, 17, 49, 17, 54, 23, 54, 45, 8, 45,
                              fill="#148fc9", outline=hi, width=2, joinstyle="round")
        canvas.create_polygon(8, 27, 54, 27, 48, 49, 12, 49,
                              fill="#18baf2", outline=c, width=2, joinstyle="round")
    elif kind == "downloads":
        canvas.create_line(31, 10, 31, 37, fill=glow, width=8, capstyle="round")
        canvas.create_line(31, 10, 31, 37, fill=c, width=5, capstyle="round")
        canvas.create_line(21, 28, 31, 39, 42, 28, fill=c, width=5,
                           capstyle="round", joinstyle="round")
        canvas.create_line(13, 46, 13, 52, 49, 52, 49, 46, fill=c, width=5,
                           capstyle="round", joinstyle="round")
    elif kind == "tools":
        # crossed wrench/screwdriver silhouette
        canvas.create_line(14, 13, 48, 48, fill="#8edcff", width=8, capstyle="round")
        canvas.create_line(48, 13, 15, 48, fill="#e8f7ff", width=7, capstyle="round")
        canvas.create_oval(8, 8, 23, 23, outline=c, width=4)
        canvas.create_oval(42, 42, 54, 54, outline="#9fe6ff", width=4)
    elif kind == "language":
        canvas.create_oval(8, 8, 54, 54, outline=hi, width=4)
        canvas.create_oval(19, 8, 43, 54, outline="#8ddfff", width=3)
        canvas.create_line(9, 31, 53, 31, fill="#8ddfff", width=3)
        canvas.create_arc(10, 17, 52, 45, start=0, extent=180, style="arc", outline="#8ddfff", width=2)
        canvas.create_arc(10, 17, 52, 45, start=180, extent=180, style="arc", outline="#8ddfff", width=2)
    else:
        canvas.create_oval(9, 8, 53, 52, outline=c, width=4)
        canvas.create_arc(20, 16, 43, 37, start=0, extent=215, style="arc", outline=hi, width=4)
        canvas.create_line(31, 34, 31, 39, fill=hi, width=4, capstyle="round")
        canvas.create_oval(29, 44, 33, 48, fill=hi, outline=hi)
'''
text, count = icon_pattern.subn(lambda m: icon_replacement, text, count=1)
if count != 1:
    raise RuntimeError("Could not replace v32.74 navigation icons")

# Enlarge and restyle each navigation tile.
tile_pattern = re.compile(
    r'    active = kind == "downloads"\n    tile_bg = .*?_v3272_draw_nav_icon\(icon, kind, .*?\)\n',
    re.S,
)
tile_replacement = '''    active = kind == "downloads"\n    tile_bg = "#0a3150" if active else UI_TOP\n    tile = tk.Frame(\n        menu_strip, bg=tile_bg, cursor="hand2", padx=16, pady=5,\n        highlightthickness=(1 if active else 0),\n        highlightbackground=("#08bdf8" if active else UI_TOP),\n    )\n    tile.pack(side="left", padx=7, pady=4, fill="y")\n    icon = tk.Canvas(tile, width=62, height=58, bg=tile_bg, highlightthickness=0, bd=0, cursor="hand2")\n    icon.pack(pady=(0, 0))\n    _v3272_draw_nav_icon(icon, kind, "#12cfff" if active else "#8bdcff")\n'''
text, count = tile_pattern.subn(lambda m: tile_replacement, text, count=1)
if count != 1:
    raise RuntimeError("Could not enlarge navigation tiles")

text = text.replace(
    'font=("Segoe UI Semibold", 9),\n        fg=("#6ad8ff" if active else UI_TOP_TEXT),\n        bg=tile_bg,',
    'font=("Segoe UI Semibold", 11),\n        fg=("#16d5ff" if active else "#e8f4fb"),\n        bg=tile_bg,',
    1,
)
text = text.replace(
    'underline = tk.Frame(tile, height=3, bg="#35bdff")',
    'underline = tk.Frame(tile, height=4, bg="#08c9ff")',
    1,
)
text = text.replace('height=88,', 'height=118,', 1)

# Make the completed-media preview clearly interactive, including hover feedback.
preview_bind = 'v3270_preview.bind("<Button-1>", _v3271_open_preview, add="+")\n'
if preview_bind not in text:
    raise RuntimeError("Preview click binding missing")
preview_hover = r'''
def _v3275_preview_enter(event=None):
    try:
        if v3271_preview_enabled.get("path"):
            v3270_preview.configure(cursor="hand2", highlightthickness=1, highlightbackground="#13cfff")
    except Exception:
        pass


def _v3275_preview_leave(event=None):
    try:
        v3270_preview.configure(highlightthickness=0)
    except Exception:
        pass


v3270_preview.bind("<Enter>", _v3275_preview_enter, add="+")
v3270_preview.bind("<Leave>", _v3275_preview_leave, add="+")
'''
text = text.replace(preview_bind, preview_bind + preview_hover, 1)

# Fix the clipped/misleading instruction in the narrow details pane.
text = text.replace(
    'text="Cliquez sur ▶ pour ouvrir un fichier terminé. Double-cliquez sur une ligne pour la fiche complète.",',
    'text="▶ Cliquez sur l’aperçu pour lire le fichier terminé.\nDouble-cliquez sur une ligne pour les détails.",',
    1,
)

text = text.replace('Clean Editor v32.74: startup draft/PART rows cleared.', 'Clean Editor v32.75: startup draft/PART rows cleared.', 1)
text = text.replace('Clean Editor v32.74 warning:', 'Clean Editor v32.75 warning:', 1)
text = text.replace('Download details v32.74 warning:', 'Download details v32.75 warning:', 1)

ast.parse(text)
app_path.write_text(text, encoding="utf-8")

manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
manifest["product"] = "Z2SE Media Downloader"
manifest["version"] = TARGET_VERSION
manifest["created_by"] = "GitHub Actions / v32.75 premium reference navigation + preview polish"
manifest["files"] = [
    {"path": "app.py", "sha256": sha256_file(app_path), "size": app_path.stat().st_size},
    {"path": "z2se_updater.pyw", "sha256": sha256_file(updater_path), "size": updater_path.stat().st_size},
]
manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")

print("Prepared Z2SE v32.75 premium reference navigation and preview polish")
print("app.py", app_path.stat().st_size, sha256_file(app_path))
