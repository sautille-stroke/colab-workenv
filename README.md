# Colab Workenv: Google Colab Acceleration Hub & Automation Suite

[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/sautille-stroke/colab-workenv/blob/main/colab_bootstrap.ipynb)
[![GitHub license](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Runtime](https://img.shields.io/badge/Colab-GPU%20(T4%2FA100%2FH100)-orange.svg)](https://colab.research.google.com)

Dedicated cloud automation tools, bootstrap notebooks, and setup scripts for running GPU workloads, model inference/fine-tuning, headless C++ rendering, and 3D datasets on Google Colab with Google Drive persistent storage.

> [!NOTE]
> Architecture design, storage taxonomy, and ecosystem standards are maintained in the main architecture repository:
> [`all-overview/architecture/google-colab-and-drive-standards.md`](https://github.com/dervgen/all-overview/blob/main/architecture/google-colab-and-drive-standards.md).

---

## ⚡ 1-Click Launch

Click the badge above to open [`colab_bootstrap.ipynb`](./colab_bootstrap.ipynb) directly in Google Colab.

Or clone in Colab terminal:
```bash
!git clone https://github.com/sautille-stroke/colab-workenv.git /content/colab-workenv
%cd /content/colab-workenv
```

---

## 📁 Key Components & Capabilities

### 1. 📥 Data & Asset Download
| Tool | Description |
|---|---|
| [`download_open_assets.py`](./download_open_assets.py) | **Open 3D & Game Downloader**: One-click downloader for CC0 PBR materials, HDRIs (Poly Haven), free 3D models (Stanford, Bistro), and modular game kits under SSOT V2.1 |
| [`init_datasets.py`](./init_datasets.py) | **Dataset Staging**: Stages 3D scenes, RFC 0053 SWE-bench for 3D suites (90 cases), and closed-loop test cases directly into Google Drive |

### 2. 🤖 Model Pre-fetch & Management
| Tool | Description |
|---|---|
| [`init_models.py`](./init_models.py) / [`init_models.sh`](./init_models.sh) | **Cloud-to-Drive Model Fetcher**: Pre-fetches model weights across 7 categories (`fast`, `P0`, `all`) directly into Google Drive |
| [`models/model_registry.json`](./models/model_registry.json) | Complete metadata registry for foundation vision models, diffusion models, and 3D reconstructors |
| [`google_ultra_pool.py`](./google_ultra_pool.py) | Multi-account load-balancing API client pool for Google AI Studio / Gemini |

### 3. 🌐 Remote Connectivity (Tailscale & VS Code Tunnel)
| Tool | Description |
|---|---|
| [`tailscale.sh`](./tailscale.sh) | **Tailscale WireGuard P2P**: Sets up Tailscale & Tailscale SSH with ephemeral auth keys |
| [`scripts/start_tailscale_ssh.sh`](./scripts/start_tailscale_ssh.sh) | Quick-start script for running Tailscale daemon and SSH service in background |
| [`connect_colab.ps1`](./connect_colab.ps1) | Windows PowerShell helper to connect directly to the Colab machine |
| [`vscode_tunnel.sh`](./vscode_tunnel.sh) | **Microsoft VS Code Tunnel**: Launches `code tunnel` to connect from desktop VS Code / Antigravity |

### 4. 💾 Storage & Persistence (Google Drive SSOT V2.0)
| Tool | Description |
|---|---|
| [`drive_manager.py`](./drive_manager.py) | Google Drive SSOT V2.0 storage manager enforcing `/dervgen/{data,tools,cache,work}` layout |
| [`drive_sync.py`](./drive_sync.py) | Safely mirrors notebook outputs and checkpoints to Google Drive |
| [`organize_directories.py`](./organize_directories.py) | Universal Drive directory organizer conforming to Domain-Driven Architecture |
| [`migrate_drive_v1_to_v2.py`](./migrate_drive_v1_to_v2.py) | Migration script upgrading legacy Drive structures to V2.0 |

### 5. 🛠️ Build & Runtime Automation
| Tool | Description |
|---|---|
| [`colab_bootstrap.ipynb`](./colab_bootstrap.ipynb) | Master Colab notebook: hardware check, toolchain setup, drive mount, repo cloner |
| [`setup_env.sh`](./setup_env.sh) | Unattended script installing Bazelisk (9.3.1), LLVM/Clang 18, Go 1.23+, Blender 4.3 LTS, and Python packages |
| [`run_cpp.sh`](./run_cpp.sh) | C++ Bazel build & headless execution runner with Drive disk cache & Xvfb |
| [`stage_all_for_experiments.py`](./stage_all_for_experiments.py) | Master staging controller for Drive directories, datasets, and workspaces |
| [`init_tools.py`](./init_tools.py) | Pre-fetches wheel packages for offline ML training toolchains |
| [`git_sync.sh`](./git_sync.sh) | Fast commit and push helper with timestamp and branch management |

---

## 🔒 Connect Local Terminal via Tailscale SSH

1. Generate a Tailscale auth key from [Tailscale Admin > Settings > Keys](https://login.tailscale.com/admin/settings/keys) (recommended: **Reusable**, **Ephemeral**).
2. Store key in Colab Secrets as `TAILSCALE_AUTHKEY`, or pass it as an argument:
   ```bash
   !bash /content/colab-workenv/tailscale.sh "tskey-auth-xxxx" "dervgen-colab-gpu"
   ```
3. Connect from your local terminal:
   ```bash
   ssh root@dervgen-colab-gpu
   ```
   Or on Windows, run:
   ```powershell
   .\connect_colab.ps1 -Hostname "dervgen-colab-gpu"
   ```

---

## 💻 Connect Local VS Code / Antigravity via Tunnel

1. Run the tunnel script in Colab:
   ```bash
   !bash /content/colab-workenv/vscode_tunnel.sh "dervgen-colab-gpu"
   ```
2. Open the printed authorization link (e.g., `https://github.com/login/device`) and enter the 8-digit code.
3. In desktop VS Code / Antigravity:
   - Install **Remote - Tunnels** extension.
   - Run `Remote-Tunnels: Connect to Tunnel...` and choose `dervgen-colab-gpu`.

---

## 🔐 Credentials & Secrets Handling

To push commits from Google Colab without hardcoding tokens:
1. Open Google Colab left sidebar -> Click 🔑 **Secrets**.
2. Add a secret named `GITHUB_TOKEN` with your GitHub Personal Access Token (`repo` scope).
3. Toggle "Notebook access" ON.
4. `colab_bootstrap.ipynb` reads `userdata.get('GITHUB_TOKEN')` and configures Git credentials securely.
