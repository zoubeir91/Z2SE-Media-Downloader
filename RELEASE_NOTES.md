Z2SE v33.17

- Add offline startup/dependency diagnostics for the actual yt-dlp executable used by Z2SE, instead of inspecting unrelated host-Python packages.
- Report the Cryptodome/Crypto dependency and version when yt-dlp exposes it. Clearly distinguish a missing/unreported dependency from an engine startup failure. Detection does not certify HLS or cookie decryption compatibility.
- Recheck the executable after a successful yt-dlp self-update before recording the check as successful. Restore update controls on check failure or timeout.
- Display the result in both health views and exported diagnostics. The check ignores user config and plugins, supplies no URL, and never asks for browser cookies. Only allowlisted version/dependency fields are retained.
- Cache results briefly and invalidate them after the executable changes. Verify the embedded checker during release packaging.

Validation: 47 automated tests passed; one old fixture test skipped. Also tested the diagnostic against the official yt-dlp 2026.08.19 portable executable in Linux. Windows UI, Windows bundled dependency reporting, encrypted HLS and browser-cookie decryption remain untested on-device.

No separate cryptography-library installation or upgrade is performed. Z2SE uses yt-dlp.exe and its updater; the PyCryptodome 4 namespace transition is left to compatible upstream distributions. Existing FFmpeg watchdog, Deno preference and release-channel behavior are preserved.

Sources reviewed on 2026-10-17:
https://www.pycryptodome.org/src/changelog
https://github.com/yt-dlp/yt-dlp/issues/17820
https://github.com/yt-dlp/yt-dlp/releases/tag/2026.08.19
