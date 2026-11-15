#!/usr/bin/env bash
# ==============================================================================
# DervGen Workspace: Selective / Batch Repository Cloner for Cloud & Colab
# ==============================================================================

set -euo pipefail

TARGET_DIR="${1:-/content/dervgen}"
REPOS_INPUT="${2:-aether,fulgur}"
SHALLOW="${3:-true}"

mkdir -p "${TARGET_DIR}"

GITHUB_TOKEN="${GITHUB_TOKEN:-}"
if [ -n "${GITHUB_TOKEN}" ]; then
  BASE_URL="https://${GITHUB_TOKEN}@github.com/dervgen"
else
  BASE_URL="https://github.com/dervgen"
fi

IFS=',' read -ra REPO_LIST <<< "${REPOS_INPUT}"

echo "=========================================================="
echo " [DervGen Cloner] Target directory: ${TARGET_DIR}"
echo " [DervGen Cloner] Repositories to clone: ${REPOS_INPUT}"
echo " [DervGen Cloner] Shallow clone: ${SHALLOW}"
echo "=========================================================="

for repo in "${REPO_LIST[@]}"; do
  # Trim whitespace
  repo="$(echo "${repo}" | xargs)"
  [ -z "${repo}" ] && continue

  DEST="${TARGET_DIR}/${repo}"
  if [ "${repo}" = "synapse" ]; then
    if [ -n "${GITHUB_TOKEN}" ]; then
      REPO_URL="https://${GITHUB_TOKEN}@github.com/sautille-stroke/synapse.git"
    else
      REPO_URL="https://github.com/sautille-stroke/synapse.git"
    fi
  else
    REPO_URL="${BASE_URL}/${repo}.git"
  fi

  if [ -d "${DEST}/.git" ]; then
    echo "--> [UPDATE] ${repo} already exists, fetching latest changes..."
    git -C "${DEST}" pull --rebase || echo "Warning: git pull failed for ${repo}"
  else
    echo "--> [CLONE] Cloning ${repo} into ${DEST}..."
    if [ "${SHALLOW}" = "true" ]; then
      git clone --depth 1 "${REPO_URL}" "${DEST}"
    else
      git clone "${REPO_URL}" "${DEST}"
    fi
  fi
done

echo "=========================================================="
echo " [DervGen Cloner] All requested repositories are ready!"
echo "=========================================================="
