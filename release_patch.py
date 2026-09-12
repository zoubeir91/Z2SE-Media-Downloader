from pathlib import Path
import hashlib
import json
import re
import sys

TARGET_VERSION = "32.62"


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
# V32.62 — ADAPTIVE PART RECOVERY MEMORY
# ----------------------------------------------------------------------
text, count = re.subn(
    r'APP_VERSION\s*=\s*"32\.61"',
    'APP_VERSION = "32.62"',
    text,
    count=1,
)
if count != 1:
    raise RuntimeError("Could not update APP_VERSION 32.61 -> 32.62")

part_start = text.find("def ytdlp_sections_part_download(")
part_end = text.find("\ndef _format_size_estimate(", part_start)
if part_start < 0 or part_end < 0:
    raise RuntimeError("PART engine block anchor missing")

# Add a tiny process-local memory layer immediately before the PART engine.
# It deliberately expires after 30 minutes so a temporary YouTube route does
# not become a permanent preference after YouTube changes again.
helpers = '''# V32.62 adaptive YouTube PART profile memory.\n_PART_PROFILE_MEMORY_TTL = 30 * 60\n_part_profile_memory = {"profile": "", "saved_at": 0.0}\n\n\ndef _remember_part_profile(profile):\n    profile = str(profile or "").strip().lower()\n    if profile not in {"default", "mweb", "web_safari", "web_embedded"}:\n        return\n    _part_profile_memory["profile"] = profile\n    _part_profile_memory["saved_at"] = time.monotonic()\n\n\ndef _recent_part_profile():\n    profile = str(_part_profile_memory.get("profile") or "").strip().lower()\n    try:\n        age = time.monotonic() - float(_part_profile_memory.get("saved_at") or 0.0)\n    except Exception:\n        age = _PART_PROFILE_MEMORY_TTL + 1\n    if profile and 0 <= age <= _PART_PROFILE_MEMORY_TTL:\n        return profile\n    _part_profile_memory["profile"] = ""\n    _part_profile_memory["saved_at"] = 0.0\n    return ""\n\n\n'''
if "_PART_PROFILE_MEMORY_TTL" not in text:
    text = text[:part_start] + helpers + text[part_start:]
    part_start += len(helpers)
    part_end += len(helpers)

part = text[part_start:part_end]

old_init = '''    youtube_part = is_youtube_page_url(url)\n    client_attempts = ["default"]\n\n    last_code = 994\n'''
new_init = '''    youtube_part = is_youtube_page_url(url)\n    preferred_profile = (\n        _recent_part_profile()\n        if youtube_part\n        else ""\n    )\n\n    # A recently successful route gets first chance. If it no longer works,\n    # Smart Recovery V2 immediately takes over and diagnoses the new failure.\n    # mweb is only preferred while the local PO provider is actually healthy.\n    if preferred_profile == "mweb" and not pot_ping():\n        preferred_profile = ""\n\n    client_attempts = [preferred_profile or "default"]\n\n    if preferred_profile:\n        log(\n            prefix\n            + "⚡ Adaptive PART memory: trying recent successful YouTube profile first: "\n            + preferred_profile\n        )\n\n    last_code = 994\n'''
if old_init not in part:
    raise RuntimeError("V32.61 PART initialization anchor missing")
part = part.replace(old_init, new_init, 1)

# after_move is emitted only after yt-dlp has successfully produced the PART
# output, making it a safe point to learn the winning profile.
old_file = '''                if line.startswith(\n                    "__VD_PART_FILE__"\n                ):\n'''
new_file = '''                if line.startswith(\n                    "__VD_PART_FILE__"\n                ):\n                    if youtube_part:\n                        _remember_part_profile(client_profile)\n                        log(\n                            prefix\n                            + "🧠 Adaptive PART memory learned: "\n                            + client_profile\n                            + " (30 min)"\n                        )\n'''
if old_file not in part:
    raise RuntimeError("V32.61 PART successful-file anchor missing")
part = part.replace(old_file, new_file, 1)

# If a remembered non-default route fails, always give the normal extractor a
# chance before/alongside the diagnosis-specific fallbacks. This prevents the
# memory optimization from ever reducing v32.61 recovery coverage.
old_else = '''                else:\n                    reasons = []\n'''
new_else = '''                else:\n                    if (\n                        preferred_profile\n                        and client_profile == preferred_profile\n                        and client_profile != "default"\n                        and "default" not in client_attempts\n                    ):\n                        client_attempts.append("default")\n\n                    reasons = []\n'''
if old_else not in part:
    raise RuntimeError("V32.61 diagnosis anchor missing")
part = part.replace(old_else, new_else, 1)

text = text[:part_start] + part + text[part_end:]
app_path.write_text(text, encoding="utf-8")

manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
manifest["product"] = "Z2SE Media Downloader"
manifest["version"] = TARGET_VERSION
manifest["created_by"] = "GitHub Actions / v32.62 adaptive YouTube PART profile memory"
manifest["files"] = [
    {"path": "app.py", "sha256": sha256_file(app_path), "size": app_path.stat().st_size},
    {"path": "z2se_updater.pyw", "sha256": sha256_file(updater_path), "size": updater_path.stat().st_size},
]
manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")

print("Prepared Z2SE v32.62 adaptive PART profile memory")
print("app.py", app_path.stat().st_size, sha256_file(app_path))
print("z2se_updater.pyw", updater_path.stat().st_size, sha256_file(updater_path))
