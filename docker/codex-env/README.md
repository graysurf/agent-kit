# Docker Codex env (Ubuntu 24.04)

This folder defines a Linux container development environment intended to mirror the macOS `zsh-kit` + `codex-kit` workflow as closely as practical.

## Build

```sh
docker build -f docker/codex-env/Dockerfile -t codex-env:ubuntu24 .
```

Build-time pinning (recommended):

```sh
docker build -f docker/codex-env/Dockerfile -t codex-env:ubuntu24 \
  --build-arg ZSH_KIT_REF=main \
  --build-arg CODEX_KIT_REF=main \
  .
```

Build with tools preinstalled (can be slow; installs optional tools by default):

```sh
docker build -f docker/codex-env/Dockerfile -t codex-env:ubuntu24-tools \
  --build-arg INSTALL_TOOLS=1 \
  .
```

Notes:
- `visual-studio-code` cannot be installed via Linuxbrew; `INSTALL_VSCODE=1` uses the Microsoft apt repo to install `code`.
- `mitmproxy` is macOS-only in Homebrew (cask); it is installed via `apt` instead.

## Tool audit (Ubuntu 24.04)

Runs `brew install -n` across `zsh-kit` tool lists and prints a TSV report:

```sh
docker run --rm codex-env:ubuntu24 /opt/codex-env/bin/audit-tools.sh | sed -n '1,40p'
```

## Interactive shell

```sh
docker run --rm -it codex-env:ubuntu24 zsh -l
```
