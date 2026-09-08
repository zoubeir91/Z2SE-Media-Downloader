"""Z2SE v32.49 playlist planning primitives.

Dependency-free helpers for safe playlist preview/selection. The GUI integration
will call yt-dlp for metadata, then pass the returned entries through this layer.
"""
from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Iterable


@dataclass
class PlaylistEntry:
    index: int
    media_id: str
    title: str
    url: str
    duration: float | None = None
    uploader: str = ""
    selected: bool = True

    def to_dict(self) -> dict:
        return asdict(self)


def _safe_duration(value):
    try:
        if value in (None, ""):
            return None
        value = float(value)
        return value if value >= 0 else None
    except (TypeError, ValueError):
        return None


def normalize_playlist_entries(raw_entries: Iterable[dict]) -> list[dict]:
    """Normalize yt-dlp flat-playlist entries into stable UI rows."""
    rows: list[dict] = []
    for fallback_index, raw in enumerate(raw_entries or [], 1):
        if not isinstance(raw, dict):
            continue
        media_id = str(raw.get("id") or "").strip()
        url = str(raw.get("webpage_url") or raw.get("url") or "").strip()
        title = str(raw.get("title") or raw.get("fulltitle") or media_id or f"Item {fallback_index}").strip()
        try:
            index = int(raw.get("playlist_index") or raw.get("playlist_autonumber") or fallback_index)
        except (TypeError, ValueError):
            index = fallback_index
        rows.append(
            PlaylistEntry(
                index=max(1, index),
                media_id=media_id,
                title=title[:500],
                url=url,
                duration=_safe_duration(raw.get("duration")),
                uploader=str(raw.get("uploader") or raw.get("channel") or "").strip()[:300],
                selected=True,
            ).to_dict()
        )
    rows.sort(key=lambda item: (item["index"], item["title"].lower()))
    return rows


def select_range(entries: list[dict], start: int | None = None, end: int | None = None) -> list[dict]:
    """Select only the inclusive playlist-index range; None keeps an open edge."""
    start = max(1, int(start)) if start not in (None, "") else None
    end = max(1, int(end)) if end not in (None, "") else None
    if start is not None and end is not None and start > end:
        start, end = end, start
    result = []
    for entry in entries or []:
        row = dict(entry)
        idx = int(row.get("index") or 0)
        row["selected"] = (start is None or idx >= start) and (end is None or idx <= end)
        result.append(row)
    return result


def apply_search(entries: list[dict], query: str) -> list[dict]:
    """Return visible entries matching title/uploader/id without mutating selection."""
    needle = (query or "").strip().casefold()
    if not needle:
        return [dict(item) for item in entries or []]
    visible = []
    for item in entries or []:
        haystack = " ".join(
            str(item.get(key) or "") for key in ("title", "uploader", "media_id")
        ).casefold()
        if needle in haystack:
            visible.append(dict(item))
    return visible


def selected_entries(entries: list[dict]) -> list[dict]:
    return [dict(item) for item in entries or [] if item.get("selected", True)]


def chunk_entries(entries: list[dict], offset: int = 0, limit: int = 100) -> tuple[list[dict], int | None]:
    """Lazy UI paging helper for very large playlists."""
    offset = max(0, int(offset or 0))
    limit = min(500, max(1, int(limit or 100)))
    page = [dict(item) for item in (entries or [])[offset : offset + limit]]
    next_offset = offset + len(page)
    if next_offset >= len(entries or []):
        next_offset = None
    return page, next_offset


def estimate_selected_duration(entries: list[dict]) -> float | None:
    values = [item.get("duration") for item in selected_entries(entries)]
    known = [float(value) for value in values if value is not None]
    if not known:
        return None
    return sum(known)
