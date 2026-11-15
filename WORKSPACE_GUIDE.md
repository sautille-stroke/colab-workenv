# DervGen Unified Cloud Workspace & Google Colab Hub

[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/sautille-stroke/workspace/blob/main/colab/colab_bootstrap.ipynb)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Bazel](https://img.shields.io/badge/Bazel-9.3.1-green.svg)](https://bazel.build/)
[![C++20](https://img.shields.io/badge/C%2B%2B-20-blue.svg)](https://en.cppreference.com/w/cpp/20)

> **DervGen Workspace** is the central repository for maintaining complete cloud development environments, persistent Google Colab GPU sessions, interactive notebooks, and seamless synchronization with the [DervGen](https://github.com/dervgen) ecosystem.

---

## 🌟 Highlights

- **🚀 1-Click Google Colab Launch**: Spin up a fully configured Linux GPU environment with one click.
- **🛠️ Pre-configured Toolchains**: Automated bootstrap for **Bazelisk (Bazel 9.3.1)**, **Clang C++20**, **Go**, and **PyTorch CUDA**.
- **💾 Dual Persistence Strategy**: Sync state back to **GitHub** via automated scripts or backup large datasets/artifacts to **Google Drive**.
- **💻 Desktop IDE Integration**: First-class support for **VS Code Tunnel** (`code tunnel`), letting you develop from your local desktop VS Code or Antigravity IDE directly on Colab GPUs.
- **📦 Selective Repo Cloner**: Fast shallow-cloning tool for ecosystem repositories (`aether`, `fulgur`, `caelum-core`, `vg-core`, `synapse`, etc.).

---

## 📂 Repository Layout

```
workspace/
├── colab/                                 # Google Colab specific entrypoints & scripts
│   ├── colab_bootstrap.ipynb              # ⭐ Main 1-Click Bootstrap Notebook
│   ├── setup_env.sh                       # Unattended environment installation script
│   ├── vscode_tunnel.sh                   # VS Code Remote Tunnel launcher
│   ├── tailscale.sh                       # Tailscale & Tailscale SSH WireGuard launcher
│   ├── git_sync.sh                        # One-command commit & push to GitHub
│   ├── drive_sync.py                      # Google Drive backup & restore utility
│   └── README.md                          # Colab guide & secrets instructions
├── configs/                               # Configuration templates
│   ├── .env.example                       # API keys & token template
│   └── colab_config.json                  # Runtime parameters & preferences
├── environments/                          # Python & shell environments
│   ├── requirements.txt                   # Base Python dependencies
│   ├── requirements-gpu.txt               # GPU, vision, and 3D processing extensions
│   └── bashrc_addon.sh                    # Handy terminal aliases and environment variables
├── experiments/                           # Modular frontier experiment execution sandboxes
│   ├── exp05_3d_anchor_video_gen/         # Step 1-2: 3D concept & diffusion video synthesis
│   ├── exp06_kinematic_distillation/      # Step 3: 4D tracking, foot-plant IK & de-lighting
│   ├── exp07_physics_surgical_inpaint/    # Step 4-6: FGPP AOV bake & surgical inpainting
│   └── exp08_e2e_ablation_scorecard/      # Step 7: Cross-modal metrics & 4-group ablation
├── notebooks/                             # Jupyter notebooks & experiment scratchpads
│   ├── 00_quickstart_and_gpu_check.ipynb  # GPU micro-benchmarks (TFLOPS, VRAM)
│   ├── 01_dervgen_build_smoke_test.ipynb  # DervGen Bazel build verification
│   ├── 02_model_and_drive_management.ipynb# Model pre-fetcher & Drive explorer
│   ├── 03_cpp_headless_rendering_pipeline.ipynb # Headless C++ rendering pipeline
│   ├── 04_experiment_lab.ipynb            # One-click Master Experiment Lab (3D, Video, OIDN, Mocap)
│   └── 05_seedance_closed_loop_pipeline.ipynb # Bidirectional Neural-Physical Closed Loop (Model <-> Seedance)
├── weekly/                                # Weekly execution plans & specialized runbooks
│   └── 2026-11-09/                        # W46 roadmap, grandforge pipeline & Seedance loop plan
├── repos/                                 # Ecosystem manifest and selective cloner
│   ├── repo_manifest.json                 # Metadata registry of DervGen repositories
│   └── clone_repos.sh                     # Fast shallow cloner script
├── scripts/                               # Cross-platform utility scripts
│   ├── check_env.sh                       # Full environment & hardware diagnostics
│   └── clean_cache.sh                     # Cache & checkpoint cleaner
├── .gitattributes                         # Normalized LF line-endings
├── .gitignore                             # Ignore rules for checkpoints, venvs, and models
├── LICENSE                                # MIT License
└── README.md                              # This documentation
```

---

## 🗄️ Storage SSOT Specification (100% Pure Cloud / Zero Local Disk Footprint)

> [!TIP]
> **本地零存储负担原则**：无需在本地电脑安装 Google Drive 客户端，不向本地磁盘同步或下载任何 GB 级别的模型权重与原始数据集。
> - **数据集导入**：直接在浏览器打开 [Google Drive Web 端](https://drive.google.com/) 拖拽上传到 `dervgen/data/`，或在 Colab 内使用 `download_data` 脚本直接从公网/S3/HuggingFace 灌入云端 Drive。
> - **模型权重管理**：直接在 Colab Web 单元格内调用 `download_model`，以数据中心带宽（50-150 MB/s）直达云端 Drive。
> - **实验结果查看**：在 Colab Notebook 单元格内直接内联渲染预览，或在 Google Drive Web 端单点下载最终生成的 `.glb` / `.png` 成果物。

All shared models, raw datasets, and per-job task outputs follow a strict single-source-of-truth directory layout under `/dervgen/` (e.g. `/content/drive/MyDrive/dervgen/`):

```
/dervgen/
├── model/{usage}/                  # Model weights organized by purpose
│   ├── 3d_recon/                   # 3DGS, DUSt3R, MASt3R, InstantMesh, NeRF
│   ├── texture_gen/                # Material synthesis, OpenPBR diffusion
│   ├── actor_dynamics/             # SMPL-X, Face rigs, neural cloth & dynamics
│   ├── foundation/                 # SAM 2, DINOv2, CLIP, Vision-Language
│   └── denoise_upscale/            # Neural denoisers, super-resolution
├── data/                           # Ground-truth raw datasets & benchmark assets
│   ├── benchmarks/                 # Sponza, Bistro, Cornell Box
│   ├── captures/                   # Multi-view image captures & calibration files
│   └── raw/                        # Unprocessed sensor and scan inputs
├── workspace/${jobname}/           # Self-contained per-job execution sandbox
│   ├── input/                      # Task parameters, job_config.yaml, scene manifests
│   ├── output/                     # Generated 3D meshes, render frames, metrics.json, logs
│   └── checkpoints/                # Periodic training states and optimizer dumps
└── cache/                          # Persistent caches
    ├── bazel/                      # Bazel build disk cache
    └── huggingface/                # Hugging Face hub cache
```

---

## 🚀 Getting Started

### Scenario A: Working in Google Colab (Cloud GPU)

1. **Launch**: Click the [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/sautille-stroke/workspace/blob/main/colab/colab_bootstrap.ipynb) badge.
2. **Configure**: Select your options in the top form (Mount Google Drive, install toolchains, select repos).
3. **Run**: Click `Runtime` -> `Run all`.
4. **Develop**:
   - Write code in Colab notebooks, or
   - Start VS Code Tunnel (`START_VSCODE_TUNNEL = True`) to connect from your local IDE, or
   - Start Tailscale SSH (`START_TAILSCALE = True`) to connect directly from your local terminal via `ssh root@dervgen-colab-gpu`.
5. **Sync**:
   - Run `sync_to_github('your commit message')` to commit and push your work back to GitHub.

### Scenario B: Working Locally or on Cloud Server (`ubuntu24`)

Clone the workspace to your local machine or dev server:

```bash
git clone https://github.com/sautille-stroke/workspace.git
cd workspace

# Run environment check
bash scripts/check_env.sh

# Clone selected DervGen repos into /path/to/dervgen
bash repos/clone_repos.sh ~/work/dervgen "aether,fulgur"
```

---

## 🔒 Security Best Practices

- **Never commit `.env` or plain-text tokens!** `.env` is ignored by default in `.gitignore`.
- On Google Colab, use **Colab Secrets** (Key icon in the left toolbar) to store `GITHUB_TOKEN`, `TAILSCALE_AUTHKEY`, `HF_TOKEN`, or `WANDB_API_KEY`.
- Run `bash scripts/clean_cache.sh` before pushing to avoid staging ephemeral `.ipynb_checkpoints` or `__pycache__` artifacts.

---

## 📄 License

Licensed under the [MIT License](../../LICENSE). Copyright (c) 2026 Sautille Stroke.
