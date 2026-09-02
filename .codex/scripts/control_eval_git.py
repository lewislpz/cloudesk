#!/usr/bin/env python3
from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Callable

from control_bindings import bind_git
from control_eval_fixtures import write_workspace
from control_io import file_hash, read_json, write_json
from control_validation import validate_workspace


def initialize_repository(repository: Path) -> Path:
    repository.mkdir()
    subprocess.run(["git", "init", "-q"], cwd=repository, check=True)
    source = repository / "source.txt"
    source.write_text("verified", encoding="utf-8")
    subprocess.run(["git", "add", "source.txt"], cwd=repository, check=True)
    subprocess.run(
        [
            "git", "-c", "user.name=Eval", "-c", "user.email=eval@example.invalid",
            "commit", "-qm", "initial",
        ],
        cwd=repository,
        check=True,
    )
    return source


def write_gate(workspace: Path) -> None:
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


def bind_after_mutation(
    root: Path,
    mutate: Callable[[Path, Path], None],
    allowed_paths: list[str],
) -> int:
    repository = root / "repository"
    source = initialize_repository(repository)
    workspace = write_workspace(root, state="completed")
    write_gate(workspace)
    mutate(repository, source)
    bind_git(workspace, repository, allowed_paths)
    return int(bool(validate_workspace(workspace)))


def run_git_scenario(scenario: str, root: Path) -> int | None:
    if scenario == "git-binding-worktree-change":
        repository = root / "repository"
        source = initialize_repository(repository)
        workspace = write_workspace(root, state="completed")
        write_gate(workspace)
        bind_git(workspace, repository, ["source.txt"])
        source.write_text("changed", encoding="utf-8")
        return int(bool(validate_workspace(workspace)))
    if scenario in {"git-binding-staged-change", "git-binding-staged-out-of-scope"}:
        def stage(repository: Path, source: Path) -> None:
            source.write_text("staged", encoding="utf-8")
            subprocess.run(["git", "add", "source.txt"], cwd=repository, check=True)

        allowed = ["source.txt"] if scenario.endswith("change") else ["other/**"]
        return bind_after_mutation(root, stage, allowed)
    if scenario == "git-binding-staged-deletion":
        def delete(repository: Path, source: Path) -> None:
            source.unlink()
            subprocess.run(["git", "add", "source.txt"], cwd=repository, check=True)

        return bind_after_mutation(root, delete, ["source.txt"])
    if scenario == "git-binding-staged-rename":
        def rename(repository: Path, source: Path) -> None:
            source.rename(repository / "renamed.txt")
            subprocess.run(["git", "add", "-A"], cwd=repository, check=True)

        repository = root / "repository"
        initialize_repository(repository)
        workspace = write_workspace(root, state="completed")
        write_gate(workspace)
        rename(repository, repository / "source.txt")
        bind_git(workspace, repository, ["source.txt", "renamed.txt"])
        files = read_json(workspace / "control" / "git-binding.json")["worktree_files"]
        return 0 if set(files) == {"source.txt", "renamed.txt"} else 1
    if scenario == "git-binding-mixed-staged-unstaged":
        def mixed(repository: Path, source: Path) -> None:
            source.write_text("staged", encoding="utf-8")
            subprocess.run(["git", "add", "source.txt"], cwd=repository, check=True)
            source.write_text("working tree", encoding="utf-8")

        repository = root / "repository"
        source = initialize_repository(repository)
        workspace = write_workspace(root, state="completed")
        write_gate(workspace)
        mixed(repository, source)
        bind_git(workspace, repository, ["source.txt"])
        actual = read_json(workspace / "control" / "git-binding.json")[
            "worktree_files"
        ]["source.txt"]
        return 0 if actual == file_hash(source) else 1
    return None
