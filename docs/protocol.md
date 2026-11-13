# Experiment protocol and evidence status

## Adopted study

The user-approved model pair is Qwen2.5-0.5B-Instruct and Qwen2.5-1.5B-Instruct, each with official Q4_K_M and Q8_0 GGUF files. The original proposal is retained as project history. The selected device pair is the Apple M1 MacBook Air (8 GB) and an Android phone whose exact model and memory remain unverified. The study uses llama.cpp commit `79967ec596c0dacfd2251b085a57e79df292b1cc`, a 3,072-token context, four CPU threads, one request at a time, F16 KV cache, temperature zero, seed 113, disabled prompt caching, and exact formatted input budgets of 256, 1,024, and 2,048 tokens. Output budgets are 128 and 512 tokens. The harness sets `ignore_eos` to obtain fixed work; this is a throughput workload, not normal conversational stopping behavior.

The complete repeated protocol has 24 configurations per device (2 sizes x 2 weight variants x 3 inputs x 2 outputs), one same-process warm-up and three measured requests per configuration, randomized configuration order, at least 120 seconds between repeated requests, and a 60-second CPU-temperature window with range at most 1 C and mean no more than 2 C above an idle baseline. The main cache is F16. A separately labeled long-context cache comparison uses Qwen2.5-1.5B Q4_K_M at 2,048/128 with F16 and Q8_0 cache. Quality evaluation and operator profiling are separate studies.

## User-authorized presentation pilot

For presentation feasibility, the user reduced the immediate scope to one measured request per configuration. The Mac presentation session therefore schedules all 24 main configurations once each, randomizes four model/quantization blocks and their six configurations, and performs one server warm-up before the first request for each loaded model. It does not calculate standard deviations, claim repeatability, or substitute for the complete protocol. Its settings and provenance are frozen separately in `configs/presentation-pilot.json` and the corresponding session directory under `results/`.

Thermal measurements continue throughout the exploratory session, but the strict 60-second repeated-study gate is not claimed. The presentation configuration uses one bounded 30-second temperature observation window per loaded model block, permits a wait of at most 120 seconds, and proceeds as an exploratory measurement. The relaxed 10 C window criterion is not evidence of stabilization. In the first presentation observation, the reference window ranged from 40.85 C to 50.25 C (mean 43.46 C); label this an exploratory temperature reference, not a stable idle baseline. A timeout is preserved as failed stabilization. Stop the run if system thermal pressure is non-nominal. A missing temperature remains unavailable. The initial strict session stopped during idle-gate setup and produced no model measurement; its raw gate record is retained separately.

At 05:52:10 UTC (00:52:10 EST), the operator enabled a native `caffeinate` assertion to prevent idle sleep. This occurred after the presentation sweep began. Earlier and later observations therefore have different power-management context; the per-run power state and session operations log must accompany any interpretation. It is not evidence that the CPU was thermally stable or that the later observations are controlled repeats.

## Measurement boundaries

- Save each formatted prompt's token IDs and verify the runtime input count. Verify actual generated count, stop type, truncation state, and prompt-cache counters before treating a request as valid.
- Retain server logs, client SSE events, request JSON, run result JSON, sampled process RSS, and timestamped `macmon` samples. Client TTFT and inter-token intervals are arrival-event proxies; batched events share a timestamp and are not internal per-token timing.
- Keep runtime-reported prompt processing, decode, and total timings separate from client wall time and startup time. `sampled_peak_rss_kib` is a sampled process RSS peak, not a guaranteed OS lifetime maximum.
- The Mac CPU/GPU/ANE estimates do not measure whole-device wall energy. Report gross component-rail energy only if sample timestamps cover the observed request interval and the sample cadence is adequate. Do not call request energy decode J/token.
- macmon CPU temperature is the available temperature field; GPU temperature is unavailable in these samples. Preserve nulls. A separate privileged `powermetrics` log is supplementary and has its own sampler limitations; do not infer whole-device power from it.
- One observation per configuration supports descriptive points only. Do not report SD or significance. Main-matrix Q4/Q8 comparisons hold the checkpoint fixed; model-size comparisons remain specific to these two Qwen checkpoints.

## Reproduction

From the repository root, retrieve and verify the four model files with `python3 scripts/fetch_models.py`, build the pinned Mac CPU runtime with `sh scripts/build_runtime.sh`, and run the exploratory presentation session with:

```sh
python3 scripts/run_study.py --session mac-YYYYMMDD-presentation-v1 \
  --study-config configs/presentation-pilot.json
```

The script freezes configuration, plan, harness, runtime binary, model manifest, corpus, and checksums in the session directory. Do not edit those inputs while resuming a session. For the controlled repeated study, use `configs/study.json` in a new session only after the largest pilot and validated monitoring on both devices. Preserve interrupted and failed run directories; a corrected protocol requires a new session ID.
