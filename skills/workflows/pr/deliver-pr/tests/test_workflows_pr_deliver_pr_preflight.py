from __future__ import annotations

import os
import stat
import subprocess
from pathlib import Path


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "deliver-pr.sh"


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
    _seed_commit(
        repo,
        {"README.md": "seed\n"},
        message="chore: seed repository",
    )


def _install_fake_gh(tmp_path: Path) -> Path:
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    gh_path = bin_dir / "gh"
    gh_path.write_text(
        "#!/usr/bin/env bash\n"
        "set -euo pipefail\n"
        "if [[ \"${1-}\" == \"auth\" && \"${2-}\" == \"status\" ]]; then\n"
        "  exit 0\n"
        "fi\n"
        "echo \"unexpected gh args: $*\" >&2\n"
        "exit 9\n",
        encoding="utf-8",
    )
    gh_path.chmod(gh_path.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
    return bin_dir


def _setup_preflight_repo(tmp_path: Path) -> tuple[Path, dict[str, str]]:
    repo = tmp_path / "repo"
    repo.mkdir()
    _init_repo(repo)
    fake_bin = _install_fake_gh(tmp_path)
    env = {"PATH": os.pathsep.join([str(fake_bin), os.environ.get("PATH", "")])}
    return repo, env


def _run_preflight(
    repo: Path,
    env: dict[str, str],
    *args: str,
    kind: str = "feature",
) -> subprocess.CompletedProcess[str]:
    return _run([str(SCRIPT), "--kind", kind, "preflight", *args], cwd=repo, env=env)


def _combined(proc: subprocess.CompletedProcess[str]) -> str:
    return f"{proc.stdout}\n{proc.stderr}".lower()


def _assert_state_summary_marker(proc: subprocess.CompletedProcess[str]) -> None:
    combined = _combined(proc)
    assert (
        "state_summary" in combined
        or "change_state_summary" in combined
        or "state: worktree changes" in combined
    )


def test_preflight_state_summary_marker(tmp_path: Path) -> None:
    repo, env = _setup_preflight_repo(tmp_path)
    _seed_commit(
        repo,
        {"app/seed.txt": "base\n"},
        message="chore: add app seed",
    )
    _write(repo, "app/seed.txt", "base\nstate-summary\n")
    _assert_ok(_git(repo, "add", "app/seed.txt"))

    proc = _run_preflight(repo, env)

    assert proc.returncode == 0, proc.stderr
    _assert_state_summary_marker(proc)


def test_preflight_requires_kind(tmp_path: Path) -> None:
    repo, env = _setup_preflight_repo(tmp_path)

    proc = _run([str(SCRIPT), "preflight"], cwd=repo, env=env)

    assert proc.returncode == 2
    assert "--kind <bug|feature> is required" in proc.stderr


def test_preflight_kind_outputs_branch_prefixes(tmp_path: Path) -> None:
    repo, env = _setup_preflight_repo(tmp_path)

    feature_proc = _run_preflight(repo, env, kind="feature")
    bug_proc = _run_preflight(repo, env, kind="bug")

    assert feature_proc.returncode == 0, feature_proc.stderr
    assert bug_proc.returncode == 0, bug_proc.stderr
    assert "KIND=feature" in feature_proc.stdout
    assert "BRANCH_PREFIX=feat" in feature_proc.stdout
    assert "CREATE_SKILL=create-feature-pr" in feature_proc.stdout
    assert "CLOSE_SKILL=close-feature-pr" in feature_proc.stdout
    assert "KIND=bug" in bug_proc.stdout
    assert "BRANCH_PREFIX=fix" in bug_proc.stdout
    assert "CREATE_SKILL=create-bug-pr" in bug_proc.stdout
    assert "CLOSE_SKILL=close-bug-pr" in bug_proc.stdout


def test_preflight_mixed_status_pass_path(tmp_path: Path) -> None:
    repo, env = _setup_preflight_repo(tmp_path)
    _seed_commit(
        repo,
        {
            "app/feature_a.txt": "base\n",
            "app/feature_b.txt": "base\n",
        },
        message="chore: add app files",
    )
    _write(repo, "app/feature_a.txt", "base\nstaged\n")
    _assert_ok(_git(repo, "add", "app/feature_a.txt"))
    _write(repo, "app/feature_b.txt", "base\nunstaged\n")

    proc = _run_preflight(repo, env)

    assert proc.returncode == 0, proc.stderr
    assert "ok: preflight passed" in proc.stdout.lower()
    combined = _combined(proc)
    assert "mixed_status" in combined
    _assert_state_summary_marker(proc)


def test_preflight_mixed_status_suspicious_block(tmp_path: Path) -> None:
    repo, env = _setup_preflight_repo(tmp_path)
    _seed_commit(
        repo,
        {
            "app/product.txt": "base\n",
            ".github/workflows/ci.yml": "name: ci\n",
        },
        message="chore: add mixed-domain files",
    )
    _write(repo, "app/product.txt", "base\nstaged\n")
    _assert_ok(_git(repo, "add", "app/product.txt"))
    _write(repo, ".github/workflows/ci.yml", "name: ci\n# unstaged\n")

    proc = _run_preflight(repo, env)

    assert proc.returncode == 1
    combined = _combined(proc)
    assert "mixed_status" in combined
    assert "blocked_for_ambiguity" in combined


def test_preflight_same_file_overlap_block(tmp_path: Path) -> None:
    repo, env = _setup_preflight_repo(tmp_path)
    _seed_commit(
        repo,
        {"app/overlap.txt": "base\n"},
        message="chore: add overlap file",
    )
    _write(repo, "app/overlap.txt", "base\nstaged\n")
    _assert_ok(_git(repo, "add", "app/overlap.txt"))
    _write(repo, "app/overlap.txt", "base\nstaged\nunstaged\n")

    proc = _run_preflight(repo, env)

    assert proc.returncode == 1
    combined = _combined(proc)
    assert "blocked_for_ambiguity" in combined
    assert (
        "same_file_overlap" in combined
        or "same-file" in combined
        or "staged+unstaged overlap" in combined
    )


def test_preflight_single_status_fast_path_pass(tmp_path: Path) -> None:
    repo, env = _setup_preflight_repo(tmp_path)
    _seed_commit(
        repo,
        {"app/fast-path.txt": "base\n"},
        message="chore: add fast path file",
    )
    _write(repo, "app/fast-path.txt", "base\nstaged\n")
    _assert_ok(_git(repo, "add", "app/fast-path.txt"))

    proc = _run_preflight(repo, env)

    assert proc.returncode == 0, proc.stderr
    assert "ok: preflight passed" in proc.stdout.lower()
    assert "single_status_fast_path" in _combined(proc)


def test_preflight_single_status_escalation_block(tmp_path: Path) -> None:
    repo, env = _setup_preflight_repo(tmp_path)
    _write(repo, ".github/workflows/ci.yml", "name: ci\n")

    proc = _run_preflight(repo, env)

    assert proc.returncode == 1
    combined = _combined(proc)
    assert "single_status_escalation" in combined
    assert "blocked_for_ambiguity" in combined


def test_preflight_treats_skill_workflow_paths_as_infra_tooling(tmp_path: Path) -> None:
    repo, env = _setup_preflight_repo(tmp_path)
    _write(repo, "skills/workflows/pr/example/SKILL.md", "# Example\n")
    _assert_ok(_git(repo, "add", "skills/workflows/pr/example/SKILL.md"))

    proc = _run_preflight(repo, env)

    assert proc.returncode == 1
    combined = _combined(proc)
    assert "single_status_escalation" in combined
    assert "blocked_for_ambiguity" in combined
    assert "infra_tooling_only" in combined


def test_preflight_single_status_escalation_bypass_pass(tmp_path: Path) -> None:
    repo, env = _setup_preflight_repo(tmp_path)
    _write(repo, ".github/workflows/ci.yml", "name: ci\n")

    proc = _run_preflight(repo, env, "--bypass-ambiguity")

    assert proc.returncode == 0, proc.stderr
    combined = _combined(proc)
    assert "bypass_state=ambiguity_bypassed" in combined
    assert "ok: preflight passed" in proc.stdout.lower()


def test_preflight_mixed_status_suspicious_bypass_pass(tmp_path: Path) -> None:
    repo, env = _setup_preflight_repo(tmp_path)
    _seed_commit(
        repo,
        {
            "app/product.txt": "base\n",
            ".github/workflows/ci.yml": "name: ci\n",
        },
        message="chore: add mixed-domain files",
    )
    _write(repo, "app/product.txt", "base\nstaged\n")
    _assert_ok(_git(repo, "add", "app/product.txt"))
    _write(repo, ".github/workflows/ci.yml", "name: ci\n# unstaged\n")

    proc = _run_preflight(repo, env, "--bypass-ambiguity")

    assert proc.returncode == 0, proc.stderr
    combined = _combined(proc)
    assert "bypass_state=ambiguity_bypassed" in combined
    assert "mixed_status=true" in combined
    assert "ok: preflight passed" in proc.stdout.lower()


def test_preflight_stop_and_confirm_payload_fields(tmp_path: Path) -> None:
    repo, env = _setup_preflight_repo(tmp_path)
    _seed_commit(
        repo,
        {
            "app/work.txt": "base\n",
            ".github/workflows/ci.yml": "name: ci\n",
        },
        message="chore: add payload fixtures",
    )
    _write(repo, "app/work.txt", "base\nstaged\n")
    _assert_ok(_git(repo, "add", "app/work.txt"))
    _write(repo, ".github/workflows/ci.yml", "name: ci\n# suspicious\n")

    proc = _run_preflight(repo, env)

    assert proc.returncode == 1
    combined = _combined(proc)
    for marker in [
        "block_state",
        "change_state_summary",
        "suspicious_files",
        "suspicious_reasons",
        "diff_inspection_result",
        "confirmation_prompt",
        "next_action",
    ]:
        assert marker in combined


def test_preflight_base_branch_guard_fail(tmp_path: Path) -> None:
    repo, env = _setup_preflight_repo(tmp_path)
    _assert_ok(_git(repo, "checkout", "-q", "-B", "feature/demo"))

    proc = _run_preflight(repo, env, "--base", "main")

    assert proc.returncode == 1
    assert "initial branch guard failed" in proc.stderr.lower()
    assert "stop and ask user to confirm source branch and merge target" in proc.stderr.lower()


def test_preflight_base_branch_guard_runs_before_ambiguity_triage(tmp_path: Path) -> None:
    repo, env = _setup_preflight_repo(tmp_path)
    _assert_ok(_git(repo, "checkout", "-q", "-B", "feature/demo"))
    _write(repo, ".github/workflows/ci.yml", "name: ci\n")
    _assert_ok(_git(repo, "add", ".github/workflows/ci.yml"))

    proc = _run_preflight(repo, env, "--base", "main")

    assert proc.returncode == 1
    combined = _combined(proc)
    assert "initial branch guard failed" in combined
    assert "blocked_for_ambiguity" not in combined


def test_preflight_base_branch_guard_still_fails_with_bypass(tmp_path: Path) -> None:
    repo, env = _setup_preflight_repo(tmp_path)
    _assert_ok(_git(repo, "checkout", "-q", "-B", "feature/demo"))

    proc = _run_preflight(repo, env, "--base", "main", "--bypass-ambiguity")

    assert proc.returncode == 1
    assert "initial branch guard failed" in proc.stderr.lower()
