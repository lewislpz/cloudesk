#!/usr/bin/env python3
from __future__ import annotations

import subprocess
from pathlib import Path

from control_config import is_valid_gate_name, required_gates, technical_gates
from control_io import (
    TRANSITIONS,
    ControlError,
    atomic_write_text,
    append_jsonl,
    contained_workspace_file,
    file_hash,
    now_iso,
    read_frontmatter,
    read_json,
    write_frontmatter,
    write_json,
)
from control_lock import workspace_lock
from control_validation import validate_workspace


def record_metric(workspace: Path, name: str, value: float) -> None:
    with workspace_lock(workspace):
        path = workspace / "control" / "metrics.json"
        metrics = read_json(path, {"counters": {}, "updated_at": now_iso()})
        metrics["counters"][name] = metrics["counters"].get(name, 0) + value
        metrics["updated_at"] = now_iso()
        write_json(path, metrics)


def transition_workspace(workspace: Path, target: str, actor: str, evidence: list[str]) -> None:
    with workspace_lock(workspace):
        status_path = workspace / "status.md"
        status, body = read_frontmatter(status_path)
        current = status.get("status", "")
        if target not in TRANSITIONS.get(current, set()):
            raise ControlError(f"invalid transition: {current} -> {target}")
        if target == "approved" and actor in {"", "pending"}:
            raise ControlError("approval transition requires a concrete actor")
        original = status_path.read_text(encoding="utf-8")
        status["status"] = target
        status["updated_at"] = now_iso()
        if target == "approved":
            status["approved_by"] = actor
        write_frontmatter(status_path, status, body)
        if target in {"completed", "delivered"}:
            errors = validate_workspace(workspace)
            if errors:
                atomic_write_text(status_path, original)
                raise ControlError("; ".join(errors))
        append_jsonl(
            workspace / "control" / "events.jsonl",
            {
                "actor": actor,
                "evidence": evidence,
                "from": current,
                "timestamp": now_iso(),
                "to": target,
            },
        )
        record_metric(workspace, "transitions", 1)


def record_gate(
    workspace: Path,
    gate_name: str,
    actor: str,
    evidence_paths: list[str],
    command: str,
    exit_code: int | None = None,
    executed: bool = False,
) -> None:
    with workspace_lock(workspace):
        status, _ = read_frontmatter(workspace / "status.md")
        risk = status.get("risk", "")
        if not is_valid_gate_name(gate_name):
            raise ControlError(f"invalid gate name: {gate_name}")
        if gate_name not in required_gates(workspace, risk):
            raise ControlError(f"gate '{gate_name}' is not required for risk '{risk}'")
        if gate_name in technical_gates(workspace) and not executed:
            raise ControlError("technical gates must be executed with run-gate")
        if not actor or actor == "pending":
            raise ControlError("gate requires a concrete actor")
        if not evidence_paths:
            raise ControlError("gate requires at least one evidence file")
        evidence = []
        for relative in evidence_paths:
            path = contained_workspace_file(workspace, relative)
            evidence.append({"path": relative, "sha256": file_hash(path)})
        gates_path = workspace / "control" / "gates.json"
        gates = read_json(gates_path, {})
        gates[gate_name] = {
            "actor": actor,
            "command": command,
            "evidence": evidence,
            "execution": "run-gate" if executed else "manual",
            "exit_code": exit_code,
            "recorded_at": now_iso(),
            "status": "passed",
        }
        write_json(gates_path, gates)


def run_gate(
    workspace: Path, gate_name: str, actor: str, command: list[str], repository: Path
) -> int:
    with workspace_lock(workspace):
        if not command:
            raise ControlError("run-gate requires a command")
        if not is_valid_gate_name(gate_name):
            raise ControlError(f"invalid gate name: {gate_name}")
        result = subprocess.run(
            command, cwd=repository, text=True, capture_output=True, check=False
        )
        output_path = workspace / "control" / "gate-output" / f"{gate_name}.log"
        atomic_write_text(output_path, result.stdout + result.stderr)
        record_gate(
            workspace,
            gate_name,
            actor,
            [str(output_path.relative_to(workspace))],
            " ".join(command),
            result.returncode,
            True,
        )
        record_metric(workspace, "gate_runs", 1)
        if result.returncode != 0:
            record_metric(workspace, "failed_gate_runs", 1)
        return result.returncode


def create_checkpoint(workspace: Path, task_id: str, result: str, next_action: str) -> Path:
    with workspace_lock(workspace):
        path = workspace / "checkpoints" / f"{task_id}.json"
        write_json(
            path,
            {
                "created_at": now_iso(),
                "next_action": next_action,
                "result": result,
                "task_id": task_id,
            },
        )
        record_metric(workspace, "checkpoints", 1)
        return path


def record_implementation(workspace: Path, actor: str) -> None:
    with workspace_lock(workspace):
        write_json(
            workspace / "control" / "implementation.json",
            {"actor": actor, "recorded_at": now_iso()},
        )


def select_workspace(root: Path) -> Path:
    eligible = []
    for status_path in root.glob("*/status.md"):
        status, _ = read_frontmatter(status_path)
        if status.get("status") in {"approved", "in_progress"}:
            eligible.append(status_path.parent)
    if not eligible:
        raise ControlError(f"no approved or in-progress workspace in {root}")
    if len(eligible) > 1:
        raise ControlError("multiple eligible workspaces; provide an explicit path")
    return eligible[0]
