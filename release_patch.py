from pathlib import Path
import hashlib
import json
import re
import sys

TARGET_VERSION = "32.69"


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
text, count = re.subn(r'APP_VERSION\s*=\s*"32\.68"', 'APP_VERSION = "32.69"', text, count=1)
if count != 1:
    raise RuntimeError("Could not update APP_VERSION 32.68 -> 32.69")

# V32.69 — PROFESSIONAL DOWNLOAD EXPERIENCE
# Preserve the proven v32.68 engine/recovery behavior. This release focuses on
# visual density, selection clarity and a modern details window on double-click.
text = text.replace(
    'foreground="#f2f6fb", rowheight=34, borderwidth=0,',
    'foreground="#f2f6fb", rowheight=38, borderwidth=0,',
    1,
)
text = text.replace(
    'background=[("selected", "#21415f")],',
    'background=[("selected", "#20507e")],',
    1,
)
text = text.replace(
    'foreground=[("selected", "#f3f7fc")],',
    'foreground=[("selected", "#ffffff")],',
    1,
)

# Insert at a proven top-level UI anchor, not inside the surrounding tag-config try block.
anchor = '''bulk_tree.bind(\n    "<Button-3>",\n    show_download_context_menu,'''
if anchor not in text:
    raise RuntimeError("Could not find top-level download-list bind anchor for v32.69")

injection = r'''
# V32.69 — professional row details (double-click a download)
def _z2se_open_download_details(event=None):
    try:
        selection = bulk_tree.selection()
        if not selection:
            row = bulk_tree.identify_row(getattr(event, "y", 0)) if event is not None else ""
            if row:
                bulk_tree.selection_set(row)
                selection = (row,)
        if not selection:
            return

        item_id = selection[0]
        item = bulk_tree.item(item_id) or {}
        values = list(item.get("values") or [])
        columns = list(bulk_tree.cget("columns") or [])

        labels = []
        for column in columns:
            try:
                labels.append(str(bulk_tree.heading(column).get("text") or column))
            except Exception:
                labels.append(str(column))

        window = tk.Toplevel(root)
        window.title("Z²SE • Détails du téléchargement")
        window.transient(root)
        window.minsize(560, 430)
        window.configure(bg=UI_BG)

        outer = tk.Frame(window, bg=UI_BG, padx=18, pady=16)
        outer.pack(fill="both", expand=True)

        header = tk.Frame(outer, bg=UI_PANEL, highlightthickness=1, highlightbackground=UI_BORDER)
        header.pack(fill="x", pady=(0, 12))
        tk.Label(
            header,
            text="DÉTAILS DU TÉLÉCHARGEMENT",
            bg=UI_PANEL,
            fg=UI_TEXT,
            font=("Segoe UI Semibold", 12),
            anchor="w",
            padx=16,
            pady=12,
        ).pack(fill="x")

        card = tk.Frame(outer, bg=UI_PANEL, highlightthickness=1, highlightbackground=UI_BORDER)
        card.pack(fill="both", expand=True)
        body = tk.Frame(card, bg=UI_PANEL, padx=18, pady=16)
        body.pack(fill="both", expand=True)
        body.grid_columnconfigure(1, weight=1)

        for i, value in enumerate(values):
            label = labels[i] if i < len(labels) else f"Champ {i + 1}"
            clean_value = str(value or "—")
            tk.Label(
                body, text=f"{label} :", bg=UI_PANEL, fg=UI_MUTED,
                font=("Segoe UI", 10), anchor="w",
            ).grid(row=i, column=0, sticky="nw", padx=(0, 18), pady=5)
            tk.Label(
                body, text=clean_value, bg=UI_PANEL, fg=UI_TEXT,
                font=("Segoe UI Semibold", 10), anchor="w", justify="left",
                wraplength=360,
            ).grid(row=i, column=1, sticky="ew", pady=5)

        percent = None
        for value in values:
            match = re.search(r"(\d+(?:\.\d+)?)\s*%", str(value))
            if match:
                try:
                    percent = max(0.0, min(100.0, float(match.group(1))))
                    break
                except Exception:
                    pass

        progress_row = len(values) + 1
        if percent is not None:
            tk.Label(
                body, text="Progression :", bg=UI_PANEL, fg=UI_MUTED,
                font=("Segoe UI", 10), anchor="w",
            ).grid(row=progress_row, column=0, sticky="w", padx=(0, 18), pady=(14, 6))
            progress = ttk.Progressbar(
                body, style="Z2SE.Horizontal.TProgressbar", maximum=100, value=percent
            )
            progress.grid(row=progress_row, column=1, sticky="ew", pady=(14, 6))
            tk.Label(
                body, text=f"{percent:.1f}%", bg=UI_PANEL, fg=UI_TEXT,
                font=("Segoe UI Semibold", 10), anchor="e",
            ).grid(row=progress_row + 1, column=1, sticky="e", pady=(0, 8))

        buttons = tk.Frame(outer, bg=UI_BG)
        buttons.pack(fill="x", pady=(12, 0))

        def copy_details():
            try:
                lines = [
                    f"{labels[i] if i < len(labels) else 'Champ'}: {values[i]}"
                    for i in range(len(values))
                ]
                root.clipboard_clear()
                root.clipboard_append("\n".join(lines))
                log("Download details copied to clipboard.")
            except Exception:
                pass

        ttk.Button(
            buttons, text="Copier les détails", style="Z2SE.Ghost.TButton",
            command=copy_details,
        ).pack(side="left")
        ttk.Button(
            buttons, text="Fermer", style="Z2SE.Primary.TButton",
            command=window.destroy,
        ).pack(side="right")

        try:
            window.update_idletasks()
            x = root.winfo_rootx() + max(20, (root.winfo_width() - window.winfo_width()) // 2)
            y = root.winfo_rooty() + max(20, (root.winfo_height() - window.winfo_height()) // 2)
            window.geometry(f"+{x}+{y}")
        except Exception:
            pass

    except Exception as exc:
        try:
            log(f"Download details v32.69 warning: {exc}")
        except Exception:
            pass

bulk_tree.bind("<Double-1>", _z2se_open_download_details, add="+")

'''
text = text.replace(anchor, injection + anchor, 1)

text = text.replace('Clean Editor v32.68: startup draft/PART rows cleared.', 'Clean Editor v32.69: startup draft/PART rows cleared.', 1)
text = text.replace('Clean Editor v32.68 warning:', 'Clean Editor v32.69 warning:', 1)

app_path.write_text(text, encoding="utf-8")

manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
manifest["product"] = "Z2SE Media Downloader"
manifest["version"] = TARGET_VERSION
manifest["created_by"] = "GitHub Actions / v32.69 professional download experience"
manifest["files"] = [
    {"path": "app.py", "sha256": sha256_file(app_path), "size": app_path.stat().st_size},
    {"path": "z2se_updater.pyw", "sha256": sha256_file(updater_path), "size": updater_path.stat().st_size},
]
manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")

print("Prepared Z2SE v32.69 professional download experience")
print("app.py", app_path.stat().st_size, sha256_file(app_path))
print("z2se_updater.pyw", updater_path.stat().st_size, sha256_file(updater_path))
