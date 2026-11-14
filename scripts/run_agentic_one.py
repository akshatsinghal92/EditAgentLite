#!/usr/bin/env python3
"""Run a one-task Qwen route -> edit -> failure review -> one repair loop."""

import argparse
import csv
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
QWEN_PY = ROOT / ".venv-qwen/bin/python"
BAGEL_PY = ROOT / ".venv-bagel/bin/python"


def run(command):
    print("+", " ".join(map(str, command)), flush=True)
    subprocess.run(command, cwd=ROOT, check=True)


def load_record(path):
    return json.loads((ROOT / path).read_text())


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--task-id", default="removal_0088_0")
    parser.add_argument("--seed", type=int, default=2026)
    parser.add_argument("--steps", type=int, default=30)
    parser.add_argument("--max-new-tokens", type=int, default=768)
    parser.add_argument("--reuse-route", action="store_true",
                        help="Use an already saved route decision")
    parser.add_argument("--reuse-review", action="store_true",
                        help="Use an already saved first review")
    args = parser.parse_args()
    with (ROOT / "pilot/manifest.csv").open(newline="") as handle:
        task = next(row for row in csv.DictReader(handle) if row["task_id"] == args.task_id)

    trace_dir = Path("outputs/pilot") / args.task_id / "agent"
    trace_dir.mkdir(parents=True, exist_ok=True)
    route_path = str(trace_dir / "route.json")
    if not (args.reuse_route and (ROOT / route_path).exists()):
        run([str(QWEN_PY), "scripts/qwen_decide.py", "--mode", "route",
             "--task-id", args.task_id, "--output", route_path,
             "--max-new-tokens", str(args.max_new_tokens)])
    route = load_record(route_path)["decision"]["route"]
    allowed = {"removal": {"inpaint", "bagel"}, "lighting": {"tool", "bagel"}}
    if route not in allowed[task["category"]]:
        raise ValueError(f"Qwen chose unsupported route {route!r} for {task['category']}")

    first_route_path = str(trace_dir / "first_route.txt")
    (ROOT / first_route_path).write_text(route + "\n")
    run([str(BAGEL_PY if route == "bagel" else QWEN_PY),
         "scripts/run_pilot.py", "--task-id", args.task_id, "--route", route,
         "--seed", str(args.seed), "--steps", str(args.steps), "--run-id", "first"])
    first_image = str(Path("outputs/pilot") / args.task_id / route / "first" / "edited.png")
    review_path = str(trace_dir / "review_first.json")
    if not (args.reuse_review and (ROOT / review_path).exists()):
        run([str(QWEN_PY), "scripts/qwen_decide.py", "--mode", "review",
             "--task-id", args.task_id, "--edited-image", first_image,
             "--output", review_path, "--max-new-tokens", str(args.max_new_tokens)])
    review = load_record(review_path)["decision"]

    final_route = route
    repair_attempted = False
    repair_trigger = None
    if review.get("label") != "pass":
        repair_trigger = "Qwen returned a non-pass failure label"
        if review.get("repair_action") != "bagel":
            repair_trigger += "; controller fallback routes failed edits to BAGEL"
        final_route = "bagel"
        repair_attempted = True
        repair_instruction = review.get("repair_instruction") or task["instruction"]
        run([str(BAGEL_PY), "scripts/run_pilot.py", "--task-id", args.task_id,
             "--route", "bagel", "--seed", str(args.seed), "--steps", str(args.steps),
             "--instruction", repair_instruction, "--run-id", "repair"])
        repair_image = str(Path("outputs/pilot") / args.task_id / "bagel" / "repair" / "edited.png")
        repair_review_path = str(trace_dir / "review_repair.json")
        run([str(QWEN_PY), "scripts/qwen_decide.py", "--mode", "review",
             "--task-id", args.task_id, "--edited-image", repair_image,
             "--output", repair_review_path,
             "--max-new-tokens", str(args.max_new_tokens)])
        final_review = load_record(repair_review_path)["decision"]
    else:
        final_review = review

    trace = {
        "task_id": args.task_id,
        "instruction": task["instruction"],
        "first_route": route,
        "first_review": review,
        "repair_attempted": repair_attempted,
        "repair_trigger": repair_trigger,
        "final_route": final_route,
        "final_review": final_review,
        "route_record": route_path,
        "first_review_record": review_path,
    }
    (ROOT / trace_dir / "trace.json").write_text(json.dumps(trace, indent=2) + "\n")
    print(json.dumps(trace, indent=2))


if __name__ == "__main__":
    main()
