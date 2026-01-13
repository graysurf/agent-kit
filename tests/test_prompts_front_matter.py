from __future__ import annotations

from pathlib import Path

import pytest


def parse_front_matter(text: str) -> dict[str, str]:
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        raise ValueError("missing YAML front matter start marker '---'")

    end = None
    for i in range(1, len(lines)):
        if lines[i].strip() == "---":
            end = i
            break
    if end is None:
        raise ValueError("missing YAML front matter end marker '---'")

    fm_lines = lines[1:end]
    data: dict[str, str] = {}
    for raw in fm_lines:
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        if ":" not in line:
            raise ValueError(f"invalid YAML front matter line (expected key: value): {raw!r}")
        key, value = line.split(":", 1)
        key = key.strip()
        value = value.strip()
        if not key:
            raise ValueError(f"invalid YAML front matter key: {raw!r}")
        data[key] = value
    return data


@pytest.mark.parametrize("prompt_path", sorted(Path("prompts").glob("*.md")))
def test_prompts_front_matter_required_keys(prompt_path: Path):
    text = prompt_path.read_text("utf-8")
    fm = parse_front_matter(text)

    assert "description" in fm, f"missing 'description' in {prompt_path}"
    assert "argument-hint" in fm, f"missing 'argument-hint' in {prompt_path}"
