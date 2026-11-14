#!/usr/bin/env python3
"""Check eight frozen edits with Qwen; attempt at most two valid repairs."""

import argparse
import csv
import json
import shutil
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ARTIFACTS = ROOT / "outputs/pilot_artifacts"
LABELS = {"pass", "incomplete_edit", "wrong_target", "unwanted_change",
          "wrong_strength", "artifact", "uncertain"}


def read_rows(path):
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()] if path.exists() else []


def append(path, row):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a") as stream:
        stream.write(json.dumps(row) + "\n")


def check(task, first_row):
    task_id = task["task_id"]
    image = first_row["output_image"]
    if not image or not (ROOT / image).is_file():
        raise FileNotFoundError(f"Frozen first output missing: {image}")
    agent_dir = ROOT / "outputs/pilot" / task_id / "agent"
    agent_dir.mkdir(parents=True, exist_ok=True)
    attempts = []
    record = None
    for number in (1, 2):
        target = agent_dir / f"midterm_check_attempt{number}.json"
        command = [str(ROOT / ".venv-qwen/bin/python"), "scripts/qwen_decide.py",
                   "--mode", "review", "--task-id", task_id, "--edited-image", image,
                   "--output", str(target.relative_to(ROOT))]
        result = subprocess.run(command, cwd=ROOT, capture_output=True, text=True)
        record = json.loads(target.read_text()) if result.returncode == 0 and target.exists() else None
        decision = record.get("decision") if record else None
        valid = isinstance(decision, dict) and decision.get("label") in LABELS
        attempts.append({"record": str(target.relative_to(ROOT)) if record else None,
                         "status": "ok" if valid else "parse_failed" if record else "execution_failed",
                         "error": record.get("parse_error") if record else result.stderr[-2000:],
                         "load_seconds": record.get("load_seconds") if record else None,
                         "elapsed_seconds": record.get("inference_seconds") if record else None,
                         "peak_gpu_bytes": record.get("peak_gpu_bytes") if record else None})
        if valid or result.returncode:
            break
    if record:
        shutil.copyfile(target, agent_dir / "midterm_check.json")
    decision = record.get("decision") if record else None
    status = "ok" if isinstance(decision, dict) and decision.get("label") in LABELS else attempts[-1]["status"]
    row = {"task_id": task_id, "stage": "check", "tool_or_model": "Qwen3-VL-4B-Thinking",
           "model_revision": "1de27d8c51f12e819435303b9e84c4e25ba8401e", "seed": 2026,
           "input_image": task["source_path"], "output_image": image,
           "elapsed_seconds": sum(a["elapsed_seconds"] or 0 for a in attempts),
           "load_seconds": sum(a["load_seconds"] or 0 for a in attempts),
           "peak_gpu_bytes": max((a["peak_gpu_bytes"] or 0 for a in attempts), default=0),
           "status": status, "error": attempts[-1]["error"] if status != "ok" else None,
           "decision_record": str((agent_dir / "midterm_check.json").relative_to(ROOT)) if record else None,
           "decision": decision, "attempts": attempts}
    append(ARTIFACTS / "checks.jsonl", row)
    print(json.dumps({"task_id": task_id, "check_status": status,
                      "label": decision.get("label") if isinstance(decision, dict) else None}), flush=True)
    return row


def repair_spec(task, decision):
    if task["category"] == "removal":
        instruction = decision.get("repair_instruction")
        if decision.get("repair_action") == "bagel" and isinstance(instruction, str) and instruction.strip():
            return {"route": "bagel", "instruction": instruction.strip()}
    elif task["category"] == "lighting" and decision.get("repair_action") == "tool":
        try:
            factor = float(decision.get("brightness_factor"))
        except (TypeError, ValueError):
            return None
        if 0.5 <= factor <= 2.0 and abs(factor - 1.25) >= 0.03:
            return {"route": "tool", "brightness_factor": factor}
    return None


def do_repair(task, spec, steps):
    task_id = task["task_id"]
    route = spec["route"]
    image = ROOT / "outputs/pilot" / task_id / route / "repair/edited.png"
    if image.exists():
        raise FileExistsError(f"Repair output already exists: {image}")
    python = ROOT / (".venv-bagel/bin/python" if route == "bagel" else ".venv-qwen/bin/python")
    command = [str(python), "scripts/run_pilot.py", "--task-id", task_id, "--route", route,
               "--run-id", "repair", "--seed", "2026", "--steps", str(steps)]
    command += (["--instruction", spec["instruction"]] if route == "bagel"
                else ["--brightness", str(spec["brightness_factor"])])
    result = subprocess.run(command, cwd=ROOT, text=True, capture_output=True)
    record_path = image.parent / "run.json"
    record = json.loads(record_path.read_text()) if result.returncode == 0 and record_path.exists() else {}
    row = {"task_id": task_id, "stage": "repair", "tool_or_model": route,
           "model_revision": record.get("model_revision"), "seed": 2026,
           "input_image": task["source_path"],
           "output_image": str(image.relative_to(ROOT)) if image.exists() else None,
           "repair_spec": spec, "elapsed_seconds": record.get("elapsed_seconds"),
           "load_seconds": record.get("load_seconds"), "peak_gpu_bytes": record.get("peak_gpu_bytes"),
           "status": "ok" if result.returncode == 0 and image.exists() else "execution_failed",
           "error": result.stderr[-2000:] if result.returncode else None}
    append(ARTIFACTS / "repair_outputs.jsonl", row)
    print(json.dumps({"task_id": task_id, "repair_status": row["status"], "route": route}), flush=True)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--task-id", help="Check one task; default is all completed first outputs")
    parser.add_argument("--max-repairs", type=int, default=0)
    parser.add_argument("--steps", type=int, default=30)
    args = parser.parse_args()
    if not 0 <= args.max_repairs <= 2:
        parser.error("max repairs must be 0, 1, or 2")
    first_path = ARTIFACTS / "first_outputs.jsonl"
    if not first_path.exists():
        parser.error(f"Missing frozen first-output log: {first_path}")
    first = {row["task_id"]: row for row in read_rows(first_path)}
    with (ROOT / "pilot/manifest.csv").open(newline="") as stream:
        tasks = list(csv.DictReader(stream))
    checks = {row["task_id"]: row for row in read_rows(ARTIFACTS / "checks.jsonl")}
    repair_rows = read_rows(ARTIFACTS / "repair_outputs.jsonl")
    attempted = sum(row.get("stage") == "repair" for row in repair_rows)
    skipped = {row["task_id"] for row in repair_rows if row.get("status") == "unsupported_repair"}
    for task in tasks:
        task_id = task["task_id"]
        if args.task_id and task_id != args.task_id:
            continue
        first_row = first.get(task_id)
        if not first_row or first_row["status"] != "ok":
            continue
        check_row = checks.get(task_id) or check(task, first_row)
        decision = check_row.get("decision")
        if args.max_repairs == 0 or check_row["status"] != "ok" or decision["label"] == "pass":
            continue
        if task_id in skipped or any(row.get("task_id") == task_id and row.get("stage") == "repair" for row in repair_rows):
            continue
        if attempted >= args.max_repairs:
            continue
        spec = repair_spec(task, decision)
        if spec is None:
            row = {"task_id": task_id, "status": "unsupported_repair",
                   "reason": "Qwen did not provide a valid category-specific repair", "decision": decision}
            append(ARTIFACTS / "repair_outputs.jsonl", row)
            repair_rows.append(row)
            skipped.add(task_id)
            continue
        do_repair(task, spec, args.steps)
        attempted += 1


if __name__ == "__main__":
    main()
