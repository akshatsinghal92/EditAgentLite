#!/usr/bin/env python3
"""Combine real rater CSVs; require a third blind vote for disagreements."""

import csv
import json
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ARTIFACTS = ROOT / "outputs/pilot_artifacts"
PACKET = ARTIFACTS / "rating_packet"
FIELDS = ("requested_change", "preservation", "usability")


def read_csv(path):
    with path.open(newline="") as stream:
        return list(csv.DictReader(stream))


def write_csv(path, fields, rows):
    with path.open("w", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def main():
    key = {row["case_id"]: row for row in read_csv(ARTIFACTS / "rating_key.csv")}
    votes = defaultdict(list)
    all_rows = []
    for number in (1, 2, 3):
        path = PACKET / f"rater_{number}.csv"
        if not path.exists():
            if number == 3:
                continue
            raise SystemExit(f"Missing {path}")
        for row in read_csv(path):
            case_id = row["case_id"]
            if case_id not in key:
                raise SystemExit(f"Unknown case ID {case_id}")
            values = [row[name] for name in FIELDS]
            if number == 3 and all(value == "" for value in values):
                continue
            if any(value not in ("0", "1") for value in values):
                raise SystemExit(f"Incomplete or invalid rating for {case_id} in {path}")
            votes[case_id].append(row)
            all_rows.append({**row, **key[case_id]})
    consensus = {}
    for case_id, meta in key.items():
        case_votes = votes[case_id]
        if len(case_votes) < 2:
            raise SystemExit(f"Need two independent ratings for {case_id}")
        if len({row["rater_id"] for row in case_votes}) != len(case_votes):
            raise SystemExit(f"Rater IDs must be distinct for {case_id}")
        result = dict(meta)
        for name in FIELDS:
            values = [int(row[name]) for row in case_votes]
            if len(values) == 2 and values[0] != values[1]:
                raise SystemExit(f"Third blind rating required for {case_id}: {name}")
            result[name] = int(sum(values) > len(values) / 2)
        result["full_success"] = int(all(result[name] for name in FIELDS))
        consensus[case_id] = result
    write_csv(ARTIFACTS / "ratings.csv",
              ["rater_id", "case_id", "requested_change", "preservation", "usability", "notes",
               "task_id", "stage", "candidate_path"], all_rows)
    write_csv(ARTIFACTS / "ratings_consensus.csv",
              ["case_id", "task_id", "stage", "candidate_path", *FIELDS, "full_success"],
              list(consensus.values()))
    first = {r["task_id"]: r for r in consensus.values() if r["stage"] == "first"}
    repair = {r["task_id"]: r for r in consensus.values() if r["stage"] == "repair"}
    checks = [json.loads(x) for x in (ARTIFACTS / "checks.jsonl").read_text().splitlines()]
    passed = [r for r in checks if r["status"] == "ok" and r["decision"]["label"] == "pass"]
    false_accept = sum(not first[r["task_id"]]["full_success"] for r in passed)
    outcomes = {"improved": 0, "unchanged": 0, "worse": 0}
    selected = {}
    for task_id, after in repair.items():
        before = first[task_id]
        prior_score = sum(before[name] for name in FIELDS)
        after_score = sum(after[name] for name in FIELDS)
        if after["preservation"] < before["preservation"] or after["usability"] < before["usability"]:
            outcome = "worse"
        elif after_score > prior_score:
            outcome = "improved"
        elif after_score < prior_score:
            outcome = "worse"
        else:
            outcome = "unchanged"
        outcomes[outcome] += 1
        selected[task_id] = "first" if outcome == "worse" else "repair"
    result = json.loads((ARTIFACTS / "results_pending.json").read_text())
    result.update({"human_first_full_success": {"success": sum(r["full_success"] for r in first.values()),
                                                "denominator": len(first)},
                   "qwen_false_acceptances": {"count": false_accept, "denominator": len(passed)},
                   "repair_improved_unchanged_worse": outcomes,
                   "final_selected_stage": selected,
                   "human_ratings_status": "complete"})
    (ARTIFACTS / "results_final.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
