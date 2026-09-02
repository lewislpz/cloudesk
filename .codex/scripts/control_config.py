#!/usr/bin/env python3
from __future__ import annotations

import fnmatch
import json
import re
from pathlib import Path
from typing import Any

DEFAULT_CONFIG: dict[str, Any] = {
    "binding_excludes": [
        ".git/**",
        ".orchestrator/**",
        ".next/**",
        ".turbo/**",
        ".codex/evals/results/**",
        "**/.DS_Store",
        "**/__pycache__/**",
        "**/.next/**",
        "**/.turbo/**",
        "**/coverage/**",
        "**/dist/**",
        "**/node_modules/**",
        "coverage/**",
        "dist/**",
        "node_modules/**",
    ],
    "documentation_candidates": ["docs/00-general-docs.md", "README.md"],
    "forbidden_gate_commands": [":", "exit 0", "true"],
    "git": {"primary_branches": ["main", "master"], "remote": "origin"},
    "gates": {
        "low": ["consistency"],
        "medium": ["tests", "review"],
        "high": [
            "threat_model",
            "tests",
            "integration",
            "independent_review",
            "user_approval",
        ],
        "technical": ["consistency", "integration", "tests"],
    },
    "version": 1,
    "workspace_roots": [".orchestrator/plans", ".orchestrator/audits"],
}
GATE_NAME_PATTERN = re.compile(r"^[a-z][a-z0-9_-]*$")
CONFIG_KEYS = {
    "$schema",
    "binding_excludes",
    "documentation_candidates",
    "forbidden_gate_commands",
    "gates",
    "git",
    "version",
    "workspace_roots",
}
REQUIRED_CONFIG_KEYS = CONFIG_KEYS - {"$schema"}


def find_repository_root(start: Path) -> Path:
    resolved = start.resolve()
    if resolved.is_file():
        resolved = resolved.parent
    for candidate in (resolved, *resolved.parents):
        if (candidate / ".codex").is_dir():
            return candidate
    return Path.cwd().resolve()


def load_config(start: Path = Path(".")) -> dict[str, Any]:
    path = find_repository_root(start) / ".codex" / "config.json"
    if not path.exists():
        return DEFAULT_CONFIG
    config = json.loads(path.read_text(encoding="utf-8"))
    return {
        **DEFAULT_CONFIG,
        **config,
        "gates": {**DEFAULT_CONFIG["gates"], **config.get("gates", {})},
        "git": {**DEFAULT_CONFIG["git"], **config.get("git", {})},
    }


def validate_config(start: Path = Path(".")) -> list[str]:
    path = find_repository_root(start) / ".codex" / "config.json"
    if not path.exists():
        config = DEFAULT_CONFIG
    else:
        try:
            config = json.loads(path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError) as error:
            return [f"invalid config JSON: {error}"]
    if not isinstance(config, dict):
        return ["config must be a JSON object"]
    errors: list[str] = []
    for key in sorted(set(config) - CONFIG_KEYS):
        errors.append(f"unknown config field: {key}")
    for key in sorted(REQUIRED_CONFIG_KEYS - set(config)):
        errors.append(f"missing config field: {key}")
    if "$schema" in config and not isinstance(config["$schema"], str):
        errors.append("config $schema must be a string")
    if type(config.get("version")) is not int or config.get("version") != 1:
        errors.append("config version must be 1")
    for field in (
        "binding_excludes",
        "documentation_candidates",
        "forbidden_gate_commands",
        "workspace_roots",
    ):
        values = config.get(field)
        if not isinstance(values, list) or not values or not all(
            isinstance(value, str) and value for value in values
        ):
            errors.append(f"config field must be a non-empty string list: {field}")
    gates = config.get("gates", {})
    if not isinstance(gates, dict):
        errors.append("config gates must be an object")
        gates = {}
    for key in sorted(set(gates) - {"low", "medium", "high", "technical"}):
        errors.append(f"unknown config gate policy: {key}")
    for risk in ("low", "medium", "high"):
        values = gates.get(risk)
        if not isinstance(values, list) or not values or not all(
            isinstance(value, str) for value in values
        ):
            errors.append(f"config requires gates for risk: {risk}")
    technical_values = gates.get("technical", [])
    if not isinstance(technical_values, list) or not all(
        isinstance(value, str) for value in technical_values
    ):
        errors.append("config technical gates must be a string list")
        technical_values = []
    technical = set(technical_values)
    declared = set().union(
        *(set(gates.get(risk, [])) for risk in ("low", "medium", "high")
          if isinstance(gates.get(risk), list))
    )
    if not technical <= declared:
        errors.append("technical gates must also be declared in a risk policy")
    for gate_name in declared | technical:
        if not isinstance(gate_name, str) or not GATE_NAME_PATTERN.fullmatch(gate_name):
            errors.append(f"invalid gate name: {gate_name}")
    git = config.get("git", {})
    if not isinstance(git, dict):
        errors.append("config Git settings must be an object")
        git = {}
    for key in sorted(set(git) - {"primary_branches", "remote"}):
        errors.append(f"unknown config Git field: {key}")
    remote = git.get("remote")
    branches = git.get("primary_branches")
    if not isinstance(remote, str) or not remote or not isinstance(branches, list) \
            or not branches or not all(isinstance(value, str) and value for value in branches):
        errors.append("config requires Git remote and primary branches")
    return errors


def required_gates(start: Path, risk: str) -> set[str]:
    return set(load_config(start).get("gates", {}).get(risk, []))


def technical_gates(start: Path) -> set[str]:
    return set(load_config(start).get("gates", {}).get("technical", []))


def is_valid_gate_name(gate_name: str) -> bool:
    return bool(GATE_NAME_PATTERN.fullmatch(gate_name))


def is_excluded(path: str, patterns: list[str]) -> bool:
    normalized = path.replace("\\", "/")
    return any(
        fnmatch.fnmatch(normalized, pattern)
        or fnmatch.fnmatch(f"/{normalized}", f"*/{pattern}")
        for pattern in patterns
    )
