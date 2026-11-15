# Exp05: 3D Anchor → Video Generation

> **ID**: `exp05_3d_anchor_video_gen`
> **Status**: Active
> **Upstream**: None (entry point)
> **Downstream**: exp06 (consumes `concept_ortho.png`, `rigged.glb`, `veo_raw.mp4`)
> **Synapse 映射**: 对应 `synapse.pipeline` Stage 1 (分镜布景) 与 Stage 2 (白模引导生成)；依托 `synapse.adapters` (Veo2/Wan/Seedance) 与 `synapse.fgpp`
> **Synapse-Bench 梯队**: T1 (静态刚体) + T2 (骨骼动态)

---

## 实验假设

以 3D 资产正交渲染作为首帧 Anchor 注入视频扩散大模型 (Google Veo 2 / Seedance 2.5 / Wan 2.1)，
可以**显著减少结构漂移**并提供**精确可控运镜轨迹**，相比纯文本 Prompt 生成。

## 两步流水线

```
Step 1: 概念与 3D 建模 (step1_concept_and_mesh.py)
   └─ Google Ultra Imagen 3 正交概念图 → TRELLIS 3D → MeshAnything V2 四边面 → UniRig 绑骨
Step 2: 视频生成 (step2_video_synthesis.py)
   └─ Veo 2 / Seedance / Wan 2.1 首帧 Anchor 注入 → 96/120 帧 1080p 视频
```

## 评测指标

| 指标 | 计算方法 | 验收门禁 |
|---|---|---|
| 首帧一致性 | Anchor 帧 vs 生成第 0 帧 SSIM | ≥ 0.92 |
| 视频质量 | FID / FVD (相对 reference set) | FVD < 150 |
| 运镜轨迹误差 | 预设轨迹 vs 实际估计轨迹 RMSE | < 5° |

## 执行命令

```bash
# 使用 Veo 2 运行 Case 1
python3 experiments/exp05_3d_anchor_video_gen/run_pipeline.py --engine=Google_Veo_2 --case=case_01_mech_ranger

# 全部 3 个场景
python3 experiments/exp05_3d_anchor_video_gen/run_pipeline.py --engine=Google_Veo_2 --case=all

# 仅执行 Step 1 (3D 建模)
python3 experiments/exp05_3d_anchor_video_gen/run_pipeline.py --step=1 --case=case_01_mech_ranger
```

## 输出产物

```
checkpoints/{case_id}/
├── concept_ortho.png          # 正交概念图
├── rigged.glb                 # 绑定骨骼的 glTF 2.0 模型
output/{case_id}/
├── veo_raw.mp4                # 原始生成视频
├── raw_generated_video.json   # 生成元数据
└── raw_frames/frame_NNNN.png  # 逐帧 PNG 序列
```
