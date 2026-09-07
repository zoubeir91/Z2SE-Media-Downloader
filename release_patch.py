from pathlib import Path
import hashlib
import json
import os
import re
import sys

TARGET_VERSION = "32.47"


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
    r'APP_VERSION\s*=\s*"32\.46"',
    'APP_VERSION = "32.47"',
    text,
    count=1,
)
if count != 1:
    raise RuntimeError("Could not update APP_VERSION 32.46 -> 32.47")

# ----------------------------------------------------------------------
# V32.47 — MULTI-CLIENT YOUTUBE SMART RECOVERY
# Normal path remains unchanged. Extra clients are used only after failure.
# ----------------------------------------------------------------------

# 1) Let build_command optionally force one YouTube client.
text = replace_once(
    text,
    """    referer=None,
    broad_format=False,
):
""",
    """    referer=None,
    broad_format=False,
    youtube_client=None,
):
""",
    "build_command signature",
)

old_build_client = """    if pot_ready:
        extractor_args = \"youtube:player_client=mweb\"
        if fast_extract:
            extractor_args += \";skip=hls,dash,translated_subs\"

        command += [
            \"--extractor-args\",
            extractor_args,
        ]
    elif fast_extract:
        command += [
            \"--extractor-args\",
            \"youtube:skip=hls,dash,translated_subs\",
        ]
"""

new_build_client = """    forced_youtube_client = str(
        youtube_client or \"\"
    ).strip().lower()

    if forced_youtube_client and forced_youtube_client != \"default\":
        extractor_args = (
            \"youtube:player_client=\"
            + forced_youtube_client
        )

        # web_safari is intentionally used as a manifest-capable recovery
        # route. Do not disable HLS/DASH on that profile.
        if (
            fast_extract
            and forced_youtube_client != \"web_safari\"
        ):
            extractor_args += \";skip=hls,dash,translated_subs\"

        command += [
            \"--extractor-args\",
            extractor_args,
        ]

    elif forced_youtube_client == \"default\":
        if fast_extract:
            command += [
                \"--extractor-args\",
                \"youtube:skip=hls,dash,translated_subs\",
            ]

    elif pot_ready:
        extractor_args = \"youtube:player_client=mweb\"
        if fast_extract:
            extractor_args += \";skip=hls,dash,translated_subs\"

        command += [
            \"--extractor-args\",
            extractor_args,
        ]

    elif fast_extract:
        command += [
            \"--extractor-args\",
            \"youtube:skip=hls,dash,translated_subs\",
        ]
"""
text = replace_once(
    text,
    old_build_client,
    new_build_client,
    "build_command YouTube client block",
)

# 2) Propagate optional profile through run_download_once.
text = replace_once(
    text,
    """    referer=None,
    broad_format=False,
):
    if should_stop_current_job():
""",
    """    referer=None,
    broad_format=False,
    youtube_client=None,
):
    if should_stop_current_job():
""",
    "run_download_once signature",
)

text = replace_once(
    text,
    """        referer=referer,
        broad_format=broad_format,
    )
""",
    """        referer=referer,
        broad_format=broad_format,
        youtube_client=youtube_client,
    )
""",
    "run_download_once -> build_command",
)

# 3) After engine repair/default retry, try web_safari once before broad-format.
smart_anchor = """        profile = _get_download_error_profile()

    # Last-resort format recovery. This deliberately does NOT run on HTTP 429
"""
smart_insert = """        profile = _get_download_error_profile()

    # V32.47: if YouTube still fails after repair + normal extraction, try one
    # independent client path. web_safari can expose a different manifest
    # route and is especially useful when mweb/GVS access is the failing layer.
    if (
        code != 0
        and is_youtube_page_url(url)
        and not profile.get(\"saw_rate_limit\")
        and not should_stop_current_job()
    ):
        prefix = f\"[{job_label}] \" if job_label else \"\"
        log(
            prefix
            + \"Smart Recovery: trying YouTube web_safari fallback...\"
        )

        code, saw_403, stopped, saw_format_problem = run_download_once(
            url=url,
            quality=quality,
            mode=mode,
            start=start,
            end=end,
            output_prefix=output_prefix,
            progress_callback=progress_callback,
            stats_callback=stats_callback,
            job_label=job_label,
            fast_extract=False,
            media_format=media_format,
            output_name=output_name,
            referer=referer,
            youtube_client=\"web_safari\",
        )

        if stopped:
            return code, \"stopped\"

        profile = _get_download_error_profile()

    # Last-resort format recovery. This deliberately does NOT run on HTTP 429
"""
text = replace_once(
    text,
    smart_anchor,
    smart_insert,
    "full-download web_safari recovery",
)

# 4) PART engine: mweb -> default -> web_safari, no duplicate default attempt
# when the PO provider is unavailable.
old_part_attempts = """    # For YouTube, try the same mweb path first because the app already has
    # PO-token support. If that route fails, retry without forcing a client.
    client_attempts = (
        [True, False]
        if is_youtube_page_url(
            url
        )
        else [False]
    )

    last_code = 994

    for attempt_number, use_mweb in enumerate(
        client_attempts,
        start=1,
    ):
"""
new_part_attempts = """    # V32.47 multi-client PART recovery:
    # mweb + PO first (when available), normal yt-dlp next, web_safari last.
    if is_youtube_page_url(url):
        client_attempts = (
            [\"mweb\", \"default\", \"web_safari\"]
            if pot_ready
            else [\"default\", \"web_safari\"]
        )
    else:
        client_attempts = [\"default\"]

    last_code = 994

    for attempt_number, client_profile in enumerate(
        client_attempts,
        start=1,
    ):
"""
text = replace_once(
    text,
    old_part_attempts,
    new_part_attempts,
    "PART client attempt list",
)

old_part_client_arg = """        if (
            use_mweb
            and pot_ready
        ):
            command += [
                \"--extractor-args\",
                \"youtube:player_client=mweb\",
            ]
"""
new_part_client_arg = """        if client_profile != \"default\":
            command += [
                \"--extractor-args\",
                (
                    \"youtube:player_client=\"
                    + client_profile
                ),
            ]
"""
text = replace_once(
    text,
    old_part_client_arg,
    new_part_client_arg,
    "PART extractor client argument",
)

old_part_log = """            + (
                \" • YouTube mweb\"
                if use_mweb
                else \" • normal extractor\"
            )
"""
new_part_log = """            + (
                \" • YouTube \" + client_profile
                if is_youtube_page_url(url)
                else \" • normal extractor\"
            )
"""
text = replace_once(
    text,
    old_part_log,
    new_part_log,
    "PART client log",
)

# 5) TURBO cache: allow forcing default/web_safari on recovery attempts.
text = replace_once(
    text,
    """    fast_extract=True,
    media_format=\"MP4\"
):
    media_format = str(media_format or \"MP4\").upper()
""",
    """    fast_extract=True,
    media_format=\"MP4\",
    youtube_client=None,
):
    media_format = str(media_format or \"MP4\").upper()
""",
    "build_cache_download_command signature",
)

old_cache_client = """    if pot_ready:
        # \"formats=dashy\" lets yt-dlp expose segmented variants so -N can
        # actually help. Keep mweb because the existing PO-token provider is
        # already configured for it.
        extractor_args = (
            \"youtube:player_client=mweb;\"
            \"formats=dashy\"
        )

        if fast_extract:
            extractor_args += \";skip=hls,translated_subs\"

        command += [
            \"--extractor-args\",
            extractor_args,
        ]

    elif fast_extract:
        command += [
            \"--extractor-args\",
            \"youtube:formats=dashy;skip=hls,translated_subs\",
        ]
"""
new_cache_client = """    forced_youtube_client = str(
        youtube_client or \"\"
    ).strip().lower()

    if forced_youtube_client == \"web_safari\":
        command += [
            \"--extractor-args\",
            \"youtube:player_client=web_safari\",
        ]

    elif forced_youtube_client == \"default\":
        if fast_extract:
            command += [
                \"--extractor-args\",
                \"youtube:formats=dashy;skip=hls,translated_subs\",
            ]

    elif forced_youtube_client and forced_youtube_client != \"default\":
        extractor_args = (
            \"youtube:player_client=\"
            + forced_youtube_client
            + \";formats=dashy\"
        )
        if fast_extract:
            extractor_args += \";skip=hls,translated_subs\"
        command += [
            \"--extractor-args\",
            extractor_args,
        ]

    elif pot_ready:
        # \"formats=dashy\" lets yt-dlp expose segmented variants so -N can
        # actually help. Keep mweb because the existing PO-token provider is
        # already configured for it.
        extractor_args = (
            \"youtube:player_client=mweb;\"
            \"formats=dashy\"
        )

        if fast_extract:
            extractor_args += \";skip=hls,translated_subs\"

        command += [
            \"--extractor-args\",
            extractor_args,
        ]

    elif fast_extract:
        command += [
            \"--extractor-args\",
            \"youtube:formats=dashy;skip=hls,translated_subs\",
        ]
"""
text = replace_once(
    text,
    old_cache_client,
    new_cache_client,
    "TURBO cache client block",
)

text = replace_once(
    text,
    """    fast_extract=True,
    media_format=\"MP4\"
):
    process = None
""",
    """    fast_extract=True,
    media_format=\"MP4\",
    youtube_client=None,
):
    process = None
""",
    "cache_download_once signature",
)

text = replace_once(
    text,
    """        fast_extract=fast_extract,
        media_format=media_format,
    )

    prefix = f\"[{job_label}] \" if job_label else \"\"
""",
    """        fast_extract=fast_extract,
        media_format=media_format,
        youtube_client=youtube_client,
    )

    prefix = f\"[{job_label}] \" if job_label else \"\"
""",
    "cache_download_once -> build cache command",
)

# On the post-repair TURBO retry, deliberately switch away from mweb.
turbo_retry_anchor = """            fast_extract=False,
            media_format=media_format,
        )

        (
            code,
            _,
            stopped,
            _,
            title2,
            final_file2,
        ) = result

        title = title2 or title
        final_file = final_file2 or final_file

        if stopped:
            return code, \"stopped\", None, title

    if code != 0:
        return code, \"error\", None, title
"""
turbo_retry_replacement = """            fast_extract=False,
            media_format=media_format,
            youtube_client=\"default\",
        )

        (
            code,
            _,
            stopped,
            _,
            title2,
            final_file2,
        ) = result

        title = title2 or title
        final_file = final_file2 or final_file

        if stopped:
            return code, \"stopped\", None, title

    if (
        code != 0
        and is_youtube_page_url(url)
        and not stop_all_event.is_set()
    ):
        log(
            prefix
            + \"Smart Recovery: TURBO trying web_safari fallback...\"
        )

        result = cache_download_once(
            url=url,
            quality=quality,
            cache_key=cache_key,
            progress_callback=progress_callback,
            stats_callback=stats_callback,
            job_label=job_label,
            fast_extract=False,
            media_format=media_format,
            youtube_client=\"web_safari\",
        )

        (
            code,
            _,
            stopped,
            _,
            title2,
            final_file2,
        ) = result

        title = title2 or title
        final_file = final_file2 or final_file

        if stopped:
            return code, \"stopped\", None, title

    if code != 0:
        return code, \"error\", None, title
"""
text = replace_once(
    text,
    turbo_retry_anchor,
    turbo_retry_replacement,
    "TURBO multi-client recovery",
)

app_path.write_text(text, encoding="utf-8", newline="\n")

# Refresh manifest after the patch.
manifest = json.loads(manifest_path.read_text(encoding="utf-8-sig"))
manifest["version"] = TARGET_VERSION
manifest["created_by"] = (
    "GitHub Actions / v32.47 Multi-Client YouTube Smart Recovery"
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

print(
    f"Prepared Z2SE v{TARGET_VERSION} "
    "Multi-Client YouTube Smart Recovery"
)
