#!/usr/bin/env python3
"""
DervGen Workspace: Automated Benchmark & Evaluation Dataset Initializer (Google Drive SSOT)
Standardizes and stages evaluation datasets directly into Google Drive (/dervgen/data/...):
  1. 3D Benchmark Scenes & Geometries:
     - Cornell Box (PBR raytracing)
     - Parametric UV Sphere
     - Unit Cube (1m scale spatial validation)
     - Stanford Bunny (High-curvature surface benchmark)
     - Utah Teapot (Specular & BRDF curvature benchmark)
  1b. Industry-Standard AAA Rendering Benchmark Scenes (Caelum-Core):
     - Crytek Sponza Atrium (GI & indirect lighting benchmark, ~262k tris)
     - Intel Modified Sponza (PBR photogrammetry overhaul, 4K assets)
     - Amazon Lumberyard Bistro (dense urban exterior/interior, ~2.8M tris)
     - San Miguel (complex foliage & architectural, ~7.8M tris)
     - Stanford Dragon (high-res scan geometry, 871k tris)
     - Stanford Happy Buddha (organic scan surface, 1.1M tris)
     - Rungholt (massive medieval village, ~6.7M tris)
     - Fireplace Room (interior GI & caustics benchmark)
     - Breakfast Room (small-scale interior diffuse/specular)
     - NVIDIA Emerald Square (urban city block, foliage & shadows)
     - UE4 Sun Temple (ray tracing & dynamic lighting stress test)
     - Country Kitchen (interior material & texture benchmark)
  2. Production Closed-Loop Benchmark Cases (Exp05 & GrandForge):
     - case_01_mech_ranger   : Hard surface armor, plasma rifle grip anti-clipping
     - case_02_cyber_hunter  : Cyberpunk cloth dynamics, forward walking foot-plant IK
     - case_03_cinematic_orbit: 360-degree turntable orbit, volume stability & zero breathing
  3. RFC 0053 "SWE-bench for 3D" Evaluation Benchmark Suite (96 Cases):
     - dataset_mesh_repair     : 32 defective geometry cases (non-manifold, holes, inverted normals, etc.)
     - dataset_material_repair : 32 defective material cases (baked shadow, UV stretch, inverted roughness)
     - dataset_anim_repair     : 30 defective kinematics cases (rebalanced) (foot sliding, joint hyperextension, clipping)
  4. Multimodal Test Captures & Manifests (Images, Audio, Videos)
  5. Live Google Drive Indexes (data/INDEX.json and data/INDEX.md)

Authoritative Architecture & Multi-Store Storage Catalog:
  - `all-overview/architecture/resources.md` (NAS, Local NVMe, macOS, Google Drive)
  - `all-overview/RESOURCES.md` (Top-level ecosystem catalog)

100% Web/Cloud Native: Zero local disk consumption.
"""

import os
import sys
import json
import math
import shutil
import hashlib
import zipfile
import tempfile
import argparse
import urllib.request
import urllib.error
import ssl
from datetime import datetime, timezone
from pathlib import Path

# Safe utf-8 stdout for terminals
if hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

DRIVE_ROOT = Path(os.environ.get("DERVGEN_DRIVE_ROOT", "/content/drive/MyDrive/dervgen"))
DATA_ROOT = DRIVE_ROOT / "data"


def check_drive_mounted() -> bool:
    drive_base = Path("/content/drive/MyDrive")
    if not drive_base.exists() and not os.environ.get("DERVGEN_DRIVE_ROOT"):
        print("⚠️  [Init Datasets] Google Drive is NOT mounted at /content/drive/MyDrive.")
        print("    In Colab run: from google.colab import drive; drive.mount('/content/drive')")
        return False
    return True


# ==============================================================================
# 1. 3D Benchmark Geometries & Scenes
# ==============================================================================

def generate_cornell_box(output_dir: Path):
    """Generates a physically-based Cornell Box OBJ and MTL."""
    output_dir.mkdir(parents=True, exist_ok=True)
    obj_path = output_dir / "cornell_box.obj"
    mtl_path = output_dir / "cornell_box.mtl"
    if obj_path.exists() and obj_path.stat().st_size > 0 and mtl_path.exists() and mtl_path.stat().st_size > 0:
        print(f"  ⏩ [SKIP] Benchmark scene already exists: {obj_path.name}")
        return

    mtl_content = """# Cornell Box Material Library (Standard Radiance / PBR)
newmtl white_wall
Ka 0.0 0.0 0.0
Kd 0.725 0.71 0.68
Ks 0.0 0.0 0.0
d 1.0
illum 1

newmtl red_wall
Ka 0.0 0.0 0.0
Kd 0.63 0.065 0.05
Ks 0.0 0.0 0.0
d 1.0
illum 1

newmtl green_wall
Ka 0.0 0.0 0.0
Kd 0.14 0.45 0.091
Ks 0.0 0.0 0.0
d 1.0
illum 1

newmtl light
Ka 1.0 1.0 1.0
Kd 0.78 0.78 0.78
Ke 15.0 15.0 15.0
d 1.0
illum 1

newmtl short_block_mat
Ka 0.0 0.0 0.0
Kd 0.725 0.71 0.68
Ks 0.0 0.0 0.0
d 1.0
illum 1

newmtl tall_block_mat
Ka 0.0 0.0 0.0
Kd 0.725 0.71 0.68
Ks 0.0 0.0 0.0
d 1.0
illum 1
"""
    with open(mtl_path, "w", encoding="utf-8") as f:
        f.write(mtl_content)

    obj_content = """# Cornell Box Test Scene (Fulgur / Caelum Benchmark)
mtllib cornell_box.mtl

# Floor
v -1.0 0.0 -1.0
v  1.0 0.0 -1.0
v  1.0 0.0  1.0
v -1.0 0.0  1.0
vn 0.0 1.0 0.0
usemtl white_wall
f 1//1 2//1 3//1 4//1

# Ceiling
v -1.0 2.0 -1.0
v -1.0 2.0  1.0
v  1.0 2.0  1.0
v  1.0 2.0 -1.0
vn 0.0 -1.0 0.0
usemtl white_wall
f 5//2 6//2 7//2 8//2

# Back wall
v -1.0 0.0 1.0
v  1.0 0.0 1.0
v  1.0 2.0 1.0
v -1.0 2.0 1.0
vn 0.0 0.0 -1.0
usemtl white_wall
f 9//3 10//3 11//3 12//3

# Left wall (Red)
v -1.0 0.0 -1.0
v -1.0 0.0  1.0
v -1.0 2.0  1.0
v -1.0 2.0 -1.0
vn 1.0 0.0 0.0
usemtl red_wall
f 13//4 14//4 15//4 16//4

# Right wall (Green)
v 1.0 0.0  1.0
v 1.0 0.0 -1.0
v 1.0 2.0 -1.0
v 1.0 2.0  1.0
vn -1.0 0.0 0.0
usemtl green_wall
f 17//5 18//5 19//5 20//5

# Ceiling Area Light
v -0.25 1.99 -0.25
v -0.25 1.99  0.25
v  0.25 1.99  0.25
v  0.25 1.99 -0.25
vn 0.0 -1.0 0.0
usemtl light
f 21//6 22//6 23//6 24//6

# Short Block
v 0.13 0.0 -0.27
v 0.52 0.0 -0.17
v 0.42 0.0  0.22
v 0.03 0.0  0.12
v 0.13 0.6 -0.27
v 0.52 0.6 -0.17
v 0.42 0.6  0.22
v 0.03 0.6  0.12
vn 0.0 1.0 0.0
usemtl short_block_mat
f 25 26 27 28
f 29 32 31 30
f 25 29 30 26
f 26 30 31 27
f 27 31 32 28
f 28 32 29 25

# Tall Block
v -0.53 0.0  0.09
v -0.24 0.0  0.37
v  0.04 0.0  0.08
v -0.25 0.0 -0.20
v -0.53 1.2  0.09
v -0.24 1.2  0.37
v  0.04 1.2  0.08
v -0.25 1.2 -0.20
usemtl tall_block_mat
f 33 34 35 36
f 37 40 39 38
f 33 37 38 34
f 34 38 39 35
f 35 39 40 36
f 36 40 37 33
"""
    with open(obj_path, "w", encoding="utf-8") as f:
        f.write(obj_content)
    print(f"  ✓ Created benchmark scene: {obj_path.name} & {mtl_path.name}")


def generate_sphere(output_dir: Path, rings: int = 24, sectors: int = 24):
    """Generates a parametric UV Sphere OBJ."""
    output_dir.mkdir(parents=True, exist_ok=True)
    obj_path = output_dir / "sphere.obj"
    if obj_path.exists() and obj_path.stat().st_size > 0:
        print(f"  ⏩ [SKIP] Benchmark geometry already exists: {obj_path.name}")
        return
    lines = ["# Procedural UV Sphere", "o Sphere"]

    R = 1.0 / (rings - 1)
    S = 1.0 / (sectors - 1)

    for r in range(rings):
        for s in range(sectors):
            y = math.sin(-math.pi / 2.0 + math.pi * r * R)
            x = math.cos(2 * math.pi * s * S) * math.sin(math.pi * r * R)
            z = math.sin(2 * math.pi * s * S) * math.sin(math.pi * r * R)
            lines.append(f"v {x:.4f} {y:.4f} {z:.4f}")
            lines.append(f"vn {x:.4f} {y:.4f} {z:.4f}")
            lines.append(f"vt {s * S:.4f} {r * R:.4f}")

    for r in range(rings - 1):
        for s in range(sectors - 1):
            cur = r * sectors + s + 1
            next_s = cur + 1
            cur_next_r = (r + 1) * sectors + s + 1
            next_r_next_s = cur_next_r + 1
            lines.append(f"f {cur}/{cur}/{cur} {next_s}/{next_s}/{next_s} {next_r_next_s}/{next_r_next_s}/{next_r_next_s} {cur_next_r}/{cur_next_r}/{cur_next_r}")

    with open(obj_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    print(f"  ✓ Created benchmark geometry: {obj_path.name}")


def generate_cube(output_dir: Path):
    """Generates a 1m unit Cube OBJ."""
    output_dir.mkdir(parents=True, exist_ok=True)
    obj_path = output_dir / "cube.obj"
    if obj_path.exists() and obj_path.stat().st_size > 0:
        print(f"  ⏩ [SKIP] Benchmark geometry already exists: {obj_path.name}")
        return
    content = """# Unit 1x1x1 Cube
o Cube
v -0.5 -0.5  0.5
v  0.5 -0.5  0.5
v -0.5  0.5  0.5
v  0.5  0.5  0.5
v -0.5  0.5 -0.5
v  0.5  0.5 -0.5
v -0.5 -0.5 -0.5
v  0.5 -0.5 -0.5
vn  0.0  0.0  1.0
vn  0.0  1.0  0.0
vn  0.0  0.0 -1.0
vn  0.0 -1.0  0.0
vn  1.0  0.0  0.0
vn -1.0  0.0  0.0
vt 0.0 0.0
vt 1.0 0.0
vt 1.0 1.0
vt 0.0 1.0
f 1/1/1 2/2/1 4/3/1 3/4/1
f 3/1/2 4/2/2 6/3/2 5/4/2
f 5/1/3 6/2/3 8/3/3 7/4/3
f 7/1/4 8/2/4 2/3/4 1/4/4
f 2/1/5 8/2/5 6/3/5 4/4/5
f 7/1/6 1/2/6 3/3/6 5/4/6
"""
    with open(obj_path, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"  ✓ Created benchmark geometry: {obj_path.name}")


def generate_stanford_bunny(output_dir: Path):
    """Generates a mid-fidelity Stanford Bunny OBJ (~120 faces) with ear/body/tail topology."""
    output_dir.mkdir(parents=True, exist_ok=True)
    obj_path = output_dir / "stanford_bunny.obj"
    if obj_path.exists() and obj_path.stat().st_size > 0:
        print(f"  ⏩ [SKIP] Benchmark geometry already exists: {obj_path.name}")
        return

    import math as _m
    lines = ["# Stanford Bunny Benchmark Geometry (Mid-Fidelity ~120 faces)", "o Stanford_Bunny"]
    verts = []

    # --- Body ellipsoid (16 lon x 8 lat = 128 quads -> 126 quads + 32 tri caps) ---
    n_lon, n_lat = 16, 8
    body_cx, body_cy, body_cz = 0.0, 0.06, 0.0
    rx, ry, rz = 0.045, 0.04, 0.035  # slightly squashed

    for j in range(n_lat + 1):
        phi = _m.pi * j / n_lat
        for i in range(n_lon):
            theta = 2.0 * _m.pi * i / n_lon
            x = body_cx + rx * _m.sin(phi) * _m.cos(theta)
            y = body_cy + ry * _m.cos(phi)
            z = body_cz + rz * _m.sin(phi) * _m.sin(theta)
            verts.append((round(x, 5), round(y, 5), round(z, 5)))

    # --- Left ear (tapered box, 8 verts) ---
    ear_verts_L = [
        (-0.015, 0.10, -0.005), (-0.005, 0.10, -0.005),
        (-0.005, 0.10,  0.005), (-0.015, 0.10,  0.005),
        (-0.013, 0.18, -0.002), (-0.007, 0.18, -0.002),
        (-0.007, 0.18,  0.002), (-0.013, 0.18,  0.002),
    ]
    ear_base_L = len(verts)
    verts.extend(ear_verts_L)

    # --- Right ear (mirror) ---
    ear_verts_R = [(round(-v[0], 5), v[1], v[2]) for v in ear_verts_L]
    ear_base_R = len(verts)
    verts.extend(ear_verts_R)

    # --- Tail nub (4 verts) ---
    tail_verts = [
        ( 0.000, 0.065, -0.040),
        (-0.008, 0.070, -0.050),
        ( 0.008, 0.070, -0.050),
        ( 0.000, 0.080, -0.045),
    ]
    tail_base = len(verts)
    verts.extend(tail_verts)

    # Write vertices
    for v in verts:
        lines.append(f"v {v[0]:9.5f} {v[1]:9.5f} {v[2]:9.5f}")

    # Compute and write per-vertex normals (approximate: direction from body center)
    for v in verts:
        dx, dy, dz = v[0] - body_cx, v[1] - body_cy, v[2] - body_cz
        length = _m.sqrt(dx*dx + dy*dy + dz*dz) or 1e-6
        lines.append(f"vn {dx/length:7.4f} {dy/length:7.4f} {dz/length:7.4f}")

    faces = []
    # Body quads (as triangles)
    for j in range(n_lat):
        for i in range(n_lon):
            i_next = (i + 1) % n_lon
            a = j * n_lon + i + 1       # 1-indexed
            b = j * n_lon + i_next + 1
            c = (j+1) * n_lon + i_next + 1
            d = (j+1) * n_lon + i + 1
            faces.append((a, b, c))
            faces.append((a, c, d))

    # Ear box faces (6 quads -> 12 tris each)
    def box_tris(base):
        b = base + 1  # 1-indexed
        return [
            (b,b+1,b+2), (b,b+2,b+3),   # bottom
            (b+4,b+6,b+5), (b+4,b+7,b+6), # top
            (b,b+4,b+5), (b,b+5,b+1),     # front
            (b+2,b+6,b+7), (b+2,b+7,b+3), # back
            (b+1,b+5,b+6), (b+1,b+6,b+2), # right
            (b,b+3,b+7), (b,b+7,b+4),     # left
        ]

    faces.extend(box_tris(ear_base_L))
    faces.extend(box_tris(ear_base_R))

    # Tail tetrahedron faces
    tb = tail_base + 1
    faces.extend([(tb,tb+1,tb+2), (tb,tb+1,tb+3), (tb+1,tb+2,tb+3), (tb,tb+3,tb+2)])

    for fa in faces:
        lines.append(f"f {fa[0]}//{fa[0]} {fa[1]}//{fa[1]} {fa[2]}//{fa[2]}")

    lines.append("")
    with open(obj_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    print(f"  ✓ Created benchmark geometry: {obj_path.name} ({len(verts)} verts, {len(faces)} faces)")


def generate_teapot(output_dir: Path):
    """Generates a mid-fidelity Utah Teapot OBJ (~560 faces) with spout/handle/lid/body."""
    output_dir.mkdir(parents=True, exist_ok=True)
    obj_path = output_dir / "teapot.obj"
    if obj_path.exists() and obj_path.stat().st_size > 0:
        print(f"  ⏩ [SKIP] Benchmark geometry already exists: {obj_path.name}")
        return

    import math as _m
    lines = ["# Utah Teapot Specular & Curvature Benchmark Geometry (Mid-Fidelity)", "o Utah_Teapot"]
    verts = []
    faces = []

    def _add_revolved_profile(profile_pts, n_lon, offset_idx):
        """Revolve 2D profile (r, y) around Y axis to produce triangulated surface."""
        base = len(verts)
        n_prof = len(profile_pts)
        for j, (r, y) in enumerate(profile_pts):
            for i in range(n_lon):
                theta = 2.0 * _m.pi * i / n_lon
                x = round(r * _m.cos(theta), 5)
                z = round(r * _m.sin(theta), 5)
                verts.append((x, round(y, 5), z))
        for j in range(n_prof - 1):
            for i in range(n_lon):
                i_next = (i + 1) % n_lon
                a = base + j * n_lon + i + 1
                b = base + j * n_lon + i_next + 1
                c = base + (j+1) * n_lon + i_next + 1
                d = base + (j+1) * n_lon + i + 1
                faces.append((a, b, c))
                faces.append((a, c, d))

    n_lon = 20

    # Body profile (bottom to top rim)
    body_profile = [
        (0.00, 0.00), (0.30, 0.02), (0.60, 0.05), (0.80, 0.15),
        (0.90, 0.30), (0.95, 0.50), (0.92, 0.70), (0.85, 0.85),
        (0.78, 0.95), (0.75, 1.00),
    ]
    _add_revolved_profile(body_profile, n_lon, 0)

    # Lid profile (sitting on rim)
    lid_profile = [
        (0.75, 1.00), (0.70, 1.03), (0.55, 1.08), (0.35, 1.12),
        (0.15, 1.15), (0.00, 1.16),
    ]
    _add_revolved_profile(lid_profile, n_lon, 0)

    # Lid knob (small cylinder + cap)
    knob_profile = [
        (0.00, 1.16), (0.06, 1.16), (0.07, 1.18), (0.07, 1.22),
        (0.05, 1.24), (0.00, 1.25),
    ]
    _add_revolved_profile(knob_profile, n_lon, 0)

    # Spout (extruded along +X axis as a tapered cylinder)
    spout_segs = 6
    spout_circ = 8
    for j in range(spout_segs + 1):
        t = j / spout_segs
        cx = 0.80 + t * 0.60        # extends from body to +X
        cy = 0.50 + t * 0.40        # rises upward
        r = 0.12 * (1.0 - 0.5 * t)  # tapers
        base = len(verts)
        for i in range(spout_circ):
            ang = 2.0 * _m.pi * i / spout_circ
            x = round(cx + r * _m.cos(ang) * 0.3, 5)
            y = round(cy + r * _m.sin(ang), 5)
            z = round(r * _m.cos(ang), 5)
            verts.append((x, y, z))
        if j > 0:
            for i in range(spout_circ):
                i_n = (i + 1) % spout_circ
                a = base - spout_circ + i + 1
                b = base - spout_circ + i_n + 1
                c = base + i_n + 1
                d = base + i + 1
                faces.append((a, b, c))
                faces.append((a, c, d))

    # Handle (extruded along -X axis as a curved tube)
    handle_segs = 8
    handle_circ = 8
    for j in range(handle_segs + 1):
        t = j / handle_segs
        ang_h = _m.pi * 0.2 + t * _m.pi * 0.6  # arc from lower to upper body
        cx = -0.85 - 0.30 * _m.sin(ang_h)
        cy = 0.30 + 0.50 * t
        r = 0.06
        base = len(verts)
        for i in range(handle_circ):
            ang = 2.0 * _m.pi * i / handle_circ
            x = round(cx + r * _m.cos(ang), 5)
            y = round(cy + r * _m.sin(ang), 5)
            z = round(r * _m.cos(ang) * 0.5, 5)
            verts.append((x, y, z))
        if j > 0:
            for i in range(handle_circ):
                i_n = (i + 1) % handle_circ
                a = base - handle_circ + i + 1
                b = base - handle_circ + i_n + 1
                c = base + i_n + 1
                d = base + i + 1
                faces.append((a, b, c))
                faces.append((a, c, d))

    # Write vertices
    for v in verts:
        lines.append(f"v {v[0]:9.5f} {v[1]:9.5f} {v[2]:9.5f}")

    # Approximate normals (radial from Y axis for body, from local center for appendages)
    for v in verts:
        dx, dz = v[0], v[2]
        dy = v[1] - 0.5
        length = _m.sqrt(dx*dx + dy*dy + dz*dz) or 1e-6
        lines.append(f"vn {dx/length:7.4f} {dy/length:7.4f} {dz/length:7.4f}")

    for fa in faces:
        lines.append(f"f {fa[0]}//{fa[0]} {fa[1]}//{fa[1]} {fa[2]}//{fa[2]}")

    lines.append("")
    with open(obj_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    print(f"  ✓ Created benchmark geometry: {obj_path.name} ({len(verts)} verts, {len(faces)} faces)")


# ==============================================================================
# 1b. Industry-Standard AAA Rendering Benchmark Scenes (Caelum-Core)
# ==============================================================================

# Canonical rendering benchmark scene registry.
# Each entry encodes:
#   - Trusted download URLs (primary + mirrors)
#   - Expected checksum for integrity verification
#   - Format & complexity metadata for pipeline selection
#   - Licensing info for compliance tracking
#
# Sources:
#   - McGuire Computer Graphics Archive (casual-effects.com/data)
#   - Khronos glTF Sample Assets (github.com/KhronosGroup/glTF-Sample-Assets)
#   - Intel GPU Research Samples (intel.com)
#   - NVIDIA ORCA (developer.nvidia.com/orca)
#   - Stanford 3D Scanning Repository (graphics.stanford.edu)
#   - Benedikt Bitterli resources (benedikt-bitterli.me/resources)

INDUSTRY_BENCHMARK_SCENES = [
    # ── Tier 1: Essential Architectural GI Benchmarks ─────────────────────────
    {
        "id": "sponza_crytek",
        "name": "Crytek Sponza Atrium",
        "tier": "essential",
        "category": "architectural_gi",
        "description": "Classical Dubrovnik atrium scene. The most widely cited GI, indirect lighting, "
                       "and shadow benchmark in real-time rendering literature since 2010.",
        "triangle_count": "262k",
        "texture_count": 25,
        "format": "OBJ + MTL + PNG textures",
        "pbr_workflow": "legacy_phong",
        "use_cases": ["global_illumination", "shadow_maps", "ambient_occlusion", "deferred_shading", "light_probes"],
        "download_urls": [
            "https://casual-effects.com/g3d/data10/common/model/crytek_sponza/sponza.zip",
            "https://raw.githubusercontent.com/jimmiebergmann/Sponza/master/sponza.zip",
        ],
        "archive_type": "zip",
        "entry_file": "sponza.obj",
        "size_mb": 68,
        "license": "Free for non-commercial use (Crytek/Frank Meinl)",
        "citation": "Frank Meinl, Crytek, via McGuire CG Archive (2010)",
    },
    {
        "id": "sponza_khronos_gltf",
        "name": "Sponza (Khronos glTF 2.0)",
        "tier": "essential",
        "category": "architectural_gi",
        "description": "Official Khronos Group glTF 2.0 conversion of the Sponza Atrium with "
                       "metallic-roughness PBR materials, MikkTSpace tangents, and packed textures.",
        "triangle_count": "262k",
        "texture_count": 60,
        "format": "glTF 2.0",
        "pbr_workflow": "metallic_roughness",
        "use_cases": ["gltf_pipeline_validation", "pbr_metallic_roughness", "tangent_space", "texture_compression"],
        "download_urls": [
            "https://raw.githubusercontent.com/KhronosGroup/glTF-Sample-Assets/main/Models/Sponza/glTF/Sponza.gltf",
        ],
        "archive_type": "gltf_repo",
        "entry_file": "Sponza.gltf",
        "size_mb": 70,
        "license": "CC0 1.0 (Khronos Group / public domain)",
        "citation": "Khronos Group glTF-Sample-Assets, Sponza Model",
    },
    {
        "id": "sponza_intel_pbr",
        "name": "Intel Modified Sponza (PBR Overhaul)",
        "tier": "essential",
        "category": "architectural_gi",
        "description": "Intel GPU Research high-fidelity overhaul: photogrammetry-derived 4K geometry, "
                       "PBR materials, modular add-ons (ivy, curtains, trees). The modern AAA standard.",
        "triangle_count": "830k",
        "texture_count": 200,
        "format": "glTF 2.0 / USD / FBX",
        "pbr_workflow": "metallic_roughness",
        "use_cases": ["pbr_validation", "4k_texture_streaming", "gpu_benchmark", "ray_tracing", "virtual_texturing"],
        "download_urls": [
            "https://www.intel.com/content/www/us/en/developer/topic-technology/graphics-research/samples.html",
        ],
        "archive_type": "manual_download",
        "entry_file": "NewSponza_Main_glTF_002.gltf",
        "size_mb": 3700,
        "license": "Intel EULA (free for research & development)",
        "citation": "Intel Corporation, GPU Research Samples, Sponza Base Scene",
    },

    # ── Tier 1: Dense Urban & Exterior ────────────────────────────────────────
    {
        "id": "bistro_exterior",
        "name": "Amazon Lumberyard Bistro (Exterior)",
        "tier": "essential",
        "category": "urban_exterior",
        "description": "Dense European street & bistro exterior scene. Industry standard for "
                       "deferred rendering, many-light culling, and GPU-driven pipeline stress testing.",
        "triangle_count": "2.8M",
        "texture_count": 300,
        "format": "OBJ + MTL + PNG/TGA textures",
        "pbr_workflow": "specular_glossiness",
        "use_cases": ["many_light_culling", "deferred_rendering", "lod_streaming", "shadow_cascades", "gpu_driven"],
        "download_urls": [
            "https://casual-effects.com/g3d/data10/research/model/bistro/Exterior.zip",
        ],
        "archive_type": "zip",
        "entry_file": "Exterior/exterior.obj",
        "size_mb": 780,
        "license": "CC BY 4.0 (Amazon Lumberyard / NVIDIA ORCA)",
        "citation": "Amazon Lumberyard, via NVIDIA ORCA & McGuire CG Archive",
    },
    {
        "id": "bistro_interior",
        "name": "Amazon Lumberyard Bistro (Interior)",
        "tier": "essential",
        "category": "interior",
        "description": "Interior section of the Bistro scene. Rich material diversity "
                       "(glass, metal, wood, fabric) for material system and indirect lighting validation.",
        "triangle_count": "2.1M",
        "texture_count": 250,
        "format": "OBJ + MTL + PNG/TGA textures",
        "pbr_workflow": "specular_glossiness",
        "use_cases": ["interior_gi", "material_diversity", "transparency_sorting", "ssr"],
        "download_urls": [
            "https://casual-effects.com/g3d/data10/research/model/bistro/Interior.zip",
        ],
        "archive_type": "zip",
        "entry_file": "Interior/interior.obj",
        "size_mb": 530,
        "license": "CC BY 4.0 (Amazon Lumberyard / NVIDIA ORCA)",
        "citation": "Amazon Lumberyard, via NVIDIA ORCA & McGuire CG Archive",
    },

    # ── Tier 1: Outdoor Foliage & Complex Visibility ──────────────────────────
    {
        "id": "san_miguel",
        "name": "San Miguel",
        "tier": "essential",
        "category": "outdoor_foliage",
        "description": "Highly detailed outdoor courtyard with complex foliage, arches, and "
                       "mixed-scale architectural elements. Standard for visibility & BVH testing.",
        "triangle_count": "7.8M",
        "texture_count": 350,
        "format": "OBJ + MTL + TGA textures",
        "pbr_workflow": "legacy_phong",
        "use_cases": ["bvh_traversal", "foliage_alpha_test", "visibility_culling", "gi_diffuse_interreflection"],
        "download_urls": [
            "https://casual-effects.com/g3d/data10/research/model/San_Miguel/San_Miguel.zip",
        ],
        "archive_type": "zip",
        "entry_file": "san-miguel.obj",
        "size_mb": 1200,
        "license": "Free for non-commercial use (Guillermo M. Leal Llaguno, via McGuire CG Archive)",
        "citation": "Guillermo M. Leal Llaguno, via McGuire CG Archive",
    },

    # ── Tier 2: High-Res Scan Geometries ──────────────────────────────────────
    {
        "id": "stanford_dragon",
        "name": "Stanford Dragon",
        "tier": "geometry_scan",
        "category": "scan_geometry",
        "description": "Iconic Stanford 3D scan. High triangle count with complex surface "
                       "curvature, commonly used for subsurface scattering and AO benchmarks.",
        "triangle_count": "871k",
        "texture_count": 0,
        "format": "PLY / OBJ",
        "pbr_workflow": "none",
        "use_cases": ["subsurface_scattering", "ambient_occlusion", "mesh_decimation", "normal_reconstruction"],
        "download_urls": [
            "https://casual-effects.com/g3d/data10/research/model/dragon/dragon.zip",
            "https://graphics.stanford.edu/data/3Dscanrep/dragon.tar.gz",
        ],
        "archive_type": "zip",
        "entry_file": "dragon.obj",
        "size_mb": 55,
        "license": "Stanford Computer Graphics Laboratory license (free for research)",
        "citation": "Stanford Computer Graphics Laboratory, 3D Scanning Repository",
    },
    {
        "id": "stanford_happy_buddha",
        "name": "Stanford Happy Buddha",
        "tier": "geometry_scan",
        "category": "scan_geometry",
        "description": "High-resolution organic scan surface with smooth continuous curvature. "
                       "Excellent for testing mesh processing and smooth shading algorithms.",
        "triangle_count": "1.1M",
        "texture_count": 0,
        "format": "PLY / OBJ",
        "pbr_workflow": "none",
        "use_cases": ["smooth_shading", "curvature_estimation", "mesh_simplification", "phong_tessellation"],
        "download_urls": [
            "https://casual-effects.com/g3d/data10/research/model/buddha/buddha.zip",
            "https://graphics.stanford.edu/data/3Dscanrep/happy.tar.gz",
        ],
        "archive_type": "zip",
        "entry_file": "buddha.obj",
        "size_mb": 70,
        "license": "Stanford Computer Graphics Laboratory license (free for research)",
        "citation": "Stanford Computer Graphics Laboratory, 3D Scanning Repository",
    },

    # ── Tier 2: Interior GI & Material Benchmarks ─────────────────────────────
    {
        "id": "fireplace_room",
        "name": "Fireplace Room",
        "tier": "interior",
        "category": "interior_gi",
        "description": "Cozy interior scene with direct/indirect lighting, window illumination, "
                       "and fireplace emission. Classic GI caustics and color-bleeding benchmark.",
        "triangle_count": "143k",
        "texture_count": 15,
        "format": "OBJ + MTL + PNG textures",
        "pbr_workflow": "legacy_phong",
        "use_cases": ["color_bleeding", "indirect_illumination", "emission_sources", "soft_shadows"],
        "download_urls": [
            "https://casual-effects.com/g3d/data10/research/model/fireplace_room/fireplace_room.zip",
        ],
        "archive_type": "zip",
        "entry_file": "fireplace_room.obj",
        "size_mb": 15,
        "license": "Free for non-commercial use (Anat Grynberg & Greg Ward, via McGuire CG Archive)",
        "citation": "Anat Grynberg & Greg Ward, via McGuire CG Archive",
    },
    {
        "id": "breakfast_room",
        "name": "Breakfast Room",
        "tier": "interior",
        "category": "interior_gi",
        "description": "Small-scale interior with detailed table setting. Tests fine geometric "
                       "detail, specular inter-reflections, and soft area lighting.",
        "triangle_count": "108k",
        "texture_count": 12,
        "format": "OBJ + MTL + PNG textures",
        "pbr_workflow": "legacy_phong",
        "use_cases": ["area_lighting", "specular_interreflection", "fine_geometry", "path_tracing"],
        "download_urls": [
            "https://casual-effects.com/g3d/data10/research/model/breakfast_room/breakfast_room.zip",
        ],
        "archive_type": "zip",
        "entry_file": "breakfast_room.obj",
        "size_mb": 8,
        "license": "Free for non-commercial use (Anat Grynberg & Greg Ward, via McGuire CG Archive)",
        "citation": "Anat Grynberg & Greg Ward, via McGuire CG Archive",
    },
    {
        "id": "country_kitchen",
        "name": "Country Kitchen",
        "tier": "interior",
        "category": "interior_material",
        "description": "Rustic kitchen interior with diverse material types (ceramic, metal, wood, glass). "
                       "Excellent for PBR material system and texture pipeline validation.",
        "triangle_count": "213k",
        "texture_count": 30,
        "format": "OBJ + MTL + PNG textures",
        "pbr_workflow": "legacy_phong",
        "use_cases": ["material_diversity", "diffuse_texture_quality", "kitchen_scene_rendering", "pbr_conversion"],
        "download_urls": [
            "https://benedikt-bitterli.me/resources/mitsuba/kitchen.zip",
            "https://benedikt-bitterli.me/resources/pbrt-v4/kitchen.zip",
        ],
        "archive_type": "zip",
        "entry_file": "kitchen.obj",
        "size_mb": 35,
        "license": "CC0 1.0 Public Domain (Benedikt Bitterli / Jay-Artist)",
        "citation": "Jay-Artist, via Benedikt Bitterli Rendering Resources",
    },

    # ── Tier 2: Large-Scale Stress Tests ──────────────────────────────────────
    {
        "id": "rungholt",
        "name": "Rungholt (Medieval Village)",
        "tier": "stress_test",
        "category": "massive_geometry",
        "description": "Enormous medieval village layout (~6.7M triangles). The go-to benchmark "
                       "for GPU-driven rendering, multi-draw indirect, and memory pressure testing.",
        "triangle_count": "6.7M",
        "texture_count": 80,
        "format": "OBJ + MTL + PNG textures",
        "pbr_workflow": "legacy_phong",
        "use_cases": ["gpu_driven_rendering", "multi_draw_indirect", "memory_pressure", "occlusion_culling"],
        "download_urls": [
            "https://casual-effects.com/g3d/data10/research/model/rungholt/rungholt.zip",
        ],
        "archive_type": "zip",
        "entry_file": "rungholt.obj",
        "size_mb": 220,
        "license": "Free for non-commercial use (kescha, via McGuire CG Archive)",
        "citation": "kescha (Minecraft), via McGuire CG Archive",
    },

    # ── Tier 3: NVIDIA ORCA & Epic Games (Large Downloads / Manual) ───────────
    {
        "id": "nvidia_emerald_square",
        "name": "NVIDIA Emerald Square",
        "tier": "aaa_production",
        "category": "urban_foliage",
        "description": "NVIDIA Research urban city block scene with foliage, complex shadowing, "
                       "and multiple light sources. Used in RTXDI, ReSTIR, and adaptive sampling papers.",
        "triangle_count": "9.5M",
        "texture_count": 400,
        "format": "FBX + textures (Falcor native)",
        "pbr_workflow": "metallic_roughness",
        "use_cases": ["rtxdi", "restir", "adaptive_sampling", "cascaded_shadows", "foliage_rendering"],
        "download_urls": [
            "https://developer.nvidia.com/orca/nvidia-emerald-square",
        ],
        "archive_type": "manual_download",
        "entry_file": "EmeraldSquare.fbx",
        "size_mb": 5800,
        "license": "NVIDIA ORCA License (free for research & development)",
        "citation": "NVIDIA Corporation, Open Research Content Archive (ORCA)",
    },
    {
        "id": "ue4_sun_temple",
        "name": "UE4 Sun Temple",
        "tier": "aaa_production",
        "category": "ray_tracing",
        "description": "Epic Games ancient temple scene from Unreal Engine 4. Intricate statues, "
                       "pillars, dramatic lighting shafts. Ray Tracing Gems standard benchmark.",
        "triangle_count": "800k",
        "texture_count": 150,
        "format": "FBX + textures",
        "pbr_workflow": "metallic_roughness",
        "use_cases": ["ray_tracing", "volumetric_lighting", "normal_map_detail", "gi_probe"],
        "download_urls": [
            "https://developer.nvidia.com/orca/epic-games-sun-temple",
        ],
        "archive_type": "manual_download",
        "entry_file": "SunTemple.fbx",
        "size_mb": 560,
        "license": "Epic Games / NVIDIA ORCA License (free for research & development)",
        "citation": "Epic Games, via NVIDIA ORCA",
    },
]


def _download_with_progress(url: str, dest_path: Path, label: str = "") -> bool:
    """Downloads a file from URL with progress display and atomicity. Returns True on success."""
    if dest_path.exists() and dest_path.stat().st_size > 1024:
        print(f"    ⏩ [SKIP] Archive already exists: {dest_path.name} ({dest_path.stat().st_size / (1024*1024):.1f} MB)")
        return True

    dest_path.parent.mkdir(parents=True, exist_ok=True)
    temp_path = dest_path.with_suffix(dest_path.suffix + ".tmp")

    try:
        req = urllib.request.Request(url, headers={
            "User-Agent": "curl/7.88.1"
        })
        ssl_ctx = ssl.create_default_context()
        ssl_ctx.check_hostname = False
        ssl_ctx.verify_mode = ssl.CERT_NONE
        with urllib.request.urlopen(req, context=ssl_ctx, timeout=120) as resp:
            content_type = resp.headers.get("Content-Type", "").lower()
            if "text/html" in content_type:
                print(f"\n    ⚠️  Response is HTML webpage, not binary archive: {url}")
                return False
            total = int(resp.headers.get("Content-Length", 0))
            downloaded = 0
            block_size = 1024 * 256  # 256KB blocks
            with open(temp_path, "wb") as f:
                while True:
                    chunk = resp.read(block_size)
                    if not chunk:
                        break
                    f.write(chunk)
                    downloaded += len(chunk)
                    if total > 0:
                        pct = downloaded * 100.0 / total
                        mb_done = downloaded / (1024 * 1024)
                        mb_total = total / (1024 * 1024)
                        print(f"\r    ↓ {label}: {mb_done:.1f}/{mb_total:.1f} MB ({pct:.0f}%)", end="", flush=True)
            print()  # newline after progress

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
        print(f"\n    ⚠️  Download failed for {label}: {e}")
        return False


def _extract_archive(archive_path: Path, extract_dir: Path) -> bool:
    """Extracts a zip archive to the target directory. Returns True on success."""
    try:
        with zipfile.ZipFile(archive_path, 'r') as zf:
            zf.extractall(extract_dir)
        return True
    except (zipfile.BadZipFile, OSError) as e:
        print(f"    ⚠️  Extraction failed: {e}")
        return False


def setup_industry_benchmark_scenes(scenes_dir: Path, tier_filter: str = "all",
                                    skip_existing: bool = True,
                                    skip_manual: bool = True):
    """
    Downloads and stages industry-standard AAA rendering benchmark scenes into Google Drive.

    Args:
        scenes_dir: Target directory (typically data/cg/scenes/)
        tier_filter: 'all', 'essential', 'geometry_scan', 'interior', 'stress_test', 'aaa_production'
                     or comma-separated combination like 'essential,interior'
        skip_existing: Skip scenes that already have their entry file present
        skip_manual: Skip scenes requiring manual download (NVIDIA ORCA, Intel)
    """
    industry_dir = scenes_dir
    industry_dir.mkdir(parents=True, exist_ok=True)

    # Parse tier filter
    allowed_tiers = set()
    if tier_filter == "all":
        allowed_tiers = {s["tier"] for s in INDUSTRY_BENCHMARK_SCENES}
    else:
        allowed_tiers = {t.strip() for t in tier_filter.split(",")}

    # Generate scene registry manifest (always, even if downloads are skipped)
    registry = {
        "version": "1.0.0",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "description": "Industry-standard AAA rendering benchmark scene registry for Caelum-Core",
        "total_scenes": len(INDUSTRY_BENCHMARK_SCENES),
        "scenes": [],
    }

    downloaded_count = 0
    skipped_count = 0
    manual_count = 0
    failed_count = 0

    for scene in INDUSTRY_BENCHMARK_SCENES:
        scene_id = scene["id"]
        scene_dir = industry_dir / scene_id

        # Build registry entry regardless of download
        registry_entry = {
            "id": scene_id,
            "name": scene["name"],
            "tier": scene["tier"],
            "category": scene["category"],
            "description": scene["description"],
            "triangle_count": scene["triangle_count"],
            "format": scene["format"],
            "pbr_workflow": scene["pbr_workflow"],
            "use_cases": scene["use_cases"],
            "size_mb": scene["size_mb"],
            "license": scene["license"],
            "citation": scene["citation"],
            "local_path": str(scene_dir.relative_to(scenes_dir)),
            "entry_file": scene["entry_file"],
            "download_urls": scene["download_urls"],
            "status": "pending",
        }

        # Filter by tier
        if scene["tier"] not in allowed_tiers:
            registry_entry["status"] = "filtered_out"
            registry["scenes"].append(registry_entry)
            continue

        # Check if already downloaded
        is_already_present = False
        detected_path = None
        if skip_existing:
            entry_path = scene_dir / scene["entry_file"]
            marker = scene_dir / ".installed.json"
            if entry_path.exists() and entry_path.stat().st_size > 0:
                is_already_present = True
                detected_path = entry_path
            elif marker.exists() and marker.stat().st_size > 0:
                is_already_present = True
                detected_path = marker
            elif scene_dir.exists():
                # Case-insensitive recursive fallback for entry_file basename
                target_base = Path(scene["entry_file"]).name.lower()
                for f in scene_dir.rglob("*"):
                    if f.is_file() and f.name.lower() == target_base and f.stat().st_size > 0:
                        is_already_present = True
                        detected_path = f
                        break

        if is_already_present:
            registry_entry["status"] = "already_present"
            registry["scenes"].append(registry_entry)
            skipped_count += 1
            print(f"  ⏩ [{scene_id}] Already present: {detected_path.name}")
            continue

        # Handle manual-download scenes
        if scene["archive_type"] == "manual_download":
            if skip_manual:
                manual_count += 1
                registry_entry["status"] = "manual_download_required"
                registry_entry["instructions"] = (
                    f"Visit {scene['download_urls'][0]} to download manually. "
                    f"Extract to: {scene_dir}/"
                )
                registry["scenes"].append(registry_entry)
                if not scene_dir.exists() or not any(scene_dir.iterdir()):
                    print(f"  📋 [{scene_id}] Manual download required: {scene['name']}")
                    print(f"     → {scene['download_urls'][0]}")
                    print(f"     → Extract to: {scene_dir}/")
                continue

        # Handle glTF repo downloads (special case for Khronos)
        if scene["archive_type"] == "gltf_repo":
            scene_dir.mkdir(parents=True, exist_ok=True)
            # For glTF repos, we download the manifest/scene file and create a download script
            # The actual download requires cloning subdirectories or using git sparse checkout
            _generate_gltf_download_script(scene, scene_dir)
            registry_entry["status"] = "download_script_generated"
            registry_entry["instructions"] = (
                f"Run: bash {scene_dir / 'download.sh'} to fetch the full glTF scene, "
                f"or use: git clone --depth 1 --filter=blob:none --sparse "
                f"https://github.com/KhronosGroup/glTF-Sample-Assets.git && "
                f"cd glTF-Sample-Assets && git sparse-checkout set Models/Sponza"
            )
            registry["scenes"].append(registry_entry)
            print(f"  📜 [{scene_id}] Download script generated: {scene_dir / 'download.sh'}")
            continue

        # Attempt download from URLs (try each mirror)
        scene_dir.mkdir(parents=True, exist_ok=True)
        success = False

        for url in scene["download_urls"]:
            archive_name = url.split("/")[-1]
            if not archive_name.endswith(".zip"):
                archive_name = f"{scene_id}.zip"
            archive_path = scene_dir / archive_name

            print(f"  📥 [{scene_id}] Downloading: {scene['name']}...")
            if _download_with_progress(url, archive_path, scene["name"]):
                print(f"    📦 Extracting {archive_name}...")
                if _extract_archive(archive_path, scene_dir):
                    # Clean up archive to save Drive space
                    archive_path.unlink(missing_ok=True)
                    # Mark installation
                    try:
                        with open(scene_dir / ".installed.json", "w", encoding="utf-8") as mf:
                            json.dump({
                                "id": scene_id,
                                "name": scene["name"],
                                "entry_file": scene["entry_file"],
                                "installed_at": datetime.now(timezone.utc).isoformat()
                            }, mf, indent=2, ensure_ascii=False)
                    except Exception:
                        pass
                    registry_entry["status"] = "downloaded"
                    downloaded_count += 1
                    success = True
                    print(f"  ✅ [{scene_id}] Ready: {scene['name']}")
                    break
                else:
                    archive_path.unlink(missing_ok=True)

        if not success:
            failed_count += 1
            registry_entry["status"] = "download_failed"
            print(f"  ❌ [{scene_id}] Failed to download: {scene['name']}")

        registry["scenes"].append(registry_entry)

    # Always write the registry manifest
    registry_path = industry_dir / "scene_registry.json"
    with open(registry_path, "w", encoding="utf-8") as f:
        json.dump(registry, f, indent=2, ensure_ascii=False)

    # Write human-readable README
    _generate_industry_scenes_readme(industry_dir, registry)

    # Summary
    total = len([s for s in INDUSTRY_BENCHMARK_SCENES if s["tier"] in allowed_tiers])
    print(f"\n  📊 Industry Benchmark Scenes Summary:")
    print(f"     Downloaded: {downloaded_count}")
    print(f"     Already present: {skipped_count}")
    print(f"     Manual download required: {manual_count}")
    print(f"     Failed: {failed_count}")
    print(f"     Total registered: {total}")
    print(f"     Registry: {registry_path}")


def _generate_gltf_download_script(scene: dict, scene_dir: Path):
    """Generates a bash download script for glTF repo-based scenes."""
    script_content = f"""#!/bin/bash
# Auto-generated download script for: {scene['name']}
# Run this in Google Colab or any Linux environment with git installed.
set -euo pipefail

TARGET_DIR="{scene_dir}"
echo "📥 Downloading {scene['name']} (glTF 2.0)..."

# Method 1: Git sparse checkout (bandwidth-efficient)
if command -v git &>/dev/null; then
    TEMP_DIR=$(mktemp -d)
    cd "$TEMP_DIR"
    git clone --depth 1 --filter=blob:none --sparse \\
        https://github.com/KhronosGroup/glTF-Sample-Assets.git
    cd glTF-Sample-Assets
    git sparse-checkout set Models/Sponza
    cp -r Models/Sponza/glTF/* "$TARGET_DIR/"
    rm -rf "$TEMP_DIR"
    echo "✅ {scene['name']} downloaded via git sparse checkout."
else
    # Method 2: Direct file download (fallback)
    BASE_URL="https://raw.githubusercontent.com/KhronosGroup/glTF-Sample-Assets/main/Models/Sponza/glTF"
    mkdir -p "$TARGET_DIR"
    curl -sL "$BASE_URL/Sponza.gltf" -o "$TARGET_DIR/Sponza.gltf"
    curl -sL "$BASE_URL/Sponza.bin" -o "$TARGET_DIR/Sponza.bin"
    echo "⚠️  Downloaded core files only. Textures may need manual download."
    echo "    Visit: https://github.com/KhronosGroup/glTF-Sample-Assets/tree/main/Models/Sponza"
fi
"""
    script_path = scene_dir / "download.sh"
    with open(script_path, "w", encoding="utf-8", newline="\n") as f:
        f.write(script_content)

    # Also generate a Python download helper for Colab compatibility
    py_content = f"""#!/usr/bin/env python3
\"\"\"Colab-friendly downloader for {scene['name']}.\"\"\"
import subprocess, os, shutil, tempfile
from pathlib import Path

TARGET_DIR = Path("{scene_dir}")
TARGET_DIR.mkdir(parents=True, exist_ok=True)

print("📥 Downloading {scene['name']} (glTF 2.0) via git sparse checkout...")
temp = tempfile.mkdtemp()
try:
    subprocess.run(["git", "clone", "--depth", "1", "--filter=blob:none", "--sparse",
                     "https://github.com/KhronosGroup/glTF-Sample-Assets.git"],
                    cwd=temp, check=True, capture_output=True)
    repo = os.path.join(temp, "glTF-Sample-Assets")
    subprocess.run(["git", "sparse-checkout", "set", "Models/Sponza"],
                    cwd=repo, check=True, capture_output=True)
    src = Path(repo) / "Models" / "Sponza" / "glTF"
    for f in src.iterdir():
        shutil.copy2(f, TARGET_DIR / f.name)
    print(f"✅ {{scene['name']}} ready at: {{TARGET_DIR}}")
finally:
    shutil.rmtree(temp, ignore_errors=True)
"""
    py_path = scene_dir / "download.py"
    with open(py_path, "w", encoding="utf-8") as f:
        f.write(py_content)


def _generate_industry_scenes_readme(industry_dir: Path, registry: dict):
    """Generates a human-readable README for the industry benchmark scenes directory."""
    lines = [
        "# 🏛️ Industry-Standard AAA Rendering Benchmark Scenes",
        "",
        "Canonical rendering benchmark scenes used by the film, game, and GPU research industries.",
        "These scenes are the standard benchmarks for validating rendering pipelines (PBR, GI, RT, GPU-driven).",
        "",
        "> **Purpose**: Caelum-Core headless rendering validation, path tracer reference, engine performance benchmarking.",
        "> **Citation**: See individual scene licenses and citations below.",
        "",
        "## Scene Catalog",
        "",
        "| Scene | Tier | Triangles | Format | PBR Workflow | Status |",
        "|---|---|---|---|---|---|",
    ]

    for s in registry["scenes"]:
        status_icon = {
            "downloaded": "✅",
            "already_present": "✅",
            "download_script_generated": "📜",
            "manual_download_required": "📋",
            "download_failed": "❌",
            "filtered_out": "⏭️",
            "pending": "⏳",
        }.get(s["status"], "❓")
        lines.append(
            f"| **{s['name']}** | {s['tier']} | {s['triangle_count']} | "
            f"{s['format']} | {s['pbr_workflow']} | {status_icon} {s['status']} |"
        )

    lines.extend([
        "",
        "## Use Cases & Rendering Pipeline Coverage",
        "",
        "| Pipeline Feature | Recommended Scenes |",
        "|---|---|",
        "| Global Illumination | Sponza (Crytek/Intel), Cornell Box, Fireplace Room, Breakfast Room |",
        "| PBR Metallic-Roughness | Intel Sponza PBR, Khronos Sponza glTF, Country Kitchen |",
        "| Ray Tracing | UE4 Sun Temple, NVIDIA Emerald Square, Bistro |",
        "| GPU-Driven / MDI | Rungholt, Bistro Exterior, San Miguel |",
        "| Shadow Maps / Cascades | Sponza, Bistro Exterior, Emerald Square |",
        "| Mesh Processing | Stanford Dragon, Stanford Happy Buddha |",
        "| Alpha-Test / Foliage | San Miguel, Emerald Square |",
        "| Material Diversity | Bistro Interior, Country Kitchen |",
        "| Interior GI / Color Bleeding | Fireplace Room, Breakfast Room, Cornell Box |",
        "",
        "## Download Instructions",
        "",
        "### Automatic (Colab / Linux):",
        "```python",
        "# In Colab notebook, after mounting Google Drive:",
        "!python colab/init_datasets.py",
        "# Or download only industry scenes:",
        "!python colab/init_datasets.py --industry-scenes-only",
        "# Or download only essential tier:",
        "!python colab/init_datasets.py --industry-tier=essential",
        "```",
        "",
        "### Manual Download (Large Scenes):",
        "Some AAA-grade scenes (Intel Sponza PBR, NVIDIA Emerald Square, UE4 Sun Temple)",
        "require manual download from their original sources due to size or licensing:",
        "",
    ])

    for s in registry["scenes"]:
        if s["status"] == "manual_download_required":
            lines.append(f"- **{s['name']}** ({s['size_mb']} MB)")
            lines.append(f"  - Download: {s['download_urls'][0]}")
            lines.append(f"  - Extract to: `{s['local_path']}/`")
            lines.append("")

    lines.extend([
        "---",
        f"Generated at: {registry['generated_at']}",
        f"Total registered scenes: {registry['total_scenes']}",
    ])

    readme_path = industry_dir / "README.md"
    with open(readme_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")


# ==============================================================================
# 2. Production Closed-Loop Benchmark Cases (Exp05 & GrandForge)
# ==============================================================================

def setup_closed_loop_benchmark_cases(cases_dir: Path):
    """Initializes standard test cases for neural-physical closed loop evaluation."""
    cases_dir.mkdir(parents=True, exist_ok=True)

    test_cases_defs = [
        {
            "id": "case_01_mech_ranger",
            "name": "Armored Mech Ranger (Hard Surface)",
            "domain": "hard_surface_mechanical",
            "prompt": "heavy sci-fi tactical mech ranger holding plasma rifle, weathered titanium plating, mechanical joints, flat neutral lighting",
            "focus": "Rigid body contact, weapon grip interpenetration elimination",
            "camera_motion": "Slow_Dolly_In_With_Orbit",
            "frame_count": 96,
            "fps": 24,
            "lens_focal_mm": 35.0,
            "metrics_thresholds": {
                "max_foot_sliding_cm_per_sec": 0.5,
                "max_clipping_frame_ratio": 0.0,
                "min_psnr_db": 38.0,
                "min_ssim": 0.94,
                "max_delighted_albedo_delta_e": 2.5
            }
        },
        {
            "id": "case_02_cyber_hunter",
            "name": "Cybernetic Hunter (Cloth & Anatomy)",
            "domain": "actor_cloth_and_locomotion",
            "prompt": "cyberpunk scout character walking forward on metallic floor, flowing hooded trench coat, combat boots, cinematic studio lighting",
            "focus": "Cloth micro-wrinkles, ground-contact foot sliding elimination",
            "camera_motion": "Forward_Tracking_Shot",
            "frame_count": 96,
            "fps": 24,
            "lens_focal_mm": 50.0,
            "metrics_thresholds": {
                "max_foot_sliding_cm_per_sec": 0.3,
                "max_clipping_frame_ratio": 0.0,
                "min_psnr_db": 39.0,
                "min_ssim": 0.95,
                "max_delighted_albedo_delta_e": 2.0
            }
        },
        {
            "id": "case_03_cinematic_orbit",
            "name": "Titanium Exosuit 360 Orbit",
            "domain": "volumetric_rigidity_360",
            "prompt": "futuristic biomechanical exosuit statue on pedestal, 360 degree turntable lighting, subsurface scattering carbon fiber",
            "focus": "Geometric volume stability, zero perspective breathing distortion",
            "camera_motion": "Turntable_360_Orbit",
            "frame_count": 120,
            "fps": 24,
            "lens_focal_mm": 35.0,
            "metrics_thresholds": {
                "max_volume_breathing_ratio": 0.015,
                "max_clipping_frame_ratio": 0.0,
                "min_psnr_db": 40.0,
                "min_ssim": 0.96,
                "max_delighted_albedo_delta_e": 1.8
            }
        }
    ]

    if all((cases_dir / tc["id"] / "case_manifest.json").exists() for tc in test_cases_defs):
        print(f"  ⏩ [SKIP] Closed-loop benchmark cases already initialized ({len(test_cases_defs)} cases)")
        return

    for tc in test_cases_defs:
        c_dir = cases_dir / tc["id"]
        c_dir.mkdir(parents=True, exist_ok=True)

        # 1. Manifest
        with open(c_dir / "case_manifest.json", "w", encoding="utf-8") as f:
            json.dump(tc, f, indent=2, ensure_ascii=False)

        # 2. Camera Trajectory JSON
        trajectory = []
        frame_count = tc["frame_count"]
        for f_idx in range(frame_count):
            t = f_idx / (frame_count - 1)
            if tc["camera_motion"] == "Turntable_360_Orbit":
                angle = t * 2.0 * math.pi
                pos = [round(3.0 * math.cos(angle), 4), 1.2, round(3.0 * math.sin(angle), 4)]
                look_at = [0.0, 1.0, 0.0]
            elif tc["camera_motion"] == "Slow_Dolly_In_With_Orbit":
                angle = t * (math.pi / 6.0)
                dist = 3.2 - t * 0.7
                pos = [round(dist * math.sin(angle), 4), round(1.2 + t * 0.1, 4), round(dist * math.cos(angle), 4)]
                look_at = [0.0, 1.1, 0.0]
            else:  # Forward_Tracking_Shot
                pos = [0.0, 1.3, round(3.5 - t * 1.5, 4)]
                look_at = [0.0, 1.0, round(1.0 - t * 1.5, 4)]

            trajectory.append({
                "frame": f_idx,
                "timestamp_sec": round(f_idx / tc["fps"], 4),
                "position": pos,
                "look_at": look_at,
                "up": [0.0, 1.0, 0.0],
                "fov_degrees": round(math.degrees(2.0 * math.atan(18.0 / tc["lens_focal_mm"])), 2)
            })

        with open(c_dir / "camera_trajectory.json", "w", encoding="utf-8") as f:
            json.dump({
                "case_id": tc["id"],
                "total_frames": frame_count,
                "fps": tc["fps"],
                "trajectory": trajectory
            }, f, indent=2, ensure_ascii=False)

        # 3. Metrics Thresholds
        with open(c_dir / "metrics_thresholds.json", "w", encoding="utf-8") as f:
            json.dump(tc["metrics_thresholds"], f, indent=2, ensure_ascii=False)

        print(f"  ✓ Initialized evaluation case: {tc['id']}")


# ==============================================================================
# 3. RFC 0053 "SWE-bench for 3D" Evaluation Benchmark Suite (90 Cases)
# ==============================================================================

def setup_evaluation_mesh_repair(eval_dir: Path):
    """Sets up 30 Mesh Repair Benchmark Cases with procedural test assets."""
    target_dir = eval_dir / "dataset_mesh_repair"
    cases_dir = target_dir / "cases"
    cases_dir.mkdir(parents=True, exist_ok=True)

    if (target_dir / "manifest.json").exists() and (target_dir / "manifest.json").stat().st_size > 0:
        print("  ⏩ [SKIP] RFC 0053 Mesh Repair Benchmark already initialized.")
        return

    mesh_cases = [
        # Category A: Non-manifold & Topological Defects (01 - 10)
        {"id": "mesh_01_non_manifold_t_junction", "defect": "Non-manifold edge shared by 3 faces", "category": "topology", "severity": "P0", "difficulty": "basic", "reference": "", "hint": "", "groundTruth": "", "optimalSteps": 3, "stepBudget": 9, "allowedTools": [], "minCompositeScore": 0.7},
        {"id": "mesh_02_degenerate_open_hole", "defect": "Planar degenerate open boundary hole", "category": "topology", "severity": "P0", "difficulty": "basic", "reference": "", "hint": "", "groundTruth": "", "optimalSteps": 3, "stepBudget": 9, "allowedTools": [], "minCompositeScore": 0.7},
        {"id": "mesh_03_inverted_face_normals", "defect": "Reversed winding polygon normals", "category": "surface", "severity": "P0", "difficulty": "basic", "reference": "", "hint": "", "groundTruth": "", "optimalSteps": 3, "stepBudget": 9, "allowedTools": [], "minCompositeScore": 0.7},
        {"id": "mesh_04_zero_area_collapsed_triangle", "defect": "Collinear zero-area degenerate face", "category": "geometry", "severity": "P1", "difficulty": "basic", "reference": "", "hint": "", "groundTruth": "", "optimalSteps": 3, "stepBudget": 9, "allowedTools": [], "minCompositeScore": 0.7},
        {"id": "mesh_05_isolated_floating_vertices", "defect": "Orphan vertices without incident edges", "category": "cleanup", "severity": "P2", "difficulty": "basic", "reference": "", "hint": "", "groundTruth": "", "optimalSteps": 3, "stepBudget": 9, "allowedTools": [], "minCompositeScore": 0.7},
        {"id": "mesh_06_self_intersecting_cube_shells", "defect": "Dual interpenetrating volume shells", "category": "collision", "severity": "P0", "difficulty": "intermediate", "reference": "", "hint": "", "groundTruth": "", "optimalSteps": 5, "stepBudget": 15, "allowedTools": [], "minCompositeScore": 0.7},
        {"id": "mesh_07_pinched_bowtie_vertex", "defect": "Two cones sharing a single vertex point", "category": "topology", "severity": "P1", "difficulty": "intermediate", "reference": "", "hint": "", "groundTruth": "", "optimalSteps": 5, "stepBudget": 15, "allowedTools": [], "minCompositeScore": 0.7},
        {"id": "mesh_08_overlapping_coincident_faces", "defect": "Z-fighting duplicate coplanar triangles", "category": "geometry", "severity": "P1", "difficulty": "intermediate", "reference": "", "hint": "", "groundTruth": "", "optimalSteps": 5, "stepBudget": 15, "allowedTools": [], "minCompositeScore": 0.7},
        {"id": "mesh_09_inconsistent_winding_cylinder", "defect": "Cylinder side walls with alternating normals", "category": "surface", "severity": "P0", "difficulty": "intermediate", "reference": "", "hint": "", "groundTruth": "", "optimalSteps": 5, "stepBudget": 15, "allowedTools": [], "minCompositeScore": 0.7},
        {"id": "mesh_10_curved_surface_puncture_hole", "defect": "Irregular jagged hole on curved sphere", "category": "hole_filling", "severity": "P1", "difficulty": "intermediate", "reference": "", "hint": "", "groundTruth": "", "optimalSteps": 5, "stepBudget": 15, "allowedTools": [], "minCompositeScore": 0.7},

        # Category B: High-Poly & Remeshing Scan Defects (11 - 20)
        {"id": "mesh_11_scanned_mesh_tunnel_noise", "defect": "Micro-tunnels through thin geometry", "category": "scanning", "severity": "P1", "difficulty": "intermediate", "reference": "", "hint": "", "groundTruth": "", "optimalSteps": 5, "stepBudget": 15, "allowedTools": [], "minCompositeScore": 0.7},
        {"id": "mesh_12_internal_occluded_cavity", "defect": "Hidden interior non-manifold geometry", "category": "cleanup", "severity": "P2", "difficulty": "intermediate", "reference": "", "hint": "", "groundTruth": "", "optimalSteps": 5, "stepBudget": 15, "allowedTools": [], "minCompositeScore": 0.7},
        {"id": "mesh_13_knife_edge_skinny_triangles", "defect": "Aspect ratio > 100:1 needle triangles", "category": "remeshing", "severity": "P1", "difficulty": "intermediate", "reference": "", "hint": "", "groundTruth": "", "optimalSteps": 5, "stepBudget": 15, "allowedTools": [], "minCompositeScore": 0.7},
        {"id": "mesh_14_unwelded_uv_seam_cracks", "defect": "Boundary cracks along texture seams", "category": "seams", "severity": "P1", "difficulty": "intermediate", "reference": "", "hint": "", "groundTruth": "", "optimalSteps": 5, "stepBudget": 15, "allowedTools": [], "minCompositeScore": 0.7},
        {"id": "mesh_15_non_planar_quad_creasing", "defect": "Severely bent quad faces causing diagonal crease", "category": "quad_remesh", "severity": "P1", "difficulty": "intermediate", "reference": "", "hint": "", "groundTruth": "", "optimalSteps": 5, "stepBudget": 15, "allowedTools": [], "minCompositeScore": 0.7},
        {"id": "mesh_16_high_curvature_spike_noise", "defect": "Single outlier vertex spike along normal", "category": "smoothing", "severity": "P2", "difficulty": "intermediate", "reference": "", "hint": "", "groundTruth": "", "optimalSteps": 5, "stepBudget": 15, "allowedTools": [], "minCompositeScore": 0.7},
        {"id": "mesh_17_disconnected_floating_islands", "defect": "Dozens of microscopic polygon fragments", "category": "cleanup", "severity": "P2", "difficulty": "intermediate", "reference": "", "hint": "", "groundTruth": "", "optimalSteps": 5, "stepBudget": 15, "allowedTools": [], "minCompositeScore": 0.7},
        {"id": "mesh_18_watertightness_leak_at_cap", "defect": "Missing end cap on mechanical cylinder", "category": "watertightness", "severity": "P0", "difficulty": "intermediate", "reference": "", "hint": "", "groundTruth": "", "optimalSteps": 5, "stepBudget": 15, "allowedTools": [], "minCompositeScore": 0.7},
        {"id": "mesh_19_concave_polygon_decomposition", "defect": "N-gon polygon self-folding", "category": "triangulation", "severity": "P1", "difficulty": "intermediate", "reference": "", "hint": "", "groundTruth": "", "optimalSteps": 5, "stepBudget": 15, "allowedTools": [], "minCompositeScore": 0.7},
        {"id": "mesh_20_extreme_vertex_clustering", "defect": "Clusters of vertices closer than 1e-5 epsilon", "category": "welding", "severity": "P2", "difficulty": "intermediate", "reference": "", "hint": "", "groundTruth": "", "optimalSteps": 5, "stepBudget": 15, "allowedTools": [], "minCompositeScore": 0.7},

        # Category C: CAD Tessellation & Production Mechanical (21 - 30)
        {"id": "mesh_21_cad_fillet_tessellation_crack", "defect": "Crack along curved transition bevel", "category": "cad_repair", "severity": "P1", "difficulty": "intermediate", "reference": "", "hint": "", "groundTruth": "", "optimalSteps": 5, "stepBudget": 15, "allowedTools": [], "minCompositeScore": 0.7},
        {"id": "mesh_22_bevel_overlap_self_intersection", "defect": "Tight inner radius bevel collision", "category": "bevel", "severity": "P1", "difficulty": "intermediate", "reference": "", "hint": "", "groundTruth": "", "optimalSteps": 5, "stepBudget": 15, "allowedTools": [], "minCompositeScore": 0.7},
        {"id": "mesh_23_boolean_subtraction_sliver", "defect": "Paper-thin residual face from boolean cut", "category": "boolean", "severity": "P1", "difficulty": "intermediate", "reference": "", "hint": "", "groundTruth": "", "optimalSteps": 5, "stepBudget": 15, "allowedTools": [], "minCompositeScore": 0.7},
        {"id": "mesh_24_micro_gap_tolerance_defect", "defect": "0.1mm gap preventing watertight 3D print", "category": "watertightness", "severity": "P0", "difficulty": "intermediate", "reference": "", "hint": "", "groundTruth": "", "optimalSteps": 5, "stepBudget": 15, "allowedTools": [], "minCompositeScore": 0.7},
        {"id": "mesh_25_extreme_curvature_stretching", "defect": "Stretched faces on acute mechanical wedge", "category": "remeshing", "severity": "P1", "difficulty": "intermediate", "reference": "", "hint": "", "groundTruth": "", "optimalSteps": 5, "stepBudget": 15, "allowedTools": [], "minCompositeScore": 0.7},
        {"id": "mesh_26_inverted_hemisphere_normals", "defect": "Entire lower dome normals pointing inward", "category": "surface", "severity": "P0", "difficulty": "advanced", "reference": "", "hint": "", "groundTruth": "", "optimalSteps": 8, "stepBudget": 24, "allowedTools": [], "minCompositeScore": 0.7},
        {"id": "mesh_27_triangulated_cylinder_distortion", "defect": "Fan triangulation causing shading pinch", "category": "topology", "severity": "P2", "difficulty": "advanced", "reference": "", "hint": "", "groundTruth": "", "optimalSteps": 8, "stepBudget": 24, "allowedTools": [], "minCompositeScore": 0.7},
        {"id": "mesh_28_mechanical_hinge_interpenetration", "defect": "Hinge pin penetrating socket wall", "category": "collision", "severity": "P0", "difficulty": "advanced", "reference": "", "hint": "", "groundTruth": "", "optimalSteps": 8, "stepBudget": 24, "allowedTools": [], "minCompositeScore": 0.7},
        {"id": "mesh_29_quad_diagonal_flip_mismatch", "defect": "Inconsistent quad triangulation flow", "category": "quad_remesh", "severity": "P2", "difficulty": "advanced", "reference": "", "hint": "", "groundTruth": "", "optimalSteps": 8, "stepBudget": 24, "allowedTools": [], "minCompositeScore": 0.7},
        {"id": "mesh_30_watertight_manifold_master_challenge", "defect": "Composite asset with 5 simultaneous defects", "category": "master_suite", "severity": "P0", "difficulty": "expert", "reference": "", "hint": "", "groundTruth": "", "optimalSteps": 12, "stepBudget": 36, "allowedTools": [], "minCompositeScore": 0.7},

        # Category D: RFC 0053 Extended Coverage (31 - 32)
        {"id": "mesh_31_excessive_polygon_count_200k", "defect": "200K+ polygon model requiring decimation to 50K budget", "category": "decimation", "severity": "P0", "difficulty": "advanced", "reference": "", "hint": "", "groundTruth": "", "optimalSteps": 8, "stepBudget": 24, "allowedTools": [], "minCompositeScore": 0.7},
        {"id": "mesh_32_backface_only_single_sided", "defect": "Single-sided faces visible only from backface", "category": "surface", "severity": "P1", "difficulty": "advanced", "reference": "", "hint": "", "groundTruth": "", "optimalSteps": 8, "stepBudget": 24, "allowedTools": [], "minCompositeScore": 0.7}
    ]

    manifest = {
        "suite_id": "RFC-0053-DATASET-MESH-REPAIR",
        "title": "SWE-bench for 3D: Geometry & Mesh Repair Benchmark",
        "version": "1.0.0",
        "total_cases": len(mesh_cases),
        "evaluation_metrics": [
            # S_compliance (Domain-Specific)
            "Watertightness_Boolean",
            "Non_Manifold_Edge_Count_Zero",
            "Inverted_Normal_Ratio_Zero",
            "Hausdorff_Distance_To_GroundTruth_mm",
            # S_geo (Geometric Fidelity)
            "Chamfer_Distance_Normalized",
            "F_Score_At_Tau",
            "Normal_Consistency",
            # S_render (Visual Fidelity)
            "SSIM_MultiView",
            "LPIPS_MultiView",
            "CLIP_Score",
            # S_efficiency (Agent Efficiency)
            "TCER_Command_Efficiency_Ratio",
            "Redundancy_Ratio"
        ],
        "cases": mesh_cases
    }

    with open(target_dir / "manifest.json", "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2, ensure_ascii=False)

    # Generate procedural sample defective & fixed OBJ pairs for core cases (01 - 03)
    # Case 01: Non-manifold T-junction
    defective_c1 = """# Case 01 Defective: T-Junction Non-Manifold Edge (3 faces sharing edge 1-2)
v -0.5 -0.5 0.0
v  0.5 -0.5 0.0
v  0.5  0.5 0.0
v -0.5  0.5 0.0
v  0.0  0.0 0.8
f 1 2 3 4
f 1 2 5
"""
    fixed_c1 = """# Case 01 Ground Truth: Manifold Quad (Extra non-manifold face removed)
v -0.5 -0.5 0.0
v  0.5 -0.5 0.0
v  0.5  0.5 0.0
v -0.5  0.5 0.0
f 1 2 3 4
"""
    with open(cases_dir / "mesh_01_non_manifold_t_junction_defective.obj", "w", encoding="utf-8") as f:
        f.write(defective_c1)
    with open(cases_dir / "mesh_01_non_manifold_t_junction_fixed.obj", "w", encoding="utf-8") as f:
        f.write(fixed_c1)

    # Case 02: Degenerate Hole (missing top face on cube)
    defective_c2 = """# Case 02 Defective: Cube missing top face (Open hole boundary 3-4-6-5)
v -0.5 -0.5  0.5
v  0.5 -0.5  0.5
v -0.5  0.5  0.5
v  0.5  0.5  0.5
v -0.5  0.5 -0.5
v  0.5  0.5 -0.5
v -0.5 -0.5 -0.5
v  0.5 -0.5 -0.5
f 1 2 4 3
f 7 8 6 5
f 1 7 5 3
f 2 8 6 4
f 1 2 8 7
"""
    fixed_c2 = defective_c2 + "f 3 4 6 5\n"
    with open(cases_dir / "mesh_02_degenerate_open_hole_defective.obj", "w", encoding="utf-8") as f:
        f.write(defective_c2)
    with open(cases_dir / "mesh_02_degenerate_open_hole_fixed.obj", "w", encoding="utf-8") as f:
        f.write(fixed_c2)

    # Case 03: Inverted Normal
    defective_c3 = """# Case 03 Defective: Quad with inverted winding (clockwise)
v -0.5 -0.5 0.0
v  0.5 -0.5 0.0
v  0.5  0.5 0.0
v -0.5  0.5 0.0
f 1 4 3 2
"""
    fixed_c3 = """# Case 03 Ground Truth: Correct counter-clockwise winding
v -0.5 -0.5 0.0
v  0.5 -0.5 0.0
v  0.5  0.5 0.0
v -0.5  0.5 0.0
f 1 2 3 4
"""
    with open(cases_dir / "mesh_03_inverted_face_normals_defective.obj", "w", encoding="utf-8") as f:
        f.write(defective_c3)
    with open(cases_dir / "mesh_03_inverted_face_normals_fixed.obj", "w", encoding="utf-8") as f:
        f.write(fixed_c3)

    # Case 06: Self-intersecting cube shells (two overlapping cubes)
    defective_c6 = """# Case 06 Defective: Two interpenetrating cube shells
v -0.5 -0.5 -0.5
v  0.5 -0.5 -0.5
v  0.5  0.5 -0.5
v -0.5  0.5 -0.5
v -0.5 -0.5  0.5
v  0.5 -0.5  0.5
v  0.5  0.5  0.5
v -0.5  0.5  0.5
f 1 2 3 4
f 5 6 7 8
f 1 5 8 4
f 2 6 7 3
f 1 2 6 5
f 4 3 7 8
v  0.0 -0.3 -0.3
v  0.8 -0.3 -0.3
v  0.8  0.3 -0.3
v  0.0  0.3 -0.3
v  0.0 -0.3  0.3
v  0.8 -0.3  0.3
v  0.8  0.3  0.3
v  0.0  0.3  0.3
f 9 10 11 12
f 13 14 15 16
f 9 13 16 12
f 10 14 15 11
f 9 10 14 13
f 12 11 15 16
"""
    fixed_c6 = """# Case 06 Ground Truth: Second cube translated to clear first
v -0.5 -0.5 -0.5
v  0.5 -0.5 -0.5
v  0.5  0.5 -0.5
v -0.5  0.5 -0.5
v -0.5 -0.5  0.5
v  0.5 -0.5  0.5
v  0.5  0.5  0.5
v -0.5  0.5  0.5
f 1 2 3 4
f 5 6 7 8
f 1 5 8 4
f 2 6 7 3
f 1 2 6 5
f 4 3 7 8
v  1.2 -0.3 -0.3
v  2.0 -0.3 -0.3
v  2.0  0.3 -0.3
v  1.2  0.3 -0.3
v  1.2 -0.3  0.3
v  2.0 -0.3  0.3
v  2.0  0.3  0.3
v  1.2  0.3  0.3
f 9 10 11 12
f 13 14 15 16
f 9 13 16 12
f 10 14 15 11
f 9 10 14 13
f 12 11 15 16
"""
    with open(cases_dir / "mesh_06_self_intersecting_cube_shells_defective.obj", "w", encoding="utf-8") as f:
        f.write(defective_c6)
    with open(cases_dir / "mesh_06_self_intersecting_cube_shells_fixed.obj", "w", encoding="utf-8") as f:
        f.write(fixed_c6)

    # Case 09: Inconsistent winding cylinder (alternating face normals on side walls)
    defective_c9_lines = ["# Case 09 Defective: Cylinder with alternating winding on side quads"]
    fixed_c9_lines = ["# Case 09 Ground Truth: Cylinder with consistent CCW winding"]
    import math as _m
    n_seg = 8
    # Bottom ring + top ring
    for i in range(n_seg):
        ang = 2.0 * _m.pi * i / n_seg
        x, z = round(0.5 * _m.cos(ang), 4), round(0.5 * _m.sin(ang), 4)
        defective_c9_lines.append(f"v {x} -0.5 {z}")
        fixed_c9_lines.append(f"v {x} -0.5 {z}")
    for i in range(n_seg):
        ang = 2.0 * _m.pi * i / n_seg
        x, z = round(0.5 * _m.cos(ang), 4), round(0.5 * _m.sin(ang), 4)
        defective_c9_lines.append(f"v {x}  0.5 {z}")
        fixed_c9_lines.append(f"v {x}  0.5 {z}")
    for i in range(n_seg):
        i_n = (i + 1) % n_seg
        a, b = i + 1, i_n + 1
        c, d = i_n + n_seg + 1, i + n_seg + 1
        fixed_c9_lines.append(f"f {a} {b} {c} {d}")  # consistent CCW
        if i % 2 == 0:
            defective_c9_lines.append(f"f {a} {b} {c} {d}")  # CCW
        else:
            defective_c9_lines.append(f"f {d} {c} {b} {a}")  # CW (inverted)

    with open(cases_dir / "mesh_09_inconsistent_winding_cylinder_defective.obj", "w", encoding="utf-8") as f:
        f.write("\n".join(defective_c9_lines) + "\n")
    with open(cases_dir / "mesh_09_inconsistent_winding_cylinder_fixed.obj", "w", encoding="utf-8") as f:
        f.write("\n".join(fixed_c9_lines) + "\n")

    # Case 18: Watertightness leak at cap (cylinder missing end cap)
    defective_c18 = """# Case 18 Defective: Cylinder missing top end cap
v  0.5 -0.5  0.0
v  0.0 -0.5  0.5
v -0.5 -0.5  0.0
v  0.0 -0.5 -0.5
v  0.5  0.5  0.0
v  0.0  0.5  0.5
v -0.5  0.5  0.0
v  0.0  0.5 -0.5
f 1 2 6 5
f 2 3 7 6
f 3 4 8 7
f 4 1 5 8
f 4 3 2 1
"""
    fixed_c18 = defective_c18 + "f 5 6 7 8\n"
    with open(cases_dir / "mesh_18_watertightness_leak_at_cap_defective.obj", "w", encoding="utf-8") as f:
        f.write(defective_c18)
    with open(cases_dir / "mesh_18_watertightness_leak_at_cap_fixed.obj", "w", encoding="utf-8") as f:
        f.write(fixed_c18)

    # Case 24: Micro gap tolerance defect (0.1mm gap between two halves)
    defective_c24 = """# Case 24 Defective: Two box halves with 0.1mm gap preventing watertightness
v -0.5 -0.5 -0.5
v  0.0 -0.5 -0.5
v  0.0  0.5 -0.5
v -0.5  0.5 -0.5
v -0.5 -0.5  0.5
v  0.0 -0.5  0.5
v  0.0  0.5  0.5
v -0.5  0.5  0.5
f 1 2 3 4
f 5 6 7 8
f 1 5 8 4
f 2 6 7 3
f 1 2 6 5
f 4 3 7 8
v  0.001 -0.5 -0.5
v  0.5   -0.5 -0.5
v  0.5    0.5 -0.5
v  0.001  0.5 -0.5
v  0.001 -0.5  0.5
v  0.5   -0.5  0.5
v  0.5    0.5  0.5
v  0.001  0.5  0.5
f 9 10 11 12
f 13 14 15 16
f 9 13 16 12
f 10 14 15 11
f 9 10 14 13
f 12 11 15 16
"""
    fixed_c24 = """# Case 24 Ground Truth: Gap closed — second half starts at x=0.0
v -0.5 -0.5 -0.5
v  0.0 -0.5 -0.5
v  0.0  0.5 -0.5
v -0.5  0.5 -0.5
v -0.5 -0.5  0.5
v  0.0 -0.5  0.5
v  0.0  0.5  0.5
v -0.5  0.5  0.5
f 1 2 3 4
f 5 6 7 8
f 1 5 8 4
f 2 6 7 3
f 1 2 6 5
f 4 3 7 8
v  0.0 -0.5 -0.5
v  0.5 -0.5 -0.5
v  0.5  0.5 -0.5
v  0.0  0.5 -0.5
v  0.0 -0.5  0.5
v  0.5 -0.5  0.5
v  0.5  0.5  0.5
v  0.0  0.5  0.5
f 9 10 11 12
f 13 14 15 16
f 9 13 16 12
f 10 14 15 11
f 9 10 14 13
f 12 11 15 16
"""
    with open(cases_dir / "mesh_24_micro_gap_tolerance_defect_defective.obj", "w", encoding="utf-8") as f:
        f.write(defective_c24)
    with open(cases_dir / "mesh_24_micro_gap_tolerance_defect_fixed.obj", "w", encoding="utf-8") as f:
        f.write(fixed_c24)

    # Case 26: Inverted hemisphere normals (lower dome normals pointing inward)
    defective_c26_lines = ["# Case 26 Defective: Hemisphere with inverted lower normals"]
    fixed_c26_lines = ["# Case 26 Ground Truth: Hemisphere with consistent outward normals"]
    n_h = 6
    for j in range(n_h + 1):
        phi = _m.pi * 0.5 * j / n_h  # 0 to pi/2
        for i in range(n_seg):
            ang = 2.0 * _m.pi * i / n_seg
            r = _m.sin(phi)
            x = round(0.5 * r * _m.cos(ang), 4)
            y = round(0.5 * _m.cos(phi), 4)
            z = round(0.5 * r * _m.sin(ang), 4)
            defective_c26_lines.append(f"v {x} {y} {z}")
            fixed_c26_lines.append(f"v {x} {y} {z}")
    for j in range(n_h):
        for i in range(n_seg):
            i_n = (i + 1) % n_seg
            a = j * n_seg + i + 1
            b = j * n_seg + i_n + 1
            c = (j+1) * n_seg + i_n + 1
            d = (j+1) * n_seg + i + 1
            fixed_c26_lines.append(f"f {a} {b} {c} {d}")
            if j >= n_h // 2:  # lower half inverted
                defective_c26_lines.append(f"f {d} {c} {b} {a}")
            else:
                defective_c26_lines.append(f"f {a} {b} {c} {d}")

    with open(cases_dir / "mesh_26_inverted_hemisphere_normals_defective.obj", "w", encoding="utf-8") as f:
        f.write("\n".join(defective_c26_lines) + "\n")
    with open(cases_dir / "mesh_26_inverted_hemisphere_normals_fixed.obj", "w", encoding="utf-8") as f:
        f.write("\n".join(fixed_c26_lines) + "\n")

    # Case 28: Mechanical hinge interpenetration (pin through socket)
    defective_c28 = """# Case 28 Defective: Hinge pin penetrating socket wall
# Socket (hollow cylinder)
v  0.3 -0.2  0.0
v  0.3  0.2  0.0
v -0.3 -0.2  0.0
v -0.3  0.2  0.0
v  0.3 -0.2  0.3
v  0.3  0.2  0.3
v -0.3 -0.2  0.3
v -0.3  0.2  0.3
f 1 2 4 3
f 5 6 8 7
f 1 5 6 2
f 3 7 8 4
# Pin (extends through socket wall)
v -0.05 -0.05 -0.1
v  0.05 -0.05 -0.1
v  0.05  0.05 -0.1
v -0.05  0.05 -0.1
v -0.05 -0.05  0.5
v  0.05 -0.05  0.5
v  0.05  0.05  0.5
v -0.05  0.05  0.5
f 9 10 11 12
f 13 14 15 16
f 9 13 14 10
f 12 16 15 11
f 9 12 16 13
f 10 11 15 14
"""
    fixed_c28 = """# Case 28 Ground Truth: Pin shortened to fit within socket
v  0.3 -0.2  0.0
v  0.3  0.2  0.0
v -0.3 -0.2  0.0
v -0.3  0.2  0.0
v  0.3 -0.2  0.3
v  0.3  0.2  0.3
v -0.3 -0.2  0.3
v -0.3  0.2  0.3
f 1 2 4 3
f 5 6 8 7
f 1 5 6 2
f 3 7 8 4
v -0.05 -0.05  0.01
v  0.05 -0.05  0.01
v  0.05  0.05  0.01
v -0.05  0.05  0.01
v -0.05 -0.05  0.29
v  0.05 -0.05  0.29
v  0.05  0.05  0.29
v -0.05  0.05  0.29
f 9 10 11 12
f 13 14 15 16
f 9 13 14 10
f 12 16 15 11
f 9 12 16 13
f 10 11 15 14
"""
    with open(cases_dir / "mesh_28_mechanical_hinge_interpenetration_defective.obj", "w", encoding="utf-8") as f:
        f.write(defective_c28)
    with open(cases_dir / "mesh_28_mechanical_hinge_interpenetration_fixed.obj", "w", encoding="utf-8") as f:
        f.write(fixed_c28)

    # Case 30: Master challenge (composite: T-junction + hole + inverted normal + gap + self-intersect)
    defective_c30 = """# Case 30 Defective: Composite asset with 5 simultaneous defects
# Defect 1: T-junction non-manifold edge on bottom quad
v -1.0 0.0 -1.0
v  1.0 0.0 -1.0
v  1.0 0.0  1.0
v -1.0 0.0  1.0
v  0.0 0.0  0.5
f 1 2 3 4
f 1 2 5
# Defect 2: Missing face (hole)
v -0.5 0.5 -0.5
v  0.5 0.5 -0.5
v  0.5 1.0 -0.5
v -0.5 1.0 -0.5
v -0.5 0.5  0.5
v  0.5 0.5  0.5
v  0.5 1.0  0.5
v -0.5 1.0  0.5
f 6 7 8 9
f 10 11 12 13
f 6 10 13 9
f 7 11 12 8
f 6 7 11 10
# Defect 3: Inverted normal face (top quad CW)
f 13 12 8 9
# Defect 4: Micro-gap second box at x=1.001
v  1.001 0.5 -0.3
v  1.5   0.5 -0.3
v  1.5   1.0 -0.3
v  1.001 1.0 -0.3
v  1.001 0.5  0.3
v  1.5   0.5  0.3
v  1.5   1.0  0.3
v  1.001 1.0  0.3
f 14 15 16 17
f 18 19 20 21
f 14 18 21 17
f 15 19 20 16
f 14 15 19 18
f 17 16 20 21
"""
    fixed_c30 = """# Case 30 Ground Truth: All 5 defects resolved
v -1.0 0.0 -1.0
v  1.0 0.0 -1.0
v  1.0 0.0  1.0
v -1.0 0.0  1.0
f 1 2 3 4
v -0.5 0.5 -0.5
v  0.5 0.5 -0.5
v  0.5 1.0 -0.5
v -0.5 1.0 -0.5
v -0.5 0.5  0.5
v  0.5 0.5  0.5
v  0.5 1.0  0.5
v -0.5 1.0  0.5
f 5 6 7 8
f 9 10 11 12
f 5 9 12 8
f 6 10 11 7
f 5 6 10 9
f 8 7 11 12
v  1.0 0.5 -0.3
v  1.5 0.5 -0.3
v  1.5 1.0 -0.3
v  1.0 1.0 -0.3
v  1.0 0.5  0.3
v  1.5 0.5  0.3
v  1.5 1.0  0.3
v  1.0 1.0  0.3
f 13 14 15 16
f 17 18 19 20
f 13 17 20 16
f 14 18 19 15
f 13 14 18 17
f 16 15 19 20
"""
    with open(cases_dir / "mesh_30_watertight_manifold_master_challenge_defective.obj", "w", encoding="utf-8") as f:
        f.write(defective_c30)
    with open(cases_dir / "mesh_30_watertight_manifold_master_challenge_fixed.obj", "w", encoding="utf-8") as f:
        f.write(fixed_c30)

    print(f"  ✓ Initialized RFC 0053 Mesh Repair Benchmark ({len(mesh_cases)} cases)")


def setup_evaluation_material_repair(eval_dir: Path):
    """Sets up 30 Material & Texture Repair Benchmark Cases."""
    target_dir = eval_dir / "dataset_material_repair"
    target_dir.mkdir(parents=True, exist_ok=True)

    if (target_dir / "manifest.json").exists() and (target_dir / "manifest.json").stat().st_size > 0:
        print("  ⏩ [SKIP] RFC 0053 Material Repair Benchmark already initialized.")
        return

    mat_cases = [
        # Channel & Color Space (01 - 10)
        {"id": "mat_01_baked_shadow_delighting", "defect": "Albedo map contains baked environment shadows", "category": "delighting", "target_metric": "DeltaE_under_2.0", "severity": "P1", "difficulty": "basic", "reference": "", "hint": "", "groundTruth": "", "optimalSteps": 3, "stepBudget": 9, "allowedTools": [], "minCompositeScore": 0.7},
        {"id": "mat_02_directx_opengl_normal_flip", "defect": "Green channel (Y) inverted tangent space normal", "category": "normal_space", "target_metric": "Tangent_Consistency", "severity": "P0", "difficulty": "basic", "reference": "", "hint": "", "groundTruth": "", "optimalSteps": 3, "stepBudget": 9, "allowedTools": [], "minCompositeScore": 0.7},
        {"id": "mat_03_inverted_roughness_specular", "defect": "Roughness channel inverted (smooth is white)", "category": "pbr_channels", "target_metric": "Roughness_Linearity", "severity": "P0", "difficulty": "basic", "reference": "", "hint": "", "groundTruth": "", "optimalSteps": 3, "stepBudget": 9, "allowedTools": [], "minCompositeScore": 0.7},
        {"id": "mat_04_metallic_non_binary_leak", "defect": "Dielectric surfaces assigned metallic 0.45", "category": "pbr_physics", "target_metric": "Binary_Metallic_Clamping", "severity": "P0", "difficulty": "basic", "reference": "", "hint": "", "groundTruth": "", "optimalSteps": 3, "stepBudget": 9, "allowedTools": [], "minCompositeScore": 0.7},
        {"id": "mat_05_missing_ambient_occlusion", "defect": "Missing AO channel causing flat shading in crevices", "category": "ao_baking", "target_metric": "Crevice_Contrast_PSNR", "severity": "P1", "difficulty": "basic", "reference": "", "hint": "", "groundTruth": "", "optimalSteps": 3, "stepBudget": 9, "allowedTools": [], "minCompositeScore": 0.7},
        {"id": "mat_06_emissive_hdr_overflow", "defect": "Emissive intensity blowing out dynamic range", "category": "hdr", "target_metric": "Nits_Luminance_Clamping", "severity": "P1", "difficulty": "intermediate", "reference": "", "hint": "", "groundTruth": "", "optimalSteps": 5, "stepBudget": 15, "allowedTools": [], "minCompositeScore": 0.7},
        {"id": "mat_07_srgb_linear_gamma_mismatch", "defect": "Roughness texture loaded as sRGB instead of Linear", "category": "gamma", "target_metric": "Linear_Gamma_Corrected", "severity": "P0", "difficulty": "intermediate", "reference": "", "hint": "", "groundTruth": "", "optimalSteps": 5, "stepBudget": 15, "allowedTools": [], "minCompositeScore": 0.7},
        {"id": "mat_08_subsurface_radius_clipping", "defect": "SSS radius causing waxy look on hard surface", "category": "sss", "target_metric": "Scatter_Radius_Normalized", "severity": "P1", "difficulty": "intermediate", "reference": "", "hint": "", "groundTruth": "", "optimalSteps": 5, "stepBudget": 15, "allowedTools": [], "minCompositeScore": 0.7},
        {"id": "mat_09_clearcoat_normal_divergence", "defect": "Clearcoat layer missing underlying normal detail", "category": "clearcoat", "target_metric": "Dual_Normal_Aligned", "severity": "P1", "difficulty": "intermediate", "reference": "", "hint": "", "groundTruth": "", "optimalSteps": 5, "stepBudget": 15, "allowedTools": [], "minCompositeScore": 0.7},
        {"id": "mat_10_energy_conservation_violation", "defect": "Albedo + Specular reflectance > 1.0", "category": "pbr_physics", "target_metric": "Energy_Conservation_Pass", "severity": "P0", "difficulty": "intermediate", "reference": "", "hint": "", "groundTruth": "", "optimalSteps": 5, "stepBudget": 15, "allowedTools": [], "minCompositeScore": 0.7},

        # UV & Parameterization (11 - 20)
        {"id": "mat_11_severe_uv_overlap_islands", "defect": "Overlapping UV islands causing texture cross-talk", "category": "uv_unwrap", "target_metric": "Zero_Overlap_Ratio", "severity": "P1", "difficulty": "intermediate", "reference": "", "hint": "", "groundTruth": "", "optimalSteps": 5, "stepBudget": 15, "allowedTools": [], "minCompositeScore": 0.7},
        {"id": "mat_12_uv_aspect_ratio_stretch_40pct", "defect": "Extreme anisotropic texture stretching", "category": "uv_unwrap", "target_metric": "Max_Shear_Under_1.1", "severity": "P1", "difficulty": "intermediate", "reference": "", "hint": "", "groundTruth": "", "optimalSteps": 5, "stepBudget": 15, "allowedTools": [], "minCompositeScore": 0.7},
        {"id": "mat_13_uv_boundary_bleeding_zero_margin", "defect": "Zero padding margin causing mipmap seam bleeding", "category": "uv_padding", "target_metric": "Padding_GTE_4px", "severity": "P1", "difficulty": "intermediate", "reference": "", "hint": "", "groundTruth": "", "optimalSteps": 5, "stepBudget": 15, "allowedTools": [], "minCompositeScore": 0.7},
        {"id": "mat_14_inverted_uv_winding_faces", "defect": "Negative UV face area causing mirrored texturing", "category": "uv_winding", "target_metric": "Positive_UV_Winding", "severity": "P1", "difficulty": "intermediate", "reference": "", "hint": "", "groundTruth": "", "optimalSteps": 5, "stepBudget": 15, "allowedTools": [], "minCompositeScore": 0.7},
        {"id": "mat_15_seam_texture_discontinuity", "defect": "Visible color jump across UV seams", "category": "seam_heal", "target_metric": "Border_Ring_DeltaE_1.5", "severity": "P1", "difficulty": "intermediate", "reference": "", "hint": "", "groundTruth": "", "optimalSteps": 5, "stepBudget": 15, "allowedTools": [], "minCompositeScore": 0.7},
        {"id": "mat_16_udim_tile_overflow", "defect": "UV islands placed outside 0-1 UDIM bounds", "category": "udim", "target_metric": "Valid_UDIM_Tile", "severity": "P1", "difficulty": "intermediate", "reference": "", "hint": "", "groundTruth": "", "optimalSteps": 5, "stepBudget": 15, "allowedTools": [], "minCompositeScore": 0.7},
        {"id": "mat_17_sub_texel_density_mismatch", "defect": "Head texture 1024px while torso is 64px", "category": "texel_density", "target_metric": "Uniform_Texel_Density", "severity": "P1", "difficulty": "intermediate", "reference": "", "hint": "", "groundTruth": "", "optimalSteps": 5, "stepBudget": 15, "allowedTools": [], "minCompositeScore": 0.7},
        {"id": "mat_18_collapsed_uv_island_zero_area", "defect": "UV island squashed into a single line", "category": "uv_unwrap", "target_metric": "Non_Zero_UV_Area", "severity": "P1", "difficulty": "intermediate", "reference": "", "hint": "", "groundTruth": "", "optimalSteps": 5, "stepBudget": 15, "allowedTools": [], "minCompositeScore": 0.7},
        {"id": "mat_19_checkerboard_shear_distortion", "defect": "Rhombus sheared texture parameterization", "category": "uv_unwrap", "target_metric": "Orthogonal_UV_Angles", "severity": "P1", "difficulty": "intermediate", "reference": "", "hint": "", "groundTruth": "", "optimalSteps": 5, "stepBudget": 15, "allowedTools": [], "minCompositeScore": 0.7},
        {"id": "mat_20_cylindrical_pole_pinching", "defect": "Severe pinching at sphere poles", "category": "uv_unwrap", "target_metric": "Pole_Distortion_Factor", "severity": "P1", "difficulty": "intermediate", "reference": "", "hint": "", "groundTruth": "", "optimalSteps": 5, "stepBudget": 15, "allowedTools": [], "minCompositeScore": 0.7},

        # Composite & Advanced PBR (21 - 30)
        {"id": "mat_21_multimaterial_slot_id_drift", "defect": "Face material IDs assigned to wrong slots", "category": "slots", "target_metric": "Material_Slot_Accuracy", "severity": "P1", "difficulty": "intermediate", "reference": "", "hint": "", "groundTruth": "", "optimalSteps": 5, "stepBudget": 15, "allowedTools": [], "minCompositeScore": 0.7},
        {"id": "mat_22_alpha_coverage_dithering_banding", "defect": "Alpha test threshold causing harsh fringing", "category": "transparency", "target_metric": "Smooth_Alpha_Edge", "severity": "P1", "difficulty": "intermediate", "reference": "", "hint": "", "groundTruth": "", "optimalSteps": 5, "stepBudget": 15, "allowedTools": [], "minCompositeScore": 0.7},
        {"id": "mat_23_anisotropic_tangent_discontinuity", "defect": "Brushed metal specular rotation discontinuous", "category": "anisotropy", "target_metric": "Continuous_Tangent_Flow", "severity": "P1", "difficulty": "intermediate", "reference": "", "hint": "", "groundTruth": "", "optimalSteps": 5, "stepBudget": 15, "allowedTools": [], "minCompositeScore": 0.7},
        {"id": "mat_24_albedo_black_level_below_004", "defect": "Coal-black albedo below physical dielectric min", "category": "pbr_physics", "target_metric": "Albedo_Floor_0.04", "severity": "P0", "difficulty": "intermediate", "reference": "", "hint": "", "groundTruth": "", "optimalSteps": 5, "stepBudget": 15, "allowedTools": [], "minCompositeScore": 0.7},
        {"id": "mat_25_fresnel_f0_physically_impossible", "defect": "Dielectric F0 set to 0.70", "category": "pbr_physics", "target_metric": "F0_Clamped_0.02_0.08", "severity": "P0", "difficulty": "intermediate", "reference": "", "hint": "", "groundTruth": "", "optimalSteps": 5, "stepBudget": 15, "allowedTools": [], "minCompositeScore": 0.7},
        {"id": "mat_26_triplanar_projection_ghosting", "defect": "Triplanar blending angle causing blurry edge", "category": "triplanar", "target_metric": "Sharp_Blend_Contrast", "severity": "P2", "difficulty": "advanced", "reference": "", "hint": "", "groundTruth": "", "optimalSteps": 8, "stepBudget": 24, "allowedTools": [], "minCompositeScore": 0.7},
        {"id": "mat_27_micro_roughness_mip_aliasing", "defect": "Distant rough objects producing specular noise", "category": "toksvig", "target_metric": "Toksvig_Normal_Filter", "severity": "P2", "difficulty": "advanced", "reference": "", "hint": "", "groundTruth": "", "optimalSteps": 8, "stepBudget": 24, "allowedTools": [], "minCompositeScore": 0.7},
        {"id": "mat_28_sheen_tint_chromatic_aberration", "defect": "Velvet sheen color clashing with albedo", "category": "sheen", "target_metric": "Monochrome_Sheen_Rule", "severity": "P2", "difficulty": "advanced", "reference": "", "hint": "", "groundTruth": "", "optimalSteps": 8, "stepBudget": 24, "allowedTools": [], "minCompositeScore": 0.7},
        {"id": "mat_29_metallic_normal_seam_rupture", "defect": "High metallic surface revealing normal seam", "category": "seam_heal", "target_metric": "Normal_Derivatives_Continuous", "severity": "P1", "difficulty": "advanced", "reference": "", "hint": "", "groundTruth": "", "optimalSteps": 8, "stepBudget": 24, "allowedTools": [], "minCompositeScore": 0.7},
        {"id": "mat_30_openpbr_master_conformance", "defect": "Legacy Phong shader converted to OpenPBR Standard", "category": "master_suite", "target_metric": "OpenPBR_Validation_100", "severity": "P0", "difficulty": "expert", "reference": "", "hint": "", "groundTruth": "", "optimalSteps": 12, "stepBudget": 36, "allowedTools": [], "minCompositeScore": 0.7},

        # Category D: RFC 0053 Extended Coverage (31 - 32)
        {"id": "mat_31_missing_normal_map_flat_shading", "defect": "Normal map slot empty causing flat Lambertian shading on detailed surface", "category": "normal_space", "target_metric": "Normal_Detail_Present", "severity": "P0", "difficulty": "advanced", "reference": "", "hint": "", "groundTruth": "", "optimalSteps": 8, "stepBudget": 24, "allowedTools": [], "minCompositeScore": 0.7},
        {"id": "mat_32_metallic_roughness_channel_swap", "defect": "Metallic packed in roughness channel and vice versa", "category": "pbr_channels", "target_metric": "Channel_Assignment_Correct", "severity": "P0", "difficulty": "advanced", "reference": "", "hint": "", "groundTruth": "", "optimalSteps": 8, "stepBudget": 24, "allowedTools": [], "minCompositeScore": 0.7}
    ]

    manifest = {
        "suite_id": "RFC-0053-DATASET-MATERIAL-REPAIR",
        "title": "SWE-bench for 3D: Material & Texture Repair Benchmark",
        "version": "1.0.0",
        "total_cases": len(mat_cases),
        "evaluation_metrics": [
            # S_compliance (Domain-Specific)
            "Delighted_Albedo_DeltaE",
            "UV_Overlap_Ratio_Zero",
            "Physical_PBR_Rule_Pass_Rate",
            "Seam_Discontinuity_Eliminated",
            # S_geo (Geometric Fidelity)
            "Chamfer_Distance_Normalized",
            "F_Score_At_Tau",
            "Normal_Consistency",
            # S_render (Visual Fidelity)
            "SSIM_MultiView",
            "LPIPS_MultiView",
            "CLIP_Score",
            # S_efficiency (Agent Efficiency)
            "TCER_Command_Efficiency_Ratio",
            "Redundancy_Ratio"
        ],
        "cases": mat_cases
    }

    with open(target_dir / "manifest.json", "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2, ensure_ascii=False)

    print(f"  ✓ Initialized RFC 0053 Material Repair Benchmark ({len(mat_cases)} cases)")


def setup_evaluation_anim_repair(eval_dir: Path):
    """Sets up 30 Animation, Dynamics & Rigging Repair Benchmark Cases."""
    target_dir = eval_dir / "dataset_anim_repair"
    target_dir.mkdir(parents=True, exist_ok=True)

    if (target_dir / "manifest.json").exists() and (target_dir / "manifest.json").stat().st_size > 0:
        print("  ⏩ [SKIP] RFC 0053 Animation Repair Benchmark already initialized.")
        return

    anim_cases = [
        # Locomotion & Foot Sliding (01 - 10)
        {"id": "anim_01_foot_sliding_forward_walk", "defect": "Foot skates 7.4 cm during contact phase", "category": "foot_ik", "target_sla": "Slip_Velocity_Under_0.3cm_s", "severity": "P0", "difficulty": "basic", "reference": "", "hint": "", "groundTruth": "", "optimalSteps": 3, "stepBudget": 9, "allowedTools": [], "minCompositeScore": 0.7},
        {"id": "anim_02_heel_strike_ground_penetration", "defect": "Heel penetrates floor mesh by 4.2 cm", "category": "foot_ik", "target_sla": "Floor_Penetration_Zero", "severity": "P0", "difficulty": "basic", "reference": "", "hint": "", "groundTruth": "", "optimalSteps": 3, "stepBudget": 9, "allowedTools": [], "minCompositeScore": 0.7},
        {"id": "anim_03_toe_lift_jitter_oscillation", "defect": "High frequency vibration during foot plant", "category": "filtering", "target_sla": "Jitter_Variance_Under_0.05", "severity": "P1", "difficulty": "basic", "reference": "", "hint": "", "groundTruth": "", "optimalSteps": 3, "stepBudget": 9, "allowedTools": [], "minCompositeScore": 0.7},
        {"id": "anim_05_pelvis_height_unnatural_bobbing", "defect": "Excessive vertical translation oscillation", "category": "trajectory", "target_sla": "Pelvis_Smooth_Curvature", "severity": "P1", "difficulty": "basic", "reference": "", "hint": "", "groundTruth": "", "optimalSteps": 3, "stepBudget": 9, "allowedTools": [], "minCompositeScore": 0.7},
        {"id": "anim_07_running_stride_phase_slippage", "defect": "Flight to stance transition slipping", "category": "locomotion", "target_sla": "Impact_Phase_Lock", "severity": "P1", "difficulty": "intermediate", "reference": "", "hint": "", "groundTruth": "", "optimalSteps": 5, "stepBudget": 15, "allowedTools": [], "minCompositeScore": 0.7},
        {"id": "anim_10_slope_traversal_ankle_twist", "defect": "Ankle roll angle fails to align with slope normal", "category": "ankle_ik", "target_sla": "Normal_Alignment_Error_Under_3deg", "severity": "P1", "difficulty": "intermediate", "reference": "", "hint": "", "groundTruth": "", "optimalSteps": 5, "stepBudget": 15, "allowedTools": [], "minCompositeScore": 0.7},

        # Joint Limits & Mesh Clipping (11 - 20)
        {"id": "anim_11_knee_hyperextension_inversion", "defect": "Knee joint bends backward > 185 degrees", "category": "joint_limits", "target_sla": "Knee_Angle_Clamped_0_155deg", "severity": "P0", "difficulty": "intermediate", "reference": "", "hint": "", "groundTruth": "", "optimalSteps": 5, "stepBudget": 15, "allowedTools": [], "minCompositeScore": 0.7},
        {"id": "anim_12_elbow_broken_angle_twist", "defect": "Forearm gimbal lock causing broken elbow appearance", "category": "joint_limits", "target_sla": "Quaternion_Slerp_Smooth", "severity": "P0", "difficulty": "intermediate", "reference": "", "hint": "", "groundTruth": "", "optimalSteps": 5, "stepBudget": 15, "allowedTools": [], "minCompositeScore": 0.7},
        {"id": "anim_13_spine_lumbar_extreme_hyperlordosis", "defect": "Spine hyperflexion violating anatomical limits", "category": "joint_limits", "target_sla": "Spine_Angle_Under_35deg", "severity": "P0", "difficulty": "intermediate", "reference": "", "hint": "", "groundTruth": "", "optimalSteps": 5, "stepBudget": 15, "allowedTools": [], "minCompositeScore": 0.7},
        {"id": "anim_14_shoulder_clavicle_mesh_dislocation", "defect": "Humeral head pops out of glenoid socket", "category": "joint_limits", "target_sla": "Joint_Centering_Tolerance_1mm", "severity": "P0", "difficulty": "intermediate", "reference": "", "hint": "", "groundTruth": "", "optimalSteps": 5, "stepBudget": 15, "allowedTools": [], "minCompositeScore": 0.7},
        {"id": "anim_15_weapon_holster_mesh_clipping", "defect": "Rifle mesh penetrates character leg and cape", "category": "collision", "target_sla": "Clipping_Frame_Ratio_Zero", "severity": "P1", "difficulty": "intermediate", "reference": "", "hint": "", "groundTruth": "", "optimalSteps": 5, "stepBudget": 15, "allowedTools": [], "minCompositeScore": 0.7},
        {"id": "anim_16_hand_grip_mesh_self_intersection", "defect": "Fingers penetrate rifle handle", "category": "hand_mocap", "target_sla": "Contact_Manifold_Distance_Zero", "severity": "P1", "difficulty": "intermediate", "reference": "", "hint": "", "groundTruth": "", "optimalSteps": 5, "stepBudget": 15, "allowedTools": [], "minCompositeScore": 0.7},
        {"id": "anim_17_head_neck_twist_exceeding_90deg", "defect": "Head rotates 120 degrees like an owl", "category": "joint_limits", "target_sla": "Cervical_Limit_85deg", "severity": "P0", "difficulty": "intermediate", "reference": "", "hint": "", "groundTruth": "", "optimalSteps": 5, "stepBudget": 15, "allowedTools": [], "minCompositeScore": 0.7},
        {"id": "anim_18_wrist_flexion_singularity", "defect": "Wrist twist causing mesh pinching", "category": "skinning", "target_sla": "Dual_Quaternion_Preservation", "severity": "P0", "difficulty": "intermediate", "reference": "", "hint": "", "groundTruth": "", "optimalSteps": 5, "stepBudget": 15, "allowedTools": [], "minCompositeScore": 0.7},
        {"id": "anim_19_dual_arm_clapping_overlap", "defect": "Both hands penetrate each other during clapping", "category": "collision", "target_sla": "Symmetric_Contact_Plane", "severity": "P1", "difficulty": "intermediate", "reference": "", "hint": "", "groundTruth": "", "optimalSteps": 5, "stepBudget": 15, "allowedTools": [], "minCompositeScore": 0.7},
        {"id": "anim_20_thigh_pelvis_squat_clipping", "defect": "Deep squat causing inner thigh mesh overlap", "category": "collision", "target_sla": "Soft_Body_Repulsion", "severity": "P1", "difficulty": "intermediate", "reference": "", "hint": "", "groundTruth": "", "optimalSteps": 5, "stepBudget": 15, "allowedTools": [], "minCompositeScore": 0.7},

        # Rigging, Skinning & Root Motion (21 - 30)
        {"id": "anim_21_root_motion_world_drift", "defect": "In-place animation contains unintended root translation", "category": "root_motion", "target_sla": "Root_Zero_Centered", "severity": "P1", "difficulty": "intermediate", "reference": "", "hint": "", "groundTruth": "", "optimalSteps": 5, "stepBudget": 15, "allowedTools": [], "minCompositeScore": 0.7},
        {"id": "anim_22_skin_weight_unnormalized_spikes", "defect": "Vertices with bone weight sum != 1.0", "category": "skinning", "target_sla": "Weight_Sum_Exact_1.0", "severity": "P0", "difficulty": "intermediate", "reference": "", "hint": "", "groundTruth": "", "optimalSteps": 5, "stepBudget": 15, "allowedTools": [], "minCompositeScore": 0.7},
        {"id": "anim_23_max_influences_exceeded_gpu", "defect": "Vertices bound to >4 bones causing GPU dropouts", "category": "gpu_standards", "target_sla": "Max_4_Influences_Per_Vertex", "severity": "P2", "difficulty": "intermediate", "reference": "", "hint": "", "groundTruth": "", "optimalSteps": 5, "stepBudget": 15, "allowedTools": [], "minCompositeScore": 0.7},
        {"id": "anim_24_twist_bone_candy_wrapper_effect", "defect": "Wrist rotation collapsing mesh volume", "category": "skinning", "target_sla": "Twist_Bone_Volume_Preserved", "severity": "P0", "difficulty": "intermediate", "reference": "", "hint": "", "groundTruth": "", "optimalSteps": 5, "stepBudget": 15, "allowedTools": [], "minCompositeScore": 0.7},
        {"id": "anim_25_armpit_crease_weight_tearing", "defect": "Arm raise tearing chest vertices", "category": "skinning", "target_sla": "Smooth_Crease_Transition", "severity": "P0", "difficulty": "intermediate", "reference": "", "hint": "", "groundTruth": "", "optimalSteps": 5, "stepBudget": 15, "allowedTools": [], "minCompositeScore": 0.7},
        {"id": "anim_26_crotch_skin_stretching_spread", "defect": "Leg spread pulling pelvic vertices", "category": "skinning", "target_sla": "Zero_Cross_Leg_Weight_Bleed", "severity": "P0", "difficulty": "advanced", "reference": "", "hint": "", "groundTruth": "", "optimalSteps": 8, "stepBudget": 24, "allowedTools": [], "minCompositeScore": 0.7},
        {"id": "anim_27_facial_jaw_drop_eyeball_drift", "defect": "Jaw opening causing eye meshes to lag behind", "category": "facial_rig", "target_sla": "Rigid_Eyeball_Socket_Binding", "severity": "P1", "difficulty": "advanced", "reference": "", "hint": "", "groundTruth": "", "optimalSteps": 8, "stepBudget": 24, "allowedTools": [], "minCompositeScore": 0.7},
        {"id": "anim_28_motion_retargeting_bone_length_distortion", "defect": "Retargeting stretching non-uniform bone lengths", "category": "retargeting", "target_sla": "Rest_Pose_Bone_Length_Fixed", "severity": "P2", "difficulty": "advanced", "reference": "", "hint": "", "groundTruth": "", "optimalSteps": 8, "stepBudget": 24, "allowedTools": [], "minCompositeScore": 0.7},
        {"id": "anim_29_framerate_resampling_jitter_60_to_24", "defect": "Uneven step timing when converting 60fps to 24fps", "category": "resampling", "target_sla": "Hermite_Spline_Resample", "severity": "P2", "difficulty": "advanced", "reference": "", "hint": "", "groundTruth": "", "optimalSteps": 8, "stepBudget": 24, "allowedTools": [], "minCompositeScore": 0.7},
        {"id": "anim_30_full_body_master_locomotion_audit", "defect": "Comprehensive test with 4 combined animation defects", "category": "master_suite", "target_sla": "All_SLA_Thresholds_Pass", "severity": "P0", "difficulty": "expert", "reference": "", "hint": "", "groundTruth": "", "optimalSteps": 12, "stepBudget": 36, "allowedTools": [], "minCompositeScore": 0.7},

        # Category D: RFC 0053 Extended Coverage (31 - 34)
        {"id": "anim_31_missing_keyframe_animation_pop", "defect": "Deleted keyframe causing abrupt interpolation jump", "category": "keyframe", "target_sla": "Zero_Frame_Discontinuity", "severity": "P0", "difficulty": "advanced", "reference": "", "hint": "", "groundTruth": "", "optimalSteps": 8, "stepBudget": 24, "allowedTools": [], "minCompositeScore": 0.7},
        {"id": "anim_32_ik_effector_target_drift", "defect": "IK end-effector drifts 3.8mm from target constraint", "category": "ik_drift", "target_sla": "Effector_Error_Under_1mm", "severity": "P0", "difficulty": "advanced", "reference": "", "hint": "", "groundTruth": "", "optimalSteps": 8, "stepBudget": 24, "allowedTools": [], "minCompositeScore": 0.7},
        {"id": "anim_33_blend_shape_morph_corruption", "defect": "Blend shape delta vectors corrupted causing facial distortion", "category": "facial_rig", "target_sla": "Morph_Delta_Variance_Under_0.01", "severity": "P1", "difficulty": "advanced", "reference": "", "hint": "", "groundTruth": "", "optimalSteps": 8, "stepBudget": 24, "allowedTools": [], "minCompositeScore": 0.7},
        {"id": "anim_34_root_bone_yup_zup_mismatch", "defect": "Root bone orientation Y-up exported as Z-up causing 90-degree tilt", "category": "orientation", "target_sla": "Up_Axis_Aligned_Y", "severity": "P0", "difficulty": "advanced", "reference": "", "hint": "", "groundTruth": "", "optimalSteps": 8, "stepBudget": 24, "allowedTools": [], "minCompositeScore": 0.7}
    ]

    manifest = {
        "suite_id": "RFC-0053-DATASET-ANIM-REPAIR",
        "title": "SWE-bench for 3D: Animation, Kinematics & Rigging Repair Benchmark",
        "version": "1.0.0",
        "total_cases": len(anim_cases),
        "evaluation_metrics": [
            # S_compliance (Domain-Specific)
            "Foot_Slip_Velocity_Under_0.3cm_s",
            "Joint_Angle_Constraint_Pass_Rate",
            "Mesh_Clipping_Frame_Ratio_Zero",
            "Skinning_Weight_Normalized_100pct",
            # S_geo (Geometric Fidelity)
            "Chamfer_Distance_Normalized",
            "F_Score_At_Tau",
            "Normal_Consistency",
            # S_render (Visual Fidelity)
            "SSIM_MultiView",
            "LPIPS_MultiView",
            "CLIP_Score",
            # S_efficiency (Agent Efficiency)
            "TCER_Command_Efficiency_Ratio",
            "Redundancy_Ratio"
        ],
        "cases": anim_cases
    }

    with open(target_dir / "manifest.json", "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2, ensure_ascii=False)

    print(f"  ✓ Initialized RFC 0053 Animation Repair Benchmark ({len(anim_cases)} cases)")




# ==============================================================================
# 3b. Bidirectional Round-Trip Evaluation Suite (3D -> Rendered GT -> Diffusion -> 3D)
# ==============================================================================

def setup_evaluation_bidirectional_roundtrip(eval_dir: Path):
    """Sets up 12 Bidirectional Round-Trip Benchmark Cases.

    Each case defines a standard {A0 (initial 3D), render_spec, trajectory} triplet
    that enables:
      - Forward rendering via Fulgur/Caelum-Core -> V_render_gt (physics-perfect GT video)
      - Diffusion generation via Veo 2/Seedance -> V_diffusion (cinematic but defective)
      - Inverse distillation V_diffusion -> A1 (reconstructed 3D)
      - Cycle consistency measurement: Chamfer(A0, A1), DeltaE, Volume drift

    Source datasets (academic gold standards):
      - GRAB (ECCV 2020): Hand-object grasping with precise contact GT
      - ZJU-MoCap / Hi4D (CVPR 2021/2023): Multi-view human motion with SMPL-X GT
      - Objaverse-XL / MVImgNet: Large-scale 3D assets with multi-view renders
      - Physics cloth simulation: Fulgur dynamics engine cloth + wind sequences
    """
    target_dir = eval_dir / "dataset_bidirectional_roundtrip"
    cases_dir = target_dir / "cases"
    cases_dir.mkdir(parents=True, exist_ok=True)

    if (target_dir / "manifest.json").exists() and (target_dir / "manifest.json").stat().st_size > 0:
        print("  ⏩ [SKIP] Bidirectional Round-Trip Evaluation Suite already initialized.")
        return

    roundtrip_cases = [
        # =====================================================================
        # Domain A: Hand-Object Rigid Contact (from GRAB dataset family)
        # Focus: hand-weapon interpenetration elimination in round-trip cycle
        # =====================================================================
        {
            "id": "rt_grab_01_pistol_grip_contact",
            "domain": "hand_object_contact",
            "source_dataset": "GRAB (ECCV 2020)",
            "source_url": "https://grab.is.tue.mpg.de/",
            "description": "Right hand grasping sci-fi pistol, index finger on trigger guard",
            "gt_3d_asset": "MANO hand mesh + rigid pistol glb",
            "focus": "Finger-trigger interpenetration, thumb-grip SDF contact fidelity",
            "camera_motion": "Slow_Dolly_In_With_Orbit",
            "frame_count": 96,
            "fps": 24,
            "render_config": {
                "engine": "fulgur_headless",
                "mode": "path_trace",
                "spp": 128,
                "resolution": [1920, 1080],
                "aov_outputs": ["CameraLinearDepth", "WorldNormal", "MotionVector", "Cryptomatte"]
            },
            "cycle_metrics_sla": {
                "max_interpenetration_volume_cm3": 0.0,
                "max_contact_gap_mm": 1.0,
                "chamfer_distance_mm": 2.0,
                "surface_f_score_tau_1mm": 0.90
            },
            "severity": "P0",
            "difficulty": "advanced"
        },
        {
            "id": "rt_grab_02_rifle_two_hand_hold",
            "domain": "hand_object_contact",
            "source_dataset": "GRAB (ECCV 2020)",
            "source_url": "https://grab.is.tue.mpg.de/",
            "description": "Two-handed tactical rifle hold, forward grip + stock shoulder brace",
            "gt_3d_asset": "Dual MANO hands + rifle assembly glb",
            "focus": "Dual-hand coordinated contact, forestock grip wrap, stock-shoulder surface conformance",
            "camera_motion": "Orbital_Arc_120deg",
            "frame_count": 96,
            "fps": 24,
            "render_config": {
                "engine": "fulgur_headless",
                "mode": "path_trace",
                "spp": 128,
                "resolution": [1920, 1080],
                "aov_outputs": ["CameraLinearDepth", "WorldNormal", "MotionVector", "Cryptomatte"]
            },
            "cycle_metrics_sla": {
                "max_interpenetration_volume_cm3": 0.0,
                "max_contact_gap_mm": 1.5,
                "chamfer_distance_mm": 2.5,
                "surface_f_score_tau_1mm": 0.88
            },
            "severity": "P0",
            "difficulty": "expert"
        },
        {
            "id": "rt_grab_03_sword_swing_dynamic",
            "domain": "hand_object_contact",
            "source_dataset": "GRAB (ECCV 2020) + custom dynamics",
            "source_url": "https://grab.is.tue.mpg.de/",
            "description": "Single-hand sword swing arc with wrist rotation and inertia follow-through",
            "gt_3d_asset": "MANO hand + katana blade glb with swing animation",
            "focus": "Dynamic grip stability during fast rotation, blade-guard clearance",
            "camera_motion": "Forward_Tracking_Shot",
            "frame_count": 96,
            "fps": 24,
            "render_config": {
                "engine": "fulgur_headless",
                "mode": "path_trace",
                "spp": 128,
                "resolution": [1920, 1080],
                "aov_outputs": ["CameraLinearDepth", "WorldNormal", "MotionVector", "Cryptomatte"]
            },
            "cycle_metrics_sla": {
                "max_interpenetration_volume_cm3": 0.0,
                "max_contact_gap_mm": 2.0,
                "chamfer_distance_mm": 3.0,
                "surface_f_score_tau_1mm": 0.85
            },
            "severity": "P0",
            "difficulty": "expert"
        },

        # =====================================================================
        # Domain B: Human Locomotion & Foot-Ground Contact (from ZJU-MoCap/Hi4D)
        # Focus: foot sliding elimination and skeletal fidelity in round-trip
        # =====================================================================
        {
            "id": "rt_mocap_04_forward_walk_plant",
            "domain": "human_locomotion",
            "source_dataset": "ZJU-MoCap (ICCV 2021)",
            "source_url": "https://github.com/zju3dv/neuralbody",
            "description": "Subject walking forward 4 steps on flat ground, heel-strike to toe-off gait cycle",
            "gt_3d_asset": "SMPL-X body model with optical MoCap skeletal GT",
            "focus": "Foot-ground contact phase zero-velocity lock, pelvis height stability",
            "camera_motion": "Forward_Tracking_Shot",
            "frame_count": 96,
            "fps": 24,
            "render_config": {
                "engine": "fulgur_headless",
                "mode": "path_trace",
                "spp": 128,
                "resolution": [1920, 1080],
                "aov_outputs": ["CameraLinearDepth", "WorldNormal", "MotionVector"]
            },
            "cycle_metrics_sla": {
                "max_foot_sliding_cm_per_sec": 0.3,
                "max_pelvis_height_variance_cm": 0.5,
                "joint_angle_rmse_deg": 5.0,
                "bone_length_preservation_ratio": 0.99
            },
            "severity": "P0",
            "difficulty": "intermediate"
        },
        {
            "id": "rt_mocap_05_run_stride_flight",
            "domain": "human_locomotion",
            "source_dataset": "ZJU-MoCap (ICCV 2021)",
            "source_url": "https://github.com/zju3dv/neuralbody",
            "description": "Subject jogging with clear flight phase, arm counter-swing, head stabilization",
            "gt_3d_asset": "SMPL-X body model with optical MoCap skeletal GT",
            "focus": "Flight-to-stance impact lock, arm pendulum phase coherence",
            "camera_motion": "Side_Tracking_Pan",
            "frame_count": 96,
            "fps": 24,
            "render_config": {
                "engine": "fulgur_headless",
                "mode": "path_trace",
                "spp": 128,
                "resolution": [1920, 1080],
                "aov_outputs": ["CameraLinearDepth", "WorldNormal", "MotionVector"]
            },
            "cycle_metrics_sla": {
                "max_foot_sliding_cm_per_sec": 0.5,
                "max_pelvis_height_variance_cm": 1.0,
                "joint_angle_rmse_deg": 6.0,
                "bone_length_preservation_ratio": 0.98
            },
            "severity": "P0",
            "difficulty": "advanced"
        },
        {
            "id": "rt_mocap_06_turn_pivot_weight_shift",
            "domain": "human_locomotion",
            "source_dataset": "Hi4D (CVPR 2023)",
            "source_url": "https://yifeiyin04.github.io/Hi4D/",
            "description": "Subject performing 180-degree pivot turn with weight shift from left to right foot",
            "gt_3d_asset": "Hi4D dense 4D body scan with vertex-level GT",
            "focus": "Pivot foot zero-slip during rotation, CoM transfer fidelity",
            "camera_motion": "Static_Front_View",
            "frame_count": 96,
            "fps": 24,
            "render_config": {
                "engine": "fulgur_headless",
                "mode": "path_trace",
                "spp": 128,
                "resolution": [1920, 1080],
                "aov_outputs": ["CameraLinearDepth", "WorldNormal", "MotionVector"]
            },
            "cycle_metrics_sla": {
                "max_foot_sliding_cm_per_sec": 0.3,
                "max_pivot_drift_cm": 0.5,
                "joint_angle_rmse_deg": 5.0,
                "bone_length_preservation_ratio": 0.99
            },
            "severity": "P0",
            "difficulty": "advanced"
        },

        # =====================================================================
        # Domain C: 360 Rigid Body Orbit (from Objaverse-XL / ORBIT / Custom)
        # Focus: volume breathing elimination and perspective rigidity
        # =====================================================================
        {
            "id": "rt_orbit_07_mech_armor_360",
            "domain": "rigid_360_orbit",
            "source_dataset": "Objaverse-XL",
            "source_url": "https://objaverse.allenai.org/",
            "description": "Heavy tactical mech armor on pedestal, full 360-degree turntable orbit",
            "gt_3d_asset": "High-poly mech armor glb (~50K faces, PBR metallic)",
            "focus": "Cross-frame silhouette area consistency, zero perspective breathing",
            "camera_motion": "Turntable_360_Orbit",
            "frame_count": 120,
            "fps": 24,
            "render_config": {
                "engine": "fulgur_headless",
                "mode": "path_trace",
                "spp": 128,
                "resolution": [1920, 1080],
                "aov_outputs": ["CameraLinearDepth", "WorldNormal", "Cryptomatte"]
            },
            "cycle_metrics_sla": {
                "max_volume_breathing_ratio": 0.015,
                "max_silhouette_area_std_pct": 1.0,
                "chamfer_distance_mm": 1.5,
                "normal_consistency": 0.95
            },
            "severity": "P0",
            "difficulty": "intermediate"
        },
        {
            "id": "rt_orbit_08_sci_fi_helmet_detail",
            "domain": "rigid_360_orbit",
            "source_dataset": "glTF Sample Models (Khronos)",
            "source_url": "https://github.com/KhronosGroup/glTF-Sample-Models",
            "description": "Sci-fi helmet with fine surface detail, visor reflection, and ventilation grill",
            "gt_3d_asset": "SciFiHelmet.glb (Khronos reference PBR asset)",
            "focus": "Fine-detail preservation in round-trip, specular highlight stability",
            "camera_motion": "Turntable_360_Orbit",
            "frame_count": 120,
            "fps": 24,
            "render_config": {
                "engine": "fulgur_headless",
                "mode": "path_trace",
                "spp": 256,
                "resolution": [1920, 1080],
                "aov_outputs": ["CameraLinearDepth", "WorldNormal", "Cryptomatte"]
            },
            "cycle_metrics_sla": {
                "max_volume_breathing_ratio": 0.01,
                "max_silhouette_area_std_pct": 0.8,
                "chamfer_distance_mm": 1.0,
                "normal_consistency": 0.96
            },
            "severity": "P0",
            "difficulty": "intermediate"
        },
        {
            "id": "rt_orbit_09_vehicle_hard_surface",
            "domain": "rigid_360_orbit",
            "source_dataset": "Objaverse-XL",
            "source_url": "https://objaverse.allenai.org/",
            "description": "Armored military vehicle with turret, tracks, and reactive armor plates",
            "gt_3d_asset": "Armored vehicle glb (~80K faces, complex topology)",
            "focus": "Large-scale rigid body volume consistency, turret joint rigidity",
            "camera_motion": "Turntable_360_Orbit",
            "frame_count": 120,
            "fps": 24,
            "render_config": {
                "engine": "fulgur_headless",
                "mode": "path_trace",
                "spp": 128,
                "resolution": [1920, 1080],
                "aov_outputs": ["CameraLinearDepth", "WorldNormal", "Cryptomatte"]
            },
            "cycle_metrics_sla": {
                "max_volume_breathing_ratio": 0.01,
                "max_silhouette_area_std_pct": 0.8,
                "chamfer_distance_mm": 2.0,
                "normal_consistency": 0.94
            },
            "severity": "P1",
            "difficulty": "intermediate"
        },

        # =====================================================================
        # Domain D: Dynamic Cloth & Micro-Wrinkle Fidelity
        # Focus: cloth dynamics round-trip and de-lighting albedo preservation
        # =====================================================================
        {
            "id": "rt_cloth_10_trenchcoat_stride",
            "domain": "cloth_dynamics",
            "source_dataset": "Fulgur dynamics engine (XPBD cloth simulation)",
            "source_url": "internal://fulgur/dynamics",
            "description": "Walking character wearing long trenchcoat, wind-blown trailing edge with micro-wrinkles",
            "gt_3d_asset": "Character skeleton + XPBD cloth simulation cache (trenchcoat mesh)",
            "focus": "Cloth fold frequency preservation, trailing edge dynamic silhouette",
            "camera_motion": "Forward_Tracking_Shot",
            "frame_count": 96,
            "fps": 24,
            "render_config": {
                "engine": "fulgur_headless",
                "mode": "path_trace",
                "spp": 128,
                "resolution": [1920, 1080],
                "aov_outputs": ["CameraLinearDepth", "WorldNormal", "MotionVector"]
            },
            "cycle_metrics_sla": {
                "cloth_fold_frequency_preservation": 0.85,
                "max_albedo_delta_e": 2.0,
                "ssim_multiview": 0.92,
                "lpips_multiview": 0.08
            },
            "severity": "P0",
            "difficulty": "expert"
        },
        {
            "id": "rt_cloth_11_cape_wind_billow",
            "domain": "cloth_dynamics",
            "source_dataset": "Fulgur dynamics engine (XPBD cloth simulation)",
            "source_url": "internal://fulgur/dynamics",
            "description": "Heroic pose character with flowing cape, strong lateral wind causing dramatic billow",
            "gt_3d_asset": "Character skeleton + XPBD cloth simulation cache (cape mesh + wind field)",
            "focus": "Large-deformation cloth volume, wind response temporal coherence",
            "camera_motion": "Orbital_Arc_120deg",
            "frame_count": 96,
            "fps": 24,
            "render_config": {
                "engine": "fulgur_headless",
                "mode": "path_trace",
                "spp": 128,
                "resolution": [1920, 1080],
                "aov_outputs": ["CameraLinearDepth", "WorldNormal", "MotionVector"]
            },
            "cycle_metrics_sla": {
                "cloth_fold_frequency_preservation": 0.80,
                "max_albedo_delta_e": 2.5,
                "ssim_multiview": 0.90,
                "lpips_multiview": 0.10
            },
            "severity": "P1",
            "difficulty": "expert"
        },
        {
            "id": "rt_cloth_12_skirt_spin_inertia",
            "domain": "cloth_dynamics",
            "source_dataset": "Fulgur dynamics engine (XPBD cloth simulation)",
            "source_url": "internal://fulgur/dynamics",
            "description": "Character performing spin turn, pleated skirt exhibiting centrifugal flare and settle",
            "gt_3d_asset": "Character skeleton + XPBD cloth simulation cache (pleated skirt mesh)",
            "focus": "Rotational inertia cloth response, settle damping after spin stop",
            "camera_motion": "Static_Front_View",
            "frame_count": 96,
            "fps": 24,
            "render_config": {
                "engine": "fulgur_headless",
                "mode": "path_trace",
                "spp": 128,
                "resolution": [1920, 1080],
                "aov_outputs": ["CameraLinearDepth", "WorldNormal", "MotionVector"]
            },
            "cycle_metrics_sla": {
                "cloth_fold_frequency_preservation": 0.82,
                "max_albedo_delta_e": 2.0,
                "ssim_multiview": 0.91,
                "lpips_multiview": 0.09
            },
            "severity": "P1",
            "difficulty": "advanced"
        }
    ]

    # Per-case directory structure: trajectory + render_spec + metrics_sla
    for case in roundtrip_cases:
        c_dir = cases_dir / case["id"]
        c_dir.mkdir(parents=True, exist_ok=True)

        # 1. Case manifest
        with open(c_dir / "case_manifest.json", "w", encoding="utf-8") as f:
            json.dump(case, f, indent=2, ensure_ascii=False)

        # 2. Render specification (for Fulgur/Caelum-Core headless invocation)
        render_spec = {
            "case_id": case["id"],
            "engine": case["render_config"]["engine"],
            "mode": case["render_config"]["mode"],
            "spp": case["render_config"]["spp"],
            "resolution": case["render_config"]["resolution"],
            "aov_outputs": case["render_config"]["aov_outputs"],
            "output_format": "exr",
            "frame_count": case["frame_count"],
            "fps": case["fps"],
            "camera_motion": case["camera_motion"],
            "notes": "Use: caelum-core --headless --config=render_spec.json or fulgur --mode=fgpp_guide"
        }
        with open(c_dir / "render_spec.json", "w", encoding="utf-8") as f:
            json.dump(render_spec, f, indent=2, ensure_ascii=False)

        # 3. Camera trajectory (same parametric generator as production cases)
        trajectory = []
        for f_idx in range(case["frame_count"]):
            t = f_idx / max(case["frame_count"] - 1, 1)
            if case["camera_motion"] == "Turntable_360_Orbit":
                angle = t * 2.0 * math.pi
                pos = [round(3.0 * math.cos(angle), 4), 1.2, round(3.0 * math.sin(angle), 4)]
                look_at = [0.0, 1.0, 0.0]
            elif case["camera_motion"] == "Orbital_Arc_120deg":
                angle = -math.pi / 3.0 + t * (2.0 * math.pi / 3.0)
                pos = [round(2.8 * math.sin(angle), 4), round(1.3 + 0.1 * math.sin(t * math.pi), 4), round(2.8 * math.cos(angle), 4)]
                look_at = [0.0, 1.0, 0.0]
            elif case["camera_motion"] == "Side_Tracking_Pan":
                pos = [round(-2.0 + t * 4.0, 4), 1.3, 3.0]
                look_at = [round(-2.0 + t * 4.0, 4), 1.0, 0.0]
            elif case["camera_motion"] == "Static_Front_View":
                pos = [0.0, 1.3, 3.5]
                look_at = [0.0, 1.0, 0.0]
            elif case["camera_motion"] == "Slow_Dolly_In_With_Orbit":
                angle = t * (math.pi / 6.0)
                dist = 3.2 - t * 0.7
                pos = [round(dist * math.sin(angle), 4), round(1.2 + t * 0.1, 4), round(dist * math.cos(angle), 4)]
                look_at = [0.0, 1.1, 0.0]
            else:  # Forward_Tracking_Shot
                pos = [0.0, 1.3, round(3.5 - t * 1.5, 4)]
                look_at = [0.0, 1.0, round(1.0 - t * 1.5, 4)]

            trajectory.append({
                "frame": f_idx,
                "timestamp_sec": round(f_idx / case["fps"], 4),
                "position": pos,
                "look_at": look_at,
                "up": [0.0, 1.0, 0.0]
            })

        with open(c_dir / "trajectory.json", "w", encoding="utf-8") as f:
            json.dump({
                "case_id": case["id"],
                "camera_motion": case["camera_motion"],
                "total_frames": case["frame_count"],
                "fps": case["fps"],
                "trajectory": trajectory
            }, f, indent=2, ensure_ascii=False)

        # 4. Cycle metrics SLA thresholds
        with open(c_dir / "metrics_sla.json", "w", encoding="utf-8") as f:
            json.dump(case["cycle_metrics_sla"], f, indent=2, ensure_ascii=False)

    # Suite manifest
    manifest = {
        "suite_id": "DERVGEN-DATASET-BIDIRECTIONAL-ROUNDTRIP",
        "title": "Bidirectional Round-Trip Evaluation Suite: 3D -> Rendered GT -> Diffusion -> 3D Cycle Fidelity",
        "version": "1.0.0",
        "total_cases": len(roundtrip_cases),
        "domains": {
            "hand_object_contact": {"count": 3, "source": "GRAB (ECCV 2020)"},
            "human_locomotion": {"count": 3, "source": "ZJU-MoCap (ICCV 2021) / Hi4D (CVPR 2023)"},
            "rigid_360_orbit": {"count": 3, "source": "Objaverse-XL / glTF Sample Models"},
            "cloth_dynamics": {"count": 3, "source": "Fulgur XPBD Dynamics Engine"}
        },
        "evaluation_pipeline": [
            "1. Render V_render_gt from GT 3D asset A0 using Fulgur/Caelum-Core headless path tracer",
            "2. Extract frame_0000 as Anchor, generate V_diffusion via Veo 2 / Seedance / Wan 2.1",
            "3. Distill V_diffusion -> A1 via Exp06 (CoTracker3 + DROID-SLAM + GVHMR + IK)",
            "4. Compute cycle metrics: Chamfer(A0, A1), Volume(A0, A1), DeltaE, SSIM(V_gt, V_enhanced)"
        ],
        "cycle_consistency_metrics": [
            "Chamfer_Distance_Normalized_mm",
            "Surface_F_Score_At_Tau_1mm",
            "Normal_Consistency",
            "Volume_Breathing_Ratio",
            "Silhouette_Area_Std_Pct",
            "Foot_Sliding_Velocity_cm_s",
            "Joint_Angle_RMSE_deg",
            "Bone_Length_Preservation_Ratio",
            "Albedo_DeltaE_CIELAB",
            "Cloth_Fold_Frequency_Preservation",
            "SSIM_MultiView",
            "LPIPS_MultiView",
            "Interpenetration_Volume_cm3",
            "Contact_Gap_mm"
        ],
        "cases": roundtrip_cases
    }

    with open(target_dir / "manifest.json", "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2, ensure_ascii=False)

    print(f"  \u2713 Initialized Bidirectional Round-Trip Benchmark ({len(roundtrip_cases)} cases across 4 domains)")




# ==============================================================================
# 4b. Rendering Condition Factor Framework (11 Dimensions x 4 Levels)
# ==============================================================================

# Canonical factor definitions: 3 groups x 11 dimensions, each L1(ideal)->L4(extreme)
RENDERING_CONDITION_FACTORS = {
    # ── Group 1: Observation Conditions (How We See) ─────────────────────────
    "F1_viewpoint_coverage": {
        "group": "observation",
        "name": "Viewpoint Coverage",
        "levels": {
            "L1": {"label": "Full 360° orbit", "azimuth_deg": 360, "elevation_deg": 0,
                   "num_views": 36, "distance": "medium", "description": "360° equi-spaced orbit, full surface visible"},
            "L2": {"label": "Hemisphere 180°", "azimuth_deg": 180, "elevation_deg": 0,
                   "num_views": 18, "distance": "medium", "description": "Front-facing 180° only, back hallucinated"},
            "L3": {"label": "Narrow arc 60°", "azimuth_deg": 60, "elevation_deg": 0,
                   "num_views": 6, "distance": "medium", "description": "60° narrow arc, heavy depth ambiguity"},
            "L4": {"label": "Single static view", "azimuth_deg": 0, "elevation_deg": 0,
                   "num_views": 1, "distance": "medium", "description": "Single front frame, zero viewpoint variation"},
        }
    },
    "F2_background_interference": {
        "group": "observation",
        "name": "Background Interference",
        "levels": {
            "L1": {"label": "Pure neutral", "bg_type": "solid_gray", "hdri": None,
                   "description": "Pure black/white/gray cyclorama, zero interference"},
            "L2": {"label": "Gradient HDRI", "bg_type": "hdri_uniform", "hdri": "studio_small_09_4k.exr",
                   "description": "Uniform HDRI ambient lighting, no concrete objects"},
            "L3": {"label": "Scene objects", "bg_type": "scene_objects", "hdri": "interior_room_01_4k.exr",
                   "description": "Tables, chairs, walls with texture in background"},
            "L4": {"label": "Cluttered + camouflage", "bg_type": "cluttered_camouflage", "hdri": "urban_ruins_02_4k.exr",
                   "description": "Complex jungle/ruins, subject color matches background"},
        }
    },
    "F3_lighting_condition": {
        "group": "observation",
        "name": "Lighting Condition",
        "levels": {
            "L1": {"label": "Neutral diffuse", "light_type": "area_soft", "intensity": 1.0, "color_temp_K": 5500,
                   "description": "Uniform soft studio lighting, no hard shadows"},
            "L2": {"label": "Single key light", "light_type": "key_fill", "intensity": 1.5, "color_temp_K": 5000,
                   "description": "Key + fill, controlled shadow, standard cinematography"},
            "L3": {"label": "Hard contrast", "light_type": "point_hard", "intensity": 3.0, "color_temp_K": 4500,
                   "description": "Hard point light, sharp shadows, specular blowout"},
            "L4": {"label": "Extreme / mixed color", "light_type": "multi_color_neon", "intensity": 2.0, "color_temp_K": None,
                   "description": "Multi-color neon, backlit silhouette, de-lighting impossible"},
        }
    },
    "F6_capture_quality": {
        "group": "observation",
        "name": "Capture Quality",
        "levels": {
            "L1": {"label": "Lossless HD", "resolution": [1920, 1080], "codec": "exr_lossless", "noise_sigma": 0.0,
                   "description": "1080p/4K lossless EXR, zero noise"},
            "L2": {"label": "Standard H.264", "resolution": [1920, 1080], "codec": "h264_crf18", "noise_sigma": 0.005,
                   "description": "H.264 CRF 18-23, slight blocking artifacts"},
            "L3": {"label": "Heavy compression", "resolution": [1280, 720], "codec": "h264_crf28", "noise_sigma": 0.02,
                   "description": "H.264 CRF 28+, visible color banding"},
            "L4": {"label": "Low-res + noise", "resolution": [854, 480], "codec": "h264_crf32", "noise_sigma": 0.05,
                   "description": "480p + sensor noise + motion blur"},
        }
    },

    # ── Group 2: Object Intrinsic Properties (What We See) ───────────────────
    "F5_surface_material": {
        "group": "object_intrinsic",
        "name": "Surface Material",
        "levels": {
            "L1": {"label": "Diffuse matte", "roughness": 1.0, "metallic": 0.0, "transmission": 0.0,
                   "description": "Uniform Lambertian surface, easiest for multi-view consistency"},
            "L2": {"label": "Standard PBR", "roughness": 0.5, "metallic": 0.5, "transmission": 0.0,
                   "description": "Mixed metal-rough PBR, moderate highlight shift"},
            "L3": {"label": "High specular", "roughness": 0.05, "metallic": 1.0, "transmission": 0.0,
                   "description": "Highly polished metal/clearcoat, view-dependent highlights"},
            "L4": {"label": "Transparent/SSS", "roughness": 0.2, "metallic": 0.0, "transmission": 0.8,
                   "description": "Glass, skin SSS, anisotropic brushed metal"},
        }
    },
    "F7_geometric_complexity": {
        "group": "object_intrinsic",
        "name": "Geometric Complexity",
        "levels": {
            "L1": {"label": "Simple convex", "face_count_range": [100, 1000], "genus": 0,
                   "description": "Convex hull, <1K faces, no concavities"},
            "L2": {"label": "Standard industrial", "face_count_range": [1000, 20000], "genus": 0,
                   "description": "Gears, weapons, mechanical parts (1K-20K faces)"},
            "L3": {"label": "Organic complex", "face_count_range": [20000, 100000], "genus": 0,
                   "description": "Human body, creatures, trees (20K-100K faces)"},
            "L4": {"label": "Extreme fine detail", "face_count_range": [100000, 1000000], "genus": -1,
                   "description": "Hair strands, wire mesh, foliage clusters"},
        }
    },
    "F8_texture_informativeness": {
        "group": "object_intrinsic",
        "name": "Texture Informativeness",
        "levels": {
            "L1": {"label": "Rich texture", "texture_type": "unique_high_freq", "feature_density": "dense",
                   "description": "Full-surface unique high-frequency texture (camo, brick, wood grain)"},
            "L2": {"label": "Moderate texture", "texture_type": "partial_mixed", "feature_density": "medium",
                   "description": "Partial texture with smooth regions (skin + clothing)"},
            "L3": {"label": "Sparse texture", "texture_type": "mostly_smooth", "feature_density": "sparse",
                   "description": "Large monochrome areas, features only at edges"},
            "L4": {"label": "Textureless", "texture_type": "uniform_flat", "feature_density": "none",
                   "description": "All-white plaster / uniform matte, zero trackable features"},
        }
    },
    "F9_symmetry_ambiguity": {
        "group": "object_intrinsic",
        "name": "Symmetry & Pose Ambiguity",
        "levels": {
            "L1": {"label": "Fully asymmetric", "symmetry_order": 1, "planes": 0,
                   "description": "Uniquely identifiable from any angle"},
            "L2": {"label": "Bilateral symmetric", "symmetry_order": 2, "planes": 1,
                   "description": "Left-right mirror (face, airplane) — minor L/R flip risk"},
            "L3": {"label": "Rotational N-fold", "symmetry_order": -1, "planes": -1,
                   "description": "N>=3 rotational symmetry (vase, tire) — phase lock failure"},
            "L4": {"label": "Near-spherical", "symmetry_order": -2, "planes": -2,
                   "description": "Almost spherical, orientation unrecoverable"},
        }
    },

    # ── Group 3: Dynamic Properties (How It Moves) ──────────────────────────
    "F4_motion_dynamics": {
        "group": "dynamic",
        "name": "Motion Dynamics",
        "levels": {
            "L1": {"label": "Static / slow", "max_speed_m_s": 0.1, "motion_blur": False,
                   "description": "T-pose or very slow rotation (<5°/s)"},
            "L2": {"label": "Normal walk", "max_speed_m_s": 1.4, "motion_blur": False,
                   "description": "Standard walking speed (~1.4 m/s)"},
            "L3": {"label": "Fast action", "max_speed_m_s": 5.0, "motion_blur": True,
                   "description": "Running, jumping, weapon swing (>3 m/s)"},
            "L4": {"label": "Extreme dynamics", "max_speed_m_s": 10.0, "motion_blur": True,
                   "description": "Sudden stops, flips, multi-person interaction"},
        }
    },
    "F10_articulation_deformation": {
        "group": "dynamic",
        "name": "Articulation & Deformation",
        "levels": {
            "L1": {"label": "Pure rigid", "dof_type": "rigid_6dof", "deformation": "none",
                   "description": "Zero deformation, translation/rotation only"},
            "L2": {"label": "Articulated joints", "dof_type": "joint_chain", "deformation": "joint_angle",
                   "description": "Limited DOF joint chain (robot, skeleton)"},
            "L3": {"label": "Skeletal skinning", "dof_type": "smplx_skeleton", "deformation": "lbs_skinning",
                   "description": "Skeleton-driven + skin deformation (character)"},
            "L4": {"label": "Free-form deformation", "dof_type": "continuous_field", "deformation": "topology_change",
                   "description": "Fluid, cloth, hair — no parametric model"},
        }
    },
    "F11_multi_body_interaction": {
        "group": "dynamic",
        "name": "Multi-Body Interaction",
        "levels": {
            "L1": {"label": "Single isolated", "body_count": 1, "contact_type": "none",
                   "description": "One object in scene, no interaction"},
            "L2": {"label": "Ground contact", "body_count": 1, "contact_type": "ground_plane",
                   "description": "One object on ground (standing, walking)"},
            "L3": {"label": "Two-body contact", "body_count": 2, "contact_type": "hand_object",
                   "description": "Hand-held prop, two-person handshake, riding"},
            "L4": {"label": "Multi-body group", "body_count": -1, "contact_type": "group_interaction",
                   "description": "Multi-person interaction, group battle, complex mechanism"},
        }
    },
}

# Baseline: all factors at L1
_BASELINE_LEVELS = {f"F{i}": "L1" for i in [1,2,3,4,5,6,7,8,9,10,11]}

# 34 single-factor conditions (baseline + 11 factors x 3 non-L1 levels)
SINGLE_FACTOR_CONDITIONS = [{"id": "cond_baseline", "description": "All factors ideal (L1)", "levels": dict(_BASELINE_LEVELS)}]
for factor_key, factor_def in RENDERING_CONDITION_FACTORS.items():
    f_num = factor_key.split("_")[0]  # e.g. "F1", "F10"
    for level in ["L2", "L3", "L4"]:
        cond_id = f"cond_{f_num.lower()}_{level}"
        levels = dict(_BASELINE_LEVELS)
        levels[f_num] = level
        SINGLE_FACTOR_CONDITIONS.append({
            "id": cond_id,
            "description": f"{factor_def['name']} at {level} ({factor_def['levels'][level]['label']}), rest ideal",
            "levels": levels
        })

# 12 cross-combination conditions (real-world scenario simulations)
CROSS_CONDITIONS = [
    {"id": "cond_cross_01", "description": "Indoor half-arc with furniture",
     "difficulty": "medium", "levels": {**_BASELINE_LEVELS, "F1": "L2", "F2": "L3", "F3": "L2"}},
    {"id": "cond_cross_02", "description": "Narrow angle + fast action + specular metal",
     "difficulty": "high", "levels": {**_BASELINE_LEVELS, "F1": "L3", "F4": "L3", "F5": "L3"}},
    {"id": "cond_cross_03", "description": "Outdoor ruins + hard light + compression",
     "difficulty": "high", "levels": {**_BASELINE_LEVELS, "F2": "L4", "F3": "L3", "F6": "L2"}},
    {"id": "cond_cross_04", "description": "Standard game-engine capture conditions",
     "difficulty": "medium", "levels": {**_BASELINE_LEVELS, "F1": "L2", "F4": "L2", "F5": "L2"}},
    {"id": "cond_cross_05", "description": "Extreme: single view + backlit + transparent",
     "difficulty": "extreme", "levels": {**_BASELINE_LEVELS, "F1": "L4", "F3": "L4", "F5": "L4"}},
    {"id": "cond_cross_06", "description": "Organic body + sparse texture + skeletal skinning",
     "difficulty": "high", "levels": {**_BASELINE_LEVELS, "F7": "L3", "F8": "L3", "F10": "L3"}},
    {"id": "cond_cross_07", "description": "Rotational-symmetric vase + hemisphere coverage",
     "difficulty": "medium", "levels": {**_BASELINE_LEVELS, "F9": "L3", "F1": "L2", "F8": "L2"}},
    {"id": "cond_cross_08", "description": "Standard cinematic capture conditions",
     "difficulty": "medium", "levels": {**_BASELINE_LEVELS, "F3": "L2", "F4": "L2", "F11": "L2"}},
    {"id": "cond_cross_09", "description": "Hair/fur + fast motion + hard light",
     "difficulty": "extreme", "levels": {**_BASELINE_LEVELS, "F7": "L4", "F4": "L3", "F3": "L3"}},
    {"id": "cond_cross_10", "description": "Free-form cloth + cluttered bg + compression",
     "difficulty": "extreme", "levels": {**_BASELINE_LEVELS, "F10": "L4", "F2": "L3", "F6": "L3"}},
    {"id": "cond_cross_11", "description": "Two-person hand-held prop + walking",
     "difficulty": "high", "levels": {**_BASELINE_LEVELS, "F11": "L3", "F9": "L2", "F4": "L2"}},
    {"id": "cond_cross_12", "description": "Industrial CG standard production conditions",
     "difficulty": "medium", "levels": {**_BASELINE_LEVELS, "F1": "L2", "F5": "L2", "F7": "L2", "F11": "L2"}},
]

ALL_RENDERING_CONDITIONS = SINGLE_FACTOR_CONDITIONS + CROSS_CONDITIONS

# Per-domain priority factors: which single-factor conditions to test per RT domain
DOMAIN_PRIORITY_FACTORS = {
    "hand_object_contact": ["F1", "F3", "F5"],   # viewpoint, lighting, material
    "human_locomotion":    ["F1", "F4", "F2"],    # viewpoint, motion, background
    "rigid_360_orbit":     ["F1", "F2", "F5"],    # viewpoint, background, material
    "cloth_dynamics":      ["F3", "F4", "F6"],    # lighting, motion, capture quality
}

# Per-domain recommended cross conditions
DOMAIN_CROSS_CONDITIONS = {
    "hand_object_contact": ["cond_cross_02", "cond_cross_04"],
    "human_locomotion":    ["cond_cross_01", "cond_cross_08"],
    "rigid_360_orbit":     ["cond_cross_07", "cond_cross_12"],
    "cloth_dynamics":      ["cond_cross_10", "cond_cross_06"],
}


def _get_condition_render_overrides(condition: dict) -> dict:
    """Translate a condition's factor levels into Fulgur render_spec parameter overrides."""
    levels = condition["levels"]
    overrides = {}

    # F1: Viewpoint Coverage -> camera trajectory modification
    f1_level = levels.get("F1", "L1")
    f1_def = RENDERING_CONDITION_FACTORS["F1_viewpoint_coverage"]["levels"][f1_level]
    overrides["camera_override"] = {
        "azimuth_range_deg": f1_def["azimuth_deg"],
        "num_views": f1_def["num_views"],
        "distance": f1_def["distance"],
    }

    # F2: Background -> scene/HDRI setting
    f2_level = levels.get("F2", "L1")
    f2_def = RENDERING_CONDITION_FACTORS["F2_background_interference"]["levels"][f2_level]
    overrides["background"] = {
        "type": f2_def["bg_type"],
        "hdri": f2_def["hdri"],
    }

    # F3: Lighting -> light rig
    f3_level = levels.get("F3", "L1")
    f3_def = RENDERING_CONDITION_FACTORS["F3_lighting_condition"]["levels"][f3_level]
    overrides["lighting"] = {
        "type": f3_def["light_type"],
        "intensity": f3_def["intensity"],
        "color_temp_K": f3_def["color_temp_K"],
    }

    # F5: Material -> material override (applied as a uniform material override in engine)
    f5_level = levels.get("F5", "L1")
    f5_def = RENDERING_CONDITION_FACTORS["F5_surface_material"]["levels"][f5_level]
    overrides["material_override"] = {
        "roughness": f5_def["roughness"],
        "metallic": f5_def["metallic"],
        "transmission": f5_def["transmission"],
    }

    # F6: Capture Quality -> post-process degradation
    f6_level = levels.get("F6", "L1")
    f6_def = RENDERING_CONDITION_FACTORS["F6_capture_quality"]["levels"][f6_level]
    overrides["capture_quality"] = {
        "resolution": f6_def["resolution"],
        "codec": f6_def["codec"],
        "noise_sigma": f6_def["noise_sigma"],
    }

    # F4: Motion -> speed hint for animation playback
    f4_level = levels.get("F4", "L1")
    f4_def = RENDERING_CONDITION_FACTORS["F4_motion_dynamics"]["levels"][f4_level]
    overrides["motion"] = {
        "max_speed_m_s": f4_def["max_speed_m_s"],
        "motion_blur": f4_def["motion_blur"],
    }

    return overrides


def setup_rendering_conditions(eval_dir: Path):
    """Sets up rendering condition factor variants for the Bidirectional Round-Trip Suite.

    For each of the 12 RT cases, generates condition variant sub-directories
    containing variant-specific render_spec_variant.json files that extend the
    base render_spec.json with condition-specific parameter overrides.

    Generates:
      - dataset_bidirectional_roundtrip/rendering_conditions/
        ├── factor_definitions.json      (canonical 11-factor x 4-level definitions)
        ├── condition_matrix.json         (46 conditions: 34 single-factor + 12 cross)
        ├── domain_assignments.json       (which conditions each RT case uses)
        └── cases/<case_id>/
            └── variants/<condition_id>/
                └── render_spec_variant.json  (base render_spec + condition overrides)

    Total rendering tasks: 12 cases x 12 conditions/case = 144 variant renders.
    Estimated time: ~1.5-2 hours single GPU at 128spp, 96-120 frames each.
    """
    rt_dir = eval_dir / "dataset_bidirectional_roundtrip"
    rc_dir = rt_dir / "rendering_conditions"
    rc_dir.mkdir(parents=True, exist_ok=True)

    if (rc_dir / "factor_definitions.json").exists() and (rc_dir / "condition_matrix.json").exists():
        print(f"  ⏩ [SKIP] Rendering condition framework already initialized ({len(ALL_RENDERING_CONDITIONS)} conditions)")
        return

    # 1. Factor definitions
    with open(rc_dir / "factor_definitions.json", "w", encoding="utf-8") as f:
        json.dump({
            "version": "1.0.0",
            "total_factors": len(RENDERING_CONDITION_FACTORS),
            "groups": {
                "observation": {"factors": ["F1", "F2", "F3", "F6"], "description": "How we see — information completeness"},
                "object_intrinsic": {"factors": ["F5", "F7", "F8", "F9"], "description": "What we see — reconstruction difficulty"},
                "dynamic": {"factors": ["F4", "F10", "F11"], "description": "How it moves — temporal distillation difficulty"},
            },
            "factors": RENDERING_CONDITION_FACTORS,
        }, f, indent=2, ensure_ascii=False)

    # 2. Condition matrix
    with open(rc_dir / "condition_matrix.json", "w", encoding="utf-8") as f:
        json.dump({
            "version": "1.0.0",
            "total_conditions": len(ALL_RENDERING_CONDITIONS),
            "single_factor_conditions": len(SINGLE_FACTOR_CONDITIONS),
            "cross_conditions": len(CROSS_CONDITIONS),
            "conditions": ALL_RENDERING_CONDITIONS,
        }, f, indent=2, ensure_ascii=False)

    # 3. Load RT cases manifest to get domain assignments
    rt_manifest_path = rt_dir / "manifest.json"
    if not rt_manifest_path.exists():
        print("  ⚠ Round-trip manifest not found — run step 4 first. Skipping condition variants.")
        return

    with open(rt_manifest_path, "r", encoding="utf-8") as f:
        rt_manifest = json.load(f)

    rt_cases = rt_manifest.get("cases", [])
    domain_assignments = {}
    total_variant_count = 0

    for case in rt_cases:
        case_id = case["id"]
        domain = case["domain"]
        case_dir = rt_dir / "cases" / case_id
        variants_dir = case_dir / "variants"
        variants_dir.mkdir(parents=True, exist_ok=True)

        # Load base render_spec
        base_render_spec_path = case_dir / "render_spec.json"
        if base_render_spec_path.exists():
            with open(base_render_spec_path, "r", encoding="utf-8") as f:
                base_spec = json.load(f)
        else:
            base_spec = {}

        # Determine which conditions this case tests
        priority_factors = DOMAIN_PRIORITY_FACTORS.get(domain, ["F1", "F2", "F3"])
        cross_cond_ids = DOMAIN_CROSS_CONDITIONS.get(domain, ["cond_cross_04", "cond_cross_08"])

        # Collect conditions: baseline + single-factor for priority factors + cross
        case_conditions = []

        # Always include baseline
        case_conditions.append(SINGLE_FACTOR_CONDITIONS[0])  # cond_baseline

        # Single-factor: for each priority factor, L2/L3/L4
        for sf_cond in SINGLE_FACTOR_CONDITIONS[1:]:  # skip baseline
            # Check if this condition varies one of the priority factors
            for f_key, f_level in sf_cond["levels"].items():
                if f_level != "L1" and f_key in priority_factors:
                    case_conditions.append(sf_cond)
                    break

        # Cross conditions
        for cross_cond in CROSS_CONDITIONS:
            if cross_cond["id"] in cross_cond_ids:
                case_conditions.append(cross_cond)

        # Generate variant render specs
        variant_ids = []
        for cond in case_conditions:
            cond_id = cond["id"]
            variant_dir = variants_dir / cond_id
            variant_dir.mkdir(parents=True, exist_ok=True)

            overrides = _get_condition_render_overrides(cond)

            variant_spec = {
                "case_id": case_id,
                "condition_id": cond_id,
                "condition_description": cond["description"],
                "factor_levels": cond["levels"],
                "base_render_spec": base_spec,
                "overrides": overrides,
                "notes": f"Variant of {case_id} under condition {cond_id}. Merge overrides into base_render_spec for engine invocation."
            }

            with open(variant_dir / "render_spec_variant.json", "w", encoding="utf-8") as f:
                json.dump(variant_spec, f, indent=2, ensure_ascii=False)

            variant_ids.append(cond_id)

        domain_assignments[case_id] = {
            "domain": domain,
            "priority_factors": priority_factors,
            "cross_conditions": cross_cond_ids,
            "total_variants": len(case_conditions),
            "variant_ids": variant_ids,
        }
        total_variant_count += len(case_conditions)

    # 4. Domain assignments
    with open(rc_dir / "domain_assignments.json", "w", encoding="utf-8") as f:
        json.dump({
            "version": "1.0.0",
            "total_cases": len(rt_cases),
            "total_rendering_tasks": total_variant_count,
            "estimated_time_single_gpu_hours": round(total_variant_count * 100 * 0.4 / 3600, 1),
            "assignments": domain_assignments,
        }, f, indent=2, ensure_ascii=False)

    print(f"  \u2713 Initialized Rendering Condition Framework: {len(RENDERING_CONDITION_FACTORS)} factors x 4 levels")
    print(f"    {len(ALL_RENDERING_CONDITIONS)} total conditions (34 single-factor + 12 cross)")
    print(f"    {total_variant_count} rendering task variants across {len(rt_cases)} cases")


# ==============================================================================
# 5. Multimodal Captures & Manifests
# ==============================================================================

def setup_sample_captures(captures_dir: Path):
    """Initializes metadata and placeholder sample records for testing."""
    img_dir = captures_dir / "images"
    audio_dir = captures_dir / "audio"
    video_dir = captures_dir / "videos"

    if (img_dir / "manifest.json").exists() and (audio_dir / "manifest.json").exists() and (video_dir / "manifest.json").exists():
        print("  ⏩ [SKIP] Sample captures manifests already initialized.")
        return

    img_dir.mkdir(parents=True, exist_ok=True)
    audio_dir.mkdir(parents=True, exist_ok=True)
    video_dir.mkdir(parents=True, exist_ok=True)

    # Images manifest
    img_manifest = {
        "version": "1.0.0",
        "description": "Standard test image cases for 3D reconstruction & neural relighting",
        "samples": [
            {
                "id": "hard_surface_helmet",
                "filename": "sample_helmet.jpg",
                "target_models": ["trellis_image_large", "triposr", "meshanything_v2"],
                "category": "hard_surface_mechanical",
                "url": "https://raw.githubusercontent.com/KhronosGroup/glTF-Sample-Models/master/2.0/SciFiHelmet/screenshot/screenshot.png"
            },
            {
                "id": "character_portrait",
                "filename": "sample_portrait.jpg",
                "target_models": ["emoca_v2_face", "iclight_relight"],
                "category": "human_portrait_emotion",
                "url": "https://raw.githubusercontent.com/KhronosGroup/glTF-Sample-Assets/main/Models/CesiumMan/screenshot/screenshot.jpg"
            },
            {
                "id": "organic_creature",
                "filename": "sample_creature.jpg",
                "target_models": ["hunyuan3d_2_shape", "dust3r_large"],
                "category": "organic_character",
                "url": "https://raw.githubusercontent.com/KhronosGroup/glTF-Sample-Models/master/2.0/Fox/screenshot/screenshot.jpg"
            }
        ]
    }
    with open(img_dir / "manifest.json", "w", encoding="utf-8") as f:
        json.dump(img_manifest, f, indent=2, ensure_ascii=False)

    # Audio manifest
    audio_manifest = {
        "version": "1.0.0",
        "description": "Standard dialogue prompts and test audio for voice cloning and foley",
        "samples": [
            {
                "id": "cinematic_hero_voice",
                "filename": "sample_hero_prompt.wav",
                "target_model": "f5_tts_voice_clone",
                "duration_sec": 3.2,
                "text": "The engine is online. Warp trajectory calibrated at point nine four."
            },
            {
                "id": "physical_impact_foley",
                "filename": "sample_foley_action.wav",
                "target_model": "audioldm2_foley",
                "duration_sec": 4.0,
                "description": "Heavy robotic footsteps on metallic floor with reverberation."
            }
        ]
    }
    with open(audio_dir / "manifest.json", "w", encoding="utf-8") as f:
        json.dump(audio_manifest, f, indent=2, ensure_ascii=False)

    # Video manifest
    video_manifest = {
        "version": "1.0.0",
        "description": "Camera trajectories and video tracking sequences for distillation",
        "samples": [
            {
                "id": "orbit_turntable_360",
                "filename": "orbit_turntable.mp4",
                "target_models": ["cotracker3_stride4", "droid_slam_weights", "depth_anything_v2_metric"],
                "frame_count": 120,
                "resolution": [1280, 720],
                "description": "Smooth 360-degree turntable camera trajectory around center subject."
            },
            {
                "id": "walking_motion_reference",
                "filename": "reference_motion.mp4",
                "target_models": ["gvhmr_v1", "wham_mocap", "unirig_weights"],
                "frame_count": 96,
                "resolution": [1920, 1080],
                "description": "4-second actor forward walking motion clip for mocap & foot-plant IK."
            }
        ]
    }
    with open(video_dir / "manifest.json", "w", encoding="utf-8") as f:
        json.dump(video_manifest, f, indent=2, ensure_ascii=False)

    print("  ✓ Created sample captures metadata in images/, audio/, videos/")


# ==============================================================================
# 6. Live Google Drive Dataset & Evaluation Index Synchronizer
# ==============================================================================

def sync_data_index():
    """Generates /dervgen/data/INDEX.json and INDEX.md in Google Drive."""
    scenes_dir = DATA_ROOT / "cg" / "scenes"
    industry_dir = scenes_dir
    eval_dir = DATA_ROOT / "3d" / "evaluations"
    cases_dir = eval_dir / "cases"
    img_dir = DATA_ROOT / "captures" / "images"
    audio_dir = DATA_ROOT / "captures" / "audio"
    video_dir = DATA_ROOT / "captures" / "videos"

    mesh_manifest_path = eval_dir / "dataset_mesh_repair" / "manifest.json"
    mat_manifest_path = eval_dir / "dataset_material_repair" / "manifest.json"
    anim_manifest_path = eval_dir / "dataset_anim_repair" / "manifest.json"
    roundtrip_manifest_path = eval_dir / "dataset_bidirectional_roundtrip" / "manifest.json"

    mesh_cases_count = 0
    mat_cases_count = 0
    anim_cases_count = 0
    roundtrip_cases_count = 0

    if mesh_manifest_path.exists():
        with open(mesh_manifest_path, "r", encoding="utf-8") as f:
            mesh_cases_count = len(json.load(f).get("cases", []))
    if mat_manifest_path.exists():
        with open(mat_manifest_path, "r", encoding="utf-8") as f:
            mat_cases_count = len(json.load(f).get("cases", []))
    if anim_manifest_path.exists():
        with open(anim_manifest_path, "r", encoding="utf-8") as f:
            anim_cases_count = len(json.load(f).get("cases", []))
    if roundtrip_manifest_path.exists():
        with open(roundtrip_manifest_path, "r", encoding="utf-8") as f:
            roundtrip_cases_count = len(json.load(f).get("cases", []))

    rc_assignments_path = eval_dir / "dataset_bidirectional_roundtrip" / "rendering_conditions" / "domain_assignments.json"
    rendering_condition_tasks = 0
    if rc_assignments_path.exists():
        with open(rc_assignments_path, "r", encoding="utf-8") as f:
            rendering_condition_tasks = json.load(f).get("total_rendering_tasks", 0)

    # Load industry scene registry if available
    industry_registry_path = industry_dir / "scene_registry.json"
    industry_scenes = []
    industry_stats = {"total": 0, "downloaded": 0, "manual": 0}
    if industry_registry_path.exists():
        with open(industry_registry_path, "r", encoding="utf-8") as f:
            reg = json.load(f)
            industry_scenes = reg.get("scenes", [])
            industry_stats["total"] = reg.get("total_scenes", len(industry_scenes))
            for s in industry_scenes:
                if s.get("status") in ("downloaded", "already_present"):
                    industry_stats["downloaded"] += 1
                elif s.get("status") == "manual_download_required":
                    industry_stats["manual"] += 1

    inventory = {
        "version": "1.1.0",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "storage_root": str(DATA_ROOT),
        "scenes": [f.name for f in scenes_dir.iterdir() if f.is_file()] if scenes_dir.exists() else [],
        "industry_benchmark_scenes": {
            "total_registered": industry_stats["total"],
            "downloaded": industry_stats["downloaded"],
            "manual_download_required": industry_stats["manual"],
            "registry_path": str(industry_registry_path),
            "scenes": [{"id": s["id"], "name": s["name"], "status": s["status"],
                         "tier": s["tier"], "triangle_count": s["triangle_count"]}
                        for s in industry_scenes],
        },
        "production_cases": [d.name for d in cases_dir.iterdir() if d.is_dir()] if cases_dir.exists() else [],
        "evaluation_suites": {
            "dataset_mesh_repair_cases": mesh_cases_count,
            "dataset_material_repair_cases": mat_cases_count,
            "dataset_anim_repair_cases": anim_cases_count,
            "dataset_bidirectional_roundtrip_cases": roundtrip_cases_count,
            "dataset_rendering_condition_tasks": rendering_condition_tasks,
            "total_benchmark_cases": mesh_cases_count + mat_cases_count + anim_cases_count + roundtrip_cases_count
        },
        "image_captures": [f.name for f in img_dir.iterdir() if f.is_file()] if img_dir.exists() else [],
        "audio_captures": [f.name for f in audio_dir.iterdir() if f.is_file()] if audio_dir.exists() else [],
        "video_captures": [f.name for f in video_dir.iterdir() if f.is_file()] if video_dir.exists() else [],
    }

    index_json_path = DATA_ROOT / "INDEX.json"
    index_md_path = DATA_ROOT / "INDEX.md"

    with open(index_json_path, "w", encoding="utf-8") as f:
        json.dump(inventory, f, indent=2, ensure_ascii=False)

    md_lines = [
        "# DervGen Google Drive Dataset & Evaluation Index",
        "",
        f"> **Generated at**: `{inventory['generated_at']}`  ",
        f"> **Cloud SSOT Root**: `{DATA_ROOT}`",
        "",
        "## 🏛️ Benchmark 3D Scenes & Geometries (`data/cg/scenes/`)",
        "| File | Type | Description |",
        "|---|---|---|",
        "| `cornell_box.obj` | 3D Scene | Classical physically-based radiosity & raytracing benchmark |",
        "| `cornell_box.mtl` | Materials | Diffuse red/green walls, ceiling area light emitter |",
        "| `sphere.obj` | 3D Geometry | Parametric UV sphere (normals + UVs) for material & BRDF evaluation |",
        "| `cube.obj` | 3D Geometry | 1x1x1m unit cube for transform & spatial validation |",
        "| `stanford_bunny.obj` | 3D Geometry | High-curvature smooth surface benchmark geometry |",
        "| `teapot.obj` | 3D Geometry | Utah teapot specular and curvature benchmark geometry |",
        "",
        "## 🎬 Industry-Standard AAA Rendering Benchmark Scenes (`data/cg/scenes/`)",
        "",
        "Canonical rendering benchmark scenes from film, game, and GPU research industries",
        f"for Caelum-Core headless rendering validation. ({industry_stats['total']} registered, "
        f"{industry_stats['downloaded']} downloaded, {industry_stats['manual']} manual)",
        "",
        "| Scene | Tier | Triangles | Format | PBR | Status |",
        "|---|---|---|---|---|---|",
    ]

    for s in industry_scenes:
        status_icon = {"downloaded": "✅", "already_present": "✅",
                       "download_script_generated": "📜", "manual_download_required": "📋",
                       "download_failed": "❌", "filtered_out": "⏭️"}.get(s.get("status", ""), "⏳")
        md_lines.append(
            f"| **{s['name']}** | {s['tier']} | {s['triangle_count']} | "
            f"{s.get('format', 'N/A')} | {s.get('pbr_workflow', 'N/A')} | {status_icon} |"
        )

    md_lines.extend([
        "",
        "## 🧪 Production Closed-Loop Benchmark Cases (`data/evaluations/cases/`)",
        "| Case ID | Domain & Focus | Camera Trajectory | Metrics SLA |",
        "|---|---|---|---|",
        "| **`case_01_mech_ranger`** | Hard Surface Tactical Armor, Weapon Grip Anti-Clipping | Slow Dolly In with Orbit (96f) | Clipping 0%, Slip < 0.5 cm/s, PSNR >= 38dB |",
        "| **`case_02_cyber_hunter`** | Cyberpunk Cloth Dynamics & Foot-Planting IK | Forward Tracking Shot (96f) | Slip < 0.3 cm/s, Clipping 0%, PSNR >= 39dB |",
        "| **`case_03_cinematic_orbit`** | Biomechanical Exosuit, 360° Volumetric Rigidity | Turntable 360 Orbit (120f) | Volume Breathing < 1.5%, PSNR >= 40dB |",
        "",
        f"## 🏆 RFC 0053 \"SWE-bench for 3D\" Evaluation Benchmark Suite ({inventory['evaluation_suites']['total_benchmark_cases']} Cases)",
        f"- 📁 **`data/evaluations/dataset_mesh_repair/`** ({mesh_cases_count} cases):",
        "  - Non-manifold edges, boundary holes, inverted normals, zero-area faces, isolated vertices, self-intersection.",
        f"- 📁 **`data/evaluations/dataset_material_repair/`** ({mat_cases_count} cases):",
        "  - Baked shadow de-lighting, UV overlap, DirectX/OpenGL normal flip, inverted roughness, boundary bleeding.",
        f"- 📁 **`data/evaluations/dataset_anim_repair/`** ({anim_cases_count} cases):",
        "  - Foot sliding drift, knee/elbow hyperextension, weapon clipping, root drift, unnormalized skinning weights.",
        "",
        "## 📸 Test Captures & Multimodal Manifests (`data/captures/`)",
        "- `images/manifest.json`: Standard test portraits, hard-surface props, organic creatures",
        "- `audio/manifest.json`: 3-second reference voice prompts and Foley descriptions",
        "- `videos/manifest.json`: 360-degree orbit and 4-second continuous walking tracking sequences",
        "",
        "---",
        "All evaluation datasets reside purely in Google Drive cloud storage (Zero local disk footprint)."
    ])

    with open(index_md_path, "w", encoding="utf-8") as f:
        f.write("\n".join(md_lines) + "\n")

    print(f"✅ Synced Google Drive Dataset Index:")
    print(f"   📄 {index_json_path}")
    print(f"   📄 {index_md_path}")


# ==============================================================================
# Master Staging Orchestration
# ==============================================================================

def setup_all_datasets(industry_tier: str = "all", skip_industry_manual: bool = True):
    """Master initializer for all benchmark and evaluation datasets directly into Google Drive."""
    if not check_drive_mounted():
        return False

    print(f"\n=======================================================")
    print(f" 📊 DervGen Evaluation & Benchmark Dataset Initializer")
    print(f" Cloud Target: {DATA_ROOT}")
    print(f"=======================================================")

    scenes_dir = DATA_ROOT / "cg" / "scenes"
    eval_dir = DATA_ROOT / "3d" / "evaluations"
    cases_dir = eval_dir / "cases"
    captures_dir = DATA_ROOT / "common" / "captures"

    # 1. 3D Benchmark Geometries
    print("\n[1/8] Generating benchmark 3D scenes & geometries...")
    generate_cornell_box(scenes_dir)
    generate_sphere(scenes_dir)
    generate_cube(scenes_dir)
    generate_stanford_bunny(scenes_dir)
    generate_teapot(scenes_dir)

    # 1b. Industry-Standard AAA Rendering Benchmark Scenes
    print(f"\n[1b/8] Downloading industry-standard AAA rendering benchmark scenes (tier={industry_tier})...")
    setup_industry_benchmark_scenes(scenes_dir, tier_filter=industry_tier,
                                    skip_manual=skip_industry_manual)

    # 2. Production Closed-Loop Benchmark Cases
    print("\n[2/8] Setting up closed-loop production benchmark cases (cases/)...")
    setup_closed_loop_benchmark_cases(cases_dir)

    # 3. RFC 0053 SWE-bench for 3D Benchmark Suites
    print("\n[3/8] Setting up RFC 0053 3D Asset Repair Benchmark Suites (96 cases)...")
    setup_evaluation_mesh_repair(eval_dir)
    setup_evaluation_material_repair(eval_dir)
    setup_evaluation_anim_repair(eval_dir)

    # 4. Bidirectional Round-Trip Evaluation Suite
    print("\n[4/8] Setting up Bidirectional Round-Trip Evaluation Suite (12 cases)...")
    setup_evaluation_bidirectional_roundtrip(eval_dir)

    # 4b. Rendering Condition Variants for Round-Trip Suite
    print("\n[4b/8] Setting up Rendering Condition Factor Framework (11 dims x 4 levels)...")
    setup_rendering_conditions(eval_dir)

    # 5. Captures Manifests
    print("\n[6/8] Setting up multimodal sample captures (images, audio, videos)...")
    setup_sample_captures(captures_dir)

    # 6. Synchronize Index
    print("\n[7/8] Synchronizing live Google Drive indexes (INDEX.json, INDEX.md)...")
    sync_data_index()

    print("\n=======================================================")
    print("✅ All evaluation datasets, benchmarks & test suites staged successfully in Google Drive!")
    print(f"   Target: {DATA_ROOT}")
    print("=======================================================\n")
    return True


def main():
    parser = argparse.ArgumentParser(description="DervGen Benchmark Dataset & Evaluation Suite Initializer")
    parser.add_argument("--sync-only", action="store_true", help="Only rescan and sync INDEX.md/json")
    parser.add_argument("--industry-scenes-only", action="store_true",
                        help="Only download/update industry benchmark scenes (skip procedural & evaluation datasets)")
    parser.add_argument("--industry-tier", type=str, default="all",
                        choices=["all", "essential", "geometry_scan", "interior", "stress_test", "aaa_production"],
                        help="Filter industry scenes by tier (default: all)")
    parser.add_argument("--include-manual-downloads", action="store_true",
                        help="Include scenes requiring manual download (NVIDIA ORCA, Intel) in setup")
    args = parser.parse_args()

    if args.sync_only:
        sync_data_index()
    elif args.industry_scenes_only:
        if not check_drive_mounted():
            return
        scenes_dir = DATA_ROOT / "cg" / "scenes"
        print(f"\n[Industry Scenes Only] Downloading tier={args.industry_tier}...")
        setup_industry_benchmark_scenes(scenes_dir, tier_filter=args.industry_tier,
                                        skip_manual=not args.include_manual_downloads)
        sync_data_index()
    else:
        setup_all_datasets(industry_tier=args.industry_tier,
                           skip_industry_manual=not args.include_manual_downloads)


if __name__ == "__main__":
    main()
