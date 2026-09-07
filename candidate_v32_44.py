import os
import sys
import ctypes
import re
import json
import hashlib
import shutil
import subprocess
import threading
import time
import zipfile
import tkinter as tk
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse, parse_qs, urlsplit, urlunsplit, urljoin
from datetime import datetime, timedelta
from queue import Queue, Empty
from tkinter import ttk, messagebox, filedialog

# Optional system-tray support.
# Install once with:
#   python -m pip install pystray pillow
try:
    import pystray
    from PIL import Image, ImageDraw, ImageTk
    TRAY_AVAILABLE = True
except Exception:
    pystray = None
    Image = None
    ImageDraw = None
    TRAY_AVAILABLE = False

# ============================================================
# PATHS — V32.29 EXE READY
# ============================================================

APP_NAME = "Z²SE Media Downloader"
APP_SHORT_NAME = "Z²SE"
APP_VERSION = "32.44"

IS_COMPILED = (
    "__compiled__" in globals()
    or getattr(
        sys,
        "frozen",
        False,
    )
)

# Where the launched EXE/app.py physically lives.
PROGRAM_DIR = os.path.dirname(
    os.path.abspath(
        sys.argv[0]
        if sys.argv
        else __file__
    )
)

# During the first Nuitka standalone test the EXE lives in:
#   E:\\download videos\\APP\\Z2SE.dist\\Z2SE.exe
# Keep ALL persistent app files in the normal APP folder.
if (
    PROGRAM_DIR.lower().endswith(
        ".dist"
    )
    and os.path.basename(
        os.path.dirname(
            PROGRAM_DIR
        )
    ).lower() == "app"
):
    APP_DIR = os.path.dirname(
        PROGRAM_DIR
    )
else:
    APP_DIR = PROGRAM_DIR

BASE_DIR = os.path.dirname(
    APP_DIR
)

# Bundled images live beside __file__ in standalone/onefile extraction.
BUNDLE_DIR = os.path.dirname(
    os.path.abspath(
        __file__
    )
)

def resource_path(filename):
    return os.path.join(
        BUNDLE_DIR,
        filename,
    )

# ============================================================
# V32.31 — MULTI-LANGUAGE UI
# ============================================================

LANGUAGE_CONFIG_FILE = os.path.join(APP_DIR, "z2se_language.json")
LANGUAGE_LABELS = {
    "fr": "Français",
    "en": "English",
    "ar": "العربية",
    "darija": "الدارجة المغربية",
    "nl": "Nederlands",
}
DEFAULT_LANGUAGE = "fr"

TRANSLATIONS = {'File': {'fr': 'Fichier', 'en': 'File', 'ar': 'ملف', 'darija': 'ملف'}, 'Downloads': {'fr': 'Téléchargements', 'en': 'Downloads', 'ar': 'التنزيلات', 'darija': 'التحميلات'}, 'Tools': {'fr': 'Outils', 'en': 'Tools', 'ar': 'أدوات', 'darija': 'الأدوات'}, 'Help': {'fr': 'Aide', 'en': 'Help', 'ar': 'مساعدة', 'darija': 'المساعدة'}, 'Language': {'fr': 'Langue', 'en': 'Language', 'ar': 'اللغة', 'darija': 'اللغة'}, 'Add new row': {'fr': 'Ajouter une ligne', 'en': 'Add new row', 'ar': 'إضافة سطر', 'darija': 'زيد سطر'}, 'Paste links': {'fr': 'Coller les liens', 'en': 'Paste links', 'ar': 'لصق الروابط', 'darija': 'لسّق الروابط'}, 'Load links file…': {'fr': 'Charger un fichier de liens…', 'en': 'Load links file…', 'ar': 'تحميل ملف الروابط…', 'darija': 'دخل ملف الروابط…'}, 'Open Downloads folder': {'fr': 'Ouvrir le dossier Téléchargements', 'en': 'Open Downloads folder', 'ar': 'فتح مجلد التنزيلات', 'darija': 'حل دوسي التحميلات'}, 'Open Z²SE app folder': {'fr': 'Ouvrir le dossier Z²SE', 'en': 'Open Z²SE app folder', 'ar': 'فتح مجلد Z²SE', 'darija': 'حل دوسي Z²SE'}, 'Hide main window to tray': {'fr': 'Réduire dans la zone de notification', 'en': 'Hide main window to tray', 'ar': 'إخفاء النافذة في شريط النظام', 'darija': 'خبي النافذة حد الساعة'}, 'Quit Z²SE': {'fr': 'Quitter Z²SE', 'en': 'Quit Z²SE', 'ar': 'الخروج من Z²SE', 'darija': 'خرج من Z²SE'}, 'Start downloads': {'fr': 'Démarrer les téléchargements', 'en': 'Start downloads', 'ar': 'بدء التنزيلات', 'darija': 'بدا التحميلات'}, 'Pause all': {'fr': 'Tout mettre en pause', 'en': 'Pause all', 'ar': 'إيقاف الكل مؤقتًا', 'darija': 'وقف الكل مؤقتاً'}, 'Resume all': {'fr': 'Tout reprendre', 'en': 'Resume all', 'ar': 'استئناف الكل', 'darija': 'كمّل الكل'}, 'Stop all': {'fr': 'Tout arrêter', 'en': 'Stop all', 'ar': 'إيقاف الكل', 'darija': 'حبس الكل'}, 'Select all': {'fr': 'Tout sélectionner', 'en': 'Select all', 'ar': 'تحديد الكل', 'darija': 'اختار الكل'}, 'Deselect all': {'fr': 'Tout désélectionner', 'en': 'Deselect all', 'ar': 'إلغاء تحديد الكل', 'darija': 'حيد الاختيار كامل'}, 'Delete selected…': {'fr': 'Supprimer la sélection…', 'en': 'Delete selected…', 'ar': 'حذف المحدد…', 'darija': 'حيد المختار…'}, 'Clear finished/history list': {'fr': 'Vider la liste / l’historique', 'en': 'Clear finished/history list', 'ar': 'مسح القائمة والسجل', 'darija': 'مسح اللائحة والهيستوري'}, 'Check Z²SE updates': {'fr': 'Rechercher les mises à jour Z²SE', 'en': 'Check Z²SE updates', 'ar': 'البحث عن تحديثات Z²SE', 'darija': 'قلب على تحديثات Z²SE'}, 'Update settings': {'fr': 'Paramètres de mise à jour', 'en': 'Update settings', 'ar': 'إعدادات التحديث', 'darija': 'إعدادات التحديث'}, 'Update download engine': {'fr': 'Mettre à jour le moteur', 'en': 'Update download engine', 'ar': 'تحديث محرك التنزيل', 'darija': 'حدّث موتور التحميل'}, 'Clear Turbo cache': {'fr': 'Vider le cache Turbo', 'en': 'Clear Turbo cache', 'ar': 'مسح ذاكرة Turbo', 'darija': 'مسح Turbo Cache'}, 'Show / Hide technical log': {'fr': 'Afficher / masquer le journal technique', 'en': 'Show / Hide technical log', 'ar': 'إظهار / إخفاء السجل التقني', 'darija': 'بيّن / خبي اللوغ التقني'}, 'Open Chrome Extensions': {'fr': 'Ouvrir les extensions Chrome', 'en': 'Open Chrome Extensions', 'ar': 'فتح إضافات Chrome', 'darija': 'حل إضافات Chrome'}, 'Open stable V15 extension folder': {'fr': 'Ouvrir le dossier Extension V15', 'en': 'Open stable V15 extension folder', 'ar': 'فتح مجلد إضافة V15', 'darija': 'حل دوسي Extension V15'}, 'Keyboard shortcuts': {'fr': 'Raccourcis clavier', 'en': 'Keyboard shortcuts', 'ar': 'اختصارات لوحة المفاتيح', 'darija': 'اختصارات الكلافي'}, 'Chrome extension setup': {'fr': 'Configuration de l’extension Chrome', 'en': 'Chrome extension setup', 'ar': 'إعداد إضافة Chrome', 'darija': 'إعداد Extension ديال Chrome'}, 'About Z²SE': {'fr': 'À propos de Z²SE', 'en': 'About Z²SE', 'ar': 'حول Z²SE', 'darija': 'على Z²SE'}, 'MEDIA DOWNLOADER': {'fr': 'TÉLÉCHARGEUR MULTIMÉDIA', 'en': 'MEDIA DOWNLOADER', 'ar': 'منزّل الوسائط', 'darija': 'تحميل الفيديو والصوت'}, '●  ENGINE READY': {'fr': '●  MOTEUR PRÊT', 'en': '●  ENGINE READY', 'ar': '●  المحرك جاهز', 'darija': '●  الموتور واجد'}, '＋  Add Link': {'fr': '＋  Ajouter un lien', 'en': '＋  Add Link', 'ar': '＋  إضافة رابط', 'darija': '＋  زيد رابط'}, 'Paste Links': {'fr': 'Coller les liens', 'en': 'Paste Links', 'ar': 'لصق الروابط', 'darija': 'لسّق الروابط'}, '▶  Start': {'fr': '▶  Démarrer', 'en': '▶  Start', 'ar': '▶  بدء', 'darija': '▶  بدا'}, '■  Stop All': {'fr': '■  Tout arrêter', 'en': '■  Stop All', 'ar': '■  إيقاف الكل', 'darija': '■  حبس الكل'}, 'Ⅱ  Pause': {'fr': 'Ⅱ  Pause', 'en': 'Ⅱ  Pause', 'ar': 'Ⅱ  إيقاف مؤقت', 'darija': 'Ⅱ  وقف مؤقت'}, '▶  Resume': {'fr': '▶  Reprendre', 'en': '▶  Resume', 'ar': '▶  استئناف', 'darija': '▶  كمّل'}, 'Open Folder': {'fr': 'Ouvrir le dossier', 'en': 'Open Folder', 'ar': 'فتح المجلد', 'darija': 'حل الدوسي'}, 'Clear List': {'fr': 'Vider la liste', 'en': 'Clear List', 'ar': 'مسح القائمة', 'darija': 'مسح اللائحة'}, 'Clear Cache': {'fr': 'Vider le cache', 'en': 'Clear Cache', 'ar': 'مسح الذاكرة المؤقتة', 'darija': 'مسح الكاش'}, 'Check Updates': {'fr': 'Mises à jour', 'en': 'Check Updates', 'ar': 'التحديثات', 'darija': 'التحديثات'}, 'Download': {'fr': 'Télécharger', 'en': 'Download', 'ar': 'تنزيل', 'darija': 'حمّل'}, 'CATEGORIES': {'fr': 'CATÉGORIES', 'en': 'CATEGORIES', 'ar': 'الفئات', 'darija': 'الأقسام'}, 'QUICK ACTIONS': {'fr': 'ACTIONS RAPIDES', 'en': 'QUICK ACTIONS', 'ar': 'إجراءات سريعة', 'darija': 'اختصارات سريعة'}, 'All Downloads': {'fr': 'Tous les téléchargements', 'en': 'All Downloads', 'ar': 'كل التنزيلات', 'darija': 'التحميلات كاملين'}, 'Downloading': {'fr': 'Téléchargement', 'en': 'Downloading', 'ar': 'جارٍ التنزيل', 'darija': 'كيتحمّل'}, 'Finished': {'fr': 'Terminés', 'en': 'Finished', 'ar': 'مكتملة', 'darija': 'سالاو'}, 'Video  •  MP4': {'fr': 'Vidéo  •  MP4', 'en': 'Video  •  MP4', 'ar': 'فيديو  •  MP4', 'darija': 'فيديو  •  MP4'}, 'Audio  •  MP3': {'fr': 'Audio  •  MP3', 'en': 'Audio  •  MP3', 'ar': 'صوت  •  MP3', 'darija': 'صوت  •  MP3'}, 'Partial Downloads': {'fr': 'Extraits vidéo', 'en': 'Partial Downloads', 'ar': 'تنزيل أجزاء الفيديو', 'darija': 'أجزاء من الفيديو'}, 'Open Downloads': {'fr': 'Ouvrir Téléchargements', 'en': 'Open Downloads', 'ar': 'فتح التنزيلات', 'darija': 'حل التحميلات'}, 'Update yt-dlp': {'fr': 'Mettre à jour yt-dlp', 'en': 'Update yt-dlp', 'ar': 'تحديث yt-dlp', 'darija': 'حدّث yt-dlp'}, 'Browser Bridge': {'fr': 'Bridge navigateur', 'en': 'Browser Bridge', 'ar': 'جسر المتصفح', 'darija': 'Bridge ديال المتصفح'}, 'System Tray': {'fr': 'Zone de notification', 'en': 'System Tray', 'ar': 'شريط النظام', 'darija': 'الأيقونة حد الساعة'}, '●  ACTIVE': {'fr': '●  ACTIF', 'en': '●  ACTIVE', 'ar': '●  نشط', 'darija': '●  خدام'}, 'NEW DOWNLOADS': {'fr': 'NOUVEAUX TÉLÉCHARGEMENTS', 'en': 'NEW DOWNLOADS', 'ar': 'تنزيلات جديدة', 'darija': 'تحميلات جديدة'}, 'From / To empty = full video': {'fr': 'Début / Fin vides = vidéo complète', 'en': 'From / To empty = full video', 'ar': 'ترك من / إلى فارغين = الفيديو كامل', 'darija': 'خلي من / حتى خاويين = الفيديو كامل'}, 'From': {'fr': 'Début', 'en': 'From', 'ar': 'من', 'darija': 'من'}, 'To': {'fr': 'Fin', 'en': 'To', 'ar': 'إلى', 'darija': 'حتى'}, 'Mode': {'fr': 'Mode', 'en': 'Mode', 'ar': 'الوضع', 'darija': 'المود'}, 'Format': {'fr': 'Format', 'en': 'Format', 'ar': 'الصيغة', 'darija': 'الفورما'}, '+ Add': {'fr': '+ Ajouter', 'en': '+ Add', 'ar': '+ إضافة', 'darija': '+ زيد'}, 'Paste': {'fr': 'Coller', 'en': 'Paste', 'ar': 'لصق', 'darija': 'لسّق'}, 'Load File': {'fr': 'Charger un fichier', 'en': 'Load File', 'ar': 'تحميل ملف', 'darija': 'دخل ملف'}, 'Clear': {'fr': 'Effacer', 'en': 'Clear', 'ar': 'مسح', 'darija': 'مسح'}, 'Quality': {'fr': 'Qualité', 'en': 'Quality', 'ar': 'الجودة', 'darija': 'الجودة'}, 'Parallel': {'fr': 'Parallèle', 'en': 'Parallel', 'ar': 'متوازٍ', 'darija': 'مع بعض'}, 'All:': {'fr': 'Tous :', 'en': 'All:', 'ar': 'الكل:', 'darija': 'الكل:'}, 'Apply': {'fr': 'Appliquer', 'en': 'Apply', 'ar': 'تطبيق', 'darija': 'طبّق'}, 'DOWNLOAD': {'fr': 'TÉLÉCHARGER', 'en': 'DOWNLOAD', 'ar': 'تنزيل', 'darija': 'حمّل'}, 'DOWNLOADS': {'fr': 'TÉLÉCHARGEMENTS', 'en': 'DOWNLOADS', 'ar': 'التنزيلات', 'darija': 'التحميلات'}, 'Deselect': {'fr': 'Désélectionner', 'en': 'Deselect', 'ar': 'إلغاء التحديد', 'darija': 'حيد الاختيار'}, 'Select All': {'fr': 'Tout sélectionner', 'en': 'Select All', 'ar': 'تحديد الكل', 'darija': 'اختار الكل'}, 'File / Video': {'fr': 'Fichier / Vidéo', 'en': 'File / Video', 'ar': 'الملف / الفيديو', 'darija': 'الملف / الفيديو'}, 'Type': {'fr': 'Type', 'en': 'Type', 'ar': 'النوع', 'darija': 'النوع'}, 'Progress': {'fr': 'Progression', 'en': 'Progress', 'ar': 'التقدم', 'darija': 'التقدم'}, 'Transfer rate': {'fr': 'Vitesse', 'en': 'Transfer rate', 'ar': 'سرعة النقل', 'darija': 'السرعة'}, 'Time left': {'fr': 'Temps restant', 'en': 'Time left', 'ar': 'الوقت المتبقي', 'darija': 'الوقت الباقي'}, 'Size': {'fr': 'Taille', 'en': 'Size', 'ar': 'الحجم', 'darija': 'الحجم'}, 'Status': {'fr': 'État', 'en': 'Status', 'ar': 'الحالة', 'darija': 'الحالة'}, 'Main Window': {'fr': 'Fenêtre principale', 'en': 'Main Window', 'ar': 'النافذة الرئيسية', 'darija': 'النافذة الرئيسية'}, 'Cancel Download': {'fr': 'Annuler le téléchargement', 'en': 'Cancel Download', 'ar': 'إلغاء التنزيل', 'darija': 'حبس التحميل'}, 'Resume': {'fr': 'Reprendre', 'en': 'Resume', 'ar': 'استئناف', 'darija': 'كمّل'}, 'Pause': {'fr': 'Pause', 'en': 'Pause', 'ar': 'إيقاف مؤقت', 'darija': 'وقف مؤقت'}, 'Open file': {'fr': 'Ouvrir le fichier', 'en': 'Open file', 'ar': 'فتح الملف', 'darija': 'حل الملف'}, 'Show in folder': {'fr': 'Afficher dans le dossier', 'en': 'Show in folder', 'ar': 'إظهار في المجلد', 'darija': 'بيّن فالدوسي'}, 'Pause selected': {'fr': 'Mettre la sélection en pause', 'en': 'Pause selected', 'ar': 'إيقاف المحدد مؤقتًا', 'darija': 'وقف المختار مؤقتاً'}, 'Resume selected': {'fr': 'Reprendre la sélection', 'en': 'Resume selected', 'ar': 'استئناف المحدد', 'darija': 'كمّل المختار'}, 'Cancel selected': {'fr': 'Annuler la sélection', 'en': 'Cancel selected', 'ar': 'إلغاء المحدد', 'darija': 'حبس المختار'}, 'Copy file name(s)': {'fr': 'Copier le(s) nom(s)', 'en': 'Copy file name(s)', 'ar': 'نسخ أسماء الملفات', 'darija': 'كوبي سميات الملفات'}, 'Copy full path(s)': {'fr': 'Copier le(s) chemin(s)', 'en': 'Copy full path(s)', 'ar': 'نسخ المسارات الكاملة', 'darija': 'كوبي المسارات كاملين'}, 'Properties': {'fr': 'Propriétés', 'en': 'Properties', 'ar': 'الخصائص', 'darija': 'الخصائص'}, 'Remove selected from list (keep files)': {'fr': 'Retirer de la liste (garder les fichiers)', 'en': 'Remove selected from list (keep files)', 'ar': 'إزالة من القائمة مع الاحتفاظ بالملفات', 'darija': 'حيد من اللائحة وخلي الملفات'}, 'Delete selected file(s) from PC (Recycle Bin)': {'fr': 'Supprimer du PC (Corbeille)', 'en': 'Delete selected file(s) from PC (Recycle Bin)', 'ar': 'حذف من الكمبيوتر (سلة المحذوفات)', 'darija': 'حيد من PC للسلة'}, 'Delete selected download': {'fr': 'Supprimer le téléchargement sélectionné', 'en': 'Delete selected download', 'ar': 'حذف التنزيل المحدد', 'darija': 'حيد التحميل المختار'}, 'Remove from list only': {'fr': 'Retirer de la liste seulement', 'en': 'Remove from list only', 'ar': 'إزالة من القائمة فقط', 'darija': 'حيد غير من اللائحة'}, 'Delete file + list': {'fr': 'Supprimer le fichier + la ligne', 'en': 'Delete file + list', 'ar': 'حذف الملف + السطر', 'darija': 'حيد الملف + السطر'}, 'Cancel': {'fr': 'Annuler', 'en': 'Cancel', 'ar': 'إلغاء', 'darija': 'رجع'}, 'TECHNICAL LOG': {'fr': 'JOURNAL TECHNIQUE', 'en': 'TECHNICAL LOG', 'ar': 'السجل التقني', 'darija': 'اللوغ التقني'}, 'Show Log': {'fr': 'Afficher le journal', 'en': 'Show Log', 'ar': 'إظهار السجل', 'darija': 'بيّن اللوغ'}, 'Hide Log': {'fr': 'Masquer le journal', 'en': 'Hide Log', 'ar': 'إخفاء السجل', 'darija': 'خبي اللوغ'}, 'Z²SE Update Settings': {'fr': 'Paramètres de mise à jour Z²SE', 'en': 'Z²SE Update Settings', 'ar': 'إعدادات تحديث Z²SE', 'darija': 'إعدادات تحديث Z²SE'}, 'GitHub owner': {'fr': 'Propriétaire GitHub', 'en': 'GitHub owner', 'ar': 'مالك GitHub', 'darija': 'GitHub owner'}, 'Update repository': {'fr': 'Dépôt de mise à jour', 'en': 'Update repository', 'ar': 'مستودع التحديث', 'darija': 'Repo ديال التحديث'}, 'Check automatically': {'fr': 'Vérifier automatiquement', 'en': 'Check automatically', 'ar': 'التحقق تلقائيًا', 'darija': 'قلب على التحديث بوحدو'}, 'Install automatically when idle': {'fr': 'Installer automatiquement quand Z²SE est inactif', 'en': 'Install automatically when idle', 'ar': 'التثبيت تلقائيًا عند عدم وجود تنزيلات', 'darija': 'ركّب التحديث بوحدو ملي ما كاين حتى تحميل'}, 'Save': {'fr': 'Enregistrer', 'en': 'Save', 'ar': 'حفظ', 'darija': 'حفظ'}, 'Ready': {'fr': 'Prêt', 'en': 'Ready', 'ar': 'جاهز', 'darija': 'واجد'}, 'Waiting': {'fr': 'En attente', 'en': 'Waiting', 'ar': 'في الانتظار', 'darija': 'كيتسنى'}, 'Done ✅': {'fr': 'Terminé ✅', 'en': 'Done ✅', 'ar': 'مكتمل ✅', 'darija': 'سالا ✅'}, 'Stopped': {'fr': 'Arrêté', 'en': 'Stopped', 'ar': 'متوقف', 'darija': 'محبوس'}, 'Paused': {'fr': 'En pause', 'en': 'Paused', 'ar': 'متوقف مؤقتًا', 'darija': 'واقف مؤقتاً'}, 'Interrupted': {'fr': 'Interrompu', 'en': 'Interrupted', 'ar': 'تمت مقاطعته', 'darija': 'تقطع'}, 'Saved': {'fr': 'Enregistré', 'en': 'Saved', 'ar': 'محفوظ', 'darija': 'محفوظ'}, 'Error': {'fr': 'Erreur', 'en': 'Error', 'ar': 'خطأ', 'darija': 'خطأ'}, 'Analyzing…': {'fr': 'Analyse…', 'en': 'Analyzing…', 'ar': 'جارٍ التحليل…', 'darija': 'كيحلل…'}, 'Downloading...': {'fr': 'Téléchargement en cours…', 'en': 'Downloading...', 'ar': 'جارٍ التنزيل…', 'darija': 'كيتحمّل…'}, 'Download completed ✅': {'fr': 'Téléchargement terminé ✅', 'en': 'Download completed ✅', 'ar': 'اكتمل التنزيل ✅', 'darija': 'التحميل سالا ✅'}, 'Download failed ❌': {'fr': 'Échec du téléchargement ❌', 'en': 'Download failed ❌', 'ar': 'فشل التنزيل ❌', 'darija': 'التحميل فشل ❌'}, 'Download stopped': {'fr': 'Téléchargement arrêté', 'en': 'Download stopped', 'ar': 'تم إيقاف التنزيل', 'darija': 'التحميل تحبس'}, 'Download paused ⏸': {'fr': 'Téléchargement en pause ⏸', 'en': 'Download paused ⏸', 'ar': 'التنزيل متوقف مؤقتًا ⏸', 'darija': 'التحميل واقف مؤقتاً ⏸'}, 'Update': {'fr': 'Mise à jour', 'en': 'Update', 'ar': 'تحديث', 'darija': 'تحديث'}, 'Time': {'fr': 'Temps', 'en': 'Time', 'ar': 'الوقت', 'darija': 'الوقت'}, 'Links': {'fr': 'Liens', 'en': 'Links', 'ar': 'الروابط', 'darija': 'الروابط'}, 'Clipboard': {'fr': 'Presse-papiers', 'en': 'Clipboard', 'ar': 'الحافظة', 'darija': 'Clipboard'}, 'Files': {'fr': 'Fichiers', 'en': 'Files', 'ar': 'الملفات', 'darija': 'الملفات'}, 'Cache': {'fr': 'Cache', 'en': 'Cache', 'ar': 'الذاكرة المؤقتة', 'darija': 'الكاش'}, 'Turbo Cache': {'fr': 'Cache Turbo', 'en': 'Turbo Cache', 'ar': 'ذاكرة Turbo', 'darija': 'Turbo Cache'}, 'Multiple URLs': {'fr': 'Plusieurs URL', 'en': 'Multiple URLs', 'ar': 'روابط متعددة', 'darija': 'روابط بزاف'}, 'Language saved': {'fr': 'Langue enregistrée', 'en': 'Language saved', 'ar': 'تم حفظ اللغة', 'darija': 'اللغة تحفظات'}, 'Restart now to apply the new language?': {'fr': 'Redémarrer Z²SE maintenant pour appliquer la nouvelle langue ?', 'en': 'Restart now to apply the new language?', 'ar': 'هل تريد إعادة تشغيل Z²SE الآن لتطبيق اللغة الجديدة؟', 'darija': 'نبداو Z²SE من جديد دابا باش تتبدل اللغة؟'}, 'Language saved. Restart Z²SE after the active downloads finish.': {'fr': 'Langue enregistrée. Redémarrez Z²SE après la fin des téléchargements en cours.', 'en': 'Language saved. Restart Z²SE after the active downloads finish.', 'ar': 'تم حفظ اللغة. أعد تشغيل Z²SE بعد انتهاء التنزيلات الحالية.', 'darija': 'اللغة تحفظات. منين يساليو التحميلات اللي خدامين عاود شعل Z²SE.'}, 'Wait for downloads to finish before clearing cache.': {'fr': 'Attendez la fin des téléchargements avant de vider le cache.', 'en': 'Wait for downloads to finish before clearing cache.', 'ar': 'انتظر انتهاء التنزيلات قبل مسح الذاكرة المؤقتة.', 'darija': 'خلي التحميلات يساليو قبل ما تمسح الكاش.'}, 'Turbo Cache cleared ✅': {'fr': 'Cache Turbo vidé ✅', 'en': 'Turbo Cache cleared ✅', 'ar': 'تم مسح ذاكرة Turbo ✅', 'darija': 'Turbo Cache تمسح ✅'}, 'A download is already running.': {'fr': 'Un téléchargement est déjà en cours.', 'en': 'A download is already running.', 'ar': 'يوجد تنزيل قيد التشغيل.', 'darija': 'راه كاين تحميل خدام.'}, 'yt-dlp is updating. Please wait.': {'fr': 'yt-dlp est en cours de mise à jour. Patientez.', 'en': 'yt-dlp is updating. Please wait.', 'ar': 'يجري تحديث yt-dlp. يرجى الانتظار.', 'darija': 'yt-dlp كيتحدّث، تسنى شوية.'}, 'Enter the video URL.': {'fr': 'Entrez l’URL de la vidéo.', 'en': 'Enter the video URL.', 'ar': 'أدخل رابط الفيديو.', 'darija': 'دخل رابط الفيديو.'}, 'Enter start and end times.': {'fr': 'Entrez le début et la fin.', 'en': 'Enter start and end times.', 'ar': 'أدخل وقت البداية والنهاية.', 'darija': 'دخل وقت البداية والنهاية.'}, 'End time must be after start time.': {'fr': 'La fin doit être après le début.', 'en': 'End time must be after start time.', 'ar': 'يجب أن يكون وقت النهاية بعد البداية.', 'darija': 'وقت النهاية خاصو يكون من بعد البداية.'}, 'Add at least one link.': {'fr': 'Ajoutez au moins un lien.', 'en': 'Add at least one link.', 'ar': 'أضف رابطًا واحدًا على الأقل.', 'darija': 'زيد على الأقل رابط واحد.'}, 'Nothing found in the clipboard.': {'fr': 'Aucun lien trouvé dans le presse-papiers.', 'en': 'Nothing found in the clipboard.', 'ar': 'لم يتم العثور على شيء في الحافظة.', 'darija': 'ما لقيت والو فالـClipboard.'}, 'Enter both From and To.': {'fr': 'Renseignez Début et Fin.', 'en': 'Enter both From and To.', 'ar': 'أدخل من وإلى معًا.', 'darija': 'دخل From و To بجوج.'}, 'To must be after From.': {'fr': 'La fin doit être après le début.', 'en': 'To must be after From.', 'ar': 'يجب أن تكون النهاية بعد البداية.', 'darija': 'To خاصو يكون من بعد From.'}, 'Wait for downloads to finish before clearing the list.': {'fr': 'Attendez la fin des téléchargements avant de vider la liste.', 'en': 'Wait for downloads to finish before clearing the list.', 'ar': 'انتظر انتهاء التنزيلات قبل مسح القائمة.', 'darija': 'خلي التحميلات يساليو قبل ما تمسح اللائحة.'}, 'Stopping downloads...': {'fr': 'Arrêt des téléchargements…', 'en': 'Stopping downloads...', 'ar': 'جارٍ إيقاف التنزيلات…', 'darija': 'كيحبس التحميلات…'}, 'Z²SE is still running in the background. Click the tray icon to reopen it.': {'fr': 'Z²SE fonctionne toujours en arrière-plan. Cliquez sur son icône près de l’horloge pour le rouvrir.', 'en': 'Z²SE is still running in the background. Click the tray icon to reopen it.', 'ar': 'لا يزال Z²SE يعمل في الخلفية. انقر على أيقونته في شريط النظام لإعادة فتحه.', 'darija': 'Z²SE باقي خدام فالخلفية. كليكي على الأيقونة حد الساعة باش تحلو.'}, 'Update settings saved ✅': {'fr': 'Paramètres de mise à jour enregistrés ✅', 'en': 'Update settings saved ✅', 'ar': 'تم حفظ إعدادات التحديث ✅', 'darija': 'إعدادات التحديث تحفظو ✅'}, 'Update could not be completed:': {'fr': 'La mise à jour n’a pas pu être terminée :', 'en': 'Update could not be completed:', 'ar': 'تعذر إكمال التحديث:', 'darija': 'التحديث ما قدرش يكمل:'}, 'Update failed, but rollback restored the previous version ✅': {'fr': 'La mise à jour a échoué, mais la version précédente a été restaurée ✅', 'en': 'Update failed, but rollback restored the previous version ✅', 'ar': 'فشل التحديث، لكن تمت استعادة النسخة السابقة ✅', 'darija': 'التحديث فشل ولكن Rollback رجع النسخة القديمة ✅'}, 'A new version is available, but a download is active.': {'fr': 'Une nouvelle version est disponible, mais un téléchargement est en cours.', 'en': 'A new version is available, but a download is active.', 'ar': 'يتوفر إصدار جديد، لكن يوجد تنزيل قيد التشغيل.', 'darija': 'كاينة نسخة جديدة ولكن كاين تحميل خدام.'}, 'Check for updates again after the download finishes.': {'fr': 'Relancez la recherche de mises à jour après la fin du téléchargement.', 'en': 'Check for updates again after the download finishes.', 'ar': 'تحقق من التحديثات بعد انتهاء التنزيل.', 'darija': 'منين يسالي التحميل عاود قلب على التحديثات.'}, 'You already have the latest version ✅': {'fr': 'Vous avez déjà la dernière version ✅', 'en': 'You already have the latest version ✅', 'ar': 'لديك أحدث إصدار بالفعل ✅', 'darija': 'راه عندك آخر نسخة دابا ✅'}, 'A new version is available ✅': {'fr': 'Une nouvelle version est disponible ✅', 'en': 'A new version is available ✅', 'ar': 'يتوفر إصدار جديد ✅', 'darija': 'كاينة نسخة جديدة ✅'}, 'Download and install it now?': {'fr': 'La télécharger et l’installer maintenant ?', 'en': 'Download and install it now?', 'ar': 'هل تريد تنزيلها وتثبيتها الآن؟', 'darija': 'نحمّلوها ونركبوها دابا؟'}, 'Final file not found.': {'fr': 'Fichier final introuvable.', 'en': 'Final file not found.', 'ar': 'تعذر العثور على الملف النهائي.', 'darija': 'الملف النهائي ما تلقاش.'}, 'No file path found for the current selection.': {'fr': 'Aucun chemin de fichier trouvé pour la sélection.', 'en': 'No file path found for the current selection.', 'ar': 'لم يتم العثور على مسار ملف للتحديد الحالي.', 'darija': 'ما لقيت حتى file path فالاختيار الحالي.'}, 'This download is still active. Stop it before deleting.': {'fr': 'Ce téléchargement est encore actif. Arrêtez-le avant de le supprimer.', 'en': 'This download is still active. Stop it before deleting.', 'ar': 'لا يزال هذا التنزيل نشطًا. أوقفه قبل الحذف.', 'darija': 'هاد التحميل مازال خدام. حبسو قبل ما تحيدو.'}, 'Could not delete the file:': {'fr': 'Impossible de supprimer le fichier :', 'en': 'Could not delete the file:', 'ar': 'تعذر حذف الملف:', 'darija': 'ما قدرناش نحيدو الملف:'}, 'The file will be moved to the Recycle Bin:': {'fr': 'Le fichier sera déplacé vers la Corbeille :', 'en': 'The file will be moved to the Recycle Bin:', 'ar': 'سيتم نقل الملف إلى سلة المحذوفات:', 'darija': 'الملف غادي يمشي لـRecycle Bin:'}, 'Continue?': {'fr': 'Continuer ?', 'en': 'Continue?', 'ar': 'هل تريد المتابعة؟', 'darija': 'نكملو؟'}, 'Live Queue finished ✅ ': {'fr': 'File d’attente terminée ✅ ', 'en': 'Live Queue finished ✅ ', 'ar': 'اكتملت قائمة الانتظار ✅ ', 'darija': 'Live Queue سالات ✅ '}, 'Live Queue downloads: ': {'fr': 'Téléchargements en file : ', 'en': 'Live Queue downloads: ', 'ar': 'تنزيلات قائمة الانتظار: ', 'darija': 'تحميلات Live Queue: '}, 'Browser downloads: ': {'fr': 'Téléchargements navigateur : ', 'en': 'Browser downloads: ', 'ar': 'تنزيلات المتصفح: ', 'darija': 'تحميلات المتصفح: '}, 'Browser downloads finished ✅ ': {'fr': 'Téléchargements navigateur terminés ✅ ', 'en': 'Browser downloads finished ✅ ', 'ar': 'اكتملت تنزيلات المتصفح ✅ ', 'darija': 'تحميلات المتصفح سالاو ✅ '}, 'Downloads finished ✅ ': {'fr': 'Téléchargements terminés ✅ ', 'en': 'Downloads finished ✅ ', 'ar': 'اكتملت التنزيلات ✅ ', 'darija': 'التحميلات سالاو ✅ '}}

TRANSLATIONS.update({
    "Delete download": {
        "fr": "Supprimer le téléchargement",
        "en": "Delete download",
        "ar": "حذف التنزيل",
        "darija": "حيد التحميل",
    },
    "Delete selected files": {
        "fr": "Supprimer les fichiers sélectionnés",
        "en": "Delete selected files",
        "ar": "حذف الملفات المحددة",
        "darija": "حيد الملفات المختارين",
    },
    "Remove selected": {
        "fr": "Retirer la sélection",
        "en": "Remove selected",
        "ar": "إزالة المحدد",
        "darija": "حيد المختار",
    },
    "This download is still active. Stop or cancel it before deleting.": {
        "fr": "Ce téléchargement est encore actif. Arrêtez-le ou annulez-le avant de le supprimer.",
        "en": "This download is still active. Stop or cancel it before deleting.",
        "ar": "لا يزال هذا التنزيل نشطًا. أوقفه أو ألغِه قبل الحذف.",
        "darija": "هاد التحميل مازال خدام. حبسو ولا Cancel قبل ما تحيدو.",
    },
    "One or more selected downloads are still active. Stop or cancel them first.": {
        "fr": "Un ou plusieurs téléchargements sélectionnés sont encore actifs. Arrêtez-les ou annulez-les d’abord.",
        "en": "One or more selected downloads are still active. Stop or cancel them first.",
        "ar": "لا يزال تنزيل واحد أو أكثر من المحددات نشطًا. أوقفها أو ألغها أولًا.",
        "darija": "كاين شي تحميل من المختارين مازال خدام. حبسو ولا Cancel قبل.",
    },
    "What do you want to delete?": {
        "fr": "Que voulez-vous supprimer ?",
        "en": "What do you want to delete?",
        "ar": "ماذا تريد أن تحذف؟",
        "darija": "شنو بغيتي تحيد؟",
    },
    "The real file was not found. File deletion is unavailable.": {
        "fr": "Le fichier réel est introuvable. La suppression du fichier n’est pas disponible.",
        "en": "The real file was not found. File deletion is unavailable.",
        "ar": "لم يتم العثور على الملف الحقيقي. حذف الملف غير متاح.",
        "darija": "الملف الحقيقي ما تلقاش. حذف الملف ما متاحش.",
    },
})

TRANSLATIONS.update({
    "Check updates now": {
        "fr": "Rechercher les mises à jour maintenant",
        "en": "Check for updates now",
        "ar": "البحث عن التحديثات الآن",
        "darija": "قلب على التحديثات دابا",
    },
})

TRANSLATIONS.update({
    "Health Check": {
        "fr": "Diagnostic système",
        "en": "Health Check",
        "ar": "فحص النظام",
        "darija": "فحص النظام",
    },
    "Smart repair": {
        "fr": "Réparation intelligente",
        "en": "Smart repair",
        "ar": "إصلاح ذكي",
        "darija": "إصلاح ذكي",
    },
    "Refresh": {
        "fr": "Actualiser",
        "en": "Refresh",
        "ar": "تحديث الفحص",
        "darija": "عاود الفحص",
    },
    "Close": {
        "fr": "Fermer",
        "en": "Close",
        "ar": "إغلاق",
        "darija": "سد",
    },
    "All essential components are ready.": {
        "fr": "Tous les composants essentiels sont prêts.",
        "en": "All essential components are ready.",
        "ar": "جميع المكونات الأساسية جاهزة.",
        "darija": "المكونات المهمة كاملين واجدين.",
    },
    "Some components need attention.": {
        "fr": "Certains composants nécessitent votre attention.",
        "en": "Some components need attention.",
        "ar": "بعض المكونات تحتاج إلى الانتباه.",
        "darija": "كاين شي مكونات خاصها تتصلح.",
    },
})

LEGACY_UI_ALIASES = {'جاهز': 'Ready', 'جاري التحميل...': 'Downloading...', 'جاري تحميل الفيديو...': 'Downloading...', 'تم التحميل ✅': 'Download completed ✅', 'التحميل سالا بنجاح ✅': 'Download completed ✅', 'التحميل فشل ❌': 'Download failed ❌', 'فشل التحميل ❌': 'Download failed ❌', 'تم إيقاف التحميل': 'Download stopped', 'التحميل متوقف مؤقتاً ⏸': 'Download paused ⏸', 'شنو بغيتي تحيد؟': 'Delete selected download', 'الملف الحقيقي ما تلقاش دابا؛ لذلك Delete file + list معطلة.': 'Delete file + list', 'خلي التحميلات تسالي قبل ما تمسح Cache.': 'Wait for downloads to finish before clearing cache.', 'Turbo Cache تمسح ✅': 'Turbo Cache cleared ✅', 'هاد Single download راه خدام دابا.': 'A download is already running.', 'yt-dlp كيدير update دابا. تسنى شوية.': 'yt-dlp is updating. Please wait.', 'دخل رابط الفيديو.': 'Enter the video URL.', 'دخل وقت البداية والنهاية.': 'Enter start and end times.', 'وقت النهاية خاصو يكون من بعد وقت البداية.': 'End time must be after start time.', 'زيد على الأقل رابط واحد.': 'Add at least one link.', 'ما لقيت والو فالـClipboard.': 'Nothing found in the clipboard.', 'دخل From و To بجوج.': 'Enter both From and To.', 'وقت To خاصو يكون من بعد From.': 'To must be after From.', 'خلي التحميلات اللي خدامين يساليو قبل ما تمسح اللائحة.': 'Wait for downloads to finish before clearing the list.', 'إيقاف التحميلات...': 'Stopping downloads...', 'مازال خدام فالخلفية. كليكي على الأيقونة حد الساعة باش تحلو.': 'Z²SE is still running in the background. Click the tray icon to reopen it.', 'Update settings محفوظين ✅': 'Update settings saved ✅', 'Update ما قدرش يكمل:': 'Update could not be completed:', 'Update فشلات ولكن Rollback رجع النسخة القديمة بنجاح ✅': 'Update failed, but rollback restored the previous version ✅', 'كاينة نسخة جديدة ولكن كاين download خدام.': 'A new version is available, but a download is active.', 'منين يسالي التحميل عاود Check Updates.': 'Check for updates again after the download finishes.', 'راه عندك آخر نسخة دابا ✅': 'You already have the latest version ✅', 'كاينة نسخة جديدة ✅': 'A new version is available ✅', 'نحمّلها ونركبها دابا؟': 'Download and install it now?', 'الملف النهائي ما لقيتوش دابا.': 'Final file not found.', 'ما لقيت حتى file path فالاختيار الحالي.': 'No file path found for the current selection.', 'هاد التحميل مازال خدام. دير Cancel/Stop قبل Delete.': 'This download is still active. Stop it before deleting.', 'ما قدرناش نحيدو الملف:': 'Could not delete the file:', 'غادي يتحيد الملف من الدوسي ويتحط فـ Recycle Bin:': 'The file will be moved to the Recycle Bin:', 'واش نكمل؟': 'Continue?', 'Live Queue سالات ✅ ': 'Live Queue finished ✅ ', 'تحميلات Live Queue: ': 'Live Queue downloads: ', 'تحميلات المتصفح: ': 'Browser downloads: ', 'تحميلات المتصفح سالاو ✅ ': 'Browser downloads finished ✅ ', 'التحميلات سالاو ✅ ': 'Downloads finished ✅ '}


def _load_language():
    try:
        if os.path.isfile(LANGUAGE_CONFIG_FILE):
            with open(LANGUAGE_CONFIG_FILE, "r", encoding="utf-8") as handle:
                payload = json.load(handle)
            code = str(payload.get("language", "")).strip().lower()
            if code in LANGUAGE_LABELS:
                return code
    except Exception:
        pass
    return DEFAULT_LANGUAGE


CURRENT_LANGUAGE = _load_language()


def _save_language(code):
    code = str(code or "").strip().lower()
    if code not in LANGUAGE_LABELS:
        return False
    try:
        with open(LANGUAGE_CONFIG_FILE, "w", encoding="utf-8") as handle:
            json.dump({"language": code}, handle, indent=2, ensure_ascii=False)
        return True
    except Exception:
        return False


def tr(key, language=None):
    key = str(key)
    code = language if language in LANGUAGE_LABELS else CURRENT_LANGUAGE
    item = TRANSLATIONS.get(key)
    if not isinstance(item, dict):
        return key
    return str(item.get(code, item.get("en", key)))


def _translation_pairs():
    pairs = []
    for canonical, variants in TRANSLATIONS.items():
        candidates = {str(canonical)}
        if isinstance(variants, dict):
            candidates.update(str(v) for v in variants.values() if v)
        for candidate in candidates:
            pairs.append((candidate, canonical))
    for source, canonical in LEGACY_UI_ALIASES.items():
        pairs.append((str(source), str(canonical)))
    pairs.sort(key=lambda p: len(p[0]), reverse=True)
    return pairs


_TRANSLATION_PAIRS = _translation_pairs()


def tr_dynamic(value):
    if value is None:
        return value
    raw = str(value)
    for source, canonical in _TRANSLATION_PAIRS:
        if raw == source:
            return tr(canonical)
    result = raw
    for source, canonical in _TRANSLATION_PAIRS:
        if len(source) >= 4 and source in result:
            target = tr(canonical)
            if source != target:
                result = result.replace(source, target)
    return result


_STATUS_KEYS = (
    "Waiting", "Downloading", "Done ✅", "Stopped",
    "Paused", "Interrupted", "Saved", "Error", "Analyzing…"
)


def canonical_status(value):
    raw = str(value or "").strip()
    low = raw.lower()
    for canonical in _STATUS_KEYS:
        variants = {canonical}
        item = TRANSLATIONS.get(canonical, {})
        if isinstance(item, dict):
            variants.update(item.values())
        for candidate in variants:
            candidate = str(candidate).strip()
            if candidate and low.startswith(candidate.lower()):
                return canonical
    if low.startswith("done"):
        return "Done ✅"
    if low.startswith("error"):
        return "Error"
    if low.startswith(("stop", "cancel")):
        return "Stopped"
    if low.startswith("pause"):
        return "Paused"
    if low.startswith("interrupted"):
        return "Interrupted"
    if low.startswith("saved"):
        return "Saved"
    if low.startswith(("waiting", "queued")):
        return "Waiting"
    if low.startswith(("downloading", "starting")):
        return "Downloading"
    return raw

BRAND_LOGO = resource_path("z2se_logo.png")
BRAND_ICON_PNG = resource_path("z2se_icon.png")
BRAND_ICON_ICO = resource_path("z2se.ico")

YTDLP = os.path.join(BASE_DIR, "yt-dlp.exe")

LOCAL_FFMPEG = os.path.join(BASE_DIR, "ffmpeg.exe")
LOCAL_FFPROBE = os.path.join(BASE_DIR, "ffprobe.exe")

DOWNLOADS = os.path.join(BASE_DIR, "downloads")
CACHE_DIR = os.path.join(DOWNLOADS, "_video_cache")
LIENS_TXT = os.path.join(BASE_DIR, "liens.txt")

UPDATE_STATE = os.path.join(APP_DIR, "update_state.json")
APP_UPDATE_CONFIG_FILE = os.path.join(APP_DIR, "z2se_update_config.json")
APP_UPDATE_STATE_FILE = os.path.join(APP_DIR, "z2se_app_update_state.json")
APP_UPDATE_RESULT_FILE = os.path.join(APP_DIR, "last_update_result.json")
APP_BINARY_FILE = os.path.join(APP_DIR, "Z2SE.exe")
APP_UPDATER_EXE = os.path.join(APP_DIR, "Z2SE_Updater.exe")
APP_UPDATER_PY = os.path.join(APP_DIR, "z2se_updater.pyw")
APP_UPDATE_STAGING = os.path.join(APP_DIR, "_update_staging")
APP_UPDATE_ASSET_DEFAULT = "Z2SE_UPDATE.zip"
DOWNLOAD_HISTORY_FILE = os.path.join(APP_DIR, "download_history.json")

USERPROFILE = os.environ.get("USERPROFILE", "")

POT_PLUGIN = os.path.join(
    USERPROFILE,
    "yt-dlp-plugins",
    "bgutil-ytdlp-pot-provider.zip"
)

POT_SERVER_FILE = os.path.join(
    USERPROFILE,
    "bgutil-ytdlp-pot-provider",
    "server",
    "src",
    "main.ts"
)

POT_WORKDIR = os.path.join(
    USERPROFILE,
    "bgutil-ytdlp-pot-provider",
    "server",
    "node_modules"
)

POT_PING_URL = "http://127.0.0.1:4416/ping"

BRIDGE_HOST = "127.0.0.1"
BRIDGE_PORT = 8765
BRIDGE_URL = f"http://{BRIDGE_HOST}:{BRIDGE_PORT}"

# Started by the tiny browser launcher: keep the full manager hidden.
BROWSER_LAUNCH_MODE = "--browser-launch" in sys.argv

# ============================================================
# SINGLE INSTANCE
# ============================================================
# Clicking the Desktop shortcut again must NOT create a second
# Z²SE process / taskbar icon. Instead, restore the existing app.

_SINGLE_INSTANCE_MUTEX = None
ERROR_ALREADY_EXISTS = 183


def _focus_existing_z2se_window():
    """Best-effort restore/focus of the already running Z²SE window."""
    if os.name != "nt":
        return

    try:
        user32 = ctypes.windll.user32

        hwnd = user32.FindWindowW(None, APP_NAME)

        if hwnd:
            # 9 = SW_RESTORE
            user32.ShowWindow(hwnd, 9)
            user32.SetForegroundWindow(hwnd)
            return
    except Exception:
        pass

    # Fallback through the local bridge, useful if the Tk window
    # is hidden in the tray.
    for _ in range(5):
        try:
            with urllib.request.urlopen(
                BRIDGE_URL + "/focus",
                timeout=0.35,
            ):
                return
        except Exception:
            time.sleep(0.12)


def ensure_single_instance():
    global _SINGLE_INSTANCE_MUTEX

    if os.name != "nt":
        return

    try:
        kernel32 = ctypes.windll.kernel32

        _SINGLE_INSTANCE_MUTEX = kernel32.CreateMutexW(
            None,
            False,
            "Local\\Z2SE_Media_Downloader_Single_Instance",
        )

        if kernel32.GetLastError() == ERROR_ALREADY_EXISTS:
            _focus_existing_z2se_window()
            raise SystemExit(0)

    except SystemExit:
        raise

    except Exception:
        # Never prevent the app from starting merely because
        # Windows mutex creation failed unexpectedly.
        pass


ensure_single_instance()

os.makedirs(DOWNLOADS, exist_ok=True)
os.makedirs(CACHE_DIR, exist_ok=True)


# ============================================================
# WORKING FFMPEG / FFPROBE RESOLVER
# ============================================================

def _tool_runs(path):
    if not path:
        return False

    try:
        result = subprocess.run(
            [path, "-version"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            timeout=8,
            creationflags=(
                subprocess.CREATE_NO_WINDOW
                if os.name == "nt"
                else 0
            ),
        )
        return result.returncode == 0

    except Exception:
        return False


def resolve_working_tool(command_name, local_candidate):
    """
    Prefer the Windows-installed FFmpeg/FFprobe (winget PATH entry).
    Fall back to the old local exe only if it is actually executable.

    This specifically avoids WinError 4551 when Windows Application
    Control blocks the old downloaded ffmpeg.exe beside the project.
    """
    candidates = []

    # 1) System / winget installation from PATH
    system_path = shutil.which(command_name)
    if system_path:
        candidates.append(system_path)

    # 2) Old project-local binary as fallback only
    if local_candidate:
        candidates.append(local_candidate)

    seen = set()

    for candidate in candidates:
        try:
            candidate = os.path.abspath(candidate)
        except Exception:
            pass

        key = os.path.normcase(str(candidate))

        if key in seen:
            continue

        seen.add(key)

        if _tool_runs(candidate):
            return candidate

    return None


FFMPEG = resolve_working_tool("ffmpeg", LOCAL_FFMPEG)
FFPROBE = resolve_working_tool("ffprobe", LOCAL_FFPROBE)

FFMPEG_DIR = (
    os.path.dirname(FFMPEG)
    if FFMPEG
    else BASE_DIR
)


# ============================================================
# GLOBALS
# ============================================================

pot_ready = False
pot_lock = threading.Lock()

update_in_progress = False
update_lock = threading.Lock()

app_update_in_progress = False
app_update_lock = threading.Lock()
app_update_pending = False

# V32.36 — VIDEO MERGER
merge_running = False
merge_cancel_event = threading.Event()
merge_process_lock = threading.Lock()
merge_current_process = None

single_running = False
bulk_running = False

stop_all_event = threading.Event()

# V32.4: Pause/Resume is independent from Cancel/Stop.
pause_all_event = threading.Event()
paused_process_ids = set()
paused_process_ids_lock = threading.Lock()

active_processes = set()
active_processes_lock = threading.Lock()

# V32.13 — every download owns its own runtime/process group.
job_runtime_context = threading.local()
process_job_map = {}
process_job_map_lock = threading.Lock()

cancelled_job_indices = set()
cancelled_job_lock = threading.Lock()

paused_job_indices = set()
paused_job_processes = {}
paused_job_lock = threading.Lock()

bulk_done = 0
bulk_total = 0
bulk_count_lock = threading.Lock()

last_repair_time = 0.0
repair_lock = threading.Lock()

# V32.42 — Smart Recovery keeps an error profile per worker thread.
download_error_context = threading.local()

# Same-video parts can arrive at the same time in Bulk mode.
# Only the first worker downloads the cache; the rest reuse it.
cache_locks_guard = threading.Lock()
cache_locks = {}

# ============================================================
# APP
# ============================================================

root = tk.Tk()
root.title(APP_NAME)
root.geometry("1280x860")
root.minsize(1020, 720)

# ============================================================
# Z²SE V24 — CLEAN PROFESSIONAL UI
# Inspired by the efficient desktop-download-manager layout:
# compact toolbar, dominant download list, restrained colors.
# ============================================================

# V32.41 — PRO DESIGN SYSTEM
# Windows 11 / modern download-manager inspired visual language.
UI_BG = "#f3f6fb"
UI_PANEL = "#ffffff"
UI_PANEL_SOFT = "#f8fafc"
UI_BORDER = "#dfe5ee"
UI_BORDER_STRONG = "#cfd8e6"
UI_TEXT = "#101828"
UI_MUTED = "#667085"
UI_ACCENT = "#2563eb"
UI_ACCENT_DARK = "#1d4ed8"
UI_ACCENT_SOFT = "#eaf2ff"
UI_SUCCESS = "#12b76a"
UI_DANGER = "#d92d20"
UI_WARNING = "#dc8a00"
UI_TOP = "#0f172a"
UI_TOP_SOFT = "#1e293b"
UI_TOP_TEXT = "#f8fafc"
UI_TOP_MUTED = "#aebbd0"
UI_SIDEBAR = "#edf1f6"

root.configure(bg=UI_BG)

style = ttk.Style(root)
try:
    style.theme_use("clam")
except Exception:
    pass

style.configure(
    "Z2SE.TFrame",
    background=UI_BG,
)
style.configure(
    "Panel.TFrame",
    background=UI_PANEL,
)
style.configure(
    "Sidebar.TFrame",
    background=UI_SIDEBAR,
)
style.configure(
    "Toolbar.TButton",
    font=("Segoe UI", 9),
    padding=(12, 8),
    foreground=UI_TEXT,
    background=UI_PANEL_SOFT,
    bordercolor=UI_BORDER_STRONG,
    relief="flat",
)
style.map(
    "Toolbar.TButton",
    background=[("active", "#eef4ff"), ("pressed", UI_ACCENT_SOFT)],
    foreground=[("disabled", "#98a2b3"), ("active", UI_TEXT)],
)
style.configure(
    "Primary.TButton",
    font=("Segoe UI Semibold", 9),
    padding=(16, 9),
    foreground="#ffffff",
    background=UI_ACCENT,
    bordercolor=UI_ACCENT,
    relief="flat",
)
style.map(
    "Primary.TButton",
    background=[("active", UI_ACCENT_DARK), ("pressed", "#1e40af")],
    foreground=[("disabled", "#dbe7ff"), ("active", "#ffffff")],
)
style.configure(
    "Danger.TButton",
    font=("Segoe UI", 9),
    padding=(12, 8),
    foreground="#b42318",
    background="#fff5f4",
    bordercolor="#fecdca",
    relief="flat",
)
style.map(
    "Danger.TButton",
    background=[("active", "#fee4e2"), ("pressed", "#fecdca")],
    foreground=[("disabled", "#b8bfc9"), ("active", "#912018")],
)
style.configure(
    "Ghost.TButton",
    font=("Segoe UI", 8),
    padding=(9, 5),
    foreground="#344054",
    background=UI_PANEL,
    bordercolor=UI_BORDER,
    relief="flat",
)
style.map(
    "Ghost.TButton",
    background=[("active", UI_PANEL_SOFT), ("pressed", UI_ACCENT_SOFT)],
)
style.configure(
    "Remove.TButton",
    font=("Segoe UI", 9),
    padding=(5, 4),
    foreground="#98a2b3",
    background=UI_PANEL,
    bordercolor=UI_PANEL,
    relief="flat",
)
style.map(
    "Remove.TButton",
    background=[("active", "#fff1f0")],
    foreground=[("active", UI_DANGER)],
)
style.configure(
    "Panel.TLabel",
    background=UI_PANEL,
    foreground=UI_TEXT,
    font=("Segoe UI", 9),
)
style.configure(
    "Field.TEntry",
    font=("Segoe UI", 9),
    padding=(9, 7),
    fieldbackground="#ffffff",
    foreground=UI_TEXT,
    bordercolor=UI_BORDER_STRONG,
    lightcolor=UI_BORDER_STRONG,
    darkcolor=UI_BORDER_STRONG,
    insertcolor=UI_TEXT,
)
style.map(
    "Field.TEntry",
    bordercolor=[("focus", UI_ACCENT)],
    lightcolor=[("focus", UI_ACCENT)],
    darkcolor=[("focus", UI_ACCENT)],
)
style.configure(
    "Field.TCombobox",
    font=("Segoe UI", 9),
    padding=(7, 5),
    fieldbackground="#ffffff",
    foreground=UI_TEXT,
    background="#ffffff",
    bordercolor=UI_BORDER_STRONG,
    arrowcolor="#475467",
)
style.map(
    "Field.TCombobox",
    bordercolor=[("focus", UI_ACCENT)],
    fieldbackground=[("readonly", "#ffffff")],
    foreground=[("readonly", UI_TEXT)],
)
style.configure(
    "Field.TSpinbox",
    font=("Segoe UI", 9),
    padding=(7, 5),
    fieldbackground="#ffffff",
    foreground=UI_TEXT,
    bordercolor=UI_BORDER_STRONG,
    arrowcolor="#475467",
)
style.configure(
    "Z2SE.Treeview",
    rowheight=33,
    font=("Segoe UI", 9),
    background="#ffffff",
    fieldbackground="#ffffff",
    foreground=UI_TEXT,
    bordercolor=UI_BORDER,
    relief="flat",
)
style.configure(
    "Z2SE.Treeview.Heading",
    font=("Segoe UI Semibold", 9),
    background="#f4f7fb",
    foreground="#344054",
    relief="flat",
    padding=(8, 9),
    bordercolor=UI_BORDER,
)
style.map(
    "Z2SE.Treeview",
    background=[("selected", UI_ACCENT_SOFT)],
    foreground=[("selected", "#123a72")],
)
style.map(
    "Z2SE.Treeview.Heading",
    background=[("active", "#edf3fb")],
)
style.configure(
    "Z2SE.Horizontal.TProgressbar",
    troughcolor="#e9eef5",
    background=UI_ACCENT,
    lightcolor=UI_ACCENT,
    darkcolor=UI_ACCENT,
    bordercolor="#e9eef5",
    thickness=7,
)
style.configure(
    "Z2SE.Vertical.TScrollbar",
    troughcolor=UI_PANEL,
    background="#c8d2df",
    bordercolor=UI_PANEL,
    arrowcolor="#667085",
)

# Z²SE Windows/app icon
try:
    if os.path.isfile(BRAND_ICON_ICO):
        root.iconbitmap(BRAND_ICON_ICO)
except Exception:
    pass

try:
    if os.path.isfile(BRAND_ICON_PNG):
        _brand_window_icon = tk.PhotoImage(file=BRAND_ICON_PNG)
        root.iconphoto(True, _brand_window_icon)
except Exception:
    _brand_window_icon = None

status_var = tk.StringVar(value=tr("Ready"))
pot_status_var = tk.StringVar(value="PO Token: checking...")
update_status_var = tk.StringVar(value="yt-dlp: checking...")
fast_status_var = tk.StringVar(
    value=(
        f"v{APP_VERSION} • {LANGUAGE_LABELS.get(CURRENT_LANGUAGE, CURRENT_LANGUAGE)}"
        " • LIVE QUEUE • PART AUTO"
    )
)

single_progress_var = tk.DoubleVar(value=0)
bulk_progress_var = tk.DoubleVar(value=0)
bulk_counter_var = tk.StringVar(value="0 / 0")
selected_rows_var = tk.StringVar(value="")
language_var = tk.StringVar(value=CURRENT_LANGUAGE)

single_url_var = tk.StringVar()
single_quality_var = tk.StringVar(value="1080p")
single_mode_var = tk.StringVar(value="full")
single_start_var = tk.StringVar()
single_end_var = tk.StringVar()

bulk_quality_var = tk.StringVar(value="1080p")
bulk_workers_var = tk.IntVar(value=4)

bulk_tree_ids = {}
bulk_job_progress = {}

# V32.21 — exact relationship between a visible history row and the REAL
# downloaded file. This removes fuzzy guessing from Open/Delete operations.
row_file_paths = {}
job_output_paths = {}
job_output_paths_lock = threading.Lock()

# V32.22 — once a real title is discovered, never downgrade it later to
# "Browser Video", "chunks", "manifest", etc.
job_best_titles = {}
job_best_titles_lock = threading.Lock()

single_stats_var = tk.StringVar(value="")

# V15 editable Multiple-URLs rows
bulk_editor_rows = []
bulk_same_from_var = tk.StringVar()
bulk_same_to_var = tk.StringVar()

# V20: browser downloads are a real queue.
# Every click from the extension becomes its own visible job.
browser_queue_active = False
browser_job_counter = 0
browser_jobs_total = 0
browser_jobs_done = 0
browser_jobs_pending = 0
browser_active_jobs = 0
browser_worker_limit = 4
browser_queue_lock = threading.Lock()
browser_queue_condition = threading.Condition(browser_queue_lock)

# V32.30 — UNIVERSAL LIVE QUEUE
# One real concurrency limit shared by manual FULL/PART, browser jobs and
# the legacy single-download panel. New jobs can be added while others run.
live_queue_lock = threading.Lock()
live_queue_condition = threading.Condition(live_queue_lock)
live_active_jobs = 0
live_worker_limit = 4

# Manual editor queue counters. "bulk_running" now means there is at least
# one manual editor job waiting/running, not that one immutable batch owns
# the whole app.
manual_jobs_pending = 0
manual_jobs_done = 0
manual_jobs_total = 0

# Runtime job IDs must never collide when a second batch is added while the
# first one is still active.
live_job_counter_lock = threading.Lock()

bridge_status_var = tk.StringVar(value="Browser Bridge: starting...")
tray_status_var = tk.StringVar(
    value="Tray: starting..." if TRAY_AVAILABLE else "Tray: install pystray + pillow"
)
bridge_server = None
tray_icon = None
mini_tray_icon = None
mini_tray_thread_started = False
first_tray_notice = True
app_quitting = False

# V32.2 — small IDM-style floating download window.
mini_panel = None
mini_panel_session = 0
mini_panel_user_opened_main = False
mini_panel_user_hidden = False
mini_panel_in_tray = False
mini_panel_completion_after = None
mini_pause_button = None
mini_resume_button = None
main_pause_button = None
main_resume_button = None


# ============================================================
# V32.21 — EXACT OUTPUT FILE TRACKING + CLEAN TITLES
# ============================================================

_BIDI_CONTROL_RE = re.compile(
    r"[\u200e\u200f\u202a-\u202e\u2066-\u2069]"
)


def clean_video_title(value, page_url=""):
    """
    Turn browser/tab/extractor titles into one clean video title.

    Handles titles such as:
      " | | First Day of School | YouTube"
      "BabyBus Arabic | First Day of School | YouTube"
    without keeping empty separators / browser-site decoration.
    """
    raw = str(value or "")

    raw = _BIDI_CONTROL_RE.sub(
        "",
        raw,
    )

    raw = raw.replace(
        "\u00a0",
        " ",
    )

    raw = re.sub(
        r"\s+",
        " ",
        raw,
    ).strip()

    # Strip obvious browser/site decoration on either end.
    site_names = (
        r"YouTube|Facebook|Instagram|TikTok|Forja|Vimeo|Dailymotion|"
        r"Twitch|X|Twitter"
    )

    raw = re.sub(
        rf"^\s*(?:{site_names})\s*(?:[|¦•·–—-]+\s*)+",
        "",
        raw,
        flags=re.IGNORECASE,
    )

    raw = re.sub(
        rf"(?:\s*[|¦•·–—-]+\s*)+(?:{site_names})\s*$",
        "",
        raw,
        flags=re.IGNORECASE,
    )

    raw = raw.strip(
        " |¦•·–—-\t\r\n"
    )

    # Multiple pipe-separated page-title components are common on video
    # sites. Pick the strongest meaningful component instead of showing
    # "| | |" in the Downloads list.
    pipe_parts = [
        part.strip(" |¦•·–—-\t\r\n")
        for part in re.split(
            r"\s*[|¦]\s*",
            raw,
        )
    ]

    pipe_parts = [
        part
        for part in pipe_parts
        if part
        and not re.fullmatch(
            rf"(?:{site_names})",
            part,
            flags=re.IGNORECASE,
        )
    ]

    if len(pipe_parts) >= 2:
        def title_score(part):
            letters = len(
                re.findall(
                    r"[^\W\d_]",
                    part,
                    flags=re.UNICODE,
                )
            )
            words = len(
                re.findall(
                    r"\S+",
                    part,
                )
            )

            score = letters + words * 4

            # Common channel/brand-looking fragments should lose to the
            # actual episode/video title if another good component exists.
            if re.search(
                r"\b(?:official|channel|arabic|english|tv|videos?)\b",
                part,
                flags=re.IGNORECASE,
            ):
                score -= 10

            return score

        raw = max(
            pipe_parts,
            key=title_score,
        )
    elif pipe_parts:
        raw = pipe_parts[0]

    raw = re.sub(
        r"\s+",
        " ",
        raw,
    ).strip(
        " |¦•·–—-\t\r\n"
    )

    # A title that is only punctuation is not useful.
    if not re.search(
        r"[^\W_]",
        raw,
        flags=re.UNICODE,
    ):
        raw = ""

    if not raw and page_url:
        try:
            parsed = urlparse(
                str(page_url)
            )
            slug = (
                parsed.path.rstrip("/")
                .split("/")[-1]
            )

            if slug and slug.lower() not in {
                "watch",
                "video",
                "videos",
                "content",
            }:
                raw = slug.replace(
                    "-",
                    " ",
                ).replace(
                    "_",
                    " ",
                )
        except Exception:
            pass

    return windows_safe_name(
        raw or "Browser Video",
        max_length=145,
    )



def _is_placeholder_video_title(value):
    raw = str(value or "").strip()

    if not raw:
        return True

    cleaned = clean_video_title(raw)

    value_low = cleaned.strip().lower()

    placeholders = {
        "browser video",
        "video",
        "stream",
        "streams",
        "chunk",
        "chunks",
        "manifest",
        "master",
        "playlist",
        "segment",
        "segments",
        "loading title",
        "loading title...",
        "analyzing",
        "analyzing...",
        "unknown",
        "accueil",
        "home",
        "facebook home",
        "facebook accueil",
        "facebook - log in or sign up",
        "facebook – log in or sign up",
        "facebook | connexion ou inscription",
    }

    if value_low in placeholders:
        return True

    if re.fullmatch(
        r"(?:chunk|segment|frag(?:ment)?|stream)[-_ ]?\d*",
        value_low,
        flags=re.IGNORECASE,
    ):
        return True

    # Only separators / punctuation.
    if not re.search(
        r"[^\W_]",
        cleaned,
        flags=re.UNICODE,
    ):
        return True

    return False


def remember_job_title(index, title):
    """
    Store a meaningful title. Placeholder/generic values can NEVER replace
    a real title already discovered earlier in the same download.
    """
    try:
        index = int(index)
    except Exception:
        return ""

    candidate = clean_video_title(
        title
    )

    with job_best_titles_lock:
        previous = job_best_titles.get(
            index,
            "",
        )

        if _is_placeholder_video_title(
            candidate
        ):
            return previous

        job_best_titles[index] = candidate
        return candidate


def best_job_title(index):
    try:
        index = int(index)
    except Exception:
        return ""

    with job_best_titles_lock:
        title = job_best_titles.get(
            index,
            "",
        )

    if title and not _is_placeholder_video_title(
        title
    ):
        return title

    item_id = bulk_tree_ids.get(
        index
    )

    if item_id:
        try:
            current = str(
                bulk_tree.set(
                    item_id,
                    "title",
                )
                or ""
            )
        except Exception:
            current = ""

        if current and not _is_placeholder_video_title(
            current
        ):
            return remember_job_title(
                index,
                current,
            )

    return ""


def best_output_title(index, fallback=""):
    """
    Filename/output title used by direct/HLS fallbacks.
    Prefer the title already discovered by yt-dlp/browser page extraction.
    """
    best = best_job_title(
        index
    )

    if best:
        return best

    candidate = clean_video_title(
        fallback
    )

    if not _is_placeholder_video_title(
        candidate
    ):
        remember_job_title(
            index,
            candidate,
        )
        return candidate

    return "Browser Video"


def _display_title_from_final_path(path):
    stem = os.path.splitext(
        os.path.basename(
            str(path or "")
        )
    )[0]

    # Manual batch files historically use "0001 - title".
    stem = re.sub(
        r"^\d{4}\s*-\s*",
        "",
        stem,
    )

    return clean_video_title(
        stem
    )


def _normalize_output_path(path):
    value = str(path or "").strip().strip('"')

    if not value:
        return ""

    if not os.path.isabs(value):
        value = os.path.join(
            DOWNLOADS,
            value,
        )

    return os.path.abspath(
        value
    )


def _attach_exact_path_to_row(index, path):
    path = _normalize_output_path(
        path
    )

    if not path:
        return

    item_id = bulk_tree_ids.get(
        index
    )

    if not item_id:
        return

    row_file_paths[item_id] = path

    # V32.22 TITLE LOCK:
    # The filename is useful only if it contains a meaningful title.
    # Never let "Browser Video.mp4" destroy the correct title that was shown
    # during the download.
    filename_title = _display_title_from_final_path(
        path
    )

    if not _is_placeholder_video_title(
        filename_title
    ):
        chosen_title = remember_job_title(
            index,
            filename_title,
        )
    else:
        chosen_title = best_job_title(
            index
        )

    if chosen_title:
        try:
            bulk_tree.set(
                item_id,
                "title",
                chosen_title,
            )
        except Exception:
            pass

    if os.path.isfile(path):
        try:
            bulk_tree.set(
                item_id,
                "size",
                _human_file_size(
                    os.path.getsize(path)
                ),
            )
        except Exception:
            pass

    schedule_download_history_save(
        50
    )


def register_job_output_path(index, path):
    if index is None:
        return

    path = _normalize_output_path(
        path
    )

    if not path:
        return

    try:
        index = int(index)
    except Exception:
        return

    with job_output_paths_lock:
        job_output_paths[index] = path

    gui_call(
        _attach_exact_path_to_row,
        index,
        path,
    )


def register_current_job_output_path(path):
    index = _current_job_index()

    if index is not None:
        register_job_output_path(
            index,
            path,
        )


def _exact_path_for_row(item_id):
    path = row_file_paths.get(
        item_id
    )

    if path:
        return _normalize_output_path(
            path
        )

    return ""


# ============================================================
# TOOL ENVIRONMENT
# ============================================================

def build_tool_env():
    env = os.environ.copy()
    current_path = env.get("PATH", "")

    if FFMPEG_DIR:
        env["PATH"] = (
            FFMPEG_DIR
            + (os.pathsep + current_path if current_path else "")
        )

    return env


# ============================================================
# SAFE GUI HELPERS
# ============================================================

def gui_call(func, *args, **kwargs):
    root.after(0, lambda: func(*args, **kwargs))


_raw_showinfo = messagebox.showinfo
_raw_showwarning = messagebox.showwarning
_raw_showerror = messagebox.showerror
_raw_askyesno = messagebox.askyesno


def _msg_call(raw_func, title, message=None, *args, **kwargs):
    return raw_func(
        tr_dynamic(title),
        tr_dynamic(message) if message is not None else message,
        *args,
        **kwargs,
    )


messagebox.showinfo = lambda title, message=None, *args, **kwargs: _msg_call(
    _raw_showinfo, title, message, *args, **kwargs
)
messagebox.showwarning = lambda title, message=None, *args, **kwargs: _msg_call(
    _raw_showwarning, title, message, *args, **kwargs
)
messagebox.showerror = lambda title, message=None, *args, **kwargs: _msg_call(
    _raw_showerror, title, message, *args, **kwargs
)
messagebox.askyesno = lambda title, message=None, *args, **kwargs: _msg_call(
    _raw_askyesno, title, message, *args, **kwargs
)


def gui_log(text):
    log_box.configure(state="normal")
    log_box.insert("end", str(text) + "\n")
    log_box.see("end")
    log_box.configure(state="disabled")


def log(text):
    gui_call(gui_log, text)


def set_status(text):
    gui_call(status_var.set, tr_dynamic(text))


def set_pot_status(text):
    gui_call(pot_status_var.set, text)


def set_update_status(text):
    gui_call(update_status_var.set, text)


def set_single_progress(value):
    gui_call(single_progress_var.set, value)


def set_bulk_progress(value):
    gui_call(bulk_progress_var.set, value)


def set_bulk_counter(text):
    gui_call(bulk_counter_var.set, text)


def clear_log():
    log_box.configure(state="normal")
    log_box.delete("1.0", "end")
    log_box.configure(state="disabled")


def open_downloads():
    os.startfile(DOWNLOADS)


def downloads_are_running():
    return (
        single_running
        or bulk_running
        or browser_queue_active
        or merge_running
    )


def _set_live_worker_limit(value=None):
    """
    Update the global live concurrency limit.

    If 4 jobs are already running and the user lowers Parallel to 2, the
    current 4 are allowed to finish; new jobs simply wait until active < 2.
    """
    global live_worker_limit
    global browser_worker_limit

    if value is None:
        try:
            value = int(
                bulk_workers_var.get()
            )
        except Exception:
            value = 4

    try:
        value = int(
            value
        )
    except Exception:
        value = 4

    value = max(
        1,
        min(
            value,
            8,
        ),
    )

    with live_queue_condition:
        live_worker_limit = value
        browser_worker_limit = value
        live_queue_condition.notify_all()

    try:
        gui_call(
            bulk_workers_var.set,
            value,
        )
    except Exception:
        pass

    return value


def _allocate_live_job_index():
    """
    Give every manual/browser job one unique runtime id.

    We seed from the largest visible row number so restored history can never
    collide with a new live job.
    """
    global browser_job_counter

    with live_job_counter_lock:
        try:
            visible_max = int(
                max_download_display_number()
            )
        except Exception:
            visible_max = 0

        try:
            mapped_max = max(
                [
                    int(key)
                    for key in bulk_tree_ids.keys()
                ]
                or [0]
            )
        except Exception:
            mapped_max = 0

        browser_job_counter = max(
            int(
                browser_job_counter
                or 0
            ),
            visible_max,
            mapped_max,
        ) + 1

        return browser_job_counter


def _acquire_live_slot(index=None, waiting_text=tr("Waiting")):
    """
    Wait until the global Parallel limit has room.
    Returns False if Stop All / per-job Cancel fires before starting.
    """
    global live_active_jobs

    if index is not None:
        update_tree_status(
            index,
            waiting_text,
        )

    with live_queue_condition:
        while (
            live_active_jobs
            >= live_worker_limit
        ):
            if (
                stop_all_event.is_set()
                or (
                    index is not None
                    and job_is_cancelled(
                        index
                    )
                )
            ):
                return False

            live_queue_condition.wait(
                timeout=0.25
            )

        if (
            stop_all_event.is_set()
            or (
                index is not None
                and job_is_cancelled(
                    index
                )
            )
        ):
            return False

        live_active_jobs += 1

    if index is not None:
        update_tree_status(
            index,
            "Downloading",
        )

    return True


def _release_live_slot():
    global live_active_jobs

    with live_queue_condition:
        live_active_jobs = max(
            0,
            live_active_jobs - 1,
        )
        live_queue_condition.notify_all()

    # Older browser queue waiters also listen on this condition.
    try:
        with browser_queue_condition:
            browser_queue_condition.notify_all()
    except Exception:
        pass


def _live_queue_status_text():
    with live_queue_condition:
        active = live_active_jobs
        limit = live_worker_limit

    return (
        f"{active} خدامين / {limit} Parallel"
    )



# ============================================================
# V32.36 — VIDEO MERGER
# ============================================================

MERGE_I18N = {
    "merge_videos": {
        "fr": "Fusionner des vidéos…",
        "en": "Merge videos…",
        "ar": "دمج الفيديوهات…",
        "darija": "جمع الفيديوهات…",
    },
    "merge_selected": {
        "fr": "Fusionner les vidéos sélectionnées…",
        "en": "Merge selected videos…",
        "ar": "دمج الفيديوهات المحددة…",
        "darija": "جمع الفيديوهات المختارين…",
    },
    "need_two": {
        "fr": "Sélectionnez au moins deux vidéos terminées.",
        "en": "Select at least two finished videos.",
        "ar": "حدد مقطعي فيديو مكتملين على الأقل.",
        "darija": "اختار على الأقل جوج فيديوهات سالاو.",
    },
    "choose_two": {
        "fr": "Choisissez au moins deux fichiers vidéo.",
        "en": "Choose at least two video files.",
        "ar": "اختر ملفي فيديو على الأقل.",
        "darija": "اختار على الأقل جوج ملفات فيديو.",
    },
    "order": {
        "fr": "Ordre de fusion",
        "en": "Merge order",
        "ar": "ترتيب الدمج",
        "darija": "ترتيب الجمع",
    },
    "up": {
        "fr": "↑ Monter",
        "en": "↑ Move up",
        "ar": "↑ للأعلى",
        "darija": "↑ طلّع",
    },
    "down": {
        "fr": "↓ Descendre",
        "en": "↓ Move down",
        "ar": "↓ للأسفل",
        "darija": "↓ هبّط",
    },
    "add_files": {
        "fr": "+ Ajouter",
        "en": "+ Add files",
        "ar": "+ إضافة ملفات",
        "darija": "+ زيد ملفات",
    },
    "remove": {
        "fr": "Retirer",
        "en": "Remove",
        "ar": "إزالة",
        "darija": "حيد",
    },
    "output": {
        "fr": "Fichier de sortie",
        "en": "Output file",
        "ar": "ملف الإخراج",
        "darija": "الفيديو النهائي",
    },
    "browse": {
        "fr": "Parcourir…",
        "en": "Browse…",
        "ar": "اختيار…",
        "darija": "اختار…",
    },
    "mode": {
        "fr": "Mode",
        "en": "Mode",
        "ar": "الوضع",
        "darija": "الطريقة",
    },
    "auto": {
        "fr": "Auto — rapide si compatible, sinon TV Safe",
        "en": "Auto — fast if compatible, otherwise TV Safe",
        "ar": "تلقائي — سريع إن كان متوافقًا، وإلا TV Safe",
        "darija": "Auto — سريع إلا توافقو، وإلا TV Safe",
    },
    "fast": {
        "fr": "Rapide — sans réencodage",
        "en": "Fast — no re-encode",
        "ar": "سريع — بدون إعادة ترميز",
        "darija": "سريع — بلا إعادة ترميز",
    },
    "tv": {
        "fr": "TV Safe — H.264 + AAC",
        "en": "TV Safe — H.264 + AAC",
        "ar": "TV Safe — H.264 + AAC",
        "darija": "TV Safe — H.264 + AAC",
    },
    "start": {
        "fr": "Fusionner",
        "en": "Merge",
        "ar": "دمج",
        "darija": "جمع",
    },
    "cancel": {
        "fr": "Annuler",
        "en": "Cancel",
        "ar": "إلغاء",
        "darija": "حبس",
    },
    "working": {
        "fr": "Fusion en cours…",
        "en": "Merging…",
        "ar": "جارٍ الدمج…",
        "darija": "كيجمع الفيديوهات…",
    },
    "preparing": {
        "fr": "Préparation",
        "en": "Preparing",
        "ar": "تجهيز",
        "darija": "كيجهز",
    },
    "fast_try": {
        "fr": "Fusion rapide…",
        "en": "Fast merge…",
        "ar": "دمج سريع…",
        "darija": "جمع سريع…",
    },
    "fallback": {
        "fr": "Les vidéos sont différentes — conversion TV Safe…",
        "en": "Videos differ — switching to TV Safe conversion…",
        "ar": "الفيديوهات مختلفة — التحويل إلى TV Safe…",
        "darija": "الفيديوهات مختلفين — غادي لـ TV Safe…",
    },
    "done": {
        "fr": "Fusion terminée ✅",
        "en": "Merge completed ✅",
        "ar": "اكتمل الدمج ✅",
        "darija": "الجمع سالا ✅",
    },
    "failed": {
        "fr": "Échec de la fusion.",
        "en": "Merge failed.",
        "ar": "فشل الدمج.",
        "darija": "الجمع فشل.",
    },
    "cancelled": {
        "fr": "Fusion annulée.",
        "en": "Merge cancelled.",
        "ar": "تم إلغاء الدمج.",
        "darija": "الجمع تحبس.",
    },
    "open_folder": {
        "fr": "Ouvrir le dossier ?",
        "en": "Open the folder?",
        "ar": "فتح المجلد؟",
        "darija": "نحل الدوسي؟",
    },
    "same_files": {
        "fr": "Les fichiers sélectionnés ne sont pas tous des vidéos valides.",
        "en": "The selected files are not all valid videos.",
        "ar": "ليست كل الملفات المحددة فيديوهات صالحة.",
        "darija": "ماشي كاع الملفات المختارين فيديوهات صالحين.",
    },
}


def _mtr(key):
    item = MERGE_I18N.get(
        key,
        {},
    )

    return str(
        item.get(
            CURRENT_LANGUAGE,
            item.get(
                "en",
                key,
            ),
        )
    )



MERGE_I18N.update({
    "missing_paths": {
        "fr": "Z²SE voit bien les lignes sélectionnées, mais il ne retrouve pas le fichier réel de certaines vidéos. Sélectionnez les fichiers manquants.",
        "en": "Z²SE can see the selected rows, but it cannot find the real file for some videos. Select the missing files.",
        "ar": "يرى Z²SE الصفوف المحددة، لكنه لا يجد الملف الحقيقي لبعض الفيديوهات. اختر الملفات المفقودة.",
        "darija": "Z²SE شايف السطور اللي اخترتي، ولكن ما لقاوش الملفات الحقيقيين ديال شي فيديوهات. اختار الملفات الناقصين.",
    },
    "resolved_count": {
        "fr": "Vidéos trouvées",
        "en": "Videos found",
        "ar": "الفيديوهات التي تم العثور عليها",
        "darija": "الفيديوهات اللي تلقاو",
    },
    "selected_count": {
        "fr": "Lignes sélectionnées",
        "en": "Selected rows",
        "ar": "الصفوف المحددة",
        "darija": "السطور المختارين",
    },
})

MERGE_VIDEO_EXTENSIONS = {
    ".mp4",
    ".mkv",
    ".webm",
    ".mov",
    ".m4v",
    ".avi",
    ".ts",
    ".mts",
    ".m2ts",
}


def _is_mergeable_video_path(path):
    return (
        bool(
            path
        )
        and os.path.isfile(
            path
        )
        and os.path.splitext(
            path
        )[1].lower()
        in MERGE_VIDEO_EXTENSIONS
    )


def _probe_merge_info(path):
    """
    Probe enough stream properties to decide whether stream-copy concat
    is worth trying and to choose the TV-safe normalization size.
    """
    result = {
        "has_video": False,
        "has_audio": False,
        "video_codec": "",
        "width": 0,
        "height": 0,
        "pix_fmt": "",
        "profile": "",
        "level": 0,
        "video_rate": "",
        "video_time_base": "",
        "audio_codec": "",
        "sample_rate": "",
        "channels": 0,
        "channel_layout": "",
    }

    if (
        not FFPROBE
        or not path
        or not os.path.isfile(
            path
        )
    ):
        return result

    try:
        proc = subprocess.run(
            [
                FFPROBE,
                "-v",
                "error",
                "-show_entries",
                (
                    "stream=codec_type,codec_name,width,height,pix_fmt,"
                    "profile,level,avg_frame_rate,time_base,sample_rate,"
                    "channels,channel_layout"
                ),
                "-of",
                "json",
                path,
            ],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=20,
            env=build_tool_env(),
            creationflags=(
                subprocess.CREATE_NO_WINDOW
                if os.name == "nt"
                else 0
            ),
        )

        if proc.returncode != 0:
            return result

        payload = json.loads(
            proc.stdout
            or "{}"
        )

        for stream in payload.get(
            "streams",
            [],
        ):
            stream_type = str(
                stream.get(
                    "codec_type",
                    "",
                )
            ).lower()

            if (
                stream_type == "video"
                and not result[
                    "has_video"
                ]
            ):
                result[
                    "has_video"
                ] = True
                result[
                    "video_codec"
                ] = str(
                    stream.get(
                        "codec_name",
                        "",
                    )
                    or ""
                ).lower()
                result[
                    "width"
                ] = int(
                    stream.get(
                        "width",
                        0,
                    )
                    or 0
                )
                result[
                    "height"
                ] = int(
                    stream.get(
                        "height",
                        0,
                    )
                    or 0
                )
                result[
                    "pix_fmt"
                ] = str(
                    stream.get(
                        "pix_fmt",
                        "",
                    )
                    or ""
                ).lower()
                result[
                    "profile"
                ] = str(
                    stream.get(
                        "profile",
                        "",
                    )
                    or ""
                )
                result[
                    "level"
                ] = int(
                    stream.get(
                        "level",
                        0,
                    )
                    or 0
                )
                result[
                    "video_rate"
                ] = str(
                    stream.get(
                        "avg_frame_rate",
                        "",
                    )
                    or ""
                )
                result[
                    "video_time_base"
                ] = str(
                    stream.get(
                        "time_base",
                        "",
                    )
                    or ""
                )

            elif (
                stream_type == "audio"
                and not result[
                    "has_audio"
                ]
            ):
                result[
                    "has_audio"
                ] = True
                result[
                    "audio_codec"
                ] = str(
                    stream.get(
                        "codec_name",
                        "",
                    )
                    or ""
                ).lower()
                result[
                    "sample_rate"
                ] = str(
                    stream.get(
                        "sample_rate",
                        "",
                    )
                    or ""
                )
                result[
                    "channels"
                ] = int(
                    stream.get(
                        "channels",
                        0,
                    )
                    or 0
                )
                result[
                    "channel_layout"
                ] = str(
                    stream.get(
                        "channel_layout",
                        "",
                    )
                    or ""
                )

    except Exception:
        pass

    return result


def _merge_copy_signature(info):
    return (
        info.get(
            "video_codec"
        ),
        info.get(
            "width"
        ),
        info.get(
            "height"
        ),
        info.get(
            "pix_fmt"
        ),
        info.get(
            "profile"
        ),
        info.get(
            "level"
        ),
        info.get(
            "video_rate"
        ),
        info.get(
            "video_time_base"
        ),
        bool(
            info.get(
                "has_audio"
            )
        ),
        info.get(
            "audio_codec"
        ),
        info.get(
            "sample_rate"
        ),
        info.get(
            "channels"
        ),
        info.get(
            "channel_layout"
        ),
    )


def _merge_escape_concat_path(path):
    value = os.path.abspath(
        path
    ).replace(
        "\\",
        "/",
    )

    # FFmpeg concat-demuxer single-quote escape.
    value = value.replace(
        "'",
        "'\\''",
    )

    return (
        "file '"
        + value
        + "'"
    )


def _merge_set_current_process(process):
    global merge_current_process

    with merge_process_lock:
        merge_current_process = process


def _merge_clear_current_process(process=None):
    global merge_current_process

    with merge_process_lock:
        if (
            process is None
            or merge_current_process
            is process
        ):
            merge_current_process = None


def cancel_video_merge():
    merge_cancel_event.set()

    with merge_process_lock:
        process = merge_current_process

    if process:
        try:
            process.terminate()
        except Exception:
            pass


def _run_merge_command(command):
    process = None

    try:
        process = subprocess.Popen(
            command,
            env=build_tool_env(),
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            encoding="utf-8",
            errors="replace",
            creationflags=(
                subprocess.CREATE_NO_WINDOW
                if os.name == "nt"
                else 0
            ),
        )

        _merge_set_current_process(
            process
        )
        register_process(
            process
        )

        output_lines = []

        for raw in process.stdout:
            if merge_cancel_event.is_set():
                try:
                    process.terminate()
                except Exception:
                    pass
                break

            line = raw.strip()

            if line:
                output_lines.append(
                    line
                )

                if len(
                    output_lines
                ) > 30:
                    output_lines = output_lines[
                        -30:
                    ]

        code = process.wait()

        return (
            code,
            "\n".join(
                output_lines
            ),
        )

    except Exception as exc:
        return (
            999,
            str(
                exc
            ),
        )

    finally:
        if process:
            unregister_process(
                process
            )

        _merge_clear_current_process(
            process
        )


def _write_merge_concat_file(paths, list_path):
    with open(
        list_path,
        "w",
        encoding="utf-8",
        newline="\n",
    ) as handle:
        for path in paths:
            handle.write(
                _merge_escape_concat_path(
                    path
                )
                + "\n"
            )


def _merge_fast_concat(paths, output_file, work_dir):
    list_path = os.path.join(
        work_dir,
        "concat.txt",
    )

    _write_merge_concat_file(
        paths,
        list_path,
    )

    command = [
        FFMPEG,
        "-y",
        "-fflags",
        "+genpts",
        "-f",
        "concat",
        "-safe",
        "0",
        "-i",
        list_path,
        "-map",
        "0:v:0",
        "-map",
        "0:a:0?",
        "-c",
        "copy",
        "-movflags",
        "+faststart",
        "-loglevel",
        "warning",
        output_file,
    ]

    code, output = _run_merge_command(
        command
    )

    if merge_cancel_event.is_set():
        return (
            False,
            output,
        )

    valid = (
        code == 0
        and os.path.isfile(
            output_file
        )
        and os.path.getsize(
            output_file
        ) > 1024
        and _probe_merge_info(
            output_file
        ).get(
            "has_video",
            False,
        )
    )

    if not valid:
        try:
            if os.path.isfile(
                output_file
            ):
                os.remove(
                    output_file
                )
        except Exception:
            pass

    return (
        valid,
        output,
    )


def _merge_even_dimension(value, fallback):
    try:
        value = int(
            value
        )
    except Exception:
        value = int(
            fallback
        )

    value = max(
        2,
        value,
    )

    if value % 2:
        value -= 1

    return max(
        2,
        value,
    )


def _normalize_merge_clip(
    input_file,
    output_file,
    width,
    height,
    has_audio,
):
    video_filter = (
        f"scale={width}:{height}:"
        "force_original_aspect_ratio=decrease,"
        f"pad={width}:{height}:(ow-iw)/2:(oh-ih)/2:black,"
        "setsar=1,fps=30,format=yuv420p"
    )

    command = [
        FFMPEG,
        "-y",
        "-i",
        input_file,
    ]

    if has_audio:
        command += [
            "-map",
            "0:v:0",
            "-map",
            "0:a:0",
        ]
    else:
        command += [
            "-f",
            "lavfi",
            "-i",
            "anullsrc=channel_layout=stereo:sample_rate=48000",
            "-map",
            "0:v:0",
            "-map",
            "1:a:0",
        ]

    command += [
        "-vf",
        video_filter,
        "-c:v",
        "libx264",
        "-preset",
        "veryfast",
        "-crf",
        "20",
        "-pix_fmt",
        "yuv420p",
        "-profile:v",
        "high",
        "-tag:v",
        "avc1",
        "-c:a",
        "aac",
        "-b:a",
        "192k",
        "-ac",
        "2",
        "-ar",
        "48000",
        "-shortest",
        "-movflags",
        "+faststart",
        "-loglevel",
        "warning",
        output_file,
    ]

    code, output = _run_merge_command(
        command
    )

    return (
        code == 0
        and os.path.isfile(
            output_file
        )
        and os.path.getsize(
            output_file
        ) > 1024,
        output,
    )


def _merge_tv_safe(
    paths,
    output_file,
    work_dir,
    infos,
    status_callback=None,
):
    first_video = next(
        (
            info
            for info in infos
            if info.get(
                "has_video"
            )
        ),
        {},
    )

    width = _merge_even_dimension(
        first_video.get(
            "width",
            1920,
        ),
        1920,
    )
    height = _merge_even_dimension(
        first_video.get(
            "height",
            1080,
        ),
        1080,
    )

    normalized = []

    for position, (
        input_file,
        info,
    ) in enumerate(
        zip(
            paths,
            infos,
        ),
        start=1,
    ):
        if merge_cancel_event.is_set():
            return (
                False,
                "",
            )

        if status_callback:
            status_callback(
                f"{_mtr('preparing')} {position}/{len(paths)}"
            )

        temp_file = os.path.join(
            work_dir,
            f"clip_{position:03d}.mp4",
        )

        ok, output = _normalize_merge_clip(
            input_file=input_file,
            output_file=temp_file,
            width=width,
            height=height,
            has_audio=bool(
                info.get(
                    "has_audio"
                )
            ),
        )

        if not ok:
            return (
                False,
                output,
            )

        normalized.append(
            temp_file
        )

    if status_callback:
        status_callback(
            _mtr(
                "fast_try"
            )
        )

    return _merge_fast_concat(
        normalized,
        output_file,
        work_dir,
    )


def _register_merged_output_in_history(output_file):
    try:
        index = _allocate_live_job_index()

        title = os.path.splitext(
            os.path.basename(
                output_file
            )
        )[0]

        item_id = bulk_tree.insert(
            "",
            "end",
            values=(
                index,
                title,
                "MP4",
                "MERGE",
                "100.0%",
                "",
                "",
                _human_file_size(
                    os.path.getsize(
                        output_file
                    )
                ),
                tr(
                    "Done ✅"
                ),
            ),
        )

        bulk_tree_ids[
            index
        ] = item_id
        row_file_paths[
            item_id
        ] = output_file

        with job_output_paths_lock:
            job_output_paths[
                index
            ] = output_file

        schedule_download_history_save(
            50
        )

        try:
            bulk_tree.see(
                item_id
            )
            bulk_tree.selection_set(
                item_id
            )
            bulk_tree.focus(
                item_id
            )
        except Exception:
            pass

    except Exception as exc:
        log(
            "MERGE history registration warning: "
            + str(
                exc
            )
        )


def _merge_worker(
    paths,
    output_file,
    mode,
    status_callback,
    finished_callback,
):
    global merge_running

    merge_running = True
    merge_cancel_event.clear()

    work_dir = os.path.join(
        APP_DIR,
        "_merge_work",
        datetime.now().strftime(
            "%Y%m%d_%H%M%S_%f"
        ),
    )

    os.makedirs(
        work_dir,
        exist_ok=True,
    )

    success = False
    error_text = ""

    try:
        infos = [
            _probe_merge_info(
                path
            )
            for path in paths
        ]

        if not all(
            info.get(
                "has_video"
            )
            for info in infos
        ):
            error_text = _mtr(
                "same_files"
            )
            return

        signatures_match = (
            len(
                {
                    _merge_copy_signature(
                        info
                    )
                    for info in infos
                }
            )
            == 1
        )

        if mode in (
            "auto",
            "fast",
        ):
            if status_callback:
                status_callback(
                    _mtr(
                        "fast_try"
                    )
                )

            if (
                mode == "fast"
                or signatures_match
            ):
                success, error_text = _merge_fast_concat(
                    paths,
                    output_file,
                    work_dir,
                )

                if success:
                    return

                if (
                    mode == "fast"
                    or merge_cancel_event.is_set()
                ):
                    return

        if status_callback:
            status_callback(
                _mtr(
                    "fallback"
                )
            )

        success, error_text = _merge_tv_safe(
            paths=paths,
            output_file=output_file,
            work_dir=work_dir,
            infos=infos,
            status_callback=status_callback,
        )

    finally:
        merge_running = False
        _merge_clear_current_process()

        try:
            shutil.rmtree(
                work_dir,
                ignore_errors=True,
            )
        except Exception:
            pass

        gui_call(
            finished_callback,
            success,
            output_file,
            error_text,
            merge_cancel_event.is_set(),
        )


def _default_merge_output_path():
    name = (
        "Merged "
        + datetime.now().strftime(
            "%Y-%m-%d %H-%M-%S"
        )
        + ".mp4"
    )

    return unique_output_path(
        os.path.join(
            DOWNLOADS,
            name,
        )
    )


def _open_merge_dialog(initial_paths):
    paths = [
        os.path.abspath(
            path
        )
        for path in initial_paths
        if _is_mergeable_video_path(
            path
        )
    ]

    # Deduplicate while preserving order.
    clean_paths = []
    seen = set()

    for path in paths:
        key = os.path.normcase(
            path
        )

        if key in seen:
            continue

        seen.add(
            key
        )
        clean_paths.append(
            path
        )

    paths = clean_paths

    if len(
        paths
    ) < 2:
        messagebox.showinfo(
            _mtr(
                "merge_videos"
            ),
            _mtr(
                "need_two"
            ),
        )
        return

    window = tk.Toplevel(
        root
    )
    window.title(
        _mtr(
            "merge_videos"
        )
    )
    window.geometry(
        "760x520"
    )
    window.minsize(
        650,
        450,
    )
    window.transient(
        root
    )

    container = ttk.Frame(
        window,
        padding=16,
    )
    container.pack(
        fill="both",
        expand=True,
    )

    ttk.Label(
        container,
        text=_mtr(
            "order"
        ),
        font=(
            "Segoe UI",
            10,
            "bold",
        ),
    ).pack(
        anchor="w",
        pady=(
            0,
            7,
        ),
    )

    list_frame = ttk.Frame(
        container
    )
    list_frame.pack(
        fill="both",
        expand=True,
    )

    listbox = tk.Listbox(
        list_frame,
        selectmode="browse",
        activestyle="dotbox",
        font=(
            "Segoe UI",
            9,
        ),
    )
    listbox.pack(
        side="left",
        fill="both",
        expand=True,
    )

    scrollbar = ttk.Scrollbar(
        list_frame,
        orient="vertical",
        command=listbox.yview,
    )
    scrollbar.pack(
        side="right",
        fill="y",
    )
    listbox.configure(
        yscrollcommand=scrollbar.set
    )

    current_paths = list(
        paths
    )

    def refresh_list(
        select_index=None,
    ):
        listbox.delete(
            0,
            "end",
        )

        for position, path in enumerate(
            current_paths,
            start=1,
        ):
            listbox.insert(
                "end",
                f"{position}. {os.path.basename(path)}",
            )

        if (
            select_index is not None
            and current_paths
        ):
            select_index = max(
                0,
                min(
                    int(
                        select_index
                    ),
                    len(
                        current_paths
                    )
                    - 1,
                ),
            )
            listbox.selection_set(
                select_index
            )
            listbox.activate(
                select_index
            )
            listbox.see(
                select_index
            )

    refresh_list(
        0
    )

    buttons = ttk.Frame(
        container
    )
    buttons.pack(
        fill="x",
        pady=(
            8,
            12,
        ),
    )

    def move_up():
        selection = listbox.curselection()

        if not selection:
            return

        index = int(
            selection[0]
        )

        if index <= 0:
            return

        current_paths[
            index - 1
        ], current_paths[
            index
        ] = (
            current_paths[
                index
            ],
            current_paths[
                index - 1
            ],
        )

        refresh_list(
            index - 1
        )

    def move_down():
        selection = listbox.curselection()

        if not selection:
            return

        index = int(
            selection[0]
        )

        if index >= len(
            current_paths
        ) - 1:
            return

        current_paths[
            index + 1
        ], current_paths[
            index
        ] = (
            current_paths[
                index
            ],
            current_paths[
                index + 1
            ],
        )

        refresh_list(
            index + 1
        )

    def add_files():
        chosen = filedialog.askopenfilenames(
            parent=window,
            title=_mtr(
                "merge_videos"
            ),
            filetypes=[
                (
                    "Video files",
                    "*.mp4 *.mkv *.webm *.mov *.m4v *.avi *.ts *.mts *.m2ts",
                ),
                (
                    "All files",
                    "*.*",
                ),
            ],
        )

        for path in chosen:
            if not _is_mergeable_video_path(
                path
            ):
                continue

            normalized = os.path.abspath(
                path
            )

            if all(
                os.path.normcase(
                    existing
                )
                != os.path.normcase(
                    normalized
                )
                for existing in current_paths
            ):
                current_paths.append(
                    normalized
                )

        refresh_list(
            len(
                current_paths
            )
            - 1
        )

    def remove_file():
        selection = listbox.curselection()

        if not selection:
            return

        index = int(
            selection[0]
        )
        current_paths.pop(
            index
        )

        refresh_list(
            min(
                index,
                len(
                    current_paths
                )
                - 1,
            )
            if current_paths
            else None
        )

    ttk.Button(
        buttons,
        text=_mtr(
            "up"
        ),
        command=move_up,
    ).pack(
        side="left",
    )
    ttk.Button(
        buttons,
        text=_mtr(
            "down"
        ),
        command=move_down,
    ).pack(
        side="left",
        padx=5,
    )
    ttk.Button(
        buttons,
        text=_mtr(
            "add_files"
        ),
        command=add_files,
    ).pack(
        side="left",
        padx=(
            12,
            5,
        ),
    )
    ttk.Button(
        buttons,
        text=_mtr(
            "remove"
        ),
        command=remove_file,
    ).pack(
        side="left",
    )

    output_frame = ttk.Frame(
        container
    )
    output_frame.pack(
        fill="x",
        pady=(
            0,
            10,
        ),
    )

    ttk.Label(
        output_frame,
        text=_mtr(
            "output"
        ),
    ).pack(
        side="left",
        padx=(
            0,
            7,
        ),
    )

    output_var = tk.StringVar(
        value=_default_merge_output_path()
    )

    output_entry = ttk.Entry(
        output_frame,
        textvariable=output_var,
    )
    output_entry.pack(
        side="left",
        fill="x",
        expand=True,
    )

    def browse_output():
        chosen = filedialog.asksaveasfilename(
            parent=window,
            title=_mtr(
                "output"
            ),
            initialdir=DOWNLOADS,
            initialfile=os.path.basename(
                output_var.get()
            ),
            defaultextension=".mp4",
            filetypes=[
                (
                    "MP4 video",
                    "*.mp4",
                )
            ],
        )

        if chosen:
            if not chosen.lower().endswith(
                ".mp4"
            ):
                chosen += ".mp4"

            output_var.set(
                chosen
            )

    ttk.Button(
        output_frame,
        text=_mtr(
            "browse"
        ),
        command=browse_output,
    ).pack(
        side="left",
        padx=(
            7,
            0,
        ),
    )

    mode_frame = ttk.Frame(
        container
    )
    mode_frame.pack(
        fill="x",
        pady=(
            0,
            10,
        ),
    )

    ttk.Label(
        mode_frame,
        text=_mtr(
            "mode"
        ),
    ).pack(
        side="left",
        padx=(
            0,
            7,
        ),
    )

    mode_labels = {
        _mtr(
            "auto"
        ): "auto",
        _mtr(
            "fast"
        ): "fast",
        _mtr(
            "tv"
        ): "tv",
    }

    mode_var = tk.StringVar(
        value=_mtr(
            "auto"
        )
    )

    mode_box = ttk.Combobox(
        mode_frame,
        textvariable=mode_var,
        values=list(
            mode_labels.keys()
        ),
        state="readonly",
    )
    mode_box.pack(
        side="left",
        fill="x",
        expand=True,
    )

    status_var_merge = tk.StringVar(
        value=""
    )

    ttk.Label(
        container,
        textvariable=status_var_merge,
    ).pack(
        anchor="w",
        pady=(
            2,
            4,
        ),
    )

    progress = ttk.Progressbar(
        container,
        mode="indeterminate",
    )
    progress.pack(
        fill="x",
        pady=(
            0,
            10,
        ),
    )

    footer = ttk.Frame(
        container
    )
    footer.pack(
        fill="x",
    )

    start_button = ttk.Button(
        footer,
        text=_mtr(
            "start"
        ),
    )
    start_button.pack(
        side="right",
    )

    cancel_button = ttk.Button(
        footer,
        text=_mtr(
            "cancel"
        ),
        command=window.destroy,
    )
    cancel_button.pack(
        side="right",
        padx=(
            0,
            7,
        ),
    )

    controls = [
        listbox,
        output_entry,
        mode_box,
        start_button,
    ]

    def set_merge_status(
        value
    ):
        gui_call(
            status_var_merge.set,
            value,
        )

    def finished(
        success,
        output_file,
        error_text,
        cancelled,
    ):
        try:
            progress.stop()
        except Exception:
            pass

        if cancelled:
            messagebox.showinfo(
                _mtr(
                    "merge_videos"
                ),
                _mtr(
                    "cancelled"
                ),
            )
            try:
                if os.path.isfile(
                    output_file
                ):
                    os.remove(
                        output_file
                    )
            except Exception:
                pass
            window.destroy()
            return

        if success:
            _register_merged_output_in_history(
                output_file
            )

            message = (
                _mtr(
                    "done"
                )
                + "\n\n"
                + output_file
                + "\n\n"
                + _mtr(
                    "open_folder"
                )
            )

            open_it = messagebox.askyesno(
                _mtr(
                    "merge_videos"
                ),
                message,
            )

            window.destroy()

            if open_it:
                try:
                    subprocess.Popen(
                        [
                            "explorer.exe",
                            "/select,",
                            output_file,
                        ]
                    )
                except Exception:
                    try:
                        os.startfile(
                            os.path.dirname(
                                output_file
                            )
                        )
                    except Exception:
                        pass

        else:
            for widget in controls:
                try:
                    widget.configure(
                        state="normal"
                    )
                except Exception:
                    pass

            mode_box.configure(
                state="readonly"
            )

            cancel_button.configure(
                text=_mtr(
                    "cancel"
                ),
                command=window.destroy,
            )

            messagebox.showerror(
                _mtr(
                    "merge_videos"
                ),
                _mtr(
                    "failed"
                )
                + (
                    "\n\n"
                    + str(
                        error_text
                    )[
                        -1500:
                    ]
                    if error_text
                    else ""
                ),
            )

    def start_merge():
        if len(
            current_paths
        ) < 2:
            messagebox.showinfo(
                _mtr(
                    "merge_videos"
                ),
                _mtr(
                    "choose_two"
                ),
            )
            return

        if not all(
            _is_mergeable_video_path(
                path
            )
            for path in current_paths
        ):
            messagebox.showerror(
                _mtr(
                    "merge_videos"
                ),
                _mtr(
                    "same_files"
                ),
            )
            return

        output_file = os.path.abspath(
            output_var.get().strip()
        )

        if not output_file:
            return

        if not output_file.lower().endswith(
            ".mp4"
        ):
            output_file += ".mp4"

        output_file = unique_output_path(
            output_file
        )
        output_var.set(
            output_file
        )

        for widget in controls:
            try:
                widget.configure(
                    state="disabled"
                )
            except Exception:
                pass

        cancel_button.configure(
            state="normal",
            command=cancel_video_merge,
        )

        progress.start(
            12
        )
        status_var_merge.set(
            _mtr(
                "working"
            )
        )

        selected_mode = mode_labels.get(
            mode_var.get(),
            "auto",
        )

        threading.Thread(
            target=_merge_worker,
            args=(
                list(
                    current_paths
                ),
                output_file,
                selected_mode,
                set_merge_status,
                finished,
            ),
            daemon=True,
        ).start()

    start_button.configure(
        command=start_merge
    )

    def close_window():
        if merge_running:
            cancel_video_merge()
        else:
            window.destroy()

    window.protocol(
        "WM_DELETE_WINDOW",
        close_window,
    )

    try:
        window.update_idletasks()
        x = root.winfo_rootx() + max(
            0,
            (
                root.winfo_width()
                - window.winfo_width()
            )
            // 2,
        )
        y = root.winfo_rooty() + max(
            0,
            (
                root.winfo_height()
                - window.winfo_height()
            )
            // 2,
        )
        window.geometry(
            f"+{x}+{y}"
        )
    except Exception:
        pass


def merge_selected_videos():
    """
    V32.37:
    The selection itself is authoritative.

    Older/history rows can visibly be "Terminé" while their exact output path
    was never persisted, so the old merger silently filtered them out and then
    wrongly said "select at least two finished videos".

    New behavior:
      - keep all selected finished rows
      - resolve every real file we can
      - if one/more paths are missing, ask the user to locate them
      - then open the merger with the complete resolved file list
    """
    try:
        selected = set(
            _selected_download_items()
        )

        tree_order = {
            item_id: position
            for position, item_id in enumerate(
                bulk_tree.get_children()
            )
        }

        items = sorted(
            selected,
            key=lambda item: tree_order.get(
                item,
                10**9,
            ),
        )
    except Exception:
        items = []

    if len(items) < 2:
        messagebox.showinfo(
            _mtr(
                "merge_selected"
            ),
            _mtr(
                "need_two"
            ),
        )
        return

    terminal_items = [
        item_id
        for item_id in items
        if _mini_is_terminal_status(
            _item_status(
                item_id
            )
        )
    ]

    if len(terminal_items) < 2:
        messagebox.showinfo(
            _mtr(
                "merge_selected"
            ),
            _mtr(
                "need_two"
            ),
        )
        return

    resolved_paths = []
    unresolved_items = []

    for item_id in terminal_items:
        path = _find_download_file_for_row(
            item_id
        )

        if _is_mergeable_video_path(
            path
        ):
            resolved_paths.append(
                os.path.abspath(
                    path
                )
            )
        else:
            unresolved_items.append(
                item_id
            )

    # Older restored rows may not have an exact path. Let the user point
    # Z²SE to the actual files instead of pretending the selection is wrong.
    if unresolved_items:
        info = (
            _mtr(
                "missing_paths"
            )
            + "\n\n"
            + _mtr(
                "selected_count"
            )
            + f": {len(terminal_items)}\n"
            + _mtr(
                "resolved_count"
            )
            + f": {len(resolved_paths)}"
        )

        messagebox.showinfo(
            _mtr(
                "merge_selected"
            ),
            info,
        )

        needed = len(
            unresolved_items
        )

        chosen = filedialog.askopenfilenames(
            parent=root,
            title=_mtr(
                "merge_selected"
            ),
            initialdir=DOWNLOADS,
            filetypes=[
                (
                    "Video files",
                    "*.mp4 *.mkv *.webm *.mov *.m4v *.avi *.ts *.mts *.m2ts",
                ),
                (
                    "All files",
                    "*.*",
                ),
            ],
        )

        chosen = [
            os.path.abspath(
                path
            )
            for path in chosen
            if _is_mergeable_video_path(
                path
            )
        ]

        if len(
            chosen
        ) < needed:
            messagebox.showinfo(
                _mtr(
                    "merge_selected"
                ),
                _mtr(
                    "choose_two"
                ),
            )
            return

        # Attach the chosen files to the unresolved rows in selection order.
        # This also repairs future Open/Delete/Merge actions for these rows.
        for item_id, path in zip(
            unresolved_items,
            chosen[
                :needed
            ],
        ):
            row_file_paths[
                item_id
            ] = path

            index = _job_index_for_item(
                item_id
            )

            if index is not None:
                try:
                    with job_output_paths_lock:
                        job_output_paths[
                            int(
                                index
                            )
                        ] = path
                except Exception:
                    pass

            resolved_paths.append(
                path
            )

        schedule_download_history_save(
            50
        )

    # Restore the selected row order, not the arbitrary "resolved first"
    # order, so the merge sequence matches what the user sees.
    ordered_paths = []

    for item_id in terminal_items:
        path = _find_download_file_for_row(
            item_id
        )

        if _is_mergeable_video_path(
            path
        ):
            ordered_paths.append(
                os.path.abspath(
                    path
                )
            )

    # Final fallback: if a just-repaired row still cannot be rediscovered,
    # use the directly resolved list.
    if len(
        ordered_paths
    ) < 2:
        ordered_paths = list(
            resolved_paths
        )

    # Deduplicate while preserving order.
    clean_paths = []
    seen = set()

    for path in ordered_paths:
        key = os.path.normcase(
            os.path.abspath(
                path
            )
        )

        if key in seen:
            continue

        seen.add(
            key
        )
        clean_paths.append(
            path
        )

    if len(
        clean_paths
    ) < 2:
        messagebox.showinfo(
            _mtr(
                "merge_selected"
            ),
            _mtr(
                "need_two"
            ),
        )
        return

    _open_merge_dialog(
        clean_paths
    )


def merge_videos_from_files():
    chosen = filedialog.askopenfilenames(
        parent=root,
        title=_mtr(
            "merge_videos"
        ),
        initialdir=DOWNLOADS,
        filetypes=[
            (
                "Video files",
                "*.mp4 *.mkv *.webm *.mov *.m4v *.avi *.ts *.mts *.m2ts",
            ),
            (
                "All files",
                "*.*",
            ),
        ],
    )

    if len(
        chosen
    ) < 2:
        if chosen:
            messagebox.showinfo(
                _mtr(
                    "merge_videos"
                ),
                _mtr(
                    "choose_two"
                ),
            )
        return

    _open_merge_dialog(
        list(
            chosen
        )
    )



# ============================================================
# SYSTEM TRAY
# ============================================================

def create_tray_image():
    """Use the official Z²SE icon in the Windows system tray."""
    if Image is not None:
        try:
            if os.path.isfile(BRAND_ICON_PNG):
                return Image.open(BRAND_ICON_PNG).convert("RGBA").resize(
                    (64, 64),
                    Image.Resampling.LANCZOS
                )
        except Exception:
            pass

    # Emergency fallback if the logo asset is missing.
    image = Image.new("RGBA", (64, 64), (15, 35, 70, 255))
    draw = ImageDraw.Draw(image)
    draw.rounded_rectangle(
        (7, 7, 57, 57),
        radius=13,
        fill=(245, 248, 255, 255)
    )
    draw.rectangle((29, 17, 35, 37), fill=(0, 90, 220, 255))
    draw.polygon(
        [(20, 33), (32, 48), (44, 33)],
        fill=(0, 90, 220, 255)
    )
    return image



def create_mini_tray_image():
    """Z²SE logo with a small download badge for the progress tray icon."""
    if Image is None:
        return create_tray_image()

    try:
        image = create_tray_image().convert("RGBA").resize(
            (64, 64),
            Image.Resampling.LANCZOS,
        )
        draw = ImageDraw.Draw(image)

        # Small bottom-right badge so Main and Progress icons are distinguishable.
        draw.ellipse(
            (37, 37, 63, 63),
            fill=(15, 35, 70, 255),
            outline=(255, 255, 255, 255),
            width=2,
        )
        draw.rectangle(
            (48, 41, 52, 51),
            fill=(255, 255, 255, 255),
        )
        draw.polygon(
            [(42, 49), (50, 58), (58, 49)],
            fill=(255, 255, 255, 255),
        )
        return image
    except Exception:
        return create_tray_image()


def tray_notify(message, title=APP_NAME):
    if not TRAY_AVAILABLE:
        return

    icon = tray_icon

    if icon is None:
        return

    try:
        icon.notify(str(tr_dynamic(message)), str(tr_dynamic(title)))
    except Exception:
        pass


def tray_set_title(text):
    if not TRAY_AVAILABLE:
        return

    icon = tray_icon

    if icon is None:
        return

    try:
        value = str(tr_dynamic(text)).strip()
        if value:
            icon.title = (APP_NAME + " — " + value)[:120]
        else:
            icon.title = APP_NAME
    except Exception:
        pass


def _show_app_window():
    global mini_panel_user_opened_main

    try:
        # V32.6: the main manager and the download progress window are
        # independent, IDM-style. Opening one never replaces the other.
        mini_panel_user_opened_main = True

        root.deiconify()
        root.state("normal")
        root.lift()
        root.focus_force()
        root.attributes("-topmost", True)
        root.after(
            300,
            lambda: root.attributes("-topmost", False)
        )
    except Exception:
        pass


def show_app_from_tray(icon=None, item=None):
    gui_call(_show_app_window)


def open_downloads_from_tray(icon=None, item=None):
    try:
        os.startfile(DOWNLOADS)
    except Exception:
        pass


def _show_mini_progress_window():
    global mini_panel_user_hidden
    global mini_panel_in_tray

    if mini_panel is None:
        return

    try:
        mini_panel_user_hidden = False
        mini_panel_in_tray = False

        mini_panel.deiconify()
        mini_panel.state("normal")
        _mini_place_bottom_right()
        mini_panel.lift()
        mini_panel.attributes("-topmost", True)

        # Bring it forward, then let Windows manage z-order normally.
        mini_panel.after(
            750,
            lambda: mini_panel.attributes("-topmost", False),
        )
    except Exception:
        pass


def show_mini_from_tray(icon=None, item=None):
    gui_call(_show_mini_progress_window)


def hide_to_tray():
    global first_tray_notice
    global mini_panel_user_opened_main

    if app_quitting:
        return

    # V32.6: the full manager and the mini progress window are separate.
    # Minimizing/closing the full manager only affects the full manager.
    # It never creates, hides, enlarges or replaces the mini window.
    if not TRAY_AVAILABLE:
        # Fallback: keep normal Windows taskbar behavior.
        try:
            root.iconify()
        except Exception:
            pass
        return

    try:
        root.withdraw()

        if first_tray_notice:
            first_tray_notice = False
            tray_notify(
                "مازال خدام فالخلفية. كليكي على الأيقونة حد الساعة باش تحلو.",
                APP_NAME
            )
    except Exception:
        pass


def on_window_close():
    """
    X does NOT quit the downloader. It hides it next to the clock.
    Quit is available from the tray menu.
    """
    hide_to_tray()


def on_window_unmap(event):
    """
    V32.8:
    - Main manager Minimize (_) stays in the normal Windows taskbar.
    - Mini progress Minimize (_) goes to the system tray beside the clock.
    """
    global mini_panel_in_tray
    global mini_panel_user_hidden

    if app_quitting:
        return

    if event.widget is mini_panel:
        def move_mini_to_tray():
            if mini_panel is None or app_quitting:
                return

            try:
                if str(mini_panel.state()).lower() == "iconic":
                    hide_mini_to_own_tray()
            except Exception:
                pass

        try:
            mini_panel.after(100, move_mini_to_tray)
        except Exception:
            pass


def really_quit_app(icon=None, item=None):
    global app_quitting

    if app_quitting:
        return

    app_quitting = True
    stop_all_event.set()

    # Stop active yt-dlp processes
    with active_processes_lock:
        processes = list(active_processes)

    for process in processes:
        try:
            if process.poll() is None:
                process.terminate()
        except Exception:
            pass

    # Stop local bridge without blocking the Tk thread
    try:
        if bridge_server is not None:
            threading.Thread(
                target=bridge_server.shutdown,
                daemon=True
            ).start()
    except Exception:
        pass

    try:
        if tray_icon is not None:
            tray_icon.stop()
    except Exception:
        pass

    remove_mini_tray_icon()

    try:
        for _idx in list(job_progress_windows.keys()):
            _destroy_job_progress_window(_idx)
    except Exception:
        pass

    try:
        job_progress_minimized.clear()
        _stop_shared_progress_tray_if_unused()
    except Exception:
        pass

    gui_call(root.destroy)



def hide_mini_to_own_tray():
    global mini_panel_user_hidden
    global mini_panel_in_tray

    mini_panel_user_hidden = True
    mini_panel_in_tray = True

    try:
        if mini_panel is not None:
            mini_panel.withdraw()
    except Exception:
        pass

    ensure_mini_tray_icon()


def mini_tray_open(icon=None, item=None):
    gui_call(_show_mini_progress_window)


def mini_tray_open_main(icon=None, item=None):
    gui_call(_show_app_window)


def mini_tray_cancel(icon=None, item=None):
    gui_call(mini_cancel_downloads)



def remove_mini_tray_icon():
    """Remove only the dedicated Download Progress tray icon."""
    global mini_tray_icon
    global mini_tray_thread_started

    icon = mini_tray_icon
    mini_tray_icon = None
    mini_tray_thread_started = False

    if icon is not None:
        try:
            icon.stop()
        except Exception:
            pass


def _cleanup_mini_progress_ui():
    """
    Hide the mini progress window and remove its own tray icon.
    The main Z²SE tray icon remains untouched.
    """
    global mini_panel_user_hidden
    global mini_panel_in_tray

    mini_panel_user_hidden = True
    mini_panel_in_tray = False

    try:
        if mini_panel is not None:
            mini_panel.withdraw()
    except Exception:
        pass

    remove_mini_tray_icon()


def _mini_tray_loop():
    global mini_tray_icon
    global mini_tray_thread_started

    if not TRAY_AVAILABLE:
        mini_tray_thread_started = False
        return

    try:
        menu = pystray.Menu(
            pystray.MenuItem(
                tr("Show Download Progress"),
                mini_tray_open,
                default=True,
            ),
            pystray.MenuItem(
                tr("Open Main Z²SE"),
                mini_tray_open_main,
            ),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem(
                "Cancel Active Download",
                mini_tray_cancel,
            ),
        )

        mini_tray_icon = pystray.Icon(
            "z2se_download_progress",
            create_mini_tray_image(),
            f"Z²SE • {tr('Progress')}",
            menu,
        )

        mini_tray_icon.run()

    except Exception as exc:
        log(f"Mini tray ERROR: {exc}")

    finally:
        mini_tray_icon = None
        mini_tray_thread_started = False


def ensure_mini_tray_icon():
    global mini_tray_thread_started

    if not TRAY_AVAILABLE or app_quitting:
        return

    if mini_tray_thread_started:
        return

    mini_tray_thread_started = True

    threading.Thread(
        target=_mini_tray_loop,
        daemon=True,
        name="Z2SEDownloadProgressTray",
    ).start()


def start_system_tray():
    global tray_icon

    if not TRAY_AVAILABLE:
        gui_call(
            tray_status_var.set,
            "Tray: install pystray + pillow ⚠"
        )
        log(
            "Tray support unavailable. Run: "
            "python -m pip install pystray pillow"
        )
        return

    try:
        menu = pystray.Menu(
            pystray.MenuItem(
                "Open Z²SE",
                show_app_from_tray,
                default=True
            ),
            pystray.MenuItem(
                "Open Downloads",
                open_downloads_from_tray
            ),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem(
                "Quit",
                really_quit_app
            ),
        )

        tray_icon = pystray.Icon(
            "z2se_media_downloader",
            create_tray_image(),
            APP_NAME,
            menu
        )

        gui_call(
            tray_status_var.set,
            "Tray: ACTIVE ✅"
        )

        log("🟢 System tray ACTIVE — close/minimize = hide near clock.")

        tray_icon.run()

    except Exception as exc:
        gui_call(
            tray_status_var.set,
            "Tray: ERROR ❌"
        )
        log(f"Tray ERROR: {exc}")


# ============================================================
# PROCESS MANAGEMENT
# ============================================================

# Windows Toolhelp process snapshot flags.
_TH32CS_SNAPPROCESS = 0x00000002
_PROCESS_SUSPEND_RESUME = 0x0800
_PROCESS_QUERY_LIMITED_INFORMATION = 0x1000


class _PROCESSENTRY32W(ctypes.Structure):
    _fields_ = [
        ("dwSize", ctypes.c_ulong),
        ("cntUsage", ctypes.c_ulong),
        ("th32ProcessID", ctypes.c_ulong),
        ("th32DefaultHeapID", ctypes.c_void_p),
        ("th32ModuleID", ctypes.c_ulong),
        ("cntThreads", ctypes.c_ulong),
        ("th32ParentProcessID", ctypes.c_ulong),
        ("pcPriClassBase", ctypes.c_long),
        ("dwFlags", ctypes.c_ulong),
        ("szExeFile", ctypes.c_wchar * 260),
    ]


def _windows_process_parent_map():
    """Return {pid: parent_pid} without external dependencies."""
    if os.name != "nt":
        return {}

    kernel32 = ctypes.windll.kernel32
    snapshot = kernel32.CreateToolhelp32Snapshot(
        _TH32CS_SNAPPROCESS,
        0,
    )

    if snapshot in (0, ctypes.c_void_p(-1).value):
        return {}

    result = {}

    try:
        entry = _PROCESSENTRY32W()
        entry.dwSize = ctypes.sizeof(_PROCESSENTRY32W)

        ok = kernel32.Process32FirstW(
            snapshot,
            ctypes.byref(entry),
        )

        while ok:
            result[int(entry.th32ProcessID)] = int(
                entry.th32ParentProcessID
            )

            ok = kernel32.Process32NextW(
                snapshot,
                ctypes.byref(entry),
            )

    finally:
        kernel32.CloseHandle(snapshot)

    return result


def _process_tree_pids(root_pids):
    roots = {
        int(pid)
        for pid in root_pids
        if pid
    }

    if not roots:
        return set()

    parent_map = _windows_process_parent_map()

    tree = set(roots)
    changed = True

    while changed:
        changed = False

        for pid, parent_pid in parent_map.items():
            if parent_pid in tree and pid not in tree:
                tree.add(pid)
                changed = True

    return tree


def _nt_change_process_state(pid, suspend=True):
    """
    Suspend/resume one Windows process via NtSuspendProcess/NtResumeProcess.
    Returns True when the API call succeeds.
    """
    if os.name != "nt":
        return False

    kernel32 = ctypes.windll.kernel32
    ntdll = ctypes.windll.ntdll

    access = (
        _PROCESS_SUSPEND_RESUME
        | _PROCESS_QUERY_LIMITED_INFORMATION
    )

    handle = kernel32.OpenProcess(
        access,
        False,
        int(pid),
    )

    if not handle:
        return False

    try:
        if suspend:
            status = ntdll.NtSuspendProcess(handle)
        else:
            status = ntdll.NtResumeProcess(handle)

        return int(status) == 0

    finally:
        kernel32.CloseHandle(handle)


def _active_root_pids():
    with active_processes_lock:
        processes = list(active_processes)

    roots = []

    for process in processes:
        try:
            if process.poll() is None:
                roots.append(int(process.pid))
        except Exception:
            pass

    return roots


def pause_all_downloads():
    """Pause all active yt-dlp / FFmpeg process trees."""
    if pause_all_event.is_set():
        return

    root_pids = _active_root_pids()

    if not root_pids:
        return

    # Children first, then parents.
    pids = sorted(
        _process_tree_pids(root_pids),
        reverse=True,
    )

    suspended = set()

    for pid in pids:
        if _nt_change_process_state(
            pid,
            suspend=True,
        ):
            suspended.add(pid)

    with paused_process_ids_lock:
        paused_process_ids.clear()
        paused_process_ids.update(suspended)

    if suspended:
        pause_all_event.set()
        set_status("التحميل متوقف مؤقتاً ⏸")
        log(
            f"⏸ PAUSE requested — suspended {len(suspended)} process(es)."
        )

        _refresh_pause_controls()


def resume_all_downloads():
    """Resume exactly the processes suspended by pause_all_downloads()."""
    if not pause_all_event.is_set():
        return

    with paused_process_ids_lock:
        pids = list(paused_process_ids)

    # Parents first is safe for process trees.
    for pid in sorted(pids):
        _nt_change_process_state(
            pid,
            suspend=False,
        )

    with paused_process_ids_lock:
        paused_process_ids.clear()

    pause_all_event.clear()
    set_status("جاري التحميل...")
    log("▶ RESUME requested.")

    _refresh_pause_controls()


def _refresh_pause_controls():
    """Keep main-window and mini-panel Pause/Resume buttons unambiguous."""
    running = downloads_are_running()
    paused = pause_all_event.is_set()

    pairs = (
        (main_pause_button, "pause"),
        (main_resume_button, "resume"),
        (mini_pause_button, "pause"),
        (mini_resume_button, "resume"),
    )

    for button, role in pairs:
        if button is None:
            continue

        try:
            if role == "pause":
                button.configure(
                    state=(
                        "normal"
                        if running and not paused
                        else "disabled"
                    )
                )
            else:
                button.configure(
                    state=(
                        "normal"
                        if running and paused
                        else "disabled"
                    )
                )
        except Exception:
            pass


def toggle_pause_downloads():
    # Kept for backward compatibility, but the visible UI now has
    # separate Pause and Resume buttons so there is no ambiguity.
    if pause_all_event.is_set():
        resume_all_downloads()
    else:
        pause_all_downloads()


def _reset_pause_state_for_new_session():
    # Defensive cleanup in case a previous job ended while paused.
    if pause_all_event.is_set():
        resume_all_downloads()

    pause_all_event.clear()

    with paused_process_ids_lock:
        paused_process_ids.clear()

    _refresh_pause_controls()



def _current_job_index():
    try:
        value = getattr(
            job_runtime_context,
            "index",
            None,
        )
        return int(value) if value is not None else None
    except Exception:
        return None


def job_is_cancelled(index=None):
    if index is None:
        index = _current_job_index()

    if index is None:
        return False

    with cancelled_job_lock:
        return int(index) in cancelled_job_indices


def should_stop_current_job():
    return stop_all_event.is_set() or job_is_cancelled()


def _active_processes_for_job(index):
    index = int(index)
    result = []

    with active_processes_lock:
        processes = list(active_processes)

    with process_job_map_lock:
        mapping = dict(process_job_map)

    for process in processes:
        try:
            if (
                process.poll() is None
                and mapping.get(process) == index
            ):
                result.append(process)
        except Exception:
            pass

    return result


def pause_download_job(index):
    index = int(index)

    if job_is_cancelled(index):
        return

    processes = _active_processes_for_job(index)

    if not processes:
        return

    suspended = set()

    for process in processes:
        try:
            pids = _process_tree_pids([process.pid])

            for pid in sorted(pids, reverse=True):
                if _nt_change_process_state(pid, suspend=True):
                    suspended.add(pid)
        except Exception:
            pass

    if suspended:
        with paused_job_lock:
            paused_job_indices.add(index)
            paused_job_processes[index] = suspended

        update_tree_status(index, "Paused ⏸")
        log(
            f"[{index}] ⏸ PAUSE — "
            f"{len(suspended)} process(es) suspended."
        )


def resume_download_job(index):
    index = int(index)

    with paused_job_lock:
        pids = set(
            paused_job_processes.get(index, set())
        )

    for pid in sorted(pids):
        try:
            _nt_change_process_state(pid, suspend=False)
        except Exception:
            pass

    with paused_job_lock:
        paused_job_indices.discard(index)
        paused_job_processes.pop(index, None)

    if not job_is_cancelled(index):
        update_tree_status(index, "Downloading")
        log(f"[{index}] ▶ RESUME")


def cancel_download_job(index):
    index = int(index)

    # Resume first so termination is deterministic.
    with paused_job_lock:
        paused = index in paused_job_indices

    if paused:
        resume_download_job(index)

    with cancelled_job_lock:
        cancelled_job_indices.add(index)

    update_tree_status(index, "Cancelling…")

    for process in _active_processes_for_job(index):
        try:
            if process.poll() is None:
                process.terminate()
        except Exception:
            pass

    log(f"[{index}] ✕ CANCEL requested.")


def _finish_job_runtime_state(index):
    index = int(index)

    with paused_job_lock:
        paused_job_indices.discard(index)
        paused_job_processes.pop(index, None)


def register_process(process):
    with active_processes_lock:
        active_processes.add(process)

    current_job = _current_job_index()

    if current_job is not None:
        with process_job_map_lock:
            process_job_map[process] = current_job

        # If the user already cancelled this job, kill any late/retry process.
        if job_is_cancelled(current_job):
            try:
                process.terminate()
            except Exception:
                pass

        # If this job is paused and a fallback creates a new process,
        # immediately suspend the new process as well.
        with paused_job_lock:
            job_paused = current_job in paused_job_indices

        if job_paused:
            try:
                suspended = set()

                for pid in sorted(
                    _process_tree_pids([process.pid]),
                    reverse=True,
                ):
                    if _nt_change_process_state(pid, suspend=True):
                        suspended.add(pid)

                with paused_job_lock:
                    paused_job_processes.setdefault(
                        current_job,
                        set(),
                    ).update(suspended)
            except Exception:
                pass

    # A queued job can create a new FFmpeg/yt-dlp process while the user
    # has the session paused. Pause it immediately as well.
    if pause_all_event.is_set():
        try:
            pids = _process_tree_pids(
                [process.pid]
            )

            newly_paused = set()

            for pid in sorted(
                pids,
                reverse=True,
            ):
                if _nt_change_process_state(
                    pid,
                    suspend=True,
                ):
                    newly_paused.add(pid)

            with paused_process_ids_lock:
                paused_process_ids.update(
                    newly_paused
                )
        except Exception:
            pass


def unregister_process(process):
    with active_processes_lock:
        active_processes.discard(process)

    with process_job_map_lock:
        process_job_map.pop(process, None)


def stop_all():
    global single_running

    # Cancel must work even if the download is currently paused.
    if pause_all_event.is_set():
        resume_all_downloads()

    stop_all_event.set()

    try:
        with browser_queue_condition:
            browser_queue_condition.notify_all()
    except Exception:
        pass

    try:
        with live_queue_condition:
            live_queue_condition.notify_all()
    except Exception:
        pass

    with active_processes_lock:
        processes = list(active_processes)

    for process in processes:
        try:
            if process.poll() is None:
                process.terminate()
        except Exception:
            pass

    set_status("إيقاف التحميلات...")
    log("⛔ STOP ALL requested.")


# ============================================================
# PO TOKEN PROVIDER
# ============================================================

def pot_ping():
    try:
        with urllib.request.urlopen(POT_PING_URL, timeout=1) as response:
            return 200 <= response.status < 300
    except Exception:
        return False


def ensure_pot_fast():
    """
    Fast path used immediately before downloads.
    If the provider was already confirmed ACTIVE at app startup,
    do not ping/restart it again. A 403 will still trigger auto-repair.
    """
    if pot_ready:
        return True
    return check_and_start_pot()


def check_and_start_pot():
    global pot_ready

    with pot_lock:
        if pot_ping():
            pot_ready = True
            set_pot_status("PO Token: ACTIVE ✅")
            return True

        if not os.path.exists(POT_PLUGIN):
            pot_ready = False
            set_pot_status("PO Token: plugin missing")
            log("PO Token plugin غير موجود.")
            return False

        if not os.path.exists(POT_SERVER_FILE):
            pot_ready = False
            set_pot_status("PO Token: server missing")
            log("PO Token server غير موجود.")
            return False

        deno = shutil.which("deno")
        if not deno:
            pot_ready = False
            set_pot_status("PO Token: Deno missing")
            log("Deno غير موجود.")
            return False

        if not os.path.isdir(POT_WORKDIR):
            pot_ready = False
            set_pot_status("PO Token: workdir missing")
            log(f"PO Token workdir غير موجود: {POT_WORKDIR}")
            return False

        try:
            creationflags = 0
            startupinfo = None

            if os.name == "nt":
                creationflags = subprocess.CREATE_NO_WINDOW
                startupinfo = subprocess.STARTUPINFO()
                startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW

            subprocess.Popen(
                [
                    deno,
                    "run",
                    "--allow-env",
                    "--allow-net",
                    "--allow-ffi=.",
                    "--allow-read=.",
                    "../src/main.ts",
                ],
                cwd=POT_WORKDIR,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                creationflags=creationflags,
                startupinfo=startupinfo,
            )

            for _ in range(15):
                if pot_ping():
                    pot_ready = True
                    set_pot_status("PO Token: ACTIVE ✅")
                    log("PO Token provider بدا وخدام ✅")
                    return True
                time.sleep(0.7)

        except Exception as exc:
            log(f"PO Token ERROR: {exc}")

        pot_ready = False
        set_pot_status("PO Token: unavailable")
        return False


# ============================================================
# YT-DLP UPDATE
# ============================================================


# ============================================================
# Z²SE V32.28 — SAFE GITHUB RELEASE AUTO-UPDATER
# ============================================================

APP_UPDATE_DEFAULTS = {
    "enabled": True,
    "auto_install": True,
    "github_owner": "zoubeir91",
    "github_repo": "Z2SE-Media-Downloader",
    "asset_name": APP_UPDATE_ASSET_DEFAULT,
    "check_interval_hours": 24,
}


def _load_app_update_config():
    config = dict(APP_UPDATE_DEFAULTS)

    try:
        if os.path.isfile(APP_UPDATE_CONFIG_FILE):
            with open(
                APP_UPDATE_CONFIG_FILE,
                "r",
                encoding="utf-8",
            ) as handle:
                saved = json.load(handle)

            if isinstance(saved, dict):
                config.update(saved)
    except Exception as exc:
        log(f"App updater config read warning: {exc}")

    return config


def _save_app_update_config(config):
    merged = dict(APP_UPDATE_DEFAULTS)
    merged.update(
        config
        if isinstance(config, dict)
        else {}
    )

    try:
        with open(
            APP_UPDATE_CONFIG_FILE,
            "w",
            encoding="utf-8",
        ) as handle:
            json.dump(
                merged,
                handle,
                indent=2,
                ensure_ascii=False,
            )

        return True
    except Exception as exc:
        log(f"App updater config save ERROR: {exc}")
        return False


def _version_tuple(value):
    numbers = re.findall(
        r"\d+",
        str(value or ""),
    )

    if not numbers:
        return (0,)

    return tuple(
        int(number)
        for number in numbers
    )


def _version_is_newer(candidate, current):
    left = list(
        _version_tuple(candidate)
    )
    right = list(
        _version_tuple(current)
    )

    size = max(
        len(left),
        len(right),
    )

    left += [0] * (
        size - len(left)
    )
    right += [0] * (
        size - len(right)
    )

    return tuple(left) > tuple(right)


def _read_app_update_state():
    try:
        if os.path.isfile(
            APP_UPDATE_STATE_FILE
        ):
            with open(
                APP_UPDATE_STATE_FILE,
                "r",
                encoding="utf-8",
            ) as handle:
                value = json.load(
                    handle
                )

            return (
                value
                if isinstance(value, dict)
                else {}
            )
    except Exception:
        pass

    return {}


def _save_app_update_state(**values):
    state = _read_app_update_state()
    state.update(
        values
    )

    try:
        with open(
            APP_UPDATE_STATE_FILE,
            "w",
            encoding="utf-8",
        ) as handle:
            json.dump(
                state,
                handle,
                indent=2,
                ensure_ascii=False,
            )
    except Exception:
        pass


def _app_update_check_is_recent(config):
    state = _read_app_update_state()
    raw = state.get(
        "last_check"
    )

    if not raw:
        return False

    try:
        last = datetime.fromisoformat(
            raw
        )
    except Exception:
        return False

    try:
        hours = max(
            1,
            int(
                config.get(
                    "check_interval_hours",
                    24,
                )
                or 24
            ),
        )
    except Exception:
        hours = 24

    return (
        datetime.now() - last
        < timedelta(
            hours=hours
        )
    )


def _github_release_request(owner, repo):
    owner = str(
        owner or ""
    ).strip()
    repo = str(
        repo or ""
    ).strip()

    if (
        not owner
        or not repo
    ):
        raise ValueError(
            "GitHub update repository is not configured."
        )

    api_url = (
        "https://api.github.com/repos/"
        + owner
        + "/"
        + repo
        + "/releases/latest"
    )

    request = urllib.request.Request(
        api_url,
        headers={
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2026-03-10",
            "User-Agent": (
                "Z2SE-Media-Downloader/"
                + APP_VERSION
            ),
        },
        method="GET",
    )

    with urllib.request.urlopen(
        request,
        timeout=20,
    ) as response:
        payload = response.read()

    release = json.loads(
        payload.decode(
            "utf-8",
            errors="replace",
        )
    )

    if not isinstance(
        release,
        dict,
    ):
        raise RuntimeError(
            "GitHub returned invalid release metadata."
        )

    return release


def _find_release_asset(release, asset_name):
    for asset in (
        release.get(
            "assets"
        )
        or []
    ):
        if (
            isinstance(
                asset,
                dict,
            )
            and str(
                asset.get(
                    "name",
                    "",
                )
            ) == str(
                asset_name
            )
        ):
            return asset

    return None


def _sha256_file(path):
    digest = hashlib.sha256()

    with open(
        path,
        "rb",
    ) as handle:
        while True:
            block = handle.read(
                1024 * 1024
            )

            if not block:
                break

            digest.update(
                block
            )

    return digest.hexdigest()


def _download_update_asset(asset, target_file):
    url = str(
        asset.get(
            "browser_download_url",
            "",
        )
        or ""
    ).strip()

    if not url.startswith(
        "https://"
    ):
        raise RuntimeError(
            "Update asset URL is missing or not HTTPS."
        )

    request = urllib.request.Request(
        url,
        headers={
            "User-Agent": (
                "Z2SE-Media-Downloader/"
                + APP_VERSION
            )
        },
        method="GET",
    )

    os.makedirs(
        os.path.dirname(
            target_file
        ),
        exist_ok=True,
    )

    temp_file = (
        target_file
        + ".part"
    )

    try:
        if os.path.isfile(
            temp_file
        ):
            os.remove(
                temp_file
            )
    except Exception:
        pass

    with urllib.request.urlopen(
        request,
        timeout=45,
    ) as response, open(
        temp_file,
        "wb",
    ) as output:
        while True:
            block = response.read(
                1024 * 1024
            )

            if not block:
                break

            output.write(
                block
            )

    os.replace(
        temp_file,
        target_file,
    )


def _safe_update_member_name(name):
    value = str(
        name or ""
    ).replace(
        "\\",
        "/",
    )

    if (
        not value
        or value.startswith(
            "/"
        )
        or ":" in value
    ):
        return False

    pieces = [
        piece
        for piece in value.split(
            "/"
        )
        if piece not in (
            "",
            ".",
        )
    ]

    if (
        not pieces
        or ".." in pieces
    ):
        return False

    return True


def _verify_update_payload(staging_dir, expected_version):
    manifest_path = os.path.join(
        staging_dir,
        "update_manifest.json",
    )

    if not os.path.isfile(
        manifest_path
    ):
        raise RuntimeError(
            "update_manifest.json is missing."
        )

    with open(
        manifest_path,
        "r",
        encoding="utf-8",
    ) as handle:
        manifest = json.load(
            handle
        )

    manifest_version = str(
        manifest.get(
            "version",
            "",
        )
    ).lstrip(
        "vV"
    )

    expected_clean = str(
        expected_version
    ).lstrip(
        "vV"
    )

    if (
        manifest_version
        != expected_clean
    ):
        raise RuntimeError(
            "Update manifest version does not match GitHub release tag."
        )

    files = manifest.get(
        "files"
    )

    if (
        not isinstance(
            files,
            list,
        )
        or not files
    ):
        raise RuntimeError(
            "Update manifest has no files."
        )

    has_app = False

    for item in files:
        if not isinstance(
            item,
            dict,
        ):
            raise RuntimeError(
                "Invalid file entry in update manifest."
            )

        rel = str(
            item.get(
                "path",
                "",
            )
        ).replace(
            "\\",
            "/",
        )

        if not _safe_update_member_name(
            rel
        ):
            raise RuntimeError(
                "Unsafe path in update manifest: "
                + rel
            )

        expected_main = (
            "z2se.exe"
            if IS_COMPILED
            else "app.py"
        )

        if rel.lower() == expected_main:
            has_app = True

        expected_hash = str(
            item.get(
                "sha256",
                "",
            )
        ).lower().strip()

        source = os.path.join(
            staging_dir,
            *rel.split(
                "/"
            ),
        )

        if not os.path.isfile(
            source
        ):
            raise RuntimeError(
                "Missing update file: "
                + rel
            )

        actual_hash = _sha256_file(
            source
        )

        if (
            not expected_hash
            or actual_hash != expected_hash
        ):
            raise RuntimeError(
                "SHA-256 mismatch for "
                + rel
            )

    if not has_app:
        raise RuntimeError(
            "Update package does not contain "
            + (
                "Z2SE.exe."
                if IS_COMPILED
                else "app.py."
            )
        )

    return manifest


def _extract_update_zip(zip_path, staging_dir):
    if os.path.isdir(
        staging_dir
    ):
        shutil.rmtree(
            staging_dir,
            ignore_errors=True,
        )

    os.makedirs(
        staging_dir,
        exist_ok=True,
    )

    with zipfile.ZipFile(
        zip_path,
        "r",
    ) as archive:
        for info in archive.infolist():
            name = info.filename

            if not _safe_update_member_name(
                name
            ):
                raise RuntimeError(
                    "Unsafe path in update ZIP: "
                    + str(name)
                )

        archive.extractall(
            staging_dir
        )


def _launch_external_updater(staging_dir, version):
    """
    Python mode uses the trusted Python updater first.

    The unsigned Z2SE_Updater.exe can be blocked by Windows Application
    Control on this PC, while pythonw.exe is already trusted/allowed.
    """
    # Current installation runs app.py through Python, so always prefer the
    # Python updater in that mode.
    if (
        not IS_COMPILED
        and os.path.isfile(
            APP_UPDATER_PY
        )
    ):
        python_exe = sys.executable

        if python_exe.lower().endswith(
            "python.exe"
        ):
            candidate = os.path.join(
                os.path.dirname(
                    python_exe
                ),
                "pythonw.exe",
            )

            if os.path.isfile(
                candidate
            ):
                python_exe = candidate

        command = [
            python_exe,
            APP_UPDATER_PY,
            "--apply",
            staging_dir,
            "--app-dir",
            APP_DIR,
            "--version",
            str(version),
            "--parent-pid",
            str(
                os.getpid()
            ),
            "--launch-exe",
            sys.executable,
        ]

        subprocess.Popen(
            command,
            cwd=APP_DIR,
            creationflags=(
                subprocess.CREATE_NO_WINDOW
                if os.name == "nt"
                else 0
            ),
        )

        return True

    # Compiled mode can still use the small compiled updater.
    if os.path.isfile(
        APP_UPDATER_EXE
    ):
        command = [
            APP_UPDATER_EXE,
            "--apply",
            staging_dir,
            "--app-dir",
            APP_DIR,
            "--version",
            str(version),
            "--parent-pid",
            str(
                os.getpid()
            ),
            "--target",
            (
                "Z2SE.exe"
                if IS_COMPILED
                else "app.py"
            ),
        ]

        subprocess.Popen(
            command,
            cwd=APP_DIR,
            creationflags=(
                subprocess.CREATE_NO_WINDOW
                if os.name == "nt"
                else 0
            ),
        )

        return True

    # Last fallback for Python/dev installs.
    if os.path.isfile(
        APP_UPDATER_PY
    ):
        python_exe = sys.executable

        if python_exe.lower().endswith(
            "python.exe"
        ):
            candidate = os.path.join(
                os.path.dirname(
                    python_exe
                ),
                "pythonw.exe",
            )

            if os.path.isfile(
                candidate
            ):
                python_exe = candidate

        subprocess.Popen(
            [
                python_exe,
                APP_UPDATER_PY,
                "--apply",
                staging_dir,
                "--app-dir",
                APP_DIR,
                "--version",
                str(version),
                "--parent-pid",
                str(
                    os.getpid()
                ),
                "--launch-exe",
                sys.executable,
            ],
            cwd=APP_DIR,
            creationflags=(
                subprocess.CREATE_NO_WINDOW
                if os.name == "nt"
                else 0
            ),
        )

        return True

    raise RuntimeError(
        "z2se_updater.pyw is missing."
    )


def _queue_app_update_retry():
    global app_update_pending

    if app_update_pending:
        return

    app_update_pending = True

    def retry():
        global app_update_pending
        app_update_pending = False

        threading.Thread(
            target=check_z2se_app_update,
            kwargs={
                "manual": False,
                "force": True,
            },
            daemon=True,
        ).start()

    try:
        root.after(
            5 * 60 * 1000,
            retry,
        )
    except Exception:
        app_update_pending = False


def check_z2se_app_update(
    manual=False,
    force=False,
    auto_confirm=False,
):
    global app_update_in_progress

    with app_update_lock:
        if app_update_in_progress:
            return False

        config = _load_app_update_config()

        if (
            not manual
            and not config.get(
                "enabled",
                True,
            )
        ):
            return False

        owner = str(
            config.get(
                "github_owner",
                "",
            )
            or ""
        ).strip()

        repo = str(
            config.get(
                "github_repo",
                "",
            )
            or ""
        ).strip()

        if (
            not owner
            or not repo
        ):
            if manual:
                gui_call(
                    messagebox.showinfo,
                    "Z²SE Updates",
                    "خاص غير نحدد GitHub owner و repository مرة وحدة.\n\n"
                    "Tools → Update settings",
                )
            return False

        if (
            not manual
            and not force
            and _app_update_check_is_recent(
                config
            )
        ):
            return True

        app_update_in_progress = True

    try:
        log(
            "🔄 Checking Z²SE application update..."
        )

        release = _github_release_request(
            owner,
            repo,
        )

        _save_app_update_state(
            last_check=datetime.now().isoformat(),
        )

        latest_tag = str(
            release.get(
                "tag_name",
                "",
            )
            or ""
        ).strip()

        if not latest_tag:
            raise RuntimeError(
                "Latest GitHub release has no tag."
            )

        if not _version_is_newer(
            latest_tag,
            APP_VERSION,
        ):
            log(
                f"✅ Z²SE is current: v{APP_VERSION}"
            )

            if manual:
                gui_call(
                    messagebox.showinfo,
                    "Z²SE Updates",
                    "راه عندك آخر نسخة دابا ✅\n\n"
                    f"Installed: v{APP_VERSION}\n"
                    f"Latest: {latest_tag}",
                )

            return True

        asset_name = str(
            config.get(
                "asset_name",
                APP_UPDATE_ASSET_DEFAULT,
            )
            or APP_UPDATE_ASSET_DEFAULT
        )

        asset = _find_release_asset(
            release,
            asset_name,
        )

        if asset is None:
            raise RuntimeError(
                "Latest release is missing asset: "
                + asset_name
            )

        log(
            f"🆕 Z²SE update found: {latest_tag}"
        )

        if downloads_are_running():
            log(
                "Update postponed: download is active."
            )

            if not manual:
                _queue_app_update_retry()
            else:
                gui_call(
                    messagebox.showinfo,
                    "Z²SE Update",
                    "كاينة نسخة جديدة ولكن كاين download خدام.\n"
                    "منين يسالي التحميل عاود Check Updates.",
                )

            return False

        auto_install = bool(
            config.get(
                "auto_install",
                True,
            )
        )

        if (
            (manual and not auto_confirm)
            or not auto_install
        ):
            answer_holder = {
                "value": False
            }
            done_event = threading.Event()

            def ask_user():
                try:
                    answer_holder[
                        "value"
                    ] = messagebox.askyesno(
                        "Z²SE Update",
                        "كاينة نسخة جديدة ✅\n\n"
                        f"Installed: v{APP_VERSION}\n"
                        f"New: {latest_tag}\n\n"
                        "نحمّلها ونركبها دابا؟",
                    )
                finally:
                    done_event.set()

            gui_call(
                ask_user
            )
            done_event.wait()

            if not answer_holder[
                "value"
            ]:
                return False

        version_clean = latest_tag.lstrip(
            "vV"
        )

        os.makedirs(
            APP_UPDATE_STAGING,
            exist_ok=True,
        )

        zip_path = os.path.join(
            APP_UPDATE_STAGING,
            "Z2SE_UPDATE_"
            + version_clean
            + ".zip",
        )

        extract_dir = os.path.join(
            APP_UPDATE_STAGING,
            "payload_"
            + version_clean,
        )

        log(
            "⬇ Downloading Z²SE update..."
        )

        _download_update_asset(
            asset,
            zip_path,
        )

        expected_digest = str(
            asset.get(
                "digest",
                "",
            )
            or ""
        ).strip().lower()

        actual_digest = _sha256_file(
            zip_path
        )

        if expected_digest.startswith(
            "sha256:"
        ):
            expected_hash = expected_digest.split(
                ":",
                1,
            )[1]

            if (
                not expected_hash
                or actual_digest != expected_hash
            ):
                raise RuntimeError(
                    "GitHub release asset SHA-256 verification failed."
                )

            log(
                "🔐 GitHub asset SHA-256 verified."
            )
        else:
            log(
                "ℹ GitHub asset digest unavailable; internal file hashes will be verified."
            )

        _extract_update_zip(
            zip_path,
            extract_dir,
        )

        _verify_update_payload(
            extract_dir,
            version_clean,
        )

        log(
            "🔐 Update package files verified."
        )
        log(
            "🛡 Creating rollback backup and applying update..."
        )

        _save_app_update_state(
            pending_version=version_clean,
            pending_started=datetime.now().isoformat(),
        )

        _launch_external_updater(
            extract_dir,
            version_clean,
        )

        # Give the external updater a moment to initialize, then quit cleanly.
        def quit_for_update():
            really_quit_app()

        gui_call(
            root.after,
            500,
            quit_for_update,
        )

        return True

    except Exception as exc:
        log(
            "❌ Z²SE app update ERROR: "
            + str(exc)
        )

        if manual:
            gui_call(
                messagebox.showerror,
                "Z²SE Update",
                "Update ما قدرش يكمل:\n\n"
                + str(exc),
            )

        return False

    finally:
        app_update_in_progress = False


def manual_z2se_update():
    """One-click update check from the Tools menu."""
    threading.Thread(
        target=check_z2se_app_update,
        kwargs={
            "manual": True,
            "force": True,
            "auto_confirm": True,
        },
        daemon=True,
    ).start()


def _show_update_settings():
    config = _load_app_update_config()

    window = tk.Toplevel(
        root
    )
    window.title(
        tr("Z²SE Update Settings")
    )
    window.resizable(
        False,
        False,
    )
    window.transient(
        root
    )
    window.grab_set()

    frame = ttk.Frame(
        window,
        padding=18,
    )
    frame.pack(
        fill="both",
        expand=True,
    )

    owner_var = tk.StringVar(
        value=str(
            config.get(
                "github_owner",
                "",
            )
            or ""
        )
    )
    repo_var = tk.StringVar(
        value=str(
            config.get(
                "github_repo",
                "",
            )
            or ""
        )
    )
    enabled_var = tk.BooleanVar(
        value=bool(
            config.get(
                "enabled",
                True,
            )
        )
    )
    auto_var = tk.BooleanVar(
        value=bool(
            config.get(
                "auto_install",
                True,
            )
        )
    )

    ttk.Label(
        frame,
        text=tr("GitHub owner"),
    ).grid(
        row=0,
        column=0,
        sticky="w",
        pady=(0, 5),
    )

    ttk.Entry(
        frame,
        textvariable=owner_var,
        width=38,
    ).grid(
        row=1,
        column=0,
        sticky="ew",
        pady=(0, 12),
    )

    ttk.Label(
        frame,
        text=tr("Update repository"),
    ).grid(
        row=2,
        column=0,
        sticky="w",
        pady=(0, 5),
    )

    ttk.Entry(
        frame,
        textvariable=repo_var,
        width=38,
    ).grid(
        row=3,
        column=0,
        sticky="ew",
        pady=(0, 12),
    )

    ttk.Checkbutton(
        frame,
        text=tr("Check automatically"),
        variable=enabled_var,
    ).grid(
        row=4,
        column=0,
        sticky="w",
        pady=3,
    )

    ttk.Checkbutton(
        frame,
        text=tr("Install automatically when idle"),
        variable=auto_var,
    ).grid(
        row=5,
        column=0,
        sticky="w",
        pady=3,
    )

    ttk.Label(
        frame,
        text=(
            "Release asset: "
            + APP_UPDATE_ASSET_DEFAULT
            + (" • EXE mode" if IS_COMPILED else " • Python dev mode")
        ),
    ).grid(
        row=6,
        column=0,
        sticky="w",
        pady=(12, 8),
    )

    buttons = ttk.Frame(
        frame
    )
    buttons.grid(
        row=7,
        column=0,
        sticky="e",
        pady=(10, 0),
    )

    def save_settings():
        new_config = dict(
            APP_UPDATE_DEFAULTS
        )
        new_config.update(
            {
                "github_owner": owner_var.get().strip(),
                "github_repo": repo_var.get().strip(),
                "enabled": bool(
                    enabled_var.get()
                ),
                "auto_install": bool(
                    auto_var.get()
                ),
            }
        )

        if _save_app_update_config(
            new_config
        ):
            window.destroy()
            messagebox.showinfo(
                "Z²SE Updates",
                "Update settings محفوظين ✅",
            )

    ttk.Button(
        buttons,
        text=tr("Cancel"),
        command=window.destroy,
    ).pack(
        side="left",
        padx=4,
    )

    ttk.Button(
        buttons,
        text=tr("Save"),
        command=save_settings,
    ).pack(
        side="left",
        padx=4,
    )

    try:
        window.update_idletasks()

        x = (
            root.winfo_rootx()
            + max(
                0,
                (
                    root.winfo_width()
                    - window.winfo_width()
                )
                // 2,
            )
        )
        y = (
            root.winfo_rooty()
            + max(
                0,
                (
                    root.winfo_height()
                    - window.winfo_height()
                )
                // 2,
            )
        )

        window.geometry(
            f"+{x}+{y}"
        )
    except Exception:
        pass


def show_update_settings():
    _show_update_settings()


def _show_last_app_update_result():
    if not os.path.isfile(
        APP_UPDATE_RESULT_FILE
    ):
        return

    try:
        with open(
            APP_UPDATE_RESULT_FILE,
            "r",
            encoding="utf-8",
        ) as handle:
            result = json.load(
                handle
            )

        status = str(
            result.get(
                "status",
                "",
            )
        )

        version = str(
            result.get(
                "version",
                "",
            )
        )

        if status == "success":
            log(
                "✅ Auto-update completed successfully"
                + (
                    f": v{version}"
                    if version
                    else ""
                )
            )

            try:
                os.remove(
                    APP_UPDATE_RESULT_FILE
                )
            except Exception:
                pass

        elif status == "rolled_back":
            log(
                "⚠ Auto-update failed and rollback restored the previous version."
            )

            gui_call(
                messagebox.showwarning,
                "Z²SE Update",
                "Update فشلات ولكن Rollback رجع النسخة القديمة بنجاح ✅",
            )

    except Exception:
        pass


def schedule_z2se_auto_update_check():
    def launch_check():
        threading.Thread(
            target=check_z2se_app_update,
            kwargs={
                "manual": False,
                "force": False,
            },
            daemon=True,
        ).start()

    try:
        # Do not compete with browser auto-launch / bridge startup.
        root.after(
            12000,
            launch_check,
        )
    except Exception:
        pass



def read_last_update():
    try:
        if not os.path.exists(UPDATE_STATE):
            return None

        with open(UPDATE_STATE, "r", encoding="utf-8") as f:
            data = json.load(f)

        value = data.get("last_check")
        return datetime.fromisoformat(value) if value else None
    except Exception:
        return None


def save_last_update():
    try:
        with open(UPDATE_STATE, "w", encoding="utf-8") as f:
            json.dump(
                {"last_check": datetime.now().isoformat()},
                f,
                indent=2
            )
    except Exception:
        pass


def set_update_button_state(state):
    """
    Safe for startup/background threads and UI rebuilds.
    If the button is not created yet, simply skip the visual state change.
    """
    button = globals().get("update_button")

    if button is None:
        return

    try:
        gui_call(button.configure, state=state)
    except Exception:
        pass


def update_ytdlp(force=False, quiet_if_recent=True):
    global update_in_progress

    with update_lock:
        if not os.path.exists(YTDLP):
            set_update_status("yt-dlp: missing ❌")
            log("yt-dlp.exe غير موجود.")
            return False

        if not force:
            last = read_last_update()
            if last and datetime.now() - last < timedelta(hours=24):
                set_update_status("yt-dlp: checked ✅")
                if not quiet_if_recent:
                    log("yt-dlp checked recently; no update needed.")
                return True

        update_in_progress = True
        set_update_button_state("disabled")
        set_update_status("yt-dlp: updating...")
        log("Checking yt-dlp update...")

        try:
            creationflags = (
                subprocess.CREATE_NO_WINDOW
                if os.name == "nt"
                else 0
            )

            process = subprocess.Popen(
                [YTDLP, "-U"],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                encoding="utf-8",
                errors="replace",
                creationflags=creationflags,
            )

            for line in process.stdout:
                line = line.strip()
                if line:
                    log("[UPDATE] " + line)

            code = process.wait()

            if code == 0:
                save_last_update()
                set_update_status("yt-dlp: UPDATED / OK ✅")
                result = True
            else:
                set_update_status("yt-dlp: update failed")
                log(f"Update فشل. Code: {code}")
                result = False

        except Exception as exc:
            set_update_status("yt-dlp: update error")
            log(f"Update ERROR: {exc}")
            result = False

        update_in_progress = False
        set_update_button_state("normal")
        return result


def manual_update():
    if downloads_are_running():
        messagebox.showwarning(
            "Download",
            "خلي التحميلات تسالي قبل update."
        )
        return

    threading.Thread(
        target=update_ytdlp,
        args=(True, False),
        daemon=True
    ).start()


def auto_repair(reason="download failure"):
    global last_repair_time

    with repair_lock:
        now = time.time()

        # If another parallel job repaired recently, only re-check PO Token.
        if now - last_repair_time < 120:
            log("Smart Recovery: repair already ran recently; rechecking PO Token.")
            check_and_start_pot()
            return

        log(f"⚕ Smart Recovery triggered: {reason}")
        log("Smart Recovery: refreshing yt-dlp + PO Token provider...")
        update_ytdlp(force=True, quiet_if_recent=False)
        check_and_start_pot()
        last_repair_time = time.time()


def _tool_version_line(path, args=("--version",), timeout=8):
    if not path:
        return None
    try:
        result = subprocess.run(
            [path, *args],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=timeout,
            creationflags=(subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0),
        )
        if result.returncode != 0:
            return None
        lines = [line.strip() for line in (result.stdout or "").splitlines() if line.strip()]
        return lines[0] if lines else "OK"
    except Exception:
        return None


def _bridge_is_alive():
    try:
        with urllib.request.urlopen(BRIDGE_URL + "/ping", timeout=1.5) as response:
            return 200 <= response.status < 300
    except Exception:
        return False


def collect_health_report():
    """Read-only diagnostics used by the professional Health Check window."""
    ytdlp_version = _tool_version_line(YTDLP)
    ffmpeg_version = _tool_version_line(FFMPEG, ("-version",)) if FFMPEG else None
    ffprobe_version = _tool_version_line(FFPROBE, ("-version",)) if FFPROBE else None
    deno = shutil.which("deno")
    pot_plugin_ok = os.path.isfile(POT_PLUGIN)
    pot_server_ok = os.path.isfile(POT_SERVER_FILE) and os.path.isdir(POT_WORKDIR)
    pot_live = pot_ping()
    bridge_live = _bridge_is_alive()
    update_cfg = _load_app_update_config()
    update_ready = bool(
        str(update_cfg.get("github_owner", "") or "").strip()
        and str(update_cfg.get("github_repo", "") or "").strip()
        and (os.path.isfile(APP_UPDATER_PY) or os.path.isfile(APP_UPDATER_EXE))
    )

    items = [
        {
            "name": "yt-dlp",
            "ok": bool(ytdlp_version),
            "detail": ytdlp_version or "Engine unavailable",
            "critical": True,
        },
        {
            "name": "FFmpeg",
            "ok": bool(ffmpeg_version),
            "detail": (ffmpeg_version or "FFmpeg unavailable")[:92],
            "critical": True,
        },
        {
            "name": "FFprobe",
            "ok": bool(ffprobe_version),
            "detail": (ffprobe_version or "FFprobe unavailable")[:92],
            "critical": True,
        },
        {
            "name": "PO Token",
            "ok": bool(pot_live),
            "detail": (
                "Provider active"
                if pot_live
                else "Provider offline" if (pot_plugin_ok and pot_server_ok and deno)
                else "Provider components incomplete"
            ),
            "critical": False,
        },
        {
            "name": "Deno / Provider files",
            "ok": bool(deno and pot_plugin_ok and pot_server_ok),
            "detail": "Ready" if (deno and pot_plugin_ok and pot_server_ok) else "Missing component",
            "critical": False,
        },
        {
            "name": "Browser Bridge",
            "ok": bool(bridge_live),
            "detail": BRIDGE_URL if bridge_live else "Bridge not responding",
            "critical": True,
        },
        {
            "name": "Auto Update",
            "ok": bool(update_ready),
            "detail": "GitHub updater ready" if update_ready else "Update configuration incomplete",
            "critical": True,
        },
    ]

    essential_ok = all(item["ok"] for item in items if item.get("critical"))
    return {
        "items": items,
        "essential_ok": essential_ok,
        "all_ok": all(item["ok"] for item in items),
    }


def _open_health_dialog(report):
    win = tk.Toplevel(root)
    win.title(f"{APP_SHORT_NAME} • {tr('Health Check')}")
    win.geometry("690x560")
    win.minsize(620, 500)
    win.configure(bg=UI_BG)
    try:
        win.transient(root)
        win.grab_set()
    except Exception:
        pass

    header = tk.Frame(win, bg=UI_TOP, height=92)
    header.pack(fill="x")
    header.pack_propagate(False)
    tk.Label(
        header,
        text="Z²SE  •  " + tr("Health Check"),
        bg=UI_TOP,
        fg=UI_TOP_TEXT,
        font=("Segoe UI Semibold", 16),
    ).pack(anchor="w", padx=24, pady=(18, 2))
    tk.Label(
        header,
        text=(
            tr("All essential components are ready.")
            if report.get("essential_ok")
            else tr("Some components need attention.")
        ),
        bg=UI_TOP,
        fg=UI_TOP_MUTED,
        font=("Segoe UI", 9),
    ).pack(anchor="w", padx=24)

    body = tk.Frame(win, bg=UI_BG)
    body.pack(fill="both", expand=True, padx=22, pady=18)

    for item in report.get("items", []):
        row = tk.Frame(
            body,
            bg=UI_PANEL,
            highlightthickness=1,
            highlightbackground=UI_BORDER,
        )
        row.pack(fill="x", pady=4)
        ok = bool(item.get("ok"))
        tk.Label(
            row,
            text="●",
            bg=UI_PANEL,
            fg=UI_SUCCESS if ok else UI_DANGER,
            font=("Segoe UI", 12),
            width=3,
        ).pack(side="left", padx=(10, 2), pady=10)
        text_frame = tk.Frame(row, bg=UI_PANEL)
        text_frame.pack(side="left", fill="x", expand=True, pady=8)
        tk.Label(
            text_frame,
            text=str(item.get("name", "")),
            bg=UI_PANEL,
            fg=UI_TEXT,
            font=("Segoe UI Semibold", 9),
        ).pack(anchor="w")
        tk.Label(
            text_frame,
            text=str(item.get("detail", "")),
            bg=UI_PANEL,
            fg=UI_MUTED,
            font=("Segoe UI", 8),
        ).pack(anchor="w")
        tk.Label(
            row,
            text="READY" if ok else "CHECK",
            bg=UI_ACCENT_SOFT if ok else "#fff1f0",
            fg="#175cd3" if ok else UI_DANGER,
            font=("Segoe UI Semibold", 8),
            padx=9,
            pady=4,
        ).pack(side="right", padx=12)

    footer = tk.Frame(win, bg=UI_BG)
    footer.pack(fill="x", padx=22, pady=(0, 18))

    def refresh():
        try:
            win.destroy()
        except Exception:
            pass
        show_health_check()

    def repair():
        if downloads_are_running():
            messagebox.showwarning(
                tr("Health Check"),
                tr("Wait for downloads to finish before clearing cache."),
            )
            return
        try:
            win.destroy()
        except Exception:
            pass
        threading.Thread(target=_health_repair_worker, daemon=True).start()

    ttk.Button(
        footer,
        text=tr("Smart repair"),
        style="Primary.TButton",
        command=repair,
    ).pack(side="left")
    ttk.Button(
        footer,
        text=tr("Refresh"),
        style="Toolbar.TButton",
        command=refresh,
    ).pack(side="right", padx=(8, 0))
    ttk.Button(
        footer,
        text=tr("Close"),
        style="Ghost.TButton",
        command=win.destroy,
    ).pack(side="right")


def _health_repair_worker():
    set_status("Smart Recovery...")
    auto_repair(reason="manual Health Check")
    report = collect_health_report()
    set_status(tr("Ready"))
    gui_call(_open_health_dialog, report)


def show_health_check():
    set_status("Health Check...")

    def worker():
        report = collect_health_report()
        set_status(tr("Ready"))
        gui_call(_open_health_dialog, report)

    threading.Thread(target=worker, daemon=True).start()



# ============================================================
# TIME / PART PROGRESS HELPERS
# ============================================================

def timecode_to_seconds(value):
    """
    Accepts:
      00.02.05
      00:02:05
      02:05
      125
    """
    value = str(value or "").strip().replace(".", ":")

    if not value:
        return 0.0

    parts = value.split(":")

    try:
        nums = [float(part) for part in parts]
    except Exception:
        return 0.0

    if len(nums) == 1:
        return nums[0]

    if len(nums) == 2:
        return nums[0] * 60 + nums[1]

    # Use last 3 pieces as HH:MM:SS
    h, m, s = nums[-3], nums[-2], nums[-1]
    return h * 3600 + m * 60 + s


def seconds_to_eta(seconds):
    try:
        seconds = max(0, int(round(float(seconds))))
    except Exception:
        return ""

    h, rem = divmod(seconds, 3600)
    m, s = divmod(rem, 60)

    if h:
        return f"{h:02d}:{m:02d}:{s:02d}"

    return f"{m:02d}:{s:02d}"


def bytes_to_human(value):
    try:
        value = float(value)
    except Exception:
        return None

    units = ["B", "KiB", "MiB", "GiB", "TiB"]
    index = 0

    while value >= 1024 and index < len(units) - 1:
        value /= 1024.0
        index += 1

    if index == 0:
        return f"{value:.0f}{units[index]}"

    return f"{value:.1f}{units[index]}"


# ============================================================
# FORMATS / COMMAND
# ============================================================

def get_format(quality):
    """
    V32.23 — TV SAFE MP4

    MP4 is only a container. Older TVs often reject MP4 files whose video is
    VP9 / AV1 / HEVC even though the audio still plays.

    Prefer:
      video = H.264 / AVC (avc1)
      audio = AAC (mp4a)
      container = MP4

    A generic fallback remains for sites that do not expose AVC/AAC; the
    post-download TV compatibility check will transcode only when necessary.
    """
    height_map = {
        "1080p": 1080,
        "720p": 720,
        "480p": 480,
    }

    height = height_map.get(
        str(quality),
        1080,
    )

    return (
        f"bv*[height<={height}][vcodec^=avc1][ext=mp4]"
        f"+ba[acodec^=mp4a][ext=m4a]/"
        f"bv*[height<={height}][vcodec^=avc1]"
        f"+ba[acodec^=mp4a]/"
        f"b[height<={height}][vcodec^=avc1][acodec^=mp4a]/"
        f"b[height<={height}][vcodec^=avc1]/"
        f"bv*[height<={height}]+ba/"
        f"b[height<={height}]"
    )


def _probe_tv_codecs(path):
    """
    Return codec information needed for USB/TV compatibility.
    """
    result = {
        "video_codec": "",
        "audio_codec": "",
        "pix_fmt": "",
        "has_video": False,
        "has_audio": False,
    }

    if (
        not path
        or not os.path.isfile(path)
        or not FFPROBE
    ):
        return result

    try:
        probe = subprocess.run(
            [
                FFPROBE,
                "-v", "error",
                "-show_entries",
                "stream=codec_type,codec_name,pix_fmt",
                "-of", "json",
                path,
            ],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=20,
            env=build_tool_env(),
            creationflags=(
                subprocess.CREATE_NO_WINDOW
                if os.name == "nt"
                else 0
            ),
        )

        if probe.returncode != 0:
            return result

        payload = json.loads(
            probe.stdout or "{}"
        )

        for stream in payload.get(
            "streams",
            [],
        ):
            stream_type = str(
                stream.get(
                    "codec_type",
                    "",
                )
            ).lower()

            if (
                stream_type == "video"
                and not result["has_video"]
            ):
                result["has_video"] = True
                result["video_codec"] = str(
                    stream.get(
                        "codec_name",
                        "",
                    )
                ).lower()
                result["pix_fmt"] = str(
                    stream.get(
                        "pix_fmt",
                        "",
                    )
                ).lower()

            elif (
                stream_type == "audio"
                and not result["has_audio"]
            ):
                result["has_audio"] = True
                result["audio_codec"] = str(
                    stream.get(
                        "codec_name",
                        "",
                    )
                ).lower()

    except Exception:
        pass

    return result


def _is_tv_safe_mp4(path):
    info = _probe_tv_codecs(
        path
    )

    if not info["has_video"]:
        return False

    video_ok = (
        info["video_codec"] == "h264"
        and (
            not info["pix_fmt"]
            or info["pix_fmt"] == "yuv420p"
        )
    )

    audio_ok = (
        not info["has_audio"]
        or info["audio_codec"] == "aac"
    )

    return video_ok and audio_ok


def ensure_tv_compatible_mp4(
    path,
    stats_callback=None,
    job_label="",
):
    """
    Guarantee a conservative TV/USB MP4:
      H.264/AVC + yuv420p + AAC stereo.

    Fast path:
      Already compatible -> no re-encode.

    If only audio is incompatible:
      Copy H.264 video, convert only audio.

    If video is VP9/AV1/HEVC/etc:
      Convert video to H.264 and audio to AAC.
    """
    path = str(
        path or ""
    ).strip()

    if (
        not path
        or not os.path.isfile(path)
        or os.path.splitext(path)[1].lower() != ".mp4"
    ):
        return True

    info = _probe_tv_codecs(
        path
    )

    prefix = (
        f"[{job_label}] "
        if job_label
        else ""
    )

    if _is_tv_safe_mp4(path):
        log(
            prefix
            + "📺 TV SAFE: H.264 + AAC — no conversion needed."
        )
        return True

    video_codec = info.get(
        "video_codec",
        "",
    )
    audio_codec = info.get(
        "audio_codec",
        "",
    )
    pix_fmt = info.get(
        "pix_fmt",
        "",
    )

    log(
        prefix
        + "📺 TV compatibility conversion needed: "
        + f"video={video_codec or '?'} "
        + f"pix_fmt={pix_fmt or '?'} "
        + f"audio={audio_codec or 'none'}"
    )

    if stats_callback:
        try:
            stats_callback(
                percent=99.0,
                speed="TV SAFE",
                eta="",
                size=None,
            )
        except Exception:
            pass

    root_name, _ = os.path.splitext(
        path
    )

    temp_path = (
        root_name
        + ".z2se_tv_safe.tmp.mp4"
    )

    try:
        if os.path.isfile(
            temp_path
        ):
            os.remove(
                temp_path
            )
    except Exception:
        pass

    # If H.264/yuv420p is already good, do not re-encode the video.
    video_can_copy = (
        info.get(
            "video_codec"
        ) == "h264"
        and (
            not info.get(
                "pix_fmt"
            )
            or info.get(
                "pix_fmt"
            ) == "yuv420p"
        )
    )

    command = [
        FFMPEG,
        "-y",
        "-i", path,
        "-map", "0:v:0",
        "-map", "0:a:0?",
    ]

    if video_can_copy:
        command += [
            "-c:v", "copy",
            "-tag:v", "avc1",
        ]
    else:
        command += [
            "-c:v", "libx264",
            "-preset", "veryfast",
            "-crf", "20",
            "-pix_fmt", "yuv420p",
            "-vf",
            "scale=trunc(iw/2)*2:trunc(ih/2)*2,format=yuv420p",
            "-profile:v", "high",
            "-tag:v", "avc1",
        ]

    if info.get(
        "has_audio"
    ):
        if info.get(
            "audio_codec"
        ) == "aac":
            command += [
                "-c:a", "copy",
            ]
        else:
            command += [
                "-c:a", "aac",
                "-b:a", "192k",
                "-ac", "2",
                "-ar", "48000",
            ]
    else:
        command += [
            "-an",
        ]

    command += [
        "-movflags", "+faststart",
        "-progress", "pipe:1",
        "-nostats",
        "-loglevel", "error",
        temp_path,
    ]

    process = None

    try:
        process = subprocess.Popen(
            command,
            env=build_tool_env(),
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            encoding="utf-8",
            errors="replace",
            creationflags=(
                subprocess.CREATE_NO_WINDOW
                if os.name == "nt"
                else 0
            ),
        )

        register_process(
            process
        )

        for raw in process.stdout:
            if should_stop_current_job():
                try:
                    process.terminate()
                except Exception:
                    pass
                return False

            line = raw.strip()

            if (
                stats_callback
                and line.startswith(
                    "progress="
                )
            ):
                try:
                    stats_callback(
                        percent=99.3,
                        speed="TV SAFE",
                        eta="",
                        size=None,
                    )
                except Exception:
                    pass

        code = process.wait()

        if (
            code != 0
            or not os.path.isfile(
                temp_path
            )
        ):
            log(
                prefix
                + f"TV SAFE conversion failed. Code: {code}"
            )
            return False

        if not _is_tv_safe_mp4(
            temp_path
        ):
            log(
                prefix
                + "TV SAFE verification failed after conversion."
            )
            return False

        os.replace(
            temp_path,
            path,
        )

        log(
            prefix
            + "✅ TV SAFE MP4 ready: H.264 + AAC."
        )

        if stats_callback:
            try:
                stats_callback(
                    percent=99.8,
                    speed="TV SAFE ✓",
                    eta="",
                    size=_human_file_size(
                        os.path.getsize(
                            path
                        )
                    ),
                )
            except Exception:
                pass

        return True

    except Exception as exc:
        log(
            prefix
            + f"TV SAFE conversion ERROR: {exc}"
        )
        return False

    finally:
        if process is not None:
            unregister_process(
                process
            )

        try:
            if os.path.isfile(
                temp_path
            ):
                os.remove(
                    temp_path
                )
        except Exception:
            pass


def build_command(
    url,
    quality,
    mode="full",
    start="",
    end="",
    output_prefix="",
    fast_extract=True,
    media_format="MP4",
    output_name=None,
    referer=None,
    broad_format=False,
):
    command = [
        YTDLP,
        "--newline",
        "--windows-filenames",
        "--no-playlist",
        "--retries", "10",
        "--fragment-retries", "10",
        "--ffmpeg-location", FFMPEG_DIR,
    ]

    if referer:
        command += [
            "--referer", str(referer),
        ]

    # FAST START:
    # On the first attempt, skip HLS/DASH manifest extraction and
    # translated subtitles. For ordinary direct YouTube formats this
    # removes extra network work before the download starts.
    # If a video needs those manifests, V5 automatically retries
    # with the normal extractor path.
    if pot_ready:
        extractor_args = "youtube:player_client=mweb"
        if fast_extract:
            extractor_args += ";skip=hls,dash,translated_subs"

        command += [
            "--extractor-args",
            extractor_args,
        ]
    elif fast_extract:
        command += [
            "--extractor-args",
            "youtube:skip=hls,dash,translated_subs",
        ]

    if mode == "full":
        command += ["-N", "16"]

    output_template = "%(title)s.%(ext)s"

    if output_name:
        output_template = windows_safe_name(
            output_name,
            max_length=145,
        ) + ".%(ext)s"
    elif output_prefix:
        output_template = output_prefix + "%(title)s.%(ext)s"

    media_format = str(media_format or "MP4").upper()

    if media_format == "MP3":
        command += [
            "-f", "ba/b",
            "-x",
            "--audio-format", "mp3",
            "--audio-quality", "320K",
            "-P", DOWNLOADS,
            "-o", output_template,
        ]
    else:
        # V32.42 Smart Recovery: normal downloads keep the TV-friendly
        # AVC/AAC preference. Only the final recovery attempt widens format
        # selection so unusual sites/videos still have a chance to download;
        # the existing TV Safe pass converts the result afterwards if needed.
        selected_format = (
            "bv*+ba/b"
            if broad_format
            else get_format(quality)
        )
        command += [
            "-f", selected_format,
            "--merge-output-format", "mp4",
            "-P", DOWNLOADS,
            "-o", output_template,
        ]

    if mode == "part":
        start = start.strip().replace(".", ":")
        end = end.strip().replace(".", ":")

        command += [
            "--download-sections",
            f"*{start}-{end}",

            # --download-sections is handled by FFmpeg, not the normal
            # yt-dlp downloader. Ask FFmpeg for newline-based progress
            # so the GUI can show live percentage / speed / ETA.
            "--downloader-args",
            "ffmpeg:-progress pipe:1 -nostats -loglevel error",
        ]

    # Stable marker so the GUI can show the real video title
    command += [
        "--print",
        "before_dl:__VD_TITLE__%(title)s",

        # Exact final file path after merge/post-processing.
        # V32.21 uses this for Open/Delete instead of guessing from title.
        "--print",
        "after_move:__VD_FILEPATH__%(filepath)s",

        # IMPORTANT:
        # --print makes yt-dlp quiet by default. Explicitly re-enable
        # progress so the GUI gets live %, speed, ETA and size.
        "--progress",
    ]

    command.append(url)
    return command


# ============================================================
# V32.42 — SMART RECOVERY ERROR PROFILE
# ============================================================

def _set_download_error_profile(**values):
    try:
        download_error_context.profile = dict(values)
    except Exception:
        pass


def _get_download_error_profile():
    try:
        value = getattr(download_error_context, "profile", None)
        return dict(value) if isinstance(value, dict) else {}
    except Exception:
        return {}


# ============================================================
# RUN ONE DOWNLOAD
# ============================================================

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


def run_download_once(
    url,
    quality,
    mode="full",
    start="",
    end="",
    output_prefix="",
    progress_callback=None,
    stats_callback=None,
    job_label="",
    fast_extract=True,
    media_format="MP4",
    output_name=None,
    referer=None,
    broad_format=False,
):
    if should_stop_current_job():
        return 130, False, True, False

    command = build_command(
        url=url,
        quality=quality,
        mode=mode,
        start=start,
        end=end,
        output_prefix=output_prefix,
        fast_extract=fast_extract,
        media_format=media_format,
        output_name=output_name,
        referer=referer,
        broad_format=broad_format,
    )

    saw_403 = False
    saw_format_problem = False
    saw_pot_problem = False
    saw_auth_problem = False
    saw_rate_limit = False
    stopped = False
    process = None
    final_output_path = ""

    launched_at = time.perf_counter()
    first_output_at = None
    first_download_at = None

    # Part downloads are handled by FFmpeg. yt-dlp's normal
    # "[download] xx%" lines are not reliable there, so V8 also
    # parses FFmpeg's "-progress pipe:1" key/value output.
    part_duration = 0.0
    if mode == "part":
        part_duration = max(
            0.0,
            timecode_to_seconds(end) - timecode_to_seconds(start)
        )

    requested_start_seconds = (
        timecode_to_seconds(start) if mode == "part" else 0.0
    )

    ffmpeg_progress = {
        "out_time": 0.0,
        "base_out_time": None,
        "total_size": 0,
        "speed_factor": 0.0,
        "first_wall": None,
        "last_wall": None,
        "last_size": 0,
        "last_speed_text": None,
    }

    try:
        creationflags = (
            subprocess.CREATE_NO_WINDOW
            if os.name == "nt"
            else 0
        )

        process = subprocess.Popen(
            command,
            env=build_tool_env(),
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            encoding="utf-8",
            errors="replace",
            creationflags=creationflags,
        )

        register_process(process)

        for line in process.stdout:
            if should_stop_current_job():
                stopped = True
                try:
                    process.terminate()
                except Exception:
                    pass
                break

            line = line.strip()
            if not line:
                continue

            if first_output_at is None:
                first_output_at = time.perf_counter()

            # ------------------------------------------------
            # CLEAN LIVE PROGRESS FOR PART DOWNLOADS (FFmpeg)
            # ------------------------------------------------
            if mode == "part" and "=" in line:
                key, value = line.split("=", 1)
                key = key.strip()
                value = value.strip()

                # FFmpeg -progress emits a block like:
                # frame=...
                # fps=...
                # bitrate=...
                # total_size=...
                # out_time_us=...
                # out_time_ms=...
                # out_time=HH:MM:SS.xxxxxx
                # speed=...
                # progress=continue
                #
                # We swallow ALL of these lines so the Log stays clean.
                ffmpeg_keys = {
                    "frame",
                    "fps",
                    "stream_0_0_q",
                    "stream_0_1_q",
                    "bitrate",
                    "total_size",
                    "out_time_us",
                    "out_time_ms",
                    "out_time",
                    "dup_frames",
                    "drop_frames",
                    "speed",
                    "progress",
                }

                if key in ffmpeg_keys:
                    if key == "out_time":
                        # This is the safest FFmpeg clock to parse.
                        ffmpeg_progress["out_time"] = timecode_to_seconds(value)

                    elif key == "total_size":
                        try:
                            ffmpeg_progress["total_size"] = max(0, int(value))
                        except Exception:
                            pass

                    elif key == "speed":
                        try:
                            ffmpeg_progress["speed_factor"] = float(
                                value.lower().replace("x", "").strip()
                            )
                        except Exception:
                            pass

                    elif key == "progress":
                        now = time.perf_counter()

                        if ffmpeg_progress["first_wall"] is None:
                            ffmpeg_progress["first_wall"] = now

                        current_out = ffmpeg_progress["out_time"]

                        # FFmpeg can report timestamps in several timelines
                        # depending on the selected YouTube format and seek mode.
                        # The safest solution is to remember the FIRST out_time
                        # emitted for this cut and measure progress from there.
                        if ffmpeg_progress["base_out_time"] is None:
                            ffmpeg_progress["base_out_time"] = current_out
                            prefix = f"[{job_label}] " if job_label else ""
                            log(
                                prefix
                                + f"PART clock baseline: {current_out:.3f}s | "
                                + f"requested duration: {part_duration:.3f}s"
                            )

                        base_out = ffmpeg_progress["base_out_time"]
                        media_elapsed = max(0.0, current_out - base_out)

                        percent_value = None
                        if part_duration > 0:
                            percent_value = max(
                                0.0,
                                min(
                                    media_elapsed / part_duration * 100.0,
                                    99.0 if value != "end" else 99.9
                                )
                            )

                        current_size = ffmpeg_progress["total_size"]

                        # Live output-file throughput.
                        speed_text = ffmpeg_progress["last_speed_text"]
                        last_wall = ffmpeg_progress["last_wall"]
                        last_size = ffmpeg_progress["last_size"]

                        if (
                            last_wall is not None
                            and current_size >= last_size
                            and now > last_wall
                        ):
                            delta_bytes = current_size - last_size
                            delta_time = now - last_wall

                            if delta_bytes > 0 and delta_time > 0:
                                bps = delta_bytes / delta_time

                                if bps >= 1024 * 1024:
                                    speed_text = f"{bps / (1024 * 1024):.2f}MiB/s"
                                else:
                                    speed_text = f"{bps / 1024:.1f}KiB/s"

                                ffmpeg_progress["last_speed_text"] = speed_text

                        ffmpeg_progress["last_wall"] = now
                        ffmpeg_progress["last_size"] = current_size

                        # Robust ETA from actual wall time and percentage.
                        eta_text = None
                        first_wall = ffmpeg_progress["first_wall"]

                        if (
                            percent_value is not None
                            and percent_value >= 0.5
                            and percent_value < 99.9
                            and first_wall is not None
                        ):
                            wall_elapsed = max(0.001, now - first_wall)
                            eta_seconds = (
                                wall_elapsed
                                * (100.0 - percent_value)
                                / percent_value
                            )
                            eta_text = seconds_to_eta(eta_seconds)

                        size_text = (
                            bytes_to_human(current_size)
                            if current_size > 0
                            else None
                        )

                        if percent_value is not None and progress_callback:
                            try:
                                progress_callback(percent_value)
                            except Exception:
                                pass

                        if stats_callback:
                            try:
                                stats_callback(
                                    percent=percent_value,
                                    speed=speed_text,
                                    eta=eta_text,
                                    size=size_text,
                                )
                            except Exception:
                                pass

                    # Do not print FFmpeg machine-progress lines in GUI log.
                    continue

            low_line = line.lower()

            if (
                "requested format is not available" in low_line
                or "no video formats found" in low_line
                or "no suitable formats" in low_line
                or "requested format not available" in low_line
            ):
                saw_format_problem = True

            # YouTube / provider failures evolve often. Keep detection broad
            # enough to trigger one safe repair attempt without looping.
            if (
                "po token" in low_line
                or "pot provider" in low_line
                or "bgutil" in low_line
            ) and (
                "error" in low_line
                or "failed" in low_line
                or "missing" in low_line
                or "unavailable" in low_line
                or "not provided" in low_line
                or "not found" in low_line
            ):
                saw_pot_problem = True

            if (
                "sign in to confirm" in low_line
                or "confirm you’re not a bot" in low_line
                or "confirm you're not a bot" in low_line
                or "login required" in low_line
                or "authentication required" in low_line
            ):
                saw_auth_problem = True

            if (
                "http error 429" in low_line
                or "too many requests" in low_line
            ):
                saw_rate_limit = True

            if line.startswith("[download]") and first_download_at is None:
                first_download_at = time.perf_counter()
                prefix = f"[{job_label}] " if job_label else ""
                log(
                    prefix
                    + f"⚡ Download stream started after "
                    + f"{first_download_at - launched_at:.2f}s"
                )

            # Title marker generated by --print before_dl.
            if line.startswith("__VD_TITLE__"):
                title_value = clean_video_title(
                    line[len("__VD_TITLE__"):].strip()
                )

                if stats_callback and title_value:
                    try:
                        stats_callback(
                            title=title_value
                        )
                    except Exception:
                        pass

                prefix = f"[{job_label}] " if job_label else ""
                log(
                    prefix
                    + "Title: "
                    + title_value
                )
                continue

            # Authoritative final filepath generated by yt-dlp after_move.
            if line.startswith("__VD_FILEPATH__"):
                final_path = line[
                    len("__VD_FILEPATH__"):
                ].strip()

                final_output_path = _normalize_output_path(
                    final_path
                )

                register_current_job_output_path(
                    final_output_path
                )

                prefix = f"[{job_label}] " if job_label else ""
                log(
                    prefix
                    + "Final file: "
                    + final_path
                )
                continue

            prefix = f"[{job_label}] " if job_label else ""
            log(prefix + line)

            low = line.lower()
            if "403" in low and (
                "forbidden" in low
                or "http error 403" in low
            ):
                saw_403 = True

            percent_match = re.search(
                r"\[download\]\s+(\d+(?:\.\d+)?)%",
                line
            )

            percent_value = None
            if percent_match:
                try:
                    percent_value = float(percent_match.group(1))
                except Exception:
                    percent_value = None

            if percent_value is not None and progress_callback:
                try:
                    progress_callback(percent_value)
                except Exception:
                    pass

            # Parse the standard yt-dlp progress line:
            # [download] 12.3% of 10.66MiB at 9.21MiB/s ETA 00:01
            speed_match = re.search(
                r"\bat\s+([^\s]+/s)\s+ETA\s+",
                line
            )

            eta_match = re.search(
                r"\bETA\s+([^\s]+)",
                line
            )

            size_match = re.search(
                r"\bof\s+~?\s*([0-9.]+\s*[KMGTPE]?i?B)",
                line,
                re.IGNORECASE
            )

            if stats_callback and (
                percent_value is not None
                or speed_match
                or eta_match
                or size_match
            ):
                try:
                    stats_callback(
                        percent=percent_value,
                        speed=speed_match.group(1) if speed_match else None,
                        eta=eta_match.group(1) if eta_match else None,
                        size=size_match.group(1) if size_match else None,
                    )
                except Exception:
                    pass

        code = process.wait()

        prefix = f"[{job_label}] " if job_label else ""
        if first_output_at is not None:
            log(
                prefix
                + f"Engine first response: "
                + f"{first_output_at - launched_at:.2f}s"
            )

        if stopped or should_stop_current_job():
            return 130, saw_403, True, saw_format_problem

        if (
            code == 0
            and final_output_path
            and os.path.isfile(final_output_path)
        ):
            media_ok, media_reason = _validate_completed_download(
                final_output_path,
                media_format=media_format,
            )

            if not media_ok:
                log(prefix + "False-success blocked: " + media_reason + f" | {final_output_path}")
                try:
                    os.remove(final_output_path)
                except Exception:
                    pass
                saw_format_problem = True
                code = 95

            elif str(media_format).upper() == "MP4":
                ensure_tv_compatible_mp4(
                    final_output_path,
                    stats_callback=stats_callback,
                    job_label=job_label,
                )
                register_current_job_output_path(final_output_path)

        return code, saw_403, False, saw_format_problem

    except Exception as exc:
        prefix = f"[{job_label}] " if job_label else ""
        log(prefix + f"DOWNLOAD ERROR: {exc}")
        return 999, False, False, False

    finally:
        _set_download_error_profile(
            saw_403=saw_403,
            saw_format_problem=saw_format_problem,
            saw_pot_problem=saw_pot_problem,
            saw_auth_problem=saw_auth_problem,
            saw_rate_limit=saw_rate_limit,
            broad_format=bool(broad_format),
        )
        if process is not None:
            unregister_process(process)



# ============================================================
# V11 TURBO PART ENGINE
# Full TURBO download -> local cache -> instant local cut
# ============================================================

def youtube_video_id(url):
    """
    Extract a stable YouTube video id without another network request.
    Falls back to a short SHA1 key for unusual URLs.
    """
    try:
        parsed = urlparse(url)
        host = (parsed.hostname or "").lower()
        path = parsed.path.strip("/")

        if host == "youtu.be":
            value = path.split("/")[0].strip()
            if value:
                return re.sub(r"[^A-Za-z0-9_-]", "", value)[:32]

        if host == "youtube.com" or host.endswith(".youtube.com"):
            query_id = parse_qs(parsed.query).get("v", [""])[0].strip()
            if query_id:
                return re.sub(r"[^A-Za-z0-9_-]", "", query_id)[:32]

            pieces = [p for p in path.split("/") if p]
            if len(pieces) >= 2 and pieces[0] in (
                "shorts", "embed", "live"
            ):
                return re.sub(
                    r"[^A-Za-z0-9_-]",
                    "",
                    pieces[1]
                )[:32]
    except Exception:
        pass

    return hashlib.sha1(
        str(url).encode("utf-8", errors="ignore")
    ).hexdigest()[:16]


def windows_safe_name(value, max_length=150):
    value = str(value or "video").strip()

    # Remove Windows-invalid and control characters.
    value = re.sub(r'[<>:"/\\|?*\x00-\x1F]', "_", value)
    value = re.sub(r"\s+", " ", value).strip(" .")

    if not value:
        value = "video"

    return value[:max_length].rstrip(" .")


def get_cache_lock(cache_key):
    with cache_locks_guard:
        lock = cache_locks.get(cache_key)

        if lock is None:
            lock = threading.Lock()
            cache_locks[cache_key] = lock

        return lock


def acquire_cache_lock(lock):
    while not stop_all_event.is_set():
        if lock.acquire(timeout=0.25):
            return True

    return False


def cache_paths(cache_key):
    meta_path = os.path.join(
        CACHE_DIR,
        cache_key + ".json"
    )

    candidates = []

    for ext in ("mp4", "mkv", "webm", "mov", "m4a", "mp3"):
        path = os.path.join(
            CACHE_DIR,
            cache_key + "." + ext
        )

        if os.path.isfile(path):
            candidates.append(path)

    return candidates, meta_path


def read_cache_meta(meta_path):
    try:
        with open(
            meta_path,
            "r",
            encoding="utf-8"
        ) as file:
            data = json.load(file)

        return data if isinstance(data, dict) else {}
    except Exception:
        return {}


def write_cache_meta(meta_path, title, cache_file, url, quality):
    try:
        with open(
            meta_path,
            "w",
            encoding="utf-8"
        ) as file:
            json.dump(
                {
                    "title": title,
                    "file": cache_file,
                    "url": url,
                    "quality": quality,
                    "cached_at": datetime.now().isoformat(),
                },
                file,
                ensure_ascii=False,
                indent=2
            )
    except Exception:
        pass


def choose_cache_file(candidates, meta):
    preferred = str(meta.get("file", "")).strip()

    if preferred and os.path.isfile(preferred):
        return preferred

    for candidate in candidates:
        if os.path.isfile(candidate):
            return candidate

    return None


def parse_ytdlp_download_stats(line):
    percent = None
    speed = None
    eta = None
    size = None

    match = re.search(
        r"\[download\]\s+(\d+(?:\.\d+)?)%",
        line
    )

    if match:
        try:
            percent = float(match.group(1))
        except Exception:
            percent = None

    match = re.search(
        r"\bat\s+([^\s]+/s)\s+ETA\s+",
        line
    )
    if match:
        speed = match.group(1)

    match = re.search(
        r"\bETA\s+([^\s]+)",
        line
    )
    if match:
        eta = match.group(1)

    match = re.search(
        r"\bof\s+~?\s*([0-9.]+\s*[KMGTPE]?i?B)",
        line,
        re.IGNORECASE
    )
    if match:
        size = match.group(1)

    return percent, speed, eta, size


def build_cache_download_command(
    url,
    quality,
    cache_key,
    fast_extract=True,
    media_format="MP4"
):
    media_format = str(media_format or "MP4").upper()

    command = [
        YTDLP,
        "--newline",
        "--windows-filenames",
        "--no-playlist",
        "--retries", "10",
        "--fragment-retries", "10",
        "--socket-timeout", "20",
        "--ffmpeg-location", FFMPEG_DIR,

        # V32.27 FASTEST-PART cache path:
        # Native bounded HTTP chunks avoid the long open-ended request that
        # YouTube currently throttles in FFmpeg section downloads.
        "--http-chunk-size", "8M",
        "--throttled-rate", "500K",

        # Concurrent DASH/native fragments where available.
        "-N", "16",
    ]

    if media_format == "MP3":
        command += [
            "-f", "ba/b",
            "-x",
            "--audio-format", "mp3",
            "--audio-quality", "320K",
            "-P", CACHE_DIR,
            "-o", cache_key + ".%(ext)s",
        ]
    else:
        command += [
            "-f", get_format(quality),
            "--merge-output-format", "mp4",
            "-P", CACHE_DIR,
            "-o", cache_key + ".%(ext)s",
        ]

    command += [
        "--print",
        "before_dl:__VD_TITLE__%(title)s",

        "--print",
        "after_move:__VD_FILE__%(filepath)s",

        "--progress",
    ]

    if pot_ready:
        # "formats=dashy" lets yt-dlp expose segmented variants so -N can
        # actually help. Keep mweb because the existing PO-token provider is
        # already configured for it.
        extractor_args = (
            "youtube:player_client=mweb;"
            "formats=dashy"
        )

        if fast_extract:
            extractor_args += ";skip=hls,translated_subs"

        command += [
            "--extractor-args",
            extractor_args,
        ]

    elif fast_extract:
        command += [
            "--extractor-args",
            "youtube:formats=dashy;skip=hls,translated_subs",
        ]

    command.append(url)
    return command


def cache_download_once(
    url,
    quality,
    cache_key,
    progress_callback=None,
    stats_callback=None,
    job_label="",
    fast_extract=True,
    media_format="MP4"
):
    process = None
    saw_403 = False
    saw_format_problem = False
    stopped = False
    title = ""
    final_file = ""

    command = build_cache_download_command(
        url=url,
        quality=quality,
        cache_key=cache_key,
        fast_extract=fast_extract,
        media_format=media_format,
    )

    prefix = f"[{job_label}] " if job_label else ""

    try:
        creationflags = (
            subprocess.CREATE_NO_WINDOW
            if os.name == "nt"
            else 0
        )

        process = subprocess.Popen(
            command,
            env=build_tool_env(),
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            encoding="utf-8",
            errors="replace",
            creationflags=creationflags,
        )

        register_process(process)

        for raw_line in process.stdout:
            if should_stop_current_job():
                stopped = True

                try:
                    process.terminate()
                except Exception:
                    pass

                break

            line = raw_line.strip()

            if not line:
                continue

            if line.startswith("__VD_TITLE__"):
                title = clean_video_title(
                    line[len("__VD_TITLE__"):].strip()
                )

                if stats_callback and title:
                    try:
                        stats_callback(title=title)
                    except Exception:
                        pass

                log(prefix + "Title: " + title)
                continue

            if line.startswith("__VD_FILE__"):
                final_file = line[len("__VD_FILE__"):].strip()
                continue

            low = line.lower()

            if (
                "403" in low
                and (
                    "forbidden" in low
                    or "http error 403" in low
                )
            ):
                saw_403 = True

            if (
                "requested format is not available" in low
                or "no video formats found" in low
                or "no suitable formats" in low
            ):
                saw_format_problem = True

            percent, speed, eta, size = parse_ytdlp_download_stats(line)

            if percent is not None:
                # Reserve the last 4% for the local cut.
                overall = min(95.5, max(0.0, percent * 0.955))

                if progress_callback:
                    try:
                        progress_callback(overall)
                    except Exception:
                        pass

                if stats_callback:
                    try:
                        stats_callback(
                            percent=overall,
                            speed=speed,
                            eta=eta,
                            size=size,
                        )
                    except Exception:
                        pass

            # Keep useful yt-dlp information, but not every progress line.
            if not line.startswith("[download]"):
                log(prefix + line)

        code = process.wait()

        if stopped or stop_all_event.is_set():
            return (
                130,
                saw_403,
                True,
                saw_format_problem,
                title,
                final_file,
            )

        return (
            code,
            saw_403,
            False,
            saw_format_problem,
            title,
            final_file,
        )

    except Exception as exc:
        log(prefix + f"TURBO CACHE ERROR: {exc}")

        return (
            999,
            False,
            False,
            False,
            title,
            final_file,
        )

    finally:
        if process is not None:
            unregister_process(process)



def probe_stream_types(path):
    if not FFPROBE or not os.path.isfile(FFPROBE):
        return set()

    try:
        result = subprocess.run(
            [
                FFPROBE,
                "-v", "error",
                "-show_entries", "stream=codec_type",
                "-of", "json",
                path,
            ],
            env=build_tool_env(),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding="utf-8",
            errors="replace",
            creationflags=(
                subprocess.CREATE_NO_WINDOW
                if os.name == "nt"
                else 0
            ),
            timeout=20,
        )

        if result.returncode != 0:
            return set()

        data = json.loads(result.stdout or "{}")
        return {
            stream.get("codec_type")
            for stream in data.get("streams", [])
            if stream.get("codec_type")
        }

    except Exception:
        return set()


def find_orphan_cache_fragments(cache_key):
    files = []

    try:
        for name in os.listdir(CACHE_DIR):
            if not name.startswith(cache_key + "."):
                continue

            lower = name.lower()

            if lower.endswith((".json", ".part", ".ytdl", ".tmp", ".temp")):
                continue

            if name in {
                cache_key + ".mp4",
                cache_key + ".mkv",
                cache_key + ".webm",
                cache_key + ".mov",
            }:
                continue

            path = os.path.join(CACHE_DIR, name)

            if os.path.isfile(path):
                files.append(path)

    except Exception:
        pass

    return files


def manual_merge_cache_fragments(
    cache_key,
    title="",
    url="",
    quality="",
    progress_callback=None,
    stats_callback=None,
    job_label=""
):
    prefix = f"[{job_label}] " if job_label else ""

    if not FFMPEG or not os.path.isfile(FFMPEG):
        log(prefix + "System FFmpeg is not available.")
        return None

    fragments = find_orphan_cache_fragments(cache_key)

    if len(fragments) < 2:
        return None

    video_candidates = []
    audio_candidates = []

    for path in fragments:
        types = probe_stream_types(path)

        if "video" in types:
            video_candidates.append(path)

        if "audio" in types and "video" not in types:
            audio_candidates.append(path)

    if not video_candidates:
        video_candidates = [
            p for p in fragments
            if os.path.splitext(p)[1].lower() in (".mp4", ".webm", ".mkv")
        ]

    if not audio_candidates:
        audio_candidates = [
            p for p in fragments
            if os.path.splitext(p)[1].lower() in (".m4a", ".aac", ".mp3", ".opus", ".webm")
            and p not in video_candidates
        ]

    if not video_candidates or not audio_candidates:
        return None

    video_file = max(video_candidates, key=lambda p: os.path.getsize(p))
    audio_file = max(audio_candidates, key=lambda p: os.path.getsize(p))

    output_file = os.path.join(CACHE_DIR, cache_key + ".mp4")

    log(prefix + "🛠 Manual FFmpeg merge fallback...")
    log(prefix + "Video: " + os.path.basename(video_file))
    log(prefix + "Audio: " + os.path.basename(audio_file))

    if progress_callback:
        try:
            progress_callback(94.0)
        except Exception:
            pass

    if stats_callback:
        try:
            stats_callback(
                percent=94.0,
                speed="MERGING",
                eta="00:00",
                size=None,
                title=title or None,
            )
        except Exception:
            pass

    try:
        result = subprocess.run(
            [
                FFMPEG,
                "-y",
                "-i", video_file,
                "-i", audio_file,
                "-map", "0:v:0",
                "-map", "1:a:0",
                "-c", "copy",
                "-movflags", "+faststart",
                output_file,
            ],
            env=build_tool_env(),
            stdout=subprocess.DEVNULL,
            stderr=subprocess.PIPE,
            text=True,
            encoding="utf-8",
            errors="replace",
            creationflags=(
                subprocess.CREATE_NO_WINDOW
                if os.name == "nt"
                else 0
            ),
        )

        if result.returncode != 0 or not os.path.isfile(output_file):
            log(prefix + "Manual FFmpeg merge failed.")
            return None

        for path in (video_file, audio_file):
            try:
                if os.path.isfile(path):
                    os.remove(path)
            except Exception:
                pass

        write_cache_meta(
            os.path.join(CACHE_DIR, cache_key + ".json"),
            title,
            output_file,
            url,
            quality,
        )

        log(prefix + "🛠 Manual FFmpeg merge completed ✅")

        if progress_callback:
            try:
                progress_callback(95.5)
            except Exception:
                pass

        if stats_callback:
            try:
                stats_callback(
                    percent=95.5,
                    speed="MERGED",
                    eta="00:00",
                    size=None,
                    title=title or None,
                )
            except Exception:
                pass

        return output_file

    except Exception as exc:
        log(prefix + f"Manual merge ERROR: {exc}")
        return None


def obtain_turbo_cache(
    url,
    quality,
    cache_key,
    progress_callback=None,
    stats_callback=None,
    job_label="",
    media_format="MP4"
):
    candidates, meta_path = cache_paths(cache_key)
    meta = read_cache_meta(meta_path)
    cached = choose_cache_file(candidates, meta)

    prefix = f"[{job_label}] " if job_label else ""

    if cached:
        title = str(meta.get("title", "")).strip()

        log(prefix + "⚡ CACHE HIT — full video already available.")

        if progress_callback:
            try:
                progress_callback(95.5)
            except Exception:
                pass

        if stats_callback:
            try:
                stats_callback(
                    percent=95.5,
                    speed="CACHE",
                    eta="00:00",
                    size=None,
                    title=title or None,
                )
            except Exception:
                pass

        return 0, "done", cached, title

    rescued = None

    if str(media_format).upper() != "MP3":
        rescued = manual_merge_cache_fragments(
            cache_key=cache_key,
            title=str(meta.get("title", "")).strip(),
            url=url,
            quality=quality,
            progress_callback=progress_callback,
            stats_callback=stats_callback,
            job_label=job_label,
        )

    if rescued:
        rescued_meta = read_cache_meta(meta_path)
        rescued_title = str(rescued_meta.get("title", "")).strip()
        log(prefix + "⚡ Old video cache rescued; no re-download needed.")
        return 0, "done", rescued, rescued_title

    # First try: FAST extraction.
    result = cache_download_once(
        url=url,
        quality=quality,
        cache_key=cache_key,
        progress_callback=progress_callback,
        stats_callback=stats_callback,
        job_label=job_label,
        fast_extract=True,
        media_format=media_format,
    )

    (
        code,
        saw_403,
        stopped,
        saw_format_problem,
        title,
        final_file,
    ) = result

    if stopped:
        return code, "stopped", None, title

    if (
        code != 0
        and saw_format_problem
        and not stop_all_event.is_set()
    ):
        log(
            prefix
            + "FAST cache path had no suitable format -> normal fallback..."
        )

        result = cache_download_once(
            url=url,
            quality=quality,
            cache_key=cache_key,
            progress_callback=progress_callback,
            stats_callback=stats_callback,
            job_label=job_label,
            fast_extract=False,
            media_format=media_format,
        )

        (
            code,
            saw_403,
            stopped,
            _,
            title2,
            final_file2,
        ) = result

        title = title2 or title
        final_file = final_file2 or final_file

        if stopped:
            return code, "stopped", None, title

    if (
        code != 0
        and saw_403
        and not stop_all_event.is_set()
    ):
        auto_repair()

        if stop_all_event.is_set():
            return 130, "stopped", None, title

        log(prefix + "Retrying TURBO cache after auto-repair...")

        result = cache_download_once(
            url=url,
            quality=quality,
            cache_key=cache_key,
            progress_callback=progress_callback,
            stats_callback=stats_callback,
            job_label=job_label,
            fast_extract=False,
            media_format=media_format,
        )

        (
            code,
            _,
            stopped,
            _,
            title2,
            final_file2,
        ) = result

        title = title2 or title
        final_file = final_file2 or final_file

        if stopped:
            return code, "stopped", None, title

    if code != 0:
        return code, "error", None, title

    # Resolve actual final file even if after_move output was missing.
    candidates, _ = cache_paths(cache_key)

    if not final_file or not os.path.isfile(final_file):
        final_file = choose_cache_file(candidates, {})

    if not final_file and str(media_format).upper() != "MP3":
        final_file = manual_merge_cache_fragments(
            cache_key=cache_key,
            title=title,
            url=url,
            quality=quality,
            progress_callback=progress_callback,
            stats_callback=stats_callback,
            job_label=job_label,
        )

    if not final_file:
        log(prefix + "TURBO cache finished but final merged file was not found.")
        return 998, "error", None, title

    write_cache_meta(
        meta_path=meta_path,
        title=title,
        cache_file=final_file,
        url=url,
        quality=quality,
    )

    return 0, "done", final_file, title


def unique_output_path(path):
    if not os.path.exists(path):
        return path

    root_name, extension = os.path.splitext(path)
    number = 2

    while True:
        candidate = f"{root_name} ({number}){extension}"

        if not os.path.exists(candidate):
            return candidate

        number += 1


def cut_cache_to_part(
    cache_file,
    title,
    start,
    end,
    output_prefix="",
    progress_callback=None,
    stats_callback=None,
    job_label="",
    media_format="MP4"
):
    if not FFMPEG or not os.path.isfile(FFMPEG):
        log("System FFmpeg is not available for local cut.")
        return 997, "error", None

    start_seconds = timecode_to_seconds(start)
    end_seconds = timecode_to_seconds(end)
    duration = max(0.0, end_seconds - start_seconds)

    if duration <= 0:
        return 2, "error", None

    safe_title = windows_safe_name(
        title or os.path.splitext(os.path.basename(cache_file))[0]
    )

    start_tag = str(start).replace(":", "-").replace(".", "-")
    end_tag = str(end).replace(":", "-").replace(".", "-")

    media_format = str(media_format or "MP4").upper()
    extension = "mp3" if media_format == "MP3" else "mp4"

    filename = (
        f"{output_prefix}{safe_title} "
        f"[{start_tag} to {end_tag}].{extension}"
    )

    output_file = unique_output_path(
        os.path.join(
            DOWNLOADS,
            filename
        )
    )

    prefix = f"[{job_label}] " if job_label else ""

    if progress_callback:
        try:
            progress_callback(96.0)
        except Exception:
            pass

    if stats_callback:
        try:
            stats_callback(
                percent=96.0,
                speed="LOCAL CUT",
                eta="00:00",
                size=None,
            )
        except Exception:
            pass

    log(prefix + "✂ Local cut started from TURBO cache...")

    # Fast stream-copy cut. This avoids downloading the section through
    # FFmpeg and avoids re-encoding the whole requested part.
    if media_format == "MP3":
        # The turbo audio cache is already MP3, so this is an extremely
        # fast local frame-copy cut with no second audio re-encode.
        command = [
            FFMPEG,
            "-y",
            "-ss", f"{start_seconds:.3f}",
            "-i", cache_file,
            "-t", f"{duration:.3f}",
            "-map", "0:a:0?",
            "-c:a", "copy",
            "-progress", "pipe:1",
            "-nostats",
            "-loglevel", "error",
            output_file,
        ]
    else:
        command = [
            FFMPEG,
            "-y",
            "-ss", f"{start_seconds:.3f}",
            "-i", cache_file,
            "-t", f"{duration:.3f}",
            "-map", "0:v:0?",
            "-map", "0:a:0?",
            "-c", "copy",
            "-avoid_negative_ts", "make_zero",
            "-movflags", "+faststart",
            "-progress", "pipe:1",
            "-nostats",
            "-loglevel", "error",
            output_file,
        ]

    process = None
    out_time = 0.0

    try:
        creationflags = (
            subprocess.CREATE_NO_WINDOW
            if os.name == "nt"
            else 0
        )

        process = subprocess.Popen(
            command,
            env=build_tool_env(),
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            encoding="utf-8",
            errors="replace",
            creationflags=creationflags,
        )

        register_process(process)

        for raw_line in process.stdout:
            if stop_all_event.is_set():
                try:
                    process.terminate()
                except Exception:
                    pass

                return 130, "stopped", None

            line = raw_line.strip()

            if not line or "=" not in line:
                continue

            key, value = line.split("=", 1)
            key = key.strip()
            value = value.strip()

            if key == "out_time":
                out_time = timecode_to_seconds(value)

            elif key == "progress":
                local_ratio = (
                    min(1.0, max(0.0, out_time / duration))
                    if duration > 0
                    else 0.0
                )

                overall = 96.0 + local_ratio * 3.5

                if progress_callback:
                    try:
                        progress_callback(overall)
                    except Exception:
                        pass

                if stats_callback:
                    try:
                        stats_callback(
                            percent=overall,
                            speed="LOCAL CUT",
                            eta="00:00",
                            size=None,
                        )
                    except Exception:
                        pass

        code = process.wait()

        if code == 0 and os.path.isfile(output_file):
            if media_format == "MP4":
                ensure_tv_compatible_mp4(
                    output_file,
                    stats_callback=stats_callback,
                    job_label=job_label,
                )

            register_current_job_output_path(
                output_file
            )

            if progress_callback:
                try:
                    progress_callback(100.0)
                except Exception:
                    pass

            if stats_callback:
                try:
                    stats_callback(
                        percent=100.0,
                        speed="DONE",
                        eta="",
                        size=(
                            _human_file_size(
                                os.path.getsize(
                                    output_file
                                )
                            )
                            if os.path.isfile(
                                output_file
                            )
                            else None
                        ),
                    )
                except Exception:
                    pass

            log(
                prefix
                + "✂ Local cut finished ✅ • TV SAFE checked"
            )
            return 0, "done", output_file

        log(prefix + f"Local cut failed. Code: {code}")
        return code, "error", None

    except Exception as exc:
        log(prefix + f"LOCAL CUT ERROR: {exc}")
        return 999, "error", None

    finally:
        if process is not None:
            unregister_process(process)



# ============================================================
# V32.24 — SMART FAST PART
# ============================================================

def _existing_turbo_cache_for_part(
    url,
    quality,
    media_format="MP4",
):
    """
    Return (cache_file, title) only if the OLD full-video cache already exists.
    IMPORTANT: this function NEVER downloads anything.
    """
    video_id = youtube_video_id(
        url
    )

    media_format = str(
        media_format or "MP4"
    ).upper()

    if media_format == "MP3":
        cache_key = (
            f"{video_id}__AUDIO_MP3"
        )
    else:
        cache_key = (
            f"{video_id}__{quality}__MP4"
        )

    candidates, meta_path = cache_paths(
        cache_key
    )
    meta = read_cache_meta(
        meta_path
    )

    cache_file = choose_cache_file(
        candidates,
        meta,
    )

    if (
        cache_file
        and os.path.isfile(
            cache_file
        )
    ):
        title = str(
            meta.get(
                "title",
                "",
            )
            or ""
        ).strip()

        if not title:
            title = os.path.splitext(
                os.path.basename(
                    cache_file
                )
            )[0]

        return (
            cache_file,
            title,
        )

    return (
        None,
        "",
    )



def normalize_part_time_text(value):
    """
    Normalize user-entered PART time for yt-dlp/FFmpeg.
    Examples:
      00.10.00 -> 00:10:00
      00:10:00 -> 00:10:00
      10.30    -> 10:30
    """
    raw = str(value or "").strip()

    if not raw:
        return ""

    raw = raw.replace(".", ":")
    raw = re.sub(r":+", ":", raw).strip(":")

    parts = raw.split(":")

    if not all(part.isdigit() for part in parts if part != ""):
        return raw

    return ":".join(part.zfill(2) for part in parts)


def part_seconds(value):
    return timecode_to_seconds(normalize_part_time_text(value))


def _part_output_filename(
    title,
    start,
    end,
    output_prefix="",
    media_format="MP4",
):
    media_format = str(
        media_format or "MP4"
    ).upper()

    extension = (
        "mp3"
        if media_format == "MP3"
        else "mp4"
    )

    safe_title = windows_safe_name(
        clean_video_title(
            title
        ),
        max_length=135,
    )

    start_tag = (
        str(start)
        .replace(":", "-")
        .replace(".", "-")
    )
    end_tag = (
        str(end)
        .replace(":", "-")
        .replace(".", "-")
    )

    filename = (
        f"{output_prefix}{safe_title} "
        f"[{start_tag} to {end_tag}].{extension}"
    )

    return unique_output_path(
        os.path.join(
            DOWNLOADS,
            filename,
        )
    )


def _headers_to_ffmpeg_string(*header_dicts):
    merged = {}

    for header_dict in header_dicts:
        if not isinstance(
            header_dict,
            dict,
        ):
            continue

        for key, value in header_dict.items():
            key = str(
                key or ""
            ).strip()
            value = str(
                value or ""
            ).strip()

            if (
                not key
                or not value
            ):
                continue

            # FFmpeg supplies these itself; passing stale values can break
            # signed media requests.
            if key.lower() in {
                "host",
                "content-length",
                "connection",
            }:
                continue

            merged[
                key
            ] = value

    if "User-Agent" not in merged:
        merged[
            "User-Agent"
        ] = (
            "Mozilla/5.0 "
            "(Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 "
            "(KHTML, like Gecko) "
            "Chrome/152.0.0.0 Safari/537.36"
        )

    return "".join(
        f"{key}: {value}\r\n"
        for key, value in merged.items()
    )


def _run_ytdlp_json_for_part(
    url,
    quality,
    media_format="MP4",
    job_label="",
):
    """
    Metadata-only resolver.

    V32.25 intentionally does NOT pass -f here. Some YouTube clients expose
    different format sets; asking for one strict selector can fail before JSON
    is returned. Fetch all formats, then Z²SE selects a usable stream itself.
    """
    prefix = f"[{job_label}] " if job_label else ""

    command = [
        YTDLP,
        "-J",
        "--no-playlist",
        "--no-warnings",
        "--no-progress",
        "--ffmpeg-location",
        FFMPEG_DIR,
    ]

    if pot_ready:
        command += [
            "--extractor-args",
            "youtube:player_client=mweb",
        ]

    command.append(url)

    process = None

    try:
        process = subprocess.Popen(
            command,
            env=build_tool_env(),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding="utf-8",
            errors="replace",
            creationflags=(
                subprocess.CREATE_NO_WINDOW
                if os.name == "nt"
                else 0
            ),
        )

        register_process(process)

        stdout = ""
        stderr = ""

        while True:
            if should_stop_current_job():
                try:
                    process.terminate()
                except Exception:
                    pass
                return 130, None, "stopped"

            try:
                stdout, stderr = process.communicate(timeout=0.25)
                break
            except subprocess.TimeoutExpired:
                continue

        if process.returncode != 0:
            useful_error = (
                stderr.strip()
                or stdout.strip()
                or f"yt-dlp code {process.returncode}"
            )
            log(
                prefix
                + "FAST PART metadata resolver failed: "
                + useful_error[-600:]
            )
            return process.returncode, None, "error"

        try:
            info = json.loads(stdout)
        except Exception as exc:
            log(prefix + f"FAST PART resolver JSON ERROR: {exc}")
            return 998, None, "error"

        return 0, info, "done"

    except Exception as exc:
        log(prefix + f"FAST PART metadata resolver ERROR: {exc}")
        return 999, None, "error"

    finally:
        if process is not None:
            unregister_process(process)


def _quality_height_limit(quality):
    mapping = {
        "1080p": 1080,
        "720p": 720,
        "480p": 480,
        "Best": 99999,
        "BEST": 99999,
    }
    return mapping.get(str(quality), 99999)


def _format_is_direct_http(fmt):
    if not isinstance(fmt, dict):
        return False
    url = str(fmt.get("url", "") or "").strip()
    return url.startswith(("http://", "https://"))


def _format_height(fmt):
    try:
        return int(fmt.get("height", 0) or 0)
    except Exception:
        return 0


def _format_tbr(fmt):
    try:
        return float(fmt.get("tbr", 0) or 0)
    except Exception:
        return 0.0


def _format_abr(fmt):
    try:
        return float(fmt.get("abr", 0) or 0)
    except Exception:
        return 0.0


def _select_best_direct_streams(info, quality, media_format="MP4"):
    """
    Select direct URLs from the complete yt-dlp format table.
    H.264/AAC is preferred for TV compatibility, but any usable stream can be
    selected and the final short PART can be converted to TV-safe MP4.
    """
    if not isinstance(info, dict):
        return None

    formats = [
        fmt
        for fmt in (info.get("formats") or [])
        if _format_is_direct_http(fmt)
    ]

    if not formats:
        if _format_is_direct_http(info):
            return {"mode": "combined", "media": info}
        return None

    height_limit = _quality_height_limit(quality)
    video_only = []
    audio_only = []
    combined = []

    for fmt in formats:
        vcodec = str(fmt.get("vcodec", "none") or "none").lower()
        acodec = str(fmt.get("acodec", "none") or "none").lower()
        has_video = vcodec != "none"
        has_audio = acodec != "none"
        height = _format_height(fmt)

        if has_video and height and height > height_limit:
            continue

        if has_video and has_audio:
            combined.append(fmt)
        elif has_video:
            video_only.append(fmt)
        elif has_audio:
            audio_only.append(fmt)

    media_format = str(media_format or "MP4").upper()

    if media_format == "MP3":
        if audio_only:
            best_audio = max(
                audio_only,
                key=lambda fmt: (
                    1 if str(fmt.get("acodec", "")).lower().startswith(("mp4a", "aac")) else 0,
                    _format_abr(fmt),
                    _format_tbr(fmt),
                ),
            )
            return {"mode": "audio", "audio": best_audio}

        if combined:
            best_combined = max(
                combined,
                key=lambda fmt: (_format_abr(fmt), _format_tbr(fmt)),
            )
            return {"mode": "combined", "media": best_combined}

        return None

    def video_score(fmt):
        codec = str(fmt.get("vcodec", "") or "").lower()
        return (
            1 if (codec.startswith("avc1") or codec in {"h264", "avc"}) else 0,
            _format_height(fmt),
            _format_tbr(fmt),
        )

    def audio_score(fmt):
        codec = str(fmt.get("acodec", "") or "").lower()
        return (
            1 if (codec.startswith("mp4a") or codec == "aac") else 0,
            _format_abr(fmt),
            _format_tbr(fmt),
        )

    if video_only:
        best_video = max(video_only, key=video_score)

        if audio_only:
            best_audio = max(audio_only, key=audio_score)
            return {
                "mode": "separate",
                "video": best_video,
                "audio": best_audio,
            }

        return {"mode": "video", "video": best_video}

    if combined:
        best_combined = max(
            combined,
            key=lambda fmt: (video_score(fmt), audio_score(fmt)),
        )
        return {"mode": "combined", "media": best_combined}

    return None


def _selected_direct_streams_from_info(
    info,
    quality="Best",
    media_format="MP4",
):
    return _select_best_direct_streams(
        info,
        quality,
        media_format,
    )


def _ffmpeg_seek_input_args(
    stream,
    start_seconds,
    base_headers=None,
):
    stream_url = str(
        stream.get(
            "url",
            "",
        )
        or ""
    ).strip()

    if not stream_url:
        return []

    headers = _headers_to_ffmpeg_string(
        base_headers,
        stream.get(
            "http_headers",
            {},
        ),
    )

    args = [
        "-ss",
        f"{start_seconds:.3f}",
    ]

    if headers:
        args += [
            "-headers",
            headers,
        ]

    args += [
        "-i",
        stream_url,
    ]

    return args


def _fast_part_validate_output(
    path,
    requested_duration,
    media_format="MP4",
):
    if (
        not path
        or not os.path.isfile(
            path
        )
    ):
        return False

    try:
        size = os.path.getsize(
            path
        )
    except Exception:
        return False

    media_format = str(
        media_format or "MP4"
    ).upper()

    minimum_size = (
        48 * 1024
        if media_format == "MP3"
        else 96 * 1024
    )

    if size < minimum_size:
        return False

    duration, has_audio, has_video = _probe_final_media(
        path
    )

    if media_format == "MP3":
        if not has_audio:
            return False
    else:
        if not has_video:
            return False

    requested_duration = float(
        requested_duration or 0.0
    )

    # Stream-copy starts can land on the previous keyframe. A result slightly
    # longer/shorter than requested is acceptable, but a tiny/incomplete file
    # is not.
    if (
        requested_duration >= 4.0
        and duration > 0
        and duration
        < requested_duration * 0.55
    ):
        return False

    return True


def fast_direct_part_download(
    url,
    quality,
    start,
    end,
    output_prefix="",
    progress_callback=None,
    stats_callback=None,
    job_label="",
    media_format="MP4",
):
    """
    FAST PART primary engine:
    1) yt-dlp resolves selected direct URLs only.
    2) FFmpeg seeks BEFORE the network input.
    3) Only the requested time window is fetched/processed.

    This is fundamentally different from the old V11 Turbo Part which first
    downloaded the entire video.
    """
    prefix = (
        f"[{job_label}] "
        if job_label
        else ""
    )

    start = normalize_part_time_text(start)
    end = normalize_part_time_text(end)

    start_seconds = part_seconds(start)
    end_seconds = part_seconds(end)
    duration = max(
        0.0,
        end_seconds - start_seconds,
    )

    if duration <= 0:
        return (
            2,
            "error",
        )

    set_status(
        "Fast Part: resolving stream..."
    )

    if stats_callback:
        try:
            stats_callback(
                percent=1.0,
                speed="RESOLVING",
                eta="",
                size=None,
            )
        except Exception:
            pass

    code, info, state = _run_ytdlp_json_for_part(
        url=url,
        quality=quality,
        media_format=media_format,
        job_label=job_label,
    )

    if state != "done":
        return (
            code,
            state,
        )

    title = clean_video_title(
        info.get(
            "title",
            "",
        )
    )

    if not title:
        title = (
            best_job_title(
                _current_job_index()
            )
            if _current_job_index() is not None
            else ""
        )

    title = (
        title
        or "Video"
    )

    current_index = _current_job_index()

    if current_index is not None:
        remember_job_title(
            current_index,
            title,
        )

    if stats_callback:
        try:
            stats_callback(
                percent=3.0,
                speed="STREAM READY",
                eta=seconds_to_eta(
                    duration
                ),
                size=None,
                title=title,
            )
        except Exception:
            pass

    selected = _selected_direct_streams_from_info(
        info,
        quality=quality,
        media_format=media_format,
    )

    if not selected:
        log(
            prefix
            + "FAST PART: no usable direct stream found in extractor format table."
        )
        return (
            997,
            "error",
        )

    media_format = str(
        media_format or "MP4"
    ).upper()

    output_file = _part_output_filename(
        title=title,
        start=start,
        end=end,
        output_prefix=output_prefix,
        media_format=media_format,
    )

    base_headers = info.get(
        "http_headers",
        {},
    )

    command = [
        FFMPEG,
        "-y",
        "-hide_banner",
    ]

    mode = selected[
        "mode"
    ]

    selected_video = None
    selected_audio = None

    if mode == "separate":
        selected_video = selected[
            "video"
        ]
        selected_audio = selected[
            "audio"
        ]

        command += _ffmpeg_seek_input_args(
            selected_video,
            start_seconds,
            base_headers,
        )

        command += _ffmpeg_seek_input_args(
            selected_audio,
            start_seconds,
            base_headers,
        )

    elif mode == "combined":
        selected_video = selected[
            "media"
        ]
        selected_audio = selected[
            "media"
        ]

        command += _ffmpeg_seek_input_args(
            selected[
                "media"
            ],
            start_seconds,
            base_headers,
        )

    elif mode == "audio":
        selected_audio = selected[
            "audio"
        ]

        command += _ffmpeg_seek_input_args(
            selected_audio,
            start_seconds,
            base_headers,
        )

    elif mode == "video":
        selected_video = selected[
            "video"
        ]

        command += _ffmpeg_seek_input_args(
            selected_video,
            start_seconds,
            base_headers,
        )

    else:
        return (
            996,
            "error",
        )

    command += [
        "-t",
        f"{duration:.3f}",
    ]

    if media_format == "MP3":
        if mode == "separate":
            command += [
                "-map",
                "1:a:0?",
            ]
        else:
            command += [
                "-map",
                "0:a:0?",
            ]

        command += [
            "-vn",
            "-c:a",
            "libmp3lame",
            "-b:a",
            "320k",
        ]

    else:
        if mode == "separate":
            command += [
                "-map",
                "0:v:0?",
                "-map",
                "1:a:0?",
            ]
        else:
            command += [
                "-map",
                "0:v:0?",
                "-map",
                "0:a:0?",
            ]

        video_codec = str(
            (
                selected_video
                or {}
            ).get(
                "vcodec",
                "",
            )
            or ""
        ).lower()

        audio_codec = str(
            (
                selected_audio
                or {}
            ).get(
                "acodec",
                "",
            )
            or ""
        ).lower()

        # Keep the fast stream-copy path whenever the selected source is
        # already TV-safe. Otherwise transcode ONLY the requested short part.
        video_can_copy = (
            video_codec.startswith(
                "avc1"
            )
            or video_codec in {
                "h264",
                "avc",
            }
        )

        audio_can_copy = (
            audio_codec.startswith(
                "mp4a"
            )
            or audio_codec == "aac"
            or not selected_audio
        )

        if video_can_copy:
            command += [
                "-c:v",
                "copy",
                "-tag:v",
                "avc1",
            ]
        else:
            command += [
                "-c:v",
                "libx264",
                "-preset",
                "veryfast",
                "-crf",
                "20",
                "-pix_fmt",
                "yuv420p",
                "-vf",
                "scale=trunc(iw/2)*2:trunc(ih/2)*2,format=yuv420p",
                "-tag:v",
                "avc1",
            ]

        if selected_audio:
            if audio_can_copy:
                command += [
                    "-c:a",
                    "copy",
                ]
            else:
                command += [
                    "-c:a",
                    "aac",
                    "-b:a",
                    "192k",
                    "-ac",
                    "2",
                    "-ar",
                    "48000",
                ]
        else:
            command += [
                "-an",
            ]

        command += [
            "-avoid_negative_ts",
            "make_zero",
            "-movflags",
            "+faststart",
        ]

    command += [
        "-progress",
        "pipe:1",
        "-nostats",
        "-loglevel",
        "error",
        output_file,
    ]

    log(
        prefix
        + f"⚡ FAST PART: downloading only "
        + f"{start} → {end}"
    )

    set_status(
        "Fast Part: downloading selected time only..."
    )

    process = None
    out_time = 0.0
    started_at = time.perf_counter()
    last_size = 0
    last_wall = started_at

    try:
        process = subprocess.Popen(
            command,
            env=build_tool_env(),
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            encoding="utf-8",
            errors="replace",
            creationflags=(
                subprocess.CREATE_NO_WINDOW
                if os.name == "nt"
                else 0
            ),
        )

        register_process(
            process
        )

        for raw_line in process.stdout:
            if should_stop_current_job():
                try:
                    process.terminate()
                except Exception:
                    pass

                return (
                    130,
                    "stopped",
                )

            line = raw_line.strip()

            if not line:
                continue

            if "=" not in line:
                log(
                    prefix
                    + line
                )
                continue

            key, value = line.split(
                "=",
                1,
            )
            key = key.strip()
            value = value.strip()

            if key == "out_time":
                out_time = timecode_to_seconds(
                    value
                )

            elif key == "progress":
                now = time.perf_counter()

                ratio = (
                    min(
                        1.0,
                        max(
                            0.0,
                            out_time / duration,
                        ),
                    )
                    if duration > 0
                    else 0.0
                )

                # 0-3% = stream resolve, 3-98.5% = actual selected range.
                percent = (
                    3.0
                    + ratio * 95.5
                )

                speed_text = None

                try:
                    current_size = (
                        os.path.getsize(
                            output_file
                        )
                        if os.path.isfile(
                            output_file
                        )
                        else 0
                    )

                    elapsed = max(
                        0.05,
                        now - last_wall,
                    )
                    delta = max(
                        0,
                        current_size - last_size,
                    )

                    if delta > 0:
                        speed_text = bytes_to_human(
                            delta / elapsed
                        ) + "/s"

                    last_size = current_size
                    last_wall = now
                except Exception:
                    current_size = 0

                remaining = max(
                    0.0,
                    duration - out_time,
                )

                eta = seconds_to_eta(
                    remaining
                )

                if progress_callback:
                    try:
                        progress_callback(
                            percent
                        )
                    except Exception:
                        pass

                if stats_callback:
                    try:
                        stats_callback(
                            percent=percent,
                            speed=speed_text,
                            eta=eta,
                            size=(
                                bytes_to_human(
                                    current_size
                                )
                                if current_size
                                else None
                            ),
                            title=title,
                        )
                    except Exception:
                        pass

        code = process.wait()

        if should_stop_current_job():
            return (
                130,
                "stopped",
            )

        if (
            code == 0
            and _fast_part_validate_output(
                output_file,
                duration,
                media_format,
            )
        ):
            if media_format == "MP4":
                # Usually already TV-safe because the selected format prefers
                # AVC/AAC. This is a cheap verification / emergency conversion.
                ensure_tv_compatible_mp4(
                    output_file,
                    stats_callback=stats_callback,
                    job_label=job_label,
                )

            register_current_job_output_path(
                output_file
            )

            if progress_callback:
                try:
                    progress_callback(
                        100.0
                    )
                except Exception:
                    pass

            if stats_callback:
                try:
                    stats_callback(
                        percent=100.0,
                        speed="DONE",
                        eta="",
                        size=_human_file_size(
                            os.path.getsize(
                                output_file
                            )
                        ),
                        title=title,
                    )
                except Exception:
                    pass

            log(
                prefix
                + "✅ FAST PART finished — full video was NOT downloaded."
            )

            return (
                0,
                "done",
            )

        log(
            prefix
            + f"FAST PART direct engine failed/invalid. Code: {code}"
        )

        try:
            if os.path.isfile(
                output_file
            ):
                os.remove(
                    output_file
                )
        except Exception:
            pass

        return (
            code or 995,
            "error",
        )

    except Exception as exc:
        log(
            prefix
            + f"FAST PART direct ERROR: {exc}"
        )

        try:
            if os.path.isfile(
                output_file
            ):
                os.remove(
                    output_file
                )
        except Exception:
            pass

        return (
            999,
            "error",
        )

    finally:
        if process is not None:
            unregister_process(
                process
            )



def is_youtube_page_url(url):
    try:
        host = (
            urlparse(
                str(url or "")
            ).hostname
            or ""
        ).lower()

        return (
            host == "youtu.be"
            or host.endswith(
                ".youtube.com"
            )
            or host == "youtube.com"
            or host.endswith(
                ".youtube-nocookie.com"
            )
        )
    except Exception:
        return False


def get_part_format(quality):
    """
    PART downloads prioritize availability and speed.
    TV Safe conversion runs on the SHORT final section afterwards, so we do
    not reject the job just because H.264/AAC is missing on this YouTube client.
    """
    value = str(
        quality or "Best"
    ).strip()

    limits = {
        "1080p": 1080,
        "720p": 720,
        "480p": 480,
    }

    height = limits.get(
        value
    )

    if height:
        return (
            f"bv*[height<={height}]+ba/"
            f"b[height<={height}]"
        )

    return "bv*+ba/b"


def _cleanup_part_attempt_files(temp_base):
    """
    Remove only temporary files belonging to THIS failed PART attempt.
    Never touches unrelated downloads.
    """
    try:
        folder = os.path.dirname(
            temp_base
        )
        prefix = os.path.basename(
            temp_base
        )

        for name in os.listdir(
            folder
        ):
            if not name.startswith(
                prefix
            ):
                continue

            path = os.path.join(
                folder,
                name,
            )

            if not os.path.isfile(
                path
            ):
                continue

            lower = name.lower()

            if lower.endswith(
                (
                    ".part",
                    ".ytdl",
                    ".tmp",
                    ".temp",
                )
            ):
                try:
                    os.remove(
                        path
                    )
                except Exception:
                    pass
    except Exception:
        pass


def ytdlp_sections_part_download(
    url,
    quality,
    start,
    end,
    output_prefix="",
    progress_callback=None,
    stats_callback=None,
    job_label="",
    media_format="MP4",
):
    """
    V32.26 robust section engine.

    YouTube:
      - yt-dlp owns extraction/auth/PO-token handling.
      - FFmpeg receives only the selected From -> To range.
      - Real FFmpeg progress is parsed, so UI no longer sits at 3%.
      - If mweb fails, retry once with yt-dlp's normal client selection.
      - A dead/stalled attempt is terminated instead of hanging forever.

    The whole source video is NOT downloaded first.
    """
    prefix = (
        f"[{job_label}] "
        if job_label
        else ""
    )

    start = normalize_part_time_text(
        start
    )
    end = normalize_part_time_text(
        end
    )

    start_seconds = part_seconds(
        start
    )
    end_seconds = part_seconds(
        end
    )
    duration = max(
        0.0,
        end_seconds - start_seconds,
    )

    if duration <= 0:
        return (
            2,
            "error",
        )

    media_format = str(
        media_format or "MP4"
    ).upper()

    # Metadata/title only. Failure here is not fatal; the real section command
    # below may still work.
    code, info, state = _run_ytdlp_json_for_part(
        url=url,
        quality=quality,
        media_format=media_format,
        job_label=job_label,
    )

    if state == "stopped":
        return (
            code,
            state,
        )

    title = (
        clean_video_title(
            info.get(
                "title",
                "",
            )
        )
        if isinstance(
            info,
            dict,
        )
        else ""
    )

    if not title:
        current_index = _current_job_index()

        if current_index is not None:
            title = best_job_title(
                current_index
            )

    title = (
        title
        or "Video"
    )

    current_index = _current_job_index()

    if current_index is not None:
        remember_job_title(
            current_index,
            title,
        )

    output_file = _part_output_filename(
        title=title,
        start=start,
        end=end,
        output_prefix=output_prefix,
        media_format=media_format,
    )

    temp_base = os.path.splitext(
        output_file
    )[0]

    format_selector = (
        "ba/b"
        if media_format == "MP3"
        else get_part_format(
            quality
        )
    )

    # For YouTube, try the same mweb path first because the app already has
    # PO-token support. If that route fails, retry without forcing a client.
    client_attempts = (
        [True, False]
        if is_youtube_page_url(
            url
        )
        else [False]
    )

    last_code = 994

    for attempt_number, use_mweb in enumerate(
        client_attempts,
        start=1,
    ):
        if should_stop_current_job():
            return (
                130,
                "stopped",
            )

        _cleanup_part_attempt_files(
            temp_base
        )

        command = [
            YTDLP,
            "--newline",
            "--windows-filenames",
            "--no-playlist",
            "--retries",
            "10",
            "--fragment-retries",
            "10",
            "--socket-timeout",
            "20",
            "--ffmpeg-location",
            FFMPEG_DIR,
            "--download-sections",
            (
                "*"
                + start
                + "-"
                + end
            ),
            "-f",
            format_selector,
            "-P",
            DOWNLOADS,
            "-o",
            os.path.basename(
                temp_base
            ) + ".%(ext)s",
            "--print",
            "after_move:__VD_PART_FILE__%(filepath)s",
            "--progress",
            "--downloader-args",
            (
                "ffmpeg:-progress pipe:1 "
                "-nostats -loglevel error"
            ),
        ]

        if media_format == "MP3":
            command += [
                "-x",
                "--audio-format",
                "mp3",
                "--audio-quality",
                "320K",
            ]
        else:
            command += [
                "--merge-output-format",
                "mp4",
            ]

        if (
            use_mweb
            and pot_ready
        ):
            command += [
                "--extractor-args",
                "youtube:player_client=mweb",
            ]

        command.append(
            url
        )

        process = None
        final_path = ""
        out_time = 0.0
        total_size = 0
        ffmpeg_speed_factor = 0.0
        saw_ffmpeg_machine_progress = False

        started_at = time.monotonic()
        last_activity = started_at
        last_progress_at = started_at
        reader_done = False

        line_queue = Queue()

        log(
            prefix
            + "⚡ PART engine attempt "
            + str(attempt_number)
            + (
                " • YouTube mweb"
                if use_mweb
                else " • normal extractor"
            )
        )

        if stats_callback:
            try:
                stats_callback(
                    percent=3.0,
                    speed="STARTING PART",
                    eta=seconds_to_eta(
                        duration
                    ),
                    size=None,
                    title=title,
                )
            except Exception:
                pass

        try:
            process = subprocess.Popen(
                command,
                env=build_tool_env(),
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                encoding="utf-8",
                errors="replace",
                bufsize=1,
                creationflags=(
                    subprocess.CREATE_NO_WINDOW
                    if os.name == "nt"
                    else 0
                ),
            )

            register_process(
                process
            )

            def _reader():
                try:
                    for raw in process.stdout:
                        line_queue.put(
                            raw
                        )
                except Exception:
                    pass
                finally:
                    line_queue.put(
                        None
                    )

            threading.Thread(
                target=_reader,
                daemon=True,
                name=(
                    f"Z2SEPartReader"
                    f"{job_label or attempt_number}"
                ),
            ).start()

            while True:
                if should_stop_current_job():
                    try:
                        process.terminate()
                    except Exception:
                        pass

                    return (
                        130,
                        "stopped",
                    )

                now = time.monotonic()

                # Never hang forever. With -progress pipe:1 a healthy FFmpeg
                # section download produces activity regularly.
                if (
                    not reader_done
                    and now - last_activity > 75.0
                ):
                    log(
                        prefix
                        + "PART engine stalled for 75s -> terminating attempt."
                    )

                    try:
                        process.terminate()
                    except Exception:
                        pass

                    break

                try:
                    raw = line_queue.get(
                        timeout=0.40
                    )
                except Empty:
                    if process.poll() is not None:
                        # Allow the reader to flush any final lines.
                        if reader_done:
                            break
                    continue

                if raw is None:
                    reader_done = True

                    if process.poll() is not None:
                        break

                    continue

                last_activity = now

                line = raw.strip()

                if not line:
                    continue

                if line.startswith(
                    "__VD_PART_FILE__"
                ):
                    final_path = _normalize_output_path(
                        line[
                            len(
                                "__VD_PART_FILE__"
                            ):
                        ].strip()
                    )
                    continue

                # FFmpeg machine progress from yt-dlp's section downloader.
                if "=" in line:
                    key, value = line.split(
                        "=",
                        1,
                    )
                    key = key.strip()
                    value = value.strip()

                    if key == "out_time":
                        saw_ffmpeg_machine_progress = True
                        out_time = timecode_to_seconds(
                            value
                        )

                    elif key == "total_size":
                        try:
                            total_size = max(
                                0,
                                int(
                                    value
                                ),
                            )
                        except Exception:
                            pass

                    elif key == "speed":
                        try:
                            ffmpeg_speed_factor = float(
                                value.lower()
                                .replace(
                                    "x",
                                    "",
                                )
                                .strip()
                            )
                        except Exception:
                            pass

                    elif key == "progress":
                        saw_ffmpeg_machine_progress = True
                        last_progress_at = now

                        ratio = (
                            min(
                                1.0,
                                max(
                                    0.0,
                                    out_time
                                    / duration,
                                ),
                            )
                            if duration > 0
                            else 0.0
                        )

                        percent_value = (
                            3.0
                            + ratio * 95.0
                        )

                        remaining = max(
                            0.0,
                            duration - out_time,
                        )

                        eta_text = seconds_to_eta(
                            (
                                remaining
                                / ffmpeg_speed_factor
                                if ffmpeg_speed_factor > 0
                                else remaining
                            )
                        )

                        speed_text = (
                            f"{ffmpeg_speed_factor:.2f}x"
                            if ffmpeg_speed_factor > 0
                            else "PART"
                        )

                        if progress_callback:
                            try:
                                progress_callback(
                                    percent_value
                                )
                            except Exception:
                                pass

                        if stats_callback:
                            try:
                                stats_callback(
                                    percent=percent_value,
                                    speed=speed_text,
                                    eta=eta_text,
                                    size=(
                                        bytes_to_human(
                                            total_size
                                        )
                                        if total_size
                                        else None
                                    ),
                                    title=title,
                                )
                            except Exception:
                                pass

                        continue

                # Standard yt-dlp downloader progress (some sites don't expose
                # FFmpeg machine-progress cleanly).
                percent, speed, eta, size = parse_ytdlp_download_stats(
                    line
                )

                if (
                    percent is not None
                    or speed
                    or eta
                    or size
                ):
                    last_progress_at = now

                    # yt-dlp may report its *input request* as 100% while
                    # FFmpeg is still only halfway through the requested
                    # section. Never let that fake 100% overwrite real
                    # out_time-based progress.
                    if stats_callback:
                        try:
                            stats_callback(
                                percent=(
                                    None
                                    if saw_ffmpeg_machine_progress
                                    else (
                                        min(
                                            98.0,
                                            max(
                                                3.0,
                                                float(
                                                    percent
                                                ),
                                            ),
                                        )
                                        if percent is not None
                                        else None
                                    )
                                ),
                                speed=(
                                    None
                                    if saw_ffmpeg_machine_progress
                                    else speed
                                ),
                                eta=(
                                    None
                                    if saw_ffmpeg_machine_progress
                                    else eta
                                ),
                                size=(
                                    None
                                    if saw_ffmpeg_machine_progress
                                    else size
                                ),
                                title=title,
                            )
                        except Exception:
                            pass

                # Suppress raw FFmpeg -progress machine fields. They used to
                # generate thousands of log lines. Keep only useful errors and
                # extractor messages.
                machine_key = (
                    line.split(
                        "=",
                        1,
                    )[0].strip()
                    if "=" in line
                    else ""
                )

                if machine_key in {
                    "frame",
                    "fps",
                    "stream_0_0_q",
                    "bitrate",
                    "total_size",
                    "out_time_us",
                    "out_time_ms",
                    "out_time",
                    "dup_frames",
                    "drop_frames",
                    "speed",
                    "progress",
                }:
                    continue

                if not line.startswith(
                    "[download]"
                ):
                    log(
                        prefix
                        + line
                    )

            # Process may still be alive after watchdog break.
            if process.poll() is None:
                try:
                    process.terminate()
                except Exception:
                    pass

                try:
                    process.wait(
                        timeout=5
                    )
                except Exception:
                    try:
                        process.kill()
                    except Exception:
                        pass

            code = (
                process.returncode
                if process.returncode is not None
                else 995
            )

            last_code = code

            if should_stop_current_job():
                return (
                    130,
                    "stopped",
                )

            if (
                not final_path
                or not os.path.isfile(
                    final_path
                )
            ):
                candidates = []

                for extension in (
                    ".mp4",
                    ".mkv",
                    ".webm",
                    ".mp3",
                    ".m4a",
                ):
                    candidate = (
                        temp_base
                        + extension
                    )

                    if os.path.isfile(
                        candidate
                    ):
                        candidates.append(
                            candidate
                        )

                if candidates:
                    final_path = max(
                        candidates,
                        key=lambda candidate: os.path.getmtime(
                            candidate
                        ),
                    )

            if (
                code == 0
                and final_path
                and _fast_part_validate_output(
                    final_path,
                    duration,
                    media_format,
                )
            ):
                if media_format == "MP4":
                    ensure_tv_compatible_mp4(
                        final_path,
                        stats_callback=stats_callback,
                        job_label=job_label,
                    )

                register_current_job_output_path(
                    final_path
                )

                if progress_callback:
                    try:
                        progress_callback(
                            100.0
                        )
                    except Exception:
                        pass

                if stats_callback:
                    try:
                        stats_callback(
                            percent=100.0,
                            speed="DONE",
                            eta="",
                            size=_human_file_size(
                                os.path.getsize(
                                    final_path
                                )
                            ),
                            title=title,
                        )
                    except Exception:
                        pass

                log(
                    prefix
                    + "✅ PART finished — only requested range processed."
                )

                return (
                    0,
                    "done",
                )

            log(
                prefix
                + "PART attempt failed. Code: "
                + str(
                    code
                )
            )

        except Exception as exc:
            last_code = 999

            log(
                prefix
                + f"PART engine ERROR: {exc}"
            )

        finally:
            if process is not None:
                unregister_process(
                    process
                )

        # Retry next client only after cleaning dead partials.
        _cleanup_part_attempt_files(
            temp_base
        )

    log(
        prefix
        + "❌ PART engine failed after all fast attempts."
    )

    return (
        last_code or 994,
        "error",
    )



def _format_size_estimate(fmt, source_duration=0.0):
    if not isinstance(
        fmt,
        dict,
    ):
        return 0

    for key in (
        "filesize",
        "filesize_approx",
    ):
        try:
            value = int(
                fmt.get(
                    key,
                    0,
                )
                or 0
            )

            if value > 0:
                return value
        except Exception:
            pass

    # Last resort: bitrate estimate.
    try:
        tbr = float(
            fmt.get(
                "tbr",
                0,
            )
            or 0
        )

        if (
            tbr > 0
            and source_duration > 0
        ):
            return int(
                tbr
                * 1000.0
                / 8.0
                * source_duration
            )
    except Exception:
        pass

    return 0


def _estimate_selected_source_bytes(
    info,
    quality,
    media_format="MP4",
):
    if not isinstance(
        info,
        dict,
    ):
        return 0

    try:
        source_duration = float(
            info.get(
                "duration",
                0,
            )
            or 0
        )
    except Exception:
        source_duration = 0.0

    selected = _select_best_direct_streams(
        info,
        quality,
        media_format,
    )

    if not selected:
        return 0

    mode = selected.get(
        "mode"
    )

    if mode == "separate":
        return (
            _format_size_estimate(
                selected.get(
                    "video"
                ),
                source_duration,
            )
            + _format_size_estimate(
                selected.get(
                    "audio"
                ),
                source_duration,
            )
        )

    if mode == "combined":
        return _format_size_estimate(
            selected.get(
                "media"
            ),
            source_duration,
        )

    if mode == "audio":
        return _format_size_estimate(
            selected.get(
                "audio"
            ),
            source_duration,
        )

    if mode == "video":
        return _format_size_estimate(
            selected.get(
                "video"
            ),
            source_duration,
        )

    return 0


def choose_youtube_part_strategy(
    url,
    quality,
    start,
    end,
    media_format="MP4",
    job_label="",
):
    """
    Return ("turbo"|"section", info).

    Current YouTube behavior can throttle FFmpeg --download-sections to about
    playback-rate speed for larger media. Native yt-dlp downloads use bounded
    chunks/fragments and can be much faster.

    We compare a conservative estimate:
      section engine ~= 1.9x realtime when throttled
      native full cache ~= 3 MiB/s

    Full-cache is chosen only when its estimated completion time is clearly
    better. For tiny clips from huge videos, section mode remains available.
    """
    prefix = (
        f"[{job_label}] "
        if job_label
        else ""
    )

    start_seconds = part_seconds(
        start
    )
    end_seconds = part_seconds(
        end
    )
    part_duration = max(
        0.0,
        end_seconds - start_seconds,
    )

    code, info, state = _run_ytdlp_json_for_part(
        url=url,
        quality=quality,
        media_format=media_format,
        job_label=job_label,
    )

    if state == "stopped":
        return (
            "stopped",
            info,
        )

    if not isinstance(
        info,
        dict,
    ):
        # Metadata failed. Long requested sections are safer in Turbo mode;
        # short ones can still try the section engine.
        strategy = (
            "turbo"
            if part_duration >= 300.0
            else "section"
        )

        log(
            prefix
            + f"AUTO PART: metadata incomplete -> {strategy.upper()}."
        )

        return (
            strategy,
            info,
        )

    try:
        source_duration = float(
            info.get(
                "duration",
                0,
            )
            or 0
        )
    except Exception:
        source_duration = 0.0

    total_bytes = _estimate_selected_source_bytes(
        info,
        quality,
        media_format,
    )

    # Fresh YouTube/FFmpeg section downloads commonly behave around ~1.9x
    # realtime for larger responses. Add margin so Turbo must be meaningfully
    # faster before we download the whole source.
    section_est_seconds = (
        part_duration / 1.9
        if part_duration > 0
        else 999999.0
    )

    conservative_native_bps = (
        3.0
        * 1024.0
        * 1024.0
    )

    full_est_seconds = (
        total_bytes
        / conservative_native_bps
        if total_bytes > 0
        else 0.0
    )

    # Small source (< ~12 MiB) generally does not hit the current FFmpeg
    # throttling cliff, so section mode is ideal.
    likely_ffmpeg_throttled = (
        total_bytes <= 0
        or total_bytes > 12 * 1024 * 1024
    )

    if (
        total_bytes > 0
        and likely_ffmpeg_throttled
        and full_est_seconds
        < section_est_seconds * 0.78
    ):
        strategy = "turbo"

    elif (
        total_bytes <= 0
        and part_duration >= 300.0
    ):
        strategy = "turbo"

    else:
        strategy = "section"

    size_text = (
        bytes_to_human(
            total_bytes
        )
        if total_bytes > 0
        else "?"
    )

    log(
        prefix
        + "AUTO PART decision: "
        + strategy.upper()
        + f" • part={seconds_to_eta(part_duration)}"
        + f" • source≈{size_text}"
        + (
            f" • full≈{int(full_est_seconds)}s"
            if full_est_seconds > 0
            else ""
        )
        + f" • section≈{int(section_est_seconds)}s"
    )

    return (
        strategy,
        info,
    )


def smart_fast_part_download(
    url,
    quality,
    start,
    end,
    output_prefix="",
    progress_callback=None,
    stats_callback=None,
    job_label="",
    media_format="MP4",
):
    """
    V32.26 orchestration.

    0) Existing old cache -> instant local cut.
    1) YouTube -> yt-dlp section engine directly (avoids raw googlevideo 403).
    2) Other sites -> direct range engine, then yt-dlp section engine.
    3) Never fall back to downloading the whole video first.
    """
    prefix = (
        f"[{job_label}] "
        if job_label
        else ""
    )

    cached_file, cached_title = _existing_turbo_cache_for_part(
        url=url,
        quality=quality,
        media_format=media_format,
    )

    if cached_file:
        log(
            prefix
            + "⚡ FAST PART: existing cache found -> instant local cut."
        )

        code, result, _ = cut_cache_to_part(
            cache_file=cached_file,
            title=cached_title,
            start=start,
            end=end,
            output_prefix=output_prefix,
            progress_callback=progress_callback,
            stats_callback=stats_callback,
            job_label=job_label,
            media_format=media_format,
        )

        return (
            code,
            result,
        )

    log(
        prefix
        + "⚡ SMART PART: only requested time range will be processed."
    )

    if is_youtube_page_url(
        url
    ):
        strategy, _ = choose_youtube_part_strategy(
            url=url,
            quality=quality,
            start=start,
            end=end,
            media_format=media_format,
            job_label=job_label,
        )

        if strategy == "stopped":
            return (
                130,
                "stopped",
            )

        if strategy == "turbo":
            log(
                prefix
                + "🚀 YouTube AUTO FASTEST -> native parallel download + local cut."
            )

            # This is the repaired/high-speed version of the original Turbo
            # concept: bounded chunks + dashy fragments + -N16.
            return turbo_part_download(
                url=url,
                quality=quality,
                start=start,
                end=end,
                output_prefix=output_prefix,
                progress_callback=progress_callback,
                stats_callback=stats_callback,
                job_label=job_label,
                media_format=media_format,
            )

        log(
            prefix
            + "⚡ YouTube AUTO FASTEST -> section engine (small/short case)."
        )

        code, result = ytdlp_sections_part_download(
            url=url,
            quality=quality,
            start=start,
            end=end,
            output_prefix=output_prefix,
            progress_callback=progress_callback,
            stats_callback=stats_callback,
            job_label=job_label,
            media_format=media_format,
        )

    else:
        code, result = fast_direct_part_download(
            url=url,
            quality=quality,
            start=start,
            end=end,
            output_prefix=output_prefix,
            progress_callback=progress_callback,
            stats_callback=stats_callback,
            job_label=job_label,
            media_format=media_format,
        )

        if result not in {
            "done",
            "stopped",
        }:
            log(
                prefix
                + "Direct range unavailable -> yt-dlp section engine."
            )

            code, result = ytdlp_sections_part_download(
                url=url,
                quality=quality,
                start=start,
                end=end,
                output_prefix=output_prefix,
                progress_callback=progress_callback,
                stats_callback=stats_callback,
                job_label=job_label,
                media_format=media_format,
            )

    if result == "error":
        log(
            prefix
            + "❌ SMART PART failed. Full-video cache download was NOT started."
        )

    return (
        code,
        result,
    )


def _cache_file_for_key_if_complete(cache_key):
    try:
        candidates, meta_path = cache_paths(cache_key)
        meta = read_cache_meta(meta_path)
        cached = choose_cache_file(candidates, meta)

        if cached and os.path.isfile(cached):
            return cached, str(meta.get("title", "") or "").strip()
    except Exception:
        pass

    return None, ""


def _cleanup_isolated_cache_key(cache_key):
    try:
        if not os.path.isdir(CACHE_DIR):
            return

        for name in os.listdir(CACHE_DIR):
            if not name.startswith(str(cache_key)):
                continue

            path = os.path.join(CACHE_DIR, name)

            if os.path.isfile(path):
                try:
                    os.remove(path)
                except Exception:
                    pass
    except Exception:
        pass


def turbo_part_download(
    url,
    quality,
    start,
    end,
    output_prefix="",
    progress_callback=None,
    stats_callback=None,
    job_label="",
    media_format="MP4"
):
    """
    V32.32:
    Never let concurrent PART/FULL jobs of the same YouTube video share the
    same in-progress cache filename. A completed shared cache is still reused.
    """
    video_id = youtube_video_id(url)
    media_format = str(media_format or "MP4").upper()

    if media_format == "MP3":
        shared_cache_key = f"{video_id}__AUDIO_MP3"
    else:
        shared_cache_key = f"{video_id}__{quality}__MP4"

    prefix = f"[{job_label}] " if job_label else ""

    cached_file, cached_title = _cache_file_for_key_if_complete(
        shared_cache_key
    )

    if cached_file:
        log(prefix + "⚡ TURBO PART: completed shared cache hit -> local cut.")

        cut_code, cut_result, _ = cut_cache_to_part(
            cache_file=cached_file,
            title=cached_title,
            start=start,
            end=end,
            output_prefix=output_prefix,
            progress_callback=progress_callback,
            stats_callback=stats_callback,
            job_label=job_label,
            media_format=media_format,
        )

        return cut_code, cut_result

    safe_job = re.sub(
        r"[^A-Za-z0-9_-]+",
        "_",
        str(job_label or threading.get_ident()),
    ).strip("_")

    isolated_cache_key = (
        shared_cache_key
        + "__LIVE_"
        + safe_job
        + "_"
        + str(threading.get_ident())
    )

    log(prefix + "🚀 TURBO PART: isolated same-video-safe cache -> local cut")

    lock = get_cache_lock(isolated_cache_key)

    if not acquire_cache_lock(lock):
        return 130, "stopped"

    try:
        code, result, cache_file, title = obtain_turbo_cache(
            url=url,
            quality=quality,
            cache_key=isolated_cache_key,
            progress_callback=progress_callback,
            stats_callback=stats_callback,
            job_label=job_label,
            media_format=media_format,
        )

        if result != "done":
            return code, result

        set_status("Smart Fast Part: local cut...")

        cut_code, cut_result, _ = cut_cache_to_part(
            cache_file=cache_file,
            title=title,
            start=start,
            end=end,
            output_prefix=output_prefix,
            progress_callback=progress_callback,
            stats_callback=stats_callback,
            job_label=job_label,
            media_format=media_format,
        )

        return cut_code, cut_result

    finally:
        try:
            lock.release()
        except Exception:
            pass

        _cleanup_isolated_cache_key(isolated_cache_key)


def clear_turbo_cache():
    if downloads_are_running():
        messagebox.showwarning(
            "Cache",
            "خلي التحميلات تسالي قبل ما تمسح Cache."
        )
        return

    try:
        if os.path.isdir(CACHE_DIR):
            shutil.rmtree(CACHE_DIR)

        os.makedirs(CACHE_DIR, exist_ok=True)

        messagebox.showinfo(
            "Turbo Cache",
            "Turbo Cache تمسح ✅"
        )

        log("Turbo Cache cleared.")

    except Exception as exc:
        messagebox.showerror(
            "Turbo Cache",
            str(exc)
        )


def download_with_repair(
    url,
    quality,
    mode="full",
    start="",
    end="",
    output_prefix="",
    progress_callback=None,
    stats_callback=None,
    job_label="",
    media_format="MP4",
    output_name=None,
    referer=None
):
    # V32.24:
    # PART mode no longer downloads the whole video first.
    # Smart Fast Part fetches only the requested range; an already-existing
    # old Turbo cache is still reused instantly if available.
    if mode == "part":
        return smart_fast_part_download(
            url=url,
            quality=quality,
            start=start,
            end=end,
            output_prefix=output_prefix,
            progress_callback=progress_callback,
            stats_callback=stats_callback,
            job_label=job_label,
            media_format=media_format,
        )

    # --------------------------------------------------------
    # TRY 1: FAST extractor path
    # --------------------------------------------------------
    code, saw_403, stopped, saw_format_problem = run_download_once(
        url=url,
        quality=quality,
        mode=mode,
        start=start,
        end=end,
        output_prefix=output_prefix,
        progress_callback=progress_callback,
        stats_callback=stats_callback,
        job_label=job_label,
        fast_extract=True,
        media_format=media_format,
        output_name=output_name,
        referer=referer,
    )

    if stopped:
        return code, "stopped"

    # Some videos need HLS/DASH manifests. If FAST mode skipped
    # something necessary, retry immediately with normal extraction.
    if (
        code != 0
        and saw_format_problem
        and not should_stop_current_job()
    ):
        prefix = f"[{job_label}] " if job_label else ""
        log(prefix + "FAST path had no suitable format -> normal fallback...")

        code, saw_403, stopped, _ = run_download_once(
            url=url,
            quality=quality,
            mode=mode,
            start=start,
            end=end,
            output_prefix=output_prefix,
            progress_callback=progress_callback,
            stats_callback=stats_callback,
            job_label=job_label,
            fast_extract=False,
            media_format=media_format,
            output_name=output_name,
            referer=referer,
        )

        if stopped:
            return code, "stopped"

    # --------------------------------------------------------
    # V32.42 SMART RECOVERY
    # --------------------------------------------------------
    profile = _get_download_error_profile()
    needs_engine_repair = bool(
        code != 0
        and (
            saw_403
            or profile.get("saw_403")
            or profile.get("saw_pot_problem")
            or profile.get("saw_auth_problem")
        )
    )

    if needs_engine_repair and not should_stop_current_job():
        reasons = []
        if saw_403 or profile.get("saw_403"):
            reasons.append("HTTP 403")
        if profile.get("saw_pot_problem"):
            reasons.append("PO Token/provider")
        if profile.get("saw_auth_problem"):
            reasons.append("YouTube authentication/bot check")
        reason = ", ".join(reasons) or "YouTube access failure"

        auto_repair(reason=reason)

        if should_stop_current_job():
            return 130, "stopped"

        prefix = f"[{job_label}] " if job_label else ""
        log(prefix + "Smart Recovery: retrying with normal extraction...")

        code, saw_403, stopped, saw_format_problem = run_download_once(
            url=url,
            quality=quality,
            mode=mode,
            start=start,
            end=end,
            output_prefix=output_prefix,
            progress_callback=progress_callback,
            stats_callback=stats_callback,
            job_label=job_label,
            fast_extract=False,
            media_format=media_format,
            output_name=output_name,
            referer=referer,
        )

        if stopped:
            return code, "stopped"

        profile = _get_download_error_profile()

    # Last-resort format recovery. This deliberately does NOT run on HTTP 429
    # because repeated requests would make rate limiting worse.
    if (
        code != 0
        and str(media_format or "MP4").upper() == "MP4"
        and not profile.get("saw_rate_limit")
        and (saw_format_problem or profile.get("saw_format_problem"))
        and not should_stop_current_job()
    ):
        prefix = f"[{job_label}] " if job_label else ""
        log(prefix + "Smart Recovery: widening format selection...")
        code, _, stopped, _ = run_download_once(
            url=url,
            quality=quality,
            mode=mode,
            start=start,
            end=end,
            output_prefix=output_prefix,
            progress_callback=progress_callback,
            stats_callback=stats_callback,
            job_label=job_label,
            fast_extract=False,
            media_format=media_format,
            output_name=output_name,
            referer=referer,
            broad_format=True,
        )
        if stopped:
            return code, "stopped"

    if should_stop_current_job():
        return 130, "stopped"

    return code, ("done" if code == 0 else "error")


# ============================================================
# SINGLE DOWNLOAD
# ============================================================

def set_single_part_state():
    state = (
        "normal"
        if single_mode_var.get() == "part"
        else "disabled"
    )
    single_start_entry.configure(state=state)
    single_end_entry.configure(state=state)


def start_single():
    global single_running

    if single_running:
        messagebox.showinfo(
            "Download",
            "هاد Single download راه خدام دابا."
        )
        return

    if update_in_progress:
        messagebox.showinfo(
            "Update",
            "yt-dlp كيدير update دابا. تسنى شوية."
        )
        return

    url = single_url_var.get().strip()
    if not url:
        messagebox.showwarning("URL", "دخل رابط الفيديو.")
        return

    mode = single_mode_var.get()
    start = single_start_var.get().strip()
    end = single_end_var.get().strip()

    if mode == "part" and (not start or not end):
        messagebox.showwarning(
            "Time",
            "دخل وقت البداية والنهاية."
        )
        return

    if mode == "part":
        duration = timecode_to_seconds(end) - timecode_to_seconds(start)

        if duration <= 0:
            messagebox.showwarning(
                "Time",
                "وقت النهاية خاصو يكون من بعد وقت البداية."
            )
            return

    if not os.path.exists(YTDLP) or not os.path.exists(FFMPEG):
        messagebox.showerror(
            "Files",
            "تأكد من yt-dlp.exe و ffmpeg.exe فالدوسي الرئيسي."
        )
        return

    if not downloads_are_running():
        stop_all_event.clear()
        _reset_pause_state_for_new_session()

    _set_live_worker_limit()

    single_running = True
    single_progress_var.set(0)
    single_stats_var.set("")
    single_download_button.configure(state="disabled")
    status_var.set("جاري تحميل الفيديو...")

    # V32.2: full window gives way to the compact IDM-like progress panel.
    root.after(80, mini_panel_begin)

    threading.Thread(
        target=single_worker,
        args=(
            url,
            single_quality_var.get(),
            mode,
            start,
            end,
        ),
        daemon=True,
    ).start()


def single_worker(url, quality, mode, start, end):
    global single_running

    live_slot_acquired = False

    try:
        live_slot_acquired = _acquire_live_slot()

        if not live_slot_acquired:
            return

        ensure_pot_fast()

        log("")
        log("=" * 60)
        log("SINGLE DOWNLOAD")
        log(url)

        if mode == "part":
            log(
                "PART MODE: YOUTUBE SMART PART engine active ⚡"
            )

        code, result = download_with_repair(
            url=url,
            quality=quality,
            mode=mode,
            start=start,
            end=end,
            progress_callback=set_single_progress,
            stats_callback=single_stats_callback,
        )

        if result == "done":
            set_single_progress(100)
            set_status("تم التحميل ✅")
            tray_set_title("Ready")
            tray_notify("التحميل سالا بنجاح ✅")
            log("✅ Single download completed.")
        elif result == "stopped":
            set_status("تم إيقاف التحميل")
            tray_set_title("Stopped")
            log("⛔ Single download stopped.")
        else:
            set_status("فشل التحميل ❌")
            tray_set_title("Download failed")
            tray_notify("التحميل فشل ❌")
            log(f"❌ Single download failed. Code: {code}")

        log("=" * 60)

    finally:
        if live_slot_acquired:
            _release_live_slot()

        single_running = False
        gui_call(
            single_download_button.configure,
            state="normal",
        )

        try:
            with browser_queue_condition:
                browser_queue_condition.notify_all()
        except Exception:
            pass


# ============================================================
# BULK EDITOR / PARSER
# ============================================================

TIME_PATTERN = r"\d{1,2}[.:]\d{2}(?:[.:]\d{2})?"

BULK_LINE_RE = re.compile(
    rf"^(https?://\S+)"
    rf"(?:\s+({TIME_PATTERN})\s*-\s*({TIME_PATTERN}))?"
    rf"\s*$",
    re.IGNORECASE
)


def normalize_time_text(value):
    return str(value or "").strip().replace(".", ":")


def parse_bulk_text(text):
    """
    Backward compatible import:
      URL
      URL  00.05.00 - 00.10.00
    """
    jobs = []
    invalid = []

    for line_number, raw in enumerate(text.splitlines(), start=1):
        line = raw.strip()

        if not line or line.startswith("#"):
            continue

        match = BULK_LINE_RE.match(line)

        if not match:
            invalid.append((line_number, raw))
            continue

        url, start, end = match.groups()

        jobs.append(
            {
                "url": url,
                "start": start or "",
                "end": end or "",
            }
        )

    return jobs, invalid


def update_bulk_editor_scrollregion():
    try:
        bulk_editor_canvas.configure(
            scrollregion=bulk_editor_canvas.bbox("all")
        )
    except Exception:
        pass


def refresh_bulk_row_numbers():
    for index, row in enumerate(bulk_editor_rows, start=1):
        row["number_var"].set(str(index))

    update_bulk_editor_scrollregion()


def update_bulk_row_mode(row):
    start = normalize_time_text(row["start_var"].get())
    end = normalize_time_text(row["end_var"].get())

    if not start and not end:
        row["mode_var"].set("FULL")
    elif start and end:
        row["mode_var"].set("PART")
    else:
        row["mode_var"].set("TIME ?")


def remove_bulk_row(row):
    if bulk_running:
        return

    try:
        row["frame"].destroy()
    except Exception:
        pass

    try:
        bulk_editor_rows.remove(row)
    except ValueError:
        pass

    refresh_bulk_row_numbers()

    if not bulk_editor_rows:
        add_bulk_row()


def add_bulk_row(url="", start="", end="", media_format="MP4"):
    if bulk_running:
        return None

    row_frame = ttk.Frame(bulk_rows_frame, style="Panel.TFrame")
    row_frame.pack(fill="x", pady=2)

    number_var = tk.StringVar()
    url_var = tk.StringVar(value=str(url or "").strip())
    start_var = tk.StringVar(value=str(start or "").strip())
    end_var = tk.StringVar(value=str(end or "").strip())
    mode_var = tk.StringVar(value="FULL")
    format_var = tk.StringVar(value=str(media_format or "MP4").upper())

    ttk.Label(
        row_frame,
        textvariable=number_var,
        width=3,
        anchor="center",
        style="Panel.TLabel",
    ).grid(row=0, column=0, padx=(2, 4))

    url_entry = ttk.Entry(
        row_frame,
        textvariable=url_var,
        style="Field.TEntry",
    )
    url_entry.grid(
        row=0,
        column=1,
        sticky="ew",
        padx=(0, 6),
    )

    start_entry = ttk.Entry(
        row_frame,
        textvariable=start_var,
        width=11,
        style="Field.TEntry",
    )
    start_entry.grid(row=0, column=2, padx=4)

    end_entry = ttk.Entry(
        row_frame,
        textvariable=end_var,
        width=11,
        style="Field.TEntry",
    )
    end_entry.grid(row=0, column=3, padx=4)

    ttk.Label(
        row_frame,
        textvariable=mode_var,
        width=8,
        anchor="center",
        style="Panel.TLabel",
    ).grid(row=0, column=4, padx=5)

    format_box = ttk.Combobox(
        row_frame,
        textvariable=format_var,
        values=["MP4", "MP3"],
        state="readonly",
        width=7,
        style="Field.TCombobox",
    )
    format_box.grid(row=0, column=5, padx=4)

    row = {
        "frame": row_frame,
        "number_var": number_var,
        "url_var": url_var,
        "start_var": start_var,
        "end_var": end_var,
        "mode_var": mode_var,
        "format_var": format_var,
        "url_entry": url_entry,
        "start_entry": start_entry,
        "end_entry": end_entry,
    }

    remove_button = ttk.Button(
        row_frame,
        text="✕",
        width=3,
        command=lambda r=row: remove_bulk_row(r),
        style="Remove.TButton",
    )
    remove_button.grid(row=0, column=6, padx=(4, 2))

    row_frame.columnconfigure(1, weight=1)

    bulk_editor_rows.append(row)

    start_var.trace_add(
        "write",
        lambda *_args, r=row: update_bulk_row_mode(r)
    )
    end_var.trace_add(
        "write",
        lambda *_args, r=row: update_bulk_row_mode(r)
    )

    update_bulk_row_mode(row)
    refresh_bulk_row_numbers()

    return row


def clear_bulk_editor_rows():
    for row in list(bulk_editor_rows):
        try:
            row["frame"].destroy()
        except Exception:
            pass

    bulk_editor_rows.clear()


def import_bulk_text(content, replace_existing=False):
    jobs, invalid = parse_bulk_text(content)

    if not jobs:
        messagebox.showwarning(
            "Links",
            "ما لقيت حتى رابط صالح."
        )
        return

    if replace_existing:
        clear_bulk_editor_rows()
    else:
        # Remove the default totally-empty first row.
        if (
            len(bulk_editor_rows) == 1
            and not bulk_editor_rows[0]["url_var"].get().strip()
            and not bulk_editor_rows[0]["start_var"].get().strip()
            and not bulk_editor_rows[0]["end_var"].get().strip()
        ):
            remove_bulk_row(bulk_editor_rows[0])
            if (
                len(bulk_editor_rows) == 1
                and not bulk_editor_rows[0]["url_var"].get().strip()
            ):
                clear_bulk_editor_rows()

    for job in jobs:
        add_bulk_row(
            url=job["url"],
            start=job["start"],
            end=job["end"],
            media_format="MP4",
        )

    if invalid:
        bad_lines = ", ".join(str(item[0]) for item in invalid[:12])
        log(f"⚠ أسطر ما تفهموش: {bad_lines}")

    refresh_bulk_row_numbers()


def paste_bulk_links():
    if bulk_running:
        return

    try:
        content = root.clipboard_get()
    except Exception:
        messagebox.showwarning(
            "Clipboard",
            "ما لقيت والو فالـClipboard."
        )
        return

    import_bulk_text(content, replace_existing=False)


def load_liens_txt():
    if bulk_running:
        return

    path = filedialog.askopenfilename(
        title=tr("Import link list"),
        initialdir=(BASE_DIR if os.path.isdir(BASE_DIR) else APP_DIR),
        filetypes=[(f"{tr('Text files')} (*.txt)", "*.txt"), (tr("All files"), "*.*")],
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


def remove_selected_bulk_rows():
    if bulk_running:
        return

    selected = [
        row for row in bulk_editor_rows
        if row["selected_var"].get()
    ]

    if not selected:
        return

    for row in selected:
        try:
            row["frame"].destroy()
        except Exception:
            pass

        try:
            bulk_editor_rows.remove(row)
        except ValueError:
            pass

    if not bulk_editor_rows:
        add_bulk_row()

    refresh_bulk_row_numbers()


def apply_same_time_to_all():
    if bulk_running:
        return

    start = bulk_same_from_var.get().strip()
    end = bulk_same_to_var.get().strip()

    if not start and not end:
        # Empty = turn all rows into FULL mode.
        for row in bulk_editor_rows:
            row["start_var"].set("")
            row["end_var"].set("")
        return

    if not start or not end:
        messagebox.showwarning(
            "Time",
            "دخل From و To بجوج."
        )
        return

    start_seconds = timecode_to_seconds(start)
    end_seconds = timecode_to_seconds(end)

    if end_seconds <= start_seconds:
        messagebox.showwarning(
            "Time",
            "وقت To خاصو يكون من بعد From."
        )
        return

    for row in bulk_editor_rows:
        if row["url_var"].get().strip():
            row["start_var"].set(start)
            row["end_var"].set(end)



# ============================================================
# V32.1 — IDM-LIKE PERSISTENT DOWNLOAD HISTORY
# ============================================================

_history_save_after_id = None


def _history_row_values(item_id):
    """Return a JSON-safe copy of one visible Downloads row."""
    try:
        values = list(bulk_tree.item(item_id, "values"))
    except Exception:
        return None

    if not values:
        return None

    # Keep the schema fixed even if an old row is shorter.
    while len(values) < 9:
        values.append("")

    return [str(value) for value in values[:9]]


def save_download_history():
    """
    Persist the visible Downloads table exactly like a download manager.
    Atomic replace protects the history file from a half-written JSON file.
    """
    global _history_save_after_id

    _history_save_after_id = None

    try:
        rows = []

        for item_id in bulk_tree.get_children():
            values = _history_row_values(item_id)

            if values:
                rows.append(
                    {
                        "values": values,
                        "file_path": row_file_paths.get(
                            item_id,
                            "",
                        ),
                    }
                )

        payload = {
            "version": 2,
            "saved_at": datetime.now().isoformat(timespec="seconds"),
            "rows": rows,
        }

        temp_path = DOWNLOAD_HISTORY_FILE + ".tmp"

        with open(
            temp_path,
            "w",
            encoding="utf-8",
        ) as file:
            json.dump(
                payload,
                file,
                ensure_ascii=False,
                indent=2,
            )

        os.replace(
            temp_path,
            DOWNLOAD_HISTORY_FILE,
        )

    except Exception as exc:
        log(f"History save warning: {exc}")


def schedule_download_history_save(delay_ms=350):
    """
    Progress callbacks can fire many times per second.
    Debounce disk writes so history stays current without slowing downloads.
    """
    global _history_save_after_id

    try:
        if _history_save_after_id is not None:
            root.after_cancel(_history_save_after_id)
    except Exception:
        pass

    try:
        _history_save_after_id = root.after(
            delay_ms,
            save_download_history,
        )
    except Exception:
        pass


def _tree_set_and_save(item_id, field, value):
    try:
        bulk_tree.set(
            item_id,
            field,
            value,
        )
        schedule_download_history_save()
    except Exception:
        pass


def max_download_display_number():
    highest = 0

    try:
        for item_id in bulk_tree.get_children():
            values = bulk_tree.item(
                item_id,
                "values",
            )

            if not values:
                continue

            try:
                highest = max(
                    highest,
                    int(values[0]),
                )
            except Exception:
                pass

    except Exception:
        pass

    return highest


def _restored_status(status):
    raw = str(status or "").strip()
    canonical = canonical_status(raw)
    if canonical in {"Downloading", "Waiting", "Analyzing…"}:
        return tr("Interrupted")
    if not raw:
        return tr("Saved")
    return tr_dynamic(raw)


def load_download_history():
    """Restore the Downloads table from the previous app/PC session."""
    global browser_job_counter

    if not os.path.isfile(DOWNLOAD_HISTORY_FILE):
        return

    try:
        with open(
            DOWNLOAD_HISTORY_FILE,
            "r",
            encoding="utf-8",
        ) as file:
            payload = json.load(file)

        rows = payload.get(
            "rows",
            [],
        )

        if not isinstance(rows, list):
            return

        restored = 0

        for row in rows:
            file_path = ""

            # V32.21 schema.
            if isinstance(row, dict):
                raw_values = row.get(
                    "values",
                    [],
                )
                file_path = str(
                    row.get(
                        "file_path",
                        "",
                    )
                    or ""
                )

            # Backward compatibility with V32.1–V32.20.
            elif isinstance(row, (list, tuple)):
                raw_values = row

            else:
                continue

            values = [
                str(value)
                for value in raw_values[:9]
            ]

            while len(values) < 9:
                values.append("")

            # Speed / ETA are session-only values.
            values[5] = ""
            values[6] = ""
            values[8] = _restored_status(
                values[8]
            )

            restored_item = bulk_tree.insert(
                "",
                "end",
                values=tuple(values),
            )

            if file_path:
                row_file_paths[
                    restored_item
                ] = _normalize_output_path(
                    file_path
                )

            restored_tag = _status_tag_for_value(
                values[8]
            )

            if restored_tag:
                try:
                    bulk_tree.item(
                        restored_item,
                        tags=(restored_tag,),
                    )
                except Exception:
                    pass

            restored += 1

        browser_job_counter = max(
            browser_job_counter,
            max_download_display_number(),
        )

        if restored:
            log(
                f"📚 Restored {restored} download history row(s)."
            )

    except Exception as exc:
        log(f"History load warning: {exc}")



def clear_download_list():
    if downloads_are_running():
        messagebox.showinfo(
            "Downloads",
            "خلي التحميلات اللي خدامين يساليو قبل ما تمسح اللائحة."
        )
        return

    for item in bulk_tree.get_children():
        bulk_tree.delete(item)

    bulk_tree_ids.clear()
    bulk_job_progress.clear()
    row_file_paths.clear()
    job_output_paths.clear()

    with job_best_titles_lock:
        job_best_titles.clear()

    set_bulk_progress(0)
    set_bulk_counter("0 / 0")
    schedule_download_history_save(50)


def clear_bulk():
    """
    Clear only the NEW DOWNLOADS editor.
    Finished/history rows are intentionally kept until Clear List is used.
    """
    if bulk_running:
        return

    clear_bulk_editor_rows()
    add_bulk_row()


def collect_bulk_jobs():
    jobs = []
    errors = []

    for display_index, row in enumerate(bulk_editor_rows, start=1):
        url = row["url_var"].get().strip()
        start = row["start_var"].get().strip()
        end = row["end_var"].get().strip()
        media_format = row["format_var"].get().strip().upper() or "MP4"

        # Completely empty row = ignore it.
        if not url and not start and not end:
            continue

        if not url:
            errors.append(
                f"السطر {display_index}: الرابط خاوي"
            )
            continue

        if not re.match(r"^https?://", url, re.IGNORECASE):
            errors.append(
                f"السطر {display_index}: الرابط ماشي صالح"
            )
            continue

        if bool(start) != bool(end):
            errors.append(
                f"السطر {display_index}: خاص From و To بجوج"
            )
            continue

        mode = "full"

        if start and end:
            start_seconds = timecode_to_seconds(start)
            end_seconds = timecode_to_seconds(end)

            if end_seconds <= start_seconds:
                errors.append(
                    f"السطر {display_index}: To خاصو يكون من بعد From"
                )
                continue

            mode = "part"

        jobs.append(
            {
                "index": len(jobs) + 1,
                "row_number": display_index,
                "url": url,
                "mode": mode,
                "start": start,
                "end": end,
                "format": media_format,
            }
        )

    return jobs, errors


def _status_tag_for_value(status):
    value = canonical_status(status)
    if value in {"Done ✅", "Saved"}:
        return "done"
    if value == "Error":
        return "error"
    if value == "Paused":
        return "paused"
    if value in {"Stopped", "Interrupted"}:
        return "cancelled"
    if str(value or "").strip():
        return "active"
    return ""


def _set_tree_status_and_cleanup(item_id, status):
    """
    Terminal rows clear Transfer rate / Time left and receive a subtle
    status color. Active/paused rows are also visually distinguishable.
    """
    try:
        canonical = canonical_status(status)
        display_status = tr_dynamic(status)

        bulk_tree.set(
            item_id,
            "status",
            display_status,
        )

        tag = _status_tag_for_value(canonical)

        try:
            bulk_tree.item(
                item_id,
                tags=((tag,) if tag else ()),
            )
        except Exception:
            pass

        terminal = canonical in {
            "Done ✅",
            "Error",
            "Stopped",
            "Interrupted",
            "Saved",
        }

        if terminal:
            bulk_tree.set(item_id, "speed", "")
            bulk_tree.set(item_id, "eta", "")

        schedule_download_history_save()

    except Exception:
        pass


def update_tree_status(index, status):
    item_id = bulk_tree_ids.get(index)
    if item_id:
        gui_call(
            _set_tree_status_and_cleanup,
            item_id,
            tr_dynamic(status),
        )


def update_tree_field(index, field, value):
    item_id = bulk_tree_ids.get(index)
    if item_id:
        gui_call(
            _tree_set_and_save,
            item_id,
            field,
            value,
        )


def refresh_bulk_average_progress():
    # Only CURRENT jobs belong in the progress bar. Persistent history
    # may have row numbers 50, 100, ... and must not dilute the average.
    if not bulk_job_progress:
        set_bulk_progress(0)
        return

    values = [
        float(value)
        for value in bulk_job_progress.values()
    ]

    set_bulk_progress(
        sum(values) / len(values)
    )


def make_bulk_stats_callback(index):
    def callback(percent=None, speed=None, eta=None, size=None, title=None):
        if title:
            locked_title = remember_job_title(
                index,
                title,
            )

            if locked_title:
                update_tree_field(
                    index,
                    "title",
                    locked_title,
                )

        if percent is not None:
            percent = max(0.0, min(float(percent), 100.0))
            bulk_job_progress[index] = percent
            update_tree_field(index, "progress", f"{percent:.1f}%")
            refresh_bulk_average_progress()

        if speed:
            update_tree_field(index, "speed", speed)

        if eta:
            update_tree_field(index, "eta", eta)

        if size:
            update_tree_field(index, "size", size)

    return callback


def single_stats_callback(percent=None, speed=None, eta=None, size=None, title=None):
    parts = []

    if percent is not None:
        percent_value = max(0.0, min(float(percent), 100.0))
        set_single_progress(percent_value)
        parts.append(f"{percent_value:.1f}%")

        status_text = f"جاري التحميل... {percent_value:.1f}%"
        if speed:
            status_text += f" — {speed}"

        set_status(status_text)
        tray_set_title(f"{percent_value:.1f}% downloading")

    if speed:
        parts.append(speed)

    if eta:
        parts.append(f"ETA {eta}")

    if size:
        parts.append(size)

    if parts:
        gui_call(single_stats_var.set, "   |   ".join(parts))


# ============================================================
# BULK DOWNLOAD
# ============================================================

def start_bulk():
    """
    V32.30 LIVE QUEUE

    Pressing DOWNLOAD never rejects a new manual batch merely because another
    download is active. Every new FULL/PART row joins the same global queue.
    Parallel=N is the total number of simultaneous jobs across batches.
    """
    global bulk_running
    global bulk_done
    global bulk_total
    global manual_jobs_pending
    global manual_jobs_done
    global manual_jobs_total

    if update_in_progress:
        messagebox.showinfo(
            "Update",
            "yt-dlp كيدير update دابا. تسنى شوية."
        )
        return

    jobs, errors = collect_bulk_jobs()

    if errors:
        preview = "\n".join(
            errors[:10]
        )

        if len(errors) > 10:
            preview += (
                f"\n... و {len(errors) - 10} أخطاء خرين"
            )

        messagebox.showwarning(
            "Multiple URLs",
            preview,
        )
        return

    if not jobs:
        messagebox.showwarning(
            "Links",
            "زيد على الأقل رابط واحد.",
        )
        return

    try:
        workers = int(
            bulk_workers_var.get()
        )
    except Exception:
        workers = 4

    workers = _set_live_worker_limit(
        workers
    )

    # Starting a brand-new live session may clear an old Stop/Pause state.
    # Adding jobs to an already-running session MUST NOT disturb active jobs.
    if not downloads_are_running():
        stop_all_event.clear()
        _reset_pause_state_for_new_session()

        manual_jobs_done = 0
        manual_jobs_total = 0
        bulk_done = 0
        bulk_total = 0
        bulk_job_progress.clear()

    # Assign unique runtime IDs BEFORE inserting rows.
    queued_jobs = []

    for original in jobs:
        job = dict(
            original
        )
        job[
            "index"
        ] = _allocate_live_job_index()
        queued_jobs.append(
            job
        )

    manual_jobs_total += len(
        queued_jobs
    )
    manual_jobs_pending += len(
        queued_jobs
    )

    bulk_total = manual_jobs_total
    bulk_done = manual_jobs_done
    bulk_running = (
        manual_jobs_pending > 0
    )

    for job in queued_jobs:
        index = job[
            "index"
        ]

        part_text = (
            f"{job['start']} → {job['end']}"
            if job[
                "mode"
            ] == "part"
            else "FULL"
        )

        item_id = bulk_tree.insert(
            "",
            "end",
            values=(
                index,
                "Loading title...",
                job[
                    "format"
                ],
                part_text,
                "0.0%",
                "",
                "",
                "",
                tr("Waiting"),
            ),
        )

        bulk_tree_ids[
            index
        ] = item_id
        bulk_job_progress[
            index
        ] = 0.0

        create_job_progress_window(
            index
        )

    schedule_download_history_save(
        50
    )

    set_bulk_counter(
        f"{manual_jobs_done} / {manual_jobs_total}"
    )

    set_status(
        f"تزادو {len(queued_jobs)} للصف — "
        + _live_queue_status_text()
    )

    log("")
    log("=" * 60)
    log(
        f"LIVE QUEUE ADD: {len(queued_jobs)} manual job(s) • "
        f"Parallel={workers} • "
        f"pending={manual_jobs_pending}"
    )

    # One lightweight waiter thread per visible job. The universal slot gate
    # decides when each one may actually start.
    for job in queued_jobs:
        threading.Thread(
            target=manual_live_job_worker,
            args=(
                job,
                bulk_quality_var.get(),
            ),
            daemon=True,
        ).start()


def manual_live_job_worker(
    job,
    quality,
):
    global bulk_running
    global bulk_done
    global bulk_total
    global manual_jobs_pending
    global manual_jobs_done

    index = job[
        "index"
    ]
    label = f"{index:04d}"

    acquired = _acquire_live_slot(
        index=index,
        waiting_text=tr("Waiting"),
    )

    if not acquired:
        code = 130
        result = "stopped"

    else:
        job_runtime_context.index = index

        try:
            log(
                f"[{label}] LIVE WORKER START • "
                f"{job['mode'].upper()} • "
                f"{_live_queue_status_text()}"
            )

            output_prefix = (
                f"{index:04d} - "
            )

            stats_callback = make_bulk_stats_callback(
                index
            )

            code, result = download_with_repair(
                url=job[
                    "url"
                ],
                quality=quality,
                mode=job[
                    "mode"
                ],
                start=job[
                    "start"
                ],
                end=job[
                    "end"
                ],
                output_prefix=output_prefix,
                progress_callback=None,
                stats_callback=stats_callback,
                job_label=label,
                media_format=job[
                    "format"
                ],
            )

            if job_is_cancelled(
                index
            ):
                result = "stopped"
                code = 130

        except Exception as exc:
            code = 999
            result = "error"
            log(
                f"[{label}] LIVE WORKER ERROR: {exc}"
            )

        finally:
            try:
                job_runtime_context.index = None
            except Exception:
                pass

            _release_live_slot()

    if result == "done":
        bulk_job_progress[
            index
        ] = 100.0
        update_tree_field(
            index,
            "progress",
            "100.0%",
        )
        update_tree_field(
            index,
            "eta",
            "",
        )
        update_tree_status(
            index,
            "Done ✅",
        )

    elif result == "stopped":
        update_tree_status(
            index,
            "Stopped",
        )

    else:
        update_tree_status(
            index,
            f"Error ({code})",
        )

    _finish_job_runtime_state(
        index
    )

    with bulk_count_lock:
        manual_jobs_pending = max(
            0,
            manual_jobs_pending - 1,
        )
        manual_jobs_done += 1

        bulk_done = manual_jobs_done
        bulk_total = manual_jobs_total
        bulk_running = (
            manual_jobs_pending > 0
        )

        done = manual_jobs_done
        total = manual_jobs_total
        pending = manual_jobs_pending

    set_bulk_counter(
        f"{done} / {total}"
    )
    refresh_bulk_average_progress()

    if pending:
        set_status(
            f"تحميلات Live Queue: {done} / {total} — "
            + _live_queue_status_text()
        )
    else:
        set_status(
            f"Live Queue سالات ✅ {done} / {total}"
        )
        tray_set_title(
            "Ready"
        )
        tray_notify(
            f"التحميلات سالاو ✅ {done} / {total}"
        )

        log(
            f"✅ LIVE QUEUE FINISHED: {done}/{total}"
        )
        log(
            "=" * 60
        )

    try:
        with browser_queue_condition:
            browser_queue_condition.notify_all()
    except Exception:
        pass


def bulk_controller(jobs, quality, workers):
    global bulk_running

    ensure_pot_fast()

    log("")
    log("=" * 60)
    log(
        f"BULK START: {len(jobs)} link(s), "
        f"{workers} simultaneous"
    )

    job_queue = Queue()

    for job in jobs:
        job_queue.put(job)

    threads = []

    for worker_number in range(1, workers + 1):
        thread = threading.Thread(
            target=bulk_worker,
            args=(job_queue, quality, worker_number),
            daemon=True,
        )
        thread.start()
        threads.append(thread)

    for thread in threads:
        thread.join()

    bulk_running = False

    try:
        with browser_queue_condition:
            browser_queue_condition.notify_all()
    except Exception:
        pass

    gui_call(bulk_start_button.configure, state="normal")

    if stop_all_event.is_set():
        set_status(
            f"تم الإيقاف — كملو {bulk_done} / {bulk_total}"
        )
        tray_set_title("Bulk stopped")
        log(
            f"⛔ BULK STOPPED: {bulk_done}/{bulk_total}"
        )
    else:
        set_status(
            f"المجموعة سالات ✅ {bulk_done} / {bulk_total}"
        )
        tray_set_title("Ready")
        tray_notify(
            f"المجموعة سالات ✅ {bulk_done} / {bulk_total}"
        )
        log(
            f"✅ BULK FINISHED: {bulk_done}/{bulk_total}"
        )

    log("=" * 60)


def bulk_worker(job_queue, quality, worker_number):
    while not stop_all_event.is_set():
        try:
            job = job_queue.get_nowait()
        except Empty:
            return

        index = job["index"]
        label = f"{index:04d}"

        job_runtime_context.index = index

        update_tree_status(index, "Downloading")
        log(f"[{label}] Worker {worker_number} START")

        output_prefix = f"{index:04d} - "

        stats_callback = make_bulk_stats_callback(index)

        code, result = download_with_repair(
            url=job["url"],
            quality=quality,
            mode=job["mode"],
            start=job["start"],
            end=job["end"],
            output_prefix=output_prefix,
            progress_callback=None,
            stats_callback=stats_callback,
            job_label=label,
            media_format=job["format"],
        )

        if job_is_cancelled(index):
            result = "stopped"
            code = 130

        if result == "done":
            bulk_job_progress[index] = 100.0
            update_tree_field(index, "progress", "100.0%")
            update_tree_field(index, "eta", "")
            refresh_bulk_average_progress()
            update_tree_status(index, "Done ✅")
        elif result == "stopped":
            update_tree_status(index, "Stopped")
        else:
            update_tree_status(index, f"Error ({code})")

        _finish_job_runtime_state(index)

        try:
            job_runtime_context.index = None
        except Exception:
            pass

        mark_bulk_job_finished()
        job_queue.task_done()


def mark_bulk_job_finished():
    global bulk_done

    with bulk_count_lock:
        bulk_done += 1
        done = bulk_done
        total = bulk_total

    set_bulk_counter(f"{done} / {total}")
    refresh_bulk_average_progress()
    set_status(f"تحميل المجموعة: {done} / {total}")



# ============================================================
# BROWSER BRIDGE
# ============================================================

def is_allowed_browser_url(url):
    """
    V17 accepts normal public HTTP/HTTPS pages and direct media URLs.
    The local bridge itself is excluded.
    """
    try:
        parsed = urlparse(url)
        host = (parsed.hostname or "").lower()

        if parsed.scheme not in ("http", "https"):
            return False

        if not host:
            return False

        if host in ("127.0.0.1", "localhost", "::1"):
            return False

        return True

    except Exception:
        return False


def browser_friendly_title(page_url, page_title=""):
    """
    Stable human title for browser-triggered downloads.
    V32.21 first cleans empty pipe components / site decoration, then keeps
    Forja episode suffix support.
    """
    title = clean_video_title(
        page_title,
        page_url=page_url,
    )

    if _is_placeholder_video_title(title):
        title = clean_video_title("", page_url=page_url)

    try:
        parsed = urlparse(
            page_url
        )
        query = parse_qs(
            parsed.query
        )

        episode = ""

        for key in (
            "c2",
            "episode",
            "ep",
            "e",
        ):
            values = query.get(key)

            if values and values[0]:
                episode = str(
                    values[0]
                ).strip()
                break

        if (
            episode
            and episode.lower()
            not in title.lower()
        ):
            title = (
                f"{title} - {episode}"
            )

    except Exception:
        pass

    return clean_video_title(
        title,
        page_url=page_url,
    )


def is_generic_stream_title(value):
    value = str(value or "").strip().lower()

    if not value:
        return True

    generic = {
        "chunk",
        "chunks",
        "segment",
        "segments",
        "frag",
        "fragment",
        "playlist",
        "master",
        "manifest",
        "index",
        "stream",
        "video",
    }

    if value in generic:
        return True

    if re.fullmatch(r"(?:chunk|segment|frag(?:ment)?)[-_ ]?\d*", value):
        return True

    return False


def normalize_sniffed_media_url(media_url):
    """
    Some Forja responses are a proxy URL like:
      https://vod.forja.ma/snrt?url=https://vod.forja.ma//vod/.../playlist.m3u8

    yt-dlp sees /snrt as an extension-less generic direct file and cannot
    enumerate 1080p/720p variants. V27 unwraps the real .m3u8/.mpd first.
    """
    value = str(media_url or "").strip()

    if not value:
        return value

    try:
        parsed = urlparse(value)
        host = (parsed.hostname or "").lower()
        path = parsed.path.rstrip("/").lower()

        if host == "vod.forja.ma" and path.endswith("/snrt"):
            inner_values = parse_qs(parsed.query).get("url")

            if inner_values:
                inner = str(inner_values[0] or "").strip()

                if inner.startswith(("http://", "https://")):
                    # Clean accidental double slash in the path while
                    # preserving the scheme's //.
                    p = urlsplit(inner)
                    clean_path = re.sub(r"/{2,}", "/", p.path)
                    inner = urlunsplit(
                        (
                            p.scheme,
                            p.netloc,
                            clean_path,
                            p.query,
                            p.fragment,
                        )
                    )

                    return inner

    except Exception:
        pass

    return value


def is_direct_media_url(url):
    try:
        parsed = urlparse(str(url or "").strip())

        if parsed.scheme not in ("http", "https"):
            return False

        value = parsed.path.lower()

        return (
            value.endswith((
                ".mp4", ".webm", ".m4v", ".mov",
                ".m3u8", ".mpd", ".ts"
            ))
            or ".m3u8" in value
            or ".mpd" in value
        )

    except Exception:
        return False


def bring_app_to_front():
    try:
        root.deiconify()
        root.lift()
        root.focus_force()
        root.attributes("-topmost", True)
        root.after(
            350,
            lambda: root.attributes("-topmost", False)
        )
    except Exception:
        pass



def begin_browser_batch_if_needed():
    """
    V25:
    Keep previous browser rows visible. This matters for sites where
    extraction can fail immediately: three clicks must remain three rows.
    """
    global browser_queue_active
    global browser_job_counter
    global browser_jobs_total
    global browser_jobs_done
    global browser_jobs_pending
    global browser_active_jobs
    global bulk_total
    global bulk_done

    if browser_queue_active:
        return

    browser_queue_active = True

    try:
        visible_count = max_download_display_number()
    except Exception:
        visible_count = browser_job_counter

    browser_job_counter = max(browser_job_counter, visible_count)

    # Progress bar represents the CURRENT browser batch, not saved history.
    bulk_job_progress.clear()

    browser_jobs_total = 0
    browser_jobs_done = 0
    browser_jobs_pending = 0
    browser_active_jobs = 0

    bulk_done = 0

    stop_all_event.clear()
    _reset_pause_state_for_new_session()
    bulk_progress_var.set(0)
    bulk_counter_var.set("0 / 0")


def add_browser_job_row(page_url, quality, media_format, page_title=""):
    """
    Runs on Tk thread and returns a unique row/job index.
    """
    global browser_job_counter
    global browser_jobs_total
    global browser_jobs_pending
    global browser_worker_limit
    global bulk_total

    begin_browser_batch_if_needed()

    try:
        workers = int(bulk_workers_var.get())
    except Exception:
        workers = 4

    browser_worker_limit = max(1, min(workers, 8))
    _set_live_worker_limit(
        browser_worker_limit
    )

    index = _allocate_live_job_index()

    browser_jobs_total += 1
    browser_jobs_pending += 1

    # Keep callback compatibility with persistent row numbering.
    bulk_total = max(bulk_total, index)
    bulk_job_progress[index] = 0.0

    try:
        host = urlparse(page_url).hostname or "Browser video"
    except Exception:
        host = "Browser video"

    friendly_title = browser_friendly_title(
        page_url,
        page_title,
    )

    quality_text = (
        "BEST"
        if str(quality).lower() == "best"
        else str(quality)
    )

    item_id = bulk_tree.insert(
        "",
        "end",
        values=(
            index,
            (friendly_title if not _is_placeholder_video_title(friendly_title) else f"{tr('Analyzing…')}  {host}"),
            str(media_format).upper(),
            f"FULL • {quality_text}",
            "0.0%",
            "",
            "",
            "",
            tr("Waiting"),
        ),
    )

    bulk_tree_ids[index] = item_id

    if not _is_placeholder_video_title(
        friendly_title
    ):
        remember_job_title(
            index,
            friendly_title,
        )

    schedule_download_history_save(50)

    # V32.13: every browser download gets its own progress window.
    create_job_progress_window(index)

    bulk_counter_var.set(
        f"{browser_jobs_done} / {browser_jobs_total}"
    )

    return index


def update_browser_batch_status():
    set_bulk_counter(
        f"{browser_jobs_done} / {browser_jobs_total}"
    )
    refresh_bulk_average_progress()

    if browser_jobs_pending > 0:
        set_status(
            f"تحميلات المتصفح: "
            f"{browser_jobs_done} / {browser_jobs_total} — "
            f"{browser_active_jobs} خدامين"
        )


def browser_job_finished(index, result, code):
    global browser_queue_active
    global browser_jobs_done
    global browser_jobs_pending
    global browser_active_jobs

    if result == "done":
        bulk_job_progress[index] = 100.0
        update_tree_field(index, "progress", "100.0%")
        update_tree_field(index, "eta", "")
        update_tree_status(index, "Done ✅")

    elif result == "stopped":
        bulk_job_progress[index] = 100.0
        update_tree_status(index, "Stopped")

    else:
        bulk_job_progress[index] = 100.0
        update_tree_status(index, f"Error ({code})")

    with browser_queue_condition:
        browser_active_jobs = max(0, browser_active_jobs - 1)
        browser_jobs_pending = max(0, browser_jobs_pending - 1)
        browser_jobs_done += 1

        pending = browser_jobs_pending
        done = browser_jobs_done
        total = browser_jobs_total
        active = browser_active_jobs

        browser_queue_condition.notify_all()

    set_bulk_counter(f"{done} / {total}")
    refresh_bulk_average_progress()

    if pending == 0:
        browser_queue_active = False

        if stop_all_event.is_set():
            set_status(f"تم الإيقاف — {done} / {total}")
            tray_set_title("Stopped")
            log(f"⛔ BROWSER QUEUE STOPPED: {done}/{total}")
        else:
            set_status(f"تحميلات المتصفح سالاو ✅ {done} / {total}")
            tray_set_title("Ready")
            tray_notify(
                f"تحميلات المتصفح سالاو ✅ {done} / {total}",
                APP_NAME
            )
            log(f"✅ BROWSER QUEUE FINISHED: {done}/{total}")

    else:
        set_status(
            f"تحميلات المتصفح: {done} / {total} — {active} خدامين"
        )



# ============================================================
# V28 — REAL HLS ENGINE
# ============================================================

def is_hls_manifest_url(url):
    try:
        path = urlparse(str(url or "")).path.lower()
        return path.endswith(".m3u8") or ".m3u8" in path
    except Exception:
        return False


def _http_text(url, referer=None, timeout=15):
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/152.0.0.0 Safari/537.36"
        ),
        "Accept": "*/*",
    }

    if referer:
        headers["Referer"] = str(referer)

    request = urllib.request.Request(
        str(url),
        headers=headers,
    )

    with urllib.request.urlopen(
        request,
        timeout=timeout,
    ) as response:
        raw = response.read()

    return raw.decode("utf-8", errors="replace")


def _m3u8_attrs(value):
    """
    Parse:
      BANDWIDTH=1234,RESOLUTION=1920x1080,AUDIO="audio"
    """
    result = {}

    pattern = re.compile(
        r'([A-Z0-9-]+)=("(?:[^"\\]|\\.)*"|[^,]*)',
        re.IGNORECASE,
    )

    for match in pattern.finditer(str(value or "")):
        key = match.group(1).upper()
        item = match.group(2).strip()

        if len(item) >= 2 and item[0] == '"' and item[-1] == '"':
            item = item[1:-1]

        result[key] = item

    return result


def _hls_duration_from_text(manifest_text):
    total = 0.0

    for raw in str(manifest_text or "").splitlines():
        line = raw.strip()

        if not line.startswith("#EXTINF:"):
            continue

        try:
            value = line.split(":", 1)[1].split(",", 1)[0]
            total += float(value)
        except Exception:
            pass

    return total


def resolve_hls_source(master_url, quality, referer=None, job_label="", log_details=True):
    """
    Returns:
      {
        video_url,
        audio_url,
        height,
        duration,
        variants
      }

    If master_url is already a media playlist, video_url stays unchanged.
    """
    prefix = f"[{job_label}] " if job_label else ""

    master_text = _http_text(
        master_url,
        referer=referer,
    )

    if "#EXTM3U" not in master_text:
        raise RuntimeError(
            "The captured URL did not return an HLS manifest."
        )

    lines = [
        line.strip()
        for line in master_text.splitlines()
    ]

    # Audio groups from the master manifest.
    audio_groups = {}

    for line in lines:
        if not line.startswith("#EXT-X-MEDIA:"):
            continue

        attrs = _m3u8_attrs(
            line.split(":", 1)[1]
        )

        if attrs.get("TYPE", "").upper() != "AUDIO":
            continue

        group_id = attrs.get("GROUP-ID")
        uri = attrs.get("URI")

        if group_id and uri:
            item = {
                "url": urljoin(master_url, uri),
                "default": attrs.get("DEFAULT", "").upper() == "YES",
                "autoselect": attrs.get("AUTOSELECT", "").upper() == "YES",
                "name": attrs.get("NAME", ""),
            }

            audio_groups.setdefault(
                group_id,
                []
            ).append(item)

    # Variant video playlists.
    variants = []

    for number, line in enumerate(lines):
        if not line.startswith("#EXT-X-STREAM-INF:"):
            continue

        attrs = _m3u8_attrs(
            line.split(":", 1)[1]
        )

        uri = None

        for next_line in lines[number + 1:]:
            if not next_line:
                continue

            if next_line.startswith("#"):
                continue

            uri = next_line
            break

        if not uri:
            continue

        width = 0
        height = 0

        resolution = attrs.get("RESOLUTION", "")

        if "x" in resolution.lower():
            try:
                width_text, height_text = re.split(
                    r"[xX]",
                    resolution,
                    maxsplit=1,
                )
                width = int(width_text)
                height = int(height_text)
            except Exception:
                width = 0
                height = 0

        try:
            bandwidth = int(
                attrs.get("AVERAGE-BANDWIDTH")
                or attrs.get("BANDWIDTH")
                or 0
            )
        except Exception:
            bandwidth = 0

        variants.append(
            {
                "url": urljoin(master_url, uri),
                "width": width,
                "height": height,
                "bandwidth": bandwidth,
                "audio_group": attrs.get("AUDIO"),
            }
        )

    # Media playlist: no variants.
    if not variants:
        duration = _hls_duration_from_text(
            master_text
        )

        return {
            "video_url": master_url,
            "audio_url": None,
            "height": None,
            "bandwidth": 0,
            "duration": duration,
            "variants": [],
        }

    desired_height = None

    if str(quality).lower() != "best":
        match = re.search(
            r"(\d+)",
            str(quality),
        )

        if match:
            desired_height = int(
                match.group(1)
            )

    # Prefer known-resolution variants, then bandwidth.
    known = [
        item for item in variants
        if item["height"] > 0
    ]

    pool = known or variants

    if desired_height is None:
        selected = max(
            pool,
            key=lambda item: (
                item["height"],
                item["bandwidth"],
            ),
        )
    else:
        fitting = [
            item for item in pool
            if (
                item["height"] <= desired_height
                if item["height"] > 0
                else True
            )
        ]

        if fitting:
            selected = max(
                fitting,
                key=lambda item: (
                    item["height"],
                    item["bandwidth"],
                ),
            )
        else:
            # No resolution <= requested: take the smallest available
            # rather than failing or downloading only the playlist text.
            selected = min(
                pool,
                key=lambda item: (
                    item["height"]
                    if item["height"] > 0
                    else 99999,
                    item["bandwidth"],
                ),
            )

    selected_audio = None
    audio_group = selected.get(
        "audio_group"
    )

    if audio_group:
        candidates = audio_groups.get(
            audio_group,
            [],
        )

        if candidates:
            selected_audio = next(
                (
                    item for item in candidates
                    if item["default"]
                ),
                candidates[0],
            )["url"]

    # Fetch chosen child media playlist to get real duration.
    duration = 0.0

    try:
        child_text = _http_text(
            selected["url"],
            referer=referer,
        )
        duration = _hls_duration_from_text(
            child_text
        )
    except Exception:
        pass

    available = sorted(
        {
            item["height"]
            for item in variants
            if item["height"] > 0
        },
        reverse=True,
    )

    if log_details and available:
        log(
            prefix
            + "HLS qualities: "
            + ", ".join(
                f"{height}p"
                for height in available
            )
        )

    chosen_text = (
        f"{selected['height']}p"
        if selected["height"]
        else "adaptive"
    )

    if log_details:
        log(
            prefix
            + f"✅ HLS selected: {chosen_text}"
        )

    return {
        "video_url": selected["url"],
        "audio_url": selected_audio,
        "height": (
            selected["height"]
            or None
        ),
        "bandwidth": int(
            selected.get("bandwidth")
            or 0
        ),
        "duration": duration,
        "variants": variants,
    }



def resolve_hls_source_recursive(
    manifest_url,
    quality,
    referer=None,
    job_label="",
    log_details=True,
    max_depth=5,
):
    """
    Follow nested HLS master playlists until we reach a real media playlist.

    Some VOD platforms have:
      master -> 720p master -> media playlist -> segments
    V28 only resolved the first level.
    """
    current_url = str(manifest_url or "").strip()
    last_result = None
    inherited_bandwidth = 0

    for depth in range(max_depth):
        result = resolve_hls_source(
            current_url,
            quality,
            referer=referer,
            job_label=job_label,
            log_details=(
                log_details
                and depth == 0
            ),
        )

        last_result = result

        current_bandwidth = int(
            result.get("bandwidth")
            or 0
        )

        if current_bandwidth > 0:
            inherited_bandwidth = current_bandwidth

        # Real media playlist: EXTINF duration is now known.
        if float(result.get("duration") or 0.0) > 0:
            if not int(result.get("bandwidth") or 0):
                result["bandwidth"] = inherited_bandwidth

            result["resolved_manifest_url"] = current_url
            result["depth"] = depth + 1
            return result

        variants = result.get("variants") or []
        next_url = str(
            result.get("video_url")
            or ""
        ).strip()

        # No nested variant left to follow.
        if not variants or not next_url or next_url == current_url:
            if not int(result.get("bandwidth") or 0):
                result["bandwidth"] = inherited_bandwidth

            result["resolved_manifest_url"] = current_url
            result["depth"] = depth + 1
            return result

        if log_details:
            prefix = (
                f"[{job_label}] "
                if job_label
                else ""
            )
            log(
                prefix
                + "↳ Nested HLS level "
                + f"{depth + 2}: {next_url}"
            )

        current_url = next_url

    if last_result is None:
        raise RuntimeError(
            "Could not resolve HLS manifest."
        )

    if not int(last_result.get("bandwidth") or 0):
        last_result["bandwidth"] = inherited_bandwidth

    last_result["resolved_manifest_url"] = current_url
    last_result["depth"] = max_depth
    return last_result



def probe_remote_video_resolution(
    media_url,
    referer=None,
    timeout=12,
):
    """
    Verify the REAL decoded stream resolution with ffprobe.

    Manifest metadata can claim 1080p while the chosen child stream
    actually resolves to something much smaller. This check is the
    final authority.
    """
    if not FFPROBE or not media_url:
        return (0, 0)

    headers = (
        "User-Agent: Mozilla/5.0 "
        "(Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 "
        "(KHTML, like Gecko) "
        "Chrome/152.0.0.0 Safari/537.36\r\n"
    )

    if referer:
        headers += f"Referer: {referer}\r\n"

    command = [
        FFPROBE,
        "-v", "error",
        "-headers", headers,
        "-select_streams", "v:0",
        "-show_entries",
        "stream=width,height",
        "-of", "csv=s=x:p=0",
        str(media_url),
    ]

    try:
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            timeout=timeout,
            env=build_tool_env(),
            creationflags=(
                subprocess.CREATE_NO_WINDOW
                if os.name == "nt"
                else 0
            ),
        )

        if result.returncode != 0:
            return (0, 0)

        line = (result.stdout or "").strip().splitlines()

        if not line:
            return (0, 0)

        match = re.search(
            r"(\d+)\s*x\s*(\d+)",
            line[0],
            flags=re.IGNORECASE,
        )

        if not match:
            return (0, 0)

        return (
            int(match.group(1)),
            int(match.group(2)),
        )

    except Exception:
        return (0, 0)


def requested_quality_height(quality):
    if str(quality).strip().lower() == "best":
        return None

    match = re.search(
        r"(\d+)",
        str(quality),
    )

    if not match:
        return None

    return int(match.group(1))


def choose_best_hls_candidate(
    primary_url,
    media_candidates,
    quality,
    referer=None,
    expected_duration=0.0,
    job_label="",
):
    """
    V30:
    1. Resolve all recent HLS candidates.
    2. Keep candidates matching the real browser-video duration.
    3. FFprobe the selected child streams and choose by ACTUAL resolution,
       not only #EXT-X-STREAM-INF metadata.
    """
    prefix = (
        f"[{job_label}] "
        if job_label
        else ""
    )

    urls = []

    def add_candidate(value):
        normalized = normalize_sniffed_media_url(
            value
        )

        if (
            normalized
            and is_hls_manifest_url(normalized)
            and normalized not in urls
        ):
            urls.append(normalized)

    add_candidate(primary_url)

    for item in media_candidates or []:
        if isinstance(item, dict):
            add_candidate(item.get("url"))
            add_candidate(item.get("originalUrl"))
        else:
            add_candidate(item)

    urls = urls[:12]

    if not urls:
        return (
            normalize_sniffed_media_url(primary_url),
            None,
        )

    probed = []

    for number, candidate_url in enumerate(
        urls,
        start=1,
    ):
        try:
            resolved = resolve_hls_source_recursive(
                candidate_url,
                quality,
                referer=referer,
                job_label=job_label,
                log_details=False,
            )

            duration = float(
                resolved.get("duration")
                or 0.0
            )

            metadata_height = int(
                resolved.get("height")
                or 0
            )

            video_url = str(
                resolved.get("video_url")
                or candidate_url
            )

            log(
                prefix
                + f"HLS candidate {number}: "
                + (
                    seconds_to_eta(duration)
                    if duration > 0
                    else "duration unknown"
                )
                + (
                    f" • metadata {metadata_height}p"
                    if metadata_height
                    else ""
                )
            )

            probed.append(
                {
                    "number": number,
                    "url": candidate_url,
                    "resolved": resolved,
                    "video_url": video_url,
                    "duration": duration,
                    "metadata_height": metadata_height,
                    "actual_width": 0,
                    "actual_height": 0,
                }
            )

        except Exception as exc:
            log(
                prefix
                + f"HLS candidate {number} skipped: {exc}"
            )

    if not probed:
        return urls[0], None

    expected_duration = float(
        expected_duration
        or 0.0
    )

    if expected_duration > 5:
        meaningful = [
            item for item in probed
            if item["duration"] >= expected_duration * 0.45
        ]

        if not meaningful:
            meaningful = sorted(
                probed,
                key=lambda item: item["duration"],
                reverse=True,
            )[:6]
    else:
        meaningful = list(probed)

    # Prefer candidates closest to the real video duration and with
    # strongest advertised resolution. Probe a bounded number.
    meaningful.sort(
        key=lambda item: (
            (
                abs(item["duration"] - expected_duration)
                if expected_duration > 5
                else 0
            ),
            -item["metadata_height"],
            -item["duration"],
        )
    )

    # Probe unique child-stream URLs only.
    unique_streams = set()
    verified = []

    for item in meaningful:
        stream_url = item["video_url"]

        if stream_url in unique_streams:
            # Reuse previously verified result for duplicate stream.
            other = next(
                (
                    row for row in verified
                    if row["video_url"] == stream_url
                ),
                None,
            )

            if other:
                item["actual_width"] = other["actual_width"]
                item["actual_height"] = other["actual_height"]

            verified.append(item)
            continue

        unique_streams.add(stream_url)

        # Keep startup delay bounded.
        if len(unique_streams) <= 6:
            width, height = probe_remote_video_resolution(
                stream_url,
                referer=referer,
                timeout=12,
            )

            item["actual_width"] = width
            item["actual_height"] = height

            if height:
                log(
                    prefix
                    + f"🔎 Candidate {item['number']} actual stream: "
                    + f"{width}x{height}"
                )
            else:
                log(
                    prefix
                    + f"🔎 Candidate {item['number']} actual resolution: unknown"
                )

        verified.append(item)

    desired_height = requested_quality_height(
        quality
    )

    actual_known = [
        item for item in verified
        if item["actual_height"] > 0
    ]

    if actual_known:
        if desired_height is None:
            selected = max(
                actual_known,
                key=lambda item: (
                    item["actual_height"],
                    item["actual_width"],
                    item["duration"],
                ),
            )
        else:
            fitting = [
                item for item in actual_known
                if item["actual_height"] <= desired_height
            ]

            if fitting:
                selected = max(
                    fitting,
                    key=lambda item: (
                        item["actual_height"],
                        item["actual_width"],
                        item["duration"],
                    ),
                )
            else:
                # All actual streams are above requested resolution.
                selected = min(
                    actual_known,
                    key=lambda item: item["actual_height"],
                )
    else:
        # Last resort when remote probing is blocked.
        selected = min(
            meaningful,
            key=lambda item: (
                (
                    abs(item["duration"] - expected_duration)
                    if expected_duration > 5
                    else 0
                ),
                -item["metadata_height"],
            ),
        )

    if expected_duration > 5:
        log(
            prefix
            + "Browser video duration: "
            + seconds_to_eta(expected_duration)
        )

    selected_height = (
        selected["actual_height"]
        or selected["metadata_height"]
        or 0
    )

    log(
        prefix
        + "✅ VERIFIED HLS selected: "
        + (
            f"{selected_height}p"
            if selected_height
            else "resolution unknown"
        )
        + " • "
        + (
            seconds_to_eta(selected["duration"])
            if selected["duration"] > 0
            else "duration unknown"
        )
    )

    # Record verified height so the downloader/UI uses the real value.
    selected["resolved"]["verified_width"] = selected["actual_width"]
    selected["resolved"]["verified_height"] = selected["actual_height"]

    if selected["actual_height"]:
        selected["resolved"]["height"] = selected["actual_height"]

    return (
        selected["url"],
        selected["resolved"],
    )


def download_hls_with_ffmpeg(
    manifest_url,
    quality,
    media_format,
    output_name,
    referer=None,
    stats_callback=None,
    job_label="",
    selected_callback=None,
    resolved_source=None,
    expected_duration=0.0,
):
    """
    Download the ACTUAL HLS media segments with FFmpeg.

    This intentionally bypasses yt-dlp's generic-direct-file behavior
    that previously saved only a ~45 KiB .m3u8 text file.
    """
    prefix = (
        f"[{job_label}] "
        if job_label
        else ""
    )

    try:
        source = (
            resolved_source
            if resolved_source is not None
            else resolve_hls_source_recursive(
                manifest_url,
                quality,
                referer=referer,
                job_label=job_label,
                log_details=True,
            )
        )
    except Exception as exc:
        log(
            prefix
            + f"HLS manifest ERROR: {exc}"
        )
        return 1, "error"

    selected_height = source.get(
        "height"
    )

    if selected_callback:
        try:
            selected_callback(
                selected_height
            )
        except Exception:
            pass

    video_url = source["video_url"]
    audio_url = source.get(
        "audio_url"
    )

    verified_height = int(
        source.get("verified_height")
        or 0
    )
    verified_width = int(
        source.get("verified_width")
        or 0
    )

    if verified_height:
        log(
            prefix
            + f"🎯 FFmpeg input verified: "
            + f"{verified_width}x{verified_height}"
        )
    else:
        log(
            prefix
            + f"🎯 FFmpeg input manifest: {video_url}"
        )
    duration = float(
        source.get("duration")
        or 0.0
    )

    expected_duration = float(
        expected_duration
        or 0.0
    )

    if duration <= 0 and expected_duration > 0:
        duration = expected_duration

    source_bandwidth = int(
        source.get("bandwidth")
        or 0
    )

    # HLS BANDWIDTH/AVERAGE-BANDWIDTH is bits per second.
    # For external audio renditions, add a modest audio estimate so
    # the expected total does not finish too early.
    effective_bandwidth = source_bandwidth

    if audio_url and effective_bandwidth > 0:
        effective_bandwidth += 160000

    expected_total_bytes = 0.0

    if duration > 0 and effective_bandwidth > 0:
        expected_total_bytes = (
            duration
            * effective_bandwidth
            / 8.0
        )

        log(
            prefix
            + "Estimated final size: "
            + bytes_to_human(
                expected_total_bytes
            )
        )

    safe_name = windows_safe_name(
        output_name or "Video",
        max_length=145,
    )

    media_format = str(
        media_format or "MP4"
    ).upper()

    extension = (
        "mp3"
        if media_format == "MP3"
        else "mp4"
    )

    output_file = unique_output_path(
        os.path.join(
            DOWNLOADS,
            f"{safe_name}.{extension}",
        )
    )

    headers = (
        "User-Agent: Mozilla/5.0 "
        "(Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 "
        "(KHTML, like Gecko) "
        "Chrome/152.0.0.0 Safari/537.36\r\n"
    )

    if referer:
        headers += (
            f"Referer: {referer}\r\n"
        )

    command = [
        FFMPEG,
        "-y",
        "-headers", headers,
        "-i", video_url,
    ]

    if audio_url:
        command += [
            "-headers", headers,
            "-i", audio_url,
        ]

    if media_format == "MP3":
        # If an external audio group exists, use it directly.
        if audio_url:
            command += [
                "-map", "1:a:0?",
            ]
        else:
            command += [
                "-map", "0:a:0?",
            ]

        command += [
            "-vn",
            "-c:a", "libmp3lame",
            "-b:a", "320k",
        ]

    else:
        command += [
            "-map", "0:v:0?",
        ]

        if audio_url:
            command += [
                "-map", "1:a:0?",
            ]
        else:
            command += [
                "-map", "0:a:0?",
            ]

        command += [
            "-c", "copy",
            "-movflags", "+faststart",
            "-avoid_negative_ts", "make_zero",
        ]

    command += [
        "-progress", "pipe:1",
        "-nostats",
        "-loglevel", "error",
        output_file,
    ]

    process = None
    started_at = time.perf_counter()
    last_size = 0
    last_wall = started_at

    # FFmpeg/HLS streams can start with a large source timestamp.
    # Using out_time / duration directly can therefore jump instantly
    # to 99.9%. V31 measures only plausible timestamp DELTAS.
    out_time = 0.0
    last_raw_out_time = None
    media_elapsed = 0.0
    total_size = 0
    speed_factor = 0.0
    ignored_pts_jump_logged = False

    try:
        creationflags = (
            subprocess.CREATE_NO_WINDOW
            if os.name == "nt"
            else 0
        )

        process = subprocess.Popen(
            command,
            env=build_tool_env(),
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            encoding="utf-8",
            errors="replace",
            creationflags=creationflags,
        )

        register_process(process)

        if stats_callback:
            stats_callback(
                percent=0.0,
                speed="Starting…",
                eta=(
                    seconds_to_eta(duration)
                    if duration > 0
                    else None
                ),
                title=output_name,
            )

        for raw in process.stdout:
            if stop_all_event.is_set():
                try:
                    process.terminate()
                except Exception:
                    pass

                return 0, "stopped"

            line = raw.strip()

            if not line:
                continue

            if "=" not in line:
                log(
                    prefix
                    + line
                )
                continue

            key, value = line.split(
                "=",
                1,
            )

            key = key.strip()
            value = value.strip()

            if key == "out_time":
                out_time = timecode_to_seconds(
                    value
                )

            elif key == "total_size":
                try:
                    total_size = max(
                        0,
                        int(value),
                    )
                except Exception:
                    pass

            elif key == "speed":
                try:
                    speed_factor = float(
                        value.lower()
                        .replace("x", "")
                        .strip()
                    )
                except Exception:
                    pass

            elif key == "progress":
                now = time.perf_counter()
                wall_delta = max(
                    0.001,
                    now - last_wall,
                )
                byte_delta = max(
                    0,
                    total_size - last_size,
                )

                bps = byte_delta / wall_delta

                if bps >= 1024 * 1024:
                    speed_text = (
                        f"{bps / (1024 * 1024):.2f}MiB/s"
                    )
                elif bps >= 1024:
                    speed_text = (
                        f"{bps / 1024:.1f}KiB/s"
                    )
                else:
                    speed_text = (
                        f"{bps:.0f}B/s"
                    )

                # --------------------------------------------------
                # V32 DOWNLOAD PROGRESS
                # --------------------------------------------------
                # The most reliable value for this HLS workflow is how many
                # output bytes FFmpeg has actually written compared with the
                # size implied by the selected HLS bitrate and duration.
                #
                # This avoids both previous problems:
                #   V30 -> jumped immediately to 99.9%
                #   V31 -> stayed around 1% while hundreds of MiB arrived.
                percent = None
                eta = None

                if expected_total_bytes > 0:
                    byte_percent = (
                        float(total_size)
                        / float(expected_total_bytes)
                        * 100.0
                    )

                    if value == "end":
                        percent = 100.0
                    else:
                        percent = max(
                            0.0,
                            min(
                                byte_percent,
                                99.5,
                            ),
                        )

                    if bps > 0:
                        remaining_bytes = max(
                            0.0,
                            expected_total_bytes
                            - float(total_size),
                        )

                        eta = seconds_to_eta(
                            remaining_bytes
                            / bps
                        )

                elif duration > 0 and speed_factor > 0:
                    # Fallback when the HLS manifest has no bitrate.
                    wall_elapsed = max(
                        0.0,
                        now - started_at,
                    )

                    estimated_media_time = min(
                        duration,
                        wall_elapsed
                        * speed_factor,
                    )

                    if value == "end":
                        percent = 100.0
                    else:
                        percent = max(
                            0.0,
                            min(
                                estimated_media_time
                                / duration
                                * 100.0,
                                99.5,
                            ),
                        )

                    remaining = max(
                        0.0,
                        duration
                        - estimated_media_time,
                    )

                    eta = seconds_to_eta(
                        remaining
                        / speed_factor
                    )

                if stats_callback:
                    stats_callback(
                        percent=percent,
                        speed=speed_text,
                        eta=eta,
                        size=bytes_to_human(
                            total_size
                        ),
                        title=output_name,
                    )

                last_size = total_size
                last_wall = now

        code = process.wait()

        if stop_all_event.is_set():
            return code, "stopped"

        if code == 0 and os.path.isfile(
            output_file
        ):
            size = os.path.getsize(
                output_file
            )

            minimum_real_media = (
                256 * 1024
                if media_format == "MP3"
                else 512 * 1024
            )

            output_duration = 0.0
            output_width = 0
            output_height = 0

            try:
                probe = subprocess.run(
                    [
                        FFPROBE,
                        "-v", "error",
                        "-show_entries",
                        "format=duration:stream=width,height",
                        "-of",
                        "default=noprint_wrappers=1",
                        output_file,
                    ],
                    capture_output=True,
                    text=True,
                    timeout=15,
                    env=build_tool_env(),
                    creationflags=(
                        subprocess.CREATE_NO_WINDOW
                        if os.name == "nt"
                        else 0
                    ),
                )

                output_width = 0
                output_height = 0

                if probe.returncode == 0:
                    probe_text = probe.stdout or ""

                    duration_match = re.search(
                        r"duration=([0-9.]+)",
                        probe_text,
                    )
                    width_match = re.search(
                        r"width=(\d+)",
                        probe_text,
                    )
                    height_match = re.search(
                        r"height=(\d+)",
                        probe_text,
                    )

                    if duration_match:
                        output_duration = float(
                            duration_match.group(1)
                        )

                    if width_match:
                        output_width = int(
                            width_match.group(1)
                        )

                    if height_match:
                        output_height = int(
                            height_match.group(1)
                        )
            except Exception:
                output_width = 0
                output_height = 0

            expected_check = (
                expected_duration
                if expected_duration > 5
                else float(
                    source.get("duration")
                    or 0.0
                )
            )

            too_short = (
                expected_check > 30
                and output_duration > 0
                and output_duration
                < expected_check * 0.45
            )

            if (
                size < minimum_real_media
                or too_short
            ):
                reason = (
                    f"{bytes_to_human(size)}"
                )

                if output_duration > 0:
                    reason += (
                        " • "
                        + seconds_to_eta(
                            output_duration
                        )
                    )

                log(
                    prefix
                    + "❌ HLS output is incomplete/suspicious: "
                    + reason
                )

                try:
                    os.remove(
                        output_file
                    )
                except Exception:
                    pass

                return 998, "error"

            if output_duration > 0:
                log(
                    prefix
                    + "Final media duration: "
                    + seconds_to_eta(
                        output_duration
                    )
                )

            if output_height > 0:
                log(
                    prefix
                    + "✅ FINAL FILE RESOLUTION: "
                    + f"{output_width}x{output_height}"
                )

                if selected_callback:
                    try:
                        selected_callback(
                            output_height
                        )
                    except Exception:
                        pass

            if media_format == "MP4":
                ensure_tv_compatible_mp4(
                    output_file,
                    stats_callback=stats_callback,
                    job_label=job_label,
                )

                try:
                    size = os.path.getsize(
                        output_file
                    )
                except Exception:
                    pass

            if stats_callback:
                stats_callback(
                    percent=100.0,
                    speed="DONE",
                    eta="",
                    size=bytes_to_human(
                        size
                    ),
                    title=output_name,
                )

            register_current_job_output_path(
                output_file
            )

            log(
                prefix
                + "✅ Real HLS media downloaded: "
                + output_file
            )

            return 0, "done"

        log(
            prefix
            + f"FFmpeg HLS failed. Code: {code}"
        )

        return code, "error"

    except Exception as exc:
        log(
            prefix
            + f"FFmpeg HLS ERROR: {exc}"
        )
        return 999, "error"

    finally:
        if process is not None:
            unregister_process(
                process
            )



# ============================================================
# V32.6 — VERIFIED FINAL FILE RECONCILIATION
# ============================================================

_FINAL_MEDIA_EXTENSIONS = {
    ".mp4", ".mkv", ".webm", ".mov", ".m4v",
    ".mp3", ".m4a", ".aac", ".wav", ".flac", ".ogg", ".opus",
}


def _snapshot_finished_media_files():
    """
    Snapshot only final media files in the user's Downloads folder.
    Cache / .part / temporary files are ignored.
    """
    snapshot = {}

    try:
        for root_dir, dirs, files in os.walk(DOWNLOADS):
            dirs[:] = [
                directory
                for directory in dirs
                if directory != "_video_cache"
            ]

            for filename in files:
                extension = os.path.splitext(filename)[1].lower()

                if extension not in _FINAL_MEDIA_EXTENSIONS:
                    continue

                path = os.path.join(root_dir, filename)

                try:
                    stat = os.stat(path)
                except Exception:
                    continue

                snapshot[
                    os.path.normcase(os.path.abspath(path))
                ] = (
                    int(stat.st_size),
                    int(stat.st_mtime_ns),
                )

    except Exception:
        pass

    return snapshot


def _probe_final_media(path):
    """Return (duration_seconds, has_audio, has_video)."""
    if not FFPROBE or not os.path.isfile(path):
        return 0.0, False, False

    try:
        probe = subprocess.run(
            [
                FFPROBE,
                "-v", "error",
                "-show_entries",
                "format=duration:stream=codec_type",
                "-of", "json",
                path,
            ],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=18,
            env=build_tool_env(),
            creationflags=(
                subprocess.CREATE_NO_WINDOW
                if os.name == "nt"
                else 0
            ),
        )

        if probe.returncode != 0:
            return 0.0, False, False

        payload = json.loads(probe.stdout or "{}")

        try:
            duration = float(
                payload.get("format", {}).get("duration", 0)
                or 0
            )
        except Exception:
            duration = 0.0

        stream_types = {
            str(stream.get("codec_type", "")).lower()
            for stream in payload.get("streams", [])
        }

        return (
            duration,
            "audio" in stream_types,
            "video" in stream_types,
        )

    except Exception:
        return 0.0, False, False


def _filename_similarity_score(path, expected_title):
    expected = _safe_filename_key(expected_title)

    if not expected:
        return 0

    stem = _safe_filename_key(
        os.path.splitext(
            os.path.basename(path)
        )[0]
    )

    if not stem:
        return 0

    if stem == expected:
        return 100

    if expected in stem:
        return 85

    if stem in expected:
        return 75

    expected_words = {
        word
        for word in expected.split()
        if len(word) >= 2
    }
    stem_words = {
        word
        for word in stem.split()
        if len(word) >= 2
    }

    if not expected_words or not stem_words:
        return 0

    common = len(
        expected_words & stem_words
    )

    return common * 12


def _verify_new_finished_output(
    before_snapshot,
    expected_title="",
    media_format="MP4",
    expected_duration=0.0,
):
    """
    Return a verified final path, or None.

    Important safety rule:
    if several parallel downloads created files and there is no confident
    title match, we do NOT guess which file belongs to this row.
    """
    after = _snapshot_finished_media_files()
    candidates = []

    expected_duration = float(
        expected_duration or 0.0
    )

    for normalized_path, state in after.items():
        previous = before_snapshot.get(normalized_path)

        # File must be new or actually modified by this job.
        if previous is not None and previous == state:
            continue

        path = normalized_path
        size = int(state[0])

        minimum_size = (
            256 * 1024
            if str(media_format).upper() == "MP3"
            else 512 * 1024
        )

        if size < minimum_size:
            continue

        duration, has_audio, has_video = _probe_final_media(path)

        if duration < 2.0:
            continue

        if str(media_format).upper() == "MP3":
            if not has_audio:
                continue
        else:
            if not has_video:
                continue

        # If the browser knows the real video duration, reject short intros,
        # adverts and tiny manifests exactly like the HLS safeguards.
        if expected_duration >= 30.0:
            minimum_duration = max(
                8.0,
                expected_duration * 0.45,
            )

            if duration < minimum_duration:
                continue

        similarity = _filename_similarity_score(
            path,
            expected_title,
        )

        candidates.append(
            {
                "path": path,
                "size": size,
                "duration": duration,
                "similarity": similarity,
                "mtime": state[1],
            }
        )

    if not candidates:
        return None

    # Strong filename match wins.
    candidates.sort(
        key=lambda item: (
            item["similarity"],
            item["mtime"],
            item["size"],
        ),
        reverse=True,
    )

    best = candidates[0]

    if best["similarity"] >= 24:
        return best["path"]

    # With no useful title, accepting exactly one verified new media file is
    # safe. With 2+ parallel candidates we deliberately refuse to guess.
    if len(candidates) == 1:
        return best["path"]

    return None


def _human_file_size(byte_count):
    value = float(byte_count or 0)

    for unit in ("B", "KiB", "MiB", "GiB", "TiB"):
        if value < 1024.0 or unit == "TiB":
            if unit == "B":
                return f"{int(value)}B"
            return f"{value:.1f}{unit}"

        value /= 1024.0

    return ""


def browser_download_job_worker(job):
    global browser_active_jobs

    index = job["index"]
    job_runtime_context.index = index

    page_url = job["page_url"]
    media_url = job["media_url"]
    quality = job["quality"]
    media_format = job["media_format"]
    media_detected = bool(job.get("media_detected", False))
    page_title = str(job.get("page_title", "")).strip()
    media_candidates = list(
        job.get("media_candidates")
        or []
    )

    try:
        page_duration = float(
            job.get("page_duration")
            or 0.0
        )
    except Exception:
        page_duration = 0.0

    friendly_title = browser_friendly_title(
        page_url,
        page_title,
    )

    # V32.6: remember final media files before this job. If an engine later
    # returns code 1 after already writing a complete file, we can prove
    # success instead of falsely showing Error (1).
    output_snapshot_before = _snapshot_finished_media_files()

    # V32.30: browser/manual/single jobs all share ONE Parallel limit.
    _set_live_worker_limit(
        browser_worker_limit
    )

    acquired_live_slot = _acquire_live_slot(
        index=index,
        waiting_text=tr("Waiting"),
    )

    if not acquired_live_slot:
        browser_job_finished(
            index,
            "stopped",
            0,
        )
        return

    with browser_queue_condition:
        browser_active_jobs += 1

    update_browser_batch_status()

    base_stats_callback = make_bulk_stats_callback(index)

    def stats_callback(
        percent=None,
        speed=None,
        eta=None,
        size=None,
        title=None,
    ):
        # Direct stream URLs often call themselves "chunks", "manifest",
        # etc. Keep the real page title in the UI instead.
        display_title = (
            clean_video_title(
                title
            )
            if title
            else ""
        )

        if (
            display_title
            and not _is_placeholder_video_title(
                display_title
            )
            and not is_generic_stream_title(
                display_title
            )
        ):
            display_title = remember_job_title(
                index,
                display_title,
            )
        else:
            display_title = (
                best_job_title(
                    index
                )
                or (
                    friendly_title
                    if not _is_placeholder_video_title(
                        friendly_title
                    )
                    else ""
                )
            )

        base_stats_callback(
            percent=percent,
            speed=speed,
            eta=eta,
            size=size,
            title=display_title,
        )

    try:
        ensure_pot_fast()

        parsed = urlparse(page_url)
        host = parsed.hostname or "site"

        label = f"B{index:03d}"

        log("")
        log("-" * 60)
        log(
            f"[{label}] 🌍 BROWSER START: {host} | "
            f"{media_format} | {quality}"
        )
        log(f"[{label}] Page: {page_url}")

        normalized_media_url = normalize_sniffed_media_url(media_url)
        pre_resolved_hls = None

        if (
            normalized_media_url
            and is_hls_manifest_url(
                normalized_media_url
            )
        ):
            (
                normalized_media_url,
                pre_resolved_hls,
            ) = choose_best_hls_candidate(
                primary_url=normalized_media_url,
                media_candidates=media_candidates,
                quality=quality,
                referer=page_url,
                expected_duration=page_duration,
                job_label=label,
            )

        if media_url and (media_detected or is_direct_media_url(media_url)):
            log(f"[{label}] Network media fallback detected: {media_url}")

            if normalized_media_url != media_url:
                log(
                    f"[{label}] ✅ Unwrapped real manifest: "
                    f"{normalized_media_url}"
                )

        code, result = download_with_repair(
            url=page_url,
            quality=quality,
            mode="full",
            start="",
            end="",
            progress_callback=None,
            stats_callback=stats_callback,
            job_label=label,
            media_format=media_format,
        )

        # If page extraction fails, try a real media URL detected by
        # the extension (MP4/HLS/DASH).
        if (
            result == "error"
            and normalized_media_url
            and (
                media_detected
                or is_direct_media_url(media_url)
                or is_direct_media_url(normalized_media_url)
            )
            and normalized_media_url != page_url
            and not stop_all_event.is_set()
        ):
            log(
                f"[{label}] ⚡ Page extraction failed "
                f"-> trying detected media stream..."
            )

            bulk_job_progress[index] = 0.0
            update_tree_field(index, "progress", "0.0%")
            update_tree_field(index, "speed", "")
            update_tree_field(index, "eta", "")
            update_tree_field(index, "size", "")
            update_tree_status(index, "Stream fallback")

            if is_hls_manifest_url(normalized_media_url):
                log(
                    f"[{label}] 🎬 Real HLS engine -> downloading media segments..."
                )

                fallback_output_title = best_output_title(
                    index,
                    friendly_title,
                )

                code, result = download_hls_with_ffmpeg(
                    manifest_url=normalized_media_url,
                    quality=quality,
                    media_format=media_format,
                    output_name=fallback_output_title,
                    referer=page_url,
                    stats_callback=stats_callback,
                    job_label=label,
                    selected_callback=lambda height: (
                        update_tree_field(
                            index,
                            "part",
                            (
                                f"FULL • {height}p"
                                if height
                                else f"FULL • {quality}"
                            ),
                        )
                    ),
                    resolved_source=pre_resolved_hls,
                    expected_duration=page_duration,
                )
            else:
                fallback_output_title = best_output_title(
                    index,
                    friendly_title,
                )

                code, result = download_with_repair(
                    url=normalized_media_url,
                    quality=quality,
                    mode="full",
                    start="",
                    end="",
                    progress_callback=None,
                    stats_callback=stats_callback,
                    job_label=label,
                    media_format=media_format,
                    output_name=fallback_output_title,
                    referer=page_url,
                )

        # Some extractors can return a late code 1 even after the final,
        # playable media file has already been written. Verify the real output
        # before reporting an error to the user.
        if (
            result == "error"
            and not stop_all_event.is_set()
        ):
            verified_output = _verify_new_finished_output(
                before_snapshot=output_snapshot_before,
                expected_title=(
                    friendly_title
                    or page_title
                ),
                media_format=media_format,
                expected_duration=page_duration,
            )

            if verified_output:
                result = "done"
                code = 0

                register_job_output_path(
                    index,
                    verified_output,
                )

                verified_name = os.path.splitext(
                    os.path.basename(
                        verified_output
                    )
                )[0]

                try:
                    verified_size = os.path.getsize(
                        verified_output
                    )
                except Exception:
                    verified_size = 0

                if (
                    verified_name
                    and not _is_placeholder_video_title(
                        verified_name
                    )
                ):
                    locked_verified_title = remember_job_title(
                        index,
                        verified_name,
                    )

                    if locked_verified_title:
                        update_tree_field(
                            index,
                            "title",
                            locked_verified_title,
                        )

                if verified_size:
                    update_tree_field(
                        index,
                        "size",
                        _human_file_size(
                            verified_size
                        ),
                    )

                log(
                    f"[{label}] ✅ Engine returned a late error, "
                    f"but final media verified successfully: "
                    f"{verified_output}"
                )

        log(
            f"[{label}] Browser job finished: "
            f"{result} | code={code}"
        )
        log("-" * 60)

    except Exception as exc:
        code = 999
        result = "error"
        log(f"[B{index:03d}] Browser worker ERROR: {exc}")

    if job_is_cancelled(index):
        result = "stopped"
        code = 130

    final_locked_title = best_job_title(
        index
    )

    if final_locked_title:
        update_tree_field(
            index,
            "title",
            final_locked_title,
        )

    _finish_job_runtime_state(index)

    try:
        job_runtime_context.index = None
    except Exception:
        pass

    _release_live_slot()
    browser_job_finished(
        index,
        result,
        code,
    )


def queue_browser_download(page_url, media_url, quality, media_format, media_detected=False, page_title="", media_candidates=None, page_duration=0.0):
    """
    Runs on Tk thread. Add the click immediately to the table, then
    let a worker wait for a free simultaneous-download slot.
    """
    index = add_browser_job_row(
        page_url=page_url,
        quality=quality,
        media_format=media_format,
        page_title=page_title,
    )

    job = {
        "index": index,
        "page_url": page_url,
        "media_url": media_url,
        "quality": quality,
        "media_format": media_format,
        "media_detected": bool(media_detected),
        "page_title": str(page_title or "").strip(),
        "media_candidates": list(media_candidates or []),
        "page_duration": float(page_duration or 0.0),
    }

    update_tree_status(index, "Waiting")

    threading.Thread(
        target=browser_download_job_worker,
        args=(job,),
        daemon=True,
    ).start()

    set_status(
        f"تزادت للصف: {browser_jobs_total} تحميلات — "
        f"حتى {browser_worker_limit} مع بعض"
    )

def browser_request_received(payload):
    """
    Runs on the Tk main thread.
    action=start -> start full video immediately
    action=open  -> fill the app, show it, do not start
    """
    url = str(payload.get("url", "")).strip()
    media_url = str(payload.get("media_url", "")).strip()
    media_detected = bool(payload.get("media_detected", False))
    page_title = str(payload.get("page_title", "")).strip()

    raw_candidates = payload.get(
        "media_candidates",
        [],
    )

    media_candidates = (
        raw_candidates
        if isinstance(raw_candidates, list)
        else []
    )

    try:
        page_duration = float(
            payload.get("page_duration", 0)
            or 0
        )
    except Exception:
        page_duration = 0.0

    quality = str(payload.get("quality", "Best")).strip()
    media_format = str(payload.get("format", "MP4")).strip().upper()
    action = str(payload.get("action", "start")).strip().lower()

    if media_format not in ("MP4", "MP3"):
        media_format = "MP4"

    if quality not in ("Best", "1080p", "720p", "480p"):
        quality = "Best"

    if not is_allowed_browser_url(url):
        log("Browser Bridge rejected invalid URL.")
        return

    # --------------------------------------------------------
    # PART FROM BROWSER -> UNIFIED EDITOR ROW
    # --------------------------------------------------------
    if action in ("open", "part"):
        bulk_quality_var.set(quality)

        target_row = None

        # Reuse a completely empty row first.
        for row in bulk_editor_rows:
            if (
                not row["url_var"].get().strip()
                and not row["start_var"].get().strip()
                and not row["end_var"].get().strip()
            ):
                target_row = row
                break

        if target_row is None:
            target_row = add_bulk_row()

        # V32.25: PART editor keeps the stable page URL.
        # googlevideo/videoplayback links are signed and expire quickly.
        # Smart Part resolves a fresh direct stream only when Start is pressed.
        part_url = url

        if target_row is not None:
            target_row["url_var"].set(part_url)
            target_row["start_var"].set("")
            target_row["end_var"].set("")
            target_row["format_var"].set(media_format)
            update_bulk_row_mode(target_row)

        bring_app_to_front()
        status_var.set("Part of video جاهز — دخل From و To ✅")
        log(f"🌐 Browser -> Unified PART row: {url}")

        # Cursor goes straight to From.
        try:
            if target_row is not None:
                target_row["start_entry"].focus_set()
                target_row["start_entry"].icursor("end")
        except Exception:
            pass

        return

    # --------------------------------------------------------
    # FULL FROM BROWSER -> REAL QUEUE
    # --------------------------------------------------------
    if update_in_progress:
        status_var.set("Browser request waiting for yt-dlp update...")
        root.after(
            500,
            lambda: browser_request_received(payload)
        )
        return

    # V20: do NOT reject the second/third/fourth click.
    # Every browser click becomes a visible queued download.
    queue_browser_download(
        page_url=url,
        media_url=media_url,
        quality=quality,
        media_format=media_format,
        media_detected=media_detected,
        page_title=page_title,
        media_candidates=media_candidates,
        page_duration=page_duration,
    )





class BrowserBridgeHandler(BaseHTTPRequestHandler):

    server_version = "Z2SEBridge/1.0"

    def log_message(self, format, *args):
        # Keep the console clean.
        return

    def _cors_headers(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header(
            "Access-Control-Allow-Headers",
            "Content-Type"
        )
        self.send_header(
            "Access-Control-Allow-Methods",
            "GET, POST, OPTIONS"
        )

    def _send_json(self, code, data):
        body = json.dumps(
            data,
            ensure_ascii=False
        ).encode("utf-8")

        self.send_response(code)
        self._cors_headers()
        self.send_header(
            "Content-Type",
            "application/json; charset=utf-8"
        )
        self.send_header(
            "Content-Length",
            str(len(body))
        )
        self.end_headers()
        self.wfile.write(body)

    def do_OPTIONS(self):
        self.send_response(204)
        self._cors_headers()
        self.end_headers()

    def do_GET(self):
        path = self.path.rstrip("/")

        if path in ("", "/ping"):
            self._send_json(
                200,
                {
                    "ok": True,
                    "app": APP_NAME,
                    "bridge": "active",
                }
            )
            return

        if path == "/focus":
            gui_call(bring_app_to_front)

            self._send_json(
                200,
                {
                    "ok": True,
                    "focused": True,
                }
            )
            return

        self._send_json(
            404,
            {
                "ok": False,
                "error": "not_found"
            }
        )

    def do_POST(self):
        if self.path.rstrip("/") != "/download":
            self._send_json(
                404,
                {
                    "ok": False,
                    "error": "not_found"
                }
            )
            return

        try:
            length = int(
                self.headers.get(
                    "Content-Length",
                    "0"
                )
            )

            if length <= 0 or length > 65536:
                self._send_json(
                    400,
                    {
                        "ok": False,
                        "error": "bad_length"
                    }
                )
                return

            raw = self.rfile.read(length)
            payload = json.loads(
                raw.decode("utf-8")
            )

            url = str(
                payload.get("url", "")
            ).strip()

            if not is_allowed_browser_url(url):
                self._send_json(
                    400,
                    {
                        "ok": False,
                        "error": "invalid_media_page_url"
                    }
                )
                return

            gui_call(
                browser_request_received,
                payload
            )

            self._send_json(
                200,
                {
                    "ok": True,
                    "accepted": True
                }
            )

        except Exception as exc:
            self._send_json(
                500,
                {
                    "ok": False,
                    "error": str(exc)
                }
            )


def start_browser_bridge():
    global bridge_server

    try:
        bridge_server = ThreadingHTTPServer(
            (BRIDGE_HOST, BRIDGE_PORT),
            BrowserBridgeHandler
        )

        set_status("جاهز")
        gui_call(
            bridge_status_var.set,
            f"Universal Bridge: ACTIVE ✅  {BRIDGE_HOST}:{BRIDGE_PORT}"
        )
        log(
            f"🌍 Universal Browser Bridge ACTIVE: {BRIDGE_URL}"
        )

        bridge_server.serve_forever(
            poll_interval=0.5
        )

    except OSError as exc:
        gui_call(
            bridge_status_var.set,
            "Browser Bridge: PORT BUSY ❌"
        )
        log(
            f"Browser Bridge could not start: {exc}"
        )

    except Exception as exc:
        gui_call(
            bridge_status_var.set,
            "Browser Bridge: ERROR ❌"
        )
        log(
            f"Browser Bridge ERROR: {exc}"
        )


# ============================================================
# STARTUP CHECKS
# ============================================================

def startup_checks():
    log(f"Z²SE V{APP_VERSION} PRO DESIGN starting system checks...")
    log(
        f"FFmpeg: {'OK' if FFMPEG and os.path.isfile(FFMPEG) else 'MISSING'}"
    )
    log(
        f"FFmpeg path: {FFMPEG or 'NOT FOUND'}"
    )
    log(
        f"FFprobe: {'OK' if FFPROBE and os.path.isfile(FFPROBE) else 'MISSING'}"
    )
    log(
        f"FFprobe path: {FFPROBE or 'NOT FOUND'}"
    )
    check_and_start_pot()
    update_ytdlp(force=False)
    log("System ready.")
    log("FAST START ready: repeated pre-download PO checks disabled.")
    _show_last_app_update_result()



# V32.43 copy hierarchy overrides
TRANSLATIONS.update({'MEDIA DOWNLOADER': {'fr': 'TÉLÉCHARGEUR MULTIMÉDIA', 'en': 'MEDIA DOWNLOADER', 'ar': 'منزّل الوسائط', 'darija': 'تحميل الوسائط'}, 'File': {'fr': 'Fichier', 'en': 'File', 'ar': 'ملف', 'darija': 'ملف'}, 'Downloads': {'fr': 'Téléchargements', 'en': 'Downloads', 'ar': 'التنزيلات', 'darija': 'التحميلات'}, 'Tools': {'fr': 'Outils', 'en': 'Tools', 'ar': 'الأدوات', 'darija': 'الأدوات'}, 'Language': {'fr': 'Langue', 'en': 'Language', 'ar': 'اللغة', 'darija': 'اللغة'}, 'Help': {'fr': 'Aide', 'en': 'Help', 'ar': 'مساعدة', 'darija': 'مساعدة'}, '●  ENGINE READY': {'fr': '●  PRÊT', 'en': '●  READY', 'ar': '●  جاهز', 'darija': '●  واجد'}, '＋  Add Link': {'fr': '＋  Ajouter', 'en': '＋  Add', 'ar': '＋  إضافة', 'darija': '＋  زيد'}, 'Paste Links': {'fr': 'Coller', 'en': 'Paste', 'ar': 'لصق', 'darija': 'لسّق'}, '▶  Start': {'fr': '▶  Télécharger', 'en': '▶  Download', 'ar': '▶  تنزيل', 'darija': '▶  حمّل'}, '■  Stop All': {'fr': '■  Tout arrêter', 'en': '■  Stop all', 'ar': '■  إيقاف الكل', 'darija': '■  وقف الكل'}, 'Ⅱ  Pause': {'fr': 'Ⅱ  Pause', 'en': 'Ⅱ  Pause', 'ar': 'Ⅱ  إيقاف مؤقت', 'darija': 'Ⅱ  وقف مؤقت'}, '▶  Resume': {'fr': '▶  Reprendre', 'en': '▶  Resume', 'ar': '▶  استئناف', 'darija': '▶  كمّل'}, 'Open Folder': {'fr': 'Dossier', 'en': 'Folder', 'ar': 'المجلد', 'darija': 'الدوسي'}, 'Clear List': {'fr': 'Vider la liste', 'en': 'Clear list', 'ar': 'مسح القائمة', 'darija': 'خوي اللائحة'}, 'Clear Cache': {'fr': 'Vider le cache', 'en': 'Clear cache', 'ar': 'مسح الذاكرة المؤقتة', 'darija': 'خوي الكاش'}, 'NEW DOWNLOADS': {'fr': 'AJOUTER DES TÉLÉCHARGEMENTS', 'en': 'ADD DOWNLOADS', 'ar': 'إضافة تنزيلات', 'darija': 'زيد تحميلات'}, 'From / To empty = full video': {'fr': 'Début et fin vides : vidéo entière', 'en': 'Leave start and end empty for the full video', 'ar': 'اترك البداية والنهاية فارغتين لتنزيل الفيديو كاملاً', 'darija': 'خلي البداية والنهاية خاويين باش تحمل الفيديو كامل'}, 'From': {'fr': 'Début', 'en': 'Start', 'ar': 'البداية', 'darija': 'البداية'}, 'To': {'fr': 'Fin', 'en': 'End', 'ar': 'النهاية', 'darija': 'النهاية'}, 'Mode': {'fr': 'Mode', 'en': 'Mode', 'ar': 'الوضع', 'darija': 'الوضع'}, 'Format': {'fr': 'Format', 'en': 'Format', 'ar': 'الصيغة', 'darija': 'الفورما'}, '+ Add': {'fr': '+ Ajouter une ligne', 'en': '+ Add row', 'ar': '+ إضافة سطر', 'darija': '+ زيد سطر'}, 'Paste': {'fr': 'Coller des liens', 'en': 'Paste links', 'ar': 'لصق الروابط', 'darija': 'لسّق الروابط'}, 'Load File': {'fr': 'Importer un fichier', 'en': 'Import file', 'ar': 'استيراد ملف', 'darija': 'دخل ملف'}, 'Clear': {'fr': 'Effacer', 'en': 'Clear', 'ar': 'مسح', 'darija': 'مسح'}, 'Quality': {'fr': 'Qualité', 'en': 'Quality', 'ar': 'الجودة', 'darija': 'الجودة'}, 'Parallel': {'fr': 'Simultanés', 'en': 'Concurrent', 'ar': 'متزامنة', 'darija': 'فـ نفس الوقت'}, 'DOWNLOAD': {'fr': 'TÉLÉCHARGER', 'en': 'DOWNLOAD', 'ar': 'تنزيل', 'darija': 'حمّل'}, 'DOWNLOADS': {'fr': 'TÉLÉCHARGEMENTS', 'en': 'DOWNLOADS', 'ar': 'التنزيلات', 'darija': 'التحميلات'}, 'Deselect': {'fr': 'Tout désélectionner', 'en': 'Deselect all', 'ar': 'إلغاء تحديد الكل', 'darija': 'حيد الاختيار كامل'}, 'Select All': {'fr': 'Tout sélectionner', 'en': 'Select all', 'ar': 'تحديد الكل', 'darija': 'اختار الكل'}, 'File / Video': {'fr': 'Fichier', 'en': 'File', 'ar': 'الملف', 'darija': 'الملف'}, 'Type': {'fr': 'Type', 'en': 'Type', 'ar': 'النوع', 'darija': 'النوع'}, 'Progress': {'fr': 'Progression', 'en': 'Progress', 'ar': 'التقدم', 'darija': 'التقدم'}, 'Transfer rate': {'fr': 'Vitesse', 'en': 'Speed', 'ar': 'السرعة', 'darija': 'السرعة'}, 'Time left': {'fr': 'Restant', 'en': 'Remaining', 'ar': 'المتبقي', 'darija': 'الباقي'}, 'Size': {'fr': 'Taille', 'en': 'Size', 'ar': 'الحجم', 'darija': 'الحجم'}, 'Status': {'fr': 'État', 'en': 'Status', 'ar': 'الحالة', 'darija': 'الحالة'}, 'Add new row': {'fr': 'Ajouter une ligne', 'en': 'Add row', 'ar': 'إضافة سطر', 'darija': 'زيد سطر'}, 'Paste links': {'fr': 'Coller des liens', 'en': 'Paste links', 'ar': 'لصق الروابط', 'darija': 'لسّق الروابط'}, 'Load links file…': {'fr': 'Importer une liste…', 'en': 'Import link list…', 'ar': 'استيراد قائمة روابط…', 'darija': 'دخل لائحة ديال الروابط…'}, 'Open Downloads folder': {'fr': 'Ouvrir le dossier des téléchargements', 'en': 'Open Downloads folder', 'ar': 'فتح مجلد التنزيلات', 'darija': 'حل دوسي التحميلات'}, 'Open Z²SE app folder': {'fr': 'Ouvrir le dossier de Z²SE', 'en': 'Open Z²SE folder', 'ar': 'فتح مجلد Z²SE', 'darija': 'حل دوسي Z²SE'}, 'Hide main window to tray': {'fr': 'Réduire dans la zone de notification', 'en': 'Minimize to tray', 'ar': 'تصغير إلى منطقة الإشعارات', 'darija': 'صغّر حدا الساعة'}, 'Quit Z²SE': {'fr': 'Quitter Z²SE', 'en': 'Quit Z²SE', 'ar': 'إغلاق Z²SE', 'darija': 'سد Z²SE'}, 'Start downloads': {'fr': 'Démarrer les téléchargements', 'en': 'Start downloads', 'ar': 'بدء التنزيلات', 'darija': 'بدا التحميلات'}, 'Pause all': {'fr': 'Tout mettre en pause', 'en': 'Pause all', 'ar': 'إيقاف الكل مؤقتاً', 'darija': 'وقف الكل مؤقت'}, 'Resume all': {'fr': 'Tout reprendre', 'en': 'Resume all', 'ar': 'استئناف الكل', 'darija': 'كمّل الكل'}, 'Stop all': {'fr': 'Tout arrêter', 'en': 'Stop all', 'ar': 'إيقاف الكل', 'darija': 'وقف الكل'}, 'Select all': {'fr': 'Tout sélectionner', 'en': 'Select all', 'ar': 'تحديد الكل', 'darija': 'اختار الكل'}, 'Deselect all': {'fr': 'Tout désélectionner', 'en': 'Deselect all', 'ar': 'إلغاء تحديد الكل', 'darija': 'حيد الاختيار كامل'}, 'Delete selected…': {'fr': 'Supprimer la sélection…', 'en': 'Delete selected…', 'ar': 'حذف المحدد…', 'darija': 'مسح المختار…'}, 'Clear finished/history list': {'fr': 'Vider les éléments terminés', 'en': 'Clear finished items', 'ar': 'مسح العناصر المكتملة', 'darija': 'خوي اللي سالاو'}, 'Health Check': {'fr': 'Diagnostic système', 'en': 'System diagnostics', 'ar': 'تشخيص النظام', 'darija': 'تشخيص النظام'}, 'Check updates now': {'fr': 'Rechercher les mises à jour', 'en': 'Check for updates', 'ar': 'البحث عن تحديثات', 'darija': 'قلب على التحديثات'}, 'Update download engine': {'fr': 'Mettre à jour le moteur de téléchargement', 'en': 'Update download engine', 'ar': 'تحديث محرك التنزيل', 'darija': 'حدّث موتور التحميل'}, 'Clear Turbo cache': {'fr': 'Vider le cache Turbo', 'en': 'Clear Turbo cache', 'ar': 'مسح ذاكرة Turbo المؤقتة', 'darija': 'خوي كاش Turbo'}, 'Show / Hide technical log': {'fr': 'Afficher / masquer le journal technique', 'en': 'Show / hide technical log', 'ar': 'إظهار / إخفاء السجل التقني', 'darija': 'بيّن / خبي اللوغ التقني'}, 'Open Chrome Extensions': {'fr': 'Ouvrir les extensions Chrome', 'en': 'Open Chrome extensions', 'ar': 'فتح إضافات Chrome', 'darija': 'حل إضافات Chrome'}, 'Open stable V15 extension folder': {'fr': 'Ouvrir le dossier de l’extension V15', 'en': 'Open V15 extension folder', 'ar': 'فتح مجلد إضافة V15', 'darija': 'حل دوسي Extension V15'}, 'Keyboard shortcuts': {'fr': 'Raccourcis clavier', 'en': 'Keyboard shortcuts', 'ar': 'اختصارات لوحة المفاتيح', 'darija': 'اختصارات الكلافي'}, 'Chrome extension setup': {'fr': 'Configurer l’extension Chrome', 'en': 'Set up Chrome extension', 'ar': 'إعداد إضافة Chrome', 'darija': 'وجد Extension ديال Chrome'}, 'About Z²SE': {'fr': 'À propos de Z²SE', 'en': 'About Z²SE', 'ar': 'حول Z²SE', 'darija': 'على Z²SE'}})


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
    "fr": "Le fichier .txt contient un lien par ligne.\n\nVidéo entière :\nhttps://youtube.com/watch?v=AAAA\nhttps://youtu.be/BBBB\n\nAvec début / fin :\nhttps://youtube.com/watch?v=CCCC  00.05.00 - 00.15.00\nhttps://youtu.be/DDDD  00:02:30 - 00:08:10\n\nSans horaires = vidéo entière. Avec les deux horaires = PART.",
    "en": "The .txt file contains one link per line.\n\nFull video:\nhttps://youtube.com/watch?v=AAAA\nhttps://youtu.be/BBBB\n\nWith start / end:\nhttps://youtube.com/watch?v=CCCC  00.05.00 - 00.15.00\nhttps://youtu.be/DDDD  00:02:30 - 00:08:10\n\nNo times = full video. Both times = PART.",
    "ar": "ملف .txt فيه رابط واحد في كل سطر.\n\nفيديو كامل:\nhttps://youtube.com/watch?v=AAAA\nhttps://youtu.be/BBBB\n\nمع البداية والنهاية:\nhttps://youtube.com/watch?v=CCCC  00.05.00 - 00.15.00\nhttps://youtu.be/DDDD  00:02:30 - 00:08:10\n\nبدون أوقات = الفيديو كامل. مع الوقتين = PART.",
    "darija": "ملف .txt فيه رابط واحد فكل سطر.\n\nفيديو كامل:\nhttps://youtube.com/watch?v=AAAA\nhttps://youtu.be/BBBB\n\nمع البداية والنهاية:\nhttps://youtube.com/watch?v=CCCC  00.05.00 - 00.15.00\nhttps://youtu.be/DDDD  00:02:30 - 00:08:10\n\nبلا توقيت = الفيديو كامل. بجوج الأوقات = PART.",
    "nl": "Het .txt-bestand bevat één link per regel.\n\nVolledige video:\nhttps://youtube.com/watch?v=AAAA\nhttps://youtu.be/BBBB\n\nMet begin- en eindtijd:\nhttps://youtube.com/watch?v=CCCC  00.05.00 - 00.15.00\nhttps://youtu.be/DDDD  00:02:30 - 00:08:10\n\nGeen tijden = volledige video. Beide tijden = PART.",
}

def show_import_list_help():
    messagebox.showinfo(tr("Import list help"), _IMPORT_HELP.get(CURRENT_LANGUAGE, _IMPORT_HELP["en"]))



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


# ============================================================
# MAIN UI — Z²SE V32.44 PRO UX / FACEBOOK RELIABILITY
# ============================================================

main = ttk.Frame(root, style="Z2SE.TFrame", padding=0)
main.pack(fill="both", expand=True)

# ------------------------------------------------------------
# Compact brand / menu strip
# ------------------------------------------------------------

top_brand = tk.Frame(
    main,
    bg=UI_TOP,
    height=66,
    highlightthickness=0,
)
top_brand.pack(fill="x")
top_brand.pack_propagate(False)

brand_left = tk.Frame(top_brand, bg=UI_TOP)
brand_left.pack(side="left", fill="y", padx=(18, 10))

brand_icon_photo = None
try:
    if Image is not None and ImageTk is not None and os.path.isfile(BRAND_ICON_PNG):
        _brand_icon = Image.open(BRAND_ICON_PNG).convert("RGBA").resize(
            (36, 36),
            Image.Resampling.LANCZOS,
        )
        brand_icon_photo = ImageTk.PhotoImage(_brand_icon)
        tk.Label(
            brand_left,
            image=brand_icon_photo,
            bg=UI_TOP,
            bd=0,
        ).pack(side="left", pady=13)
except Exception:
    brand_icon_photo = None

brand_text = tk.Frame(brand_left, bg=UI_TOP)
brand_text.pack(side="left", padx=(10, 0), pady=9)

tk.Label(
    brand_text,
    text="Z²SE",
    font=("Segoe UI Semibold", 16),
    fg=UI_TOP_TEXT,
    bg=UI_TOP,
).pack(anchor="w")

tk.Label(
    brand_text,
    text=tr("MEDIA DOWNLOADER"),
    font=("Segoe UI Semibold", 7),
    fg=UI_TOP_MUTED,
    bg=UI_TOP,
).pack(anchor="w")

menu_strip = tk.Frame(top_brand, bg=UI_TOP)
menu_strip.pack(side="left", padx=(26, 0))


def _open_chrome_extensions_page():
    """Open Chrome's extension manager from the desktop app."""
    try:
        subprocess.Popen(
            [
                "cmd.exe",
                "/c",
                "start",
                "",
                "chrome://extensions",
            ],
            creationflags=(
                subprocess.CREATE_NO_WINDOW
                if os.name == "nt"
                else 0
            ),
        )
    except Exception:
        messagebox.showinfo(
            "Chrome Extensions",
            "فتح Chrome وكتب:\\n\\nchrome://extensions",
        )


def _open_stable_extension_folder():
    stable_folder = os.path.join(
        APP_DIR,
        "ChromeExtension_V15_STABLE",
    )

    if os.path.isdir(stable_folder):
        try:
            os.startfile(stable_folder)
            return
        except Exception:
            pass

    messagebox.showinfo(
        "Z²SE Browser Extension",
        "Stable extension folder ما لقيتوش.\\n\\n"
        f"Expected:\\n{stable_folder}",
    )


def _show_keyboard_shortcuts():
    body = {
        "fr": (
            "LISTE DES TÉLÉCHARGEMENTS\n"
            "Ctrl + A        Tout sélectionner\n"
            "Ctrl + Shift+A  Tout désélectionner\n"
            "Suppr           Supprimer / retirer la sélection\n"
            "Entrée          Ouvrir le fichier terminé\n"
            "Ctrl + clic     Ajouter/retirer une ligne\n"
            "Maj + clic      Sélectionner une plage\n\n"
            "Pause / Reprendre / Annuler sont aussi disponibles "
            "avec le clic droit et dans les fenêtres de progression."
        ),
        "en": (
            "DOWNLOADS LIST\n"
            "Ctrl + A        Select all\n"
            "Ctrl + Shift+A  Deselect all\n"
            "Delete          Delete / remove selected\n"
            "Enter           Open selected finished file\n"
            "Ctrl + Click    Add/remove individual row\n"
            "Shift + Click   Select a range\n\n"
            "Pause / Resume / Cancel are also available "
            "from right-click and progress windows."
        ),
        "ar": (
            "قائمة التنزيلات\n"
            "Ctrl + A        تحديد الكل\n"
            "Ctrl + Shift+A  إلغاء تحديد الكل\n"
            "Delete          حذف المحدد\n"
            "Enter           فتح الملف المكتمل\n"
            "Ctrl + Click    إضافة/إزالة سطر\n"
            "Shift + Click   تحديد نطاق\n\n"
            "الإيقاف المؤقت والاستئناف والإلغاء متاحة أيضًا "
            "بالزر الأيمن ومن نوافذ التقدم."
        ),
        "darija": (
            "لائحة التحميلات\n"
            "Ctrl + A        اختار الكل\n"
            "Ctrl + Shift+A  حيد الاختيار كامل\n"
            "Delete          حيد المختار\n"
            "Enter           حل الملف اللي سالا\n"
            "Ctrl + Click    زيد/حيد سطر\n"
            "Shift + Click   اختار مجموعة\n\n"
            "Pause / كمّل / Cancel كاينين حتى فالكليك باليمين "
            "وفنوافذ Progress."
        ),
        "nl": (
            "DOWNLOADLIJST\n"
            "Ctrl + A        Alles selecteren\n"
            "Ctrl + Shift+A  Alles deselecteren\n"
            "Delete          Selectie verwijderen\n"
            "Enter           Voltooid bestand openen\n"
            "Ctrl + Click    Rij toevoegen/verwijderen\n"
            "Shift + Click   Bereik selecteren\n\n"
            "Pauzeren / Hervatten / Annuleren kan ook via rechtsklik "
            "en via de voortgangsvensters."
        ),
    }.get(CURRENT_LANGUAGE)

    messagebox.showinfo(
        tr("Keyboard shortcuts"),
        body,
    )


def _show_about_z2se():
    body = {
        "fr": (
            "Z²SE Media Downloader\n"
            f"Version {APP_VERSION}\n\n"
            "Bridge navigateur + Smart HLS + FFmpeg + yt-dlp\n"
            "Historique persistant • Progression par téléchargement • "
            "Lancement automatique depuis le navigateur"
        ),
        "en": (
            "Z²SE Media Downloader\n"
            f"Version {APP_VERSION}\n\n"
            "Browser Bridge + Smart HLS + FFmpeg + yt-dlp\n"
            "Persistent history • Per-download progress • Browser auto-launch"
        ),
        "ar": (
            "Z²SE Media Downloader\n"
            f"الإصدار {APP_VERSION}\n\n"
            "جسر المتصفح + Smart HLS + FFmpeg + yt-dlp\n"
            "سجل دائم • تقدم مستقل لكل تنزيل • تشغيل تلقائي من المتصفح"
        ),
        "darija": (
            "Z²SE Media Downloader\n"
            f"النسخة {APP_VERSION}\n\n"
            "Browser Bridge + Smart HLS + FFmpeg + yt-dlp\n"
            "History محفوظ • Progress لكل تحميل بوحدو • تشغيل من المتصفح"
        ),
        "nl": (
            "Z²SE Media Downloader\n"
            f"Versie {APP_VERSION}\n\n"
            "Browser Bridge + Smart HLS + FFmpeg + yt-dlp\n"
            "Blijvende geschiedenis • Voortgang per download • Automatisch starten vanuit de browser"
        ),
    }.get(CURRENT_LANGUAGE)

    messagebox.showinfo(
        tr("About Z²SE"),
        body,
    )


def _make_top_menu_button(label, menu):
    button = tk.Menubutton(
        menu_strip,
        text=label,
        font=("Segoe UI", 9),
        fg="#d8e1ef",
        bg=UI_TOP,
        activeforeground="#ffffff",
        activebackground=UI_TOP_SOFT,
        bd=0,
        relief="flat",
        padx=10,
        pady=23,
        cursor="hand2",
        menu=menu,
    )
    button.pack(side="left")

    # V32.33: explicit popup binding.
    # This fixes cases where a Tk Menubutton visually clicks but does not
    # display its attached dropdown menu on some Windows/Tk combinations.
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

    button.bind(
        "<Button-1>",
        _popup_menu,
        add="+",
    )

    return button


# FILE -------------------------------------------------------------
file_menu = tk.Menu(
    menu_strip,
    tearoff=0,
)
file_menu.add_command(
    label=tr("Add new row"),
    command=lambda: add_bulk_row(),
)
file_menu.add_command(
    label=tr("Paste links"),
    command=paste_bulk_links,
)
file_menu.add_command(
    label=tr("Load links file…"),
    command=load_liens_txt,
)
file_menu.add_separator()
file_menu.add_command(
    label=tr("Open Downloads folder"),
    command=open_downloads,
)
file_menu.add_command(
    label=tr("Open Z²SE app folder"),
    command=lambda: os.startfile(APP_DIR),
)
file_menu.add_separator()
file_menu.add_command(
    label=tr("Hide main window to tray"),
    command=hide_to_tray,
)
file_menu.add_command(
    label=tr("Quit Z²SE"),
    command=really_quit_app,
)
_make_top_menu_button(
    tr("File"),
    file_menu,
)


# DOWNLOADS --------------------------------------------------------
downloads_menu = tk.Menu(
    menu_strip,
    tearoff=0,
)
downloads_menu.add_command(
    label=tr("Start downloads"),
    command=start_bulk,
)
downloads_menu.add_separator()
downloads_menu.add_command(
    label=tr("Pause all"),
    command=pause_all_downloads,
)
downloads_menu.add_command(
    label=tr("Resume all"),
    command=resume_all_downloads,
)
downloads_menu.add_command(
    label=tr("Stop all"),
    command=stop_all,
)
downloads_menu.add_separator()
downloads_menu.add_command(
    label=tr("Select all"),
    command=lambda: select_all_download_rows(),
)
downloads_menu.add_command(
    label=tr("Deselect all"),
    command=lambda: deselect_all_download_rows(),
)
downloads_menu.add_command(
    label=tr("Delete selected…"),
    command=lambda: delete_selected_with_keyboard_v15(),
)
downloads_menu.add_separator()
downloads_menu.add_command(
    label=tr("Clear finished/history list"),
    command=clear_download_list,
)
_make_top_menu_button(
    tr("Downloads"),
    downloads_menu,
)


# TOOLS ------------------------------------------------------------
tools_menu = tk.Menu(
    menu_strip,
    tearoff=0,
)
tools_menu.add_command(
    label=_mtr("merge_videos"),
    command=merge_videos_from_files,
)
tools_menu.add_separator()
tools_menu.add_command(
    label=tr("Health Check"),
    command=show_health_check,
)
tools_menu.add_command(
    label=tr("Check updates now"),
    command=manual_z2se_update,
)
tools_menu.add_separator()
tools_menu.add_command(
    label=tr("Update download engine"),
    command=manual_update,
)
tools_menu.add_command(
    label=tr("Clear Turbo cache"),
    command=clear_turbo_cache,
)
tools_menu.add_separator()
tools_menu.add_command(
    label=tr("Show / Hide technical log"),
    command=lambda: toggle_log(),
)
tools_menu.add_separator()
tools_menu.add_command(
    label=tr("Open Chrome Extensions"),
    command=_open_chrome_extensions_page,
)
tools_menu.add_command(
    label=tr("Open stable V15 extension folder"),
    command=_open_stable_extension_folder,
)
_make_top_menu_button(
    tr("Tools"),
    tools_menu,
)


# LANGUAGE ---------------------------------------------------------
def _restart_after_language_change():
    try:
        if IS_COMPILED:
            cmd = [sys.executable]
        else:
            cmd = [sys.executable, os.path.abspath(__file__)]

        subprocess.Popen(
            cmd,
            cwd=APP_DIR,
            creationflags=(
                subprocess.CREATE_NO_WINDOW
                if os.name == "nt"
                else 0
            ),
        )

        root.after(250, really_quit_app)

    except Exception as exc:
        messagebox.showerror(tr("Language"), str(exc))


def _change_language(code):
    code = str(code or "").strip().lower()

    if code not in LANGUAGE_LABELS:
        return

    if code == CURRENT_LANGUAGE:
        _raw_showinfo(
            tr("Language"),
            LANGUAGE_LABELS.get(
                CURRENT_LANGUAGE,
                CURRENT_LANGUAGE,
            ),
        )
        return

    if not _save_language(code):
        messagebox.showerror(
            tr("Language"),
            "Could not save language settings.",
        )
        return

    if downloads_are_running():
        _raw_showinfo(
            tr("Language"),
            tr("Language saved. Restart Z²SE after the active downloads finish."),
        )
        return

    if _raw_askyesno(
        tr("Language saved"),
        tr("Restart now to apply the new language?"),
    ):
        _restart_after_language_change()


language_menu = tk.Menu(menu_strip, tearoff=0)

for _lang_code in ("fr", "en", "ar", "darija", "nl"):
    language_menu.add_radiobutton(
        label=LANGUAGE_LABELS[_lang_code],
        variable=language_var,
        value=_lang_code,
        command=lambda code=_lang_code: _change_language(code),
    )

_make_top_menu_button(
    tr("Language"),
    language_menu,
)


# HELP -------------------------------------------------------------
help_menu = tk.Menu(
    menu_strip,
    tearoff=0,
)
help_menu.add_command(
    label=tr("Keyboard shortcuts"),
    command=_show_keyboard_shortcuts,
)
help_menu.add_command(
    label=tr("Chrome extension setup"),
    command=lambda: messagebox.showinfo(
        "Chrome Extension Setup",
        "1. Open chrome://extensions\\n"
        "2. Enable Developer mode\\n"
        "3. Click Load unpacked\\n"
        "4. Select:\\n"
        + os.path.join(
            APP_DIR,
            "ChromeExtension_V15_STABLE",
        ),
    ),
)
help_menu.add_separator()
help_menu.add_command(
    label=tr("About Z²SE"),
    command=_show_about_z2se,
)
_make_top_menu_button(
    tr("Help"),
    help_menu,
)

engine_badge = tk.Label(
    top_brand,
    text=tr("●  ENGINE READY"),
    font=("Segoe UI Semibold", 8),
    fg="#6ee7a7",
    bg=UI_TOP_SOFT,
    padx=10,
    pady=6,
)
engine_badge.pack(side="right", padx=(8, 18))

version_badge = tk.Label(
    top_brand,
    text=f"v{APP_VERSION}",
    font=("Segoe UI Semibold", 8),
    fg="#b8c7dc",
    bg=UI_TOP,
)
version_badge.pack(side="right", padx=(4, 4))


# ------------------------------------------------------------
# Toolbar — compact, desktop-manager style
# ------------------------------------------------------------

toolbar = tk.Frame(
    main,
    bg=UI_BG,
    height=76,
    highlightthickness=0,
)
toolbar.pack(fill="x")
toolbar.pack_propagate(False)

toolbar_inner = tk.Frame(
    toolbar,
    bg=UI_PANEL,
    highlightthickness=1,
    highlightbackground=UI_BORDER,
)
toolbar_inner.pack(fill="both", expand=True, padx=14, pady=(10, 6))

ttk.Button(
    toolbar_inner,
    text=tr("▶  Start"),
    command=start_bulk,
    style="Primary.TButton",
).pack(side="left", padx=(0, 7))

ttk.Button(
    toolbar_inner,
    text=tr("■  Stop All"),
    command=stop_all,
    style="Danger.TButton",
).pack(side="left", padx=5)

main_pause_button = ttk.Button(
    toolbar_inner,
    text=tr("Ⅱ  Pause"),
    command=pause_all_downloads,
    style="Toolbar.TButton",
    state="disabled",
)
main_pause_button.pack(side="left", padx=(8, 4))

main_resume_button = ttk.Button(
    toolbar_inner,
    text=tr("▶  Resume"),
    command=resume_all_downloads,
    style="Toolbar.TButton",
    state="disabled",
)
main_resume_button.pack(side="left", padx=4)

ttk.Separator(
    toolbar_inner,
    orient="vertical",
).pack(side="left", fill="y", padx=10)

ttk.Button(
    toolbar_inner,
    text=tr("Open Folder"),
    command=open_downloads,
    style="Toolbar.TButton",
).pack(side="left", padx=5)

ttk.Button(
    toolbar_inner,
    text=tr("Clear List"),
    command=clear_download_list,
    style="Toolbar.TButton",
).pack(side="left", padx=5)




# ============================================================
# INTERNAL SINGLE ENGINE UI (HIDDEN)
# ============================================================

single_tab = ttk.Frame(main)

single_url_entry = ttk.Entry(
    single_tab,
    textvariable=single_url_var,
)

single_quality_box = ttk.Combobox(
    single_tab,
    textvariable=single_quality_var,
    values=["Best", "1080p", "720p", "480p"],
    state="readonly",
)

single_start_entry = ttk.Entry(
    single_tab,
    textvariable=single_start_var,
)

single_end_entry = ttk.Entry(
    single_tab,
    textvariable=single_end_var,
)

single_download_button = ttk.Button(
    single_tab,
    text=tr("Download"),
    command=start_single,
)

single_progress = ttk.Progressbar(
    single_tab,
    variable=single_progress_var,
    maximum=100,
    style="Z2SE.Horizontal.TProgressbar",
)

set_single_part_state()


# ------------------------------------------------------------
# Main work area
# ------------------------------------------------------------

workspace = tk.Frame(main, bg=UI_BG)
workspace.pack(fill="both", expand=True, padx=14, pady=(8, 14))


# ------------------------------------------------------------
# V32.34 CLEAN UI
# Decorative left categories/quick-actions sidebar removed.
# Useful actions remain in the toolbar and top menus.
# ------------------------------------------------------------

# ------------------------------------------------------------
# Center content
# ------------------------------------------------------------

content = tk.Frame(workspace, bg=UI_BG)
content.pack(fill="both", expand=True)


# ------------------------------------------------------------
# Compact "new downloads" editor
# ------------------------------------------------------------

editor_card = tk.Frame(
    content,
    bg=UI_PANEL,
    highlightthickness=1,
    highlightbackground=UI_BORDER,
)
editor_card.pack(fill="x", pady=(0, 12))

editor_accent = tk.Frame(editor_card, bg=UI_ACCENT, height=3)
editor_accent.pack(fill="x")

editor_title = tk.Frame(editor_card, bg=UI_PANEL)
editor_title.pack(fill="x", padx=14, pady=(12, 8))

tk.Label(
    editor_title,
    text=tr("NEW DOWNLOADS"),
    font=("Segoe UI Semibold", 10),
    fg=UI_TEXT,
    bg=UI_PANEL,
).pack(side="left")

tk.Label(
    editor_title,
    text=tr("From / To empty = full video"),
    font=("Segoe UI", 8),
    fg=UI_MUTED,
    bg=UI_PANEL,
).pack(side="left", padx=12)

bulk_editor_header = tk.Frame(editor_card, bg=UI_PANEL)
bulk_editor_header.pack(fill="x", padx=(10, 26))

tk.Label(
    bulk_editor_header,
    text="#",
    width=3,
    anchor="center",
    font=("Segoe UI", 8, "bold"),
    fg=UI_MUTED,
    bg=UI_PANEL,
).grid(row=0, column=0)

tk.Label(
    bulk_editor_header,
    text="URL",
    anchor="center",
    font=("Segoe UI", 8, "bold"),
    fg=UI_MUTED,
    bg=UI_PANEL,
).grid(row=0, column=1, sticky="ew")

tk.Label(
    bulk_editor_header,
    text=tr("From"),
    width=11,
    anchor="center",
    font=("Segoe UI", 8, "bold"),
    fg=UI_MUTED,
    bg=UI_PANEL,
).grid(row=0, column=2, padx=4)

tk.Label(
    bulk_editor_header,
    text=tr("To"),
    width=11,
    anchor="center",
    font=("Segoe UI", 8, "bold"),
    fg=UI_MUTED,
    bg=UI_PANEL,
).grid(row=0, column=3, padx=4)

tk.Label(
    bulk_editor_header,
    text=tr("Mode"),
    width=8,
    anchor="center",
    font=("Segoe UI", 8, "bold"),
    fg=UI_MUTED,
    bg=UI_PANEL,
).grid(row=0, column=4, padx=5)

tk.Label(
    bulk_editor_header,
    text=tr("Format"),
    width=7,
    anchor="center",
    font=("Segoe UI", 8, "bold"),
    fg=UI_MUTED,
    bg=UI_PANEL,
).grid(row=0, column=5, padx=4)

tk.Label(
    bulk_editor_header,
    text="",
    width=3,
    bg=UI_PANEL,
).grid(row=0, column=6)

bulk_editor_header.columnconfigure(1, weight=1)

bulk_editor_outer = tk.Frame(editor_card, bg=UI_PANEL)
bulk_editor_outer.pack(fill="x", padx=10)

bulk_editor_canvas = tk.Canvas(
    bulk_editor_outer,
    height=92,
    bg=UI_PANEL,
    highlightthickness=0,
)

bulk_editor_scroll = ttk.Scrollbar(
    bulk_editor_outer,
    orient="vertical",
    command=bulk_editor_canvas.yview,
    style="Z2SE.Vertical.TScrollbar",
)

bulk_rows_frame = ttk.Frame(bulk_editor_canvas, style="Panel.TFrame")

bulk_rows_window = bulk_editor_canvas.create_window(
    (0, 0),
    window=bulk_rows_frame,
    anchor="nw",
)

bulk_editor_canvas.configure(
    yscrollcommand=bulk_editor_scroll.set
)

bulk_editor_canvas.pack(
    side="left",
    fill="x",
    expand=True,
)

bulk_editor_scroll.pack(
    side="right",
    fill="y",
)


def _bulk_rows_configure(_event=None):
    update_bulk_editor_scrollregion()


def _bulk_canvas_configure(event):
    try:
        bulk_editor_canvas.itemconfigure(
            bulk_rows_window,
            width=event.width
        )
    except Exception:
        pass


bulk_rows_frame.bind(
    "<Configure>",
    _bulk_rows_configure
)

bulk_editor_canvas.bind(
    "<Configure>",
    _bulk_canvas_configure
)


editor_footer = ttk.Frame(editor_card, style="Panel.TFrame")
editor_footer.pack(fill="x", padx=10, pady=(7, 10))

ttk.Button(
    editor_footer,
    text=tr("+ Add"),
    command=add_bulk_row,
    style="Toolbar.TButton",
).pack(side="left")

ttk.Button(
    editor_footer,
    text=tr("Paste"),
    command=paste_bulk_links,
    style="Toolbar.TButton",
).pack(side="left", padx=4)

ttk.Button(
    editor_footer,
    text=tr("Load File"),
    command=load_liens_txt,
    style="Toolbar.TButton",
).pack(side="left", padx=(4, 2))

import_help_button = ttk.Button(
    editor_footer,
    text="?",
    width=3,
    command=show_import_list_help,
    style="Ghost.TButton",
)
import_help_button.pack(side="left", padx=(0, 4))

ttk.Button(
    editor_footer,
    text=tr("Clear"),
    command=clear_bulk,
    style="Toolbar.TButton",
).pack(side="left", padx=4)

ttk.Label(
    editor_footer,
    text=tr("Quality"),
    style="Panel.TLabel",
).pack(side="left", padx=(18, 5))

bulk_quality_box = ttk.Combobox(
    editor_footer,
    textvariable=bulk_quality_var,
    values=["1080p", "720p", "480p"],
    state="readonly",
    width=8,
    style="Field.TCombobox",
)
bulk_quality_box.pack(side="left")

ttk.Label(
    editor_footer,
    text=tr("Parallel"),
    style="Panel.TLabel",
).pack(side="left", padx=(14, 5))

bulk_workers_spin = ttk.Spinbox(
    editor_footer,
    from_=1,
    to=8,
    textvariable=bulk_workers_var,
    width=4,
    style="Field.TSpinbox",
)
bulk_workers_spin.pack(side="left")


bulk_start_button = ttk.Button(
    editor_footer,
    text=tr("DOWNLOAD"),
    command=start_bulk,
    style="Primary.TButton",
)
bulk_start_button.pack(side="right")


# Start with one clean row.
add_bulk_row()


# ------------------------------------------------------------
# Download list — main visual focus
# ------------------------------------------------------------

list_card = tk.Frame(
    content,
    bg=UI_PANEL,
    highlightthickness=1,
    highlightbackground=UI_BORDER,
)
list_card.pack(fill="both", expand=True)

list_header = tk.Frame(list_card, bg=UI_PANEL)
list_header.pack(fill="x", padx=14, pady=(12, 8))

tk.Label(
    list_header,
    text=tr("DOWNLOADS"),
    font=("Segoe UI Semibold", 10),
    fg=UI_TEXT,
    bg=UI_PANEL,
).pack(side="left")

ttk.Button(
    list_header,
    text=tr("Deselect"),
    command=lambda: deselect_all_download_rows(),
    style="Ghost.TButton",
).pack(side="right", padx=(5, 0))

ttk.Button(
    list_header,
    text=tr("Select All"),
    command=lambda: select_all_download_rows(),
    style="Ghost.TButton",
).pack(side="right", padx=(8, 0))

tk.Label(
    list_header,
    textvariable=selected_rows_var,
    font=("Segoe UI", 8),
    fg="#5c6a7f",
    bg=UI_PANEL,
).pack(side="right", padx=(8, 0))

tk.Label(
    list_header,
    textvariable=bulk_counter_var,
    font=("Segoe UI", 9),
    fg=UI_MUTED,
    bg=UI_PANEL,
).pack(side="right")

tree_frame = ttk.Frame(list_card, style="Panel.TFrame")
tree_frame.pack(fill="both", expand=True, padx=8)

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

bulk_tree.column("num", width=38, anchor="center", stretch=False)
bulk_tree.column("title", width=345)
bulk_tree.column("format", width=65, anchor="center")
bulk_tree.column("part", width=120, anchor="center")
bulk_tree.column("progress", width=78, anchor="center")
bulk_tree.column("speed", width=105, anchor="center")
bulk_tree.column("eta", width=75, anchor="center")
bulk_tree.column("size", width=90, anchor="center")
bulk_tree.column("status", width=100, anchor="center")

# V32.15 — subtle professional status styling.
try:
    bulk_tree.tag_configure("active", foreground="#17365d")
    bulk_tree.tag_configure("paused", foreground="#8a5a00")
    bulk_tree.tag_configure("done", foreground="#16733c")
    bulk_tree.tag_configure("error", foreground="#a12622")
    bulk_tree.tag_configure("cancelled", foreground="#666666")
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




# ------------------------------------------------------------
# V32.13 — ONE INDEPENDENT PROGRESS WINDOW PER DOWNLOAD
# ------------------------------------------------------------

job_progress_windows = {}
job_progress_vars = {}

# V32.14:
# Every download still has its OWN progress window.
# Minimized progress windows share ONE reliable tray icon.
job_progress_minimized = set()
job_shared_tray_icon = None
job_shared_tray_running = False

# Kept only for backward compatibility with older V32.13 helpers.
job_progress_tray_icons = {}
job_progress_tray_threads = set()
job_progress_lock = threading.Lock()


def _job_row_snapshot(index):
    item_id = bulk_tree_ids.get(index)

    if not item_id:
        return None

    try:
        values = list(
            bulk_tree.item(
                item_id,
                "values",
            )
        )
    except Exception:
        return None

    while len(values) < 9:
        values.append("")

    return {
        "title": str(values[1] or f"Download #{index}"),
        "type": str(values[2] or ""),
        "mode": str(values[3] or ""),
        "progress": str(values[4] or "0.0%"),
        "speed": str(values[5] or "—"),
        "eta": str(values[6] or "—"),
        "size": str(values[7] or "—"),
        "status": str(values[8] or "Waiting"),
    }


def _job_terminal(status):
    return canonical_status(status) in {
        "Done ✅",
        "Error",
        "Stopped",
        "Interrupted",
        "Saved",
    }


def _job_window_center_geometry(window, index):
    window.update_idletasks()

    width = 560
    height = 232

    sw = window.winfo_screenwidth()
    sh = window.winfo_screenheight()

    # Cascade simultaneous IDM-like windows around the center so they do not
    # hide each other completely.
    active_order = [
        key
        for key, value in job_progress_windows.items()
        if value is not None
    ]

    try:
        slot = active_order.index(index)
    except Exception:
        slot = len(active_order)

    offset = (slot % 6) * 24

    x = max(10, (sw - width) // 2 + offset)
    y = max(10, (sh - height) // 2 + offset)

    window.geometry(
        f"{width}x{height}+{x}+{y}"
    )



def _stop_shared_progress_tray_if_unused():
    global job_shared_tray_icon
    global job_shared_tray_running

    if job_progress_minimized:
        return

    icon = job_shared_tray_icon
    job_shared_tray_icon = None
    job_shared_tray_running = False

    if icon is not None:
        try:
            icon.stop()
        except Exception:
            pass


def _show_all_minimized_progress_windows():
    for index in list(job_progress_minimized):
        _show_job_progress_window(index)


def _shared_progress_tray_loop():
    global job_shared_tray_icon
    global job_shared_tray_running

    try:
        menu = pystray.Menu(
            pystray.MenuItem(
                "Show Download Progress",
                lambda icon, item: gui_call(
                    _show_all_minimized_progress_windows
                ),
                default=True,
            ),
            pystray.MenuItem(
                tr("Open Main Z²SE"),
                lambda icon, item: gui_call(
                    _show_app_window
                ),
            ),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem(
                tr("Pause all"),
                lambda icon, item: gui_call(
                    pause_all_downloads
                ),
            ),
            pystray.MenuItem(
                tr("Resume all"),
                lambda icon, item: gui_call(
                    resume_all_downloads
                ),
            ),
            pystray.MenuItem(
                tr("Cancel All Active"),
                lambda icon, item: gui_call(
                    stop_all
                ),
            ),
        )

        icon = pystray.Icon(
            "z2se_download_progress_shared",
            create_mini_tray_image(),
            "Z²SE Download Progress",
            menu,
        )

        job_shared_tray_icon = icon
        icon.run()

    except Exception as exc:
        log(f"Shared progress tray ERROR: {exc}")

    finally:
        job_shared_tray_icon = None
        job_shared_tray_running = False


def _ensure_shared_progress_tray():
    global job_shared_tray_running

    if (
        not TRAY_AVAILABLE
        or app_quitting
        or not job_progress_minimized
    ):
        return

    if job_shared_tray_running:
        return

    job_shared_tray_running = True

    threading.Thread(
        target=_shared_progress_tray_loop,
        daemon=True,
        name="Z2SESharedProgressTray",
    ).start()


def _remove_job_tray_icon(index):
    # V32.14 compatibility helper:
    # progress windows no longer create one Windows icon each.
    job_progress_minimized.discard(index)
    _stop_shared_progress_tray_if_unused()


def _destroy_job_progress_window(index):
    job_progress_minimized.discard(index)
    _stop_shared_progress_tray_if_unused()

    # Stop any legacy per-job V32.13 icon if one somehow exists.
    icon = job_progress_tray_icons.pop(index, None)

    if icon is not None:
        try:
            icon.stop()
        except Exception:
            pass

    window = job_progress_windows.pop(index, None)
    job_progress_vars.pop(index, None)

    if window is not None:
        try:
            window.destroy()
        except Exception:
            pass


def _show_job_progress_window(index):
    window = job_progress_windows.get(index)

    if window is None:
        job_progress_minimized.discard(index)
        _stop_shared_progress_tray_if_unused()
        return

    job_progress_minimized.discard(index)

    try:
        window.deiconify()
        window.state("normal")
        _job_window_center_geometry(window, index)
        window.lift()
        window.attributes("-topmost", True)
        window.after(
            700,
            lambda w=window: (
                w.attributes("-topmost", False)
                if w.winfo_exists()
                else None
            ),
        )
    except Exception:
        pass

    _stop_shared_progress_tray_if_unused()


def _job_tray_loop(index):
    try:
        snapshot = _job_row_snapshot(index) or {}
        short_title = snapshot.get("title") or f"Download #{index}"

        if len(short_title) > 45:
            short_title = short_title[:42] + "…"

        menu = pystray.Menu(
            pystray.MenuItem(
                tr("Show Progress"),
                lambda icon, item, idx=index: gui_call(
                    _show_job_progress_window,
                    idx,
                ),
                default=True,
            ),
            pystray.MenuItem(
                "Open Main Z²SE",
                lambda icon, item: gui_call(_show_app_window),
            ),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem(
                tr("Pause"),
                lambda icon, item, idx=index: gui_call(
                    pause_download_job,
                    idx,
                ),
            ),
            pystray.MenuItem(
                tr("Resume"),
                lambda icon, item, idx=index: gui_call(
                    resume_download_job,
                    idx,
                ),
            ),
            pystray.MenuItem(
                tr("Cancel Download"),
                lambda icon, item, idx=index: gui_call(
                    cancel_download_job,
                    idx,
                ),
            ),
        )

        icon = pystray.Icon(
            f"z2se_job_{index}",
            create_mini_tray_image(),
            f"Z²SE #{index} • {short_title}",
            menu,
        )

        job_progress_tray_icons[index] = icon
        icon.run()

    except Exception as exc:
        log(f"[{index}] Job tray ERROR: {exc}")

    finally:
        job_progress_tray_icons.pop(index, None)
        job_progress_tray_threads.discard(index)


def _ensure_job_tray_icon(index):
    # Compatibility wrapper: one shared progress icon for all minimized jobs.
    if index in job_progress_windows:
        job_progress_minimized.add(index)
        _ensure_shared_progress_tray()


def _minimize_job_progress_to_tray(index):
    window = job_progress_windows.get(index)

    if window is None:
        return

    # Mark first, because withdraw() itself fires another <Unmap>.
    job_progress_minimized.add(index)

    try:
        window.withdraw()
    except Exception:
        pass

    _ensure_shared_progress_tray()


def _close_job_progress(index):
    """
    X on one progress window cancels ONLY that download.
    Other simultaneous downloads continue.
    """
    cancel_download_job(index)
    _destroy_job_progress_window(index)


def _refresh_job_progress_window(index):
    window = job_progress_windows.get(index)
    vars_ = job_progress_vars.get(index)

    if window is None or vars_ is None:
        return

    try:
        if not window.winfo_exists():
            _destroy_job_progress_window(index)
            return
    except Exception:
        return

    snap = _job_row_snapshot(index)

    if snap is None:
        window.after(
            300,
            lambda idx=index: _refresh_job_progress_window(idx),
        )
        return

    title = snap["title"]
    if len(title) > 66:
        title = title[:63] + "…"

    vars_["title"].set(title)
    vars_["status"].set(snap["status"])
    vars_["speed"].set(snap["speed"] or "—")
    vars_["eta"].set(snap["eta"] or "—")
    vars_["size"].set(snap["size"] or "—")

    try:
        percent = float(
            snap["progress"].replace("%", "").strip()
            or 0.0
        )
    except Exception:
        percent = 0.0

    percent = max(0.0, min(100.0, percent))

    vars_["progress"].set(percent)
    vars_["percent"].set(f"{percent:.1f}%")

    with paused_job_lock:
        paused = index in paused_job_indices

    try:
        vars_["pause_btn"].configure(
            state=(
                "disabled"
                if paused or _job_terminal(snap["status"])
                else "normal"
            )
        )
        vars_["resume_btn"].configure(
            state=(
                "normal"
                if paused and not _job_terminal(snap["status"])
                else "disabled"
            )
        )
        vars_["cancel_btn"].configure(
            state=(
                "disabled"
                if _job_terminal(snap["status"])
                else "normal"
            )
        )
    except Exception:
        pass

    if _job_terminal(snap["status"]):
        # Per IDM-style progress lifecycle: this one window/icon disappears
        # when THIS download is done/cancelled/errored.
        window.after(
            900,
            lambda idx=index: _destroy_job_progress_window(idx),
        )
        return

    window.after(
        300,
        lambda idx=index: _refresh_job_progress_window(idx),
    )


def create_job_progress_window(index):
    if index in job_progress_windows:
        _show_job_progress_window(index)
        return

    window = tk.Toplevel(root)
    window.title(f"Z²SE — {tr('Download')} #{index}")
    window.resizable(False, False)
    window.configure(bg=UI_BG)

    try:
        if os.path.isfile(BRAND_ICON_ICO):
            window.iconbitmap(BRAND_ICON_ICO)
    except Exception:
        pass

    title_var = tk.StringVar(value=f"{tr('Download')} #{index}")
    status_var_local = tk.StringVar(value=tr("Waiting"))
    speed_var = tk.StringVar(value="—")
    eta_var = tk.StringVar(value="—")
    size_var = tk.StringVar(value="—")
    progress_var = tk.DoubleVar(value=0.0)
    percent_var = tk.StringVar(value="0.0%")

    outer = tk.Frame(
        window,
        bg=UI_PANEL,
        highlightthickness=1,
        highlightbackground=UI_BORDER,
    )
    outer.pack(fill="both", expand=True, padx=10, pady=10)

    header = tk.Frame(
        outer,
        bg=UI_TOP,
        height=50,
    )
    header.pack(fill="x")
    header.pack_propagate(False)

    tk.Label(
        header,
        text=f"Z²SE  •  {tr('Download')} #{index}",
        font=("Segoe UI Semibold", 10),
        fg=UI_TOP_TEXT,
        bg=UI_TOP,
    ).pack(
        side="left",
        padx=12,
        pady=7,
    )

    tk.Label(
        header,
        textvariable=percent_var,
        font=("Segoe UI Semibold", 11),
        fg="#ffffff",
        bg=UI_ACCENT,
        padx=10,
        pady=4,
    ).pack(
        side="right",
        padx=12,
        pady=9,
    )

    body = tk.Frame(
        outer,
        bg=UI_PANEL,
    )
    body.pack(
        fill="both",
        expand=True,
        padx=13,
        pady=(12, 11),
    )

    tk.Label(
        body,
        textvariable=title_var,
        font=("Segoe UI Semibold", 10),
        fg=UI_TEXT,
        bg=UI_PANEL,
        anchor="w",
    ).pack(fill="x")

    ttk.Progressbar(
        body,
        variable=progress_var,
        maximum=100,
        style="Z2SE.Horizontal.TProgressbar",
    ).pack(
        fill="x",
        pady=(8, 5),
    )

    tk.Label(
        body,
        textvariable=status_var_local,
        font=("Segoe UI", 8),
        fg="#526077",
        bg=UI_PANEL,
        anchor="w",
    ).pack(fill="x")

    stats = tk.Frame(body, bg=UI_PANEL)
    stats.pack(fill="x", pady=(5, 6))

    for label, variable in (
        (tr("Transfer rate"), speed_var),
        (tr("Time left"), eta_var),
        (tr("Size"), size_var),
    ):
        cell = tk.Frame(
            stats,
            bg="#f7f9fc",
            highlightthickness=1,
            highlightbackground="#e2e7ef",
        )
        cell.pack(side="left", fill="x", expand=True, padx=(0, 7))

        tk.Label(
            cell,
            text=label,
            font=("Segoe UI", 7),
            fg="#8791a2",
            bg="#f7f9fc",
        ).pack(anchor="w", padx=8, pady=(4, 0))

        tk.Label(
            cell,
            textvariable=variable,
            font=("Segoe UI", 8, "bold"),
            fg="#25324a",
            bg="#f7f9fc",
        ).pack(anchor="w", padx=8, pady=(0, 5))

    footer = tk.Frame(body, bg=UI_PANEL)
    footer.pack(fill="x")

    main_btn = tk.Button(
        footer,
        text=tr("Main Window"),
        command=_show_app_window,
        font=("Segoe UI", 8, "bold"),
        padx=9,
        pady=4,
    )
    main_btn.pack(side="right")

    cancel_btn = tk.Button(
        footer,
        text=tr("Cancel Download"),
        command=lambda idx=index: (
            cancel_download_job(idx),
            _destroy_job_progress_window(idx),
        ),
        font=("Segoe UI", 8, "bold"),
        bg="#f7e7e7",
        fg="#8d1c1c",
        padx=9,
        pady=4,
    )
    cancel_btn.pack(side="right", padx=(5, 6))

    resume_btn = tk.Button(
        footer,
        text=tr("Resume"),
        command=lambda idx=index: resume_download_job(idx),
        font=("Segoe UI", 8, "bold"),
        bg="#e8f2ea",
        fg="#176c36",
        padx=9,
        pady=4,
        state="disabled",
    )
    resume_btn.pack(side="right", padx=(5, 0))

    pause_btn = tk.Button(
        footer,
        text=tr("Pause"),
        command=lambda idx=index: pause_download_job(idx),
        font=("Segoe UI", 8, "bold"),
        padx=9,
        pady=4,
    )
    pause_btn.pack(side="right")

    job_progress_windows[index] = window
    job_progress_vars[index] = {
        "title": title_var,
        "status": status_var_local,
        "speed": speed_var,
        "eta": eta_var,
        "size": size_var,
        "progress": progress_var,
        "percent": percent_var,
        "pause_btn": pause_btn,
        "resume_btn": resume_btn,
        "cancel_btn": cancel_btn,
    }

    window.protocol(
        "WM_DELETE_WINDOW",
        lambda idx=index: _close_job_progress(idx),
    )

    def on_unmap(event, idx=index, w=window):
        if event.widget is not w:
            return

        def check_minimized():
            try:
                if idx not in job_progress_windows:
                    return

                # withdraw() triggers a second Unmap; just make sure the shared
                # tray icon is alive and do nothing else.
                if idx in job_progress_minimized:
                    _ensure_shared_progress_tray()
                    return

                snap = _job_row_snapshot(idx)

                if (
                    snap is not None
                    and _job_terminal(snap.get("status"))
                ):
                    return

                # On Windows/Tk the state can race between iconic/withdrawn.
                # An Unmap from an active progress window is treated as the
                # user's Minimize request.
                _minimize_job_progress_to_tray(idx)

            except Exception as exc:
                log(f"[{idx}] Minimize-to-tray warning: {exc}")

        w.after(80, check_minimized)

    window.bind(
        "<Unmap>",
        on_unmap,
        add="+",
    )

    _job_window_center_geometry(window, index)
    window.lift()

    _refresh_job_progress_window(index)



# ------------------------------------------------------------
# V32.15 — PRO DOWNLOAD LIST / MULTI-SELECTION
# ------------------------------------------------------------

def _selected_download_items():
    try:
        return list(
            bulk_tree.selection()
        )
    except Exception:
        return []


def _job_index_for_item(item_id):
    for index, mapped_item in list(
        bulk_tree_ids.items()
    ):
        if mapped_item == item_id:
            try:
                return int(index)
            except Exception:
                return index

    return None


def _selected_job_indices():
    indices = []

    for item_id in _selected_download_items():
        index = _job_index_for_item(item_id)

        if index is not None:
            indices.append(index)

    return indices


def _item_status(item_id):
    values = _row_values(item_id)

    if len(values) >= 9:
        return str(values[8] or "")

    return ""


def select_all_download_rows(event=None):
    try:
        children = bulk_tree.get_children()

        if children:
            bulk_tree.selection_set(children)
            bulk_tree.focus(children[0])

    except Exception:
        pass

    return "break" if event is not None else None


def deselect_all_download_rows(event=None):
    try:
        bulk_tree.selection_remove(
            bulk_tree.selection()
        )
    except Exception:
        pass

    return "break" if event is not None else None


def pause_selected_downloads():
    indices = _selected_job_indices()

    if not indices:
        return

    for index in indices:
        with paused_job_lock:
            already_paused = index in paused_job_indices

        if not already_paused:
            pause_download_job(index)


def resume_selected_downloads():
    indices = _selected_job_indices()

    if not indices:
        return

    for index in indices:
        with paused_job_lock:
            is_paused = index in paused_job_indices

        if is_paused:
            resume_download_job(index)


def cancel_selected_downloads():
    indices = _selected_job_indices()

    if not indices:
        return

    active = []

    for index in indices:
        item_id = bulk_tree_ids.get(index)

        if item_id and not _mini_is_terminal_status(
            _item_status(item_id)
        ):
            active.append(index)

    if not active:
        return

    if len(active) > 1:
        confirmed = messagebox.askyesno(
            "Cancel selected downloads",
            f"Cancel {len(active)} selected active downloads?",
            icon="warning",
        )

        if not confirmed:
            return

    for index in active:
        cancel_download_job(index)


def copy_selected_names():
    names = []

    for item_id in _selected_download_items():
        values = _row_values(item_id)

        if len(values) >= 2 and str(values[1]).strip():
            names.append(str(values[1]))

    if not names:
        return

    try:
        root.clipboard_clear()
        root.clipboard_append("\\n".join(names))
        root.update_idletasks()
    except Exception:
        pass


def copy_selected_paths():
    paths = []

    for item_id in _selected_download_items():
        path = _find_download_file_for_row(
            item_id
        )

        if path:
            paths.append(path)

    if not paths:
        messagebox.showinfo(
            "Copy full path",
            "ما لقيت حتى file path فالاختيار الحالي.",
        )
        return

    try:
        root.clipboard_clear()
        root.clipboard_append("\\n".join(paths))
        root.update_idletasks()
    except Exception:
        pass


def remove_selected_from_list():
    items = _selected_download_items()

    if not items:
        return

    non_terminal = [
        item_id
        for item_id in items
        if not _mini_is_terminal_status(
            _item_status(item_id)
        )
    ]

    if non_terminal:
        messagebox.showinfo(
            tr("Remove selected"),
            tr("One or more selected downloads are still active. Stop or cancel them first."),
        )
        return

    if len(items) > 1:
        confirmed = messagebox.askyesno(
            "Remove selected from list",
            f"Remove {len(items)} selected rows from Z²SE history?\\n\\n"
            "Downloaded files will stay on the PC.",
        )

        if not confirmed:
            return

    for item_id in items:
        row_file_paths.pop(
            item_id,
            None,
        )

        try:
            bulk_tree.delete(item_id)
        except Exception:
            pass

    schedule_download_history_save(50)


def delete_selected_files_from_pc():
    """
    V32.21:
    "Delete file(s) + list" means exactly that.

    A row is removed only when:
      - its exact/found file was moved to Recycle Bin successfully, OR
      - V32.21 has an exact stored path and that exact file is already gone.

    Unresolved legacy rows are NEVER silently removed by this option.
    """
    items = _selected_download_items()

    if not items:
        return

    non_terminal = [
        item_id
        for item_id in items
        if not _mini_is_terminal_status(
            _item_status(item_id)
        )
    ]

    if non_terminal:
        messagebox.showinfo(
            tr("Delete selected files"),
            tr("One or more selected downloads are still active. Stop or cancel them first."),
        )
        return

    row_state = {}
    unique_files = {}

    for item_id in items:
        exact = _exact_path_for_row(
            item_id
        )

        if exact:
            if os.path.isfile(exact):
                normalized = os.path.normcase(
                    os.path.abspath(exact)
                )
                row_state[item_id] = (
                    "file",
                    normalized,
                )
                unique_files.setdefault(
                    normalized,
                    exact,
                )
            else:
                # Exact path is known, but the file is already gone.
                row_state[item_id] = (
                    "already_missing",
                    exact,
                )

            continue

        legacy = _legacy_find_download_file_for_row(
            item_id
        )

        if legacy and os.path.isfile(legacy):
            normalized = os.path.normcase(
                os.path.abspath(legacy)
            )
            row_state[item_id] = (
                "file",
                normalized,
            )
            unique_files.setdefault(
                normalized,
                legacy,
            )
        else:
            row_state[item_id] = (
                "unresolved",
                "",
            )

    unresolved_count = sum(
        1
        for state, _ in row_state.values()
        if state == "unresolved"
    )

    if not unique_files and unresolved_count == len(items):
        messagebox.showwarning(
            "Delete selected files",
            "ما قدرتش نربط هاد السطور بالملفات الحقيقية فالدوسي، "
            "لذلك ما مسحت والو من اللائحة باش ما نعطيكش Delete كاذبة.\\n\\n"
            "التحميلات الجديدة من V32.21 غادي يتحفظ ليهم المسار الحقيقي "
            "أوتوماتيكياً.",
        )
        return

    confirmed = messagebox.askyesno(
        "Delete selected files",
        (
            f"Selected rows: {len(items)}\\n"
            f"Real file(s) found: {len(unique_files)}\\n"
            f"Unresolved legacy row(s): {unresolved_count}\\n\\n"
            "Move the found real file(s) to Windows Recycle Bin "
            "and remove ONLY the rows whose file deletion is confirmed?"
        ),
        icon="warning",
    )

    if not confirmed:
        return

    failed_paths = {}

    for normalized, path in unique_files.items():
        ok, error = _move_file_to_recycle_bin(
            path
        )

        if not ok:
            failed_paths[
                normalized
            ] = error

    removed = 0
    unresolved_names = []
    failed_names = []

    for item_id in items:
        state, value = row_state.get(
            item_id,
            ("unresolved", ""),
        )

        should_remove = False

        if state == "already_missing":
            should_remove = True

        elif state == "file":
            if value not in failed_paths:
                should_remove = True
            else:
                values = _row_values(
                    item_id
                )
                failed_names.append(
                    str(values[1])
                    if len(values) >= 2
                    else str(item_id)
                )

        else:
            values = _row_values(
                item_id
            )
            unresolved_names.append(
                str(values[1])
                if len(values) >= 2
                else str(item_id)
            )

        if should_remove:
            row_file_paths.pop(
                item_id,
                None,
            )

            try:
                bulk_tree.delete(
                    item_id
                )
                removed += 1
            except Exception:
                pass

    schedule_download_history_save(
        50
    )

    if unresolved_names or failed_names:
        details = [
            f"Removed: {removed} row(s).",
        ]

        if unresolved_names:
            details.append(
                f"Could not locate file for: {len(unresolved_names)} row(s)."
            )

        if failed_names:
            details.append(
                f"Windows could not delete: {len(failed_names)} file(s)."
            )

        messagebox.showwarning(
            "Delete selected files",
            "\\n".join(details),
        )


def delete_selected_with_keyboard_v15(event=None):
    """
    Delete key works with one OR many selected rows.
    The dialog clearly separates history-only removal from real-file deletion.
    """
    items = _selected_download_items()

    if not items:
        return "break"

    if any(
        not _mini_is_terminal_status(
            _item_status(item_id)
        )
        for item_id in items
    ):
        messagebox.showinfo(
            tr("Delete download"),
            tr("One or more selected downloads are still active. Stop or cancel them first."),
        )
        return "break"

    existing_files = sum(
        1
        for item_id in items
        if _find_download_file_for_row(item_id)
    )

    if len(items) == 1:
        values = _row_values(items[0])
        display_name = (
            str(values[1])
            if len(values) >= 2
            else "Selected download"
        )
    else:
        display_name = f"{len(items)} selected downloads"

    choice = _delete_choice_dialog(
        root,
        display_name,
        existing_files > 0,
    )

    if choice == "list":
        remove_selected_from_list()

    elif choice == "file":
        delete_selected_files_from_pc()

    return "break"


def open_selected_file():
    items = _selected_download_items()

    if len(items) != 1:
        return

    context_open_file()


# ------------------------------------------------------------
# V32.4 — Professional right-click menu for DOWNLOADS
# ------------------------------------------------------------

def _selected_download_item():
    selection = bulk_tree.selection()

    if selection:
        return selection[0]

    focused = bulk_tree.focus()
    return focused or None


def _row_values(item_id):
    if not item_id:
        return []

    try:
        return list(
            bulk_tree.item(
                item_id,
                "values",
            )
        )
    except Exception:
        return []


def _safe_filename_key(value):
    value = str(value or "").strip().lower()

    value = re.sub(
        r'[<>:"/\\\\|?*]+',
        " ",
        value,
    )
    value = re.sub(
        r"\s+",
        " ",
        value,
    )

    return value.strip()


def _persist_relinked_row_path(item_id, path):
    """
    Save a repaired real-file path back into the row/history so Open, Delete,
    Show in folder and Merge all benefit from the same repair.
    """
    path = _normalize_output_path(
        path
    )

    if (
        not item_id
        or not path
        or not os.path.isfile(
            path
        )
    ):
        return False

    row_file_paths[
        item_id
    ] = path

    index = _job_index_for_item(
        item_id
    )

    if index is not None:
        try:
            with job_output_paths_lock:
                job_output_paths[
                    int(
                        index
                    )
                ] = path
        except Exception:
            pass

    try:
        values = _row_values(
            item_id
        )

        if len(
            values
        ) >= 8:
            bulk_tree.set(
                item_id,
                "size",
                _human_file_size(
                    os.path.getsize(
                        path
                    )
                ),
            )
    except Exception:
        pass

    schedule_download_history_save(
        50
    )

    log(
        "🔗 AUTO RELINK: "
        + os.path.basename(
            path
        )
    )

    return True


def _smart_find_download_file_for_row(item_id):
    """
    V32.38 AUTO RELINK

    Safely recover a missing/stale exact path by combining:
      - visible title
      - expected media type/extension
      - displayed final size
      - filename word overlap

    A candidate must score strongly and must not be ambiguous.
    """
    values = _row_values(
        item_id
    )

    if len(
        values
    ) < 2:
        return None

    title = _safe_filename_key(
        values[
            1
        ]
    )

    if not title:
        return None

    expected_type = (
        str(
            values[
                2
            ]
        ).strip().lower()
        if len(
            values
        ) >= 3
        else ""
    )

    expected_size = (
        _parse_human_size(
            values[
                7
            ]
        )
        if len(
            values
        ) >= 8
        else 0
    )

    expected_exts = set()

    if "mp4" in expected_type:
        expected_exts.add(
            ".mp4"
        )
    elif "mp3" in expected_type:
        expected_exts.add(
            ".mp3"
        )

    ignored_exts = {
        ".part",
        ".tmp",
        ".ytdl",
        ".m3u8",
        ".json",
    }

    title_words = {
        word
        for word in title.split()
        if len(
            word
        ) >= 2
    }

    candidates = []

    try:
        for root_dir, dirs, files in os.walk(
            DOWNLOADS
        ):
            dirs[:] = [
                directory
                for directory in dirs
                if directory != "_video_cache"
            ]

            for filename in files:
                extension = os.path.splitext(
                    filename
                )[1].lower()

                if extension in ignored_exts:
                    continue

                if (
                    "_FINAL_MEDIA_EXTENSIONS"
                    in globals()
                    and extension
                    not in _FINAL_MEDIA_EXTENSIONS
                ):
                    continue

                path = os.path.join(
                    root_dir,
                    filename,
                )

                stem = _safe_filename_key(
                    os.path.splitext(
                        filename
                    )[0]
                )

                if not stem:
                    continue

                score = 0.0

                # Filename/title confidence.
                if stem == title:
                    score += 120.0
                elif title in stem:
                    score += 105.0
                elif stem in title:
                    score += 90.0
                else:
                    stem_words = {
                        word
                        for word in stem.split()
                        if len(
                            word
                        ) >= 2
                    }

                    if (
                        title_words
                        and stem_words
                    ):
                        common = len(
                            title_words
                            & stem_words
                        )

                        coverage = common / max(
                            1,
                            len(
                                title_words
                            ),
                        )

                        if common >= 2:
                            score += (
                                coverage
                                * 85.0
                            )

                # Expected extension/type confidence.
                if expected_exts:
                    if extension in expected_exts:
                        score += 25.0
                    else:
                        score -= 35.0

                # Final-size confidence is very strong for old history rows.
                if expected_size > 0:
                    try:
                        actual_size = os.path.getsize(
                            path
                        )
                    except Exception:
                        actual_size = 0

                    if actual_size > 0:
                        difference = abs(
                            actual_size
                            - expected_size
                        )

                        ratio = difference / max(
                            actual_size,
                            expected_size,
                            1,
                        )

                        if ratio <= 0.01:
                            score += 65.0
                        elif ratio <= 0.03:
                            score += 55.0
                        elif ratio <= 0.07:
                            score += 35.0
                        elif ratio <= 0.15:
                            score += 15.0
                        else:
                            score -= 25.0

                if score <= 0:
                    continue

                candidates.append(
                    (
                        score,
                        path,
                    )
                )

    except Exception:
        return None

    if not candidates:
        return None

    candidates.sort(
        key=lambda item: item[
            0
        ],
        reverse=True,
    )

    best_score, best_path = candidates[
        0
    ]

    second_score = (
        candidates[
            1
        ][
            0
        ]
        if len(
            candidates
        ) > 1
        else -999.0
    )

    # Strong enough + sufficiently separated from second-best.
    # Exact/substring title + matching size normally lands around 170–215.
    if best_score < 115.0:
        return None

    if (
        len(
            candidates
        ) > 1
        and (
            best_score
            - second_score
        ) < 18.0
        and best_score < 180.0
    ):
        # Ambiguous: safer to ask the user instead of deleting wrong media.
        return None

    return best_path


def _find_download_file_for_row(item_id):
    """
    V32.38:
    1) Valid exact path wins.
    2) Stale/missing exact path -> automatically repair from Downloads.
    3) If no strong automatic match exists, retain the legacy fallback.

    Any successful repair is persisted immediately.
    """
    exact = _exact_path_for_row(
        item_id
    )

    if (
        exact
        and os.path.isfile(
            exact
        )
    ):
        return exact

    repaired = _smart_find_download_file_for_row(
        item_id
    )

    if repaired:
        _persist_relinked_row_path(
            item_id,
            repaired,
        )
        return repaired

    # Legacy fallback remains useful for very old rows with no size metadata.
    fallback = _legacy_find_download_file_for_row(
        item_id
    )

    if (
        fallback
        and os.path.isfile(
            fallback
        )
    ):
        _persist_relinked_row_path(
            item_id,
            fallback,
        )
        return fallback

    return None


def _legacy_find_download_file_for_row(item_id):
    """
    Best-effort finished-file lookup by visible title.
    Cache/temp files are deliberately ignored.
    """
    values = _row_values(item_id)

    if len(values) < 2:
        return None

    title = _safe_filename_key(values[1])

    if not title or not os.path.isdir(DOWNLOADS):
        return None

    candidates = []

    ignored_exts = {
        ".part",
        ".tmp",
        ".ytdl",
        ".m3u8",
        ".json",
    }

    try:
        for root_dir, dirs, files in os.walk(DOWNLOADS):
            # Never offer files from the Turbo cache.
            dirs[:] = [
                directory
                for directory in dirs
                if directory != "_video_cache"
            ]

            for filename in files:
                path = os.path.join(
                    root_dir,
                    filename,
                )

                extension = os.path.splitext(
                    filename
                )[1].lower()

                if extension in ignored_exts:
                    continue

                stem = _safe_filename_key(
                    os.path.splitext(filename)[0]
                )

                if not stem:
                    continue

                score = 0

                if stem == title:
                    score = 100
                elif title in stem:
                    score = 85
                elif stem in title:
                    score = 70
                else:
                    title_words = set(
                        title.split()
                    )
                    stem_words = set(
                        stem.split()
                    )

                    common = len(
                        title_words & stem_words
                    )

                    if common >= 2:
                        score = common * 10

                if score:
                    try:
                        modified = os.path.getmtime(
                            path
                        )
                    except Exception:
                        modified = 0

                    candidates.append(
                        (
                            score,
                            modified,
                            path,
                        )
                    )

    except Exception:
        return None

    if not candidates:
        return None

    candidates.sort(
        reverse=True
    )

    return candidates[0][2]



# ------------------------------------------------------------
# V32.11 — Professional file actions
# ------------------------------------------------------------

def _move_file_to_recycle_bin(path):
    """
    Move one existing file to the Windows Recycle Bin.
    No extra Python package is required.
    """
    if os.name != "nt" or not path or not os.path.isfile(path):
        return False, "File not found."

    FO_DELETE = 3
    FOF_SILENT = 0x0004
    FOF_NOCONFIRMATION = 0x0010
    FOF_ALLOWUNDO = 0x0040
    FOF_NOERRORUI = 0x0400

    class SHFILEOPSTRUCTW(ctypes.Structure):
        _fields_ = [
            ("hwnd", ctypes.c_void_p),
            ("wFunc", ctypes.c_uint),
            ("pFrom", ctypes.c_wchar_p),
            ("pTo", ctypes.c_wchar_p),
            ("fFlags", ctypes.c_ushort),
            ("fAnyOperationsAborted", ctypes.c_int),
            ("hNameMappings", ctypes.c_void_p),
            ("lpszProgressTitle", ctypes.c_wchar_p),
        ]

    # SHFileOperation expects a double-NUL terminated string.
    source = str(path) + "\0\0"

    operation = SHFILEOPSTRUCTW()
    operation.hwnd = None
    operation.wFunc = FO_DELETE
    operation.pFrom = source
    operation.pTo = None
    operation.fFlags = (
        FOF_SILENT
        | FOF_NOCONFIRMATION
        | FOF_ALLOWUNDO
        | FOF_NOERRORUI
    )
    operation.fAnyOperationsAborted = 0
    operation.hNameMappings = None
    operation.lpszProgressTitle = None

    try:
        result = ctypes.windll.shell32.SHFileOperationW(
            ctypes.byref(operation)
        )

        if result == 0 and not operation.fAnyOperationsAborted:
            return True, ""

        if operation.fAnyOperationsAborted:
            return False, "Operation cancelled."

        return False, f"Windows error code: {result}"

    except Exception as exc:
        return False, str(exc)



def _parse_human_size(value):
    text_value = str(
        value or ""
    ).strip()

    match = re.search(
        r"([0-9]+(?:\.[0-9]+)?)\s*(B|KiB|MiB|GiB|TiB|KB|MB|GB)",
        text_value,
        flags=re.IGNORECASE,
    )

    if not match:
        return 0

    number = float(
        match.group(1)
    )
    unit = match.group(2).lower()

    multipliers = {
        "b": 1,
        "kib": 1024,
        "mib": 1024 ** 2,
        "gib": 1024 ** 3,
        "tib": 1024 ** 4,
        "kb": 1000,
        "mb": 1000 ** 2,
        "gb": 1000 ** 3,
    }

    return int(
        number
        * multipliers.get(
            unit,
            1,
        )
    )


def relink_legacy_history_files():
    """
    Best-effort migration for pre-V32.21 Done rows.

    A legacy row is linked only when its displayed final size points to one
    unambiguous media file (or a very strong title+size match).
    """
    try:
        media_files = []

        for root_dir, dirs, files in os.walk(
            DOWNLOADS
        ):
            dirs[:] = [
                directory
                for directory in dirs
                if directory != "_video_cache"
            ]

            for filename in files:
                extension = os.path.splitext(
                    filename
                )[1].lower()

                if extension not in _FINAL_MEDIA_EXTENSIONS:
                    continue

                path = os.path.join(
                    root_dir,
                    filename,
                )

                try:
                    media_files.append(
                        (
                            path,
                            os.path.getsize(path),
                        )
                    )
                except Exception:
                    pass

        already_claimed = {
            os.path.normcase(
                os.path.abspath(path)
            )
            for path in row_file_paths.values()
            if path
        }

        linked = 0

        for item_id in bulk_tree.get_children():
            existing_path = row_file_paths.get(
                item_id
            )

            if (
                existing_path
                and os.path.isfile(
                    _normalize_output_path(
                        existing_path
                    )
                )
            ):
                continue

            values = _row_values(
                item_id
            )

            if len(values) < 9:
                continue

            if not _mini_is_terminal_status(
                str(values[8])
            ):
                continue

            expected_size = _parse_human_size(
                values[7]
            )

            if expected_size <= 0:
                continue

            tolerance = max(
                192 * 1024,
                int(
                    expected_size * 0.018
                ),
            )

            candidates = []

            for path, real_size in media_files:
                normalized = os.path.normcase(
                    os.path.abspath(path)
                )

                if normalized in already_claimed:
                    continue

                if abs(
                    real_size
                    - expected_size
                ) <= tolerance:
                    candidates.append(
                        (
                            path,
                            real_size,
                            _filename_similarity_score(
                                path,
                                values[1],
                            ),
                        )
                    )

            chosen = None

            if len(candidates) == 1:
                chosen = candidates[0][0]

            elif candidates:
                candidates.sort(
                    key=lambda item: (
                        item[2],
                        -abs(
                            item[1]
                            - expected_size
                        ),
                    ),
                    reverse=True,
                )

                if candidates[0][2] >= 24:
                    chosen = candidates[0][0]

            if chosen:
                row_file_paths[
                    item_id
                ] = chosen

                already_claimed.add(
                    os.path.normcase(
                        os.path.abspath(
                            chosen
                        )
                    )
                )

                final_title = _display_title_from_final_path(
                    chosen
                )

                if final_title:
                    bulk_tree.set(
                        item_id,
                        "title",
                        final_title,
                    )

                linked += 1

        if linked:
            schedule_download_history_save(
                100
            )
            log(
                f"🔗 Relinked {linked} legacy history row(s) "
                f"to exact downloaded files."
            )

    except Exception as exc:
        log(
            f"Legacy file relink warning: {exc}"
        )


def context_copy_full_path():
    item_id = _selected_download_item()
    path = _find_download_file_for_row(item_id)

    if not path:
        messagebox.showinfo(
            "Copy full path",
            "الملف النهائي ما لقيتوش دابا.",
        )
        return

    try:
        root.clipboard_clear()
        root.clipboard_append(path)
        root.update_idletasks()
    except Exception:
        pass



def _delete_choice_dialog(parent, filename, has_real_file):
    """
    Professional 3-way delete dialog.
    Returns: "list", "file", or "cancel".
    """
    result = {"value": "cancel"}

    dialog = tk.Toplevel(parent)
    dialog.title(tr("Delete download"))
    dialog.resizable(False, False)
    dialog.transient(parent)
    dialog.grab_set()
    dialog.configure(bg="#ffffff")

    try:
        if os.path.isfile(BRAND_ICON_ICO):
            dialog.iconbitmap(BRAND_ICON_ICO)
    except Exception:
        pass

    outer = tk.Frame(
        dialog,
        bg="#ffffff",
        padx=18,
        pady=16,
    )
    outer.pack(fill="both", expand=True)

    tk.Label(
        outer,
        text=tr("Delete selected download"),
        font=("Segoe UI", 11, "bold"),
        fg="#172033",
        bg="#ffffff",
        anchor="w",
    ).pack(fill="x")

    shown_name = filename or "Selected download"
    if len(shown_name) > 70:
        shown_name = shown_name[:67] + "…"

    tk.Label(
        outer,
        text=shown_name,
        font=("Segoe UI", 9),
        fg="#4f5d73",
        bg="#ffffff",
        anchor="w",
        justify="left",
        wraplength=460,
    ).pack(fill="x", pady=(5, 12))

    tk.Label(
        outer,
        text=tr("What do you want to delete?"),
        font=("Segoe UI", 9, "bold"),
        fg="#172033",
        bg="#ffffff",
        anchor="w",
    ).pack(fill="x", pady=(0, 10))

    buttons = tk.Frame(outer, bg="#ffffff")
    buttons.pack(fill="x")

    def choose(value):
        result["value"] = value
        dialog.destroy()

    list_btn = tk.Button(
        buttons,
        text=tr("Remove from list only"),
        command=lambda: choose("list"),
        font=("Segoe UI", 8, "bold"),
        padx=10,
        pady=6,
        relief="solid",
        bd=1,
        bg="#eef2f7",
        fg="#172033",
        activebackground="#dfe7f1",
    )
    list_btn.pack(side="left")

    file_btn = tk.Button(
        buttons,
        text=tr("Delete file + list"),
        command=lambda: choose("file"),
        font=("Segoe UI", 8, "bold"),
        padx=10,
        pady=6,
        relief="solid",
        bd=1,
        bg="#f7e7e7",
        fg="#8d1c1c",
        activebackground="#efd2d2",
        state=("normal" if has_real_file else "disabled"),
    )
    file_btn.pack(side="left", padx=(8, 0))

    tk.Button(
        buttons,
        text=tr("Cancel"),
        command=lambda: choose("cancel"),
        font=("Segoe UI", 8),
        padx=10,
        pady=6,
        relief="solid",
        bd=1,
        bg="#ffffff",
        fg="#172033",
        activebackground="#f2f2f2",
    ).pack(side="right")

    if not has_real_file:
        tk.Label(
            outer,
            text=tr("The real file was not found. File deletion is unavailable."),
            font=("Segoe UI", 8),
            fg="#8a5a00",
            bg="#ffffff",
            anchor="w",
            justify="left",
        ).pack(fill="x", pady=(10, 0))

    dialog.update_idletasks()

    width = max(520, dialog.winfo_reqwidth())
    height = dialog.winfo_reqheight()

    try:
        px = parent.winfo_rootx()
        py = parent.winfo_rooty()
        pw = parent.winfo_width()
        ph = parent.winfo_height()

        x = px + max(0, (pw - width) // 2)
        y = py + max(0, (ph - height) // 2)
        dialog.geometry(f"{width}x{height}+{x}+{y}")
    except Exception:
        pass

    dialog.protocol(
        "WM_DELETE_WINDOW",
        lambda: choose("cancel"),
    )

    dialog.wait_window()
    return result["value"]


def delete_selected_with_keyboard(event=None):
    """
    DELETE key:
      - List only
      - File + list (Recycle Bin)
      - Cancel
    """
    item_id = _selected_download_item()

    if not item_id:
        return "break"

    values = _row_values(item_id)
    status = (
        str(values[8])
        if len(values) >= 9
        else ""
    )

    if not _mini_is_terminal_status(status):
        messagebox.showinfo(
            "Delete download",
            "هاد التحميل مازال خدام. دير Cancel/Stop قبل Delete.",
        )
        return "break"

    real_file = _find_download_file_for_row(item_id)
    filename = (
        os.path.basename(real_file)
        if real_file
        else (
            str(values[1])
            if len(values) >= 2
            else "Selected download"
        )
    )

    choice = _delete_choice_dialog(
        root,
        filename,
        bool(real_file),
    )

    if choice == "list":
        try:
            bulk_tree.delete(item_id)
            schedule_download_history_save(50)
        except Exception:
            pass

    elif choice == "file":
        # Reuse the same safe Recycle Bin flow as the context menu.
        context_delete_file_from_pc()

    return "break"


def context_delete_file_from_pc():
    """
    Delete action from context menu.
    With multiple selected rows, reuse the professional bulk-delete flow.
    """
    selected_items = _selected_download_items()

    if len(selected_items) > 1:
        delete_selected_files_from_pc()
        return

    item_id = _selected_download_item()

    if not item_id:
        return

    values = _row_values(item_id)
    status = (
        str(values[8])
        if len(values) >= 9
        else ""
    )

    if not _mini_is_terminal_status(status):
        messagebox.showinfo(
            tr("Delete download"),
            tr("This download is still active. Stop or cancel it before deleting."),
        )
        return

    path = _find_download_file_for_row(item_id)

    if not path:
        messagebox.showinfo(
            "Delete file",
            "Z²SE ما لقا حتى ملف نهائي مربوط بهاد السطر.",
        )
        return

    filename = os.path.basename(path)

    confirmed = messagebox.askyesno(
        "Delete file from PC",
        "غادي يتحيد الملف من الدوسي ويتحط فـ Recycle Bin:\n\n"
        f"{filename}\n\n"
        "وغادي يتحيد حتى السطر من لائحة Z²SE.\n\n"
        "واش نكمل؟",
        icon="warning",
    )

    if not confirmed:
        return

    ok, error = _move_file_to_recycle_bin(path)

    if not ok:
        messagebox.showerror(
            "Delete file",
            f"ما قدرناش نحيدو الملف:\n\n{error}",
        )
        return

    try:
        row_file_paths.pop(
            item_id,
            None,
        )
        bulk_tree.delete(item_id)
        schedule_download_history_save(50)
    except Exception:
        pass


def context_open_file():
    item_id = _selected_download_item()
    path = _find_download_file_for_row(
        item_id
    )

    if not path:
        messagebox.showinfo(
            "Open file",
            "الملف النهائي ما لقيتوش دابا. إلا كان التحميل مازال خدام، خليو يسالي.",
        )
        return

    try:
        os.startfile(path)
    except Exception as exc:
        messagebox.showerror(
            "Open file",
            str(exc),
        )


def context_show_in_folder():
    item_id = _selected_download_item()
    path = _find_download_file_for_row(
        item_id
    )

    try:
        if path and os.name == "nt":
            subprocess.Popen(
                [
                    "explorer.exe",
                    "/select,",
                    path,
                ]
            )
        else:
            os.startfile(DOWNLOADS)

    except Exception:
        try:
            os.startfile(DOWNLOADS)
        except Exception:
            pass


def context_copy_name():
    item_id = _selected_download_item()
    values = _row_values(item_id)

    if len(values) < 2:
        return

    try:
        root.clipboard_clear()
        root.clipboard_append(
            str(values[1])
        )
        root.update_idletasks()
    except Exception:
        pass


def context_remove_from_list():
    item_id = _selected_download_item()

    if not item_id:
        return

    values = _row_values(item_id)
    status = (
        str(values[8])
        if len(values) >= 9
        else ""
    )

    if not _mini_is_terminal_status(status):
        messagebox.showinfo(
            "Remove",
            "هاد التحميل مازال خدام. دير Cancel/Stop قبل ما تحيدو من اللائحة.",
        )
        return

    try:
        bulk_tree.delete(item_id)
        schedule_download_history_save(50)
    except Exception:
        pass


def context_properties():
    item_id = _selected_download_item()
    values = _row_values(item_id)

    if len(values) < 9:
        return

    path = _find_download_file_for_row(
        item_id
    )

    details = (
        f"File / Video: {values[1]}\n"
        f"Type: {values[2]}\n"
        f"Mode: {values[3]}\n"
        f"Progress: {values[4]}\n"
        f"Transfer rate: {values[5]}\n"
        f"Time left: {values[6]}\n"
        f"Size: {values[7]}\n"
        f"Status: {values[8]}\n\n"
        f"Folder: {DOWNLOADS}"
    )

    if path:
        details += f"\nFull path: {path}"

    messagebox.showinfo(
        "Download Properties",
        details,
    )


download_context_menu = tk.Menu(
    root,
    tearoff=0,
)

download_context_menu.add_command(
    label=tr("Open file"),
    command=open_selected_file,
)
download_context_menu.add_command(
    label=tr("Show in folder"),
    command=context_show_in_folder,
)
download_context_menu.add_command(
    label=_mtr("merge_selected"),
    command=merge_selected_videos,
)
MERGE_CONTEXT_MENU_INDEX = download_context_menu.index("end")
download_context_menu.add_separator()

download_context_menu.add_command(
    label=tr("Pause selected"),
    command=pause_selected_downloads,
)
download_context_menu.add_command(
    label=tr("Resume selected"),
    command=resume_selected_downloads,
)
download_context_menu.add_command(
    label=tr("Cancel selected"),
    command=cancel_selected_downloads,
)
download_context_menu.add_separator()

download_context_menu.add_command(
    label=tr("Select all"),
    command=select_all_download_rows,
)
download_context_menu.add_command(
    label=tr("Deselect all"),
    command=deselect_all_download_rows,
)
download_context_menu.add_separator()

download_context_menu.add_command(
    label=tr("Copy file name(s)"),
    command=copy_selected_names,
)
download_context_menu.add_command(
    label=tr("Copy full path(s)"),
    command=copy_selected_paths,
)
download_context_menu.add_command(
    label=tr("Properties"),
    command=context_properties,
)
download_context_menu.add_separator()

download_context_menu.add_command(
    label=tr("Remove selected from list (keep files)"),
    command=remove_selected_from_list,
)
download_context_menu.add_command(
    label=tr("Delete selected file(s) from PC (Recycle Bin)"),
    command=delete_selected_files_from_pc,
)


def show_download_context_menu(event):
    item_id = bulk_tree.identify_row(
        event.y
    )

    if not item_id:
        return

    # Professional Windows behavior:
    # right-clicking an already selected row PRESERVES the multi-selection.
    # right-clicking a non-selected row selects only that row.
    current_selection = set(
        _selected_download_items()
    )

    if item_id not in current_selection:
        bulk_tree.selection_set(item_id)

    bulk_tree.focus(item_id)

    items = _selected_download_items()
    job_indices = _selected_job_indices()

    statuses = [
        _item_status(item)
        for item in items
    ]

    all_terminal = bool(items) and all(
        _mini_is_terminal_status(status)
        for status in statuses
    )

    active_indices = []

    for index in job_indices:
        mapped = bulk_tree_ids.get(index)

        if (
            mapped
            and not _mini_is_terminal_status(
                _item_status(mapped)
            )
        ):
            active_indices.append(index)

    any_paused = False
    any_unpaused_active = False

    with paused_job_lock:
        for index in active_indices:
            if index in paused_job_indices:
                any_paused = True
            else:
                any_unpaused_active = True

    real_files = [
        _find_download_file_for_row(item)
        for item in items
    ]
    real_files = [
        path
        for path in real_files
        if path
    ]

    try:
        download_context_menu.entryconfigure(
            "Open file",
            state=(
                "normal"
                if len(items) == 1 and bool(real_files)
                else "disabled"
            ),
        )

        download_context_menu.entryconfigure(
            "Show in folder",
            state=(
                "normal"
                if len(items) == 1 and bool(real_files)
                else "disabled"
            ),
        )

        download_context_menu.entryconfigure(
            MERGE_CONTEXT_MENU_INDEX,
            state=(
                "normal"
                if (
                    all_terminal
                    and len(
                        items
                    )
                    >= 2
                )
                else "disabled"
            ),
        )

        download_context_menu.entryconfigure(
            "Pause selected",
            state=(
                "normal"
                if any_unpaused_active
                else "disabled"
            ),
        )

        download_context_menu.entryconfigure(
            "Resume selected",
            state=(
                "normal"
                if any_paused
                else "disabled"
            ),
        )

        download_context_menu.entryconfigure(
            "Cancel selected",
            state=(
                "normal"
                if bool(active_indices)
                else "disabled"
            ),
        )

        download_context_menu.entryconfigure(
            "Deselect all",
            state=(
                "normal"
                if bool(items)
                else "disabled"
            ),
        )

        download_context_menu.entryconfigure(
            "Copy file name(s)",
            state=(
                "normal"
                if bool(items)
                else "disabled"
            ),
        )

        download_context_menu.entryconfigure(
            "Copy full path(s)",
            state=(
                "normal"
                if bool(real_files)
                else "disabled"
            ),
        )

        download_context_menu.entryconfigure(
            "Properties",
            state=(
                "normal"
                if len(items) == 1
                else "disabled"
            ),
        )

        download_context_menu.entryconfigure(
            "Remove selected from list (keep files)",
            state=(
                "normal"
                if all_terminal
                else "disabled"
            ),
        )

        download_context_menu.entryconfigure(
            "Delete selected file(s) from PC (Recycle Bin)",
            state=(
                "normal"
                if all_terminal and bool(real_files)
                else "disabled"
            ),
        )

    except Exception:
        pass

    try:
        download_context_menu.tk_popup(
            event.x_root,
            event.y_root,
        )
    finally:
        try:
            download_context_menu.grab_release()
        except Exception:
            pass


def open_download_on_double_click(event=None):
    open_selected_file()



def refresh_selected_rows_counter(event=None):
    try:
        count = len(
            bulk_tree.selection()
        )

        selected_rows_var.set(
            f"{count} selected"
            if count
            else ""
        )
    except Exception:
        pass


bulk_tree.bind(
    "<<TreeviewSelect>>",
    refresh_selected_rows_counter,
    add="+",
)


# ------------------------------------------------------------
# V32.19 — WINDOWS-STYLE MARQUEE + TRUE MOUSE MULTI-SELECTION
# ------------------------------------------------------------

mouse_select_anchor = None
mouse_select_dragging = False
mouse_select_original = set()
mouse_select_last_item = None
mouse_drag_start_screen = None

# Visible Windows-style selection rectangle.
marquee_fill = None
marquee_edges = []
marquee_visible = False


def _tree_children():
    try:
        return list(
            bulk_tree.get_children()
        )
    except Exception:
        return []


def _nearest_tree_row(y):
    item_id = bulk_tree.identify_row(y)

    if item_id:
        return item_id

    children = _tree_children()

    if not children:
        return None

    visible = []

    for child in children:
        try:
            bbox = bulk_tree.bbox(child)

            if bbox:
                visible.append(
                    (child, bbox[1], bbox[1] + bbox[3])
                )
        except Exception:
            pass

    if not visible:
        return children[0]

    visible.sort(
        key=lambda value: value[1]
    )

    first_item, first_top, _ = visible[0]
    last_item, _, last_bottom = visible[-1]

    if y <= first_top:
        return first_item

    if y >= last_bottom:
        return last_item

    return min(
        visible,
        key=lambda value: abs(
            y - ((value[1] + value[2]) / 2.0)
        ),
    )[0]


def _mouse_range_items(anchor_item, current_item):
    children = _tree_children()

    if not anchor_item or not current_item:
        return []

    try:
        a = children.index(anchor_item)
        b = children.index(current_item)
    except ValueError:
        return []

    lo = min(a, b)
    hi = max(a, b)

    return children[lo:hi + 1]


def _mouse_apply_range(anchor_item, current_item, additive=False):
    range_items = _mouse_range_items(
        anchor_item,
        current_item,
    )

    if not range_items:
        return

    if additive:
        selected = set(
            mouse_select_original
        )
        selected.update(
            range_items
        )

        bulk_tree.selection_set(
            tuple(selected)
        )
    else:
        bulk_tree.selection_set(
            tuple(range_items)
        )

    bulk_tree.focus(
        current_item
    )
    bulk_tree.see(
        current_item
    )


def _mouse_drag_autoscroll(event):
    height = max(
        1,
        bulk_tree.winfo_height()
    )

    margin = 30

    if event.y < margin:
        bulk_tree.yview_scroll(
            -1,
            "units",
        )
    elif event.y > height - margin:
        bulk_tree.yview_scroll(
            1,
            "units",
        )


def _marquee_make_clickthrough(window):
    """
    Make overlay windows ignore mouse input so they never interrupt dragging.
    Windows-only; silently no-op elsewhere.
    """
    if os.name != "nt":
        return

    try:
        window.update_idletasks()
        hwnd = int(window.winfo_id())

        GWL_EXSTYLE = -20
        WS_EX_TRANSPARENT = 0x00000020
        WS_EX_TOOLWINDOW = 0x00000080
        WS_EX_NOACTIVATE = 0x08000000

        user32 = ctypes.windll.user32

        get_style = getattr(
            user32,
            "GetWindowLongPtrW",
            user32.GetWindowLongW,
        )
        set_style = getattr(
            user32,
            "SetWindowLongPtrW",
            user32.SetWindowLongW,
        )

        style = get_style(
            hwnd,
            GWL_EXSTYLE,
        )

        set_style(
            hwnd,
            GWL_EXSTYLE,
            style
            | WS_EX_TRANSPARENT
            | WS_EX_TOOLWINDOW
            | WS_EX_NOACTIVATE,
        )
    except Exception:
        pass


def _ensure_marquee_windows():
    global marquee_fill
    global marquee_edges

    if marquee_fill is not None:
        return

    # Semi-transparent blue fill, similar to Windows Explorer/Desktop.
    marquee_fill = tk.Toplevel(root)
    marquee_fill.withdraw()
    marquee_fill.overrideredirect(True)
    marquee_fill.configure(bg="#5aa9ff")

    try:
        marquee_fill.attributes("-alpha", 0.18)
        marquee_fill.attributes("-topmost", True)
    except Exception:
        pass

    _marquee_make_clickthrough(
        marquee_fill
    )

    # Separate crisp blue border strips.
    marquee_edges = []

    for _ in range(4):
        edge = tk.Toplevel(root)
        edge.withdraw()
        edge.overrideredirect(True)
        edge.configure(bg="#0078d7")

        try:
            edge.attributes("-topmost", True)
        except Exception:
            pass

        _marquee_make_clickthrough(edge)
        marquee_edges.append(edge)


def _hide_marquee():
    global marquee_visible

    marquee_visible = False

    if marquee_fill is not None:
        try:
            marquee_fill.withdraw()
        except Exception:
            pass

    for edge in marquee_edges:
        try:
            edge.withdraw()
        except Exception:
            pass


def _show_marquee(start_x, start_y, current_x, current_y):
    """
    Draw the blue rectangle clipped to the Downloads Treeview.
    Coordinates are screen/global coordinates.
    """
    global marquee_visible

    try:
        tree_left = bulk_tree.winfo_rootx()
        tree_top = bulk_tree.winfo_rooty()
        tree_right = tree_left + bulk_tree.winfo_width()
        tree_bottom = tree_top + bulk_tree.winfo_height()

        x1 = max(
            tree_left,
            min(start_x, current_x),
        )
        y1 = max(
            tree_top,
            min(start_y, current_y),
        )
        x2 = min(
            tree_right,
            max(start_x, current_x),
        )
        y2 = min(
            tree_bottom,
            max(start_y, current_y),
        )

        width = max(
            1,
            x2 - x1,
        )
        height = max(
            1,
            y2 - y1,
        )

        # Do not flash a rectangle for a normal simple click.
        if width < 4 and height < 4:
            _hide_marquee()
            return

        _ensure_marquee_windows()

        marquee_fill.geometry(
            f"{width}x{height}+{x1}+{y1}"
        )
        marquee_fill.deiconify()
        marquee_fill.lift()

        border = 2

        geometries = (
            # top
            (width, border, x1, y1),
            # bottom
            (
                width,
                border,
                x1,
                max(y1, y2 - border),
            ),
            # left
            (border, height, x1, y1),
            # right
            (
                border,
                height,
                max(x1, x2 - border),
                y1,
            ),
        )

        for edge, (
            edge_w,
            edge_h,
            edge_x,
            edge_y,
        ) in zip(
            marquee_edges,
            geometries,
        ):
            edge.geometry(
                f"{max(1, edge_w)}x{max(1, edge_h)}"
                f"+{edge_x}+{edge_y}"
            )
            edge.deiconify()
            edge.lift()

        marquee_visible = True

    except Exception:
        pass


def bulk_mouse_select_press(event):
    """
    Desktop/Explorer-style selection:
      click row        = one row
      drag row->row    = select range + visible blue rectangle
      drag blank->rows = select range + visible blue rectangle
      Ctrl+click       = toggle
      Ctrl+drag        = add range
      Shift+click      = range

    IMPORTANT: mouse press explicitly gives keyboard focus to the Treeview,
    fixing Ctrl+A / Delete immediately after mouse selection.
    """
    global mouse_select_anchor
    global mouse_select_dragging
    global mouse_select_original
    global mouse_select_last_item
    global mouse_drag_start_screen

    _hide_marquee()

    try:
        bulk_tree.focus_set()
    except Exception:
        pass

    mouse_drag_start_screen = (
        event.x_root,
        event.y_root,
    )

    region = bulk_tree.identify_region(
        event.x,
        event.y,
    )

    if region in ("heading", "separator"):
        mouse_select_anchor = None
        mouse_select_dragging = False
        mouse_drag_start_screen = None
        return None

    children = _tree_children()

    if not children:
        return "break"

    item_id = _nearest_tree_row(
        event.y
    )

    if not item_id:
        return "break"

    current_selection = set(
        bulk_tree.selection()
    )
    mouse_select_original = set(
        current_selection
    )

    ctrl_down = bool(
        event.state & 0x0004
    )
    shift_down = bool(
        event.state & 0x0001
    )

    actual_row = bulk_tree.identify_row(
        event.y
    )
    started_in_blank = not bool(
        actual_row
    )

    if shift_down:
        anchor = (
            bulk_tree.focus()
            or mouse_select_last_item
            or item_id
        )

        mouse_select_anchor = anchor

        _mouse_apply_range(
            anchor,
            item_id,
            additive=ctrl_down,
        )

    elif ctrl_down and not started_in_blank:
        mouse_select_anchor = item_id

        if item_id in current_selection:
            bulk_tree.selection_remove(
                item_id
            )
        else:
            bulk_tree.selection_add(
                item_id
            )

        bulk_tree.focus(
            item_id
        )

    else:
        mouse_select_anchor = item_id

        if started_in_blank:
            bulk_tree.selection_remove(
                bulk_tree.selection()
            )
        else:
            bulk_tree.selection_set(
                item_id
            )
            bulk_tree.focus(
                item_id
            )

    mouse_select_last_item = item_id
    mouse_select_dragging = False

    return "break"


def bulk_mouse_select_motion(event):
    global mouse_select_dragging
    global mouse_select_last_item

    if not mouse_select_anchor:
        return "break"

    _mouse_drag_autoscroll(
        event
    )

    current_item = _nearest_tree_row(
        event.y
    )

    if not current_item:
        return "break"

    if (
        current_item != mouse_select_anchor
        or (
            mouse_drag_start_screen
            and (
                abs(
                    event.x_root
                    - mouse_drag_start_screen[0]
                ) > 3
                or abs(
                    event.y_root
                    - mouse_drag_start_screen[1]
                ) > 3
            )
        )
    ):
        mouse_select_dragging = True

    ctrl_down = bool(
        event.state & 0x0004
    )

    _mouse_apply_range(
        mouse_select_anchor,
        current_item,
        additive=ctrl_down,
    )

    mouse_select_last_item = current_item

    if (
        mouse_drag_start_screen
        and mouse_select_dragging
    ):
        _show_marquee(
            mouse_drag_start_screen[0],
            mouse_drag_start_screen[1],
            event.x_root,
            event.y_root,
        )

    return "break"


def bulk_mouse_select_release(event):
    global mouse_select_anchor
    global mouse_select_dragging
    global mouse_select_original
    global mouse_drag_start_screen

    _hide_marquee()

    mouse_select_anchor = None
    mouse_select_dragging = False
    mouse_select_original = set()
    mouse_drag_start_screen = None

    # Keep keyboard focus here so Delete / Ctrl+A work immediately.
    try:
        bulk_tree.focus_set()
    except Exception:
        pass

    return "break"


Z2SE_MOUSE_BINDTAG = "Z2SE_DownloadList_MouseSelect"

try:
    tags = list(
        bulk_tree.bindtags()
    )

    if Z2SE_MOUSE_BINDTAG in tags:
        tags.remove(
            Z2SE_MOUSE_BINDTAG
        )

    tags.insert(
        0,
        Z2SE_MOUSE_BINDTAG,
    )

    bulk_tree.bindtags(
        tuple(tags)
    )
except Exception:
    pass

bulk_tree.bind_class(
    Z2SE_MOUSE_BINDTAG,
    "<ButtonPress-1>",
    bulk_mouse_select_press,
)
bulk_tree.bind_class(
    Z2SE_MOUSE_BINDTAG,
    "<B1-Motion>",
    bulk_mouse_select_motion,
)
bulk_tree.bind_class(
    Z2SE_MOUSE_BINDTAG,
    "<ButtonRelease-1>",
    bulk_mouse_select_release,
)


bulk_tree.bind(
    "<Button-3>",
    show_download_context_menu,
)
bulk_tree.bind(
    "<Double-1>",
    open_download_on_double_click,
)

bulk_tree.bind(
    "<Delete>",
    delete_selected_with_keyboard_v15,
)

bulk_tree.bind(
    "<Control-a>",
    select_all_download_rows,
)
bulk_tree.bind(
    "<Control-A>",
    select_all_download_rows,
)
bulk_tree.bind(
    "<Control-Shift-a>",
    deselect_all_download_rows,
)
bulk_tree.bind(
    "<Control-Shift-A>",
    deselect_all_download_rows,
)
bulk_tree.bind(
    "<Return>",
    lambda event: (
        open_selected_file(),
        "break",
    )[1],
)


def _focus_is_text_editor():
    try:
        widget = root.focus_get()

        if widget is None:
            return False

        klass = str(
            widget.winfo_class()
        ).lower()

        return klass in {
            "entry",
            "tentry",
            "text",
            "spinbox",
            "tspinbox",
            "combobox",
            "tcombobox",
        }
    except Exception:
        return False


def global_downloads_ctrl_a(event):
    # Never steal Ctrl+A from URL/time/text fields.
    if _focus_is_text_editor():
        return None

    try:
        if bulk_tree.get_children():
            bulk_tree.focus_set()
            return select_all_download_rows(
                event
            )
    except Exception:
        pass

    return None


def global_downloads_delete(event):
    # Never steal Delete while editing a URL/time/text field.
    if _focus_is_text_editor():
        return None

    try:
        if bulk_tree.selection():
            bulk_tree.focus_set()
            return delete_selected_with_keyboard_v15(
                event
            )
    except Exception:
        pass

    return None


# App-level fallback. The Treeview's own bindings still take priority when it
# has focus; these catch the exact case where mouse selection left keyboard
# focus elsewhere.
root.bind_all(
    "<Control-a>",
    global_downloads_ctrl_a,
    add="+",
)
root.bind_all(
    "<Control-A>",
    global_downloads_ctrl_a,
    add="+",
)
root.bind_all(
    "<Delete>",
    global_downloads_delete,
    add="+",
)


# ------------------------------------------------------------
# Bottom progress / status area
# ------------------------------------------------------------

bottom_bar = tk.Frame(list_card, bg=UI_PANEL)
bottom_bar.pack(fill="x", padx=8, pady=(6, 8))

bulk_progress = ttk.Progressbar(
    bottom_bar,
    variable=bulk_progress_var,
    maximum=100,
    style="Z2SE.Horizontal.TProgressbar",
)
bulk_progress.pack(fill="x", padx=4, pady=(5, 7))

bottom_status = tk.Frame(bottom_bar, bg=UI_PANEL)
bottom_status.pack(fill="x", padx=4)

tk.Label(
    bottom_status,
    textvariable=status_var,
    font=("Segoe UI", 8),
    fg=UI_MUTED,
    bg=UI_PANEL,
).pack(side="left")

tk.Label(
    bottom_status,
    text="PO Token  ●",
    font=("Segoe UI", 8),
    fg=UI_SUCCESS,
    bg=UI_PANEL,
).pack(side="right", padx=(10, 0))

tk.Label(
    bottom_status,
    text="Bridge  ●",
    font=("Segoe UI", 8),
    fg=UI_SUCCESS,
    bg=UI_PANEL,
).pack(side="right", padx=(10, 0))

tk.Label(
    bottom_status,
    text="Tray  ●",
    font=("Segoe UI", 8),
    fg=UI_SUCCESS,
    bg=UI_PANEL,
).pack(side="right", padx=(10, 0))


# ------------------------------------------------------------
# Log is still available, but hidden by default
# ------------------------------------------------------------

log_panel = tk.Frame(
    main,
    bg=UI_PANEL,
    highlightthickness=1,
    highlightbackground=UI_BORDER,
)

log_header = tk.Frame(log_panel, bg=UI_PANEL)
log_header.pack(fill="x", padx=10, pady=(6, 3))

tk.Label(
    log_header,
    text=tr("TECHNICAL LOG"),
    font=("Segoe UI", 8, "bold"),
    fg=UI_MUTED,
    bg=UI_PANEL,
).pack(side="left")

ttk.Button(
    log_header,
    text=tr("Clear"),
    command=clear_log,
    style="Toolbar.TButton",
).pack(side="right")

log_box = tk.Text(
    log_panel,
    height=7,
    state="disabled",
    font=("Consolas", 8),
    bg="#0b1220",
    fg="#d7e2f0",
    relief="flat",
)
log_box.pack(fill="x", padx=8, pady=(0, 8))

_log_visible = False

def toggle_log():
    global _log_visible

    if _log_visible:
        log_panel.pack_forget()
        _log_visible = False
        log_toggle_button.configure(text=tr("Show Log"))
    else:
        log_panel.pack(fill="x", padx=10, pady=(0, 10))
        _log_visible = True
        log_toggle_button.configure(text=tr("Hide Log"))


log_toggle_button = ttk.Button(
    bottom_status,
    text=tr("Show Log"),
    command=toggle_log,
    style="Toolbar.TButton",
)
log_toggle_button.pack(
    side="right",
    padx=(10, 0),
)


# ============================================================
# V32.2 — IDM-LIKE MINI DOWNLOAD PANEL
# ============================================================

mini_title_var = tk.StringVar(value="Preparing download…")
mini_status_var = tk.StringVar(value="Starting…")
mini_speed_var = tk.StringVar(value="—")
mini_eta_var = tk.StringVar(value="—")
mini_size_var = tk.StringVar(value="—")
mini_counter_var = tk.StringVar(value="")
mini_progress_var = tk.DoubleVar(value=0.0)
mini_percent_var = tk.StringVar(value="0.0%")


def _mini_is_terminal_status(status):
    """
    V32.33: language-independent terminal-state check.

    Tree rows may display:
      Terminé ✅ / Done ✅ / مكتمل ✅ / سالا ✅
    but delete/progress logic must reason from the canonical state.
    """
    return canonical_status(status) in {
        "Done ✅",
        "Error",
        "Stopped",
        "Interrupted",
        "Saved",
    }


def _mini_active_tree_rows():
    rows = []

    try:
        for item_id in bulk_tree.get_children():
            values = list(
                bulk_tree.item(
                    item_id,
                    "values",
                )
            )

            if len(values) < 9:
                continue

            status = str(values[8] or "")
            progress_text = str(values[4] or "0")

            try:
                progress_value = float(
                    progress_text.replace("%", "").strip()
                )
            except Exception:
                progress_value = 0.0

            # During a running session, terminal historic rows must be ignored.
            if not _mini_is_terminal_status(status) and progress_value < 100.0:
                rows.append(values)

    except Exception:
        pass

    return rows


def _mini_snapshot():
    """
    Read current GUI state only. No downloader-engine changes.
    Returns title/status/progress/speed/eta/size/counter.
    """
    if single_running:
        progress = max(
            0.0,
            min(
                100.0,
                float(single_progress_var.get() or 0.0),
            )
        )

        stats = str(single_stats_var.get() or "")
        parts = [
            part.strip()
            for part in stats.split("|")
            if part.strip()
        ]

        speed = "—"
        eta = "—"
        size = "—"

        for part in parts:
            lower = part.lower()

            if "/s" in lower:
                speed = part
            elif lower.startswith("eta "):
                eta = part[4:].strip() or "—"
            elif (
                "mib" in lower
                or "gib" in lower
                or "kib" in lower
                or "mb" in lower
                or "gb" in lower
            ):
                size = part

        title = single_url_var.get().strip() or "Video download"

        try:
            host = urlparse(title).hostname
            if host:
                title = host
        except Exception:
            pass

        return {
            "title": title,
            "status": str(status_var.get() or "Downloading…"),
            "progress": progress,
            "speed": speed,
            "eta": eta,
            "size": size,
            "counter": "1 download",
        }

    active_rows = _mini_active_tree_rows()

    # Prefer an actually transferring row over a merely Waiting row.
    selected = None

    for row in active_rows:
        status = str(row[8] or "").lower()

        if "waiting" not in status and "queued" not in status:
            selected = row
            break

    if selected is None and active_rows:
        selected = active_rows[0]

    try:
        progress = max(
            0.0,
            min(
                100.0,
                float(bulk_progress_var.get() or 0.0),
            )
        )
    except Exception:
        progress = 0.0

    if selected is not None:
        title = str(selected[1] or "Download")
        speed = str(selected[5] or "—")
        eta = str(selected[6] or "—")
        size = str(selected[7] or "—")
        row_status = str(selected[8] or "Downloading…")
    else:
        title = "Z²SE downloads"
        speed = "—"
        eta = "—"
        size = "—"
        row_status = str(status_var.get() or "Downloading…")

    if len(title) > 58:
        title = title[:55] + "…"

    active_count = len(active_rows)

    if browser_queue_active:
        counter = (
            f"{browser_jobs_done}/{browser_jobs_total} completed"
        )

        if browser_active_jobs:
            counter += f" • {browser_active_jobs} active"

    elif bulk_running:
        counter = str(bulk_counter_var.get() or "")

        if active_count:
            counter += f" • {active_count} active"

    else:
        counter = str(bulk_counter_var.get() or "")

    return {
        "title": title,
        "status": row_status,
        "progress": progress,
        "speed": speed,
        "eta": eta,
        "size": size,
        "counter": counter,
    }


def _mini_place_bottom_right():
    if mini_panel is None:
        return

    try:
        mini_panel.update_idletasks()

        width = 500
        height = 208

        screen_width = mini_panel.winfo_screenwidth()
        screen_height = mini_panel.winfo_screenheight()

        x = max(
            10,
            screen_width - width - 22,
        )
        y = max(
            10,
            screen_height - height - 72,
        )

        mini_panel.geometry(
            f"{width}x{height}+{x}+{y}"
        )

    except Exception:
        pass


def mini_open_main():
    global mini_panel_user_opened_main

    # V32.6: do not hide/transform the mini window.
    # Just open the full manager beside it, like IDM.
    mini_panel_user_opened_main = True
    _show_app_window()


def mini_hide_only():
    """Hide only; used internally. It does NOT cancel downloads."""
    global mini_panel_user_hidden

    mini_panel_user_hidden = True

    try:
        if mini_panel is not None:
            mini_panel.withdraw()
    except Exception:
        pass


def mini_close_and_cancel():
    """
    Minimize (_) => progress stays available from its tray icon.
    Close (X)    => cancel active transfer(s) and remove mini progress UI.
    """
    try:
        if downloads_are_running():
            try:
                mini_status_var.set("Cancelling…")
            except Exception:
                pass

            stop_all()
            log(
                "✕ Mini download window closed — "
                "active download(s) cancelled."
            )
    except Exception as exc:
        log(f"Mini close/cancel warning: {exc}")

    _cleanup_mini_progress_ui()


def mini_cancel_downloads():
    try:
        mini_status_var.set(
            "Cancelling…"
        )
    except Exception:
        pass

    stop_all()
    _cleanup_mini_progress_ui()


def mini_stop_all():
    # Backward-compatible alias.
    mini_cancel_downloads()


def mini_panel_begin(hide_main=False):
    """
    V32.9:
    Start/update the progress session without popping the small window.
    The dedicated Download Progress tray icon is the entry point.
    """
    global mini_panel_session
    global mini_panel_user_opened_main
    global mini_panel_user_hidden
    global mini_panel_in_tray
    global mini_panel_completion_after

    if app_quitting:
        return

    mini_panel_session += 1
    session = mini_panel_session
    mini_panel_user_opened_main = False

    # V32.12: a new download shows the small progress window immediately.
    # It moves to its dedicated tray icon only if the user presses Minimize.
    mini_panel_user_hidden = False
    mini_panel_in_tray = False

    try:
        if mini_panel_completion_after is not None:
            root.after_cancel(
                mini_panel_completion_after
            )
    except Exception:
        pass

    mini_panel_completion_after = None

    if hide_main:
        try:
            root.withdraw()
        except Exception:
            pass

    try:
        if mini_panel is not None:
            mini_panel.deiconify()
            mini_panel.state("normal")
            _mini_place_bottom_right()
            mini_panel.lift()
            mini_panel.attributes("-topmost", True)

            # Bring it forward for the new job, then let Windows handle z-order.
            mini_panel.after(
                900,
                lambda: mini_panel.attributes("-topmost", False),
            )
    except Exception:
        pass

    # No progress tray icon yet. It is created only after Minimize.
    _mini_refresh(session)


def _mini_hide_after_finish(session):
    global mini_panel_completion_after

    mini_panel_completion_after = None

    if session != mini_panel_session:
        return

    if downloads_are_running():
        return

    # V32.10: no active job => remove all temporary progress UI.
    _cleanup_mini_progress_ui()


def _mini_refresh(session):
    global mini_panel_completion_after

    if app_quitting:
        return

    if session != mini_panel_session:
        return

    try:
        snap = _mini_snapshot()

        mini_title_var.set(
            snap["title"]
        )
        if pause_all_event.is_set():
            mini_status_var.set(
                "Paused ⏸"
            )
        else:
            mini_status_var.set(
                snap["status"]
            )
        mini_speed_var.set(
            snap["speed"] or "—"
        )
        mini_eta_var.set(
            snap["eta"] or "—"
        )
        mini_size_var.set(
            snap["size"] or "—"
        )
        mini_counter_var.set(
            snap["counter"] or ""
        )

        progress = max(
            0.0,
            min(
                100.0,
                float(snap["progress"]),
            )
        )

        mini_progress_var.set(progress)
        mini_percent_var.set(
            f"{progress:.1f}%"
        )

    except Exception:
        pass

    _refresh_pause_controls()

    if downloads_are_running():
        # V32.7:
        # Respect the Windows minimize button. When state == "iconic",
        # NEVER deiconify/lift it here; the download keeps running quietly.
        if (
            not mini_panel_user_hidden
            and not mini_panel_in_tray
        ):
            try:
                if mini_panel is not None:
                    state = str(mini_panel.state()).lower()

                    if state == "normal":
                        mini_panel.lift()
            except Exception:
                pass

        root.after(
            300,
            lambda: _mini_refresh(session),
        )
        return

    # Session completed. Keep a small "Done" panel briefly, then disappear.
    try:
        mini_progress_var.set(100.0)
        mini_percent_var.set("100%")
        mini_status_var.set("Completed ✅")
        mini_counter_var.set("Download session finished")
        mini_speed_var.set("—")
        mini_eta_var.set("00:00")
    except Exception:
        pass

    if mini_panel_completion_after is None:
        mini_panel_completion_after = root.after(
            900,
            lambda: _mini_hide_after_finish(
                session
            ),
        )


# ------------------------------------------------------------
# Build the compact panel once.
# ------------------------------------------------------------

mini_panel = tk.Toplevel(root)
mini_panel.withdraw()
mini_panel.title("Z²SE — Download Progress")
mini_panel.resizable(False, False)
mini_panel.configure(bg="#ffffff")
mini_panel.attributes("-topmost", True)

try:
    if os.path.isfile(BRAND_ICON_ICO):
        mini_panel.iconbitmap(
            BRAND_ICON_ICO
        )
except Exception:
    pass

# V32.7:
# Windows Minimize keeps downloading.
# Windows Close (X) cancels active downloads and closes this mini window.
mini_panel.protocol(
    "WM_DELETE_WINDOW",
    mini_close_and_cancel,
)

# Detect the Windows minimize button on this independent window.
mini_panel.bind(
    "<Unmap>",
    on_window_unmap,
    add="+",
)

mini_outer = tk.Frame(
    mini_panel,
    bg="#ffffff",
    highlightthickness=1,
    highlightbackground="#cfd6e2",
)
mini_outer.pack(
    fill="both",
    expand=True,
)

mini_header = tk.Frame(
    mini_outer,
    bg="#10294a",
    height=38,
)
mini_header.pack(
    fill="x",
)
mini_header.pack_propagate(False)

mini_header_left = tk.Frame(
    mini_header,
    bg="#10294a",
)
mini_header_left.pack(
    side="left",
    fill="y",
    padx=(11, 5),
)

mini_logo_photo = None

try:
    if (
        Image is not None
        and ImageTk is not None
        and os.path.isfile(BRAND_ICON_PNG)
    ):
        _mini_logo = Image.open(
            BRAND_ICON_PNG
        ).convert("RGBA").resize(
            (23, 23),
            Image.Resampling.LANCZOS,
        )

        mini_logo_photo = ImageTk.PhotoImage(
            _mini_logo
        )

        tk.Label(
            mini_header_left,
            image=mini_logo_photo,
            bg="#10294a",
            bd=0,
        ).pack(
            side="left",
            pady=7,
        )
except Exception:
    mini_logo_photo = None

tk.Label(
    mini_header_left,
    text="Z²SE Download",
    font=("Segoe UI", 10, "bold"),
    fg="#ffffff",
    bg="#10294a",
).pack(
    side="left",
    padx=(7, 0),
    pady=7,
)

tk.Label(
    mini_header,
    textvariable=mini_percent_var,
    font=("Segoe UI", 10, "bold"),
    fg="#ffffff",
    bg="#10294a",
).pack(
    side="right",
    padx=(6, 12),
)

mini_body = tk.Frame(
    mini_outer,
    bg="#ffffff",
)
mini_body.pack(
    fill="both",
    expand=True,
    padx=13,
    pady=(9, 8),
)

tk.Label(
    mini_body,
    textvariable=mini_title_var,
    font=("Segoe UI", 9, "bold"),
    fg="#172033",
    bg="#ffffff",
    anchor="w",
).pack(
    fill="x",
)

mini_progress = ttk.Progressbar(
    mini_body,
    variable=mini_progress_var,
    maximum=100,
    style="Z2SE.Horizontal.TProgressbar",
)
mini_progress.pack(
    fill="x",
    pady=(8, 5),
)

tk.Label(
    mini_body,
    textvariable=mini_status_var,
    font=("Segoe UI", 8),
    fg="#526077",
    bg="#ffffff",
    anchor="w",
).pack(
    fill="x",
)

mini_stats = tk.Frame(
    mini_body,
    bg="#ffffff",
)
mini_stats.pack(
    fill="x",
    pady=(5, 5),
)

for label, variable in (
    ("Speed", mini_speed_var),
    ("ETA", mini_eta_var),
    ("Size", mini_size_var),
):
    cell = tk.Frame(
        mini_stats,
        bg="#ffffff",
    )
    cell.pack(
        side="left",
        padx=(0, 18),
    )

    tk.Label(
        cell,
        text=label,
        font=("Segoe UI", 7),
        fg="#8791a2",
        bg="#ffffff",
    ).pack(
        anchor="w",
    )

    tk.Label(
        cell,
        textvariable=variable,
        font=("Segoe UI", 8, "bold"),
        fg="#25324a",
        bg="#ffffff",
    ).pack(
        anchor="w",
    )

mini_footer = tk.Frame(
    mini_body,
    bg="#ffffff",
)
mini_footer.pack(
    fill="x",
    pady=(1, 0),
)

tk.Label(
    mini_footer,
    textvariable=mini_counter_var,
    font=("Segoe UI", 7),
    fg="#7a8495",
    bg="#ffffff",
).pack(
    side="left",
)

# Explicit tk.Button styling is intentional here:
# on some Windows ttk themes the compact footer button captions could render
# blank/clipped. These controls stay readable regardless of the active theme.
mini_open_button = tk.Button(
    mini_footer,
    text=tr("Main Window"),
    command=mini_open_main,
    font=("Segoe UI", 8, "bold"),
    bg="#eef2f7",
    fg="#172033",
    activebackground="#dfe7f1",
    activeforeground="#172033",
    relief="solid",
    bd=1,
    padx=10,
    pady=4,
    cursor="hand2",
)
mini_open_button.pack(
    side="right",
    padx=(6, 0),
)

mini_cancel_button = tk.Button(
    mini_footer,
    text=tr("Cancel Download"),
    command=mini_cancel_downloads,
    font=("Segoe UI", 8, "bold"),
    bg="#f7e7e7",
    fg="#8d1c1c",
    activebackground="#efd2d2",
    activeforeground="#6f1414",
    relief="solid",
    bd=1,
    padx=10,
    pady=4,
    cursor="hand2",
)
mini_cancel_button.pack(
    side="right",
    padx=(6, 0),
)

mini_resume_button = tk.Button(
    mini_footer,
    text=tr("Resume"),
    command=resume_all_downloads,
    font=("Segoe UI", 8, "bold"),
    bg="#e8f2ea",
    fg="#176c36",
    activebackground="#d7eadc",
    activeforeground="#12582c",
    relief="solid",
    bd=1,
    padx=10,
    pady=4,
    cursor="hand2",
    state="disabled",
)
mini_resume_button.pack(
    side="right",
    padx=(6, 0),
)

mini_pause_button = tk.Button(
    mini_footer,
    text=tr("Pause"),
    command=pause_all_downloads,
    font=("Segoe UI", 8, "bold"),
    bg="#eef2f7",
    fg="#172033",
    activebackground="#dfe7f1",
    activeforeground="#172033",
    relief="solid",
    bd=1,
    padx=10,
    pady=4,
    cursor="hand2",
    state="disabled",
)
mini_pause_button.pack(
    side="right",
)

_mini_place_bottom_right()
_refresh_pause_controls()


# ============================================================
# WINDOW / TRAY BEHAVIOR
# ============================================================

root.protocol("WM_DELETE_WINDOW", on_window_close)
root.bind("<Unmap>", on_window_unmap)

# ============================================================
# START
# ============================================================

# Restore previous finished/error/interrupted rows before background services.
load_download_history()

# V32.21: upgrade older history rows to exact file links whenever the match
# is unambiguous.
relink_legacy_history_files()

# If Chrome woke Z²SE, do not flash the large window first.
# The mini panel will appear automatically as soon as the download job arrives.
if BROWSER_LAUNCH_MODE:
    try:
        root.withdraw()
    except Exception:
        pass

threading.Thread(
    target=start_system_tray,
    daemon=True,
).start()

# V32.10: Download Progress tray icon exists only while a
# download/paused session is active.
threading.Thread(
    target=start_browser_bridge,
    daemon=True,
).start()

threading.Thread(
    target=startup_checks,
    daemon=True,
).start()

# Normal manual startup keeps the historical tray behavior.
# Browser-triggered startup is already hidden and waits for the mini panel.
if TRAY_AVAILABLE and not BROWSER_LAUNCH_MODE:
    root.after(1500, hide_to_tray)

# V32.28 — one quiet GitHub Releases check after startup.
# If owner/repo is not configured yet, this simply does nothing.
schedule_z2se_auto_update_check()

root.mainloop()
