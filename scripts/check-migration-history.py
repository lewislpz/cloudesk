"""Reject changes or removal of migrations already present in the CI baseline."""
import os
import subprocess

base = os.environ.get("OPENAPI_BASE_REF", "origin/main")
subprocess.run(["git", "rev-parse", "--verify", base + "^{commit}"], check=True, stdout=subprocess.DEVNULL)
paths = subprocess.check_output(["git", "ls-tree", "-r", "--name-only", base, "backend/migrations/"], text=True).splitlines()
for path in paths:
    subprocess.run(["git", "diff", "--exit-code", base, "--", path], check=True)
print("Shared migration history: PASS")
