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
    env: dict[str, str] | None = None,
) -> tuple[int, dict[str, object] | None, str]:
    completed = subprocess.run(
        [sys.executable, str(HOOK_DIR / script_name)],
        input=json.dumps(payload),
        capture_output=True,
        text=True,
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


def command_payload(command: str) -> dict[str, Any]:
    return {"tool_name": "Bash", "tool_input": {"command": command}}


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
        code, decision, _ = run_python_hook(
            "block-direct-git-commit.py",
            command_payload("git commit -m test"),
        )
        assert code == 0
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


class TestDirectPrCreateHook:
    def test_blocks_bare_gh_pr_create(self) -> None:
        code, decision, _ = run_python_hook(
            "block-direct-pr-create.py",
            command_payload("gh pr create --draft"),
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

    def test_blocks_glab_until_mr_skill_is_allowed(self) -> None:
        commands = (
            "glab mr create --draft",
            "AGENT_KIT_PR_SKILL=create-feature-pr glab mr create --draft",
        )
        for command in commands:
            code, decision, _ = run_python_hook(
                "block-direct-pr-create.py",
                command_payload(command),
            )
            assert code == 0
            assert_blocked(decision, "MR workflow")

    def test_allows_pr_view(self) -> None:
        code, decision, _ = run_python_hook(
            "block-direct-pr-create.py",
            command_payload("gh pr view 123"),
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
