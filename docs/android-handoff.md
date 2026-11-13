# Android handoff: CPU replication

This handoff is for the teammate who will measure the second device. It is an execution guide, not evidence that Android has been tested. Record the phone's model, SoC, RAM, Android build, battery condition, storage path, and available sensors before deciding whether a configuration fits.

## 1. Freeze and identify the device

On the Mac, note the repository commit and hashes for `configs/study.json`, `configs/models.json`, `prompts/corpus-v1.txt`, and the pinned runtime binary. On the phone, save:

```sh
adb devices -l
adb shell getprop ro.product.manufacturer
adb shell getprop ro.product.model
adb shell getprop ro.soc.model
adb shell getprop ro.build.version.release
adb shell getprop ro.build.fingerprint
adb shell cat /proc/meminfo
adb shell dumpsys battery
adb shell dumpsys thermalservice
```

Keep the complete outputs, including unavailable or permission-denied fields. Verify physical RAM from a trustworthy device source if the system does not report it. Record room conditions, screen state, battery percentage, charging state, foreground apps, and whether the phone is attached to a charger. Do not describe the user's earlier 6-8 GB estimate as verified hardware data.

## 2. Build the pinned ARM64 CPU runtime

Install/use the Android NDK already available on the Mac; record its version and path. Then:

```sh
export ANDROID_NDK="$HOME/Library/Android/sdk/ndk/<installed-version>"
sh scripts/build_android.sh
```

The script builds ARM64 CPU-only `llama-server`, `llama-bench`, and `llama-perplexity` from the pinned source with Vulkan, OpenMP, BLAS, and Metal disabled. It requests static project libraries and the static C++ runtime so the transferred server does not depend on unshipped llama.cpp shared libraries. Record the NDK version, build log, CMake cache, and SHA-256 of each binary. A successful cross-build is not a phone runtime validation.

## 3. Transfer runtime and one model

Download the official model files on the Mac and verify all manifest SHA-256 values with `python3 scripts/fetch_models.py`. Copy the chosen binary and model to a shell-readable temporary directory on the device. Start with the largest pilot: Qwen2.5-1.5B Q8_0, 2,048 input tokens, and 512 generated tokens.

```sh
adb shell mkdir -p /data/local/tmp/effai
adb shell getprop ro.product.cpu.abi
adb push "$HOME/.cache/effai/runtime/llama.cpp-79967ec596c0dacfd2251b085a57e79df292b1cc/build-android-cpu/bin/llama-server" /data/local/tmp/effai/
adb push "$HOME/.cache/effai/models/qwen2.5-1.5b-instruct-q8_0.gguf" /data/local/tmp/effai/
adb shell chmod 755 /data/local/tmp/effai/llama-server
adb shell sha256sum /data/local/tmp/effai/llama-server /data/local/tmp/effai/qwen2.5-1.5b-instruct-q8_0.gguf
adb forward tcp:8088 tcp:8088
```

Start the server in a retained `adb shell` or terminal session:

```sh
adb shell '/data/local/tmp/effai/llama-server -m /data/local/tmp/effai/qwen2.5-1.5b-instruct-q8_0.gguf -c 3072 -t 4 -tb 4 -b 512 -ub 128 -ngl 0 -np 1 -fa on -ctk f16 -ctv f16 --host 127.0.0.1 --port 8088 --no-webui'
```

Save the entire startup log. Confirm the loaded model, context size, CPU backend, and zero accelerator layers in the runtime output. Do not infer CPU use from the command alone. Confirm the host-side forwarded `/health` endpoint responds before sending prompts.

## 4. Validate the largest case before a matrix

Monitor process RSS and device free memory before, during, and after the largest case. Record `adb shell dumpsys meminfo <pid>`, `/proc/meminfo`, `dumpsys thermalservice`, and available battery temperature at consistent timestamps. Android may hide or virtualize counters; label unavailable data as unavailable. Capture process exit status, OOM evidence, logcat entries, throttling/thermal state, and whether the server remained responsive. Do not claim the phone supports the matrix based only on weight file size or a short startup smoke test.

For a single presentation-pilot request from the Mac, use a fresh unique run directory:

```sh
python3 scripts/record_request.py --url http://127.0.0.1:8088 \
  --input 2048 --output 512 \
  --run-dir results/android-pilot-<device>-largest \
  --label android-qwen15-q8-i2048-o512
```

This recorder preserves the exact prompt tokens, request, SSE stream, output count, stop reason, runtime timings, and client arrival proxies. It does not collect Android memory or thermal evidence. Attach a timestamped device-monitor log and server log. If any exact-count, context, or backend check fails, preserve the failure and do not schedule a full sweep.

## 5. Execute and return evidence

If the user-approved immediate presentation scope remains one measurement per configuration, execute the 24 main configurations once, with four randomized model/quantization blocks and six randomized configurations per block, one warm-up per loaded model, one request at a time, and F16 KV cache. The team may later run the complete protocol from `configs/study.json`: largest pilot first, then one warm-up plus three measured requests/configuration, randomized configuration blocks, at least 120 seconds between repeated configurations, and the strict thermal gate. Do not mix exploratory and controlled sessions or calculate SD from one observation.

For every run return a unique ID, exact config, prompt/request/stream files, server log, binary/model hashes, timestamps, process-memory samples, thermal/charge evidence, outcome or failure reason, and sensor-availability notes. Preserve originals. Return a compressed evidence bundle excluding model weights and credentials; include hashes for every returned file. Do not compare phone USB input energy with Mac component estimates unless the energy boundary is made comparable. No decode J/token without decode-phase-isolated energy.
