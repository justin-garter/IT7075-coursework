# IT7075 — Applied AI for Cybersecurity

Coursework repository for IT7075C, University of Cincinnati, School of Information Technology.

## Layout

| Path | Contents |
|---|---|
| `module02/` | Tools & environment setup and validation |

## Environment

Python 3.13 in a local virtual environment. Rebuild it with:

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

## Secrets

API keys live in a `.env` file at the repository root, loaded at runtime with `python-dotenv`.
`.env` is excluded by `.gitignore` and is never committed. `.env.example` documents which
variables are expected, with no values. Keys are never printed, logged, or embedded in code.

## Course repository

The instructor's repository is cloned separately as read-only reference and is never pushed to.
