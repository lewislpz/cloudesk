#!/usr/bin/env python3
from __future__ import annotations

import os
import time
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator

from control_io import ControlError

_HELD_LOCKS: set[Path] = set()


def clear_stale_lock(lock_path: Path) -> None:
    try:
        process_id = int(lock_path.read_text(encoding="utf-8").strip())
        os.kill(process_id, 0)
    except ProcessLookupError:
        lock_path.unlink(missing_ok=True)
    except (OSError, ValueError):
        return


@contextmanager
def workspace_lock(workspace: Path, timeout_seconds: float = 10) -> Iterator[None]:
    lock_path = (workspace / "control" / ".lock").resolve()
    if lock_path in _HELD_LOCKS:
        yield
        return
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    deadline = time.monotonic() + timeout_seconds
    while True:
        try:
            descriptor = os.open(lock_path, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
            os.write(descriptor, f"{os.getpid()}\n".encode())
            os.close(descriptor)
            break
        except FileExistsError as error:
            clear_stale_lock(lock_path)
            if time.monotonic() >= deadline:
                raise ControlError(f"workspace is locked: {workspace}") from error
            time.sleep(0.05)
    _HELD_LOCKS.add(lock_path)
    try:
        yield
    finally:
        _HELD_LOCKS.remove(lock_path)
        lock_path.unlink(missing_ok=True)
