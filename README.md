# EditAgentLite

EditAgentLite is a two-week, three-person course project on **budget-aware image editing**. Qwen3-VL-4B-Thinking checks a first edit, classifies a failure if one occurs, and chooses at most one targeted repair. BAGEL-7B-MoT is the fixed learned image editor. The project tests whether this selective workflow gives better results per editing call than simple alternatives.

## Research question

With a maximum of two editing actions, does failure-specific repair improve edit success over a one-shot edit and two independent edits, while using fewer than two actions on average?

## Scope

- Single source image and one instruction per task; no multi-turn conversations or model training.
- Two edit types: **object removal** and **global lighting adjustment**. These exercise a learned image editor and a cheap deterministic tool.
- **Controller:** [Qwen3-VL-4B-Thinking](https://huggingface.co/Qwen/Qwen3-VL-4B-Thinking) for planning, inspection, failure classification, and candidate selection.
- **Learned editor:** [BAGEL-7B-MoT](https://huggingface.co/ByteDance-Seed/BAGEL-7B-MoT) for image edits. Keep its checkpoint and generation settings fixed across conditions.
- **Cheap tools:** deterministic brightness/contrast for global lighting and OpenCV Telea inpainting for removal when an input mask is available. The eight-task pilot includes four human-drawn removal masks, with annotation effort disclosed separately. BAGEL remains the learned removal route.
- At most two editing actions per task. No broad tool search or full EditAgent reproduction.
- A hand-checked set of **40 tasks** (20 per edit type), split into 10 development and 30 final test tasks.

## Dataset and task selection

Use the public [Complex-Edit dataset](https://huggingface.co/datasets/UCSC-VLAA/Complex-Edit), which is listed as CC BY-NC 4.0. Use its **atomic** instructions from the real-image test split, not compound instructions or multi-turn chains. Select 20 tasks named `Remove an Object` and 20 named `Adjust Lighting`. Keep only global lighting instructions that a brightness/contrast operator can reasonably perform; exclude local relighting, color-temperature changes, and instructions requiring newly generated content.

Before running either model, record the source image ID, instruction, category, and exclusion reason for screened-out examples. Use a fixed seed to sample eligible examples, inspect them for broken or ambiguous instructions, and freeze the 40 task IDs. Allocate 5 tasks per category to development and 15 per category to final test. Do not select examples based on model outputs. Report results as a **40-task course-project subset**, not an official Complex-Edit benchmark score. Keep dataset images outside Git; publish IDs and selection rules rather than copying benchmark assets into this repository.

BAGEL has 14B total parameters and 7B active parameters; it is not a small or cheap editor in absolute terms. The [official setup](https://github.com/ByteDance-Seed/Bagel) calls for 32GB+ GPU memory for standard inference or NF4 quantization for 12–32GB. On days 1–2, run one end-to-end editing smoke test at the intended resolution and record GPU memory and latency before committing to the full evaluation. If local BAGEL inference is unavailable, use a hosted BAGEL endpoint if permitted by the course budget; report its actual cost. Do not silently substitute another editor in the final comparison.

## Workflow

1. The controller identifies the requested change and what must remain unchanged.
2. It chooses the general editor or deterministic tool for the first action.
3. It checks the result against the source and instruction.
4. If the result passes, it stops. Otherwise it labels the failure: incomplete edit, wrong target, unwanted change, wrong strength, or artifact.
5. It chooses one targeted repair: adjust tool parameters, rewrite the editor instruction, or switch tools if supported.
6. It compares the two results and returns the better one, or records that neither passed.

Every run records the images, actions, VLM decisions, failure label, edit-call count, and elapsed time.

## Evaluation

Run only three conditions on the same 30 test tasks:

1. **One-shot:** first edit only.
2. **Two-sample baseline:** two independent attempts from the same source with the same initial tool as one-shot, then select the better result. For deterministic lighting requests, use two predeclared parameter settings so this baseline yields different outputs.
3. **EditAgentLite:** first edit, early stop or one failure-specific repair.

Cache and reuse the same first candidate across conditions for each task; count that candidate in each condition's logical cost, but generate it only once physically. Use a short rubric: requested change succeeds, unrelated content is preserved, and result is visually usable. All three team members independently review the 90 anonymized test outputs, then resolve disagreements. Report success counts by edit type, average BAGEL calls, average deterministic-tool calls, Qwen calls, wall-clock time, and a small gallery of successes and failures. Treat VLM self-scores as diagnostics, not ground truth. Do not claim statistical significance from 30 test tasks.

## Compute budget

These are **planning estimates, not measured runtimes or prices**. With 30 test tasks and three conditions, there are 120–150 logical editing actions: 30 one-shot, 60 two-sample, and 30–60 EditAgentLite. The 10 development tasks add roughly 40–50 logical actions. Caching the shared first output reduces physical executions. Under the intended routing (BAGEL for removal; deterministic operator first for lighting), budget roughly **80–120 physical BAGEL generations** across development, smoke tests, and final runs. The absolute ceiling if every editing action uses BAGEL is about **200 generations**. Budget roughly **120–160 Qwen calls** for routing, checking, repair decisions, and selection; record actual counts.

If measured BAGEL latency is 30–120 seconds per image, 80–120 generations imply about **0.7–4 GPU hours of generation time** before model loading, Qwen inference, failed runs, and setup. This interval is an illustrative calculation, not a benchmark claim. On day 2, replace it with `measured_seconds_per_edit × planned_BAGEL_calls / 3600`, then add a 25% retry margin. For rented compute, multiply total GPU hours by the provider's actual hourly price; do not assume a free hosted endpoint. Run the models sequentially if they cannot fit in GPU memory together.

## Two-week schedule and ownership

| Time | Member A: pipeline | Member B: controller | Member C: evaluation | Shared checkpoint |
| --- | --- | --- | --- | --- |
| Days 1–2 | Smoke-test BAGEL and deterministic tool; measure memory and latency | Smoke-test Qwen and define structured outputs | Filter and freeze 40 Complex-Edit tasks and rubric | Freeze models, task IDs, and measured budget |
| Days 3–5 | Implement tool wrappers and logging | Implement first-action routing and result check | Prepare blinded review sheet | End-to-end run on 10 development tasks |
| Days 6–7 | Add second-action execution | Add failure labels and repair mapping | Inspect development outputs | Freeze prompts and code for test |
| Days 8–10 | Run all three conditions on 30 test tasks | Debug only execution failures | Collect independent ratings | Complete test outputs and ratings |
| Days 11–12 | Compute cost and latency summary | Analyze routing and repair mistakes | Resolve rating disagreements | Results table and example gallery |
| Days 13–14 | Support demo and reproducibility | Write method and limitations | Write evaluation and results | Final report, demo, and presentation |

The member labels are roles, not assigned people. Keep one person responsible for each workstream and use the shared checkpoints to integrate work.

## Minimum viable result

By day 2, BAGEL and Qwen must each pass a single-image smoke test within the available memory and time budget. By day 7, the system must run on the 10 development tasks, save both candidate images when a repair occurs, and produce a machine-readable trace. If the day-7 milestone slips, drop optional specialists and preserve the three-condition evaluation.

## Deliverables

- Reproducible code and setup instructions
- Frozen 40-task list and evaluation rubric
- Test outputs and anonymized human ratings
- Short report with quality-versus-cost results and limitations
- Small demo showing a first edit, failure diagnosis, repair, and final result

## Related work

EditAgent already uses tool routing, verification, feedback, and retries. This project focuses on a much smaller two-action policy and its quality-cost tradeoff; it does not claim to invent feedback-based editing or reproduce EditAgent's full system.

- [EditAgent: Rethinking Agentic Image Editing](https://arxiv.org/abs/2610.39664)
- [BAGEL official implementation](https://github.com/ByteDance-Seed/Bagel)
