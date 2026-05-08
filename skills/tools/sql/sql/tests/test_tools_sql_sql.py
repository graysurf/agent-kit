from __future__ import annotations

from pathlib import Path

from skills._shared.python.skill_testing import assert_entrypoints_exist, assert_skill_contract


def test_tools_sql_contract() -> None:
    skill_root = Path(__file__).resolve().parents[1]
    assert_skill_contract(skill_root)


def test_tools_sql_entrypoints_exist() -> None:
    skill_root = Path(__file__).resolve().parents[1]
    assert_entrypoints_exist(skill_root, ["scripts/sql.sh"])


def test_tools_sql_documents_all_supported_dialects() -> None:
    skill_root = Path(__file__).resolve().parents[1]
    text = (skill_root / "SKILL.md").read_text(encoding="utf-8")

    assert "postgres" in text
    assert "mysql" in text
    assert "mssql" in text
    assert "<PREFIX>_PGHOST" in text
    assert "<PREFIX>_MYSQL_HOST" in text
    assert "<PREFIX>_MSSQL_HOST" in text
