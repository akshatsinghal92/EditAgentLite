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

One BAGEL removal and Qwen assessment smoke test also completed for `removal_0088_0`. BAGEL NF4 loaded in 134.94 s, generated a 30-step edit in 56.31 s, and peaked at 9.64 GB allocated GPU memory. Qwen loaded in 3.72 s on the warm rerun, assessed the pair in 10.30 s, peaked at 9.08 GB allocated GPU memory, and returned `pass`. The output and JSON records are in `outputs/pilot/removal_0088_0/bagel/` on the VM and in the local ignored `outputs/` directory. A human glance confirms the spoon is removed, while some food detail changed. Treat this as one successful smoke test, not an evaluation result.

The VM initially preempted during installation. The repaired BAGEL environment reuses the Deep Learning VM's CUDA Torch 2.7.1, with Transformers 4.49.0 and FlashAttention 2.8.3; Qwen uses Transformers 5.20.2. The Qwen environment also requires Jinja2 3.1 or newer for its chat template.
