#!/usr/bin/env python3
"""
DervGen Google Drive V1 → V2.0 Migration Script
=================================================
Restructures the existing /dervgen/ directory on Google Drive to conform to
the SSOT V2.0 standard defined in:
  architecture/google-colab-and-drive-standards.md

Migration actions:
  1. Move /dervgen/model/{usage}/  →  /dervgen/data/models/{usage}/
  2. Move /dervgen/workspace/      →  /dervgen/work/
  3. Move /dervgen/bundles/        →  (archive or delete)
  4. Move MyDrive/DervGen_Workspace_Backup  →  /dervgen/cache/backups
  5. Create all missing V2.0 standard directories
  6. Clean up empty V1 directories
  7. Generate migration report

Safety:
  - Default mode is --dry-run (preview only, no changes)
  - Pass --execute to actually perform the migration
  - All moves use shutil.move (atomic within same filesystem)
  - Nothing is deleted without --prune flag

Usage:
  # In Google Colab (after mounting Drive):
  python migrate_drive_v1_to_v2.py              # Dry run: preview changes
  python migrate_drive_v1_to_v2.py --execute    # Apply migration
  python migrate_drive_v1_to_v2.py --execute --prune  # Apply + remove empty V1 dirs
"""

import os
import sys
import json
import shutil
import argparse
from pathlib import Path
from datetime import datetime, timezone

# Safe utf-8 stdout for terminals
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
DRIVE_ROOT = Path(os.environ.get("DERVGEN_DRIVE_ROOT", "/content/drive/MyDrive/dervgen"))
MYDRIVE = DRIVE_ROOT.parent  # /content/drive/MyDrive

# V2.0 Standard directories (from architecture spec)
V2_MODEL_USAGES = [
    "3d_recon", "texture_gen", "video_gen", "actor_dynamics",
    "audio_foley", "foundation", "denoise_upscale",
]

V2_DATA_DIRS = ["benchmarks", "evaluations", "captures", "raw"]

V2_TOOL_DIRS = [
    "wheels/A_training", "wheels/B_evaluation", "wheels/C_tracking",
    "wheels/D_classical", "wheels/E_data", "wheels/F_hpo", "bin",
]

V2_CACHE_DIRS = ["bazel", "huggingface", "pip"]

# V1 remnants to detect
V1_MODEL_DIR = DRIVE_ROOT / "model"           # old: /dervgen/model/
V1_WORKSPACE_DIR = DRIVE_ROOT / "workspace"   # old: /dervgen/workspace/
V1_BUNDLES_DIR = DRIVE_ROOT / "bundles"       # old: /dervgen/bundles/
V1_BACKUP_DIR = MYDRIVE / "DervGen_Workspace_Backup"  # root clutter

# V2 targets
V2_MODELS_DIR = DRIVE_ROOT / "data" / "models"
V2_WORK_DIR = DRIVE_ROOT / "work"
V2_BACKUPS_DIR = DRIVE_ROOT / "cache" / "backups"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
class MigrationPlan:
    """Collects planned actions for preview and execution."""

    def __init__(self):
        self.moves = []       # (src, dst, description)
        self.creates = []     # (path, description)
        self.deletes = []     # (path, description)
        self.warnings = []    # free-text warnings
        self.already_ok = []  # things that are already V2-compliant

    def move(self, src: Path, dst: Path, desc: str):
        self.moves.append((src, dst, desc))

    def create(self, path: Path, desc: str):
        self.creates.append((path, desc))

    def delete(self, path: Path, desc: str):
        self.deletes.append((path, desc))

    def warn(self, msg: str):
        self.warnings.append(msg)

    def ok(self, msg: str):
        self.already_ok.append(msg)


def dir_summary(path: Path) -> str:
    """Returns a short summary of a directory's contents."""
    if not path.exists():
        return "(does not exist)"
    items = list(path.iterdir())
    files = [i for i in items if i.is_file()]
    dirs = [i for i in items if i.is_dir()]
    total_bytes = sum(f.stat().st_size for f in files)
    total_mb = total_bytes / (1024 * 1024)
    return f"{len(dirs)} dirs, {len(files)} files ({total_mb:.1f} MB)"


def dir_tree(path: Path, prefix: str = "", max_depth: int = 2, _depth: int = 0) -> list:
    """Returns a list of strings representing a directory tree."""
    if not path.exists() or _depth >= max_depth:
        return []
    lines = []
    items = sorted(path.iterdir(), key=lambda x: (x.is_file(), x.name))
    for i, item in enumerate(items):
        is_last = (i == len(items) - 1)
        connector = "└── " if is_last else "├── "
        if item.is_dir():
            sub_summary = dir_summary(item)
            lines.append(f"{prefix}{connector}{item.name}/  [{sub_summary}]")
            extension = "    " if is_last else "│   "
            lines.extend(dir_tree(item, prefix + extension, max_depth, _depth + 1))
        else:
            size_mb = item.stat().st_size / (1024 * 1024)
            lines.append(f"{prefix}{connector}{item.name}  ({size_mb:.1f} MB)")
    return lines


# ---------------------------------------------------------------------------
# Planning Phase
# ---------------------------------------------------------------------------
def plan_migration(plan: MigrationPlan, prune: bool = False):
    """Scans the current Drive structure and builds a migration plan."""

    print("=" * 70)
    print("  DervGen Drive Migration Planner: V1 → V2.0")
    print(f"  Drive Root: {DRIVE_ROOT}")
    print(f"  Timestamp:  {datetime.now(timezone.utc).isoformat()}")
    print("=" * 70)

    # --- Check Drive is accessible ---
    if not DRIVE_ROOT.parent.exists() and not os.environ.get("DERVGEN_DRIVE_ROOT"):
        plan.warn("Google Drive is NOT mounted. Mount it first:\n"
                  "  from google.colab import drive; drive.mount('/content/drive')")
        return

    # ---- 1. model/ → data/models/ ----
    if V1_MODEL_DIR.exists() and V1_MODEL_DIR.is_dir():
        for child in sorted(V1_MODEL_DIR.iterdir()):
            if child.is_dir():
                dest = V2_MODELS_DIR / child.name
                if dest.exists():
                    # Merge: move contents one level deeper
                    for item in child.iterdir():
                        item_dest = dest / item.name
                        if item_dest.exists():
                            plan.warn(f"CONFLICT: Both {item} and {item_dest} exist — skipping")
                        else:
                            plan.move(item, item_dest,
                                      f"Merge model/{child.name}/{item.name} → data/models/{child.name}/{item.name}")
                else:
                    plan.move(child, dest,
                              f"Move model/{child.name}/ → data/models/{child.name}/")
            elif child.is_file():
                # Files at model/ root (like INDEX.json, INDEX.md)
                dest = V2_MODELS_DIR / child.name
                plan.move(child, dest, f"Move model/{child.name} → data/models/{child.name}")

        if prune:
            plan.delete(V1_MODEL_DIR, "Remove empty V1 model/ directory")
    elif V1_MODEL_DIR.exists():
        plan.warn(f"V1 model/ exists but is not a directory: {V1_MODEL_DIR}")
    else:
        plan.ok("No V1 model/ directory found (already migrated or never created)")

    # ---- 2. workspace/ → work/ ----
    if V1_WORKSPACE_DIR.exists() and V1_WORKSPACE_DIR.is_dir():
        summary = dir_summary(V1_WORKSPACE_DIR)
        if V2_WORK_DIR.exists():
            # Merge contents
            for child in sorted(V1_WORKSPACE_DIR.iterdir()):
                dest = V2_WORK_DIR / child.name
                if dest.exists():
                    plan.warn(f"CONFLICT: Both workspace/{child.name} and work/{child.name} exist — skipping")
                else:
                    plan.move(child, dest, f"Move workspace/{child.name} → work/{child.name}")
        else:
            plan.move(V1_WORKSPACE_DIR, V2_WORK_DIR,
                      f"Move workspace/ → work/  [{summary}]")
        if prune and V1_WORKSPACE_DIR != V2_WORK_DIR:
            plan.delete(V1_WORKSPACE_DIR, "Remove empty V1 workspace/ directory")
    else:
        plan.ok("No V1 workspace/ directory found")

    # ---- 3. bundles/ → archive or remove ----
    if V1_BUNDLES_DIR.exists():
        summary = dir_summary(V1_BUNDLES_DIR)
        items = list(V1_BUNDLES_DIR.iterdir())
        if len(items) == 0:
            plan.delete(V1_BUNDLES_DIR, "Remove empty V1 bundles/ directory")
        else:
            archive_dest = DRIVE_ROOT / "cache" / "_archived_v1_bundles"
            plan.move(V1_BUNDLES_DIR, archive_dest,
                      f"Archive bundles/ → cache/_archived_v1_bundles/  [{summary}]")
            plan.warn("V1 bundles/ had content — archived to cache/_archived_v1_bundles/. "
                      "Review and delete manually when safe.")
    else:
        plan.ok("No V1 bundles/ directory found")

    # ---- 4. DervGen_Workspace_Backup → dervgen/cache/backups ----
    if V1_BACKUP_DIR.exists():
        summary = dir_summary(V1_BACKUP_DIR)
        plan.move(V1_BACKUP_DIR, V2_BACKUPS_DIR,
                  f"Move MyDrive/DervGen_Workspace_Backup → dervgen/cache/backups  [{summary}]")
    else:
        plan.ok("No root-level DervGen_Workspace_Backup clutter found")

    # ---- 5. Other root-level clutter detection ----
    if MYDRIVE.exists():
        known_root_items = {"dervgen", "Colab Notebooks"}  # expected items
        for item in sorted(MYDRIVE.iterdir()):
            if item.name.startswith("DervGen") or item.name.startswith("dervgen_"):
                if item != DRIVE_ROOT and item.name not in known_root_items:
                    plan.warn(f"Root clutter detected: MyDrive/{item.name} — "
                              f"violates Zero Clutter rule, consider removing")

    # ---- 6. Create missing V2.0 standard directories ----
    v2_dirs = []

    # data/models/{usage}/
    for usage in V2_MODEL_USAGES:
        v2_dirs.append((DRIVE_ROOT / "data" / "models" / usage, f"data/models/{usage}/"))

    # data/{category}/
    for cat in V2_DATA_DIRS:
        v2_dirs.append((DRIVE_ROOT / "data" / cat, f"data/{cat}/"))

    # tools/
    for td in V2_TOOL_DIRS:
        v2_dirs.append((DRIVE_ROOT / "tools" / td, f"tools/{td}/"))

    # cache/
    for cd in V2_CACHE_DIRS:
        v2_dirs.append((DRIVE_ROOT / "cache" / cd, f"cache/{cd}/"))

    # work/
    v2_dirs.append((DRIVE_ROOT / "work", "work/"))

    for dirpath, label in v2_dirs:
        if not dirpath.exists():
            plan.create(dirpath, f"Create {label}")
        else:
            plan.ok(f"{label} already exists")


# ---------------------------------------------------------------------------
# Execution Phase
# ---------------------------------------------------------------------------
def execute_plan(plan: MigrationPlan, dry_run: bool = True):
    """Prints and optionally executes the migration plan."""

    mode = "DRY RUN" if dry_run else "EXECUTING"
    print(f"\n{'=' * 70}")
    print(f"  Migration Plan — {mode}")
    print(f"{'=' * 70}")

    # Warnings
    if plan.warnings:
        print(f"\n⚠️  WARNINGS ({len(plan.warnings)}):")
        for w in plan.warnings:
            print(f"  ⚠️  {w}")

    # Already OK
    if plan.already_ok:
        print(f"\n✅ Already V2.0 Compliant ({len(plan.already_ok)}):")
        for msg in plan.already_ok:
            print(f"  ✓ {msg}")

    # Moves
    if plan.moves:
        print(f"\n📦 MOVES ({len(plan.moves)}):")
        for src, dst, desc in plan.moves:
            print(f"  → {desc}")
            print(f"    FROM: {src}")
            print(f"    TO:   {dst}")
            if not dry_run:
                dst.parent.mkdir(parents=True, exist_ok=True)
                if src.exists():
                    shutil.move(str(src), str(dst))
                    print(f"    ✓ Done")
                else:
                    print(f"    ⚠️ Source no longer exists, skipping")

    # Creates
    if plan.creates:
        print(f"\n📁 CREATES ({len(plan.creates)}):")
        for path, desc in plan.creates:
            print(f"  + {desc}")
            if not dry_run:
                path.mkdir(parents=True, exist_ok=True)

    # Deletes
    if plan.deletes:
        print(f"\n🗑️  DELETES ({len(plan.deletes)}):")
        for path, desc in plan.deletes:
            print(f"  - {desc}")
            if not dry_run:
                if path.exists():
                    if path.is_dir():
                        # Only remove if empty
                        try:
                            path.rmdir()
                            print(f"    ✓ Removed empty directory")
                        except OSError:
                            print(f"    ⚠️ Directory not empty after migration, keeping")
                    else:
                        path.unlink()

    # Summary
    total_actions = len(plan.moves) + len(plan.creates) + len(plan.deletes)
    print(f"\n{'=' * 70}")
    if dry_run:
        print(f"  DRY RUN COMPLETE — {total_actions} actions planned")
        print(f"  To apply: python {Path(__file__).name} --execute")
        if plan.deletes:
            print(f"  To apply + cleanup: python {Path(__file__).name} --execute --prune")
    else:
        print(f"  MIGRATION COMPLETE — {total_actions} actions executed")
    print(f"{'=' * 70}")

    # Write migration log
    if not dry_run:
        log_path = DRIVE_ROOT / "cache" / "migration_v1_to_v2.json"
        log_path.parent.mkdir(parents=True, exist_ok=True)
        log = {
            "version": "2.0.0",
            "migrated_at": datetime.now(timezone.utc).isoformat(),
            "moves": [{"from": str(s), "to": str(d), "desc": desc} for s, d, desc in plan.moves],
            "creates": [{"path": str(p), "desc": desc} for p, desc in plan.creates],
            "deletes": [{"path": str(p), "desc": desc} for p, desc in plan.deletes],
            "warnings": plan.warnings,
        }
        with open(log_path, "w", encoding="utf-8") as f:
            json.dump(log, f, indent=2, ensure_ascii=False)
        print(f"\n📄 Migration log saved to: {log_path}")


# ---------------------------------------------------------------------------
# Pre-flight: show current state
# ---------------------------------------------------------------------------
def show_current_state():
    """Prints the current Drive directory tree for visual inspection."""
    print(f"\n{'=' * 70}")
    print(f"  Current Drive State: {DRIVE_ROOT}")
    print(f"{'=' * 70}")

    if not DRIVE_ROOT.exists():
        print("  (Drive root does not exist yet)")
        return

    tree = dir_tree(DRIVE_ROOT, max_depth=2)
    print(f"  {DRIVE_ROOT.name}/")
    for line in tree:
        print(f"  {line}")

    # Check for root clutter
    if MYDRIVE.exists():
        clutter = [i.name for i in MYDRIVE.iterdir()
                    if i.name.startswith("DervGen") or i.name.startswith("dervgen_")]
        if clutter:
            print(f"\n  ⚠️ Root-level clutter in MyDrive: {clutter}")

    # V1 remnant detection summary
    v1_found = []
    if V1_MODEL_DIR.exists():
        v1_found.append(f"model/  [{dir_summary(V1_MODEL_DIR)}]")
    if V1_WORKSPACE_DIR.exists():
        v1_found.append(f"workspace/  [{dir_summary(V1_WORKSPACE_DIR)}]")
    if V1_BUNDLES_DIR.exists():
        v1_found.append(f"bundles/  [{dir_summary(V1_BUNDLES_DIR)}]")
    if V1_BACKUP_DIR.exists():
        v1_found.append(f"MyDrive/DervGen_Workspace_Backup  [{dir_summary(V1_BACKUP_DIR)}]")

    if v1_found:
        print(f"\n  🔍 V1 Remnants Detected ({len(v1_found)}):")
        for r in v1_found:
            print(f"    • {r}")
    else:
        print(f"\n  ✅ No V1 remnants detected — Drive appears V2.0 compliant")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main():
    parser = argparse.ArgumentParser(
        description="Migrate DervGen Google Drive from V1 to V2.0 directory structure",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python migrate_drive_v1_to_v2.py                  # Preview changes (dry run)
  python migrate_drive_v1_to_v2.py --execute         # Apply migration
  python migrate_drive_v1_to_v2.py --execute --prune  # Apply + remove empty V1 dirs
  python migrate_drive_v1_to_v2.py --show-state       # Just show current Drive tree
        """
    )
    parser.add_argument(
        "--execute", action="store_true",
        help="Actually perform the migration (default is dry-run preview)"
    )
    parser.add_argument(
        "--prune", action="store_true",
        help="Remove empty V1 directories after migration (requires --execute)"
    )
    parser.add_argument(
        "--show-state", action="store_true",
        help="Only show current Drive directory tree and exit"
    )
    args = parser.parse_args()

    if args.show_state:
        show_current_state()
        return

    show_current_state()

    plan = MigrationPlan()
    plan_migration(plan, prune=args.prune)
    execute_plan(plan, dry_run=not args.execute)


if __name__ == "__main__":
    main()
