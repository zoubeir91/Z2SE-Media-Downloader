from pathlib import Path
import ast
import hashlib
import json
import re
import sys

TARGET_VERSION = "32.73"


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
text, count = re.subn(r'APP_VERSION\s*=\s*"32\.72"', 'APP_VERSION = "32.73"', text, count=1)
if count != 1:
    raise RuntimeError("Could not update APP_VERSION 32.72 -> 32.73")

# Premium palette: richer navy layers plus clearer semantic accent colors.
palette = {
    '#0b1726': '#071421',
    '#122238': '#10263d',
    '#0a1a2a': '#081725',
    '#18324d': '#193a59',
    '#2b4968': '#2c557a',
    '#238df5': '#1f9cff',
    '#f1f6fc': '#f5f9ff',
    '#a4b8cf': '#a9bfd7',
    '#49d982': '#37e28a',
    '#f6f9fd': '#ffffff',
    '#a9bbcf': '#afc3da',
    '#172d47': '#173653',
    '#e4edf7': '#edf5ff',
    '#21415f': '#245780',
    '#264968': '#2a5a82',
    '#748ba4': '#7892ad',
    '#3299f7': '#27a8ff',
    '#147bdc': '#1387ec',
    '#34232f': '#3a2330',
    '#ffc1ca': '#ffc5ce',
    '#512d3d': '#5a2d3e',
    '#603247': '#6b344b',
    '#b8c9dc': '#c4d4e6',
    '#1b3551': '#1d3e60',
    '#101f32': '#0d2135',
    '#f3f7fc': '#f7fbff',
    '#19314b': '#183957',
    '#b1c4d8': '#bad0e6',
    '#112137': '#0d2237',
    '#c8d6e6': '#d5e2f0',
    '#1a314b': '#173753',
    '#20507e': '#126fbd',
    '#172f49': '#163651',
    '#14263c': '#102a42',
    '#224d77': '#1c5f91',
}
for old, new in palette.items():
    text = text.replace(old, new)

# Add richer button styles without changing engine behavior.
style_anchor = 'main = ttk.Frame(root, style="Z2SE.TFrame", padding=0)\n'
if style_anchor not in text:
    raise RuntimeError("Main-frame style anchor missing")
style_injection = r'''
try:
    _v3266_style.configure(
        "Cyan.TButton", background="#0c5f83", foreground="#ecfbff",
        font=("Segoe UI Semibold", 9), padding=(12, 8), borderwidth=0,
    )
    _v3266_style.map(
        "Cyan.TButton", background=[("active", "#0f789f"), ("pressed", "#0a516f")],
    )
    _v3266_style.configure(
        "Success.TButton", background="#146b49", foreground="#effff7",
        font=("Segoe UI Semibold", 9), padding=(12, 8), borderwidth=0,
    )
    _v3266_style.map(
        "Success.TButton", background=[("active", "#1a875d"), ("pressed", "#10583d")],
    )
    _v3266_style.configure(
        "Purple.TButton", background="#493486", foreground="#f5f1ff",
        font=("Segoe UI Semibold", 9), padding=(12, 8), borderwidth=0,
    )
    _v3266_style.map(
        "Purple.TButton", background=[("active", "#5b43a5"), ("pressed", "#3c2b70")],
    )
except Exception:
    pass

'''
text = text.replace(style_anchor, style_injection + style_anchor, 1)

# Make the status shortcuts visually meaningful instead of four similar buttons.
status_pattern = re.compile(
    r'for _txt, _mode in \(\("Tous", "all"\), \("En cours", "active"\), \("Terminés", "done"\), \("Erreurs", "error"\)\):\n.*?\n\s*\)\.pack\(side="right", padx=3\)\n',
    re.S,
)
status_replacement = r'''for _txt, _mode, _bg, _fg in (
    ("Tous", "all", "#168fff", "#ffffff"),
    ("En cours", "active", "#0f6688", "#eafaff"),
    ("Terminés", "done", "#176443", "#effff6"),
    ("Erreurs", "error", "#6b2e3e", "#fff2f5"),
):
    tk.Button(
        list_header,
        text=_txt,
        bg=_bg,
        fg=_fg,
        activebackground=_bg,
        activeforeground="#ffffff",
        font=("Segoe UI Semibold", 8),
        bd=0,
        relief="flat",
        padx=14,
        pady=8,
        cursor="hand2",
        command=lambda m=_mode: _v3270_select_status(m),
    ).pack(side="right", padx=3)
'''
text, count = status_pattern.subn(lambda m: status_replacement, text, count=1)
if count != 1:
    raise RuntimeError("Could not restyle status shortcut buttons")

# Add a premium empty state so the main area does not look unfinished.
tree_anchor = 'tree_scroll.pack(side="right", fill="y")\n'
if tree_anchor not in text:
    raise RuntimeError("Tree scroll anchor missing")
empty_state = r'''

v3273_empty = tk.Frame(tree_frame, bg="#0d2237")
v3273_empty.place(relx=0.5, rely=0.54, anchor="center")

v3273_empty_icon = tk.Canvas(
    v3273_empty, width=86, height=86, bg="#0d2237",
    highlightthickness=0, bd=0,
)
v3273_empty_icon.pack()
v3273_empty_icon.create_rectangle(25, 17, 61, 60, outline="#68bfff", width=3)
v3273_empty_icon.create_line(43, 30, 43, 58, fill="#68bfff", width=4)
v3273_empty_icon.create_line(33, 48, 43, 59, 53, 48, fill="#68bfff", width=4)
v3273_empty_icon.create_line(29, 69, 57, 69, fill="#2aa7ff", width=4)

tk.Label(
    v3273_empty,
    text="Aucun téléchargement",
    fg="#f5f9ff",
    bg="#0d2237",
    font=("Segoe UI Semibold", 14),
).pack(pady=(4, 2))

tk.Label(
    v3273_empty,
    text="Collez un lien ci-dessus puis cliquez sur TÉLÉCHARGER",
    fg="#a9bfd7",
    bg="#0d2237",
    font=("Segoe UI", 9),
).pack()

badges = tk.Frame(v3273_empty, bg="#0d2237")
badges.pack(pady=(15, 0))
for _name, _bg in (("VIDEO", "#165b92"), ("AUDIO", "#513a8f"), ("PART", "#137458"), ("HLS", "#8a5520")):
    tk.Label(
        badges, text=_name, bg=_bg, fg="#ffffff",
        font=("Segoe UI Semibold", 8), padx=10, pady=4,
    ).pack(side="left", padx=4)


def _v3273_sync_empty_state():
    try:
        if bulk_tree.get_children(""):
            v3273_empty.place_forget()
        else:
            v3273_empty.place(relx=0.5, rely=0.54, anchor="center")
    except Exception:
        pass
'''
text = text.replace(tree_anchor, tree_anchor + empty_state, 1)

# Keep the empty-state overlay in sync with downloads appearing/disappearing.
footer_items_anchor = '        items = list(bulk_tree.get_children(""))\n'
if footer_items_anchor not in text:
    raise RuntimeError("Footer item anchor missing")
text = text.replace(
    footer_items_anchor,
    footer_items_anchor + '        _v3273_sync_empty_state()\n',
    1,
)

# More premium side panel: colored accent and semantic control buttons.
details_anchor = 'details_panel.pack_propagate(False)\n'
if details_anchor not in text:
    raise RuntimeError("Details panel anchor missing")
text = text.replace(
    details_anchor,
    details_anchor + 'tk.Frame(details_panel, bg="#8b5cf6", height=3).pack(fill="x")\n',
    1,
)
text = text.replace('style="Toolbar.TButton",\n    command=lambda: globals().get("pause_selected_downloads"', 'style="Cyan.TButton",\n    command=lambda: globals().get("pause_selected_downloads"', 1)
text = text.replace('style="Toolbar.TButton",\n    command=lambda: globals().get("resume_selected_downloads"', 'style="Success.TButton",\n    command=lambda: globals().get("resume_selected_downloads"', 1)

# Strengthen the main editor card and title hierarchy.
text = text.replace('editor_accent = tk.Frame(editor_card, bg=UI_ACCENT, height=3)', 'editor_accent = tk.Frame(editor_card, bg="#1f9cff", height=4)', 1)
text = text.replace('font=("Segoe UI Semibold", 10),', 'font=("Segoe UI Semibold", 11),', 1)

text = text.replace('Clean Editor v32.72: startup draft/PART rows cleared.', 'Clean Editor v32.73: startup draft/PART rows cleared.', 1)
text = text.replace('Clean Editor v32.72 warning:', 'Clean Editor v32.73 warning:', 1)
text = text.replace('Download details v32.72 warning:', 'Download details v32.73 warning:', 1)

ast.parse(text)
app_path.write_text(text, encoding="utf-8")

manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
manifest["product"] = "Z2SE Media Downloader"
manifest["version"] = TARGET_VERSION
manifest["created_by"] = "GitHub Actions / v32.73 premium visual polish"
manifest["files"] = [
    {"path": "app.py", "sha256": sha256_file(app_path), "size": app_path.stat().st_size},
    {"path": "z2se_updater.pyw", "sha256": sha256_file(updater_path), "size": updater_path.stat().st_size},
]
manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")

print("Prepared Z2SE v32.73 premium visual polish")
print("app.py", app_path.stat().st_size, sha256_file(app_path))
