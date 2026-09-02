#!/usr/bin/env python3
from __future__ import annotations

import fnmatch
import subprocess
from pathlib import Path

from control_bindings import git_changed_paths
from control_config import is_excluded, load_config
from control_io import ControlError, file_hash, read_json


def binding_repository(workspace: Path, binding: dict) -> Path:
    configured = Path(binding.get("repository", "."))
    return configured if configured.is_absolute() else (workspace / configured).resolve()


def current_git_worktree(repository: Path) -> dict[str, str | None] | None:
    try:
        paths = git_changed_paths(repository)
    except ControlError:
        return None
    return {
        path: file_hash(repository / path) if (repository / path).is_file() else None
        for path in paths
    }


def validate_git_binding(workspace: Path) -> list[str]:
    binding = read_json(workspace / "control" / "git-binding.json")
    if not binding:
        return []
    repository = binding_repository(workspace, binding)
    result = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=repository,
        text=True,
        capture_output=True,
        check=False,
    )
    if result.returncode != 0:
        return ["cannot validate recorded Git binding"]
    if result.stdout.strip() != binding.get("head_commit"):
        return ["Git HEAD changed after workspace binding; gates must be renewed"]
    errors = []
    allowed_paths = binding.get("allowed_paths", [])
    if not allowed_paths:
        errors.append("Git binding has no allowed paths")
    current = current_git_worktree(repository)
    if current is None:
        errors.append("cannot inspect recorded Git working tree")
        current = {}
    if current != binding.get("worktree_files", {}):
        errors.append("Git working tree changed after workspace binding; gates must be renewed")
    for changed_path in current:
        if not any(fnmatch.fnmatch(changed_path, pattern) for pattern in allowed_paths):
            errors.append(f"Git change outside allowed scope: {changed_path}")
    return errors


def validate_file_binding(workspace: Path) -> list[str]:
    binding = read_json(workspace / "control" / "file-binding.json")
    if not binding:
        return []
    repository = binding_repository(workspace, binding)
    expected = binding.get("files", {})
    errors = []
    if not expected:
        errors.append("file binding contains no source files")
    for relative, expected_hash in expected.items():
        path = repository / relative
        if not path.exists():
            errors.append(f"bound file missing: {relative}")
        elif file_hash(path) != expected_hash:
            errors.append(f"bound file changed after verification: {relative}")
    current = set()
    exclusions = load_config(repository).get("binding_excludes", [])
    for root in binding.get("roots", []):
        root_path = repository / root
        if not root_path.exists():
            errors.append(f"binding root does not exist: {root}")
            continue
        candidates = root_path.rglob("*") if root_path.is_dir() else [root_path]
        for path in candidates:
            if path.is_file():
                relative = str(path.relative_to(repository))
                if not is_excluded(relative, exclusions):
                    current.add(relative)
    for relative in sorted(current - set(expected)):
        errors.append(f"new file added after verification: {relative}")
    return errors
