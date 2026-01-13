from __future__ import annotations

import json
import os
import subprocess
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class ScriptRunResult:
    script: str
    argv: list[str]
    exit_code: int
    duration_ms: int
    stdout_path: str
    stderr_path: str
    status: str  # pass|fail
    note: str | None = None


SCRIPT_RUN_RESULTS: list[ScriptRunResult] = []


def repo_root() -> Path:
    if code_home := os.environ.get("CODEX_HOME"):
        p = Path(code_home)
        if p.is_dir():
            return p.resolve()
    root = subprocess.check_output(["git", "rev-parse", "--show-toplevel"], text=True).strip()
    return Path(root).resolve()


def out_dir() -> Path:
    return repo_root() / "out" / "tests" / "script-regression"


def _coerce_str_env(env: dict[str, Any]) -> dict[str, str]:
    out: dict[str, str] = {}
    for key, value in env.items():
        if value is None:
            continue
        out[str(key)] = str(value)
    return out


def load_script_specs(spec_root: Path) -> dict[str, dict[str, Any]]:
    specs: dict[str, dict[str, Any]] = {}
    if not spec_root.exists():
        return specs

    for spec_path in sorted(spec_root.rglob("*.json")):
        rel = spec_path.relative_to(spec_root)
        script_rel = rel.with_suffix("")  # drop ".json"
        raw = json.loads(spec_path.read_text("utf-8"))
        if not isinstance(raw, dict):
            raise TypeError(f"spec must be a JSON object: {spec_path}")
        specs[script_rel.as_posix()] = raw

    return specs


def discover_scripts() -> list[str]:
    tracked = subprocess.check_output(["git", "ls-files"], text=True).splitlines()
    scripts: list[str] = []
    for p in tracked:
        if p.endswith(".md"):
            continue
        if p.startswith("scripts/") or (p.startswith("skills/") and "/scripts/" in p):
            scripts.append(p)
    return sorted(scripts)


def write_summary_json(results: list[ScriptRunResult]) -> Path:
    out_base = out_dir()
    out_base.mkdir(parents=True, exist_ok=True)
    summary_path = out_base / "summary.json"

    payload = {
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
        "repo_root": str(repo_root()),
        "python": sys.version.splitlines()[0],
        "results": [
            {
                "script": r.script,
                "argv": r.argv,
                "exit_code": r.exit_code,
                "duration_ms": r.duration_ms,
                "stdout_path": r.stdout_path,
                "stderr_path": r.stderr_path,
                "status": r.status,
                "note": r.note,
            }
            for r in results
        ],
    }

    summary_path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", "utf-8")
    return summary_path


def pytest_sessionfinish(session, exitstatus):  # type: ignore[no-untyped-def]
    summary_path = write_summary_json(SCRIPT_RUN_RESULTS)
    if hasattr(session.config, "stash"):
        session.config.stash["script_regression_summary_path"] = str(summary_path)
