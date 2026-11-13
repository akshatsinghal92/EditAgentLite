# EditAgentLite: 48-hour midterm experiment plan

**Team:** Shubhangi Katariyar, Ashvin Sehgal, Akshat Singhal  
**Target:** Prepare evidence for a one-page CVPR-format midterm report due in two days. This document plans the work; it is not the report.

## What the midterm should establish

Show that the scoped pipeline is executable and that a small controller can produce an interpretable failure diagnosis and targeted repair on a few image edits. The midterm is a **pilot**, not the final 40-task evaluation. Report measured results and failures without claiming a quality improvement from a tiny sample.

## Fixed pilot scope

- **Models:** Qwen3-VL-4B-Thinking as controller; BAGEL-7B-MoT as image editor.
- **Cheap tool:** deterministic brightness/contrast adjustment.
- **Data:** 8 atomic instructions from the real-image split of Complex-Edit: 4 `Remove an Object` and 4 suitable *global* `Adjust Lighting` requests. Record source IDs and instructions before any model runs.
- **Budget:** One initial action per task; a maximum of one targeted repair on up to 4 selected tasks. For those repaired tasks, also generate one independent second attempt from the original source if time and compute permit.
- **Output:** source, instruction, first edit, failure label, repair action, repaired image, and a short trace. Keep images and model checkpoints out of Git.

Use the same first output for every comparison on a task. Do not choose pilot tasks after seeing BAGEL outputs. If fewer than 8 examples are usable, report the actual count and why tasks were excluded.

## Team ownership

| Person | Primary responsibility | Deliverable by end of day 1 | Deliverable by end of day 2 |
| --- | --- | --- | --- |
| **Akshat** | BAGEL execution and integration | One successful source-image edit; recorded GPU memory, runtime, settings, and failures | First edits for the frozen pilot set; image paths and timing log |
| **Ashvin** | Qwen controller and repair logic | Structured prompt that returns intended change, preservation requirement, pass/fail, failure type, and next action | Qwen diagnoses for all first edits; at most 4 executable repair instructions and traces |
| **Shubhangi** | Dataset and independent evaluation | Frozen 8-task manifest and a short human rating rubric | Blinded ratings, results table, example figure, and notes on disagreement or ambiguity |

All three review the report claims together. Shubhangi coordinates ratings, but the person who generated an output should not be its only reviewer.

## 48-hour schedule

| Time | Work and decision gate |
| --- | --- |
| **Hours 0–4** | Shubhangi freezes 8 task IDs and the rubric. Akshat starts BAGEL; Ashvin starts Qwen. Run one image through each model. |
| **Hours 4–10** | Record model setup and latency. Run 2 removal and 2 lighting first edits. Integrate the controller output with tool inputs. |
| **Hours 10–18** | Finish the remaining 4 first edits. Inspect traces and select up to 4 failed or incomplete cases for repair using a predeclared rule: all failures in task-ID order until the cap is reached. |
| **Hours 18–28** | Run one targeted repair per selected case. If feasible, generate a matched independent second attempt for the same cases. Freeze all outputs. |
| **Hours 28–36** | Blindly rate final outputs for instruction success, preservation, and usability. Record disagreements rather than silently changing scores. |
| **Hours 36–44** | Compute counts and mean runtimes; prepare one compact result table and one before/first/repair example. Draft only claims supported by the logs. |
| **Hours 44–48** | Check citations, authors, camera-ready formatting, and page limit when the separate report is written; leave time for every teammate to submit it. |

## Pilot comparisons and measurements

The minimum comparison is **one-shot versus one targeted repair** on the cases that the controller flags. If compute allows, add **independent second attempt plus selection** on those same cases. This is a diagnostic pilot, not a randomized benchmark comparison; report denominators for every result.

For each output, record:

1. **Instruction success:** requested change completed? yes/no.
2. **Preservation:** unrelated content remains acceptable? yes/no.
3. **Usability:** visible artifacts or obvious damage? yes/no.
4. **Controller outcome:** accepted first edit, failure type, repair selected, or abstained.
5. **Resources:** BAGEL calls, Qwen calls, deterministic-tool calls, elapsed seconds, peak GPU memory, and any provider charges.

Use human ratings as the preliminary outcome. Qwen's own pass/fail label is a system decision, not independent ground truth. The report can show a table such as `first edits accepted by humans: x/8`, `repairs improved judged result: y/n`, and `median BAGEL seconds per edit: z`, filling values only after runs complete.

## Compute allowance and fallback

Plan for **8 first actions**, up to **4 repairs**, and optionally **4 independent second attempts**: at most **16 editing actions** in the pilot. If BAGEL is used for all of them, this means at most 16 BAGEL generations; lighting tasks handled by the deterministic tool reduce that number. At an illustrative 30–120 seconds per BAGEL generation, 16 generations take 8–32 minutes of generation time, **excluding** downloads, model loading, Qwen inference, and failed runs. Replace this estimate with day-1 measurements.

**Gate at hour 10:** If BAGEL cannot run with available hardware, do not imply that the full method was tested. Preserve setup logs and report the obstacle. Complete the deterministic lighting pipeline and Qwen diagnosis on those outputs; show an executable component-level pilot and list BAGEL integration as the immediate next step. If Qwen cannot run, use a fixed human-authored diagnosis on a few examples only as a software integration check and label it clearly as such.

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
