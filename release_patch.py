from pathlib import Path
import hashlib
import json
import os
import re
import sys

TARGET_VERSION = "32.48"


def replace_once(text, old, new, label):
    if old not in text:
        raise RuntimeError(f"Patch anchor missing: {label}")
    return text.replace(old, new, 1)


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

# Version bump.
text, count = re.subn(
    r'APP_VERSION\s*=\s*"32\.47"',
    'APP_VERSION = "32.48"',
    text,
    count=1,
)
if count != 1:
    raise RuntimeError("Could not update APP_VERSION 32.47 -> 32.48")

# ----------------------------------------------------------------------
# V32.48 — ENGINE HEALTH + SAFE DIAGNOSTICS + PROVIDER SELF-HEALING
# ----------------------------------------------------------------------

# Broaden PO/provider error recognition so version incompatibilities trigger
# the existing repair logic instead of wasting retries on a broken provider.
old_provider_detection = '''            if (
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
'''
new_provider_detection = '''            if (
                "po token" in low_line
                or "pot provider" in low_line
                or "bgutil" in low_line
                or "provider version" in low_line
            ) and (
                "error" in low_line
                or "failed" in low_line
                or "missing" in low_line
                or "unavailable" in low_line
                or "not provided" in low_line
                or "not found" in low_line
                or "mismatch" in low_line
                or "incompatible" in low_line
                or "version" in low_line
            ):
                saw_pot_problem = True
'''
if old_provider_detection in text:
    text = text.replace(old_provider_detection, new_provider_detection, 1)

# TURBO previously tracked 403/format failures but did not feed PO/provider
# failures into the shared Smart Recovery profile. Add the same diagnosis.
old_cache_vars = '''    process = None
    saw_403 = False
    saw_format_problem = False
    stopped = False
'''
new_cache_vars = '''    process = None
    saw_403 = False
    saw_format_problem = False
    saw_pot_problem = False
    saw_auth_problem = False
    saw_rate_limit = False
    stopped = False
'''
if old_cache_vars in text:
    text = text.replace(old_cache_vars, new_cache_vars, 1)

old_cache_low = '''            low = line.lower()

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
'''
new_cache_low = '''            low = line.lower()

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

            if (
                "po token" in low
                or "pot provider" in low
                or "bgutil" in low
                or "provider version" in low
            ) and (
                "error" in low
                or "failed" in low
                or "missing" in low
                or "unavailable" in low
                or "not provided" in low
                or "not found" in low
                or "mismatch" in low
                or "incompatible" in low
                or "version" in low
            ):
                saw_pot_problem = True

            if (
                "sign in to confirm" in low
                or "confirm you’re not a bot" in low
                or "confirm you're not a bot" in low
                or "login required" in low
                or "authentication required" in low
            ):
                saw_auth_problem = True

            if (
                "http error 429" in low
                or "too many requests" in low
            ):
                saw_rate_limit = True
'''
if old_cache_low in text:
    text = text.replace(old_cache_low, new_cache_low, 1)

# Publish cache diagnostics into the shared error profile before leaving the
# TURBO attempt, without changing the stable return tuple.
old_cache_finally = '''    finally:
        if process is not None:
            unregister_process(process)



def probe_stream_types(path):
'''
new_cache_finally = '''    finally:
        _set_download_error_profile(
            saw_403=saw_403,
            saw_format_problem=saw_format_problem,
            saw_pot_problem=saw_pot_problem,
            saw_auth_problem=saw_auth_problem,
            saw_rate_limit=saw_rate_limit,
            turbo_cache=True,
        )
        if process is not None:
            unregister_process(process)



def probe_stream_types(path):
'''
if old_cache_finally in text:
    text = text.replace(old_cache_finally, new_cache_finally, 1)

# Make TURBO auto-repair react to provider failure too, not only raw HTTP 403.
old_turbo_repair = '''    if (
        code != 0
        and saw_403
        and not stop_all_event.is_set()
    ):
        auto_repair()
'''
new_turbo_repair = '''    turbo_profile = _get_download_error_profile()

    if (
        code != 0
        and (
            saw_403
            or turbo_profile.get("saw_403")
            or turbo_profile.get("saw_pot_problem")
        )
        and not turbo_profile.get("saw_rate_limit")
        and not stop_all_event.is_set()
    ):
        turbo_reasons = []
        if saw_403 or turbo_profile.get("saw_403"):
            turbo_reasons.append("HTTP 403")
        if turbo_profile.get("saw_pot_problem"):
            turbo_reasons.append("PO Token/provider")

        auto_repair(
            reason=", ".join(turbo_reasons) or "TURBO YouTube access failure"
        )
'''
if old_turbo_repair in text:
    text = text.replace(old_turbo_repair, new_turbo_repair, 1)

# Add a safe one-click diagnostics collector. It contains versions, local
# health state and the tail of the technical log, but never exports cookies,
# passwords, browser profiles or authentication tokens.
diagnostics_block = r'''

# ============================================================
# V32.48 — SAFE COPY DIAGNOSTICS
# ============================================================

def _z2se_version_line(executable, args=None):
    if not executable or not os.path.isfile(executable):
        return "missing"

    command = [executable] + list(args or ["--version"])

    try:
        result = subprocess.run(
            command,
            env=build_tool_env(),
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=8,
            creationflags=(
                subprocess.CREATE_NO_WINDOW
                if os.name == "nt"
                else 0
            ),
        )
        line = (result.stdout or "").strip().splitlines()
        return line[0][:300] if line else f"code {result.returncode}"
    except Exception as exc:
        return "error: " + str(exc)[:160]


def build_safe_diagnostics_text():
    profile = _get_download_error_profile()

    lines = [
        f"{APP_NAME} diagnostics",
        f"App version: {APP_VERSION}",
        f"Python: {sys.version.split()[0]}",
        f"Compiled: {bool(IS_COMPILED)}",
        f"yt-dlp: {_z2se_version_line(YTDLP)}",
        f"FFmpeg: {_z2se_version_line(FFMPEG, ['-version'])}",
        f"FFprobe: {_z2se_version_line(FFPROBE, ['-version'])}",
        f"PO provider ready: {bool(pot_ready)}",
        f"PO plugin path exists: {bool(POT_PLUGIN and os.path.exists(POT_PLUGIN))}",
        "Smart Recovery clients: mweb+PO -> default -> web_safari",
        "Last error profile: " + json.dumps(profile, ensure_ascii=False, sort_keys=True),
    ]

    # Copy only the visible technical-log tail. Scrub common secret-like query
    # parameters defensively before placing anything on the clipboard.
    try:
        raw_log = log_box.get("1.0", "end-1c")[-8000:]
    except Exception:
        raw_log = ""

    if raw_log:
        raw_log = re.sub(
            r'(?i)(po[_ -]?token|token|authorization|cookie|password|passwd|secret|key)=([^&\s]+)',
            r'\1=<redacted>',
            raw_log,
        )
        raw_log = re.sub(
            r'(?i)(Authorization:\s*)([^\r\n]+)',
            r'\1<redacted>',
            raw_log,
        )
        raw_log = re.sub(
            r'(?i)(Cookie:\s*)([^\r\n]+)',
            r'\1<redacted>',
            raw_log,
        )
        lines.extend([
            "",
            "--- Recent technical log (redacted) ---",
            raw_log,
        ])

    return "\n".join(lines)


def copy_z2se_diagnostics():
    try:
        report = build_safe_diagnostics_text()
        root.clipboard_clear()
        root.clipboard_append(report)
        root.update_idletasks()
        log("📋 Safe diagnostics copied to clipboard.")
        messagebox.showinfo(
            "Z²SE Diagnostics",
            "Diagnostics copied ✅\n\nPasswords, cookies and token-like values are redacted.",
        )
    except Exception as exc:
        messagebox.showerror(
            "Z²SE Diagnostics",
            "Could not copy diagnostics:\n\n" + str(exc),
        )

'''

if "def copy_z2se_diagnostics():" not in text:
    anchor = "def manual_z2se_update():"
    position = text.find(anchor)
    if position < 0:
        raise RuntimeError("manual_z2se_update anchor missing")
    text = text[:position] + diagnostics_block + text[position:]

# Add Copy Diagnostics to Tools next to Health Check when that menu exists.
menu_anchor = '''tools_menu.add_command(
    label=tr("Check updates now"),
    command=manual_z2se_update,
)
'''
menu_replacement = '''tools_menu.add_command(
    label="Copy Diagnostics",
    command=copy_z2se_diagnostics,
)
tools_menu.add_command(
    label=tr("Check updates now"),
    command=manual_z2se_update,
)
'''
if "command=copy_z2se_diagnostics" not in text:
    if menu_anchor not in text:
        raise RuntimeError("Tools menu update anchor missing")
    text = text.replace(menu_anchor, menu_replacement, 1)

# Smoke-level structural checks before producing the release payload.
required_markers = [
    'APP_VERSION = "32.48"',
    "def copy_z2se_diagnostics():",
    "Smart Recovery clients: mweb+PO -> default -> web_safari",
    "saw_pot_problem=saw_pot_problem",
]
for marker in required_markers:
    if marker not in text:
        raise RuntimeError("v32.48 marker missing: " + marker)

compile(text, "payload/app.py", "exec")
app_path.write_text(text, encoding="utf-8", newline="\n")

# Refresh manifest after the patch.
manifest = json.loads(manifest_path.read_text(encoding="utf-8-sig"))
manifest["version"] = TARGET_VERSION
manifest["created_by"] = (
    "GitHub Actions / v32.48 Engine Health + Safe Diagnostics"
)

file_map = {
    "app.py": app_path,
    "z2se_updater.pyw": updater_path,
}

entries = []
for name, path in file_map.items():
    entries.append(
        {
            "path": name,
            "sha256": sha256_file(path),
            "size": os.path.getsize(path),
        }
    )
manifest["files"] = entries
manifest_path.write_text(
    json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
    encoding="utf-8",
)

print(f"Prepared Z2SE v{TARGET_VERSION} Engine Health + Safe Diagnostics")
