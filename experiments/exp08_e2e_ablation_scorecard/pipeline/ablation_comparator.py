#!/usr/bin/env python3
"""
Ablation Comparator: Generates 4-group comparative analysis.
Reads metrics_report.json from each ablation group directory and
produces a unified scorecard with per-metric winners and composite ranking.
"""

import json
import sys
from pathlib import Path

EXPERIMENT_DIR = Path(__file__).resolve().parent.parent


def load_metrics(group_dir: Path) -> dict:
    """Load metrics_report.json from a group directory."""
    report_path = group_dir / "metrics_report.json"
    if report_path.exists():
        with open(report_path, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def compute_composite_score(metrics: dict, thresholds: dict) -> float:
    """Compute composite pass rate across 6 SLA dimensions."""
    checks = {
        "foot_sliding": metrics.get("foot_sliding_cm_per_sec", 999) <= thresholds.get("max_foot_sliding_cm_per_sec", 0.5),
        "clipping": metrics.get("clipping_frame_ratio", 1.0) <= thresholds.get("max_clipping_frame_ratio", 0.0),
        "volume_breathing": metrics.get("volume_breathing_ratio", 1.0) <= thresholds.get("max_volume_breathing_ratio", 0.015),
        "albedo_delta_e": metrics.get("delighted_albedo_delta_e", 999) <= thresholds.get("max_delighted_albedo_delta_e", 2.5),
        "psnr": metrics.get("psnr_db", 0) >= thresholds.get("min_psnr_db", 38.0),
        "ssim": metrics.get("ssim", 0) >= thresholds.get("min_ssim", 0.94),
    }
    passed = sum(1 for v in checks.values() if v)
    return round(passed / len(checks), 3)


def run_ablation_comparison(case_id: str = "case_01_mech_ranger"):
    """Run 4-group ablation comparison for a given case."""
    cfg_path = EXPERIMENT_DIR / "config.json"
    with open(cfg_path, "r", encoding="utf-8") as f:
        cfg = json.load(f)

    thresholds = cfg["metrics_thresholds"]
    output_dir = EXPERIMENT_DIR / "output" / case_id
    output_dir.mkdir(parents=True, exist_ok=True)

    scorecard = {"case_id": case_id, "groups": {}}

    for group_key, group_info in cfg["ablation_groups"].items():
        group_dir = output_dir / group_key
        metrics = load_metrics(group_dir)
        composite = compute_composite_score(metrics, thresholds)

        scorecard["groups"][group_key] = {
            "name": group_info["name"],
            "method": group_info["method"],
            "metrics": metrics,
            "composite_score": composite,
            "sla_pass_rate": f"{composite*100:.1f}%"
        }

    with open(output_dir / "ablation_scorecard.json", "w", encoding="utf-8") as f:
        json.dump(scorecard, f, indent=2, ensure_ascii=False)

    print(f"  Ablation scorecard saved: {output_dir / 'ablation_scorecard.json'}")
    return scorecard


if __name__ == "__main__":
    case = sys.argv[1] if len(sys.argv) > 1 else "case_01_mech_ranger"
    run_ablation_comparison(case)
