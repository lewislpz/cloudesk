#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path

from control_eval_fixtures import write_workspace
from control_io import file_hash, write_json
from control_validation import validate_workspace


def run_plan_scenario(scenario: str, root: Path) -> int | None:
    plans = {
        "canonical-plan-closed-task": """# Plan

- [x] Task task-1: verified outcome
  - Owner: `main`
  - Note: [ ] metadata is not a task marker
""",
        "canonical-plan-open-task": """# Plan

- [ ] Task task-1: unfinished outcome
  - Owner: `main`
""",
    }
    if scenario not in plans:
        return None
    workspace = write_workspace(root, state="completed")
    evidence = workspace / "evidence.md"
    evidence.write_text("current", encoding="utf-8")
    write_json(
        workspace / "control" / "gates.json",
        {
            "consistency": {
                "actor": "main",
                "command": "printf verified",
                "evidence": [{"path": "evidence.md", "sha256": file_hash(evidence)}],
                "execution": "run-gate",
                "exit_code": 0,
                "status": "passed",
            }
        },
    )
    workspace.joinpath("plan.md").write_text(plans[scenario], encoding="utf-8")
    return int(bool(validate_workspace(workspace)))
