# Exp08: End-to-End Ablation Scorecard

> **ID**: `exp08_e2e_ablation_scorecard`
> **Status**: Active
> **Upstream**: exp05 + exp06 + exp07 (consumes 4 组成片与遥测数据)
> **Downstream**: None (终端评测实验)
> **Synapse 映射**: 对应 `synapse.pipeline` Stage 5 (统一剪辑与评分)；依托 `synapse.metrics` 与 `synapse.bench.scenario`
> **Synapse-Bench 梯队**: T5 (端到端全链路消融评分)

---

## 实验假设

完整双向闭环管线 (Exp05→06→07 = Group D) 在所有 **6 项 SLA 指标**上同时达标（100% 通过率），
综合得分显著优于任何单阶段消融组 (Group A / B / C)。

## 4 组消融对比设计

| 组别 | 方案 | 预期优势 | 预期瓶颈 |
|---|---|---|---|
| **Group A** | 纯 3D 物理离线渲染 (caelum-core 128spp + OIDN) | 几何 100% 正确 | 缺乏生成式微表面动态 |
| **Group B** | 纯生成视频扩散 (Veo 2 / Seedance) | 极致电影光影 | 穿模 12.5%, 滑步 6.42 cm/s |
| **Group C** | 全局 ControlNet 重绘 | 修复物理缺陷 | 破坏原始光影, 时间闪烁 |
| **Group D** | **双向闭环微创手术刀 (本方案)** | **穿模 0% + 保留光影** | 需要 3 个上游实验 |

## 6 项 SLA 评分维度

| 指标 | 验收门禁 | Group B (纯生成) | Group D (本方案) |
|---|---|---|---|
| 足底滑步速度 | < 0.5 cm/s | 6.42 cm/s | **< 0.3 cm/s** |
| 穿模帧率 | 0.0% | 12.5% | **0.0%** |
| 体积呼吸漂移 | < ±1.5% | ±14.2% | **< ±0.8%** |
| Albedo ΔE | < 2.5 | 18.4 | **< 1.8** |
| PSNR | ≥ 38 dB | baseline | **≥ 42 dB** |
| SSIM | ≥ 0.94 | baseline | **≥ 0.99** |

## 执行命令

```bash
# 完整评测 + 消融对比
python3 experiments/exp08_e2e_ablation_scorecard/run_pipeline.py --case=case_01_mech_ranger

# 仅量化指标计算 (Step 7)
python3 experiments/exp08_e2e_ablation_scorecard/run_pipeline.py --step=metrics --case=all

# 仅消融对比评分卡
python3 experiments/exp08_e2e_ablation_scorecard/run_pipeline.py --step=ablation --case=all
```

## 输出产物

```
output/{case_id}/
├── metrics_report.json           # 6 维量化指标报告
├── ablation_scorecard.json       # 4 组消融对比评分卡
├── ablation_radar.png            # 雷达图可视化
└── group_{a,b,c,d}/             # 各组成片与指标
```

> [!TIP]
> 本实验为**纯评测实验**，不消耗 GPU 生成算力，可反复执行。
> 可独立增加新消融组（如 "仅 Foot IK 不做 Inpaint" 等变体）。
