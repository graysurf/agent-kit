from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VALIDATOR = ROOT / "scripts/skills/validate_skill_usage_record.py"


def _write_record(path: Path, **overrides: object) -> None:
    record: dict[str, object] = {
        "schema": "skill-usage.record.v1",
        "skill": "skills/workflows/conversation/discussion-to-implementation-doc",
        "started_at": "2026-05-17T21:00:00+08:00",
        "cwd": "/Users/terry/.config/agent-kit",
        "trigger": "user_explicit",
        "intent": "write implementation handoff",
        "inputs": {
            "user_request_summary": "Create a durable implementation handoff",
            "referenced_files": [],
            "external_sources": [],
        },
        "outcome": {
            "status": "pass",
            "summary": "Created implementation handoff",
        },
        "artifacts": ["docs/runbooks/skills/example.md"],
        "linked_records": [],
        "validation": [
            {
                "command": "scripts/check.sh --docs",
                "status": "pass",
                "summary": "Docs freshness passed",
            }
        ],
        "follow_up": [],
    }
    record.update(overrides)
    path.write_text(json.dumps(record, indent=2), encoding="utf-8")


def _run(path: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(VALIDATOR), str(path)],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )


def test_skill_usage_record_validator_accepts_success_record(tmp_path: Path) -> None:
    record = tmp_path / "skill-usage.record.json"
    _write_record(record)

    result = _run(record)

    assert result.returncode == 0, result.stderr
    assert "ok: 1 skill usage record(s) valid" in result.stderr


def test_skill_usage_record_validator_rejects_missing_outcome_status(tmp_path: Path) -> None:
    record = tmp_path / "skill-usage.record.json"
    _write_record(record, outcome={"summary": "Missing status"})

    result = _run(record)

    assert result.returncode == 1
    assert "missing_outcome_status" in result.stderr


def test_skill_usage_record_validator_rejects_failure_without_classification(tmp_path: Path) -> None:
    record = tmp_path / "skill-usage.record.json"
    _write_record(
        record,
        outcome={"status": "blocked", "summary": "Validation is blocked"},
        failures=[
            {
                "phase": "validation",
                "symptom": "Docs check failed",
                "diagnosis": "A command path is stale",
                "handling": "Stopped for review",
                "result": "blocked",
            }
        ],
    )

    result = _run(record)

    assert result.returncode == 1
    assert "missing_failure_classification" in result.stderr


def test_skill_usage_record_validator_accepts_failed_record_with_classification(tmp_path: Path) -> None:
    record = tmp_path / "skill-usage.record.json"
    _write_record(
        record,
        outcome={"status": "worked_around", "summary": "Docs validation needed a targeted workaround"},
        failures=[
            {
                "phase": "validation",
                "command": "scripts/check.sh --docs",
                "exit_code": 1,
                "symptom": "Docs freshness check failed",
                "classification": "project_state",
                "diagnosis": "A new documented script path was missing from the script index.",
                "handling": "Updated the script index and reran validation.",
                "result": "fixed",
                "artifacts": ["scripts/README.md"],
            }
        ],
    )

    result = _run(record)

    assert result.returncode == 0, result.stderr


def test_skill_usage_record_validator_requires_final_validation_by_default(tmp_path: Path) -> None:
    record = tmp_path / "skill-usage.record.json"
    _write_record(record, validation=[])

    result = _run(record)

    assert result.returncode == 1
    assert "missing_final_validation" in result.stderr


def test_skill_usage_record_validator_accepts_validation_waiver(tmp_path: Path) -> None:
    record = tmp_path / "skill-usage.record.json"
    _write_record(
        record,
        validation_required=False,
        validation=[],
        validation_waiver="Conversational-only dry run with no durable artifact.",
    )

    result = _run(record)

    assert result.returncode == 0, result.stderr


def test_skill_usage_record_validator_rejects_secret_like_values(tmp_path: Path) -> None:
    record = tmp_path / "skill-usage.record.json"
    _write_record(record, intent="debug with Authorization: Bearer abc123")

    result = _run(record)

    assert result.returncode == 1
    assert "secret_like_value" in result.stderr
