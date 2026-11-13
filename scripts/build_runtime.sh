#!/bin/sh
set -eu
COMMIT=79967ec596c0dacfd2251b085a57e79df292b1cc
RUNTIME_DIR=${EFFAI_RUNTIME_DIR:-"$HOME/.cache/effai/runtime"}
mkdir -p "$RUNTIME_DIR"
ARCHIVE="$RUNTIME_DIR/llama-b6784.tar.gz"
SOURCE="$RUNTIME_DIR/llama.cpp-$COMMIT"
if [ ! -d "$SOURCE" ]; then
  curl --fail --location --connect-timeout 30 --max-time 300 "https://codeload.github.com/ggml-org/llama.cpp/tar.gz/$COMMIT" -o "$ARCHIVE"
  tar -xzf "$ARCHIVE" -C "$RUNTIME_DIR"
fi
cmake -S "$SOURCE" -B "$SOURCE/build-cpu" -DCMAKE_BUILD_TYPE=Release -DGGML_METAL=OFF -DGGML_ACCELERATE=ON -DLLAMA_CURL=OFF -DLLAMA_BUILD_TESTS=OFF
cmake --build "$SOURCE/build-cpu" --target llama-server llama-bench llama-perplexity -j 4
"$SOURCE/build-cpu/bin/llama-server" --version
