#!/usr/bin/env python3
from __future__ import annotations

import sys

from control_config import validate_config


def main() -> int:
    errors = validate_config()
    for error in errors:
        print(error, file=sys.stderr)
    if errors:
        return 1
    print("valid workflow configuration")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
