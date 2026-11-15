#!/usr/bin/env bash
# ==============================================================================
# DervGen Workspace: Model Initialization Wrapper Script for Google Colab
# Fetches curated models directly into Google Drive (/dervgen/model/{usage}/...)
# ==============================================================================

set -euo pipefail

PRESET="${1:-P0}" # P0 | P1 | all
USAGE="${2:-}"    # optional: foundation | 3d_recon | texture_gen | denoise_upscale

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WORKSPACE_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

EXTRA_ARGS=""
if [ -n "${USAGE}" ]; then
  EXTRA_ARGS="--usage=${USAGE}"
fi

echo "=========================================================="
echo " [DervGen Model Init] Running Cloud Pre-fetcher"
echo " Preset: ${PRESET}"
echo " Usage Filter: ${USAGE:-all}"
echo "=========================================================="

python3 "${WORKSPACE_ROOT}/colab/init_models.py" --preset="${PRESET}" ${EXTRA_ARGS}
