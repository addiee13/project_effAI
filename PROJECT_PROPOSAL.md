# Topic 1 Project Proposal

## Efficiency Profiling of Small Language Models on Edge Hardware

**Team:** Adam Dalwai, Mahean Seam, and Vrushti Patel

## Why We Chose Topic 1

We chose Topic 1 because it lets us study how small language models behave under real hardware limits such as memory capacity, processor speed, power use, and temperature. The Topic 1 brief asks us to measure and explain efficiency rather than only compare model outputs. This makes the project a clear systems-focused experiment with practical results for selecting models on edge devices.

## Scope and Experimental Matrix

We will compare an Apple M1 MacBook Air and an Android phone using llama.cpp with GGUF models. The current adopted matrix has **2 devices × 2 models × 2 quantization levels × 3 input lengths × 2 output budgets**, for **48 configurations total (24 per device)**. The original proposal counted 24 across both devices because it included only a 128-token output condition; adding the assignment brief's 512-token output condition doubles that count. At three measured repetitions, the complete two-device matrix would contain 144 measured requests, plus warm-ups and focused studies. We will record the Android phone's model, chipset, RAM, and operating system version before benchmarking.

| Factor | Settings |
| --- | --- |
| Models | Qwen2.5-0.5B-Instruct and Qwen2.5-1.5B-Instruct (user-approved 2026-11-13; original choices retained below as proposal history) |
| Quantization | Q4_K_M and Q8_0 GGUF files |
| Input lengths | 256, 1,024, and 2,048 actual formatted tokens |
| Generation settings | One request at a time, 128 and 512 output tokens, temperature = 0 |
| Runtime settings | Same llama.cpp source revision, prompt set, and fixed thread setting per device; platform-specific builds |

## Method

Each configuration will receive one warm-up run followed by three measured runs in randomized order. We will report prompt processing (prefill) separately from token generation (decode), since the Topic 1 brief identifies them as different performance stages. We will wait at least two minutes between repeated runs and begin the next run only after the device temperature has stabilized.

The main comparison uses the standard F16 KV cache. To directly study the memory tradeoff highlighted in Topic 1, we will run one focused 2,048-token sub-study using a Q4_K_M model with F16 cache versus Q8_0 cache through `--cache-type-k q8_0 --cache-type-v q8_0`. This keeps the project manageable while showing how KV-cache quantization affects long-context use.

## Instrumentation and Measurements

We will record time to first token, prefill latency, inter-token latency, tokens per second, total time, peak memory, temperature, throttling, and utilization.

| Device | Instrumentation |
| --- | --- |
| Apple M1 MacBook Air | `powermetrics`, `/usr/bin/time -l`, and `asitop` for power, thermal, memory, and utilization monitoring, subject to supported samplers and permissions. |
| Android phone | llama.cpp timing logs; Perfetto/atrace for utilization and scheduling traces; ADB-accessible process memory and thermal information; and an inline USB-C power meter for external power and energy measurements. Available counters and permissions will be validated during pilot tests. |

For the Android phone, we will document charging state, battery level, screen state, background activity, and ambient conditions. USB input measurements will be reported as device-level measurements under the stated charging conditions; we will validate whether they can support a reliable inference-energy estimate during pilot testing.

For quality, we will run `llama-perplexity` on the WikiText-2 test data for each model and quantization level. This gives us a repeatable measure of whether Q4_K_M creates a measurable quality loss compared with Q8_0.

## Analysis, Expected Results, and Deliverables

We will calculate mean and standard deviation across the three measured runs and compare results per token. We expect Q4_K_M to reduce memory use and improve feasibility on the Android phone, while Q8_0 may provide better perplexity results. Longer contexts should increase prefill time and KV-cache memory use. Our final submission will include benchmark scripts, raw logs, plots, a short report, and a presentation with device-specific recommendations.

## Timeline

| Weeks | Activities |
| --- | --- |
| 1–2 | Setup, pilot tests, and validation of monitoring tools. |
| 3–4 | Run the full benchmark on both devices. |
| 5–6 | Complete KV-cache tests, quality tests, and analysis. |
| 7–8 | Create figures, finish the report, and prepare the presentation. |

## Adopted update — 2026-11-13

The user approved Qwen2.5-0.5B-Instruct and Qwen2.5-1.5B-Instruct in place of the originally proposed TinyLlama/Qwen2.5-3B pair. The selected models yield 24 configurations per device (48 total) at two quantizations, three input lengths, and two output budgets. The 512-token output condition was added to cover the assignment brief. Exact GGUF revisions and checksums are frozen in `configs/models.json`.

For the presentation, the user authorized one measured Mac request per configuration instead of the complete three-repetition experiment. This exploratory Mac sample has 24 planned configurations, one observation each; it supports descriptive points only, not a sample SD or repeatability claim. The full controlled study across both devices would have 144 measured requests. Its protocol remains documented in `configs/study.json` and `docs/protocol.md` for later completion. Android execution is pending and is not implied by this Mac plan.
