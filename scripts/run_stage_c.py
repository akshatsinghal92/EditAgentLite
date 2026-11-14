#!/usr/bin/env python3
"""One-command Stage C runner with persistent logs and an eight-task progress bar."""

import csv
import json
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ARTIFACTS = ROOT / "outputs/pilot_artifacts"
PROGRESS = ARTIFACTS / "stage_c_progress.json"
PROGRESS_LOG = ARTIFACTS / "stage_c_progress.log"


def rows(name):
    path = ARTIFACTS / name
    return [json.loads(x) for x in path.read_text().splitlines() if x.strip()] if path.exists() else []


def update(state):
    with (ROOT / "pilot/manifest.csv").open(newline="") as stream:
        tasks = list(csv.DictReader(stream))
    checks = {r["task_id"]: r for r in rows("checks.jsonl")}
    repairs = [r for r in rows("repair_outputs.jsonl") if r.get("stage") == "repair"]
    complete = sum(task["task_id"] in checks for task in tasks)
    current = next((task["task_id"] for task in tasks if task["task_id"] not in checks), None)
    bar = "[" + "#" * complete + "." * (len(tasks) - complete) + "]"
    record = {"time_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
              "state": state, "progress": bar, "checks_recorded": complete,
              "checks_total": len(tasks), "current_or_next": current,
              "repairs_attempted": len(repairs),
              "repairs_completed": sum(r["status"] == "ok" for r in repairs)}
    PROGRESS.write_text(json.dumps(record, indent=2) + "\n")
    with PROGRESS_LOG.open("a") as stream:
        stream.write(f"{record['time_utc']} {bar} {complete}/{len(tasks)} {state} "
                     f"repairs={record['repairs_completed']}/{len(repairs)}\n")
    return record


def main():
    ARTIFACTS.mkdir(parents=True, exist_ok=True)
    update("starting")
    with (ARTIFACTS / "stage_c_run.log").open("a") as stream:
        process = subprocess.Popen([sys.executable, "scripts/run_check_repair.py", "--max-repairs", "2"],
                                   cwd=ROOT, stdout=stream, stderr=subprocess.STDOUT)
        while process.poll() is None:
            update("running Qwen checks and selective repairs")
            time.sleep(30)
        if process.returncode:
            update(f"interrupted or failed (exit {process.returncode}); rerun to resume")
            raise SystemExit(process.returncode)
        for script in ("scripts/prepare_ratings.py", "scripts/summarize_midterm.py"):
            result = subprocess.run([sys.executable, script], cwd=ROOT,
                                    stdout=stream, stderr=subprocess.STDOUT)
            if result.returncode:
                update(f"checks finished; {script} failed")
                raise SystemExit(result.returncode)
    record = update("checks, repairs, and rating packet complete; human ratings pending")
    if record["checks_recorded"] != record["checks_total"]:
        raise SystemExit("Stage C ended with missing check rows")


if __name__ == "__main__":
    main()
