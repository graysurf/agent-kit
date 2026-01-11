# scripts

Repo-local command entrypoints and helpers for codex-kit.

## Structure

```text
scripts/
├── build/          Tooling to generate bundled commands.
├── commands/       Standalone command entrypoints used by skills and docs.
├── db-connect/     DB connection helpers (psql/mysql/mssql wrappers).
├── codex-tools.sh  Single-source loader for repo tools.
└── env.zsh         Environment defaults shared by repo scripts.
```

## Bundling wrappers

Use `build/bundle-wrapper.zsh` to inline a wrapper (and its `source` files)
into a single executable script. This is helpful when you want a portable,
repo-local command without external dependencies on wrapper paths.

Example (git-tools):

```zsh
zsh -f scripts/build/bundle-wrapper.zsh \
  --input $HOME/.config/zsh/cache/wrappers/bin/git-tools \
  --output scripts/commands/git-tools \
  --entry git-tools
```

Notes:

- Only simple `source` lines and the `typeset -a sources=(...)` pattern
  are supported.
- The bundler writes a shebang + minimal env exports into the output file.
- If the wrapper relies on side effects (PATH, cache dirs, etc.), you may
  need to expand the bundler to inline those sections too.

## Validation

- Skill contract lint: `scripts/validate_skill_contracts.sh`
