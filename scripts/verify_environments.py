#!/usr/bin/env python
"""
Provera da ista codebase radi sa lokalnim SQLite i produkcijskim postavkama.
Pokreni: python scripts/verify_environments.py
"""
import os
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def run_check(settings_module: str, deploy: bool = False) -> int:
    env = os.environ.copy()
    env["DJANGO_SETTINGS_MODULE"] = settings_module
    if settings_module.endswith("production"):
        env.setdefault("DATABASE_URL", "postgres://user:pass@localhost:5432/testdb")
        env.setdefault("SECRET_KEY", "verify-only-not-for-production")
        env.setdefault("ALLOWED_HOSTS", "localhost")
        env.setdefault("REQUIRE_R2_CONFIG", "False")
        env.setdefault("USE_R2_STORAGE", "False")

    cmd = [sys.executable, "manage.py", "check"]
    if deploy:
        cmd.append("--deploy")
    result = subprocess.run(cmd, cwd=ROOT, env=env)
    return result.returncode


def main() -> int:
    print("Checking config.settings.local (SQLite)...")
    local_rc = run_check("config.settings.local")

    print("Checking config.settings.production (PostgreSQL config)...")
    prod_rc = run_check("config.settings.production", deploy=True)

    if local_rc == 0 and prod_rc == 0:
        print("OK — oba okruženja prolaze Django check.")
        return 0
    print("FAILED — pogledajte izlaz iznad.")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
