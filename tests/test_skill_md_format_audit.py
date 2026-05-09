from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from types import ModuleType


def load_audit_module() -> ModuleType:
    repo = Path(__file__).resolve().parents[1]
    module_path = repo / "scripts" / "skills" / "audit_skill_md_format.py"
    spec = importlib.util.spec_from_file_location("audit_skill_md_format", module_path)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


AUDIT = load_audit_module()


def write_skill(path: Path, front_matter: str) -> None:
    path.write_text(
        "\n".join(
            [
                "---",
                *front_matter.splitlines(),
                "---",
                "",
                "# Fixture Skill",
                "",
                "## Contract",
                "",
                "Prereqs:",
                "",
                "- N/A",
                "",
                "Inputs:",
                "",
                "- N/A",
                "",
                "Outputs:",
                "",
                "- N/A",
                "",
                "Exit codes:",
                "",
                "- `0`: success",
                "",
                "Failure modes:",
                "",
                "- N/A",
                "",
            ]
        ),
        "utf-8",
    )


def test_skill_md_format_flags_plain_multiline_description_with_colon(tmp_path: Path) -> None:
    skill_md = tmp_path / "SKILL.md"
    write_skill(
        skill_md,
        "\n".join(
            [
                "name: fixture-skill",
                "description:",
                "  Deliver bug or feature PRs end to end with one workflow: preflight, create PR, wait/fix CI until green, then close. Use `kind=bug` or",
                "  `kind=feature` to select branch prefix and PR templates.",
            ]
        ),
    )

    result = AUDIT.audit_file(skill_md, tmp_path, 2)

    assert not result.ok
    assert "frontmatter_plain_scalar_colon" in {violation.kind for violation in result.violations}


def test_skill_md_format_accepts_quoted_multiline_description_with_colon(tmp_path: Path) -> None:
    skill_md = tmp_path / "SKILL.md"
    write_skill(
        skill_md,
        "\n".join(
            [
                "name: fixture-skill",
                "description:",
                '  "Deliver bug or feature PRs end to end with one workflow: preflight, create PR, wait/fix CI until green, then close. Use `kind=bug` or',
                '  `kind=feature` to select branch prefix and PR templates."',
            ]
        ),
    )

    result = AUDIT.audit_file(skill_md, tmp_path, 2)

    assert result.ok
