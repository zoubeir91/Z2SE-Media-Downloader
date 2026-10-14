Z2SE v33.16

- Add a watchdog to directly launched, registered FFmpeg processes used for downloads, merging and conversions. Stop and reap an operation after 10 minutes without advancing media counters or an output-file change; paused jobs receive a fresh grace period on resume.
- Ignore repeated warning messages, unchanged frame/time counters and speed fluctuations when deciding whether media is progressing. Existing cancellation and output validation remain in place.
- Add evidence-based PO-token hints to the technical log: missing token/provider, generation/request failure, or explicitly reported client/context mismatch. A generic 403 is not labelled a token failure. Hints do not echo token values or URLs.
- Verify the embedded watchdog source during release packaging. Preserve v33.15 runtime support and FFmpeg path fixes.

Validation: 39 automated tests passed, including a real silent subprocess killed and reaped by the watchdog, pause/resume timing, repeated-output hangs, process cleanup, token diagnostics and package hashes. One legacy fixture test is skipped. Windows UI and live site downloads require on-device validation.

Scope: this is a hang mitigation, not a fix for FFmpeg CVEs. It does not replace or upgrade the installed FFmpeg executable. It covers directly registered FFmpeg processes, not FFmpeg children launched internally by yt-dlp, standalone probes or previews. Legitimate direct processing with no observable progress for 10 minutes can also time out. SABR, YouTube client defaults and the yt-dlp release channel are unchanged.
