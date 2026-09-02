#!/usr/bin/env python3
from __future__ import annotations

import subprocess
from pathlib import Path


def run_validator(script: Path, skills: Path | None = None) -> int:
    command = ["python3", str(script)]
    if skills is not None:
        command.append(str(skills))
    return subprocess.run(
        command, check=False, capture_output=True, text=True
    ).returncode


def run_skill_scenario(scenario: str, root: Path) -> int | None:
    script = Path(__file__).with_name("control_skill_validation.py")
    if scenario == "current-skills-integrity":
        return run_validator(script)
    if scenario == "oversized-skill-entrypoint":
        skills = root / "skills"
        skill = skills / "large"
        skill.mkdir(parents=True)
        skill.joinpath("SKILL.md").write_text(
            "---\nname: large\ndescription: Use when testing size.\n---\n"
            + "word " * 601,
            encoding="utf-8",
        )
        return run_validator(script, skills)
    if scenario == "broken-local-skill-reference":
        skills = root / "skills"
        skill = skills / "broken"
        skill.mkdir(parents=True)
        skill.joinpath("SKILL.md").write_text(
            "---\nname: broken\ndescription: Use when testing references.\n---\n"
            "[Missing](references/missing.md)\n",
            encoding="utf-8",
        )
        return run_validator(script, skills)
    return None
