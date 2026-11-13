# EditAgentLite

A budget-aware agentic image editing research project. A small vision-language controller chooses an initial low-cost editing action, checks the result, classifies any failure, and makes at most one targeted repair.

## Research question

Can selective, failure-specific repair improve edit success per unit of inference cost compared with one-shot editing, independent sampling, and a generic retry?

## Initial workflow

1. Parse the request into the intended change and preservation constraints.
2. Route to a cheap general editor or a deterministic/specialized image tool.
3. Check the edited image against the request and source image.
4. Accept a passing edit. Otherwise, classify the failure and choose one repair.
5. Compare the first and repaired candidates, then return the better result or flag failure.

The initial system permits at most two editing actions per request. Every decision should be logged with tool, latency, estimated cost, failure label, and outcome.

## Planned evaluation

- **Baselines:** one-shot cheap edit; two independent edits plus selection; generic retry; limited-tool parallel selection.
- **Outcomes:** edit success, preservation, artifacts, false acceptance, latency, editor/VLM calls, and estimated cost.
- **Ablations:** remove failure classification; remove early stopping.
- **Review:** blinded human ratings on a hand-checked test subset.

## Project phases

1. Freeze edit categories, budgets, baselines, and evaluation rubric.
2. Implement a common interface for editors and deterministic tools.
3. Implement planning, routing, checking, and failure classification.
4. Add targeted one-step repair and structured traces.
5. Run baselines, ablations, and human evaluation.
6. Analyze the quality-cost tradeoff and document failure cases.

## Status

Research plan and repository scaffold. Models, datasets, and implementation details are still to be selected.

## Related work

- [EditAgent: Rethinking Agentic Image Editing](https://arxiv.org/abs/2610.39664)
