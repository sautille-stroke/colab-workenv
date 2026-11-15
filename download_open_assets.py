#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
DervGen Ecosystem: Free 3D Resources, Benchmarks & Game Assets Downloader (Mega Suite)
======================================================================================
Authoritative automated downloader for the DervGen open asset ecosystem, scaling from
lightweight ~150 MB starter bundles up to hundreds of gigabytes (180+ GB) of open 3D
models, AAA benchmark scenes, CC0 PBR textures, NeRF/3DGS datasets, motion capture,
Blender production files, and complete game development kits.

All assets strictly adhere to the Domain-Driven SSOT V2.1 storage standard:
  - data/cg/scenes/                 # Benchmark & ArchViz scenes (Sponza, Bistro, San Miguel, Bitterli)
  - data/cg/models/                 # High-precision 3D scans & glTF sample models (Bunny, Teapot, DamagedHelmet)
  - data/cg/materials/              # CC0 2K/4K PBR material textures (ambientCG)
  - data/common/hdri/               # CC0 2K/4K Radiance HDR environment light probes (Poly Haven)
  - data/cg/game_assets/            # Modular low-poly game asset kits (Kenney Complete, KayKit Complete)
  - data/cg/game_assets/characters/ # Rigged & animated skeletal characters (glTF 2.0)
  - data/cg/game_demos/             # Full playable open-source 3D game demos (Godot TPS)
  - data/3d/radiance_fields/        # Mip-NeRF 360 & NeRF Synthetic ground truth benchmarks
  - data/3d/mocap/                  # CMU & Bandai Namco skeletal animation motion capture
  - data/3d/hair_terrain/           # Cem Yuksel hair curves & 16-bit DEM heightmaps
  - data/3d/blender_production/     # Blender Studio open movie production benchmarks

Scale Tiers:
  - quick:     ~150 MB starter smoke-test set
  - standard:  ~2.5 GB balanced high-frequency development set
  - heavy:     ~50 GB high-fidelity 3A scenes, Mip-NeRF 360, NeRF Synthetic, Kenney 20+ kit complete
  - mega:      ~180+ GB complete open 3D universe (benchmarks, NeRF/3DGS, mocap, production assets)
  - all:       All registered open datasets & packages

Usage Examples:
  # Quick test (~150 MB):
  python3 download_open_assets.py --preset quick

  # Standard recommended set (~2.5 GB):
  python3 download_open_assets.py --preset standard

  # Heavy set (50+ GB):
  python3 download_open_assets.py --preset heavy

  # Mega full-universe set (180+ GB):
  python3 download_open_assets.py --preset mega

  # Download games, characters and demos only:
  python3 download_open_assets.py --category game_assets,characters,game_demos

  # Include 75+ 3D AI foundation models (~180 GB via init_models.py):
  python3 download_open_assets.py --preset standard --include-ai-models

  # Dry run preview (plan and size calculations):
  python3 download_open_assets.py --preset mega --dry-run
"""

import argparse
import http.cookiejar
import json
import os
import shutil
import ssl
import sys
import tempfile
import time
import urllib.error
import urllib.request
import zipfile
import tarfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any

# Ensure terminal UTF-8 encoding
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

# Configure HuggingFace endpoint mirror if needed
os.environ.setdefault("HF_ENDPOINT", "https://hf-mirror.com")
os.environ.setdefault("HF_HUB_ENABLE_HF_TRANSFER", "0")

# ==============================================================================
# Asset Registry Definitions (Hundreds of GBs of Curated Open Data)
# ==============================================================================

ASSET_REGISTRY: List[Dict[str, Any]] = [
    # --------------------------------------------------------------------------
    # 1. Industry AAA Benchmark & ArchViz Scenes (data/cg/scenes/)
    # --------------------------------------------------------------------------
    {
        "id": "sponza_crytek",
        "name": "Crytek Sponza Atrium",
        "category": "scenes",
        "domain_path": "data/cg/scenes/sponza_crytek",
        "url": "https://casual-effects.com/g3d/data10/common/model/crytek_sponza/sponza.zip",
        "format": "zip",
        "size_mb": 32.5,
        "presets": ["standard", "heavy", "mega", "all"],
        "check_file": "sponza.obj",
        "description": "Standard real-time graphics benchmark atrium scene (OBJ + MTL + Textures)"
    },
    {
        "id": "bistro_exterior",
        "name": "Amazon Lumberyard Bistro (Exterior)",
        "category": "scenes",
        "domain_path": "data/cg/scenes/bistro_exterior",
        "url": "https://casual-effects.com/g3d/data10/research/model/bistro/Exterior.zip",
        "format": "zip",
        "size_mb": 348.0,
        "presets": ["standard", "heavy", "mega", "all"],
        "check_file": "exterior.obj",
        "description": "Amazon Lumberyard Bistro exterior Parisian street with ~3M triangles and dense foliage"
    },
    {
        "id": "bistro_interior",
        "name": "Amazon Lumberyard Bistro (Interior)",
        "category": "scenes",
        "domain_path": "data/cg/scenes/bistro_interior",
        "url": "https://casual-effects.com/g3d/data10/research/model/bistro/Interior.zip",
        "format": "zip",
        "size_mb": 372.0,
        "presets": ["heavy", "mega", "all"],
        "check_file": "interior.obj",
        "description": "Amazon Lumberyard Bistro interior cafe scene for indirect GI and transmissive materials"
    },
    {
        "id": "san_miguel",
        "name": "San Miguel Architectural Courtyard",
        "category": "scenes",
        "domain_path": "data/cg/scenes/san_miguel",
        "url": "https://casual-effects.com/g3d/data10/research/model/San_Miguel/San_Miguel.zip",
        "format": "zip",
        "size_mb": 268.0,
        "presets": ["standard", "heavy", "mega", "all"],
        "check_file": "san-miguel.obj",
        "description": "Detailed courtyard scene with thousands of leaves, tables, plants, and high-frequency geometry"
    },
    {
        "id": "breakfast_room",
        "name": "Bitterli Breakfast Room",
        "category": "scenes",
        "domain_path": "data/cg/scenes/breakfast_room",
        "url": "https://casual-effects.com/g3d/data10/research/model/breakfast_room/breakfast_room.zip",
        "format": "zip",
        "size_mb": 15.0,
        "presets": ["quick", "standard", "heavy", "mega", "all"],
        "check_file": "breakfast_room.obj",
        "description": "Classic ArchViz interior daylight benchmark with sunlight entering through windows"
    },
    {
        "id": "fireplace_room",
        "name": "Bitterli Fireplace Room",
        "category": "scenes",
        "domain_path": "data/cg/scenes/fireplace_room",
        "url": "https://casual-effects.com/g3d/data10/research/model/fireplace_room/fireplace_room.zip",
        "format": "zip",
        "size_mb": 22.0,
        "presets": ["quick", "standard", "heavy", "mega", "all"],
        "check_file": "fireplace_room.obj",
        "description": "Cozy fireplace living room scene with soft indirect illumination and velvet/wood materials"
    },
    {
        "id": "country_kitchen",
        "name": "Bitterli Country Kitchen",
        "category": "scenes",
        "domain_path": "data/cg/scenes/country_kitchen",
        "url": "https://benedikt-bitterli.me/resources/pbrt-v4/kitchen.zip",
        "format": "zip",
        "size_mb": 28.0,
        "presets": ["standard", "heavy", "mega", "all"],
        "check_file": "scene-v4.pbrt",
        "description": "High geometric density rustic kitchen scene with ceramic tableware and glassware (PBRT-v4 / PLY)"
    },
    {
        "id": "rungholt",
        "name": "Rungholt Minecraft Island",
        "category": "scenes",
        "domain_path": "data/cg/scenes/rungholt",
        "url": "https://casual-effects.com/g3d/data10/research/model/rungholt/rungholt.zip",
        "format": "zip",
        "size_mb": 85.0,
        "presets": ["heavy", "mega", "all"],
        "check_file": "rungholt.obj",
        "description": "Vast medieval Minecraft terrain with 6.7M block triangles for Voxel/LOD testing"
    },
    {
        "id": "pixar_kitchen_usd",
        "name": "Pixar USD Kitchen Set (Disney/Pixar Official)",
        "category": "scenes",
        "domain_path": "data/cg/scenes/pixar_kitchen",
        "url": "https://graphics.pixar.com/usd/files/Kitchen_set.zip",
        "format": "zip",
        "size_mb": 2.7,
        "presets": ["standard", "heavy", "mega", "all"],
        "check_file": "Kitchen_set.usd",
        "description": "Official Pixar OpenUSD production-grade indoor kitchen benchmark scene"
    },
    {
        "id": "disney_moana_pbrtv4",
        "name": "Disney Moana Island (PBRT-v4 Package, Official)",
        "category": "scenes",
        "domain_path": "data/cg/scenes/disney_moana_pbrtv4",
        "url": "https://datasets.disneyanimation.com/moanaislandscene/island-pbrtV4-v2.0.tgz",
        "format": "tgz",
        "size_mb": 5663.0,
        "presets": ["disney", "mega", "all"],
        "check_file": "island.pbrt",
        "check_files": ["island.pbrt", "island.dump.pbrt", "README.pdf", "README.txt", "pbrt/island.pbrt", "island/island.pbrt", "island.json"],
        "description": "Walt Disney Animation Studios official Moana Island Scene translated for PBRT-v4 (5.6 GB download)"
    },
    {
        "id": "disney_moana_usd",
        "name": "Disney Moana Island (OpenUSD Package, Official)",
        "category": "scenes",
        "domain_path": "data/cg/scenes/disney_moana_usd",
        "url": "https://datasets.disneyanimation.com/moanaislandscene/island-usd-v2.1.tgz",
        "format": "tgz",
        "size_mb": 14457.0,
        "presets": ["disney", "all"],
        "check_file": "island.usda",
        "check_files": ["island.usda", "island.usd", "README.pdf", "README-USD.pdf", "usd/island.usda", "usd/island.usd"],
        "description": "Walt Disney Animation Studios official Moana Island OpenUSD production scene (15.0 GB download)"
    },
    {
        "id": "disney_moana_base",
        "name": "Disney Moana Island (Base Production Package, 45 GB)",
        "category": "scenes",
        "domain_path": "data/cg/scenes/disney_moana_base",
        "url": "https://wdas-datasets-disneyanimation-com.s3-us-west-2.amazonaws.com/moanaislandscene/island-basepackage-v1.1.tgz",
        "format": "tgz",
        "size_mb": 45887.0,
        "presets": ["disney", "all"],
        "check_file": "island.json",
        "check_files": ["island.json", "island/island.json", "island-README-v1.1.pdf", "README.md", "textures", "models"],
        "description": "Walt Disney Animation Studios full raw production assets for Moana Island single frame (45 GB download)"
    },

    # --------------------------------------------------------------------------
    # 2. Standard 3D Reference Models & Khronos glTF Samples (data/cg/models/)
    # --------------------------------------------------------------------------
    {
        "id": "stanford_bunny",
        "name": "Stanford Bunny (OBJ)",
        "category": "models",
        "domain_path": "data/cg/models/stanford_bunny",
        "url": "https://raw.githubusercontent.com/alecjacobson/common-3d-test-models/master/data/stanford-bunny.obj",
        "format": "raw",
        "size_mb": 2.3,
        "presets": ["quick", "standard", "heavy", "mega", "all"],
        "target_filename": "stanford_bunny.obj",
        "check_file": "stanford_bunny.obj",
        "description": "Canonical 1994 Stanford Computer Graphics Laboratory 3D range scan mesh (69,451 polys)"
    },
    {
        "id": "utah_teapot",
        "name": "Utah Teapot (OBJ)",
        "category": "models",
        "domain_path": "data/cg/models/utah_teapot",
        "url": "https://raw.githubusercontent.com/alecjacobson/common-3d-test-models/master/data/teapot.obj",
        "format": "raw",
        "size_mb": 0.2,
        "presets": ["quick", "standard", "heavy", "mega", "all"],
        "target_filename": "teapot.obj",
        "check_file": "teapot.obj",
        "description": "Historical 1975 Martin Newell Bézier curve reference teapot model"
    },
    {
        "id": "suzanne_monkey",
        "name": "Blender Suzanne (OBJ)",
        "category": "models",
        "domain_path": "data/cg/models/suzanne_monkey",
        "url": "https://raw.githubusercontent.com/alecjacobson/common-3d-test-models/master/data/suzanne.obj",
        "format": "raw",
        "size_mb": 0.05,
        "presets": ["quick", "standard", "heavy", "mega", "all"],
        "target_filename": "suzanne.obj",
        "check_file": "suzanne.obj",
        "description": "Standard Blender mascot geometry for transformation and normal tests"
    },
    {
        "id": "armadillo_scan",
        "name": "Stanford Armadillo (OBJ)",
        "category": "models",
        "domain_path": "data/cg/models/stanford_armadillo",
        "url": "https://raw.githubusercontent.com/alecjacobson/common-3d-test-models/master/data/armadillo.obj",
        "format": "raw",
        "size_mb": 17.5,
        "presets": ["standard", "heavy", "mega", "all"],
        "target_filename": "armadillo.obj",
        "check_file": "armadillo.obj",
        "description": "Stanford Cyberware 3D range scan of Armadillo figurine (345,944 triangles)"
    },
    {
        "id": "dragon_scan",
        "name": "Stanford Dragon (OBJ)",
        "category": "models",
        "domain_path": "data/cg/models/stanford_dragon",
        "url": "https://raw.githubusercontent.com/alecjacobson/common-3d-test-models/master/data/xyzrgb_dragon.obj",
        "format": "raw",
        "size_mb": 34.0,
        "presets": ["standard", "heavy", "mega", "all"],
        "target_filename": "dragon.obj",
        "check_file": "dragon.obj",
        "description": "High-resolution Stanford dragon range scan mesh with intricate details"
    },
    {
        "id": "happy_buddha_scan",
        "name": "Stanford Happy Buddha (OBJ)",
        "category": "models",
        "domain_path": "data/cg/models/stanford_happy_buddha",
        "url": "https://raw.githubusercontent.com/alecjacobson/common-3d-test-models/master/data/happy.obj",
        "format": "raw",
        "size_mb": 39.0,
        "presets": ["standard", "heavy", "mega", "all"],
        "target_filename": "happy_buddha.obj",
        "check_file": "happy_buddha.obj",
        "description": "Stanford 3D scanning repository Happy Buddha statue scan"
    },
    {
        "id": "lucy_scan",
        "name": "Stanford Lucy Angel (OBJ)",
        "category": "models",
        "domain_path": "data/cg/models/stanford_lucy",
        "url": "https://raw.githubusercontent.com/alecjacobson/common-3d-test-models/master/data/lucy.obj",
        "format": "raw",
        "size_mb": 14.0,
        "presets": ["heavy", "mega", "all"],
        "target_filename": "lucy.obj",
        "check_file": "lucy.obj",
        "description": "Stanford Computer Graphics Laboratory Lucy angel statue with feathered wings"
    },
    {
        "id": "gso_starter_subset",
        "name": "Google Scanned Objects (20 Golden Assets / RFC 0063)",
        "category": "models",
        "domain_path": "data/evaluations/benchmarks/gso_starter",
        "url": "https://huggingface.co/datasets/google/google_scanned_objects/resolve/main/models.zip",
        "format": "zip",
        "size_mb": 110.0,
        "presets": ["benchmarks", "quick", "standard", "heavy", "mega", "all"],
        "check_file": "metadata.json",
        "description": "Google Scanned Objects (GSO) watertight benchmark models for 3D reconstruction Chamfer/F-score evaluation"
    },
    {
        "id": "gso_standard_100",
        "name": "Google Scanned Objects (100 Benchmark Split / RFC 0063)",
        "category": "models",
        "domain_path": "data/evaluations/benchmarks/gso_standard",
        "repo_id": "google/google_scanned_objects",
        "repo_type": "dataset",
        "format": "hf_dataset",
        "size_mb": 1200.0,
        "presets": ["benchmarks", "standard", "heavy", "mega", "all"],
        "check_file": "README.md",
        "description": "GSO 100 benchmark split for direct comparison with Microsoft TRELLIS and Tencent Hunyuan3D-2.0"
    },
    {
        "id": "objaverse_lvis_benchmark",
        "name": "Objaverse-LVIS Benchmark Split (100 Verified Manifold Meshes)",
        "category": "models",
        "domain_path": "data/evaluations/benchmarks/objaverse_eval_100",
        "repo_id": "allenai/objaverse-xl",
        "repo_type": "dataset",
        "format": "hf_dataset",
        "size_mb": 1500.0,
        "presets": ["benchmarks", "standard", "heavy", "mega", "all"],
        "check_file": "README.md",
        "description": "100 official test split assets from CVPR 2023 Objaverse-LVIS benchmark for manifold and watertightness evaluation"
    },
    {
        "id": "vbench_canonical_prompts",
        "name": "VBench Official Prompt & Trajectory Suite (CVPR 2024)",
        "category": "evaluations",
        "domain_path": "data/evaluations/benchmarks/vbench_prompts",
        "url": "https://raw.githubusercontent.com/Vchitect/VBench/main/prompts/prompts_per_dimension.json",
        "format": "raw",
        "size_mb": 5.0,
        "presets": ["benchmarks", "quick", "standard", "heavy", "mega", "all"],
        "target_filename": "prompts_per_dimension.json",
        "check_file": "prompts_per_dimension.json",
        "description": "Official 16-dimension video benchmark prompt and evaluation trajectory suite"
    },
    {
        "id": "chronomagic_physics_50",
        "name": "ChronoMagic-Bench Physical Causality Core (50 Scenarios / RFC 0063)",
        "category": "evaluations",
        "domain_path": "data/evaluations/benchmarks/chronomagic_core",
        "repo_id": "PKU-YuanGroup/ChronoMagic-Bench",
        "repo_type": "dataset",
        "format": "hf_dataset",
        "size_mb": 1500.0,
        "presets": ["benchmarks", "standard", "heavy", "mega", "all"],
        "check_file": "README.md",
        "description": "50 high-frame-rate physical video scenarios testing gravity, collisions, and liquid time-arrow irreversibility"
    },
    {
        "id": "damaged_helmet",
        "name": "Khronos DamagedHelmet (glTF 2.0 PBR)",
        "category": "models",
        "domain_path": "data/cg/models/damaged_helmet",
        "url": "https://raw.githubusercontent.com/KhronosGroup/glTF-Sample-Models/master/2.0/DamagedHelmet/glTF-Binary/DamagedHelmet.glb",
        "format": "raw",
        "size_mb": 3.6,
        "presets": ["quick", "standard", "heavy", "mega", "all"],
        "target_filename": "DamagedHelmet.glb",
        "check_file": "DamagedHelmet.glb",
        "description": "Official Khronos glTF 2.0 PBR metallic-roughness benchmark with baked normals and emissive"
    },
    {
        "id": "boombox",
        "name": "Khronos BoomBox (glTF 2.0 PBR)",
        "category": "models",
        "domain_path": "data/cg/models/boombox",
        "url": "https://raw.githubusercontent.com/KhronosGroup/glTF-Sample-Models/master/2.0/BoomBox/glTF-Binary/BoomBox.glb",
        "format": "raw",
        "size_mb": 10.5,
        "presets": ["standard", "heavy", "mega", "all"],
        "target_filename": "BoomBox.glb",
        "check_file": "BoomBox.glb",
        "description": "High detail retro cassette boombox with wood grain, brushed metal, and rubber shaders"
    },
    {
        "id": "metal_rough_spheres",
        "name": "Khronos MetalRoughSpheres (glTF 2.0 Matrix)",
        "category": "models",
        "domain_path": "data/cg/models/metal_rough_spheres",
        "url": "https://raw.githubusercontent.com/KhronosGroup/glTF-Sample-Models/master/2.0/MetalRoughSpheres/glTF-Binary/MetalRoughSpheres.glb",
        "format": "raw",
        "size_mb": 10.7,
        "presets": ["quick", "standard", "heavy", "mega", "all"],
        "target_filename": "MetalRoughSpheres.glb",
        "check_file": "MetalRoughSpheres.glb",
        "description": "PBR metallic/roughness parameter verification matrix (5x5 spheres from 0.0 to 1.0)"
    },
    {
        "id": "water_bottle",
        "name": "Khronos WaterBottle (glTF 2.0 Transmission)",
        "category": "models",
        "domain_path": "data/cg/models/water_bottle",
        "url": "https://raw.githubusercontent.com/KhronosGroup/glTF-Sample-Models/master/2.0/WaterBottle/glTF-Binary/WaterBottle.glb",
        "format": "raw",
        "size_mb": 5.4,
        "presets": ["standard", "heavy", "mega", "all"],
        "target_filename": "WaterBottle.glb",
        "check_file": "WaterBottle.glb",
        "description": "Clear transmissive plastic bottle with water liquid meniscus and bubble geometry"
    },
    {
        "id": "lantern",
        "name": "Khronos Lantern (glTF 2.0 Emissive)",
        "category": "models",
        "domain_path": "data/cg/models/lantern",
        "url": "https://raw.githubusercontent.com/KhronosGroup/glTF-Sample-Models/master/2.0/Lantern/glTF-Binary/Lantern.glb",
        "format": "raw",
        "size_mb": 9.1,
        "presets": ["standard", "heavy", "mega", "all"],
        "target_filename": "Lantern.glb",
        "check_file": "Lantern.glb",
        "description": "Antique brass lantern model with complex cage geometry and inner flame emissive source"
    },
    {
        "id": "cesium_milk_truck",
        "name": "Khronos CesiumMilkTruck (Vehicle glTF)",
        "category": "models",
        "domain_path": "data/cg/models/cesium_milk_truck",
        "url": "https://raw.githubusercontent.com/KhronosGroup/glTF-Sample-Models/master/2.0/CesiumMilkTruck/glTF-Binary/CesiumMilkTruck.glb",
        "format": "raw",
        "size_mb": 0.8,
        "presets": ["standard", "heavy", "mega", "all"],
        "target_filename": "CesiumMilkTruck.glb",
        "check_file": "CesiumMilkTruck.glb",
        "description": "Rigged animated delivery milk truck with rotating wheels for physics vehicle tests"
    },

    # --------------------------------------------------------------------------
    # 3. Free CC0 2K PBR Materials (data/cg/materials/)
    # --------------------------------------------------------------------------
    {
        "id": "pbr_paving_stones_070",
        "name": "ambientCG Paving Stones 070 (2K)",
        "category": "materials",
        "domain_path": "data/cg/materials/paving_stones_070",
        "url": "https://ambientcg.com/get?file=PavingStones070_2K-JPG.zip",
        "format": "zip",
        "size_mb": 25.0,
        "presets": ["quick", "standard", "heavy", "mega", "all"],
        "check_file": "PavingStones070_2K_Color.jpg",
        "description": "Old European cobblestone street surface with displacement, roughness, and normal maps"
    },
    {
        "id": "pbr_bricks_075a",
        "name": "ambientCG Red Bricks 075A (2K)",
        "category": "materials",
        "domain_path": "data/cg/materials/bricks_075a",
        "url": "https://ambientcg.com/get?file=Bricks075A_2K-JPG.zip",
        "format": "zip",
        "size_mb": 17.0,
        "presets": ["quick", "standard", "heavy", "mega", "all"],
        "check_file": "Bricks075A_2K_Color.jpg",
        "description": "Weathered red brick wall with mortar grooves and fine surface bumps"
    },
    {
        "id": "pbr_wood_floor_041",
        "name": "ambientCG Wood Floor 041 (2K)",
        "category": "materials",
        "domain_path": "data/cg/materials/wood_floor_041",
        "url": "https://ambientcg.com/get?file=WoodFloor041_2K-JPG.zip",
        "format": "zip",
        "size_mb": 23.0,
        "presets": ["quick", "standard", "heavy", "mega", "all"],
        "check_file": "WoodFloor041_2K_Color.jpg",
        "description": "Herringbone wooden parquet floor with anisotropic specular reflections"
    },
    {
        "id": "pbr_metal_006",
        "name": "ambientCG Scratched Metal 006 (2K)",
        "category": "materials",
        "domain_path": "data/cg/materials/metal_006",
        "url": "https://ambientcg.com/get?file=Metal006_2K-JPG.zip",
        "format": "zip",
        "size_mb": 5.6,
        "presets": ["quick", "standard", "heavy", "mega", "all"],
        "check_file": "Metal006_2K_Color.jpg",
        "description": "Industrial brushed and scratched sheet metal with high metalness value"
    },
    {
        "id": "pbr_marble_012",
        "name": "ambientCG Luxury Marble 012 (2K)",
        "category": "materials",
        "domain_path": "data/cg/materials/marble_012",
        "url": "https://ambientcg.com/get?file=Marble012_2K-JPG.zip",
        "format": "zip",
        "size_mb": 14.8,
        "presets": ["standard", "heavy", "mega", "all"],
        "check_file": "Marble012_2K_Color.jpg",
        "description": "Polished white marble floor with dark natural veins and high gloss clearcoat"
    },
    {
        "id": "pbr_ground_037",
        "name": "ambientCG Forest Ground 037 (2K)",
        "category": "materials",
        "domain_path": "data/cg/materials/ground_037",
        "url": "https://ambientcg.com/get?file=Ground037_2K-JPG.zip",
        "format": "zip",
        "size_mb": 37.8,
        "presets": ["standard", "heavy", "mega", "all"],
        "check_file": "Ground037_2K_Color.jpg",
        "description": "Forest dirt soil with fallen pine needles, pebbles, and organic moisture"
    },
    {
        "id": "pbr_concrete_019",
        "name": "ambientCG Rough Concrete 019 (2K)",
        "category": "materials",
        "domain_path": "data/cg/materials/concrete_019",
        "url": "https://ambientcg.com/get?file=Concrete019_2K-JPG.zip",
        "format": "zip",
        "size_mb": 28.8,
        "presets": ["standard", "heavy", "mega", "all"],
        "check_file": "Concrete019_2K_Color.jpg",
        "description": "Poured rough architectural concrete with air pockets and aggregate speckles"
    },

    # --------------------------------------------------------------------------
    # 4. Free CC0 2K HDR Environment Maps (data/common/hdri/)
    # --------------------------------------------------------------------------
    {
        "id": "hdri_studio_small_03",
        "name": "Poly Haven Studio Small 03 (2K HDR)",
        "category": "hdri",
        "domain_path": "data/common/hdri",
        "url": "https://dl.polyhaven.org/file/ph-assets/HDRIs/hdr/2k/studio_small_03_2k.hdr",
        "format": "raw",
        "size_mb": 6.7,
        "presets": ["quick", "standard", "heavy", "mega", "all"],
        "target_filename": "studio_small_03_2k.hdr",
        "check_file": "studio_small_03_2k.hdr",
        "description": "Neutral indoor studio light probe with 3 softboxes for clean material lookdev"
    },
    {
        "id": "hdri_sunset_chalk_quarry",
        "name": "Poly Haven Sunset Chalk Quarry (2K HDR)",
        "category": "hdri",
        "domain_path": "data/common/hdri",
        "url": "https://dl.polyhaven.org/file/ph-assets/HDRIs/hdr/2k/sunset_in_the_chalk_quarry_2k.hdr",
        "format": "raw",
        "size_mb": 6.3,
        "presets": ["quick", "standard", "heavy", "mega", "all"],
        "target_filename": "sunset_in_the_chalk_quarry_2k.hdr",
        "check_file": "sunset_in_the_chalk_quarry_2k.hdr",
        "description": "Golden hour sunset with low-angle directional sun and deep warm ambient sky"
    },
    {
        "id": "hdri_courtyard",
        "name": "Poly Haven Courtyard (2K HDR)",
        "category": "hdri",
        "domain_path": "data/common/hdri",
        "url": "https://dl.polyhaven.org/file/ph-assets/HDRIs/hdr/2k/courtyard_2k.hdr",
        "format": "raw",
        "size_mb": 6.7,
        "presets": ["standard", "heavy", "mega", "all"],
        "target_filename": "courtyard_2k.hdr",
        "check_file": "courtyard_2k.hdr",
        "description": "Historic European stone courtyard environment with complex shadow bounce"
    },

    # --------------------------------------------------------------------------
    # 5. NeRF & 3D Gaussian Splatting Ground Truth (data/3d/radiance_fields/)
    # --------------------------------------------------------------------------
    {
        "id": "mipnerf_360_processed",
        "name": "Mip-NeRF 360 & 3DGS Benchmarks (Bicycle, Garden, Room, Kitchen, Bonsai...)",
        "category": "radiance_fields",
        "domain_path": "data/3d/radiance_fields/mipnerf360",
        "repo_id": "ethanweber/Mip-NeRF_360_Processed_with_Nerfstudio",
        "repo_type": "dataset",
        "format": "hf_dataset",
        "size_mb": 15360.0,  # ~15 GB
        "presets": ["heavy", "mega", "all"],
        "check_file": "bicycle/transforms.json",
        "description": "Authoritative real-world unbounded 360-degree NeRF and 3DGS radiance field dataset with COLMAP poses"
    },
    {
        "id": "nerf_synthetic_dataset",
        "name": "NeRF Synthetic Multi-View Benchmark (Lego, Chair, Drums, Ship, Hotdog...)",
        "category": "radiance_fields",
        "domain_path": "data/3d/radiance_fields/nerf_synthetic",
        "repo_id": "XayahHina/nerf_synthetic",
        "repo_type": "dataset",
        "format": "hf_dataset",
        "size_mb": 5120.0,   # ~5 GB
        "presets": ["heavy", "mega", "all"],
        "check_file": "lego/transforms_train.json",
        "description": "DeepMind/Mildenhall canonical synthetic 360 multi-view dataset with ground truth camera matrices"
    },

    # --------------------------------------------------------------------------
    # 6. Motion Capture & Skeletal Animation Datasets (data/3d/mocap/)
    # --------------------------------------------------------------------------
    {
        "id": "cmu_mocap_dataset",
        "name": "CMU Graphics Lab Motion Capture Database (2,600+ Sequences)",
        "category": "mocap",
        "domain_path": "data/3d/mocap/cmu_mocap",
        "repo_id": "gbionics/cmu-fbx",
        "repo_type": "dataset",
        "format": "hf_dataset",
        "size_mb": 5600.0,
        "presets": ["mega", "all"],
        "check_file": "README.md",
        "description": "World-standard CMU optical mocap database (2,500+ sequences in FBX): walking, martial arts, acrobatics, sports, and interactions"
    },
    {
        "id": "bandai_namco_motion",
        "name": "Bandai Namco Research Motion Dataset",
        "category": "mocap",
        "domain_path": "data/3d/mocap/bandai_namco_motion",
        "url": "https://github.com/BandaiNamcoResearchInc/Bandai-Namco-Research-Motiondataset/archive/refs/heads/master.zip",
        "format": "zip",
        "size_mb": 1850.0,  # ~1.85 GB
        "presets": ["mega", "all"],
        "check_file": "README.md",
        "description": "Commercial fighting game actions, dance sequences, combat stances, and stunt mocap BVH tracks"
    },
    {
        "id": "humanml3d_mocap_dataset",
        "name": "HumanML3D 3D Motion-Language & Pose Feature Dataset",
        "category": "mocap",
        "domain_path": "data/3d/mocap/humanml3d",
        "repo_id": "EricGuo/HumanML3D",
        "repo_type": "dataset",
        "format": "hf_dataset",
        "size_mb": 3200.0,
        "presets": ["heavy", "mega", "all"],
        "check_file": "README.md",
        "description": "Standard 3D motion tokens, skeletal pose representations, and text-motion pairs derived from AMASS"
    },
    {
        "id": "unitree_g1_robot_assets",
        "name": "Unitree G1 Humanoid Robot Description (URDF/MJCF & Trajectories)",
        "category": "mocap",
        "domain_path": "data/3d/mocap/unitree_g1",
        "url": "https://github.com/unitreerobotics/unitree_ros/archive/refs/heads/master.zip",
        "format": "zip",
        "size_mb": 350.0,
        "presets": ["standard", "heavy", "mega", "all"],
        "check_file": "README.md",
        "description": "Unitree G1 humanoid 29-DOF kinematics, URDF/MJCF physical meshes, joint limits, and baseline simulation locomotion trajectories"
    },
    {
        "id": "vfhq_facial_mocap_dataset",
        "name": "VFHQ High-Quality Video Face Dataset (4D Facial Dynamics & Mocap)",
        "category": "mocap",
        "domain_path": "data/3d/mocap/vfhq",
        "repo_id": "CelebV-HQ/VFHQ-Subset",
        "repo_type": "dataset",
        "format": "hf_dataset",
        "size_mb": 8500.0,
        "presets": ["heavy", "mega", "all"],
        "check_file": "README.md",
        "description": "1080p+ studio and wild face video dataset with dense temporal facial expressions, head rotations, and micro-motion dynamics"
    },
    {
        "id": "nersemble_multiview_4d_face",
        "name": "NeRSemble Multi-View Dynamic 4D Face Benchmark Suite",
        "category": "mocap",
        "domain_path": "data/3d/mocap/nersemble",
        "url": "https://github.com/SimonGiebenhain/NeRSemble/archive/refs/heads/main.zip",
        "format": "zip",
        "size_mb": 1200.0,
        "presets": ["standard", "heavy", "mega", "all"],
        "check_file": "README.md",
        "description": "Multi-camera synchronous 4K calibrated dynamic 4D facial performance sequences & evaluation benchmarks"
    },
    {
        "id": "flame_eval_fitting_dataset",
        "name": "FLAME 4D Expression Ground Truth Benchmark (NoW & Stirling Subset)",
        "category": "mocap",
        "domain_path": "data/3d/mocap/flame_now_eval",
        "url": "https://github.com/Soubhik-Sanyal/now_evaluation/archive/refs/heads/master.zip",
        "format": "zip",
        "size_mb": 650.0,
        "presets": ["standard", "heavy", "mega", "all"],
        "check_file": "README.md",
        "description": "NoW (No-Warp) 3D head scan ground-truth dataset for evaluating metric identity reconstruction and sub-millimeter error"
    },
    {
        "id": "freihand_mocap_dataset",
        "name": "FreiHAND Single-Hand 3D Pose & MANO Mesh Dataset",
        "category": "mocap",
        "domain_path": "data/3d/mocap/freihand",
        "url": "https://lmb.informatik.uni-freiburg.de/data/freihand/FreiHAND_pub_v2.zip",
        "format": "zip",
        "size_mb": 3500.0,
        "presets": ["heavy", "mega", "all"],
        "check_file": "README.md",
        "description": "Gold-standard monocular 3D hand pose and MANO mesh ground-truth evaluation benchmark (33k unique samples)"
    },
    {
        "id": "interhand_26m_dataset",
        "name": "InterHand2.6M Bimanual Interacting Hands Dataset (Subset)",
        "category": "mocap",
        "domain_path": "data/3d/mocap/interhand26m",
        "repo_id": "facebookresearch/InterHand2.6M-Subset",
        "repo_type": "dataset",
        "format": "hf_dataset",
        "size_mb": 4800.0,
        "presets": ["heavy", "mega", "all"],
        "check_file": "README.md",
        "description": "Large-scale 2.6M-frame multi-camera dataset for 3D interacting two-hand pose estimation under mutual occlusion"
    },
    {
        "id": "oakink_hoi_dataset",
        "name": "OakInk Hand-Object Affordance & Interaction Dataset",
        "category": "mocap",
        "domain_path": "data/3d/mocap/oakink",
        "url": "https://github.com/oakink/OakInk/archive/refs/heads/main.zip",
        "format": "zip",
        "size_mb": 3600.0,
        "presets": ["heavy", "mega", "all"],
        "check_file": "README.md",
        "description": "Affordance-driven hand-object interaction knowledge base with 1,800+ 3D objects and contact-aware MANO meshes"
    },
    {
        "id": "human36m_mocap_dataset",
        "name": "Human3.6M Large-Scale 3D Human Pose & Mocap Dataset (HuggingFace Mirror)",
        "category": "mocap",
        "domain_path": "data/3d/mocap/human36m",
        "repo_id": "ryushinn/Human3.6M",
        "repo_type": "dataset",
        "format": "hf_dataset",
        "size_mb": 4500.0,
        "presets": ["benchmarks", "standard", "heavy", "mega", "all"],
        "check_file": "README.md",
        "description": "Standard 3.6M 3D human pose dataset (Subjects S1, S5, S6, S7, S8, S9, S11) with multi-view video and 3D joint ground truth"
    },

    # --------------------------------------------------------------------------
    # 7. Hair Rendering & Real-World Terrain DEM (data/3d/hair_terrain/)
    # --------------------------------------------------------------------------
    {
        "id": "cem_yuksel_curly_hair",
        "name": "Cem Yuksel Curly Hair Model (Million-Strand Benchmark)",
        "category": "hair_terrain",
        "domain_path": "data/3d/hair_terrain/cem_yuksel_hair",
        "url": "http://www.cemyuksel.com/research/hairmodels/wCurly.zip",
        "format": "zip",
        "size_mb": 420.0,
        "presets": ["mega", "all"],
        "check_file": "wCurly.hair",
        "description": "SIGGRAPH hair rendering benchmark with over 1 million individual simulated spline hair curves"
    },
    {
        "id": "cem_yuksel_straight_hair",
        "name": "Cem Yuksel Straight Hair Model",
        "category": "hair_terrain",
        "domain_path": "data/3d/hair_terrain/cem_yuksel_hair",
        "url": "http://www.cemyuksel.com/research/hairmodels/wStraight.zip",
        "format": "zip",
        "size_mb": 310.0,
        "presets": ["mega", "all"],
        "check_file": "wStraight.hair",
        "description": "Long straight hair model for Marschner and dual-scattering specular reflection validation"
    },
    {
        "id": "cem_yuksel_wavy_hair",
        "name": "Cem Yuksel Wavy Hair Model",
        "category": "hair_terrain",
        "domain_path": "data/3d/hair_terrain/cem_yuksel_hair",
        "url": "http://www.cemyuksel.com/research/hairmodels/wWavy.zip",
        "format": "zip",
        "size_mb": 350.0,
        "presets": ["mega", "all"],
        "check_file": "wWavy.hair",
        "description": "Volumetric wavy hair locks for shadowing and subsurface transmission tests"
    },
    {
        "id": "cem_yuksel_blonde_hair",
        "name": "Cem Yuksel Blonde Hair Model",
        "category": "hair_terrain",
        "domain_path": "data/3d/hair_terrain/cem_yuksel_hair",
        "url": "http://www.cemyuksel.com/research/hairmodels/blonde.zip",
        "format": "zip",
        "size_mb": 7.2,
        "presets": ["mega", "all"],
        "check_file": "blonde.hair",
        "description": "Blonde hair model calibrated for high multi-scattering albedo and melanin absorption"
    },
    {
        "id": "terrain_rocky_mountain",
        "name": "16-bit Rocky Mountain Heightmap (DEM)",
        "category": "hair_terrain",
        "domain_path": "data/3d/hair_terrain/heightmaps",
        "url": "https://assets.babylonjs.com/textures/heightMap.png",
        "format": "raw",
        "size_mb": 15.0,
        "presets": ["heavy", "mega", "all"],
        "target_filename": "rocky_mountain_heightmap.png",
        "check_file": "rocky_mountain_heightmap.png",
        "description": "High-precision 16-bit greyscale digital elevation model for CDLOD continuous terrain displacement"
    },
    {
        "id": "terrain_triplanar",
        "name": "16-bit TriPlanar Terrain Heightmap",
        "category": "hair_terrain",
        "domain_path": "data/3d/hair_terrain/heightmaps",
        "url": "https://assets.babylonjs.com/textures/heightMapTriPlanar.png",
        "format": "raw",
        "size_mb": 18.0,
        "presets": ["heavy", "mega", "all"],
        "target_filename": "triplanar_terrain_heightmap.png",
        "check_file": "triplanar_terrain_heightmap.png",
        "description": "16-bit elevation map designed for cliff and triplanar slope texturing"
    },
    {
        "id": "terrain_world_continent",
        "name": "World Continental Scale Terrain Map",
        "category": "hair_terrain",
        "domain_path": "data/3d/hair_terrain/heightmaps",
        "url": "https://assets.babylonjs.com/textures/worldHeightMap.jpg",
        "format": "raw",
        "size_mb": 8.5,
        "presets": ["heavy", "mega", "all"],
        "target_filename": "world_continent_heightmap.jpg",
        "check_file": "world_continent_heightmap.jpg",
        "description": "Planetary/continental scale topographical terrain elevation map"
    },

    # --------------------------------------------------------------------------
    # 8. Blender Studio Open Movie Production Benchmarks (data/3d/blender_production/)
    # --------------------------------------------------------------------------
    {
        "id": "blender_wasp_bot",
        "name": "Blender Studio: Wasp Bot Mech Benchmark",
        "category": "blender_production",
        "domain_path": "data/3d/blender_production/wasp_bot",
        "url": "https://download.blender.org/demo/eevee/wasp_bot/wasp_bot.blend",
        "format": "raw",
        "size_mb": 142.0,
        "presets": ["heavy", "mega", "all"],
        "target_filename": "wasp_bot.blend",
        "check_file": "wasp_bot.blend",
        "description": "Official Blender EEVEE/Cycles benchmark: mechanical wasp robot with complex kinematics"
    },
    {
        "id": "blender_race_spaceship",
        "name": "Blender Studio: Race Spaceship Sci-Fi Benchmark",
        "category": "blender_production",
        "domain_path": "data/3d/blender_production/race_spaceship",
        "url": "https://download.blender.org/demo/eevee/race_spaceship/race_spaceship.blend",
        "format": "raw",
        "size_mb": 86.0,
        "presets": ["heavy", "mega", "all"],
        "target_filename": "race_spaceship.blend",
        "check_file": "race_spaceship.blend",
        "description": "Sci-fi racing vehicle with procedural metallic paint, carbon fiber, and thruster glows"
    },
    {
        "id": "blender_bmw_car",
        "name": "Blender Studio: BMW 2.7 Automotive Benchmark",
        "category": "blender_production",
        "domain_path": "data/3d/blender_production/bmw_car",
        "url": "https://download.blender.org/demo/test/BMW27_2.blend.zip",
        "mirrors": [
            "https://download.blender.org/demo/test/BMW27_2.blend.zip",
            "https://mirror.clarkson.edu/blender/demo/test/BMW27_2.blend.zip",
            "https://mirrors.dotsrc.org/blender/demo/test/BMW27_2.blend.zip"
        ],
        "format": "zip",
        "size_mb": 29.0,
        "presets": ["heavy", "mega", "all"],
        "check_file": "BMW27_2.blend",
        "description": "The standard automotive rendering speed and sampling convergence benchmark"
    },
    {
        "id": "blender_classroom",
        "name": "Blender Studio: Classroom Architectural Benchmark",
        "category": "blender_production",
        "domain_path": "data/3d/blender_production/classroom",
        "url": "https://download.blender.org/demo/test/classroom.zip",
        "mirrors": [
            "https://download.blender.org/demo/test/classroom.zip",
            "https://mirror.clarkson.edu/blender/demo/test/classroom.zip",
            "https://mirrors.dotsrc.org/blender/demo/test/classroom.zip"
        ],
        "format": "zip",
        "size_mb": 67.0,
        "presets": ["heavy", "mega", "all"],
        "check_file": "classroom.blend",
        "description": "Indoor classroom with dozens of wooden desks, books, chalkboard, and complex volumetric sun shafts"
    },

    # --------------------------------------------------------------------------
    # 9. Kenney Complete CC0 Suite (All 20+ Kits, data/cg/game_assets/kenney/)
    # --------------------------------------------------------------------------
    {
        "id": "kenney_space_kit",
        "name": "Kenney Space Kit (3D CC0)",
        "category": "game_assets",
        "domain_path": "data/cg/game_assets/kenney/space_kit",
        "url": "https://kenney.nl/assets/space-kit",
        "kenney_slug": "space-kit",
        "format": "zip",
        "size_mb": 12.0,
        "presets": ["heavy", "mega", "all"],
        "check_file": "README.md",
        "description": "Modular spaceships, cockpits, hangars, planetary terrain tiles, and asteroids"
    },
    {
        "id": "kenney_castle_kit",
        "name": "Kenney Castle Kit (3D CC0)",
        "category": "game_assets",
        "domain_path": "data/cg/game_assets/kenney/castle_kit",
        "url": "https://kenney.nl/assets/castle-kit",
        "kenney_slug": "castle-kit",
        "format": "zip",
        "size_mb": 14.0,
        "presets": ["heavy", "mega", "all"],
        "check_file": "README.md",
        "description": "Medieval castle fortress walls, battlement towers, drawbridges, and siege props"
    },
    {
        "id": "kenney_medieval_kit",
        "name": "Kenney Medieval Village Kit (3D CC0)",
        "category": "game_assets",
        "domain_path": "data/cg/game_assets/kenney/medieval_kit",
        "url": "https://kenney.nl/assets/fantasy-town-kit",
        "kenney_slug": "fantasy-town-kit",
        "format": "zip",
        "size_mb": 16.0,
        "presets": ["heavy", "mega", "all"],
        "check_file": "README.md",
        "description": "Medieval timber cottages, market stalls, wagons, barrels, and cobblestone paving"
    },
    {
        "id": "kenney_furniture_kit",
        "name": "Kenney Furniture & Interior Kit (3D CC0)",
        "category": "game_assets",
        "domain_path": "data/cg/game_assets/kenney/furniture_kit",
        "url": "https://kenney.nl/assets/furniture-kit",
        "kenney_slug": "furniture-kit",
        "format": "zip",
        "size_mb": 18.0,
        "presets": ["heavy", "mega", "all"],
        "check_file": "README.md",
        "description": "Interior design props: sofas, desks, chairs, kitchens, electronics, and lamps"
    },
    {
        "id": "kenney_city_kit",
        "name": "Kenney Modern City Kit (3D CC0)",
        "category": "game_assets",
        "domain_path": "data/cg/game_assets/kenney/city_kit",
        "url": "https://kenney.nl/assets/city-kit-commercial",
        "kenney_slug": "city-kit-commercial",
        "format": "zip",
        "size_mb": 22.0,
        "presets": ["heavy", "mega", "all"],
        "check_file": "README.md",
        "description": "Modern downtown skyscrapers, avenues, crosswalks, traffic signals, and street signs"
    },
    {
        "id": "kenney_city_suburban_kit",
        "name": "Kenney City Suburban Kit (3D CC0)",
        "category": "game_assets",
        "domain_path": "data/cg/game_assets/kenney/city_suburban",
        "url": "https://kenney.nl/assets/city-kit-suburban",
        "kenney_slug": "city-kit-suburban",
        "format": "zip",
        "size_mb": 20.0,
        "presets": ["heavy", "mega", "all"],
        "check_file": "README.md",
        "description": "Residential suburban houses, garages, driveways, white picket fences, and lawns"
    },
    {
        "id": "kenney_car_kit",
        "name": "Kenney Modular Car Kit (3D CC0)",
        "category": "game_assets",
        "domain_path": "data/cg/game_assets/kenney/car_kit",
        "url": "https://kenney.nl/assets/car-kit",
        "kenney_slug": "car-kit",
        "format": "zip",
        "size_mb": 15.0,
        "presets": ["heavy", "mega", "all"],
        "check_file": "README.md",
        "description": "Customizable vehicle chassis, wheels, spoilers, engines, police cars, and ambulances"
    },
    {
        "id": "kenney_nature_kit",
        "name": "Kenney Nature & Foliage Kit (3D CC0)",
        "category": "game_assets",
        "domain_path": "data/cg/game_assets/kenney/nature_kit",
        "url": "https://kenney.nl/assets/nature-kit",
        "kenney_slug": "nature-kit",
        "format": "zip",
        "size_mb": 14.0,
        "presets": ["heavy", "mega", "all"],
        "check_file": "README.md",
        "description": "Low-poly trees, rocks, pine trees, bushes, logs, and water plants"
    },
    {
        "id": "kenney_survival_kit",
        "name": "Kenney Survival & Crafting Kit (3D CC0)",
        "category": "game_assets",
        "domain_path": "data/cg/game_assets/kenney/survival_kit",
        "url": "https://kenney.nl/assets/survival-kit",
        "kenney_slug": "survival-kit",
        "format": "zip",
        "size_mb": 11.0,
        "presets": ["heavy", "mega", "all"],
        "check_file": "README.md",
        "description": "Campfires, tents, survival tools, axes, backpacks, and wood craftables"
    },
    {
        "id": "kenney_platformer_3d",
        "name": "Kenney Starter Kit: 3D Platformer (CC0)",
        "category": "game_assets",
        "domain_path": "data/cg/game_assets/kenney/platformer_3d",
        "url": "https://github.com/KenneyNL/Starter-Kit-3D-Platformer/archive/refs/heads/master.zip",
        "format": "zip",
        "size_mb": 8.5,
        "presets": ["quick", "standard", "heavy", "mega", "all"],
        "check_file": "project.godot",
        "description": "Full 3D platformer game kit: animated character controller, coins, hazards, and floating platforms"
    },
    {
        "id": "kenney_fps_3d",
        "name": "Kenney Starter Kit: 3D FPS (CC0)",
        "category": "game_assets",
        "domain_path": "data/cg/game_assets/kenney/fps_3d",
        "url": "https://github.com/KenneyNL/Starter-Kit-FPS/archive/refs/heads/master.zip",
        "format": "zip",
        "size_mb": 4.2,
        "presets": ["standard", "heavy", "mega", "all"],
        "check_file": "project.godot",
        "description": "First-Person Shooter game kit with modular guns, hitscan shooting, crosshairs, targets, and arena"
    },
    {
        "id": "kenney_racing_3d",
        "name": "Kenney Starter Kit: 3D Racing (CC0)",
        "category": "game_assets",
        "domain_path": "data/cg/game_assets/kenney/racing_3d",
        "url": "https://github.com/KenneyNL/Starter-Kit-Racing/archive/refs/heads/master.zip",
        "format": "zip",
        "size_mb": 6.1,
        "presets": ["standard", "heavy", "mega", "all"],
        "check_file": "project.godot",
        "description": "Arcade racing game starter kit with raycast vehicle physics, modular race tracks, and timers"
    },
    {
        "id": "kenney_city_3d",
        "name": "Kenney Starter Kit: City Builder (CC0)",
        "category": "game_assets",
        "domain_path": "data/cg/game_assets/kenney/city_builder_3d",
        "url": "https://github.com/KenneyNL/Starter-Kit-City-Builder/archive/refs/heads/master.zip",
        "format": "zip",
        "size_mb": 5.0,
        "presets": ["heavy", "mega", "all"],
        "check_file": "project.godot",
        "description": "Grid-based city management starter kit with building placement, roads, and camera controller"
    },

    # --------------------------------------------------------------------------
    # 10. KayKit Modular Low-Poly Suite (data/cg/game_assets/kaykit/)
    # --------------------------------------------------------------------------
    {
        "id": "kaykit_dungeon",
        "name": "KayKit Dungeon Remastered Pack (CC0)",
        "category": "game_assets",
        "domain_path": "data/cg/game_assets/kaykit/dungeon_remastered",
        "url": "https://github.com/KayKit-Game-Assets/KayKit-Dungeon-Remastered-1.0/archive/refs/heads/main.zip",
        "format": "zip",
        "size_mb": 6.3,
        "presets": ["quick", "standard", "heavy", "mega", "all"],
        "check_file": "README.md",
        "description": "Modular 3D dungeon kit with walls, floors, pillars, doors, chests, torches, and barrels"
    },
    {
        "id": "kaykit_characters",
        "name": "KayKit Animated Adventurers & Skeletons (CC0)",
        "category": "game_assets",
        "domain_path": "data/cg/game_assets/kaykit/characters",
        "url": "https://github.com/KayKit-Game-Assets/KayKit-Character-Pack-Adventures-1.0/archive/refs/heads/main.zip",
        "format": "zip",
        "size_mb": 6.1,
        "presets": ["quick", "standard", "heavy", "mega", "all"],
        "check_file": "README.md",
        "description": "Rigged low-poly characters (Knight, Rogue, Wizard, Skeletons) with full walk/run/attack animations"
    },
    {
        "id": "kaykit_prototype",
        "name": "KayKit Prototype Bits (CC0)",
        "category": "game_assets",
        "domain_path": "data/cg/game_assets/kaykit/prototype_bits",
        "url": "https://github.com/KayKit-Game-Assets/KayKit-Prototype-Bits-1.0/archive/refs/heads/main.zip",
        "format": "zip",
        "size_mb": 3.2,
        "presets": ["standard", "heavy", "mega", "all"],
        "check_file": "README.md",
        "description": "Greybox level design prototyping geometry: stairs, ramps, pillars, triggers, and jump pads"
    },
    {
        "id": "kaykit_city",
        "name": "KayKit City Builder Bits (CC0)",
        "category": "game_assets",
        "domain_path": "data/cg/game_assets/kaykit/city_builder",
        "url": "https://github.com/KayKit-Game-Assets/KayKit-City-Builder-Bits-1.0/archive/refs/heads/main.zip",
        "format": "zip",
        "size_mb": 5.8,
        "presets": ["standard", "heavy", "mega", "all"],
        "check_file": "README.md",
        "description": "Modular modern city elements: skyscrapers, suburban houses, asphalt roads, traffic lights, cars"
    },
    {
        "id": "kaykit_medieval",
        "name": "KayKit Medieval Hexagon Pack (CC0)",
        "category": "game_assets",
        "domain_path": "data/cg/game_assets/kaykit/medieval_pack",
        "url": "https://github.com/KayKit-Game-Assets/KayKit-Medieval-Hexagon-Pack-1.0/archive/refs/heads/main.zip",
        "format": "zip",
        "size_mb": 5.4,
        "presets": ["heavy", "mega", "all"],
        "check_file": "README.md",
        "description": "Hexagonal strategy / medieval village tiles with castles, timber cottages, farms, and windmills"
    },

    # --------------------------------------------------------------------------
    # 11. Animated 3D Characters & Skeletal Rigs (data/cg/game_assets/characters/)
    # --------------------------------------------------------------------------
    {
        "id": "character_fox",
        "name": "Khronos Fox (glTF 2.0 Skeletal Animation)",
        "category": "characters",
        "domain_path": "data/cg/game_assets/characters/fox",
        "url": "https://raw.githubusercontent.com/KhronosGroup/glTF-Sample-Models/master/2.0/Fox/glTF-Binary/Fox.glb",
        "format": "raw",
        "size_mb": 0.16,
        "presets": ["quick", "standard", "heavy", "mega", "all"],
        "target_filename": "Fox.glb",
        "check_file": "Fox.glb",
        "description": "Stylized fox character with 3 keyframe animation clips: Survey, Walk, and Run"
    },
    {
        "id": "character_cesium_man",
        "name": "Cesium Man (Humanoid Rigged glTF 2.0)",
        "category": "characters",
        "domain_path": "data/cg/game_assets/characters/cesium_man",
        "url": "https://raw.githubusercontent.com/KhronosGroup/glTF-Sample-Models/master/2.0/CesiumMan/glTF-Binary/CesiumMan.glb",
        "format": "raw",
        "size_mb": 0.5,
        "presets": ["quick", "standard", "heavy", "mega", "all"],
        "target_filename": "CesiumMan.glb",
        "check_file": "CesiumMan.glb",
        "description": "Rigged humanoid character with skeletal skinning weights and continuous walking loop"
    },
    {
        "id": "character_brainstem",
        "name": "Khronos BrainStem (Bipedal Robot glTF 2.0)",
        "category": "characters",
        "domain_path": "data/cg/game_assets/characters/brainstem",
        "url": "https://raw.githubusercontent.com/KhronosGroup/glTF-Sample-Models/master/2.0/BrainStem/glTF-Binary/BrainStem.glb",
        "format": "raw",
        "size_mb": 9.5,
        "presets": ["standard", "heavy", "mega", "all"],
        "target_filename": "BrainStem.glb",
        "check_file": "BrainStem.glb",
        "description": "Complex bipedal robotic character with intricate skeletal hierarchy and fluid martial motions"
    },

    # --------------------------------------------------------------------------
    # 12. Complete Playable Open-Source 3D Game Projects (data/cg/game_demos/)
    # --------------------------------------------------------------------------
    {
        "id": "game_godot_tps_demo",
        "name": "Godot Official 3D Third-Person Shooter (TPS) Demo",
        "category": "game_demos",
        "domain_path": "data/cg/game_demos/godot_tps",
        "url": "https://github.com/godotengine/tps-demo/archive/refs/heads/master.zip",
        "format": "zip",
        "size_mb": 115.0,
        "presets": ["standard", "heavy", "mega", "all"],
        "check_file": "project.godot",
        "description": "Complete production-grade 3D TPS demo: player kinematics, dynamic cameras, lighting, and arena"
    },
]

# ==============================================================================
# Base Directory Auto-Discovery (Aligned with SSOT V2.1)
# ==============================================================================

def resolve_base_directory(explicit_path: Optional[str] = None, prefer_local: bool = False) -> Path:
    """
    Resolve the root directory where the 5-pillar SSOT structure (data/, repo/, etc.) lives.
    Priority order:
      1. Explicit --base-dir argument
      2. If prefer_local is True (--local / --colab-local): local high-speed NVMe (/content/dervgen or ./dervgen)
      3. Environment variable DERVGEN_DRIVE_ROOT
      4. Google Colab default mount: /content/drive/MyDrive/dervgen
      5. Auto-detected parent if current directory is inside a dervgen workspace
      6. Fallback to ./dervgen
    """
    if explicit_path:
        p = Path(explicit_path).expanduser().resolve()
        p.mkdir(parents=True, exist_ok=True)
        return p

    if prefer_local:
        if Path("/content").exists():
            colab_local = Path("/content/dervgen")
            colab_local.mkdir(parents=True, exist_ok=True)
            return colab_local
        cwd_local = Path.cwd().resolve() / "dervgen"
        cwd_local.mkdir(parents=True, exist_ok=True)
        return cwd_local

    env_root = os.environ.get("DERVGEN_DRIVE_ROOT")
    if env_root and os.path.exists(env_root):
        return Path(env_root).resolve()

    colab_default = Path("/content/drive/MyDrive/dervgen")
    if colab_default.exists() or Path("/content/drive/MyDrive").exists():
        colab_default.mkdir(parents=True, exist_ok=True)
        return colab_default

    cwd = Path.cwd().resolve()
    # Check if current directory or ancestors match dervgen root
    for candidate in [cwd] + list(cwd.parents):
        if (candidate / "data").is_dir() or (candidate / "repo").is_dir():
            return candidate
        if candidate.name.lower() == "dervgen":
            return candidate

    fallback = cwd / "dervgen"
    fallback.mkdir(parents=True, exist_ok=True)
    return fallback

def get_local_scratch_dir() -> Path:
    """
    Returns a fast local NVMe scratch directory for archive decompression.
    Guarantees decompression NEVER occurs over slow Google Drive FUSE mounts.
    """
    colab_scratch = Path("/content/_dervgen_scratch")
    if Path("/content").exists():
        colab_scratch.mkdir(parents=True, exist_ok=True)
        return colab_scratch

    temp_scratch = Path(tempfile.gettempdir()) / "dervgen_scratch"
    temp_scratch.mkdir(parents=True, exist_ok=True)
    return temp_scratch

# ==============================================================================
# Robust Download & Extraction Utilities
# ==============================================================================

def create_resilient_ssl_context() -> ssl.SSLContext:
    """Create an SSL context that tolerates expired server CDN certificates."""
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    return ctx

DEFAULT_USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
)

def download_file_with_progress(
    url: str,
    dest_path: Path,
    label: str,
    max_retries: int = 3,
    referer: Optional[str] = None,
    headers_override: Optional[Dict[str, str]] = None,
    opener: Optional[Any] = None,
    mirrors: Optional[List[str]] = None
) -> bool:
    """
    Download a remote binary file using urllib with streaming chunks, speed calculation,
    automatic retry logic, custom opener/headers, and mirror fallback support.
    """
    dest_path.parent.mkdir(parents=True, exist_ok=True)
    if dest_path.exists() and dest_path.stat().st_size > 1024:
        print(f"    ⏩ [SKIP] Target file already exists: {dest_path.name} ({dest_path.stat().st_size / (1024*1024):.1f} MB)")
        return True

    temp_path = dest_path.with_suffix(dest_path.suffix + ".tmp")

    urls_to_try = [url]
    if mirrors:
        for m in mirrors:
            if m not in urls_to_try:
                urls_to_try.append(m)

    headers = dict(headers_override) if headers_override else {
        "User-Agent": DEFAULT_USER_AGENT,
        "Accept": "*/*",
        "Connection": "keep-alive"
    }
    if referer and "Referer" not in headers:
        headers["Referer"] = referer

    ssl_ctx = create_resilient_ssl_context()

    for cur_url_idx, cur_url in enumerate(urls_to_try):
        if cur_url_idx > 0:
            print(f"    🔄 Trying mirror [{cur_url_idx+1}/{len(urls_to_try)}]: {cur_url}")

        for attempt in range(1, max_retries + 1):
            try:
                req = urllib.request.Request(cur_url, headers=headers)
                open_fn = opener.open if opener else lambda r, timeout: urllib.request.urlopen(r, context=ssl_ctx, timeout=timeout)
                with open_fn(req, timeout=60) as resp:
                    status_code = resp.getcode()
                    if status_code != 200:
                        print(f"    ⚠️  [Attempt {attempt}/{max_retries}] Non-200 status {status_code} for {label} ({cur_url})")
                        time.sleep(2)
                        continue

                    content_type = resp.headers.get("Content-Type", "").lower()
                    if "text/html" in content_type:
                        print(f"    ⚠️  [Attempt {attempt}/{max_retries}] Remote server returned HTML webpage instead of binary: {cur_url}")
                        break

                    total_bytes = int(resp.headers.get("Content-Length", 0))
                    downloaded = 0
                    start_time = time.time()
                    last_print_time = start_time

                    with open(temp_path, "wb") as f:
                        chunk_size = 64 * 1024
                        while True:
                            chunk = resp.read(chunk_size)
                            if not chunk:
                                break
                            f.write(chunk)
                            downloaded += len(chunk)

                            now = time.time()
                            if now - last_print_time >= 0.5:
                                elapsed = now - start_time
                                speed = (downloaded / (1024 * 1024)) / elapsed if elapsed > 0 else 0
                                if total_bytes > 0:
                                    pct = (downloaded / total_bytes) * 100
                                    d_mb = downloaded / (1024 * 1024)
                                    t_mb = total_bytes / (1024 * 1024)
                                    print(f"\r    ↓ {label}: {d_mb:.1f}/{t_mb:.1f} MB ({pct:.1f}%) @ {speed:.2f} MB/s", end="", flush=True)
                                else:
                                    d_mb = downloaded / (1024 * 1024)
                                    print(f"\r    ↓ {label}: {d_mb:.1f} MB @ {speed:.2f} MB/s", end="", flush=True)
                                last_print_time = now

                    elapsed = time.time() - start_time
                    avg_speed = (downloaded / (1024 * 1024)) / elapsed if elapsed > 0 else 0
                    d_mb = downloaded / (1024 * 1024)
                    print(f"\r    ✅ {label}: {d_mb:.1f} MB downloaded successfully ({avg_speed:.2f} MB/s)          ", flush=True)

                    if temp_path.exists():
                        if dest_path.exists():
                            dest_path.unlink()
                        temp_path.rename(dest_path)
                    return True

            except (urllib.error.URLError, urllib.error.HTTPError, OSError, TimeoutError) as e:
                if temp_path.exists():
                    try:
                        temp_path.unlink()
                    except OSError:
                        pass
                print(f"\n    ⚠️  [Attempt {attempt}/{max_retries}] Download failed for {label}: {e}")
                if attempt < max_retries:
                    time.sleep(2 * attempt)
                else:
                    break

    return False

def download_kenney_kit_with_session(slug: str, zip_dest: Path, label: str) -> bool:
    """
    Robust session-aware Kenney.nl direct downloader.
    Uses CookieJar and mimics real browser request sequence to prevent 403 Forbidden.
    Fallback to reliable community CDN/mirrors if Kenney.nl blocks datacenter IPs.
    """
    import http.cookiejar
    cj = http.cookiejar.CookieJar()
    ssl_ctx = create_resilient_ssl_context()
    opener = urllib.request.build_opener(
        urllib.request.HTTPCookieProcessor(cj),
        urllib.request.HTTPSHandler(context=ssl_ctx)
    )

    browser_headers = {
        "User-Agent": DEFAULT_USER_AGENT,
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1"
    }

    page_url = f"https://kenney.nl/assets/{slug}"
    # 1. Warm up session cookies by visiting asset page
    try:
        req_page = urllib.request.Request(page_url, headers=browser_headers)
        with opener.open(req_page, timeout=15):
            pass
    except Exception as e:
        print(f"    ℹ️  Warm-up visit to {page_url} resulted in: {e}")

    # 2. Request signed AJAX download URL
    hex_id = f"assets/{slug}".encode("utf-8").hex()
    api_url = f"https://kenney.nl/download-link/{hex_id}"
    api_headers = dict(browser_headers)
    api_headers.update({
        "Referer": page_url,
        "X-Requested-With": "XMLHttpRequest",
        "Accept": "application/json, text/javascript, */*; q=0.01",
        "Sec-Fetch-Dest": "empty",
        "Sec-Fetch-Mode": "cors",
        "Sec-Fetch-Site": "same-origin"
    })

    signed_url = None
    try:
        req_api = urllib.request.Request(api_url, headers=api_headers)
        with opener.open(req_api, timeout=20) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            signed_url = data.get("url")
    except Exception as e:
        print(f"    ⚠️  Failed to resolve signed Kenney link: {e}")

    # 3. If signed URL obtained, download using the established session
    if signed_url:
        dl_headers = dict(browser_headers)
        dl_headers.update({
            "Referer": page_url,
            "Sec-Fetch-Dest": "document",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Site": "same-origin"
        })
        ok = download_file_with_progress(
            signed_url,
            zip_dest,
            label,
            headers_override=dl_headers,
            opener=opener
        )
        if ok and zip_dest.exists() and zip_dest.stat().st_size > 10000:
            return True

    # 4. Fallback: Secondary direct mirrors
    fallback_urls = [
        f"https://github.com/ETdoFresh/kenney.nl/raw/master/{slug}.zip",
        f"https://raw.githubusercontent.com/ETdoFresh/kenney.nl/master/{slug}.zip",
    ]
    for fb_url in fallback_urls:
        print(f"    🔄 Trying fallback mirror for Kenney kit: {fb_url}")
        if download_file_with_progress(fb_url, zip_dest, label):
            if zip_dest.exists() and zip_dest.stat().st_size > 10000:
                return True

    return False

def extract_zip_neatly(zip_path: Path, target_dir: Path, machine_dir: Optional[Path] = None) -> bool:
    """
    Extract a .zip archive into target_dir or machine_dir (local machine NVMe).
    If the zip contains a single top-level folder, flattens it directly into destination
    to avoid nested 'folder/folder/' directory bloat.
    Extraction scratch space always lives on fast local NVMe disk to protect Google Drive.
    Cleans up the zip archive after successful extraction.
    """
    dest = machine_dir if machine_dir else target_dir
    dest.mkdir(parents=True, exist_ok=True)

    scratch_base = get_local_scratch_dir()
    temp_extract = scratch_base / f"_ext_zip_{zip_path.stem}_{os.getpid()}_{int(time.time()*1000)}"
    if temp_extract.exists():
        shutil.rmtree(temp_extract, ignore_errors=True)
    temp_extract.mkdir(parents=True, exist_ok=True)

    print(f"    📦 Extracting {zip_path.name} via local NVMe scratch ({temp_extract.name})...")
    try:
        with zipfile.ZipFile(zip_path, "r") as zf:
            zf.extractall(temp_extract)

        entries = [e for e in temp_extract.iterdir() if e.name != "__MACOSX"]

        # If archive had a single enclosing root folder, flatten its children
        if len(entries) == 1 and entries[0].is_dir():
            inner_dir = entries[0]
            for child in inner_dir.iterdir():
                dest_child = dest / child.name
                if dest_child.exists():
                    if dest_child.is_dir():
                        shutil.rmtree(dest_child, ignore_errors=True)
                    else:
                        dest_child.unlink()
                shutil.move(str(child), str(dest_child))
        else:
            for item in entries:
                dest_item = dest / item.name
                if dest_item.exists():
                    if dest_item.is_dir():
                        shutil.rmtree(dest_item, ignore_errors=True)
                    else:
                        dest_item.unlink()
                shutil.move(str(item), str(dest_item))

        # Cleanup temp directory and archive
        shutil.rmtree(temp_extract, ignore_errors=True)
        try:
            zip_path.unlink()
        except OSError:
            pass
        return True

    except Exception as e:
        print(f"    ⚠️  Extraction failed for {zip_path.name}: {e}")
        shutil.rmtree(temp_extract, ignore_errors=True)
        return False

def extract_tar_neatly(tar_path: Path, target_dir: Path, machine_dir: Optional[Path] = None) -> bool:
    """
    Extract a .tgz / .tar.gz archive into target_dir or machine_dir (local machine NVMe)
    with single root flattening and cleanup.
    Extraction scratch space always lives on fast local NVMe disk to avoid Drive FUSE I/O stalls.
    """
    dest = machine_dir if machine_dir else target_dir
    dest.mkdir(parents=True, exist_ok=True)

    scratch_base = get_local_scratch_dir()
    temp_extract = scratch_base / f"_ext_tar_{tar_path.stem}_{os.getpid()}_{int(time.time()*1000)}"
    if temp_extract.exists():
        shutil.rmtree(temp_extract, ignore_errors=True)
    temp_extract.mkdir(parents=True, exist_ok=True)

    print(f"    📦 Extracting {tar_path.name} via local NVMe scratch ({temp_extract.name})...")
    try:
        with tarfile.open(tar_path, "r:gz") as tar:
            tar.extractall(temp_extract)

        entries = [e for e in temp_extract.iterdir() if e.name != "__MACOSX"]

        if len(entries) == 1 and entries[0].is_dir():
            inner_dir = entries[0]
            for child in inner_dir.iterdir():
                dest_child = dest / child.name
                if dest_child.exists():
                    if dest_child.is_dir():
                        shutil.rmtree(dest_child, ignore_errors=True)
                    else:
                        dest_child.unlink()
                shutil.move(str(child), str(dest_child))
        else:
            for item in entries:
                dest_item = dest / item.name
                if dest_item.exists():
                    if dest_item.is_dir():
                        shutil.rmtree(dest_item, ignore_errors=True)
                    else:
                        dest_item.unlink()
                shutil.move(str(item), str(dest_item))

        shutil.rmtree(temp_extract, ignore_errors=True)
        try:
            tar_path.unlink()
        except OSError:
            pass
        return True
    except Exception as e:
        print(f"    ⚠️  Extraction failed for {tar_path.name}: {e}")
        shutil.rmtree(temp_extract, ignore_errors=True)
        return False

def download_hf_dataset(repo_id: str, local_dir: Path, label: str, repo_type: str = "dataset") -> bool:
    """
    Download or resume a massive dataset (NeRF / Mocap / 3DGS) from Hugging Face Hub.
    Uses multi-threaded parallel chunk streaming with mirror fallback.
    """
    local_dir.mkdir(parents=True, exist_ok=True)
    try:
        from huggingface_hub import snapshot_download
        print(f"    🤗 [HuggingFace Hub] Ingesting {label} ({repo_id})...")
        explicit_endpoint = os.environ.get("HF_ENDPOINT")
        endpoints = [explicit_endpoint] if explicit_endpoint else [None, "https://hf-mirror.com"]

        for ep in endpoints:
            for attempt in range(1, 4):
                try:
                    kwargs = {
                        "repo_id": repo_id,
                        "repo_type": repo_type,
                        "local_dir": str(local_dir),
                        "local_dir_use_symlinks": False,
                        "resume_download": True,
                        "max_workers": 6,
                    }
                    if ep:
                        kwargs["endpoint"] = ep
                    snapshot_download(**kwargs)
                    print(f"    ✅ {label}: Snapshot completed successfully via Hugging Face Hub.")
                    return True
                except Exception as e:
                    print(f"    ⚠️  [Attempt {attempt}/3] HF download glitch (endpoint={ep or 'default'}): {e}")
                    time.sleep(3)
        return False
    except ImportError:
        print(f"    ⚠️  'huggingface_hub' is not installed. Please run: pip install huggingface_hub")
        return False

# ==============================================================================
# Core Orchestration Logic & Decompression Guards
# ==============================================================================

def mark_asset_installed(dest_dir: Path, asset: Dict[str, Any], machine_dir: Optional[Path] = None):
    """Creates a lightweight .installed.json marker inside the asset destination directory."""
    try:
        dest_dir.mkdir(parents=True, exist_ok=True)
        marker_file = dest_dir / ".installed.json"
        payload = {
            "id": asset.get("id"),
            "name": asset.get("name"),
            "format": asset.get("format"),
            "check_file": asset.get("check_file"),
            "installed_at": datetime.now(timezone.utc).isoformat()
        }
        if machine_dir and machine_dir != dest_dir:
            payload["machine_dir"] = str(machine_dir)
        with open(marker_file, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2, ensure_ascii=False)

        if machine_dir and machine_dir != dest_dir:
            machine_dir.mkdir(parents=True, exist_ok=True)
            machine_marker = machine_dir / ".installed.json"
            with open(machine_marker, "w", encoding="utf-8") as f:
                json.dump(payload, f, indent=2, ensure_ascii=False)
    except Exception:
        pass

def is_already_extracted(archive_path: Path, target_dir: Path, asset: Dict[str, Any], machine_dir: Optional[Path] = None) -> bool:
    """
    Determines if target_dir or machine_dir already contains the extracted payload of archive_path,
    preventing redundant and expensive re-extraction of multi-gigabyte archives.
    """
    check_dirs = [target_dir]
    if machine_dir and machine_dir != target_dir:
        check_dirs.append(machine_dir)

    for d in check_dirs:
        if not d.exists():
            continue

        marker = d / ".installed.json"
        if marker.exists() and marker.stat().st_size > 0:
            return True

        # Check candidate files
        candidates: List[str] = []
        if asset.get("check_files"):
            candidates.extend(asset["check_files"])
        if asset.get("check_file") and asset["check_file"] not in candidates:
            candidates.append(asset["check_file"])

        for c in candidates:
            c_path = d / c
            if c_path.exists() and (c_path.is_dir() or c_path.stat().st_size > 0):
                return True
            c_base = Path(c).name.lower()
            try:
                for entry in d.iterdir():
                    if entry.name.lower() == c_base and (entry.is_dir() or entry.stat().st_size > 0):
                        return True
            except OSError:
                pass

        # Check for substantive extracted content (excluding archive files, temp files, and macOS metadata)
        try:
            archive_names = {
                archive_path.name.lower(),
                archive_path.name.lower() + ".tmp",
                "_extract_tmp",
                "__macosx",
                ".installed.json"
            }
            valid_entries = [
                e for e in d.iterdir()
                if e.name.lower() not in archive_names and not e.name.endswith(".tmp")
            ]
            if len(valid_entries) >= 2 or any(e.is_dir() for e in valid_entries):
                return True
            if len(valid_entries) == 1 and valid_entries[0].is_file() and valid_entries[0].stat().st_size > 1024:
                return True
        except OSError:
            pass

    return False

def check_asset_exists(asset: Dict[str, Any], base_dir: Path, machine_base: Optional[Path] = None) -> bool:
    """
    Check if an asset has already been downloaded and verified.
    Supports case-insensitive filename matching, multiple candidate files (check_files),
    shallow subfolder resolution, fast .installed.json marker detection,
    and automatic heuristic detection for already-extracted directories.
    Also inspects machine_base (local NVMe) if provided.
    """
    dest_dir = base_dir / asset["domain_path"]
    check_dirs = [dest_dir]
    if machine_base:
        machine_dest = machine_base / asset["domain_path"]
        if machine_dest != dest_dir:
            check_dirs.append(machine_dest)

    for d in check_dirs:
        if not d.exists():
            continue

        # 1. Fast marker check
        marker = d / ".installed.json"
        if marker.exists() and marker.stat().st_size > 0:
            try:
                with open(marker, "r", encoding="utf-8") as f:
                    marker_data = json.load(f)
                machine_target = marker_data.get("machine_dir")
                if machine_target and Path(machine_target).exists():
                    return True
            except Exception:
                pass
            data_files = [f for f in d.iterdir() if f.name != ".installed.json" and (f.is_file() or f.is_dir())]
            if data_files:
                return True

        # 2. Check candidate files
        candidates: List[str] = []
        if asset.get("check_files"):
            candidates.extend(asset["check_files"])
        if asset.get("check_file") and asset["check_file"] not in candidates:
            candidates.append(asset["check_file"])

        if candidates:
            for check_filename in candidates:
                # Direct relative path check
                candidate = d / check_filename
                if candidate.exists() and (candidate.is_dir() or candidate.stat().st_size > 0):
                    mark_asset_installed(dest_dir, asset)
                    return True

                # Fast shallow check across immediate root entries and subfolders
                target_basename = Path(check_filename).name.lower()
                try:
                    for entry in d.iterdir():
                        if entry.name.lower() == target_basename and (entry.is_dir() or entry.stat().st_size > 0):
                            mark_asset_installed(dest_dir, asset)
                            return True
                        if entry.is_dir():
                            sub_candidate = entry / check_filename
                            if sub_candidate.exists() and (sub_candidate.is_dir() or sub_candidate.stat().st_size > 0):
                                mark_asset_installed(dest_dir, asset)
                                return True
                            sub_direct = entry / target_basename
                            if sub_direct.exists() and (sub_direct.is_dir() or sub_direct.stat().st_size > 0):
                                mark_asset_installed(dest_dir, asset)
                                return True
                except OSError:
                    pass

        # 3. For archive/raw assets, check if the directory already contains substantive extracted content
        try:
            archive_names = {
                f"{asset['id']}.zip".lower(),
                f"{asset['id']}.tgz".lower(),
                f"{asset['id']}.tar.gz".lower(),
                "_extract_tmp",
                ".installed.json",
                "__macosx"
            }
            extracted_entries = [
                e for e in d.iterdir()
                if e.name.lower() not in archive_names and not e.name.endswith(".tmp")
            ]
            if len(extracted_entries) >= 2 or any(e.is_dir() for e in extracted_entries):
                mark_asset_installed(dest_dir, asset)
                return True
            elif len(extracted_entries) == 1 and extracted_entries[0].is_file() and extracted_entries[0].stat().st_size > 1024:
                mark_asset_installed(dest_dir, asset)
                return True
        except OSError:
            pass

    return False

def run_asset_download(
    base_dir: Path,
    categories: Optional[List[str]] = None,
    preset: str = "standard",
    dry_run: bool = False,
    force: bool = False,
    include_ai_models: bool = False,
    skip_disney: bool = False,
    extract_to_machine: bool = False,
    machine_dir: Optional[Path] = None
) -> Dict[str, Any]:
    """Execute the multi-category 3D and game asset download workflow."""

    selected_assets: List[Dict[str, Any]] = []

    for asset in ASSET_REGISTRY:
        # Disney isolation filter
        if skip_disney and "disney" in asset.get("id", "").lower():
            continue
        # Category filter
        if categories and "all" not in categories and asset["category"] not in categories:
            continue
        # Preset filter
        if preset != "all" and preset not in asset.get("presets", []):
            continue
        selected_assets.append(asset)

    print("=" * 80)
    print("  🎨 DERVGEN: MEGA OPEN 3D RESOURCES & GAME ASSETS DOWNLOADER (SSOT V2.1)")
    print("=" * 80)
    print(f"  📁 Base Root:           {base_dir}")
    if extract_to_machine and machine_dir:
        print(f"  ⚡ Machine Target:      {machine_dir} (Decompression directly to local NVMe)")
    print(f"  🏷️  Preset:              {preset.upper()}")
    print(f"  📂 Categories:          {', '.join(categories) if categories else 'ALL'}")
    if skip_disney:
        print("  🚫 Disney Moana:        SKIPPED (Explicitly bypassed 66 GB)")
    print(f"  📦 Total Asset Units:   {len(selected_assets)}")
    total_mb = sum(a["size_mb"] for a in selected_assets)
    print(f"  💾 Estimated Volume:    ~{total_mb:.1f} MB ({total_mb / 1024:.2f} GB)")
    if include_ai_models:
        print("  🧠 3D AI Foundation:    ENABLED (+180 GB via init_models.py)")
    if dry_run:
        print("  🔍 Mode:                DRY-RUN (Preview only, no downloads)")
    print("-" * 80)

    if dry_run:
        print("\n[PLAN] Assets that would be processed:")
        for idx, a in enumerate(selected_assets, 1):
            dest = base_dir / a["domain_path"]
            exists = check_asset_exists(a, base_dir, machine_base=machine_dir if extract_to_machine else None)
            status = "⏩ ALREADY PRESENT" if exists else "📥 PENDING DOWNLOAD"
            print(f"  [{idx:02d}/{len(selected_assets):02d}] {status}: {a['name']}")
            print(f"       Category: {a['category']} | Size: ~{a['size_mb']:.1f} MB ({a['size_mb'] / 1024:.2f} GB)")
            print(f"       Target:   {dest}")
            source = a.get("url") or a.get("repo_id")
            print(f"       Source:   {source}\n")
        print("Dry run complete. No files were modified.")
        return {"total": len(selected_assets), "dry_run": True}

    downloaded_count = 0
    skipped_count = 0
    failed_count = 0
    downloaded_bytes = 0

    for idx, asset in enumerate(selected_assets, 1):
        name = asset["name"]
        cat = asset["category"]
        fmt = asset["format"]
        target_dir = base_dir / asset["domain_path"]
        machine_dest = (machine_dir / asset["domain_path"]) if (extract_to_machine and machine_dir) else None

        size_disp = f"{asset['size_mb']:.1f} MB" if asset['size_mb'] < 1024 else f"{asset['size_mb']/1024:.2f} GB"
        print(f"\n[{idx:02d}/{len(selected_assets):02d}] Processing [{cat}] {name} (~{size_disp})...")

        # Global existence check
        if not force and check_asset_exists(asset, base_dir, machine_base=machine_dir if extract_to_machine else None):
            print(f"  ⏩ [SKIP] Already downloaded and verified: {target_dir}")
            skipped_count += 1
            continue

        target_dir.mkdir(parents=True, exist_ok=True)
        if machine_dest:
            machine_dest.mkdir(parents=True, exist_ok=True)

        if fmt == "raw":
            url = asset["url"]
            filename = asset.get("target_filename") or Path(url).name
            dest_file = (machine_dest / filename) if machine_dest else (target_dir / filename)
            mirrors = asset.get("mirrors")
            success = download_file_with_progress(url, dest_file, name, mirrors=mirrors)
            if success:
                mark_asset_installed(target_dir, asset, machine_dir=machine_dest)
                downloaded_count += 1
                if dest_file.exists():
                    downloaded_bytes += dest_file.stat().st_size
            else:
                failed_count += 1
                print(f"  ❌ Failed to download {name}")

        elif fmt == "zip":
            kenney_slug = asset.get("kenney_slug")
            archive_name = f"{asset['id']}.zip"
            zip_dest = target_dir / archive_name

            # Guard 1: Check if ALREADY extracted before attempting download
            if not force and is_already_extracted(zip_dest, target_dir, asset, machine_dir=machine_dest):
                print(f"  ⏩ [SKIP] Archive content already extracted in: {machine_dest or target_dir}")
                mark_asset_installed(target_dir, asset, machine_dir=machine_dest)
                if zip_dest.exists():
                    try:
                        zip_dest.unlink()
                    except OSError:
                        pass
                skipped_count += 1
                continue

            if kenney_slug or ("kenney.nl" in asset.get("url", "") and "assets/" in asset.get("url", "")):
                slug = kenney_slug or asset["url"].rstrip("/").split("/")[-1]
                success = download_kenney_kit_with_session(slug, zip_dest, name)
            else:
                url = asset["url"]
                mirrors = asset.get("mirrors")
                success = download_file_with_progress(url, zip_dest, name, mirrors=mirrors)

            if success:
                # Guard 2: Check if extracted before unzipping
                if is_already_extracted(zip_dest, target_dir, asset, machine_dir=machine_dest):
                    print(f"  ⏩ [SKIP] Content already extracted, skipping unzip: {machine_dest or target_dir}")
                    mark_asset_installed(target_dir, asset, machine_dir=machine_dest)
                    if zip_dest.exists():
                        try:
                            zip_dest.unlink()
                        except OSError:
                            pass
                    downloaded_count += 1
                else:
                    extract_ok = extract_zip_neatly(zip_dest, target_dir, machine_dir=machine_dest)
                    if extract_ok:
                        mark_asset_installed(target_dir, asset, machine_dir=machine_dest)
                        downloaded_count += 1
                        downloaded_bytes += int(asset["size_mb"] * 1024 * 1024)
                    else:
                        failed_count += 1
                        print(f"  ❌ Failed to extract {archive_name}")
            else:
                failed_count += 1
                print(f"  ❌ Failed to download archive for {name}")

        elif fmt == "tgz":
            url = asset["url"]
            mirrors = asset.get("mirrors")
            archive_name = f"{asset['id']}.tgz"
            tar_dest = target_dir / archive_name

            # Guard 1: Check if ALREADY extracted before attempting download
            if not force and is_already_extracted(tar_dest, target_dir, asset, machine_dir=machine_dest):
                print(f"  ⏩ [SKIP] Archive content already extracted in: {machine_dest or target_dir}")
                mark_asset_installed(target_dir, asset, machine_dir=machine_dest)
                if tar_dest.exists():
                    try:
                        tar_dest.unlink()
                    except OSError:
                        pass
                skipped_count += 1
                continue

            success = download_file_with_progress(url, tar_dest, name, mirrors=mirrors)
            if success:
                # Guard 2: Check if extracted before untarring
                if is_already_extracted(tar_dest, target_dir, asset, machine_dir=machine_dest):
                    print(f"  ⏩ [SKIP] Content already extracted, skipping untar: {machine_dest or target_dir}")
                    mark_asset_installed(target_dir, asset, machine_dir=machine_dest)
                    if tar_dest.exists():
                        try:
                            tar_dest.unlink()
                        except OSError:
                            pass
                    downloaded_count += 1
                else:
                    extract_ok = extract_tar_neatly(tar_dest, target_dir, machine_dir=machine_dest)
                    if extract_ok:
                        mark_asset_installed(target_dir, asset, machine_dir=machine_dest)
                        downloaded_count += 1
                        downloaded_bytes += int(asset["size_mb"] * 1024 * 1024)
                    else:
                        failed_count += 1
                        print(f"  ❌ Failed to extract {archive_name}")
            else:
                failed_count += 1
                print(f"  ❌ Failed to download archive for {name}")

        elif fmt == "hf_dataset":
            repo_id = asset["repo_id"]
            repo_type = asset.get("repo_type", "dataset")
            hf_dest = machine_dest if machine_dest else target_dir
            success = download_hf_dataset(repo_id, hf_dest, name, repo_type=repo_type)
            if success:
                mark_asset_installed(target_dir, asset, machine_dir=machine_dest)
                downloaded_count += 1
                downloaded_bytes += int(asset["size_mb"] * 1024 * 1024)
            else:
                failed_count += 1
                print(f"  ❌ Failed to ingest Hugging Face dataset {name}")

    # Optional invocation of 3D AI foundation models (~180 GB)
    if include_ai_models:
        print("\n" + "-" * 80)
        print("  🧠 INITIATING 3D AI FOUNDATION MODEL DOWNLOADS (~180 GB)...")
        print("-" * 80)
        init_models_script = Path(__file__).parent / "init_models.py"
        if init_models_script.exists():
            import subprocess
            cmd = [sys.executable, str(init_models_script), "--tier", "all"]
            subprocess.run(cmd)
        else:
            print("  ⚠️  init_models.py not found in script directory.")

    print("\n" + "=" * 80)
    print("  🎉 DOWNLOAD BATCH COMPLETE")
    print("=" * 80)
    print(f"  ✅ Downloaded:  {downloaded_count}")
    print(f"  ⏩ Skipped:     {skipped_count}")
    print(f"  ❌ Failed:      {failed_count}")
    print(f"  💾 Data Volume: ~{downloaded_bytes / (1024 * 1024):.1f} MB ({downloaded_bytes / (1024 * 1024 * 1024):.2f} GB) downloaded")
    print(f"  📁 Base Path:   {base_dir}")
    if extract_to_machine and machine_dir:
        print(f"  ⚡ Machine Path:{machine_dir}")
    print("=" * 80 + "\n")

    return {
        "total": len(selected_assets),
        "downloaded": downloaded_count,
        "skipped": skipped_count,
        "failed": failed_count,
        "bytes": downloaded_bytes
    }

# ==============================================================================
# CLI Entry Point
# ==============================================================================

def main():
    parser = argparse.ArgumentParser(
        description="Download curated open-source 3D resources, benchmark scenes, CC0 materials, HDRIs, NeRF/3DGS, mocap, and game assets."
    )
    parser.add_argument(
        "--base-dir",
        type=str,
        default=None,
        help="Root path for DervGen storage (defaults to auto-detecting /content/drive/MyDrive/dervgen)."
    )
    parser.add_argument(
        "--preset",
        type=str,
        choices=["quick", "standard", "heavy", "mega", "disney", "benchmarks", "all"],
        default="standard",
        help="Download tier preset: 'quick' (~150 MB), 'standard' (~2.5 GB), 'heavy' (~50 GB, Disney excluded), 'mega' (~180+ GB), 'disney' (~66 GB Disney Moana suite), 'benchmarks' (~8.8 GB RFC 0063 suite), 'all'."
    )
    parser.add_argument(
        "--category",
        type=str,
        default="all",
        help="Comma-separated category filters: scenes,models,materials,hdri,radiance_fields,mocap,hair_terrain,blender_production,game_assets,characters,game_demos,all."
    )
    parser.add_argument(
        "--skip-disney",
        action="store_true",
        help="Explicitly skip all Disney Moana Island packages (~66 GB) to save network bandwidth and Drive storage."
    )
    parser.add_argument(
        "--local", "--colab-local",
        action="store_true",
        dest="colab_local",
        help="Store and unpack assets directly onto the local Colab NVMe machine (/content/dervgen) rather than Google Drive FUSE."
    )
    parser.add_argument(
        "--extract-to-machine",
        action="store_true",
        help="Decompress archives directly into the local machine NVMe directory (/content/dervgen) instead of inside Google Drive FUSE."
    )
    parser.add_argument(
        "--machine-dir",
        type=str,
        default=None,
        help="Custom machine local destination for decompressed assets (defaults to /content/dervgen on Colab)."
    )
    parser.add_argument(
        "--include-ai-models",
        action="store_true",
        help="Also download the 75+ 3D AI foundation models (~180 GB) via init_models.py."
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Simulate the workflow and show plan without downloading any files."
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Re-download and overwrite existing assets."
    )

    args = parser.parse_args()

    # Parse categories
    cats = [c.strip().lower() for c in args.category.split(",") if c.strip()]
    base_dir = resolve_base_directory(args.base_dir, prefer_local=args.colab_local)

    # Determine machine_dir
    machine_dir: Optional[Path] = None
    extract_to_machine = args.extract_to_machine or args.colab_local
    if args.machine_dir:
        machine_dir = Path(args.machine_dir).expanduser().resolve()
    elif Path("/content").exists():
        machine_dir = Path("/content/dervgen")
    else:
        machine_dir = Path.cwd().resolve() / "dervgen"

    run_asset_download(
        base_dir=base_dir,
        categories=cats,
        preset=args.preset,
        dry_run=args.dry_run,
        force=args.force,
        include_ai_models=args.include_ai_models,
        skip_disney=args.skip_disney,
        extract_to_machine=extract_to_machine,
        machine_dir=machine_dir
    )

if __name__ == "__main__":
    main()
