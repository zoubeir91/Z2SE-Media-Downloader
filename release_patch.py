from pathlib import Path
import hashlib
import json
import re
import sys

TARGET_VERSION = "32.66"


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
# V32.66 — PREMIUM BASIC UI REFRESH
# ----------------------------------------------------------------------
text, count = re.subn(
    r'APP_VERSION\s*=\s*"32\.65"',
    'APP_VERSION = "32.66"',
    text,
    count=1,
)
if count != 1:
    raise RuntimeError("Could not update APP_VERSION 32.65 -> 32.66")

# Keep the proven downloader engine untouched. This release is deliberately
# a visual/basic-UX refresh: darker Windows-11-style palette, calmer blue,
# cleaner hierarchy, roomier rows and more polished menus/buttons.
ui_anchor = "# ============================================================\n# MAIN UI — Z²SE V32.43 CONTENT POLISH\n# ============================================================\n"
if ui_anchor not in text:
    raise RuntimeError("Main UI anchor missing")

premium_ui = '''# ============================================================\n# V32.66 — PREMIUM BASIC UI REFRESH\n# ============================================================\n# Keep advanced/technical features out of the way and make the everyday\n# surface feel like a current commercial Windows desktop application.\nUI_BG = "#07111f"\nUI_PANEL = "#0c1929"\nUI_TOP = "#071522"\nUI_TOP_SOFT = "#10263d"\nUI_BORDER = "#1f3a57"\nUI_ACCENT = "#1687f8"\nUI_TEXT = "#edf5ff"\nUI_MUTED = "#8fa8c5"\nUI_SUCCESS = "#43d77d"\nUI_TOP_TEXT = "#f4f8ff"\nUI_TOP_MUTED = "#94aac2"\n\ntry:\n    root.configure(bg=UI_BG)\nexcept Exception:\n    pass\n\n# Re-apply the named ttk styles after the palette override so the existing\n# widgets automatically inherit the new premium look without touching the\n# download engine or its state handling.\ntry:\n    _v3266_style = ttk.Style(root)\n    _v3266_style.configure(\n        "Z2SE.TFrame",\n        background=UI_BG,\n    )\n    _v3266_style.configure(\n        "Panel.TFrame",\n        background=UI_PANEL,\n    )\n    _v3266_style.configure(\n        "Panel.TLabel",\n        background=UI_PANEL,\n        foreground=UI_TEXT,\n        font=("Segoe UI", 9),\n    )\n    _v3266_style.configure(\n        "Toolbar.TButton",\n        background="#11233a",\n        foreground="#dce9f8",\n        font=("Segoe UI Semibold", 9),\n        padding=(12, 8),\n        borderwidth=0,\n    )\n    _v3266_style.map(\n        "Toolbar.TButton",\n        background=[("active", "#183452"), ("pressed", "#1b3b5e")],\n        foreground=[("disabled", "#627890"), ("active", "#ffffff")],\n    )\n    _v3266_style.configure(\n        "Primary.TButton",\n        background=UI_ACCENT,\n        foreground="#ffffff",\n        font=("Segoe UI Semibold", 9),\n        padding=(14, 9),\n        borderwidth=0,\n    )\n    _v3266_style.map(\n        "Primary.TButton",\n        background=[("active", "#2a97ff"), ("pressed", "#0875de")],\n        foreground=[("disabled", "#b9c9dc"), ("active", "#ffffff")],\n    )\n    _v3266_style.configure(\n        "Danger.TButton",\n        background="#2a1c28",\n        foreground="#ffb8c2",\n        font=("Segoe UI Semibold", 9),\n        padding=(12, 8),\n        borderwidth=0,\n    )\n    _v3266_style.map(\n        "Danger.TButton",\n        background=[("active", "#452333"), ("pressed", "#55273a")],\n    )\n    _v3266_style.configure(\n        "Ghost.TButton",\n        background=UI_PANEL,\n        foreground="#a9bed7",\n        font=("Segoe UI", 8),\n        padding=(9, 6),\n        borderwidth=0,\n    )\n    _v3266_style.map(\n        "Ghost.TButton",\n        background=[("active", "#132740")],\n        foreground=[("active", "#ffffff")],\n    )\n    _v3266_style.configure(\n        "Field.TEntry",\n        fieldbackground="#0a1524",\n        foreground="#eef6ff",\n        insertcolor="#eef6ff",\n        padding=(8, 7),\n    )\n    _v3266_style.configure(\n        "Field.TCombobox",\n        fieldbackground="#0a1524",\n        background="#11243a",\n        foreground="#eef6ff",\n        arrowcolor="#9eb6d0",\n        padding=(7, 6),\n    )\n    _v3266_style.configure(\n        "Field.TSpinbox",\n        fieldbackground="#0a1524",\n        background="#11243a",\n        foreground="#eef6ff",\n        arrowcolor="#9eb6d0",\n        padding=(6, 6),\n    )\n    _v3266_style.configure(\n        "Z2SE.Treeview",\n        background="#0b1727",\n        fieldbackground="#0b1727",\n        foreground="#dce9f8",\n        rowheight=34,\n        borderwidth=0,\n        font=("Segoe UI", 9),\n    )\n    _v3266_style.configure(\n        "Z2SE.Treeview.Heading",\n        background="#12243a",\n        foreground="#b9cbe0",\n        relief="flat",\n        font=("Segoe UI Semibold", 8),\n        padding=(7, 8),\n    )\n    _v3266_style.map(\n        "Z2SE.Treeview",\n        background=[("selected", "#153b63")],\n        foreground=[("selected", "#ffffff")],\n    )\n    _v3266_style.configure(\n        "Z2SE.Horizontal.TProgressbar",\n        troughcolor="#102238",\n        background=UI_ACCENT,\n        borderwidth=0,\n        lightcolor=UI_ACCENT,\n        darkcolor=UI_ACCENT,\n    )\nexcept Exception:\n    pass\n\n'''
text = text.replace(ui_anchor, premium_ui + ui_anchor, 1)

# More confident brand/header proportions and spacing.
replacements = [
    ('height=66,\n    highlightthickness=0,', 'height=76,\n    highlightthickness=0,'),
    ('(36, 36),\n            Image.Resampling.LANCZOS,', '(40, 40),\n            Image.Resampling.LANCZOS,'),
    ('font=("Segoe UI Semibold", 16),\n    fg=UI_TOP_TEXT,', 'font=("Segoe UI Semibold", 18),\n    fg=UI_TOP_TEXT,'),
    ('text=tr("MEDIA DOWNLOADER"),\n    font=("Segoe UI Semibold", 7),', 'text=tr("MEDIA DOWNLOADER") + "  •  Fast  •  Simple  •  Reliable",\n    font=("Segoe UI", 8),'),
    ('font=("Segoe UI", 9),\n        fg="#d8e1ef",', 'font=("Segoe UI Semibold", 9),\n        fg="#dce9f8",'),
    ('padx=10,\n        pady=23,', 'padx=12,\n        pady=28,'),
    ('height=76,\n    highlightthickness=0,\n)\ntoolbar.pack', 'height=72,\n    highlightthickness=0,\n)\ntoolbar.pack'),
    ('toolbar_inner.pack(fill="both", expand=True, padx=14, pady=(10, 6))', 'toolbar_inner.pack(fill="both", expand=True, padx=18, pady=(8, 6))'),
    ('workspace.pack(fill="both", expand=True, padx=14, pady=(8, 14))', 'workspace.pack(fill="both", expand=True, padx=18, pady=(10, 16))'),
    ('editor_card.pack(fill="x", pady=(0, 12))', 'editor_card.pack(fill="x", pady=(0, 14))'),
    ('font=("Segoe UI Semibold", 10),\n    fg=UI_TEXT,\n    bg=UI_PANEL,\n).pack(side="left")', 'font=("Segoe UI Semibold", 11),\n    fg=UI_TEXT,\n    bg=UI_PANEL,\n).pack(side="left")'),
    ('height=92,\n    bg=UI_PANEL,', 'height=98,\n    bg=UI_PANEL,'),
]
for old, new in replacements:
    if old in text:
        text = text.replace(old, new, 1)

# Give every top popup the same dark visual language. This is intentionally
# basic-user focused: no new proxy/advanced/network menus are introduced.
menu_helper_anchor = "# FILE -------------------------------------------------------------\n"
if menu_helper_anchor not in text:
    raise RuntimeError("Top menu anchor missing")
menu_helper = '''def _v3266_style_menu(menu):\n    try:\n        menu.configure(\n            bg="#0d1b2d",\n            fg="#dce9f8",\n            activebackground="#173a60",\n            activeforeground="#ffffff",\n            selectcolor=UI_ACCENT,\n            relief="flat",\n            bd=0,\n            font=("Segoe UI", 9),\n        )\n    except Exception:\n        pass\n\n\n'''
text = text.replace(menu_helper_anchor, menu_helper + menu_helper_anchor, 1)

for menu_name in ("file_menu", "downloads_menu", "tools_menu", "language_menu", "help_menu"):
    # Insert styling immediately before the button/menu population begins.
    if menu_name == "language_menu":
        anchor = 'language_menu = tk.Menu(menu_strip, tearoff=0)\n'
    else:
        anchor = f'{menu_name} = tk.Menu(\n    menu_strip,\n    tearoff=0,\n)\n'
    if anchor in text:
        text = text.replace(anchor, anchor + f'_v3266_style_menu({menu_name})\n', 1)

# The download table is the visual focus: slightly wider breathing room and
# clearer headings while keeping the same data/behavior.
text = text.replace(
    'tree_frame.pack(fill="both", expand=True, padx=8)',
    'tree_frame.pack(fill="both", expand=True, padx=10, pady=(0, 2))',
    1,
)
text = text.replace(
    'bulk_tree.column("title", width=345)',
    'bulk_tree.column("title", width=380)',
    1,
)

# Preserve the v32.65 clean-startup fix; only update its visible log version
# so support logs make it obvious the fix is still active in this build.
text = text.replace(
    'Clean Editor v32.65: startup draft/PART rows cleared.',
    'Clean Editor v32.66: startup draft/PART rows cleared.',
    1,
)
text = text.replace(
    'Clean Editor v32.65 warning:',
    'Clean Editor v32.66 warning:',
    1,
)

app_path.write_text(text, encoding="utf-8")

manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
manifest["product"] = "Z2SE Media Downloader"
manifest["version"] = TARGET_VERSION
manifest["created_by"] = "GitHub Actions / v32.66 premium basic UI refresh"
manifest["files"] = [
    {"path": "app.py", "sha256": sha256_file(app_path), "size": app_path.stat().st_size},
    {"path": "z2se_updater.pyw", "sha256": sha256_file(updater_path), "size": updater_path.stat().st_size},
]
manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")

print("Prepared Z2SE v32.66 premium basic UI refresh")
print("app.py", app_path.stat().st_size, sha256_file(app_path))
print("z2se_updater.pyw", updater_path.stat().st_size, sha256_file(updater_path))
