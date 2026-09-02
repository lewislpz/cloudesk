#!/usr/bin/env python3
from __future__ import annotations

import subprocess
from pathlib import Path

from control_config import find_repository_root, load_config
from control_io import atomic_write_text

START = "<!-- codex-workflow:start -->"
END = "<!-- codex-workflow:end -->"
GITIGNORE_BLOCK = """# codex-workflow generated files
.DS_Store
**/__pycache__/
.codex/evals/results/*.json
"""


def managed_block(template: str) -> str:
    start = template.index(START)
    end = template.index(END) + len(END)
    return template[start:end]


def install_agents(repository: Path) -> None:
    target = repository / "AGENTS.md"
    template = (repository / ".codex" / "templates" / "AGENTS.md").read_text(
        encoding="utf-8"
    )
    block = managed_block(template)
    if not target.exists():
        atomic_write_text(target, template.rstrip() + "\n")
        return
    current = target.read_text(encoding="utf-8")
    has_start = START in current
    has_end = END in current
    if has_start != has_end:
        raise ValueError("AGENTS.md contains an incomplete codex workflow block")
    if has_start:
        prefix, rest = current.split(START, 1)
        _, suffix = rest.split(END, 1)
        updated = prefix.rstrip() + "\n\n" + block + suffix
    else:
        updated = current.rstrip() + "\n\n" + block + "\n"
    atomic_write_text(target, updated)


def install_gitignore(repository: Path) -> None:
    target = repository / ".gitignore"
    current = target.read_text(encoding="utf-8") if target.exists() else ""
    missing = [
        line
        for line in GITIGNORE_BLOCK.splitlines()
        if line and line not in current.splitlines()
    ]
    if missing:
        atomic_write_text(target, current.rstrip() + "\n\n" + "\n".join(missing) + "\n")


def main() -> int:
    repository = find_repository_root(Path("."))
    config = load_config(repository)
    subprocess.run(
        ["python3", ".codex/scripts/control_doctor.py"], cwd=repository, check=True
    )
    for configured_root in config.get("workspace_roots", []):
        (repository / configured_root).mkdir(parents=True, exist_ok=True)
    install_agents(repository)
    install_gitignore(repository)
    subprocess.run(
        ["bash", ".codex/scripts/validate-workflows.sh"], cwd=repository, check=True
    )
    print("agentic workflow bootstrap complete")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
