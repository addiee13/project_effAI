# Project 1: Profiling LLMs on Edge Devices

## 1. Objectives & Research Questions

**Goal:** Systematically measure and explain the efficiency of small LLMs on edge hardware.

### Key Questions

- How do model family, parameter count, and quantization (INT8/INT4/KV-cache quant) affect latency, tokens/s, energy, memory, and thermals?
- Where are the bottlenecks (prefill vs. decode; attention vs. matmul vs. sampling ops)?
- How do sequence length, KV-cache size, and scheduler settings influence performance and energy?
- How do results vary across edge hardware (phone vs. Pi/Jetson vs. NPU/TPU-class accelerators)?

## 2. Scope & Experimental Matrix

Pick 2 edge devices and 2–3 LLMs with 2 quantization levels; vary sequence lengths.

### Suggested Devices

- Android phone
- Laptops
- Raspberry Pi 5

### Suggested Runtimes

- MLC LLM
- llama.cpp / gguf

### Suggested Models

- Phi-3 Mini (~3.8B)
- Qwen2.5-3B
- Llama-3.1-8B-Instruct
- TinyLlama (~1–2B)

### Quantization

- INT8 and INT4 (with/without KV-cache quant)

### Sequence Lengths

- Prefill: 256, 1024, 2048
- Decode: 128, 512

## 3. Metrics & Instrumentation

### Core Metrics

- Latency
- Throughput
- Energy/Power
- Memory footprint
- Thermals
- Utilization
- Quality (optional)

### Collection Methods

- Wall-clock timing
- Profiler hooks (MLC/TVM, llama.cpp)
- Energy/Power (USB power meter, Android Battery Historian, Jetson tegrastats)
- Thermals/Utilization (perfetto, tegrastats)
- Memory (RSS, allocator logs)

## 4. Study Design & Methodology

A. **Baselines:** Establish baseline runs with standard prompt set, warm-up + 3 measured runs.

B. **Factorial sweeps:** Model × Quantization × SeqLen × Device.

C. **Bottleneck analysis:** Operator-level breakdowns to identify top-k kernels.

D. **Stability checks:** Replications, DVFS variations.

E. **Reporting conventions:** Separate prefill/decode, energy/token, efficiency (tokens/s/W).

## 5. Week-by-Week Timeline (8 weeks)

| Week | Activities |
| --- | --- |
| W1 | Setup, pilot run, protocol. |
| W2 | Baseline runs, pipeline. |
| W3 | Sweep Device A. |
| W4 | Sweep Device B. |
| W5 | Bottleneck study, paper draft. |
| W6 | Replications, finalize figures. |
| W7 | Write results, finalize repo. |
| W8 | Polish paper & slides. |

## 7. Analysis Checklist

- [ ] Normalize decode latency/energy per token.
- [ ] Attribute slowdowns to memory vs. compute bound.
- [ ] Discuss quantization accuracy impact.
- [ ] Note thermal throttling behavior.
- [ ] Identify knee points for context length.
- [ ] Provide deployment recommendations.
