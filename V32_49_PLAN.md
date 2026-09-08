# Z2SE v32.49 — Smart Queue + Playlist Pro

Status: implementation complete and release-gated against the real v32.48 update payload.

## Included

- Persistent queue state for queued/running manual download jobs.
- Restart recovery: interrupted active jobs return to the editor as retryable pending jobs.
- Atomic queue persistence with no cookies, passwords, authorization headers or token-like credentials serialized.
- Duplicate/archive protection keyed by normalized source plus mode/range/format/quality.
- Completed archive capped to a bounded local history for accidental duplicate prevention.
- Playlist Pro preview for playlists/channels with title/duration list, text filtering, range selection, multi-select and MP4/MP3 add-to-queue.
- Existing v32.48 Smart Recovery, provider diagnostics, HTTP 429 protection, Facebook/Meta recovery, TV Safe, FULL/PART/TURBO/MP3 and updater integrity preserved.

## Release gates passed

- Queue and playlist core regression tests passed on Windows/Python 3.12.
- v32.49 release patch compiled successfully.
- Patch applied successfully to the actual public v32.48 `Z2SE_UPDATE.zip` payload.
- Patched `app.py` and updater compiled successfully.
- Manifest version, SHA-256 hashes and file sizes verified.
- Required v32.48 Smart Recovery and diagnostics markers verified after the v32.49 patch.

Temporary payload-probe and patch-fixer workflows were removed before merge.
