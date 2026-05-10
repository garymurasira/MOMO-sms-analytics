#!/bin/bash
# ==================================================
# Run ETL Pipeline
# Processes MoMo XML transaction data
# ==================================================

echo "Starting ETL pipeline..."

python3 etl/run.py --xml data/raw/momo.xml || echo "(etl/run.py not yet implemented)"

echo "ETL pipeline completed."
exit 0
