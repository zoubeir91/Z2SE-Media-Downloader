from pathlib import Path
import ast, hashlib, json, sys

version = sys.argv[1]
assert version == "33.11"
app_path = Path("payload/app.py")
text = app_path.read_text(encoding="utf-8-sig")

def replace_once(old, new):
    global text
    assert text.count(old) == 1, (old[:220], text.count(old))
    text = text.replace(old, new, 1)

replace_once('APP_VERSION = "33.10"', 'APP_VERSION = "33.11"')

# Cancelled work is a user decision, not a retryable failure. Keeping it in
# pending_queue_jobs made a cancelled row return after restart.
replace_once(
    '''        persist_pending_queue()
        _v3249_persist_archive()
    else:
        safe = _v3249_safe_job(job, quality, status="retry")
        with pending_queue_lock:
            pending_queue_jobs[identity] = safe
        persist_pending_queue()
''',
    '''        persist_pending_queue()
        _v3249_persist_archive()
    elif result == "stopped":
        with pending_queue_lock:
            pending_queue_jobs.pop(identity, None)
        persist_pending_queue()
    else:
        safe = _v3249_safe_job(job, quality, status="retry")
        with pending_queue_lock:
            pending_queue_jobs[identity] = safe
        persist_pending_queue()
''',
)

# Native forced process-tree termination. A paused FFmpeg child can survive a
# simple Popen.terminate() of yt-dlp, which left the row permanently active.
replace_once(
    '''_PROCESS_SUSPEND_RESUME = 0x0800
_PROCESS_QUERY_LIMITED_INFORMATION = 0x1000
''',
    '''_PROCESS_TERMINATE = 0x0001
_PROCESS_SUSPEND_RESUME = 0x0800
_PROCESS_QUERY_LIMITED_INFORMATION = 0x1000
''',
)

force_helpers = r'''

def _force_terminate_pid(pid):
    """Terminate one Windows PID without relying on the parent staying alive."""
    if os.name != "nt":
        return False
    handle = None
    try:
        kernel32 = ctypes.windll.kernel32
        handle = kernel32.OpenProcess(_PROCESS_TERMINATE, False, int(pid))
        if not handle:
            return False
        return bool(kernel32.TerminateProcess(handle, 130))
    except Exception:
        return False
    finally:
        try:
            if handle:
                ctypes.windll.kernel32.CloseHandle(handle)
        except Exception:
            pass


def _force_terminate_process_tree(processes, extra_pids=None):
    """Kill children first, reap Popen handles, and never block the Tk thread."""
    processes = list(processes or [])
    roots = set()
    for process in processes:
        try:
            if process.poll() is None:
                roots.add(int(process.pid))
        except Exception:
            pass
    roots.update(int(pid) for pid in (extra_pids or set()) if pid)
    tree = _process_tree_pids(roots)

    # Children first. This also kills ffmpeg/deno descendants when the yt-dlp
    # parent is paused or has stopped responding.
    if os.name == "nt":
        for pid in sorted(tree, reverse=True):
            _force_terminate_pid(pid)
    else:
        for process in processes:
            try:
                if process.poll() is None:
                    process.kill()
            except Exception:
                pass

    for process in processes:
        try:
            if process.poll() is None:
                process.kill()
            process.wait(timeout=1.0)
        except Exception:
            pass
        finally:
            unregister_process(process)
'''

replace_once(
    "\n\ndef pause_all_downloads():",
    force_helpers + "\n\ndef pause_all_downloads():",
)

old_cancel = '''def cancel_download_job(index):
    index = int(index)

    # Resume first so termination is deterministic.
    with paused_job_lock:
        paused = index in paused_job_indices

    if paused:
        resume_download_job(index)

    with cancelled_job_lock:
        cancelled_job_indices.add(index)

    update_tree_status(index, "Cancelling…")

    for process in _active_processes_for_job(index):
        try:
            if process.poll() is None:
                process.terminate()
        except Exception:
            pass

    log(f"[{index}] ✕ CANCEL requested.")
'''

new_cancel = '''def cancel_download_job(index):
    index = int(index)

    with cancelled_job_lock:
        cancelled_job_indices.add(index)

    processes = _active_processes_for_job(index)
    with paused_job_lock:
        suspended_pids = set(paused_job_processes.pop(index, set()))
        paused_job_indices.discard(index)

    # Wake a job that is still waiting for a Parallel slot.
    try:
        with live_queue_condition:
            live_queue_condition.notify_all()
    except Exception:
        pass
    try:
        with browser_queue_condition:
            browser_queue_condition.notify_all()
    except Exception:
        pass

    # Make the UI terminal immediately. Delete/Remove is available now even
    # while the background reaper finishes a stubborn process tree.
    update_tree_status(index, "Stopped")
    update_tree_field(index, "speed", "")
    update_tree_field(index, "eta", "")
    schedule_download_history_save(50)

    threading.Thread(
        target=_force_terminate_process_tree,
        args=(processes, suspended_pids),
        daemon=True,
        name=f"Z2SECancel-{index}",
    ).start()

    log(
        f"[{index}] ✕ FORCE CANCEL — row released immediately; "
        f"{len(processes)} root process(es), {len(suspended_pids)} paused PID(s)."
    )
'''
replace_once(old_cancel, new_cancel)

# Stop All gets the same tree-safe behavior instead of terminating parents only.
replace_once(
    '''    with active_processes_lock:
        processes = list(active_processes)

    for process in processes:
        try:
            if process.poll() is None:
                process.terminate()
        except Exception:
            pass

    set_status("إيقاف التحميلات...")''',
    '''    with active_processes_lock:
        processes = list(active_processes)

    threading.Thread(
        target=_force_terminate_process_tree,
        args=(processes, set()),
        daemon=True,
        name="Z2SEStopAll",
    ).start()

    set_status("إيقاف التحميلات...")''',
)

ast.parse(text)
app_path.write_text(text, encoding="utf-8")
app_hash = hashlib.sha256(app_path.read_bytes()).hexdigest()
manifest_path = Path("payload/update_manifest.json")
manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
manifest["version"] = version
manifest["created_by"] = (
    "v33.11 adds deterministic force-cancel for paused/stuck process trees, "
    "releases rows immediately for deletion, and removes cancelled jobs from "
    "the restart queue"
)
manifest["files"][0]["sha256"] = app_hash
manifest["files"][0]["size"] = app_path.stat().st_size
manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
print("VERIFIED v33.11 app.py sha256", app_hash)
