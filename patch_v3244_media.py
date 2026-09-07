"""Z2SE v32.44 - final media validation / Facebook false-success fix."""


def apply_media_patch(text: str) -> str:
    marker = "\n\n# ============================================================\n# RUN ONE DOWNLOAD\n# ============================================================\n"
    if marker not in text:
        raise RuntimeError("run-download marker not found")

    validator = r'''

# ============================================================
# V32.44 — FINAL MEDIA VALIDATION
# Never trust a downloader exit code alone. Some websites can return an
# HTML/login/error page with a media-looking filename and exit successfully.
# A completed row must therefore contain a real audio/video stream.
# ============================================================
def _detach_current_job_output_path():
    index = _current_job_index()
    if index is None:
        return

    try:
        with job_output_paths_lock:
            job_output_paths.pop(int(index), None)
    except Exception:
        pass

    def _detach_visible_row():
        try:
            item_id = bulk_tree_ids.get(int(index))
            if item_id:
                row_file_paths.pop(item_id, None)
                bulk_tree.set(item_id, "size", "")
                schedule_download_history_save(50)
        except Exception:
            pass

    gui_call(_detach_visible_row)


def _validate_downloaded_media_file(path, media_format="MP4"):
    """Return (ok, reason). Real success requires a real media stream."""
    path = _normalize_output_path(path)
    media_format = str(media_format or "MP4").upper()

    if not path or not os.path.isfile(path):
        return False, "final file is missing"

    try:
        size = os.path.getsize(path)
    except Exception:
        size = 0

    # Explicit webpage/error-page detection. The 1.4 KiB Facebook `Accueil`
    # files that exposed this bug are caught here before they can be marked Done.
    try:
        with open(path, "rb") as handle:
            head = handle.read(4096).lstrip().lower()
        html_markers = (
            b"<!doctype html", b"<html", b"<head", b"<body",
            b"<script", b"<meta", b"facebook.com/login",
        )
        if any(marker in head for marker in html_markers):
            return False, "web page returned instead of media"
    except Exception:
        pass

    info = _probe_tv_codecs(path)
    if media_format == "MP3":
        if not info.get("has_audio"):
            return False, "no audio stream found"
    else:
        if not info.get("has_video"):
            return False, "no video stream found"

    # A valid probed stream is authoritative. The size is only included in
    # diagnostics; we deliberately do not reject legitimate very short clips.
    return True, f"verified media ({size} bytes)"


def _discard_invalid_download_output(path, url, reason, job_label=""):
    prefix = f"[{job_label}] " if job_label else ""
    host = ""
    try:
        host = (urlparse(str(url)).netloc or "").lower()
    except Exception:
        pass

    if "facebook.com" in host or "fb.watch" in host:
        log(
            prefix
            + "Facebook validation failed: the response is not a real video "
            + f"({reason}). Z2SE will not mark it as completed."
        )
    else:
        log(prefix + f"Final media validation failed: {reason}.")

    try:
        normalized = _normalize_output_path(path)
        if normalized and os.path.isfile(normalized):
            os.remove(normalized)
            log(prefix + "Removed invalid output file.")
    except Exception as exc:
        log(prefix + f"Could not remove invalid output: {exc}")

    _detach_current_job_output_path()
'''
    text = text.replace(marker, validator + marker, 1)

    old = '''        if (\n            code == 0\n            and str(media_format).upper() == "MP4"\n            and final_output_path\n            and os.path.isfile(final_output_path)\n        ):\n            ensure_tv_compatible_mp4(\n                final_output_path,\n                stats_callback=stats_callback,\n                job_label=job_label,\n            )\n\n            register_current_job_output_path(\n                final_output_path\n            )\n\n        return code, saw_403, False, saw_format_problem\n'''
    new = '''        # V32.44: exit code 0 is not sufficient. Validate the actual file.\n        if code == 0:\n            valid_media, validation_reason = _validate_downloaded_media_file(\n                final_output_path,\n                media_format=media_format,\n            )\n\n            if not valid_media:\n                _discard_invalid_download_output(\n                    final_output_path,\n                    url,\n                    validation_reason,\n                    job_label=job_label,\n                )\n                saw_format_problem = True\n                saw_invalid_media = True\n                code = 996\n\n        if (\n            code == 0\n            and str(media_format).upper() == "MP4"\n            and final_output_path\n            and os.path.isfile(final_output_path)\n        ):\n            tv_ok = ensure_tv_compatible_mp4(\n                final_output_path,\n                stats_callback=stats_callback,\n                job_label=job_label,\n            )\n\n            if not tv_ok:\n                valid_after_tv, tv_reason = _validate_downloaded_media_file(\n                    final_output_path,\n                    media_format=media_format,\n                )\n                if not valid_after_tv:\n                    _discard_invalid_download_output(\n                        final_output_path,\n                        url,\n                        tv_reason,\n                        job_label=job_label,\n                    )\n                    saw_invalid_media = True\n                    code = 996\n\n            if code == 0:\n                register_current_job_output_path(final_output_path)\n\n        return code, saw_403, False, saw_format_problem\n'''
    if old not in text:
        raise RuntimeError("run_download_once success block not found")
    text = text.replace(old, new, 1)

    # Track validation failure in the existing per-thread Smart Recovery profile.
    needle = '    saw_rate_limit = False\n    stopped = False\n'
    if needle not in text:
        raise RuntimeError("error profile locals marker not found")
    text = text.replace(
        needle,
        '    saw_rate_limit = False\n    saw_invalid_media = False\n    stopped = False\n',
        1,
    )

    needle = '            saw_rate_limit=saw_rate_limit,\n            broad_format=bool(broad_format),\n'
    if needle not in text:
        raise RuntimeError("error profile final marker not found")
    text = text.replace(
        needle,
        '            saw_rate_limit=saw_rate_limit,\n            saw_invalid_media=saw_invalid_media,\n            broad_format=bool(broad_format),\n',
        1,
    )

    # Preserve the specific invalid-media result after the final recovery attempt.
    old = '    return code, ("done" if code == 0 else "error")\n\n\n# ============================================================\n# SINGLE DOWNLOAD\n'
    new = '''    final_profile = _get_download_error_profile()\n    if code != 0 and final_profile.get("saw_invalid_media"):\n        return code, "invalid_media"\n\n    return code, ("done" if code == 0 else "error")\n\n\n# ============================================================\n# SINGLE DOWNLOAD\n'''
    if old not in text:
        raise RuntimeError("download_with_repair return marker not found")
    text = text.replace(old, new, 1)

    # Both current and legacy bulk workers must clear fake 100%/size values.
    old_live = '''    elif result == "stopped":\n        update_tree_status(\n            index,\n            "Stopped",\n        )\n\n    else:\n        update_tree_status(\n            index,\n            f"Error ({code})",\n        )\n'''
    new_live = '''    elif result == "stopped":\n        update_tree_status(index, "Stopped")\n\n    elif result == "invalid_media":\n        bulk_job_progress[index] = 0.0\n        update_tree_field(index, "progress", "0.0%")\n        update_tree_field(index, "speed", "")\n        update_tree_field(index, "eta", "")\n        update_tree_field(index, "size", "")\n        update_tree_status(index, tr("Invalid media"))\n\n    else:\n        update_tree_status(index, f"Error ({code})")\n'''
    if old_live not in text:
        raise RuntimeError("live worker result block not found")
    text = text.replace(old_live, new_live, 1)

    old_legacy = '''        elif result == "stopped":\n            update_tree_status(index, "Stopped")\n        else:\n            update_tree_status(index, f"Error ({code})")\n'''
    new_legacy = '''        elif result == "stopped":\n            update_tree_status(index, "Stopped")\n        elif result == "invalid_media":\n            bulk_job_progress[index] = 0.0\n            update_tree_field(index, "progress", "0.0%")\n            update_tree_field(index, "speed", "")\n            update_tree_field(index, "eta", "")\n            update_tree_field(index, "size", "")\n            update_tree_status(index, tr("Invalid media"))\n        else:\n            update_tree_status(index, f"Error ({code})")\n'''
    if old_legacy not in text:
        raise RuntimeError("legacy worker result block not found")
    text = text.replace(old_legacy, new_legacy, 1)

    return text
