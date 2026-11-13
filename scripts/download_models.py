#!/usr/bin/env python3
"""Download the public Qwen and BAGEL checkpoints to local, untracked paths."""

from pathlib import Path
from huggingface_hub import snapshot_download

root = Path(__file__).resolve().parents[1]
for repo_id, target in [
    ("Qwen/Qwen3-VL-4B-Thinking", root / "models" / "Qwen3-VL-4B-Thinking"),
    ("ByteDance-Seed/BAGEL-7B-MoT", root / "models" / "BAGEL-7B-MoT"),
]:
    target.mkdir(parents=True, exist_ok=True)
    print(f"Downloading {repo_id} to {target}", flush=True)
    snapshot_download(repo_id=repo_id, local_dir=target, max_workers=4)
    print(f"Finished {repo_id}", flush=True)
