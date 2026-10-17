Z2SE v33.18

- Refresh the desktop interface with a calmer slate palette, one blue primary action, consistent secondary buttons and compact native menu controls.
- Separate import actions from quality/concurrency controls so the Download button remains visible at the minimum window width.
- Give the download list clearer spacing, a separate row of selection shortcuts and horizontal scrolling for all columns.
- Reserve space for the details panel before allocating the table width. Adapt the preview and helper text to available height so download controls remain visible in shorter windows.
- Use a neutral Ready badge instead of claiming the download engine has passed a health check.

Validation: 47 automated tests passed; one old fixture test skipped. Release packaging and embedded-module verification passed. Visually inspected empty/populated layouts at 1280x860 and 1020x720 using Tk in Linux. Native Windows fonts, scaling and menu behavior still require on-device verification.
