#!/usr/bin/env python3
"""Summarize measured pilot counts; leave human quality metrics pending until rated."""

import csv
import json
from collections import Counter
from pathlib import Path

from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[1]
ARTIFACTS = ROOT / "outputs/pilot_artifacts"


def rows(name):
    path = ARTIFACTS / name
    return [json.loads(x) for x in path.read_text().splitlines() if x.strip()] if path.exists() else []


def total(records, key):
    return round(sum(float(r.get(key) or 0) for r in records), 2)


def make_figure(first, checks, repairs):
    by_first = {r["task_id"]: r for r in first}
    selected = next((r for r in repairs if r.get("stage") == "repair" and r["status"] == "ok"), None)
    if selected is None:
        selected = next((r for r in checks if r.get("decision", {}).get("label") not in (None, "pass")), None)
    if selected is None:
        return None
    task_id = selected["task_id"]
    with (ROOT / "pilot/manifest.csv").open(newline="") as stream:
        task = next(r for r in csv.DictReader(stream) if r["task_id"] == task_id)
    paths = [("Source", ROOT / task["source_path"]),
             ("First edit", ROOT / by_first[task_id]["output_image"])]
    if selected.get("stage") == "repair":
        paths.append(("Repair", ROOT / selected["output_image"]))
    canvas = Image.new("RGB", (520 * len(paths), 590), "white")
    draw = ImageDraw.Draw(canvas)
    draw.text((10, 8), f"{task_id}: {task['instruction']}", fill="black")
    for index, (label, path) in enumerate(paths):
        image = Image.open(path).convert("RGB")
        image.thumbnail((500, 500))
        canvas.paste(image, (10 + 520 * index, 52))
        draw.text((10 + 520 * index, 563), label, fill="black")
    target = ARTIFACTS / "representative.png"
    canvas.save(target)
    return str(target.relative_to(ROOT))


def main():
    first = rows("first_outputs.jsonl")
    checks = rows("checks.jsonl")
    repairs = rows("repair_outputs.jsonl")
    check_ok = [r for r in checks if r["status"] == "ok"]
    attempted = [r for r in repairs if r.get("stage") == "repair"]
    labels = Counter(r["decision"]["label"] for r in check_ok)
    summary = {
        "first_completed": sum(r["status"] == "ok" for r in first),
        "first_execution_failed": sum(r["status"] != "ok" for r in first),
        "first_bagel_calls": sum(r["tool_or_model"] == "bagel" and r["status"] == "ok" for r in first),
        "first_tool_calls": sum(r["tool_or_model"] == "tool" and r["status"] == "ok" for r in first),
        "qwen_checked": len(check_ok), "qwen_check_attempts": sum(len(r.get("attempts", [])) for r in checks),
        "qwen_labels": dict(labels),
        "qwen_flagged": sum(label != "pass" for label, count in labels.items() for _ in range(count)),
        "repair_attempted": len(attempted), "repair_completed": sum(r["status"] == "ok" for r in attempted),
        "repair_routes": dict(Counter(r["tool_or_model"] for r in attempted)),
        "unsupported_repairs": sum(r.get("status") == "unsupported_repair" for r in repairs),
        "first_generation_seconds": total(first, "elapsed_seconds"),
        "first_model_load_seconds": total(first, "load_seconds"),
        "qwen_inference_seconds": total(checks, "elapsed_seconds"),
        "qwen_model_load_seconds": total(checks, "load_seconds"),
        "repair_generation_seconds": total(attempted, "elapsed_seconds"),
        "repair_model_load_seconds": total(attempted, "load_seconds"),
        "peak_gpu_bytes": max([r.get("peak_gpu_bytes") or 0 for r in first + checks + attempted], default=0),
        "human_first_full_success": None,
        "qwen_false_acceptances": None,
        "repair_improved_unchanged_worse": None,
        "human_ratings_status": "pending two independent team raters",
    }
    summary["representative_figure"] = make_figure(first, checks, repairs)
    (ARTIFACTS / "results_pending.json").write_text(json.dumps(summary, indent=2) + "\n")
    lines = ["# Midterm pilot measured results", "",
             f"First edits: {summary['first_completed']}/{len(first)} completed; "
             f"{summary['first_execution_failed']} execution failures.",
             f"Qwen checks: {summary['qwen_checked']}/{len(first)}; labels {summary['qwen_labels']}.",
             f"Repairs: {summary['repair_completed']}/{summary['repair_attempted']} completed; "
             f"routes {summary['repair_routes']}.",
             f"First BAGEL/tool calls: {summary['first_bagel_calls']}/{summary['first_tool_calls']}.",
             f"GPU peak allocated: {summary['peak_gpu_bytes'] / 1024**3:.2f} GiB.",
             "", "Human success, Qwen false acceptance, and repair improvement remain pending independent ratings."]
    (ARTIFACTS / "results_pending.md").write_text("\n".join(lines) + "\n")
    print(json.dumps(summary, indent=2), flush=True)


if __name__ == "__main__":
    main()
