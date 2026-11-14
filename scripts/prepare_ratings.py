#!/usr/bin/env python3
"""Create blinded rating cards and independent, empty rating forms."""

import csv
import json
import random
from pathlib import Path

from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[1]
ARTIFACTS = ROOT / "outputs/pilot_artifacts"
PACKET = ARTIFACTS / "rating_packet"


def read_rows(name):
    path = ARTIFACTS / name
    return [json.loads(x) for x in path.read_text().splitlines()] if path.exists() else []


def write_csv(path, fields, rows):
    with path.open("w", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def card(source, candidate, instruction, case_id, target):
    canvas = Image.new("RGB", (1050, 585), "white")
    draw = ImageDraw.Draw(canvas)
    draw.text((12, 8), f"{case_id}: {instruction[:125]}", fill="black")
    for x, path, label in ((12, source, "SOURCE"), (538, candidate, "CANDIDATE")):
        image = Image.open(path).convert("RGB")
        image.thumbnail((500, 500))
        canvas.paste(image, (x, 58))
        draw.text((x, 563), label, fill="black")
    canvas.save(target)


def main():
    PACKET.mkdir(parents=True, exist_ok=True)
    with (ROOT / "pilot/manifest.csv").open(newline="") as stream:
        tasks = list(csv.DictReader(stream))
    first = {r["task_id"]: r for r in read_rows("first_outputs.jsonl") if r["status"] == "ok"}
    repairs = {r["task_id"]: r for r in read_rows("repair_outputs.jsonl")
               if r.get("stage") == "repair" and r["status"] == "ok"}
    candidates = []
    for task in tasks:
        task_id = task["task_id"]
        if task_id not in first:
            continue
        candidates.append((task, "first", first[task_id]["output_image"]))
        if task_id in repairs:
            candidates.append((task, "repair", repairs[task_id]["output_image"]))
    random.Random(2026).shuffle(candidates)
    key = []
    for index, (task, stage, path) in enumerate(candidates, 1):
        case_id = f"C{index:03d}"
        key.append({"case_id": case_id, "task_id": task["task_id"], "stage": stage,
                    "candidate_path": path})
        card(ROOT / task["source_path"], ROOT / path, task["instruction"], case_id,
             PACKET / f"{case_id}.jpg")
    write_csv(ARTIFACTS / "rating_key.csv", ["case_id", "task_id", "stage", "candidate_path"], key)
    fields = ["rater_id", "case_id", "requested_change", "preservation", "usability", "notes"]
    for rater in (1, 2):
        order = list(key)
        random.Random(2026 + rater).shuffle(order)
        write_csv(PACKET / f"rater_{rater}.csv", fields,
                  [{"rater_id": f"rater_{rater}", "case_id": row["case_id"],
                    "requested_change": "", "preservation": "", "usability": "", "notes": ""}
                   for row in order])
    (PACKET / "README.md").write_text(
        "# Blind image ratings\n\n"
        "Each C-number JPG shows the source, the instruction, and one edited candidate. "
        "Rate each candidate independently. Fill requested_change, preservation, and usability "
        "with 1 (yes) or 0 (no). Do not look at rating_key.csv until both forms are complete. "
        "Rater 1 and rater 2 should be different people; at least one must not be the output runner. "
        "Send the completed CSVs back for consolidation. If any component disagrees, a third "
        "person rates that candidate without seeing prior votes.\n")
    print(f"Prepared {len(key)} blinded candidates and two independent rating forms", flush=True)


if __name__ == "__main__":
    main()
