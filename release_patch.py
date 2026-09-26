from pathlib import Path
import ast
import hashlib
import json
import sys

version = sys.argv[1]
assert version == "33.01"
app_path = Path("payload/app.py")
text = app_path.read_text(encoding="utf-8-sig")

def replace_once(old, new):
    global text
    assert text.count(old) == 1, (old[:160], text.count(old))
    text = text.replace(old, new, 1)

replace_once('APP_VERSION = "33.00"', 'APP_VERSION = "33.01"')

# app.py imports os but not pathlib.Path.  Keep the preview self-contained by
# validating the extension with the module already available in the app.
replace_once(
    'if Path(normalized).suffix.lower() not in video_exts:',
    'if os.path.splitext(normalized)[1].lower() not in video_exts:',
)

ast.parse(text)
app_path.write_text(text, encoding="utf-8")

app_hash = hashlib.sha256(app_path.read_bytes()).hexdigest()
manifest_path = Path("payload/update_manifest.json")
manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
manifest["version"] = version
manifest["created_by"] = (
    "v33.01 fixes the embedded preview Path NameError exposed by v33.00 "
    "diagnostics and keeps stage-by-stage preview error reporting"
)
manifest["files"][0]["sha256"] = app_hash
manifest["files"][0]["size"] = app_path.stat().st_size
manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
print("VERIFIED v33.01 app.py sha256", app_hash)
