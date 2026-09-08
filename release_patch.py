from pathlib import Path
import hashlib
import json
import os
import re
import sys

TARGET_VERSION = "32.49"


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

# ----------------------------------------------------------------------
# V32.49 — PERSISTENT QUEUE + DUPLICATE ARCHIVE + PLAYLIST PRO
# ----------------------------------------------------------------------

text, count = re.subn(
    r'APP_VERSION\s*=\s*"32\.48"',
    'APP_VERSION = "32.49"',
    text,
    count=1,
)
if count != 1:
    raise RuntimeError("Could not update APP_VERSION 32.48 -> 32.49")

# URL normalization uses the urllib helpers already present in v32.48.
# Keep this incremental patch independent of the exact formatting of that import.

# Persistent files live beside the existing download history in the app folder.
history_anchor = 'DOWNLOAD_HISTORY_FILE = os.path.join(APP_DIR, "download_history.json")\n'
history_replacement = history_anchor + '''PENDING_QUEUE_FILE = os.path.join(APP_DIR, "z2se_pending_queue.json")
DOWNLOAD_ARCHIVE_FILE = os.path.join(APP_DIR, "z2se_download_archive.json")
'''
text = replace_once(text, history_anchor, history_replacement, "download history constants")

# Runtime state is intentionally separate from the visible-history table.
state_anchor = '''bulk_editor_rows = []
bulk_same_from_var = tk.StringVar()
bulk_same_to_var = tk.StringVar()
'''
state_replacement = '''bulk_editor_rows = []
bulk_same_from_var = tk.StringVar()
bulk_same_to_var = tk.StringVar()

# V32.49 — restart-safe manual queue state. Credentials/cookies/tokens are
# deliberately never serialized here.
pending_queue_jobs = {}
pending_queue_lock = threading.Lock()
download_archive = {}
download_archive_lock = threading.Lock()
'''
text = replace_once(text, state_anchor, state_replacement, "persistent queue globals")

queue_helpers = r'''

# ============================================================
# V32.49 — PERSISTENT QUEUE + DUPLICATE / ARCHIVE PROTECTION
# ============================================================

_V3249_SECRET_QUERY_KEYS = {
    "cookie", "cookies", "authorization", "password", "passwd", "secret",
    "token", "po_token", "pot", "api_key", "key",
}
_V3249_TRACKING_QUERY_KEYS = {"si", "pp", "fbclid", "gclid"}


def _v3249_normalize_source_url(url):
    raw = str(url or "").strip()
    if not raw:
        return ""
    try:
        parts = urlsplit(raw)
        scheme = (parts.scheme or "https").lower()
        host = parts.netloc.lower()
        clean_query = []
        for segment in str(parts.query or "").split("&"):
            if not segment:
                continue
            key = segment.partition("=")[0].strip().lower()
            if (
                key.startswith("utm_")
                or key in _V3249_TRACKING_QUERY_KEYS
                or key in _V3249_SECRET_QUERY_KEYS
            ):
                continue
            clean_query.append(segment)
        clean_query.sort(key=str.lower)
        path = re.sub(r"/{2,}", "/", parts.path or "/")
        return urlunsplit(
            (scheme, host, path, "&".join(clean_query), "")
        )
    except Exception:
        return raw


def _v3249_job_identity(job, quality=None):
    safe_url = _v3249_normalize_source_url(job.get("url", ""))
    mode = str(job.get("mode") or "full").lower()
    start = str(job.get("start") or "") if mode == "part" else ""
    end = str(job.get("end") or "") if mode == "part" else ""
    media_format = str(job.get("format") or "MP4").upper()
    quality_value = str(quality or job.get("quality") or "").strip()
    stable = "|".join((safe_url, mode, start, end, media_format, quality_value))
    return hashlib.sha256(stable.encode("utf-8", "replace")).hexdigest()


def _v3249_safe_job(job, quality=None, status=None):
    mode = str(job.get("mode") or "full").lower()
    safe = {
        "url": _v3249_normalize_source_url(job.get("url", "")),
        "mode": mode,
        "start": str(job.get("start") or "") if mode == "part" else "",
        "end": str(job.get("end") or "") if mode == "part" else "",
        "format": str(job.get("format") or "MP4").upper(),
        "quality": str(quality or job.get("quality") or "1080p"),
        "status": str(status or job.get("status") or "pending"),
        "title": str(job.get("title") or "")[:500],
        "playlist_id": str(job.get("playlist_id") or "")[:300],
        "playlist_index": int(job.get("playlist_index") or 0),
        "updated_at": int(time.time()),
    }
    safe["identity"] = _v3249_job_identity(safe, safe["quality"])
    return safe


def _v3249_atomic_json_write(path, payload):
    temp_path = path + ".tmp"
    with open(temp_path, "w", encoding="utf-8") as handle:
        json.dump(payload, handle, ensure_ascii=False, indent=2)
        handle.write("\n")
        handle.flush()
        try:
            os.fsync(handle.fileno())
        except Exception:
            pass
    os.replace(temp_path, path)


def _v3249_load_persistent_state():
    global pending_queue_jobs
    global download_archive

    loaded_pending = {}
    try:
        with open(PENDING_QUEUE_FILE, "r", encoding="utf-8") as handle:
            payload = json.load(handle)
        for raw in payload.get("jobs", []):
            if not isinstance(raw, dict) or not raw.get("url"):
                continue
            safe = _v3249_safe_job(raw, raw.get("quality"))
            if safe["status"] in {"running", "waiting", "starting", "postprocessing"}:
                safe["status"] = "pending"
            loaded_pending[safe["identity"]] = safe
    except (FileNotFoundError, OSError, ValueError, TypeError, json.JSONDecodeError):
        pass

    loaded_archive = {}
    try:
        with open(DOWNLOAD_ARCHIVE_FILE, "r", encoding="utf-8") as handle:
            payload = json.load(handle)
        rows = payload.get("items", [])
        if isinstance(rows, list):
            for raw in rows[-5000:]:
                if isinstance(raw, dict) and raw.get("identity"):
                    loaded_archive[str(raw["identity"])] = dict(raw)
    except (FileNotFoundError, OSError, ValueError, TypeError, json.JSONDecodeError):
        pass

    with pending_queue_lock:
        pending_queue_jobs = loaded_pending
    with download_archive_lock:
        download_archive = loaded_archive


def persist_pending_queue():
    try:
        with pending_queue_lock:
            rows = [dict(value) for value in pending_queue_jobs.values()]
        _v3249_atomic_json_write(
            PENDING_QUEUE_FILE,
            {"schema": 1, "saved_at": int(time.time()), "jobs": rows},
        )
    except Exception as exc:
        try:
            log(f"Persistent queue save warning: {exc}")
        except Exception:
            pass


def _v3249_persist_archive():
    try:
        with download_archive_lock:
            rows = list(download_archive.values())[-5000:]
        _v3249_atomic_json_write(
            DOWNLOAD_ARCHIVE_FILE,
            {"schema": 1, "saved_at": int(time.time()), "items": rows},
        )
    except Exception as exc:
        try:
            log(f"Download archive save warning: {exc}")
        except Exception:
            pass


def remember_pending_job(job, quality, status="waiting"):
    safe = _v3249_safe_job(job, quality, status=status)
    with pending_queue_lock:
        pending_queue_jobs[safe["identity"]] = safe
    persist_pending_queue()
    return safe["identity"]


def mark_pending_job_status(job, quality, status):
    identity = _v3249_job_identity(job, quality)
    with pending_queue_lock:
        existing = pending_queue_jobs.get(identity)
        if existing:
            existing["status"] = str(status)
            existing["updated_at"] = int(time.time())
    persist_pending_queue()


def finish_pending_job(job, quality, result, title=""):
    identity = _v3249_job_identity(job, quality)
    if result == "done":
        with pending_queue_lock:
            safe = pending_queue_jobs.pop(identity, None)
        if safe is None:
            safe = _v3249_safe_job(job, quality, status="done")
        safe["status"] = "done"
        safe["completed_at"] = int(time.time())
        if title:
            safe["title"] = str(title)[:500]
        with download_archive_lock:
            download_archive[identity] = safe
            while len(download_archive) > 5000:
                try:
                    download_archive.pop(next(iter(download_archive)))
                except Exception:
                    break
        persist_pending_queue()
        _v3249_persist_archive()
    else:
        safe = _v3249_safe_job(job, quality, status="retry")
        with pending_queue_lock:
            pending_queue_jobs[identity] = safe
        persist_pending_queue()


def _v3249_filter_duplicate_jobs(jobs, quality):
    accepted = []
    skipped = []
    seen = set()
    with pending_queue_lock:
        pending_snapshot = {key: dict(value) for key, value in pending_queue_jobs.items()}
    with download_archive_lock:
        archive_ids = set(download_archive.keys())

    for job in jobs:
        identity = _v3249_job_identity(job, quality)
        if identity in seen:
            skipped.append((job, "same batch"))
            continue
        seen.add(identity)
        if identity in archive_ids:
            skipped.append((job, "already downloaded"))
            continue
        existing = pending_snapshot.get(identity)
        if existing and existing.get("status") in {
            "running", "waiting", "starting", "postprocessing"
        }:
            skipped.append((job, "already queued"))
            continue
        accepted.append(job)
    return accepted, skipped


def restore_pending_queue_to_editor():
    _v3249_load_persistent_state()
    with pending_queue_lock:
        rows = [dict(value) for value in pending_queue_jobs.values()]
    if not rows:
        return

    existing_ids = set()
    for row in bulk_editor_rows:
        try:
            raw = {
                "url": row["url_var"].get().strip(),
                "start": row["start_var"].get().strip(),
                "end": row["end_var"].get().strip(),
                "mode": "part" if row["start_var"].get().strip() else "full",
                "format": row["format_var"].get().strip().upper() or "MP4",
            }
            if raw["url"]:
                existing_ids.add(_v3249_job_identity(raw, bulk_quality_var.get()))
        except Exception:
            pass

    restored = 0
    for job in rows:
        identity = _v3249_job_identity(job, job.get("quality"))
        if identity in existing_ids:
            continue
        try:
            add_bulk_row(
                url=job.get("url", ""),
                start=job.get("start", ""),
                end=job.get("end", ""),
                media_format=job.get("format", "MP4"),
            )
            existing_ids.add(identity)
            restored += 1
        except Exception:
            pass

    if restored:
        log(f"↩️ Restored {restored} pending queue job(s) from the previous session.")
        set_status(f"Restored {restored} pending download(s) — press Start to resume")

'''

# Helpers must exist before start_bulk executes. Place them directly before the
# manual job collector, after add_bulk_row has already been defined.
collector_anchor = "def collect_bulk_jobs():\n"
collector_pos = text.find(collector_anchor)
if collector_pos < 0:
    raise RuntimeError("collect_bulk_jobs anchor missing")
text = text[:collector_pos] + queue_helpers + text[collector_pos:]

# Duplicate protection is applied after validation and before queue allocation.
workers_anchor = '''    workers = _set_live_worker_limit(
        workers
    )
'''
workers_replacement = workers_anchor + '''
    jobs, duplicate_skips = _v3249_filter_duplicate_jobs(
        jobs,
        bulk_quality_var.get(),
    )
    if duplicate_skips:
        log(
            f"🛡️ Duplicate Protection: skipped {len(duplicate_skips)} duplicate job(s)."
        )
    if not jobs:
        set_status("Duplicate Protection: nothing new to download")
        messagebox.showinfo(
            "Duplicate Protection",
            "هاد التحميلات راه تزادو من قبل للصف أو راه تكمّلو من قبل.\\n\\n"
            "ما تزاد حتى duplicate جديد.",
        )
        return
'''
text = replace_once(text, workers_anchor, workers_replacement, "start_bulk duplicate filter")

# Every allocated job is persisted before its waiter thread is launched.
queue_insert_anchor = '''        queued_jobs.append(
            job
        )
'''
queue_insert_replacement = queue_insert_anchor + '''        remember_pending_job(
            job,
            bulk_quality_var.get(),
            status="waiting",
        )
'''
text = replace_once(text, queue_insert_anchor, queue_insert_replacement, "queue persistence on submit")

# Mark a job running as soon as it gets a real live slot.
worker_running_anchor = '''    else:
        job_runtime_context.index = index

        try:
'''
worker_running_replacement = '''    else:
        job_runtime_context.index = index
        mark_pending_job_status(job, quality, "running")

        try:
'''
text = replace_once(text, worker_running_anchor, worker_running_replacement, "worker running status")

# Move successful jobs into the completed archive; failed/stopped jobs remain
# retryable so a restart never silently loses them.
finish_anchor = '''    _finish_job_runtime_state(
        index
    )

    with bulk_count_lock:
'''
finish_replacement = '''    try:
        final_title = remember_job_title(index, "") or ""
    except Exception:
        final_title = ""
    finish_pending_job(
        job,
        quality,
        result,
        title=final_title,
    )

    _finish_job_runtime_state(
        index
    )

    with bulk_count_lock:
'''
text = replace_once(text, finish_anchor, finish_replacement, "worker completion persistence")

# Persist queue before the real quit path starts terminating processes.
quit_anchor = '''    app_quitting = True
    stop_all_event.set()
'''
quit_replacement = '''    app_quitting = True
    try:
        persist_pending_queue()
    except Exception:
        pass
    stop_all_event.set()
'''
text = replace_once(text, quit_anchor, quit_replacement, "quit queue persistence")

playlist_pro_block = r'''

# ============================================================
# V32.49 — PLAYLIST PRO (preview / filter / range / selection)
# ============================================================

def _v3249_duration_text(value):
    try:
        total = max(0, int(float(value or 0)))
    except Exception:
        return ""
    hours, rem = divmod(total, 3600)
    minutes, seconds = divmod(rem, 60)
    if hours:
        return f"{hours}:{minutes:02d}:{seconds:02d}"
    return f"{minutes}:{seconds:02d}"


def _v3249_playlist_entry_url(entry, playlist_url):
    raw = str(
        entry.get("webpage_url")
        or entry.get("original_url")
        or entry.get("url")
        or ""
    ).strip()
    if raw.startswith(("http://", "https://")):
        return raw
    extractor = str(
        entry.get("extractor_key")
        or entry.get("extractor")
        or ""
    ).lower()
    media_id = str(entry.get("id") or raw or "").strip()
    if media_id and "youtube" in extractor:
        return "https://www.youtube.com/watch?v=" + media_id
    if raw.startswith("/"):
        try:
            return urljoin(playlist_url, raw)
        except Exception:
            pass
    return raw


def open_playlist_pro():
    win = tk.Toplevel(root)
    win.title("Z²SE Playlist Pro")
    win.geometry("980x650")
    win.minsize(760, 500)
    try:
        set_window_icon(win)
    except Exception:
        pass

    source_var = tk.StringVar()
    filter_var = tk.StringVar()
    range_var = tk.StringVar()
    format_var = tk.StringVar(value="MP4")
    status_text = tk.StringVar(value="Paste a playlist/channel URL, then Load")
    entries = []
    visible_keys = []

    top = ttk.Frame(win, padding=10)
    top.pack(fill="x")
    ttk.Label(top, text="Playlist / Channel URL").pack(anchor="w")
    source_entry = ttk.Entry(top, textvariable=source_var)
    source_entry.pack(side="left", fill="x", expand=True, pady=(4, 0))

    body = ttk.Frame(win, padding=(10, 0, 10, 10))
    body.pack(fill="both", expand=True)

    controls = ttk.Frame(body)
    controls.pack(fill="x", pady=(8, 6))
    ttk.Label(controls, text="Filter").pack(side="left")
    filter_entry = ttk.Entry(controls, textvariable=filter_var, width=24)
    filter_entry.pack(side="left", padx=(5, 12))
    ttk.Label(controls, text="Range").pack(side="left")
    ttk.Entry(controls, textvariable=range_var, width=16).pack(side="left", padx=(5, 4))
    ttk.Label(controls, text="e.g. 1-10,15,20-25").pack(side="left", padx=(0, 12))
    ttk.Label(controls, text="Format").pack(side="left")
    ttk.Combobox(
        controls,
        textvariable=format_var,
        values=("MP4", "MP3"),
        state="readonly",
        width=7,
    ).pack(side="left", padx=(5, 0))

    tree_frame = ttk.Frame(body)
    tree_frame.pack(fill="both", expand=True)
    tree = ttk.Treeview(
        tree_frame,
        columns=("index", "title", "duration"),
        show="headings",
        selectmode="extended",
    )
    tree.heading("index", text="#")
    tree.heading("title", text="Title")
    tree.heading("duration", text="Duration")
    tree.column("index", width=70, anchor="center", stretch=False)
    tree.column("title", width=680, anchor="w")
    tree.column("duration", width=100, anchor="center", stretch=False)
    scroll = ttk.Scrollbar(tree_frame, orient="vertical", command=tree.yview)
    tree.configure(yscrollcommand=scroll.set)
    tree.pack(side="left", fill="both", expand=True)
    scroll.pack(side="right", fill="y")

    bottom = ttk.Frame(body)
    bottom.pack(fill="x", pady=(8, 0))
    ttk.Label(bottom, textvariable=status_text).pack(side="left", fill="x", expand=True)

    def refresh_view():
        tree.delete(*tree.get_children())
        visible_keys.clear()
        query = filter_var.get().strip().lower()
        for idx, entry in enumerate(entries, start=1):
            title = str(entry.get("title") or entry.get("id") or f"Item {idx}")
            media_id = str(entry.get("id") or "")
            if query and query not in title.lower() and query not in media_id.lower():
                continue
            key = str(idx - 1)
            visible_keys.append(key)
            tree.insert(
                "",
                "end",
                iid=key,
                values=(idx, title, _v3249_duration_text(entry.get("duration"))),
            )
        status_text.set(f"{len(visible_keys)} visible / {len(entries)} total")

    def apply_range():
        expression = range_var.get().strip()
        if not expression:
            return
        selected = []
        try:
            for token in expression.split(","):
                token = token.strip()
                if not token:
                    continue
                if "-" in token:
                    left, right = token.split("-", 1)
                    a, b = int(left), int(right)
                    if a > b:
                        a, b = b, a
                    selected.extend(range(a, b + 1))
                else:
                    selected.append(int(token))
        except Exception:
            messagebox.showwarning("Playlist Pro", "Range is not valid.", parent=win)
            return
        iids = [str(index - 1) for index in selected if str(index - 1) in tree.get_children()]
        tree.selection_set(iids)
        if iids:
            tree.see(iids[0])

    def add_selected():
        picked = list(tree.selection())
        if not picked:
            picked = list(tree.get_children())
        added = 0
        for iid in picked:
            try:
                entry = entries[int(iid)]
            except Exception:
                continue
            url = _v3249_playlist_entry_url(entry, source_var.get().strip())
            if not url:
                continue
            add_bulk_row(
                url=url,
                start="",
                end="",
                media_format=format_var.get().strip().upper() or "MP4",
            )
            added += 1
        if added:
            status_text.set(f"Added {added} item(s) to NEW DOWNLOADS ✅")
            set_status(f"Playlist Pro added {added} item(s) to the queue editor")

    def loaded(result, error=None):
        if error:
            status_text.set("Playlist load failed")
            messagebox.showerror("Playlist Pro", str(error), parent=win)
            return
        entries.clear()
        raw_entries = result.get("entries") if isinstance(result, dict) else None
        if isinstance(raw_entries, list):
            entries.extend([item for item in raw_entries if isinstance(item, dict)])
        elif isinstance(result, dict):
            entries.append(result)
        refresh_view()
        if entries:
            tree.selection_set(tree.get_children())

    def load_worker(url):
        try:
            command = [
                YTDLP,
                "--flat-playlist",
                "--dump-single-json",
                "--skip-download",
                "--no-warnings",
                url,
            ]
            result = subprocess.run(
                command,
                env=build_tool_env(),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=120,
                creationflags=(subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0),
            )
            if result.returncode != 0:
                raise RuntimeError((result.stderr or result.stdout or "yt-dlp error")[-1500:])
            payload = json.loads(result.stdout)
            gui_call(loaded, payload, None)
        except Exception as exc:
            gui_call(loaded, None, exc)

    def load_playlist():
        url = source_var.get().strip()
        if not re.match(r"^https?://", url, re.IGNORECASE):
            messagebox.showwarning("Playlist Pro", "Paste a valid http(s) URL.", parent=win)
            return
        status_text.set("Loading playlist preview…")
        threading.Thread(target=load_worker, args=(url,), daemon=True).start()

    ttk.Button(top, text="Load", command=load_playlist).pack(side="left", padx=(8, 0), pady=(4, 0))
    ttk.Button(controls, text="Apply Filter", command=refresh_view).pack(side="left", padx=(8, 0))
    ttk.Button(controls, text="Select Range", command=apply_range).pack(side="left", padx=(6, 0))
    ttk.Button(bottom, text="Select All", command=lambda: tree.selection_set(tree.get_children())).pack(side="right", padx=(6, 0))
    ttk.Button(bottom, text="Add Selected to Queue", command=add_selected).pack(side="right", padx=(6, 0))
    source_entry.focus_set()

'''

# Insert Playlist Pro after editor row helpers and before history persistence.
playlist_anchor = "def _history_row_values(item_id):\n"
playlist_pos = text.find(playlist_anchor)
if playlist_pos < 0:
    raise RuntimeError("history-row anchor missing for Playlist Pro")
text = text[:playlist_pos] + playlist_pro_block + text[playlist_pos:]

# Restore queued jobs only after the existing visible history has been loaded.
startup_anchor = '''load_download_history()
'''
startup_replacement = startup_anchor + '''try:
    restore_pending_queue_to_editor()
except Exception as exc:
    log(f"Persistent queue restore warning: {exc}")
'''
# Use the LAST startup call, not any possible function-text occurrence.
startup_pos = text.rfind(startup_anchor)
if startup_pos < 0:
    raise RuntimeError("startup history-load anchor missing")
text = text[:startup_pos] + startup_replacement + text[startup_pos + len(startup_anchor):]

# Add Playlist Pro to Tools without disturbing v32.48 diagnostics/update commands.
menu_anchor = '''tools_menu.add_command(
    label=tr("Check updates now"),
    command=manual_z2se_update,
)
'''
menu_replacement = '''tools_menu.add_command(
    label="Playlist Pro",
    command=open_playlist_pro,
)
tools_menu.add_separator()
tools_menu.add_command(
    label=tr("Check updates now"),
    command=manual_z2se_update,
)
'''
text = replace_once(text, menu_anchor, menu_replacement, "Playlist Pro Tools menu")

# Release-gate markers. These also ensure v32.48's important protections are
# still present because this patch is incremental on top of the v32.48 payload.
required_markers = [
    'APP_VERSION = "32.49"',
    "PENDING_QUEUE_FILE",
    "DOWNLOAD_ARCHIVE_FILE",
    "def restore_pending_queue_to_editor():",
    "def open_playlist_pro():",
    "def copy_z2se_diagnostics():",
    "Smart Recovery clients: mweb+PO -> default -> web_safari",
    "saw_pot_problem=saw_pot_problem",
    "Duplicate Protection",
]
for marker in required_markers:
    if marker not in text:
        raise RuntimeError("v32.49 marker missing: " + marker)

compile(text, "payload/app.py", "exec")
app_path.write_text(text, encoding="utf-8", newline="\n")

manifest = json.loads(manifest_path.read_text(encoding="utf-8-sig"))
manifest["version"] = TARGET_VERSION
manifest["created_by"] = (
    "GitHub Actions / v32.49 Persistent Queue + Duplicate Protection + Playlist Pro"
)

file_map = {
    "app.py": app_path,
    "z2se_updater.pyw": updater_path,
}
manifest["files"] = [
    {
        "path": name,
        "sha256": sha256_file(path),
        "size": os.path.getsize(path),
    }
    for name, path in file_map.items()
]
manifest_path.write_text(
    json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
    encoding="utf-8",
)

print(
    f"Prepared Z2SE v{TARGET_VERSION} Persistent Queue + Duplicate Protection + Playlist Pro"
)
