from __future__ import annotations

import subprocess
from pathlib import Path

from skills._shared.python.skill_testing import assert_entrypoints_exist, assert_skill_contract
from skills._shared.python.skill_testing.assertions import repo_root


def test_tools_skill_management_skill_governance_contract() -> None:
    skill_root = Path(__file__).resolve().parents[1]
    assert_skill_contract(skill_root)


def test_tools_skill_management_skill_governance_entrypoints_exist() -> None:
    skill_root = Path(__file__).resolve().parents[1]
    assert_entrypoints_exist(
        skill_root,
        [
            "scripts/audit-skill-layout.sh",
            "scripts/validate_skill_contracts.sh",
            "scripts/validate_skill_paths.sh",
        ],
    )


def test_validate_skill_contracts_enforces_contract_first_h2() -> None:
    root = repo_root()
    fixture = (
        root
        / "skills"
        / "tools"
        / "skill-management"
        / "skill-governance"
        / "tests"
        / "fixtures"
        / "skill_md_contract_not_first.md"
    )
    script = (
        root
        / "skills"
        / "tools"
        / "skill-management"
        / "skill-governance"
        / "scripts"
        / "validate_skill_contracts.sh"
    )
    proc = subprocess.run([str(script), "--file", str(fixture)], text=True, capture_output=True)
    assert proc.returncode != 0
    assert "must be the first H2" in proc.stderr


def test_validate_skill_contracts_enforces_preamble_max_lines() -> None:
    root = repo_root()
    fixture = (
        root
        / "skills"
        / "tools"
        / "skill-management"
        / "skill-governance"
        / "tests"
        / "fixtures"
        / "skill_md_preamble_too_long.md"
    )
    script = (
        root
        / "skills"
        / "tools"
        / "skill-management"
        / "skill-governance"
        / "scripts"
        / "validate_skill_contracts.sh"
    )
    proc = subprocess.run([str(script), "--file", str(fixture)], text=True, capture_output=True)
    assert proc.returncode != 0
    assert "preamble too long" in proc.stderr
