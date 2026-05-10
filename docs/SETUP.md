# Developer Setup Guide

This guide walks a new contributor from a fresh clone to a running local copy of the MoMo SMS Analytics project.

## 1. Prerequisites

| Tool   | Min version | Check               |
|--------|-------------|---------------------|
| Git    | 2.30+       | `git --version`     |
| Python | 3.10+       | `python3 --version` |
| pip    | 22+         | `pip --version`     |
| Bash   | 4+          | `bash --version`    |

## 2. Clone the repository

    git clone https://github.com/SanoRod00/MOMO-sms-analytics.git
    cd MOMO-sms-analytics

## 3. Create and activate a virtual environment

macOS / Linux:

    python3 -m venv venv
    source venv/bin/activate

Windows (PowerShell):

    python -m venv venv
    venv\Scripts\Activate.ps1

Your prompt should now start with `(venv)`.

## 4. Install dependencies

    pip install --upgrade pip
    pip install -r requirements.txt

## 5. Configure environment variables

    cp .env.example .env

The default `DATABASE_URL` points to `data/db.sqlite3`, which is fine for development.

## 6. Place the raw data

The XML file is not committed. Put your copy at:

    data/raw/momo.xml

If the folder is missing:

    mkdir -p data/raw

## 7. Make scripts executable

    chmod +x scripts/*.sh

## 8. Verify setup

    bash scripts/run_etl.sh
    bash scripts/export_json.sh
    bash scripts/serve_frontend.sh

Then open http://localhost:8000 — you should see the dashboard shell.

## 9. Run tests

    pytest

## 10. Daily workflow

1. `git pull origin main`
2. `git checkout -b feat/<short-description>`
3. Activate venv: `source venv/bin/activate`
4. Code → test → commit (conventional commits)
5. Push and open a PR; link the Scrum card; request a reviewer

See `docs/AGILE.md` and `CONTRIBUTING.md` for full conventions.

---

## Common issues

### command not found: python3
On Windows use `python`. If neither works, reinstall Python and tick "Add Python to PATH".

### Permission denied running a script

    chmod +x scripts/*.sh

### ModuleNotFoundError after install
Your venv isn't active. Confirm the prompt shows `(venv)`, then reinstall.

### Port 8000 already in use
Kill the process or edit the script to use another port:

    lsof -ti:8000 | xargs kill -9

### sqlite3.OperationalError: unable to open database file
Recreate the data folders:

    mkdir -p data/raw data/processed data/logs/dead_letter

### Line-ending errors on Windows

    git config --global core.autocrlf input

Then re-clone.

### pip install slow or failing

    pip install --upgrade pip
    pip install -r requirements.txt --index-url https://pypi.org/simple

---

## Need help?
Ping the team in the group chat or open a GitHub Discussion. If something here is wrong or unclear, fix it and open a PR.
