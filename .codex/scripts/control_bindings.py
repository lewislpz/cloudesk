#!/usr/bin/env python3
from __future__ import annotations

import os
import subprocess
from pathlib import Path

from control_config import is_excluded, load_config
from control_io import ControlError, file_hash, now_iso, write_json
from control_lock import workspace_lock


def relative_repository_path(workspace: Path, repository: Path) -> str:
    return os.path.relpath(repository.resolve(), workspace.resolve())


def git_changed_paths(repository: Path) -> list[str]:
    commands = (
        ["git", "diff", "--name-only", "--no-renames", "-z", "HEAD", "--"],
        ["git", "ls-files", "--others", "--exclude-standard", "-z"],
    )
    paths: set[str] = set()
    for command in commands:
        result = subprocess.run(
            command,
            cwd=repository,
            text=True,
            capture_output=True,
            check=False,
        )
        if result.returncode != 0:
            raise ControlError(result.stderr.strip() or "Git command failed")
        paths.update(path for path in result.stdout.split("\0") if path)
    return sorted(paths)


def git_worktree_files(repository: Path) -> dict[str, str | None]:
    return {
        path: file_hash(repository / path) if (repository / path).is_file() else None
        for path in git_changed_paths(repository)
    }


def bind_git(workspace: Path, repository: Path, allowed_paths: list[str]) -> None:
    def git(*args: str) -> str:
        result = subprocess.run(
            ["git", *args], cwd=repository, text=True, capture_output=True, check=False
        )
        if result.returncode != 0:
            raise ControlError(result.stderr.strip() or "Git command failed")
        return result.stdout.strip()

    if not allowed_paths:
        raise ControlError("Git binding requires at least one allowed path")
    with workspace_lock(workspace):
        write_json(
            workspace / "control" / "git-binding.json",
            {
                "allowed_paths": allowed_paths,
                "bound_at": now_iso(),
                "branch": git("branch", "--show-current"),
                "head_commit": git("rev-parse", "HEAD"),
                "repository": relative_repository_path(workspace, repository),
                "snapshot_version": 2,
                "worktree_files": git_worktree_files(repository),
            },
        )


def bind_files(workspace: Path, repository: Path, roots: list[str]) -> None:
    exclusions = load_config(repository).get("binding_excludes", [])
    files: dict[str, str] = {}
    for root in roots:
        root_path = repository / root
        if not root_path.exists():
            raise ControlError(f"binding root does not exist: {root}")
        try:
            root_path.resolve().relative_to(repository.resolve())
        except ValueError as error:
            raise ControlError(f"binding root is outside repository: {root}") from error
        candidates = root_path.rglob("*") if root_path.is_dir() else [root_path]
        for path in candidates:
            if not path.is_file():
                continue
            relative = str(path.relative_to(repository))
            if not is_excluded(relative, exclusions):
                files[relative] = file_hash(path)
    if not files:
        raise ControlError("file binding contains no source files")
    with workspace_lock(workspace):
        write_json(
            workspace / "control" / "file-binding.json",
            {
                "bound_at": now_iso(),
                "files": files,
                "repository": relative_repository_path(workspace, repository),
                "roots": roots,
            },
        )
