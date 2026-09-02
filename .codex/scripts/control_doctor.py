#!/usr/bin/env python3
from __future__ import annotations

import shutil
import sys


def main() -> int:
    required = ("bash", "python3", "rg")
    missing = [tool for tool in required if shutil.which(tool) is None]
    if sys.version_info < (3, 9):
        print("Python 3.9 or newer is required", file=sys.stderr)
        return 1
    if missing:
        print(f"missing required tools: {', '.join(missing)}", file=sys.stderr)
        return 1
    print("agentic workflow prerequisites are available")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
