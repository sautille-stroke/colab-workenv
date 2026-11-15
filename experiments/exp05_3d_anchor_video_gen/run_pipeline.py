#!/usr/bin/env python3
"""
Exp05: 3D Anchor -> Video Generation Pipeline Runner
Executes Step 1 (Concept & 3D Mesh) and Step 2 (Video Synthesis).
"""

import argparse
import sys
from pathlib import Path

EXPERIMENT_DIR = Path(__file__).resolve().parent
PIPELINE_DIR = EXPERIMENT_DIR / "pipeline"
sys.path.insert(0, str(PIPELINE_DIR))

import step1_concept_and_mesh
import step2_video_synthesis

ALL_CASES = [
    "case_01_mech_ranger",
    "case_02_cyber_hunter",
    "case_03_cinematic_orbit",
]


def run_case(case_id: str, engine: str, step: str):
    print("\n" + "=" * 75)
    print(" exp05: 3D Anchor -> Video Generation")
    print(f" Case: [{case_id}] | Engine: [{engine}] | Step: [{step}]")
    print("=" * 75)

    if step in ["all", "1"]:
        step1_concept_and_mesh.run_step1(case_id=case_id)
    if step in ["all", "2"]:
        step2_video_synthesis.run_step2(case_id=case_id, engine=engine)

    print(f"\n{'='*75}")
    print(f"exp05 pipeline for [{case_id}] finished!")
    print("=" * 75 + "\n")


def main():
    parser = argparse.ArgumentParser(
        description="Exp05: 3D Anchor -> Video Generation"
    )
    parser.add_argument("--step", default="all", choices=["all", "1", "2"])
    parser.add_argument(
        "--engine", default="Google_Veo_2",
        choices=["Google_Veo_2", "Seedance_2.5_API", "Wan_2.1_14B", "Wan_2.1_1.3B"],
    )
    parser.add_argument(
        "--case", default="case_01_mech_ranger",
        choices=ALL_CASES + ["all"],
    )
    args = parser.parse_args()
    target_cases = ALL_CASES if args.case == "all" else [args.case]
    for cid in target_cases:
        run_case(case_id=cid, engine=args.engine, step=args.step)


if __name__ == "__main__":
    main()
