#!/usr/bin/env bash
# ==============================================================================
# DervGen Workspace: Cache & Checkpoint Cleaner
# ==============================================================================

set -uo pipefail

TARGET_ROOT="${1:-.}"

echo "Cleaning Jupyter Notebook checkpoints and Python cache in: ${TARGET_ROOT}"

# Remove Jupyter checkpoints
find "${TARGET_ROOT}" -type d -name ".ipynb_checkpoints" -prune -exec rm -rf {} + 2>/dev/null || true

# Remove __pycache__ directories
find "${TARGET_ROOT}" -type d -name "__pycache__" -prune -exec rm -rf {} + 2>/dev/null || true

# Remove pytest cache
find "${TARGET_ROOT}" -type d -name ".pytest_cache" -prune -exec rm -rf {} + 2>/dev/null || true

# Remove *.pyc, *.pyo
find "${TARGET_ROOT}" -type f \( -name "*.pyc" -o -name "*.pyo" \) -delete 2>/dev/null || true

echo "Cache cleanup completed successfully!"
