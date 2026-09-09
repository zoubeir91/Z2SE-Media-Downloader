from pathlib import Path
import hashlib
import json
import re
import sys

TARGET_VERSION = "32.54"


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
# V32.54 — FACEBOOK SINGLE-OUTPUT GUARD + PROGRESS WINDOW POLISH
# ----------------------------------------------------------------------
text, count = re.subn(
    r'APP_VERSION\s*=\s*"32\.53"',
    'APP_VERSION = "32.54"',
    text,
    count=1,
)
if count != 1:
    raise RuntimeError("Could not update APP_VERSION 32.53 -> 32.54")

# Facebook Browser Bridge can carry an unreliable page_duration from one of
# several captured byte-range/DASH candidates.  V32.53 used that value as a
# hard rejection test even after yt-dlp had already produced a playable file;
# that false rejection started Universal Resolver again and could leave 2-3
# copies. For a canonical Facebook video_id fast-path, trust the actual media
# probe (size + duration >=1s + real video/audio) and do not apply the captured
# duration ratio heuristic.
old_first_validation = '''                expected_duration=page_duration,\n                stats_callback=stats_callback,\n                job_label=label,\n            )\n        ):\n            log(\n                f"[{label}] Page extractor produced no verified media "\n                "-> activating Universal Resolver..."\n            )\n'''
new_first_validation = '''                expected_duration=(0.0 if facebook_video_id else page_duration),\n                stats_callback=stats_callback,\n                job_label=label,\n            )\n        ):\n            log(\n                f"[{label}] Page extractor produced no verified media "\n                "-> activating Universal Resolver..."\n            )\n'''
if old_first_validation not in text:
    raise RuntimeError("Facebook first validation anchor missing")
text = text.replace(old_first_validation, new_first_validation, 1)

# The resolver-success validation must use the same Facebook rule so a valid
# completed canonical file cannot be rejected and downloaded yet again.
old_second_validation = '''                        expected_duration=page_duration,\n                        stats_callback=stats_callback,\n                        job_label=label,\n                    ):\n                        result = "error"\n'''
new_second_validation = '''                        expected_duration=(0.0 if facebook_video_id else page_duration),\n                        stats_callback=stats_callback,\n                        job_label=label,\n                    ):\n                        result = "error"\n'''
if old_second_validation not in text:
    raise RuntimeError("Facebook resolver validation anchor missing")
text = text.replace(old_second_validation, new_second_validation, 1)

# Add an explicit guard/log after the first verified Facebook file. It does not
# alter the normal resolver fallback when the file is genuinely invalid.
old_resolver_gate = '''        # V32.45 UNIVERSAL RESOLVER\n        # Page extractor -> captured browser streams -> HLS / DASH / direct\n        # FFmpeg -> yt-dlp direct retry. No DRM/access-control bypassing.\n        if result == "error" and not stop_all_event.is_set():\n'''
new_resolver_gate = '''        if result == "done" and facebook_video_id:\n            verified_fb_path = _normalize_output_path(_browser_registered_output(index))\n            if verified_fb_path and os.path.isfile(verified_fb_path):\n                log(\n                    f"[{label}] ✅ Facebook single-output guard: verified first file; "\n                    "recovery chain skipped."\n                )\n\n        # V32.45 UNIVERSAL RESOLVER\n        # Page extractor -> captured browser streams -> HLS / DASH / direct\n        # FFmpeg -> yt-dlp direct retry. No DRM/access-control bypassing.\n        if result == "error" and not stop_all_event.is_set():\n'''
if old_resolver_gate not in text:
    raise RuntimeError("Universal Resolver gate anchor missing")
text = text.replace(old_resolver_gate, new_resolver_gate, 1)

# Give the compact progress window a more deliberate desktop-download-manager
# footprint instead of the small/basic 560x232 panel.
old_geometry = '''    width = 560\n    height = 232\n'''
new_geometry = '''    width = 620\n    height = 286\n'''
if old_geometry not in text:
    raise RuntimeError("Progress geometry anchor missing")
text = text.replace(old_geometry, new_geometry, 1)

# More premium header proportions and hierarchy.
text = text.replace(
    '''        bg=UI_TOP,\n        height=50,\n''',
    '''        bg=UI_TOP,\n        height=62,\n''',
    1,
)
text = text.replace(
    '''        text=f"Z²SE  •  {tr('Download')} #{index}",\n        font=("Segoe UI Semibold", 10),\n''',
    '''        text=f"Z²SE  •  DOWNLOAD MANAGER   #{index}",\n        font=("Segoe UI Semibold", 11),\n''',
    1,
)
text = text.replace(
    '''        font=("Segoe UI Semibold", 11),\n        fg="#ffffff",\n        bg=UI_ACCENT,\n        padx=10,\n        pady=4,\n''',
    '''        font=("Segoe UI Semibold", 12),\n        fg="#ffffff",\n        bg=UI_ACCENT,\n        padx=14,\n        pady=6,\n''',
    1,
)

# Make the title and live state easier to scan.
text = text.replace(
    '''        font=("Segoe UI Semibold", 10),\n        fg=UI_TEXT,\n''',
    '''        font=("Segoe UI Semibold", 11),\n        fg=UI_TEXT,\n''',
    1,
)
text = text.replace(
    '''        font=("Segoe UI", 8),\n        fg="#526077",\n''',
    '''        font=("Segoe UI Semibold", 9),\n        fg="#3f4f67",\n''',
    1,
)

# Bigger metric cards.
text = text.replace(
    '''            font=("Segoe UI", 7),\n            fg="#8791a2",\n''',
    '''            font=("Segoe UI", 8),\n            fg="#7a8799",\n''',
    1,
)
text = text.replace(
    '''            font=("Segoe UI", 8, "bold"),\n            fg="#25324a",\n''',
    '''            font=("Segoe UI Semibold", 10),\n            fg="#1d2b42",\n''',
    1,
)

# Pro completion dialog: larger, clear success banner, filename card and
# primary/secondary actions. This replaces the abrupt "window disappears"
# feeling while keeping the requested Open file / Open folder / Cancel actions.
old_dialog_geometry = '''    width = 470\n    height = 205\n'''
new_dialog_geometry = '''    width = 540\n    height = 265\n'''
if old_dialog_geometry not in text:
    raise RuntimeError("Completion dialog geometry anchor missing")
text = text.replace(old_dialog_geometry, new_dialog_geometry, 1)

old_dialog_title = '''    tk.Label(\n        body,\n        text="Téléchargement terminé ✅",\n        font=("Segoe UI", 13, "bold"),\n        fg="#172033",\n        bg="#ffffff",\n    ).pack(anchor="w")\n\n    filename = os.path.basename(path) if path else ""\n    tk.Label(\n        body,\n        text=(filename if filename else "Le téléchargement est terminé."),\n        font=("Segoe UI", 9),\n        fg="#596579",\n        bg="#ffffff",\n        anchor="w",\n        justify="left",\n        wraplength=420,\n    ).pack(fill="x", pady=(8, 18))\n'''
new_dialog_title = '''    success_bar = tk.Frame(body, bg="#eef8f1", highlightthickness=1, highlightbackground="#cfe8d7")\n    success_bar.pack(fill="x", pady=(0, 12))\n\n    tk.Label(\n        success_bar,\n        text="✓",\n        font=("Segoe UI Semibold", 18),\n        fg="#16834a",\n        bg="#eef8f1",\n        width=3,\n    ).pack(side="left", padx=(8, 0), pady=9)\n\n    success_text = tk.Frame(success_bar, bg="#eef8f1")\n    success_text.pack(side="left", fill="x", expand=True, pady=8)\n    tk.Label(\n        success_text,\n        text="Téléchargement terminé",\n        font=("Segoe UI Semibold", 13),\n        fg="#173728",\n        bg="#eef8f1",\n    ).pack(anchor="w")\n    tk.Label(\n        success_text,\n        text="Le fichier est prêt sur votre PC.",\n        font=("Segoe UI", 9),\n        fg="#567162",\n        bg="#eef8f1",\n    ).pack(anchor="w")\n\n    filename = os.path.basename(path) if path else ""\n    file_card = tk.Frame(body, bg="#f6f8fb", highlightthickness=1, highlightbackground="#e1e6ef")\n    file_card.pack(fill="x", pady=(0, 16))\n    tk.Label(\n        file_card,\n        text=(filename if filename else "Fichier téléchargé"),\n        font=("Segoe UI Semibold", 9),\n        fg="#26354d",\n        bg="#f6f8fb",\n        anchor="w",\n        justify="left",\n        wraplength=470,\n    ).pack(fill="x", padx=12, pady=10)\n'''
if old_dialog_title not in text:
    raise RuntimeError("Completion dialog body anchor missing")
text = text.replace(old_dialog_title, new_dialog_title, 1)

# Highlight Open file as primary action.
old_open_file_btn = '''    tk.Button(\n        buttons,\n        text="Ouvrir le fichier",\n        command=open_file,\n        state=("normal" if file_exists else "disabled"),\n        font=("Segoe UI", 9, "bold"),\n        padx=12,\n        pady=7,\n    ).pack(side="left")\n'''
new_open_file_btn = '''    tk.Button(\n        buttons,\n        text="Ouvrir le fichier",\n        command=open_file,\n        state=("normal" if file_exists else "disabled"),\n        font=("Segoe UI Semibold", 9),\n        bg="#1769e0",\n        fg="#ffffff",\n        activebackground="#1259c2",\n        activeforeground="#ffffff",\n        relief="flat",\n        padx=16,\n        pady=8,\n    ).pack(side="left")\n'''
if old_open_file_btn not in text:
    raise RuntimeError("Completion primary button anchor missing")
text = text.replace(old_open_file_btn, new_open_file_btn, 1)

app_path.write_text(text, encoding="utf-8")

manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
manifest["product"] = "Z2SE Media Downloader"
manifest["version"] = TARGET_VERSION
manifest["created_by"] = "GitHub Actions / v32.54 Facebook single-output guard + professional progress UX"
manifest["files"] = [
    {"path": "app.py", "sha256": sha256_file(app_path), "size": app_path.stat().st_size},
    {"path": "z2se_updater.pyw", "sha256": sha256_file(updater_path), "size": updater_path.stat().st_size},
]
manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")

print("Prepared Z2SE v32.54 Facebook duplicate guard + pro progress UX")
print("app.py", app_path.stat().st_size, sha256_file(app_path))
print("z2se_updater.pyw", updater_path.stat().st_size, sha256_file(updater_path))
