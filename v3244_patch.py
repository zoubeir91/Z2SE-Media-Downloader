from __future__ import annotations


def rep(text: str, old: str, new: str, label: str) -> str:
    if old not in text:
        raise RuntimeError(f"v32.44 marker missing: {label}")
    return text.replace(old, new, 1)


def replace_func(text: str, name: str, replacement: str, next_def: str) -> str:
    start = text.find(f"def {name}(")
    if start < 0:
        raise RuntimeError(f"v32.44 function missing: {name}")
    end = text.find(next_def, start)
    if end < 0:
        raise RuntimeError(f"v32.44 function end missing: {name}")
    return text[:start] + replacement.rstrip() + "\n\n\n" + text[end:]


def apply_patch(text: str) -> str:
    text = rep(text, 'APP_VERSION = "32.43"', 'APP_VERSION = "32.44"', 'version')
    text = text.replace(
        '# MAIN UI — Z²SE V32.43 CONTENT POLISH',
        '# MAIN UI — Z²SE V32.44 PRO UX / FACEBOOK RELIABILITY',
        1,
    )

    text = rep(
        text,
        '    "darija": "الدارجة المغربية",\n}',
        '    "darija": "الدارجة المغربية",\n    "nl": "Nederlands",\n}',
        'language labels',
    )
    text = rep(
        text,
        'for _lang_code in ("fr", "en", "ar", "darija"):',
        'for _lang_code in ("fr", "en", "ar", "darija", "nl"):',
        'language menu',
    )

    main_marker = '# ============================================================\n# MAIN UI — Z²SE V32.44 PRO UX / FACEBOOK RELIABILITY'
    if main_marker not in text:
        raise RuntimeError('v32.44 main marker missing')

    i18n_block = r'''
# ============================================================
# V32.44 — NEDERLANDS + IMPORT HELP
# ============================================================
TRANSLATIONS.update({
    "Load File": {
        "fr": "Importer une liste (.txt)", "en": "Import link list (.txt)",
        "ar": "استيراد قائمة روابط (.txt)", "darija": "دخل لائحة الروابط (.txt)",
        "nl": "Lijst importeren (.txt)",
    },
    "Load links file…": {
        "fr": "Importer une liste (.txt)…", "en": "Import link list (.txt)…",
        "ar": "استيراد قائمة روابط (.txt)…", "darija": "دخل لائحة الروابط (.txt)…",
        "nl": "Lijst importeren (.txt)…",
    },
    "Import link list": {
        "fr": "Importer une liste de liens", "en": "Import a link list",
        "ar": "استيراد قائمة روابط", "darija": "دخل لائحة ديال الروابط",
        "nl": "Lijst met links importeren",
    },
    "Import list help": {
        "fr": "Format de la liste", "en": "List format", "ar": "صيغة القائمة",
        "darija": "شكل اللائحة", "nl": "Formaat van de lijst",
    },
    "Download details": {
        "fr": "Détails du téléchargement", "en": "Download details",
        "ar": "تفاصيل التنزيل", "darija": "تفاصيل التحميل", "nl": "Downloaddetails",
    },
})

_NL = {
    "File":"Bestand", "Downloads":"Downloads", "Tools":"Extra", "Language":"Taal", "Help":"Help",
    "MEDIA DOWNLOADER":"MEDIA DOWNLOADER", "●  ENGINE READY":"●  GEREED",
    "＋  Add Link":"＋  Toevoegen", "Paste Links":"Links plakken", "▶  Start":"▶  Downloaden",
    "■  Stop All":"■  Alles stoppen", "Ⅱ  Pause":"Ⅱ  Pauzeren", "▶  Resume":"▶  Hervatten",
    "Open Folder":"Map", "Clear List":"Lijst wissen", "NEW DOWNLOADS":"DOWNLOADS TOEVOEGEN",
    "From / To empty = full video":"Laat begin en einde leeg voor de volledige video",
    "From":"Begin", "To":"Einde", "Mode":"Modus", "Format":"Formaat", "+ Add":"+ Rij toevoegen",
    "Paste":"Links plakken", "Load File":"Lijst importeren (.txt)", "Clear":"Wissen",
    "Quality":"Kwaliteit", "Parallel":"Gelijktijdig", "DOWNLOAD":"DOWNLOADEN",
    "DOWNLOADS":"DOWNLOADS", "Deselect":"Alles deselecteren", "Select All":"Alles selecteren",
    "File / Video":"Bestand", "Type":"Type", "Progress":"Voortgang", "Transfer rate":"Snelheid",
    "Time left":"Resterend", "Size":"Grootte", "Status":"Status", "Add new row":"Rij toevoegen",
    "Paste links":"Links plakken", "Load links file…":"Lijst importeren (.txt)…",
    "Open Downloads folder":"Downloadmap openen", "Open Z²SE app folder":"Z²SE-map openen",
    "Hide main window to tray":"Minimaliseren naar systeemvak", "Quit Z²SE":"Z²SE afsluiten",
    "Start downloads":"Downloads starten", "Pause all":"Alles pauzeren", "Resume all":"Alles hervatten",
    "Stop all":"Alles stoppen", "Select all":"Alles selecteren", "Deselect all":"Alles deselecteren",
    "Delete selected…":"Selectie verwijderen…", "Clear finished/history list":"Voltooide items wissen",
    "Health Check":"Systeemdiagnose", "Check updates now":"Controleren op updates",
    "Update download engine":"Download-engine bijwerken", "Clear Turbo cache":"Turbo-cache wissen",
    "Show / Hide technical log":"Technisch logboek tonen / verbergen",
    "Open Chrome Extensions":"Chrome-extensies openen", "Open stable V15 extension folder":"Map van V15-extensie openen",
    "Keyboard shortcuts":"Sneltoetsen", "Chrome extension setup":"Chrome-extensie instellen", "About Z²SE":"Over Z²SE",
    "Waiting":"Wachten", "Downloading":"Downloaden", "Done ✅":"Voltooid ✅", "Stopped":"Gestopt",
    "Paused":"Gepauzeerd", "Interrupted":"Onderbroken", "Saved":"Opgeslagen", "Error":"Fout",
    "Analyzing…":"Analyseren…", "Download":"Download", "Main Window":"Hoofdvenster",
    "Cancel Download":"Download annuleren", "Resume":"Hervatten", "Pause":"Pauzeren",
    "Download completed ✅":"Download voltooid ✅", "Download failed ❌":"Download mislukt ❌",
    "Download stopped":"Download gestopt", "Download paused ⏸":"Download gepauzeerd ⏸",
    "Add at least one link.":"Voeg minstens één link toe.",
    "Nothing found in the clipboard.":"Niets gevonden op het klembord.",
    "Enter the video URL.":"Voer de videolink in.",
    "Enter start and end times.":"Voer begin- en eindtijd in.",
    "End time must be after start time.":"De eindtijd moet na de begintijd liggen.",
    "All essential components are ready.":"Alle essentiële onderdelen zijn gereed.",
    "Some components need attention.":"Sommige onderdelen hebben aandacht nodig.",
    "Import link list":"Lijst met links importeren", "Import list help":"Formaat van de lijst",
    "Download details":"Downloaddetails",
}
for _k, _v in list(TRANSLATIONS.items()):
    if isinstance(_v, dict):
        _v["nl"] = _NL.get(_k, _v.get("nl", _v.get("en", _k)))

try:
    _NL_MERGE = {
        "merge_videos":"Video’s samenvoegen…", "merge_selected":"Geselecteerde video’s samenvoegen…",
        "need_two":"Selecteer minstens twee voltooide video’s.", "choose_two":"Kies minstens twee videobestanden.",
        "order":"Volgorde", "up":"↑ Omhoog", "down":"↓ Omlaag", "add_files":"+ Bestanden toevoegen",
        "remove":"Verwijderen", "output":"Uitvoerbestand", "browse":"Bladeren…", "mode":"Modus",
        "auto":"Auto — snel indien compatibel, anders TV Safe", "fast":"Snel — zonder hercodering",
        "tv":"TV Safe — H.264 + AAC", "start":"Samenvoegen", "cancel":"Annuleren",
        "working":"Bezig met samenvoegen…", "preparing":"Voorbereiden", "fast_try":"Snel samenvoegen…",
        "fallback":"Video’s verschillen — overschakelen naar TV Safe…", "done":"Samenvoegen voltooid ✅",
        "failed":"Samenvoegen mislukt.", "cancelled":"Samenvoegen geannuleerd.", "open_folder":"Map openen?",
        "same_files":"Niet alle geselecteerde bestanden zijn geldige video’s.",
        "missing_paths":"Z²SE kan sommige echte bestanden niet vinden. Kies de ontbrekende bestanden.",
        "resolved_count":"Video’s gevonden", "selected_count":"Geselecteerde regels",
    }
    for _k, _v in MERGE_I18N.items():
        if isinstance(_v, dict):
            _v["nl"] = _NL_MERGE.get(_k, _v.get("en", _k))
except Exception:
    pass

_TRANSLATION_PAIRS = _translation_pairs()

_IMPORT_HELP = {
    "fr": "Le fichier .txt contient un lien par ligne.\\n\\nVidéo entière :\\nhttps://youtube.com/watch?v=AAAA\\nhttps://youtu.be/BBBB\\n\\nAvec début / fin :\\nhttps://youtube.com/watch?v=CCCC  00.05.00 - 00.15.00\\nhttps://youtu.be/DDDD  00:02:30 - 00:08:10\\n\\nSans horaires = vidéo entière. Avec les deux horaires = PART.",
    "en": "The .txt file contains one link per line.\\n\\nFull video:\\nhttps://youtube.com/watch?v=AAAA\\nhttps://youtu.be/BBBB\\n\\nWith start / end:\\nhttps://youtube.com/watch?v=CCCC  00.05.00 - 00.15.00\\nhttps://youtu.be/DDDD  00:02:30 - 00:08:10\\n\\nNo times = full video. Both times = PART.",
    "ar": "ملف .txt فيه رابط واحد في كل سطر.\\n\\nفيديو كامل:\\nhttps://youtube.com/watch?v=AAAA\\nhttps://youtu.be/BBBB\\n\\nمع البداية والنهاية:\\nhttps://youtube.com/watch?v=CCCC  00.05.00 - 00.15.00\\nhttps://youtu.be/DDDD  00:02:30 - 00:08:10\\n\\nبدون أوقات = الفيديو كامل. مع الوقتين = PART.",
    "darija": "ملف .txt فيه رابط واحد فكل سطر.\\n\\nفيديو كامل:\\nhttps://youtube.com/watch?v=AAAA\\nhttps://youtu.be/BBBB\\n\\nمع البداية والنهاية:\\nhttps://youtube.com/watch?v=CCCC  00.05.00 - 00.15.00\\nhttps://youtu.be/DDDD  00:02:30 - 00:08:10\\n\\nبلا توقيت = الفيديو كامل. بجوج الأوقات = PART.",
    "nl": "Het .txt-bestand bevat één link per regel.\\n\\nVolledige video:\\nhttps://youtube.com/watch?v=AAAA\\nhttps://youtu.be/BBBB\\n\\nMet begin- en eindtijd:\\nhttps://youtube.com/watch?v=CCCC  00.05.00 - 00.15.00\\nhttps://youtu.be/DDDD  00:02:30 - 00:08:10\\n\\nGeen tijden = volledige video. Beide tijden = PART.",
}

def show_import_list_help():
    messagebox.showinfo(tr("Import list help"), _IMPORT_HELP.get(CURRENT_LANGUAGE, _IMPORT_HELP["en"]))
'''
    text = text.replace(main_marker, i18n_block + '\n\n' + main_marker, 1)

    text = text.replace('''ttk.Button(\n    toolbar_inner,\n    text=tr("＋  Add Link"),\n    command=add_bulk_row,\n    style="Toolbar.TButton",\n).pack(side="left", padx=(0, 5))\n\n''', '', 1)
    text = text.replace('''ttk.Button(\n    toolbar_inner,\n    text=tr("Paste Links"),\n    command=paste_bulk_links,\n    style="Toolbar.TButton",\n).pack(side="left", padx=5)\n\n''', '', 1)
    text = text.replace(').pack(side="left", padx=(12, 5))\n\nttk.Button(\n    toolbar_inner,\n    text=tr("■  Stop All"),', ').pack(side="left", padx=(0, 7))\n\nttk.Button(\n    toolbar_inner,\n    text=tr("■  Stop All"),', 1)

    old_import = '''ttk.Button(\n    editor_footer,\n    text=tr("Load File"),\n    command=load_liens_txt,\n    style="Toolbar.TButton",\n).pack(side="left", padx=4)\n'''
    new_import = '''ttk.Button(\n    editor_footer,\n    text=tr("Load File"),\n    command=load_liens_txt,\n    style="Toolbar.TButton",\n).pack(side="left", padx=(4, 2))\n\nimport_help_button = ttk.Button(\n    editor_footer,\n    text="?",\n    width=3,\n    command=show_import_list_help,\n    style="Ghost.TButton",\n)\nimport_help_button.pack(side="left", padx=(0, 4))\n'''
    text = rep(text, old_import, new_import, 'import help button')

    load_func = r'''def load_liens_txt():
    if bulk_running:
        return

    path = filedialog.askopenfilename(
        title=tr("Import link list"),
        initialdir=(BASE_DIR if os.path.isdir(BASE_DIR) else APP_DIR),
        filetypes=[("Text files (*.txt)", "*.txt"), ("All files", "*.*")],
    )
    if not path:
        return

    try:
        with open(path, "r", encoding="utf-8-sig", errors="replace") as file:
            content = file.read()
        import_bulk_text(content, replace_existing=True)
        log(f"Loaded link list: {path}")
    except Exception as exc:
        messagebox.showerror(tr("Import link list"), str(exc))
'''
    text = replace_func(text, 'load_liens_txt', load_func, 'def remove_selected_bulk_rows(')

    text = rep(
        text,
        '        "unknown",\n    }\n\n    if value_low in placeholders:',
        '        "unknown",\n        "accueil",\n        "home",\n        "facebook home",\n        "facebook accueil",\n        "facebook - log in or sign up",\n        "facebook – log in or sign up",\n        "facebook | connexion ou inscription",\n    }\n\n    if value_low in placeholders:',
        'facebook placeholder titles',
    )
    text = rep(
        text,
        '    return candidate or "Browser Video"\n\n\ndef _display_title_from_final_path',
        '    return "Browser Video"\n\n\ndef _display_title_from_final_path',
        'placeholder output title',
    )
    text = rep(
        text,
        '''    title = clean_video_title(\n        page_title,\n        page_url=page_url,\n    )\n\n    try:\n''',
        '''    title = clean_video_title(\n        page_title,\n        page_url=page_url,\n    )\n\n    if _is_placeholder_video_title(title):\n        title = clean_video_title("", page_url=page_url)\n\n    try:\n''',
        'browser friendly title',
    )
    text = rep(
        text,
        '            friendly_title or f"Analyzing…  {host}",\n            str(media_format).upper(),',
        '            (friendly_title if not _is_placeholder_video_title(friendly_title) else f"{tr(\'Analyzing…\')}  {host}"),\n            str(media_format).upper(),',
        'browser row title',
    )

    validator = r'''
def _validate_completed_download(path, media_format="MP4"):
    path = _normalize_output_path(path)
    if not path or not os.path.isfile(path):
        return False, "final file missing"

    try:
        with open(path, "rb") as handle:
            head = handle.read(4096).lstrip().lower()
    except Exception:
        head = b""

    if any(marker in head[:1024] for marker in (b"<!doctype html", b"<html", b"<head", b"<body", b"<meta", b"<script")):
        return False, "HTML/landing page returned instead of media"

    info = _probe_tv_codecs(path)
    if str(media_format or "MP4").upper() == "MP3":
        return (True, "ok") if info.get("has_audio") else (False, "no audio stream found")
    return (True, "ok") if info.get("has_video") else (False, "no video stream found")
'''
    text = rep(text, '\ndef run_download_once(\n', validator + '\n\ndef run_download_once(\n', 'media validator insert')

    old_success = '''        if (\n            code == 0\n            and str(media_format).upper() == "MP4"\n            and final_output_path\n            and os.path.isfile(final_output_path)\n        ):\n            ensure_tv_compatible_mp4(\n                final_output_path,\n                stats_callback=stats_callback,\n                job_label=job_label,\n            )\n\n            register_current_job_output_path(\n                final_output_path\n            )\n\n        return code, saw_403, False, saw_format_problem\n'''
    new_success = '''        if (\n            code == 0\n            and final_output_path\n            and os.path.isfile(final_output_path)\n        ):\n            media_ok, media_reason = _validate_completed_download(\n                final_output_path,\n                media_format=media_format,\n            )\n\n            if not media_ok:\n                log(prefix + "False-success blocked: " + media_reason + f" | {final_output_path}")\n                try:\n                    os.remove(final_output_path)\n                except Exception:\n                    pass\n                saw_format_problem = True\n                code = 95\n\n            elif str(media_format).upper() == "MP4":\n                ensure_tv_compatible_mp4(\n                    final_output_path,\n                    stats_callback=stats_callback,\n                    job_label=job_label,\n                )\n                register_current_job_output_path(final_output_path)\n\n        return code, saw_403, False, saw_format_problem\n'''
    text = rep(text, old_success, new_success, 'false success guard')

    text = text.replace('    width = 500\n    height = 208\n', '    width = 560\n    height = 232\n', 1)
    text = text.replace('window.configure(bg="#ffffff")', 'window.configure(bg=UI_BG)', 1)
    text = text.replace('text=f"Z²SE Download #{index}"', 'text=f"Z²SE  •  {tr(\'Download\')} #{index}"', 1)
    text = text.replace('status_var_local = tk.StringVar(value="Waiting…")', 'status_var_local = tk.StringVar(value=tr("Waiting"))', 1)
    text = text.replace('(\"Speed\", speed_var),\n        (\"ETA\", eta_var),\n        (\"Size\", size_var),', '(tr("Transfer rate"), speed_var),\n        (tr("Time left"), eta_var),\n        (tr("Size"), size_var),', 1)
    text = text.replace('font=("Segoe UI", 9, "bold"),\n        fg="#172033",', 'font=("Segoe UI Semibold", 10),\n        fg=UI_TEXT,', 1)
    text = text.replace('pady=(10, 9),', 'pady=(12, 11),', 1)

    required = (
        'APP_VERSION = "32.44"', '"nl": "Nederlands"', 'command=show_import_list_help',
        'def _validate_completed_download(', 'False-success blocked:', 'width = 560',
        'for _lang_code in ("fr", "en", "ar", "darija", "nl"):',
    )
    for marker in required:
        if marker not in text:
            raise RuntimeError(f"v32.44 sanity marker missing: {marker}")

    return text
