from pathlib import Path
import hashlib
import json
import re
import sys


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open('rb') as f:
        for block in iter(lambda: f.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def must_replace(text: str, old: str, new: str, label: str, count: int = 1) -> str:
    if old not in text:
        raise SystemExit(f'Patch marker not found: {label}')
    return text.replace(old, new, count)


version = sys.argv[1].strip()
if version != '32.43':
    raise SystemExit(f'This patch is for 32.43, got {version}')

payload = Path('payload')
app_path = payload / 'app.py'
updater_path = payload / 'z2se_updater.pyw'
text = app_path.read_text(encoding='utf-8')

# Version bump only; downloader engine logic stays untouched.
text = must_replace(text, 'APP_VERSION = "32.42"', 'APP_VERSION = "32.43"', 'version')
text = text.replace(
    '# MAIN UI — Z²SE V32.41 PRO DESIGN',
    '# MAIN UI — Z²SE V32.43 CONTENT POLISH',
    1,
)

# -----------------------------------------------------------------
# V32.43 — UI COPY & INFORMATION ARCHITECTURE
# Keep the same layout/engine, but make every visible label concise,
# consistent and professional in all four supported languages.
# -----------------------------------------------------------------
copy_updates = {
    'MEDIA DOWNLOADER': {
        'fr': 'TÉLÉCHARGEUR MULTIMÉDIA',
        'en': 'MEDIA DOWNLOADER',
        'ar': 'منزّل الوسائط',
        'darija': 'تحميل الوسائط',
    },
    'File': {'fr': 'Fichier', 'en': 'File', 'ar': 'ملف', 'darija': 'ملف'},
    'Downloads': {'fr': 'Téléchargements', 'en': 'Downloads', 'ar': 'التنزيلات', 'darija': 'التحميلات'},
    'Tools': {'fr': 'Outils', 'en': 'Tools', 'ar': 'الأدوات', 'darija': 'الأدوات'},
    'Language': {'fr': 'Langue', 'en': 'Language', 'ar': 'اللغة', 'darija': 'اللغة'},
    'Help': {'fr': 'Aide', 'en': 'Help', 'ar': 'مساعدة', 'darija': 'مساعدة'},
    '●  ENGINE READY': {'fr': '●  PRÊT', 'en': '●  READY', 'ar': '●  جاهز', 'darija': '●  واجد'},

    '＋  Add Link': {'fr': '＋  Ajouter', 'en': '＋  Add', 'ar': '＋  إضافة', 'darija': '＋  زيد'},
    'Paste Links': {'fr': 'Coller', 'en': 'Paste', 'ar': 'لصق', 'darija': 'لسّق'},
    '▶  Start': {'fr': '▶  Télécharger', 'en': '▶  Download', 'ar': '▶  تنزيل', 'darija': '▶  حمّل'},
    '■  Stop All': {'fr': '■  Tout arrêter', 'en': '■  Stop all', 'ar': '■  إيقاف الكل', 'darija': '■  وقف الكل'},
    'Ⅱ  Pause': {'fr': 'Ⅱ  Pause', 'en': 'Ⅱ  Pause', 'ar': 'Ⅱ  إيقاف مؤقت', 'darija': 'Ⅱ  وقف مؤقت'},
    '▶  Resume': {'fr': '▶  Reprendre', 'en': '▶  Resume', 'ar': '▶  استئناف', 'darija': '▶  كمّل'},
    'Open Folder': {'fr': 'Dossier', 'en': 'Folder', 'ar': 'المجلد', 'darija': 'الدوسي'},
    'Clear List': {'fr': 'Vider la liste', 'en': 'Clear list', 'ar': 'مسح القائمة', 'darija': 'خوي اللائحة'},
    'Clear Cache': {'fr': 'Vider le cache', 'en': 'Clear cache', 'ar': 'مسح الذاكرة المؤقتة', 'darija': 'خوي الكاش'},

    'NEW DOWNLOADS': {
        'fr': 'AJOUTER DES TÉLÉCHARGEMENTS',
        'en': 'ADD DOWNLOADS',
        'ar': 'إضافة تنزيلات',
        'darija': 'زيد تحميلات',
    },
    'From / To empty = full video': {
        'fr': 'Début et fin vides : vidéo entière',
        'en': 'Leave start and end empty for the full video',
        'ar': 'اترك البداية والنهاية فارغتين لتنزيل الفيديو كاملاً',
        'darija': 'خلي البداية والنهاية خاويين باش تحمل الفيديو كامل',
    },
    'From': {'fr': 'Début', 'en': 'Start', 'ar': 'البداية', 'darija': 'البداية'},
    'To': {'fr': 'Fin', 'en': 'End', 'ar': 'النهاية', 'darija': 'النهاية'},
    'Mode': {'fr': 'Mode', 'en': 'Mode', 'ar': 'الوضع', 'darija': 'الوضع'},
    'Format': {'fr': 'Format', 'en': 'Format', 'ar': 'الصيغة', 'darija': 'الفورما'},
    '+ Add': {'fr': '+ Ajouter une ligne', 'en': '+ Add row', 'ar': '+ إضافة سطر', 'darija': '+ زيد سطر'},
    'Paste': {'fr': 'Coller des liens', 'en': 'Paste links', 'ar': 'لصق الروابط', 'darija': 'لسّق الروابط'},
    'Load File': {'fr': 'Importer un fichier', 'en': 'Import file', 'ar': 'استيراد ملف', 'darija': 'دخل ملف'},
    'Clear': {'fr': 'Effacer', 'en': 'Clear', 'ar': 'مسح', 'darija': 'مسح'},
    'Quality': {'fr': 'Qualité', 'en': 'Quality', 'ar': 'الجودة', 'darija': 'الجودة'},
    'Parallel': {'fr': 'Simultanés', 'en': 'Concurrent', 'ar': 'متزامنة', 'darija': 'فـ نفس الوقت'},
    'DOWNLOAD': {'fr': 'TÉLÉCHARGER', 'en': 'DOWNLOAD', 'ar': 'تنزيل', 'darija': 'حمّل'},

    'DOWNLOADS': {'fr': 'TÉLÉCHARGEMENTS', 'en': 'DOWNLOADS', 'ar': 'التنزيلات', 'darija': 'التحميلات'},
    'Deselect': {'fr': 'Tout désélectionner', 'en': 'Deselect all', 'ar': 'إلغاء تحديد الكل', 'darija': 'حيد الاختيار كامل'},
    'Select All': {'fr': 'Tout sélectionner', 'en': 'Select all', 'ar': 'تحديد الكل', 'darija': 'اختار الكل'},
    'File / Video': {'fr': 'Fichier', 'en': 'File', 'ar': 'الملف', 'darija': 'الملف'},
    'Type': {'fr': 'Type', 'en': 'Type', 'ar': 'النوع', 'darija': 'النوع'},
    'Progress': {'fr': 'Progression', 'en': 'Progress', 'ar': 'التقدم', 'darija': 'التقدم'},
    'Transfer rate': {'fr': 'Vitesse', 'en': 'Speed', 'ar': 'السرعة', 'darija': 'السرعة'},
    'Time left': {'fr': 'Restant', 'en': 'Remaining', 'ar': 'المتبقي', 'darija': 'الباقي'},
    'Size': {'fr': 'Taille', 'en': 'Size', 'ar': 'الحجم', 'darija': 'الحجم'},
    'Status': {'fr': 'État', 'en': 'Status', 'ar': 'الحالة', 'darija': 'الحالة'},

    'Add new row': {'fr': 'Ajouter une ligne', 'en': 'Add row', 'ar': 'إضافة سطر', 'darija': 'زيد سطر'},
    'Paste links': {'fr': 'Coller des liens', 'en': 'Paste links', 'ar': 'لصق الروابط', 'darija': 'لسّق الروابط'},
    'Load links file…': {'fr': 'Importer une liste…', 'en': 'Import link list…', 'ar': 'استيراد قائمة روابط…', 'darija': 'دخل لائحة ديال الروابط…'},
    'Open Downloads folder': {'fr': 'Ouvrir le dossier des téléchargements', 'en': 'Open Downloads folder', 'ar': 'فتح مجلد التنزيلات', 'darija': 'حل دوسي التحميلات'},
    'Open Z²SE app folder': {'fr': 'Ouvrir le dossier de Z²SE', 'en': 'Open Z²SE folder', 'ar': 'فتح مجلد Z²SE', 'darija': 'حل دوسي Z²SE'},
    'Hide main window to tray': {'fr': 'Réduire dans la zone de notification', 'en': 'Minimize to tray', 'ar': 'تصغير إلى منطقة الإشعارات', 'darija': 'صغّر حدا الساعة'},
    'Quit Z²SE': {'fr': 'Quitter Z²SE', 'en': 'Quit Z²SE', 'ar': 'إغلاق Z²SE', 'darija': 'سد Z²SE'},

    'Start downloads': {'fr': 'Démarrer les téléchargements', 'en': 'Start downloads', 'ar': 'بدء التنزيلات', 'darija': 'بدا التحميلات'},
    'Pause all': {'fr': 'Tout mettre en pause', 'en': 'Pause all', 'ar': 'إيقاف الكل مؤقتاً', 'darija': 'وقف الكل مؤقت'},
    'Resume all': {'fr': 'Tout reprendre', 'en': 'Resume all', 'ar': 'استئناف الكل', 'darija': 'كمّل الكل'},
    'Stop all': {'fr': 'Tout arrêter', 'en': 'Stop all', 'ar': 'إيقاف الكل', 'darija': 'وقف الكل'},
    'Select all': {'fr': 'Tout sélectionner', 'en': 'Select all', 'ar': 'تحديد الكل', 'darija': 'اختار الكل'},
    'Deselect all': {'fr': 'Tout désélectionner', 'en': 'Deselect all', 'ar': 'إلغاء تحديد الكل', 'darija': 'حيد الاختيار كامل'},
    'Delete selected…': {'fr': 'Supprimer la sélection…', 'en': 'Delete selected…', 'ar': 'حذف المحدد…', 'darija': 'مسح المختار…'},
    'Clear finished/history list': {'fr': 'Vider les éléments terminés', 'en': 'Clear finished items', 'ar': 'مسح العناصر المكتملة', 'darija': 'خوي اللي سالاو'},

    'Health Check': {'fr': 'Diagnostic système', 'en': 'System diagnostics', 'ar': 'تشخيص النظام', 'darija': 'تشخيص النظام'},
    'Check updates now': {'fr': 'Rechercher les mises à jour', 'en': 'Check for updates', 'ar': 'البحث عن تحديثات', 'darija': 'قلب على التحديثات'},
    'Update download engine': {'fr': 'Mettre à jour le moteur de téléchargement', 'en': 'Update download engine', 'ar': 'تحديث محرك التنزيل', 'darija': 'حدّث موتور التحميل'},
    'Clear Turbo cache': {'fr': 'Vider le cache Turbo', 'en': 'Clear Turbo cache', 'ar': 'مسح ذاكرة Turbo المؤقتة', 'darija': 'خوي كاش Turbo'},
    'Show / Hide technical log': {'fr': 'Afficher / masquer le journal technique', 'en': 'Show / hide technical log', 'ar': 'إظهار / إخفاء السجل التقني', 'darija': 'بيّن / خبي اللوغ التقني'},
    'Open Chrome Extensions': {'fr': 'Ouvrir les extensions Chrome', 'en': 'Open Chrome extensions', 'ar': 'فتح إضافات Chrome', 'darija': 'حل إضافات Chrome'},
    'Open stable V15 extension folder': {'fr': 'Ouvrir le dossier de l’extension V15', 'en': 'Open V15 extension folder', 'ar': 'فتح مجلد إضافة V15', 'darija': 'حل دوسي Extension V15'},
    'Keyboard shortcuts': {'fr': 'Raccourcis clavier', 'en': 'Keyboard shortcuts', 'ar': 'اختصارات لوحة المفاتيح', 'darija': 'اختصارات الكلافي'},
    'Chrome extension setup': {'fr': 'Configurer l’extension Chrome', 'en': 'Set up Chrome extension', 'ar': 'إعداد إضافة Chrome', 'darija': 'وجد Extension ديال Chrome'},
    'About Z²SE': {'fr': 'À propos de Z²SE', 'en': 'About Z²SE', 'ar': 'حول Z²SE', 'darija': 'على Z²SE'},
}

marker = '# ============================================================\n# MAIN UI'
idx = text.find(marker)
if idx < 0:
    raise SystemExit('MAIN UI marker not found')
block = '\n# V32.43 copy hierarchy overrides\nTRANSLATIONS.update(' + repr(copy_updates) + ')\n\n'
text = text[:idx] + block + text[idx:]

# The cache action already exists in Tools. Remove the duplicate toolbar
# button so the main command bar only contains everyday actions.
cache_button = '''ttk.Button(\n    toolbar_inner,\n    text=tr("Clear Cache"),\n    command=clear_turbo_cache,\n    style="Toolbar.TButton",\n).pack(side="left", padx=5)\n'''
if cache_button in text:
    text = text.replace(cache_button, '', 1)
else:
    print('Note: toolbar cache button marker not found; continuing safely')

# Reduce visual noise in the section helper text without touching behavior.
text = text.replace(
    'editor_title.pack(fill="x", padx=14, pady=(12, 7))',
    'editor_title.pack(fill="x", padx=14, pady=(12, 8))',
    1,
)

app_path.write_text(text, encoding='utf-8')

files = []
for rel in ('app.py', 'z2se_updater.pyw'):
    p = payload / rel
    if not p.is_file():
        raise SystemExit(f'Missing payload file: {rel}')
    files.append({
        'path': rel,
        'sha256': sha256(p),
        'size': p.stat().st_size,
    })

manifest = {
    'product': 'Z2SE Media Downloader',
    'version': version,
    'created_by': 'GitHub Actions / ChatGPT release patch',
    'files': files,
}
(payload / 'update_manifest.json').write_text(
    json.dumps(manifest, indent=2, ensure_ascii=False),
    encoding='utf-8',
)

print(f'Prepared Z2SE v{version} — UI copy & information architecture polish')
