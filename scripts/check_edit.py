#!/usr/bin/env python3
"""Inspect one saved edit with Qwen3-VL and record a structured diagnosis."""

import argparse
import csv
import json
import time
from pathlib import Path

import torch
from PIL import Image
from transformers import AutoProcessor, Qwen3VLForConditionalGeneration

ROOT = Path(__file__).resolve().parents[1]
LABELS = "pass, incomplete_edit, wrong_target, unwanted_change, wrong_strength, artifact, uncertain"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--task-id", required=True)
    parser.add_argument("--route", choices=["tool", "bagel"], required=True)
    parser.add_argument("--max-new-tokens", type=int, default=256)
    args = parser.parse_args()
    with (ROOT / "pilot/manifest.csv").open(newline="") as handle:
        task = next(row for row in csv.DictReader(handle) if row["task_id"] == args.task_id)
    edited = ROOT / "outputs/pilot" / args.task_id / args.route / "edited.png"
    original = Image.open(ROOT / task["source_path"]).convert("RGB")
    output = Image.open(edited).convert("RGB")
    model_path = ROOT / "models/Qwen3-VL-4B-Thinking"
    start = time.monotonic()
    model = Qwen3VLForConditionalGeneration.from_pretrained(
        model_path, torch_dtype=torch.bfloat16, device_map="auto"
    ).eval()
    processor = AutoProcessor.from_pretrained(model_path)
    load_seconds = time.monotonic() - start
    prompt = (
        "Compare ORIGINAL and EDITED for this request: " + task["instruction"] + "\n"
        "Return only a JSON object with keys label, observed_error, suggested_repair, "
        "preservation_requirement. label must be one of: " + LABELS + ". "
        "Be conservative: use uncertain when the edit cannot be judged. "
        "A suggested repair must be a short edit instruction or a brightness/contrast factor adjustment."
    )
    messages = [{"role": "user", "content": [
        {"type": "text", "text": "ORIGINAL"}, {"type": "image", "image": original},
        {"type": "text", "text": "EDITED"}, {"type": "image", "image": output},
        {"type": "text", "text": prompt},
    ]}]
    text = processor.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
    inputs = processor(text=[text], images=[original, output], return_tensors="pt").to(model.device)
    start = time.monotonic()
    with torch.inference_mode():
        generated = model.generate(**inputs, max_new_tokens=args.max_new_tokens, do_sample=False)
    answer = processor.batch_decode(generated[:, inputs.input_ids.shape[1]:], skip_special_tokens=True)[0]
    elapsed = time.monotonic() - start
    record = {"task_id": args.task_id, "route": args.route, "model": str(model_path),
              "load_seconds": round(load_seconds, 2), "elapsed_seconds": round(elapsed, 2),
              "raw_answer": answer, "peak_gpu_bytes": torch.cuda.max_memory_allocated()}
    target = edited.parent / "qwen_check.json"
    target.write_text(json.dumps(record, indent=2) + "\n")
    print(json.dumps(record, indent=2))


if __name__ == "__main__":
    main()
