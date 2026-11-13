# Small language model efficiency testbed

This repository supports a two-device study of Qwen2.5 inference efficiency on an Apple M1 MacBook Air and an Android phone. It contains pinned configurations, source/build and model retrieval scripts, exact-token prompt construction, per-run evidence capture, analysis, and project deliverables.

## Evidence status

The user's current presentation scope is a completed exploratory Mac CPU pilot with one observation per main-matrix configuration. Session `results/mac-20261113-presentation-v2/` has 24/24 unique configurations independently audited for token counts, stop reason, truncation, disabled cache, stream counts, and timing denominators. Thermal stabilization under the full protocol was not demonstrated; treat these as descriptive observations only. One run/configuration cannot support SD, significance, or repeatability. Android results are pending, so this is not a completed two-device study.

The complete controlled protocol remains in `configs/study.json` and `docs/protocol.md`: 24 configurations per device, three measured repetitions/configuration after a warm-up, a two-minute minimum gap, and a strict thermal gate. Across both devices that would be 48 configurations and 144 measured requests. Do not blend that future protocol with the completed 24-request Mac exploratory session. All measured results, failures, and unavailable sensors remain in the raw session directories.

## Selected workload

- Models: Qwen2.5-0.5B-Instruct and Qwen2.5-1.5B-Instruct.
- Weights: official Q4_K_M and Q8_0 GGUF files; exact revisions and SHA-256 values are in `configs/models.json`.
- Inputs: 256, 1,024, and 2,048 actual formatted tokens.
- Outputs: 128 and 512 tokens; the harness forces fixed output budgets and disables prompt-prefix reuse.
- Runtime: llama.cpp commit `79967ec596c0dacfd2251b085a57e79df292b1cc`, CPU baseline, four threads, one request, F16 KV cache, 3,072 context positions.

The exact formatted token arrays, runtime output counts, stream events, timings, logs, sampled RSS, and monitoring data are retained per run. Client first-token and inter-token metrics are SSE arrival proxies, not internal kernel timings. macOS component-power estimates are not whole-device wall power. Read `docs/protocol.md` before interpreting any figure.

## Reproduce on the Mac

Requires Python 3, CMake, a C/C++ toolchain, Git/curl, and the pinned runtime build options. Large files stay outside Git in the local cache.

```sh
python3 scripts/fetch_models.py
sh scripts/build_runtime.sh
python3 scripts/run_study.py --session mac-YYYYMMDD-presentation-v1 \
  --study-config configs/presentation-pilot.json
python3 analysis/analyze.py --session mac-YYYYMMDD-presentation-v1
```

Use a new session identifier for a changed config, runtime, corpus, manifest, or harness. An existing session checks its frozen provenance before resuming. Keep the raw run folders intact. The output analysis lists coverage and failures before reporting descriptive one-observation comparisons.

## Android

The tested device must first be identified and its RAM, Android build, thermal sensors, and memory headroom recorded. Use `docs/android-handoff.md` for ARM64 CPU build, largest-condition pilot, monitoring, and evidence return instructions. The checked-in build script performs a cross-build only; it does not imply that a phone run succeeded.

## Project files

- `configs/`: adopted exploratory and full repeated study settings, model manifest.
- `prompts/`: versioned source corpus.
- `scripts/`: model retrieval, runtime builds, benchmark harness, Android client recorder.
- `results/`: immutable raw session evidence; GGUF weights are excluded.
- `analysis/`: traceable summaries and plots derived from session JSON.
- `docs/`: protocol and Android handoff.
- `deliverables/source/`: editable report and slide sources, result snapshot, and renderer.
- `deliverables/output/`: rendered 16-page report, 17-slide PDF, and speaker notes.
- `deliverables/validation/`: report and slide PDF render review. The previously created local demo was rejected for publication by the user; its video, source, and review files are excluded. A replacement is pending.

## Completion checklist

- Mac presentation pilot: complete, 24/24 unique single observations; n=1 per configuration.
- Full repeated Mac protocol: pending. Android device identification, pilot, and matrix: pending teammate execution.
- Report PDF and slide PDF: rendered and visually reviewed.
- Demo video: prior local version rejected by the user and not published; replacement pending.
- GitHub publication and iCollege submission: publication is pending until the push is verified; iCollege submission is not verified.

Rebuild the report and slide PDFs with `python3 deliverables/source/build_artifacts.py`. The prior local demo build was rejected by the user and is not part of this published testbed; replacement pending.

The course repository is [github.com/addiee13/project_effAI](https://github.com/addiee13/project_effAI). Local isolated-worktree changes are not proof that the public GitHub copy contains the final work; verify publication separately.
