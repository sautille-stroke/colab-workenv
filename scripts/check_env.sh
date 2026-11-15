#!/usr/bin/env bash
# ==============================================================================
# DervGen Workspace: Comprehensive Environment Diagnostic Tool
# ==============================================================================
# Verifies system health and readiness across 6 pillars:
#   1. System & Architecture (OS, Kernel, CPU, RAM)
#   2. Storage & Google Drive SSOT V2.0 Mount
#   3. GPU & CUDA 12.x Toolkit (nvidia-smi, nvcc, runtime libs)
#   4. Universal Toolchains:
#      - Bazel (Bazelisk version, bzlmod ready)
#      - LLVM / Clang 18 (clang, clang++, lld, C++20 concepts test)
#      - Go 1.23+ (Go version, GOROOT, GOPATH)
#      - Blender 4.3 LTS (Cycles engine headless load, GPU devices)
#   5. Python Runtime & Scientific Libraries (PyTorch, numpy, Pillow, PyYAML)
#   6. Diagnostic Scorecard (Pass / Warn / Fail)
# ==============================================================================

set -uo pipefail

BOLD="\033[1m"
GREEN="\033[32m"
YELLOW="\033[33m"
CYAN="\033[36m"
RED="\033[31m"
RESET="\033[0m"

PASS_COUNT=0
WARN_COUNT=0
FAIL_COUNT=0

pass() { echo -e "  ${GREEN}✅ PASS:${RESET} $1"; PASS_COUNT=$((PASS_COUNT + 1)); }
warn() { echo -e "  ${YELLOW}⚠️  WARN:${RESET} $1"; WARN_COUNT=$((WARN_COUNT + 1)); }
fail() { echo -e "  ${RED}❌ FAIL:${RESET} $1"; FAIL_COUNT=$((FAIL_COUNT + 1)); }
info() { echo -e "     ℹ️  $1"; }

echo -e "${BOLD}${CYAN}================================================================${RESET}"
echo -e "${BOLD}${CYAN}            DervGen Workspace Environment Diagnostics           ${RESET}"
echo -e "${BOLD}${CYAN}================================================================${RESET}"

# ──────────────────────────────────────────────────────────────
# 1. Operating System & Architecture
# ──────────────────────────────────────────────────────────────
echo -e "\n${BOLD}${YELLOW}[1] System & Architecture${RESET}"
if [ -f /etc/os-release ]; then
  # shellcheck source=/dev/null
  . /etc/os-release
  echo -e "  OS:     ${GREEN}${PRETTY_NAME}${RESET}"
else
  echo -e "  OS:     $(uname -s)"
fi
echo -e "  Kernel: $(uname -r) ($(uname -m))"
echo -e "  Uptime: $(uptime -p 2>/dev/null || uptime)"

# ──────────────────────────────────────────────────────────────
# 2. CPU & Memory Resources
# ──────────────────────────────────────────────────────────────
echo -e "\n${BOLD}${YELLOW}[2] CPU & Memory Resources${RESET}"
CPU_MODEL=$(lscpu 2>/dev/null | grep 'Model name:' | sed 's/Model name:[ \t]*//' || grep 'model name' /proc/cpuinfo | head -n 1 | awk -F: '{print $2}' | xargs)
CPU_CORES=$(nproc 2>/dev/null || echo "Unknown")
echo -e "  CPU:    ${GREEN}${CPU_MODEL}${RESET} (${CPU_CORES} vCPUs)"
free -h 2>/dev/null | awk '/^Mem:/ {print "  RAM:    Total " $2 ", Used " $3 ", Free " $4 ", Available " $7}'

# ──────────────────────────────────────────────────────────────
# 3. Disk Mounts & Google Drive Storage
# ──────────────────────────────────────────────────────────────
echo -e "\n${BOLD}${YELLOW}[3] Disk Mounts & Storage${RESET}"
df -h / | awk 'NR==1 || NR==2 {print "  " $0}'
if [ -d "/content/drive/MyDrive" ]; then
  pass "Google Drive mounted at /content/drive/MyDrive"
  df -h /content/drive 2>/dev/null | awk 'NR==2 {print "     Capacity: Total " $2 ", Used " $3 ", Free " $4}'
  DRIVE_ROOT="${DERVGEN_DRIVE_ROOT:-/content/drive/MyDrive/dervgen}"
  if [ -d "${DRIVE_ROOT}" ]; then
    pass "DervGen SSOT root exists at ${DRIVE_ROOT}"
  else
    warn "DervGen SSOT directory (${DRIVE_ROOT}) not yet initialized"
  fi
else
  warn "Google Drive not mounted at /content/drive/MyDrive"
fi

# ──────────────────────────────────────────────────────────────
# 4. GPU & CUDA 12.x Architecture
# ──────────────────────────────────────────────────────────────
echo -e "\n${BOLD}${YELLOW}[4] GPU & Hardware Accelerator${RESET}"
if command -v nvidia-smi &>/dev/null; then
  GPU_NAME=$(nvidia-smi --query-gpu=gpu_name --format=csv,noheader 2>/dev/null | head -n 1 | xargs)
  GPU_MEM=$(nvidia-smi --query-gpu=memory.total --format=csv,noheader 2>/dev/null | head -n 1 | xargs)
  DRIVER_VER=$(nvidia-smi --query-gpu=driver_version --format=csv,noheader 2>/dev/null | head -n 1 | xargs)
  RAW_CAP=$(nvidia-smi --query-gpu=compute_cap --format=csv,noheader 2>/dev/null | head -n 1 | xargs)

  pass "GPU detected: ${GPU_NAME} (${GPU_MEM})"
  info "Driver: ${DRIVER_VER} | Compute Capability: ${RAW_CAP}"

  # Check CUDA nvcc compiler
  if command -v nvcc &>/dev/null; then
    NVCC_VER=$(nvcc --version 2>/dev/null | grep "release" | sed 's/.*release //' | sed 's/,.*//' || echo "unknown")
    CUDA_MAJOR=$(echo "${NVCC_VER}" | cut -d'.' -f1)
    if [ "${CUDA_MAJOR:-0}" -ge 12 ]; then
      pass "CUDA Toolkit ${NVCC_VER} (>= 12.x)"
    else
      warn "CUDA Toolkit ${NVCC_VER} (version < 12.x)"
    fi
  elif [ -x /usr/local/cuda/bin/nvcc ]; then
    NVCC_VER=$(/usr/local/cuda/bin/nvcc --version 2>/dev/null | grep "release" | sed 's/.*release //' | sed 's/,.*//' || echo "unknown")
    pass "CUDA Toolkit ${NVCC_VER} (at /usr/local/cuda)"
  else
    warn "nvcc compiler not found in PATH"
  fi

  # Check CUDA runtime libraries
  CUDA_LIBS_OK=1
  for clib in libcudart libcublas libcusparse; do
    if ! ldconfig -p 2>/dev/null | grep -q "${clib}" && [ ! -f "/usr/local/cuda/lib64/${clib}.so" ]; then
      CUDA_LIBS_OK=0
    fi
  done
  if [ "${CUDA_LIBS_OK}" -eq 1 ]; then
    pass "CUDA runtime libraries found (cudart, cublas, cusparse)"
  else
    warn "Some CUDA runtime libraries missing from library path"
  fi
else
  warn "No NVIDIA GPU detected or nvidia-smi is unavailable"
fi

# 4.5 OptiX SDK Headers
if [ -f "/usr/local/include/optix.h" ]; then
  OPTIX_VER=$(grep '#define OPTIX_VERSION' /usr/local/include/optix.h 2>/dev/null | awk '{print $3}')
  pass "OptiX SDK headers present (version ${OPTIX_VER:-unknown})"
else
  warn "OptiX SDK headers not found — hardware ray tracing unavailable"
  info "Fix: git clone --depth=1 https://github.com/NVIDIA/optix-dev.git /opt/optix-dev && cp -r /opt/optix-dev/include/* /usr/local/include/"
fi

# ──────────────────────────────────────────────────────────────
# 5. Core Foundation Toolchains (Bazel, LLVM, Go, Blender)
# ──────────────────────────────────────────────────────────────
echo -e "\n${BOLD}${YELLOW}[5] Core Foundation Toolchains${RESET}"

# 5.1 Bazelisk / Bazel
if command -v bazel &>/dev/null; then
  BAZEL_VER=$(bazel --version 2>/dev/null || echo "Bazel wrapper found")
  pass "Bazel: ${BAZEL_VER} ($(command -v bazel))"
else
  fail "Bazel: Not installed (expected /usr/local/bin/bazel)"
fi

# 5.2 LLVM / Clang 18 (C++20)
if command -v clang &>/dev/null; then
  CLANG_VER_STR=$(clang --version | head -n 1)
  CLANG_MAJOR=$(echo "${CLANG_VER_STR}" | grep -oP 'version \K\d+' || echo "0")
  if [ "${CLANG_MAJOR}" -ge 18 ]; then
    pass "Clang ${CLANG_MAJOR}: ${CLANG_VER_STR}"
  elif [ "${CLANG_MAJOR}" -ge 14 ]; then
    warn "Clang ${CLANG_MAJOR}: satisfies C++20 but >= 18 recommended"
  else
    fail "Clang ${CLANG_MAJOR}: too old, requires LLVM >= 18"
  fi

  # Check clang++ & lld
  if command -v clang++ &>/dev/null; then
    pass "clang++ found: $(command -v clang++)"
  else
    fail "clang++ not found"
  fi
  if command -v lld &>/dev/null; then
    pass "lld linker found: $(lld --version 2>/dev/null | head -n 1)"
  else
    warn "lld linker not found (falling back to ld)"
  fi

  # C++20 concepts compile test
  TEST_SRC=$(mktemp /tmp/cpp20_check_XXXX.cc)
  cat << 'CPPEOF' > "${TEST_SRC}"
#include <concepts>
template<std::floating_point T> T sq(T x) { return x * x; }
int main() { return sq(2.0f) > 0 ? 0 : 1; }
CPPEOF
  if clang++ -std=c++20 -o /dev/null "${TEST_SRC}" 2>/dev/null; then
    pass "C++20 concepts compilation test passed"
  else
    warn "C++20 concepts compilation test failed"
  fi
  rm -f "${TEST_SRC}"
else
  fail "Clang: Not installed"
fi

# 5.3 Go 1.23+
if command -v go &>/dev/null; then
  GO_VER_STR=$(go version)
  CURRENT_GO_VER=$(echo "${GO_VER_STR}" | awk '{print $3}' | sed 's/go//')
  GO_MAJOR=$(echo "${CURRENT_GO_VER}" | cut -d'.' -f1)
  GO_MINOR=$(echo "${CURRENT_GO_VER}" | cut -d'.' -f2)
  if [ "${GO_MAJOR:-0}" -ge 1 ] && [ "${GO_MINOR:-0}" -ge 23 ]; then
    pass "Go: ${GO_VER_STR}"
  else
    warn "Go ${CURRENT_GO_VER} is below required 1.23+ (found: ${GO_VER_STR})"
  fi
  info "GOROOT: $(go env GOROOT 2>/dev/null || echo 'not set') | GOPATH: $(go env GOPATH 2>/dev/null || echo 'not set')"
else
  fail "Go: Not installed"
fi

# 5.4 Blender 4.3 LTS (Cycles Headless)
BLENDER_EXEC=$(command -v blender 2>/dev/null || echo "/usr/local/bin/blender")
if [ -x "${BLENDER_EXEC}" ]; then
  BLENDER_VER=$("${BLENDER_EXEC}" --version 2>/dev/null | head -n 1 || echo "unknown")
  pass "Blender: ${BLENDER_VER} (${BLENDER_EXEC})"

  # Test Cycles engine headless
  CYCLES_TEST=$("${BLENDER_EXEC}" --background --factory-startup -noaudio --python-exit-code 1 \
    --python-expr "import bpy; bpy.context.scene.render.engine='CYCLES'; print('CYCLES_HEADLESS_READY')" 2>&1 || true)
  if echo "${CYCLES_TEST}" | grep -q "CYCLES_HEADLESS_READY"; then
    pass "Blender Cycles headless render engine is operational"
  else
    warn "Blender Cycles headless engine test failed"
  fi

  # Enumerate Cycles compute devices
  CYCLES_DEVICES=$("${BLENDER_EXEC}" --background --factory-startup -noaudio --python-exit-code 1 \
    --python-expr "
import bpy
prefs = bpy.context.preferences.addons.get('cycles')
if prefs:
    cprefs = prefs.preferences
    cprefs.get_devices()
    for d in cprefs.devices:
        print(f'CYCLES_DEV: {d.name} ({d.type})')
" 2>&1 | grep "CYCLES_DEV:" || true)
  if [ -n "${CYCLES_DEVICES}" ]; then
    echo "${CYCLES_DEVICES}" | while IFS= read -r devline; do
      info "${devline}"
    done
  fi
else
  warn "Blender: Not installed (run setup_env.sh to install Blender 4.3 LTS)"
fi

# ──────────────────────────────────────────────────────────────
# 6. Python Runtime & Scientific Libraries
# ──────────────────────────────────────────────────────────────
echo -e "\n${BOLD}${YELLOW}[6] Python Runtime & Scientific Libraries${RESET}"
if command -v python3 &>/dev/null; then
  pass "Python: $(python3 --version 2>&1)"
  # PyTorch
  python3 -c "
import torch
print(f'     PyTorch {torch.__version__} | CUDA Available: {torch.cuda.is_available()}')
if torch.cuda.is_available():
    print(f'     Device: {torch.cuda.get_device_name(0)}')
" 2>/dev/null || info "PyTorch: Not available in current environment"

  # Core Scientific Libs
  python3 -c "
missing = []
for m in ['numpy', 'PIL', 'yaml', 'imageio', 'pytest']:
    try:
        __import__(m)
    except ImportError:
        missing.append(m)
if not missing:
    print('  \033[32m✅ PASS:\033[0m Core libraries installed (numpy, Pillow, PyYAML, imageio, pytest)')
else:
    print(f'  \033[33m⚠️  WARN:\033[0m Missing libraries: {\", \".join(missing)}')
" 2>/dev/null || true
else
  fail "Python 3: Not installed"
fi

# ──────────────────────────────────────────────────────────────
# 7. Diagnostic Summary Scorecard
# ──────────────────────────────────────────────────────────────
echo -e "\n${BOLD}${CYAN}================================================================${RESET}"
echo -e "${BOLD}${CYAN}                  Environment Diagnostic Summary                ${RESET}"
echo -e "${BOLD}${CYAN}================================================================${RESET}"
echo -e "  Passed:   ${GREEN}${PASS_COUNT}${RESET}"
echo -e "  Warnings: ${YELLOW}${WARN_COUNT}${RESET}"
echo -e "  Failures: ${RED}${FAIL_COUNT}${RESET}"

if [ "${FAIL_COUNT}" -eq 0 ]; then
  echo -e "\n${BOLD}${GREEN}  ✓ Workspace baseline is ready for development & rendering!${RESET}"
else
  echo -e "\n${BOLD}${RED}  ❌ ${FAIL_COUNT} critical check(s) failed. Run setup_env.sh to remediate.${RESET}"
fi
echo -e "${BOLD}${CYAN}================================================================${RESET}"
