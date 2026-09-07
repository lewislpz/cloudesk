"""Prove a synthetic token is blocked without committing a token-shaped fixture."""
import subprocess

result = subprocess.run(
    ["go", "run", "github.com/zricethezav/gitleaks/v8@v8.30.1", "stdin", "--redact", "--no-banner"],
    input="github_token = " + "ghp_" + "aB2cD4eF6" * 4 + "\n",
    text=True, capture_output=True,
)
if result.returncode != 1 or "leaks found: 1" not in result.stderr:
    raise SystemExit("Secret scanner did not reject the synthetic token as expected")
print("Synthetic secret rejection: PASS")
