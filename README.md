# Z²SE Media Downloader

<p align="center">
  <strong>A modern Windows media downloader built around yt-dlp and FFmpeg.</strong><br>
  Fast, simple for everyday users, and resilient when media sites change.
</p>

<p align="center">
  <a href="https://github.com/zoubeir91/Z2SE-Media-Downloader/releases/latest"><img alt="Latest release" src="https://img.shields.io/github/v/release/zoubeir91/Z2SE-Media-Downloader?display_name=tag&sort=semver"></a>
  <a href="https://github.com/zoubeir91/Z2SE-Media-Downloader/releases"><img alt="Downloads" src="https://img.shields.io/github/downloads/zoubeir91/Z2SE-Media-Downloader/total"></a>
  <a href="LICENSE"><img alt="License" src="https://img.shields.io/github/license/zoubeir91/Z2SE-Media-Downloader"></a>
  <img alt="Platform" src="https://img.shields.io/badge/platform-Windows-0078D4">
  <img alt="Python" src="https://img.shields.io/badge/Python-3.x-3776AB">
</p>

<p align="center">
  <a href="https://github.com/zoubeir91/Z2SE-Media-Downloader/releases/latest"><strong>Download latest release</strong></a>
  · <a href="SUPPORT.md">Support</a>
  · <a href="CONTRIBUTING.md">Contributing</a>
  · <a href="SECURITY.md">Security</a>
</p>

---

## What is Z²SE?

Z²SE Media Downloader is a Windows desktop application for downloading media through a clean graphical interface without forcing users to work with command-line tools.

It combines a straightforward everyday workflow with a more resilient backend based on **yt-dlp**, **FFmpeg**, adaptive recovery, browser hand-off support, and automatic updates.

The goal is simple: **paste a link, choose what you want, and download it with as little friction as possible.**

## Highlights

- **Simple Windows interface** designed for non-technical users.
- **Full media downloads** with quality and format controls.
- **PART / section downloads** for downloading only a selected time range.
- **Smart Recovery** that can try alternate YouTube extraction routes when the normal path fails.
- **Adaptive recovery memory** to reduce repeated failed attempts in the same session.
- **Browser Bridge** for sending supported media pages from the browser to Z²SE.
- **Download history and queue management** with pause, resume, stop and retry workflows.
- **Health Check** for key dependencies such as yt-dlp, FFmpeg, Deno, PO provider and Browser Bridge.
- **Built-in updater** so users can move to newer releases from inside the app.
- **Modern dark UI** focused on clarity rather than advanced settings clutter.

## Download

The recommended way to get Z²SE is from the latest GitHub release:

**[Download the latest Z²SE release](https://github.com/zoubeir91/Z2SE-Media-Downloader/releases/latest)**

Release packages are published as `Z2SE_UPDATE.zip` and are also used by the application's built-in updater.

> Z²SE is currently developed and tested primarily for Windows.

## Basic workflow

1. Open Z²SE.
2. Paste a supported media URL.
3. Leave start/end empty for the full media, or enter a time range for **PART** mode.
4. Choose the desired quality / format.
5. Start the download.
6. Use the Downloads area to follow progress, pause, resume or retry when needed.

## Reliability and recovery

Media platforms—especially YouTube—change frequently. Z²SE therefore includes recovery logic instead of relying on one fixed extraction path.

When a normal attempt fails, Z²SE can classify common failure families such as access/403 errors, authentication requirements, provider failures and unavailable formats, then choose an appropriate fallback route instead of blindly repeating the same request.

The application also contains self-repair behavior for selected local dependencies used by YouTube extraction.

## Browser integration

Z²SE includes a local Browser Bridge that can receive supported download requests from browser-side integrations and bring the desktop app to the foreground.

Normal manual startup remains separate from browser-triggered hand-off so old draft PART links are not restored into the editor.

## Updates

Z²SE has an in-app update flow backed by GitHub Releases.

Each published release is built through GitHub Actions, validated for Python syntax, packaged, and exposed to the updater as a new release asset.

See the [Releases](https://github.com/zoubeir91/Z2SE-Media-Downloader/releases) page for version notes.

## Current project status

Z²SE is under active development. The focus is currently on:

- download reliability,
- YouTube recovery behavior,
- simple UX for everyday users,
- clean Windows-style design,
- self-diagnostics and self-repair,
- safe incremental updates.

## Troubleshooting

If a download fails:

1. Update to the latest Z²SE release.
2. Run **Outils → Diagnostic système / Health Check**.
3. Confirm yt-dlp and FFmpeg are available.
4. Retry the download once so Smart Recovery can run.
5. If the problem persists, open a bug report and include the Z²SE version, the affected site, whether it was FULL or PART mode, and the relevant log excerpt.

See [SUPPORT.md](SUPPORT.md) for the full support checklist.

Please avoid posting private cookies, authentication tokens, passwords or other secrets in issues.

## Contributing

Bug reports, reproducible test cases and focused improvements are welcome. Please read [CONTRIBUTING.md](CONTRIBUTING.md) before opening a contribution.

By participating in the project, please follow the [Code of Conduct](CODE_OF_CONDUCT.md).

For security-sensitive reports, follow [SECURITY.md](SECURITY.md) instead of opening a public issue.

## Technology

Z²SE is built around:

- Python / Tkinter
- yt-dlp
- FFmpeg / ffprobe
- Deno-based components where needed for modern YouTube extraction
- GitHub Actions and GitHub Releases for update publishing

## License

Z²SE Media Downloader is released under the [MIT License](LICENSE).

## Disclaimer

Z²SE is a general-purpose media downloading tool. Users are responsible for respecting the terms of service of websites they access, applicable copyright rules, and any local laws or permissions governing the media they download.

---

<p align="center"><strong>Z²SE — fast, simple, reliable.</strong></p>
