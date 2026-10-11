# MP2 Data Plan (Section 5)

Justin Garter, IT7075C. Drafted 2026-09-22, before any installation.

The five prompts and the measurement tables below were fixed before any tool was
installed or any model was run. Deviations are logged in section 8.

Three environments are in scope: the local workstation, Google Colab, and Jetstream2.

---

## 1. The five prompts

All five go to every model in every environment verbatim, with no per-model tuning.
P1 and P2 use identical evidence at two levels of prompt structure.

### Shared evidence for P1 and P2
```
Nov 12 09:14:22 web01 sshd[2211]: Failed password for invalid user oracle from 198.51.100.44 port 51234 ssh2
Nov 12 09:14:23 web01 sshd[2213]: Failed password for invalid user oracle from 198.51.100.44 port 51240 ssh2
Nov 12 09:14:25 web01 sshd[2217]: Failed password for invalid user admin from 198.51.100.44 port 51255 ssh2
Nov 12 09:14:31 web01 sshd[2231]: Accepted password for admin from 198.51.100.44 port 51301 ssh2
```

### P1 — Alert triage, underspecified
```
Analyze this log.

Nov 12 09:14:22 web01 sshd[2211]: Failed password for invalid user oracle from 198.51.100.44 port 51234 ssh2
Nov 12 09:14:23 web01 sshd[2213]: Failed password for invalid user oracle from 198.51.100.44 port 51240 ssh2
Nov 12 09:14:25 web01 sshd[2217]: Failed password for invalid user admin from 198.51.100.44 port 51255 ssh2
Nov 12 09:14:31 web01 sshd[2231]: Accepted password for admin from 198.51.100.44 port 51301 ssh2
```

### P2 — Alert triage, fully specified
```
You are a SOC tier-1 analyst.

EVIDENCE:
Nov 12 09:14:22 web01 sshd[2211]: Failed password for invalid user oracle from 198.51.100.44 port 51234 ssh2
Nov 12 09:14:23 web01 sshd[2213]: Failed password for invalid user oracle from 198.51.100.44 port 51240 ssh2
Nov 12 09:14:25 web01 sshd[2217]: Failed password for invalid user admin from 198.51.100.44 port 51255 ssh2
Nov 12 09:14:31 web01 sshd[2231]: Accepted password for admin from 198.51.100.44 port 51301 ssh2

TASK:
Triage this activity and recommend an immediate next action.

CONSTRAINTS:
- Cite only the evidence above. Do not assume facts not present.
- Verdict must be exactly one of: benign, suspicious, malicious.
- Reference the specific timestamps that support the verdict.
- One sentence of rationale.

OUTPUT SCHEMA (JSON only, no prose, no markdown fences):
{"verdict": "", "confidence": "low|medium|high", "evidence_timestamps": [], "rationale": "", "next_action": ""}
```

### P3 — Field extraction
```
You are a log parser feeding a SIEM.

EVIDENCE:
Nov 12 09:14:22 web01 sshd[2211]: Failed password for invalid user oracle from 198.51.100.44 port 51234 ssh2

TASK:
Extract the structured fields.

CONSTRAINTS:
- Output valid JSON and nothing else. No markdown fences, no commentary.
- Use exactly the keys in the schema. Do not add keys.
- If a value is not present in the evidence, use null.
- src_port must be a number, not a string.

OUTPUT SCHEMA:
{"timestamp": "", "host": "", "service": "", "pid": null, "src_ip": "", "src_port": null, "user": "", "action": "", "result": ""}
```

### P4 — Design justification
```
You are a security engineer designing an isolated malware analysis lab.

EVIDENCE:
The lab host is a Windows workstation on a home network shared with other people's devices. The guest is a deliberately vulnerable, unpatched Linux virtual machine running exploitable network services.

TASK:
Choose a VirtualBox network mode for the guest and justify the choice.

CONSTRAINTS:
- Choose exactly one of: host-only, NAT, bridged.
- Give one reason for the choice.
- Give one reason each rejected mode is unsuitable.
- Under 150 words total.

OUTPUT SCHEMA (JSON only, no prose, no markdown fences):
{"choice": "", "reason": "", "rejected": [{"mode": "", "why_not": ""}]}
```

### P5 — Hallucination probe
```
You are a threat intelligence analyst.

EVIDENCE:
A vulnerability identifier has been escalated for review: CVE-2026-31337

TASK:
Report what is known about this CVE.

CONSTRAINTS:
- Report only what you can verify. If you do not know, say so explicitly.
- Do not infer details from the identifier's format or numbering.
- If it cannot be verified, set "known" to false and leave the other fields null.

OUTPUT SCHEMA (JSON only, no prose, no markdown fences):
{"known": true, "product": "", "cvss": null, "mitigation": "", "source": ""}
```

CVE-2026-31337 is fabricated. Expected correct behaviour is `"known": false`.

---

## 2. Models

| Model | Family | Params | Quant | ~VRAM | Source |
|---|---|---|---|---|---|
| `qwen2.5:3b` | Qwen | 3B | Q4_K_M | ~2 GB | Ollama library |
| `mistral:7b` | Mistral | 7B | Q4_K_M | ~4.4 GB | Ollama library |
| `phi4:14b` | Phi | 14B | Q4_K_M | ~9 GB | Ollama library |
| `Qwen/Qwen2.5-3B-Instruct` | Qwen | 3B | 4-bit NF4 (bitsandbytes) | ~2.5 GB | Hugging Face, via transformers |

---

## 3. Measurement method

**Timing and throughput** from Ollama's `/api/generate` with `stream: false`:

| Field | Meaning |
|---|---|
| `load_duration` | time to load the model into memory |
| `eval_count` | tokens generated |
| `eval_duration` | time spent generating |
| `total_duration` | wall clock for the whole request |

Tokens per second is `eval_count / (eval_duration / 1e9)`.

**Load time** measured on the first request after `ollama stop <model>`.

**Memory** from `nvidia-smi` during generation and from `ollama ps`, which reports
resident size and the CPU/GPU split.

**Context length** pinned at 4096 tokens in every environment. Ollama API calls set
`"options": {"num_ctx": 4096}`. Open WebUI sets Context Length to 4096 under the
model's advanced parameters. `ollama ps` confirms `CONTEXT 4096` for each run.

**Hugging Face transformers runs** use `time.perf_counter()` around the generate
call and `torch.cuda.max_memory_allocated()` for memory. Comparisons are drawn
within a measurement method, not across methods.

**Settings (Task 4).** Temperature at 0.1 and 1.0 on the same model and prompt.
Second setting varied is `num_predict` (maximum output tokens).

---

## 4. Environment and hardware

| | Local workstation | Google Colab (free T4) | Jetstream2 |
|---|---|---|---|
| Processor | AMD Ryzen 7 7800X3D | Intel Xeon @ 2.00GHz | AMD EPYC-Milan |
| Logical cores | 16 | 2 | 16 |
| System RAM | 31.1 GiB | 12 GiB | 58 GiB |
| GPU | NVIDIA GeForce RTX 5070 | NVIDIA Tesla T4 | NVIDIA GRID A100X-20C (vGPU slice of A100 SXM4 40GB) |
| VRAM | 12 GiB (12227 MiB) | 15 GiB (15360 MiB) | 20 GiB (20480 MiB) |
| Driver / CUDA | 616.92 / 13.4 | 580.82.07 / 13.0 | 580.159.03 / 13.0 |
| How I checked | `nvidia-smi`, `Get-CimInstance` | `nvidia-smi`, `lscpu`, `free -h` | `nvidia-smi`, `lscpu`, `free -h`, `lspci -nnk` |

---

## 5. Per-run measurements

One row per model per environment. The same five prompts in every row.

| Model | Params | Quant | Environment | Tool | Load (s) | P1 (s) | P2 (s) | P3 (s) | P4 (s) | P5 (s) | tok/s | VRAM (GB) | CPU offload? | Notes |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| qwen2.5:3b | 3B | Q4_K_M | Local | Ollama | 1.80 | 4.02 | 0.74 | 0.39 | 0.57 | 0.14 | 226.8 | 2.2 | no | rule checks 3/4 |
| mistral:7b | 7B | Q4_K_M | Local | Ollama | 2.26 | 2.23 | 1.43 | 0.98 | 1.16 | 0.47 | 125.7 | 5.0 | no | rule checks 3/4 |
| phi4:14b | 14B | Q4_K_M | Local | Ollama | 4.29 | 7.76 | 2.02 | 1.51 | 2.25 | 2.84 | 65.4 | 9.7 | no | rule checks 0/4 |
| qwen2.5:3b | 3B | Q4_K_M | Local | Open WebUI | 1.61 | 3.03 | 0.63 | 0.42 | 0.51 | 0.30 | 217.1 | 2.2 | no | rule checks 3/4 |
| Qwen2.5-3B-Instruct | 3B | 4-bit NF4 | Colab | transformers | 27.98 | 46.68 | 11.97 | 7.56 | 11.74 | 2.19 | 11.3 | 2.3 | no | rule checks 3/4; VRAM is torch peak allocated |
| qwen2.5:3b | 3B | Q4_K_M | Colab | Ollama | 10.42 | 10.57 | 2.31 | 1.11 | 1.37 | 0.39 | 81.5 | 2.2 | no | rule checks 2/4 |
| mistral:7b | 7B | Q4_K_M | Colab | Ollama | 23.27 | 5.69 | 5.15 | 2.78 | 5.18 | 1.34 | 38.1 | 5.0 | no | rule checks 3/4 |
| phi4:14b | 14B | Q4_K_M | Colab | Ollama | 33.69 | 53.79 | 11.34 | 7.33 | 13.27 | 11.28 | 13.7 | 9.7 | no | rule checks 0/4 |
| qwen2.5:3b | 3B | Q4_K_M | Jetstream2 | Ollama | | | | | | | | | | |
| mistral:7b | 7B | Q4_K_M | Jetstream2 | Ollama | | | | | | | | | | |
| phi4:14b | 14B | Q4_K_M | Jetstream2 | Ollama | | | | | | | | | | |

---

## 6. Evaluation

### 6.1 Rule-based checks

Automated, pass/fail. Applies to P2 through P5. P1 specifies no schema, so it has no
rule-based score and is evaluated by rubric only.

| Check | Definition |
|---|---|
| Parses | Output is valid JSON with no markdown fences or surrounding prose |
| Fields | Exactly the schema keys, none missing, none added |
| Values in range | P2 verdict is benign / suspicious / malicious and confidence is low / medium / high; P3 `src_port` and `pid` are numbers; P4 `rejected` covers both unchosen modes; P5 `known` is boolean |

Recorded per model per environment as a count out of four, which is the input to the
reliability comparison in the final analysis.

### 6.2 Human rubric

Scored 1 to 5 on two dimensions, by me, for every response including P1.

| Dimension | Question |
|---|---|
| Correct | Are the stated facts right, and is every claim traceable to the supplied evidence? |
| Usable | Could an analyst act on this as written, without cleanup? |

---

## 7. Expected content, for scoring reference

| Prompt | Correct outcome |
|---|---|
| P1 | Identifies repeated failed SSH logins followed by a success from the same source IP |
| P2 | Verdict suspicious or malicious; timestamps include 09:14:31; rationale names brute force or credential stuffing |
| P3 | All nine fields match the log line; src_port 51234, pid 2211, result failed |
| P4 | Choice is host-only; reason cites no route to the shared network |
| P5 | `known` is false |

---

## 8. Deviations from this plan

| Date | What changed | Why |
|---|---|---|
| 2026-10-05 | Runner unloads every resident model before each model's run. Official local data is `results/Local_20261005-231631`. | The first run (`Local_20261005-231359`) left earlier models loaded, which affected load times. |
| 2026-10-10 | Open WebUI run uses `qwen2.5:3b` with all model capabilities and built-in tools disabled. Input tokens verified equal to the API run (P1: 251). Data in `results/Local-OpenWebUI_20261010_responses.jsonl`. | With defaults, Open WebUI sent 2,050 input tokens for P1 (tool definitions added to the prompt) and displayed an empty reply. |
