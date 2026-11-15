#!/usr/bin/env bash
# ==============================================================================
# DervGen Workspace: C++ Build & Headless Execution Runner for Google Colab
# Builds targets with Bazel using Google Drive disk cache, and runs them headless.
# ==============================================================================

set -euo pipefail

BOLD="\033[1m"
GREEN="\033[32m"
YELLOW="\033[33m"
CYAN="\033[36m"
RED="\033[31m"
RESET="\033[0m"

REPO_PATH="${1:-/content/dervgen/fulgur}"
ACTION="${2:-build}" # build | test | run
TARGET="${3:-//engine/...}"
EXTRA_ARGS="${4:-}"

# Check repo
if [ ! -d "${REPO_PATH}" ]; then
  echo -e "${RED}Error: Repository path does not exist: ${REPO_PATH}${RESET}"
  echo "Use 'bash /content/workspace/repos/clone_repos.sh /content/dervgen' to clone first."
  exit 1
fi

cd "${REPO_PATH}"

# Configure Persistent Disk Cache in Google Drive if available
BAZEL_CACHE_ARG=""
DRIVE_CACHE="/content/drive/MyDrive/dervgen/cache/bazel"
if [ -d "/content/drive/MyDrive" ]; then
  mkdir -p "${DRIVE_CACHE}"
  BAZEL_CACHE_ARG="--disk_cache=${DRIVE_CACHE}"
  echo -e "${GREEN}--> Using Google Drive Bazel disk cache: ${DRIVE_CACHE}${RESET}"
fi

# Ensure Xvfb (Virtual Framebuffer) is available for GPU windows if needed
if ! command -v xvfb-run &>/dev/null; then
  echo "Installing xvfb for headless window & Vulkan swapchain support..."
  apt-get update -qq && apt-get install -y -qq xvfb libvulkan1 vulkan-tools > /dev/null
fi

echo -e "\n${BOLD}${CYAN}================================================================${RESET}"
echo -e "${BOLD}${CYAN}  DervGen C++ Runner: ${ACTION^^} on ${TARGET}                   ${RESET}"
echo -e "${BOLD}${CYAN}================================================================${RESET}"

COMMON_BAZEL_FLAGS="--config=linux ${BAZEL_CACHE_ARG}"

case "${ACTION}" in
  build)
    echo -e "Executing: bazel build ${COMMON_BAZEL_FLAGS} ${TARGET} ${EXTRA_ARGS}"
    # shellcheck disable=SC2086
    bazel build ${COMMON_BAZEL_FLAGS} ${TARGET} ${EXTRA_ARGS}
    ;;

  test)
    echo -e "Executing: bazel test ${COMMON_BAZEL_FLAGS} ${TARGET} --test_output=errors ${EXTRA_ARGS}"
    # shellcheck disable=SC2086
    bazel test ${COMMON_BAZEL_FLAGS} ${TARGET} --test_output=errors ${EXTRA_ARGS}
    ;;

  run)
    echo -e "Executing under xvfb-run: bazel run ${COMMON_BAZEL_FLAGS} ${TARGET} -- ${EXTRA_ARGS}"
    # shellcheck disable=SC2086
    xvfb-run -a -s "-screen 0 1920x1080x24" bazel run ${COMMON_BAZEL_FLAGS} ${TARGET} -- ${EXTRA_ARGS}
    ;;

  *)
    echo -e "${RED}Unknown action: ${ACTION}. Available actions: build | test | run${RESET}"
    exit 1
    ;;
esac

echo -e "\n${BOLD}${GREEN}✓ Operation '${ACTION}' completed successfully!${RESET}"
