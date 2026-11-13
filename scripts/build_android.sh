#!/bin/sh
# Cross-build only. No phone is modified and no Android success is implied.
set -eu
: "${ANDROID_NDK:?Set ANDROID_NDK to an installed NDK directory}"
RUNTIME_DIR=${EFFAI_RUNTIME_DIR:-"$HOME/.cache/effai/runtime"}
SOURCE="$RUNTIME_DIR/llama.cpp-79967ec596c0dacfd2251b085a57e79df292b1cc"
test -d "$SOURCE"
test -f "$ANDROID_NDK/build/cmake/android.toolchain.cmake"
cmake -S "$SOURCE" -B "$SOURCE/build-android-cpu" \
  -DCMAKE_TOOLCHAIN_FILE="$ANDROID_NDK/build/cmake/android.toolchain.cmake" \
  -DANDROID_ABI=arm64-v8a -DANDROID_PLATFORM=android-28 \
  -DCMAKE_BUILD_TYPE=Release -DCMAKE_C_FLAGS=-march=armv8-a \
  -DCMAKE_CXX_FLAGS=-march=armv8-a -DGGML_OPENMP=OFF \
  -DBUILD_SHARED_LIBS=OFF -DANDROID_STL=c++_static \
  -DGGML_LLAMAFILE=OFF -DGGML_METAL=OFF -DGGML_VULKAN=OFF \
  -DGGML_BLAS=OFF -DLLAMA_CURL=OFF -DLLAMA_BUILD_TESTS=OFF
cmake --build "$SOURCE/build-android-cpu" --target llama-server llama-bench llama-perplexity -j 4
