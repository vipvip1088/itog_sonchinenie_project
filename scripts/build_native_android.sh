#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
: "${ANDROID_SDK_ROOT:=${ANDROID_HOME:-}}"
if [[ -z "${ANDROID_SDK_ROOT}" ]]; then
  echo "Укажи ANDROID_SDK_ROOT, например: export ANDROID_SDK_ROOT=\$HOME/Android/Sdk" >&2
  exit 1
fi
if [[ -n "${ANDROID_NDK_HOME:-}" ]]; then
  NDK="$ANDROID_NDK_HOME"
else
  NDK="$(find "$ANDROID_SDK_ROOT/ndk" -mindepth 1 -maxdepth 1 -type d 2>/dev/null | sort -V | tail -n 1 || true)"
fi
if [[ -z "$NDK" || ! -f "$NDK/build/cmake/android.toolchain.cmake" ]]; then
  echo "Не найден Android NDK. Установи NDK через Android SDK Manager и задай ANDROID_NDK_HOME." >&2
  exit 1
fi
command -v cmake >/dev/null || { echo "Установи CMake 3.22+" >&2; exit 1; }

BUILD_DIR="$ROOT/native/build-android"
cmake -S "$ROOT/native" -B "$BUILD_DIR" \
  -DCMAKE_TOOLCHAIN_FILE="$NDK/build/cmake/android.toolchain.cmake" \
  -DANDROID_ABI=arm64-v8a \
  -DANDROID_PLATFORM=android-28 \
  -DANDROID_STL=c++_static \
  -DGGML_NATIVE=OFF \
  -DGGML_OPENMP=OFF \
  -DGGML_LLAMAFILE=OFF \
  -DGGML_VULKAN=OFF \
  -DLLAMA_BUILD_TESTS=OFF \
  -DLLAMA_BUILD_EXAMPLES=OFF \
  -DLLAMA_BUILD_SERVER=OFF \
  -DLLAMA_CURL=OFF \
  -DCMAKE_BUILD_TYPE=Release
cmake --build "$BUILD_DIR" --target essay_llama --parallel "${BUILD_JOBS:-2}"

LIB="$(find "$BUILD_DIR" -name 'libessay_llama.so' -type f | head -n 1)"
if [[ -z "$LIB" ]]; then
  echo "CMake завершился, но libessay_llama.so не найден." >&2
  exit 3
fi
mkdir -p "$ROOT/native/libs/arm64-v8a"
cp "$LIB" "$ROOT/native/libs/arm64-v8a/libessay_llama.so"
echo "Готово: $ROOT/native/libs/arm64-v8a/libessay_llama.so"
