#!/usr/bin/env python3
from __future__ import annotations

import os
import shutil
import subprocess
import tempfile
from pathlib import Path


def main() -> int:
    source = Path(__file__).resolve().parents[1]
    environment = {
        **os.environ,
        "CODEX_SKIP_PORTABILITY_CHECK": "1",
        "PYTHONPYCACHEPREFIX": str(Path(tempfile.gettempdir()) / "codex-portability-pycache"),
    }
    with tempfile.TemporaryDirectory(prefix="codex-portability-") as temporary:
        repository = Path(temporary)
        shutil.copytree(
            source,
            repository / ".codex",
            ignore=shutil.ignore_patterns("__pycache__", "*.pyc", "results"),
        )
        repository.joinpath("AGENTS.md").write_text(
            "# Existing Instructions\n\nPreserve this.\n", encoding="utf-8"
        )
        repository.joinpath(".gitignore").write_text("existing-output/\n", encoding="utf-8")
        for _ in range(2):
            subprocess.run(
                ["bash", ".codex/scripts/bootstrap.sh"],
                cwd=repository,
                env=environment,
                check=True,
                capture_output=True,
                text=True,
            )
        verification = subprocess.run(
            ["bash", ".codex/scripts/verify-control-plane.sh"],
            cwd=repository,
            env=environment,
            check=False,
            capture_output=True,
            text=True,
        )
        if verification.returncode != 0:
            print(verification.stdout)
            print(verification.stderr)
            return verification.returncode
        agents = repository.joinpath("AGENTS.md").read_text(encoding="utf-8")
        gitignore = repository.joinpath(".gitignore").read_text(encoding="utf-8")
        valid = (
            "Preserve this." in agents
            and agents.count("<!-- codex-workflow:start -->") == 1
            and "existing-output/" in gitignore
            and gitignore.count(".codex/evals/results/*.json") == 1
            and repository.joinpath(".orchestrator/plans").is_dir()
            and repository.joinpath(".orchestrator/audits").is_dir()
        )
        if not valid:
            return 1
    print("copy-paste bootstrap is portable and idempotent")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
