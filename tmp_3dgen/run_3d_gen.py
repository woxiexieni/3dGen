# -*- coding: utf-8 -*-
"""Compress local photo and submit image-to-3D job via buddy-cloud internals.

Usage:
  python run_3d_gen.py <photo_path> <resized_output> <max_bytes>
Token comes from stdin (first line).
Polls until done, prints JSON result to stdout.
"""
import sys
import os
import io
import json
import base64

SKILL_DIR = r"D:\software\WorkBuddy\resources\app.asar.unpacked\resources\builtin-skills\buddy-multimodal-generation\scripts"
sys.path.insert(0, SKILL_DIR)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import importlib.util
_spec = importlib.util.spec_from_file_location(
    "buddy_cloud", os.path.join(SKILL_DIR, "buddy-cloud.py"))
bc = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(bc)
from PIL import Image  # noqa: E402

MAX_DIM = 2000  # long side cap, service allows up to 5000px


def compress(src: str, dst: str, max_bytes: int) -> int:
    """Resize + re-encode JPEG until under max_bytes. Returns final size."""
    img = Image.open(src)
    # fix EXIF orientation
    try:
        from PIL import ImageOps
        img = ImageOps.exif_transpose(img)
    except Exception:
        pass
    w, h = img.size
    scale = min(1.0, MAX_DIM / max(w, h))
    if scale < 1.0:
        img = img.resize((int(w * scale), int(h * scale)), Image.LANCZOS)
    img = img.convert("RGB")
    q = 90
    while q >= 40:
        img.save(dst, "JPEG", quality=q, optimize=True)
        if os.path.getsize(dst) <= max_bytes:
            return os.path.getsize(dst)
        q -= 10
    return os.path.getsize(dst)


def main():
    photo, resized, max_bytes = sys.argv[1], sys.argv[2], int(sys.argv[3])
    token = sys.stdin.readline().strip()
    if not token:
        print(json.dumps({"error": "NO_TOKEN"}))
        sys.exit(1)

    size = compress(photo, resized, max_bytes)
    print(f"[INFO] resized image: {resized} ({size} bytes)", file=sys.stderr)

    with open(resized, "rb") as f:
        b64 = base64.b64encode(f.read()).decode()

    cfg = bc._PROVIDER_MAP["3d"]
    body = bc._build_3d_body(
        model="3.1",
        image_base64=b64,
        generate_type="Normal",
        result_format="STL",
    )

    resp = bc._call_api(
        bc._DEFAULT_ENDPOINT, cfg["provider"], cfg["service"], cfg["version"],
        cfg["submit_action"], body, token,
    )
    job_id = resp.get("JobId")
    if not job_id:
        print(json.dumps({"error": "NO_JOB_ID", "raw": resp}, ensure_ascii=False))
        sys.exit(1)
    print(f"[INFO] job submitted: {job_id}", file=sys.stderr)

    result = bc._poll_job(
        bc._DEFAULT_ENDPOINT, cfg["provider"], cfg["service"], cfg["version"],
        cfg["query_action"], job_id, token, 5, 600,
    )
    bc._ACTIVE_TOKEN = token
    bc._safe_print_json(bc._format_output(result, job_id=job_id))


if __name__ == "__main__":
    main()
