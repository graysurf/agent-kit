from __future__ import annotations

import subprocess
from pathlib import Path

from .conftest import repo_root


ALLOWED_DOTENV_FILES = {
    ".env.example",
    ".env.sample",
    ".env.template",
}


def list_tracked_files(repo: Path) -> list[str]:
    return subprocess.check_output(["git", "-C", str(repo), "ls-files"], text=True).splitlines()


def is_forbidden_dotenv(path: str) -> bool:
    name = Path(path).name
    if name == ".env":
        return True
    if name.startswith(".env.") and name not in ALLOWED_DOTENV_FILES:
        return True
    return False


def test_no_tracked_dotenv_files():
    repo = repo_root()
    offenders = [p for p in list_tracked_files(repo) if is_forbidden_dotenv(p)]
    assert not offenders, (
        "Refusing to track dotenv files (they often contain secrets). "
        "Remove them from git history / index and rely on .gitignore:\n"
        + "\n".join(f"- {p}" for p in offenders)
    )
