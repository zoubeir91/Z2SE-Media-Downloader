# Contributing to Z²SE Media Downloader

Thanks for taking the time to help improve Z²SE.

## Before opening an issue

Please check the latest release and confirm the problem still happens there.

For download failures, include:

- Z²SE version
- Windows version
- affected website
- FULL or PART mode
- selected format/quality
- whether the failure is reproducible
- the smallest useful log excerpt

Do **not** post cookies, passwords, tokens, private URLs or other secrets.

## Bug reports

A good bug report explains:

1. what you expected,
2. what actually happened,
3. exact steps to reproduce it,
4. whether it happens every time,
5. any relevant error message or log output.

## Feature requests

Keep feature requests focused on a real user problem. Z²SE intentionally favors a simple everyday interface over exposing every low-level yt-dlp or network option.

## Pull requests

Please keep pull requests small and focused where possible.

- Do not mix unrelated UI and download-engine changes in one PR.
- Preserve the existing updater and release flow unless the PR specifically targets it.
- Avoid changing fallback/recovery behavior without explaining the failure mode being addressed.
- Test Python syntax before submitting.
- For UI changes, include a screenshot when practical.

## Project direction

Z²SE currently prioritizes:

- reliability,
- simple UX,
- clear diagnostics,
- safe updates,
- resilient media extraction,
- polished Windows presentation.

Thanks for helping make Z²SE better.
