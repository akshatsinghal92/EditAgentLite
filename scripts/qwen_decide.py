#!/usr/bin/env python3
"""One Qwen route or edit-review call for the pilot controller."""

import argparse
import csv
import json
import os
import re
import time
from pathlib import Path

import torch
from PIL import Image
from transformers import AutoProcessor, Qwen3VLForConditionalGeneration

ROOT = Path(__file__).resolve().parents[1]


def extract_json(text):
    for match in reversed(list(re.finditer(r"\{[\s\S]*?\}", text))):
        try:
            return json.loads(match.group())
        except json.JSONDecodeError:
            continue
    raise ValueError(f"Qwen did not return a JSON object: {text}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=["route", "review"], required=True)
    parser.add_argument("--task-id", required=True)
    parser.add_argument("--edited-image")
    parser.add_argument("--output", required=True)
    parser.add_argument("--max-new-tokens", type=int, default=768)
    args = parser.parse_args()

    with (ROOT / "pilot/manifest.csv").open(newline="") as handle:
        task = next(row for row in csv.DictReader(handle) if row["task_id"] == args.task_id)
    source_path = (Path(os.environ["EDITAGENTLITE_DATA_ROOT"]) / Path(task["source_path"]).name
                   if os.environ.get("EDITAGENTLITE_DATA_ROOT") else ROOT / task["source_path"])
    original = Image.open(source_path).convert("RGB")
    content = [{"type": "text", "text": f"Original image. Task: {task['instruction']}"},
               {"type": "image", "image": original}]

    if args.mode == "route":
        if task["category"] == "removal":
            choices = (
                "inpaint: a CPU OpenCV Telea fill using the already prepared human mask; "
                "very cheap but may leave artifacts. bagel: BAGEL-7B-MoT NF4 generative editing; "
                "slower but can synthesize plausible background."
            )
            schema = (
            'Output one JSON object only; no explanation before or after it. '
                '{"route":"inpaint" or "bagel","reason":"at most 8 words",'
                '"risk":"at most 8 words"}'
            )
        else:
            choices = (
                "tool: deterministic CPU brightness/contrast adjustment; very cheap. "
                "bagel: BAGEL-7B-MoT NF4 generative editing; slower."
            )
            schema = (
                'Output one JSON object only; no explanation before or after it. '
                '{"route":"tool" or "bagel","reason":"at most 8 words",'
                '"risk":"at most 8 words"}'
            )
        prompt = (
            f"Task: {task['instruction']} Available routes: {choices} "
            "Choose the least costly route reasonably capable of this edit. "
            "Consider preservation risk. " + schema
        )
    else:
        if not args.edited_image:
            raise ValueError("--edited-image is required in review mode")
        edited = Image.open(args.edited_image).convert("RGB")
        content += [{"type": "text", "text": "Edited result."},
                    {"type": "image", "image": edited}]
        repair_rule = (
            'If the edit fails, use repair_action "bagel" and give a short repair_instruction '
            'from the original image.' if task["category"] == "removal" else
            'If the edit fails, use repair_action "tool" and give a numeric brightness_factor '
            'between 0.5 and 2.0 for a new edit from the original image. The first factor was 1.25.'
        )
        prompt = (
            f"Review the edit against this request: {task['instruction']} "
            "Compare the original and edited images. Mark pass only if the requested change "
            "is clearly completed and unrelated image content is reasonably preserved. "
            "Use one label from pass, incomplete_edit, wrong_target, unwanted_change, "
            "wrong_strength, artifact, uncertain. " + repair_rule + " "
            "Use repair_action none only when label is pass. "
            'Output one JSON object only; no explanation before or after it. '
            '{"label":"...","observed_error":"... or null",'
            '"repair_action":"bagel, tool, or none","repair_instruction":"... or null",'
            '"brightness_factor":number or null,'
            '"preservation_requirement":"... or null"}'
        )
    content.append({"type": "text", "text": prompt})
    messages = [{"role": "user", "content": content}]

    started = time.monotonic()
    model_path = ROOT / "models/Qwen3-VL-4B-Thinking"
    model = Qwen3VLForConditionalGeneration.from_pretrained(
        model_path, torch_dtype=torch.bfloat16, device_map="auto"
    ).eval()
    processor = AutoProcessor.from_pretrained(model_path)
    load_seconds = time.monotonic() - started
    text = processor.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
    images = [original] if args.mode == "route" else [original, edited]
    inputs = processor(text=[text], images=images, return_tensors="pt").to(model.device)
    started = time.monotonic()
    with torch.inference_mode():
        generated = model.generate(
            **inputs, max_new_tokens=args.max_new_tokens, do_sample=False
        )
    raw = processor.batch_decode(
        generated[:, inputs.input_ids.shape[1]:], skip_special_tokens=True
    )[0]
    elapsed = time.monotonic() - started
    try:
        decision = extract_json(raw)
        parse_error = None
    except ValueError as exc:
        decision = None
        parse_error = str(exc)
    record = {
        "mode": args.mode,
        "task_id": args.task_id,
        "model_revision": "1de27d8c51f12e819435303b9e84c4e25ba8401e",
        "prompt_version": "midterm-review-v2",
        "load_seconds": round(load_seconds, 2),
        "inference_seconds": round(elapsed, 2),
        "decision": decision,
        "parse_error": parse_error,
        "raw_answer": raw,
        "peak_gpu_bytes": torch.cuda.max_memory_allocated(),
    }
    output = ROOT / args.output
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(record, indent=2) + "\n")
    print(json.dumps(record, indent=2))


if __name__ == "__main__":
    main()
