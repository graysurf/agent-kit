from __future__ import annotations

import shutil
import subprocess
import uuid
from pathlib import Path

from skills._shared.python.skill_testing import assert_entrypoints_exist, assert_skill_contract
from skills._shared.python.skill_testing.assertions import repo_root


def test_tools_skill_management_create_skill_contract() -> None:
    skill_root = Path(__file__).resolve().parents[1]
    assert_skill_contract(skill_root)


def test_tools_skill_management_create_skill_entrypoints_exist() -> None:
    skill_root = Path(__file__).resolve().parents[1]
    assert_entrypoints_exist(skill_root, ["scripts/create_skill.sh"])


def test_create_skill_generates_contract_first_skill_md() -> None:
    root = repo_root()
    create_script = (
        root / "skills" / "tools" / "skill-management" / "create-skill" / "scripts" / "create_skill.sh"
    )
    validate_script = (
        root
        / "skills"
        / "tools"
        / "skill-management"
        / "skill-governance"
        / "scripts"
        / "validate_skill_contracts.sh"
    )

    skill_dir = root / "skills" / "_tmp" / f"create-skill-contract-first-{uuid.uuid4().hex}"
    rel_skill_dir = skill_dir.relative_to(root).as_posix()

    try:
        proc = subprocess.run(
            [
                "bash",
                str(create_script),
                "--skill-dir",
                rel_skill_dir,
                "--title",
                "Create Skill Contract First Smoke",
                "--description",
                "smoke",
            ],
            cwd=root,
            text=True,
            capture_output=True,
        )
        assert proc.returncode == 0, f"create_skill.sh failed:\nstdout:\n{proc.stdout}\nstderr:\n{proc.stderr}"

        skill_md = skill_dir / "SKILL.md"
        assert skill_md.is_file()

        proc2 = subprocess.run(
            [str(validate_script), "--file", str(skill_md)],
            cwd=root,
            text=True,
            capture_output=True,
        )
        assert proc2.returncode == 0, f"validate_skill_contracts.sh failed:\n{proc2.stderr}"
    finally:
        if skill_dir.exists():
            shutil.rmtree(skill_dir)
