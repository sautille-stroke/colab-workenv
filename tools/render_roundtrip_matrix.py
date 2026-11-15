#!/usr/bin/env python3
"""
DervGen: Rendering Condition Matrix Batch Renderer

Reads the rendering condition framework from the Round-Trip evaluation suite
and orchestrates headless rendering via Fulgur/Caelum-Core for all condition
variant render_spec files.

Usage:
    # Full rendering (all 12 cases x ~12 conditions each = ~144 tasks)
    python tools/render_roundtrip_matrix.py --data-root /content/drive/MyDrive/dervgen/data

    # Single case dry-run (list tasks without rendering)
    python tools/render_roundtrip_matrix.py --data-root ./data --dry-run --case rt_grab_01_pistol_grip_contact

    # Render specific condition only
    python tools/render_roundtrip_matrix.py --data-root ./data --condition cond_baseline

    # Parallel rendering on caelum-farm
    python tools/render_roundtrip_matrix.py --data-root ./data --farm --workers 4

Estimated time: ~1.5-2 hours single GPU at 128spp, 96-120 frames per task.
With caelum-farm (4 GPUs): ~25-30 minutes.

Output per task:
    data/evaluations/dataset_bidirectional_roundtrip/cases/<case_id>/variants/<cond_id>/
        ├── render_spec_variant.json   (input config, pre-generated)
        ├── frames/                    (rendered EXR frames: frame_0000.exr .. frame_0119.exr)
        ├── video_gt.mp4               (composited GT video, H.264 lossless)
        ├── aov_depth/                 (depth AOV channel EXRs)
        ├── aov_normal/                (world normal AOV EXRs)
        ├── aov_motion/                (motion vector AOV EXRs, if available)
        └── render_log.json            (timing, GPU info, error log)
"""

import os
import sys
import json
import time
import argparse
import subprocess
import shutil
from datetime import datetime, timezone
from pathlib import Path
from concurrent.futures import ProcessPoolExecutor, as_completed

# Safe utf-8 stdout
if hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass


def discover_render_tasks(data_root: Path, case_filter: str = None,
                          condition_filter: str = None) -> list:
    """Scan the round-trip suite and discover all variant render tasks.

    Returns list of dicts:
        {case_id, condition_id, variant_dir, render_spec_path, base_case_dir}
    """
    rt_dir = data_root / "evaluations" / "dataset_bidirectional_roundtrip"
    cases_dir = rt_dir / "cases"

    if not cases_dir.exists():
        print(f"ERROR: Cases directory not found: {cases_dir}")
        print("       Run `python colab/init_datasets.py` first to generate evaluation data.")
        return []

    tasks = []

    for case_dir in sorted(cases_dir.iterdir()):
        if not case_dir.is_dir():
            continue
        case_id = case_dir.name

        if case_filter and case_id != case_filter:
            continue

        variants_dir = case_dir / "variants"
        if not variants_dir.exists():
            continue

        for variant_dir in sorted(variants_dir.iterdir()):
            if not variant_dir.is_dir():
                continue
            cond_id = variant_dir.name

            if condition_filter and cond_id != condition_filter:
                continue

            spec_path = variant_dir / "render_spec_variant.json"
            if not spec_path.exists():
                continue

            tasks.append({
                "case_id": case_id,
                "condition_id": cond_id,
                "variant_dir": str(variant_dir),
                "render_spec_path": str(spec_path),
                "base_case_dir": str(case_dir),
            })

    return tasks


def merge_render_spec(variant_spec: dict) -> dict:
    """Merge base render_spec with condition overrides into a single engine-ready config."""
    base = dict(variant_spec.get("base_render_spec", {}))
    overrides = variant_spec.get("overrides", {})

    merged = {**base}

    # Camera override: modify trajectory generation parameters
    if "camera_override" in overrides:
        cam = overrides["camera_override"]
        merged["camera_azimuth_range_deg"] = cam.get("azimuth_range_deg", 360)
        merged["camera_num_views"] = cam.get("num_views", 36)

    # Background
    if "background" in overrides:
        bg = overrides["background"]
        merged["background_type"] = bg.get("type", "solid_gray")
        if bg.get("hdri"):
            merged["hdri_environment"] = bg["hdri"]

    # Lighting
    if "lighting" in overrides:
        light = overrides["lighting"]
        merged["light_type"] = light.get("type", "area_soft")
        merged["light_intensity"] = light.get("intensity", 1.0)
        if light.get("color_temp_K"):
            merged["light_color_temp_K"] = light["color_temp_K"]

    # Material override (uniform material for controlled experiments)
    if "material_override" in overrides:
        mat = overrides["material_override"]
        merged["material_roughness_override"] = mat.get("roughness")
        merged["material_metallic_override"] = mat.get("metallic")
        merged["material_transmission_override"] = mat.get("transmission")

    # Capture quality: resolution & post-process degradation
    if "capture_quality" in overrides:
        cq = overrides["capture_quality"]
        merged["resolution"] = cq.get("resolution", [1920, 1080])
        merged["output_codec"] = cq.get("codec", "exr_lossless")
        merged["noise_sigma"] = cq.get("noise_sigma", 0.0)

    # Motion
    if "motion" in overrides:
        motion = overrides["motion"]
        merged["animation_speed_multiplier"] = motion.get("max_speed_m_s", 1.0)
        merged["enable_motion_blur"] = motion.get("motion_blur", False)

    return merged


def render_single_task(task: dict, engine_path: str = None,
                       dry_run: bool = False) -> dict:
    """Execute a single rendering task.

    Returns a result dict with timing and status information.
    """
    variant_dir = Path(task["variant_dir"])
    spec_path = Path(task["render_spec_path"])

    result = {
        "case_id": task["case_id"],
        "condition_id": task["condition_id"],
        "status": "pending",
        "start_time": None,
        "end_time": None,
        "duration_sec": None,
        "frames_rendered": 0,
        "error": None,
    }

    # Load variant spec
    with open(spec_path, "r", encoding="utf-8") as f:
        variant_spec = json.load(f)

    merged_spec = merge_render_spec(variant_spec)

    if dry_run:
        result["status"] = "dry_run"
        result["merged_spec"] = merged_spec
        print(f"  [DRY] {task['case_id']} / {task['condition_id']} — "
              f"{merged_spec.get('frame_count', '?')} frames @ {merged_spec.get('resolution', '?')}")
        return result

    # Create output directories
    frames_dir = variant_dir / "frames"
    frames_dir.mkdir(exist_ok=True)
    for aov in ["aov_depth", "aov_normal", "aov_motion"]:
        (variant_dir / aov).mkdir(exist_ok=True)

    # Write merged spec for engine consumption
    merged_spec_path = variant_dir / "merged_render_spec.json"
    with open(merged_spec_path, "w", encoding="utf-8") as f:
        json.dump(merged_spec, f, indent=2, ensure_ascii=False)

    # Determine engine binary
    if engine_path is None:
        # Try to find caelum-core or fulgur in PATH
        for candidate in ["caelum-core", "fulgur"]:
            if shutil.which(candidate):
                engine_path = candidate
                break

    if engine_path is None:
        result["status"] = "error"
        result["error"] = "No rendering engine found in PATH. Install caelum-core or fulgur."
        print(f"  [ERR] {task['case_id']} / {task['condition_id']} — {result['error']}")
        return result

    # Build command line
    cmd = [
        engine_path,
        "--headless",
        f"--config={merged_spec_path}",
        f"--output={frames_dir}",
    ]

    # Load trajectory from base case
    trajectory_path = Path(task["base_case_dir"]) / "trajectory.json"
    if trajectory_path.exists():
        cmd.append(f"--trajectory={trajectory_path}")

    result["start_time"] = datetime.now(timezone.utc).isoformat()
    t0 = time.monotonic()

    try:
        print(f"  [RUN] {task['case_id']} / {task['condition_id']} — "
              f"cmd: {' '.join(cmd[:3])}...")

        proc = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=3600,  # 1-hour timeout per task
        )

        result["end_time"] = datetime.now(timezone.utc).isoformat()
        result["duration_sec"] = round(time.monotonic() - t0, 2)

        if proc.returncode == 0:
            # Count rendered frames
            rendered = list(frames_dir.glob("frame_*.exr")) + list(frames_dir.glob("frame_*.png"))
            result["frames_rendered"] = len(rendered)
            result["status"] = "success"
            print(f"  [OK]  {task['case_id']} / {task['condition_id']} — "
                  f"{result['frames_rendered']} frames in {result['duration_sec']}s")
        else:
            result["status"] = "error"
            result["error"] = proc.stderr[:500] if proc.stderr else f"Exit code {proc.returncode}"
            print(f"  [ERR] {task['case_id']} / {task['condition_id']} — {result['error'][:100]}")

    except subprocess.TimeoutExpired:
        result["status"] = "timeout"
        result["error"] = "Rendering timed out (>3600s)"
        result["duration_sec"] = round(time.monotonic() - t0, 2)
        print(f"  [TMO] {task['case_id']} / {task['condition_id']} — Timeout")

    except Exception as e:
        result["status"] = "error"
        result["error"] = str(e)
        result["duration_sec"] = round(time.monotonic() - t0, 2)
        print(f"  [ERR] {task['case_id']} / {task['condition_id']} — {e}")

    # Write render log
    with open(variant_dir / "render_log.json", "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2, ensure_ascii=False)

    return result


def run_matrix(data_root: Path, case_filter: str = None,
               condition_filter: str = None, engine_path: str = None,
               dry_run: bool = False, workers: int = 1) -> dict:
    """Run the full rendering condition matrix.

    Returns summary dict with aggregate stats.
    """
    tasks = discover_render_tasks(data_root, case_filter, condition_filter)

    if not tasks:
        print("No rendering tasks found. Ensure init_datasets.py has been run.")
        return {"total": 0, "success": 0, "error": 0}

    print(f"\n{'='*60}")
    print(f" DervGen: Rendering Condition Matrix Batch Renderer")
    print(f" Data root: {data_root}")
    print(f" Tasks: {len(tasks)} | Workers: {workers} | Dry run: {dry_run}")
    print(f"{'='*60}\n")

    results = []

    if workers <= 1 or dry_run:
        for task in tasks:
            result = render_single_task(task, engine_path, dry_run)
            results.append(result)
    else:
        with ProcessPoolExecutor(max_workers=workers) as executor:
            futures = {
                executor.submit(render_single_task, task, engine_path, dry_run): task
                for task in tasks
            }
            for future in as_completed(futures):
                try:
                    result = future.result()
                    results.append(result)
                except Exception as e:
                    task = futures[future]
                    results.append({
                        "case_id": task["case_id"],
                        "condition_id": task["condition_id"],
                        "status": "error",
                        "error": str(e),
                    })

    # Summary
    summary = {
        "total": len(results),
        "success": sum(1 for r in results if r["status"] == "success"),
        "error": sum(1 for r in results if r["status"] == "error"),
        "timeout": sum(1 for r in results if r["status"] == "timeout"),
        "dry_run": sum(1 for r in results if r["status"] == "dry_run"),
        "total_frames": sum(r.get("frames_rendered", 0) for r in results),
        "total_duration_sec": sum(r.get("duration_sec", 0) for r in results if r.get("duration_sec")),
        "completed_at": datetime.now(timezone.utc).isoformat(),
    }

    # Write summary to data root
    summary_path = data_root / "evaluations" / "dataset_bidirectional_roundtrip" / "rendering_conditions" / "render_matrix_summary.json"
    summary_path.parent.mkdir(parents=True, exist_ok=True)
    with open(summary_path, "w", encoding="utf-8") as f:
        json.dump({"summary": summary, "results": results}, f, indent=2, ensure_ascii=False)

    print(f"\n{'='*60}")
    print(f" Rendering Matrix Complete")
    print(f" Total: {summary['total']} | Success: {summary['success']} | "
          f"Errors: {summary['error']} | Timeouts: {summary['timeout']}")
    if summary['total_duration_sec'] > 0:
        print(f" Total render time: {summary['total_duration_sec']:.1f}s "
              f"({summary['total_duration_sec']/3600:.2f}h)")
        print(f" Total frames: {summary['total_frames']}")
    print(f" Summary: {summary_path}")
    print(f"{'='*60}\n")

    return summary


def main():
    parser = argparse.ArgumentParser(
        description="DervGen Rendering Condition Matrix Batch Renderer",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # List all tasks (dry run)
  python tools/render_roundtrip_matrix.py --data-root ./data --dry-run

  # Render all conditions for a single case
  python tools/render_roundtrip_matrix.py --data-root ./data --case rt_grab_01_pistol_grip_contact

  # Render baseline condition only across all cases
  python tools/render_roundtrip_matrix.py --data-root ./data --condition cond_baseline

  # Full matrix with 4 parallel GPU workers
  python tools/render_roundtrip_matrix.py --data-root ./data --farm --workers 4
        """
    )
    parser.add_argument("--data-root", type=str, required=True,
                        help="Path to dervgen data directory (e.g., /content/drive/MyDrive/dervgen/data)")
    parser.add_argument("--case", type=str, default=None,
                        help="Filter to a specific RT case ID (e.g., rt_grab_01_pistol_grip_contact)")
    parser.add_argument("--condition", type=str, default=None,
                        help="Filter to a specific condition ID (e.g., cond_baseline, cond_f1_L3)")
    parser.add_argument("--engine", type=str, default=None,
                        help="Path to rendering engine binary (auto-detect caelum-core/fulgur if omitted)")
    parser.add_argument("--dry-run", action="store_true",
                        help="List tasks and merged specs without actually rendering")
    parser.add_argument("--farm", action="store_true",
                        help="Enable parallel rendering via caelum-farm")
    parser.add_argument("--workers", type=int, default=1,
                        help="Number of parallel GPU workers (default: 1, use with --farm)")

    args = parser.parse_args()

    data_root = Path(args.data_root)
    if not data_root.exists():
        print(f"ERROR: Data root does not exist: {data_root}")
        sys.exit(1)

    workers = args.workers if args.farm else 1

    summary = run_matrix(
        data_root=data_root,
        case_filter=args.case,
        condition_filter=args.condition,
        engine_path=args.engine,
        dry_run=args.dry_run,
        workers=workers,
    )

    sys.exit(0 if summary.get("error", 0) == 0 else 1)


if __name__ == "__main__":
    main()
