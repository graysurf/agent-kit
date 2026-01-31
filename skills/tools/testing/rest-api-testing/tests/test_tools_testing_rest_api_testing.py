from __future__ import annotations

from pathlib import Path

from skills._shared.python.skill_testing import assert_skill_contract, resolve_codex_command


def test_tools_testing_rest_api_testing_contract() -> None:
    skill_root = Path(__file__).resolve().parents[1]
    assert_skill_contract(skill_root)


def test_tools_testing_rest_api_testing_commands_exist() -> None:
    resolve_codex_command("api-rest")
