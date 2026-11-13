# EditAgentLite

EditAgentLite is a two-week, three-person course project on **budget-aware image editing**. A small vision-language model (VLM) checks a first edit, classifies a failure if one occurs, and chooses at most one targeted repair. The project tests whether this selective workflow gives better results per editing call than simple alternatives.

## Research question

With a maximum of two editing actions, does failure-specific repair improve edit success over a one-shot edit and two independent edits, while using fewer than two actions on average?

## Scope

- Single source image and one instruction per task; no multi-turn conversations or model training.
- Two edit types: **object removal** and **brightness/contrast adjustment**. These exercise a learned image editor and a cheap deterministic tool.
- One small VLM controller, one general image editor, and one deterministic brightness/contrast tool. Add a removal specialist only if it is already available and straightforward to run.
- At most two editing actions per task. No broad tool search or full EditAgent reproduction.
- A hand-checked set of **40 tasks** (20 per edit type), split into 10 development and 30 final test tasks.

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
2. **Two-sample baseline:** two independent attempts from the same source, then select the better result.
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

By day 7, the system must run on the 10 development tasks, save both candidate images when a repair occurs, and produce a machine-readable trace. If that milestone slips, use the general editor plus deterministic tool, drop optional specialists, and preserve the three-condition evaluation.

## Deliverables

- Reproducible code and setup instructions
- Frozen 40-task list and evaluation rubric
- Test outputs and anonymized human ratings
- Short report with quality-versus-cost results and limitations
- Small demo showing a first edit, failure diagnosis, repair, and final result

## Related work

EditAgent already uses tool routing, verification, feedback, and retries. This project focuses on a much smaller two-action policy and its quality-cost tradeoff; it does not claim to invent feedback-based editing or reproduce EditAgent's full system.

- [EditAgent: Rethinking Agentic Image Editing](https://arxiv.org/abs/2610.39664)
