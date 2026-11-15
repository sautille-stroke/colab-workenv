#!/usr/bin/env python3
"""
Master CLI Pipeline Runner for Bidirectional Neural-Physical Closed Loop (Exp05)
Executes Steps 1 through 7 end-to-end, step-by-step, or across all 3 benchmark cases:
    1. Concept & 3D Mesh (valid PNG + glTF 2.0 .glb)
    2. Video Synthesis (Veo 2 / Seedance / Wan 2.1 -> valid MP4 + RGB frame sequence)
    3. Kinematic Distillation, Metric Scale Alignment & Anti-Slide / Anti-Clip IK
    4. Headless C++ FGPP Physical Baking (valid OpenEXR multi-AOV headers)
    5. Critic VLM & SAM 2 Dilated Union Masking (Hand/Weapon + Foot Stance regions)
    6. Physical Tensor Guided Inpainting, Temporal Blending & ACEScg Grading
    7. Real Quantitative Metric Evaluation & 4-Group Ablation Scorecard
"""

import argparse
import sys
from pathlib import Path

EXPERIMENT_DIR = Path(__file__).resolve().parent
PIPELINE_DIR = EXPERIMENT_DIR / "pipeline"
sys.path.insert(0, str(PIPELINE_DIR))

import step1_concept_and_mesh
import step2_video_synthesis
import step3_distill_and_refine
import step4_fgpp_physics_bake
import step5_critic_vlm_mask
import step6_surgical_inpaint
import step7_metrics_evaluation

ALL_CASES = [
    "case_01_mech_ranger",
    "case_02_cyber_hunter",
    "case_03_cinematic_orbit",
]


def run_case(case_id: str, engine: str, step: str):
    print("\n" + "=" * 75)
    print(" 🚀 DERVGEN CLOSED-LOOP EXPERIMENT CONTROLLER")
    print(f" Case: [{case_id}] | Engine: [{engine}] | Step: [{step}]")
    print("=" * 75)

    if step in ["all", "1"]:
        step1_concept_and_mesh.run_step1(case_id=case_id)
    if step in ["all", "2"]:
        step2_video_synthesis.run_step2(case_id=case_id, engine=engine)
    if step in ["all", "3"]:
        step3_distill_and_refine.run_step3(case_id=case_id)
    if step in ["all", "4"]:
        step4_fgpp_physics_bake.run_step4(case_id=case_id)
    if step in ["all", "5"]:
        step5_critic_vlm_mask.run_step5(case_id=case_id)
    if step in ["all", "6"]:
        step6_surgical_inpaint.run_step6(case_id=case_id)
    if step in ["all", "7"]:
        step7_metrics_evaluation.run_step7(case_id=case_id)

    print("\n" + "=" * 75)
    print(f"🎉 Pipeline execution for [{case_id}] finished successfully!")
    print("=" * 75 + "\n")


def main():
    parser = argparse.ArgumentParser(
        description="Bidirectional Closed Loop Experiment Master Runner"
    )
    parser.add_argument(
        "--step",
        default="all",
        choices=["all", "1", "2", "3", "4", "5", "6", "7"],
        help="Specific pipeline step to run, or 'all'",
    )
    parser.add_argument(
        "--engine",
        default="Google_Veo_2",
        choices=["Google_Veo_2", "Seedance_2.5_API", "Wan_2.1_14B", "Wan_2.1_1.3B"],
        help="Video diffusion generator engine (default: Google_Veo_2)",
    )
    parser.add_argument(
        "--case",
        default="case_01_mech_ranger",
        choices=ALL_CASES + ["all"],
        help="Test case scenario (or 'all' to run all 3 benchmark cases)",
    )
    args = parser.parse_args()

    target_cases = ALL_CASES if args.case == "all" else [args.case]
    for cid in target_cases:
        run_case(case_id=cid, engine=args.engine, step=args.step)


if __name__ == "__main__":
    main()
