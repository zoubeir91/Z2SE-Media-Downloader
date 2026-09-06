from pathlib import Path
import hashlib
import json
import sys


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def must_replace(text: str, old: str, new: str, label: str, count: int = 1) -> str:
    if old not in text:
        raise SystemExit(f"Patch marker not found: {label}")
    return text.replace(old, new, count)


version = sys.argv[1].strip()
if version != "32.41":
    raise SystemExit(f"This patch is for 32.41, got {version}")

payload = Path("payload")
app_path = payload / "app.py"
updater_path = payload / "z2se_updater.pyw"
text = app_path.read_text(encoding="utf-8")

# ------------------------------------------------------------
# V32.41 — PRO DESIGN PASS 1
# Keep all downloader logic intact; modernize only the main desktop UI.
# ------------------------------------------------------------
text = must_replace(text, 'APP_VERSION = "32.40"', 'APP_VERSION = "32.41"', "version")
text = must_replace(
    text,
    'root.geometry("1200x840")\nroot.minsize(950, 700)',
    'root.geometry("1280x860")\nroot.minsize(1020, 720)',
    "window geometry",
)

old_palette = '''UI_BG = "#f4f6f9"\nUI_PANEL = "#ffffff"\nUI_BORDER = "#d9dee7"\nUI_TEXT = "#172033"\nUI_MUTED = "#6b7485"\nUI_ACCENT = "#1467d8"\nUI_ACCENT_DARK = "#0f55b5"\nUI_SIDEBAR = "#edf1f6"'''
new_palette = '''# V32.41 — PRO DESIGN SYSTEM\n# Windows 11 / modern download-manager inspired visual language.\nUI_BG = "#f3f6fb"\nUI_PANEL = "#ffffff"\nUI_PANEL_SOFT = "#f8fafc"\nUI_BORDER = "#dfe5ee"\nUI_BORDER_STRONG = "#cfd8e6"\nUI_TEXT = "#101828"\nUI_MUTED = "#667085"\nUI_ACCENT = "#2563eb"\nUI_ACCENT_DARK = "#1d4ed8"\nUI_ACCENT_SOFT = "#eaf2ff"\nUI_SUCCESS = "#12b76a"\nUI_DANGER = "#d92d20"\nUI_WARNING = "#dc8a00"\nUI_TOP = "#0f172a"\nUI_TOP_SOFT = "#1e293b"\nUI_TOP_TEXT = "#f8fafc"\nUI_TOP_MUTED = "#aebbd0"\nUI_SIDEBAR = "#edf1f6"'''
text = must_replace(text, old_palette, new_palette, "palette")

style_start = text.find('style.configure(\n    "Toolbar.TButton",')
style_end = text.find('\n# Z²SE Windows/app icon', style_start)
if style_start < 0 or style_end < 0:
    raise SystemExit("Patch marker not found: style block")
style_block = '''style.configure(\n    "Toolbar.TButton",\n    font=("Segoe UI", 9),\n    padding=(12, 8),\n    foreground=UI_TEXT,\n    background=UI_PANEL_SOFT,\n    bordercolor=UI_BORDER_STRONG,\n    relief="flat",\n)\nstyle.map(\n    "Toolbar.TButton",\n    background=[("active", "#eef4ff"), ("pressed", UI_ACCENT_SOFT)],\n    foreground=[("disabled", "#98a2b3"), ("active", UI_TEXT)],\n)\nstyle.configure(\n    "Primary.TButton",\n    font=("Segoe UI Semibold", 9),\n    padding=(16, 9),\n    foreground="#ffffff",\n    background=UI_ACCENT,\n    bordercolor=UI_ACCENT,\n    relief="flat",\n)\nstyle.map(\n    "Primary.TButton",\n    background=[("active", UI_ACCENT_DARK), ("pressed", "#1e40af")],\n    foreground=[("disabled", "#dbe7ff"), ("active", "#ffffff")],\n)\nstyle.configure(\n    "Danger.TButton",\n    font=("Segoe UI", 9),\n    padding=(12, 8),\n    foreground="#b42318",\n    background="#fff5f4",\n    bordercolor="#fecdca",\n    relief="flat",\n)\nstyle.map(\n    "Danger.TButton",\n    background=[("active", "#fee4e2"), ("pressed", "#fecdca")],\n    foreground=[("disabled", "#b8bfc9"), ("active", "#912018")],\n)\nstyle.configure(\n    "Ghost.TButton",\n    font=("Segoe UI", 8),\n    padding=(9, 5),\n    foreground="#344054",\n    background=UI_PANEL,\n    bordercolor=UI_BORDER,\n    relief="flat",\n)\nstyle.map(\n    "Ghost.TButton",\n    background=[("active", UI_PANEL_SOFT), ("pressed", UI_ACCENT_SOFT)],\n)\nstyle.configure(\n    "Remove.TButton",\n    font=("Segoe UI", 9),\n    padding=(5, 4),\n    foreground="#98a2b3",\n    background=UI_PANEL,\n    bordercolor=UI_PANEL,\n    relief="flat",\n)\nstyle.map(\n    "Remove.TButton",\n    background=[("active", "#fff1f0")],\n    foreground=[("active", UI_DANGER)],\n)\nstyle.configure(\n    "Panel.TLabel",\n    background=UI_PANEL,\n    foreground=UI_TEXT,\n    font=("Segoe UI", 9),\n)\nstyle.configure(\n    "Field.TEntry",\n    font=("Segoe UI", 9),\n    padding=(9, 7),\n    fieldbackground="#ffffff",\n    foreground=UI_TEXT,\n    bordercolor=UI_BORDER_STRONG,\n    lightcolor=UI_BORDER_STRONG,\n    darkcolor=UI_BORDER_STRONG,\n    insertcolor=UI_TEXT,\n)\nstyle.map(\n    "Field.TEntry",\n    bordercolor=[("focus", UI_ACCENT)],\n    lightcolor=[("focus", UI_ACCENT)],\n    darkcolor=[("focus", UI_ACCENT)],\n)\nstyle.configure(\n    "Field.TCombobox",\n    font=("Segoe UI", 9),\n    padding=(7, 5),\n    fieldbackground="#ffffff",\n    foreground=UI_TEXT,\n    background="#ffffff",\n    bordercolor=UI_BORDER_STRONG,\n    arrowcolor="#475467",\n)\nstyle.map(\n    "Field.TCombobox",\n    bordercolor=[("focus", UI_ACCENT)],\n    fieldbackground=[("readonly", "#ffffff")],\n    foreground=[("readonly", UI_TEXT)],\n)\nstyle.configure(\n    "Field.TSpinbox",\n    font=("Segoe UI", 9),\n    padding=(7, 5),\n    fieldbackground="#ffffff",\n    foreground=UI_TEXT,\n    bordercolor=UI_BORDER_STRONG,\n    arrowcolor="#475467",\n)\nstyle.configure(\n    "Z2SE.Treeview",\n    rowheight=33,\n    font=("Segoe UI", 9),\n    background="#ffffff",\n    fieldbackground="#ffffff",\n    foreground=UI_TEXT,\n    bordercolor=UI_BORDER,\n    relief="flat",\n)\nstyle.configure(\n    "Z2SE.Treeview.Heading",\n    font=("Segoe UI Semibold", 9),\n    background="#f4f7fb",\n    foreground="#344054",\n    relief="flat",\n    padding=(8, 9),\n    bordercolor=UI_BORDER,\n)\nstyle.map(\n    "Z2SE.Treeview",\n    background=[("selected", UI_ACCENT_SOFT)],\n    foreground=[("selected", "#123a72")],\n)\nstyle.map(\n    "Z2SE.Treeview.Heading",\n    background=[("active", "#edf3fb")],\n)\nstyle.configure(\n    "Z2SE.Horizontal.TProgressbar",\n    troughcolor="#e9eef5",\n    background=UI_ACCENT,\n    lightcolor=UI_ACCENT,\n    darkcolor=UI_ACCENT,\n    bordercolor="#e9eef5",\n    thickness=7,\n)\nstyle.configure(\n    "Z2SE.Vertical.TScrollbar",\n    troughcolor=UI_PANEL,\n    background="#c8d2df",\n    bordercolor=UI_PANEL,\n    arrowcolor="#667085",\n)\n'''
text = text[:style_start] + style_block + text[style_end:]

text = text.replace('# MAIN UI — Z²SE V24', '# MAIN UI — Z²SE V32.41 PRO DESIGN', 1)
text = must_replace(
    text,
    '''top_brand = tk.Frame(\n    main,\n    bg=UI_PANEL,\n    height=54,\n    highlightthickness=1,\n    highlightbackground=UI_BORDER,\n)''',
    '''top_brand = tk.Frame(\n    main,\n    bg=UI_TOP,\n    height=66,\n    highlightthickness=0,\n)''',
    "top brand",
)
text = must_replace(text, 'brand_left = tk.Frame(top_brand, bg=UI_PANEL)', 'brand_left = tk.Frame(top_brand, bg=UI_TOP)', "brand left")
text = must_replace(text, 'brand_left.pack(side="left", fill="y", padx=(14, 8))', 'brand_left.pack(side="left", fill="y", padx=(18, 10))', "brand padding")
text = must_replace(
    text,
    '''            bg=UI_PANEL,\n            bd=0,\n        ).pack(side="left", pady=8)''',
    '''            bg=UI_TOP,\n            bd=0,\n        ).pack(side="left", pady=13)''',
    "brand icon",
)
text = must_replace(text, 'brand_text = tk.Frame(brand_left, bg=UI_PANEL)', 'brand_text = tk.Frame(brand_left, bg=UI_TOP)', "brand text frame")
text = must_replace(text, 'brand_text.pack(side="left", padx=(9, 0), pady=6)', 'brand_text.pack(side="left", padx=(10, 0), pady=9)', "brand text padding")
text = must_replace(
    text,
    '''    font=("Segoe UI", 15, "bold"),\n    fg=UI_TEXT,\n    bg=UI_PANEL,''',
    '''    font=("Segoe UI Semibold", 16),\n    fg=UI_TOP_TEXT,\n    bg=UI_TOP,''',
    "brand title",
)
text = must_replace(
    text,
    '''    font=("Segoe UI", 7, "bold"),\n    fg=UI_MUTED,\n    bg=UI_PANEL,''',
    '''    font=("Segoe UI Semibold", 7),\n    fg=UI_TOP_MUTED,\n    bg=UI_TOP,''',
    "brand subtitle",
)
text = must_replace(text, 'menu_strip = tk.Frame(top_brand, bg=UI_PANEL)', 'menu_strip = tk.Frame(top_brand, bg=UI_TOP)', "menu strip")
text = must_replace(text, 'menu_strip.pack(side="left", padx=(24, 0))', 'menu_strip.pack(side="left", padx=(26, 0))', "menu strip padding")
text = must_replace(
    text,
    '''        font=("Segoe UI", 9),\n        fg="#3d4655",\n        bg=UI_PANEL,\n        activeforeground="#10294a",\n        activebackground="#eef3f9",\n        bd=0,\n        relief="flat",\n        padx=8,\n        pady=17,''',
    '''        font=("Segoe UI", 9),\n        fg="#d8e1ef",\n        bg=UI_TOP,\n        activeforeground="#ffffff",\n        activebackground=UI_TOP_SOFT,\n        bd=0,\n        relief="flat",\n        padx=10,\n        pady=23,''',
    "menu buttons",
)
text = must_replace(
    text,
    '''engine_badge = tk.Label(\n    top_brand,\n    text=tr("●  ENGINE READY"),\n    font=("Segoe UI", 8, "bold"),\n    fg="#16854a",\n    bg=UI_PANEL,\n)\nengine_badge.pack(side="right", padx=(8, 14))''',
    '''engine_badge = tk.Label(\n    top_brand,\n    text=tr("●  ENGINE READY"),\n    font=("Segoe UI Semibold", 8),\n    fg="#6ee7a7",\n    bg=UI_TOP_SOFT,\n    padx=10,\n    pady=6,\n)\nengine_badge.pack(side="right", padx=(8, 18))\n\nversion_badge = tk.Label(\n    top_brand,\n    text=f"v{APP_VERSION}",\n    font=("Segoe UI Semibold", 8),\n    fg="#b8c7dc",\n    bg=UI_TOP,\n)\nversion_badge.pack(side="right", padx=(4, 4))''',
    "engine badge",
)
text = must_replace(
    text,
    '''toolbar = tk.Frame(\n    main,\n    bg="#ffffff",\n    height=64,\n    highlightthickness=1,\n    highlightbackground=UI_BORDER,\n)\ntoolbar.pack(fill="x", pady=(1, 0))\ntoolbar.pack_propagate(False)\n\ntoolbar_inner = ttk.Frame(toolbar, style="Panel.TFrame")\ntoolbar_inner.pack(fill="both", expand=True, padx=12, pady=10)''',
    '''toolbar = tk.Frame(\n    main,\n    bg=UI_BG,\n    height=76,\n    highlightthickness=0,\n)\ntoolbar.pack(fill="x")\ntoolbar.pack_propagate(False)\n\ntoolbar_inner = tk.Frame(\n    toolbar,\n    bg=UI_PANEL,\n    highlightthickness=1,\n    highlightbackground=UI_BORDER,\n)\ntoolbar_inner.pack(fill="both", expand=True, padx=14, pady=(10, 6))''',
    "toolbar card",
)
text = must_replace(text, 'workspace.pack(fill="both", expand=True, padx=10, pady=10)', 'workspace.pack(fill="both", expand=True, padx=14, pady=(8, 14))', "workspace padding")
text = must_replace(
    text,
    '''editor_card.pack(fill="x", pady=(0, 9))\n\neditor_title = tk.Frame(editor_card, bg=UI_PANEL)''',
    '''editor_card.pack(fill="x", pady=(0, 12))\n\neditor_accent = tk.Frame(editor_card, bg=UI_ACCENT, height=3)\neditor_accent.pack(fill="x")\n\neditor_title = tk.Frame(editor_card, bg=UI_PANEL)''',
    "editor accent",
)
text = must_replace(text, 'editor_title.pack(fill="x", padx=12, pady=(10, 5))', 'editor_title.pack(fill="x", padx=14, pady=(12, 7))', "editor title padding")
text = must_replace(
    text,
    '''    font=("Segoe UI", 9, "bold"),\n    fg=UI_TEXT,\n    bg=UI_PANEL,\n).pack(side="left")\n\ntk.Label(\n    editor_title,''',
    '''    font=("Segoe UI Semibold", 10),\n    fg=UI_TEXT,\n    bg=UI_PANEL,\n).pack(side="left")\n\ntk.Label(\n    editor_title,''',
    "editor title font",
)

text = must_replace(text, 'row_frame = ttk.Frame(bulk_rows_frame)', 'row_frame = ttk.Frame(bulk_rows_frame, style="Panel.TFrame")', "row frame")
text = must_replace(
    text,
    '''        width=3,\n        anchor="center",\n    ).grid(row=0, column=0, padx=(2, 4))''',
    '''        width=3,\n        anchor="center",\n        style="Panel.TLabel",\n    ).grid(row=0, column=0, padx=(2, 4))''',
    "row number label",
)
text = must_replace(
    text,
    '''    url_entry = ttk.Entry(\n        row_frame,\n        textvariable=url_var,\n    )''',
    '''    url_entry = ttk.Entry(\n        row_frame,\n        textvariable=url_var,\n        style="Field.TEntry",\n    )''',
    "url field",
)
text = must_replace(
    text,
    '''    start_entry = ttk.Entry(\n        row_frame,\n        textvariable=start_var,\n        width=11,\n    )''',
    '''    start_entry = ttk.Entry(\n        row_frame,\n        textvariable=start_var,\n        width=11,\n        style="Field.TEntry",\n    )''',
    "start field",
)
text = must_replace(
    text,
    '''    end_entry = ttk.Entry(\n        row_frame,\n        textvariable=end_var,\n        width=11,\n    )''',
    '''    end_entry = ttk.Entry(\n        row_frame,\n        textvariable=end_var,\n        width=11,\n        style="Field.TEntry",\n    )''',
    "end field",
)
text = must_replace(
    text,
    '''        width=8,\n        anchor="center",\n    ).grid(row=0, column=4, padx=5)''',
    '''        width=8,\n        anchor="center",\n        style="Panel.TLabel",\n    ).grid(row=0, column=4, padx=5)''',
    "mode label",
)
text = must_replace(
    text,
    '''        state="readonly",\n        width=7,\n    )''',
    '''        state="readonly",\n        width=7,\n        style="Field.TCombobox",\n    )''',
    "row format field",
)
text = must_replace(
    text,
    '''        text="✕",\n        width=3,\n        command=lambda r=row: remove_bulk_row(r),\n    )''',
    '''        text="✕",\n        width=3,\n        command=lambda r=row: remove_bulk_row(r),\n        style="Remove.TButton",\n    )''',
    "remove row button",
)
text = must_replace(
    text,
    '''ttk.Label(\n    editor_footer,\n    text=tr("Quality")\n).pack(side="left", padx=(18, 4))''',
    '''ttk.Label(\n    editor_footer,\n    text=tr("Quality"),\n    style="Panel.TLabel",\n).pack(side="left", padx=(18, 5))''',
    "quality label",
)
text = must_replace(
    text,
    '''    state="readonly",\n    width=8,\n)''',
    '''    state="readonly",\n    width=8,\n    style="Field.TCombobox",\n)''',
    "quality box",
)
text = must_replace(
    text,
    '''ttk.Label(\n    editor_footer,\n    text=tr("Parallel")\n).pack(side="left", padx=(12, 4))''',
    '''ttk.Label(\n    editor_footer,\n    text=tr("Parallel"),\n    style="Panel.TLabel",\n).pack(side="left", padx=(14, 5))''',
    "parallel label",
)
text = must_replace(
    text,
    '''    textvariable=bulk_workers_var,\n    width=4,\n)''',
    '''    textvariable=bulk_workers_var,\n    width=4,\n    style="Field.TSpinbox",\n)''',
    "parallel spinbox",
)

list_idx = text.find('list_header = tk.Frame(list_card, bg=UI_PANEL)')
font_idx = text.find('font=("Segoe UI", 9, "bold")', list_idx)
if list_idx < 0 or font_idx < 0:
    raise SystemExit("Patch marker not found: list header font")
text = text[:font_idx] + text[font_idx:].replace('font=("Segoe UI", 9, "bold")', 'font=("Segoe UI Semibold", 10)', 1)

text = must_replace(
    text,
    '''tk.Button(\n    list_header,\n    text=tr("Deselect"),\n    command=lambda: deselect_all_download_rows(),\n    font=("Segoe UI", 7),\n    bg="#ffffff",\n    fg="#4f5d73",\n    activebackground="#eef2f7",\n    relief="solid",\n    bd=1,\n    padx=7,\n    pady=2,\n    cursor="hand2",\n).pack(side="right", padx=(5, 0))\n\ntk.Button(\n    list_header,\n    text=tr("Select All"),\n    command=lambda: select_all_download_rows(),\n    font=("Segoe UI", 7, "bold"),\n    bg="#eef2f7",\n    fg="#17365d",\n    activebackground="#dfe7f1",\n    relief="solid",\n    bd=1,\n    padx=7,\n    pady=2,\n    cursor="hand2",\n).pack(side="right", padx=(8, 0))''',
    '''ttk.Button(\n    list_header,\n    text=tr("Deselect"),\n    command=lambda: deselect_all_download_rows(),\n    style="Ghost.TButton",\n).pack(side="right", padx=(5, 0))\n\nttk.Button(\n    list_header,\n    text=tr("Select All"),\n    command=lambda: select_all_download_rows(),\n    style="Ghost.TButton",\n).pack(side="right", padx=(8, 0))''',
    "list selection buttons",
)
text = must_replace(
    text,
    '''bulk_editor_scroll = ttk.Scrollbar(\n    bulk_editor_outer,\n    orient="vertical",\n    command=bulk_editor_canvas.yview,\n)''',
    '''bulk_editor_scroll = ttk.Scrollbar(\n    bulk_editor_outer,\n    orient="vertical",\n    command=bulk_editor_canvas.yview,\n    style="Z2SE.Vertical.TScrollbar",\n)''',
    "editor scrollbar",
)
text = must_replace(
    text,
    '''tree_scroll = ttk.Scrollbar(\n    tree_frame,\n    orient="vertical",\n    command=bulk_tree.yview,\n)''',
    '''tree_scroll = ttk.Scrollbar(\n    tree_frame,\n    orient="vertical",\n    command=bulk_tree.yview,\n    style="Z2SE.Vertical.TScrollbar",\n)''',
    "tree scrollbar",
)
text = must_replace(text, 'list_header.pack(fill="x", padx=12, pady=(9, 5))', 'list_header.pack(fill="x", padx=14, pady=(12, 8))', "list header spacing")
text = must_replace(text, 'bottom_bar = tk.Frame(list_card, bg="#f8fafc")', 'bottom_bar = tk.Frame(list_card, bg=UI_PANEL)', "bottom bar")
text = must_replace(text, 'bottom_status = tk.Frame(bottom_bar, bg="#f8fafc")', 'bottom_status = tk.Frame(bottom_bar, bg=UI_PANEL)', "bottom status")
text = must_replace(text, 'fg="#465064",\n    bg="#f8fafc"', 'fg=UI_MUTED,\n    bg=UI_PANEL', "bottom status text")
for _ in range(3):
    text = must_replace(text, 'fg="#16854a",\n    bg="#f8fafc"', 'fg=UI_SUCCESS,\n    bg=UI_PANEL', "bottom green status")
text = must_replace(text, 'bg="#fbfcfe",\n    fg="#273246"', 'bg="#0b1220",\n    fg="#d7e2f0"', "log colors")
text = text.replace(
    'Z²SE V{APP_VERSION} MANUAL UPDATE MENU starting system checks...',
    'Z²SE V{APP_VERSION} PRO DESIGN starting system checks...',
    1,
)

app_path.write_text(text, encoding="utf-8")

files = []
for rel in ("app.py", "z2se_updater.pyw"):
    p = payload / rel
    if not p.is_file():
        raise SystemExit(f"Missing payload file: {rel}")
    files.append({
        "path": rel,
        "sha256": sha256(p),
        "size": p.stat().st_size,
    })
manifest = {
    "product": "Z2SE Media Downloader",
    "version": version,
    "created_by": "GitHub Actions / ChatGPT release patch",
    "files": files,
}
(payload / "update_manifest.json").write_text(
    json.dumps(manifest, indent=2, ensure_ascii=False),
    encoding="utf-8",
)
print(f"Prepared Z2SE v{version} PRO DESIGN")
