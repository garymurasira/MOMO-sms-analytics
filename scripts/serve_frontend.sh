#!/bin/bash
# ==================================================
# Serve Frontend Locally
# Starts local development server
# ==================================================

echo "Serving frontend at http://localhost:8000"
echo "Press Ctrl+C to stop."

python3 -m http.server 8000

exit 0
