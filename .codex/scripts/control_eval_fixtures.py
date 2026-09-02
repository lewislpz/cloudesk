#!/usr/bin/env python3
from pathlib import Path


def write_workspace(
    root: Path,
    *,
    state: str,
    risk: str = "low",
    approved_by: str = "user",
    timestamp: str = "2026-06-09T06:00:00+00:00",
    open_task: bool = False,
) -> Path:
    workspace = root / "workspace"
    workspace.mkdir()
    workspace.joinpath("status.md").write_text(
        f"""---
id: eval-workspace
workflow: forge
status: {state}
phase: eval
risk: {risk}
approved_by: {approved_by}
created_at: {timestamp}
updated_at: {timestamp}
---

# Status
""",
        encoding="utf-8",
    )
    marker = " " if open_task else "x"
    workspace.joinpath("plan.md").write_text(
        f"# Plan\n\n- [{marker}] eval task\n", encoding="utf-8"
    )
    for artifact in ("investigation.md", "design.md", "implementation.md"):
        workspace.joinpath(artifact).write_text(f"# {artifact}\n", encoding="utf-8")
    return workspace
