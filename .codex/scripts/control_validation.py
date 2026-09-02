#!/usr/bin/env python3
from __future__ import annotations

import fnmatch
import re
from pathlib import Path

from control_binding_validation import validate_file_binding, validate_git_binding
from control_config import is_valid_gate_name, load_config, required_gates, technical_gates
from control_io import (
    RISKS,
    STATUSES,
    WORKFLOWS,
    ControlError,
    contained_workspace_file,
    file_hash,
    parse_timestamp,
    read_frontmatter,
    read_json,
    required_artifacts,
    unchecked_tasks,
)

RFC3339_PATTERN = re.compile(
    r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|[+-]\d{2}:\d{2})$"
)


def validate_gate_receipts(workspace: Path, risk: str) -> list[str]:
    errors: list[str] = []
    gates_path = workspace / "control" / "gates.json"
    gates = read_json(gates_path, {})
    if not isinstance(gates, dict):
        return [f"invalid gate receipt object: {gates_path}"]
    required = required_gates(workspace, risk)
    technical = technical_gates(workspace)
    for gate_name in sorted(required):
        if not is_valid_gate_name(gate_name):
            errors.append(f"invalid gate name: {gate_name}")
            continue
        receipt = gates.get(gate_name)
        if not isinstance(receipt, dict) or receipt.get("status") != "passed":
            errors.append(f"required gate not passed: {gate_name}")
            continue
        actor = receipt.get("actor")
        if not actor or actor == "pending":
            errors.append(f"gate has invalid actor: {gate_name}")
        evidence_items = receipt.get("evidence", [])
        if not evidence_items:
            errors.append(f"gate lacks evidence: {gate_name}")
        for evidence in evidence_items:
            relative_path = evidence.get("path")
            expected_hash = evidence.get("sha256")
            try:
                evidence_path = contained_workspace_file(workspace, str(relative_path))
            except ControlError as error:
                errors.append(f"invalid gate evidence for {gate_name}: {error}")
                continue
            if expected_hash and file_hash(evidence_path) != expected_hash:
                errors.append(f"stale gate evidence for {gate_name}: {relative_path}")
        if gate_name in technical:
            if receipt.get("exit_code") != 0 or not receipt.get("command"):
                errors.append(f"technical gate lacks successful command evidence: {gate_name}")
            if receipt.get("execution") != "run-gate":
                errors.append(f"technical gate was not executed by run-gate: {gate_name}")
            forbidden = load_config(workspace).get("forbidden_gate_commands", [])
            if str(receipt.get("command", "")).strip() in forbidden:
                errors.append(f"technical gate uses forbidden no-op command: {gate_name}")
        if gate_name == "user_approval" and actor != "user":
            errors.append("user approval gate must be recorded by user")
    independent = gates.get("independent_review", {})
    implementation = read_json(workspace / "control" / "implementation.json", {})
    if risk == "high" and independent.get("actor") == implementation.get("actor"):
        errors.append("independent review actor matches implementation actor")
    return errors


def validate_workspace(workspace: Path) -> list[str]:
    errors: list[str] = []
    status_path = workspace / "status.md"
    if not status_path.exists():
        return [f"missing required file: {status_path}"]
    try:
        status, _ = read_frontmatter(status_path)
    except ControlError as error:
        return [str(error)]
    required = (
        "id",
        "workflow",
        "status",
        "phase",
        "risk",
        "approved_by",
        "created_at",
        "updated_at",
    )
    for field in required:
        if not status.get(field):
            errors.append(f"missing status field: {field}")
    workflow = status.get("workflow", "")
    state = status.get("status", "")
    risk = status.get("risk", "")
    identifier = status.get("id", "")
    if identifier and not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", identifier):
        errors.append(f"invalid workspace id: {identifier}")
    if workflow not in WORKFLOWS:
        errors.append(f"invalid workflow: {workflow}")
    if state not in STATUSES:
        errors.append(f"invalid status: {state}")
    if risk not in RISKS:
        errors.append(f"invalid risk: {risk}")
    parsed_timestamps = {}
    for field in ("created_at", "updated_at"):
        value = status.get(field, "")
        if not RFC3339_PATTERN.fullmatch(value):
            errors.append(f"invalid timestamp: {field}")
            continue
        try:
            timestamp = parse_timestamp(value)
            parsed_timestamps[field] = timestamp
            if timestamp.tzinfo is None:
                errors.append(f"timestamp lacks timezone: {field}")
        except ValueError:
            errors.append(f"invalid timestamp: {field}")
    if (
        len(parsed_timestamps) == 2
        and parsed_timestamps["updated_at"] < parsed_timestamps["created_at"]
    ):
        errors.append("updated_at precedes created_at")
    if state in {"approved", "in_progress", "completed", "delivered"}:
        if status.get("approved_by") in {"", "pending"}:
            errors.append(f"status {state} requires approval")
    if workflow in WORKFLOWS:
        for artifact in required_artifacts(workspace, workflow, state):
            if not artifact.exists():
                errors.append(f"missing required artifact: {artifact.name}")
    if state in {"completed", "delivered"}:
        open_tasks = unchecked_tasks(workspace / "plan.md")
        if open_tasks:
            errors.append(f"completed workspace has {len(open_tasks)} open task(s)")
        if risk in RISKS:
            errors.extend(validate_gate_receipts(workspace, risk))
        errors.extend(validate_git_binding(workspace))
        errors.extend(validate_file_binding(workspace))
        if risk in {"medium", "high"}:
            control = workspace / "control"
            implementation = read_json(control / "implementation.json", {})
            if not implementation.get("actor"):
                errors.append("medium/high-risk completion requires implementation actor")
            if not (control / "git-binding.json").exists() and not (
                control / "file-binding.json"
            ).exists():
                errors.append("medium/high-risk completion requires Git or file binding")
    return errors


def validate_scope(contract_path: Path, changed_paths: list[str]) -> list[str]:
    contract = read_json(contract_path, {})
    allowed = contract.get("allowed_paths", [])
    forbidden = contract.get("forbidden_paths", [])
    errors = []
    for changed_path in changed_paths:
        if any(fnmatch.fnmatch(changed_path, pattern) for pattern in forbidden):
            errors.append(f"forbidden delegated path: {changed_path}")
        elif not any(fnmatch.fnmatch(changed_path, pattern) for pattern in allowed):
            errors.append(f"delegated path outside allowed scope: {changed_path}")
    return errors
