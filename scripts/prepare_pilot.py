#!/usr/bin/env python3
"""Freeze eight Complex-Edit atomic tasks before running either model."""

import csv
import json
import random
import re
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "complex_edit" / "real"
MANIFEST = ROOT / "pilot" / "manifest.csv"
BASE = "https://huggingface.co/datasets/UCSC-VLAA/Complex-Edit/resolve/main/test/real/"
SEED = 2026
SCREENED_OUT = {
    "removal_0287_1": "Named cup is not clearly visible on the desk.",
    "removal_0580_7": "Named bowl is ambiguous in the source image.",
    "removal_1007_5": "Named dish rack is ambiguous in the source image.",
}

REMOVAL = re.compile(r"^Remove (the|a|an) [^.]+\.$", re.I)
LIGHTING = re.compile(
    r"^(Brighten (the image|the scene|the overall lighting|the lighting|up the image|up the scene)"
    r"|Dim (the image|the scene|the lighting|the overall lighting)"
    r"|Increase (the overall brightness|the brightness|the ambient lighting)"
    r"|Decrease (the overall brightness|the brightness|the lighting)"
    r"|Enhance the overall brightness)[^.]*\.$",
    re.I,
)
REMOVAL_EXCLUDE = re.compile(r"\b(all|every|two|three|several|multiple|clutter|background|entire|whole)\b", re.I)
LIGHTING_EXCLUDE = re.compile(
    r"\b(and|to create|to simulate|warm|cool|sunset|daylight|spotlight|highlight|golden|neon|local|around|tinge|orange|blue|mood|evening|night)\b",
    re.I,
)


def download(url: str, target: Path) -> None:
    if target.exists():
        return
    target.parent.mkdir(parents=True, exist_ok=True)
    urllib.request.urlretrieve(url, target)


def main() -> None:
    metadata = DATA / "metadata.jsonl"
    download(BASE + "metadata.jsonl", metadata)
    candidates = {"removal": [], "lighting": []}
    with metadata.open() as stream:
        for line in stream:
            row = json.loads(line)
            for index, edit in enumerate(row["edit"]["sequence"]):
                instruction = edit["instruction"]
                category = None
                if edit["name"] == "Remove an Object" and REMOVAL.fullmatch(instruction) and not REMOVAL_EXCLUDE.search(instruction):
                    category = "removal"
                elif edit["name"] == "Adjust Lighting" and LIGHTING.fullmatch(instruction) and not LIGHTING_EXCLUDE.search(instruction):
                    category = "lighting"
                if category:
                    candidates[category].append((row["file_name"], index, instruction))

    tasks = []
    exclusions = []
    for category in ("removal", "lighting"):
        pool = sorted(candidates[category])
        if len(pool) < 4:
            raise RuntimeError(f"Only {len(pool)} eligible {category} tasks")
        selected = []
        for file_name, index, instruction in random.Random(SEED).sample(pool, len(pool)):
            image_id = Path(file_name).stem
            task_id = f"{category}_{image_id}_{index}"
            if task_id in SCREENED_OUT:
                exclusions.append({"task_id": task_id, "reason": SCREENED_OUT[task_id]})
                continue
            selected.append((file_name, index, instruction))
            if len(selected) == 4:
                break
        for file_name, index, instruction in sorted(selected):
            image_id = Path(file_name).stem
            source = DATA / file_name
            download(BASE + file_name, source)
            tasks.append({
                "task_id": f"{category}_{image_id}_{index}",
                "source_id": image_id,
                "instruction_index": index,
                "category": category,
                "instruction": instruction,
                "source_path": str(source.relative_to(ROOT)),
                "selection_seed": SEED,
            })

    MANIFEST.parent.mkdir(parents=True, exist_ok=True)
    if MANIFEST.exists():
        raise FileExistsError(f"{MANIFEST} exists; task selection is frozen")
    with MANIFEST.open("w", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(tasks[0]), lineterminator="\n")
        writer.writeheader()
        writer.writerows(tasks)
    with (MANIFEST.parent / "screening_log.csv").open("w", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=["task_id", "reason"], lineterminator="\n")
        writer.writeheader()
        writer.writerows(exclusions)
    print(f"Wrote {len(tasks)} tasks to {MANIFEST}")
    for task in tasks:
        print(task["task_id"], task["instruction"])


if __name__ == "__main__":
    main()
