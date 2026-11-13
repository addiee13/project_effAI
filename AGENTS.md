# Project guidance

## Purpose and team

This repository supports **Topic 1: Efficiency Profiling of Small Language Models on Edge Hardware**, by **Adam Dalwai, Mahean Seam, and Vrushti Patel**. Measure and explain inference efficiency with reproducible experiments on an **Apple M1 MacBook Air (8 GB RAM)** and an **Android phone**. The user estimates **6–8 GB phone RAM**; use this range for planning until verified. The phone's exact model, chipset, RAM, and OS remain unconfirmed. Raspberry Pi is outside the selected study.

Use standard shell commands and native agent tools directly, without command-rewriting wrappers.

## Read the relevant source

- **Scope or research questions:** read `PROJECT_OBJECTIVES.md` for the assignment brief and `PROJECT_PROPOSAL.md` for the team's proposed experiment. They describe one project, not separate projects.
- **Model selection or downloads:** read `MODEL_RECOMMENDATIONS.md`, including sources, RAM estimates, context limits, and license differences. Research recommendations are not adopted changes to the proposal.
- **Reports, slides, demos, scheduling, or completion checks:** read `PRESENTATION_AND_SUBMISSION_REQUIREMENTS.md`, transcribed from the instructor's screenshots. It records explicit requirements and unresolved differences between the slides.

Follow the user's latest decisions. Preserve the distinction between the assignment brief, current proposal, research recommendations, and measured results. When a plan differs from an explicit instructor requirement, document the difference rather than silently dropping the requirement.

## Current experimental plan

The proposal specifies llama.cpp/GGUF, TinyLlama 1.1B and Qwen2.5 3B Instruct, Q4_K_M and Q8_0 weights, 256/1,024/2,048 input tokens, 128 output tokens, temperature 0, and one request at a time. The main matrix has 24 configurations, with one warm-up and three measured runs per configuration in randomized order. Keep at least two minutes between repeated runs and require temperature stabilization; define a measurable stabilization rule in the protocol.

Use F16 KV cache for the main matrix and a focused long-context F16 versus Q8_0 cache comparison. Treat the objectives' additional 512-output-token condition as a scope difference to resolve before claiming full assignment coverage.

Model research recommends Qwen2.5 0.5B/1.5B Instruct as the main recommendation for the estimated 6–8 GB phone; defer 3B models from the main matrix and validate the smaller pair on both devices. The proposal has not been revised to adopt this pair. Resolve the selected pair before freezing the experiment matrix. TinyLlama's advertised 2,048-token context does not accommodate a 2,048-token input plus 128 output tokens; document a valid model/context choice before that run.

The user has explicitly asked to ignore disk-space limits for model selection. Continue to assess runtime RAM, context feasibility, and process limits. Reuse available tools after checking that they work; installation alone is not validation.

## Implementation and measurement

- Start with a successful, repeatable pilot on both devices, including the largest planned model/quant/context condition, before the full sweep.
- Pin the llama.cpp commit, platform build options, model checkpoint and file checksum, prompt/corpus version, thread count, backend, batch settings, sampling settings, and cache types.
- Record Android hardware/software details before making device-specific feasibility claims. Use a documented CPU baseline; label Metal, Android GPU, or other accelerator experiments separately and verify the actual backend in runtime logs.
- Count actual input tokens after formatting and reserve context for generated tokens. Distinguish configured capacity from occupied context. Save actual output counts and stop reasons.
- Separate model loading, prefill, decode, and end-to-end timing. Measure decode at the intended populated context. llama-bench excludes tokenization and sampling; use an instrumented real-prompt workload for first-token/inter-token and application timing.
- Preserve raw logs and per-run measurements alongside machine-readable configurations, run identifiers, timestamps, random seeds, and failure records. Record unsupported or failed configurations explicitly.
- Capture memory, temperature, throttling evidence, utilization, power conditions, and monitoring availability. Define memory metrics and units per platform; report missing sensors as unavailable.
- State the energy measurement boundary and phase, sampling method, charging conditions, and idle-baseline policy. USB input energy can include charging. Compare energy across devices only when boundaries are comparable; compute decode J/token only from isolated decode energy.
- Keep operator-profiling runs separate from headline timing runs. Validate instrumentation overhead. LM-Meter integration depends on runtime/backend support; verify compatibility before making it a dependency.
- Report means and standard deviations with individual observations retained. Quantization effects should compare variants of the same checkpoint. Model-family and parameter-count effects are confounded in a cross-family pair; matching token counts across tokenizers does not establish equal semantic work.
- Use the same held-out data and evaluation settings for within-model perplexity comparisons. Treat perplexity separately from instruction-following quality. Label hypotheses, estimates, and untested configurations clearly; every result and plot must trace to measured data.

## Work organization and validation

Keep scripts, configurations, raw results, analysis, and final artifacts distinguishable as they are added. Store large model files and local environments outside Git; record reproducible retrieval instructions and checksums instead. Preserve existing user work and raw evidence.

For benchmark changes, validate a small case and the resulting logs/schema before scheduling a sweep. For analysis changes, verify units, denominators, aggregation, and plots against raw runs. For research updates, verify changeable model/runtime facts against primary sources and link the supporting pages.

## Ongoing project journal

Maintain `PROJECT_JOURNAL.md` throughout the project as context for the final report, presentation, and Q&A. Read relevant entries when resuming work or explaining previous decisions. Before finishing a work session, record any meaningful research effort, difficulty, failed attempt, decision, tradeoff, workaround, or lesson from that session; update an existing issue's status when new evidence resolves it. Routine actions without a new finding do not need entries.

The user has given standing authorization to maintain this journal automatically, without asking for confirmation or waiting for a reminder. Log significant developments as they happen during longer sessions, not only at session end. Include validation milestones, unexpected findings, rejected alternatives, reproducibility improvements, and limitations when they help explain the project's contribution or engineering process. When drafting the paper or presentation, consult the journal and use relevant entries as context with their supporting evidence. Select entries for clarity and relevance; keep the account accurate even when outcomes are unfavorable.

Each entry should include the date, problem or decision, alternatives considered, action and rationale, observed outcome or pending status, supporting files/logs/sources, and the implication for the presentation. Distinguish user-approved decisions from agent recommendations and attempted fixes from verified resolutions. Record time or effort only when observed or measured; use "not timed" rather than inventing durations. Preserve earlier entries and append dated follow-ups when a decision changes. Capture useful failures as well as successes, with evidence instead of an exaggerated difficulty narrative.

## Deliverables and completion

The deliverables are a documented GitHub testbed, raw evidence and reproducible analysis, slides, a demo video **under 2 minutes**, and a report **at least 10 pages** with the required sections and GitHub link. Plan a presentation within **15–20 minutes** and prepare both a working testbed and video to cover the rubric. Consult the requirements file for exact coverage and deadline ambiguities.

A complete project requires executed device experiments, evidence-backed conclusions, reproducible commands, verified artifact rendering/playback, and the submission checklist. Distinguish implemented, tested, measured, and submitted states. Claim iCollege submission only after observing confirmation; creating files or a repository is not proof of submission.
