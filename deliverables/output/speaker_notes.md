# Speaker notes and rehearsal plan

Target: 18:00 including the 1:30 evidence demo. Timing is a rehearsal budget, not measured delivery.

## 1. How much does local inference cost?
Budget: 60 s | 00:00 to 01:00

Introduce the team and Topic 1. Our study asks how the cost of inference changes under a real edge device's memory, compute, and thermal limits. The selected pair is Qwen2.5 0.5B and 1.5B Instruct. We use two official GGUF weight variants for each checkpoint. The Mac phase uses a CPU baseline to create a clear starting point for the later phone replication. State the evidence cut shown in the results slides: Android has not been measured. A laptop result cannot establish phone feasibility or a cross-device winner. The contribution is a reproducible measurement chain that connects a configuration to raw observations and then to every plotted value.

## 2. A fast decoder can still feel slow
Budget: 60 s | 01:00 to 02:00

Explain the inference phases using the horizontal diagram. Loading is separate because a warm server has already paid that cost. Prefill processes the user's input, including formatting. Decode generates tokens after that populated context. A user sees request handling and delivery as well as runtime work, so client first-token time differs from the runtime's prefill number. This is why one tokens-per-second ranking cannot describe responsiveness. llama-bench excludes tokenization and sampling, as its official documentation states; our real-prompt stream complements runtime timing. Keep this distinction in mind when we discuss the results. Source: pinned llama-bench documentation, https://github.com/ggml-org/llama.cpp/blob/79967ec596c0dacfd2251b085a57e79df292b1cc/tools/llama-bench/README.md.

## 3. We narrowed the pair after feasibility research
Budget: 60 s | 02:00 to 03:00

The historical proposal is preserved in the repository. Research exposed two planning concerns: TinyLlama's advertised 2048-token context did not fit our longest input plus generation, and the 3B Q8 file left uncertain runtime headroom on a phone estimated at six to eight gigabytes. Neither concern is presented as an observed out-of-memory failure. The user approved the smaller same-family pair. This improves control over family and tuning while retaining a useful size difference, but it does not make parameter count the only architectural change. Official GGUF repositories provide both target weight variants. Sources: Qwen official 0.5B and 1.5B GGUF model cards, linked in references; PROJECT_JOURNAL.md for the decision history.

## 4. The Mac matrix has 24 configurations
Budget: 75 s | 03:00 to 04:15

The current main matrix contains 24 configurations per device because we include both output budgets: two model sizes, two weight variants, three input lengths, and two output lengths. The exploratory Mac presentation session has one measured request per configuration. It does not meet the complete repeated protocol. If all configurations were run on both devices, the full matrix would be 48 configurations. The original proposal counted 24 across both devices when it included only the 128-token output condition. A future controlled study uses three measured repetitions per configuration (144 measured requests across both devices), after a warm-up and with the strict thermal gate. Android is pending. The coverage table counts validated requests only.

## 5. Equal labels need exact token workloads
Budget: 75 s | 04:15 to 05:30

A nominal 2048-token prompt must really contain 2048 tokens after formatting. We save the token array and verify the runtime count. The maximum occupied workload is 2048 input plus 512 output, which fits inside the configured capacity of 3072. Capacity and occupancy are different: an allocated cache can reserve more memory than currently occupied positions. Timed requests disable prompt reuse so the long-context condition does the intended prefill work. Ignore-EOS forces a fixed generation budget for this controlled throughput workload. That is a measurement choice, not ordinary chat behavior or a claim that all generated tokens are useful. Tokens are a workload dimension rather than a measure of semantic work.

## 6. Pin the experiment, then prove the backend
Budget: 60 s | 05:30 to 06:30

Show the evidence flow. Model names alone do not identify the actual file, so the manifest saves revisions and SHA-256 checksums. The runtime is pinned to commit 79967ec596c0dacfd2251b085a57e79df292b1cc. The Mac Release build disables Metal, enables Accelerate, and uses zero GPU layers. We retain backend logs, not just configuration intent. An archive build can report an unknown version string because it lacks Git metadata; source and binary checksums provide the provenance. Every run is joined to a configuration and raw stream, memory, thermal, and server evidence. Derived tables and artifacts must come from the same saved snapshot. The public repository link is real, but new local work still needs publication verification.

## 7. Thermal data are exploratory in this presentation run
Budget: 75 s | 06:30 to 07:45

The presentation run used a bounded 30-second CPU-temperature observation window and one measurement per configuration. Its first reference window ranged from 40.85 to 50.25 degrees C, so it is not a stable idle baseline. Do not say the exploratory run passed the full thermal-stability rule. Later raw samples and power-state context are retained, and any timeouts remain visible. The complete controlled protocol remains stricter: a 60-second window with range at most one degree C and a mean no more than two degrees above a stable idle baseline, plus 120 seconds between repeated configurations.

## 8. Power boundaries decide which claims are valid
Budget: 60 s | 07:45 to 08:45

This panel integrates timestamped macmon CPU, GPU, and ANE power estimates across the client request interval. Eleven of twelve 512-output observations have sample brackets with no gap above the chosen limit; the plotted points are gross estimated component-rail joules, one per configuration. It excludes some system components and is not a whole-device measurement. It is not decode-phase isolated, so do not call it decode joules per token. The separate powermetrics log is supplementary; its system thermal-pressure samples were nominal while CPU-temperature readings rose substantially. Caffeinate began partway through the sweep, which also limits comparisons. Android USB input may include charging and remains a different boundary.

## 9. Results begin with coverage
Budget: 75 s | 08:45 to 10:00

Use the current generated coverage line rather than an earlier manually copied number. Explain the definition of included records, whether the required three repetitions are present, and why any attempts are excluded. Coverage tells the audience whether a comparison is a complete repeated result or a pilot. If the snapshot is incomplete, say so explicitly. Do not use a short smoke result as a throughput conclusion. Android has no measured values at this evidence cut. The table should not represent missing phone data as zero. Point the audience to the snapshot manifest and raw run identifiers supporting the numerical slides.

## 10. Weight quantization: compare within each checkpoint
Budget: 75 s | 10:00 to 11:15

Describe each point as a single Mac observation for the stated checkpoint, input, output, cache, and backend. There is no SD or error bar because n=1. The measured Q4/Q8 difference is descriptive for this run and exact runtime, not a reliable general ranking. A speed change alone does not prove a bandwidth bottleneck. Android and repeated controlled runs remain pending. The source table and run IDs trace each plotted point.

## 11. Context changes both work and interpretation
Budget: 60 s | 11:15 to 12:15

Explain how prefill and decode behave as populated context changes in the current data. The context plot must hold checkpoint, weight type, output budget, backend, and cache constant. Configured capacity remains 3072, so allocated cache memory may not rise with input length even though occupied context does. Three input lengths support a trend over the tested range but do not precisely locate a knee or justify extrapolation to maximum advertised context. Compare 128 and 512 outputs separately where evidence exists. Longer outputs increase total work and may expose sustained thermal behavior. Use actual output counts and retained stop reasons to verify the comparison.

## 12. Focused tests answer different questions
Budget: 60 s | 12:15 to 13:15

These focused studies are outside the current single-pass presentation matrix. The full protocol retains a long-context F16 versus Q8_0 KV-cache comparison, same-data within-model WikiText-2 perplexity, and a separate operator profile. We do not present results for work that was not executed. Perplexity would measure held-out likelihood, not instruction-following quality. Profiling timings would remain separate from headline timing.

## 13. What the evidence can support
Budget: 60 s | 13:15 to 14:15

The evidence supports descriptive observations for the validated Mac CPU requests only. One run per configuration cannot estimate within-configuration variability or support statistical significance. It does not support a repeatability claim. Android is pending, so there is no device winner or two-device conclusion. The observed values are specific to this pinned model, quantization, runtime, context, and thread setup.

## 14. Demo: trace one real request to its evidence
Budget: 90 s | 14:15 to 15:45

Play the actual generated demo video. This slot is ninety seconds and is included in the eighteen-minute presentation budget. The video uses real saved testbed evidence, not a synthetic interface simulating live inference. If live inference is available and approved under the presentation conditions, show one small case; do not run a new benchmark sweep. The evidence fallback should remain ready if a device or runtime is unavailable. Explain whether the view is replayed evidence or a current request. Show a run identifier, the exact token counts, the runtime timings, and the location of the corresponding analysis record. Do not type passwords or expose unrelated terminal history. After playback, transition directly to the handoff and conclusion.

## 15. Android handoff preserves the experiment
Budget: 60 s | 15:45 to 16:45

The teammate's work begins with device identification and the documented handoff, not with a blind full sweep. Physical RAM, available memory, process limits, thermal units, and supported counters must be checked. Keep model and runtime identities aligned with the Mac baseline and label platform build options. Run a small schema check, then the largest-condition pilot with complete output counts and monitoring. If it fails, save the evidence and revise the plan explicitly rather than dropping Q8 on only one device. Return the raw directory, hardware record, commands, and failures. When those files arrive, validate them before merging aggregates; energy comparisons require compatible boundaries.

## 16. The contribution is an auditable testbed
Budget: 45 s | 16:45 to 17:30

Close with the strongest measured conclusion currently present in the generated snapshot. Keep the distinction between implemented, measured, published, and submitted. The repository is the place to inspect configurations and reproduce analysis; verify the new work is published before claiming that every local file is available remotely. Our practical contribution is the chain from pinned workload to retained evidence to figures and conclusions. The Android phase will test whether the local recommendations survive on the actual phone. Thank the audience and move to questions without claiming that pending experiments or iCollege submission are complete.

## 17. References and questions
Budget: 30 s | 17:30 to 18:00

Sources are provided in full in the report and the deck's editable source. Qwen report: https://arxiv.org/abs/2412.15115v2. Official GGUF sources: https://huggingface.co/Qwen/Qwen2.5-0.5B-Instruct-GGUF and https://huggingface.co/Qwen/Qwen2.5-1.5B-Instruct-GGUF. Runtime: https://github.com/ggml-org/llama.cpp/tree/79967ec596c0dacfd2251b085a57e79df292b1cc. WikiText source: https://arxiv.org/abs/1609.07843. Reserve question time according to the instructor's final timing clarification. Prepare to explain why lower precision does not guarantee speedup, why CPU and energy boundaries matter, how exact token lengths were enforced, and what Android still needs to validate.
