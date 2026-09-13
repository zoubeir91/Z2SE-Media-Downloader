from pathlib import Path
import ast
import hashlib
import json
import re
import sys

TARGET_VERSION = "32.70"


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
text, count = re.subn(r'APP_VERSION\s*=\s*"32\.69"', 'APP_VERSION = "32.70"', text, count=1)
if count != 1:
    raise RuntimeError("Could not update APP_VERSION 32.69 -> 32.70")

# ------------------------------------------------------------------
# V32.70 — REAL MAIN-UI OVERHAUL
# This deliberately keeps the downloader/recovery engine unchanged. The goal
# is to make the live application match the approved mockup much more closely:
# compact icon navigation, one focused new-download card, a dense downloads
# manager, search/status shortcuts, a persistent details pane and a live footer.
# ------------------------------------------------------------------

# Compact icon navigation instead of the old tall text-only menu strip.
menu_pattern = re.compile(
    r'def _make_top_menu_button\(label, menu\):\n.*?\n    return button\n',
    re.S,
)
menu_replacement = r'''def _make_top_menu_button(label, menu):
    icon_map = {
        tr("File"): "▱",
        tr("Downloads"): "▣",
        tr("Tools"): "⌘",
        tr("Language"): "◎",
        tr("Help"): "?",
    }
    icon = icon_map.get(label, "•")
    active = label == tr("Downloads")
    button = tk.Menubutton(
        menu_strip,
        text=f"{icon}\\n{label}",
        font=("Segoe UI Semibold", 9),
        fg=(UI_ACCENT if active else UI_TOP_TEXT),
        bg=UI_TOP,
        activeforeground="#ffffff",
        activebackground=UI_TOP_SOFT,
        bd=0,
        relief="flat",
        padx=17,
        pady=8,
        cursor="hand2",
        menu=menu,
        justify="center",
    )
    button.pack(side="left", padx=2)

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
text, count = menu_pattern.subn(menu_replacement, text, count=1)
if count != 1:
    raise RuntimeError("Could not replace top navigation for v32.70")

# The old command toolbar duplicated actions and made the app look like the
# previous layout. Keep the widgets alive for compatibility, but do not pack
# the toolbar into the visible UI.
old_toolbar_pack = 'toolbar.pack(fill="x")'
if old_toolbar_pack not in text:
    raise RuntimeError("Toolbar pack anchor missing")
text = text.replace(
    old_toolbar_pack,
    '# v32.70: legacy command toolbar intentionally hidden; actions live in menus/details pane.',
    1,
)

# Tighter workspace and editor proportions.
text = text.replace(
    'workspace.pack(fill="both", expand=True, padx=18, pady=(10, 16))',
    'workspace.pack(fill="both", expand=True, padx=20, pady=(8, 12))',
    1,
)
text = text.replace('height=98,\n    bg=UI_PANEL,', 'height=62,\n    bg=UI_PANEL,', 1)
text = text.replace(
    'editor_footer.pack(fill="x", padx=10, pady=(7, 10))',
    'editor_footer.pack(fill="x", padx=12, pady=(9, 12))',
    1,
)
text = text.replace(
    'text=tr("DOWNLOAD"),\n    command=start_bulk,',
    'text="⇩  " + tr("DOWNLOAD"),\n    command=start_bulk,',
    1,
)

# Replace the complete downloads visual block while preserving the same
# bulk_tree variable and nine canonical data columns expected by the engine.
list_pattern = re.compile(
    r'# ------------------------------------------------------------\n# Download list — main visual focus\n# ------------------------------------------------------------\n.*?(?=# ------------------------------------------------------------\n# V32\.13 — ONE INDEPENDENT PROGRESS WINDOW PER DOWNLOAD)',
    re.S,
)

list_replacement = r'''# ------------------------------------------------------------
# V32.70 DOWNLOAD MANAGER — main visual focus
# ------------------------------------------------------------

downloads_shell = tk.Frame(content, bg=UI_BG)
downloads_shell.pack(fill="both", expand=True)

list_card = tk.Frame(
    downloads_shell,
    bg=UI_PANEL,
    highlightthickness=1,
    highlightbackground=UI_BORDER,
)
list_card.pack(side="left", fill="both", expand=True)

list_header = tk.Frame(list_card, bg=UI_PANEL)
list_header.pack(fill="x", padx=14, pady=(11, 9))

tk.Label(
    list_header,
    text=tr("DOWNLOADS"),
    font=("Segoe UI Semibold", 11),
    fg=UI_TEXT,
    bg=UI_PANEL,
).pack(side="left")

tk.Label(
    list_header,
    textvariable=bulk_counter_var,
    font=("Segoe UI", 9),
    fg=UI_MUTED,
    bg=UI_PANEL,
).pack(side="left", padx=(12, 0))

# Search box + useful status shortcuts. The shortcuts select matching rows
# instead of detaching them, so persistent history and engine bookkeeping stay safe.
v3270_search_var = tk.StringVar(value="")
v3270_search = ttk.Entry(
    list_header,
    textvariable=v3270_search_var,
    width=25,
    style="Field.TEntry",
)
v3270_search.pack(side="right", padx=(8, 0))


def _v3270_select_status(mode="all"):
    try:
        items = list(bulk_tree.get_children(""))
        if mode == "all":
            if items:
                bulk_tree.selection_set(items)
            return

        matches = []
        for item in items:
            values = list(bulk_tree.item(item, "values") or [])
            status = str(values[8] if len(values) > 8 else "").lower()
            if mode == "active" and any(k in status for k in ("download", "télécharg", "waiting", "pause")):
                matches.append(item)
            elif mode == "done" and any(k in status for k in ("done", "termin", "saved", "complete")):
                matches.append(item)
            elif mode == "error" and any(k in status for k in ("error", "erreur", "failed", "interrupted")):
                matches.append(item)

        bulk_tree.selection_remove(bulk_tree.selection())
        if matches:
            bulk_tree.selection_set(matches)
            bulk_tree.focus(matches[0])
            bulk_tree.see(matches[0])
    except Exception:
        pass


def _v3270_search_rows(event=None):
    needle = v3270_search_var.get().strip().lower()
    try:
        items = list(bulk_tree.get_children(""))
        bulk_tree.selection_remove(bulk_tree.selection())
        if not needle:
            return
        matches = []
        for item in items:
            values = list(bulk_tree.item(item, "values") or [])
            haystack = " ".join(str(v) for v in values).lower()
            if needle in haystack:
                matches.append(item)
        if matches:
            bulk_tree.selection_set(matches)
            bulk_tree.focus(matches[0])
            bulk_tree.see(matches[0])
    except Exception:
        pass


v3270_search.bind("<KeyRelease>", _v3270_search_rows, add="+")

for _txt, _mode in (("Tous", "all"), ("En cours", "active"), ("Terminés", "done"), ("Erreurs", "error")):
    ttk.Button(
        list_header,
        text=_txt,
        style=("Primary.TButton" if _mode == "all" else "Ghost.TButton"),
        command=lambda m=_mode: _v3270_select_status(m),
    ).pack(side="right", padx=3)

search_hint = tk.Label(
    list_header,
    text="⌕",
    font=("Segoe UI Semibold", 12),
    fg=UI_MUTED,
    bg=UI_PANEL,
)
search_hint.pack(side="right", padx=(8, 0))

# Dense professional table.
tree_frame = ttk.Frame(list_card, style="Panel.TFrame")
tree_frame.pack(fill="both", expand=True, padx=10, pady=(0, 8))

bulk_tree = ttk.Treeview(
    tree_frame,
    columns=(
        "num",
        "title",
        "format",
        "part",
        "progress",
        "speed",
        "eta",
        "size",
        "status",
    ),
    show="headings",
    height=14,
    style="Z2SE.Treeview",
    selectmode="extended",
)

bulk_tree.heading("num", text="#")
bulk_tree.heading("title", text=tr("File / Video"))
bulk_tree.heading("format", text=tr("Type"))
bulk_tree.heading("part", text=tr("Mode"))
bulk_tree.heading("progress", text=tr("Progress"))
bulk_tree.heading("speed", text=tr("Transfer rate"))
bulk_tree.heading("eta", text=tr("Time left"))
bulk_tree.heading("size", text=tr("Size"))
bulk_tree.heading("status", text=tr("Status"))

bulk_tree.column("num", width=34, anchor="center", stretch=False)
bulk_tree.column("title", width=280)
bulk_tree.column("format", width=62, anchor="center", stretch=False)
bulk_tree.column("part", width=105, anchor="center")
bulk_tree.column("progress", width=82, anchor="center")
bulk_tree.column("speed", width=92, anchor="center")
bulk_tree.column("eta", width=75, anchor="center")
bulk_tree.column("size", width=88, anchor="center")
bulk_tree.column("status", width=112, anchor="center")

try:
    bulk_tree.tag_configure("active", foreground="#67b7ff")
    bulk_tree.tag_configure("paused", foreground="#f2c96d")
    bulk_tree.tag_configure("done", foreground="#59df91")
    bulk_tree.tag_configure("error", foreground="#ff8193")
    bulk_tree.tag_configure("cancelled", foreground="#aebdce")
except Exception:
    pass

tree_scroll = ttk.Scrollbar(
    tree_frame,
    orient="vertical",
    command=bulk_tree.yview,
    style="Z2SE.Vertical.TScrollbar",
)
bulk_tree.configure(yscrollcommand=tree_scroll.set)
bulk_tree.pack(side="left", fill="both", expand=True)
tree_scroll.pack(side="right", fill="y")

# Persistent selected-download details pane, inspired by mature desktop download
# managers but kept intentionally simple for ordinary users.
details_panel = tk.Frame(
    downloads_shell,
    width=360,
    bg=UI_PANEL,
    highlightthickness=1,
    highlightbackground=UI_BORDER,
)
details_panel.pack(side="right", fill="y", padx=(12, 0))
details_panel.pack_propagate(False)

details_head = tk.Frame(details_panel, bg=UI_PANEL)
details_head.pack(fill="x", padx=14, pady=(13, 9))

tk.Label(
    details_head,
    text="DÉTAILS DU TÉLÉCHARGEMENT",
    font=("Segoe UI Semibold", 10),
    fg=UI_TEXT,
    bg=UI_PANEL,
).pack(side="left")

v3270_preview = tk.Canvas(
    details_panel,
    height=118,
    bg="#0b1b2d",
    highlightthickness=1,
    highlightbackground=UI_BORDER,
)
v3270_preview.pack(fill="x", padx=14, pady=(0, 10))
v3270_preview.create_polygon(145, 34, 145, 84, 190, 59, fill=UI_ACCENT, outline="")
v3270_preview.create_text(18, 16, anchor="nw", text="Z²SE  •  MEDIA", fill=UI_MUTED, font=("Segoe UI Semibold", 9))

v3270_detail_title = tk.StringVar(value="Sélectionnez un téléchargement")
v3270_detail_status = tk.StringVar(value="—")
v3270_detail_mode = tk.StringVar(value="—")
v3270_detail_type = tk.StringVar(value="—")
v3270_detail_speed = tk.StringVar(value="—")
v3270_detail_eta = tk.StringVar(value="—")
v3270_detail_size = tk.StringVar(value="—")
v3270_detail_percent = tk.DoubleVar(value=0.0)
v3270_detail_percent_text = tk.StringVar(value="0.0%")

body = tk.Frame(details_panel, bg=UI_PANEL)
body.pack(fill="x", padx=14)

tk.Label(
    body,
    textvariable=v3270_detail_title,
    font=("Segoe UI Semibold", 11),
    fg=UI_TEXT,
    bg=UI_PANEL,
    anchor="w",
    justify="left",
    wraplength=320,
).pack(fill="x", pady=(0, 9))

status_line = tk.Frame(body, bg=UI_PANEL)
status_line.pack(fill="x", pady=(0, 6))
tk.Label(status_line, text="Statut :", fg=UI_MUTED, bg=UI_PANEL, font=("Segoe UI", 9)).pack(side="left")
v3270_status_label = tk.Label(status_line, textvariable=v3270_detail_status, fg=UI_ACCENT, bg=UI_PANEL, font=("Segoe UI Semibold", 9))
v3270_status_label.pack(side="left", padx=(8, 0))

progress_line = tk.Frame(body, bg=UI_PANEL)
progress_line.pack(fill="x", pady=(2, 8))
ttk.Progressbar(
    progress_line,
    variable=v3270_detail_percent,
    maximum=100,
    style="Z2SE.Horizontal.TProgressbar",
).pack(side="left", fill="x", expand=True)
tk.Label(
    progress_line,
    textvariable=v3270_detail_percent_text,
    fg=UI_TEXT,
    bg=UI_PANEL,
    font=("Segoe UI Semibold", 9),
    width=7,
    anchor="e",
).pack(side="right", padx=(8, 0))

for _label, _var in (
    ("Type", v3270_detail_type),
    ("Mode", v3270_detail_mode),
    ("Vitesse", v3270_detail_speed),
    ("Temps restant", v3270_detail_eta),
    ("Taille", v3270_detail_size),
):
    line = tk.Frame(body, bg=UI_PANEL)
    line.pack(fill="x", pady=3)
    tk.Label(line, text=_label + " :", fg=UI_MUTED, bg=UI_PANEL, font=("Segoe UI", 9), width=15, anchor="w").pack(side="left")
    tk.Label(line, textvariable=_var, fg=UI_TEXT, bg=UI_PANEL, font=("Segoe UI Semibold", 9), anchor="w").pack(side="left", fill="x", expand=True)

actions = tk.Frame(details_panel, bg=UI_PANEL)
actions.pack(fill="x", padx=14, pady=(14, 7))

ttk.Button(
    actions,
    text="Ⅱ  Pause",
    style="Toolbar.TButton",
    command=lambda: globals().get("pause_selected_downloads", lambda: None)(),
).pack(side="left", fill="x", expand=True, padx=(0, 4))
ttk.Button(
    actions,
    text="▶  Reprendre",
    style="Toolbar.TButton",
    command=lambda: globals().get("resume_selected_downloads", lambda: None)(),
).pack(side="left", fill="x", expand=True, padx=4)
ttk.Button(
    actions,
    text="✕  Annuler",
    style="Danger.TButton",
    command=lambda: globals().get("cancel_selected_downloads", lambda: None)(),
).pack(side="left", fill="x", expand=True, padx=(4, 0))

v3270_tip = tk.Label(
    details_panel,
    text="Double-cliquez sur une ligne pour ouvrir la fiche complète.",
    fg=UI_MUTED,
    bg=UI_PANEL,
    font=("Segoe UI", 8),
    wraplength=320,
    justify="left",
)
v3270_tip.pack(fill="x", padx=14, pady=(5, 10))


def _v3270_refresh_details(event=None):
    try:
        selection = list(bulk_tree.selection())
        if not selection:
            return
        values = list(bulk_tree.item(selection[0], "values") or [])
        while len(values) < 9:
            values.append("")
        v3270_detail_title.set(str(values[1] or "Téléchargement"))
        v3270_detail_type.set(str(values[2] or "—"))
        v3270_detail_mode.set(str(values[3] or "—"))
        v3270_detail_speed.set(str(values[5] or "—"))
        v3270_detail_eta.set(str(values[6] or "—"))
        v3270_detail_size.set(str(values[7] or "—"))
        status = str(values[8] or "—")
        v3270_detail_status.set(status)
        low = status.lower()
        color = UI_ACCENT
        if any(k in low for k in ("done", "termin", "saved", "complete")):
            color = "#59df91"
        elif any(k in low for k in ("error", "erreur", "failed", "interrupted")):
            color = "#ff8193"
        elif "pause" in low:
            color = "#f2c96d"
        v3270_status_label.configure(fg=color)
        try:
            pct = float(str(values[4]).replace("%", "").strip() or 0)
        except Exception:
            pct = 0.0
        pct = max(0.0, min(100.0, pct))
        v3270_detail_percent.set(pct)
        v3270_detail_percent_text.set(f"{pct:.1f}%")
    except Exception:
        pass


bulk_tree.bind("<<TreeviewSelect>>", _v3270_refresh_details, add="+")

# Bottom status bar — useful density instead of empty space.
v3270_footer = tk.Frame(content, bg=UI_BG)
v3270_footer.pack(fill="x", pady=(8, 0))
v3270_total_speed_var = tk.StringVar(value="Vitesse totale : —")
v3270_jobs_var = tk.StringVar(value="Téléchargements : —")
v3270_free_var = tk.StringVar(value="Espace libre : —")

for _var in (v3270_total_speed_var, v3270_jobs_var):
    tk.Label(v3270_footer, textvariable=_var, fg=UI_MUTED, bg=UI_BG, font=("Segoe UI", 8)).pack(side="left", padx=(0, 18))

tk.Label(v3270_footer, textvariable=v3270_free_var, fg=UI_MUTED, bg=UI_BG, font=("Segoe UI", 8)).pack(side="right")
tk.Label(v3270_footer, text="▱  " + str(DOWNLOADS_DIR), fg=UI_MUTED, bg=UI_BG, font=("Segoe UI", 8)).pack(side="right", padx=(0, 22))


def _v3270_footer_tick():
    try:
        total_mib = 0.0
        active = 0
        done = 0
        items = list(bulk_tree.get_children(""))
        for item in items:
            values = list(bulk_tree.item(item, "values") or [])
            while len(values) < 9:
                values.append("")
            speed = str(values[5] or "")
            match = re.search(r"([0-9.]+)\s*(MiB|KiB|MB|KB)/s", speed, re.I)
            if match:
                value = float(match.group(1))
                unit = match.group(2).lower()
                if unit in ("kib", "kb"):
                    value /= 1024.0
                total_mib += value
            status = str(values[8] or "").lower()
            if any(k in status for k in ("done", "termin", "saved", "complete")):
                done += 1
            elif not any(k in status for k in ("error", "erreur", "stopped", "cancel", "interrupted")):
                active += 1
        v3270_total_speed_var.set(f"Vitesse totale : {total_mib:.2f} MiB/s" if total_mib > 0 else "Vitesse totale : —")
        v3270_jobs_var.set(f"Téléchargements : {active} en cours, {done} terminé(s)")
        try:
            free_gb = shutil.disk_usage(DOWNLOADS_DIR).free / (1024 ** 3)
            v3270_free_var.set(f"Espace libre : {free_gb:.0f} GB")
        except Exception:
            pass
        _v3270_refresh_details()
    except Exception:
        pass
    try:
        root.after(900, _v3270_footer_tick)
    except Exception:
        pass


root.after(700, _v3270_footer_tick)


'''
text, count = list_pattern.subn(list_replacement, text, count=1)
if count != 1:
    raise RuntimeError("Could not replace download manager block for v32.70")

# A little more row height for the denser manager and clean startup labels.
text = text.replace(
    'foreground="#f2f6fb", rowheight=38, borderwidth=0,',
    'foreground="#f2f6fb", rowheight=42, borderwidth=0,',
    1,
)
text = text.replace('Clean Editor v32.69: startup draft/PART rows cleared.', 'Clean Editor v32.70: startup draft/PART rows cleared.', 1)
text = text.replace('Clean Editor v32.69 warning:', 'Clean Editor v32.70 warning:', 1)
text = text.replace('Download details v32.69 warning:', 'Download details v32.70 warning:', 1)

# Fail the release before publishing if the transformed source is not valid Python.
ast.parse(text)
app_path.write_text(text, encoding="utf-8")

manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
manifest["product"] = "Z2SE Media Downloader"
manifest["version"] = TARGET_VERSION
manifest["created_by"] = "GitHub Actions / v32.70 full professional UI overhaul"
manifest["files"] = [
    {"path": "app.py", "sha256": sha256_file(app_path), "size": app_path.stat().st_size},
    {"path": "z2se_updater.pyw", "sha256": sha256_file(updater_path), "size": updater_path.stat().st_size},
]
manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")

print("Prepared Z2SE v32.70 full professional UI overhaul")
print("app.py", app_path.stat().st_size, sha256_file(app_path))
print("z2se_updater.pyw", updater_path.stat().st_size, sha256_file(updater_path))
