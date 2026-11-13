#!/usr/bin/env python3
"""Run one seeded pilot edit using either the cheap tool or BAGEL."""

import argparse
import csv
import json
import sys
import time
from pathlib import Path

from PIL import Image, ImageEnhance

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--task-id", required=True)
    parser.add_argument("--route", choices=["tool", "inpaint", "bagel"], required=True)
    parser.add_argument("--seed", type=int, default=2026)
    parser.add_argument("--steps", type=int, default=30)
    parser.add_argument("--brightness", type=float, default=1.25)
    parser.add_argument("--contrast", type=float, default=1.0)
    args = parser.parse_args()
    with (ROOT / "pilot/manifest.csv").open(newline="") as handle:
        rows = {row["task_id"]: row for row in csv.DictReader(handle)}
    task = rows[args.task_id]
    source = Image.open(ROOT / task["source_path"]).convert("RGB")
    out_dir = ROOT / "outputs/pilot" / args.task_id / args.route
    out_dir.mkdir(parents=True, exist_ok=True)
    start = time.monotonic()
    load_seconds = 0.0
    peak_gpu_bytes = None
    if args.route == "tool":
        if task["category"] != "lighting":
            raise ValueError("Brightness tool is only valid for global lighting tasks")
        if not 0.5 <= args.brightness <= 2.0 or not 0.5 <= args.contrast <= 2.0:
            raise ValueError("Tool factors must lie in [0.5, 2.0]")
        result = ImageEnhance.Brightness(source).enhance(args.brightness)
        result = ImageEnhance.Contrast(result).enhance(args.contrast)
        method = f"Pillow brightness={args.brightness}, contrast={args.contrast}"
    elif args.route == "inpaint":
        if task["category"] != "removal":
            raise ValueError("Inpainting tool is only valid for removal tasks")
        import cv2
        import numpy as np
        from PIL import ImageDraw

        polygons = json.loads((ROOT / "pilot/removal_masks.json").read_text())
        mask = Image.new("L", source.size, 0)
        ImageDraw.Draw(mask).polygon([tuple(p) for p in polygons[args.task_id]], fill=255)
        mask.save(out_dir / "human_mask.png")
        rgb = np.asarray(source)
        result = Image.fromarray(cv2.inpaint(rgb, np.asarray(mask), 3, cv2.INPAINT_TELEA))
        method = "OpenCV Telea inpainting, human polygon mask, radius=3"
    else:
        bagel_path = ROOT / "external/Bagel"
        sys.path.insert(0, str(bagel_path))
        sys.argv = ["app.py", "--mode", "2", "--model_path", str(ROOT / "models/BAGEL-7B-MoT")]
        import app as bagel

        load_seconds = time.monotonic() - start
        start = time.monotonic()
        result, _ = bagel.edit_image(source, task["instruction"], seed=args.seed, num_timesteps=args.steps)
        method = f"BAGEL-7B-MoT NF4, {args.steps} timesteps"
        import torch
        peak_gpu_bytes = torch.cuda.max_memory_allocated()
    elapsed = time.monotonic() - start
    result.save(out_dir / "edited.png")
    record = {
        "task_id": args.task_id,
        "instruction": task["instruction"],
        "route": args.route,
        "method": method,
        "seed": args.seed,
        "elapsed_seconds": round(elapsed, 2),
        "load_seconds": round(load_seconds, 2),
        "peak_gpu_bytes": peak_gpu_bytes,
        "source": task["source_path"],
        "edited": str((out_dir / "edited.png").relative_to(ROOT)),
    }
    (out_dir / "run.json").write_text(json.dumps(record, indent=2) + "\n")
    print(json.dumps(record, indent=2))


if __name__ == "__main__":
    main()
