from __future__ import annotations

import os
import shutil
import stat
import subprocess
import tempfile
from pathlib import Path

from skills._shared.python.skill_testing import assert_skill_contract


def test_automation_semantic_commit_autostage_contract() -> None:
    skill_root = Path(__file__).resolve().parents[1]
    assert_skill_contract(skill_root)


def _run(
    args: list[str],
    *,
    cwd: Path,
    env: dict[str, str] | None = None,
    input_text: str | None = None,
) -> subprocess.CompletedProcess[str]:
    proc_env = os.environ.copy()
    if env:
        proc_env.update(env)
    return subprocess.run(
        args,
        cwd=str(cwd),
        env=proc_env,
        text=True,
        input=input_text,
        capture_output=True,
    )


def _init_repo(dir_path: Path) -> None:
    for cmd in [
        ["git", "init", "-q"],
        ["git", "checkout", "-q", "-B", "main"],
        ["git", "config", "user.email", "test@example.com"],
        ["git", "config", "user.name", "Test User"],
        ["git", "config", "commit.gpgsign", "false"],
        ["git", "config", "tag.gpgSign", "false"],
    ]:
        proc = _run(cmd, cwd=dir_path, env=None)
        assert proc.returncode == 0, proc.stderr


def _write_executable(dir_path: Path, name: str, contents: str) -> None:
    path = dir_path / name
    path.write_text(contents, encoding="utf-8")
    path.chmod(path.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)


def test_automation_semantic_commit_autostage_flow_works_with_semantic_commit_binary() -> None:
    semantic_commit = shutil.which("semantic-commit")
    assert semantic_commit, "semantic-commit binary not found on PATH"

    with tempfile.TemporaryDirectory() as temp_dir:
        repo = Path(temp_dir)
        _init_repo(repo)
        (repo / "a.txt").write_text("hello\n", encoding="utf-8")

        proc = _run(["git", "add", "-A"], cwd=repo, env=None)
        assert proc.returncode == 0, proc.stderr

        with tempfile.TemporaryDirectory() as tools_dir:
            tools = Path(tools_dir)
            _write_executable(
                tools,
                "git-scope",
                "#!/usr/bin/env bash\n"
                "set -euo pipefail\n"
                "if [[ \"${1-}\" == \"help\" ]]; then\n"
                "  exit 0\n"
                "fi\n"
                "if [[ \"${1-}\" != \"commit\" || \"${2-}\" != \"HEAD\" || \"${3-}\" != \"--no-color\" ]]; then\n"
                "  echo \"unexpected args: $*\" >&2\n"
                "  exit 2\n"
                "fi\n"
                "echo \"GIT_SCOPE_OK\"\n",
            )
            path_env = f"{tools}:/usr/bin:/bin:/usr/sbin:/sbin"

            proc = _run(
                [semantic_commit, "commit"],
                cwd=repo,
                env={"PATH": path_env},
                input_text="chore: test\n",
            )

        assert proc.returncode == 0, proc.stderr
        assert "warning:" not in proc.stderr
        assert "error:" not in proc.stderr
        assert "GIT_SCOPE_OK" in proc.stdout

        head = _run(["git", "rev-parse", "--verify", "HEAD"], cwd=repo, env=None)
        assert head.returncode == 0
