#!/usr/bin/env python3
"""Check frozen first outputs with Qwen; optionally try bounded removal repairs."""

import argparse
import csv
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ARTIFACTS = ROOT / "outputs/pilot_artifacts"


def append(path, row):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a") as stream:
        stream.write(json.dumps(row) + "\n")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--task-id", help="Check one task; default is all completed first outputs")
    parser.add_argument("--max-repairs", type=int, default=0,
                        help="Stage A smoke test uses 0; Stage C may use at most 2")
    parser.add_argument("--steps", type=int, default=30)
    args = parser.parse_args()
    if not 0 <= args.max_repairs <= 2:
        parser.error("max repairs must be 0, 1, or 2")
    first_log = ARTIFACTS / "first_outputs.jsonl"
    if not first_log.exists():
        parser.error(f"Missing frozen first-output log: {first_log}")
    first = {row["task_id"]: row for row in map(json.loads, first_log.read_text().splitlines())}
    with (ROOT / "pilot/manifest.csv").open(newline="") as stream:
        tasks = list(csv.DictReader(stream))
    checks_path = ARTIFACTS / "checks.jsonl"
    repairs_path = ARTIFACTS / "repair_outputs.jsonl"
    checked = {row["task_id"] for row in map(json.loads, checks_path.read_text().splitlines())} if checks_path.exists() else set()
    repairs = sum(1 for row in map(json.loads, repairs_path.read_text().splitlines()) if row.get("status") == "ok") if repairs_path.exists() else 0
    for task in tasks:
        task_id = task["task_id"]
        if args.task_id and task_id != args.task_id:
            continue
        first_row = first.get(task_id)
        if not first_row or first_row["status"] != "ok":
            continue
        if task_id in checked:
            print(f"reuse check {task_id}", flush=True)
            continue
        image = first_row["output_image"]
        if not image or not (ROOT / image).is_file():
            raise FileNotFoundError(f"Frozen output missing: {image}")
        decision_path = f"outputs/pilot/{task_id}/agent/midterm_check.json"
        command = [str(ROOT / ".venv-qwen/bin/python"), "scripts/qwen_decide.py",
                   "--mode", "review", "--task-id", task_id,
                   "--edited-image", image, "--output", decision_path]
        result = subprocess.run(command, cwd=ROOT, text=True, capture_output=True)
        decision_record = json.loads((ROOT / decision_path).read_text()) if result.returncode == 0 else {}
        decision = decision_record.get("decision", {})
        append(checks_path, {"task_id": task_id, "stage": "check", "tool_or_model": "Qwen3-VL-4B-Thinking",
                             "model_revision": "1de27d8c51f12e819435303b9e84c4e25ba8401e", "seed": 2026,
                             "input_image": task["source_path"], "output_image": image,
                             "elapsed_seconds": decision_record.get("inference_seconds"),
                             "load_seconds": decision_record.get("load_seconds"),
                             "peak_gpu_bytes": decision_record.get("peak_gpu_bytes"),
                             "status": "ok" if result.returncode == 0 else "execution_failed",
                             "error": result.stderr[-2000:] if result.returncode else None,
                             "decision_record": decision_path if decision_record else None,
                             "decision": decision})
        if result.returncode:
            sys.exit(1)
        if args.max_repairs == 0 or decision.get("label") == "pass":
            continue
        if task["category"] != "removal" or decision.get("repair_action") != "bagel":
            append(repairs_path, {"task_id": task_id, "status": "unsupported_repair",
                                  "reason": "Only BAGEL removal repair is implemented in this handoff"})
            continue
        if repairs >= args.max_repairs:
            continue
        repair_image = ROOT / "outputs/pilot" / task_id / "bagel/repair/edited.png"
        if repair_image.exists():
            raise FileExistsError(f"Repair output already exists: {repair_image}")
        instruction = decision.get("repair_instruction") or task["instruction"]
        command = [str(ROOT / ".venv-bagel/bin/python"), "scripts/run_pilot.py", "--task-id", task_id,
                   "--route", "bagel", "--run-id", "repair", "--steps", str(args.steps),
                   "--instruction", instruction]
        result = subprocess.run(command, cwd=ROOT, text=True, capture_output=True)
        record_path = repair_image.parent / "run.json"
        record = json.loads(record_path.read_text()) if result.returncode == 0 and record_path.exists() else {}
        append(repairs_path, {"task_id": task_id, "stage": "repair", "tool_or_model": "BAGEL-7B-MoT",
                              "model_revision": "5019f57d168e5816e8f3f701b17cc816bb7cf24b", "seed": 2026,
                              "input_image": task["source_path"],
                              "output_image": str(repair_image.relative_to(ROOT)) if repair_image.exists() else None,
                              "instruction": instruction, "elapsed_seconds": record.get("elapsed_seconds"),
                              "load_seconds": record.get("load_seconds"),
                              "peak_gpu_bytes": record.get("peak_gpu_bytes"),
                              "status": "ok" if result.returncode == 0 and repair_image.exists() else "execution_failed",
                              "error": result.stderr[-2000:] if result.returncode else None})
        if result.returncode:
            sys.exit(1)
        repairs += 1


if __name__ == "__main__":
    main()
