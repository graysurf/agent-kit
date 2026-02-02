from __future__ import annotations

from pathlib import Path

from skills._shared.python.skill_testing import assert_entrypoints_exist, assert_skill_contract


def test_screenshot_contract() -> None:
    skill_root = Path(__file__).resolve().parents[1]
    assert_skill_contract(skill_root)


def test_screenshot_entrypoints_exist() -> None:
    skill_root = Path(__file__).resolve().parents[1]
    assert_entrypoints_exist(
        skill_root,
        [
            "scripts/screenshot.sh",
            "scripts/take_screenshot.py",
            "scripts/take_screenshot.ps1",
            "scripts/ensure_macos_permissions.sh",
        ],
    )
