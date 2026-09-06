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


version = sys.argv[1].strip()
if version != "32.40":
    raise SystemExit(f"This patch is for 32.40, got {version}")

payload = Path("payload")
app_path = payload / "app.py"
updater_path = payload / "z2se_updater.pyw"

text = app_path.read_text(encoding="utf-8")

# Version bump.
text = text.replace('APP_VERSION = "32.39"', 'APP_VERSION = "32.40"', 1)
text = text.replace(
    'log(f"Z²SE V{APP_VERSION} GITHUB AUTO UPDATE starting system checks...")',
    'log(f"Z²SE V{APP_VERSION} MANUAL UPDATE MENU starting system checks...")',
    1,
)

# Localized Tools menu label.
marker = "LEGACY_UI_ALIASES = "
idx = text.find(marker)
if idx < 0:
    raise SystemExit("Translation marker not found")
extra = '''TRANSLATIONS.update({\n    "Check updates now": {\n        "fr": "Rechercher les mises à jour maintenant",\n        "en": "Check for updates now",\n        "ar": "البحث عن التحديثات الآن",\n        "darija": "قلب على التحديثات دابا",\n    },\n})\n\n'''
text = text[:idx] + extra + text[idx:]

# Allow a manual click to install immediately while still showing
# the normal "already up to date" message when nothing is available.
old = '''def check_z2se_app_update(\n    manual=False,\n    force=False,\n):'''
new = '''def check_z2se_app_update(\n    manual=False,\n    force=False,\n    auto_confirm=False,\n):'''
if old not in text:
    raise SystemExit("Update-check signature not found")
text = text.replace(old, new, 1)

old = '''        if (\n            manual\n            or not auto_install\n        ):'''
new = '''        if (\n            (manual and not auto_confirm)\n            or not auto_install\n        ):'''
if old not in text:
    raise SystemExit("Update confirmation block not found")
text = text.replace(old, new, 1)

old = '''def manual_z2se_update():\n    threading.Thread(\n        target=check_z2se_app_update,\n        kwargs={\n            "manual": True,\n            "force": True,\n        },\n        daemon=True,\n    ).start()\n'''
new = '''def manual_z2se_update():\n    """One-click update check from the Tools menu."""\n    threading.Thread(\n        target=check_z2se_app_update,\n        kwargs={\n            "manual": True,\n            "force": True,\n            "auto_confirm": True,\n        },\n        daemon=True,\n    ).start()\n'''
if old not in text:
    raise SystemExit("manual_z2se_update block not found")
text = text.replace(old, new, 1)

old = '''tools_menu.add_separator()\ntools_menu.add_command(\n    label=tr("Update download engine"),\n    command=manual_update,\n)'''
new = '''tools_menu.add_separator()\ntools_menu.add_command(\n    label=tr("Check updates now"),\n    command=manual_z2se_update,\n)\ntools_menu.add_separator()\ntools_menu.add_command(\n    label=tr("Update download engine"),\n    command=manual_update,\n)'''
if old not in text:
    raise SystemExit("Tools menu insertion point not found")
text = text.replace(old, new, 1)

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

print(f"Prepared Z2SE v{version}")
