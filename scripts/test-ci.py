"""Exercise CI policy failures in disposable repositories, never the working tree."""
import os
from pathlib import Path
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]


class Policies(unittest.TestCase):
    def run_check(self, script, directory, expected, env=None):
        result = subprocess.run(
            ["python3", str(ROOT / "scripts" / script)], cwd=directory,
            env=env, capture_output=True, text=True,
        )
        self.assertEqual(result.returncode == 0, expected, result.stdout + result.stderr)

    def test_documentation_rejects_missing_links_and_bad_fences(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "README.md").write_text("# ClouDesk\n")
            self.run_check("check-docs.py", root, True)
            for bad in ["[missing](absent.md)", "```python\n", "# CloudDesk"]:
                (root / "README.md").write_text(bad)
                self.run_check("check-docs.py", root, False)

    def test_existing_migration_is_immutable_but_new_migration_is_allowed(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            def git(*args):
                return subprocess.check_output(["git", *args], cwd=root, stderr=subprocess.DEVNULL, text=True).strip()
            git("init")
            migrations = root / "backend/migrations"
            migrations.mkdir(parents=True)
            original = migrations / "000001.up.sql"
            original.write_text("SELECT 1;\n")
            git("add", ".")
            git("-c", "user.name=CI Fixture", "-c", "user.email=ci@example.invalid", "commit", "-m", "fixture")
            env = {**os.environ, "OPENAPI_BASE_REF": git("rev-parse", "HEAD")}
            self.run_check("check-migration-history.py", root, True, env)
            (migrations / "000002.up.sql").write_text("SELECT 2;\n")
            self.run_check("check-migration-history.py", root, True, env)
            original.write_text("SELECT 3;\n")
            self.run_check("check-migration-history.py", root, False, env)
            original.unlink()
            self.run_check("check-migration-history.py", root, False, env)
            self.run_check("check-migration-history.py", root, False, {**env, "OPENAPI_BASE_REF": "missing"})


if __name__ == "__main__":
    unittest.main()
