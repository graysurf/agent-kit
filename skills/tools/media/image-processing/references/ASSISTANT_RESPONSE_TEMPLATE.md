# Assistant completion template (fixed)

Use this template after a successful image-processing run.

```md
Output:
- [<output file or folder name>](/absolute/path/to/output)

Next prompt:
- "<a single-sentence prompt that repeats the same task with concrete paths/options>"

Notes:
- Report (if used): [report.md](/absolute/path/to/out/image-processing/runs/<run_id>/report.md)
- Summary (if `--json`/`--report` used): [summary.json](/absolute/path/to/out/image-processing/runs/<run_id>/summary.json)
- Warnings (if any): <short list>
```

## Prompt guidance (for reuse)

A good “next prompt” should include:

- The subcommand (`convert` or `svg-validate`)
- Exact input path (`--in`)
- Exact output path (`--out`)
- Exact convert target (`--to png|webp|jpg`) when using `convert`
- Any non-default flags (e.g., `--width`, `--height`, `--overwrite`, `--report`, `--dry-run`)

Example:

```text
Convert `assets/icons/logo.svg` to WebP and write to `out/image-processing/logo.webp` with `--report`.
```
