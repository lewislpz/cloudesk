#!/usr/bin/env python3
import tempfile
from pathlib import Path
import subprocess

from control_actions import select_workspace, transition_workspace
from control_eval_config import run_config_scenario
from control_eval_hardening import run_hardening_scenario
from control_eval_plans import run_plan_scenario
from control_io import ControlError, file_hash, write_json
from control_eval_fixtures import write_workspace
from control_validation import validate_scope, validate_workspace


def run_scenario(scenario: str) -> int:
    with tempfile.TemporaryDirectory(prefix="codex-control-eval-") as temp:
        root = Path(temp)
        config_result = run_config_scenario(scenario, root)
        if config_result is not None:
            return config_result
        hardening_result = run_hardening_scenario(scenario, root)
        if hardening_result is not None:
            return hardening_result
        plan_result = run_plan_scenario(scenario, root)
        if plan_result is not None:
            return plan_result
        if scenario == "approved-with-pending-approval":
            workspace = write_workspace(root, state="approved", approved_by="pending")
            return int(bool(validate_workspace(workspace)))
        if scenario == "completed-with-open-task":
            workspace = write_workspace(root, state="completed", open_task=True)
            return int(bool(validate_workspace(workspace)))
        if scenario == "completed-without-gates":
            workspace = write_workspace(root, state="completed", risk="high")
            return int(bool(validate_workspace(workspace)))
        if scenario == "invalid-timestamp":
            workspace = write_workspace(root, state="approved", timestamp="invalid")
            return int(bool(validate_workspace(workspace)))
        if scenario == "declared-technical-gate":
            workspace = write_workspace(root, state="completed")
            write_json(
                workspace / "control" / "gates.json",
                {"consistency": {"actor": "main", "evidence": [], "status": "passed"}},
            )
            return int(bool(validate_workspace(workspace)))
        if scenario == "stale-gate-evidence":
            workspace = write_workspace(root, state="completed")
            evidence = workspace / "evidence.md"
            evidence.write_text("current", encoding="utf-8")
            write_json(
                workspace / "control" / "gates.json",
                {
                    "consistency": {
                        "actor": "main",
                        "command": "true",
                        "evidence": [{"path": "evidence.md", "sha256": "stale"}],
                        "exit_code": 0,
                        "status": "passed",
                    }
                },
            )
            return int(bool(validate_workspace(workspace)))
        if scenario == "valid-completed-workspace":
            workspace = write_workspace(root, state="completed")
            evidence = workspace / "evidence.md"
            evidence.write_text("current", encoding="utf-8")
            write_json(
                workspace / "control" / "gates.json",
                {
                    "consistency": {
                        "actor": "main",
                        "command": "printf verified",
                        "evidence": [
                            {"path": "evidence.md", "sha256": file_hash(evidence)}
                        ],
                        "execution": "run-gate",
                        "exit_code": 0,
                        "status": "passed",
                    }
                },
            )
            return int(bool(validate_workspace(workspace)))
        if scenario == "selection-ignores-draft":
            approved = write_workspace(root, state="approved")
            approved.rename(root / "approved")
            root.joinpath("workspace")
            draft = write_workspace(root, state="draft", approved_by="pending")
            draft.rename(root / "newer-draft")
            return 0 if select_workspace(root).name == "approved" else 1
        if scenario == "delegation-scope-violation":
            contract = root / "contract.json"
            write_json(
                contract,
                {
                    "allowed_paths": ["backend/**"],
                    "forbidden_paths": ["frontend/**"],
                },
            )
            return int(bool(validate_scope(contract, ["frontend/App.tsx"])))
        if scenario == "same-actor-independent-review":
            workspace = write_workspace(root, state="completed", risk="high")
            evidence = workspace / "evidence.md"
            evidence.write_text("reviewed", encoding="utf-8")
            hashed = [{"path": "evidence.md", "sha256": file_hash(evidence)}]
            write_json(
                workspace / "control" / "implementation.json",
                {"actor": "main"},
            )
            write_json(
                workspace / "control" / "gates.json",
                {
                    "threat_model": {
                        "actor": "architect",
                        "evidence": hashed,
                        "execution": "run-gate",
                        "status": "passed",
                    },
                    "tests": {
                        "actor": "main",
                        "command": "true",
                        "evidence": hashed,
                        "execution": "run-gate",
                        "exit_code": 0,
                        "status": "passed",
                    },
                    "integration": {
                        "actor": "main",
                        "command": "true",
                        "evidence": hashed,
                        "execution": "run-gate",
                        "exit_code": 0,
                        "status": "passed",
                    },
                    "independent_review": {
                        "actor": "main",
                        "evidence": hashed,
                        "status": "passed",
                    },
                    "user_approval": {
                        "actor": "user",
                        "evidence": hashed,
                        "status": "passed",
                    },
                },
            )
            return int(bool(validate_workspace(workspace)))
        if scenario == "manual-gate-persists":
            workspace = write_workspace(root, state="in_progress", risk="medium")
            evidence = workspace / "review.md"
            evidence.write_text("reviewed", encoding="utf-8")
            control_path = Path(__file__).with_name("control.py")
            result = subprocess.run(
                [
                    "python3",
                    str(control_path),
                    "record-gate",
                    str(workspace),
                    "review",
                    "--actor",
                    "reviewer",
                    "--evidence",
                    "review.md",
                ],
                text=True,
                capture_output=True,
                check=False,
            )
            gates = workspace / "control" / "gates.json"
            return 0 if result.returncode == 0 and gates.exists() else 1
        if scenario == "medium-completion-without-binding":
            workspace = write_workspace(root, state="completed", risk="medium")
            evidence = workspace / "review.md"
            evidence.write_text("reviewed", encoding="utf-8")
            hashed = [{"path": "review.md", "sha256": file_hash(evidence)}]
            write_json(
                workspace / "control" / "gates.json",
                {
                    "tests": {
                        "actor": "main",
                        "command": "true",
                        "evidence": hashed,
                        "exit_code": 0,
                        "status": "passed",
                    },
                    "review": {
                        "actor": "reviewer",
                        "evidence": hashed,
                        "status": "passed",
                    },
                },
            )
            return int(bool(validate_workspace(workspace)))
        if scenario == "draft-to-completed":
            workspace = write_workspace(root, state="draft", approved_by="pending")
            try:
                transition_workspace(workspace, "completed", "user", [])
            except ControlError:
                return 1
            return 0
    raise ControlError(f"unknown eval scenario: {scenario}")
