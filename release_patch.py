from pathlib import Path
import hashlib
import json
import re
import sys

TARGET_VERSION = "32.60"


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
# V32.60 — BGUTIL/DENO SELF-REPAIR + PART PROVIDER RECOVERY
# ----------------------------------------------------------------------
text, count = re.subn(
    r'APP_VERSION\s*=\s*"32\.59"',
    'APP_VERSION = "32.60"',
    text,
    count=1,
)
if count != 1:
    raise RuntimeError("Could not update APP_VERSION 32.59 -> 32.60")

# Replace the provider starter with a self-healing version.  The v32.59 user
# journal showed Deno resolving commander from package.json but refusing to run
# because node_modules was out of date.  Deno itself explicitly recommends
# `deno install` for this state.  Run that repair automatically once, then retry
# the same local provider.  No user shell/PowerShell action is required.
provider_pattern = re.compile(
    r'def check_and_start_pot\(\):\n.*?(?=\n# ============================================================\n# )',
    re.S,
)

provider_replacement = r'''def check_and_start_pot():
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

        # POT_WORKDIR historically points at server/node_modules because the
        # provider is launched as ../src/main.ts from there.  Dependency repair
        # must however run from the parent server directory where package.json
        # lives.
        provider_server_dir = (
            os.path.dirname(POT_WORKDIR)
            if os.path.basename(POT_WORKDIR).lower() == "node_modules"
            else POT_WORKDIR
        )

        if not os.path.isdir(provider_server_dir):
            pot_ready = False
            set_pot_status("PO Token: workdir missing")
            log(f"PO Token workdir غير موجود: {provider_server_dir}")
            return False

        def _launch_provider_once():
            creationflags = 0
            startupinfo = None

            if os.name == "nt":
                creationflags = getattr(subprocess, "CREATE_NO_WINDOW", 0)
                try:
                    startupinfo = subprocess.STARTUPINFO()
                    startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
                    startupinfo.wShowWindow = 0
                except Exception:
                    startupinfo = None

            try:
                # Keep the original launch layout when node_modules exists.
                launch_cwd = POT_WORKDIR if os.path.isdir(POT_WORKDIR) else provider_server_dir
                launch_script = "../src/main.ts" if launch_cwd == POT_WORKDIR else "src/main.ts"

                subprocess.Popen(
                    [
                        deno,
                        "run",
                        "--allow-net",
                        "--allow-ffi=.",
                        "--allow-read=.",
                        launch_script,
                    ],
                    cwd=launch_cwd,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    creationflags=creationflags,
                    startupinfo=startupinfo,
                )

                for _ in range(15):
                    if pot_ping():
                        return True
                    time.sleep(0.7)
            except Exception as exc:
                log(f"PO Token launch ERROR: {exc}")

            return False

        if _launch_provider_once():
            pot_ready = True
            set_pot_status("PO Token: ACTIVE ✅")
            log("PO Token provider بدا وخدام ✅")
            return True

        # V32.60: repair the exact Deno dependency state seen in the journal.
        # This is intentionally attempted only after a normal provider start
        # fails, so healthy starts remain fast.
        log("🩹 PO Token provider unavailable -> repairing Deno dependencies automatically...")
        try:
            repair = subprocess.run(
                [deno, "install"],
                cwd=provider_server_dir,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=120,
                creationflags=(getattr(subprocess, "CREATE_NO_WINDOW", 0) if os.name == "nt" else 0),
            )
            repair_output = str(repair.stdout or "").strip()
            if repair_output:
                # Keep the technical log useful without flooding it.
                tail = repair_output[-1600:]
                log("PO Token Deno repair: " + tail)

            if repair.returncode == 0:
                log("✅ PO Token Deno dependencies repaired; restarting provider...")
                if _launch_provider_once():
                    pot_ready = True
                    set_pot_status("PO Token: ACTIVE ✅")
                    log("✅ PO Token provider recovered automatically.")
                    return True
            else:
                log(f"PO Token Deno repair exited with code {repair.returncode}")
        except subprocess.TimeoutExpired:
            log("PO Token Deno repair timed out.")
        except Exception as exc:
            log(f"PO Token Deno repair ERROR: {exc}")

        pot_ready = False
        set_pot_status("PO Token: unavailable")
        return False
'''

text, provider_count = provider_pattern.subn(provider_replacement, text, count=1)
if provider_count != 1:
    raise RuntimeError("PO provider function anchor missing")

# PART v32.59 correctly tried a second YouTube profile after the first GVS 403,
# but the second attempt reached yt-dlp while the local provider was dead.  If a
# YouTube PART attempt fails and provider ping is down, heal/restart it before
# the loop moves to the next client profile.
part_failure = '''            log(\n                prefix\n                + "PART attempt failed. Code: "\n                + str(\n                    code\n                )\n            )\n'''
part_recovery = part_failure + '''\n            if is_youtube_page_url(url) and not pot_ping():\n                log(\n                    prefix\n                    + "🩹 PART recovery: PO provider is offline -> self-repair before next profile"\n                )\n                check_and_start_pot()\n'''

if part_failure not in text:
    raise RuntimeError("PART failure/recovery anchor missing")
text = text.replace(part_failure, part_recovery, 1)

app_path.write_text(text, encoding="utf-8")

manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
manifest["product"] = "Z2SE Media Downloader"
manifest["version"] = TARGET_VERSION
manifest["created_by"] = "GitHub Actions / v32.60 bgutil Deno self-repair + PART provider recovery"
manifest["files"] = [
    {"path": "app.py", "sha256": sha256_file(app_path), "size": app_path.stat().st_size},
    {"path": "z2se_updater.pyw", "sha256": sha256_file(updater_path), "size": updater_path.stat().st_size},
]
manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")

print("Prepared Z2SE v32.60 bgutil/Deno self-repair + PART recovery")
print("app.py", app_path.stat().st_size, sha256_file(app_path))
print("z2se_updater.pyw", updater_path.stat().st_size, sha256_file(updater_path))
