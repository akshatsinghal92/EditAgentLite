# Akshat's pilot setup and handoff

## Fixed inputs and routes

`pilot/manifest.csv` contains eight Complex-Edit real-image atomic tasks: four removal and four global brightness requests. `scripts/prepare_pilot.py` retrieves the images. `pilot/screening_log.csv` records three excluded removal candidates. The pilot selection and removal masks were frozen from source images before inspecting model edits.

The edit routes are:

| Route | Task | Input | Compute |
| --- | --- | --- | --- |
| `tool` | global lighting | source image, fixed brightness and contrast factors | CPU |
| `inpaint` | removal | source image, human polygon mask in `pilot/removal_masks.json` | CPU |
| `bagel` | removal | source image, original instruction | L4 GPU, BAGEL NF4 |

The inpainting masks require human annotation. Report this separately from inference time. Do not present the route as autonomous segmentation. The tool is an optional low-compute comparison; BAGEL remains the intended first removal action for the midterm sequential workflow.

## Frozen Stage A handoff to Ashvin

The setup commit contains `pilot/manifest.csv` (eight tasks), `pilot/screening_log.csv` (three source-screened exclusions), scripts, and this guide. Keep `pilot/manifest.csv`, prompts, seeds, and BAGEL's 30-step setting fixed during the planned first experiment. Raw images, model weights, generated images, and credentials stay outside Git.

Actual source/model revisions from the VM on November 13, 2026:

| Component | Revision or version |
| --- | --- |
| BAGEL source | `a2fa77dd8caeefc41e6607ae0ec17408d3f4ee9f` |
| BAGEL checkpoint | `5019f57d168e5816e8f3f701b17cc816bb7cf24b` |
| Qwen checkpoint | `1de27d8c51f12e819435303b9e84c4e25ba8401e` |
| GPU | NVIDIA L4, 23 GB |
| BAGEL runtime | NF4; Torch 2.7.1+cu128, Transformers 4.49.0, FlashAttention 2.8.3 |
| Qwen runtime | bfloat16; Torch 2.7.1+cu128, Transformers 5.20.2 |

The default data directory is `data/complex_edit/real/images/`, populated by `python3 scripts/prepare_pilot.py` before the manifest is frozen. In a clean checkout where the manifest already exists, download the 8 listed source images from the public Complex-Edit `test/real/` files to this directory; do not rerun selection. Set `EDITAGENTLITE_DATA_ROOT` to an absolute directory of those image files when using a shared copy. Scripts resolve each manifest basename under that directory. The VM already has all eight images. The output directory is `outputs/`, which is ignored by Git.

Ashvin's exact first-pass command on the VM is:

```bash
cd ~/EditAgentLite
.venv-qwen/bin/python scripts/run_first.py --resume
```

This processes the frozen manifest in order: BAGEL for the four removal tasks, Pillow for the four lighting tasks. It writes `outputs/pilot/<task-id>/<route>/first/edited.png`, a per-call `run.json`, and `outputs/pilot_artifacts/first_outputs.jsonl`. `--resume` skips completed tasks with a log row and image. On an execution failure, the script writes a failure row and exits; rerun once with the same settings, record both rows, and stop if it fails again. The command never overwrites an existing first image. The previous component smoke outputs outside the `first/` subfolder are not frozen Stage B results.

Shubhangi's checker contract is:

```bash
cd ~/EditAgentLite
.venv-qwen/bin/python scripts/run_check_repair.py --max-repairs 0
```

It reads completed rows in `first_outputs.jsonl`, uses the source plus frozen first image, saves Qwen's raw and parsed response in each task's `agent/midterm_check.json`, and appends `outputs/pilot_artifacts/checks.jsonl`. `--max-repairs 0` is the Stage A check-only smoke path. For Stage C, `--max-repairs 2` additionally attempts the first two supported BAGEL removal repairs from original images, writing `repair_outputs.jsonl` and `bagel/repair/edited.png`. The current handoff does not implement lighting-parameter repair; those are logged `unsupported_repair`, and the next flagged removal can be considered. Human ratings, final selection, and contact sheet remain Shubhangi's Stage C work.

The repo also contains `scripts/run_agentic_one.py` for a separate one-task route-choice experiment. Its adaptive first route does not match the frozen midterm first-action protocol, so do not mix its outputs into Stage B counts.

## Reproduce on the VM

The GCP VM is `editagentlite-spot` in project `cs771-513220`, zone `us-east1-c`. It is a Spot `g2-standard-8` with one NVIDIA L4. Spot capacity may disappear; store outputs in the repo directory and copy them off the VM after each stage.

```bash
bash scripts/setup_vm.sh
.venv-qwen/bin/python scripts/download_models.py
python3 scripts/prepare_pilot.py
python3 scripts/run_pilot.py --task-id lighting_0093_0 --route tool
.venv-qwen/bin/python scripts/run_pilot.py --task-id removal_0088_0 --route inpaint
.venv-bagel/bin/python scripts/run_pilot.py --task-id removal_0088_0 --route bagel
.venv-qwen/bin/python scripts/check_edit.py --task-id removal_0088_0 --route bagel
```

Each edit writes `outputs/pilot/<task-id>/<route>/edited.png` and `run.json`. The inpainting route also writes `human_mask.png`. The checker writes `qwen_check.json`. `outputs/`, `models/`, and dataset images are untracked. Share a subset of pilot results through the team handoff without committing large or licensed image files.

## Status

The four lighting tool calls and four OpenCV inpainting calls have completed on the VM. Visual inspection found conspicuous artifacts and incomplete removal in the inpainting outputs, especially where large objects cross textured backgrounds. This is a useful failure case, not a successful removal claim.

One BAGEL removal and Qwen assessment smoke test also completed for `removal_0088_0`. BAGEL NF4 loaded in 134.94 s, generated a 30-step edit in 56.31 s, and peaked at 9.64 GB allocated GPU memory. Qwen assessed the pair in 10.30 s, peaked at 9.08 GB allocated GPU memory, and returned `pass`; its successful rerun loaded weights in 3.72 s with the local file cache warm. The initial cold Qwen load took about 3 minutes 41 seconds and reached the same completed weight load, but the assessment then stopped because Jinja2 was too old; the dependency was upgraded before the successful rerun. The output and JSON records are in `outputs/pilot/removal_0088_0/bagel/` on the VM and in the local ignored `outputs/` directory. A human glance confirms the spoon is removed, while some food detail changed. Treat this as one successful smoke test, not an evaluation result.

The VM initially preempted during installation. The repaired BAGEL environment reuses the Deep Learning VM's CUDA Torch 2.7.1, with Transformers 4.49.0 and FlashAttention 2.8.3; Qwen uses Transformers 5.20.2. The Qwen environment also requires Jinja2 3.1 or newer for its chat template.
