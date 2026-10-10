"""Embedded in app.py at release time; no additional installed file required."""
import os
import re
import shutil
import subprocess
import threading
import time

_js_runtime_lock = threading.Lock()
_js_runtime_cache = None


def _js_runtime_candidates(name):
    candidates = [shutil.which(name)]
    suffix = ".exe" if os.name == "nt" else ""
    candidates.append(os.path.join(BASE_DIR, name + suffix))
    if name == "deno":
        candidates.append(os.path.expanduser("~/.deno/bin/deno" + suffix))
    elif os.name == "nt":
        for key in ("ProgramFiles", "ProgramFiles(x86)", "LOCALAPPDATA"):
            root = os.environ.get(key)
            if root:
                candidates.append(os.path.join(root, "nodejs", "node.exe"))
    found = []
    for path in candidates:
        if path and os.path.isfile(path):
            path = os.path.abspath(path)
            if os.path.normcase(path) not in {os.path.normcase(p) for p in found}:
                found.append(path)
    return found


def discover_js_runtimes(force=False):
    """Validate supported installed runtimes; cache probes for one minute.

    Deno remains preferred. Enable Node >=22 as yt-dlp's secondary solver.
    This does not replace the separate Deno-based PO-token server.
    """
    global _js_runtime_cache
    with _js_runtime_lock:
        now = time.monotonic()
        candidates = {name: _js_runtime_candidates(name) for name in ("deno", "node")}
        fingerprint = []
        for name, paths in candidates.items():
            for path in paths:
                try:
                    stat = os.stat(path)
                    fingerprint.append((name, path, stat.st_mtime_ns, stat.st_size))
                except OSError:
                    pass
        if not force and _js_runtime_cache:
            saved_at, saved_fingerprint, saved = _js_runtime_cache
            if now - saved_at < 60 and fingerprint == saved_fingerprint:
                return [dict(item) for item in saved]
        result = []
        for name, minimum in (("deno", (2, 3, 0)), ("node", (22, 0, 0))):
            for path in candidates[name]:
                try:
                    probe = subprocess.run(
                        [path, "--version"], capture_output=True, text=True,
                        encoding="utf-8", errors="replace", timeout=3,
                        creationflags=(subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0),
                    )
                    pattern = r"^deno (\d+)\.(\d+)\.(\d+)(?:\s|$)" if name == "deno" else r"^v(\d+)\.(\d+)\.(\d+)(?:\s|$)"
                    match = re.match(pattern, (probe.stdout or "").strip())
                    if probe.returncode or not match:
                        continue
                    version = tuple(map(int, match.groups()))
                    if version < minimum:
                        continue
                    result.append({"name": name, "path": path, "version": ".".join(map(str, version))})
                    break
                except (OSError, subprocess.SubprocessError):
                    continue
        _js_runtime_cache = (now, fingerprint, result)
        return [dict(item) for item in result]


def js_runtime_args():
    runtimes = discover_js_runtimes()
    # With none available leave yt-dlp defaults alone, so non-YouTube sites
    # still work and yt-dlp can report its own actionable runtime warning.
    args = ["--no-js-runtimes"] if runtimes else []
    for runtime in runtimes:
        args.extend(["--js-runtimes", runtime["name"] + ":" + runtime["path"]])
    return args


def js_runtime_summary():
    runtimes = discover_js_runtimes()
    if not runtimes:
        return "Missing compatible runtime: install Deno >=2.3 or Node.js >=22"
    return " + ".join(item["name"] + " " + item["version"] for item in runtimes)
