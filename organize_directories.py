#!/usr/bin/env python3
"""
DervGen Storage SSOT V2.1: Universal Directory Organizer & Migration Tool
==========================================================================
Organizes and restructures the /dervgen/ storage root to strictly conform to
the latest SSOT V2.1 specification (Domain-Driven Architecture):
  - architecture/google-colab-and-drive-standards.md
  - architecture/resources.md
  - RESOURCES.md

Architecture Layout (5 Pillars):
--------------------------------
/dervgen/ (or /content/drive/MyDrive/dervgen, or DERVGEN_DRIVE_ROOT)
├── 📦 data/               # Domain-Driven Data Hub (6 Core Domains + 1 Foundation)
│   ├── common/            # Cross-Domain: foundations, hdri, captures
│   ├── llm/               # Language & Reasoning: weights, adapters, embeddings, benchmarks
│   ├── video/             # Video & Neural Render: base_models, neural_render, loras
│   ├── cg/                # Computer Graphics: scenes, models, materials, denoisers, references
│   ├── 3d/                # Spatial 3D & Recon: recon, textures, evaluations (SWE-bench for 3D)
│   ├── anim/              # Animation & Dynamics: mocap, facial, rigs
│   └── audio/             # Audio & Foley: speech, foley, spatial
├── 🛠️ tools/              # Immutable Toolchains: wheels (A-F), bin
├── ⚡ cache/              # Persistent Caches: bazel, huggingface, pip, backups
├── 🚀 work/               # Dynamic Workspaces: {user}/{repo}/{date}/{job_id}/
└── 💻 repo/               # Code Repositories: all-overview, caelum-core, fulgur, etc.
                           # e.g., /dervgen/repo/all-overview

Migration & Reorganization Capabilities:
----------------------------------------
1. V1 Legacy:
   - model/{usage}/         → data/3d/recon, data/cg/denoisers, data/common/foundations, etc.
   - workspace/             → work/
   - bundles/               → cache/_archived_v1_bundles/ (or remove if empty)
   - MyDrive/DervGen_*      → cache/backups/ (Zero Clutter rule enforcement)
2. V2.0 Legacy:
   - data/models/{usage}/   → domain-driven target under data/{domain}/{sub}/
   - data/benchmarks/scenes → data/cg/scenes/
   - data/benchmarks/primitives → data/cg/models/
   - data/benchmarks/hdri   → data/common/hdri/
   - data/benchmarks/measured_brdf → data/cg/materials/
   - data/evaluations/      → data/3d/evaluations/
   - data/captures/         → data/common/captures/
3. Repository Layout:
   - repos/ (plural)        → repo/ (singular)
   - Ensures repo/all-overview exists or stages current repository
4. Safety & Idempotence:
   - Dry-run preview by default (no changes without --execute)
   - Recursive directory merge on target collision, zero destructive overwrite
   - Optional --prune to clean empty legacy folders bottom-up
   - Audit report exported to cache/organize_report.json

Usage:
------
  # 1. Preview changes (Safe dry-run):
  python organize_directories.py

  # 2. Apply directory organization:
  python organize_directories.py --execute

  # 3. Apply + clean up empty legacy folders:
  python organize_directories.py --execute --prune

  # 4. Initialize clean standard V2.1 structure:
  python organize_directories.py --execute --init-only

  # 5. Stage specific local repository into /dervgen/repo/<name>:
  python organize_directories.py --execute --stage-repo /path/to/all-overview

  # 6. View current directory tree & compliance scorecard:
  python organize_directories.py --show-state
"""

import os
import sys
import json
import shutil
import argparse
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, List, Tuple, Optional, Any

# Safe UTF-8 stdout for terminals (Windows / Linux / macOS)
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass


# ==============================================================================
# Domain Specifications (SSOT V2.1)
# ==============================================================================

# 6 Core Domains + 1 Common Foundation
DOMAIN_SUBDIRECTORIES: Dict[str, List[str]] = {
    "common": ["foundations", "hdri", "captures"],
    "llm": ["weights", "adapters", "embeddings", "benchmarks"],
    "video": ["base_models", "neural_render", "loras"],
    "cg": ["scenes", "models", "materials", "denoisers", "references"],
    "3d": ["recon", "textures", "evaluations"],
    "anim": ["mocap", "facial", "rigs"],
    "audio": ["speech", "foley", "spatial"],
}

# Immutable Tools Structure
TOOL_SUBDIRECTORIES: List[str] = [
    "wheels/A_training",
    "wheels/B_evaluation",
    "wheels/C_tracking",
    "wheels/D_classical",
    "wheels/E_data",
    "wheels/F_hpo",
    "bin",
]

# Persistent Cache Structure
CACHE_SUBDIRECTORIES: List[str] = [
    "bazel",
    "huggingface",
    "pip",
    "backups",
]

# Code Repository Staging (e.g. /dervgen/repo/all-overview)
DEFAULT_REPOS: List[str] = [
    "all-overview",
]

# Mapping from V1/V2.0 legacy model usages to SSOT V2.1 domain paths
LEGACY_MODEL_USAGE_MAP: Dict[str, Tuple[str, str]] = {
    "3d_recon": ("3d", "recon"),
    "texture_gen": ("3d", "textures"),
    "video_gen": ("video", "base_models"),
    "actor_dynamics": ("anim", "mocap"),
    "audio_foley": ("audio", "foley"),
    "foundation": ("common", "foundations"),
    "denoise_upscale": ("cg", "denoisers"),
}


# ==============================================================================
# Helper Classes & Utilities
# ==============================================================================

class OrganizationPlan:
    """Collects and reports planned filesystem operations."""

    def __init__(self, root: Path):
        self.root = root
        self.moves: List[Tuple[Path, Path, str]] = []       # (src, dst, description)
        self.creates: List[Tuple[Path, str]] = []           # (path, description)
        self.deletes: List[Tuple[Path, str]] = []           # (path, description)
        self.stages: List[Tuple[Path, Path, str]] = []      # (src, dst, description)
        self.warnings: List[str] = []                       # Non-fatal warnings / conflicts
        self.compliant_items: List[str] = []                # Already conforming paths

    def add_move(self, src: Path, dst: Path, desc: str):
        self.moves.append((src, dst, desc))

    def add_create(self, path: Path, desc: str):
        self.creates.append((path, desc))

    def add_delete(self, path: Path, desc: str):
        self.deletes.append((path, desc))

    def add_stage(self, src: Path, dst: Path, desc: str):
        self.stages.append((src, dst, desc))

    def warn(self, msg: str):
        self.warnings.append(msg)

    def ok(self, msg: str):
        self.compliant_items.append(msg)

    @property
    def total_actions(self) -> int:
        return len(self.moves) + len(self.creates) + len(self.deletes) + len(self.stages)


def get_default_drive_root() -> Path:
    """Resolves standard storage root path across platforms."""
    env_root = os.environ.get("DERVGEN_DRIVE_ROOT")
    if env_root:
        return Path(env_root).resolve()

    # Colab environment standard path
    colab_drive = Path("/content/drive/MyDrive/dervgen")
    if colab_drive.parent.exists():
        return colab_drive

    # Local development Windows/Linux fallback
    local_dervgen = Path("H:/dervgen")
    if local_dervgen.exists():
        return local_dervgen

    # Default to current directory's dervgen or /dervgen
    if os.name == "nt":
        return Path("C:/dervgen")
    return Path("/dervgen")


def dir_summary(path: Path) -> str:
    """Returns human-readable summary of directory items and size."""
    if not path.exists():
        return "(does not exist)"
    try:
        items = list(path.iterdir())
        files = [i for i in items if i.is_file()]
        dirs = [i for i in items if i.is_dir()]
        total_bytes = sum(f.stat().st_size for f in files if f.exists())
        total_mb = total_bytes / (1024 * 1024)
        return f"{len(dirs)} dirs, {len(files)} files ({total_mb:.1f} MB)"
    except Exception as e:
        return f"(error: {e})"


def dir_tree(path: Path, prefix: str = "", max_depth: int = 2, _depth: int = 0) -> List[str]:
    """Builds a formatted string list representing directory hierarchy."""
    if not path.exists() or _depth >= max_depth:
        return []
    lines = []
    try:
        items = sorted(path.iterdir(), key=lambda x: (x.is_file(), x.name))
        for i, item in enumerate(items):
            is_last = (i == len(items) - 1)
            connector = "└── " if is_last else "├── "
            if item.is_dir():
                sub_sum = dir_summary(item)
                lines.append(f"{prefix}{connector}{item.name}/  [{sub_sum}]")
                ext = "    " if is_last else "│   "
                lines.extend(dir_tree(item, prefix + ext, max_depth, _depth + 1))
            else:
                try:
                    size_mb = item.stat().st_size / (1024 * 1024)
                    lines.append(f"{prefix}{connector}{item.name}  ({size_mb:.2f} MB)")
                except Exception:
                    lines.append(f"{prefix}{connector}{item.name}")
    except Exception as e:
        lines.append(f"{prefix}└── [error reading directory: {e}]")
    return lines


# ==============================================================================
# Planning Phase
# ==============================================================================

def plan_organization(
    root: Path,
    plan: OrganizationPlan,
    prune: bool = False,
    stage_repo_path: Optional[Path] = None,
    init_only: bool = False,
):
    """Scans storage root and generates comprehensive organization plan."""
    mydrive = root.parent

    # 1. Zero Clutter Detection in MyDrive
    if mydrive.exists() and mydrive.name == "MyDrive":
        known_allowed = {"dervgen", "Colab Notebooks"}
        for item in sorted(mydrive.iterdir()):
            if item.name.startswith("DervGen") or item.name.startswith("dervgen_"):
                if item != root and item.name not in known_allowed:
                    if item.name == "DervGen_Workspace_Backup":
                        target_backup = root / "cache" / "backups" / "DervGen_Workspace_Backup"
                        plan.add_move(
                            item, target_backup,
                            f"Move legacy backup MyDrive/{item.name} → cache/backups/ (Zero Clutter)"
                        )
                    else:
                        plan.warn(
                            f"Zero Clutter Violation: MyDrive/{item.name} detected outside /dervgen/."
                        )

    # If --init-only is requested, skip migration scanning and just generate canonical dirs
    if not init_only:
        _plan_v1_migrations(root, plan, prune)
        _plan_v2_data_domain_migrations(root, plan, prune)
        _plan_repo_migrations(root, plan, prune)

    # 2. Stage Requested or Current Repository into repo/
    _plan_repository_staging(root, plan, stage_repo_path)

    # 3. Create All Missing SSOT V2.1 Canonical Directories
    _plan_canonical_directories(root, plan)


def _plan_v1_migrations(root: Path, plan: OrganizationPlan, prune: bool):
    """Detects and plans migration for legacy V1 directories."""
    # V1: model/ -> data/{domain}/{sub}/
    v1_model = root / "model"
    if v1_model.exists() and v1_model.is_dir():
        for child in sorted(v1_model.iterdir()):
            if child.is_dir():
                domain, sub = LEGACY_MODEL_USAGE_MAP.get(child.name, ("common", f"legacy_{child.name}"))
                target = root / "data" / domain / sub
                for item in sorted(child.iterdir()):
                    _merge_or_move(item, target / item.name, f"V1 model/{child.name}/{item.name} → data/{domain}/{sub}/{item.name}", plan)
                if prune:
                    plan.add_delete(child, f"Prune empty V1 model/{child.name}/")
            elif child.is_file():
                target = root / "data" / "common" / child.name
                _merge_or_move(child, target, f"V1 model/{child.name} → data/common/{child.name}", plan)
        if prune:
            plan.add_delete(v1_model, "Prune empty legacy V1 model/ directory")

    # V1: workspace/ -> work/
    v1_workspace = root / "workspace"
    if v1_workspace.exists() and v1_workspace.is_dir():
        target_work = root / "work"
        for child in sorted(v1_workspace.iterdir()):
            _merge_or_move(child, target_work / child.name, f"V1 workspace/{child.name} → work/{child.name}", plan)
        if prune:
            plan.add_delete(v1_workspace, "Prune empty legacy V1 workspace/ directory")

    # V1: bundles/ -> archive
    v1_bundles = root / "bundles"
    if v1_bundles.exists() and v1_bundles.is_dir():
        items = list(v1_bundles.iterdir())
        if len(items) == 0:
            if prune:
                plan.add_delete(v1_bundles, "Prune empty legacy V1 bundles/ directory")
        else:
            target_archive = root / "cache" / "_archived_v1_bundles"
            _merge_or_move(v1_bundles, target_archive, "Archive legacy V1 bundles/ → cache/_archived_v1_bundles/", plan)
            plan.warn("V1 bundles/ had active content. Archived to cache/_archived_v1_bundles/.")


def _plan_v2_data_domain_migrations(root: Path, plan: OrganizationPlan, prune: bool):
    """Migrates V2.0 fragmented data/ directories to V2.1 Domain-Driven layout."""
    data_dir = root / "data"
    if not data_dir.exists() or not data_dir.is_dir():
        return

    # A. Migrate data/models/{usage}/ -> data/{domain}/{sub}/
    v2_models = data_dir / "models"
    if v2_models.exists() and v2_models.is_dir():
        for child in sorted(v2_models.iterdir()):
            if child.is_dir():
                domain, sub = LEGACY_MODEL_USAGE_MAP.get(child.name, ("common", f"models_{child.name}"))
                target = data_dir / domain / sub
                for item in sorted(child.iterdir()):
                    _merge_or_move(item, target / item.name, f"V2.0 data/models/{child.name}/{item.name} → data/{domain}/{sub}/{item.name}", plan)
                if prune:
                    plan.add_delete(child, f"Prune empty V2.0 data/models/{child.name}/")
            elif child.is_file():
                target = data_dir / "common" / child.name
                _merge_or_move(child, target, f"V2.0 data/models/{child.name} → data/common/{child.name}", plan)
        if prune:
            plan.add_delete(v2_models, "Prune empty V2.0 data/models/ directory")

    # B. Migrate data/benchmarks/ -> data/cg/scenes, data/cg/models, data/common/hdri, etc.
    v2_benchmarks = data_dir / "benchmarks"
    if v2_benchmarks.exists() and v2_benchmarks.is_dir():
        # 1. scenes/ -> data/cg/scenes/
        scenes_dir = v2_benchmarks / "scenes"
        if scenes_dir.exists():
            target_scenes = data_dir / "cg" / "scenes"
            industry = scenes_dir / "industry"
            if industry.exists() and industry.is_dir():
                # Unnest industry folder directly into cg/scenes/
                for item in sorted(industry.iterdir()):
                    _merge_or_move(item, target_scenes / item.name, f"Benchmark scene {item.name} → data/cg/scenes/{item.name}", plan)
                if prune:
                    plan.add_delete(industry, "Prune empty data/benchmarks/scenes/industry/")
            for item in sorted(scenes_dir.iterdir()):
                if item.name != "industry":
                    _merge_or_move(item, target_scenes / item.name, f"Benchmark scene {item.name} → data/cg/scenes/{item.name}", plan)
            if prune:
                plan.add_delete(scenes_dir, "Prune empty data/benchmarks/scenes/")

        # 2. primitives/ -> data/cg/models/
        primitives_dir = v2_benchmarks / "primitives"
        if primitives_dir.exists():
            target_models = data_dir / "cg" / "models"
            for item in sorted(primitives_dir.iterdir()):
                _merge_or_move(item, target_models / item.name, f"data/benchmarks/primitives/{item.name} → data/cg/models/{item.name}", plan)
            if prune:
                plan.add_delete(primitives_dir, "Prune empty data/benchmarks/primitives/")

        # 3. hdri/ -> data/common/hdri/
        hdri_dir = v2_benchmarks / "hdri"
        if hdri_dir.exists():
            target_hdri = data_dir / "common" / "hdri"
            for item in sorted(hdri_dir.iterdir()):
                _merge_or_move(item, target_hdri / item.name, f"data/benchmarks/hdri/{item.name} → data/common/hdri/{item.name}", plan)
            if prune:
                plan.add_delete(hdri_dir, "Prune empty data/benchmarks/hdri/")

        # 4. measured_brdf/ -> data/cg/materials/
        brdf_dir = v2_benchmarks / "measured_brdf"
        if brdf_dir.exists():
            target_mat = data_dir / "cg" / "materials"
            for item in sorted(brdf_dir.iterdir()):
                _merge_or_move(item, target_mat / item.name, f"data/benchmarks/measured_brdf/{item.name} → data/cg/materials/{item.name}", plan)
            if prune:
                plan.add_delete(brdf_dir, "Prune empty data/benchmarks/measured_brdf/")

        # Any remaining files/dirs in data/benchmarks/
        for item in sorted(v2_benchmarks.iterdir()):
            if item.name not in {"scenes", "primitives", "hdri", "measured_brdf"}:
                target = data_dir / "cg" / "scenes" / item.name if item.suffix in {".obj", ".gltf", ".glb", ".fbx"} else data_dir / "cg" / item.name
                _merge_or_move(item, target, f"data/benchmarks/{item.name} → data/cg/{target.name}", plan)

        if prune:
            plan.add_delete(v2_benchmarks, "Prune empty V2.0 data/benchmarks/ directory")

    # C. Migrate data/evaluations/ -> data/3d/evaluations/
    v2_evaluations = data_dir / "evaluations"
    if v2_evaluations.exists() and v2_evaluations.is_dir():
        target_eval = data_dir / "3d" / "evaluations"
        for child in sorted(v2_evaluations.iterdir()):
            _merge_or_move(child, target_eval / child.name, f"data/evaluations/{child.name} → data/3d/evaluations/{child.name}", plan)
        if prune:
            plan.add_delete(v2_evaluations, "Prune empty V2.0 data/evaluations/ directory")

    # D. Migrate data/captures/ -> data/common/captures/
    v2_captures = data_dir / "captures"
    if v2_captures.exists() and v2_captures.is_dir():
        target_captures = data_dir / "common" / "captures"
        for child in sorted(v2_captures.iterdir()):
            _merge_or_move(child, target_captures / child.name, f"data/captures/{child.name} → data/common/captures/{child.name}", plan)
        if prune:
            plan.add_delete(v2_captures, "Prune empty V2.0 data/captures/ directory")

    # E. Migrate data/raw/ -> data/common/captures/raw/
    v2_raw = data_dir / "raw"
    if v2_raw.exists() and v2_raw.is_dir():
        target_raw = data_dir / "common" / "captures" / "raw"
        for child in sorted(v2_raw.iterdir()):
            _merge_or_move(child, target_raw / child.name, f"data/raw/{child.name} → data/common/captures/raw/{child.name}", plan)
        if prune:
            plan.add_delete(v2_raw, "Prune empty V2.0 data/raw/ directory")


def _plan_repo_migrations(root: Path, plan: OrganizationPlan, prune: bool):
    """Normalizes repository paths: repos/ (plural) -> repo/ (singular)."""
    old_repos = root / "repos"
    new_repo = root / "repo"

    if old_repos.exists() and old_repos.is_dir():
        for child in sorted(old_repos.iterdir()):
            target = new_repo / child.name
            _merge_or_move(child, target, f"Normalize repos/{child.name} → repo/{child.name}", plan)
        if prune:
            plan.add_delete(old_repos, "Prune empty legacy repos/ (plural) directory")


def _plan_repository_staging(root: Path, plan: OrganizationPlan, stage_repo_path: Optional[Path]):
    """Plans staging of repositories into /dervgen/repo/all-overview."""
    repo_root = root / "repo"
    all_overview_target = repo_root / "all-overview"

    # If user provided explicit repository path to stage
    if stage_repo_path and stage_repo_path.exists():
        repo_name = stage_repo_path.name
        target = repo_root / repo_name
        if not target.exists():
            plan.add_stage(
                stage_repo_path, target,
                f"Stage local repository {stage_repo_path} → repo/{repo_name}"
            )
        else:
            plan.ok(f"Repository repo/{repo_name} already exists")
        return

    # Check if all-overview is already staged or planned to be moved
    target_already_planned = any(dst == all_overview_target for _, dst, _ in plan.moves)
    if all_overview_target.exists() or target_already_planned:
        plan.ok("repo/all-overview already exists or scheduled for migration")
        return

    # Auto-detect if current script is being executed inside an all-overview clone
    current_dir = Path.cwd().resolve()
    candidate_overview: Optional[Path] = None
    if current_dir.name == "all-overview" and (current_dir / ".git").exists():
        candidate_overview = current_dir
    elif (current_dir.parent).name == "all-overview" and (current_dir.parent / ".git").exists():
        candidate_overview = current_dir.parent
    elif Path("/content/dervgen/all-overview").exists():
        candidate_overview = Path("/content/dervgen/all-overview")

    if candidate_overview and candidate_overview.exists():
        plan.add_stage(
            candidate_overview, all_overview_target,
            f"Stage detected repository {candidate_overview.name} → repo/all-overview"
        )
    else:
        # Plan creation of empty placeholder directory for all-overview
        plan.add_create(all_overview_target, "Create repo/all-overview repository workspace")


def _plan_canonical_directories(root: Path, plan: OrganizationPlan):
    """Ensures all standard SSOT V2.1 directories exist in the plan."""
    # 1. 5 Pillars Root
    for pillar in ["data", "tools", "cache", "work", "repo"]:
        p = root / pillar
        if not p.exists():
            plan.add_create(p, f"Create pillar /{pillar}")
        else:
            plan.ok(f"Pillar /{pillar} exists")

    # 2. data/ 7 domains + subdirectories
    for domain, subs in DOMAIN_SUBDIRECTORIES.items():
        domain_path = root / "data" / domain
        if not domain_path.exists():
            plan.add_create(domain_path, f"Create data/{domain}/")
        for sub in subs:
            sub_path = domain_path / sub
            if not sub_path.exists():
                plan.add_create(sub_path, f"Create data/{domain}/{sub}/")
            else:
                plan.ok(f"data/{domain}/{sub}/ exists")

    # 3. tools/
    for td in TOOL_SUBDIRECTORIES:
        tool_path = root / "tools" / td
        if not tool_path.exists():
            plan.add_create(tool_path, f"Create tools/{td}/")
        else:
            plan.ok(f"tools/{td}/ exists")

    # 4. cache/
    for cd in CACHE_SUBDIRECTORIES:
        cache_path = root / "cache" / cd
        if not cache_path.exists():
            plan.add_create(cache_path, f"Create cache/{cd}/")
        else:
            plan.ok(f"cache/{cd}/ exists")

    # 5. repo/
    for rd in DEFAULT_REPOS:
        repo_path = root / "repo" / rd
        if not repo_path.exists():
            plan.add_create(repo_path, f"Create repo/{rd}/")
        else:
            plan.ok(f"repo/{rd}/ exists")


def _merge_or_move(src: Path, dst: Path, desc: str, plan: OrganizationPlan):
    """Safely plans moving a path or recursively merging directory contents."""
    if not src.exists():
        return

    if not dst.exists():
        plan.add_move(src, dst, desc)
        return

    # Destination already exists: if both are directories, plan per-item merge
    if src.is_dir() and dst.is_dir():
        for item in sorted(src.iterdir()):
            item_dest = dst / item.name
            if item_dest.exists():
                if item.is_dir() and item_dest.is_dir():
                    _merge_or_move(item, item_dest, f"{desc} -> sub/{item.name}", plan)
                else:
                    plan.warn(f"FILE COLLISION: {item} and {item_dest} both exist. Skipping to prevent overwrite.")
            else:
                plan.add_move(item, item_dest, f"Merge {item.name} into {dst.name}/")
        return

    # Collision where one is file or both are files
    plan.warn(f"COLLISION: Target already exists: {dst}. Skipping move of {src}.")


# ==============================================================================
# Execution Phase
# ==============================================================================

def _execute_move(src: Path, dst: Path):
    """Executes a file or directory move with recursive merge on conflict."""
    if not src.exists():
        return
    dst.parent.mkdir(parents=True, exist_ok=True)
    if not dst.exists():
        shutil.move(str(src), str(dst))
    elif src.is_dir() and dst.is_dir():
        for item in list(src.iterdir()):
            _execute_move(item, dst / item.name)
        try:
            src.rmdir()
        except OSError:
            pass
    elif src.is_file() and dst.is_file():
        print(f"    ⚠️ Conflict: {dst} already exists, skipping")
    else:
        print(f"    ⚠️ Incompatible collision: {src} and {dst}")


def execute_organization(
    plan: OrganizationPlan,
    dry_run: bool = True,
    symlink_repo: bool = False,
) -> Dict[str, Any]:
    """Applies planned filesystem operations with comprehensive logging."""
    mode = "DRY RUN (Preview Only)" if dry_run else "EXECUTING CHANGES"
    print(f"\n{'=' * 75}")
    print(f"  DervGen SSOT V2.1 Directory Organizer — {mode}")
    print(f"  Root: {plan.root}")
    print(f"  Timestamp: {datetime.now(timezone.utc).isoformat()}")
    print(f"{'=' * 75}")

    # Display Warnings
    if plan.warnings:
        print(f"\n⚠️  WARNINGS & CONFLICTS ({len(plan.warnings)}):")
        for w in plan.warnings:
            print(f"  ⚠️  {w}")

    # Compliant paths
    if plan.compliant_items:
        print(f"\n✅ Compliant Directories ({len(plan.compliant_items)}):")
        for c in plan.compliant_items[:10]:
            print(f"  ✓ {c}")
        if len(plan.compliant_items) > 10:
            print(f"  ... and {len(plan.compliant_items) - 10} more compliant paths.")

    # Creates
    if plan.creates:
        print(f"\n📁 CREATIONS ({len(plan.creates)}):")
        for p, desc in plan.creates:
            print(f"  + {desc}")
            if not dry_run:
                try:
                    p.mkdir(parents=True, exist_ok=True)
                except Exception as e:
                    print(f"    ❌ Error creating {p}: {e}")

    # Moves
    if plan.moves:
        print(f"\n📦 MOVES & MERGES ({len(plan.moves)}):")
        for src, dst, desc in plan.moves:
            print(f"  → {desc}")
            print(f"    FROM: {src}")
            print(f"    TO:   {dst}")
            if not dry_run:
                if not src.exists():
                    print(f"    ⚠️ Source does not exist: {src}")
                    continue
                try:
                    _execute_move(src, dst)
                    print(f"    ✓ Processed successfully")
                except Exception as e:
                    print(f"    ❌ Error moving: {e}")

    # Stages (Repositories)
    if plan.stages:
        print(f"\n💻 REPOSITORY STAGING ({len(plan.stages)}):")
        for src, dst, desc in plan.stages:
            print(f"  💻 {desc}")
            print(f"    SRC: {src}")
            print(f"    DST: {dst}")
            if not dry_run:
                try:
                    dst.parent.mkdir(parents=True, exist_ok=True)
                    if symlink_repo:
                        try:
                            if dst.exists():
                                dst.unlink()
                            os.symlink(str(src), str(dst), target_is_directory=True)
                            print(f"    ✓ Symlinked successfully")
                        except Exception as sym_err:
                            print(f"    ⚠️ Symlink failed ({sym_err}), falling back to copy...")
                            _copy_repo(src, dst)
                    else:
                        _copy_repo(src, dst)
                except Exception as e:
                    print(f"    ❌ Error staging repo: {e}")

    # Deletions (Pruning)
    if plan.deletes:
        print(f"\n🗑️  PRUNING EMPTY DIRECTORIES ({len(plan.deletes)}):")
        for p, desc in plan.deletes:
            print(f"  - {desc}")
            if not dry_run:
                if p.exists() and p.is_dir():
                    try:
                        p.rmdir()
                        print(f"    ✓ Removed empty directory")
                    except OSError:
                        print(f"    ⚠️ Directory not empty: {p} (kept for safety)")

    # Execution Summary
    print(f"\n{'=' * 75}")
    if dry_run:
        print(f"  DRY RUN COMPLETED: {plan.total_actions} actions planned.")
        print(f"  To apply changes, run with: --execute")
        if plan.deletes:
            print(f"  To apply changes + prune empty folders: --execute --prune")
    else:
        print(f"  ORGANIZATION COMPLETED: {plan.total_actions} actions processed.")
    print(f"{'=' * 75}")

    # Save JSON Report
    report_data = {
        "version": "2.1.0",
        "standard": "SSOT V2.1 Domain-Driven Architecture",
        "dry_run": dry_run,
        "executed_at": datetime.now(timezone.utc).isoformat(),
        "root": str(plan.root),
        "actions_summary": {
            "creates": len(plan.creates),
            "moves": len(plan.moves),
            "stages": len(plan.stages),
            "deletes": len(plan.deletes),
            "warnings": len(plan.warnings),
        },
        "moves": [{"src": str(s), "dst": str(d), "desc": desc} for s, d, desc in plan.moves],
        "creates": [{"path": str(p), "desc": desc} for p, desc in plan.creates],
        "stages": [{"src": str(s), "dst": str(d), "desc": desc} for s, d, desc in plan.stages],
        "deletes": [{"path": str(p), "desc": desc} for p, desc in plan.deletes],
        "warnings": plan.warnings,
    }

    if not dry_run:
        cache_dir = plan.root / "cache"
        cache_dir.mkdir(parents=True, exist_ok=True)
        report_file = cache_dir / "organize_report_v2.1.json"
        try:
            with open(report_file, "w", encoding="utf-8") as f:
                json.dump(report_data, f, indent=2, ensure_ascii=False)
            print(f"\n📄 Execution report written to: {report_file}")
        except Exception as e:
            print(f"⚠️ Could not write report file: {e}")

    return report_data


def _copy_repo(src: Path, dst: Path):
    """Copies repository excluding ephemeral or bulky caches (.git/objects unpacked if needed)."""
    def _ignore(directory, files):
        # Ignore heavy local intermediate artifacts
        ignored = []
        for f in files:
            if f in {"__pycache__", ".pytest_cache", "bazel-bin", "bazel-out", "bazel-testlogs"}:
                ignored.append(f)
        return ignored

    if not dst.exists():
        shutil.copytree(str(src), str(dst), ignore=_ignore, dirs_exist_ok=True)
        print(f"    ✓ Staged copy completed")
    else:
        print(f"    ✓ Destination already exists, contents retained")


# ==============================================================================
# Inspection & Scorecard Phase
# ==============================================================================

def show_directory_state(root: Path):
    """Inspects and prints current storage tree with compliance verification."""
    print(f"\n{'=' * 75}")
    print(f"  DervGen Storage SSOT V2.1 Scorecard & Tree Inspection")
    print(f"  Target Root: {root}")
    print(f"{'=' * 75}")

    if not root.exists():
        print(f"  ❌ Storage root does not exist: {root}")
        return

    # 1. 5 Pillars Check
    pillars = ["data", "tools", "cache", "work", "repo"]
    pillar_status = {}
    for p in pillars:
        path = root / p
        pillar_status[p] = path.exists() and path.is_dir()

    print("\n🏛️  Architecture 5-Pillar Scorecard:")
    for p, exists in pillar_status.items():
        icon = "✅" if exists else "❌"
        desc = dir_summary(root / p) if exists else "MISSING"
        print(f"  {icon} /{p:<6} : {desc}")

    # 2. Domain Data Check
    data_dir = root / "data"
    if data_dir.exists():
        print("\n📦 Data Domains (SSOT V2.1):")
        for domain, subs in DOMAIN_SUBDIRECTORIES.items():
            d_path = data_dir / domain
            status = "✓" if d_path.exists() else "✗"
            sub_count = sum(1 for s in subs if (d_path / s).exists())
            print(f"    [{status}] {domain:<8} ({sub_count}/{len(subs)} sub-domains)")

    # 3. Repository Check
    repo_dir = root / "repo"
    print("\n💻 Code Repositories (/dervgen/repo/):")
    if repo_dir.exists():
        repos = [r.name for r in repo_dir.iterdir() if r.is_dir()]
        print(f"    Active repos: {', '.join(repos) if repos else '(none)'}")
    else:
        print("    ❌ /dervgen/repo/ does not exist")

    # 4. Tree Preview
    print(f"\n🌳 Directory Tree Preview (Depth=2):")
    tree = dir_tree(root, max_depth=2)
    print(f"  {root.name}/")
    for line in tree:
        print(f"  {line}")

    # 5. Legacy Remnants Detection
    remnants = []
    if (root / "model").exists():
        remnants.append(f"V1 model/ [{dir_summary(root / 'model')}]")
    if (root / "workspace").exists():
        remnants.append(f"V1 workspace/ [{dir_summary(root / 'workspace')}]")
    if (root / "bundles").exists():
        remnants.append(f"V1 bundles/ [{dir_summary(root / 'bundles')}]")
    if (root / "data" / "models").exists():
        remnants.append(f"V2.0 data/models/ [{dir_summary(root / 'data' / 'models')}]")
    if (root / "data" / "benchmarks").exists():
        remnants.append(f"V2.0 data/benchmarks/ [{dir_summary(root / 'data' / 'benchmarks')}]")
    if (root / "data" / "evaluations").exists():
        remnants.append(f"V2.0 data/evaluations/ [{dir_summary(root / 'data' / 'evaluations')}]")
    if (root / "repos").exists():
        remnants.append(f"Legacy repos/ (plural) [{dir_summary(root / 'repos')}]")

    print(f"\n🔍 Legacy Remnants Status:")
    if remnants:
        print(f"  ⚠️  Found {len(remnants)} unmigrated legacy directories:")
        for r in remnants:
            print(f"     • {r}")
        print("  💡 Run 'python organize_directories.py --execute --prune' to resolve.")
    else:
        print("  ✅ Zero legacy remnants found. Storage layout is 100% V2.1 compliant!")


# ==============================================================================
# CLI Entry Point
# ==============================================================================

def main():
    parser = argparse.ArgumentParser(
        description="Organize /dervgen/ storage into SSOT V2.1 Domain-Driven Architecture",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python organize_directories.py                     # Safe preview (dry run)
  python organize_directories.py --execute            # Apply reorganization
  python organize_directories.py --execute --prune     # Apply + prune empty legacy dirs
  python organize_directories.py --show-state          # Inspect current tree & scorecard
  python organize_directories.py --execute --init-only # Bootstrap clean V2.1 structure
  python organize_directories.py --execute --stage-repo /path/to/all-overview
        """
    )
    parser.add_argument(
        "--root", type=str, default=None,
        help="Custom storage root directory (defaults to $DERVGEN_DRIVE_ROOT or /dervgen)"
    )
    parser.add_argument(
        "--execute", action="store_true",
        help="Actually perform the filesystem moves and creations (default is dry-run)"
    )
    parser.add_argument(
        "--prune", action="store_true",
        help="Remove empty legacy directories after migrating contents (requires --execute)"
    )
    parser.add_argument(
        "--show-state", action="store_true",
        help="Show current directory structure, compliance scorecard, and exit"
    )
    parser.add_argument(
        "--init-only", action="store_true",
        help="Only initialize standard SSOT V2.1 directory tree without scanning legacy paths"
    )
    parser.add_argument(
        "--stage-repo", type=str, default=None,
        help="Path to a repository to stage into /dervgen/repo/<repo_name>"
    )
    parser.add_argument(
        "--symlink-repo", action="store_true",
        help="Create a symbolic link for staged repositories instead of copying (Linux/Colab only)"
    )
    parser.add_argument(
        "--json", action="store_true",
        help="Output plan summary as JSON to stdout"
    )
    args = parser.parse_args()

    # Determine storage root
    root = Path(args.root).resolve() if args.root else get_default_drive_root()

    if args.show_state:
        show_directory_state(root)
        return

    # Build plan
    stage_path = Path(args.stage_repo).resolve() if args.stage_repo else None
    plan = OrganizationPlan(root)
    plan_organization(
        root=root,
        plan=plan,
        prune=args.prune,
        stage_repo_path=stage_path,
        init_only=args.init_only,
    )

    if args.json:
        report = {
            "root": str(root),
            "dry_run": not args.execute,
            "actions": plan.total_actions,
            "moves": [m[2] for m in plan.moves],
            "creates": [c[1] for c in plan.creates],
            "stages": [s[2] for s in plan.stages],
            "deletes": [d[1] for d in plan.deletes],
            "warnings": plan.warnings,
        }
        print(json.dumps(report, indent=2, ensure_ascii=False))
        return

    # Display inspection first
    show_directory_state(root)

    # Execute or preview
    execute_organization(
        plan=plan,
        dry_run=not args.execute,
        symlink_repo=args.symlink_repo,
    )


if __name__ == "__main__":
    main()
