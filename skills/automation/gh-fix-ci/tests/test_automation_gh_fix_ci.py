from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

from skills._shared.python.skill_testing import assert_entrypoints_exist, assert_skill_contract


def load_inspector_module():
    script = Path(__file__).resolve().parents[1] / "scripts" / "inspect_ci_checks.py"
    spec = importlib.util.spec_from_file_location("gh_fix_ci_inspect_ci_checks", script)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_automation_gh_fix_ci_contract() -> None:
    skill_root = Path(__file__).resolve().parents[1]
    assert_skill_contract(skill_root)


def test_automation_gh_fix_ci_entrypoints_exist() -> None:
    skill_root = Path(__file__).resolve().parents[1]
    assert_entrypoints_exist(
        skill_root,
        [
            "scripts/gh-fix-ci.sh",
            "scripts/inspect_ci_checks.py",
        ],
    )


def test_inspector_treats_startup_failure_as_failing() -> None:
    inspector = load_inspector_module()

    assert inspector.is_failing({"conclusion": "startup_failure"})
    assert inspector.is_failing({"state": "startup_failure"})


def test_inspector_keeps_startup_failures_for_newest_branch_sha(monkeypatch) -> None:
    inspector = load_inspector_module()

    newest_sha = "f259dee9352fbfed28a6202c3dc881ebe05e394a"
    older_sha = "1700ae21103b6ab1470da461cd809dd464698926"
    gh_payload = [
        {
            "databaseId": 25906913749,
            "name": "CodeQL",
            "status": "completed",
            "conclusion": "startup_failure",
            "url": "https://github.com/graysurf/agent-kit/actions/runs/25906913749",
            "headBranch": "main",
            "headSha": newest_sha,
            "workflowName": "CodeQL",
        },
        {
            "databaseId": 25906914048,
            "name": "Lint",
            "status": "completed",
            "conclusion": "success",
            "url": "https://github.com/graysurf/agent-kit/actions/runs/25906914048",
            "headBranch": "main",
            "headSha": newest_sha,
            "workflowName": "Lint",
        },
        {
            "databaseId": 25904784497,
            "name": "Lint",
            "status": "completed",
            "conclusion": "failure",
            "url": "https://github.com/graysurf/agent-kit/actions/runs/25904784497",
            "headBranch": "main",
            "headSha": older_sha,
            "workflowName": "Lint",
        },
    ]

    def fake_run_gh_command(args, cwd):
        assert args[:2] == ["run", "list"]
        assert "--branch" in args
        return inspector.GhResult(0, json.dumps(gh_payload), "")

    monkeypatch.setattr(inspector, "run_gh_command", fake_run_gh_command)

    checks = inspector.fetch_runs_for_ref("main", "branch", Path("."), 20)

    assert checks == [
        {
            "name": "CodeQL",
            "state": "completed",
            "conclusion": "startup_failure",
            "detailsUrl": "https://github.com/graysurf/agent-kit/actions/runs/25906913749",
            "runId": "25906913749",
        },
        {
            "name": "Lint",
            "state": "completed",
            "conclusion": "success",
            "detailsUrl": "https://github.com/graysurf/agent-kit/actions/runs/25906914048",
            "runId": "25906914048",
        },
    ]
    assert [check["name"] for check in checks if inspector.is_failing(check)] == ["CodeQL"]
