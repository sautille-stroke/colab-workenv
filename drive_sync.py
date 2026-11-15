#!/usr/bin/env python3
"""
DervGen Workspace: Smart Google Drive Backup & Synchronization
Safely syncs critical files, notebooks, and outputs between Colab and Google Drive.
"""

import os
import shutil
import sys
from pathlib import Path
from datetime import datetime

DRIVE_BASE = Path("/content/drive/MyDrive/dervgen/cache/backups")
WORKSPACE_ROOT = Path(os.environ.get("WORKSPACE_ROOT", "/content/dervgen/all-overview"))

EXCLUDE_PATTERNS = {
    ".git",
    "__pycache__",
    ".ipynb_checkpoints",
    "bazel-*",
    ".cache",
    ".pytest_cache",
    "venv",
    ".venv",
}


def is_excluded(path: Path) -> bool:
    for part in path.parts:
        if part in EXCLUDE_PATTERNS:
            return True
    return False


def backup_to_drive(dest_folder: Path = DRIVE_BASE) -> None:
    if not Path("/content/drive/MyDrive").exists():
        print("[Drive Sync Error] Google Drive is not mounted at /content/drive/MyDrive.")
        print("Please run drive.mount('/content/drive') first.")
        sys.exit(1)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    dest_dir = dest_folder / "latest"
    dest_dir.mkdir(parents=True, exist_ok=True)

    print(f"[Drive Sync] Starting backup from {WORKSPACE_ROOT} to {dest_dir}...")
    copied_count = 0

    for root, dirs, files in os.walk(WORKSPACE_ROOT):
        # Modify dirs in-place to avoid descending into excluded directories
        dirs[:] = [d for d in dirs if d not in EXCLUDE_PATTERNS]

        rel_dir = Path(root).relative_to(WORKSPACE_ROOT)
        target_dir = dest_dir / rel_dir
        target_dir.mkdir(parents=True, exist_ok=True)

        for file in files:
            source_file = Path(root) / file
            if source_file.suffix in {".pyc", ".pyo", ".so"}:
                continue
            dest_file = target_dir / file
            shutil.copy2(source_file, dest_file)
            copied_count += 1

    print(f"[Drive Sync] Backup complete! Synced {copied_count} files to Google Drive ({dest_dir}).")


if __name__ == "__main__":
    backup_to_drive()
