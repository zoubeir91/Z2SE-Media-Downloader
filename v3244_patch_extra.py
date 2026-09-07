from __future__ import annotations


def rep(text: str, old: str, new: str, label: str) -> str:
    if old not in text:
        raise RuntimeError(f"v32.44 extra marker missing: {label}")
    return text.replace(old, new, 1)


def apply_extra(text: str) -> str:
    main_marker = '# ============================================================\n# MAIN UI — Z²SE V32.44 PRO UX / FACEBOOK RELIABILITY'
    if main_marker not in text:
        raise RuntimeError('v32.44 extra main marker missing')

    extra_i18n = r'''
# V32.44 — remaining small-window / tray / dialog translations
TRANSLATIONS.update({
    "Show Progress": {"fr":"Afficher la progression", "en":"Show progress", "ar":"إظهار التقدم", "darija":"بيّن التقدم", "nl":"Voortgang tonen"},
    "Show Download Progress": {"fr":"Afficher la progression", "en":"Show download progress", "ar":"إظهار تقدم التنزيل", "darija":"بيّن تقدم التحميل", "nl":"Downloadvoortgang tonen"},
    "Open Main Z²SE": {"fr":"Ouvrir Z²SE", "en":"Open main Z²SE", "ar":"فتح Z²SE", "darija":"حل Z²SE", "nl":"Z²SE openen"},
    "Cancel All Active": {"fr":"Annuler les téléchargements actifs", "en":"Cancel all active", "ar":"إلغاء التنزيلات النشطة", "darija":"حبس التحميلات اللي خدامين", "nl":"Alle actieve annuleren"},
    "Text files": {"fr":"Fichiers texte", "en":"Text files", "ar":"ملفات نصية", "darija":"ملفات النص", "nl":"Tekstbestanden"},
    "All files": {"fr":"Tous les fichiers", "en":"All files", "ar":"كل الملفات", "darija":"الملفات كاملين", "nl":"Alle bestanden"},
})
for _k, _v in TRANSLATIONS.items():
    if isinstance(_v, dict) and "nl" not in _v:
        _v["nl"] = _v.get("en", _k)
_TRANSLATION_PAIRS = _translation_pairs()
'''
    text = text.replace(main_marker, extra_i18n + '\n\n' + main_marker, 1)

    text = rep(
        text,
        'filetypes=[("Text files (*.txt)", "*.txt"), ("All files", "*.*")],',
        'filetypes=[(f"{tr(\'Text files\')} (*.txt)", "*.txt"), (tr("All files"), "*.*")],',
        'localized file chooser',
    )

    shortcut_darija = '''        "darija": (\n            "لائحة التحميلات\\n"\n            "Ctrl + A        اختار الكل\\n"\n            "Ctrl + Shift+A  حيد الاختيار كامل\\n"\n            "Delete          حيد المختار\\n"\n            "Enter           حل الملف اللي سالا\\n"\n            "Ctrl + Click    زيد/حيد سطر\\n"\n            "Shift + Click   اختار مجموعة\\n\\n"\n            "Pause / كمّل / Cancel كاينين حتى فالكليك باليمين "\n            "وفنوافذ Progress."\n        ),\n'''
    shortcut_nl = shortcut_darija + '''        "nl": (\n            "DOWNLOADLIJST\\n"\n            "Ctrl + A        Alles selecteren\\n"\n            "Ctrl + Shift+A  Alles deselecteren\\n"\n            "Delete          Selectie verwijderen\\n"\n            "Enter           Voltooid bestand openen\\n"\n            "Ctrl + Click    Rij toevoegen/verwijderen\\n"\n            "Shift + Click   Bereik selecteren\\n\\n"\n            "Pauzeren / Hervatten / Annuleren kan ook via rechtsklik "\n            "en via de voortgangsvensters."\n        ),\n'''
    text = rep(text, shortcut_darija, shortcut_nl, 'Dutch shortcuts body')

    about_darija = '''        "darija": (\n            "Z²SE Media Downloader\\n"\n            f"النسخة {APP_VERSION}\\n\\n"\n            "Browser Bridge + Smart HLS + FFmpeg + yt-dlp\\n"\n            "History محفوظ • Progress لكل تحميل بوحدو • تشغيل من المتصفح"\n        ),\n'''
    about_nl = about_darija + '''        "nl": (\n            "Z²SE Media Downloader\\n"\n            f"Versie {APP_VERSION}\\n\\n"\n            "Browser Bridge + Smart HLS + FFmpeg + yt-dlp\\n"\n            "Blijvende geschiedenis • Voortgang per download • Automatisch starten vanuit de browser"\n        ),\n'''
    text = rep(text, about_darija, about_nl, 'Dutch about body')

    text = text.replace('                "Show Download Progress",', '                tr("Show Download Progress"),', 1)
    text = text.replace('                "Open Main Z²SE",', '                tr("Open Main Z²SE"),', 1)
    text = text.replace('                "Pause All",', '                tr("Pause all"),', 1)
    text = text.replace('                "Resume All",', '                tr("Resume all"),', 1)
    text = text.replace('                "Cancel All Active",', '                tr("Cancel All Active"),', 1)
    text = text.replace('            "Z²SE Download Progress",', '            f"Z²SE • {tr(\'Progress\')}",', 1)

    text = text.replace('                "Show Progress",', '                tr("Show Progress"),', 1)
    text = text.replace('                "Open Main Z²SE",', '                tr("Open Main Z²SE"),', 1)
    text = text.replace('                "Pause",', '                tr("Pause"),', 1)
    text = text.replace('                "Resume",', '                tr("Resume"),', 1)
    text = text.replace('                "Cancel Download",', '                tr("Cancel Download"),', 1)

    text = rep(
        text,
        '    window.title(f"Z²SE — Download #{index}")',
        '    window.title(f"Z²SE — {tr(\'Download\')} #{index}")',
        'progress window title',
    )
    text = rep(
        text,
        '    title_var = tk.StringVar(value=f"Download #{index}")',
        '    title_var = tk.StringVar(value=f"{tr(\'Download\')} #{index}")',
        'progress title var',
    )
    text = rep(
        text,
        '''    outer = tk.Frame(\n        window,\n        bg="#ffffff",\n        highlightthickness=1,\n        highlightbackground="#cfd6e2",\n    )\n    outer.pack(fill="both", expand=True)\n''',
        '''    outer = tk.Frame(\n        window,\n        bg=UI_PANEL,\n        highlightthickness=1,\n        highlightbackground=UI_BORDER,\n    )\n    outer.pack(fill="both", expand=True, padx=10, pady=10)\n''',
        'progress outer card',
    )
    text = rep(
        text,
        '''    header = tk.Frame(\n        outer,\n        bg="#10294a",\n        height=38,\n    )\n''',
        '''    header = tk.Frame(\n        outer,\n        bg=UI_TOP,\n        height=50,\n    )\n''',
        'progress header',
    )
    text = text.replace('        bg="#10294a",', '        bg=UI_TOP,', 2)
    text = text.replace('        font=("Segoe UI", 10, "bold"),\n        fg="#ffffff",', '        font=("Segoe UI Semibold", 10),\n        fg=UI_TOP_TEXT,', 1)
    text = rep(
        text,
        '''    tk.Label(\n        header,\n        textvariable=percent_var,\n        font=("Segoe UI", 10, "bold"),\n        fg="#ffffff",\n        bg=UI_TOP,\n    ).pack(\n        side="right",\n        padx=12,\n    )\n''',
        '''    tk.Label(\n        header,\n        textvariable=percent_var,\n        font=("Segoe UI Semibold", 11),\n        fg="#ffffff",\n        bg=UI_ACCENT,\n        padx=10,\n        pady=4,\n    ).pack(\n        side="right",\n        padx=12,\n        pady=9,\n    )\n''',
        'progress percent badge',
    )
    text = text.replace('        bg="#ffffff",\n    )\n    body.pack(', '        bg=UI_PANEL,\n    )\n    body.pack(', 1)
    text = text.replace('        bg="#ffffff",\n        anchor="w",\n    ).pack(fill="x")', '        bg=UI_PANEL,\n        anchor="w",\n    ).pack(fill="x")', 2)
    text = text.replace('    stats = tk.Frame(body, bg="#ffffff")', '    stats = tk.Frame(body, bg=UI_PANEL)', 1)
    text = rep(
        text,
        '''        cell = tk.Frame(stats, bg="#ffffff")\n        cell.pack(side="left", padx=(0, 28))\n''',
        '''        cell = tk.Frame(\n            stats,\n            bg="#f7f9fc",\n            highlightthickness=1,\n            highlightbackground="#e2e7ef",\n        )\n        cell.pack(side="left", fill="x", expand=True, padx=(0, 7))\n''',
        'progress stat cards',
    )
    text = text.replace('            bg="#ffffff",\n        ).pack(anchor="w")', '            bg="#f7f9fc",\n        ).pack(anchor="w", padx=8, pady=(4, 0))', 1)
    text = text.replace('            bg="#ffffff",\n        ).pack(anchor="w")', '            bg="#f7f9fc",\n        ).pack(anchor="w", padx=8, pady=(0, 5))', 1)
    text = text.replace('    footer = tk.Frame(body, bg="#ffffff")', '    footer = tk.Frame(body, bg=UI_PANEL)', 1)

    required = (
        '"nl": (\n            "DOWNLOADLIJST',
        'tr("Show Download Progress")',
        'f"Z²SE • {tr(\'Progress\')}"',
        'window.title(f"Z²SE — {tr(\'Download\')} #{index}")',
        'bg=UI_ACCENT,',
        'highlightbackground="#e2e7ef"',
    )
    for marker in required:
        if marker not in text:
            raise RuntimeError(f"v32.44 extra sanity marker missing: {marker}")

    return text
