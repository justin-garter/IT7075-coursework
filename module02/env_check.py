#!/usr/bin/env python3
"""Environment validation for IT7075 Module 2.

Reports the interpreter, the isolation state, the installed dependencies, the
available compute, and whether credentials are loadable -- WITHOUT printing any
credential value. Safe to screenshot.

Run:
    python module02/env_check.py

Design notes (deliberate differences from the course verify_env.py):
  * Validates key SHAPE, not just presence, so a freshly copied placeholder is
    reported as a placeholder instead of producing a traceback later.
  * Every optional import is guarded, so a missing package degrades to a clear
    line of output rather than stopping the run.
  * No network call and no secret value ever reaches stdout.
"""

import os
import platform
import shutil
import sys
from pathlib import Path

OK, WARN, BAD = "[ OK ]", "[WARN]", "[FAIL]"


def section(title):
    print(f"\n{title}")
    print("-" * len(title))


def check_interpreter():
    section("1. Interpreter and isolation")
    print(f"{OK} Python {platform.python_version()} ({platform.architecture()[0]})")
    print(f"     executable: {sys.executable}")

    in_venv = sys.prefix != sys.base_prefix
    if in_venv:
        print(f"{OK} Running inside a virtual environment")
        print(f"     venv root:  {sys.prefix}")
    else:
        print(f"{BAD} NOT in a virtual environment -- this is the system interpreter")
        print(f"     base:       {sys.base_prefix}")
    return in_venv


def check_compute():
    section("2. Compute inventory")
    print(f"{OK} Platform:  {platform.system()} {platform.release()}")
    print(f"{OK} Processor: {platform.processor() or 'unknown'}")
    print(f"{OK} Logical cores: {os.cpu_count()}")

    try:
        import psutil
        gib = psutil.virtual_memory().total / (1024 ** 3)
        print(f"{OK} Total RAM: {gib:.1f} GiB")
    except ImportError:
        print(f"{WARN} Total RAM: psutil not installed (pip install psutil)")

    try:
        import torch
    except ImportError:
        print(f"{WARN} torch not installed -- GPU framework query skipped")
        return

    print(f"{OK} torch {torch.__version__}")
    if torch.cuda.is_available():
        print(f"{OK} torch.cuda.is_available() -> True")
        for i in range(torch.cuda.device_count()):
            print(f"     device {i}: {torch.cuda.get_device_name(i)}")
        print(f"     CUDA build: {torch.version.cuda}")
    else:
        print(f"{WARN} torch.cuda.is_available() -> False (CPU-only path)")

    if shutil.which("nvidia-smi"):
        print(f"{OK} nvidia-smi present on PATH -- run it separately for driver detail")
    else:
        print(f"{WARN} nvidia-smi not on PATH")


def check_packages():
    section("3. Required packages")
    for name, label in [
        ("dotenv", "python-dotenv"),
        ("openai", "openai"),
        ("anthropic", "anthropic"),
        ("jupyter_core", "jupyter"),
    ]:
        try:
            __import__(name)
            print(f"{OK} {label}")
        except ImportError:
            print(f"{WARN} {label} not installed")


def check_credentials():
    """Report credential loadability. Never prints a key value."""
    section("4. Credentials (values never printed)")

    try:
        from dotenv import find_dotenv, load_dotenv
    except ImportError:
        print(f"{WARN} python-dotenv not installed -- cannot load .env")
        return

    path = find_dotenv(usecwd=True)
    if path:
        load_dotenv(path)
        print(f"{OK} .env found: {Path(path).name} (in {Path(path).parent})")
    else:
        print(f"{WARN} No .env found -- checking process environment only")

    placeholders = {"", "sk-...", "sk-ant-...", "your-key-here"}
    for var in ("OPENAI_API_KEY", "ANTHROPIC_API_KEY"):
        value = os.getenv(var, "")
        if not value:
            print(f"{WARN} {var}: not set")
        elif value in placeholders or value.endswith("..."):
            print(f"{BAD} {var}: still the placeholder -- edit .env")
        else:
            print(f"{OK} {var}: loaded, {len(value)} chars (value not shown)")


def main():
    print("=" * 60)
    print("IT7075 Module 2 -- Environment Validation")
    print("=" * 60)

    in_venv = check_interpreter()
    check_compute()
    check_packages()
    check_credentials()

    print("\n" + "=" * 60)
    if in_venv:
        print("Interpreter isolation: PASS")
    else:
        print("Interpreter isolation: FAIL -- activate the venv, then re-run")
    print("=" * 60)
    return 0 if in_venv else 1


if __name__ == "__main__":
    sys.exit(main())
