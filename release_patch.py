from pathlib import Path
import hashlib
import json
import re
import sys

TARGET_VERSION = "32.63"


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
# V32.63 — CLEAN MANUAL STARTUP + SELF-DIAGNOSIS HEALTH CHECK
# ----------------------------------------------------------------------
text, count = re.subn(
    r'APP_VERSION\s*=\s*"32\.62"',
    'APP_VERSION = "32.63"',
    text,
    count=1,
)
if count != 1:
    raise RuntimeError("Could not update APP_VERSION 32.62 -> 32.63")

# The editor itself is created with one clean row. The recurring old PART URLs
# seen after restart were therefore coming from Browser Bridge open/part
# requests replayed as the app came back online. Protect normal manual/update
# startup from those stale retries without breaking the intentional case where
# Chrome itself launched Z2SE for a PART request.
bridge_anchor = "def browser_request_received(payload):\n"
if bridge_anchor not in text:
    raise RuntimeError("Browser request handler anchor missing")

bridge_helpers = '''# V32.63: keep the manual PART editor clean across restart/update.\n# Browser extensions may retry an old open/part request as soon as the local\n# bridge comes back online. Ignore those startup replays briefly on a normal\n# manual launch. Browser-triggered launches remain exempt so intentional\n# Chrome -> PART still works immediately.\n_Z2SE_STARTED_MONOTONIC = time.monotonic()\n_STARTUP_PART_REPLAY_GUARD_SECONDS = 10.0\n\n\ndef _browser_request_is_stale_startup_part(payload, action):\n    if str(action or "").strip().lower() not in {"open", "part"}:\n        return False\n\n    if BROWSER_LAUNCH_MODE:\n        return False\n\n    # Prefer an explicit request timestamp when an extension supplies one.\n    # Accept common seconds or milliseconds epoch formats.\n    for key in ("timestamp", "sent_at", "created_at", "ts"):\n        raw = payload.get(key) if isinstance(payload, dict) else None\n        if raw in (None, ""):\n            continue\n        try:\n            stamp = float(raw)\n            if stamp > 10_000_000_000:\n                stamp /= 1000.0\n            if stamp > 1_000_000_000 and time.time() - stamp > 30.0:\n                return True\n        except Exception:\n            pass\n\n    try:\n        return (\n            time.monotonic() - _Z2SE_STARTED_MONOTONIC\n            < _STARTUP_PART_REPLAY_GUARD_SECONDS\n        )\n    except Exception:\n        return False\n\n\n'''
text = text.replace(bridge_anchor, bridge_helpers + bridge_anchor, 1)

old_part_entry = '''    # --------------------------------------------------------\n    # PART FROM BROWSER -> UNIFIED EDITOR ROW\n    # --------------------------------------------------------\n    if action in ("open", "part"):\n        bulk_quality_var.set(quality)\n'''
new_part_entry = '''    # --------------------------------------------------------\n    # PART FROM BROWSER -> UNIFIED EDITOR ROW\n    # --------------------------------------------------------\n    if action in ("open", "part"):\n        if _browser_request_is_stale_startup_part(payload, action):\n            log(\n                "🧹 Clean Startup: ignored stale Browser Bridge PART/open replay: "\n                + url\n            )\n            return\n\n        bulk_quality_var.set(quality)\n'''
if old_part_entry not in text:
    raise RuntimeError("Browser PART entry anchor missing")
text = text.replace(old_part_entry, new_part_entry, 1)

# Replace/override the older basic health-check implementation by defining a
# stronger one immediately before the UI translation/menu section. The menu is
# built afterwards, so it will bind to this v32.63 function.
health_insert_anchor = "\n# V32.43 copy hierarchy overrides\n"
if health_insert_anchor not in text:
    raise RuntimeError("Health-check insertion anchor missing")

health_code = r'''
# ============================================================
# V32.63 — SYSTEM HEALTH CHECK / SAFE SELF-REPAIR
# ============================================================
def _health_command_ok(command, timeout=8):
    try:
        result = subprocess.run(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=timeout,
            env=build_tool_env(),
            creationflags=(
                subprocess.CREATE_NO_WINDOW
                if os.name == "nt"
                else 0
            ),
        )
        output = str(result.stdout or "").strip().splitlines()
        first = output[0].strip() if output else ""
        return result.returncode == 0, first
    except Exception as exc:
        return False, str(exc)


def _health_bridge_ping():
    try:
        url = str(BRIDGE_URL or "").rstrip("/") + "/ping"
        with urllib.request.urlopen(url, timeout=2.0) as response:
            return 200 <= int(response.status) < 300
    except Exception:
        return False


def _health_check_worker():
    rows = []

    def add(name, ok, detail=""):
        rows.append((name, bool(ok), str(detail or "").strip()))

    # yt-dlp
    ytdlp_ok = bool(YTDLP and os.path.isfile(YTDLP))
    ytdlp_detail = YTDLP or "not found"
    if ytdlp_ok:
        command_ok, version_text = _health_command_ok([YTDLP, "--version"])
        ytdlp_ok = ytdlp_ok and command_ok
        if version_text:
            ytdlp_detail = version_text
    add("yt-dlp", ytdlp_ok, ytdlp_detail)

    # FFmpeg / FFprobe
    ffmpeg_ok = bool(FFMPEG and os.path.isfile(FFMPEG))
    ffmpeg_detail = FFMPEG or "not found"
    if ffmpeg_ok:
        command_ok, version_text = _health_command_ok([FFMPEG, "-version"])
        ffmpeg_ok = ffmpeg_ok and command_ok
        if version_text:
            ffmpeg_detail = version_text
    add("FFmpeg", ffmpeg_ok, ffmpeg_detail)

    ffprobe_ok = bool(FFPROBE and os.path.isfile(FFPROBE))
    ffprobe_detail = FFPROBE or "not found"
    if ffprobe_ok:
        command_ok, version_text = _health_command_ok([FFPROBE, "-version"])
        ffprobe_ok = ffprobe_ok and command_ok
        if version_text:
            ffprobe_detail = version_text
    add("FFprobe", ffprobe_ok, ffprobe_detail)

    # Deno
    deno = shutil.which("deno")
    deno_ok = bool(deno)
    deno_detail = deno or "not found"
    if deno_ok:
        command_ok, version_text = _health_command_ok([deno, "--version"])
        deno_ok = deno_ok and command_ok
        if version_text:
            deno_detail = version_text
    add("Deno", deno_ok, deno_detail)

    # PO provider: safe auto-repair is already implemented by v32.60.
    provider_ok = pot_ping()
    repaired = False
    if not provider_ok:
        try:
            repaired = bool(check_and_start_pot())
        except Exception:
            repaired = False
        provider_ok = pot_ping()
    add(
        "PO Token Provider",
        provider_ok,
        (
            "active after automatic repair"
            if provider_ok and repaired
            else ("active" if provider_ok else "unavailable")
        ),
    )

    # Browser bridge
    bridge_ok = _health_bridge_ping()
    add(
        "Browser Bridge",
        bridge_ok,
        (BRIDGE_URL if bridge_ok else "local bridge did not answer /ping"),
    )

    # Main download folder
    downloads_ok = bool(DOWNLOADS and os.path.isdir(DOWNLOADS))
    add("Downloads folder", downloads_ok, DOWNLOADS or "not found")

    ok_count = sum(1 for _, ok, _ in rows if ok)
    total = len(rows)

    lines = [
        f"Z²SE v{APP_VERSION} — System Health Check",
        "",
    ]

    for name, ok, detail in rows:
        lines.append(("✅ " if ok else "❌ ") + name)
        if detail:
            # Keep the popup compact while preserving useful diagnosis.
            compact = detail.replace("\n", " ").strip()
            if len(compact) > 130:
                compact = compact[:127] + "..."
            lines.append("    " + compact)

    lines += [
        "",
        f"Result: {ok_count}/{total} checks OK",
    ]

    if ok_count == total:
        lines.append("Z²SE is ready ✅")
    else:
        lines.append("Problems were logged. Safe PO-provider repair was attempted automatically.")

    body = "\n".join(lines)

    for line in lines:
        log("HEALTH: " + line if line else "HEALTH:")

    def show_result():
        try:
            if ok_count == total:
                messagebox.showinfo("Z²SE Health Check", body)
            else:
                messagebox.showwarning("Z²SE Health Check", body)
        except Exception:
            pass

    gui_call(show_result)


def show_health_check():
    set_status("Health Check...")
    log("🩺 Z²SE Health Check started...")
    threading.Thread(
        target=_health_check_worker,
        daemon=True,
        name="Z2SEHealthCheck",
    ).start()

'''
text = text.replace(health_insert_anchor, "\n" + health_code + health_insert_anchor, 1)

app_path.write_text(text, encoding="utf-8")

manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
manifest["product"] = "Z2SE Media Downloader"
manifest["version"] = TARGET_VERSION
manifest["created_by"] = "GitHub Actions / v32.63 clean startup + system health check"
manifest["files"] = [
    {"path": "app.py", "sha256": sha256_file(app_path), "size": app_path.stat().st_size},
    {"path": "z2se_updater.pyw", "sha256": sha256_file(updater_path), "size": updater_path.stat().st_size},
]
manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")

print("Prepared Z2SE v32.63 clean startup + system health check")
print("app.py", app_path.stat().st_size, sha256_file(app_path))
print("z2se_updater.pyw", updater_path.stat().st_size, sha256_file(updater_path))
