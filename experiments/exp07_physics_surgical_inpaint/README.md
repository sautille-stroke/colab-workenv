# Exp07: Physics-Guided Surgical Inpainting

> **ID**: `exp07_physics_surgical_inpaint`
> **Status**: Active
> **Upstream**: exp05 (`veo_raw.mp4`, `rigged.glb`) + exp06 (`refined_mocap.bvh`)
> **Downstream**: exp08 (produces `final_master_cinematic.mp4`, FGPP AOVs)
> **Synapse 映射**: 对应 `synapse.pipeline` Stage 4 (局部重渲染与风格对齐)；依托 `synapse.fgpp`, `synapse.composite`, `synapse.style`
> **Synapse-Bench 梯队**: T4 (局部手术刀重绘与风格对齐)

---

## 实验假设

C++ 物理张量 (FGPP LinearDepth + WorldNormal + MotionVector) 引导 ControlNeXt 局部手术刀微创重绘，
可以 **100% 消除肢体武器穿模**，同时在非掩膜区域**保留 ≥ 38 dB PSNR** 的原始电影级光影。

## 三步流水线

```
Step 4: C++ FGPP 物理 AOV 烘焙 (step4_fgpp_physics_bake.py)
   └─ Fulgur Headless 导出 LinearDepth, WorldNormal, MotionVector, Cryptomatte (< 0.4s/帧)
Step 5: Critic VLM 审查 + SAM 2 手术刀掩膜 (step5_critic_vlm_mask.py)
   └─ Google Ultra 20x 并发扫描穿模 → SAM 2 追踪 → 8px 膨胀并集掩膜 M_surgical
Step 6: 物理张量引导手术刀精修 (step6_surgical_inpaint.py)
   └─ ControlNeXt 深度/法线约束局部重绘 → 16px 边缘直方图对齐 → ACEScg 调色
```

## 评测指标

| 指标 | 验收门禁 |
|---|---|
| 穿模帧率 | 0.0% (完全消除) |
| 手术掩膜面积占比 | < 15% (越小越精准) |
| 背景 PSNR | ≥ 38 dB |
| 背景 SSIM | ≥ 0.94 |
| 体积呼吸漂移 | < ±1.5% |

## 执行命令

```bash
# 完整 3 步精修流程
python3 experiments/exp07_physics_surgical_inpaint/run_pipeline.py --case=case_01_mech_ranger

# 仅烘焙 FGPP 物理张量
python3 experiments/exp07_physics_surgical_inpaint/run_pipeline.py --step=4 --case=all

# 仅 VLM 审查 + 掩膜生成
python3 experiments/exp07_physics_surgical_inpaint/run_pipeline.py --step=5 --case=case_02_cyber_hunter
```

## 输出产物

```
checkpoints/{case_id}/
├── fgpp/
│   ├── CameraLinearDepth.exr     # Float32 度量深度
│   ├── WorldNormal.exr           # [-1,1] half3 法线
│   ├── MotionVector.exr          # 亚像素运动向量
│   └── Cryptomatte.exr           # 刚体实例掩膜
├── surgical_masks/mask_NNNN.png  # 逐帧手术刀掩膜
output/{case_id}/
├── pre_grade_frames/             # 精修帧 (调色前, 用于公平 PSNR 计算)
├── master_frames/                # 最终 ACEScg 调色 + 35mm 胶片颗粒
└── final_master_cinematic.mp4    # 最终成片
```
