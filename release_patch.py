from pathlib import Path
import hashlib
import json
import os
import re
import sys

TARGET_VERSION = "32.50"


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
# V32.50 — BGUTIL 2.0.0 SECURITY UPDATE / LOCALHOST HARDENING
# ----------------------------------------------------------------------
text, count = re.subn(
    r'APP_VERSION\s*=\s*"32\.49"',
    'APP_VERSION = "32.50"',
    text,
    count=1,
)
if count != 1:
    raise RuntimeError("Could not update APP_VERSION 32.49 -> 32.50")

constants_anchor = 'POT_PING_URL = "http://127.0.0.1:4416/ping"\n'
constants_replacement = constants_anchor + '''\n# V32.50 — security-pinned bgutil provider. 2.0.0 fixes GHSA-qpv9-8xfj-xx9m.\nPOT_REQUIRED_VERSION = "2.0.0"\nPOT_REQUIRED_COMMIT = "37169ee2656e08c5c2e5dc9df4c598c0cb4c88a8"\nPOT_PLUGIN_SHA256 = "bce874dfa25896c2798e0f4f8147b7b22e785479eb1e459ab232bf2506c95016"\nPOT_PLUGIN_URL = (\n    "https://github.com/Brainicism/bgutil-ytdlp-pot-provider/releases/download/"\n    + POT_REQUIRED_VERSION\n    + "/bgutil-ytdlp-pot-provider.zip"\n)\nPOT_SOURCE_URL = (\n    "https://github.com/Brainicism/bgutil-ytdlp-pot-provider/archive/"\n    + POT_REQUIRED_COMMIT\n    + ".zip"\n)\nPOT_SERVER_ROOT = os.path.join(USERPROFILE, "bgutil-ytdlp-pot-provider")\nPOT_VERSION_MARKER = os.path.join(POT_SERVER_ROOT, ".z2se_provider_version")\n'''
if constants_anchor not in text:
    raise RuntimeError("POT constants anchor missing")
text = text.replace(constants_anchor, constants_replacement, 1)

start = text.find("def pot_ping():")
end_marker = "# ============================================================\n# YT-DLP UPDATE\n# ============================================================"
end = text.find(end_marker, start)
if start < 0 or end < 0:
    raise RuntimeError("Could not locate PO Token provider block")

new_pot_block = r'''def _pot_file_sha256(path):
    try:
        digest = hashlib.sha256()
        with open(path, "rb") as handle:
            for chunk in iter(lambda: handle.read(1024 * 1024), b""):
                digest.update(chunk)
        return digest.hexdigest().lower()
    except Exception:
        return ""


def _pot_server_version():
    package_json = os.path.join(POT_SERVER_ROOT, "server", "package.json")
    try:
        with open(package_json, "r", encoding="utf-8") as handle:
            data = json.load(handle)
        return str(data.get("version") or "").strip()
    except Exception:
        return ""


def _pot_security_current():
    """Require both official v2 plugin bytes and the v2 server tree."""
    if _pot_server_version() != POT_REQUIRED_VERSION:
        return False
    if _pot_file_sha256(POT_PLUGIN) != POT_PLUGIN_SHA256:
        return False
    try:
        with open(POT_VERSION_MARKER, "r", encoding="utf-8") as handle:
            marker = handle.read().strip()
        return marker == (POT_REQUIRED_VERSION + " " + POT_REQUIRED_COMMIT)
    except Exception:
        return False


def _download_pot_file(url, destination, expected_sha256=""):
    temp_path = destination + ".tmp"
    os.makedirs(os.path.dirname(destination), exist_ok=True)
    try:
        request = urllib.request.Request(
            url,
            headers={"User-Agent": "Z2SE-Media-Downloader/" + APP_VERSION},
        )
        with urllib.request.urlopen(request, timeout=45) as response, open(temp_path, "wb") as handle:
            while True:
                chunk = response.read(1024 * 1024)
                if not chunk:
                    break
                handle.write(chunk)
        if expected_sha256:
            actual = _pot_file_sha256(temp_path)
            if actual != expected_sha256.lower():
                raise RuntimeError("PO Token provider SHA-256 verification failed")
        os.replace(temp_path, destination)
    finally:
        try:
            if os.path.exists(temp_path):
                os.remove(temp_path)
        except Exception:
            pass


def _stop_pot_server_process():
    """Best effort: stop the old process bound to the provider's dedicated port."""
    global pot_ready
    pot_ready = False
    if os.name != "nt":
        return
    try:
        script = (
            "$c=Get-NetTCPConnection -LocalPort 4416 -State Listen -ErrorAction SilentlyContinue; "
            "if($c){$c|Select-Object -ExpandProperty OwningProcess -Unique|ForEach-Object{"
            "Stop-Process -Id $_ -Force -ErrorAction SilentlyContinue}}"
        )
        subprocess.run(
            ["powershell.exe", "-NoProfile", "-NonInteractive", "-Command", script],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            timeout=12,
            creationflags=subprocess.CREATE_NO_WINDOW,
        )
        time.sleep(0.5)
    except Exception:
        pass


def _install_secure_pot_provider():
    """Install the official bgutil 2.0.0 plugin + server with rollback."""
    if _pot_security_current():
        return True

    log("🔐 PO Token security update: installing bgutil 2.0.0...")
    set_pot_status("PO Token: security update...")

    deno = shutil.which("deno")
    if not deno:
        log("PO Token security update needs Deno.")
        return False

    parent = os.path.dirname(POT_SERVER_ROOT)
    staging_root = os.path.join(parent, "bgutil-ytdlp-pot-provider.z2se-new")
    backup_root = os.path.join(parent, "bgutil-ytdlp-pot-provider.z2se-backup")
    source_zip = os.path.join(parent, "bgutil-ytdlp-pot-provider-2.0.0.z2se.zip")
    plugin_new = POT_PLUGIN + ".z2se-new"

    try:
        _stop_pot_server_process()
        for path in (staging_root, backup_root):
            if os.path.isdir(path):
                shutil.rmtree(path, ignore_errors=True)
        for path in (source_zip, plugin_new):
            try:
                if os.path.exists(path):
                    os.remove(path)
            except Exception:
                pass

        # Plugin release asset is pinned to the upstream-published SHA-256.
        _download_pot_file(POT_PLUGIN_URL, plugin_new, POT_PLUGIN_SHA256)
        # Server source is pinned to the exact upstream 2.0.0 commit.
        _download_pot_file(POT_SOURCE_URL, source_zip)

        extract_parent = staging_root + ".extract"
        if os.path.isdir(extract_parent):
            shutil.rmtree(extract_parent, ignore_errors=True)
        os.makedirs(extract_parent, exist_ok=True)
        with zipfile.ZipFile(source_zip, "r") as archive:
            archive.extractall(extract_parent)
        roots = [
            os.path.join(extract_parent, name)
            for name in os.listdir(extract_parent)
            if os.path.isdir(os.path.join(extract_parent, name))
        ]
        if len(roots) != 1:
            raise RuntimeError("Unexpected PO Token source archive layout")
        shutil.move(roots[0], staging_root)
        shutil.rmtree(extract_parent, ignore_errors=True)

        package_json = os.path.join(staging_root, "server", "package.json")
        with open(package_json, "r", encoding="utf-8") as handle:
            package = json.load(handle)
        if str(package.get("version") or "") != POT_REQUIRED_VERSION:
            raise RuntimeError("Unexpected PO Token server version")

        # Install the dependencies required by this exact server version.
        result = subprocess.run(
            [deno, "install", "--allow-scripts=npm:canvas", "--frozen"],
            cwd=os.path.join(staging_root, "server"),
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=300,
            creationflags=(subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0),
        )
        if result.returncode != 0:
            raise RuntimeError("Deno dependency install failed: " + (result.stdout or "")[-800:])

        if os.path.isdir(POT_SERVER_ROOT):
            os.replace(POT_SERVER_ROOT, backup_root)
        os.replace(staging_root, POT_SERVER_ROOT)
        os.makedirs(os.path.dirname(POT_PLUGIN), exist_ok=True)
        os.replace(plugin_new, POT_PLUGIN)
        with open(POT_VERSION_MARKER, "w", encoding="utf-8") as handle:
            handle.write(POT_REQUIRED_VERSION + " " + POT_REQUIRED_COMMIT + "\n")

        shutil.rmtree(backup_root, ignore_errors=True)
        try:
            os.remove(source_zip)
        except Exception:
            pass
        log("🔐 PO Token provider updated to secure bgutil 2.0.0 ✅")
        return True

    except Exception as exc:
        log("PO Token security update ERROR: " + str(exc))
        try:
            if os.path.isdir(POT_SERVER_ROOT):
                shutil.rmtree(POT_SERVER_ROOT, ignore_errors=True)
            if os.path.isdir(backup_root):
                os.replace(backup_root, POT_SERVER_ROOT)
        except Exception:
            pass
        for path in (staging_root, staging_root + ".extract"):
            shutil.rmtree(path, ignore_errors=True)
        return False
    finally:
        for path in (source_zip, plugin_new):
            try:
                if os.path.exists(path):
                    os.remove(path)
            except Exception:
                pass


def pot_ping():
    try:
        with urllib.request.urlopen(POT_PING_URL, timeout=1) as response:
            return 200 <= response.status < 300
    except Exception:
        return False


def ensure_pot_fast():
    """Fast path immediately before downloads; never trust an outdated provider."""
    if pot_ready and _pot_security_current():
        return True
    return check_and_start_pot()


def check_and_start_pot():
    global pot_ready

    with pot_lock:
        # Security gate comes BEFORE ping: a live pre-2.0 server must never be
        # accepted merely because /ping responds.
        if not _pot_security_current():
            if not _install_secure_pot_provider():
                pot_ready = False
                set_pot_status("PO Token: SECURITY UPDATE REQUIRED")
                return False

        if pot_ping():
            pot_ready = True
            set_pot_status("PO Token: ACTIVE ✅ • v2.0.0 secure")
            return True

        if not os.path.exists(POT_PLUGIN) or not os.path.exists(POT_SERVER_FILE):
            pot_ready = False
            set_pot_status("PO Token: secure components missing")
            return False

        deno = shutil.which("deno")
        if not deno:
            pot_ready = False
            set_pot_status("PO Token: Deno missing")
            return False

        if not os.path.isdir(POT_WORKDIR):
            pot_ready = False
            set_pot_status("PO Token: workdir missing")
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
                    "--host",
                    "127.0.0.1",
                ],
                cwd=POT_WORKDIR,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                creationflags=creationflags,
                startupinfo=startupinfo,
            )

            for _ in range(20):
                if pot_ping():
                    pot_ready = True
                    set_pot_status("PO Token: ACTIVE ✅ • v2.0.0 secure")
                    log("PO Token provider v2.0.0 بدا وخدام على localhost فقط ✅")
                    return True
                time.sleep(0.7)
        except Exception as exc:
            log(f"PO Token ERROR: {exc}")

        pot_ready = False
        set_pot_status("PO Token: unavailable")
        return False


'''
text = text[:start] + new_pot_block + text[end:]

# Health Check: show the actual security/version state instead of mere file presence.
old_health = '''    pot_plugin_ok = os.path.isfile(POT_PLUGIN)\n    pot_server_ok = os.path.isfile(POT_SERVER_FILE) and os.path.isdir(POT_WORKDIR)\n    pot_live = pot_ping()\n'''
new_health = '''    pot_plugin_ok = os.path.isfile(POT_PLUGIN)\n    pot_server_ok = os.path.isfile(POT_SERVER_FILE) and os.path.isdir(POT_WORKDIR)\n    pot_secure = _pot_security_current()\n    pot_live = pot_ping() if pot_secure else False\n'''
if old_health not in text:
    raise RuntimeError("Health Check PO Token anchor missing")
text = text.replace(old_health, new_health, 1)

old_detail = '''                "Provider active"\n                if pot_live\n                else "Provider offline" if (pot_plugin_ok and pot_server_ok and deno)\n                else "Provider components incomplete"\n'''
new_detail = '''                "Provider active • bgutil 2.0.0 secure • localhost only"\n                if pot_live\n                else "Security update required" if not pot_secure\n                else "Provider offline" if (pot_plugin_ok and pot_server_ok and deno)\n                else "Provider components incomplete"\n'''
if old_detail not in text:
    raise RuntimeError("Health Check PO Token detail anchor missing")
text = text.replace(old_detail, new_detail, 1)

old_files_item = '''            "ok": bool(deno and pot_plugin_ok and pot_server_ok),\n            "detail": "Ready" if (deno and pot_plugin_ok and pot_server_ok) else "Missing component",\n'''
new_files_item = '''            "ok": bool(deno and pot_plugin_ok and pot_server_ok and pot_secure),\n            "detail": (\n                "Ready • bgutil 2.0.0 verified"\n                if (deno and pot_plugin_ok and pot_server_ok and pot_secure)\n                else "Security update required" if not pot_secure\n                else "Missing component"\n            ),\n'''
if old_files_item not in text:
    raise RuntimeError("Health Check provider-files anchor missing")
text = text.replace(old_files_item, new_files_item, 1)

app_path.write_text(text, encoding="utf-8")

# Update the payload manifest after patching.
manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
manifest["product"] = "Z2SE Media Downloader"
manifest["version"] = TARGET_VERSION
manifest["created_by"] = "GitHub Actions / v32.50 PO Token Security Hardening"
manifest["files"] = [
    {
        "path": "app.py",
        "sha256": sha256_file(app_path),
        "size": app_path.stat().st_size,
    },
    {
        "path": "z2se_updater.pyw",
        "sha256": sha256_file(updater_path),
        "size": updater_path.stat().st_size,
    },
]
manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")

print("Prepared Z2SE v32.50 security update")
print("app.py", app_path.stat().st_size, sha256_file(app_path))
print("z2se_updater.pyw", updater_path.stat().st_size, sha256_file(updater_path))
