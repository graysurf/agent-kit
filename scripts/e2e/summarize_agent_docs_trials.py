#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def load_results(path: Path) -> dict[str, Any]:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise SystemExit(f"error: invalid JSON input: {path}: {exc}") from exc


def normalize_failure_reason(reason: str) -> str:
    text = reason.strip()
    if not text:
        return "none"
    if ":" in text:
        return text.split(":", 1)[0].strip().lower()
    return text.lower()


def owner_for_failure(reason: str) -> str:
    lower = reason.lower()
    if "agent-docs" in lower:
        return "Agent Docs Maintainer"
    if "agent_doc_init.sh" in lower or "agent-doc-init" in lower:
        return "Skill Maintainer"
    if "invalid command spec" in lower or "unsupported scenario kind" in lower:
        return "Trial Harness Maintainer"
    return "Rollout Operator"


def main() -> int:
    parser = argparse.ArgumentParser(description="Summarize agent-docs trial results into a markdown report.")
    parser.add_argument("--input", required=True, help="Path to trial-results.json")
    parser.add_argument("--output", required=True, help="Path to trial-summary.md")
    args = parser.parse_args()

    input_path = Path(args.input).resolve()
    output_path = Path(args.output).resolve()
    payload = load_results(input_path)
    results = payload.get("results", [])
    if not isinstance(results, list) or not results:
        raise SystemExit("error: results payload missing non-empty `results` array")

    total = len(results)
    passed = sum(1 for item in results if item.get("status") == "pass")
    failed = total - passed
    pass_rate = round((passed / total) * 100.0, 2)

    trace_ok = sum(1 for item in results if isinstance(item.get("command_trace"), list) and item["command_trace"])
    trace_completeness = round((trace_ok / total) * 100.0, 2)

    fail_reasons = Counter(
        normalize_failure_reason(str(item.get("failure_reason", "")))
        for item in results
        if item.get("status") != "pass"
    )

    top_failure_rows: list[str] = []
    if fail_reasons:
        for reason, count in fail_reasons.most_common(5):
            owner = owner_for_failure(reason)
            top_failure_rows.append(f"| {reason} | {count} | {owner} |")
    else:
        top_failure_rows.append("| none | 0 | Rollout Operator |")

    threshold_pass_rate = 95.0
    threshold_trace = 100.0
    threshold_failed = 0
    threshold_pass = pass_rate >= threshold_pass_rate and trace_completeness >= threshold_trace and failed == threshold_failed
    go_no_go = "go" if threshold_pass else "no-go"

    lines = [
        "# Agent-Docs Trial Summary",
        "",
        f"- generated_at: {now_iso()}",
        f"- input: `{input_path}`",
        "",
        "## Metrics",
        "",
        f"- pass rate: **{pass_rate}%** ({passed}/{total})",
        f"- command trace completeness: **{trace_completeness}%** ({trace_ok}/{total})",
        f"- failed scenarios: **{failed}**",
        "",
        "## Top failure modes and remediation owners",
        "",
        "| failure_mode | count | remediation_owner |",
        "| --- | ---: | --- |",
        *top_failure_rows,
        "",
        "## go/no-go threshold evaluation",
        "",
        f"- threshold (pass rate): >= {threshold_pass_rate}%",
        f"- threshold (command trace completeness): >= {threshold_trace}%",
        f"- threshold (failed scenarios): <= {threshold_failed}",
        f"- go/no-go decision: **{go_no_go}**",
        "",
        "## Evidence links",
        "",
        f"- raw trial results: `{input_path}`",
        f"- scenario config: `{payload.get('config_path', '')}`",
    ]

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"ok: wrote summary to {output_path}")
    print(f"decision: {go_no_go} (pass_rate={pass_rate}%, failed={failed}, trace={trace_completeness}%)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

