#!/usr/bin/env python3
"""
Exp07: Physics-Guided Surgical Inpainting Pipeline Runner
Executes Step 4 (FGPP Bake) + Step 5 (VLM Critic + SAM 2 Mask) + Step 6 (Surgical Inpaint).
"""

import argparse
import sys
from pathlib import Path

EXPERIMENT_DIR = Path(__file__).resolve().parent
PIPELINE_DIR = EXPERIMENT_DIR / "pipeline"
sys.path.insert(0, str(PIPELINE_DIR))

import step4_fgpp_physics_bake
import step5_critic_vlm_mask
import step6_surgical_inpaint

ALL_CASES = [
    "case_01_mech_ranger",
    "case_02_cyber_hunter",
    "case_03_cinematic_orbit",
]


def run_case(case_id: str, step: str):
    print("\n" + "=" * 75)
    print(" exp07: Physics-Guided Surgical Inpainting")
    print(f" Case: [{case_id}] | Step: [{step}]")
    print("=" * 75)

    if step in ["all", "4"]:
        step4_fgpp_physics_bake.run_step4(case_id=case_id)
    if step in ["all", "5"]:
        step5_critic_vlm_mask.run_step5(case_id=case_id)
    if step in ["all", "6"]:
        step6_surgical_inpaint.run_step6(case_id=case_id)

    print(f"\n{'='*75}")
    print(f"exp07 pipeline for [{case_id}] finished!")
    print("=" * 75 + "\n")


def main():
    parser = argparse.ArgumentParser(
        description="Exp07: Physics-Guided Surgical Inpainting"
    )
    parser.add_argument("--step", default="all", choices=["all", "4", "5", "6"])
    parser.add_argument(
        "--case", default="case_01_mech_ranger",
        choices=ALL_CASES + ["all"],
    )
    parser.add_argument(
        "--input-dir", default=None,
        help="Override: path to exp05/exp06 output dir (for cross-experiment data flow)",
    )
    args = parser.parse_args()
    target_cases = ALL_CASES if args.case == "all" else [args.case]
    for cid in target_cases:
        run_case(case_id=cid, step=args.step)


if __name__ == "__main__":
    main()
