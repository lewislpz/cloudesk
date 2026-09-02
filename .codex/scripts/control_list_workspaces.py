#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path

from control_config import find_repository_root, load_config
from control_io import read_frontmatter


def main() -> int:
    repository = find_repository_root(Path("."))
    config = load_config(repository)
    found = False
    for configured_root in config.get("workspace_roots", []):
        root = repository / configured_root
        for status_path in sorted(root.glob("*/status.md")):
            status, _ = read_frontmatter(status_path)
            workspace = status_path.parent.relative_to(repository)
            print(
                f"{status.get('status', ''):<20} "
                f"{status.get('workflow', ''):<12} "
                f"{status.get('risk', ''):<8} {workspace}"
            )
            found = True
    if not found:
        print("no structured workspaces found")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
