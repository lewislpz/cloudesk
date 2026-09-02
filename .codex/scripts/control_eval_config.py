#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
from typing import Any

from control_config import DEFAULT_CONFIG, validate_config
from control_eval_fixtures import write_workspace
from control_io import write_json
from control_validation import validate_workspace


def run_config_scenario(scenario: str, root: Path) -> int | None:
    if scenario == "status-non-rfc3339-timestamp":
        workspace = write_workspace(
            root, state="approved", timestamp="2026-06-09T06:00:00+0000"
        )
        return int(bool(validate_workspace(workspace)))
    configs: dict[str, dict[str, Any]] = {
        "config-unknown-key": {**DEFAULT_CONFIG, "typo": True},
        "config-missing-required": {
            key: value for key, value in DEFAULT_CONFIG.items() if key != "workspace_roots"
        },
        "config-unknown-git-key": {
            **DEFAULT_CONFIG,
            "git": {**DEFAULT_CONFIG["git"], "branch": "main"},
        },
        "config-invalid-nested-type": {
            **DEFAULT_CONFIG,
            "gates": {**DEFAULT_CONFIG["gates"], "low": "consistency"},
        },
    }
    if scenario not in configs:
        return None
    codex = root / ".codex"
    codex.mkdir()
    write_json(codex / "config.json", configs[scenario])
    return int(bool(validate_config(root)))
