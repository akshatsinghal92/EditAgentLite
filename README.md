# EditAgentLite

EditAgentLite is a two-week, three-person course project on **budget-aware image editing**. Qwen3-VL-4B-Thinking checks a first edit, classifies a failure if one occurs, and chooses at most one targeted repair. BAGEL-7B-MoT is the fixed learned image editor. The project tests whether this selective workflow gives better results per editing call than simple alternatives.

## Research question

With a maximum of two editing actions, does failure-specific repair improve edit success over a one-shot edit and two independent edits, while using fewer than two actions on average?

## Scope

- Single source image and one instruction per task; no multi-turn conversations or model training.
- Two edit types: **object removal** and **brightness/contrast adjustment**. These exercise a learned image editor and a cheap deterministic tool.
- **Controller:** [Qwen3-VL-4B-Thinking](https://huggingface.co/Qwen/Qwen3-VL-4B-Thinking) for planning, inspection, failure classification, and candidate selection.
- **Learned editor:** [BAGEL-7B-MoT](https://huggingface.co/ByteDance-Seed/BAGEL-7B-MoT) for image edits. Keep its checkpoint and generation settings fixed across conditions.
- **Cheap tool:** a deterministic brightness/contrast operator. Add a removal specialist only if it is already available and straightforward to run.
- At most two editing actions per task. No broad tool search or full EditAgent reproduction.
- A hand-checked set of **40 tasks** (20 per edit type), split into 10 development and 30 final test tasks.

BAGEL has 14B total parameters and 7B active parameters; it is not a small or cheap editor in absolute terms. The official setup calls for 32GB+ GPU memory for standard inference or NF4 quantization for 12–32GB. On days 1–2, run one end-to-end editing smoke test at the intended resolution and record GPU memory and latency before committing to the full evaluation. If local BAGEL inference is unavailable, use a hosted BAGEL endpoint if permitted by the course budget; report its actual cost. Do not silently substitute another editor in the final comparison.

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
2. **Two-sample baseline:** two independent BAGEL attempts from the same source, then select the better result. For deterministic brightness/contrast requests, use two predeclared parameter settings so this baseline actually yields two different outputs.
3. **EditAgentLite:** first edit, early stop or one failure-specific repair.

Use a short rubric: requested change succeeds, unrelated content is preserved, and result is visually usable. All three team members independently review the anonymized outputs, then resolve disagreements. Report success counts by edit type, average editing actions, average wall-clock time, and a small gallery of successes and failures. Treat VLM self-scores as diagnostics, not ground truth. Do not claim statistical significance from 30 test tasks.

## Two-week schedule and ownership

| Time | Member A: pipeline | Member B: controller | Member C: evaluation | Shared checkpoint |
| --- | --- | --- | --- | --- |
| Days 1–2 | Select and smoke-test editor/tool | Define structured controller output and prompts | Select 40 tasks and rubric | Freeze models, task list, and budget |
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
