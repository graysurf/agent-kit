from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any, cast

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
HOOK_DIR = REPO_ROOT / "hooks" / "codex"


def parse_stdout(stdout: str) -> dict[str, object] | None:
    stripped = stdout.strip()
    if not stripped:
        return None
    return cast(dict[str, object], json.loads(stripped))


def run_python_hook(
    script_name: str,
    payload: dict[str, Any],
    *,
    cwd: Path | None = None,
    env: dict[str, str] | None = None,
) -> tuple[int, dict[str, object] | None, str]:
    completed = subprocess.run(
        [sys.executable, str(HOOK_DIR / script_name)],
        input=json.dumps(payload),
        capture_output=True,
        text=True,
        cwd=cwd,
        env=env,
        check=False,
    )
    return completed.returncode, parse_stdout(completed.stdout), completed.stderr


def run_shell_hook(
    script_name: str,
    payload: dict[str, Any],
    *,
    cwd: Path,
    env: dict[str, str] | None = None,
) -> tuple[int, dict[str, object] | None, str]:
    completed = subprocess.run(
        [str(HOOK_DIR / script_name)],
        input=json.dumps(payload),
        capture_output=True,
        text=True,
        cwd=cwd,
        env=env,
        check=False,
    )
    return completed.returncode, parse_stdout(completed.stdout), completed.stderr


def command_payload(command: str, **tool_input: str) -> dict[str, Any]:
    return {"tool_name": "Bash", "tool_input": {"command": command, **tool_input}}


def assert_blocked(decision: dict[str, object] | None, fragment: str) -> None:
    assert decision is not None
    assert decision.get("decision") == "block"
    assert fragment in str(decision.get("reason", ""))


def assert_allowed(decision: dict[str, object] | None) -> None:
    assert decision is None


def git(repo: Path, *args: str) -> str:
    completed = subprocess.run(
        ["git", *args],
        cwd=repo,
        capture_output=True,
        text=True,
        check=True,
    )
    return completed.stdout.strip()


def commit_with_tree(repo: Path, message: str, *, parent: str | None = None) -> str:
    tree = git(repo, "write-tree")
    args = ["commit-tree", tree]
    if parent:
        args.extend(["-p", parent])
    completed = subprocess.run(
        ["git", *args],
        input=f"{message}\n",
        cwd=repo,
        capture_output=True,
        text=True,
        check=True,
    )
    return completed.stdout.strip()


def init_repo_with_main(repo: Path) -> str:
    git(repo, "init", "-b", "main")
    git(repo, "config", "user.email", "codex-hooks@example.invalid")
    git(repo, "config", "user.name", "Codex Hooks")
    (repo / "README.md").write_text("# Fixture\n", "utf-8")
    git(repo, "add", "README.md")
    initial = commit_with_tree(repo, "initial")
    git(repo, "update-ref", "refs/heads/main", initial)
    git(repo, "reset", "--hard", "main")
    return initial


class TestDirectGitCommitHook:
    def test_blocks_git_commit(self) -> None:
        for command in (
            "git commit -m test",
            "git -c user.name=Codex commit -m test",
            "env GIT_AUTHOR_NAME=Codex git commit -m test",
            "command git commit -m test",
        ):
            code, decision, _ = run_python_hook(
                "block-direct-git-commit.py",
                command_payload(command),
            )
            assert code == 0, command
            assert_blocked(decision, "semantic-commit")

    def test_allows_semantic_commit_and_commit_tree(self) -> None:
        for command in (
            "semantic-commit commit --message 'fix: thing\n\n- explain scope'",
            "git commit-tree HEAD^{tree}",
        ):
            code, decision, _ = run_python_hook(
                "block-direct-git-commit.py",
                command_payload(command),
            )
            assert code == 0, command
            assert_allowed(decision)

    def test_allows_searching_for_git_commit_text(self) -> None:
        for command in (
            "rg -n 'git commit' MEMORY.md",
            "printf '%s\\n' 'git commit'",
        ):
            code, decision, _ = run_python_hook(
                "block-direct-git-commit.py",
                command_payload(command),
            )
            assert code == 0, command
            assert_allowed(decision)


class TestSemanticCommitBodyGate:
    def test_blocks_non_trivial_subject_without_body(self) -> None:
        code, decision, _ = run_python_hook(
            "semantic-commit-body-gate.py",
            command_payload("semantic-commit commit --message 'fix(agent): tighten hook parser'"),
        )
        assert code == 0
        assert_blocked(decision, "missing a body")

    def test_allows_trivial_body_and_validate_only(self) -> None:
        commands = (
            "semantic-commit commit --message 'docs: refresh hook docs'",
            "semantic-commit commit --message 'fix(agent): tighten hook parser\n\n- Covers Codex payloads'",
            "semantic-commit commit --validate-only --message 'fix(agent): no body'",
        )
        for command in commands:
            code, decision, _ = run_python_hook(
                "semantic-commit-body-gate.py",
                command_payload(command),
            )
            assert code == 0
            assert_allowed(decision)


class TestDirectPythonHook:
    def test_blocks_bare_python_in_uv_project(self, tmp_path: Path) -> None:
        (tmp_path / "uv.lock").write_text("# fixture\n", "utf-8")

        code, decision, _ = run_python_hook(
            "block-direct-python.py",
            command_payload("python3 -m pytest"),
            cwd=tmp_path,
        )

        assert code == 0
        assert_blocked(decision, "uv run --locked python")

    def test_blocks_bare_python_using_payload_workdir(self, tmp_path: Path) -> None:
        repo = tmp_path / "repo"
        outside = tmp_path / "outside"
        repo.mkdir()
        outside.mkdir()
        (repo / "uv.lock").write_text("# fixture\n", "utf-8")

        code, decision, _ = run_python_hook(
            "block-direct-python.py",
            command_payload("python3 -m pytest", workdir=str(repo)),
            cwd=outside,
        )

        assert code == 0
        assert_blocked(decision, "uv run --locked python")

    def test_blocks_bare_python_using_top_level_cwd(self, tmp_path: Path) -> None:
        repo = tmp_path / "repo"
        outside = tmp_path / "outside"
        repo.mkdir()
        outside.mkdir()
        (repo / "uv.lock").write_text("# fixture\n", "utf-8")
        payload = command_payload("python3 -m pytest")
        payload["cwd"] = str(repo)

        code, decision, _ = run_python_hook(
            "block-direct-python.py",
            payload,
            cwd=outside,
        )

        assert code == 0
        assert_blocked(decision, "uv run --locked python")

    def test_blocks_bare_python_using_transcript_workdir(self, tmp_path: Path) -> None:
        repo = tmp_path / "repo"
        outside = tmp_path / "outside"
        repo.mkdir()
        outside.mkdir()
        (repo / "uv.lock").write_text("# fixture\n", "utf-8")
        transcript = tmp_path / "rollout.jsonl"
        call_id = "call_python"
        transcript.write_text(
            json.dumps(
                {
                    "type": "response_item",
                    "payload": {
                        "type": "function_call",
                        "name": "exec_command",
                        "call_id": call_id,
                        "arguments": json.dumps(
                            {
                                "cmd": "python3 -m pytest",
                                "workdir": str(repo),
                            }
                        ),
                    },
                }
            )
            + "\n",
            "utf-8",
        )
        payload = command_payload("python3 -m pytest")
        payload["tool_use_id"] = call_id
        payload["transcript_path"] = str(transcript)

        code, decision, _ = run_python_hook(
            "block-direct-python.py",
            payload,
            cwd=outside,
        )

        assert code == 0
        assert_blocked(decision, "uv run --locked python")

    def test_blocks_bare_python_after_cd(self, tmp_path: Path) -> None:
        repo = tmp_path / "repo"
        outside = tmp_path / "outside"
        repo.mkdir()
        outside.mkdir()
        (repo / "uv.lock").write_text("# fixture\n", "utf-8")

        code, decision, _ = run_python_hook(
            "block-direct-python.py",
            command_payload(f"cd {repo} && python3 -m pytest"),
            cwd=outside,
        )

        assert code == 0
        assert_blocked(decision, "uv run --locked python")

    def test_blocks_bare_python_after_shell_separator(self, tmp_path: Path) -> None:
        (tmp_path / "pyproject.toml").write_text("[tool.uv.sources] # fixture\n", "utf-8")

        code, decision, _ = run_python_hook(
            "block-direct-python.py",
            command_payload("echo ready && python -m scripts.tool"),
            cwd=tmp_path,
        )

        assert code == 0
        assert_blocked(decision, "uv")

    def test_blocks_env_python_in_virtualenv_project(self, tmp_path: Path) -> None:
        pyvenv_cfg = tmp_path / ".venv" / "pyvenv.cfg"
        pyvenv_cfg.parent.mkdir()
        pyvenv_cfg.write_text("home = /usr/bin\n", "utf-8")

        code, decision, _ = run_python_hook(
            "block-direct-python.py",
            command_payload("env PYTHONPATH=. python3 scripts/tool.py"),
            cwd=tmp_path,
        )

        assert code == 0
        assert_blocked(decision, ".venv/bin/python")

    def test_allows_managed_python_and_diagnostics(self, tmp_path: Path) -> None:
        (tmp_path / "uv.lock").write_text("# fixture\n", "utf-8")
        commands = (
            "uv run --locked python -m pytest",
            ".venv/bin/python -m pytest",
            "command -v python3",
            "echo python3",
            "AGENT_KIT_ALLOW_SYSTEM_PYTHON=1 python3 -m ensurepip",
        )

        for command in commands:
            code, decision, _ = run_python_hook(
                "block-direct-python.py",
                command_payload(command),
                cwd=tmp_path,
            )
            assert code == 0, command
            assert_allowed(decision)

    def test_allows_python_without_repo_markers(self, tmp_path: Path) -> None:
        code, decision, _ = run_python_hook(
            "block-direct-python.py",
            command_payload("python3 -m pytest"),
            cwd=tmp_path,
        )

        assert code == 0
        assert_allowed(decision)


class TestDirectPrCreateHook:
    def test_blocks_bare_gh_pr_create(self) -> None:
        commands = (
            "gh pr create --draft",
            "env FOO=1 gh -R owner/repo pr create --draft",
        )
        for command in commands:
            code, decision, _ = run_python_hook(
                "block-direct-pr-create.py",
                command_payload(command),
            )
            assert code == 0
            assert_blocked(decision, "AGENT_KIT_PR_SKILL")

    def test_allows_exact_agent_kit_pr_marker(self) -> None:
        code, decision, _ = run_python_hook(
            "block-direct-pr-create.py",
            command_payload("AGENT_KIT_PR_SKILL=create-feature-pr gh pr create --draft"),
        )
        assert code == 0
        assert_allowed(decision)

    def test_blocks_legacy_or_unknown_markers(self) -> None:
        commands = (
            "CLAUDE_KIT_PR_SKILL=create-feature-pr gh pr create --draft",
            "AGENT_KIT_PR_SKILL=1 gh pr create --draft",
            "AGENT_KIT_PR_SKILL=evil-skill gh pr create --draft",
        )
        for command in commands:
            code, decision, _ = run_python_hook(
                "block-direct-pr-create.py",
                command_payload(command),
            )
            assert code == 0
            assert_blocked(decision, "AGENT_KIT_PR_SKILL")

    def test_blocks_glab_mr_create_without_mr_skill_marker(self) -> None:
        commands = (
            "glab mr create --draft",
            "AGENT_KIT_PR_SKILL=create-feature-pr glab mr create --draft",
            "env AGENT_KIT_PR_SKILL=evil-skill glab -R group/project mr create --draft",
        )
        for command in commands:
            code, decision, _ = run_python_hook(
                "block-direct-pr-create.py",
                command_payload(command),
            )
            assert code == 0
            assert_blocked(decision, "create-gitlab-mr")

    def test_allows_exact_agent_kit_mr_marker(self) -> None:
        commands = (
            "AGENT_KIT_PR_SKILL=create-gitlab-mr glab mr create --draft",
            "env AGENT_KIT_PR_SKILL=create-gitlab-mr glab -R group/project mr create --draft",
        )
        for command in commands:
            code, decision, _ = run_python_hook(
                "block-direct-pr-create.py",
                command_payload(command),
            )
            assert code == 0
            assert_allowed(decision)

    def test_blocks_glab_api_mr_create_without_mr_skill_marker(self) -> None:
        commands = (
            "glab api --method POST projects/:fullpath/merge_requests -F source_branch=feat/demo",
            "glab api projects/123/merge_requests --field source_branch=feat/demo",
            "AGENT_KIT_PR_SKILL=create-feature-pr glab api -X POST projects/123/merge_requests",
        )
        for command in commands:
            code, decision, _ = run_python_hook(
                "block-direct-pr-create.py",
                command_payload(command),
            )
            assert code == 0
            assert_blocked(decision, "create-gitlab-mr")

    def test_allows_exact_agent_kit_mr_marker_for_glab_api_create(self) -> None:
        code, decision, _ = run_python_hook(
            "block-direct-pr-create.py",
            command_payload(
                "AGENT_KIT_PR_SKILL=create-gitlab-mr "
                "glab api --method POST projects/:fullpath/merge_requests "
                "-F source_branch=feat/demo"
            ),
        )
        assert code == 0
        assert_allowed(decision)

    def test_allows_pr_view(self) -> None:
        code, decision, _ = run_python_hook(
            "block-direct-pr-create.py",
            command_payload("gh pr view 123"),
        )
        assert code == 0
        assert_allowed(decision)

    def test_allows_searching_for_pr_mr_create_text(self) -> None:
        commands = (
            "rg -n 'gh pr create|glab mr create' hooks tests",
            "printf '%s\\n' 'glab mr create --draft'",
        )
        for command in commands:
            code, decision, _ = run_python_hook(
                "block-direct-pr-create.py",
                command_payload(command),
            )
            assert code == 0
            assert_allowed(decision)


class TestProjectMemoryWriteHook:
    def test_blocks_claude_compatible_project_memory_path(self) -> None:
        code, decision, _ = run_python_hook(
            "block-project-memory-write.py",
            {"tool_name": "Write", "tool_input": {"file_path": "/Users/me/.claude/projects/demo/memory/project_state.md"}},
        )
        assert code == 0
        assert_blocked(decision, "project-state memory")

    def test_blocks_apply_patch_project_memory_path(self) -> None:
        patch = """*** Begin Patch
*** Update File: .claude/projects/demo/memory/project_state.md
@@
+state
*** End Patch
"""
        code, decision, _ = run_python_hook(
            "block-project-memory-write.py",
            {"tool_name": "apply_patch", "tool_input": {"patch": patch}},
        )
        assert code == 0
        assert_blocked(decision, "project-state memory")

    def test_allows_regular_docs_patch(self) -> None:
        patch = """*** Begin Patch
*** Update File: docs/example.md
@@
+note
*** End Patch
"""
        code, decision, _ = run_python_hook(
            "block-project-memory-write.py",
            {"tool_name": "apply_patch", "tool_input": {"patch": patch}},
        )
        assert code == 0
        assert_allowed(decision)


class TestMcpSecretScanHook:
    def test_blocks_write_payload_secret_without_leaking_full_value(self) -> None:
        secret = "sk-testvalue1234567890abcdef"
        code, decision, _ = run_python_hook(
            "mcp-secret-scan.py",
            {"tool_name": "Write", "tool_input": {"file_path": ".mcp.json", "content": f'{{"key": "{secret}"}}'}},
        )
        assert code == 0
        assert_blocked(decision, "OpenAI-style key")
        assert secret not in str(decision)

    def test_blocks_apply_patch_home_path(self) -> None:
        patch = """*** Begin Patch
*** Add File: .mcp.json
+{"command": "/Users/terry/bin/local-tool"}
*** End Patch
"""
        code, decision, _ = run_python_hook(
            "mcp-secret-scan.py",
            {"tool_name": "apply_patch", "tool_input": {"patch": patch}},
        )
        assert code == 0
        assert_blocked(decision, "macOS home path")

    def test_allows_unrelated_json_patch(self) -> None:
        patch = """*** Begin Patch
*** Add File: package.json
+{"command": "/Users/terry/bin/local-tool"}
*** End Patch
"""
        code, decision, _ = run_python_hook(
            "mcp-secret-scan.py",
            {"tool_name": "apply_patch", "tool_input": {"patch": patch}},
        )
        assert code == 0
        assert_allowed(decision)

    def test_skip_env_allows_hook_mode(self) -> None:
        env = os.environ.copy()
        env["SKIP_MCP_SCAN"] = "1"
        code, decision, _ = run_python_hook(
            "mcp-secret-scan.py",
            {"tool_name": "Write", "tool_input": {"file_path": ".mcp.json", "content": "sk-testvalue1234567890abcdef"}},
            env=env,
        )
        assert code == 0
        assert_allowed(decision)

    def test_paths_mode_scans_files(self, tmp_path: Path) -> None:
        mcp_file = tmp_path / ".mcp.json"
        mcp_file.write_text('{"path": "/home/codex/local-tool"}\n', "utf-8")
        completed = subprocess.run(
            [sys.executable, str(HOOK_DIR / "mcp-secret-scan.py"), "--paths", str(mcp_file)],
            capture_output=True,
            text=True,
            check=False,
        )
        assert completed.returncode == 1
        assert "Linux home path" in completed.stdout
        assert "/home/codex/" not in completed.stdout


class TestUserPromptAgentDocsHook:
    def test_injects_preflight_context_for_implementation_prompt(self, tmp_path: Path) -> None:
        init_repo_with_main(tmp_path)
        (tmp_path / "AGENTS.md").write_text("# AGENTS\n", "utf-8")
        env = os.environ.copy()
        env["AGENT_HOME"] = str(REPO_ROOT)

        code, output, _ = run_shell_hook(
            "user-prompt-agent-docs.sh",
            {"prompt": "please implement the hook migration"},
            cwd=tmp_path,
            env=env,
        )

        assert code == 0
        assert output is not None
        hook_output = cast(dict[str, Any], output.get("hookSpecificOutput"))
        assert hook_output["hookEventName"] == "UserPromptSubmit"
        assert "agent-docs" in hook_output["additionalContext"]

    def test_skips_existing_agent_docs_or_suppressed_prompt(self, tmp_path: Path) -> None:
        init_repo_with_main(tmp_path)
        (tmp_path / "AGENTS.md").write_text("# AGENTS\n", "utf-8")
        env = os.environ.copy()
        env["AGENT_HOME"] = str(REPO_ROOT)

        code, output, _ = run_shell_hook(
            "user-prompt-agent-docs.sh",
            {"prompt": "implement after agent-docs"},
            cwd=tmp_path,
            env=env,
        )
        assert code == 0
        assert_allowed(output)

        suppressed_env = env | {"AGENT_KIT_SUPPRESS_PREFLIGHT": "1"}
        code, output, _ = run_shell_hook(
            "user-prompt-agent-docs.sh",
            {"prompt": "implement the feature"},
            cwd=tmp_path,
            env=suppressed_env,
        )
        assert code == 0
        assert_allowed(output)


@pytest.mark.skipif(shutil.which("agent-docs") is None, reason="agent-docs is not installed")
class TestSessionStartHealthcheckHook:
    def test_reports_missing_baseline_once_per_day(self, tmp_path: Path) -> None:
        env = os.environ.copy()
        env["AGENT_HOME"] = str(REPO_ROOT)
        env["HOME"] = str(tmp_path / "home")
        (tmp_path / "home").mkdir()

        code, output, _ = run_shell_hook(
            "session-start-healthcheck.sh",
            {"hook_event_name": "SessionStart"},
            cwd=tmp_path,
            env=env,
        )
        assert code == 0
        assert output is not None
        hook_output = cast(dict[str, Any], output.get("hookSpecificOutput"))
        assert hook_output["hookEventName"] == "SessionStart"
        assert "missing_required" in hook_output["additionalContext"]

        code, output, _ = run_shell_hook(
            "session-start-healthcheck.sh",
            {"hook_event_name": "SessionStart"},
            cwd=tmp_path,
            env=env,
        )
        assert code == 0
        assert_allowed(output)


class TestStopPrePrReminderHook:
    def test_reports_non_trivial_branch_diff_once(self, tmp_path: Path) -> None:
        initial = init_repo_with_main(tmp_path)
        git(tmp_path, "checkout", "-b", "feature/hooks")
        (tmp_path / "hook.py").write_text("print('hook')\n", "utf-8")
        git(tmp_path, "add", "hook.py")
        feature = commit_with_tree(tmp_path, "feature", parent=initial)
        git(tmp_path, "update-ref", "refs/heads/feature/hooks", feature)
        git(tmp_path, "reset", "--hard", "feature/hooks")

        env = os.environ.copy()
        env["HOME"] = str(tmp_path / "home")
        (tmp_path / "home").mkdir()

        code, output, _ = run_shell_hook(
            "stop-pre-pr-reminder.sh",
            {"hook_event_name": "Stop"},
            cwd=tmp_path,
            env=env,
        )
        assert code == 0
        assert output is not None
        assert "project validation" in str(output.get("systemMessage", ""))

        code, output, _ = run_shell_hook(
            "stop-pre-pr-reminder.sh",
            {"hook_event_name": "Stop"},
            cwd=tmp_path,
            env=env,
        )
        assert code == 0
        assert_allowed(output)


class TestCodexHooksSyncScript:
    def run_sync(
        self,
        home_path: Path,
        *args: str,
        agent_home: Path = Path("/opt/agent-kit"),
    ) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [
                sys.executable,
                str(REPO_ROOT / "scripts" / "codex-hooks-sync"),
                *args,
                "--home-path",
                str(home_path),
                "--agent-home",
                str(agent_home),
            ],
            capture_output=True,
            text=True,
            check=False,
        )

    def test_sync_replaces_unmarked_agent_kit_hook_block(self, tmp_path: Path) -> None:
        codex_dir = tmp_path / ".codex"
        codex_dir.mkdir()
        config_path = codex_dir / "config.toml"
        config_path.write_text(
            '''model = "gpt-5.5"

[[hooks.PreToolUse]]
matcher = "Bash"

[[hooks.PreToolUse.hooks]]
type = "command"
command = "/Users/terry/.agents/hooks/codex/block-direct-git-commit.py"

[[hooks.PreToolUse.hooks]]
type = "command"
command = "/Users/terry/.agents/hooks/codex/semantic-commit-body-gate.py"

[[hooks.PreToolUse.hooks]]
type = "command"
command = "/Users/terry/.agents/hooks/codex/block-direct-pr-create.py"

[[hooks.PreToolUse]]
matcher = "Write|Edit|NotebookEdit|apply_patch"

[[hooks.PreToolUse.hooks]]
type = "command"
command = "/Users/terry/.agents/hooks/codex/block-project-memory-write.py"

[[hooks.PreToolUse.hooks]]
type = "command"
command = "/Users/terry/.agents/hooks/codex/mcp-secret-scan.py"

[[hooks.UserPromptSubmit]]
matcher = ""

[[hooks.UserPromptSubmit.hooks]]
type = "command"
command = "/Users/terry/.agents/hooks/codex/user-prompt-agent-docs.sh"

[[hooks.SessionStart]]
matcher = "startup|resume|clear"

[[hooks.SessionStart.hooks]]
type = "command"
command = "/Users/terry/.agents/hooks/codex/session-start-healthcheck.sh"

[[hooks.Stop]]
matcher = ""

[[hooks.Stop.hooks]]
type = "command"
command = "/Users/terry/.agents/hooks/codex/stop-pre-pr-reminder.sh"

[features]
unified_exec = true
''',
            "utf-8",
        )

        status = self.run_sync(tmp_path, "status")
        assert status.returncode == 1
        assert "drifted" in status.stdout
        assert "replace-unmarked-agent-kit-hook-block" in status.stdout

        synced = self.run_sync(tmp_path, "sync", "--apply")
        assert synced.returncode == 0
        assert "update" in synced.stdout
        updated = config_path.read_text("utf-8")
        assert "# BEGIN agent-kit managed codex hooks" in updated
        assert 'command = "/opt/agent-kit/hooks/codex/block-direct-git-commit.py"' in updated
        assert 'command = "/opt/agent-kit/hooks/codex/block-direct-python.py"' in updated
        assert updated.count("[[hooks.PreToolUse]]") == 2
        assert "[features]" in updated

        clean = self.run_sync(tmp_path, "status")
        assert clean.returncode == 0
        assert "synced" in clean.stdout

    def test_sync_inserts_block_before_features(self, tmp_path: Path) -> None:
        codex_dir = tmp_path / ".codex"
        codex_dir.mkdir()
        config_path = codex_dir / "config.toml"
        config_path.write_text('model = "gpt-5.5"\n\n[features]\nunified_exec = true\n', "utf-8")

        synced = self.run_sync(tmp_path, "sync", "--apply")

        assert synced.returncode == 0
        updated = config_path.read_text("utf-8")
        assert updated.index("# BEGIN agent-kit managed codex hooks") < updated.index("[features]")
        assert 'command = "/opt/agent-kit/hooks/codex/mcp-secret-scan.py"' in updated
