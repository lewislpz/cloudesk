#!/usr/bin/env python3
from __future__ import annotations

import re
import sys
from pathlib import Path

MAX_ENTRYPOINT_WORDS = 600
NAME_PATTERN = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
MARKDOWN_LINK_PATTERN = re.compile(r"\[[^\]]+\]\(([^)]+)\)")
SKILL_REFERENCE_PATTERNS = (
    re.compile(r"`@([a-z0-9]+(?:-[a-z0-9]+)*)`"),
    re.compile(r"`@\[skills/([a-z0-9]+(?:-[a-z0-9]+)*)\]`"),
)


def frontmatter(text: str) -> dict[str, str]:
    lines = text.splitlines()
    if not lines or lines[0] != "---":
        return {}
    try:
        end = lines.index("---", 1)
    except ValueError:
        return {}
    data = {}
    for line in lines[1:end]:
        if ":" in line and not line.startswith(" "):
            key, value = line.split(":", 1)
            data[key.strip()] = value.strip().strip('"')
    return data


def validate_skill(skill_path: Path, available: set[str]) -> list[str]:
    errors = []
    text = skill_path.read_text(encoding="utf-8")
    metadata = frontmatter(text)
    directory_name = skill_path.parent.name
    if metadata.get("name") != directory_name or not NAME_PATTERN.fullmatch(directory_name):
        errors.append(f"skill name does not match directory: {skill_path}")
    if not metadata.get("description", "").startswith("Use when"):
        errors.append(f"skill description must start with 'Use when': {skill_path}")
    words = len(text.split())
    if words > MAX_ENTRYPOINT_WORDS:
        errors.append(
            f"skill entrypoint exceeds {MAX_ENTRYPOINT_WORDS} words "
            f"({words}): {skill_path}"
        )
    for target in MARKDOWN_LINK_PATTERN.findall(text):
        if "://" in target or target.startswith(("#", "mailto:")):
            continue
        local_target = target.split("#", 1)[0]
        if local_target and not (skill_path.parent / local_target).exists():
            errors.append(f"missing local skill reference: {skill_path}: {target}")
    for pattern in SKILL_REFERENCE_PATTERNS:
        for referenced in pattern.findall(text):
            if referenced not in available:
                errors.append(f"missing referenced skill: {skill_path}: {referenced}")
    return errors


def validate_skills(root: Path) -> list[str]:
    skill_paths = sorted(root.glob("*/SKILL.md"))
    available = {path.parent.name for path in skill_paths}
    errors = []
    for skill_path in skill_paths:
        errors.extend(validate_skill(skill_path, available))
    return errors


def main() -> int:
    root = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(".codex/skills")
    errors = validate_skills(root)
    if errors:
        print("\n".join(errors), file=sys.stderr)
        return 1
    print(f"valid skills: {len(list(root.glob('*/SKILL.md')))}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
