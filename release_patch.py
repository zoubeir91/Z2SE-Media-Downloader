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

premium_ui = '''# ============================================================\n# V32.66 — PREMIUM BASIC UI REFRESH\n# ============================================================\n# Visual/basic-UX only. The proven download engine stays untouched.\nUI_BG = "#07111f"\nUI_PANEL = "#0c1929"\nUI_TOP = "#071522"\nUI_TOP_SOFT = "#10263d"\nUI_BORDER = "#1f3a57"\nUI_ACCENT = "#1687f8"\nUI_TEXT = "#edf5ff"\nUI_MUTED = "#8fa8c5"\nUI_SUCCESS = "#43d77d"\nUI_TOP_TEXT = "#f4f8ff"\nUI_TOP_MUTED = "#94aac2"\n\ntry:\n    root.configure(bg=UI_BG)\nexcept Exception:\n    pass\n\ntry:\n    _v3266_style = ttk.Style(root)\n    _v3266_style.configure("Z2SE.TFrame", background=UI_BG)\n    _v3266_style.configure("Panel.TFrame", background=UI_PANEL)\n    _v3266_style.configure(\n        "Panel.TLabel", background=UI_PANEL, foreground=UI_TEXT,\n        font=("Segoe UI", 9),\n    )\n    _v3266_style.configure(\n        "Toolbar.TButton", background="#11233a", foreground="#dce9f8",\n        font=("Segoe UI Semibold", 9), padding=(12, 8), borderwidth=0,\n    )\n    _v3266_style.map(\n        "Toolbar.TButton",\n        background=[("active", "#183452"), ("pressed", "#1b3b5e")],\n        foreground=[("disabled", "#627890"), ("active", "#ffffff")],\n    )\n    _v3266_style.configure(\n        "Primary.TButton", background=UI_ACCENT, foreground="#ffffff",\n        font=("Segoe UI Semibold", 9), padding=(14, 9), borderwidth=0,\n    )\n    _v3266_style.map(\n        "Primary.TButton",\n        background=[("active", "#2a97ff"), ("pressed", "#0875de")],\n        foreground=[("disabled", "#b9c9dc"), ("active", "#ffffff")],\n    )\n    _v3266_style.configure(\n        "Danger.TButton", background="#2a1c28", foreground="#ffb8c2",\n        font=("Segoe UI Semibold", 9), padding=(12, 8), borderwidth=0,\n    )\n    _v3266_style.map(\n        "Danger.TButton",\n        background=[("active", "#452333"), ("pressed", "#55273a")],\n    )\n    _v3266_style.configure(\n        "Ghost.TButton", background=UI_PANEL, foreground="#a9bed7",\n        font=("Segoe UI", 8), padding=(9, 6), borderwidth=0,\n    )\n    _v3266_style.map(\n        "Ghost.TButton", background=[("active", "#132740")],\n        foreground=[("active", "#ffffff")],\n    )\n    _v3266_style.configure(\n        "Field.TEntry", fieldbackground="#0a1524", foreground="#eef6ff",\n        insertcolor="#eef6ff", padding=(8, 7),\n    )\n    _v3266_style.configure(\n        "Field.TCombobox", fieldbackground="#0a1524", background="#11243a",\n        foreground="#eef6ff", arrowcolor="#9eb6d0", padding=(7, 6),\n    )\n    _v3266_style.configure(\n        "Field.TSpinbox", fieldbackground="#0a1524", background="#11243a",\n        foreground="#eef6ff", arrowcolor="#9eb6d0", padding=(6, 6),\n    )\n    _v3266_style.configure(\n        "Z2SE.Treeview", background="#0b1727", fieldbackground="#0b1727",\n        foreground="#dce9f8", rowheight=34, borderwidth=0,\n        font=("Segoe UI", 9),\n    )\n    _v3266_style.configure(\n        "Z2SE.Treeview.Heading", background="#12243a", foreground="#b9cbe0",\n        relief="flat", font=("Segoe UI Semibold", 8), padding=(7, 8),\n    )\n    _v3266_style.map(\n        "Z2SE.Treeview", background=[("selected", "#153b63")],\n        foreground=[("selected", "#ffffff")],\n    )\n    _v3266_style.configure(\n        "Z2SE.Horizontal.TProgressbar", troughcolor="#102238",\n        background=UI_ACCENT, borderwidth=0, lightcolor=UI_ACCENT,\n        darkcolor=UI_ACCENT,\n    )\nexcept Exception:\n    pass\n\n'''

# Insert directly before construction of the main UI. This anchor is more
# stable than the historical comment/version heading above it.
main_anchor = 'main = ttk.Frame(root, style="Z2SE.TFrame", padding=0)\n'
if main_anchor not in text:
    raise RuntimeError("Main UI construction anchor missing")
text = text.replace(main_anchor, premium_ui + main_anchor, 1)

# Brand/header proportions and spacing. Optional replacements are deliberately
# tolerant because intermediate releases may already have adjusted one item.
replacements = [
    ('height=66,\n    highlightthickness=0,', 'height=76,\n    highlightthickness=0,'),
    ('(36, 36),\n            Image.Resampling.LANCZOS,', '(40, 40),\n            Image.Resampling.LANCZOS,'),
    ('font=("Segoe UI Semibold", 16),\n    fg=UI_TOP_TEXT,', 'font=("Segoe UI Semibold", 18),\n    fg=UI_TOP_TEXT,'),
    ('text=tr("MEDIA DOWNLOADER"),\n    font=("Segoe UI Semibold", 7),', 'text=tr("MEDIA DOWNLOADER") + "  •  Fast  •  Simple  •  Reliable",\n    font=("Segoe UI", 8),'),
    ('font=("Segoe UI", 9),\n        fg="#d8e1ef",', 'font=("Segoe UI Semibold", 9),\n        fg="#dce9f8",'),
    ('padx=10,\n        pady=23,', 'padx=12,\n        pady=28,'),
    ('toolbar_inner.pack(fill="both", expand=True, padx=14, pady=(10, 6))', 'toolbar_inner.pack(fill="both", expand=True, padx=18, pady=(8, 6))'),
    ('workspace.pack(fill="both", expand=True, padx=14, pady=(8, 14))', 'workspace.pack(fill="both", expand=True, padx=18, pady=(10, 16))'),
    ('editor_card.pack(fill="x", pady=(0, 12))', 'editor_card.pack(fill="x", pady=(0, 14))'),
    ('height=92,\n    bg=UI_PANEL,', 'height=98,\n    bg=UI_PANEL,'),
]
for old, new in replacements:
    if old in text:
        text = text.replace(old, new, 1)

# Premium dark popup menus, while keeping only the existing basic actions.
menu_helper = '''def _v3266_style_menu(menu):\n    try:\n        menu.configure(\n            bg="#0d1b2d", fg="#dce9f8",\n            activebackground="#173a60", activeforeground="#ffffff",\n            selectcolor=UI_ACCENT, relief="flat", bd=0,\n            font=("Segoe UI", 9),\n        )\n    except Exception:\n        pass\n\n\n'''
file_menu_anchor = 'file_menu = tk.Menu(\n'
if file_menu_anchor not in text:
    raise RuntimeError("File menu construction anchor missing")
text = text.replace(file_menu_anchor, menu_helper + file_menu_anchor, 1)

for menu_name in ("file_menu", "downloads_menu", "tools_menu", "help_menu"):
    anchor = f'{menu_name} = tk.Menu(\n    menu_strip,\n    tearoff=0,\n)\n'
    if anchor in text:
        text = text.replace(anchor, anchor + f'_v3266_style_menu({menu_name})\n', 1)

lang_anchor = 'language_menu = tk.Menu(menu_strip, tearoff=0)\n'
if lang_anchor in text:
    text = text.replace(lang_anchor, lang_anchor + '_v3266_style_menu(language_menu)\n', 1)

# Give the main download list more breathing room.
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

# Preserve the v32.65 clean-startup behavior and make the support log version
# match this release.
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
