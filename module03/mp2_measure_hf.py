"""MP2 Hugging Face transformers runner.

Downloads a model directly from Hugging Face, loads it in 4-bit (bitsandbytes
NF4), sends the five prompts from mp2_plan.md, and writes results in the same
format as mp2_measure.py.

Example (Colab, T4 GPU runtime):
    python mp2_measure_hf.py --env Colab
"""

import argparse
import csv
import datetime as dt
import json
import sys
import time
from pathlib import Path

import torch
from huggingface_hub import snapshot_download
from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig

from mp2_measure import DEFAULT_PLAN, HERE, load_prompts, rule_check

PROMPT_IDS = ["P1", "P2", "P3", "P4", "P5"]


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--env", default="Colab")
    ap.add_argument("--model", default="Qwen/Qwen2.5-3B-Instruct")
    ap.add_argument("--max-new-tokens", type=int, default=1024)
    ap.add_argument("--plan", default=str(DEFAULT_PLAN))
    ap.add_argument("--out", default=str(HERE / "results"))
    args = ap.parse_args()

    if not torch.cuda.is_available():
        sys.exit("ERROR: no CUDA GPU. In Colab: Runtime > Change runtime type > T4 GPU.")
    prompts = load_prompts(args.plan)
    print(f"GPU: {torch.cuda.get_device_name(0)} | model: {args.model}")

    t0 = time.perf_counter()
    local_path = snapshot_download(args.model)
    download_s = time.perf_counter() - t0
    print(f"download/cache check: {download_s:.1f}s")

    torch.cuda.reset_peak_memory_stats()
    t0 = time.perf_counter()
    tok = AutoTokenizer.from_pretrained(local_path)
    bnb = BitsAndBytesConfig(load_in_4bit=True, bnb_4bit_quant_type="nf4",
                             bnb_4bit_compute_dtype=torch.float16)
    model = AutoModelForCausalLM.from_pretrained(local_path, quantization_config=bnb, device_map="cuda:0")
    torch.cuda.synchronize()
    load_s = time.perf_counter() - t0
    devices = set(str(d) for d in getattr(model, "hf_device_map", {}).values())
    offload = "no" if devices <= {"0", "cuda:0"} else f"yes ({', '.join(sorted(devices))})"
    print(f"load: {load_s:.2f}s | device map: {devices or 'cuda:0'}")

    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)
    stamp = dt.datetime.now().strftime("%Y%m%d-%H%M%S")
    log_path = out_dir / f"{args.env}-HF_{stamp}_responses.jsonl"
    csv_path = out_dir / f"{args.env}-HF_{stamp}.csv"

    gen_times, new_tokens, checks = {}, 0, {}
    with open(log_path, "w", encoding="utf-8") as log:
        for pid in PROMPT_IDS:
            enc = tok.apply_chat_template([{"role": "user", "content": prompts[pid]}],
                                          add_generation_prompt=True, return_tensors="pt",
                                          return_dict=True).to("cuda:0")
            n_in = enc["input_ids"].shape[1]
            torch.cuda.synchronize()
            t0 = time.perf_counter()
            out = model.generate(**enc, max_new_tokens=args.max_new_tokens, pad_token_id=tok.eos_token_id)
            torch.cuda.synchronize()
            gen_s = time.perf_counter() - t0
            new = out[0][n_in:]
            text = tok.decode(new, skip_special_tokens=True)
            check = rule_check(pid, text)
            gen_times[pid], checks[pid] = gen_s, check
            new_tokens += len(new)
            log.write(json.dumps({
                "env": args.env, "tool": "transformers", "model": args.model, "prompt": pid,
                "options": {"max_new_tokens": args.max_new_tokens, "quant": "4-bit NF4"},
                "prompt_eval_count": n_in, "total_s": round(gen_s, 3), "eval_count": len(new),
                "rule_check": check, "response": text,
                "timestamp": dt.datetime.now().isoformat(timespec="seconds")}) + "\n")
            flag = "" if check is None else "  checks=" + "".join("Y" if c else "n" for c in check)
            print(f"  {pid}: {gen_s:6.2f}s  {len(new):4d} tok{flag}")

    peak_gb = torch.cuda.max_memory_allocated() / 1e9
    tps = new_tokens / sum(gen_times.values())
    scored = [c for c in checks.values() if c is not None]
    row = {
        "Model": args.model, "Environment": args.env, "Tool": "transformers",
        "Load (s)": f"{load_s:.2f}",
        **{f"{p} (s)": f"{gen_times[p]:.2f}" for p in PROMPT_IDS},
        "tok/s": f"{tps:.1f}", "VRAM (GB)": f"{peak_gb:.1f}", "CPU offload?": offload,
        "Rule checks": f"{sum(all(c) for c in scored)}/{len(scored)}",
        "max_new_tokens": args.max_new_tokens,
        "Notes": f"download {download_s:.1f}s; VRAM = torch peak allocated",
    }
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(row.keys()))
        w.writeheader()
        w.writerow(row)
    print(f"  load {row['Load (s)']}s | {row['tok/s']} tok/s | peak VRAM {row['VRAM (GB)']} GB | "
          f"offload {offload} | checks {row['Rule checks']}")
    print(f"\nWrote {csv_path}\nWrote {log_path}")


if __name__ == "__main__":
    main()
