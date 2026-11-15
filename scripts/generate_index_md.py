#!/usr/bin/env python3
"""
Generate models/INDEX.md from models/INDEX.json
"""

import json
from pathlib import Path

WORKSPACE_ROOT = Path(__file__).resolve().parent.parent
INDEX_JSON_PATH = WORKSPACE_ROOT / "models" / "INDEX.json"
INDEX_MD_PATH = WORKSPACE_ROOT / "models" / "INDEX.md"

def main():
    with open(INDEX_JSON_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)

    models = data["models"]
    usages = sorted(list(set(m["usage"] for m in models)))
    p0_count = sum(1 for m in models if m.get("priority") == "P0")
    p1_count = sum(1 for m in models if m.get("priority") == "P1")

    lines = [
        "# DervGen Model Catalog & Index (SSOT)",
        "",
        "> **Location in Google Drive**: `/content/drive/MyDrive/dervgen/model/`  ",
        "> **Local Repo Location**: `models/INDEX.json` & `models/INDEX.md`  ",
        f"> **Catalog Version**: `v{data.get('version', '1.6.0')}` | **Last Updated**: `{data.get('updated_at', '')[:10]}`  ",
        "> **Ecosystem Alignment**: `grand-studio` (GF-ARCH-0044 Master Pipelines & Asset Distillation), `vg-core` (Vision-Graphics Transmutation), `graphics-radar` (SOTA Evaluation), `caelum-core` (OpenPBR Path Tracing), `fulgur` (Real-time Rendering & Fast GBuffer AOV Exporter), `asset-forge` (Topology & Rigging).",
        "",
        "All model weights in the DervGen cloud ecosystem are strictly organized under `/dervgen/model/{usage}/`.",
        "",
        "---",
        "",
        f"## 📋 Comprehensive Model Registry ({len(models)} Curated Models Across {len(usages)} Usages)",
        "",
        f"- **P0 (Core Production Baseline)**: {p0_count} models",
        f"- **P1 (Extended & Auxiliary Pipelines)**: {p1_count} models",
        "",
        "| ID | Domain / Usage | Model Name | Drive Target File Path | Size | Priority | Ecosystem Role & Frontier Source |",
        "|---|---|---|---|---|---|---|",
    ]

    usage_order = ["foundation", "3d_recon", "texture_gen", "actor_dynamics", "video_gen", "denoise_upscale", "audio_foley"]

    def sort_key(m):
        u = m["usage"]
        u_idx = usage_order.index(u) if u in usage_order else 99
        p_idx = 0 if m.get("priority") == "P0" else 1
        return (u_idx, p_idx, m["id"])

    sorted_models = sorted(models, key=sort_key)

    for m in sorted_models:
        if m.get("type") == "api_config":
            size_str = "~1 MB (API)"
        elif m.get("size_mb", 0) < 1024:
            size_str = f"~{m['size_mb']} MB"
        else:
            size_str = f"~{m['size_mb'] / 1024:.2f} GB"

        prio_str = f"**{m['priority']}**" if m.get("priority") == "P0" else m.get("priority", "P1")
        lines.append(
            f"| `{m['id']}` | `{m['usage']}` | **{m['name']}** | `{m['target_file']}` | {size_str} | {prio_str} | {m['description']} |"
        )

    lines.extend([
        "",
        "---",
        "",
        "## ⚡ Quick Start in Colab",
        "",
        "```bash",
        "# 1. 一键拉取 P0 核心主力套件 (含 NVIDIA Cosmos, Wan 2.1, Oasis, CoTracker, TRELLIS 等)",
        "python3 /content/workspace/colab/init_models.py --preset=P0",
        "",
        "# 2. 极速烟测套件 (快速下载轻量模型 ~3GB，用于验证 Drive 挂载与管线连通性)",
        "python3 /content/workspace/colab/init_models.py --preset=fast",
        "",
        "# 3. 定向拉取视频与交互世界模型",
        "python3 /content/workspace/colab/init_models.py --usage=video_gen",
        "",
        "# 4. 定向拉取 3D 几何与点云重建模型",
        "python3 /content/workspace/colab/init_models.py --usage=3d_recon",
        "",
        "# 5. 同步刷新 Google Drive live inventory 索引",
        "python3 /content/workspace/colab/init_models.py --sync-index",
        "```",
    ])

    with open(INDEX_MD_PATH, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")

    print(f"Successfully generated {INDEX_MD_PATH} with {len(sorted_models)} models.")

if __name__ == "__main__":
    main()
