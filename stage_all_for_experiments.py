#!/usr/bin/env python3
"""
DervGen Workspace: Master Staging Script for Cloud Experiments
One command sets up:
  1. Google Drive Directory Structure (/dervgen/{data, tools, cache, work})
  2. Benchmark Datasets (Cornell Box, geometries, capture manifests)
  3. Experiment Workspaces (exp01_image_to_quad_3d .. exp05_bidirectional_closed_loop)
  4. Curated Model Weights (fast ~2.6GB, P0 ~26.5GB, or P1/all)
  5. Live Google Drive Indexes (data/models/INDEX.md, data/INDEX.md)
"""

import os
import sys
import argparse
from pathlib import Path

# Safe utf-8 stdout for terminals
if hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

import drive_manager
import init_datasets
import init_experiments
import init_models

DRIVE_ROOT = Path(os.environ.get("DERVGEN_DRIVE_ROOT", "/content/drive/MyDrive/dervgen"))


def check_drive_mounted() -> bool:
    drive_base = Path("/content/drive/MyDrive")
    if not drive_base.exists() and not os.environ.get("DERVGEN_DRIVE_ROOT"):
        print("⚠️  [Stage All] Google Drive is NOT mounted at /content/drive/MyDrive.")
        print("    In Google Colab, execute:")
        print("    from google.colab import drive; drive.mount('/content/drive')")
        return False
    return True


def stage_everything(preset: str = "fast", dry_run: bool = False, skip_models: bool = False):
    print("==========================================================================")
    print(f" 🚀 DervGen Cloud Staging Controller (Drive: {DRIVE_ROOT})")
    print(f" Preset: [{preset}], Dry Run: [{dry_run}], Skip Models: [{skip_models}]")
    print("==========================================================================")

    if not check_drive_mounted():
        return False

    # 1. Drive Directory Layout
    print("\n[Step 1/4] Initializing Cloud Directory Structure...")
    drive_manager.init_drive_structure()

    # 2. Benchmark Datasets
    print("\n[Step 2/4] Initializing Benchmark Datasets & Geometries...")
    init_datasets.setup_all_datasets()

    # 3. Experiment Workspaces
    print("\n[Step 3/4] Initializing RFC 0039 Experiment Workspaces...")
    init_experiments.setup_all_experiments()

    # 4. Model Pre-fetcher
    if not skip_models:
        print(f"\n[Step 4/4] Staging Model Weights (Preset: {preset})...")
        init_models.run_init(preset=preset, dry_run=dry_run)
    else:
        print("\n[Step 4/4] Skipping model weight downloads as requested.")
        init_models.sync_drive_index()

    print("\n==========================================================================")
    print(f"🎉 All experiment assets, models, and workspaces are staged in Google Drive!")
    print(f"   Root: {DRIVE_ROOT}")
    print(f"   📄 Model Index:     {DRIVE_ROOT}/data/models/INDEX.md")
    print(f"   📄 Dataset Index:   {DRIVE_ROOT}/data/INDEX.md")
    print(f"   📄 Work Index:      {DRIVE_ROOT}/work/")
    print("==========================================================================")
    return True


def main():
    parser = argparse.ArgumentParser(description="DervGen Master Cloud Staging for Google Drive")
    parser.add_argument("--preset", default="fast", choices=["fast", "P0", "P1", "all"],
                        help="Model preset: fast (~2.6GB, 1 min), P0 (~26.5GB, core), all")
    parser.add_argument("--dry-run", action="store_true", help="Simulate staging without downloading weights")
    parser.add_argument("--skip-models", action="store_true", help="Stage directories, data and workspaces without downloading weights")
    args = parser.parse_args()

    stage_everything(preset=args.preset, dry_run=args.dry_run, skip_models=args.skip_models)


if __name__ == "__main__":
    main()
