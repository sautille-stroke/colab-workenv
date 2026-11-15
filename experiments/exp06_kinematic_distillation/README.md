# Exp06: Video → 3D Kinematic Distillation

> **ID**: `exp06_kinematic_distillation`
> **Status**: Active
> **Upstream**: exp05 (consumes `veo_raw.mp4`, `rigged.glb`)
> **Downstream**: exp07 (produces `refined_mocap.bvh`, `albedo_delighted.png`)
> **Synapse 映射**: 对应 `synapse.pipeline` Stage 3 (精细 3D 建模与逆向反哺)；依托 `vg-core` 逆向算法与 `actor-core` 防滑步 IK
> **Synapse-Bench 梯队**: T2 (骨骼动态) + T3 (刚体交互)

---

## 实验假设

从高动态 AI 生成视频中可以**反向蒸馏出物理级真实骨骼动作**（消除足底滑步至 < 0.3 cm/s）和
**去光照 Albedo 贴图**（ΔE < 2.0），精度和自然度超越纯 MoCap 管线。

## 技术组件

| 模块 | 算法 | 职责 |
|---|---|---|
| 4D 点追踪 | CoTracker3 (stride=4) | 全帧密集光流追踪 |
| SLAM 定位 | DROID-SLAM | 单目相机轨迹与度量尺度恢复 |
| 人体动捕 | GVHMR v1 | 从视频估计 SMPL-X 骨骼序列 |
| 度量深度 | Depth Anything V2 Metric | 校准 SLAM 至真实世界尺度 |
| 去光照 | IntrinsicAnything | 分离 Albedo / Shading / Specular |
| IK 后处理 | Foot-Plant IK + Collision-Free IK | 物理约束的脚底锁定和碰撞消解 |

## 评测指标

| 指标 | 计算方法 | 验收门禁 |
|---|---|---|
| 足底滑步速度 | 接触相脚掌世界位移速度 | < 0.3 cm/s |
| 骨骼关节误差 | 蒸馏 vs GT 关节角度 RMSE | < 5° |
| Albedo 色差 | 去光照 vs GT DeltaE (CIELAB) | ΔE < 2.0 |

## 执行命令

```bash
# 运行 Case 1 蒸馏
python3 experiments/exp06_kinematic_distillation/run_pipeline.py --case=case_01_mech_ranger

# 指定 exp05 输出目录作为输入
python3 experiments/exp06_kinematic_distillation/run_pipeline.py --case=all \
    --input-dir=experiments/exp05_3d_anchor_video_gen/output
```

## 输出产物

```
checkpoints/{case_id}/
├── refined_mocap.bvh                # 物理约束骨骼动画
├── albedo_gt.png                    # Ground truth 去光照纹理
├── albedo_raw_baked.png             # 原始带烘焙阴影投影纹理
├── albedo_delighted.png             # IntrinsicAnything 去光照结果
├── camera_trajectory_solved.json    # DROID-SLAM 轨迹
└── kinematics_telemetry.json        # 逐帧运动学遥测
```
