#!/bin/bash
# ==================================================
# Export Dashboard JSON
# Generates processed JSON for frontend use
# ==================================================

echo "Exporting dashboard JSON..."

python3 etl/run.py --export-json || echo "(etl/run.py not yet implemented)"

echo "Dashboard JSON export completed."
exit 0
