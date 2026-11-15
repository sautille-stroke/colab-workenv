#!/usr/bin/env python3
"""
Exp08: End-to-End Ablation Scorecard Pipeline Runner
Executes Step 7 (Quantitative Evaluation) + 4-Group Ablation Comparison.
"""

import argparse
import sys
from pathlib import Path

EXPERIMENT_DIR = Path(__file__).resolve().parent
PIPELINE_DIR = EXPERIMENT_DIR / "pipeline"
sys.path.insert(0, str(PIPELINE_DIR))

import step7_metrics_evaluation
import ablation_comparator

ALL_CASES = [
    "case_01_mech_ranger",
    "case_02_cyber_hunter",
    "case_03_cinematic_orbit",
]


def run_case(case_id: str, step: str):
    print("\n" + "=" * 75)
    print(" exp08: End-to-End Ablation Scorecard")
    print(f" Case: [{case_id}] | Step: [{step}]")
    print("=" * 75)

    if step in ["all", "metrics"]:
        step7_metrics_evaluation.run_step7(case_id=case_id)
    if step in ["all", "ablation"]:
        ablation_comparator.run_ablation_comparison(case_id=case_id)

    print(f"\n{'='*75}")
    print(f"exp08 evaluation for [{case_id}] finished!")
    print("=" * 75 + "\n")


def main():
    parser = argparse.ArgumentParser(
        description="Exp08: End-to-End Ablation Scorecard"
    )
    parser.add_argument(
        "--step", default="all",
        choices=["all", "metrics", "ablation"],
        help="'metrics' = Step 7 only, 'ablation' = comparator only, 'all' = both"
    )
    parser.add_argument(
        "--case", default="case_01_mech_ranger",
        choices=ALL_CASES + ["all"],
    )
    args = parser.parse_args()
    target_cases = ALL_CASES if args.case == "all" else [args.case]
    for cid in target_cases:
        run_case(case_id=cid, step=args.step)


if __name__ == "__main__":
    main()
