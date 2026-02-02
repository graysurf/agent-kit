---
name: screenshot
description: Capture OS-level screenshots on macOS/Linux/Windows via bundled helpers.
---

# Screenshot

Capture OS-level screenshots with bundled helpers on macOS/Linux/Windows.

## Contract

Prereqs:

- `bash` and `python3` for `scripts/screenshot.sh` (macOS/Linux).
- macOS: `swift` for permission preflight and Screen Recording permission.
- Linux: `scrot`, `gnome-screenshot`, or ImageMagick `import` (optional `xdotool` for active-window capture).
- Windows: `powershell` for `scripts/take_screenshot.ps1`.

Inputs:

- `scripts/screenshot.sh` (macOS/Linux) forwards args to `scripts/take_screenshot.py`.
- Supported flags include `--mode`, `--path`, `--app`, `--window-name`, `--window-id`, `--active-window`, `--region`, `--list-windows`.
- `scripts/take_screenshot.ps1` (Windows) supports `-Mode`, `-Path`, `-Region`, `-ActiveWindow`, `-WindowHandle`.

Outputs:

- Screenshot file path(s) printed to stdout (one per line).
- Files written to the requested path, OS default screenshot folder, or temp location.

Exit codes:

- `0`: success
- `1`: runtime failure or missing dependency
- `2`: usage error or unsupported platform
- `3`: macOS permission preflight blocked in sandbox

Failure modes:

- macOS Screen Recording permission missing or denied.
- No supported screenshot tool found on Linux.
- PowerShell missing on Windows.
- App/window selection returns no matches.

## Scripts (only entrypoints)

- `$CODEX_HOME/skills/tools/media/screenshot/scripts/screenshot.sh`
- `$CODEX_HOME/skills/tools/media/screenshot/scripts/take_screenshot.ps1`

## Usage

- macOS/Linux default location:

```bash
$CODEX_HOME/skills/tools/media/screenshot/scripts/screenshot.sh
```

- macOS/Linux explicit output (recommended for Codex inspection):

```bash
$CODEX_HOME/skills/tools/media/screenshot/scripts/screenshot.sh --path "$CODEX_HOME/out/screenshot.png"
```

- macOS app capture with preflight:

```bash
$CODEX_HOME/skills/tools/media/screenshot/scripts/screenshot.sh --preflight --app "Codex" --mode temp
```

- Windows (PowerShell):

```powershell
powershell -ExecutionPolicy Bypass -File $CODEX_HOME/skills/tools/media/screenshot/scripts/take_screenshot.ps1 -Mode temp
```

## Notes

- For Codex inspection outputs, prefer `--path "$CODEX_HOME/out/..."` instead of `--mode temp`.
- Third-party license for helper scripts: `references/LICENSE.txt`.
