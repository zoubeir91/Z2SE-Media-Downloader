Z2SE v33.15

- Detect and validate Deno >=2.3 and Node.js >=22 for YouTube JavaScript challenges. Deno remains preferred; a compatible installed Node is enabled as an alternative. Includes full, cached, section, metadata and playlist commands.
- Cache runtime version probes and refresh when executable paths or files change. Show runtime availability in both health checks and exported diagnostics.
- Include the unpublished v33.14 fix for stale Winget FFmpeg/FFprobe paths. Preserve v33.13 cancellation fixes and previous Forja/audio fixes.
- Bound yt-dlp self-update to 120 seconds and restore update controls on failure.
- Build releases from the actual reviewed source with version checks, tests and SHA-256 manifests, instead of patching whatever release happens to be latest.

Node support here applies to YouTube challenge solving. The separate bgutil PO-token server still uses Deno. Runtime installations and the user's system packages are not changed by this update. The existing yt-dlp update action updates its official executable (including bundled EJS).

Validation: automated runtime discovery/fallback, command integration, update timeout and package-integrity tests. Live media downloads and Windows UI still require validation on a Windows installation.

References:
https://github.com/yt-dlp/yt-dlp/wiki/EJS
https://deno.com/blog/cloudflare
