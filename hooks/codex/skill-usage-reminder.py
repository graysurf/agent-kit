#!/usr/bin/env python3
"""UserPromptSubmit hook: remind high-impact skill workflows to retain usage records."""

from __future__ import annotations

import json
import os
import sys
from collections.abc import Iterable, Mapping
from typing import Any

from hook_common import ALLOW, read_payload


PROMPT_KEYS = ("prompt", "user_prompt", "message", "input")

SKILL_ALIASES: dict[str, tuple[str, ...]] = {
    "gh-fix-ci": ("gh-fix-ci", "fix ci", "fix github actions", "github actions failure"),
    "web-qa": ("web-qa", "web qa", "browser qa"),
    "release-workflow": ("release-workflow", "release workflow", "cut release", "publish release"),
    "deliver-github-pr": ("deliver-github-pr", "deliver github pr"),
    "deliver-gitlab-mr": ("deliver-gitlab-mr", "deliver gitlab mr"),
    "issue-pr-review": ("issue-pr-review", "issue pr review"),
    "plan-issue-delivery": ("plan-issue-delivery", "plan issue delivery"),
    "find-and-fix-bugs": ("find-and-fix-bugs", "find and fix bugs"),
    "fix-bug-pr": ("fix-bug-pr", "fix bug pr"),
    "semgrep-find-and-fix": ("semgrep-find-and-fix", "semgrep find and fix"),
}

ACTION_HINTS = (
    "use",
    "run",
    "execute",
    "do ",
    "fix",
    "deliver",
    "release",
    "publish",
    "review ",
    "scan",
    "implement",
)


def _iter_strings(value: Any) -> Iterable[str]:
    if isinstance(value, str):
        yield value
        return
    if isinstance(value, Mapping):
        for nested in value.values():
            yield from _iter_strings(nested)
        return
    if isinstance(value, list | tuple):
        for nested in value:
            yield from _iter_strings(nested)


def prompt_text(payload: Mapping[str, Any]) -> str:
    parts: list[str] = []
    for key in PROMPT_KEYS:
        value = payload.get(key)
        if isinstance(value, str):
            parts.append(value)

    # Some clients wrap prompt content under nested message arrays. Keep this as
    # a fallback so exact skill links still trigger without depending on shape.
    if not parts:
        parts.extend(_iter_strings(payload))
    return "\n".join(parts)


def explicit_skill_invocation(text: str, skill: str) -> bool:
    return any(
        marker in text
        for marker in (
            f"${skill}",
            f"[${skill}]",
            f"<name>{skill}</name>",
            f"/{skill}/SKILL.md".lower(),
        )
    )


def matched_skills(prompt: str) -> list[str]:
    text = prompt.lower()
    matches: list[str] = []
    for skill, aliases in SKILL_ALIASES.items():
        alias_match = any(alias in text for alias in aliases)
        stripped = text
        for alias in aliases:
            stripped = stripped.replace(alias, " ")
        actionish = any(hint in stripped for hint in ACTION_HINTS)
        if alias_match and (actionish or explicit_skill_invocation(text, skill)):
            matches.append(skill)
    return matches


def emit_reminder(skills: list[str]) -> None:
    skill_list = ", ".join(skills)
    context = f"""[agent-kit] High-impact skill workflow detected: {skill_list}.
If this turn actually invokes the skill and performs file edits, tool/API calls, validation, delivery, external lookup, or durable artifact creation, retain a skill-usage.record.v1 envelope:
  agent-out project --topic skill-usage --mkdir
  skill-usage init ...; skill-usage record-validation ...; skill-usage record-outcome ...; skill-usage verify --out <record-dir> --format json
Keep detailed evidence in typed child records and link them from the envelope. This hook is a reminder only; do not auto-generate or hand-edit records. See docs/runbooks/skills/SKILL_USAGE_RECORDING_V1.md."""
    sys.stdout.write(
        json.dumps(
            {
                "hookSpecificOutput": {
                    "hookEventName": "UserPromptSubmit",
                    "additionalContext": context,
                }
            }
        )
    )
    sys.stdout.write("\n")


def main() -> int:
    if os.environ.get("AGENT_KIT_SUPPRESS_SKILL_USAGE_REMINDER") == "1":
        return ALLOW

    payload = read_payload()
    prompt = prompt_text(payload)
    if not prompt:
        return ALLOW

    skills = matched_skills(prompt)
    if not skills:
        return ALLOW

    emit_reminder(skills)
    return ALLOW


if __name__ == "__main__":
    raise SystemExit(main())
