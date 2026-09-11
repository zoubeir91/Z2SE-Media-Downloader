from pathlib import Path
import hashlib
import json
import re
import sys

TARGET_VERSION = "32.61"


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
# V32.61 — YOUTUBE SMART RECOVERY V2
# ----------------------------------------------------------------------
text, count = re.subn(
    r'APP_VERSION\s*=\s*"32\.60"',
    'APP_VERSION = "32.61"',
    text,
    count=1,
)
if count != 1:
    raise RuntimeError("Could not update APP_VERSION 32.60 -> 32.61")

part_start = text.find("def ytdlp_sections_part_download(")
part_end = text.find("\ndef _format_size_estimate(", part_start)
if part_start < 0 or part_end < 0:
    raise RuntimeError("PART engine block anchor missing")
part = text[part_start:part_end]

old_clients = '''    # V32.47 multi-client PART recovery:\n    # mweb + PO first (when available), normal yt-dlp next, web_safari last.\n    if is_youtube_page_url(url):\n        client_attempts = (\n            ["mweb", "default", "web_safari"]\n            if pot_ready\n            else ["default", "web_safari"]\n        )\n    else:\n        client_attempts = ["default"]\n\n    last_code = 994\n\n    for attempt_number, client_profile in enumerate(\n        client_attempts,\n        start=1,\n    ):\n'''
new_clients = '''    # V32.61 Smart Recovery V2: begin with yt-dlp's normal extractor and\n    # append only profiles that match the observed failure. The list remains\n    # mutable on purpose: Python will visit profiles appended after failures.\n    youtube_part = is_youtube_page_url(url)\n    client_attempts = ["default"]\n\n    last_code = 994\n\n    for attempt_number, client_profile in enumerate(\n        client_attempts,\n        start=1,\n    ):\n'''
if old_clients not in part:
    raise RuntimeError("PART v32.47 client-attempt anchor missing")
part = part.replace(old_clients, new_clients, 1)

old_args = '''        if client_profile != "default":\n            command += [\n                "--extractor-args",\n                (\n                    "youtube:player_client="\n                    + client_profile\n                ),\n            ]\n\n        command.append(\n            url\n        )\n'''
new_args = '''        if client_profile == "mweb":\n            # mweb requires a current GVS PO Token. Repair/restart the local\n            # provider only when this recovery profile is actually needed.\n            if not pot_ping():\n                check_and_start_pot()\n\n            if pot_ping():\n                command += [\n                    "--extractor-args",\n                    "youtube:player_client=mweb",\n                ]\n            else:\n                log(\n                    prefix\n                    + "🧠 Smart Recovery V2: mweb skipped — PO provider unavailable."\n                )\n                if "web_safari" not in client_attempts:\n                    client_attempts.append("web_safari")\n                continue\n\n        elif client_profile == "web_safari":\n            # yt-dlp currently documents HLS on web_safari as not requiring\n            # a GVS PO Token, so this is the provider-independent route.\n            command += [\n                "--extractor-args",\n                "youtube:player_client=web_safari",\n            ]\n\n        elif client_profile == "web_embedded":\n            # Last public-video fallback; yt-dlp limits this client to videos\n            # that are allowed to be embedded.\n            command += [\n                "--extractor-args",\n                "youtube:player_client=web_embedded",\n            ]\n\n        command.append(\n            url\n        )\n'''
if old_args not in part:
    raise RuntimeError("PART current extractor-args anchor missing")
part = part.replace(old_args, new_args, 1)

old_state = '''        ffmpeg_speed_factor = 0.0\n        saw_ffmpeg_machine_progress = False\n\n        started_at = time.monotonic()\n'''
new_state = '''        ffmpeg_speed_factor = 0.0\n        saw_ffmpeg_machine_progress = False\n\n        # Per-attempt diagnosis used to choose the next recovery profile.\n        saw_403 = False\n        saw_pot_problem = False\n        saw_provider_problem = False\n        saw_auth_problem = False\n        saw_sabr_problem = False\n        saw_format_problem = False\n\n        started_at = time.monotonic()\n'''
if old_state not in part:
    raise RuntimeError("PART diagnostic state anchor missing")
part = part.replace(old_state, new_state, 1)

old_line = '''                if not line:\n                    continue\n\n                if line.startswith(\n                    "__VD_PART_FILE__"\n                ):\n'''
new_line = '''                if not line:\n                    continue\n\n                low = line.lower()\n\n                if (\n                    "403" in low\n                    and ("forbidden" in low or "http error 403" in low)\n                ):\n                    saw_403 = True\n\n                if (\n                    "po token" in low\n                    or "[pot:" in low\n                    or "pot provider" in low\n                ):\n                    saw_pot_problem = True\n\n                if (\n                    "127.0.0.1:4416" in low\n                    or "localhost:4416" in low\n                    or ("error reaching get" in low and "/ping" in low)\n                ):\n                    saw_provider_problem = True\n\n                if (\n                    "login_required" in low\n                    or "sign in to confirm" in low\n                    or "authentication required" in low\n                    or "this video is private" in low\n                ):\n                    saw_auth_problem = True\n\n                if "sabr" in low:\n                    saw_sabr_problem = True\n\n                if (\n                    "requested format is not available" in low\n                    or "only images are available" in low\n                    or "no video formats found" in low\n                ):\n                    saw_format_problem = True\n\n                if line.startswith(\n                    "__VD_PART_FILE__"\n                ):\n'''
if old_line not in part:
    raise RuntimeError("PART line classifier anchor missing")
part = part.replace(old_line, new_line, 1)

old_failure = '''            log(\n                prefix\n                + "PART attempt failed. Code: "\n                + str(\n                    code\n                )\n            )\n\n            if is_youtube_page_url(url) and not pot_ping():\n                log(\n                    prefix\n                    + "🩹 PART recovery: PO provider is offline -> self-repair before next profile"\n                )\n                check_and_start_pot()\n'''
new_failure = '''            log(\n                prefix\n                + "PART attempt failed. Code: "\n                + str(\n                    code\n                )\n            )\n\n            if youtube_part:\n                if saw_auth_problem:\n                    # Account-required content is not fixed by anonymous client\n                    # roulette. web_creator itself requires account cookies.\n                    log(\n                        prefix\n                        + "🧠 Smart Recovery V2 diagnosis: LOGIN_REQUIRED / account access "\n                        + "— anonymous fallbacks stopped."\n                    )\n\n                else:\n                    reasons = []\n                    if saw_provider_problem:\n                        reasons.append("provider offline")\n                    if saw_pot_problem:\n                        reasons.append("PO Token")\n                    if saw_403:\n                        reasons.append("GVS/HTTP 403")\n                    if saw_sabr_problem:\n                        reasons.append("SABR")\n                    if saw_format_problem:\n                        reasons.append("format availability")\n                    if not reasons:\n                        reasons.append("generic extractor failure")\n\n                    log(\n                        prefix\n                        + "🧠 Smart Recovery V2 diagnosis: "\n                        + ", ".join(reasons)\n                    )\n\n                    # Access/PO failures: heal the local provider and then add\n                    # the currently recommended mweb+PO route once.\n                    if (\n                        saw_provider_problem\n                        or saw_pot_problem\n                        or saw_403\n                    ):\n                        if not pot_ping():\n                            log(\n                                prefix\n                                + "🩹 Smart Recovery V2: repairing local PO provider..."\n                            )\n                            check_and_start_pot()\n\n                        if (\n                            pot_ping()\n                            and client_profile != "mweb"\n                            and "mweb" not in client_attempts\n                        ):\n                            client_attempts.append("mweb")\n\n                    # web_safari is the provider-independent HLS-oriented route.\n                    if (\n                        saw_403\n                        or saw_sabr_problem\n                        or saw_format_problem\n                        or client_profile == "mweb"\n                        or client_profile == "default"\n                    ):\n                        if "web_safari" not in client_attempts:\n                            client_attempts.append("web_safari")\n\n                    # Keep web_embedded last because it only supports videos\n                    # YouTube allows to be embedded.\n                    if (\n                        saw_sabr_problem\n                        or saw_format_problem\n                        or client_profile == "web_safari"\n                    ):\n                        if "web_embedded" not in client_attempts:\n                            client_attempts.append("web_embedded")\n'''
if old_failure not in part:
    raise RuntimeError("V32.60 PART provider-recovery anchor missing")
part = part.replace(old_failure, new_failure, 1)

# Update the nearby documentation from the old fixed three-client chain.
part = part.replace(
    "      - If mweb fails, retry once with yt-dlp's normal client selection.\n",
    "      - Smart Recovery diagnoses 403/PO/provider/SABR/format/auth failures.\n"
    "      - Matching client profiles are appended dynamically; blind retries are avoided.\n",
    1,
)

text = text[:part_start] + part + text[part_end:]

app_path.write_text(text, encoding="utf-8")

manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
manifest["product"] = "Z2SE Media Downloader"
manifest["version"] = TARGET_VERSION
manifest["created_by"] = "GitHub Actions / v32.61 YouTube Smart Recovery V2"
manifest["files"] = [
    {"path": "app.py", "sha256": sha256_file(app_path), "size": app_path.stat().st_size},
    {"path": "z2se_updater.pyw", "sha256": sha256_file(updater_path), "size": updater_path.stat().st_size},
]
manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")

print("Prepared Z2SE v32.61 YouTube Smart Recovery V2")
print("app.py", app_path.stat().st_size, sha256_file(app_path))
print("z2se_updater.pyw", updater_path.stat().st_size, sha256_file(updater_path))
