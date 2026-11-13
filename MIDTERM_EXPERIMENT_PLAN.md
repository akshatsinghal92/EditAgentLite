# EditAgentLite: 48-hour midterm experiment plan

**Team:** Shubhangi Katariyar, Ashvin Sehgal, Akshat Singhal  
**Target:** Prepare evidence for a one-page CVPR-format midterm report due in two days. This document plans the work; it is not the report.

## What the midterm should establish

Show that the scoped pipeline is executable and that a small controller can produce an interpretable failure diagnosis and targeted repair on a few image edits. The midterm is a **pilot**, not the final 40-task evaluation. Report measured results and failures without claiming a quality improvement from a tiny sample.

## Fixed pilot scope

- **Models:** Qwen3-VL-4B-Thinking as controller; BAGEL-7B-MoT as image editor.
- **Cheap tool:** deterministic brightness/contrast adjustment.
- **Data:** 8 atomic instructions from the real-image split of Complex-Edit: 4 `Remove an Object` and 4 suitable *global* `Adjust Lighting` requests. Record source IDs and instructions before any model runs.
- **Budget:** Ashvin runs one initial action on each task. Shubhangi then runs Qwen's check and at most one targeted repair on up to 2 failed tasks. The independent-sampling baseline belongs to the final project, not this 48-hour pilot.
- **Output:** source, instruction, first edit, failure label, repair action, repaired image, and a short trace. Keep images and model checkpoints out of Git.

Use the same first output for every comparison on a task. Do not choose pilot tasks after seeing BAGEL outputs. If fewer than 8 examples are usable, report the actual count and why tasks were excluded.

## Sequential ownership and handoffs

| Stage | Owner | Work | Required handoff |
| --- | --- | --- | --- |
| **1. Setup and push** | **Akshat** | Set up BAGEL, Qwen, the deterministic lighting tool, the Complex-Edit subset, and runnable scripts. Smoke-test one example per model, log GPU memory and runtime, and push code, setup instructions, and the frozen task manifest. | A clean clone can run the commands. Send Ashvin the commit hash and paths to local dataset assets; keep weights, images, credentials, and generated outputs out of Git. |
| **2. First experiment** | **Ashvin** | Pull Akshat's commit and run the one-shot first action on all 8 frozen tasks. Save images and a row per task with action, settings, latency, and errors. | Give Shubhangi the fixed first-output folder and run log. Do not change prompts or task IDs after this handoff. |
| **3. Second experiment** | **Shubhangi** | Pull the same code, run Qwen checks on Ashvin's outputs, classify failures, and execute at most 2 targeted repairs in task-ID order. Save the repaired outputs and traces, then coordinate blind ratings and the result table. | Give the team a frozen evidence package: first outputs, repair outputs, diagnoses, human ratings, and measured resource counts. |

The next stage begins only after its handoff is complete. All three review the report claims together; an output's creator must not be its only human reviewer.

## 48-hour schedule

| Time | Work and decision gate |
| --- | --- |
| **Hours 0–24: Akshat** | Complete model environments, dataset filtering, tools, script integration, smoke tests, and the setup commit. Push the runnable code and task manifest. |
| **Hours 24–32: Ashvin** | Pull the setup commit; run and freeze all 8 one-shot outputs and the timing/error log. Hand off outputs to Shubhangi. |
| **Hours 32–39: Shubhangi** | Run Qwen checks on the frozen outputs; select up to 2 failed cases in task-ID order; run one targeted repair per selected case. Freeze outputs and traces. |
| **Hours 39–43: Shubhangi with team review** | Blindly rate first and repaired outputs for instruction success, preservation, and usability. Record disagreements rather than silently changing scores. |
| **Hours 42–46** | Compute counts and measured runtimes; prepare one compact result table and one before/first/repair example. Draft only claims supported by the logs. |
| **Hours 46–48** | Check citations, authors, camera-ready formatting, and page limit when the separate report is written; leave time for every teammate to submit it. |

## Pilot comparisons and measurements

The pilot compares **Ashvin's one-shot output** with **Shubhangi's targeted repair** only on the cases that Qwen flags. This is a diagnostic pilot, not a randomized benchmark comparison; report denominators for every result. The two-independent-sample condition remains in the full project plan.

For each output, record:

1. **Instruction success:** requested change completed? yes/no.
2. **Preservation:** unrelated content remains acceptable? yes/no.
3. **Usability:** visible artifacts or obvious damage? yes/no.
4. **Controller outcome:** accepted first edit, failure type, repair selected, or abstained.
5. **Resources:** BAGEL calls, Qwen calls, deterministic-tool calls, elapsed seconds, peak GPU memory, and any provider charges.

Use human ratings as the preliminary outcome. Qwen's own pass/fail label is a system decision, not independent ground truth. The report can show a table such as `first edits accepted by humans: x/8`, `repairs improved judged result: y/n`, and `median BAGEL seconds per edit: z`, filling values only after runs complete.

## Compute allowance and fallback

Plan for **8 first actions** and up to **2 repairs**: at most **10 editing actions** in the pilot. If BAGEL is used for all of them, this means at most 10 BAGEL generations; lighting tasks handled by the deterministic tool reduce that number. At an illustrative 30–120 seconds per BAGEL generation, 10 generations take 5–20 minutes of generation time, **excluding** downloads, model loading, Qwen inference, and failed runs. Replace this estimate with Akshat's setup measurements.

**Gate at hour 24:** If BAGEL cannot run with available hardware, do not imply that the full method was tested. Akshat hands off setup logs and the working deterministic lighting path; Ashvin and Shubhangi run only the tasks supported by that path and report the smaller denominator. If Qwen cannot run, stop before the second experiment, preserve the one-shot results, and report controller integration as unfinished.

## Report-ready evidence package

Create a small folder outside Git containing the frozen manifest, run log, anonymized ratings, and 1–2 image examples. The midterm report should then state:

- **Status and scope change:** from the original broad 200–400-task, general-editor proposal to a two-week, two-edit-type pilot using Qwen 4B, BAGEL, and one deterministic tool.
- **Completed work:** repository and scoped protocol, plus only the model runs and ratings actually finished by the deadline.
- **Preliminary results:** counts with denominators, measured latency, one representative success or failure, and any setup limitations.
- **Next steps:** finish the 40-task evaluation with the three planned conditions and analyze quality versus compute.
- **Response to proposal feedback:** the feedback encouraged agentic editing; EditAgent motivates our focus on selective repair and lower inference use. Acknowledge that EditAgent already includes routing and feedback.

## Sources

- [Complex-Edit dataset](https://huggingface.co/datasets/UCSC-VLAA/Complex-Edit)
- [Qwen3-VL-4B-Thinking](https://huggingface.co/Qwen/Qwen3-VL-4B-Thinking)
- [BAGEL implementation](https://github.com/ByteDance-Seed/Bagel)
- [EditAgent paper](https://arxiv.org/abs/2610.39664)
