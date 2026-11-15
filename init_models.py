#!/usr/bin/env python3
"""
DervGen Workspace: Automated Cloud Model Pre-fetcher & Index Sync
Directly downloads model weights into Google Drive (/dervgen/data/models/{usage}/...)
and maintains real-time INDEX.json and INDEX.md in Google Drive root.
Supports:
  - API configuration descriptors (`type == "api_config"`, e.g. Google Veo 2)
  - Automatic `.tar.gz` member extraction (e.g. Intel OIDN 2.3 `.tza` weights)
  - HTML error-page guard (rejects 404/login HTML responses masquerading as weights)
"""

import os
import sys
import json
import tarfile
import argparse
import urllib.request
import urllib.parse
import ssl
import http.cookiejar
import re
from datetime import datetime, timezone
from pathlib import Path

# Safe utf-8 stdout for terminals
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

SCRIPT_DIR = Path(__file__).resolve().parent
WORKSPACE_ROOT = SCRIPT_DIR.parent
REGISTRY_PATH = SCRIPT_DIR / "models" / "INDEX.json"
FALLBACK_REGISTRY = SCRIPT_DIR / "models" / "model_registry.json"
DRIVE_ROOT = Path(os.environ.get("DERVGEN_DRIVE_ROOT", "/content/drive/MyDrive/dervgen"))
DEFAULT_HF_TOKEN = ""  # Use Colab Secrets: userdata.get('HF_TOKEN')

try:
    from tqdm import tqdm

    class DownloadProgressBar(tqdm):
        def update_to(self, b=1, bsize=1, tsize=None):
            if tsize is not None:
                self.total = tsize
            self.update(b * bsize - self.n)
except ImportError:
    class DownloadProgressBar:
        def __init__(self, *args, **kwargs):
            self.desc = kwargs.get("desc", "Downloading")
            self.total = kwargs.get("total", None)

        def __enter__(self):
            print(f"{self.desc}...")
            return self

        def __exit__(self, exc_type, exc_val, exc_tb):
            pass

        def update(self, n=1):
            pass

        def update_to(self, b=1, bsize=1, tsize=None):
            pass


def check_drive_mounted() -> bool:
    drive_base = Path("/content/drive/MyDrive")
    if not drive_base.exists() and not os.environ.get("DERVGEN_DRIVE_ROOT"):
        print("⚠️  [Init Models] Google Drive is NOT mounted at /content/drive/MyDrive.")
        print("    In Colab run: from google.colab import drive; drive.mount('/content/drive')")
        return False
    return True


def load_registry():
    path = REGISTRY_PATH if REGISTRY_PATH.exists() else FALLBACK_REGISTRY
    if not path.exists():
        print(f"❌ Registry file not found: {REGISTRY_PATH}")
        sys.exit(1)
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def _is_html_payload(file_path: Path) -> bool:
    """Checks if a downloaded file is accidentally an HTML error/login page."""
    try:
        with open(file_path, "rb") as f:
            head = f.read(256).lstrip().lower()
        return head.startswith(b"<!doctype html") or head.startswith(b"<html")
    except Exception:
        return False


def _download_stream(url: str, temp_path: Path, desc: str, hf_token: str = "") -> bool:
    """Streams download from URL to temp_path, handling GDrive virus prompts, HF tokens, and HTML errors."""
    if "drive.google.com" in url or "drive.usercontent.google.com" in url:
        # 1. First attempt gdown if available in Colab
        try:
            import gdown
            res = gdown.download(url, str(temp_path), quiet=False)
            if res and temp_path.exists() and not _is_html_payload(temp_path):
                return True
        except Exception:
            pass

        # 2. Native urllib GDrive large-file confirmation resolution
        cj = http.cookiejar.CookieJar()
        opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }
        with opener.open(urllib.request.Request(url, headers=headers), timeout=30) as resp:
            content_type = resp.headers.get("Content-Type", "")
            if "text/html" in content_type:
                html = resp.read().decode("utf-8", errors="ignore")
                form_action = re.search(r'<form id="download-form" action="([^"]+)"', html)
                if form_action:
                    action_url = form_action.group(1)
                    inputs = re.findall(r'<input type="hidden" name="([^"]+)" value="([^"]+)"', html)
                    query_str = urllib.parse.urlencode(dict(inputs))
                    download_url = f"{action_url}?{query_str}"
                    with opener.open(urllib.request.Request(download_url, headers=headers), timeout=60) as resp2, open(temp_path, "wb") as out_f:
                        total_size = int(resp2.headers.get("Content-Length", 0)) or None
                        with DownloadProgressBar(unit="B", unit_scale=True, miniters=1, desc=desc, total=total_size) as t:
                            if total_size and hasattr(t, "total"):
                                t.total = total_size
                            block_size = 1024 * 1024
                            while True:
                                chunk = resp2.read(block_size)
                                if not chunk:
                                    break
                                out_f.write(chunk)
                                if hasattr(t, "update"):
                                    t.update(len(chunk))
                    if not _is_html_payload(temp_path):
                        return True
                    temp_path.unlink()
                    raise ValueError("Drive download returned HTML error page")

    # Standard URL download (Hugging Face, GitHub, GDrive)
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    req = urllib.request.Request(url, headers=headers)
    if hf_token and "huggingface.co" in url:
        req.add_header("Authorization", f"Bearer {hf_token}")

    ssl_ctx = ssl.create_default_context()
    ssl_ctx.check_hostname = False
    ssl_ctx.verify_mode = ssl.CERT_NONE
    with urllib.request.urlopen(req, context=ssl_ctx, timeout=45) as resp, open(temp_path, "wb") as out_f:
        total_size = int(resp.headers.get("Content-Length", 0)) or None
        with DownloadProgressBar(unit="B", unit_scale=True, miniters=1, desc=desc, total=total_size) as t:
            if total_size and hasattr(t, "total"):
                t.total = total_size
            block_size = 1024 * 1024
            while True:
                chunk = resp.read(block_size)
                if not chunk:
                    break
                out_f.write(chunk)
                if hasattr(t, "update"):
                    t.update(len(chunk))

    if _is_html_payload(temp_path):
        temp_path.unlink()
        raise ValueError(f"Rejected HTML response from {url} (check authorization or URL)")

    return True


def provision_model_entry(model_meta: dict, output_path: Path) -> bool:
    """Downloads or provisions a single model entry into `output_path`."""
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # 1. Handle API Configuration descriptors (e.g. Google Veo 2, DeepSeek-R1, Moonshot Kimi)
    if model_meta.get("type") == "api_config":
        auth_envs = {
            "google_veo_2": "GOOGLE_ULTRA_KEYS",
            "deepseek_r1_reasoning": "DEEPSEEK_API_KEY",
            "moonshot_kimi_k1_5": "MOONSHOT_API_KEY",
            "kuaishou_kling_world": "KLING_API_KEY",
            "minimax_video_01": "MINIMAX_API_KEY",
            "minimax_speech_01": "MINIMAX_API_KEY",
            "minimax_text_01": "MINIMAX_API_KEY",
            "runway_gen3_alpha": "RUNWAY_API_KEY",
            "openai_sora": "OPENAI_API_KEY",
            "zhipu_glm4_plus": "ZHIPUAI_API_KEY",
            "zhipu_glm4v_plus": "ZHIPUAI_API_KEY",
            "zhipu_glm_zero": "ZHIPUAI_API_KEY",
            "zhipu_glm5_3": "ZHIPUAI_API_KEY",
        }
        model_names = {
            "google_veo_2": "veo-2.0-generate-001",
            "deepseek_r1_reasoning": "deepseek-reasoner",
            "moonshot_kimi_k1_5": "moonshot-v1-auto",
            "kuaishou_kling_world": "kling-v1-5",
            "minimax_video_01": "video-01",
            "minimax_speech_01": "speech-01",
            "minimax_text_01": "abab6.5s-chat",
            "runway_gen3_alpha": "gen3a_turbo",
            "openai_sora": "sora-1.0",
            "zhipu_glm4_plus": "glm-4-plus",
            "zhipu_glm4v_plus": "glm-4v-plus",
            "zhipu_glm_zero": "glm-zero-preview",
            "zhipu_glm5_3": "glm-5.3",
        }
        cfg_payload = {
            "id": model_meta["id"],
            "name": model_meta["name"],
            "model_id": model_names.get(model_meta["id"], model_meta["id"]),
            "api_base": model_meta.get("url", ""),
            "auth_env": auth_envs.get(model_meta["id"], f"{model_meta['id'].upper()}_KEY"),
            "description": model_meta.get("description", ""),
        }
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(cfg_payload, f, indent=2)
        print(f"   ✓ Generated API client config: {output_path}")
        return True

    primary_url = model_meta["url"]
    candidate_urls = [primary_url]
    if "black-forest-labs/FLUX.1-dev" in primary_url:
        candidate_urls.append("https://huggingface.co/realung/flux1-dev.safetensors/resolve/main/flux1-dev.safetensors")
    if "black-forest-labs/FLUX.1-Fill-dev" in primary_url:
        candidate_urls.append("https://huggingface.co/camenduru/FLUX.1-Fill-dev-ungated/resolve/main/flux1-fill-dev.safetensors")

    is_tar_gz = model_meta.get("archive_type") == "tar.gz" or (
        primary_url.endswith(".tar.gz") and not output_path.name.endswith(".tar.gz")
    )
    temp_path = output_path.with_suffix(output_path.suffix + (".tar.gz.tmp" if is_tar_gz else ".tmp"))

    desc = f"⬇️  {output_path.name}"
    hf_token = os.environ.get("HF_TOKEN") or ""
    if not hf_token:
        try:
            from google.colab import userdata
            hf_token = userdata.get("HF_TOKEN") or ""
        except Exception:
            pass
    if not hf_token:
        hf_token = DEFAULT_HF_TOKEN

    download_success = False
    for attempt_idx, url in enumerate(candidate_urls):
        try:
            if attempt_idx > 0:
                print(f"   🔄 正在尝试备用镜像源: {url}")
            if _download_stream(url, temp_path, desc, hf_token):
                download_success = True
                break
        except Exception as e:
            if temp_path.exists():
                temp_path.unlink()
            if "403" in str(e) and "huggingface.co" in url:
                repo_match = re.search(r"huggingface\.co/([^/]+/[^/]+)", url)
                repo_name = repo_match.group(1) if repo_match else ""
                print(f"   🔒 HTTP 403 Forbidden: 该模型为 Gated 受限模型（需访问网页接受协议许可）。")
                if repo_name:
                    print(f"      👉 请在浏览器登录 Hugging Face 并点击接受协议：https://huggingface.co/{repo_name}")
            if attempt_idx < len(candidate_urls) - 1:
                print(f"   ⚠️ 首选源下载失败 ({e})，正在自动切换备用源...")
            else:
                print(f"   ❌ Error downloading {url}: {e}")

    if not download_success:
        return False

    try:
        # 2. Extract member if archive is a .tar.gz
        if is_tar_gz:
            member_suffix = model_meta.get("archive_member_suffix", ".tza")
            extracted = False
            with tarfile.open(temp_path, "r:gz") as tar:
                for member in tar.getmembers():
                    if member.isfile() and (
                        member.name.endswith(member_suffix) or member.name.endswith(".tza")
                    ):
                        f_obj = tar.extractfile(member)
                        if f_obj:
                            with open(output_path, "wb") as out_f:
                                out_f.write(f_obj.read())
                            extracted = True
                            break
            temp_path.unlink()
            if not extracted:
                print(f"   ❌ Could not find member matching '{member_suffix}' in archive {primary_url}")
                return False
        else:
            temp_path.rename(output_path)

        actual_mb = output_path.stat().st_size / (1024 * 1024)
        print(f"   ✓ Successfully saved to: {output_path} ({actual_mb:.1f} MB)")
        return True
    except Exception as e:
        if temp_path.exists():
            temp_path.unlink()
        print(f"   ❌ Post-processing failed: {e}")
        return False


def sync_drive_index():
    """Generates and syncs /dervgen/model/INDEX.json and INDEX.md in Google Drive."""
    if not check_drive_mounted():
        return

    data = load_registry()
    models = data.get("models", [])
    model_root = DRIVE_ROOT / "data" / "models"
    model_root.mkdir(parents=True, exist_ok=True)

    drive_index_json_path = model_root / "INDEX.json"
    drive_index_md_path = model_root / "INDEX.md"

    installed_count = 0
    total_installed_bytes = 0
    inventory = []

    for m in models:
        target = model_root / m["target_file"]
        is_installed = target.exists()
        size_bytes = target.stat().st_size if is_installed else 0
        mtime = datetime.fromtimestamp(target.stat().st_mtime).isoformat() if is_installed else None

        if is_installed:
            installed_count += 1
            total_installed_bytes += size_bytes

        item = dict(m)
        item["status"] = "INSTALLED" if is_installed else "MISSING"
        item["actual_bytes"] = size_bytes
        item["actual_mb"] = round(size_bytes / (1024 * 1024), 2)
        item["last_modified"] = mtime
        inventory.append(item)

    # 1. Write /dervgen/model/INDEX.json
    index_data = {
        "version": "1.5.0",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "storage_root": str(model_root),
        "total_registered": len(models),
        "total_installed": installed_count,
        "total_installed_mb": round(total_installed_bytes / (1024 * 1024), 2),
        "models": inventory,
    }
    with open(drive_index_json_path, "w", encoding="utf-8") as f:
        json.dump(index_data, f, indent=2, ensure_ascii=False)

    # 2. Write /dervgen/model/INDEX.md
    md_lines = [
        "# DervGen Google Drive Model Index (Live Inventory)",
        "",
        f"> **Generated at**: `{index_data['generated_at']}`  ",
        f"> **Status**: **{installed_count} / {len(models)}** installed ({index_data['total_installed_mb']:.1f} MB total)",
        "",
        "| Status | Usage | Model Name | Target File | Installed Size | Expected | Priority | Description |",
        "|---|---|---|---|---|---|---|---|",
    ]

    for item in inventory:
        badge = "🟢 `INSTALLED`" if item["status"] == "INSTALLED" else "⚪ `MISSING`"
        size_display = f"{item['actual_mb']:.1f} MB" if item["status"] == "INSTALLED" else "-"
        line = (
            f"| {badge} | `{item['usage']}` | **{item['name']}** | `{item['target_file']}` | "
            f"{size_display} | ~{item['size_mb']} MB | {item['priority']} | {item['description']} |"
        )
        md_lines.append(line)

    md_lines.extend([
        "",
        "---",
        "## How to Update or Fetch Missing Models",
        "In Google Colab, run:",
        "```bash",
        "# Fetch P0 models",
        "python3 /content/workspace/colab/init_models.py --preset=P0",
        "",
        "# Re-sync this Index",
        "python3 /content/workspace/colab/init_models.py --sync-index",
        "```",
    ])

    with open(drive_index_md_path, "w", encoding="utf-8") as f:
        f.write("\n".join(md_lines) + "\n")

    print("✅ Synced Google Drive Model Index:")
    print(f"   📄 {drive_index_json_path}")
    print(f"   📄 {drive_index_md_path} ({installed_count}/{len(models)} installed)")


# Fast smoke/preview models (download size ~2.6 GB, 30s-1min on Colab)
FAST_MODEL_IDS = {
    "google_veo_2",
    "oidn_weights",
    "rife_v46",
    "realesrgan_x4plus",
    "bsrgan",
    "dinov2_vits14",
    "droid_slam_weights",
    "cotracker3_stride4",
    "motionbricks_locomotion",
    "gvhmr_v1",
    "emoca_v2_face",
    "cameractrl_svd",
    "sam2_base_plus",
    "nvidia_cosmos_tokenizer_cv8x8",
    "nvidia_cosmos_tokenizer_dv8x8",
    "nvidia_flexicubes",
    "nvidia_nvdiffrec",
    "nvidia_neuralangelo",
    "nvidia_ase_physics",
    "gamengen_doom",
    "bytedance_dwpose",
    "ubisoft_lmm_locomotion",
    "kuaishou_kling_world",
    "ue_ml_deformer_framework",
}


def run_init(
    preset: str = "P0",
    usage_filter: str = None,
    model_filter: str = None,
    dry_run: bool = False,
    sync_only: bool = False,
):
    if sync_only:
        sync_drive_index()
        return

    data = load_registry()
    models = data.get("models", [])

    filtered = []
    for m in models:
        if model_filter and m["id"] != model_filter:
            continue
        if usage_filter and m["usage"] != usage_filter:
            continue
        if preset == "fast":
            if m["id"] not in FAST_MODEL_IDS:
                continue
        elif preset != "all" and m["priority"] != preset:
            continue
        filtered.append(m)

    print("\n==========================================================================")
    print(f" DervGen Cloud Model Initializer (SSOT: {DRIVE_ROOT}/data/models)")
    print(f" Filter: Priority=[{preset}], Usage=[{usage_filter or 'all'}], Count=[{len(filtered)}]")
    print("==========================================================================")

    total_mb = sum(m["size_mb"] for m in filtered)
    print(f"Total download size: {total_mb:.1f} MB (~{total_mb / 1024:.2f} GB)\n")

    for idx, m in enumerate(filtered, start=1):
        target = DRIVE_ROOT / "data" / "models" / m["target_file"]
        status = "[EXISTS]" if target.exists() else "[MISSING]"
        print(f"{idx:2d}. {status:<9} {m['name']:<35} ({m['size_mb']:>4} MB) -> data/models/{m['target_file']}")

    if dry_run:
        print("\n[Dry Run] No files downloaded.")
        return

    if not check_drive_mounted():
        return

    print("\nStarting cloud-to-drive downloads...")
    success_count = 0
    skip_count = 0

    for m in filtered:
        target = DRIVE_ROOT / "data" / "models" / m["target_file"]
        if target.exists() and not _is_html_payload(target):
            actual_mb = target.stat().st_size / (1024 * 1024)
            print(f"⏩ [SKIP] {m['name']} already exists ({actual_mb:.1f} MB)")
            skip_count += 1
            continue

        print(f"\n📦 Fetching {m['name']} ({m['description']})...")
        if provision_model_entry(m, target):
            success_count += 1

    print("\n==========================================================================")
    print(f" Summary: {success_count} downloaded, {skip_count} already present, {len(filtered)} total.")
    print("==========================================================================")

    sync_drive_index()


def main():
    parser = argparse.ArgumentParser(description="DervGen Model Pre-fetcher & Index Sync for Cloud Storage")
    parser.add_argument(
        "--preset",
        default="P0",
        choices=["fast", "P0", "P1", "all"],
        help="Download priority preset: fast (smoke/quick ~2.6GB), P0 (core baseline ~26.5GB), P1 (extended), all",
    )
    parser.add_argument(
        "--usage",
        choices=[
            "foundation",
            "3d_recon",
            "texture_gen",
            "video_gen",
            "actor_dynamics",
            "audio_foley",
            "denoise_upscale",
        ],
        help="Filter by specific usage domain",
    )
    parser.add_argument("--model", help="Download a specific model ID (e.g. sam2_large)")
    parser.add_argument("--dry-run", action="store_true", help="Print model plan without downloading")
    parser.add_argument(
        "--sync-index",
        action="store_true",
        help="Only scan and sync Google Drive INDEX.json & INDEX.md",
    )
    args = parser.parse_args()

    run_init(
        preset=args.preset,
        usage_filter=args.usage,
        model_filter=args.model,
        dry_run=args.dry_run,
        sync_only=args.sync_index,
    )


if __name__ == "__main__":
    main()
