# Image Processing Guide

Entrypoint:

```bash
image-processing --help
```

## Design rules (important)

- The CLI has exactly two subcommands: `convert` and `svg-validate`.
- By default, the CLI refuses to overwrite outputs. Use `--overwrite` to replace.
- `convert` requires exactly one `--in` and accepts `svg|png|jpg|jpeg|webp` inputs.
- `convert` requires `--to png|webp|jpg`, and `--out` must match that target (`.jpeg` is accepted for `--to jpg`).
- `svg-validate` requires exactly one `--in` and an explicit `--out` ending in `.svg`.
- When `--json` is used, stdout is JSON only (logs go to stderr).
- JSON/report output includes `source.input_path` and `source.input_format`.

## Common flags

- Inputs:
  - `convert`: `--in <path>` (exactly one)
  - `svg-validate`: `--in <path>` (exactly one)
- Output:
  - `--out <file>` (required)
  - `--overwrite` (optional)
- Convert target:
  - `--to png|webp|jpg` (required for `convert`)
  - `--width`, `--height` (optional, raster targets only)
- Reproducibility:
  - `--dry-run` (no image outputs written)
  - `--json` (machine summary to stdout, plus `summary.json` under `out/image-processing/runs/<run_id>/`)
  - `--report` (writes `report.md` and `summary.json` under `out/image-processing/runs/<run_id>/`)

## Subcommands

### `convert`

Convert `svg|png|jpg|jpeg|webp` input to `png`, `webp`, or `jpg`.

```bash
image-processing \
  convert \
  --in path/to/icon.svg \
  --to webp \
  --out out/icon.webp \
  --json

image-processing \
  convert \
  --in path/to/photo.png \
  --to jpg \
  --out out/photo.jpg \
  --width 512 \
  --height 512 \
  --json
```

Rules:

- Must include exactly one `--in`, plus `--to` and `--out`.
- `--out` extension must match `--to` (`.jpeg` is accepted for `--to jpg`).
- `--to jpg` flattens alpha onto a white background.

### `svg-validate`

Validate and sanitize one SVG input into one SVG output.

```bash
image-processing \
  svg-validate \
  --in path/to/input.svg \
  --out out/input.cleaned.svg \
  --json
```

Rules:

- Requires exactly one `--in`.
- Requires `--out`, and output must be `.svg`.
- Does not support convert-only flags (`--to`, `--width`, `--height`).

## Known removed subcommands

The following legacy subcommands are no longer supported and now return usage errors:

- `generate`
- `info`
- `auto-orient`
- `resize`
- `rotate`
- `crop`
- `pad`
- `flip`
- `flop`
- `optimize`
