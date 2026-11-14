#!/usr/bin/env python3
"""Run the frozen midterm first actions and append one JSONL row per task."""

import argparse
import csv
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ARTIFACTS = ROOT / "outputs/pilot_artifacts"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--task-id", help="Run one manifest task; default is all eight")
    parser.add_argument("--steps", type=int, default=30)
    parser.add_argument("--resume", action="store_true", help="Reuse saved first images without overwriting")
    args = parser.parse_args()
    with (ROOT / "pilot/manifest.csv").open(newline="") as stream:
        tasks = list(csv.DictReader(stream))
    if args.task_id:
        tasks = [row for row in tasks if row["task_id"] == args.task_id]
        if not tasks:
            parser.error("task ID is absent from the frozen manifest")
    ARTIFACTS.mkdir(parents=True, exist_ok=True)
    log_path = ARTIFACTS / "first_outputs.jsonl"
    done = {}
    if log_path.exists():
        for line in log_path.read_text().splitlines():
            row = json.loads(line)
            done[row["task_id"]] = row
    for task in tasks:
        task_id = task["task_id"]
        route = "bagel" if task["category"] == "removal" else "tool"
        image = ROOT / "outputs/pilot" / task_id / route / "first" / "edited.png"
        if task_id in done and args.resume and image.is_file():
            print(f"reuse {task_id}: {image.relative_to(ROOT)}", flush=True)
            continue
        if image.exists():
            raise FileExistsError(f"Frozen first output exists: {image}. Use --resume.")
        python = ROOT / (".venv-bagel/bin/python" if route == "bagel" else ".venv-qwen/bin/python")
        command = [str(python), "scripts/run_pilot.py", "--task-id", task_id,
                   "--route", route, "--run-id", "first", "--steps", str(args.steps)]
        result = subprocess.run(command, cwd=ROOT, text=True, capture_output=True)
        record_path = image.parent / "run.json"
        record = json.loads(record_path.read_text()) if result.returncode == 0 and record_path.exists() else {}
        row = {"task_id": task_id, "stage": "first", "tool_or_model": route,
               "model_revision": "5019f57d168e5816e8f3f701b17cc816bb7cf24b" if route == "bagel" else "Pillow",
               "seed": 2026, "input_image": task["source_path"],
               "output_image": str(image.relative_to(ROOT)) if image.exists() else None,
               "elapsed_seconds": record.get("elapsed_seconds"),
               "load_seconds": record.get("load_seconds"),
               "peak_gpu_bytes": record.get("peak_gpu_bytes"),
               "status": "ok" if result.returncode == 0 and image.exists() else "execution_failed",
               "error": result.stderr[-2000:] if result.returncode else None}
        with log_path.open("a") as stream:
            stream.write(json.dumps(row) + "\n")
        print(json.dumps(row), flush=True)
        if row["status"] != "ok":
            sys.exit(1)


if __name__ == "__main__":
    main()
