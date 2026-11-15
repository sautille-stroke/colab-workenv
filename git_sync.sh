#!/usr/bin/env bash
# ==============================================================================
# DervGen Workspace: Quick Git Sync Tool for Google Colab
# Commits and pushes workspace changes back to GitHub repository
# ==============================================================================

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WORKSPACE_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

COMMIT_MSG="${1:-wip: colab session checkpoint $(date '+%Y-%m-%d %H:%M:%S') [gemini3.8]}"
BRANCH="${2:-main}"

echo "=========================================================="
echo " [Git Sync] Syncing workspace to GitHub..."
echo " Root: ${WORKSPACE_ROOT}"
echo " Branch: ${BRANCH}"
echo " Message: ${COMMIT_MSG}"
echo "=========================================================="

cd "${WORKSPACE_ROOT}"

# Clean ephemeral cache files first
if [ -f "${WORKSPACE_ROOT}/scripts/clean_cache.sh" ]; then
  bash "${WORKSPACE_ROOT}/scripts/clean_cache.sh" "${WORKSPACE_ROOT}"
fi

# Ensure git credentials if GITHUB_TOKEN is present
if [ -n "${GITHUB_TOKEN:-}" ]; then
  git remote set-url origin "https://${GITHUB_TOKEN}@github.com/sautille-stroke/workspace.git"
fi

# Stage changes
git add -A

# Check if there are changes to commit
if git diff-index --quiet HEAD --; then
  echo "--> No changes detected. Working tree clean."
else
  git commit -m "${COMMIT_MSG}"
  echo "--> Committed successfully."
fi

# Push
echo "--> Pushing to origin/${BRANCH}..."
git push origin "${BRANCH}"
echo "=========================================================="
echo " [Git Sync] Successfully synced with GitHub!"
echo "=========================================================="
