"""Build the release from reviewed source, without patching a stale release."""
from pathlib import Path
import ast
import hashlib
import json
import sys

ROOT = Path(__file__).resolve().parent


def build(version, destination=Path("payload")):
    source = (ROOT / "current_app.py").read_text(encoding="utf-8")
    tree = ast.parse(source)
    versions = [node.value.value for node in tree.body
                if isinstance(node, ast.Assign) and isinstance(node.value, ast.Constant)
                and any(isinstance(t, ast.Name) and t.id == "APP_VERSION" for t in node.targets)]
    if versions != [version]:
        raise ValueError(f"Source version {versions} does not match requested {version}")
    runtime = (ROOT / "runtime_support.py").read_text(encoding="utf-8")
    if "# BEGIN EMBEDDED RUNTIME SUPPORT\n" + runtime not in source:
        raise ValueError("Embedded runtime differs from tested runtime_support.py")
    safety = (ROOT / "media_safety.py").read_text(encoding="utf-8")
    if "# BEGIN EMBEDDED MEDIA SAFETY\n" + safety not in source:
        raise ValueError("Embedded media safety differs from tested media_safety.py")
    updater = (ROOT / "source_z2se_updater.pyw").read_text(encoding="utf-8-sig")
    compile(updater, "z2se_updater.pyw", "exec")
    destination.mkdir(parents=True, exist_ok=True)
    files = []
    for name, content in (("app.py", source), ("z2se_updater.pyw", updater)):
        path = destination / name
        path.write_bytes(content.encode("utf-8"))
        files.append({"path": name, "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
                      "size": path.stat().st_size})
    manifest = {"product": "Z2SE Media Downloader", "version": version,
                "created_by": "Verified repository source", "files": files}
    (destination / "update_manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(f"Verified Z2SE {version}: app + updater + SHA-256 manifest")


if __name__ == "__main__":
    build(sys.argv[1])
