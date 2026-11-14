#!/usr/bin/env python3
"""Freeze completed first edits with a manifest copy, image hashes, and contact sheet."""

import csv
import hashlib
import json
import shutil
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
ARTIFACTS = ROOT / "outputs/pilot_artifacts"


def sha256(path):
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main():
    with (ROOT / "pilot/manifest.csv").open(newline="") as stream:
        tasks = list(csv.DictReader(stream))
    log_path = ARTIFACTS / "first_outputs.jsonl"
    rows = {}
    for line in log_path.read_text().splitlines():
        row = json.loads(line)
        rows[row["task_id"]] = row
    missing = [task["task_id"] for task in tasks if task["task_id"] not in rows]
    if missing:
        raise RuntimeError(f"No first-output log row for: {', '.join(missing)}")
    shutil.copyfile(ROOT / "pilot/manifest.csv", ARTIFACTS / "manifest_snapshot.csv")
    cell = 350
    label_height = 50
    sheet = Image.new("RGB", (cell * 4, (cell + label_height) * 4), "white")
    draw = ImageDraw.Draw(sheet)
    hashes = []
    for index, task in enumerate(tasks):
        row = rows[task["task_id"]]
        source = ROOT / task["source_path"]
        output = ROOT / row["output_image"] if row.get("output_image") else None
        for side, path in enumerate((source, output)):
            x = (index % 2) * 2 * cell + side * cell
            y = (index // 2) * (cell + label_height)
            if path and path.is_file():
                image = Image.open(path).convert("RGB")
                image.thumbnail((cell, cell))
                sheet.paste(image, (x + (cell - image.width) // 2, y + (cell - image.height) // 2))
                hashes.append(f"{sha256(path)}  {path.relative_to(ROOT)}")
            label = f"{task['task_id']} {'source' if side == 0 else row['status']}"
            draw.text((x + 6, y + cell + 8), label, fill="black")
    sheet.save(ARTIFACTS / "first_contact_sheet.jpg", quality=90)
    (ARTIFACTS / "first_checksums.sha256").write_text("\n".join(hashes) + "\n")
    print(f"Frozen {len(tasks)} manifest tasks; {len(hashes)} source/output files hashed")


if __name__ == "__main__":
    main()
