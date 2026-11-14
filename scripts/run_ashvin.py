#!/usr/bin/env python3
"""Supervise Ashvin's sequential first edits, log progress, and freeze outputs."""

import argparse
import csv
import json
import os
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ARTIFACTS = ROOT / "outputs/pilot_artifacts"
FIRST_LOG = ARTIFACTS / "first_outputs.jsonl"
RUN_LOG = ARTIFACTS / "ashvin_run.log"
PROGRESS_LOG = ARTIFACTS / "ashvin_progress.log"
PROGRESS_JSON = ARTIFACTS / "ashvin_progress.json"


def utc_now():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def tasks():
    with (ROOT / "pilot/manifest.csv").open(newline="") as stream:
        return list(csv.DictReader(stream))


def latest_rows():
    rows = {}
    if FIRST_LOG.exists():
        for line in FIRST_LOG.read_text().splitlines():
            if line.strip():
                row = json.loads(line)
                rows[row["task_id"]] = row
    return rows


def progress(task_rows, state):
    rows = latest_rows()
    complete = sum(1 for task in task_rows if rows.get(task["task_id"], {}).get("status") == "ok"
                   and rows[task["task_id"]].get("output_image")
                   and (ROOT / rows[task["task_id"]]["output_image"]).is_file())
    failed = [task["task_id"] for task in task_rows
              if rows.get(task["task_id"], {}).get("status") == "execution_failed"]
    current = next((task["task_id"] for task in task_rows
                    if rows.get(task["task_id"], {}).get("status") != "ok"), None)
    bar = "[" + "#" * complete + "." * (len(task_rows) - complete) + "]"
    record = {"time_utc": utc_now(), "state": state, "progress": bar,
              "completed": complete, "total": len(task_rows), "current_or_next": current,
              "failed": failed, "first_log": str(FIRST_LOG.relative_to(ROOT))}
    PROGRESS_JSON.write_text(json.dumps(record, indent=2) + "\n")
    with PROGRESS_LOG.open("a") as stream:
        stream.write(f"{record['time_utc']} {bar} {complete}/{len(task_rows)} "
                     f"{state} {current or 'done'}\n")
    return record


def alive(pid):
    try:
        state = Path(f"/proc/{pid}/stat").read_text().split(") ", 1)[1].split()[0]
        return state != "Z"
    except FileNotFoundError:
        return False


def run_batch(task_rows, existing_pid=None):
    if existing_pid is None:
        with RUN_LOG.open("a") as stream:
            process = subprocess.Popen([sys.executable, "scripts/run_first.py", "--resume"],
                                       cwd=ROOT, stdout=stream, stderr=subprocess.STDOUT)
        pid = process.pid
    else:
        pid = existing_pid
    while alive(pid):
        progress(task_rows, f"running pid={pid}")
        time.sleep(30)
    progress(task_rows, "batch exited")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--existing-pid", type=int,
                        help="Adopt an already running sequential first-edit batch")
    args = parser.parse_args()
    ARTIFACTS.mkdir(parents=True, exist_ok=True)
    task_rows = tasks()
    run_batch(task_rows, args.existing_pid)
    rows = latest_rows()
    failures = [task["task_id"] for task in task_rows
                if rows.get(task["task_id"], {}).get("status") == "execution_failed"]
    if failures:
        with PROGRESS_LOG.open("a") as stream:
            stream.write(f"{utc_now()} technical rerun with identical settings: {', '.join(failures)}\n")
        run_batch(task_rows)
    record = progress(task_rows, "checking completion")
    if record["completed"] != len(task_rows):
        progress(task_rows, "incomplete; inspect ashvin_run.log")
        raise SystemExit(1)
    with PROGRESS_LOG.open("a") as stream:
        result = subprocess.run([sys.executable, "scripts/freeze_first.py"], cwd=ROOT,
                                stdout=stream, stderr=subprocess.STDOUT)
    if result.returncode:
        progress(task_rows, "outputs complete; freeze failed")
        raise SystemExit(result.returncode)
    progress(task_rows, "complete and frozen")


if __name__ == "__main__":
    main()
