#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

SCHEMA_ID = "skill-usage.record.v1"

ROOT_REQUIRED = (
    "schema",
    "skill",
    "started_at",
    "cwd",
    "trigger",
    "intent",
    "inputs",
    "outcome",
    "artifacts",
    "linked_records",
    "validation",
    "follow_up",
)

TRIGGERS = {"user_explicit", "agent_selected", "project_policy", "other"}
OUTCOME_STATUSES = {"pass", "fail", "blocked", "worked_around", "accepted_risk", "skipped"}
VALIDATION_STATUSES = {"pass", "fail", "skipped"}
FAILURE_PHASES = {"preflight", "execution", "validation", "cleanup", "delivery"}
FAILURE_CLASSIFICATIONS = {
    "skill_contract",
    "script_bug",
    "missing_dependency",
    "external_service",
    "project_state",
    "user_scope",
    "unknown",
}
FAILURE_RESULTS = {"fixed", "worked_around", "blocked", "accepted_risk"}
FAILURE_REQUIRED = ("phase", "symptom", "classification", "diagnosis", "handling", "result")
SECRET_LIKE_PATTERNS = (
    re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----"),
    re.compile(r"\bAuthorization:\s*Bearer\s+\S+", re.IGNORECASE),
    re.compile(r"\bCookie:\s*\S+", re.IGNORECASE),
    re.compile(r"\b(?:api[_-]?key|token|secret|password)\s*=\s*\S+", re.IGNORECASE),
    re.compile(r"\bsk-[A-Za-z0-9_-]{12,}"),
)


@dataclass(frozen=True)
class Violation:
    kind: str
    path: str
    message: str


@dataclass(frozen=True)
class RecordResult:
    path: str
    ok: bool
    violations: list[Violation]


def eprint(message: str) -> None:
    print(message, file=sys.stderr)


def _is_nonempty_string(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _expect_nonempty_string(violations: list[Violation], value: Any, path: str, kind: str) -> None:
    if not _is_nonempty_string(value):
        violations.append(Violation(kind, path, "must be a non-empty string"))


def _expect_array(violations: list[Violation], value: Any, path: str, kind: str) -> list[Any]:
    if not isinstance(value, list):
        violations.append(Violation(kind, path, "must be an array"))
        return []
    return value


def _expect_object(violations: list[Violation], value: Any, path: str, kind: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        violations.append(Violation(kind, path, "must be an object"))
        return {}
    return value


def _scan_secret_like_values(violations: list[Violation], value: Any, path: str = "$") -> None:
    if isinstance(value, dict):
        for key, child in value.items():
            _scan_secret_like_values(violations, child, f"{path}.{key}")
        return
    if isinstance(value, list):
        for index, child in enumerate(value):
            _scan_secret_like_values(violations, child, f"{path}[{index}]")
        return
    if not isinstance(value, str):
        return

    for pattern in SECRET_LIKE_PATTERNS:
        if pattern.search(value):
            violations.append(
                Violation(
                    "secret_like_value",
                    path,
                    "contains a token, credential, cookie, or private-key-like value",
                )
            )
            return


def validate_record(record: Any) -> list[Violation]:
    violations: list[Violation] = []
    data = _expect_object(violations, record, "$", "root_not_object")
    if not data:
        return violations

    for key in ROOT_REQUIRED:
        if key not in data:
            violations.append(Violation(f"missing_{key}", f"$.{key}", "required field is missing"))

    if data.get("schema") != SCHEMA_ID:
        violations.append(Violation("invalid_schema", "$.schema", f"must equal {SCHEMA_ID!r}"))

    for key in ("skill", "started_at", "cwd", "intent"):
        if key in data:
            _expect_nonempty_string(violations, data.get(key), f"$.{key}", f"invalid_{key}")

    trigger = data.get("trigger")
    if trigger is not None and trigger not in TRIGGERS:
        violations.append(Violation("invalid_trigger", "$.trigger", f"must be one of {sorted(TRIGGERS)}"))

    inputs = _expect_object(violations, data.get("inputs"), "$.inputs", "invalid_inputs")
    if inputs:
        for key in ("user_request_summary", "referenced_files", "external_sources"):
            if key not in inputs:
                violations.append(Violation(f"missing_input_{key}", f"$.inputs.{key}", "required field is missing"))
        if "referenced_files" in inputs:
            _expect_array(violations, inputs.get("referenced_files"), "$.inputs.referenced_files", "invalid_referenced_files")
        if "external_sources" in inputs:
            _expect_array(violations, inputs.get("external_sources"), "$.inputs.external_sources", "invalid_external_sources")

    outcome = _expect_object(violations, data.get("outcome"), "$.outcome", "invalid_outcome")
    if outcome:
        status = outcome.get("status")
        if status is None:
            violations.append(Violation("missing_outcome_status", "$.outcome.status", "required field is missing"))
        elif status not in OUTCOME_STATUSES:
            violations.append(Violation("invalid_outcome_status", "$.outcome.status", f"must be one of {sorted(OUTCOME_STATUSES)}"))
        _expect_nonempty_string(violations, outcome.get("summary"), "$.outcome.summary", "invalid_outcome_summary")

    for key in ("artifacts", "linked_records", "validation", "follow_up"):
        if key in data:
            _expect_array(violations, data.get(key), f"$.{key}", f"invalid_{key}")

    linked_records = data.get("linked_records")
    if isinstance(linked_records, list):
        for index, linked in enumerate(linked_records):
            linked_obj = _expect_object(violations, linked, f"$.linked_records[{index}]", "invalid_linked_record")
            if linked_obj:
                _expect_nonempty_string(
                    violations,
                    linked_obj.get("type"),
                    f"$.linked_records[{index}].type",
                    "invalid_linked_record_type",
                )
                _expect_nonempty_string(
                    violations,
                    linked_obj.get("path"),
                    f"$.linked_records[{index}].path",
                    "invalid_linked_record_path",
                )

    validation_required = data.get("validation_required", True)
    if not isinstance(validation_required, bool):
        violations.append(Violation("invalid_validation_required", "$.validation_required", "must be boolean when present"))
        validation_required = True

    validation = data.get("validation")
    validation_items = validation if isinstance(validation, list) else []
    for index, item in enumerate(validation_items):
        validation_obj = _expect_object(violations, item, f"$.validation[{index}]", "invalid_validation_item")
        if not validation_obj:
            continue
        _expect_nonempty_string(
            violations,
            validation_obj.get("command"),
            f"$.validation[{index}].command",
            "invalid_validation_command",
        )
        status = validation_obj.get("status")
        if status not in VALIDATION_STATUSES:
            violations.append(
                Violation(
                    "invalid_validation_status",
                    f"$.validation[{index}].status",
                    f"must be one of {sorted(VALIDATION_STATUSES)}",
                )
            )
        _expect_nonempty_string(
            violations,
            validation_obj.get("summary"),
            f"$.validation[{index}].summary",
            "invalid_validation_summary",
        )

    if validation_required and not validation_items:
        violations.append(
            Violation(
                "missing_final_validation",
                "$.validation",
                "validation is required unless validation_required is false with validation_waiver",
            )
        )

    if not validation_required:
        _expect_nonempty_string(
            violations,
            data.get("validation_waiver"),
            "$.validation_waiver",
            "missing_validation_waiver",
        )

    failures = data.get("failures", [])
    failure_items = _expect_array(violations, failures, "$.failures", "invalid_failures") if "failures" in data else []
    for index, item in enumerate(failure_items):
        failure = _expect_object(violations, item, f"$.failures[{index}]", "invalid_failure")
        if not failure:
            continue
        for key in FAILURE_REQUIRED:
            if key not in failure:
                kind = f"missing_failure_{key}"
                violations.append(Violation(kind, f"$.failures[{index}].{key}", "required field is missing"))
        phase = failure.get("phase")
        if phase is not None and phase not in FAILURE_PHASES:
            violations.append(Violation("invalid_failure_phase", f"$.failures[{index}].phase", f"must be one of {sorted(FAILURE_PHASES)}"))
        classification = failure.get("classification")
        if classification is not None and classification not in FAILURE_CLASSIFICATIONS:
            violations.append(
                Violation(
                    "invalid_failure_classification",
                    f"$.failures[{index}].classification",
                    f"must be one of {sorted(FAILURE_CLASSIFICATIONS)}",
                )
            )
        result = failure.get("result")
        if result is not None and result not in FAILURE_RESULTS:
            violations.append(Violation("invalid_failure_result", f"$.failures[{index}].result", f"must be one of {sorted(FAILURE_RESULTS)}"))
        for key in ("symptom", "diagnosis", "handling"):
            if key in failure:
                _expect_nonempty_string(violations, failure.get(key), f"$.failures[{index}].{key}", f"invalid_failure_{key}")

    outcome_status = outcome.get("status") if outcome else None
    if outcome_status in {"fail", "blocked", "worked_around", "accepted_risk"} and not failure_items:
        violations.append(
            Violation(
                "missing_failure_record",
                "$.failures",
                "non-pass/non-skipped outcomes must include at least one failure record",
            )
        )

    _scan_secret_like_values(violations, data)

    return violations


def validate_file(path: Path) -> RecordResult:
    try:
        raw = path.read_text(encoding="utf-8")
    except OSError as exc:
        return RecordResult(path.as_posix(), False, [Violation("read_error", "$", str(exc))])

    try:
        data = json.loads(raw)
    except json.JSONDecodeError as exc:
        return RecordResult(path.as_posix(), False, [Violation("json_decode_error", "$", str(exc))])

    violations = validate_record(data)
    return RecordResult(path.as_posix(), not violations, violations)


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate skill-usage.record.v1 JSON files.")
    parser.add_argument("record", nargs="+", type=Path, help="Path to a skill usage record JSON file.")
    parser.add_argument("--format", choices=["summary", "json"], default="summary", help="Output format.")
    args = parser.parse_args()

    results = [validate_file(path) for path in args.record]
    failed = [result for result in results if not result.ok]

    if args.format == "json":
        payload = {
            "schema": "cli.skill-usage-record.validate.v1",
            "files_checked": len(results),
            "files_with_violations": len(failed),
            "files": [
                {
                    "path": result.path,
                    "ok": result.ok,
                    "violations": [
                        {"kind": violation.kind, "path": violation.path, "message": violation.message}
                        for violation in result.violations
                    ],
                }
                for result in results
            ],
        }
        sys.stdout.write(json.dumps(payload, indent=2))
        sys.stdout.write("\n")
        return 1 if failed else 0

    if not failed:
        eprint(f"ok: {len(results)} skill usage record(s) valid")
        return 0

    eprint(f"error: {len(failed)} skill usage record file(s) invalid")
    for result in failed:
        eprint(result.path)
        for violation in result.violations:
            eprint(f"  - {violation.kind} at {violation.path}: {violation.message}")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
