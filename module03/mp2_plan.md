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
| (TBD) | | | 4-bit | | Hugging Face, via transformers |

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
| Processor | | | AMD EPYC-Milan |
| Logical cores | | | 16 |
| System RAM | | | 58 GiB |
| GPU | | | NVIDIA GRID A100X-20C (vGPU slice of A100 SXM4 40GB) |
| VRAM | | | 20 GiB (20480 MiB) |
| Driver / CUDA | | | 580.159.03 / 13.0 |
| How I checked | | | `nvidia-smi`, `lscpu`, `free -h`, `lspci -nnk` |

---

## 5. Per-run measurements

One row per model per environment. The same five prompts in every row.

| Model | Params | Quant | Environment | Tool | Load (s) | P1 (s) | P2 (s) | P3 (s) | P4 (s) | P5 (s) | tok/s | VRAM (GB) | CPU offload? | Notes |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| qwen2.5:3b | 3B | Q4_K_M | Local | Ollama | | | | | | | | | | |
| mistral:7b | 7B | Q4_K_M | Local | Ollama | | | | | | | | | | |
| phi4:14b | 14B | Q4_K_M | Local | Ollama | | | | | | | | | | |
| qwen2.5:3b | 3B | Q4_K_M | Local | Open WebUI | | | | | | | | | | |
| (HF model) | | 4-bit | Colab | transformers | | | | | | | | | | |
| qwen2.5:3b | 3B | Q4_K_M | Colab | Ollama | | | | | | | | | | |
| mistral:7b | 7B | Q4_K_M | Colab | Ollama | | | | | | | | | | |
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
| | | |
