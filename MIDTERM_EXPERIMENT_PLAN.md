# EditAgentLite: midterm runbook

**Team:** Akshat Singhal, Ashvin Sehgal, Shubhangi Katariyar

**Window:** 48 hours from starting this runbook. Write the report only after outputs and ratings are frozen.
**Purpose:** Obtain a small, honest preliminary result for a one-page CVPR-format course midterm. This is a pilot, not the final benchmark.

## 1. Result to aim for

Run one edit on eight frozen image-editing tasks, let a 4B VLM inspect each output, and make at most two failure-specific repairs in total. Show:

- Whether BAGEL and Qwen can run together as a reproducible pipeline.
- How often the first edit satisfies the request, based on human ratings.
- Whether the two attempted repairs improve their specific failures.
- Measured model calls, latency, and memory, including unsuccessful runs.

Do **not** claim that the method beats EditAgent, that two repaired examples prove a general gain, or that Qwen's own verdict is an independent quality score. The final project's two-independent-sample baseline is deliberately deferred until after the midterm.

## 2. Frozen pilot protocol

| Item | Rule |
| --- | --- |
| Dataset | Public [Complex-Edit](https://huggingface.co/datasets/UCSC-VLAA/Complex-Edit), `test_real` images and atomic `edit.sequence` instructions only. Do not use compound instructions or reference target images. |
| Tasks | Eight total: four `Remove an Object` and four `Adjust Lighting` requests that are global brightness/contrast changes. |
| Exclusions | Missing/corrupt image; ambiguous or absent target; lighting request that is local, changes color temperature, or requires generated content. Log the reason **before** model output is seen. |
| Selection | Sort eligible examples by dataset image ID and instruction index; use seed 2026 to sample four per category. Freeze the manifest before running edits. If fewer than four eligible cases exist in a category, use all available and state the smaller denominator. |
| First action | BAGEL for removal. Deterministic brightness/contrast tool for global lighting. No per-task manual prompt tuning after outputs are seen. |
| Repair budget | Qwen checks every first output. In manifest order, take the first two Qwen-flagged failures with executable repairs; one repair action per selected task. No third attempt. |
| Candidate selection | Keep the first image if the repair clearly worsens it or breaks preservation; otherwise keep the repair. Record the decision and show **both** images to human raters. |
| Reproducibility | Record model IDs/revisions, precision or quantization, resolution, seeds, prompt versions, GPU type, and code commit. If an editor is nondeterministic, reruns are not substituted for the frozen first output. |

An edit is **fully successful** only when the requested change happened, unrelated content was preserved, and the image remains visually usable. Record each component separately. Do not choose an easier task after seeing a failure.

## 3. Exact sequential handoffs

### Stage A — Akshat: setup, dataset, tools, push (hours 0–24)

1. Set up Qwen3-VL-4B-Thinking and BAGEL-7B-MoT from their official releases. Use one fixed BAGEL configuration for all removal tasks. Record actual checkpoint revisions and dependencies.
2. Implement a simple brightness/contrast operator and a common image I/O path. Fix image size, output format, and naming conventions.
3. Build and freeze `pilot_manifest.csv` with columns `task_id,source_id,instruction_index,category,instruction,source_path,selection_seed`. Create `screening_log.csv` for exclusions. Keep raw dataset images out of Git.
4. Provide two callable commands or scripts: `run_first` for a task manifest and `run_check_repair` for frozen first outputs. The second may initially be a smoke-test stub, but its input/output contract must be documented. Both must write machine-readable JSONL logs.
5. Smoke-test one BAGEL edit, one Qwen image comparison, and one deterministic lighting edit. Record load time, per-call time, peak GPU memory, and any error.
6. Push **code, manifest, dependency instructions, and a short run guide**. Do not push model weights, dataset images, generated images, secrets, or local absolute paths. Verify a clean clone can import the project and resolve the manifest through a documented dataset-root setting.

**Exit gate:** Ashvin receives the commit hash, exact commands, task manifest, expected output structure, and a location for dataset assets. Akshat stays available to fix setup failures, but Ashvin owns the next run.

### Stage B — Ashvin: first experiment (hours 24–32)

1. Pull Akshat's setup commit and verify its hash. Do not alter task IDs, model settings, or prompts.
2. Run all eight first actions in manifest order. Keep output for every completed task, including visibly bad edits.
3. For any execution error, log its type and attempt **one technical rerun with identical settings**. Distinguish that rerun from a research repair. If it still fails, mark the task `execution_failed`; do not replace it.
4. Produce `first_outputs.jsonl` with task ID, tool, output path, seed, runtime, status, and error message. Make a contact sheet for quick handoff; it is not an evaluation.
5. Freeze the outputs and hand Shubhangi the folder, log, manifest, and Akshat's commit hash. Use checksums or a read-only copy so later work cannot overwrite the first images.

**Exit gate:** Each manifest task has either a readable first image or a logged execution failure. Shubhangi does not start the second experiment until this handoff is complete.

### Stage C — Shubhangi: feedback experiment and evidence (hours 32–44)

1. Run Qwen on each completed first edit with the source image, instruction, first output, and fixed assessment prompt. Save the raw response and parsed record.
2. Parse into: `pass`, one failure label, a short observed-error explanation, repair action, revised instruction or tool parameter, and preservation requirement. Allowed labels: `incomplete_edit`, `wrong_target`, `unwanted_change`, `wrong_strength`, `artifact`, `uncertain`.
3. Select the first two executable failures in manifest order. For removal, the allowed repair is a revised BAGEL instruction from the **original** source image. For lighting, adjust the deterministic tool parameter from the **original** source image. If Qwen proposes an unsupported action, log `unsupported_repair` and continue to the next flagged task.
4. Run one repair for each selected task. Save `repair_outputs.jsonl` and both before/after images. If a repair fails technically, log it; do not hide the case.
5. Prepare anonymized, randomly ordered images for rating. At least two people rate each first/repaired pair independently, including someone other than the output runner. Each rater sees the source and instruction, then records requested-change, preservation, and usability as yes/no. Preserve individual ratings and disagreements.
6. Freeze `ratings.csv`, a results table with actual denominators, and one representative success **or failure** figure. Share the evidence package with the team.

**Exit gate:** Every reported number can be recomputed from the manifest, run logs, and ratings. The team reviews wording and limitations before the report is assembled.

## 4. Clock and protected report time

| Window | Owner | Required output |
| --- | --- | --- |
| Hours 0–18 | Akshat | Environments, dataset filtering, scripts, smoke tests |
| Hours 18–24 | Akshat | Reproducibility check, push, handoff; stop adding features |
| Hours 24–32 | Ashvin | Eight frozen first outputs or explicit failure rows |
| Hours 32–39 | Shubhangi | Qwen checks and at most two targeted repairs |
| Hours 39–44 | Shubhangi + team raters | Blind ratings, results table, one figure |
| Hours 44–48 | Whole team | Write and inspect the separate one-page report, verify PDF format and citations, leave submission time for all three |

The schedule is sequential for implementation and experiments. Team members may read documentation or prepare their own notes while waiting, but they must not modify the frozen manifest or another person's outputs. If an earlier stage slips, reduce the number of **completed** pilot tasks and report the denominator; preserve the final four hours for the report.

## 5. Run logs and measurements

Use relative paths under a shared local artifact directory; keep that directory out of Git. Suggested layout:

```text
pilot_artifacts/
  manifest_snapshot.csv
  screening_log.csv
  first_outputs.jsonl
  checks.jsonl
  repair_outputs.jsonl
  ratings.csv
  images/first/
  images/repair/
  figures/
```

Each model/tool call log must contain `task_id`, `stage`, `tool_or_model`, `model_revision`, `seed`, `input_image`, `output_image`, `elapsed_seconds`, `status`, and `error`. Record GPU memory when available. Do not log access tokens.

For the report, calculate:

- First-edit full success: number successful / number with completed first output.
- Qwen flag rate: number flagged / number checked.
- Qwen false acceptances: number Qwen passed but humans rejected / number Qwen passed and human-rated.
- Repair outcome: improved / unchanged / worse among the **attempted** repairs, with both images human-rated.
- Resource use: BAGEL calls, Qwen calls, deterministic calls, per-call latency, and total elapsed time. Keep model-loading time separate from per-image inference.

Do not combine missing outputs with unsuccessful images in one score. Show execution failures separately. With eight cases, use counts rather than significance tests or broad percentage claims.

## 6. Resource cap and fallback rules

The planned pilot uses eight first actions plus at most two repair actions: **ten research editing actions maximum**. With four removal tasks and four deterministic lighting tasks, the expected BAGEL count is roughly four to six, assuming no lighting repair switches to BAGEL. Up to ten BAGEL calls is a conservative ceiling if implementation changes. Qwen should make about eight inspection calls plus any final comparisons; record the actual count.

At an **illustrative** 30–120 seconds per BAGEL generation, six calls would consume 3–12 minutes of generation time. This excludes downloads, setup, model loading, Qwen time, OOM recovery, and report work. Akshat replaces the illustration with measured day-1 numbers. If a hosted service is used, record its actual charge; public weights do not imply free compute.

| Problem | Immediate response | Honest midterm evidence |
| --- | --- | --- |
| BAGEL will not load by hour 18 | Try the official documented quantized mode once, then stop setup experiments. | Environment logs, one working deterministic-tool path, and BAGEL integration as unfinished. |
| BAGEL works but is slow | Reduce to two removal and two lighting tasks, retaining manifest order. | State the smaller fixed pilot and measured latency. |
| Qwen will not load by hour 24 | Preserve one-shot run; do not replace Qwen with undisclosed human feedback. | One-shot feasibility and controller setup difficulty; no closed-loop claim. |
| Qwen JSON is invalid | Retry parsing or one request with the same fixed prompt; log both attempts. If still invalid, mark `parse_failed`. | Parse failure count and no repair for that task. |
| No first edits are flagged | Do not force a repair. Human-rate first outputs and inspect possible Qwen false acceptances. | Early-stop behavior and its limitation; zero repair denominator. |
| Repair worsens the image | Keep both outputs and ratings; apply the recorded final-selection rule. | A failure case showing why feedback is imperfect. |
| Ratings disagree | Preserve votes and use majority where possible; if two raters tie, have the third rate blindly. | Report unresolved disagreements if any. |

## 7. Midterm report content checklist

The report is a separate deliverable and is **not** created by this runbook. Use the official CVPR camera-ready, double-column, 11-point format; keep main text within one page if possible and never beyond two pages, with only references after page two. List all three authors.

- **Status:** what has actually run at the PDF freeze time; distinguish working components from planned ones.
- **Scope change:** original proposal was a larger 200–400-task, fixed-editor feedback study; current course project uses a 40-task final target and this eight-task pilot, Qwen 4B, BAGEL, and one deterministic tool.
- **Proposed solution:** first action, Qwen diagnosis, selective single repair, and source-image restart.
- **Preliminary result:** only measured counts, denominators, time, memory, and a representative example. Include a compact table if results exist.
- **Difficulty:** installation, GPU memory, latency, parse errors, unreliable judgments, or quality problems actually encountered.
- **Next steps:** full 40-task set, one-shot and independent-sampling baselines, human review, and quality-versus-cost analysis.
- **Proposal feedback:** acknowledge the encouragement to explore agentic image editing; explain how EditAgent informed the smaller budget-aware direction. EditAgent already includes routing and feedback, so claim a cost-focused study rather than a new feedback concept.
- **Final checks:** citations for datasets/models/paper, PDF page count and font size, all authors' names, image legibility, and a copy ready for each teammate's Canvas submission.

## Sources

- [Complex-Edit dataset](https://huggingface.co/datasets/UCSC-VLAA/Complex-Edit)
- [Qwen3-VL-4B-Thinking](https://huggingface.co/Qwen/Qwen3-VL-4B-Thinking)
- [BAGEL implementation](https://github.com/ByteDance-Seed/Bagel)
- [EditAgent paper](https://arxiv.org/abs/2610.39664)
