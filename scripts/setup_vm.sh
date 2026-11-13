#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$repo_root"

sudo apt-get update
sudo DEBIAN_FRONTEND=noninteractive apt-get install -y python3.10-venv git git-lfs
git lfs install --skip-repo

mkdir -p external models data outputs
if [[ ! -d external/Bagel/.git ]]; then
  git clone --depth 1 https://github.com/ByteDance-Seed/Bagel.git external/Bagel
fi
git -C external/Bagel rev-parse HEAD | tee external/bagel_commit.txt

if [[ ! -d .venv-bagel ]]; then
  python3 -m venv .venv-bagel
fi
.venv-bagel/bin/python -m pip install --upgrade pip setuptools wheel ninja packaging
.venv-bagel/bin/python -m pip install -r external/Bagel/requirements.txt
MAX_JOBS=4 .venv-bagel/bin/python -m pip install flash_attn==2.5.8 --no-build-isolation

if [[ ! -d .venv-qwen ]]; then
  python3 -m venv --system-site-packages .venv-qwen
fi
.venv-qwen/bin/python -m pip install --upgrade pip
.venv-qwen/bin/python -m pip install --upgrade 'transformers>=4.57.0' accelerate huggingface_hub pillow opencv-python-headless qwen-vl-utils

echo "Environment setup complete. Run scripts/download_models.py next."
