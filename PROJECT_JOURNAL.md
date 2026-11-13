# Project journal

This journal preserves the November 11–12 planning history and records later execution as dated follow-ups. Entries reconstructed from earlier project context are marked by their original dates; exact durations were not measured unless stated. Mac presentation-pilot evidence was collected on November 13, 2026; Android results remain pending.

For future entries, record: date; problem/decision; alternatives; action and rationale; outcome/status; evidence; presentation implication. Append follow-ups when evidence or decisions change.

## 2026-11-11 — Selecting the project and hardware

- **Problem/decision:** The initial prompt-keyword study was replaced by Topic 1, profiling small language models on edge hardware. The team also replaced Raspberry Pi with an Android phone and added Vrushti Patel.
- **Alternatives:** Prompt-keyword effects versus broader efficiency profiling; Raspberry Pi versus Android as the second platform.
- **Action and rationale:** Updated the objectives to Topic 1 and saved a proposal for the M1 MacBook Air and Android phone. The proposal motivates studying real memory, processor, power, and thermal limits. A separate rationale for replacing the Pi was not recorded.
- **Outcome/status:** User-confirmed scope and team: Adam Dalwai, Mahean Seam, and Vrushti Patel. Android model/chipset/RAM remain unknown.
- **Evidence:** `PROJECT_OBJECTIVES.md`, `PROJECT_PROPOSAL.md`, and the user's hardware/team correction.
- **Presentation implication:** Introduce this as one two-device profiling project; explain the selected testbed without implying Pi experiments were performed.

## 2026-11-11 — Model selection required a dedicated research pass

- **Problem:** The proposal's TinyLlama/Qwen pair needed checks beyond parameter count: matching quantizations, context headroom, tokenizer comparability, licenses, and runtime memory.
- **Alternatives:** Retain TinyLlama 1.1B plus Qwen2.5 3B; use Qwen2.5 0.5B/1.5B; use Qwen2.5 1.5B/3B; consider newer Qwen3 variants.
- **Action and rationale:** At the user's request, a Luna research agent compared primary model/runtime sources and documented options. Effort included checking official checkpoint/GGUF cards, quantization availability, context limits, licenses, and study-design tradeoffs. Research duration: not timed.
- **Outcome/status:** Research recommends Qwen2.5 0.5B/1.5B as a conservative pair, with larger models conditional on RAM and pilot results. This remains a recommendation; the proposal has not adopted a replacement pair. TinyLlama's advertised 2,048-token context conflicts with a 2,048-token input plus 128-token output. Cross-family comparisons also confound model size with architecture/tokenizer differences.
- **Evidence:** `MODEL_RECOMMENDATIONS.md` contains the linked primary sources; `PROJECT_PROPOSAL.md` retains the original pair.
- **Presentation implication:** Explain how deployment feasibility and experimental control shaped model selection. Research findings are design evidence, not measured model performance.

## 2026-11-11 — Reusing existing tools and finding a validation gap

- **Problem:** The team needed to know which tools were already installed and whether a full setup would fit on the Mac.
- **Alternatives:** Install a new stack or reuse existing tools; use LM-Meter or direct llama.cpp measurements.
- **Action and rationale:** Performed a read-only local inventory. Found llama.cpp executables, Git/Clang/CMake, Android SDK/NDK/ADB, Python analysis libraries, powermetrics, and LM-Meter at `~/LM-Meter` with an existing Python environment. The existing llama-cli version command stalled and was terminated; the cause was not diagnosed.
- **Outcome/status:** Installation was confirmed, operational readiness was not. The audit observed about 6.8 GiB available at that time; the user subsequently directed that disk-space limits be ignored for model research. No cleanup or installation was performed. Tool-validation and Android pilots remain pending.
- **Evidence:** Terminal inventory in the project conversation; installed paths included `/opt/homebrew/bin/llama-bench`, `~/Library/Android/sdk`, and `~/LM-Meter`. Recheck these environment details before relying on them in a final report.
- **Presentation implication:** Describe reuse and validation of the experimental environment. Do not claim successful inference based on the presence of binaries.

## 2026-11-11 — Measurement tools must match the experiment

- **Problem:** LM-Meter availability did not establish compatibility with the planned llama.cpp backend, and USB power input does not automatically isolate inference energy.
- **Alternatives:** Use LM-Meter with a verified supported backend, use runtime timing plus platform profilers, or revise instrumentation after pilot results.
- **Action and rationale:** Checked official documentation. The reviewed LM-Meter support table listed MLC Android OpenCL as released and llama.cpp integration as forthcoming. Proposed direct llama.cpp timing and platform monitoring, with energy boundaries documented explicitly.
- **Outcome/status:** Instrumentation recommendations only; no profiling or energy collection has been validated on the selected devices. Reverify compatibility against the actual versions used.
- **Evidence:** [LM-Meter repository](https://github.com/amai-gsu/LM-Meter), [llama-bench documentation](https://github.com/ggml-org/llama.cpp/blob/master/tools/llama-bench/README.md), [Perfetto power documentation](https://perfetto.dev/docs/data-sources/battery-counters), and `AGENTS.md` measurement rules.
- **Presentation implication:** Explain why multiple tools are needed and distinguish runtime timing, application latency, and device/component energy.

## 2026-11-11 — Reconciling presentation and submission instructions

- **Problem:** Instructor screenshots differed on presentation duration and poster eligibility; the proposal also described a short report while the submission slide requires at least 10 pages.
- **Alternatives:** Rely on the poster alternative or prepare slides; plan a short report or follow the explicit page minimum.
- **Action and rationale:** Transcribed both screenshots into a requirements file. Adopted slides, an approximately 18-minute presentation plan, a video under two minutes, a working testbed, and a report of at least 10 pages as the working plan covering both sets of instructions.
- **Outcome/status:** Requirements and checklist recorded. Deadline is displayed as 12/7; year, upload time, and whether Q&A is included in the presentation window remain unconfirmed. Nothing has been submitted.
- **Evidence:** `PRESENTATION_AND_SUBMISSION_REQUIREMENTS.md` and instructor screenshots supplied by the user.
- **Presentation implication:** Build the final narrative around motivation, implementation, measured results, insights, and limitations; retain evidence for testbed and video evaluation.

## 2026-11-11 — Preserving the project process as evidence

- **Problem/decision:** The user requested continuous tracking of difficulties and decisions, including the effort involved in model research, for later presentation context.
- **Action and rationale:** Created this journal and added a session-end maintenance rule to `AGENTS.md` so future work captures relevant evidence as it happens.
- **Outcome/status:** Tracking established. Future entries should include failures and changing decisions, with measured durations only where available.
- **Evidence:** `AGENTS.md`, section "Ongoing project journal", and the user's explicit request.
- **Presentation implication:** Use selected entries to explain engineering choices and lessons, supported by actual work rather than retrospective claims.

## 2026-11-11 — Basing model selection on an estimated 6–8 GB phone

- **Problem/decision:** The user estimates that the Android phone has only 6–8 GB RAM and requested model selection based on that range. Exact RAM and chipset remain unverified.
- **Alternatives:** Keep the proposed TinyLlama/3B pair, use Qwen2.5 0.5B/1.5B, or pursue a larger Qwen pair that risks incomplete Q8_0 configurations.
- **Action and rationale:** Updated `MODEL_RECOMMENDATIONS.md` to prioritize Qwen2.5-0.5B-Instruct and Qwen2.5-1.5B-Instruct at both Q4_K_M and Q8_0. Plan for the 6 GB lower bound and defer 3B from the main matrix to protect completion of both quantization conditions on both devices. Disk-space limits remain excluded from this selection.
- **Outcome/status:** The RAM range is a user-provided planning assumption. The smaller pair is the current recommendation, not a verified fit or a completed proposal revision. The 24-configuration design is preserved. Pilot the largest selected case (1.5B Q8_0, 2,048 input tokens plus 128 output tokens) on both devices before freezing the matrix. No models were downloaded or benchmarked in this update; effort was not timed.
- **Evidence:** User's RAM estimate in this conversation; `MODEL_RECOMMENDATIONS.md` and its existing official GGUF sources; synchronized hardware guidance in `AGENTS.md`.
- **Presentation implication:** Explain that hardware memory constraints narrowed the model choices and that successful deployment at both quantization levels takes priority over selecting a larger model. Distinguish the estimate, pilot evidence, and final selection when presenting results.

## 2026-11-11 — Why we moved away from the proposal's model pair

- **Problem:** The proposal selected TinyLlama 1.1B and Qwen2.5 3B Instruct before we evaluated the complete workload against the phone's estimated 6–8 GB RAM. Model selection had to account for both quantization levels and the longest input/output combination, rather than weight size alone.
- **TinyLlama context limitation:** The researched TinyLlama-1.1B-Chat-v1.0 checkpoint has an advertised 2,048-token context. Our longest condition needs 2,048 input tokens plus 128 generated tokens, with formatting included in the input count. That exceeds its advertised context. Keeping TinyLlama would require shortening the workload or explicitly validating a context-extension method, which would introduce another experimental choice. This is a documented context mismatch, not an observed benchmark failure.
- **Qwen2.5 3B memory risk:** Its official Q8_0 GGUF file is approximately 3.62 GB before KV cache, activations/work buffers, and operating-system memory. On an estimated 6–8 GB phone, we could not assume reliable completion of the full matrix. A Q4-only success would not validate the required Q8_0 condition. No out-of-memory failure has been observed; this is a planning risk pending device measurements.
- **Experimental-control tradeoff:** TinyLlama and Qwen differ in model size, architecture family, tokenizer, and tuning. Their comparison could support deployment recommendations, but it could not isolate parameter-count effects. Using Qwen2.5 0.5B and 1.5B Instruct keeps the main comparison within one family and tuning regime. It improves control without making model size the only architectural difference; tokenizer equivalence and runtime settings still require verification.
- **Other considerations:** The Qwen2.5 3B checkpoint uses the Qwen Research License, while the recommended smaller checkpoints are Apache-2.0. This is an additional difference to document, not a claim that the research license prohibits our project. Both smaller models have official GGUF sources for the two requested quantizations.
- **Decision and tradeoff:** Prioritize Qwen2.5-0.5B-Instruct and Qwen2.5-1.5B-Instruct at Q4_K_M and Q8_0 for pilot validation. This reduces memory risk and preserves the 24-configuration design, at the cost of a smaller capacity range and losing a direct cross-family comparison. Larger models may be revisited as separately labeled extensions after successful pilots.
- **Outcome/status:** The user requested documenting this move. `MODEL_RECOMMENDATIONS.md` records the revised recommendation; `PROJECT_PROPOSAL.md` still preserves the original model choices. No models have been downloaded or tested, and the revised pair's runtime fit remains unverified. Effort was not timed.
- **Evidence:** `PROJECT_PROPOSAL.md`; `MODEL_RECOMMENDATIONS.md`, including linked TinyLlama context evidence and official Qwen GGUF/license sources; the user's estimated phone RAM and request to explain the change.
- **Presentation implication:** Explain that the initial proposal was refined through feasibility research: the revised models better match the planned context budget, phone memory constraint, and controlled quantization study. Present these as design reasons rather than claiming the original models failed on our hardware.

## 2026-11-11 — Standing authorization for automatic journal maintenance

- **Decision:** The user explicitly requested continued journal updates throughout the project without confirmation or reminders, preserving material useful for the presentation and paper.
- **Action and rationale:** Updated `AGENTS.md` to require automatic logging of meaningful developments during long sessions and at session end, and consultation of the journal when drafting deliverables.
- **Outcome/status:** Ongoing instruction established. Entries will explain actual research, decisions, validation, setbacks, and limitations with supporting evidence; presentation value does not justify inventing effort or results.
- **Evidence:** User's standing instruction and `AGENTS.md`, section "Ongoing project journal".
- **Presentation implication:** Maintain a reliable source for the methodology narrative, engineering lessons, and Q&A preparation throughout the project.

## 2026-11-12 — Repository initialization and remote setup on GitHub

- **Problem/decision:** The project deliverables require a documented GitHub repository link in the final report and version-controlled experimental configurations. The local workspace had not yet been turned into a Git repository.
- **Alternatives:** Manual git setup or delegated automation via a GitHub CLI subagent.
- **Action and rationale:** Initialized a Git repository on branch `main`, drafted a comprehensive `.gitignore` excluding large `.gguf` weights, system caches, and traces to keep the repository lightweight and compliant, committed existing project documentation, and created a public repository `addiee13/project_effAI` via `gh repo create`.
- **Outcome/status:** Repository live at `https://github.com/addiee13/project_effAI`. Clean baseline established for version-controlling scripts, prompt datasets, and aggregated metrics.
- **Evidence:** Git commit `a5be00e` and GitHub remote `https://github.com/addiee13/project_effAI.git`.
- **Presentation implication:** Satisfies the deliverable requirement for a public GitHub testbed repository to be cited in the report and slides.


## 2026-11-13 — User-approved exploratory Mac pilot completed; artifact rendering validated

- **Problem/decision:** The original controlled plan required three measured repetitions/configuration and a strict thermal gate. The user reduced the immediate presentation scope to one measured request/configuration, prioritizing feasible descriptive evidence and a later Android handoff.
- **Alternatives:** Wait through the strict idle stabilization gate and attempt the original repeated study, or preserve that protocol for future work while running a separately frozen presentation session.
- **Action and rationale:** Preserved the interrupted strict session and first presentation attempt, then used the separate frozen `mac-20261113-presentation-v2` scope: four model/quantization combinations, three input budgets, two output budgets, one same-process warm-up per loaded model, and one measured request per configuration. Timing was exploratory; no stabilization, standard-deviation, or repeatability claim was made.
- **Outcome/status:** All 24 unique requests passed the parent agent's independent audit for exact input/output counts, prompt/request token agreement, stop reason, no truncation, cache disabled, stream count, runtime denominators, and unique coverage. The saved run window was 05:45:39–05:54:36 UTC (00:45:39–00:54:36 EST). Temperature varied widely; the strict gate was not satisfied, so these are exploratory Mac CPU observations. A `caffeinate` assertion began at 05:52:10 UTC, partway through the sweep. Android has not been measured. One observation/configuration cannot estimate SD or repeatability.
- **Energy and sensor limits:** The one-second `macmon` temperature field varied during requests and GPU temperature was unavailable. Timestamped macmon samples supported gross CPU+GPU+ANE request-boundary estimates for 22/24 requests, including 11/12 of the 512-output cases; these are estimated component rails, not whole-device energy or decode J/token. The privileged `powermetrics` file is supplementary, not the headline energy source.
- **Artifact outcome:** The validated records produced traceable CSV/JSON and plots. The rendered report is 16 PDF pages (12 substantive pages, one references page, and three figure appendix pages), the slide deck is 17 slides planned for 18 minutes, and the silent evidence video is 72 seconds. The video uses a saved validated run, traceable plots, and stated n=1 and power-boundary limits. PDFs were rendered and visually reviewed; the MP4 was fully decoded with ffmpeg and inspected at opening, energy, and closing frames. The final video is H.264 1920x1080 at 30 fps.
- **Evidence:** `results/mac-20261113-presentation-v2/operations-notes.md`, frozen session plan and run JSON/SSE records; `analysis/mac-20261113-presentation-v2/`; `deliverables/evidence/`; `deliverables/output/`; `deliverables/validation/`. Raw runs and interrupted evidence remain preserved.
- **Presentation implication:** Present only descriptive findings from the Mac CPU pilot. Show no SD/error bars or two-device comparison. State that Android, the three-repeat strict-thermal study, WikiText-2 perplexity, focused KV-cache comparison, monitoring-overhead controls, and operator profiling remain future work. Distinguish this locally rendered artifact set from publication to GitHub or submission to iCollege.

## 2026-11-13 — Demo video excluded from GitHub publication at user direction

- **Problem/decision:** Before publishing the completed non-demo testbed and artifacts, the user said the demo was bad and explicitly directed that it not be pushed.
- **Alternatives:** Publish the previously rendered local MP4 and its editable HyperFrames source, or publish the reproducible testbed, evidence, report, and slides while excluding the rejected demo and marking a replacement pending.
- **Action and rationale:** Excluded `deliverables/demo-video/`, `deliverables/output/effai_mac_evidence_demo.mp4`, `deliverables/validation/video-*`, and `deliverables/validation/video-review/` from publication via targeted ignore rules. Kept report and slide artifacts, shared experimental evidence, and source provenance. Updated README and build manifest so they do not advertise a published or available demo. The local rejected video remains in the isolated worktree and was not deleted.
- **Outcome/status:** Publication push and remote verification pending at the time of this entry. This does not reverse the earlier historical record that a local MP4 was rendered and reviewed; it records the user's later rejection for publication. Replacement video pending.
- **Evidence:** User instruction in the project conversation; `.gitignore`, `README.md`, and `deliverables/validation/build_manifest.json`.
- **Presentation implication:** Do not cite the rejected local demo as an available GitHub deliverable. Describe the replacement as pending and keep the independently validated report, slides, and Mac pilot evidence distinct.
