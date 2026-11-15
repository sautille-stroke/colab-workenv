#!/usr/bin/env python3
"""
DervGen Workspace: ML Training & Evaluation Toolchain Pre-fetcher (Google Drive SSOT)
Downloads Python wheel packages directly into Google Drive (/dervgen/tools/wheels/...)
and maintains real-time INDEX.json and INDEX.md, following the same pattern as init_models.py.

Usage:
  python3 init_tools.py                        # Download full preset (all categories)
  python3 init_tools.py --preset=llm           # LLM fine-tuning subset
  python3 init_tools.py --preset=cv            # Computer Vision subset
  python3 init_tools.py --categories=A,B       # Specific categories
  python3 init_tools.py --dry-run              # Plan only, no download
  python3 init_tools.py --sync-index           # Re-scan and sync INDEX
  python3 init_tools.py --install              # Install from cached wheels (offline)

Storage Layout (Google Drive):
  /dervgen/tools/
  ├── INDEX.json          # Machine-readable inventory
  ├── INDEX.md            # Human-readable inventory
  └── wheels/
      ├── A_training/     # Category A wheels
      ├── B_evaluation/   # Category B wheels
      ├── C_tracking/     # Category C wheels
      ├── D_classical/    # Category D wheels
      ├── E_data/         # Category E wheels
      └── F_hpo/          # Category F wheels
"""

import os
import sys
import json
import subprocess
import argparse
from datetime import datetime, timezone
from pathlib import Path

# Safe utf-8 stdout
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

SCRIPT_DIR = Path(__file__).resolve().parent
WORKSPACE_ROOT = SCRIPT_DIR.parent
DRIVE_ROOT = Path(os.environ.get("DERVGEN_DRIVE_ROOT", "/content/drive/MyDrive/dervgen"))
TOOLS_ROOT = DRIVE_ROOT / "tools"
WHEELS_ROOT = TOOLS_ROOT / "wheels"


# ==============================================================================
# Tool Registry: categorized packages with metadata
# ==============================================================================

TOOL_CATEGORIES = {
    "A": {
        "name": "Training Frameworks & Accelerators",
        "icon": "🏋️",
        "dir": "A_training",
        "packages": [
            {"pip": "transformers",     "desc": "Hugging Face Transformers (LLM/VLM architectures & pretrained weights)"},
            {"pip": "datasets",         "desc": "Hugging Face Datasets (streaming, caching, Arrow-backed)"},
            {"pip": "tokenizers",       "desc": "Hugging Face Tokenizers (Rust-accelerated BPE/WordPiece/Unigram)"},
            {"pip": "accelerate",       "desc": "Hugging Face Accelerate (multi-GPU, FSDP, DeepSpeed, mixed precision)"},
            {"pip": "pytorch-lightning", "desc": "PyTorch Lightning (structured training loops, auto-distributed)"},
            {"pip": "peft",             "desc": "PEFT (LoRA, QLoRA, Prefix Tuning, IA³ parameter-efficient fine-tuning)"},
            {"pip": "trl",              "desc": "TRL (SFTTrainer, DPO, PPO, ORPO alignment training)"},
            {"pip": "bitsandbytes",     "desc": "bitsandbytes (8-bit/4-bit quantization for large model fine-tuning)"},
        ],
    },
    "B": {
        "name": "Evaluation & Metrics",
        "icon": "📊",
        "dir": "B_evaluation",
        "packages": [
            {"pip": "torchmetrics",     "desc": "TorchMetrics (GPU-accelerated: Accuracy, F1, AUROC, BLEU, ROUGE, FID)"},
            {"pip": "evaluate",         "desc": "Hugging Face Evaluate (unified metric API with 100+ metrics)"},
            {"pip": "scikit-learn",     "desc": "scikit-learn (classification_report, confusion_matrix, cross_val)"},
            {"pip": "rouge-score",      "desc": "ROUGE Score (summarization evaluation)"},
            {"pip": "nltk",             "desc": "NLTK (BLEU, tokenization, linguistic tools)"},
            {"pip": "bert-score",       "desc": "BERTScore (semantic similarity evaluation)"},
        ],
    },
    "C": {
        "name": "Experiment Tracking & Visualization",
        "icon": "📈",
        "dir": "C_tracking",
        "packages": [
            {"pip": "wandb",            "desc": "Weights & Biases (experiment tracking, hyperparameter sweep, artifact store)"},
            {"pip": "tensorboard",      "desc": "TensorBoard (Colab-native training visualization)"},
            {"pip": "mlflow",           "desc": "MLflow (open-source experiment tracking & model registry)"},
        ],
    },
    "D": {
        "name": "Gradient-Boosted Trees & Classical ML",
        "icon": "🌲",
        "dir": "D_classical",
        "packages": [
            {"pip": "lightgbm",         "desc": "LightGBM (fast gradient boosting for tabular data)"},
            {"pip": "xgboost",          "desc": "XGBoost (scalable gradient boosting)"},
            {"pip": "catboost",         "desc": "CatBoost (gradient boosting with native categorical support)"},
        ],
    },
    "E": {
        "name": "Data & Tokenization Utilities",
        "icon": "🔤",
        "dir": "E_data",
        "packages": [
            {"pip": "sentencepiece",    "desc": "SentencePiece (unsupervised text tokenizer for LLM pretraining)"},
            {"pip": "tiktoken",         "desc": "tiktoken (OpenAI BPE tokenizer, GPT-4/Claude compatible)"},
            {"pip": "jsonlines",        "desc": "jsonlines (streaming JSONL reader/writer for training data)"},
            {"pip": "safetensors",      "desc": "safetensors (fast & safe model weight serialization)"},
            {"pip": "huggingface-hub",  "desc": "Hugging Face Hub (model/dataset download, upload, caching)"},
        ],
    },
    "F": {
        "name": "Hyperparameter Optimization",
        "icon": "🎯",
        "dir": "F_hpo",
        "packages": [
            {"pip": "optuna",           "desc": "Optuna (Bayesian hyperparameter optimization with pruning)"},
        ],
    },
}


# Preset profiles
PRESETS = {
    "full": {
        "desc": "All categories (A-F) — complete ML training & evaluation stack",
        "categories": ["A", "B", "C", "D", "E", "F"],
    },
    "llm": {
        "desc": "LLM/VLM fine-tuning & evaluation (A + B + C + E)",
        "categories": ["A", "B", "C", "E"],
    },
    "cv": {
        "desc": "Computer Vision training & evaluation (A partial + B + C)",
        "categories": ["B", "C"],
        "extra_pip": ["pytorch-lightning", "torchmetrics", "wandb", "timm"],
    },
    "tabular": {
        "desc": "Tabular / classical ML (B + D + F)",
        "categories": ["B", "D", "F"],
    },
    "eval_only": {
        "desc": "Evaluation & metrics only (B + C)",
        "categories": ["B", "C"],
    },
    "minimal": {
        "desc": "Bare essentials (Transformers + Accelerate + Metrics + W&B)",
        "categories": [],
        "extra_pip": ["transformers", "datasets", "accelerate", "torchmetrics", "evaluate", "wandb"],
    },
}


def check_drive_mounted() -> bool:
    drive_base = Path("/content/drive/MyDrive")
    if not drive_base.exists() and not os.environ.get("DERVGEN_DRIVE_ROOT"):
        print("⚠️  [Init Tools] Google Drive is NOT mounted at /content/drive/MyDrive.")
        print("    In Colab run: from google.colab import drive; drive.mount('/content/drive')")
        return False
    return True


def _count_wheels(directory: Path) -> tuple:
    """Count .whl files and total size in a directory."""
    if not directory.exists():
        return 0, 0
    wheels = list(directory.glob("*.whl"))
    total_bytes = sum(w.stat().st_size for w in wheels)
    return len(wheels), total_bytes


def _download_wheels(pip_name: str, dest_dir: Path, quiet: bool = True) -> bool:
    """
    Download a package and all its dependencies as wheel files into dest_dir.
    Uses `pip download` which fetches platform-compatible wheels.
    """
    dest_dir.mkdir(parents=True, exist_ok=True)
    q_flag = ["-q"] if quiet else []
    try:
        result = subprocess.run(
            [sys.executable, "-m", "pip", "download"]
            + q_flag
            + ["--dest", str(dest_dir), pip_name],
            capture_output=True,
            text=True,
            timeout=600,
        )
        if result.returncode == 0:
            return True
        else:
            stderr = result.stderr.strip()
            if stderr:
                print(f"      ⚠️ pip download stderr: {stderr[:200]}")
            return False
    except subprocess.TimeoutExpired:
        print(f"      ⚠️ pip download {pip_name} timed out (600s)")
        return False
    except Exception as e:
        print(f"      ⚠️ pip download {pip_name} failed: {e}")
        return False


def _check_wheel_exists(pip_name: str, dest_dir: Path) -> bool:
    """Check if a wheel for this package already exists in dest_dir."""
    if not dest_dir.exists():
        return False
    # Normalize: pip names use - but wheel filenames use _
    normalized = pip_name.lower().replace("-", "_")
    for whl in dest_dir.glob("*.whl"):
        whl_name = whl.name.lower().replace("-", "_")
        if whl_name.startswith(normalized):
            return True
    return False


def _resolve_packages(preset: str, categories: list = None) -> list:
    """Resolve the final list of packages to download given preset/categories."""
    packages = []
    seen_pip = set()

    if categories:
        selected_cats = categories
    elif preset in PRESETS:
        selected_cats = PRESETS[preset]["categories"]
    else:
        selected_cats = list(TOOL_CATEGORIES.keys())

    # Collect from categories
    for cat_key in selected_cats:
        if cat_key in TOOL_CATEGORIES:
            cat = TOOL_CATEGORIES[cat_key]
            for pkg in cat["packages"]:
                if pkg["pip"] not in seen_pip:
                    packages.append({**pkg, "category": cat_key})
                    seen_pip.add(pkg["pip"])

    # Add preset extra packages
    if preset in PRESETS and "extra_pip" in PRESETS[preset]:
        for pip_name in PRESETS[preset]["extra_pip"]:
            if pip_name in seen_pip:
                continue
            # Look up in registry
            found = False
            for cat_key, cat in TOOL_CATEGORIES.items():
                for pkg in cat["packages"]:
                    if pkg["pip"] == pip_name:
                        packages.append({**pkg, "category": cat_key})
                        seen_pip.add(pip_name)
                        found = True
                        break
                if found:
                    break
            if not found:
                # Ad-hoc package not in registry (e.g. timm)
                packages.append({"pip": pip_name, "desc": pip_name, "category": "A"})
                seen_pip.add(pip_name)

    return packages


def run_download(
    preset: str = "full",
    categories: list = None,
    dry_run: bool = False,
):
    """Download wheel files for selected packages into Google Drive."""
    if not dry_run and not check_drive_mounted():
        return

    packages = _resolve_packages(preset, categories)

    print("\n==========================================================================")
    print(f" DervGen ML Toolchain Pre-fetcher (SSOT: {TOOLS_ROOT})")
    print(f" Preset: [{preset}], Categories: [{','.join(categories) if categories else 'from preset'}], Count: [{len(packages)}]")
    print("==========================================================================\n")

    # Print category breakdown
    cat_groups = {}
    for pkg in packages:
        cat_key = pkg["category"]
        cat_groups.setdefault(cat_key, []).append(pkg)

    for cat_key in sorted(cat_groups.keys()):
        if cat_key in TOOL_CATEGORIES:
            cat = TOOL_CATEGORIES[cat_key]
            print(f"  {cat['icon']} Category {cat_key}: {cat['name']}")
            for pkg in cat_groups[cat_key]:
                print(f"      • {pkg['pip']:<25} {pkg['desc']}")
        print()

    if dry_run:
        print(f"[Dry Run] {len(packages)} packages planned. No files downloaded.")
        return

    print("Starting downloads to Google Drive...\n")
    success_count = 0
    skip_count = 0
    fail_count = 0

    for idx, pkg in enumerate(packages, 1):
        pip_name = pkg["pip"]
        cat_key = pkg["category"]
        cat_dir_name = TOOL_CATEGORIES.get(cat_key, {}).get("dir", f"misc")
        dest_dir = WHEELS_ROOT / cat_dir_name

        # Check if already downloaded
        if _check_wheel_exists(pip_name, dest_dir):
            whl_count, whl_bytes = _count_wheels(dest_dir)
            print(f"  [{idx:2d}/{len(packages)}] ⏩ SKIP   {pip_name:<25} (wheel already cached in {cat_dir_name}/)")
            skip_count += 1
            continue

        print(f"  [{idx:2d}/{len(packages)}] ⬇️  FETCH  {pip_name:<25} → tools/wheels/{cat_dir_name}/")

        if _download_wheels(pip_name, dest_dir, quiet=True):
            whl_count, whl_bytes = _count_wheels(dest_dir)
            print(f"           ✓ Downloaded ({whl_bytes / (1024*1024):.1f} MB total in {cat_dir_name}/)")
            success_count += 1
        else:
            print(f"           ❌ Failed to download {pip_name}")
            fail_count += 1

    print("\n==========================================================================")
    print(f" Summary: {success_count} downloaded, {skip_count} already cached, {fail_count} failed, {len(packages)} total")
    print("==========================================================================")

    # Sync index
    sync_drive_index()


def run_install_from_cache(categories: list = None):
    """Install all cached wheels from Google Drive (offline, no network needed)."""
    if not check_drive_mounted():
        return

    print("\n==========================================================================")
    print(f" DervGen ML Toolchain Installer (from cached wheels)")
    print(f" Source: {WHEELS_ROOT}")
    print("==========================================================================\n")

    target_cats = categories if categories else list(TOOL_CATEGORIES.keys())
    total_installed = 0

    for cat_key in sorted(target_cats):
        if cat_key not in TOOL_CATEGORIES:
            continue
        cat = TOOL_CATEGORIES[cat_key]
        cat_dir = WHEELS_ROOT / cat["dir"]

        if not cat_dir.exists():
            print(f"  {cat['icon']} Category {cat_key}: {cat['name']} — no cached wheels, skipping")
            continue

        wheels = list(cat_dir.glob("*.whl"))
        if not wheels:
            print(f"  {cat['icon']} Category {cat_key}: {cat['name']} — no .whl files found, skipping")
            continue

        print(f"  {cat['icon']} Category {cat_key}: {cat['name']} ({len(wheels)} wheels)")
        result = subprocess.run(
            [sys.executable, "-m", "pip", "install", "-q",
             "--no-index", "--find-links", str(cat_dir)]
            + [pkg["pip"] for pkg in cat["packages"]],
            capture_output=True, text=True, timeout=300,
        )
        if result.returncode == 0:
            print(f"     ✅ Installed successfully")
            total_installed += 1
        else:
            print(f"     ⚠️ Some packages may have failed: {result.stderr[:200]}")

    print(f"\n✅ Offline installation complete ({total_installed} categories processed)")


def sync_drive_index():
    """Generates and syncs /dervgen/tools/INDEX.json and INDEX.md on Google Drive."""
    if not check_drive_mounted():
        return

    TOOLS_ROOT.mkdir(parents=True, exist_ok=True)

    drive_index_json = TOOLS_ROOT / "INDEX.json"
    drive_index_md = TOOLS_ROOT / "INDEX.md"

    total_cached = 0
    total_missing = 0
    total_bytes = 0
    inventory = []

    for cat_key in sorted(TOOL_CATEGORIES.keys()):
        cat = TOOL_CATEGORIES[cat_key]
        cat_dir = WHEELS_ROOT / cat["dir"]

        for pkg in cat["packages"]:
            is_cached = _check_wheel_exists(pkg["pip"], cat_dir)

            # Find actual wheel file details
            whl_size = 0
            whl_filename = None
            whl_mtime = None
            if is_cached and cat_dir.exists():
                normalized = pkg["pip"].lower().replace("-", "_")
                for whl in cat_dir.glob("*.whl"):
                    if whl.name.lower().replace("-", "_").startswith(normalized):
                        whl_size = whl.stat().st_size
                        whl_filename = whl.name
                        whl_mtime = datetime.fromtimestamp(whl.stat().st_mtime).isoformat()
                        break

            if is_cached:
                total_cached += 1
                total_bytes += whl_size
            else:
                total_missing += 1

            inventory.append({
                "pip": pkg["pip"],
                "desc": pkg["desc"],
                "category": cat_key,
                "category_name": cat["name"],
                "target_dir": f"wheels/{cat['dir']}/",
                "status": "CACHED" if is_cached else "MISSING",
                "wheel_file": whl_filename,
                "actual_bytes": whl_size,
                "actual_mb": round(whl_size / (1024 * 1024), 2),
                "last_modified": whl_mtime,
            })

    # 1. Write INDEX.json
    index_data = {
        "version": "1.0.0",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "storage_root": str(TOOLS_ROOT),
        "total_registered": total_cached + total_missing,
        "total_cached": total_cached,
        "total_missing": total_missing,
        "total_cached_mb": round(total_bytes / (1024 * 1024), 2),
        "packages": inventory,
    }
    with open(drive_index_json, "w", encoding="utf-8") as f:
        json.dump(index_data, f, indent=2, ensure_ascii=False)

    # 2. Write INDEX.md
    md_lines = [
        "# DervGen Google Drive ML Toolchain Index (Live Inventory)",
        "",
        f"> **Generated at**: `{index_data['generated_at']}`  ",
        f"> **Status**: **{total_cached} / {total_cached + total_missing}** cached ({index_data['total_cached_mb']:.1f} MB total)",
        "",
    ]

    current_cat = None
    for item in inventory:
        if item["category"] != current_cat:
            current_cat = item["category"]
            cat_def = TOOL_CATEGORIES[current_cat]
            md_lines.append(f"### {cat_def['icon']} Category {current_cat}: {cat_def['name']}")
            md_lines.append("")
            md_lines.append("| Status | Package | Wheel File | Size | Description |")
            md_lines.append("|---|---|---|---|---|")

        badge = "🟢 `CACHED`" if item["status"] == "CACHED" else "⚪ `MISSING`"
        whl_display = f"`{item['wheel_file']}`" if item["wheel_file"] else "—"
        size_display = f"{item['actual_mb']:.1f} MB" if item["status"] == "CACHED" else "—"
        md_lines.append(
            f"| {badge} | **{item['pip']}** | {whl_display} | {size_display} | {item['desc']} |"
        )

    md_lines.extend([
        "",
        "---",
        "## How to Use",
        "```bash",
        "# Download all tool wheels to Drive (default: full preset)",
        "python3 /content/workspace/colab/init_tools.py --preset=full",
        "",
        "# Download LLM fine-tuning tools only",
        "python3 /content/workspace/colab/init_tools.py --preset=llm",
        "",
        "# Download specific categories",
        "python3 /content/workspace/colab/init_tools.py --categories=A,B",
        "",
        "# Install from cached wheels (offline, no network)",
        "python3 /content/workspace/colab/init_tools.py --install",
        "",
        "# Re-sync this Index",
        "python3 /content/workspace/colab/init_tools.py --sync-index",
        "```",
    ])

    with open(drive_index_md, "w", encoding="utf-8") as f:
        f.write("\n".join(md_lines) + "\n")

    print("✅ Synced Google Drive ML Toolchain Index:")
    print(f"   📄 {drive_index_json}")
    print(f"   📄 {drive_index_md} ({total_cached}/{total_cached + total_missing} cached)")


def main():
    parser = argparse.ArgumentParser(
        description="DervGen ML Toolchain Pre-fetcher & Index Sync for Google Drive",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Presets:
  full       All categories (A-F) — complete ML stack
  llm        LLM/VLM fine-tuning & evaluation (A+B+C+E)
  cv         Computer Vision (Lightning + Metrics + timm)
  tabular    Tabular ML (Boosted Trees + Metrics + Optuna)
  eval_only  Evaluation & tracking only (B+C)
  minimal    Bare essentials (Transformers + Accelerate + Metrics + W&B)

Categories:
  A  Training Frameworks & Accelerators
  B  Evaluation & Metrics
  C  Experiment Tracking & Visualization
  D  Gradient-Boosted Trees & Classical ML
  E  Data & Tokenization Utilities
  F  Hyperparameter Optimization
        """,
    )
    parser.add_argument(
        "--preset", default="full",
        choices=list(PRESETS.keys()),
        help="Download preset profile (default: full)",
    )
    parser.add_argument(
        "--categories",
        help="Comma-separated category keys to download (e.g. A,B,C). Overrides --preset.",
    )
    parser.add_argument("--dry-run", action="store_true", help="Print plan without downloading")
    parser.add_argument("--sync-index", action="store_true", help="Only scan and sync INDEX.json & INDEX.md")
    parser.add_argument("--install", action="store_true", help="Install from cached wheels (offline, no network)")
    args = parser.parse_args()

    categories = None
    if args.categories:
        categories = [c.strip().upper() for c in args.categories.split(",")]

    if args.sync_index:
        sync_drive_index()
    elif args.install:
        run_install_from_cache(categories=categories)
    else:
        run_download(
            preset=args.preset,
            categories=categories,
            dry_run=args.dry_run,
        )


if __name__ == "__main__":
    main()
