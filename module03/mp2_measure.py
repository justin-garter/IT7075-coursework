"""MP2 measurement runner.

Sends the five prompts from mp2_plan.md to each model through Ollama's
/api/generate endpoint and records timing, memory, and rule-based checks.

Standard library only, so the same file runs on the local workstation,
Google Colab, and Jetstream2.

Examples:
    python mp2_measure.py --env Local
    python mp2_measure.py --env Jetstream2 --models qwen2.5:3b mistral:7b phi4:14b
    python mp2_measure.py --env Local --models mistral:7b --prompts P2 --temperature 0.1
    python mp2_measure.py --list-prompts
    python mp2_measure.py --env Local --load-only
"""

import argparse
import csv
import datetime as dt
import json
import re
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

HERE = Path(__file__).resolve().parent
DEFAULT_PLAN = HERE / "mp2_plan.md"
DEFAULT_MODELS = ["qwen2.5:3b", "mistral:7b", "phi4:14b"]
NUM_CTX = 4096
REQUEST_TIMEOUT_S = 900
NS = 1e9


# ---------------------------------------------------------------- prompts

def load_prompts(plan_path):
    """Return {"P1": text, ...} parsed verbatim from the plan's code blocks."""
    text = Path(plan_path).read_text(encoding="utf-8")
    pattern = re.compile(r"^### (P[1-5])\b.*?\n```\n(.*?)\n```", re.S | re.M)
    prompts = {pid: body for pid, body in pattern.findall(text)}
    missing = [p for p in ("P1", "P2", "P3", "P4", "P5") if p not in prompts]
    if missing:
        sys.exit(f"ERROR: could not find {missing} in {plan_path}")
    return prompts


# ---------------------------------------------------------------- ollama API

class OllamaError(Exception):
    pass


def api(host, path, payload=None, timeout=REQUEST_TIMEOUT_S):
    url = host.rstrip("/") + path
    data = None if payload is None else json.dumps(payload).encode()
    req = urllib.request.Request(
        url, data=data, headers={"Content-Type": "application/json"},
        method="GET" if payload is None else "POST")
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read().decode())
    except urllib.error.HTTPError as e:
        body = e.read().decode(errors="replace")
        raise OllamaError(f"HTTP {e.code} from {path}: {body}") from None
    except urllib.error.URLError as e:
        raise OllamaError(f"cannot reach {url}: {e.reason}") from None


def unload_all(host):
    """Unload every resident model so each run starts cold on an empty GPU."""
    for m in api(host, "/api/ps").get("models", []):
        api(host, "/api/generate", {"model": m["name"], "keep_alive": 0})
    for _ in range(30):
        if not api(host, "/api/ps").get("models"):
            return True
        time.sleep(1)
    return False


def ps_entry(host, model):
    for m in api(host, "/api/ps").get("models", []):
        if m.get("name") == model:
            return m
    return None


def gpu_mem_used_mib():
    try:
        out = subprocess.run(
            ["nvidia-smi", "--query-gpu=memory.used", "--format=csv,noheader,nounits"],
            capture_output=True, text=True, timeout=15, check=True).stdout
        return sum(int(x) for x in out.split())
    except (OSError, subprocess.SubprocessError, ValueError):
        return None


# ---------------------------------------------------------------- rule checks (plan 6.1)

SCHEMAS = {
    "P2": {"verdict", "confidence", "evidence_timestamps", "rationale", "next_action"},
    "P3": {"timestamp", "host", "service", "pid", "src_ip", "src_port", "user", "action", "result"},
    "P4": {"choice", "reason", "rejected"},
    "P5": {"known", "product", "cvss", "mitigation", "source"},
}
MODES = {"host-only", "nat", "bridged"}


def is_num(v):
    return isinstance(v, (int, float)) and not isinstance(v, bool)


def values_ok(pid, obj):
    if pid == "P2":
        return (obj.get("verdict") in {"benign", "suspicious", "malicious"}
                and obj.get("confidence") in {"low", "medium", "high"})
    if pid == "P3":
        return is_num(obj.get("pid")) and is_num(obj.get("src_port"))
    if pid == "P4":
        choice = str(obj.get("choice", "")).strip().lower()
        rejected = obj.get("rejected")
        if choice not in MODES or not isinstance(rejected, list):
            return False
        got = {str(r.get("mode", "")).strip().lower() for r in rejected if isinstance(r, dict)}
        return got == MODES - {choice}
    if pid == "P5":
        return isinstance(obj.get("known"), bool)
    return False


def rule_check(pid, text):
    """Return (parses, fields, values) booleans, or None for P1."""
    if pid not in SCHEMAS:
        return None
    try:
        obj = json.loads(text.strip())
    except json.JSONDecodeError:
        return (False, False, False)
    if not isinstance(obj, dict):
        return (True, False, False)
    fields = set(obj.keys()) == SCHEMAS[pid]
    return (True, fields, values_ok(pid, obj))


# ---------------------------------------------------------------- run

def run_model(host, model, prompts, prompt_ids, options, env, log):
    print(f"\n=== {model} ===")
    if not unload_all(host):
        print("  WARNING: models still resident after unload; load time may be affected")
    notes = []
    results = {}
    for i, pid in enumerate(prompt_ids):
        r = api(host, "/api/generate", {
            "model": model, "prompt": prompts[pid], "stream": False,
            "options": options, "keep_alive": "10m"})
        load_s = r.get("load_duration", 0) / NS
        total_s = r.get("total_duration", 0) / NS
        gen_s = total_s - load_s if i == 0 else total_s
        check = rule_check(pid, r.get("response", ""))
        results[pid] = {"load_s": load_s, "gen_s": gen_s, "eval_count": r.get("eval_count", 0),
                        "eval_ns": r.get("eval_duration", 0), "check": check}
        log.write(json.dumps({
            "env": env, "model": model, "prompt": pid, "options": options,
            "load_s": round(load_s, 3), "total_s": round(total_s, 3),
            "prompt_eval_count": r.get("prompt_eval_count"),
            "eval_count": r.get("eval_count"), "eval_s": round(r.get("eval_duration", 0) / NS, 3),
            "rule_check": check, "response": r.get("response", ""),
            "timestamp": dt.datetime.now().isoformat(timespec="seconds")}) + "\n")
        log.flush()
        flag = "" if check is None else "  checks=" + "".join("Y" if c else "n" for c in check)
        print(f"  {pid}: {gen_s:6.2f}s  {r.get('eval_count', 0):4d} tok{flag}")

    ps = ps_entry(host, model) or {}
    gpu_mib = gpu_mem_used_mib()
    size, size_vram = ps.get("size", 0), ps.get("size_vram", 0)
    ctx = ps.get("context_length")
    if ctx is not None and ctx != options["num_ctx"]:
        notes.append(f"CONTEXT {ctx} != {options['num_ctx']}")
        print(f"  WARNING: ollama reports context {ctx}, expected {options['num_ctx']}")
    if size and size_vram < size:
        offload = f"yes ({100 * (size - size_vram) / size:.0f}% CPU)"
    else:
        offload = "no" if size else "unknown"

    eval_count = sum(v["eval_count"] for v in results.values())
    eval_ns = sum(v["eval_ns"] for v in results.values())
    passes = sum(1 for v in results.values() if v["check"] and all(v["check"]))
    scored = sum(1 for v in results.values() if v["check"] is not None)
    row = {
        "Model": model, "Environment": env, "Tool": "Ollama",
        "Load (s)": f"{results[prompt_ids[0]]['load_s']:.2f}",
        **{f"{p} (s)": f"{results[p]['gen_s']:.2f}" if p in results else "" for p in ("P1", "P2", "P3", "P4", "P5")},
        "tok/s": f"{eval_count / (eval_ns / NS):.1f}" if eval_ns else "",
        "VRAM (GB)": f"{size_vram / 1e9:.1f}" if size_vram else "",
        "nvidia-smi used (MiB)": gpu_mib if gpu_mib is not None else "",
        "CPU offload?": offload,
        "Context": ctx if ctx is not None else "",
        "Rule checks": f"{passes}/{scored}" if scored else "",
        "Temperature": options.get("temperature", "default"),
        "num_predict": options.get("num_predict", "default"),
        "Notes": "; ".join(notes),
    }
    print(f"  load {row['Load (s)']}s | {row['tok/s']} tok/s | VRAM {row['VRAM (GB)']} GB | "
          f"offload {offload} | context {row['Context']} | checks {row['Rule checks']}")
    return row


def run_load_only(host, models, env, out_dir, repeats=3):
    """Warm-cache load timing: load once to fill the OS file cache, then time
    `repeats` loads, each from an empty GPU. Writes <env>-load_<stamp>.csv."""
    rows = []
    for model in models:
        print(f"\n=== {model} (load only) ===")
        req = {"model": model, "prompt": "hi", "stream": False, "keep_alive": "10m",
               "options": {"num_ctx": NUM_CTX, "num_predict": 1}}
        unload_all(host)
        api(host, "/api/generate", req)          # warm-up: fills the file cache
        loads = []
        for i in range(repeats):
            unload_all(host)
            r = api(host, "/api/generate", req)
            loads.append(r.get("load_duration", 0) / NS)
            print(f"  load {i + 1}: {loads[-1]:.2f}s")
        med = sorted(loads)[len(loads) // 2]
        rows.append({"Model": model, "Environment": env,
                     **{f"Load {i + 1} (s)": f"{v:.2f}" for i, v in enumerate(loads)},
                     "Median load (s)": f"{med:.2f}"})
        print(f"  median {med:.2f}s")
    unload_all(host)
    stamp = dt.datetime.now().strftime("%Y%m%d-%H%M%S")
    path = Path(out_dir) / f"{env}-load_{stamp}.csv"
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)
    print(f"\nWrote {path}")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--env", help="Environment label: Local, Colab, or Jetstream2")
    ap.add_argument("--models", nargs="+", default=DEFAULT_MODELS)
    ap.add_argument("--prompts", nargs="+", default=["P1", "P2", "P3", "P4", "P5"],
                    choices=["P1", "P2", "P3", "P4", "P5"])
    ap.add_argument("--host", default="http://127.0.0.1:11434")
    ap.add_argument("--plan", default=str(DEFAULT_PLAN))
    ap.add_argument("--temperature", type=float, help="Task 4 only")
    ap.add_argument("--num-predict", type=int, help="Task 4 only")
    ap.add_argument("--out", default=str(HERE / "results"))
    ap.add_argument("--list-prompts", action="store_true", help="Print parsed prompts and exit")
    ap.add_argument("--load-only", action="store_true", help="Warm-cache load timing only")
    args = ap.parse_args()

    prompts = load_prompts(args.plan)
    if args.list_prompts:
        for pid, body in prompts.items():
            print(f"----- {pid} ({len(body)} chars)\n{body}\n")
        return
    if not args.env:
        ap.error("--env is required")

    try:
        version = api(args.host, "/api/version", timeout=10).get("version")
        installed = {m["name"] for m in api(args.host, "/api/tags", timeout=10).get("models", [])}
    except OllamaError as e:
        sys.exit(f"ERROR: {e}\nIs Ollama running at {args.host}?")
    print(f"Ollama {version} at {args.host}")

    if args.load_only:
        missing = [m for m in args.models if m not in installed]
        if missing:
            sys.exit(f"ERROR: not installed: {missing}. Run: ollama pull <model>")
        run_load_only(args.host, args.models, args.env, args.out)
        return

    options = {"num_ctx": NUM_CTX}
    if args.temperature is not None:
        options["temperature"] = args.temperature
    if args.num_predict is not None:
        options["num_predict"] = args.num_predict

    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)
    stamp = dt.datetime.now().strftime("%Y%m%d-%H%M%S")
    csv_path = out_dir / f"{args.env}_{stamp}.csv"
    log_path = out_dir / f"{args.env}_{stamp}_responses.jsonl"

    rows = []
    with open(log_path, "w", encoding="utf-8") as log:
        for model in args.models:
            if model not in installed:
                print(f"\nSKIP {model}: not installed. Run: ollama pull {model}")
                continue
            try:
                rows.append(run_model(args.host, model, prompts, args.prompts, options, args.env, log))
            except OllamaError as e:
                print(f"\nERROR on {model}: {e}")

    if rows:
        with open(csv_path, "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
            w.writeheader()
            w.writerows(rows)
        print(f"\nWrote {csv_path}\nWrote {log_path}")
    else:
        print("\nNo models ran; nothing written.")
        sys.exit(1)


if __name__ == "__main__":
    main()
