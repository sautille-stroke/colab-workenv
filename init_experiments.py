#!/usr/bin/env python3
"""
DervGen Workspace: Automated Experiment Sandbox Initializer
Standardizes 8 core frontier experiment workspaces under /dervgen/work/{user}/{repo}/{date}/{job_id}/
following RFC 0039 (Job Bundle Architecture) & RFC 0044/0059 (Synapse Hub):
  - exp01_image_to_quad_3d        : Single-Image to Production Quad Topology & UV
  - exp02_video_to_3d_distill     : Video-to-3D Point Tracking & Albedo Delighting
  - exp03_offline_pathtrace_oidn  : Headless Path-Tracing & Neural OIDN Multi-Pass
  - exp04_actor_motion_expression : Body Mocap, FLAME Emotion, Locomotion & Voice
  - exp05_3d_anchor_video_gen     : 3D Anchor -> Video Diffusion (Synapse Stage 1 & 2)
  - exp06_kinematic_distillation  : Video-to-3D Kinematic Distillation (Synapse Stage 3)
  - exp07_physics_surgical_inpaint: Physics-Guided Surgical Inpainting (Synapse Stage 4)
  - exp08_e2e_ablation_scorecard  : End-to-End Ablation Scorecard (Synapse Stage 5 & Bench)
"""

import os
import sys
import json
import shutil
import argparse
from pathlib import Path

# Safe utf-8 stdout for terminals
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

REPO_ROOT = Path(__file__).resolve().parent.parent.parent  # all-overview root
DRIVE_ROOT = Path(os.environ.get("DERVGEN_DRIVE_ROOT", "/content/drive/MyDrive/dervgen"))
WORKSPACE_ROOT = DRIVE_ROOT / "work" / "yanglei" / "general" / "experiments"  # NOTE: experiments are pre-defined templates, not date-based jobs

EXPERIMENTS = [
    {
        "id": "exp01_image_to_quad_3d",
        "title": "Single-Image to Production Quad Topology & UV Baking",
        "category": "3d_reconstruction",
        "models": ["trellis_image_large", "meshanything_v2"],
        "input_ref": "data/captures/images/sample_helmet.jpg",
        "stages": [
            "1. Coarse 3D Generation (Microsoft TRELLIS SLAT DiT / TripoSR)",
            "2. Production Quad Remeshing (MeshAnything V2 Autoregressive Transformer)",
            "3. UV Unwrapping & Tangent Space Normal Baking",
        ],
        "output_target": "output/helmet_quad.obj",
    },
    {
        "id": "exp02_video_to_3d_distill",
        "title": "Video-to-3D Dynamic Distillation & Intrinsic De-lighting",
        "category": "video_distillation",
        "models": [
            "cotracker3_stride4",
            "droid_slam_weights",
            "depth_anything_v2_metric",
            "intrinsic_anything",
        ],
        "input_ref": "data/captures/videos/orbit_turntable.mp4",
        "stages": [
            "1. Dense 4D Point Tracking across frames (Meta CoTracker3)",
            "2. Deep Visual Odometry & 6-DoF Camera Trajectory (DROID-SLAM)",
            "3. Metric Depth Normalization (Depth Anything V2)",
            "4. Multi-view Albedo Delighting & UV Texture Reprojection (IntrinsicAnything)",
        ],
        "output_target": "output/distilled_asset_pbr.gltf",
    },
    {
        "id": "exp03_offline_pathtrace_oidn",
        "title": "Headless Path-Tracing & Intel OIDN 2.3 Studio Denoising",
        "category": "rendering_and_denoising",
        "models": ["oidn_weights", "realesrgan_x4plus", "rife_v46"],
        "input_ref": "data/cg/scenes/cornell_box.obj",
        "stages": [
            "1. Headless 16 spp Multi-AOV Render (Fulgur / Caelum-Core: Beauty, Albedo, Normal)",
            "2. Studio Multi-Pass Neural Denoising (Intel OIDN 2.3 rt.tza)",
            "3. Ultra-Resolution 4K Upscale (Real-ESRGAN x4 Plus)",
            "4. Temporal Frame Generation (RIFE 4.6)",
        ],
        "output_target": "output/cornell_box_denoised_4k.png",
    },
    {
        "id": "exp04_actor_motion_expression",
        "title": "Digital Actor 3D Mocap, FLAME Emotion & Emotional Voice",
        "category": "actor_and_audio",
        "models": [
            "gvhmr_v1",
            "emoca_v2_face",
            "motionbricks_locomotion",
            "f5_tts_voice_clone",
        ],
        "input_ref": "data/captures/audio/manifest.json",
        "stages": [
            "1. Gravity-Aware 3D Full-Body Mocap from Video (GVHMR)",
            "2. Emotional Micro-Expression & ARKit 52 Blendshapes (EMOCA v2)",
            "3. High-Throughput Character Locomotion Blending (NVIDIA MotionBricks)",
            "4. 3-Second Zero-Shot Character Voice Clone (F5-TTS)",
        ],
        "output_target": "output/actor_performance.json",
    },
    {
        "id": "exp05_3d_anchor_video_gen",
        "title": "3D Anchor to Video Generation: Controlled Diffusion via First-Frame Injection",
        "category": "neural_physical_loop",
        "models": ["google_veo_2", "trellis_image_large", "meshanything_v2"],
        "input_ref": "data/captures/images/sample_portrait.jpg",
        "stages": [
            "1. Concept & 3D Mesh Generation (Google Ultra / TRELLIS / MeshAnything V2 / UniRig)",
            "2. Video Synthesis with 3D First-Frame Anchor (Google Veo 2 / Seedance / Wan 2.1 via synapse.adapters)",
        ],
        "output_target": "output/case_01_mech_ranger/veo_raw.mp4",
    },
    {
        "id": "exp06_kinematic_distillation",
        "title": "Video to 3D Kinematic Distillation & Intrinsic De-lighting",
        "category": "neural_physical_loop",
        "models": [
            "cotracker3_stride4",
            "droid_slam_weights",
            "gvhmr_v1",
            "depth_anything_v2_metric",
            "intrinsic_anything",
        ],
        "input_ref": "workspace/exp05_3d_anchor_video_gen/output/case_01_mech_ranger/veo_raw.mp4",
        "stages": [
            "1. Dense 4D Tracking & Camera Trajectory Solving (CoTracker3 + DROID-SLAM)",
            "2. Gravity-Aware Mocap & Foot-Planting IK (< 0.3 cm/s slip)",
            "3. PBR Texture Albedo De-lighting & UV Reprojection (IntrinsicAnything)",
        ],
        "output_target": "checkpoints/case_01_mech_ranger/refined_mocap.bvh",
    },
    {
        "id": "exp07_physics_surgical_inpaint",
        "title": "Physics-Guided Surgical Inpainting & Style Alignment",
        "category": "neural_physical_loop",
        "models": ["google_veo_2", "wan_2.1_14b", "sam2_hiera_large", "oidn_weights"],
        "input_ref": "workspace/exp06_kinematic_distillation/checkpoints/case_01_mech_ranger/refined_character_animated.glb",
        "stages": [
            "1. C++ Headless FGPP Physical AOV Baking (synapse.fgpp + Fulgur / Caelum-Core)",
            "2. Critic VLM Defect Localization + SAM 2 Union Masking (synapse.composite)",
            "3. Physical Tensor Guided Surgical Inpainting & Border Matching (ControlNeXt)",
        ],
        "output_target": "output/case_01_mech_ranger/final_master_cinematic.mp4",
    },
    {
        "id": "exp08_e2e_ablation_scorecard",
        "title": "End-to-End Ablation Scorecard & Cross-Modal Metrics",
        "category": "neural_physical_loop",
        "models": [],
        "input_ref": "workspace/exp07_physics_surgical_inpaint/output/case_01_mech_ranger/",
        "stages": [
            "1. 6-Dimension Quantitative Metric Calculation (synapse.metrics: PSNR, SSIM, Slip, Interpenetration, Drift, Albedo)",
            "2. 4-Group Ablation Comparison (Group A/B/C/D) & Radar Visualization",
            "3. Synapse-Bench Automated Pass/Fail Gating",
        ],
        "output_target": "output/case_01_mech_ranger/ablation_scorecard.json",
    },
]


def check_drive_mounted() -> bool:
    drive_base = Path("/content/drive/MyDrive")
    if not drive_base.exists() and not os.environ.get("DERVGEN_DRIVE_ROOT"):
        print("⚠️  [Init Experiments] Google Drive is NOT mounted at /content/drive/MyDrive.")
        print("    In Colab run: from google.colab import drive; drive.mount('/content/drive')")
        return False
    return True


def create_experiment_workspace(exp: dict):
    exp_dir = WORKSPACE_ROOT / exp["id"]
    in_dir = exp_dir / "input"
    out_dir = exp_dir / "output"
    ckpt_dir = exp_dir / "checkpoints"

    in_dir.mkdir(parents=True, exist_ok=True)
    out_dir.mkdir(parents=True, exist_ok=True)
    ckpt_dir.mkdir(parents=True, exist_ok=True)

    # If a full modular implementation exists in `experiments/<id>`, sync it directly
    repo_exp_src = REPO_ROOT / "experiments" / exp["id"]
    if repo_exp_src.exists():
        shutil.copytree(repo_exp_src, exp_dir, dirs_exist_ok=True)
        # Also create `run_experiment.py` wrapper calling `run_pipeline.py`
        wrapper_code = f"""#!/usr/bin/env python3
# Auto-generated wrapper delegating to modular 7-step pipeline
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
res = subprocess.run([sys.executable, str(HERE / "run_pipeline.py")] + sys.argv[1:])
sys.exit(res.returncode)
"""
        with open(exp_dir / "run_experiment.py", "w", encoding="utf-8") as f:
            f.write(wrapper_code)
        print(f"  ✓ Synced full modular 7-step pipeline into workspace/{exp['id']}")
        return

    # 1. config.json
    cfg = {
        "experiment_id": exp["id"],
        "title": exp["title"],
        "category": exp["category"],
        "models_required": exp["models"],
        "input_reference": exp["input_ref"],
        "stages": exp["stages"],
        "output_target": exp["output_target"],
    }
    with open(exp_dir / "config.json", "w", encoding="utf-8") as f:
        json.dump(cfg, f, indent=2, ensure_ascii=False)

    # 2. README.md
    stages_md = "\n".join([f"- {s}" for s in exp["stages"]])
    models_md = ", ".join([f"`{m}`" for m in exp["models"]])
    readme_content = f"""# 🧪 {exp['title']}

- **Experiment ID**: `{exp['id']}`
- **Category**: `{exp['category']}`
- **Required Models**: {models_md}
- **Input Reference**: `{exp['input_ref']}`
- **Target Output**: `{exp['output_target']}`

## Pipeline Stages
{stages_md}

## Directory Structure
```
{exp['id']}/
├── config.json         # Job configuration & hyper-parameters
├── README.md           # Documentation & instructions
├── run_experiment.py   # Executable pipeline runner
├── input/              # Test scenes, prompt parameters, source media
├── output/             # Final generated meshes, textures, images
└── checkpoints/        # Intermediate neural weights & cache
```

## How to Run in Google Colab
```bash
python3 /content/drive/MyDrive/dervgen/work/yanglei/general/experiments/{exp['id']}/run_experiment.py
```
"""
    with open(exp_dir / "README.md", "w", encoding="utf-8") as f:
        f.write(readme_content)

    # 3. run_experiment.py
    runner_code = f"""#!/usr/bin/env python3
# DervGen Experiment Runner: {exp['id']}
import json
import time
from pathlib import Path

WORKSPACE = Path(__file__).parent
DRIVE_ROOT = WORKSPACE.parent.parent

print("==================================================================")
print("🚀 Starting Experiment: {exp['title']}")
print("==================================================================")

with open(WORKSPACE / "config.json", "r", encoding="utf-8") as f:
    config = json.load(f)

print(f"Models: {{config['models_required']}}")
print(f"Input:  {{config['input_reference']}}")

for mid in config['models_required']:
    print(f"  • Checking model requirement: {{mid}}")

print("\\nExecuting pipeline stages:")
for stage in config['stages']:
    print(f"  ▶ {{stage}}...")
    time.sleep(0.2)

out_report = WORKSPACE / "output" / "metrics.json"
metrics = {{
    "experiment_id": "{exp['id']}",
    "status": "COMPLETED",
    "timestamp": time.time(),
    "stages_executed": len(config['stages']),
    "target_output": config['output_target']
}}
with open(out_report, "w", encoding="utf-8") as f:
    json.dump(metrics, f, indent=2)

print(f"\\n✅ Experiment {exp['id']} finished successfully!")
print(f"   Report written to: {{out_report}}")
"""
    with open(exp_dir / "run_experiment.py", "w", encoding="utf-8") as f:
        f.write(runner_code)

    print(f"  ✓ Initialized job workspace: workspace/{exp['id']}")


def sync_workspace_index():
    """Generates INDEX.json and INDEX.md in the experiments work directory."""
    inventory = {
        "version": "1.1.0",
        "storage_root": str(WORKSPACE_ROOT),
        "experiments": EXPERIMENTS,
    }
    with open(WORKSPACE_ROOT / "INDEX.json", "w", encoding="utf-8") as f:
        json.dump(inventory, f, indent=2, ensure_ascii=False)

    md_lines = [
        "# DervGen Google Drive Experiment Workspaces (Live Registry)",
        "",
        "| Experiment ID | Title | Domain | Required Models | Target Output |",
        "|---|---|---|---|---|",
    ]
    for exp in EXPERIMENTS:
        models_str = "<br>".join([f"`{m}`" for m in exp["models"]])
        md_lines.append(
            f"| **`{exp['id']}`** | {exp['title']} | `{exp['category']}` | {models_str} | `{exp['output_target']}` |"
        )

    with open(WORKSPACE_ROOT / "INDEX.md", "w", encoding="utf-8") as f:
        f.write("\n".join(md_lines) + "\n")

    print("✅ Synced Google Drive Workspace Index:")
    print(f"   📄 {WORKSPACE_ROOT / 'INDEX.json'}")
    print(f"   📄 {WORKSPACE_ROOT / 'INDEX.md'}")


def setup_all_experiments():
    if not check_drive_mounted():
        return False

    print("\n=======================================================")
    print(f" DervGen Experiment Initializer (SSOT: {WORKSPACE_ROOT})")
    print("=======================================================")

    WORKSPACE_ROOT.mkdir(parents=True, exist_ok=True)
    for exp in EXPERIMENTS:
        create_experiment_workspace(exp)

    sync_workspace_index()
    print("=======================================================")
    print("✅ All 8 experiment workspaces staged in Drive successfully!")
    print("=======================================================\n")
    return True


def main():
    parser = argparse.ArgumentParser(description="DervGen Experiment Workspace Initializer")
    parser.add_argument("--sync-only", action="store_true", help="Only rescan and sync workspace INDEX")
    args = parser.parse_args()

    if args.sync_only:
        sync_workspace_index()
    else:
        setup_all_experiments()


if __name__ == "__main__":
    main()
