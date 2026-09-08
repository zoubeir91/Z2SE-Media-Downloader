"""Z2SE v32.49 persistent queue primitives.

This module is intentionally dependency-free so the release patch can embed the
same logic into app.py after integration anchors are validated against the
v32.48 release payload.
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import tempfile
import time
from pathlib import Path
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

QUEUE_SCHEMA_VERSION = 1
SECRET_KEYS = {
    "cookie", "cookies", "authorization", "password", "passwd", "secret",
    "token", "po_token", "pot", "api_key", "key",
}
TRACKING_KEYS = {"si", "pp", "fbclid", "gclid"}


def normalize_source_url(url: str) -> str:
    """Return a stable URL suitable for duplicate detection.

    Tracking parameters are removed, query ordering is normalized and fragments
    are discarded. Authentication/token-like query values are never retained.
    """
    raw = (url or "").strip()
    if not raw:
        return ""
    try:
        parts = urlsplit(raw)
        host = parts.netloc.lower()
        scheme = parts.scheme.lower() or "https"
        clean = []
        for key, value in parse_qsl(parts.query, keep_blank_values=True):
            low = key.lower()
            if low.startswith("utm_") or low in TRACKING_KEYS or low in SECRET_KEYS:
                continue
            clean.append((key, value))
        clean.sort(key=lambda item: (item[0].lower(), item[1]))
        path = re.sub(r"/{2,}", "/", parts.path or "/")
        return urlunsplit((scheme, host, path, urlencode(clean, doseq=True), ""))
    except Exception:
        return raw


def source_identity(url: str, media_id: str | None = None) -> str:
    stable = (media_id or "").strip() or normalize_source_url(url)
    return hashlib.sha256(stable.encode("utf-8", "replace")).hexdigest()


def sanitize_job(job: dict) -> dict:
    """Return queue-safe state and intentionally drop credentials/secrets."""
    allowed = {
        "id", "url", "media_id", "title", "mode", "quality", "output_dir",
        "status", "progress", "created_at", "updated_at", "playlist_id",
        "playlist_index", "playlist_range", "selected", "force_download",
        "error", "attempts",
    }
    safe = {key: job.get(key) for key in allowed if key in job}
    safe["url"] = normalize_source_url(str(safe.get("url") or ""))
    safe["id"] = str(safe.get("id") or source_identity(safe["url"], safe.get("media_id")))
    safe["status"] = str(safe.get("status") or "pending")
    safe["progress"] = max(0.0, min(100.0, float(safe.get("progress") or 0.0)))
    safe["attempts"] = max(0, int(safe.get("attempts") or 0))
    now = int(time.time())
    safe["created_at"] = int(safe.get("created_at") or now)
    safe["updated_at"] = now
    return safe


def restore_jobs(jobs: list[dict]) -> list[dict]:
    restored = []
    for raw in jobs or []:
        if not isinstance(raw, dict):
            continue
        job = sanitize_job(raw)
        if job["status"] in {"running", "starting", "postprocessing"}:
            job["status"] = "pending"
            job["error"] = "Restored after app restart"
        restored.append(job)
    return restored


def load_queue(path: str | os.PathLike) -> list[dict]:
    target = Path(path)
    try:
        payload = json.loads(target.read_text(encoding="utf-8"))
        if int(payload.get("schema", 0)) != QUEUE_SCHEMA_VERSION:
            return []
        return restore_jobs(payload.get("jobs") or [])
    except (FileNotFoundError, OSError, ValueError, TypeError, json.JSONDecodeError):
        return []


def save_queue_atomic(path: str | os.PathLike, jobs: list[dict]) -> None:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "schema": QUEUE_SCHEMA_VERSION,
        "saved_at": int(time.time()),
        "jobs": [sanitize_job(job) for job in jobs if isinstance(job, dict)],
    }
    fd, temp_name = tempfile.mkstemp(prefix=target.name + ".", suffix=".tmp", dir=str(target.parent))
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as handle:
            json.dump(payload, handle, ensure_ascii=False, indent=2)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temp_name, target)
    finally:
        try:
            if os.path.exists(temp_name):
                os.unlink(temp_name)
        except OSError:
            pass


def is_duplicate(candidate: dict, jobs: list[dict]) -> bool:
    if candidate.get("force_download"):
        return False
    identity = source_identity(candidate.get("url", ""), candidate.get("media_id"))
    for existing in jobs or []:
        if not isinstance(existing, dict):
            continue
        if existing.get("status") in {"cancelled", "failed"}:
            continue
        if source_identity(existing.get("url", ""), existing.get("media_id")) == identity:
            return True
    return False
