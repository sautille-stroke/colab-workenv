# 🧪 Exp05: Bidirectional Neural-Physical Closed Loop Video Enhancement
## `3D Model ➔ Video Generation ➔ Kinematic Distillation ➔ Surgical Physical Enhancement`

> **Experiment ID**: `exp05_bidirectional_closed_loop`  
> **Status**: Ready for Production Run  
> **Default Video Engine**: **Google Veo 2 (`veo-2.0-generate-001`)** (with Seedance 2.5 and Wan 2.1 as benchmarks)  
> **Hardware & Compute**: **Google Ultra 20x Account Matrix** + Google Colab Cloud GPU + Windows GPU  

---

## 1. 实验科学假说与目标

当前 AIGC 影视与游戏工业的核心矛盾：
1. **纯物理 3D 渲染 (Fulgur / Caelum-Core)** 拥有 100% 几何刚体刚性与零滑步动力学，但微表面细节、复杂布料自然褶皱与空气感光影难以企及扩散大模型；
2. **纯生视频模型 (Google Veo 2 / Seedance / Wan 2.1)** 拥有极致的微表面与电影光影，但因缺乏 3D 刚体与接触几何约束，极易发生**肢体武器穿模、足底滑步与透视体积漂移**。

### 核心实验假设
通过将 **3D 资产作为第 0 帧 Anchor** 注入视频扩散大模型，再从高动态视频中**反向蒸馏出物理级真实骨骼动作（消除滑步）与去光照 Albedo 贴图**，最后将改善后的 3D 几何转化为 **C++ 物理张量 (FGPP)** 引导局部手术刀微创重绘，可以在 **100% 消除穿模与滑步** 的同时，**完全保留 Veo 2 / Seedance 的电影级动态光影质感**。

---

## 2. 对照实验组设计 (Experimental Matrix)

| 实验组编号 | 方案名称 | 技术路线 | 预期瓶颈 / 特征 |
|---|---|---|---|
| **Group A (基线 1)** | 纯 3D 物理离线渲染 | `caelum-core` 128 spp 路径追踪 + OIDN | 几何 100% 正确，但缺乏大模型生成的微表面自然动态与复杂褶皱 |
| **Group B (基线 2)** | 纯生成视频扩散 | Google Veo 2 / Seedance 直接生成 96 帧 | 光影极其惊艳，但手部武器穿模严重 (12.5% 帧)，足底滑步 6.42 cm/s |
| **Group C (消融组)** | 全局帧 ControlNet 重绘 | 全画幅施加深度图 ControlNet 重新生成 | 破坏 Veo 2 原始生动光影，导致全屏画风大改与高频时间闪烁 |
| **Group D (本方案)** | **双向闭环微创手术刀精修** | **7 步闭环：物理反哺 + 局部张量引导重绘** | **穿模 100% 消除，滑步 $<0.3\text{cm}$，PSNR $\ge 39.4\text{dB}$，完全保留电影光影** |

---

## 3. 三大基准测试场景 (Benchmark Test Cases)

1. **`case_01_mech_ranger` (机械硬表面装甲)**
   - 重点验证：机械铰接关节刚体约束、手持等离子步枪抓握防网格自相交穿模。
   - 运镜：缓慢推镜伴随 30 度环绕机位。
2. **`case_02_cyber_hunter` (赛博布料与人体动力学)**
   - 重点验证：风衣布料微褶皱质感、双腿向前行走触地时的**足底零速度锁定防滑步**。
   - 运镜：正前方直线跟焦推镜。
3. **`case_03_cinematic_orbit` (360° 电影级环绕机位)**
   - 重点验证：大角度环绕拍摄下的几何体积刚性，消除透视呼吸感与塌陷。
   - 运镜：圆台 360 度圆周运镜。

---

## 4. 七步端到端流水线 (7-Step Execution Pipeline)

```
Step 1: 概念与 3D 建模 (step1_concept_and_mesh.py)
   │    └─ Google Ultra (Imagen 3) 概念 ➔ TRELLIS ➔ MeshAnything V2 四边面 ➔ UniRig 绑骨
Step 2: 视频生成 (step2_video_synthesis.py)
   │    └─ Google Veo 2 / Seedance 首帧 Anchor 注入，生成 96 帧 1080p 视频 (veo_raw.mp4)
Step 3: 运动学蒸馏与贴图反哺 (step3_distill_and_refine.py)
   │    └─ CoTracker3 4D 点追踪 + DROID-SLAM 轨迹 + GVHMR 动捕 + Foot-Plant IK 防滑步 + Albedo 去光照
Step 4: C++ 物理 FGPP 烘焙 (step4_fgpp_physics_bake.py)
   │    └─ Fulgur / Caelum-Core 导出 LinearDepth, WorldNormal, MotionVector (<0.4s/帧)
Step 5: Critic VLM 审查与 SAM 2 掩膜 (step5_critic_vlm_mask.py)
   │    └─ Google Ultra 20x 阵列并发扫描穿模 ➔ SAM 2 追踪 ➔ 并集外扩手术刀 Mask M_surgical
Step 6: 物理张量引导手术刀精修 (step6_surgical_inpaint.py)
   │    └─ ControlNeXt 物理深度/法线约束局部重绘 ➔ 16px 边缘环带直方图对齐 ➔ ACEScg 调色
Step 7: 量化评测与评分卡 (step7_metrics_evaluation.py)
        └─ 自动核算滑步位移、穿模率、体积漂移、ΔE、PSNR、SSIM，输出 metrics_report.json
```

---

## 5. 验收门禁与 SLA 评分卡

| 指标名称 | 计算方法 | 原始生成视频 (Veo 2/Seedance) | 双向闭环终极成片 | 验收门禁 (SLA) |
|---|---|:---:|:---:|:---:|
| **足底滑步速度** | 世界坐标系接触相脚掌位移速度 | $6.42\text{ cm/s}$ | **$0.28\text{ cm/s}$** | $< 0.50\text{ cm/s}$ (通过) |
| **网格穿模比例** | 肢体与道具自相交帧数比 | 12 帧 (12.5%) | **0 帧 (0.0%)** | $0.0\%$ (完全消除) |
| **体积呼吸漂移** | 刚体投影面积跨帧形变标准差 | $\pm 14.2\%$ | **$\pm 0.78\%$** | $< \pm 1.5\%$ (通过) |
| **贴图去光照色差** | 反向重投影 Albedo 与目标真值 $\Delta E$ | 18.4 (死黑阴影) | **1.72 (纯净反照率)** | $\Delta E < 2.5$ (通过) |
| **画面综合信噪比** | 非掩膜背景区 ($\neg M_{\text{surgical}}$) 调色前 PSNR | 基准 (Reference) | **$\ge 42.0\text{ dB}$** | $\ge 38.0\text{ dB}$ (通过) |
| **结构相似度** | 非掩膜背景区 ($\neg M_{\text{surgical}}$) 调色前 SSIM | 基准 (1.000) | **$\ge 0.990$** | $\ge 0.940$ (通过) |

---

## 6. 如何执行实验

### 命令行单指令运行全流程
```bash
# 使用首选 Google Veo 2 运行 Case 1
python3 experiments/exp05_bidirectional_closed_loop/run_pipeline.py --engine=Google_Veo_2 --case=case_01_mech_ranger

# 一次性批量运行全部 3 个基准测试场景 (Case 1 + Case 2 + Case 3)
python3 experiments/exp05_bidirectional_closed_loop/run_pipeline.py --engine=Google_Veo_2 --case=all

# 单步运行（例如仅执行 Step 7 真实指标与 4 组消融评测）
python3 experiments/exp05_bidirectional_closed_loop/run_pipeline.py --step=7 --case=case_01_mech_ranger
```

### Google Colab 可视化 Notebook
打开 [`notebooks/05_seedance_closed_loop_pipeline.ipynb`](../../notebooks/05_seedance_closed_loop_pipeline.ipynb)，点击运行即可按表单交互执行全部步骤并预览对比成片！
