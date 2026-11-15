#!/usr/bin/env bash
# ==============================================================================
# DervGen Workspace: Google Colab Runtime Environment Setup Script
# ==============================================================================
# Standardizes the cloud developer environment across all sautille-stroke /
# dervgen projects (aether, fulgur, caelum-core, narrative-rail, etc.).
#
# Core Foundation Toolchains Configured:
#   1. Bazelisk (Bazel 9.3.1 / Bzlmod) at /usr/local/bin/bazel
#   2. LLVM / Clang 18 (C++20 concepts, lld, libc++, libomp) via apt.llvm.org
#   3. Go 1.23+ (Official modern Go toolchain) at /usr/local/go
#   4. Blender 4.3.2 LTS (Cycles headless reference engine) at /usr/local/bin/blender
#   5. Python scientific & rendering toolchains (pip, numpy, Pillow, PyYAML, etc.)
#   6. Shell environment variables & hooks (GOROOT, GOPATH, CC=clang, CXX=clang++)
#
# Usage:
#   !bash setup_env.sh
#   !bash setup_env.sh --skip-blender
# ==============================================================================

set -euo pipefail

BOLD="\033[1m"
GREEN="\033[32m"
YELLOW="\033[33m"
CYAN="\033[36m"
RED="\033[31m"
RESET="\033[0m"

echo -e "${BOLD}${CYAN}================================================================${RESET}"
echo -e "${BOLD}${CYAN}      Initializing DervGen Google Colab Developer Runtime       ${RESET}"
echo -e "${BOLD}${CYAN}  Toolchains: Bazelisk | LLVM 18 | Go 1.23+ | Blender 4.3 LTS  ${RESET}"
echo -e "${BOLD}${CYAN}================================================================${RESET}"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WORKSPACE_ROOT="${WORKSPACE_ROOT:-${SCRIPT_DIR}}"

# Arguments
INSTALL_BLENDER=1
INSTALL_LLVM=1
INSTALL_GO=1
INSTALL_BAZEL=1
LLVM_VERSION="${LLVM_VERSION:-18}"
GO_VERSION="${GO_VERSION:-1.23.6}"
BLENDER_VERSION="${BLENDER_VERSION:-4.3.2}"

for arg in "$@"; do
  case "$arg" in
    --skip-blender) INSTALL_BLENDER=0 ;;
    --skip-llvm)    INSTALL_LLVM=0 ;;
    --skip-go)      INSTALL_GO=0 ;;
    --skip-bazel)   INSTALL_BAZEL=0 ;;
    --with-blender) INSTALL_BLENDER=1 ;;
  esac
done

export DEBIAN_FRONTEND=noninteractive

# ──────────────────────────────────────────────────────────────
# Step 1/8: System packages & prerequisites
# ──────────────────────────────────────────────────────────────
echo -e "\n${BOLD}${YELLOW}[Step 1/8] Updating and installing system prerequisites...${RESET}"
apt-get update -qq
apt-get install -y -qq \
  build-essential \
  ca-certificates \
  curl \
  wget \
  git \
  git-lfs \
  tmux \
  htop \
  jq \
  tar \
  unzip \
  xz-utils \
  ninja-build \
  ccache \
  pkg-config \
  software-properties-common \
  gnupg \
  lsb-release > /dev/null

git lfs install --skip-repo 2>/dev/null || true

# ──────────────────────────────────────────────────────────────
# Step 2/8: Bazelisk (Bazel 9.3.1 / Bzlmod)
# ──────────────────────────────────────────────────────────────
echo -e "\n${BOLD}${YELLOW}[Step 2/8] Setting up Bazel (Bazelisk)...${RESET}"
if [ "${INSTALL_BAZEL}" -eq 1 ]; then
  BAZELISK_VERSION="v1.25.0"
  if [ ! -f /usr/local/bin/bazel ]; then
    echo -e "${CYAN}--> Fetching Bazelisk ${BAZELISK_VERSION}...${RESET}"
    wget -q "https://github.com/bazelbuild/bazelisk/releases/download/${BAZELISK_VERSION}/bazelisk-linux-amd64" -O /usr/local/bin/bazel
    chmod +x /usr/local/bin/bazel
  fi
  echo -e "${GREEN}--> Bazel ready: $(bazel --version 2>/dev/null || echo 'Bazelisk at /usr/local/bin/bazel')${RESET}"
fi

# ──────────────────────────────────────────────────────────────
# Step 3/8: LLVM / Clang 18 Toolchain (apt.llvm.org)
# ──────────────────────────────────────────────────────────────
echo -e "\n${BOLD}${YELLOW}[Step 3/8] Setting up LLVM / Clang ${LLVM_VERSION} (C++20 Toolchain)...${RESET}"
if [ "${INSTALL_LLVM}" -eq 1 ]; then
  install_llvm() {
    local ver="$1"
    # Check if already installed
    if command -v "clang-${ver}" &>/dev/null; then
      echo -e "${GREEN}--> clang-${ver} already installed.${RESET}"
      return 0
    fi

    # Check if current clang is already >= required version
    if command -v clang &>/dev/null; then
      local curr_major
      curr_major=$(clang --version | head -n 1 | grep -oP 'version \K\d+' || echo "0")
      if [ "${curr_major}" -ge "${ver}" ]; then
        echo -e "${GREEN}--> clang ${curr_major} already satisfies >= ${ver}.${RESET}"
        return 0
      fi
    fi

    echo -e "${CYAN}--> Configuring apt.llvm.org for LLVM ${ver}...${RESET}"
    wget -qO- https://apt.llvm.org/llvm-snapshot.gpg.key | tee /etc/apt/trusted.gpg.d/apt.llvm.org.asc > /dev/null
    local codename
    codename=$(lsb_release -cs 2>/dev/null || echo "jammy")
    echo "deb http://apt.llvm.org/${codename}/ llvm-toolchain-${codename}-${ver} main" \
      > /etc/apt/sources.list.d/llvm-${ver}.list

    apt-get update -qq
    echo -e "${CYAN}--> Installing clang-${ver}, lld-${ver}, libomp-${ver}-dev...${RESET}"
    apt-get install -y -qq \
      clang-${ver} \
      lld-${ver} \
      libomp-${ver}-dev \
      clang-format-${ver} \
      clang-tidy-${ver} || {
        echo -e "${YELLOW}[WARN] Full LLVM ${ver} failed; installing minimal clang/lld...${RESET}"
        apt-get install -y -qq clang-${ver} lld-${ver} || apt-get install -y -qq clang lld
      }

    # Set as default compiler alternatives
    update-alternatives --install /usr/bin/clang   clang   "/usr/bin/clang-${ver}"   100
    update-alternatives --install /usr/bin/clang++ clang++ "/usr/bin/clang++-${ver}" 100
    update-alternatives --install /usr/bin/lld     lld     "/usr/bin/lld-${ver}"     100
    if [ -x "/usr/bin/clang-format-${ver}" ]; then
      update-alternatives --install /usr/bin/clang-format clang-format "/usr/bin/clang-format-${ver}" 100
    fi
    if [ -x "/usr/bin/clang-tidy-${ver}" ]; then
      update-alternatives --install /usr/bin/clang-tidy clang-tidy "/usr/bin/clang-tidy-${ver}" 100
    fi
  }

  install_llvm "${LLVM_VERSION}"
  echo -e "${GREEN}--> Clang: $(clang --version 2>/dev/null | head -n 1)${RESET}"
fi

# ──────────────────────────────────────────────────────────────
# Step 4/8: Go 1.23+ Toolchain (Official Release)
# ──────────────────────────────────────────────────────────────
echo -e "\n${BOLD}${YELLOW}[Step 4/8] Setting up Go 1.23+ Toolchain...${RESET}"
if [ "${INSTALL_GO}" -eq 1 ]; then
  NEED_GO_INSTALL=1
  if command -v go &>/dev/null; then
    CURRENT_GO_VER=$(go version 2>/dev/null | awk '{print $3}' | sed 's/go//' || echo "0.0.0")
    GO_MAJOR=$(echo "${CURRENT_GO_VER}" | cut -d'.' -f1)
    GO_MINOR=$(echo "${CURRENT_GO_VER}" | cut -d'.' -f2)
    if [ "${GO_MAJOR}" -ge 1 ] && [ "${GO_MINOR}" -ge 23 ]; then
      echo -e "${GREEN}--> Go is already up to date: $(go version)${RESET}"
      NEED_GO_INSTALL=0
    else
      echo -e "${YELLOW}--> Existing Go ${CURRENT_GO_VER} is below 1.23; upgrading to ${GO_VERSION}...${RESET}"
    fi
  fi

  if [ "${NEED_GO_INSTALL}" -eq 1 ]; then
    echo -e "${CYAN}--> Fetching Go ${GO_VERSION} official archive...${RESET}"
    GO_ARCHIVE="go${GO_VERSION}.linux-amd64.tar.gz"
    GO_URLS=(
      "https://go.dev/dl/${GO_ARCHIVE}"
      "https://golang.google.cn/dl/${GO_ARCHIVE}"
    )
    TMP_GO="/tmp/${GO_ARCHIVE}"
    DOWNLOADED_GO=0
    for u in "${GO_URLS[@]}"; do
      if curl -fL --connect-timeout 10 --retry 2 -o "${TMP_GO}" "${u}"; then
        DOWNLOADED_GO=1
        break
      fi
    done

    if [ "${DOWNLOADED_GO}" -eq 1 ] && [ -s "${TMP_GO}" ]; then
      rm -rf /usr/local/go
      tar -xzf "${TMP_GO}" -C /usr/local/
      rm -f "${TMP_GO}"
      ln -sf /usr/local/go/bin/go /usr/local/bin/go
      ln -sf /usr/local/go/bin/gofmt /usr/local/bin/gofmt
      echo -e "${GREEN}--> Installed Go: $(/usr/local/bin/go version)${RESET}"
    else
      echo -e "${YELLOW}[WARN] Could not fetch Go archive, attempting apt fallback...${RESET}"
      apt-get install -y -qq golang-go > /dev/null || true
    fi
  fi
fi

# ──────────────────────────────────────────────────────────────
# Step 5/8: Blender 4.3 LTS (Cycles Headless Reference Engine)
# ──────────────────────────────────────────────────────────────
echo -e "\n${BOLD}${YELLOW}[Step 5/8] Setting up Blender 4.3 LTS (Cycles Headless)...${RESET}"
if [ "${INSTALL_BLENDER}" -eq 1 ]; then
  BLENDER_MAJOR_MINOR="${BLENDER_VERSION%.*}"
  INSTALL_DIR="/opt/blender-${BLENDER_VERSION}-linux-x64"
  BLENDER_BIN="/usr/local/bin/blender"

  verify_cycles() {
    local bpath="$1"
    if [ ! -x "${bpath}" ]; then return 1; fi
    local out
    out=$("${bpath}" --background --factory-startup -noaudio --python-exit-code 1 \
      --python-expr "import bpy; bpy.context.scene.render.engine='CYCLES'; print('BLENDER_CYCLES_OK', bpy.app.version_string)" 2>&1 || true)
    if echo "${out}" | grep -q "BLENDER_CYCLES_OK"; then
      return 0
    fi
    return 1
  }

  if verify_cycles "${BLENDER_BIN}"; then
    echo -e "${GREEN}--> Blender Cycles already operational at ${BLENDER_BIN}: $("${BLENDER_BIN}" --version | head -n 1)${RESET}"
  else
    echo -e "${CYAN}--> Installing headless runtime libraries for Blender...${RESET}"
    apt-get install -y -qq \
      libxrender1 \
      libxi6 \
      libxxf86vm1 \
      libxfixes3 \
      libgl1 \
      libxkbcommon0 \
      libsm6 \
      libice6 > /dev/null 2>&1 || true

    ARCHIVE_NAME="blender-${BLENDER_VERSION}-linux-x64.tar.xz"
    MIRROR_URLS=(
      "https://mirrors.tuna.tsinghua.edu.cn/blender/release/Blender${BLENDER_MAJOR_MINOR}/${ARCHIVE_NAME}"
      "https://mirrors.aliyun.com/blender/release/Blender${BLENDER_MAJOR_MINOR}/${ARCHIVE_NAME}"
      "https://download.blender.org/release/Blender${BLENDER_MAJOR_MINOR}/${ARCHIVE_NAME}"
    )

    TMP_ARCHIVE="/tmp/${ARCHIVE_NAME}"
    rm -f "${TMP_ARCHIVE}"
    DOWNLOADED=0
    for url in "${MIRROR_URLS[@]}"; do
      echo -e "${CYAN}--> Downloading Blender from ${url}...${RESET}"
      if curl -fL --connect-timeout 10 --retry 2 -o "${TMP_ARCHIVE}" "${url}"; then
        DOWNLOADED=1
        break
      fi
    done

    if [ "${DOWNLOADED}" -eq 1 ] && [ -s "${TMP_ARCHIVE}" ]; then
      echo -e "${CYAN}--> Extracting Blender to ${INSTALL_DIR}...${RESET}"
      rm -rf "${INSTALL_DIR}"
      mkdir -p /opt
      tar -xJf "${TMP_ARCHIVE}" -C /opt/
      rm -f "${TMP_ARCHIVE}"

      ln -sf "${INSTALL_DIR}/blender" "${BLENDER_BIN}"
      mkdir -p "${HOME}/tools/bin"
      ln -sf "${INSTALL_DIR}/blender" "${HOME}/tools/bin/blender"
      chmod +x "${BLENDER_BIN}"

      if verify_cycles "${BLENDER_BIN}"; then
        echo -e "${GREEN}--> Blender Cycles installed & verified: $("${BLENDER_BIN}" --version | head -n 1)${RESET}"
      else
        echo -e "${YELLOW}[WARN] Blender installed but Cycles headless smoke test failed.${RESET}"
      fi
    else
      echo -e "${RED}[ERROR] Failed to download Blender ${BLENDER_VERSION} from all mirrors.${RESET}"
    fi
  fi
else
  echo -e "${CYAN}--> Blender installation skipped (--skip-blender).${RESET}"
fi

# ──────────────────────────────────────────────────────────────
# Step 5.5: NVIDIA OptiX SDK Headers (Hardware Ray Tracing)
# ──────────────────────────────────────────────────────────────
echo -e "\n${BOLD}${YELLOW}[Step 5.5] Installing NVIDIA OptiX SDK headers...${RESET}"

OPTIX_INSTALL_DIR="/opt/optix-dev"
if [ -f "/usr/local/include/optix.h" ]; then
  OPTIX_VER=$(grep '#define OPTIX_VERSION' /usr/local/include/optix.h 2>/dev/null | awk '{print $3}')
  echo -e "${GREEN}--> OptiX SDK headers already present (version ${OPTIX_VER:-unknown}).${RESET}"
elif [ -f "${OPTIX_INSTALL_DIR}/include/optix.h" ]; then
  echo -e "${CYAN}--> Deploying cached OptiX headers from ${OPTIX_INSTALL_DIR}...${RESET}"
  cp -r "${OPTIX_INSTALL_DIR}/include/"* /usr/local/include/
  OPTIX_VER=$(grep '#define OPTIX_VERSION' /usr/local/include/optix.h 2>/dev/null | awk '{print $3}')
  echo -e "${GREEN}--> OptiX SDK headers deployed (version ${OPTIX_VER:-unknown}).${RESET}"
else
  # Try Google Drive cache first, then GitHub
  DRIVE_OPTIX="${DERVGEN_DRIVE_ROOT:-/content/drive/MyDrive/dervgen}/tools/optix-dev"
  if [ -d "${DRIVE_OPTIX}/include" ]; then
    echo -e "${CYAN}--> Restoring OptiX SDK from Google Drive cache...${RESET}"
    mkdir -p "${OPTIX_INSTALL_DIR}"
    cp -r "${DRIVE_OPTIX}" "${OPTIX_INSTALL_DIR}" 2>/dev/null || true
  else
    echo -e "${CYAN}--> Cloning OptiX SDK headers from github.com/NVIDIA/optix-dev...${RESET}"
    git clone --depth=1 https://github.com/NVIDIA/optix-dev.git "${OPTIX_INSTALL_DIR}" 2>/dev/null || {
      echo -e "${YELLOW}[WARN] Failed to clone OptiX SDK. Hardware ray tracing will be unavailable.${RESET}"
      OPTIX_INSTALL_DIR=""
    }
  fi
  if [ -n "${OPTIX_INSTALL_DIR}" ] && [ -d "${OPTIX_INSTALL_DIR}/include" ]; then
    cp -r "${OPTIX_INSTALL_DIR}/include/"* /usr/local/include/
    OPTIX_VER=$(grep '#define OPTIX_VERSION' /usr/local/include/optix.h 2>/dev/null | awk '{print $3}')
    echo -e "${GREEN}--> OptiX SDK headers deployed (version ${OPTIX_VER:-unknown}).${RESET}"
    # Cache to Drive for next session
    DRIVE_ROOT="${DERVGEN_DRIVE_ROOT:-/content/drive/MyDrive/dervgen}"
    if [ -d "${DRIVE_ROOT}" ] && [ ! -d "${DRIVE_OPTIX}" ]; then
      mkdir -p "$(dirname "${DRIVE_OPTIX}")"
      cp -r "${OPTIX_INSTALL_DIR}" "${DRIVE_OPTIX}" 2>/dev/null || true
      echo -e "${CYAN}    Cached to Google Drive for future sessions.${RESET}"
    fi
  fi
fi

# ──────────────────────────────────────────────────────────────
# Step 6/8: Python Scientific & Rendering Dependencies
# ──────────────────────────────────────────────────────────────
echo -e "\n${BOLD}${YELLOW}[Step 6/8] Installing Python scientific & workspace packages...${RESET}"
pip install -q --upgrade pip setuptools wheel

# Install core rendering & computation libraries
pip install -q numpy Pillow PyYAML imageio tqdm pytest requests || true

# If requirements files exist, install them
if [ -f "${WORKSPACE_ROOT}/environments/requirements.txt" ]; then
  pip install -q -r "${WORKSPACE_ROOT}/environments/requirements.txt" || true
fi
if [ -f "${WORKSPACE_ROOT}/environments/requirements-gpu.txt" ]; then
  pip install -q -r "${WORKSPACE_ROOT}/environments/requirements-gpu.txt" || true
fi
echo -e "${GREEN}--> Python dependencies successfully updated.${RESET}"

# ──────────────────────────────────────────────────────────────
# Step 7/8: Shell Environment & Aliases
# ──────────────────────────────────────────────────────────────
echo -e "\n${BOLD}${YELLOW}[Step 7/8] Injecting environment variables and aliases...${RESET}"
BASHRC="/root/.bashrc"
PROFILE_D="/etc/profile.d/dervgen_env.sh"

cat << 'EOF' > "${PROFILE_D}"
# DervGen Unified Environment
export CC=clang
export CXX=clang++
export GOROOT=/usr/local/go
export GOPATH=$HOME/go
export PATH=/usr/local/go/bin:$HOME/go/bin:/usr/local/bin:$HOME/tools/bin:$PATH
EOF

if [ -f "${BASHRC}" ]; then
  if ! grep -q "dervgen_env.sh" "${BASHRC}"; then
    echo "source ${PROFILE_D}" >> "${BASHRC}"
    echo "export WORKSPACE_ROOT=\"${WORKSPACE_ROOT}\"" >> "${BASHRC}"
  fi
fi
# shellcheck disable=SC1090
source "${PROFILE_D}" 2>/dev/null || true
echo -e "${GREEN}--> Shell environment configured (CC=clang, GOROOT, PATH).${RESET}"

# ──────────────────────────────────────────────────────────────
# Step 8/8: Ecosystem Hooks (ML Tools, Synapse, Datasets)
# ──────────────────────────────────────────────────────────────
echo -e "\n${BOLD}${YELLOW}[Step 8/8] Executing optional ecosystem hooks...${RESET}"

# 8.1 ML Tools Pre-fetch
INIT_TOOLS_SCRIPT=""
if [ -f "${SCRIPT_DIR}/init_tools.py" ]; then
  INIT_TOOLS_SCRIPT="${SCRIPT_DIR}/init_tools.py"
elif [ -f "${WORKSPACE_ROOT}/workenv/google-colab/init_tools.py" ]; then
  INIT_TOOLS_SCRIPT="${WORKSPACE_ROOT}/workenv/google-colab/init_tools.py"
fi

if [ -n "${INIT_TOOLS_SCRIPT}" ] && [ -d "/content/drive/MyDrive" ]; then
  INIT_TOOLS_PRESET="${INIT_TOOLS_PRESET:-minimal}"
  echo -e "${CYAN}--> Pre-fetching ML wheels (preset: ${INIT_TOOLS_PRESET})...${RESET}"
  python3 "${INIT_TOOLS_SCRIPT}" --preset="${INIT_TOOLS_PRESET}" || true
fi

# 8.2 Synapse package
if [ -d "/content/synapse" ]; then
  echo -e "${CYAN}--> Found synapse at /content/synapse, installing in editable mode...${RESET}"
  pip install -q -e "/content/synapse[dev,image,metrics]" || true
elif [ -d "/content/drive/MyDrive/dervgen/repos/synapse" ]; then
  echo -e "${CYAN}--> Found synapse in Drive repos, installing in editable mode...${RESET}"
  pip install -q -e "/content/drive/MyDrive/dervgen/repos/synapse[dev,image,metrics]" || true
fi

# 8.3 Evaluation Datasets
INIT_DATASETS_SCRIPT=""
if [ -f "${SCRIPT_DIR}/init_datasets.py" ]; then
  INIT_DATASETS_SCRIPT="${SCRIPT_DIR}/init_datasets.py"
elif [ -f "${WORKSPACE_ROOT}/workenv/google-colab/init_datasets.py" ]; then
  INIT_DATASETS_SCRIPT="${WORKSPACE_ROOT}/workenv/google-colab/init_datasets.py"
fi

if [ -d "/content/drive/MyDrive" ] && [ -n "${INIT_DATASETS_SCRIPT}" ]; then
  echo -e "${CYAN}--> Google Drive detected. Staging datasets...${RESET}"
  python3 "${INIT_DATASETS_SCRIPT}" || true
fi

echo -e "\n${BOLD}${GREEN}================================================================${RESET}"
echo -e "${BOLD}${GREEN}  ✓ DervGen Colab environment setup completed successfully!      ${RESET}"
echo -e "${BOLD}${GREEN}    - Bazelisk: $(bazel --version 2>/dev/null || echo 'ready')   ${RESET}"
echo -e "${BOLD}${GREEN}    - Clang:    $(clang --version 2>/dev/null | head -n 1)       ${RESET}"
echo -e "${BOLD}${GREEN}    - Go:       $(go version 2>/dev/null || echo 'ready')        ${RESET}"
if command -v blender &>/dev/null; then
  echo -e "${BOLD}${GREEN}    - Blender:  $(blender --version 2>/dev/null | head -n 1)     ${RESET}"
fi
echo -e "${BOLD}${GREEN}================================================================${RESET}"
