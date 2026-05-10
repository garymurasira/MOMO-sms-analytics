#!/usr/bin/env bash
# scaffold.sh — Set up the MoMo SMS project folder structure.
# Usage: bash scaffold.sh

set -e
echo "A Scaffolding MoMo SMS project structure"

# ── Directories ────────────────────────────────────────────────
mkdir -p web/assets
mkdir -p data/raw
mkdir -p data/processed
mkdir -p data/logs/dead_letter
mkdir -p etl api scripts tests

# ── Top-level files ────────────────────────────────────────────
touch README.md .env.example requirements.txt index.html .gitignore

# ── web/ ───────────────────────────────────────────────────────
touch web/styles.css web/chart_handler.js

# ── etl/ Python package ────────────────────────────────────────
touch etl/__init__.py
touch etl/config.py
touch etl/parse_xml.py
touch etl/clean_normalize.py
touch etl/categorize.py
touch etl/load_db.py
touch etl/run.py

# ── api/ Python package (optional) ─────────────────────────────
touch api/__init__.py api/app.py api/db.py api/schemas.py

# ── scripts/ ───────────────────────────────────────────────────
touch scripts/run_etl.sh scripts/export_json.sh scripts/serve_frontend.sh
chmod +x scripts/*.sh

# ── tests/ ─────────────────────────────────────────────────────
touch tests/__init__.py
touch tests/test_parse_xml.py
touch tests/test_clean_normalize.py
touch tests/test_categorize.py

# ── .gitkeep files for empty tracked dirs ──────────────────────
touch data/raw/.gitkeep
touch data/processed/.gitkeep
touch data/logs/.gitkeep
touch data/logs/dead_letter/.gitkeep
touch web/assets/.gitkeep

# ── .gitignore ─────────────────────────────────────────────────
cat > .gitignore <<'EOF'
# Python
__pycache__/
*.py[cod]
.venv/
venv/
*.egg-info/

# Environment
.env

# Data (raw XML is git-ignored per spec)
data/raw/*
!data/raw/.gitkeep
data/db.sqlite3
data/logs/*.log
data/logs/dead_letter/*
!data/logs/dead_letter/.gitkeep

# IDE / OS
.vscode/
.idea/
.DS_Store
EOF

# ── .env.example ───────────────────────────────────────────────
cat > .env.example <<'EOF'
# Database
DATABASE_URL=sqlite:///data/db.sqlite3

# ETL
XML_INPUT_PATH=data/raw/momo.xml
LOG_LEVEL=INFO
EOF

# ── requirements.txt ───────────────────────────────────────────
cat > requirements.txt <<'EOF'
# ETL
lxml>=5.0.0
python-dateutil>=2.8.2

# Optional API
fastapi>=0.110.0
uvicorn>=0.27.0
pydantic>=2.0.0

# Tests
pytest>=8.0.0
EOF

echo "✅ Scaffold complete. Run 'tree -L 2 -a' or 'ls -R' to verify."
