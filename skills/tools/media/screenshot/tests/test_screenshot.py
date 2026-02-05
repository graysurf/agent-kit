from __future__ import annotations

from pathlib import Path

from skills._shared.python.skill_testing import (
    assert_entrypoints_exist,
    assert_skill_contract,
    resolve_codex_command,
)


def test_screenshot_contract() -> None:
    skill_root = Path(__file__).resolve().parents[1]
    assert_skill_contract(skill_root)


def test_screenshot_command_exists() -> None:
    resolve_codex_command("screen-record")


def test_screenshot_entrypoints_exist() -> None:
    skill_root = Path(__file__).resolve().parents[1]
    assert_entrypoints_exist(
        skill_root,
        [
            "scripts/screenshot.sh",
        ],
    )


def test_screenshot_entrypoint_uses_screen_record() -> None:
    skill_root = Path(__file__).resolve().parents[1]
    entrypoint = (skill_root / "scripts" / "screenshot.sh").read_text("utf-8")
    assert "screen-record" in entrypoint
