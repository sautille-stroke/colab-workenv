#!/usr/bin/env python3
"""
Exp06: Video-to-3D Kinematic Distillation Pipeline Runner
Executes Step 3 (CoTracker3 + DROID-SLAM + GVHMR + Foot-Plant IK + Albedo De-lighting).
"""

import argparse
import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

EXPERIMENT_DIR = Path(__file__).resolve().parent
PIPELINE_DIR = EXPERIMENT_DIR / "pipeline"
sys.path.insert(0, str(PIPELINE_DIR))

import step3_distill_and_refine

ALL_CASES = [
    "case_01_mech_ranger",
    "case_02_cyber_hunter",
    "case_03_cinematic_orbit",
]


def run_case(case_id: str, input_dir: str = None):
    print("\n" + "=" * 75)
    print(" exp06: Kinematic Distillation & De-lighting")
    print(f" Case: [{case_id}]")
    print("=" * 75)

    step3_distill_and_refine.run_step3(case_id=case_id)

    print(f"\n{'='*75}")
    print(f"exp06 pipeline for [{case_id}] finished!")
    print("=" * 75 + "\n")


def main():
    parser = argparse.ArgumentParser(
        description="Exp06: Video-to-3D Kinematic Distillation"
    )
    parser.add_argument(
        "--case", default="case_01_mech_ranger",
        choices=ALL_CASES + ["all"],
    )
    parser.add_argument(
        "--input-dir", default=None,
        help="Override: path to exp05 output dir (for cross-experiment data flow)",
    )
    args = parser.parse_args()
    target_cases = ALL_CASES if args.case == "all" else [args.case]
    for cid in target_cases:
        run_case(case_id=cid, input_dir=args.input_dir)


if __name__ == "__main__":
    main()
