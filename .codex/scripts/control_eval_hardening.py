#!/usr/bin/env python3
from __future__ import annotations

import os
import subprocess
from pathlib import Path

from control_actions import record_gate, transition_workspace
from control_bindings import bind_files
from control_eval_fixtures import write_workspace
from control_eval_git import run_git_scenario
from control_eval_skills import run_skill_scenario
from control_config import DEFAULT_CONFIG, validate_config
from control_io import ControlError, file_hash, read_json, write_json
from control_validation import validate_workspace


def write_consistency_gate(workspace: Path) -> Path:
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
    return evidence


def run_hardening_scenario(scenario: str, root: Path) -> int | None:
    skill_result = run_skill_scenario(scenario, root)
    if skill_result is not None:
        return skill_result
    git_result = run_git_scenario(scenario, root)
    if git_result is not None:
        return git_result
    if scenario == "evidence-parent-traversal":
        workspace = write_workspace(root, state="in_progress", risk="medium")
        root.joinpath("outside.md").write_text("outside", encoding="utf-8")
        try:
            record_gate(workspace, "review", "reviewer", ["../outside.md"], "")
        except ControlError:
            return 1
        return 0
    if scenario == "evidence-symlink-escape":
        workspace = write_workspace(root, state="in_progress", risk="medium")
        outside = root / "outside.md"
        outside.write_text("outside", encoding="utf-8")
        workspace.joinpath("external.md").symlink_to(outside)
        try:
            record_gate(workspace, "review", "reviewer", ["external.md"], "")
        except ControlError:
            return 1
        return 0
    if scenario == "unsafe-gate-name":
        codex = root / ".codex"
        codex.mkdir()
        config = {
            **DEFAULT_CONFIG,
            "gates": {
                **DEFAULT_CONFIG["gates"],
                "low": ["../escaped"],
                "technical": ["../escaped"],
            },
        }
        write_json(codex / "config.json", config)
        return int(bool(validate_config(root)))
    if scenario == "manual-gate-without-evidence":
        workspace = write_workspace(root, state="in_progress", risk="medium")
        try:
            record_gate(workspace, "review", "reviewer", [], "", None)
        except ControlError:
            return 1
        return 0
    if scenario == "bind-missing-root":
        workspace = write_workspace(root, state="in_progress", risk="medium")
        try:
            bind_files(workspace, root, ["missing"])
        except ControlError:
            return 1
        return 0
    if scenario == "completed-to-delivered-invalid":
        workspace = write_workspace(root, state="completed")
        evidence = write_consistency_gate(workspace)
        evidence.write_text("stale", encoding="utf-8")
        try:
            transition_workspace(workspace, "delivered", "user", [])
        except ControlError:
            return 1
        return 0
    if scenario == "technical-gate-noop":
        workspace = write_workspace(root, state="completed")
        evidence = write_consistency_gate(workspace)
        gates = workspace / "control" / "gates.json"
        receipt = {
            "consistency": {
                "actor": "main",
                "command": "true",
                "evidence": [{"path": "evidence.md", "sha256": file_hash(evidence)}],
                "execution": "run-gate",
                "exit_code": 0,
                "status": "passed",
            }
        }
        write_json(gates, receipt)
        return int(bool(validate_workspace(workspace)))
    if scenario == "manually-recorded-technical-gate":
        workspace = write_workspace(root, state="in_progress")
        evidence = workspace / "evidence.md"
        evidence.write_text("claimed", encoding="utf-8")
        try:
            record_gate(
                workspace,
                "consistency",
                "main",
                ["evidence.md"],
                "printf verified",
                0,
            )
        except ControlError:
            return 1
        return 0
    if scenario == "concurrent-metric-mutations":
        workspace = write_workspace(root, state="in_progress")
        control_path = Path(__file__).with_name("control.py")
        processes = [
            subprocess.Popen(
                [
                    "python3",
                    str(control_path),
                    "metric",
                    str(workspace),
                    "concurrent",
                    "1",
                ],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )
            for _ in range(8)
        ]
        exits = [process.wait() for process in processes]
        metrics = read_json(workspace / "control" / "metrics.json", {})
        count = metrics.get("counters", {}).get("concurrent")
        return 0 if all(exit_code == 0 for exit_code in exits) and count == 8 else 1
    if scenario == "completed-to-delivered-valid":
        workspace = write_workspace(root, state="completed")
        write_consistency_gate(workspace)
        transition_workspace(workspace, "delivered", "user", [])
        status = workspace.joinpath("status.md").read_text(encoding="utf-8")
        return 0 if "status: delivered" in status else 1
    if scenario == "copy-paste-bootstrap":
        if os.environ.get("CODEX_SKIP_PORTABILITY_CHECK") == "1":
            return 0
        script = Path(__file__).with_name("control_portability_check.py")
        result = subprocess.run(["python3", str(script)], check=False)
        return result.returncode
    return None
