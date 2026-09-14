#!/usr/bin/env python3
"""Local model access check for IT7075 MP1 §3.5.

Loads the API key from a .env file at the repository root, makes one small
request, and prints the response. The key itself is never printed, so this
output is safe to screenshot.

Run (with the venv active):
    python module02/model_check.py

Companion to the Colab notebook, which does the same thing with the key read
from Colab Secrets instead. Between them they satisfy §3.5's requirement for a
model response from BOTH environments.

Design notes — the three failure modes this avoids, all of which the Module 2
lecture slides flag in the course's own verify_env.py:
  * A freshly copied placeholder (`sk-...`) is non-empty, so a plain `if not key`
    guard passes it through and the failure surfaces later as a raw traceback.
    This validates shape.
  * The API call is wrapped, so a 429 quota error or a blocked network produces a
    diagnosis rather than a stack trace.
  * The provider is chosen explicitly, so holding only one vendor's key is not
    misreported as a broken setup.
"""

import os
import sys
from pathlib import Path

MODEL = "gpt-4o-mini"
PROMPT = "Reply with one short sentence confirming API access works."
PLACEHOLDERS = {"", "sk-...", "sk-ant-...", "your-key-here"}


def load_key() -> str:
    try:
        from dotenv import find_dotenv, load_dotenv
    except ImportError:
        sys.exit("python-dotenv is not installed. Run: pip install -r requirements.txt")

    path = find_dotenv(usecwd=True)
    if not path:
        sys.exit(
            "No .env found.\n"
            "Copy the template and add your key:\n"
            "    Copy-Item .env.example .env\n"
            "Then edit .env. It is excluded by .gitignore and must never be committed."
        )

    load_dotenv(path)
    print(f"Loaded credentials from: {Path(path).name} (in {Path(path).parent})")

    key = os.getenv("OPENAI_API_KEY", "")
    if key in PLACEHOLDERS or key.endswith("..."):
        sys.exit("OPENAI_API_KEY is still the placeholder value. Edit .env and put the real key in.")
    if not key:
        sys.exit("OPENAI_API_KEY is not set in .env.")

    print(f"Credential loaded: {len(key)} chars (value not shown)")
    return key


def main() -> int:
    print("=" * 60)
    print("IT7075 MP1 §3.5 — Local model access via .env")
    print("=" * 60)

    key = load_key()

    try:
        from openai import OpenAI
    except ImportError:
        sys.exit("openai is not installed. Run: pip install -r requirements.txt")

    client = OpenAI(api_key=key)

    print(f"\nCalling {MODEL}...")
    try:
        resp = client.chat.completions.create(
            model=MODEL,
            messages=[{"role": "user", "content": PROMPT}],
            timeout=30,
        )
    except Exception as exc:
        print(f"\n[FAIL] {type(exc).__name__}: {exc}")
        print("\nCommon causes:")
        print("  * No billing credit on the account, or a spend limit already reached")
        print("  * The key was revoked or belongs to a different project")
        print("  * Outbound HTTPS blocked on this network")
        print("Check platform.openai.com -> Usage.")
        return 1

    print("\n" + "-" * 60)
    print("Model response (local, key loaded from .env):")
    print(resp.choices[0].message.content)
    print("-" * 60)
    print("\n[ OK ] Local programmatic model access confirmed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
