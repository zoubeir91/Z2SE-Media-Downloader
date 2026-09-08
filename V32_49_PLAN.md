# Z2SE v32.49 — Smart Queue foundation

Development branch only. Do not publish from this branch.

## Research-backed priorities

Current mature yt-dlp GUIs converge on a few high-value capabilities: a queue that survives restarts, pause/resume/retry controls, playlist item selection and lazy loading for very large playlists, download archive/duplicate protection, subtitles/metadata/thumbnail/chapters, optional SponsorBlock, cookies/auth controls, presets, and engine/dependency health.

## v32.49 first package

1. Persistent queue state stored locally with atomic writes.
2. Restart recovery: interrupted/running jobs are restored as resumable pending jobs rather than silently lost.
3. Duplicate protection based on normalized source URL / stable media identity when available, with an explicit force-download escape hatch.
4. Playlist Pro foundation: selected-item/range representation designed so large playlists can be added without eagerly materializing every entry.
5. Preserve v32.48 FULL/PART/MP3/TURBO behavior, Smart Recovery route, HTTP 429 protection, Facebook/Meta recovery, diagnostics, TV Safe and updater integrity checks.

## Safety / release gates

- No release_version.txt bump until the patch compiles against the actual previous release payload.
- No merge/release until structural markers and Python compilation pass.
- Existing updater remains the delivery mechanism.
- New persistent state must never store cookies, passwords, auth headers or PO tokens.
- Queue-state writes must be atomic and corruption-tolerant.

## Follow-up package candidates

- Subtitle/metadata/thumbnail/chapter controls.
- Optional SponsorBlock mark/remove.
- Advanced presets/templates without cluttering Simple mode.
- Engine Manager with tested rollback for yt-dlp/provider/FFmpeg components.
- Smart recovery preference memory.
- Clipboard URL cleanup/watch and channel/playlist observation.
