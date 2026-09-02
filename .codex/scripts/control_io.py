#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import os
import re
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

STATUSES = {
    "draft",
    "awaiting_approval",
    "approved",
    "in_progress",
    "blocked",
    "completed",
    "delivered",
    "cancelled",
}
WORKFLOWS = {"audit", "think", "forge", "test", "pr", "ship"}
RISKS = {"low", "medium", "high"}
TRANSITIONS = {
    "draft": {"awaiting_approval", "cancelled"},
    "awaiting_approval": {"approved", "draft", "cancelled"},
    "approved": {"in_progress", "cancelled"},
    "in_progress": {"blocked", "completed", "cancelled"},
    "blocked": {"in_progress", "cancelled"},
    "completed": {"delivered"},
    "delivered": set(),
    "cancelled": set(),
}
class ControlError(Exception):
    pass


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def parse_timestamp(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def read_frontmatter(path: Path) -> tuple[dict[str, str], str]:
    text = path.read_text(encoding="utf-8")
    lines = text.splitlines()
    if not lines or lines[0] != "---":
        raise ControlError(f"missing frontmatter: {path}")
    try:
        end = lines.index("---", 1)
    except ValueError as error:
        raise ControlError(f"unterminated frontmatter: {path}") from error
    data: dict[str, str] = {}
    for line in lines[1:end]:
        if not line.strip():
            continue
        if ":" not in line:
            raise ControlError(f"invalid frontmatter line in {path}: {line}")
        key, value = line.split(":", 1)
        data[key.strip()] = value.strip()
    return data, "\n".join(lines[end + 1 :])


def write_frontmatter(path: Path, data: dict[str, str], body: str) -> None:
    lines = ["---", *(f"{key}: {value}" for key, value in data.items()), "---", body]
    atomic_write_text(path, "\n".join(lines).rstrip() + "\n")


def read_json(path: Path, default: Any = None) -> Any:
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, data: Any) -> None:
    atomic_write_text(path, json.dumps(data, indent=2, sort_keys=True) + "\n")


def atomic_write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary = tempfile.mkstemp(dir=path.parent, prefix=f".{path.name}.")
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
            handle.write(content)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def append_jsonl(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(data, sort_keys=True) + "\n")


def file_hash(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def contained_workspace_file(workspace: Path, relative: str) -> Path:
    candidate = Path(relative)
    if candidate.is_absolute():
        raise ControlError("gate evidence must be relative to the workspace")
    workspace_root = workspace.resolve()
    resolved = (workspace / candidate).resolve()
    try:
        resolved.relative_to(workspace_root)
    except ValueError as error:
        raise ControlError("gate evidence must be stored inside the workspace") from error
    if not resolved.is_file():
        raise ControlError(f"missing evidence: {relative}")
    return resolved


def unchecked_tasks(plan_path: Path) -> list[str]:
    if not plan_path.exists():
        return []
    text = plan_path.read_text(encoding="utf-8")
    canonical_pattern = re.compile(
        r"(?m)^- \[([ xX])\] Task ([a-z0-9]+(?:-[a-z0-9]+)*): .+$"
    )
    canonical_tasks = list(canonical_pattern.finditer(text))
    if canonical_tasks:
        return [match.group(0) for match in canonical_tasks if match.group(1) == " "]
    return re.findall(r"(?m)^- \[ \] .+$", text)


def required_artifacts(workspace: Path, workflow: str, state: str) -> list[Path]:
    common = [workspace / "status.md"]
    if workflow == "think":
        if state in {"awaiting_approval", "approved", "in_progress", "completed", "delivered"}:
            return common + [
                workspace / "investigation.md",
                workspace / "design.md",
                workspace / "plan.md",
            ]
        return common
    if workflow == "forge":
        artifacts = common + [
            workspace / "investigation.md",
            workspace / "design.md",
            workspace / "plan.md",
        ]
        if state in {"in_progress", "blocked", "completed", "delivered"}:
            artifacts.append(workspace / "implementation.md")
        return artifacts
    if workflow == "test":
        alternatives = [workspace / "test-matrix.md", workspace / "plan.md"]
        if not any(path.exists() for path in alternatives):
            return common + [workspace / "test-matrix.md"]
        if state in {"completed", "delivered"}:
            return common + [workspace / "implementation.md"]
    if workflow == "audit" and state in {"completed", "delivered"}:
        return common + [
            workspace / "1-guidelines-findings.md",
            workspace / "2-security-findings.md",
            workspace / "3-architecture-findings.md",
            workspace / "audit-report.md",
        ]
    return common
