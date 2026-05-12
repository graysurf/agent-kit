from __future__ import annotations

import os
import stat
import subprocess
from pathlib import Path

from skills._shared.python.skill_testing import assert_entrypoints_exist, assert_skill_contract


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "close-gitlab-mr.sh"


def test_workflows_mr_gitlab_close_gitlab_mr_contract() -> None:
    skill_root = Path(__file__).resolve().parents[1]
    assert_skill_contract(skill_root)


def test_workflows_mr_gitlab_close_gitlab_mr_entrypoints_exist() -> None:
    skill_root = Path(__file__).resolve().parents[1]
    assert_entrypoints_exist(skill_root, ["scripts/close-gitlab-mr.sh"])


def _run(
    args: list[str],
    *,
    cwd: Path,
    env: dict[str, str] | None = None,
) -> subprocess.CompletedProcess[str]:
    proc_env = os.environ.copy()
    if env:
        proc_env.update(env)
    return subprocess.run(
        args,
        cwd=str(cwd),
        env=proc_env,
        text=True,
        capture_output=True,
        check=False,
    )


def _git(repo: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return _run(["git", *args], cwd=repo)


def _assert_ok(proc: subprocess.CompletedProcess[str]) -> None:
    assert proc.returncode == 0, proc.stderr


def _write(repo: Path, rel_path: str, content: str) -> None:
    file_path = repo / rel_path
    file_path.parent.mkdir(parents=True, exist_ok=True)
    file_path.write_text(content, encoding="utf-8")


def _seed_commit(repo: Path, files: dict[str, str], *, message: str) -> None:
    for rel_path, content in files.items():
        _write(repo, rel_path, content)
    _assert_ok(_git(repo, "add", "-A"))
    _assert_ok(_git(repo, "commit", "-q", "-m", message))


def _init_repo(repo: Path) -> None:
    _assert_ok(_run(["git", "init", "-q"], cwd=repo))
    _assert_ok(_git(repo, "checkout", "-q", "-B", "main"))
    _assert_ok(_git(repo, "config", "user.email", "test@example.com"))
    _assert_ok(_git(repo, "config", "user.name", "Test User"))
    _seed_commit(repo, {"README.md": "seed\n"}, message="chore: seed repository")


def _install_fake_glab(tmp_path: Path) -> tuple[Path, Path]:
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    log_path = tmp_path / "glab.log"
    glab_path = bin_dir / "glab"
    glab_path.write_text(
        "#!/usr/bin/env bash\n"
        "set -euo pipefail\n"
        "printf '%s\\n' \"glab $*\" >> \"${GLAB_FAKE_LOG:?}\"\n"
        "if [[ \"${1-}\" == \"auth\" && \"${2-}\" == \"status\" ]]; then\n"
        "  if [[ \"${GLAB_FAKE_AUTH_STATUS:-ok}\" == \"fail\" ]]; then\n"
        "    echo \"auth failed\" >&2\n"
        "    exit 1\n"
        "  fi\n"
        "  exit 0\n"
        "fi\n"
        "if [[ \"${1-}\" == \"ci\" && \"${2-}\" == \"status\" ]]; then\n"
        "  if [[ \"${GLAB_FAKE_PIPELINE_STATUS:-success}\" == \"no_pipeline\" ]]; then\n"
        "    echo \"No pipeline found. It might not exist yet. Check your pipeline configuration.\" >&2\n"
        "    exit 1\n"
        "  fi\n"
        "  printf '{\"status\":\"%s\"}\\n' \"${GLAB_FAKE_PIPELINE_STATUS:-success}\"\n"
        "  exit 0\n"
        "fi\n"
        "if [[ \"${1-}\" == \"mr\" && \"${2-}\" == \"view\" ]]; then\n"
        "  printf '{\"iid\":7,\"web_url\":\"https://gitlab.example/group/project/-/merge_requests/7\",'\n"
        "  printf '\"source_branch\":\"%s\",\"target_branch\":\"main\",' \"${GLAB_FAKE_SOURCE_BRANCH:-feat/demo}\"\n"
        "  printf '\"state\":\"%s\",\"draft\":%s}\\n' \"${GLAB_FAKE_MR_STATE:-opened}\" \"${GLAB_FAKE_DRAFT:-true}\"\n"
        "  exit 0\n"
        "fi\n"
        "if [[ \"${1-}\" == \"mr\" && \"${2-}\" == \"update\" ]]; then\n"
        "  exit 0\n"
        "fi\n"
        "if [[ \"${1-}\" == \"mr\" && \"${2-}\" == \"merge\" ]]; then\n"
        "  exit 0\n"
        "fi\n"
        "echo \"unexpected glab args: $*\" >&2\n"
        "exit 9\n",
        encoding="utf-8",
    )
    glab_path.chmod(glab_path.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
    return bin_dir, log_path


def _setup_repo(tmp_path: Path) -> tuple[Path, dict[str, str], Path]:
    repo = tmp_path / "repo"
    repo.mkdir()
    _init_repo(repo)
    fake_bin, log_path = _install_fake_glab(tmp_path)
    env = {
        "PATH": os.pathsep.join([str(fake_bin), os.environ.get("PATH", "")]),
        "GLAB_FAKE_LOG": str(log_path),
    }
    return repo, env, log_path


def _run_close(repo: Path, env: dict[str, str], *extra_args: str) -> subprocess.CompletedProcess[str]:
    return _run(
        [
            str(SCRIPT),
            "--kind",
            "feature",
            "--mr",
            "7",
            "--poll-seconds",
            "1",
            "--max-wait-seconds",
            "1",
            "--no-cleanup",
            *extra_args,
        ],
        cwd=repo,
        env=env,
    )


def test_help_surface() -> None:
    proc = subprocess.run(
        [str(SCRIPT), "--help"],
        text=True,
        capture_output=True,
        check=False,
    )

    assert proc.returncode == 0
    assert "close-gitlab-mr.sh --kind <feature|bug|config|deploy|docs|chore>" in proc.stdout


def test_close_blocks_missing_pipeline_by_default(tmp_path: Path) -> None:
    repo, env, log_path = _setup_repo(tmp_path)
    env["GLAB_FAKE_PIPELINE_STATUS"] = "no_pipeline"

    proc = _run_close(repo, env)

    assert proc.returncode == 1
    assert "PIPELINE_STATUS=missing" in proc.stdout
    assert "use --allow-no-pipeline" in proc.stderr
    log = log_path.read_text(encoding="utf-8")
    assert "glab mr merge 7" not in log


def test_close_accepts_missing_pipeline_when_explicitly_allowed(tmp_path: Path) -> None:
    repo, env, log_path = _setup_repo(tmp_path)
    env["GLAB_FAKE_PIPELINE_STATUS"] = "no_pipeline"

    proc = _run_close(repo, env, "--allow-no-pipeline")

    assert proc.returncode == 0, proc.stderr
    assert "PIPELINE_STATUS=missing" in proc.stdout
    assert "accepted by --allow-no-pipeline" in proc.stdout
    log = log_path.read_text(encoding="utf-8")
    assert "glab mr merge 7 --yes" in log


def test_close_blocks_failed_pipeline_even_when_no_pipeline_is_allowed(tmp_path: Path) -> None:
    repo, env, log_path = _setup_repo(tmp_path)
    env["GLAB_FAKE_PIPELINE_STATUS"] = "failed"

    proc = _run_close(repo, env, "--allow-no-pipeline")

    assert proc.returncode == 1
    assert "PIPELINE_STATUS=failed" in proc.stdout
    assert "pipeline is not mergeable" in proc.stderr
    log = log_path.read_text(encoding="utf-8")
    assert "glab mr merge 7" not in log


def test_close_marks_draft_ready_and_keeps_remote_source_branch_by_default(tmp_path: Path) -> None:
    repo, env, log_path = _setup_repo(tmp_path)

    proc = _run_close(repo, env)

    assert proc.returncode == 0, proc.stderr
    assert "MR_KIND=feature" in proc.stdout
    log = log_path.read_text(encoding="utf-8")
    assert "glab mr update 7 --ready --yes" in log
    assert "glab mr merge 7 --yes" in log
    assert "--remove-source-branch" not in log


def test_close_passes_explicit_merge_controls(tmp_path: Path) -> None:
    repo, env, log_path = _setup_repo(tmp_path)
    env["GLAB_FAKE_DRAFT"] = "false"

    proc = _run_close(
        repo,
        env,
        "--skip-pipeline",
        "--remove-source-branch",
        "--squash",
        "--sha",
        "abc123",
    )

    assert proc.returncode == 0, proc.stderr
    assert "PIPELINE_STATUS=skipped_by_user_confirmation" in proc.stdout
    log = log_path.read_text(encoding="utf-8")
    assert "glab mr update" not in log
    assert "glab mr merge 7 --remove-source-branch --squash --sha abc123 --yes" in log
