#!/usr/bin/env python3
"""
DervGen Storage SSOT: Google Drive Directory Manager (100% Cloud / Web-Native)
Standardizes cloud storage hierarchy with ZERO local disk consumption:
  - /dervgen/data/models/{usage}/  : Model weights partitioned by purpose
  - /dervgen/data/...              : Raw datasets, captures, benchmark assets
  - /dervgen/work/{user}/{repo}/{date}/{job_id}/ : Job runtime workspaces
  - /dervgen/cache/...             : Persistent build and toolchain caches (Bazel, HF)

All downloads, uploads, and data manipulations happen purely in the Cloud (Colab & Drive Web).
"""

import os
import sys
import json

import shutil
import urllib.request
from pathlib import Path

# Safe utf-8 stdout for terminals
if hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass


# Google Drive storage root in Google Colab (Pure Cloud)
DRIVE_ROOT = Path(os.environ.get("DERVGEN_DRIVE_ROOT", "/content/drive/MyDrive/dervgen"))
LOCAL_ROOT = Path("/content")

# Core Standard Directory Hierarchy
STANDARD_MODEL_USAGES = [
    "3d_recon",           # 3DGS, DUSt3R, MASt3R, InstantMesh, NeRF, CoTracker
    "texture_gen",        # Material synthesis, OpenPBR diffusion, texture baking, relighting
    "video_gen",          # Controllable video generation (Wan 2.1, ControlNeXt, CameraCtrl)
    "actor_dynamics",     # SMPL-X, Face, Rigging, MotionBricks, EMOCA, EMAGE
    "audio_foley",        # Spatial audio, physical Foley generation, zero-shot TTS
    "foundation",         # SAM 2, DINOv2, CLIP, Vision-Language backbones
    "denoise_upscale",    # Neural denoisers, super-resolution, DLSS/FSR weights
]

STANDARD_DATA_DIRS = [
    "benchmarks",         # Canonical test scenes (Sponza, Bistro, Cornell Box)
    "evaluations",        # Evaluation benchmark suites (RFC 0053 SWE-bench for 3D, closed loop cases)
    "captures",           # Raw camera captures, video frames, calibration JSONs
    "raw",                # Unprocessed source geometries, scans, audio
]

STANDARD_CACHE_DIRS = [
    "bazel",              # Bazel disk cache for C++ builds
    "huggingface",        # HuggingFace hub cache
]


def check_drive_mounted() -> bool:
    drive_base = Path("/content/drive/MyDrive")
    if not drive_base.exists() and not os.environ.get("DERVGEN_DRIVE_ROOT"):
        print("⚠️  [Drive Manager] Google Drive is NOT mounted at /content/drive/MyDrive.")
        print("    Please run in Colab notebook: from google.colab import drive; drive.mount('/content/drive')")
        return False
    return True


def init_drive_structure():
    """Initializes the standard /dervgen hierarchy directly in Google Drive Cloud."""
    if not check_drive_mounted():
        return False

    print(f"📁 Initializing DervGen Cloud Storage Layout in: {DRIVE_ROOT}")

    # 1. /dervgen/data/models/{usage}/
    for usage in STANDARD_MODEL_USAGES:
        p = DRIVE_ROOT / "data" / "models" / usage
        p.mkdir(parents=True, exist_ok=True)
        print(f"  ✓ model/{usage}")

    # 2. /dervgen/data/...
    for d in STANDARD_DATA_DIRS:
        p = DRIVE_ROOT / "data" / d
        p.mkdir(parents=True, exist_ok=True)
        print(f"  ✓ data/{d}")

    # 3. /dervgen/work/
    (DRIVE_ROOT / "work").mkdir(parents=True, exist_ok=True)
    (DRIVE_ROOT / "tools" / "wheels").mkdir(parents=True, exist_ok=True)
    (DRIVE_ROOT / "tools" / "bin").mkdir(parents=True, exist_ok=True)
    print("  ✓ work/")

    # 4. /dervgen/cache/...
    for c in STANDARD_CACHE_DIRS:
        p = DRIVE_ROOT / "cache" / c
        p.mkdir(parents=True, exist_ok=True)
        print(f"  ✓ cache/{c}")

    # Setup local shortcuts in Colab's fast NVMe RAM/Disk
    setup_local_links()

    # Sync Google Drive Model Index
    try:
        from init_models import sync_drive_index
        sync_drive_index()
    except Exception as e:
        print(f"Notice: Index sync skipped ({e})")

    print("✅ DervGen cloud directory hierarchy initialized successfully! (Local disk usage: 0 MB)")
    return True


def setup_local_links():
    """Sets up high-speed local shortcuts from /content into Drive storage inside Colab."""
    if not DRIVE_ROOT.exists():
        return
    if not LOCAL_ROOT.exists():
        # Running outside Colab environment (e.g. testing or dry run)
        return

    links = {
        LOCAL_ROOT / "models": DRIVE_ROOT / "data" / "models",
        LOCAL_ROOT / "data": DRIVE_ROOT / "data",
        LOCAL_ROOT / "work_drive": DRIVE_ROOT / "work",
    }

    for local_path, target_path in links.items():
        if local_path.is_symlink():
            local_path.unlink()
        elif local_path.exists():
            shutil.rmtree(local_path)

        target_path.mkdir(parents=True, exist_ok=True)
        local_path.symlink_to(target_path, target_is_directory=True)
        print(f"  🔗 Linked {local_path} -> {target_path}")


def download_cloud_asset(url: str, dest_path: Path, desc: str = "Asset"):
    """Downloads an asset directly from the web into Google Drive (Data-center speed)."""
    dest_path.parent.mkdir(parents=True, exist_ok=True)
    if dest_path.exists():
        print(f"ℹ️  {desc} already exists at: {dest_path}")
        return dest_path

    print(f"⬇️  Downloading {desc} directly into Drive: {dest_path.name}...")
    try:
        # Check if huggingface-cli / gdown should be used
        if "drive.google.com" in url:
            os.system(f"gdown '{url}' -O '{dest_path}'")
        else:
            urllib.request.urlretrieve(url, str(dest_path))
        print(f"✅ Successfully saved {dest_path.name} ({dest_path.stat().st_size / (1024*1024):.2f} MB)")
    except Exception as e:
        print(f"❌ Failed to download {url}: {e}")
    return dest_path


def download_model(usage: str, url: str, filename: str):
    """Directly downloads a model weight into /dervgen/data/models/{usage}/{filename}."""
    if not check_drive_mounted():
        return
    if usage not in STANDARD_MODEL_USAGES:
        print(f"⚠️ Usage '{usage}' not in standard usages ({STANDARD_MODEL_USAGES}). Creating custom folder.")

    target = DRIVE_ROOT / "data" / "models" / usage / filename
    return download_cloud_asset(url, target, f"Model [{usage}]")


def download_dataset(category: str, url: str, filename: str):
    """Directly downloads a raw dataset into /dervgen/data/{category}/{filename}."""
    if not check_drive_mounted():
        return
    target = DRIVE_ROOT / "data" / category / filename
    return download_cloud_asset(url, target, f"Dataset [{category}]")


def create_job(jobname: str, user: str = "yanglei", repo: str = "general", date: str = None) -> Path:
    """Creates a standardized job workspace: input, output, checkpoints, logs under /dervgen/work/{user}/{repo}/{date}/{job_id}."""
    if not check_drive_mounted():
        sys.exit(1)

    if not date:
        from datetime import datetime
        date = datetime.now().strftime("%Y-%m-%d")

    job_dir = DRIVE_ROOT / "work" / user / repo / date / jobname
    (job_dir / "input").mkdir(parents=True, exist_ok=True)
    (job_dir / "output").mkdir(parents=True, exist_ok=True)
    (job_dir / "checkpoints").mkdir(parents=True, exist_ok=True)
    (job_dir / "logs").mkdir(parents=True, exist_ok=True)

    readme_path = job_dir / "README.md"
    if not readme_path.exists():
        readme_path.write_text(f"""# Job: {jobname}

- **所属仓库**: `{repo}`
- **执行日期**: `{date}`
- **发起方**: `User: {user}`
- **当前状态**: `RUNNING`
- **运行环境**: Google Colab

---

## 1. 任务背景与目的 (Objective)
- 待补充

## 2. 关键超参与输入配置 (Configurations)
- 待补充

## 3. 一键复现命令 (Reproduction)
- 待补充

## 4. 关键指标与结论 (Results & Scorecard)
- 待补充
""", encoding="utf-8")

    job_json_path = job_dir / "job.json"
    if not job_json_path.exists():
        from datetime import datetime, timezone
        job_info = {
            "version": "1.0.0",
            "job_id": jobname,
            "repo": repo,
            "date": date,
            "user": user,
            "status": "RUNNING",
            "lifecycle": {
                "created_at": datetime.now(timezone.utc).isoformat(),
                "started_at": datetime.now(timezone.utc).isoformat(),
                "finished_at": None,
                "duration_seconds": None
            },
            "metrics": {},
            "exit_code": None
        }
        job_json_path.write_text(json.dumps(job_info, indent=2, ensure_ascii=False), encoding="utf-8")

    print(f"✅ Cloud Job workspace created at: {job_dir}")
    print(f"   ├── README.md     (Metadata and summary)")
    print(f"   ├── job.json      (Machine-readable state & metrics)")
    print(f"   ├── input/        (Config, parameters, scenes ref)")
    print(f"   ├── output/       (Deliverables, meshes, videos)")
    print(f"   ├── checkpoints/  (Weights, state.json)")
    print(f"   └── logs/         (Execution stdout/stderr)")
    return job_dir


def sync_job(jobname: str, local_job_dir: str = "/content/jobs"):
    """Syncs local execution output of a job to Google Drive workspace."""
    if not check_drive_mounted():
        return

    source = Path(local_job_dir) / jobname
    dest = DRIVE_ROOT / "work" / jobname

    if not source.exists():
        print(f"❌ Source local job path does not exist: {source}")
        return

    dest.mkdir(parents=True, exist_ok=True)
    print(f"💾 Syncing job '{jobname}' from {source} to {dest}...")
    shutil.copytree(source, dest, dirs_exist_ok=True)
    print(f"✅ Job '{jobname}' successfully synced to Drive!")


def list_all():
    """Lists summary of models, data, and jobs."""
    if not check_drive_mounted():
        return

    print(f"\n=======================================================")
    print(f" DervGen Cloud Storage Summary: {DRIVE_ROOT}")
    print(f" (Zero Local Disk Footprint - 100% Cloud Native)")
    print(f"=======================================================")

    # Models
    print("\n📦 [Models by Usage]:")
    model_dir = DRIVE_ROOT / "data" / "models"
    if model_dir.exists():
        for usage in STANDARD_MODEL_USAGES:
            u_dir = model_dir / usage
            items = list(u_dir.iterdir()) if u_dir.exists() else []
            print(f"  - data/models/{usage:<16} ({len(items)} items)")
            for item in items[:5]:
                size_mb = item.stat().st_size / (1024 * 1024) if item.is_file() else 0
                print(f"      • {item.name} ({size_mb:.1f} MB)")

    # Data
    print("\n💾 [Data Categories]:")
    data_dir = DRIVE_ROOT / "data"
    if data_dir.exists():
        for d in STANDARD_DATA_DIRS:
            d_dir = data_dir / d
            items = list(d_dir.iterdir()) if d_dir.exists() else []
            print(f"  - data/{d:<16} ({len(items)} items)")
            for item in items[:5]:
                size_mb = item.stat().st_size / (1024 * 1024) if item.is_file() else 0
                print(f"      • {item.name} ({size_mb:.1f} MB)")

    # Jobs in work/
    print("\n🚀 [Workspace Jobs]:")
    ws_dir = DRIVE_ROOT / "work"
    if ws_dir.exists():
        jobs = [j.name for j in ws_dir.iterdir() if j.is_dir()]
        if jobs:
            for j in jobs:
                print(f"  - work/{j}")
        else:
            print("  (No jobs created yet. Use create_job(<jobname>))")
    print(f"=======================================================\n")


if __name__ == "__main__":
    if len(sys.argv) > 1:
        cmd = sys.argv[1]
        if cmd == "list":
            list_all()
        elif cmd == "create_job" and len(sys.argv) > 2:
            create_job(sys.argv[2])
        elif cmd == "sync_job" and len(sys.argv) > 2:
            sync_job(sys.argv[2])
        elif cmd == "download_model" and len(sys.argv) > 4:
            download_model(sys.argv[2], sys.argv[3], sys.argv[4])
        elif cmd == "download_data" and len(sys.argv) > 4:
            download_dataset(sys.argv[2], sys.argv[3], sys.argv[4])
        elif cmd == "sync_index":
            from init_models import sync_drive_index
            sync_drive_index()
        else:
            print(f"Unknown command or wrong parameters: {cmd}")
            print("Usage:")
            print("  drive_manager.py init")
            print("  drive_manager.py list")
            print("  drive_manager.py sync_index")
            print("  drive_manager.py create_job <jobname>")
            print("  drive_manager.py sync_job <jobname>")
            print("  drive_manager.py download_model <usage> <url> <filename>")
            print("  drive_manager.py download_data <category> <url> <filename>")
    else:
        init_drive_structure()
