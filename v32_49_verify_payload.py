from pathlib import Path
import hashlib
import json
import re
import sys

# V32.49 integration verifier: this human-authored checkpoint also re-runs
# the real-payload workflow after any bot-assisted patch-anchor repair.
# Checkpoint 2 validates the generated duplicate-protection message syntax too.
payload = Path(sys.argv[1] if len(sys.argv) > 1 else "payload")
app = payload / "app.py"
updater = payload / "z2se_updater.pyw"
manifest_path = payload / "update_manifest.json"
for path in (app, updater, manifest_path):
    if not path.is_file():
        raise SystemExit(f"missing payload file: {path}")

text = app.read_text(encoding="utf-8-sig")
required = [
    'APP_VERSION = "32.49"',
    'PENDING_QUEUE_FILE',
    'DOWNLOAD_ARCHIVE_FILE',
    'def restore_pending_queue_to_editor():',
    'def open_playlist_pro():',
    'def copy_z2se_diagnostics():',
    'Smart Recovery clients: mweb+PO -> default -> web_safari',
    'saw_pot_problem=saw_pot_problem',
    'Duplicate Protection',
    'web_safari',
]
missing = [marker for marker in required if marker not in text]
if missing:
    raise SystemExit("missing app markers: " + repr(missing))

# Queue files must never contain obvious credential fields in their serializer.
helper_start = text.index("# V32.49 — PERSISTENT QUEUE + DUPLICATE / ARCHIVE PROTECTION")
helper_end = text.index("def collect_bulk_jobs():", helper_start)
helper = text[helper_start:helper_end]
for forbidden_assignment in ('"cookie":', '"cookies":', '"authorization":', '"password":', '"token":'):
    if forbidden_assignment in helper.lower():
        raise SystemExit(f"credential-like serialized field found: {forbidden_assignment}")

manifest = json.loads(manifest_path.read_text(encoding="utf-8-sig"))
if str(manifest.get("version")) != "32.49":
    raise SystemExit(f"bad manifest version: {manifest.get('version')!r}")
entries = {item.get("path"): item for item in manifest.get("files", []) if isinstance(item, dict)}
for name, path in (("app.py", app), ("z2se_updater.pyw", updater)):
    item = entries.get(name)
    if not item:
        raise SystemExit(f"manifest entry missing: {name}")
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    if item.get("sha256") != digest:
        raise SystemExit(f"manifest hash mismatch: {name}")
    if int(item.get("size", -1)) != path.stat().st_size:
        raise SystemExit(f"manifest size mismatch: {name}")

compile(text, str(app), "exec")
print("v32.49 payload verification OK")
print("app bytes:", app.stat().st_size)
print("manifest created_by:", manifest.get("created_by"))
